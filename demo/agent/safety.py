"""Final action safety layer."""

from __future__ import annotations

from . import config
from .schemas import CURRENT_ACTIONABLE, ActionCertificate, CandidateOption, World
from .time_utils import remaining_minutes


def pre_filter_and_attach_action_certificate(
    options: list[CandidateOption],
    world: World,
    observed_ids: set[str],
) -> list[CandidateOption]:
    safe_options: list[CandidateOption] = []
    for option in options:
        cert = _certificate_for(option, observed_ids)
        option.action_cert = cert
        if option.finish_minutes > world.horizon.horizon_minutes:
            cert.safe = False
            cert.reasons.append("finish_over_horizon")
        if cert.safe:
            safe_options.append(option)
    return safe_options


def _certificate_for(option: CandidateOption, observed_ids: set[str]) -> ActionCertificate:
    if option.action_type == "take_order":
        cargo = option.cargo
        reasons: list[str] = []
        safe = True
        if cargo is None:
            safe = False
            reasons.append("missing_cargo")
            cargo_id = None
            scope = None
        else:
            cargo_id = cargo.cargo_id
            scope = cargo.source_scope
            if cargo.source_scope != CURRENT_ACTIONABLE:
                safe = False
                reasons.append("non_actionable_source_scope")
            if cargo.cargo_id not in observed_ids:
                safe = False
                reasons.append("not_in_current_observed_set")
            if cargo.decision_id != option.decision_id:
                safe = False
                reasons.append("decision_id_mismatch")
        return ActionCertificate(option.id, option.action_type, option.decision_id, cargo_id, scope, safe, reasons)
    if option.action_type == "wait":
        safe = option.duration_minutes > 0
        reasons = [] if safe else ["non_positive_wait"]
        return ActionCertificate(option.id, option.action_type, option.decision_id, None, None, safe, reasons)
    reasons = []
    safe = option.target_lat is not None and option.target_lng is not None
    if not safe:
        reasons.append("missing_target")
    return ActionCertificate(option.id, option.action_type, option.decision_id, None, None, safe, reasons)


def reposition_payback_allowed(option: CandidateOption, world: World) -> bool:
    if option.action_type != "reposition":
        return True
    if option.trace.get("preference_repair"):
        expected_repair = float(option.trace.get("expected_repair_value", 0.0) or 0.0)
        empty_cost = abs(option.direct_money)
        if option.deadhead_km > 120.0:
            option.action_cert.reasons.append("preference_repair_too_far") if option.action_cert else None
            return False
        if expected_repair <= config.REPOSITION_PAYBACK_MULTIPLIER * empty_cost:
            option.action_cert.reasons.append("preference_repair_value_too_low") if option.action_cert else None
            return False
        if world.endgame.intensity >= config.ENDGAME_HIGH:
            option.action_cert.reasons.append("endgame_high") if option.action_cert else None
            return False
        if option.pref_cert and option.pref_cert.high_confidence_irreversible_violation:
            option.action_cert.reasons.append("preference_damage") if option.action_cert else None
            return False
        return True
    if option.trace.get("micro_reposition"):
        if option.deadhead_km > config.RESCUE_MICRO_REPOSITION_MAX_KM:
            option.action_cert.reasons.append("micro_reposition_too_far") if option.action_cert else None
            return False
        if world.endgame.intensity >= config.ENDGAME_HIGH:
            option.action_cert.reasons.append("endgame_high") if option.action_cert else None
            return False
        if option.pref_cert and option.pref_cert.high_confidence_irreversible_violation:
            option.action_cert.reasons.append("preference_damage") if option.action_cert else None
            return False
        return True
    expected_gain = float(option.trace.get("expected_gain", 0.0))
    empty_cost = abs(option.direct_money)
    payback_p50 = float(option.trace.get("payback_time_p50", 10**9))
    payback_p80 = float(option.trace.get("payback_time_p80", 10**9))
    if option.current_best_order_advantage >= config.REPOSITION_STRONG_ORDER_THRESHOLD:
        option.action_cert.reasons.append("current_order_strong") if option.action_cert else None
        return False
    if expected_gain <= config.REPOSITION_PAYBACK_MULTIPLIER * empty_cost:
        option.action_cert.reasons.append("payback_gain_too_low") if option.action_cert else None
        return False
    if payback_p50 >= config.REPOSITION_PAYBACK_P50_MAX_MIN:
        option.action_cert.reasons.append("payback_p50_too_slow") if option.action_cert else None
        return False
    if payback_p80 >= config.REPOSITION_PAYBACK_P80_MAX_MIN:
        option.action_cert.reasons.append("payback_p80_too_slow") if option.action_cert else None
        return False
    if world.endgame.intensity >= config.ENDGAME_HIGH:
        option.action_cert.reasons.append("endgame_high") if option.action_cert else None
        return False
    if option.pref_cert and option.pref_cert.high_confidence_irreversible_violation:
        option.action_cert.reasons.append("preference_damage") if option.action_cert else None
        return False
    return True


def choose_best_with_certificates(options: list[CandidateOption], world: World) -> CandidateOption:
    filtered = []
    for option in options:
        if option.action_cert is not None and not option.action_cert.safe:
            continue
        if option.action_type == "reposition" and not reposition_payback_allowed(option, world):
            continue
        if option.pref_cert and option.pref_cert.high_confidence_irreversible_violation:
            continue
        filtered.append(option)
    if not filtered:
        return _fallback_option(world, "no_safe_option")
    return max(filtered, key=lambda o: o.score)


def _fallback_option(world: World, reason: str) -> CandidateOption:
    remaining = remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)
    if remaining <= 0:
        duration = 0
    elif remaining < config.MIN_WAIT_MINUTES:
        duration = remaining
    else:
        duration = max(config.MIN_WAIT_MINUTES, min(config.WAIT_MINUTES_SHORT, remaining))
    option = CandidateOption(
        id=f"fallback_wait:{reason}",
        action_type="wait",
        decision_id=f"fallback:{world.status.simulation_progress_minutes}",
        duration_minutes=duration,
        occupied_minutes=duration,
        finish_minutes=world.status.simulation_progress_minutes + duration,
        score=0.0,
    )
    option.action_cert = ActionCertificate(option.id, "wait", option.decision_id, None, None, duration > 0, [reason])
    return option


def finalize(option: CandidateOption, world: World) -> dict:
    if option.action_type == "take_order" and option.cargo is not None and option.action_cert and option.action_cert.safe:
        return {"action": "take_order", "params": {"cargo_id": option.cargo.cargo_id}}
    if option.action_type == "reposition" and reposition_payback_allowed(option, world):
        return {
            "action": "reposition",
            "params": {
                "latitude": float(option.target_lat),
                "longitude": float(option.target_lng),
            },
        }
    remaining = remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)
    requested = option.duration_minutes if option.action_type == "wait" else config.WAIT_MINUTES_SHORT
    if remaining <= 0:
        duration = 0
    elif remaining < config.MIN_WAIT_MINUTES:
        duration = remaining
    else:
        duration = max(config.MIN_WAIT_MINUTES, min(int(requested), remaining))
    return {"action": "wait", "params": {"duration_minutes": duration}}
