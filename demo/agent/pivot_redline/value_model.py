"""Lightweight terminal value estimator from current visible market."""

from __future__ import annotations

from ..geo import haversine_km
from ..schemas import CandidateOption, NormalizedCargo


class PivotValueModel:
    """Estimate V(s') from current post-query visible cargo only."""

    def terminal_value(self, option: CandidateOption, visible: list[NormalizedCargo]) -> float:
        if option.action_type != "take_order" or option.cargo is None:
            return 0.0
        value = 0.0
        for cargo in visible:
            distance = haversine_km(option.cargo.end_lat, option.cargo.end_lng, cargo.start_lat, cargo.start_lng)
            if distance <= 60.0:
                value += cargo.price_yuan / max(1.0, cargo.cost_time_minutes / 60.0)
        return round(min(value / 10.0, 300.0), 6)
