"""Cargo source-scope isolation and W-after-query filtering."""

from __future__ import annotations

from . import config
from .geo import pickup_minutes
from .normalization import finish_minutes_for_cargo, is_online, normalize_cargo_item
from .schemas import CURRENT_ACTIONABLE, NormalizedCargo, SourceScope, World


def normalize_and_filter(
    *,
    raw_cargos: list[dict],
    world: World,
    source_scope: SourceScope,
    decision_id: str,
) -> list[NormalizedCargo]:
    out: list[NormalizedCargo] = []
    seen: set[str] = set()
    for item in raw_cargos:
        cargo = normalize_cargo_item(
            item,
            world_minutes=world.status.simulation_progress_minutes,
            source_scope=source_scope,
            decision_id=decision_id,
        )
        if cargo is None or cargo.cargo_id in seen:
            continue
        seen.add(cargo.cargo_id)
        if source_scope != CURRENT_ACTIONABLE:
            continue
        if not is_online(cargo, world.status.simulation_progress_minutes):
            continue
        p_minutes = pickup_minutes(cargo.pickup_distance_km, config.REPOSITION_SPEED_KM_PER_HOUR)
        arrival = world.status.simulation_progress_minutes + p_minutes
        if cargo.load_end_minutes is not None and arrival > cargo.load_end_minutes:
            continue
        finish = finish_minutes_for_cargo(cargo, world.status.simulation_progress_minutes, p_minutes)
        if finish > world.horizon.horizon_minutes:
            continue
        out.append(cargo)
    return out


def fast_normalize_and_filter(raw_cargos: list[dict], world: World, decision_id: str) -> list[NormalizedCargo]:
    return normalize_and_filter(
        raw_cargos=raw_cargos,
        world=world,
        source_scope=CURRENT_ACTIONABLE,
        decision_id=decision_id,
    )

