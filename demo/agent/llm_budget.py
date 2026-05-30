"""LLM budget manager.

The Tournament Build keeps judge calls disabled by default, but the manager
still exists so enabling a limited judge requires an explicit budget gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .schemas import CandidateOption, World
from .time_utils import day_index


@dataclass
class LLMBudgetManager:
    max_compile_calls_per_driver: int = config.LLM_MAX_COMPILE_CALLS_PER_DRIVER
    max_judge_calls_per_driver: int = config.LLM_MAX_JUDGE_CALLS_PER_DRIVER
    max_judge_calls_per_day: int = config.LLM_MAX_JUDGE_CALLS_PER_DAY
    timeout_seconds: float = config.LLM_TIMEOUT_SECONDS
    cache_by_pref_hash: bool = True
    compile_calls_by_driver: dict[str, int] = field(default_factory=dict)
    judge_calls_by_driver: dict[str, int] = field(default_factory=dict)
    judge_calls_by_driver_day: dict[tuple[str, int], int] = field(default_factory=dict)

    def allow_judge(self, driver_id: str, world: World, options: list[CandidateOption]) -> bool:
        if not config.ENABLE_LLM_JUDGE:
            return False
        if self.judge_calls_by_driver.get(driver_id, 0) >= self.max_judge_calls_per_driver:
            return False
        key = (driver_id, day_index(world.status.simulation_progress_minutes))
        if self.judge_calls_by_driver_day.get(key, 0) >= self.max_judge_calls_per_day:
            return False
        top = sorted(options, key=lambda o: o.score, reverse=True)[:2]
        needs_help = any(o.pref_cert and o.pref_cert.unknown_risk > 1.0 for o in top)
        return needs_help

    def record_judge(self, driver_id: str, world: World) -> None:
        key = (driver_id, day_index(world.status.simulation_progress_minutes))
        self.judge_calls_by_driver[driver_id] = self.judge_calls_by_driver.get(driver_id, 0) + 1
        self.judge_calls_by_driver_day[key] = self.judge_calls_by_driver_day.get(key, 0) + 1
    def allow_compile(self, driver_id: str, pref_hash: str, *, cached: bool) -> bool:
        if cached and self.cache_by_pref_hash:
            return True
        return self.compile_calls_by_driver.get(driver_id, 0) < self.max_compile_calls_per_driver

    def record_compile(self, driver_id: str) -> None:
        self.compile_calls_by_driver[driver_id] = self.compile_calls_by_driver.get(driver_id, 0) + 1

