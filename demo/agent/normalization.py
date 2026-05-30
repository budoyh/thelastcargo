"""Normalize API dictionaries into stable agent schemas."""

from __future__ import annotations

from typing import Any

from . import config
from .geo import haversine_km
from .schemas import CURRENT_ACTIONABLE, DriverStatus, NormalizedCargo, SourceScope, VALID_SOURCE_SCOPES
from .time_utils import parse_load_window, wall_time_to_minutes


def normalize_status(raw: dict[str, Any]) -> DriverStatus:
    return DriverStatus(
        driver_id=str(raw.get("driver_id", "")).strip(),
        current_lat=float(raw.get("current_lat", 0.0)),
        current_lng=float(raw.get("current_lng", 0.0)),
        simulation_progress_minutes=int(raw.get("simulation_progress_minutes", 0)),
        simulation_wall_time=str(raw.get("simulation_wall_time", "")),
        truck_length=str(raw.get("truck_length", "")),
        preferences=tuple(raw.get("preferences") or ()),
        completed_order_count=int(raw.get("completed_order_count", 0) or 0),
    )


def normalize_cargo_item(
    item: dict[str, Any],
    *,
    world_minutes: int,
    source_scope: SourceScope = CURRENT_ACTIONABLE,
    decision_id: str,
) -> NormalizedCargo | None:
    if source_scope not in VALID_SOURCE_SCOPES:
        raise ValueError(f"invalid source_scope: {source_scope}")
    cargo = item.get("cargo") if isinstance(item, dict) else None
    if not isinstance(cargo, dict):
        return None
    cargo_id = str(cargo.get("cargo_id", "")).strip()
    if not cargo_id:
        return None
    start = cargo.get("start") or {}
    end = cargo.get("end") or {}
    try:
        start_lat = float(start["lat"])
        start_lng = float(start["lng"])
        end_lat = float(end["lat"])
        end_lng = float(end["lng"])
        price_yuan = float(cargo.get("price", 0.0))
        cost_time_minutes = int(cargo.get("cost_time_minutes", 0) or 0)
    except (TypeError, ValueError, KeyError):
        return None
    if cost_time_minutes < 0:
        return None
    raw_load_window = cargo.get("load_time")
    load_window = parse_load_window(raw_load_window)
    if raw_load_window is not None and load_window is None:
        return None
    load_start, load_end = load_window if load_window is not None else (None, None)
    pickup_distance = item.get("distance_km")
    try:
        pickup_distance_km = float(pickup_distance)
    except (TypeError, ValueError):
        pickup_distance_km = 0.0
    return NormalizedCargo(
        cargo_id=cargo_id,
        source_scope=source_scope,
        decision_id=decision_id,
        observed_at_minutes=int(world_minutes),
        price_yuan=price_yuan,
        pickup_distance_km=pickup_distance_km,
        start_lat=start_lat,
        start_lng=start_lng,
        end_lat=end_lat,
        end_lng=end_lng,
        cost_time_minutes=cost_time_minutes,
        create_minutes=wall_time_to_minutes(str(cargo.get("create_time"))) if cargo.get("create_time") else None,
        remove_minutes=wall_time_to_minutes(str(cargo.get("remove_time"))) if cargo.get("remove_time") else None,
        load_start_minutes=load_start,
        load_end_minutes=load_end,
        haul_distance_km=haversine_km(start_lat, start_lng, end_lat, end_lng),
    )


def finish_minutes_for_cargo(cargo: NormalizedCargo, now_minutes: int, pickup_minutes: int) -> int:
    arrival = int(now_minutes) + int(pickup_minutes)
    if cargo.load_start_minutes is not None and arrival < cargo.load_start_minutes:
        arrival = cargo.load_start_minutes
    return arrival + int(cargo.cost_time_minutes)


def is_online(cargo: NormalizedCargo, at_minutes: int) -> bool:
    if cargo.create_minutes is not None and at_minutes < cargo.create_minutes:
        return False
    if cargo.remove_minutes is not None and at_minutes >= cargo.remove_minutes:
        return False
    return True


def cost_per_km_from_status(_: DriverStatus) -> float:
    return config.DEFAULT_COST_PER_KM
