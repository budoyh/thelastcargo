"""Score rescue strategies that prioritize safe positive net orders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import config, preference_monitor, visible_rollout
from .schemas import CandidateOption, World
from .wait_lock import WaitLockState, lowered_thresholds, wait_score_penalty


@dataclass(frozen=True)
class RescueStats:
    positive_count: int
    safe_positive_count: int
    best_order_net: float
    best_order_per_hour: float
    hard_block_reason_counts: dict[str, int]


def profit_per_hour(option: CandidateOption) -> float:
    return option.direct_money / max(1.0, option.occupied_minutes) * 60.0


def _load_slack(option: CandidateOption, world: World) -> float:
    cargo = option.cargo
    if cargo is None or cargo.load_end_minutes is None:
        return 6 * 60.0
    return max(0.0, float(cargo.load_end_minutes - world.status.simulation_progress_minutes))


def _rest_window_overlap_minutes(start: int, finish: int) -> int:
    if finish <= start:
        return 0
    total = 0
    rest_end = config.RESCUE_DAILY_REST_UNTIL_MINUTE
    day = start // 1440
    last_day = finish // 1440
    for current_day in range(day, last_day + 1):
        a = current_day * 1440
        b = a + rest_end
        total += max(0, min(finish, b) - max(start, a))
    return total


def _scheduled_full_rest_overlap(start: int, finish: int) -> bool:
    if config.RESCUE_FULL_REST_PERIOD_DAYS <= 0:
        return False
    first_day = start // 1440
    last_day = finish // 1440
    for current_day in range(first_day, last_day + 1):
        if (current_day + 1) % config.RESCUE_FULL_REST_PERIOD_DAYS != 0:
            continue
        a = current_day * 1440
        b = a + 1440
        if max(start, a) < min(finish, b):
            return True
    return False


def hard_block_reason(option: CandidateOption, min_direct: float, min_per_hour: float) -> str | None:
    if option.action_cert and not option.action_cert.safe:
        return ",".join(option.action_cert.reasons) or "action_cert_unsafe"
    if option.action_type != "take_order":
        return None
    if option.pref_cert and option.pref_cert.high_confidence_irreversible_violation:
        return "high_confidence_preference_violation"
    if option.direct_money < config.RESCUE_NEGATIVE_HARD_BLOCK:
        return "severe_negative_net"
    if option.direct_money < min_direct:
        return "below_direct_net_threshold"
    if profit_per_hour(option) < min_per_hour:
        return "below_profit_per_hour_threshold"
    return None


def rescue_operating_block(option: CandidateOption, world: World) -> str | None:
    if option.action_type != "take_order" or not config.ENABLE_RESCUE_REST_GUARD or not world.status.preferences:
        return None
    start = world.status.simulation_progress_minutes
    if _rest_window_overlap_minutes(start, option.finish_minutes) > 0:
        return "rest_window_overlap"
    if _scheduled_full_rest_overlap(start, option.finish_minutes):
        return "scheduled_full_rest_overlap"
    return None


def score_options(options: list[CandidateOption], world: World, state: WaitLockState) -> tuple[list[CandidateOption], RescueStats]:
    min_direct, min_per_hour = lowered_thresholds(state)
    hard_counts: dict[str, int] = {}
    positive_count = 0
    safe_positive_count = 0
    best_net = 0.0
    best_per_hour = 0.0
    take_options = [o for o in options if o.action_type == "take_order"]
    for option in options:
        if option.action_type in {"take_order", "reposition"}:
            option.pref_cert = preference_monitor.certify(option, world)
        if option.action_type == "take_order":
            per_hour = profit_per_hour(option)
            best_net = max(best_net, option.direct_money)
            best_per_hour = max(best_per_hour, per_hour)
            if option.direct_money > 0:
                positive_count += 1
            reason = hard_block_reason(option, min_direct, min_per_hour)
            operating_reason = rescue_operating_block(option, world)
            if operating_reason:
                reason = operating_reason
            if reason:
                hard_counts[reason] = hard_counts.get(reason, 0) + 1
            else:
                safe_positive_count += 1
            slack_bonus = min(80.0, _load_slack(option, world) / 30.0)
            soft_pref = 0.0
            if config.ENABLE_RESCUE_PREFERENCE_SOFT and option.pref_cert:
                soft_pref = min(config.RESCUE_SOFT_RISK_CAP, option.pref_cert.violation_debt + option.pref_cert.unknown_risk * 4.0)
            twohop = 0.0
            if config.ENABLE_RESCUE_TWOHOP_LITE:
                rollout = visible_rollout.evaluate(option, world, [o.cargo for o in take_options if o.cargo is not None])
                option.rollout = rollout
                twohop = min(120.0, max(0.0, rollout.value) * 0.25)
            time_penalty = 0.0
            if config.ENABLE_RESCUE_TIME_SHADOW_LITE:
                time_penalty = min(config.RESCUE_TIME_COST_CAP, max(0, option.occupied_minutes - 480) * 0.08)
            rest_penalty = 0.0
            if config.ENABLE_RESCUE_REST_GUARD and world.status.preferences:
                overlap = _rest_window_overlap_minutes(world.status.simulation_progress_minutes, option.finish_minutes)
                rest_penalty = min(25_000.0, overlap * 80.0)
            duration_penalty = max(0.0, option.occupied_minutes - 720) * 8.0
            deadhead_penalty = max(0.0, option.deadhead_km - 55.0) * 15.0
            score = (
                option.direct_money
                + per_hour * 4.0
                + slack_bonus
                + twohop
                - soft_pref
                - time_penalty
                - rest_penalty
                - duration_penalty
                - deadhead_penalty
            )
            if reason in {"below_direct_net_threshold", "below_profit_per_hour_threshold"}:
                score -= 120.0
            elif reason:
                score -= 10_000.0
            option.score = score
            option.score_components.update(
                {
                    "direct_net": option.direct_money,
                    "profit_per_hour": per_hour,
                    "load_slack_bonus": slack_bonus,
                    "twohop_lite": twohop,
                    "preference_soft_penalty": -soft_pref,
                    "time_shadow_lite": -time_penalty,
                    "rest_window_penalty": -rest_penalty,
                    "duration_penalty": -duration_penalty,
                    "deadhead_penalty": -deadhead_penalty,
                }
            )
            option.trace["hard_block_reason"] = reason or ""
        elif option.action_type == "wait":
            penalty = wait_score_penalty(state)
            option.score = -penalty
            option.score_components.update({"repeated_wait_penalty": -penalty})
        elif option.action_type == "reposition":
            option.score = -abs(option.direct_money) - 40.0
            option.score_components.update({"micro_reposition_cost": option.score})
    return options, RescueStats(positive_count, safe_positive_count, best_net, best_per_hour, hard_counts)


def choose(options: list[CandidateOption], stats: RescueStats, state: WaitLockState) -> CandidateOption:
    take_options = [o for o in options if o.action_type == "take_order"]
    viable = [o for o in take_options if not o.trace.get("hard_block_reason")]
    if viable:
        return max(viable, key=lambda o: o.score)
    if state.consecutive_wait >= config.RESCUE_FORCE_TAKE_AFTER_WAITS:
        positive = [
            o for o in take_options
            if o.direct_money > 0
            and not (o.action_cert and not o.action_cert.safe)
            and not (o.pref_cert and o.pref_cert.high_confidence_irreversible_violation)
            and o.trace.get("hard_block_reason", "") in {"", "below_direct_net_threshold", "below_profit_per_hour_threshold"}
        ]
        if positive:
            return max(positive, key=lambda o: (o.direct_money, profit_per_hour(o)))
    repos = [o for o in options if o.action_type == "reposition"]
    if repos:
        return max(repos, key=lambda o: o.score)
    waits = [o for o in options if o.action_type == "wait"]
    return max(waits, key=lambda o: o.score) if waits else options[0]


def wait_forensic(chosen: CandidateOption, options: list[CandidateOption], stats: RescueStats, state: WaitLockState) -> dict[str, Any]:
    takes = sorted((o for o in options if o.action_type == "take_order"), key=lambda o: o.score, reverse=True)
    top_rejected = []
    for option in takes[:5]:
        top_rejected.append(
            {
                "candidate_id": option.id,
                "cargo_id": option.cargo.cargo_id if option.cargo else None,
                "direct_net": round(option.direct_money, 2),
                "profit_per_hour": round(profit_per_hour(option), 2),
                "hard_filter_reason": option.trace.get("hard_block_reason", ""),
                "score": round(option.score, 2),
                "score_components": {k: round(float(v), 2) for k, v in option.score_components.items()},
            }
        )
    if stats.safe_positive_count > 0:
        reason = "wait_chosen_despite_safe_positive"
    elif stats.positive_count > 0:
        reason = "positive_orders_failed_threshold_or_soft_risk"
    else:
        reason = "no_safe_positive_net_cargo"
    return {
        "wait_reason": reason,
        "best_available_order": top_rejected[0] if top_rejected else None,
        "best_order_net": round(stats.best_order_net, 2),
        "best_order_per_hour": round(stats.best_order_per_hour, 2),
        "why_not_take": reason,
        "why_not_reposition": "micro_reposition_unavailable_or_disabled",
        "why_wait_minutes": chosen.duration_minutes,
        "why_wait_won": {
            "chosen_score": round(chosen.score, 2),
            "safe_positive_count": stats.safe_positive_count,
            "positive_count": stats.positive_count,
            "consecutive_wait": state.consecutive_wait,
        },
        "top_5_rejected_take": top_rejected,
        "hard_block_reason_counts": dict(stats.hard_block_reason_counts),
    }
