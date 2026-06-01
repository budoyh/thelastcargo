"""Low-risk micro-reposition candidates from current visible pickup points."""

from __future__ import annotations

from . import config, macro_commitment
from .geo import haversine_km
from .schemas import CandidateOption, NormalizedCargo, World
from .wait_lock import WaitLockState


def build_candidate(world: World, visible: list[NormalizedCargo], decision_id: str, state: WaitLockState) -> CandidateOption | None:
    if not config.ENABLE_RESCUE_MICRO_REPOSITION:
        return None
    if state.consecutive_wait < config.RESCUE_MICRO_REPOSITION_TRIGGER_WAITS:
        return None
    if not visible:
        return None
    ranked = sorted(visible, key=lambda c: c.price_yuan / max(1, c.cost_time_minutes), reverse=True)[:8]
    if not ranked:
        return None
    weights = [max(1.0, c.price_yuan / max(1, c.cost_time_minutes)) for c in ranked]
    weight_sum = sum(weights)
    best_visible_value = max((c.price_yuan - 1.5 * (c.pickup_distance_km + c.haul_distance_km) for c in ranked), default=0.0)
    target_lat = sum(c.start_lat * w for c, w in zip(ranked, weights)) / weight_sum
    target_lng = sum(c.start_lng * w for c, w in zip(ranked, weights)) / weight_sum
    distance = haversine_km(world.status.current_lat, world.status.current_lng, target_lat, target_lng)
    if distance < config.RESCUE_MICRO_REPOSITION_MIN_KM:
        return None
    interpolation_ratio = 1.0
    if distance > config.RESCUE_MICRO_REPOSITION_MAX_KM:
        interpolation_ratio = config.RESCUE_MICRO_REPOSITION_MAX_KM / distance
        target_lat = world.status.current_lat + (target_lat - world.status.current_lat) * interpolation_ratio
        target_lng = world.status.current_lng + (target_lng - world.status.current_lng) * interpolation_ratio
        distance = haversine_km(world.status.current_lat, world.status.current_lng, target_lat, target_lng)
    duration = max(1, int(distance / config.REPOSITION_SPEED_KM_PER_HOUR * 60.0 + 0.999999))
    if world.status.simulation_progress_minutes + duration > world.horizon.horizon_minutes:
        return None
    option = CandidateOption(
        id="micro_reposition:visible_cluster",
        action_type="reposition",
        decision_id=decision_id,
        target_lat=float(target_lat),
        target_lng=float(target_lng),
        direct_money=-distance * config.DEFAULT_COST_PER_KM,
        occupied_minutes=duration,
        deadhead_km=distance,
        finish_minutes=world.status.simulation_progress_minutes + duration,
    )
    option.trace.update(
        {
            "micro_reposition": True,
            "target_source": "current_visible_pickup_cluster",
            "target_source_kind": "current_actionable_pickup_cluster",
            "source_scope": "current_actionable",
            "cluster_count": len(ranked),
            "interpolation_ratio": interpolation_ratio,
            "distance_km": distance,
            "empty_drive_cost": abs(distance * config.DEFAULT_COST_PER_KM),
            "expected_gain_6h": max(0.0, best_visible_value) * 0.18,
            "expected_gain_12h": max(0.0, best_visible_value) * 0.30,
            "payback_p50_minutes": 360,
            "payback_p80_minutes": 720,
            "payback_window_6h": 360,
            "payback_window_12h": 720,
        }
    )
    macro_commitment.mark_macro_candidate(
        option,
        macro_type="escape_reposition",
        avoided_penalty=0.0,
        repair_value=max(0.0, best_visible_value) * 0.18,
        lost_gross=abs(option.direct_money),
        deadline_minutes=option.finish_minutes + 360,
        feasibility="current_visible_cluster_escape",
        confidence=0.45,
        required_duration=0,
        permits_query=True,
    )
    return option
