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
    _last_rejections.set((decision_id, []))
    seen: set[str] = set()
    for item in raw_cargos:
        cargo = normalize_cargo_item(
            item,
            world_minutes=world.status.simulation_progress_minutes,
            source_scope=source_scope,
            decision_id=decision_id,
        )
        if cargo is None:
            _record_rejection(decision_id, None, "normalize_failed")
            continue
        if cargo.cargo_id in seen:
            _record_rejection(decision_id, cargo.cargo_id, "duplicate")
            continue
        seen.add(cargo.cargo_id)
        if source_scope != CURRENT_ACTIONABLE:
            _record_rejection(decision_id, cargo.cargo_id, "non_current_actionable_source")
            continue
        if not is_online(cargo, world.status.simulation_progress_minutes):
            _record_rejection(decision_id, cargo.cargo_id, "not_online")
            continue
        if (
            config.ENABLE_RESCUE_SCORER
            and cargo.remove_minutes is not None
            and cargo.remove_minutes - world.status.simulation_progress_minutes < config.RESCUE_MIN_REMOVE_SLACK_MINUTES
        ):
            _record_rejection(decision_id, cargo.cargo_id, "remove_slack_too_short")
            continue
        p_minutes = pickup_minutes(cargo.pickup_distance_km, config.REPOSITION_SPEED_KM_PER_HOUR)
        arrival = world.status.simulation_progress_minutes + p_minutes
        if cargo.load_end_minutes is not None and arrival > cargo.load_end_minutes:
            _record_rejection(decision_id, cargo.cargo_id, "load_window_unreachable")
            continue
        finish = finish_minutes_for_cargo(cargo, world.status.simulation_progress_minutes, p_minutes)
        if finish > world.horizon.horizon_minutes:
            _record_rejection(decision_id, cargo.cargo_id, "finish_after_horizon")
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


class _LastRejections:
    def __init__(self) -> None:
        self.decision_id = ""
        self.items: list[dict[str, str | None]] = []

    def set(self, payload: tuple[str, list[dict[str, str | None]]]) -> None:
        self.decision_id, self.items = payload


_last_rejections = _LastRejections()


def _record_rejection(decision_id: str, cargo_id: str | None, reason: str) -> None:
    if _last_rejections.decision_id != decision_id:
        _last_rejections.set((decision_id, []))
    _last_rejections.items.append({"cargo_id": cargo_id, "reason": reason})


def rejection_summary(decision_id: str) -> dict[str, int]:
    if _last_rejections.decision_id != decision_id:
        return {}
    counts: dict[str, int] = {}
    for item in _last_rejections.items:
        reason = str(item.get("reason") or "unknown")
        counts[reason] = counts.get(reason, 0) + 1
    return counts
