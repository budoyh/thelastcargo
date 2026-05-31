"""Runtime preference repair helpers built from compiled DSL only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from . import config
from .geo import haversine_km
from .schemas import CandidateOption, World
from .time_utils import day_index, remaining_minutes


@dataclass(frozen=True)
class PreferenceTarget:
    rule_id: str
    lat: float
    lng: float
    value: float
    urgency: float
    day_hint: int | None
    repair_actions: tuple[str, ...]


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk(child)


def _target_coordinates(condition: dict[str, Any]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for item in _walk(condition):
        if isinstance(item, dict):
            lat_value = item.get("lat", item.get("latitude"))
            lng_value = item.get("lng", item.get("longitude"))
            if lat_value is None or lng_value is None:
                continue
            try:
                lat = float(lat_value)
                lng = float(lng_value)
            except (TypeError, ValueError):
                continue
            if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
                points.append((lat, lng))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                lat = float(item[0])
                lng = float(item[1])
            except (TypeError, ValueError):
                continue
            if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
                points.append((lat, lng))
    deduped: list[tuple[float, float]] = []
    for point in points:
        if point not in deduped:
            deduped.append(point)
    return deduped[:3]


def _day_hint(condition: dict[str, Any]) -> int | None:
    for key, value in condition.items():
        if not any(token in str(key).lower() for token in ("day", "date", "deadline")):
            continue
        candidates = value if isinstance(value, list) else [value]
        for item in candidates:
            try:
                day = int(item)
            except (TypeError, ValueError):
                continue
            if 1 <= day <= 31:
                return day
    return None


def targets(world: World) -> list[PreferenceTarget]:
    out: list[PreferenceTarget] = []
    current_day = day_index(world.status.simulation_progress_minutes) + 1
    for rule in world.rules.rules:
        coords = _target_coordinates(rule.condition)
        if not coords:
            continue
        amount = max(0.0, float(rule.reward_or_penalty.get("amount", 0.0) or 0.0))
        if amount <= 0.0:
            amount = 2500.0
        day = _day_hint(rule.condition)
        if day is None:
            urgency = 0.35
        elif current_day < day - 1:
            urgency = 0.18
        elif current_day <= day + 1:
            urgency = 1.0
        else:
            urgency = 0.15
        if rule.scope == "date_specific":
            urgency = max(urgency, 0.75)
        value = min(12_000.0, amount * max(0.25, rule.confidence) * urgency)
        for lat, lng in coords:
            out.append(
                PreferenceTarget(
                    rule_id=rule.rule_id,
                    lat=lat,
                    lng=lng,
                    value=value,
                    urgency=urgency,
                    day_hint=day,
                    repair_actions=rule.repair_action_kinds,
                )
            )
    return sorted(out, key=lambda item: item.value, reverse=True)[:5]


def take_repair_bonus(option: CandidateOption, world: World) -> float:
    if option.action_type != "take_order" or option.cargo is None or not config.ENABLE_NEXT_PREFERENCE_STATE_MACHINE:
        return 0.0
    bonus = 0.0
    for target in targets(world):
        if "take_towards_target" not in target.repair_actions and "reposition_to_target" not in target.repair_actions:
            continue
        start_distance = haversine_km(option.cargo.start_lat, option.cargo.start_lng, target.lat, target.lng)
        end_distance = haversine_km(option.cargo.end_lat, option.cargo.end_lng, target.lat, target.lng)
        nearest = min(start_distance, end_distance)
        if nearest > 45.0:
            continue
        proximity = max(0.0, 1.0 - nearest / 45.0)
        bonus += min(2200.0, target.value * (0.18 + 0.32 * proximity))
    return min(3200.0, bonus)


def build_repair_candidate(world: World, decision_id: str) -> CandidateOption | None:
    if not config.ENABLE_NEXT_PREFERENCE_STATE_MACHINE:
        return None
    remaining = remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)
    if remaining <= config.MIN_WAIT_MINUTES:
        return None
    best: CandidateOption | None = None
    for target in targets(world):
        if "reposition_to_target" not in target.repair_actions and target.urgency < 0.95:
            continue
        distance = haversine_km(world.status.current_lat, world.status.current_lng, target.lat, target.lng)
        if distance <= 5.0 and target.urgency >= 0.75:
            duration = min(180, max(config.MIN_WAIT_MINUTES, remaining))
            option = CandidateOption(
                id=f"preference_repair_wait:{target.rule_id}",
                action_type="wait",
                decision_id=decision_id,
                duration_minutes=int(duration),
                occupied_minutes=int(duration),
                finish_minutes=world.status.simulation_progress_minutes + int(duration),
                direct_money=0.0,
            )
            option.trace.update(
                {
                    "preference_repair": True,
                    "repair_kind": "target_wait",
                    "rule_id": target.rule_id,
                    "expected_repair_value": target.value,
                    "urgency": target.urgency,
                }
            )
        elif 5.0 < distance <= 120.0:
            duration = max(1, int(distance / config.REPOSITION_SPEED_KM_PER_HOUR * 60.0 + 0.999999))
            if world.status.simulation_progress_minutes + duration > world.horizon.horizon_minutes:
                continue
            cost = distance * config.DEFAULT_COST_PER_KM
            option = CandidateOption(
                id=f"preference_repair_reposition:{target.rule_id}",
                action_type="reposition",
                decision_id=decision_id,
                target_lat=float(target.lat),
                target_lng=float(target.lng),
                direct_money=-cost,
                occupied_minutes=duration,
                deadhead_km=distance,
                finish_minutes=world.status.simulation_progress_minutes + duration,
            )
            option.trace.update(
                {
                    "preference_repair": True,
                    "repair_kind": "runtime_dsl_target_reposition",
                    "rule_id": target.rule_id,
                    "target_source_kind": "runtime_preference_dsl_target",
                    "source_scope": "runtime_preference_dsl",
                    "distance_km": distance,
                    "empty_drive_cost": cost,
                    "expected_repair_value": target.value,
                    "urgency": target.urgency,
                    "day_hint": target.day_hint or "",
                    "payback_p50_minutes": min(360, duration + 120),
                    "payback_p80_minutes": min(720, duration + 300),
                }
            )
        else:
            continue
        if best is None or float(option.trace.get("expected_repair_value", 0.0)) > float(best.trace.get("expected_repair_value", 0.0)):
            best = option
    return best
