"""Cost-aware query sizing for the independent pivot path."""

from __future__ import annotations

import os

from .world_adapter import PivotQueryPlan


def _int_env(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        value = default
    return max(lo, min(hi, value))


def choose_query_plan(world: object, *, money_clean: bool, noop_exact_b0: bool) -> PivotQueryPlan:
    if noop_exact_b0:
        return PivotQueryPlan("pivot_noop_exact_b0_query", 120, "b0_noop_oracle_query_k")
    if money_clean:
        k = _int_env("CROWN_PIVOT_MONEY_QUERY_K", 300, 50, 600)
        return PivotQueryPlan("pivot_money_clean_query", k, "recover_high_gross_backbone")
    visible_pressure = float(getattr(getattr(world, "memory_view", object()), "recent_feasible_count", 0.0) or 0.0)
    endgame = float(getattr(getattr(world, "endgame", object()), "intensity", 0.0) or 0.0)
    if endgame > 0.80:
        return PivotQueryPlan("pivot_endgame_small_query", 80, "protect_horizon")
    if visible_pressure < 6:
        return PivotQueryPlan("pivot_deepen_query", 300, "low_recent_liquidity")
    return PivotQueryPlan("pivot_balanced_query", _int_env("CROWN_PIVOT_QUERY_K", 200, 50, 600), "balanced_information_cost")
