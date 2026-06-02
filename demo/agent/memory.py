"""Per-driver legal observation memory.

The memory stores aggregate summaries only. It never stores old cargo as an
actionable candidate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from . import config
from .schemas import CURRENT_ACTIONABLE, DriverMemoryView, NormalizedCargo, World


@dataclass
class DriverMemory:
    observations_count: int = 0
    recent_best_profit_per_min: float = 0.0
    recent_feasible_count: float = 0.0
    recent_query_minutes: int = 0
    recent_wait_outcomes: list[float] = field(default_factory=list)
    online_graph_cells: dict[tuple[int, int], dict[str, float]] = field(default_factory=dict)
    online_graph_observations: int = 0

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
        self._update_online_graph(cargos)

    def online_graph_snapshot(self) -> dict[str, Any]:
        return {
            "observations": self.online_graph_observations,
            "cell_count": len(self.online_graph_cells),
            "cells": {cell: dict(stats) for cell, stats in self.online_graph_cells.items()},
        }

    def _update_online_graph(self, cargos: list[NormalizedCargo]) -> None:
        alpha = 0.25
        updated = False
        for cargo in cargos:
            if cargo.source_scope != CURRENT_ACTIONABLE:
                continue
            direct = cargo.price_yuan - config.DEFAULT_COST_PER_KM * (cargo.pickup_distance_km + cargo.haul_distance_km)
            profit_per_min = direct / max(1, cargo.cost_time_minutes)
            pickup_cell = _cell_id(cargo.start_lat, cargo.start_lng)
            delivery_cell = _cell_id(cargo.end_lat, cargo.end_lng)
            pickup = self.online_graph_cells.setdefault(pickup_cell, {})
            _ema_add(pickup, "visible_count_ema", 1.0, alpha)
            _ema_add(pickup, "pickup_density_ema", 1.0, alpha)
            _ema_add(pickup, "profit_per_min_ema", profit_per_min, alpha)
            _ema_add(pickup, "top_margin_ema", max(0.0, direct), alpha)
            if direct > 0:
                _ema_add(pickup, "positive_margin_count", 1.0, alpha)
            delivery = self.online_graph_cells.setdefault(delivery_cell, {})
            _ema_add(delivery, "delivery_inflow_ema", 1.0, alpha)
            _ema_add(delivery, "top_margin_ema", max(0.0, direct), alpha)
            updated = True
        if updated:
            self.online_graph_observations += 1


def _cell_id(lat: float, lng: float) -> tuple[int, int]:
    size = max(0.000001, float(config.VISIBLE_GRAPH_CELL_DEGREES))
    return math.floor(float(lat) / size), math.floor(float(lng) / size)


def _ema_add(stats: dict[str, float], key: str, value: float, alpha: float) -> None:
    old = float(stats.get(key, 0.0) or 0.0)
    stats[key] = (1.0 - alpha) * old + alpha * float(value)
