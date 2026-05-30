"""Conservative learned ranker placeholder with enforceable constraints."""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .schemas import CandidateOption, World


@dataclass(frozen=True)
class LinearWeights:
    direct_net_profit: float = 0.0
    deadhead_km: float = 0.0
    execution_risk: float = 0.0
    preference_violation_debt: float = 0.0
    high_confidence_repair_value: float = 0.0


def validate_sign_constraints(weights: LinearWeights) -> bool:
    return (
        weights.deadhead_km <= 0.0
        and weights.execution_risk <= 0.0
        and weights.preference_violation_debt <= 0.0
        and weights.direct_net_profit >= 0.0
        and weights.high_confidence_repair_value >= 0.0
    )


def _features(option: CandidateOption) -> dict[str, float]:
    pref_debt = option.pref_cert.violation_debt if option.pref_cert else 0.0
    repair = option.pref_cert.repair_value if option.pref_cert else 0.0
    execution_risk = option.deadhead_km + max(0, option.occupied_minutes - 720) * 0.1
    return {
        "direct_net_profit": option.direct_money,
        "deadhead_km": option.deadhead_km,
        "execution_risk": execution_risk,
        "preference_violation_debt": pref_debt,
        "high_confidence_repair_value": repair,
    }


def is_ood(option: CandidateOption, world: World) -> bool:
    return option.deadhead_km > 180.0 or option.occupied_minutes > 24 * 60 or world.time_market.sample_size < 3


def predict(option: CandidateOption, weights: LinearWeights) -> float:
    phi = _features(option)
    return (
        weights.direct_net_profit * phi["direct_net_profit"]
        + weights.deadhead_km * phi["deadhead_km"]
        + weights.execution_risk * phi["execution_risk"]
        + weights.preference_violation_debt * phi["preference_violation_debt"]
        + weights.high_confidence_repair_value * phi["high_confidence_repair_value"]
    )


def adjust_if_enabled(options: list[CandidateOption], world: World, weights: LinearWeights | None = None) -> list[CandidateOption]:
    if not config.ENABLE_LEARNED_RANKER:
        return options
    weights = weights or LinearWeights()
    if not validate_sign_constraints(weights):
        return options
    for option in options:
        learned = max(-config.LEARNED_CAP, min(config.LEARNED_CAP, predict(option, weights)))
        blend = min(config.LEARNED_BLEND, config.LEARNED_MAX_BLEND)
        if is_ood(option, world):
            blend *= config.LEARNED_OOD_SHRINK
        delta = blend * learned
        option.score += delta
        option.score_components["learned_delta"] = delta
    return options

