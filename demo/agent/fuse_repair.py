"""Targeted Fuse repair overlay guarded by B0 shadow decisions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from . import config, macro_commitment, preference_repair, safety
from .geo import haversine_km
from .observed_vocab_linker import ObservedVocabLink
from .ptt_types import PTTRule
from .schemas import CandidateOption, CompiledPreferenceRule, World
from .time_utils import day_index, remaining_minutes


@dataclass(frozen=True)
class FuseSelection:
    chosen: CandidateOption
    options: list[CandidateOption]
    trace: dict[str, Any]
    repair_wait_minutes: int = 0


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _action_signature(option: CandidateOption) -> str:
    cargo_hash = _hash(option.cargo.cargo_id) if option.cargo is not None else ""
    wait = str(int(option.duration_minutes)) if option.action_type == "wait" else ""
    target = ""
    if option.action_type == "reposition" and option.target_lat is not None and option.target_lng is not None:
        target = f"{option.target_lat:.4f},{option.target_lng:.4f}"
    return _hash("|".join([option.action_type, cargo_hash, wait, target, str(option.finish_minutes)]))


def _day_allowed(world: World) -> bool:
    current_day = day_index(world.status.simulation_progress_minutes) + 1
    start = config.FUSE_REPAIR_START_DAY
    end = config.FUSE_REPAIR_END_DAY
    if start <= end:
        return start <= current_day <= end
    return current_day >= start or current_day <= end


def _gross_cap(world: World) -> float:
    cap = float(config.FUSE_LOST_GROSS_CAP)
    curve = config.FUSE_GROSS_FLOOR_CURVE
    day = day_index(world.status.simulation_progress_minutes) + 1
    if curve == "mild" and day >= 20:
        cap *= 0.85
    elif curve == "medium":
        cap *= 0.75 if day < 20 else 0.55
    elif curve == "strong":
        cap *= 0.60 if day < 20 else 0.35
    return max(0.0, cap)


def _target_value(target: preference_repair.PreferenceTarget, *, proximity: float = 1.0) -> float:
    base = float(target.value) * config.FUSE_WAIT_REPAIR_STRENGTH
    base *= config.FUSE_REPAIR_VALUE_SCALE
    base *= config.FUSE_VERIFIED_PENALTY_SCALE
    base *= max(0.0, min(1.0, proximity))
    base *= 1.0 - 0.35 * config.FUSE_ALREADY_FAILED_DISCOUNT
    base *= 1.0 - 0.25 * config.FUSE_CAP_DISCOUNT
    return max(0.0, base)


def _rule_family(rule: CompiledPreferenceRule) -> str:
    repair = " ".join([*rule.repair_action_kinds, *rule.repair])
    haystack = " ".join(
        [
            rule.observable,
            rule.predicate_type,
            rule.metric,
            rule.counting,
            rule.polarity,
            rule.scope,
            rule.kind,
            rule.repairability,
            repair,
            rule.evidence,
            str(rule.condition),
            str(rule.slots),
            str(rule.values),
            str(rule.uncertainty),
        ]
    ).lower()
    if (
        "off_day" in haystack
        or "off day" in haystack
        or "full_day_inactive" in haystack
        or "full inactive" in haystack
        or "inactive day" in haystack
        or "rest day" in haystack
        or "全天休息" in haystack
        or "整天休息" in haystack
        or "整日休息" in haystack
        or "休息日" in haystack
    ):
        return "full_inactive_day_quota"
    if "no_order" in haystack or "no order" in haystack or "不接单" in haystack or "不接货" in haystack:
        return "no_order_day_quota"
    if (
        "distinct" in haystack
        or rule.predicate_type == "count_distinct_days"
        or "不同天" in haystack
        or "天数" in haystack
        or "至少" in haystack
        or "必须" in haystack
        or "需要" in haystack
    ):
        return "required_cargo_attribute_distinct_days"
    if rule.observable == "cargo_attribute" and rule.polarity in {"require", "required", "prefer"}:
        return "required_cargo_attribute_distinct_days"
    if rule.observable == "time_window" or "quiet" in haystack or "安静" in haystack or rule.scope in {"window", "date_window"}:
        return "scheduled_quiet_window"
    if (
        rule.observable in {"duration", "work_pattern"}
        or "continuous" in haystack
        or "连续休息" in haystack
        or "每天休息" in haystack
        or rule.predicate_type == "continuous_wait"
    ):
        return "daily_continuous_rest"
    if rule.observable == "location":
        return "location_visit_or_dwell"
    if rule.observable == "sequence":
        return "ordered_multi_stop_task"
    return "unknown_soft"


def _rule_penalty(rule: CompiledPreferenceRule, family: str) -> float:
    amount = rule.penalty_amount
    if amount is None:
        raw = rule.reward_or_penalty.get("amount") if isinstance(rule.reward_or_penalty, dict) else None
        try:
            amount = float(raw)
        except (TypeError, ValueError):
            amount = None
    fallback = {
        "full_inactive_day_quota": 10_000.0,
        "no_order_day_quota": 6_000.0,
        "required_cargo_attribute_distinct_days": 6_000.0,
        "daily_continuous_rest": 1_800.0,
        "scheduled_quiet_window": 1_800.0,
        "daily_work_pattern": 2_400.0,
        "location_visit_or_dwell": 4_500.0,
        "ordered_multi_stop_task": 5_000.0,
    }.get(family, 1_200.0)
    return max(0.0, min(12_000.0, float(amount) if amount is not None else fallback))


def _rule_value(rule: CompiledPreferenceRule, family: str, *, confidence: float | None = None, coverage: float = 1.0) -> float:
    conf = rule.confidence if confidence is None else confidence
    base = _rule_penalty(rule, family)
    base *= config.FUSE_WAIT_REPAIR_STRENGTH
    base *= config.FUSE_REPAIR_VALUE_SCALE
    base *= config.FUSE_VERIFIED_PENALTY_SCALE
    base *= max(0.0, min(1.0, conf))
    base *= max(0.0, min(1.0, coverage))
    base *= 1.0 - 0.35 * config.FUSE_ALREADY_FAILED_DISCOUNT
    base *= 1.0 - 0.25 * config.FUSE_CAP_DISCOUNT
    return max(0.0, base)


def _ptt_rule_value(rule: PTTRule, *, coverage: float = 1.0) -> float:
    family_floor = {
        "full_inactive_day_quota": 10_000.0,
        "no_order_day_quota": 6_000.0,
        "required_cargo_attribute_distinct_days": 6_000.0,
        "runtime_entity_task": 5_000.0,
        "daily_continuous_rest": 1_800.0,
        "scheduled_quiet_window": 1_800.0,
        "daily_work_pattern": 2_400.0,
    }.get(rule.type, 0.0)
    base = max(rule.penalty_scale(), family_floor)
    base *= config.FUSE_WAIT_REPAIR_STRENGTH
    base *= config.FUSE_REPAIR_VALUE_SCALE
    base *= config.FUSE_VERIFIED_PENALTY_SCALE
    confidence_floor = 0.45 if rule.type in {"required_cargo_attribute_distinct_days", "runtime_entity_task"} else 0.35
    base *= max(0.0, min(1.0, max(rule.confidence, confidence_floor)))
    base *= max(0.0, min(1.0, coverage))
    base *= 1.0 - 0.35 * config.FUSE_ALREADY_FAILED_DISCOUNT
    base *= 1.0 - 0.25 * config.FUSE_CAP_DISCOUNT
    return max(0.0, base)


def _daily_budget_remaining(world: World, repair_wait_by_day: dict[int, int]) -> int:
    if config.FUSE_MAX_REPAIR_WAIT_PER_DAY <= 0:
        return 0
    day = day_index(world.status.simulation_progress_minutes)
    return max(0, int(config.FUSE_MAX_REPAIR_WAIT_PER_DAY) - int(repair_wait_by_day.get(day, 0)))


def _trace_repair_candidate(option: CandidateOption, *, kind: str, rule_id: str, expected: float, lost: float, confidence: float) -> None:
    option.trace.update(
        {
            "fuse_repair_candidate": True,
            "repair_kind": kind,
            "rule_hash": _hash(rule_id),
            "expected_avoided_penalty": round(expected, 2),
            "lost_gross": round(lost, 2),
            "confidence": round(max(0.0, min(1.0, confidence)), 4),
        }
    )
    option.score_components["fuse_expected_avoided_penalty"] = round(expected, 2)
    option.score_components["fuse_lost_gross"] = -round(lost, 2)
    option.score_components["fuse_repair_net_estimate"] = round(expected - lost, 2)


def _build_wait_repairs(world: World, decision_id: str, repair_wait_by_day: dict[int, int]) -> list[CandidateOption]:
    if not _day_allowed(world):
        return []
    budget = _daily_budget_remaining(world, repair_wait_by_day)
    if budget < config.MIN_WAIT_MINUTES:
        return []
    remaining = remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)
    if remaining < config.MIN_WAIT_MINUTES:
        return []
    out: list[CandidateOption] = []
    for target in preference_repair.targets(world):
        if "wait_at_target" not in target.repair_actions and target.urgency < 0.75:
            continue
        distance = haversine_km(world.status.current_lat, world.status.current_lng, target.lat, target.lng)
        if distance > 5.0:
            continue
        duration = min(180, budget, remaining)
        if duration < config.MIN_WAIT_MINUTES:
            continue
        proximity = max(0.2, 1.0 - distance / 5.0)
        expected = _target_value(target, proximity=proximity)
        lost = max(0.0, world.time_market.productive_time_shadow_price * duration)
        if expected <= 0:
            continue
        option = CandidateOption(
            id=f"fuse_repair_wait:{_hash(target.rule_id)}:{int(duration)}",
            action_type="wait",
            decision_id=decision_id,
            duration_minutes=int(duration),
            occupied_minutes=int(duration),
            finish_minutes=world.status.simulation_progress_minutes + int(duration),
            direct_money=0.0,
            score=expected - lost * config.FUSE_REPAIR_ROI_THRESHOLD,
        )
        _trace_repair_candidate(option, kind="target_wait", rule_id=target.rule_id, expected=expected, lost=lost, confidence=target.urgency)
        macro_commitment.mark_macro_candidate(
            option,
            macro_type="fuse_target_wait",
            source_automaton_ids=(target.rule_id,),
            avoided_penalty=expected,
            repair_value=expected,
            lost_gross=lost,
            deadline_minutes=option.finish_minutes,
            feasibility="current_position_target_wait",
            confidence=target.urgency,
            required_duration=int(duration),
            permits_query=False,
        )
        option.action_cert = safety._certificate_for(option, set())
        out.append(option)
    return out[:2]


def _build_day_window_repairs(world: World, decision_id: str, repair_wait_by_day: dict[int, int]) -> list[CandidateOption]:
    if not _day_allowed(world):
        return []
    budget = _daily_budget_remaining(world, repair_wait_by_day)
    if budget < config.MIN_WAIT_MINUTES:
        return []
    now = world.status.simulation_progress_minutes
    minute = now % 1440
    remaining = remaining_minutes(now, world.horizon.horizon_minutes)
    if remaining < config.MIN_WAIT_MINUTES:
        return []
    out: list[CandidateOption] = []
    for rule in world.rules.rules:
        family = _rule_family(rule)
        if family in {"full_inactive_day_quota", "no_order_day_quota"}:
            if minute > 120:
                continue
            duration = min(max(config.MIN_WAIT_MINUTES, 1440 - minute), budget, remaining)
            if duration < 240:
                continue
            coverage = min(1.0, duration / max(1.0, 1440.0 - minute))
            kind = "full_day_wait"
            confidence = max(0.45, rule.confidence)
        elif family in {"daily_continuous_rest", "scheduled_quiet_window", "daily_work_pattern"}:
            if minute < config.RESCUE_DAILY_REST_UNTIL_MINUTE:
                target_duration = config.RESCUE_DAILY_REST_UNTIL_MINUTE - minute
            else:
                target_duration = 240
            duration = min(max(config.MIN_WAIT_MINUTES, target_duration), budget, remaining)
            if duration < config.MIN_WAIT_MINUTES:
                continue
            coverage = min(1.0, duration / 480.0)
            kind = "window_wait"
            confidence = max(0.40, rule.confidence)
        else:
            continue
        expected = _rule_value(rule, family, confidence=confidence, coverage=coverage)
        lost = max(0.0, world.time_market.productive_time_shadow_price * duration)
        if expected <= 0:
            continue
        option = CandidateOption(
            id=f"fuse_repair_{kind}:{_hash(rule.rule_id)}:{int(duration)}",
            action_type="wait",
            decision_id=decision_id,
            duration_minutes=int(duration),
            occupied_minutes=int(duration),
            finish_minutes=now + int(duration),
            direct_money=0.0,
            score=expected - lost * config.FUSE_REPAIR_ROI_THRESHOLD,
        )
        _trace_repair_candidate(option, kind=kind, rule_id=rule.rule_id, expected=expected, lost=lost, confidence=confidence)
        macro_commitment.mark_macro_candidate(
            option,
            macro_type=f"fuse_{kind}",
            source_automaton_ids=(rule.rule_id,),
            avoided_penalty=expected,
            repair_value=expected,
            lost_gross=lost,
            deadline_minutes=option.finish_minutes,
            feasibility="runtime_rule_day_window_wait",
            confidence=confidence,
            required_duration=int(duration),
            permits_query=False,
        )
        option.action_cert = safety._certificate_for(option, set())
        out.append(option)
    return sorted(out, key=lambda item: _expected_avoided_penalty(item), reverse=True)[:2]


def _build_ptt_day_window_repairs(
    world: World,
    decision_id: str,
    repair_wait_by_day: dict[int, int],
    ptt_rules: tuple[PTTRule, ...],
) -> list[CandidateOption]:
    if not _day_allowed(world) or not ptt_rules:
        return []
    budget = _daily_budget_remaining(world, repair_wait_by_day)
    if budget < config.MIN_WAIT_MINUTES:
        return []
    now = world.status.simulation_progress_minutes
    minute = now % 1440
    remaining = remaining_minutes(now, world.horizon.horizon_minutes)
    if remaining < config.MIN_WAIT_MINUTES:
        return []
    out: list[CandidateOption] = []
    for rule in ptt_rules:
        if rule.type in {"full_inactive_day_quota", "no_order_day_quota"}:
            if minute > 120:
                continue
            duration = min(max(config.MIN_WAIT_MINUTES, 1440 - minute), budget, remaining)
            if duration < 240:
                continue
            coverage = min(1.0, duration / max(1.0, 1440.0 - minute))
            kind = "ptt_full_day_wait"
        elif rule.type in {"daily_continuous_rest", "scheduled_quiet_window", "daily_work_pattern"}:
            if minute < config.RESCUE_DAILY_REST_UNTIL_MINUTE:
                target_duration = config.RESCUE_DAILY_REST_UNTIL_MINUTE - minute
            else:
                target_duration = min(240, budget)
            duration = min(max(config.MIN_WAIT_MINUTES, target_duration), budget, remaining)
            coverage = min(1.0, duration / 480.0)
            kind = "ptt_window_wait"
        else:
            continue
        expected = _ptt_rule_value(rule, coverage=coverage)
        lost = max(0.0, world.time_market.productive_time_shadow_price * duration)
        if expected <= 0:
            continue
        option = CandidateOption(
            id=f"fuse_repair_{kind}:{_hash(rule.rule_id)}:{int(duration)}",
            action_type="wait",
            decision_id=decision_id,
            duration_minutes=int(duration),
            occupied_minutes=int(duration),
            finish_minutes=now + int(duration),
            direct_money=0.0,
            score=expected - lost * config.FUSE_REPAIR_ROI_THRESHOLD,
        )
        _trace_repair_candidate(option, kind=kind, rule_id=rule.rule_id, expected=expected, lost=lost, confidence=rule.confidence)
        macro_commitment.mark_macro_candidate(
            option,
            macro_type=f"fuse_{kind}",
            source_automaton_ids=(rule.rule_id,),
            avoided_penalty=expected,
            repair_value=expected,
            lost_gross=lost,
            deadline_minutes=option.finish_minutes,
            feasibility="runtime_ptt_day_window_wait",
            confidence=rule.confidence,
            required_duration=int(duration),
            permits_query=False,
        )
        option.action_cert = safety._certificate_for(option, set())
        out.append(option)
    return sorted(out, key=lambda item: _expected_avoided_penalty(item), reverse=True)[:2]


def _build_generic_full_day_repair(world: World, decision_id: str, repair_wait_by_day: dict[int, int]) -> list[CandidateOption]:
    if not _day_allowed(world) or not world.status.preferences:
        return []
    budget = _daily_budget_remaining(world, repair_wait_by_day)
    if budget < 720:
        return []
    used_full_days = sum(1 for minutes in repair_wait_by_day.values() if minutes >= 720)
    max_full_days = 2 if config.FUSE_MAX_REPAIR_WAIT_PER_DAY >= 1440 else 1
    if used_full_days >= max_full_days:
        return []
    now = world.status.simulation_progress_minutes
    minute = now % 1440
    if minute > 120:
        return []
    remaining = remaining_minutes(now, world.horizon.horizon_minutes)
    duration = min(1440 - minute, budget, remaining)
    if duration < 720:
        return []
    coverage = min(1.0, duration / max(1.0, 1440.0 - minute))
    expected = 10_000.0
    expected *= config.FUSE_WAIT_REPAIR_STRENGTH
    expected *= config.FUSE_REPAIR_VALUE_SCALE
    expected *= config.FUSE_VERIFIED_PENALTY_SCALE
    expected *= 0.55
    expected *= coverage
    expected *= 1.0 - 0.35 * config.FUSE_ALREADY_FAILED_DISCOUNT
    expected *= 1.0 - 0.25 * config.FUSE_CAP_DISCOUNT
    lost = max(0.0, world.time_market.productive_time_shadow_price * duration)
    if expected <= 0:
        return []
    option = CandidateOption(
        id=f"fuse_repair_generic_full_day:{day_index(now)}:{int(duration)}",
        action_type="wait",
        decision_id=decision_id,
        duration_minutes=int(duration),
        occupied_minutes=int(duration),
        finish_minutes=now + int(duration),
        direct_money=0.0,
        score=expected - lost * config.FUSE_REPAIR_ROI_THRESHOLD,
    )
    _trace_repair_candidate(
        option,
        kind="generic_full_day_wait",
        rule_id="generic_full_inactive_day_quota",
        expected=expected,
        lost=lost,
        confidence=0.55,
    )
    macro_commitment.mark_macro_candidate(
        option,
        macro_type="fuse_generic_full_day_wait",
        source_automaton_ids=("generic_full_inactive_day_quota",),
        avoided_penalty=expected,
        repair_value=expected,
        lost_gross=lost,
        deadline_minutes=option.finish_minutes,
        feasibility="runtime_day_quota_wait_budget",
        confidence=0.55,
        required_duration=int(duration),
        permits_query=False,
    )
    option.action_cert = safety._certificate_for(option, set())
    return [option]


def _apply_vocab_repair_bonus(options: list[CandidateOption], world: World, vocab_links: tuple[ObservedVocabLink, ...]) -> None:
    if not _day_allowed(world) or not vocab_links:
        return
    rules_by_id = {rule.rule_id: rule for rule in world.rules.rules}
    repair_links = [link for link in vocab_links if link.relation == "repair" and link.rule_id in rules_by_id]
    if not repair_links:
        return
    for option in options:
        if option.action_type != "take_order" or option.cargo is None:
            continue
        best_expected = 0.0
        best_link: ObservedVocabLink | None = None
        for link in repair_links:
            if str(getattr(option.cargo, link.field, "") or "") != link.value:
                continue
            rule = rules_by_id[link.rule_id]
            family = _rule_family(rule)
            if family not in {"required_cargo_attribute_distinct_days", "runtime_entity_task", "location_visit_or_dwell", "unknown_soft"}:
                continue
            expected = _rule_value(rule, family, confidence=max(link.confidence, rule.confidence))
            if expected > best_expected:
                best_expected = expected
                best_link = link
        if best_expected <= 0 or best_link is None:
            continue
        option.score += best_expected
        option.score_components["fuse_expected_avoided_penalty"] = round(best_expected, 2)
        option.score_components["fuse_take_repair_bonus"] = round(best_expected, 2)
        option.trace["fuse_repair_candidate"] = True
        option.trace["fuse_repair_kind"] = "linked_current_actionable_take"
        option.trace["fuse_rule_hash"] = _hash(best_link.rule_id)
        option.trace["fuse_vocab_field"] = best_link.field
        option.trace["fuse_vocab_value_hash"] = best_link.value_hash[:12]
        option.trace["expected_avoided_penalty"] = round(best_expected, 2)
        option.trace["lost_gross"] = 0.0


def _apply_take_repair_bonus(options: list[CandidateOption], world: World) -> None:
    if not _day_allowed(world):
        return
    targets = preference_repair.targets(world)
    if not targets:
        return
    for option in options:
        if option.action_type != "take_order" or option.cargo is None:
            continue
        best_expected = 0.0
        best_rule = ""
        for target in targets:
            if "take_towards_target" not in target.repair_actions and "reposition_to_target" not in target.repair_actions:
                continue
            start_distance = haversine_km(option.cargo.start_lat, option.cargo.start_lng, target.lat, target.lng)
            end_distance = haversine_km(option.cargo.end_lat, option.cargo.end_lng, target.lat, target.lng)
            nearest = min(start_distance, end_distance)
            if nearest > 45.0:
                continue
            proximity = max(0.0, 1.0 - nearest / 45.0)
            expected = _target_value(target, proximity=0.25 + 0.75 * proximity)
            if expected > best_expected:
                best_expected = expected
                best_rule = target.rule_id
        if best_expected <= 0:
            continue
        option.score += best_expected
        option.score_components["fuse_expected_avoided_penalty"] = round(best_expected, 2)
        option.score_components["fuse_take_repair_bonus"] = round(best_expected, 2)
        option.trace["fuse_repair_candidate"] = True
        option.trace["fuse_repair_kind"] = "current_actionable_take_repair"
        option.trace["fuse_rule_hash"] = _hash(best_rule)
        option.trace["expected_avoided_penalty"] = round(best_expected, 2)
        option.trace["lost_gross"] = 0.0


def _expected_avoided_penalty(option: CandidateOption) -> float:
    for source in (option.trace, option.score_components):
        for name in ("expected_avoided_penalty", "fuse_expected_avoided_penalty", "preference_repair_value"):
            try:
                value = float(source.get(name, 0.0) or 0.0)
            except (TypeError, ValueError):
                value = 0.0
            if value > 0:
                return value
    return 0.0


def _lost_gross(option: CandidateOption, b0_action: CandidateOption, world: World) -> float:
    trace_lost = 0.0
    try:
        trace_lost = float(option.trace.get("lost_gross", 0.0) or 0.0)
    except (TypeError, ValueError):
        trace_lost = 0.0
    if option.action_type == "take_order":
        return max(trace_lost, max(0.0, float(b0_action.direct_money) - float(option.direct_money)))
    if option.action_type == "wait":
        time_loss = max(0.0, world.time_market.productive_time_shadow_price * max(0, option.duration_minutes))
        return max(trace_lost, time_loss, max(0.0, float(b0_action.direct_money)))
    return max(trace_lost, abs(float(option.direct_money)), max(0.0, float(b0_action.direct_money)))


def _unknown_risk_cost(option: CandidateOption) -> float:
    if option.pref_cert is None:
        return 0.0
    return max(0.0, option.pref_cert.unknown_risk) * config.FUSE_UNKNOWN_SOFT_RISK * 100.0


def _candidate_allowed(option: CandidateOption, b0_action: CandidateOption, world: World, repair_wait_by_day: dict[int, int]) -> tuple[bool, str, float, float]:
    expected = _expected_avoided_penalty(option)
    lost = _lost_gross(option, b0_action, world) + _unknown_risk_cost(option)
    direct_gain = float(option.direct_money) - float(b0_action.direct_money)
    if option.action_cert is not None and not option.action_cert.safe:
        return False, "action_certificate_failed", expected, lost
    if b0_action.action_type == "wait" and str(b0_action.id).startswith("rescue_rest:") and option.action_type != "wait":
        return False, "b0_rest_guard", expected, lost
    if option.action_type == "reposition" and not safety.reposition_payback_allowed(option, world):
        return False, "reposition_payback_guard", expected, lost
    if option.action_type == "wait" and option.duration_minutes > _daily_budget_remaining(world, repair_wait_by_day):
        return False, "daily_repair_budget_exceeded", expected, lost
    if lost > _gross_cap(world):
        return False, "lost_gross_cap_guard", expected, lost
    if b0_action.action_type == "take_order" and b0_action.direct_money >= config.FUSE_MIN_PROFIT_TO_OVERRIDE_REPAIR:
        if expected < lost * config.FUSE_REPAIR_ROI_THRESHOLD:
            return False, "b0_high_profit_guard", expected, lost
    if expected >= lost * config.FUSE_REPAIR_ROI_THRESHOLD and expected > 0:
        return True, "repair_roi_pass", expected, lost
    if direct_gain >= config.FUSE_MIN_PROFIT_TO_OVERRIDE_REPAIR and expected >= 0:
        return True, "direct_gross_gain_pass", expected, lost
    return False, "repair_roi_failed", expected, lost


def apply_overlay(
    *,
    options: list[CandidateOption],
    world: World,
    b0_action: CandidateOption,
    decision_id: str,
    repair_wait_by_day: dict[int, int],
    vocab_links: tuple[ObservedVocabLink, ...] = tuple(),
    ptt_rules: tuple[PTTRule, ...] = tuple(),
) -> FuseSelection:
    if not config.ENABLE_FUSE_TARGETED_REPAIR:
        return FuseSelection(
            chosen=b0_action,
            options=options,
            trace={
                "enabled": False,
                "b0_shadow_approximation": False,
                "b0_action_signature_hash": _action_signature(b0_action),
                "new_action_signature_hash": _action_signature(b0_action),
                "b0_shadow_override": False,
                "b0_shadow_fallback": False,
                "fallback_to_b0_reason": "fuse_disabled",
            },
        )

    overlay_options = list(options)
    _apply_vocab_repair_bonus(overlay_options, world, vocab_links)
    _apply_take_repair_bonus(overlay_options, world)
    wait_repairs = _build_wait_repairs(world, decision_id, repair_wait_by_day)
    wait_repairs.extend(_build_day_window_repairs(world, decision_id, repair_wait_by_day))
    wait_repairs.extend(_build_ptt_day_window_repairs(world, decision_id, repair_wait_by_day, ptt_rules))
    wait_repairs.extend(_build_generic_full_day_repair(world, decision_id, repair_wait_by_day))
    overlay_options.extend(wait_repairs)
    candidates = [
        option
        for option in overlay_options
        if option.trace.get("fuse_repair_candidate") and not (option.action_cert is not None and not option.action_cert.safe)
    ]
    if not candidates:
        trace = _trace_payload(b0_action, b0_action, "no_fuse_repair_candidate", 0.0, 0.0, override=False)
        trace["candidate_count"] = 0
        _augment_trace(trace, world, vocab_links, ptt_rules)
        return FuseSelection(chosen=b0_action, options=overlay_options, trace=trace)

    new_action = max(candidates, key=lambda option: option.score)
    if new_action.id == b0_action.id:
        trace = _trace_payload(b0_action, b0_action, "same_as_b0", 0.0, 0.0, override=False)
        trace["candidate_count"] = len(candidates)
        _augment_trace(trace, world, vocab_links, ptt_rules)
        return FuseSelection(chosen=b0_action, options=overlay_options, trace=trace)
    if new_action.score <= b0_action.score + config.FUSE_OVERRIDE_MARGIN:
        expected = _expected_avoided_penalty(new_action)
        lost = _lost_gross(new_action, b0_action, world)
        if expected - lost < config.FUSE_OVERRIDE_MARGIN:
            trace = _trace_payload(b0_action, new_action, "shadow_score_margin_guard", expected, lost, override=False)
            trace["candidate_count"] = len(candidates)
            _augment_trace(trace, world, vocab_links, ptt_rules)
            return FuseSelection(chosen=b0_action, options=overlay_options, trace=trace)

    allowed, reason, expected, lost = _candidate_allowed(new_action, b0_action, world, repair_wait_by_day)
    if not allowed:
        trace = _trace_payload(b0_action, new_action, reason, expected, lost, override=False)
        trace["candidate_count"] = len(candidates)
        _augment_trace(trace, world, vocab_links, ptt_rules)
        return FuseSelection(chosen=b0_action, options=overlay_options, trace=trace)

    trace = _trace_payload(b0_action, new_action, reason, expected, lost, override=True)
    trace["candidate_count"] = len(candidates)
    trace["repair_kind"] = str(new_action.trace.get("repair_kind") or new_action.trace.get("fuse_repair_kind") or new_action.action_type)
    _augment_trace(trace, world, vocab_links, ptt_rules)
    repair_minutes = int(new_action.duration_minutes) if new_action.action_type == "wait" else 0
    return FuseSelection(chosen=new_action, options=overlay_options, trace=trace, repair_wait_minutes=repair_minutes)


def _trace_payload(
    b0_action: CandidateOption,
    new_action: CandidateOption,
    reason: str,
    expected: float,
    lost: float,
    *,
    override: bool,
) -> dict[str, Any]:
    return {
        "enabled": bool(config.ENABLE_FUSE_TARGETED_REPAIR),
        "b0_shadow_approximation": False,
        "b0_action_signature_hash": _action_signature(b0_action),
        "new_action_signature_hash": _action_signature(new_action),
        "b0_action_type": b0_action.action_type,
        "new_action_type": new_action.action_type,
        "override_reason": reason if override else "",
        "fallback_to_b0_reason": "" if override else reason,
        "estimated_delta_gross": round(-lost, 2),
        "estimated_delta_penalty": round(-expected, 2),
        "estimated_delta_net": round(expected - lost, 2),
        "repair_trigger_count": 1 if override and new_action.trace.get("fuse_repair_candidate") else 0,
        "repair_minutes": int(new_action.duration_minutes) if override and new_action.action_type == "wait" else 0,
        "b0_shadow_override": bool(override),
        "b0_shadow_fallback": not bool(override),
        "params": {
            "wait_repair_strength": config.FUSE_WAIT_REPAIR_STRENGTH,
            "repair_value_scale": config.FUSE_REPAIR_VALUE_SCALE,
            "verified_penalty_scale": config.FUSE_VERIFIED_PENALTY_SCALE,
            "repair_roi_threshold": config.FUSE_REPAIR_ROI_THRESHOLD,
            "lost_gross_cap": config.FUSE_LOST_GROSS_CAP,
            "max_repair_wait_per_day": config.FUSE_MAX_REPAIR_WAIT_PER_DAY,
            "gross_floor_curve": config.FUSE_GROSS_FLOOR_CURVE,
        },
    }


def _augment_trace(trace: dict[str, Any], world: World, vocab_links: tuple[ObservedVocabLink, ...], ptt_rules: tuple[PTTRule, ...]) -> None:
    counts: dict[str, int] = {}
    for rule in world.rules.rules:
        family = _rule_family(rule)
        counts[family] = counts.get(family, 0) + 1
    ptt_counts: dict[str, int] = {}
    for rule in ptt_rules:
        ptt_counts[rule.type] = ptt_counts.get(rule.type, 0) + 1
    trace["rule_count"] = len(world.rules.rules)
    trace["rule_family_counts"] = counts
    trace["vocab_link_count"] = len(vocab_links)
    trace["ptt_rule_family_counts"] = ptt_counts
