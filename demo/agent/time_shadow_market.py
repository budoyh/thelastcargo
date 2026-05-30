"""Candidate-aware time shadow pricing."""

from __future__ import annotations

from statistics import median

from . import config
from .schemas import CandidateOption, DriverMemoryView, PreferenceDebtMarket, ResourcePressureEndgame, TimeShadowMarket, World


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _shrink_to_prior(value: float, sample_size: int, prior: float) -> float:
    weight = min(1.0, max(0.0, sample_size / 18.0))
    return weight * value + (1.0 - weight) * prior


def _robust_price(memory: DriverMemoryView) -> float:
    samples = [v for v in memory.recent_wait_outcomes if v > 0]
    if samples:
        return float(median(samples))
    return max(config.GLOBAL_BASE_PRICE_PER_MIN, memory.recent_best_profit_per_min)


def price(
    *,
    memory: DriverMemoryView,
    debt_market: PreferenceDebtMarket,
    endgame: ResourcePressureEndgame,
) -> TimeShadowMarket:
    raw = _robust_price(memory)
    raw += 0.004 * debt_market.repair_price
    raw += 0.7 * endgame.intensity
    sample_size = max(0, memory.observations_count)
    productive = _shrink_to_prior(raw, sample_size, config.GLOBAL_BASE_PRICE_PER_MIN)
    productive = _clip(productive, config.MIN_PRODUCTIVE_TIME_PRICE, config.MAX_PRODUCTIVE_TIME_PRICE)
    if endgame.intensity > 0.8:
        productive = min(productive, config.ENDGAME_TIME_PRICE_CAP)
    query_cost = _clip(config.GLOBAL_BASE_PRICE_PER_MIN + 0.35 * endgame.intensity + 0.002 * debt_market.debt_value, 0.3, 3.5)
    info_value = _clip(12.0 + memory.recent_feasible_count * 2.0 + debt_market.unknown_risk * 0.12, 0.0, config.INFORMATION_OPTION_VALUE_CAP)
    return TimeShadowMarket(
        productive_time_shadow_price=productive,
        query_time_cost=query_cost,
        information_option_value=info_value,
        sample_size=sample_size,
        mode=config.TIME_SHADOW_MODE,
    )


def productive_time_shadow_price_excluding(
    option: CandidateOption,
    world: World,
    all_options: list[CandidateOption],
) -> float:
    if not config.ENABLE_TIME_SHADOW or world.time_market.mode == "baseline_profit_per_hour":
        return config.GLOBAL_BASE_PRICE_PER_MIN
    alt_values = [
        max(0.0, other.direct_money) / max(1.0, other.occupied_minutes)
        for other in all_options
        if other.id != option.id and other.action_type == "take_order"
    ]
    alt_premium = max(alt_values, default=0.0)
    top_take = max(
        (o for o in all_options if o.action_type == "take_order"),
        key=lambda o: o.direct_money / max(1.0, o.occupied_minutes),
        default=None,
    )
    if top_take is not None and top_take.id == option.id:
        alt_premium *= config.TOP1_SELF_OPPORTUNITY_DISCOUNT
    raw = world.time_market.productive_time_shadow_price + alt_premium
    return _clip(
        _shrink_to_prior(raw, world.time_market.sample_size, config.GLOBAL_BASE_PRICE_PER_MIN),
        config.MIN_PRODUCTIVE_TIME_PRICE,
        config.MAX_PRODUCTIVE_TIME_PRICE,
    )


def information_optionality_loss(option: CandidateOption, world: World) -> float:
    if option.action_type == "wait":
        return 0.15 * world.time_market.information_option_value
    if option.action_type == "reposition":
        return 0.35 * world.time_market.information_option_value
    long_factor = min(1.0, option.occupied_minutes / 720.0)
    return min(config.OPTIONALITY_LOSS_CAP, world.time_market.information_option_value * long_factor)


def query_plan_score(expected_information_gain: float, expected_query_minutes: int, world: World, missed_window_risk: float = 0.0) -> float:
    return (
        expected_information_gain
        - world.time_market.query_time_cost * max(0, expected_query_minutes)
        - missed_window_risk
        - (45.0 if world.debt_market.emergency else 0.0)
    )

