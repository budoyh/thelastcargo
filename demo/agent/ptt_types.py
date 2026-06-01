"""Preference Type Transducer rule schema and deterministic fallback mapping."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field as dataclass_field
from typing import Any

from .schemas import CompiledPreferenceRule, World

PTT_TYPES = (
    "daily_continuous_rest",
    "scheduled_quiet_window",
    "full_inactive_day_quota",
    "no_order_day_quota",
    "forbidden_cargo_attribute",
    "required_cargo_attribute_distinct_days",
    "pickup_deadhead_limit",
    "haul_distance_limit",
    "cumulative_deadhead_budget",
    "daily_order_count_limit",
    "first_order_start_deadline",
    "location_visit_or_dwell",
    "ordered_multi_stop_task",
    "stay_target_window",
    "unknown_soft",
    "region_avoid_or_require",
    "runtime_entity_task",
    "daily_work_pattern",
)

COUNTING_UNITS = {
    "per_take",
    "per_day",
    "once_if_failed",
    "capped_count",
    "month_end",
    "continuous_window",
    "distinct_days",
    "sequence",
    "unknown",
}

TRIGGER_ACTIONS = {"take", "wait", "reposition", "query", "active", "arrival", "dwell", "month_end", "unknown"}

NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
CLOCK_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")


@dataclass(frozen=True)
class PTTRule:
    rule_id: str
    type: str
    scope: str = "unknown"
    field: str = "unknown"
    operator: str = "unknown"
    value_hash: str | None = None
    duration_minutes: int | None = None
    time_window: tuple[int, int] | None = None
    deadline: int | None = None
    count: int | None = None
    distance_km: float | None = None
    penalty_amount: float | None = None
    penalty_cap: float | None = None
    penalty_source: str = "unknown"
    counting_unit: str = "unknown"
    trigger_action: str = "unknown"
    repair_actions: tuple[str, ...] = ()
    confidence: float = 0.35
    uncertainty: tuple[str, ...] = ()
    source_rule_id: str = ""
    ptt_compile_source: str = "deterministic"
    slots: dict[str, Any] = dataclass_field(default_factory=dict)

    def penalty_scale(self) -> float:
        if self.penalty_amount is not None:
            return max(0.0, float(self.penalty_amount))
        return _fallback_penalty_scale(self.type)


def short_hash(value: Any, length: int = 16) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def _numbers(text: str) -> list[float]:
    out = []
    for token in NUMBER_RE.findall(text):
        try:
            out.append(float(token))
        except ValueError:
            continue
    return out


def _minutes_from_clock(token: str) -> int | None:
    parts = token.split(":")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except (IndexError, ValueError):
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour * 60 + minute


def _time_window(text: str) -> tuple[int, int] | None:
    clocks = CLOCK_RE.findall(text)
    if len(clocks) < 2:
        return None
    start = _minutes_from_clock(clocks[0])
    end = _minutes_from_clock(clocks[1])
    if start is None or end is None:
        return None
    return start, end


def _penalty_payload(rule: CompiledPreferenceRule | None, pref: Any) -> tuple[float | None, float | None, str, tuple[str, ...]]:
    amount = None
    cap = None
    if isinstance(pref, dict):
        if pref.get("penalty_amount") is not None:
            try:
                amount = float(pref.get("penalty_amount"))
            except (TypeError, ValueError):
                amount = None
        if pref.get("penalty_cap") is not None:
            try:
                cap = float(pref.get("penalty_cap"))
            except (TypeError, ValueError):
                cap = None
    if amount is None and rule is not None and rule.penalty_amount:
        amount = float(rule.penalty_amount)
    if cap is None and rule is not None and rule.penalty_cap is not None:
        cap = float(rule.penalty_cap)
    uncertainty: list[str] = []
    source = "runtime_preference" if amount is not None else "unknown"
    if amount is None:
        uncertainty.append("missing_penalty_amount")
    return amount, cap, source, tuple(uncertainty)


def _fallback_penalty_scale(rule_type: str) -> float:
    if rule_type in {"forbidden_cargo_attribute", "pickup_deadhead_limit", "haul_distance_limit"}:
        return 900.0
    if rule_type in {"daily_continuous_rest", "scheduled_quiet_window"}:
        return 1600.0
    if rule_type in {"full_inactive_day_quota", "no_order_day_quota"}:
        return 3500.0
    if rule_type in {"required_cargo_attribute_distinct_days", "location_visit_or_dwell", "stay_target_window"}:
        return 4500.0
    if rule_type in {"ordered_multi_stop_task", "runtime_entity_task"}:
        return 5000.0
    return 1200.0


def _bytecode_for_rule_type(rule_type: str) -> list[dict[str, Any]]:
    mapping = {
        "daily_continuous_rest": ["DAILY_WINDOW", "WAIT_COVERAGE", "COUNT_PER_ACTION"],
        "scheduled_quiet_window": ["DAILY_WINDOW", "INTERVAL_OVERLAP", "WAIT_COVERAGE"],
        "full_inactive_day_quota": ["FULL_DAY_INACTIVE", "ACTIVE_COVERAGE", "COUNT_CAPPED"],
        "no_order_day_quota": ["NO_ORDER_DAY", "COUNT_CAPPED"],
        "forbidden_cargo_attribute": ["FILTER_ACTION", "TAKE_FIELD_MATCH", "COUNT_PER_ACTION"],
        "required_cargo_attribute_distinct_days": ["TAKE_FIELD_MATCH", "COUNT_DISTINCT_DAY", "ASK_LINKER"],
        "pickup_deadhead_limit": ["FILTER_ACTION", "PICKUP_DEADHEAD_LE", "COUNT_PER_ACTION"],
        "haul_distance_limit": ["FILTER_ACTION", "HAUL_DISTANCE_LE", "COUNT_PER_ACTION"],
        "cumulative_deadhead_budget": ["CUMULATIVE_DISTANCE_BUDGET", "COUNT_CAPPED"],
        "daily_order_count_limit": ["ORDER_COUNT_LE", "COUNT_PER_ACTION"],
        "first_order_start_deadline": ["ARRIVE_BEFORE", "ORDER_COUNT_GE"],
        "location_visit_or_dwell": ["POSITION_NEAR", "DWELL_MINUTES", "REPAIR"],
        "ordered_multi_stop_task": ["ORDERED_SEQUENCE", "ARRIVE_BEFORE", "DWELL_MINUTES"],
        "stay_target_window": ["POSITION_NEAR", "DAILY_WINDOW", "DWELL_MINUTES"],
        "region_avoid_or_require": ["START_END_REGION_MATCH", "ASK_LINKER", "AUDIT_TOP_CANDIDATE"],
        "runtime_entity_task": ["ASK_LINKER", "TAKE_TOWARDS_TARGET", "REPAIR"],
        "daily_work_pattern": ["ACTIVE_COVERAGE", "DAILY_WINDOW"],
        "unknown_soft": ["UNKNOWN_SOFT", "AUDIT_TOP_CANDIDATE"],
    }
    return [{"op": op, "args": {}} for op in mapping.get(rule_type, ["UNKNOWN_SOFT"])]


def _classify_from_rule(rule: CompiledPreferenceRule, pref_text: str) -> tuple[str, str, str, str, tuple[str, ...]]:
    lower = pref_text.lower()
    if rule.predicate_type == "continuous_wait":
        if _time_window(pref_text):
            return "scheduled_quiet_window", "action_interval", "not_overlaps", "continuous_window", ("wait",)
        return "daily_continuous_rest", "wait_interval", "continuous_minutes", "per_day", ("wait",)
    if rule.predicate_type == "off_day_quota":
        return "full_inactive_day_quota", "day_action_count", "count_ge", "month_end", ("wait",)
    if rule.predicate_type == "count_distinct_days":
        return "required_cargo_attribute_distinct_days", "cargo_name", "distinct_days_count", "month_end", ("take",)
    if rule.predicate_type == "cargo_field_match":
        required_words = ("required", "need", "must include", "distinct", "count")
        if any(word in lower for word in required_words):
            return "required_cargo_attribute_distinct_days", "cargo_name", "distinct_days_count", "month_end", ("take",)
        return "forbidden_cargo_attribute", "cargo_name", "contains", "per_take", ("avoid_take",)
    if rule.predicate_type == "pickup_deadhead_limit":
        return "pickup_deadhead_limit", "pickup_deadhead_km", "<=", "per_take", ("avoid_take",)
    if rule.predicate_type == "location_visit":
        if _time_window(pref_text):
            return "stay_target_window", "position", "near", "once_if_failed", ("reposition", "wait", "take")
        return "location_visit_or_dwell", "position", "near", "once_if_failed", ("reposition", "wait", "take")
    if rule.predicate_type == "route_sequence":
        return "ordered_multi_stop_task", "position", "ordered_visit", "once_if_failed", ("reposition", "take", "wait")
    nums = _numbers(pref_text)
    if "haul" in lower:
        return "haul_distance_limit", "haul_km", "<=", "per_take", ("avoid_take",)
    if "cumulative" in lower or "budget" in lower:
        return "cumulative_deadhead_budget", "cumulative_deadhead_km", "<=", "month_end", ("avoid_take",)
    if "order count" in lower or "orders per day" in lower:
        return "daily_order_count_limit", "order_count", "count_le", "per_day", ("wait",)
    if "first" in lower and ("deadline" in lower or "start" in lower):
        return "first_order_start_deadline", "action_interval", "<=", "per_day", ("take",)
    if "region" in lower:
        return "region_avoid_or_require", "other_visible_field", "contains", "per_take", ("avoid_take", "take")
    if "entity" in lower:
        return "runtime_entity_task", "other_visible_field", "contains", "once_if_failed", ("take", "wait")
    if "pattern" in lower:
        return "daily_work_pattern", "action_interval", "unknown", "per_day", ("wait", "take")
    if nums and max(nums) > 20:
        return "pickup_deadhead_limit", "pickup_deadhead_km", "<=", "per_take", ("avoid_take",)
    return "unknown_soft", "unknown", "unknown", "unknown", ("unknown",)


def from_compiled_rules(world: World, compile_source: str = "deterministic") -> tuple[PTTRule, ...]:
    prefs = list(world.status.preferences)
    rules = list(world.rules.rules)
    out: list[PTTRule] = []
    for idx, rule in enumerate(rules):
        pref = prefs[idx] if idx < len(prefs) else {}
        pref_text = str(pref.get("content", "") if isinstance(pref, dict) else pref)
        rule_type, field, operator, counting_unit, repairs = _classify_from_rule(rule, pref_text)
        amount, cap, source, uncertainty = _penalty_payload(rule, pref)
        nums = _numbers(pref_text)
        distance = None
        if rule_type in {"pickup_deadhead_limit", "haul_distance_limit", "cumulative_deadhead_budget"} and nums:
            distance = min(v for v in nums if v > 0)
        count = None
        if rule_type in {"full_inactive_day_quota", "no_order_day_quota", "required_cargo_attribute_distinct_days", "daily_order_count_limit"}:
            plausible = [int(v) for v in nums if 0 < v <= 31 and float(v).is_integer()]
            count = min(plausible) if plausible else None
        duration = None
        if rule_type in {"daily_continuous_rest", "scheduled_quiet_window", "stay_target_window"}:
            plausible = [int(v * 60 if v <= 24 else v) for v in nums if v > 0]
            duration = max((v for v in plausible if v <= 24 * 60), default=None)
        tw = _time_window(pref_text)
        out.append(
            PTTRule(
                rule_id=short_hash({"pref_hash": world.pref_hash, "idx": idx, "type": rule_type}, 12),
                type=rule_type if rule_type in PTT_TYPES else "unknown_soft",
                scope=rule.time_scope if rule.time_scope != "unknown" else rule.scope,
                field=field,
                operator=operator,
                value_hash=short_hash(rule.values or rule.evidence_hash or idx, 12),
                duration_minutes=duration,
                time_window=tw,
                deadline=None,
                count=count,
                distance_km=distance,
                penalty_amount=amount,
                penalty_cap=cap,
                penalty_source=source,
                counting_unit=counting_unit if counting_unit in COUNTING_UNITS else "unknown",
                trigger_action="take" if rule_type in {"forbidden_cargo_attribute", "pickup_deadhead_limit", "haul_distance_limit"} else "wait",
                repair_actions=repairs,
                confidence=max(0.05, min(0.95, rule.confidence)),
                uncertainty=uncertainty,
                source_rule_id=rule.rule_id,
                ptt_compile_source=compile_source,
                slots={
                    "predicate_type": rule.predicate_type,
                    "fields": list(rule.fields),
                    "operator": rule.operator,
                    "unresolved_reason": rule.unresolved_reason,
                    "bytecode_program": _bytecode_for_rule_type(rule_type),
                    "bytecode_ops": [item["op"] for item in _bytecode_for_rule_type(rule_type)],
                },
            )
        )
    if not out and world.status.preferences:
        for idx, pref in enumerate(world.status.preferences):
            amount, cap, source, uncertainty = _penalty_payload(None, pref)
            out.append(
                PTTRule(
                    rule_id=short_hash({"pref_hash": world.pref_hash, "idx": idx, "type": "unknown_soft"}, 12),
                    type="unknown_soft",
                    penalty_amount=amount,
                    penalty_cap=cap,
                    penalty_source=source,
                    uncertainty=uncertainty,
                    confidence=0.25,
                    source_rule_id=f"pref_{idx}",
                    ptt_compile_source=compile_source,
                    slots={
                        "bytecode_program": _bytecode_for_rule_type("unknown_soft"),
                        "bytecode_ops": [item["op"] for item in _bytecode_for_rule_type("unknown_soft")],
                    },
                )
            )
    return tuple(out)


def coverage_seed_rows() -> list[dict[str, Any]]:
    return [
        {
            "controller_type": rule_type,
            "compile_count": 0,
            "instantiated_count": 0,
            "scored_candidate_count": 0,
            "test_pass": False,
            "official_probe_status": "unverified_soft",
        }
        for rule_type in PTT_TYPES
    ]
