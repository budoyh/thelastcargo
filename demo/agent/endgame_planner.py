"""Resource-pressure endgame model."""

from __future__ import annotations

import math

from . import config
from .schemas import CandidateOption, PreferenceDebtMarket, ResourcePressureEndgame, RuleLedger, World
from .time_utils import remaining_minutes


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-20.0, min(20.0, x))))


def price_resource_pressure(
    *,
    status_minutes: int,
    horizon_minutes: int,
    ledger: RuleLedger,
    debt_market: PreferenceDebtMarket,
    market_liquidity: float,
) -> ResourcePressureEndgame:
    rem = remaining_minutes(status_minutes, horizon_minutes)
    remaining_ratio = rem / float(horizon_minutes)
    quota_pressure = min(1.0, ledger.preference_pressure + debt_market.debt_value / 600.0)
    scarcity = 1.0 - min(1.0, market_liquidity / 40.0)
    long_order_risk = 1.0 if rem < 36 * 60 else 0.0
    raw = (
        2.4 * quota_pressure
        + 2.0 * max(0.0, 0.18 - remaining_ratio)
        + 1.2 * long_order_risk
        + 0.7 * scarcity
        - 0.8 * min(1.0, market_liquidity / 80.0)
        - 1.1
    )
    intensity = min(config.MAX_ENDGAME_INTENSITY, max(0.0, _sigmoid(raw)))
    reasons: list[str] = []
    if debt_market.emergency:
        reasons.append("preference_debt")
    if rem < 3 * 1440:
        reasons.append("low_remaining_time")
    if scarcity > 0.6:
        reasons.append("low_liquidity")
    return ResourcePressureEndgame(intensity=intensity, remaining_minutes=rem, reasons=tuple(reasons))


def adjust(options: list[CandidateOption], world: World) -> list[CandidateOption]:
    if not config.ENABLE_RESOURCE_ENDGAME:
        return options
    for option in options:
        if option.action_type == "take_order" and world.endgame.intensity > config.ENDGAME_HIGH:
            long_ratio = option.occupied_minutes / max(1.0, world.endgame.remaining_minutes)
            penalty = 180.0 * world.endgame.intensity * max(0.0, long_ratio - 0.08)
            option.score -= penalty
            option.score_components["endgame_adjustment"] = -penalty
        elif option.action_type == "reposition":
            penalty = 90.0 * world.endgame.intensity
            option.score -= penalty
            option.score_components["endgame_adjustment"] = -penalty
    return options

