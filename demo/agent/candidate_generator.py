"""Build legal candidate options from current observed cargo only."""

from __future__ import annotations

from . import config
from .geo import haversine_km, pickup_minutes
from .normalization import cost_per_km_from_status, finish_minutes_for_cargo
from .schemas import CandidateOption, NormalizedCargo, World
from .time_utils import remaining_minutes


def _take_option(world: World, cargo: NormalizedCargo) -> CandidateOption:
    p_minutes = pickup_minutes(cargo.pickup_distance_km, config.REPOSITION_SPEED_KM_PER_HOUR)
    arrival = world.status.simulation_progress_minutes + p_minutes
    wait_to_load = 0
    if cargo.load_start_minutes is not None and arrival < cargo.load_start_minutes:
        wait_to_load = cargo.load_start_minutes - arrival
    finish = finish_minutes_for_cargo(cargo, world.status.simulation_progress_minutes, p_minutes)
    distance_cost = (cargo.pickup_distance_km + cargo.haul_distance_km) * cost_per_km_from_status(world.status)
    direct_money = cargo.price_yuan - distance_cost
    occupied = p_minutes + wait_to_load + cargo.cost_time_minutes
    return CandidateOption(
        id=f"take:{cargo.cargo_id}",
        action_type="take_order",
        decision_id=cargo.decision_id,
        cargo=cargo,
        direct_money=direct_money,
        occupied_minutes=occupied,
        deadhead_km=cargo.pickup_distance_km,
        haul_km=cargo.haul_distance_km,
        finish_minutes=finish,
    )


def _wait_option(world: World, decision_id: str) -> CandidateOption:
    remaining = remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)
    if world.endgame.intensity >= config.ENDGAME_HIGH:
        duration = config.WAIT_MINUTES_ENDGAME
    elif world.debt_market.emergency:
        duration = config.WAIT_MINUTES_SHORT
    else:
        duration = config.WAIT_MINUTES_DEFAULT
    if remaining <= 0:
        duration = 0
    elif remaining < config.MIN_WAIT_MINUTES:
        duration = remaining
    else:
        duration = max(config.MIN_WAIT_MINUTES, min(config.MAX_WAIT_MINUTES, duration, remaining))
    return CandidateOption(
        id=f"wait:{duration}",
        action_type="wait",
        decision_id=decision_id,
        duration_minutes=int(duration),
        direct_money=0.0,
        occupied_minutes=int(duration),
        finish_minutes=world.status.simulation_progress_minutes + int(duration),
    )


def _reposition_option(world: World, cargos: list[NormalizedCargo], decision_id: str, take_options: list[CandidateOption]) -> CandidateOption | None:
    if not config.ENABLE_REPOSITION or not cargos:
        return None
    ranked = sorted(take_options, key=lambda o: o.direct_money / max(1.0, o.occupied_minutes), reverse=True)
    sample = [o.cargo for o in ranked[:5] if o.cargo is not None]
    if not sample:
        return None
    weights = [max(1.0, c.price_yuan / max(1, c.cost_time_minutes)) for c in sample]
    weight_sum = sum(weights)
    target_lat = sum(c.start_lat * w for c, w in zip(sample, weights)) / weight_sum
    target_lng = sum(c.start_lng * w for c, w in zip(sample, weights)) / weight_sum
    distance = haversine_km(world.status.current_lat, world.status.current_lng, target_lat, target_lng)
    if distance < config.REPOSITION_MIN_DISTANCE_KM or distance > config.REPOSITION_MAX_DISTANCE_KM:
        return None
    duration = max(1, int(distance / config.REPOSITION_SPEED_KM_PER_HOUR * 60.0 + 0.999999))
    empty_cost = distance * config.DEFAULT_COST_PER_KM
    expected_gain = max((o.direct_money for o in ranked[:8]), default=0.0) * 0.45
    option = CandidateOption(
        id="reposition:observed_centroid",
        action_type="reposition",
        decision_id=decision_id,
        target_lat=float(target_lat),
        target_lng=float(target_lng),
        direct_money=-empty_cost,
        occupied_minutes=duration,
        deadhead_km=distance,
        finish_minutes=world.status.simulation_progress_minutes + duration,
    )
    option.trace.update(
        {
            "reposition_cost": empty_cost,
            "expected_gain": expected_gain,
            "payback_time_p50": duration + 240,
            "payback_time_p80": duration + 540,
        }
    )
    return option


def build_options(world: World, visible_cargos: list[NormalizedCargo], decision_id: str) -> list[CandidateOption]:
    take_options = [_take_option(world, cargo) for cargo in visible_cargos]
    take_options = [o for o in take_options if o.finish_minutes <= world.horizon.horizon_minutes]
    options: list[CandidateOption] = list(take_options)
    options.append(_wait_option(world, decision_id))
    reposition = _reposition_option(world, visible_cargos, decision_id, take_options)
    if reposition is not None:
        options.append(reposition)
    best_take = max((o.direct_money for o in take_options), default=0.0)
    for option in options:
        option.current_best_order_advantage = best_take
    return options
