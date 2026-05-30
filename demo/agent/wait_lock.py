"""Wait-lock state and loop-breaker helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import config
from .schemas import CandidateOption, World


@dataclass
class WaitLockState:
    consecutive_wait: int = 0
    consecutive_query_wait: int = 0
    queries_since_last_take: int = 0
    max_consecutive_wait: int = 0
    feasible_positive_cargo_but_wait: int = 0
    positive_wait_events: int = 0
    micro_reposition_count: int = 0
    last_wait_reason: str = ""
    wait_reasons: dict[str, int] = field(default_factory=dict)
    day_wait_minutes: dict[int, int] = field(default_factory=dict)
    day_non_wait_actions: dict[int, int] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "consecutive_wait": self.consecutive_wait,
            "consecutive_query_wait": self.consecutive_query_wait,
            "queries_since_last_take": self.queries_since_last_take,
            "max_consecutive_wait": self.max_consecutive_wait,
            "feasible_positive_cargo_but_wait": self.feasible_positive_cargo_but_wait,
            "positive_wait_events": self.positive_wait_events,
            "micro_reposition_count": self.micro_reposition_count,
            "last_wait_reason": self.last_wait_reason,
            "wait_reasons": dict(self.wait_reasons),
            "day_wait_minutes": dict(self.day_wait_minutes),
            "day_non_wait_actions": dict(self.day_non_wait_actions),
        }

    def record(
        self,
        action_name: str,
        query_minutes: int,
        positive_count: int,
        wait_reason: str = "",
        *,
        day: int | None = None,
        wait_minutes: int = 0,
    ) -> None:
        if query_minutes > 0:
            self.queries_since_last_take += 1
        if action_name == "wait":
            self.consecutive_wait += 1
            if query_minutes > 0:
                self.consecutive_query_wait += 1
            if positive_count > 0:
                self.feasible_positive_cargo_but_wait += 1
                self.positive_wait_events += 1
            self.max_consecutive_wait = max(self.max_consecutive_wait, self.consecutive_wait)
            self.last_wait_reason = wait_reason
            self.wait_reasons[wait_reason or "unknown"] = self.wait_reasons.get(wait_reason or "unknown", 0) + 1
            if day is not None:
                self.day_wait_minutes[day] = self.day_wait_minutes.get(day, 0) + max(0, int(wait_minutes))
        elif action_name == "take_order":
            if day is not None:
                self.day_non_wait_actions[day] = self.day_non_wait_actions.get(day, 0) + 1
            self.consecutive_wait = 0
            self.consecutive_query_wait = 0
            self.queries_since_last_take = 0
        elif action_name == "reposition":
            if day is not None:
                self.day_non_wait_actions[day] = self.day_non_wait_actions.get(day, 0) + 1
            self.micro_reposition_count += 1
            self.consecutive_wait = 0
            self.consecutive_query_wait += 1


def query_k(state: WaitLockState, world: World) -> int:
    if world.endgame.remaining_minutes <= config.MIN_WAIT_MINUTES:
        return 0
    if state.consecutive_query_wait >= config.RESCUE_LOOP_BREAK_AFTER_WAITS:
        return config.RESCUE_QUERY_K_HIGH
    return config.RESCUE_QUERY_K_DEFAULT


def lowered_thresholds(state: WaitLockState) -> tuple[float, float]:
    direct = config.RESCUE_DIRECT_NET_FLOOR
    per_hour = config.RESCUE_PROFIT_PER_HOUR_FLOOR
    if not config.ENABLE_RESCUE_WAIT_PENALTY:
        return direct, per_hour
    if state.consecutive_wait >= config.RESCUE_LOOP_BREAK_AFTER_WAITS:
        direct = max(1.0, direct - 10.0 * (state.consecutive_wait - 2))
        per_hour = max(0.0, per_hour - 4.0 * (state.consecutive_wait - 2))
    return direct, per_hour


def wait_score_penalty(state: WaitLockState) -> float:
    if not config.ENABLE_RESCUE_WAIT_PENALTY:
        return 0.0
    return min(350.0, state.consecutive_wait * config.RESCUE_WAIT_PENALTY_STEP)
