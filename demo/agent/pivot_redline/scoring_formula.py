"""Pivot-Redline scoring formula."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _float_env(name: str, default: float, lo: float, hi: float) -> float:
    try:
        value = float(os.environ.get(name, default))
    except (TypeError, ValueError):
        value = default
    return max(lo, min(hi, value))


def _int_env(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        value = default
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class PivotWeights:
    direct_net: float
    profit_per_hour: float
    preference_debt: float
    risk_model: float
    terminal_value: float
    lockup: float
    query_cost: float
    month_end: float
    repair_credit: float
    beam: float
    online_probe: float
    beam_depth: int
    beam_width: int
    all_new_weights_zero: bool = False

    @classmethod
    def from_env(cls, *, money_clean: bool) -> "PivotWeights":
        zero = os.environ.get("CROWN_PIVOT_ALL_WEIGHTS_ZERO", "0").strip() == "1"
        if zero:
            return cls(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, 0, True)
        return cls(
            direct_net=_float_env("CROWN_PIVOT_DIRECT_NET_WEIGHT", 1.0 if money_clean else 0.9, 0.0, 8.0),
            profit_per_hour=_float_env("CROWN_PIVOT_PPH_WEIGHT", 5.0 if money_clean else 3.0, 0.0, 50.0),
            preference_debt=_float_env("CROWN_PIVOT_PREF_DEBT_WEIGHT", 0.0 if money_clean else 0.8, 0.0, 20.0),
            risk_model=_float_env("CROWN_PIVOT_RISK_WEIGHT", 0.0 if money_clean else 80.0, 0.0, 500.0),
            terminal_value=_float_env("CROWN_PIVOT_TERMINAL_WEIGHT", 0.0 if money_clean else 0.18, 0.0, 5.0),
            lockup=_float_env("CROWN_PIVOT_LOCKUP_WEIGHT", 2.0 if money_clean else 3.0, 0.0, 80.0),
            query_cost=_float_env("CROWN_PIVOT_QUERY_COST_WEIGHT", 0.2, 0.0, 20.0),
            month_end=_float_env("CROWN_PIVOT_MONTH_END_WEIGHT", 0.0 if money_clean else 30.0, 0.0, 300.0),
            repair_credit=_float_env("CROWN_PIVOT_REPAIR_CREDIT_WEIGHT", 0.0 if money_clean else 0.35, 0.0, 20.0),
            beam=_float_env("CROWN_PIVOT_BEAM_WEIGHT", 0.0 if money_clean else 0.12, 0.0, 5.0),
            online_probe=_float_env("CROWN_PIVOT_ONLINE_PROBE_WEIGHT", 0.0 if money_clean else 0.25, 0.0, 5.0),
            beam_depth=_int_env("CROWN_PIVOT_BEAM_DEPTH", 1 if money_clean else 2, 1, 3),
            beam_width=_int_env("CROWN_PIVOT_BEAM_WIDTH", 0 if money_clean else 3, 0, 8),
            all_new_weights_zero=False,
        )


def weighted_score(components: dict[str, float], weights: PivotWeights) -> float:
    return (
        weights.direct_net * components.get("pivot_direct_net", 0.0)
        + weights.profit_per_hour * components.get("pivot_profit_per_hour", 0.0)
        + weights.preference_debt * components.get("pivot_preference_debt", 0.0)
        + weights.repair_credit * components.get("pivot_preference_repair_credit", 0.0)
        + weights.risk_model * components.get("pivot_risk_model", 0.0)
        + weights.terminal_value * components.get("pivot_terminal_value", 0.0)
        + weights.lockup * components.get("pivot_lockup_cost", 0.0)
        + weights.query_cost * components.get("pivot_query_cost", 0.0)
        + weights.month_end * components.get("pivot_month_end_guard", 0.0)
        + weights.beam * components.get("pivot_beam_rollout", 0.0)
        + weights.online_probe * components.get("pivot_online_probe_value", 0.0)
    )
