"""Hand scorer with candidate-aware time shadow cost."""

from __future__ import annotations

from .schemas import CandidateOption, World
from .time_shadow_market import information_optionality_loss, productive_time_shadow_price_excluding


def score(option: CandidateOption, world: World, all_options: list[CandidateOption]) -> float:
    if not isinstance(option, CandidateOption):
        raise TypeError("time_bid_scorer.score requires CandidateOption")
    time_price = productive_time_shadow_price_excluding(option, world, all_options)
    time_cost = time_price * max(0, option.occupied_minutes)
    optionality_loss = information_optionality_loss(option, world)
    pref_repair = option.pref_cert.repair_value if option.pref_cert else 0.0
    pref_debt = option.pref_cert.violation_debt if option.pref_cert else 0.0
    unknown_risk = option.pref_cert.unknown_risk * world.debt_market.unknown_risk * 0.02 if option.pref_cert else 0.0
    execution_risk = 0.0
    if option.action_type == "take_order":
        if option.deadhead_km > 80.0:
            execution_risk += (option.deadhead_km - 80.0) * 1.5
        if option.occupied_minutes > 720:
            execution_risk += (option.occupied_minutes - 720) * 0.25
    elif option.action_type == "reposition":
        execution_risk += 40.0 + option.deadhead_km * 0.5
    rollout = option.rollout.value if option.rollout else 0.0
    total = (
        option.direct_money
        - time_cost
        - optionality_loss
        + rollout
        + pref_repair
        - pref_debt
        - unknown_risk
        - execution_risk
        - world.endgame.intensity * 20.0
    )
    option.score_components.update(
        {
            "direct_money": option.direct_money,
            "time_cost": -time_cost,
            "optionality_loss": -optionality_loss,
            "rollout": rollout,
            "preference_repair": pref_repair,
            "preference_debt": -pref_debt,
            "unknown_preference_risk": -unknown_risk,
            "execution_risk": -execution_risk,
            "endgame_risk": -world.endgame.intensity * 20.0,
        }
    )
    option.score = total
    return total
