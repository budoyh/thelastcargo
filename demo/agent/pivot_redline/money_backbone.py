"""High-gross clean money scoring components."""

from __future__ import annotations

from ..schemas import CandidateOption


def components(option: CandidateOption) -> dict[str, float]:
    if option.action_type == "take_order":
        pph = option.direct_money / max(1.0, option.occupied_minutes / 60.0)
        lockup = option.occupied_minutes / 60.0
        return {
            "pivot_direct_net": float(option.direct_money),
            "pivot_profit_per_hour": float(pph),
            "pivot_lockup_cost": -float(lockup),
            "pivot_pickup_deadhead_cost": -float(option.deadhead_km),
        }
    if option.action_type == "wait":
        return {
            "pivot_direct_net": 0.0,
            "pivot_profit_per_hour": 0.0,
            "pivot_lockup_cost": -float(option.duration_minutes) / 60.0,
            "pivot_pickup_deadhead_cost": 0.0,
        }
    return {
        "pivot_direct_net": float(option.direct_money),
        "pivot_profit_per_hour": 0.0,
        "pivot_lockup_cost": -float(option.occupied_minutes) / 60.0,
        "pivot_pickup_deadhead_cost": -float(option.deadhead_km),
    }
