"""Per-driver legal observation memory.

The memory stores aggregate summaries only. It never stores old cargo as an
actionable candidate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .schemas import DriverMemoryView, NormalizedCargo, World


@dataclass
class DriverMemory:
    observations_count: int = 0
    recent_best_profit_per_min: float = 0.0
    recent_feasible_count: float = 0.0
    recent_query_minutes: int = 0
    recent_wait_outcomes: list[float] = field(default_factory=list)

    def snapshot(self) -> DriverMemoryView:
        return DriverMemoryView(
            observations_count=self.observations_count,
            recent_best_profit_per_min=self.recent_best_profit_per_min,
            recent_feasible_count=self.recent_feasible_count,
            recent_query_minutes=self.recent_query_minutes,
            recent_wait_outcomes=tuple(self.recent_wait_outcomes[-20:]),
        )

    def update_current_observation(self, world: World, cargos: list[NormalizedCargo], query_minutes: int) -> None:
        feasible = len(cargos)
        best = 0.0
        for cargo in cargos:
            minutes = max(1, cargo.cost_time_minutes)
            gross = cargo.price_yuan - config.DEFAULT_COST_PER_KM * cargo.haul_distance_km
            best = max(best, gross / minutes)
        self.observations_count += 1
        alpha = 0.25
        self.recent_best_profit_per_min = (1 - alpha) * self.recent_best_profit_per_min + alpha * best
        self.recent_feasible_count = (1 - alpha) * self.recent_feasible_count + alpha * feasible
        self.recent_query_minutes = int(query_minutes)

