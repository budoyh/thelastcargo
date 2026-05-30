"""Visible two-hop rollout using only the current observed set."""

from __future__ import annotations

from . import config
from .geo import haversine_km, pickup_minutes
from .normalization import finish_minutes_for_cargo, is_online
from .schemas import CURRENT_ACTIONABLE, CandidateOption, NormalizedCargo, RolloutValue, World


def _state_after_take(option: CandidateOption, world: World) -> tuple[int, float, float] | None:
    if option.cargo is None:
        return None
    return option.finish_minutes, option.cargo.end_lat, option.cargo.end_lng


def evaluate(option: CandidateOption, world: World, visible_cargos: list[NormalizedCargo]) -> RolloutValue:
    if not config.ENABLE_VISIBLE_TWO_HOP or option.action_type != "take_order" or option.cargo is None:
        return RolloutValue()
    state = _state_after_take(option, world)
    if state is None:
        return RolloutValue()
    time_a, lat_a, lng_a = state
    second: list[tuple[float, NormalizedCargo]] = []
    for cargo in visible_cargos:
        if cargo.cargo_id == option.cargo.cargo_id:
            continue
        if cargo.source_scope != CURRENT_ACTIONABLE or cargo.decision_id != option.decision_id:
            continue
        if not is_online(cargo, time_a):
            continue
        dead_km = haversine_km(lat_a, lng_a, cargo.start_lat, cargo.start_lng)
        dead_min = pickup_minutes(dead_km, config.REPOSITION_SPEED_KM_PER_HOUR)
        arrival = time_a + dead_min
        if cargo.load_end_minutes is not None and arrival > cargo.load_end_minutes:
            continue
        finish = finish_minutes_for_cargo(cargo, time_a, dead_min)
        if finish > world.horizon.horizon_minutes:
            continue
        direct = cargo.price_yuan - config.DEFAULT_COST_PER_KM * (dead_km + cargo.haul_distance_km)
        value = direct - world.time_market.productive_time_shadow_price * max(1, finish - time_a)
        second.append((value, cargo))
    second.sort(key=lambda item: item[0], reverse=True)
    used: list[str] = []
    best = 0.0
    for value, cargo in second[: config.TWO_HOP_SECOND_K]:
        used.append(cargo.cargo_id)
        best = max(best, config.TWO_HOP_DISCOUNT * value)
    return RolloutValue(value=best, used_second_hop_ids=used)

