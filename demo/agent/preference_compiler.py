"""Compile runtime preference text into conservative DSL rules."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from simkit.ports import SimulationApiPort

from . import config, qwen_preference_compiler
from .llm_budget import LLMBudgetManager
from .schemas import CompiledPreferenceRule, CompiledPreferenceSet, DriverStatus

NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
CLOCK_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
COORD_PAIR_RE = re.compile(r"(?<!\d)(-?\d{1,2}\.\d+)\D{1,18}(-?\d{2,3}\.\d+)(?!\d)")
_COMPILE_BUDGET = LLMBudgetManager()


def hash_preferences(preferences: tuple[Any, ...] | list[Any]) -> str:
    payload = json.dumps(list(preferences), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _preference_content(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("content", "")).strip()
    return str(item).strip()


def _amount_payload(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"amount": 0.0, "cap": None, "direction": "unknown"}
    amount = item.get("penalty_amount", 0.0)
    cap = item.get("penalty_cap")
    try:
        amount_f = float(amount)
    except (TypeError, ValueError):
        amount_f = 0.0
    try:
        cap_f = None if cap is None else float(cap)
    except (TypeError, ValueError):
        cap_f = None
    return {"amount": amount_f, "cap": cap_f, "direction": "penalty" if amount_f > 0 else "unknown"}


def _numeric_values(content: str) -> list[float]:
    values: list[float] = []
    for token in NUMBER_RE.findall(content):
        try:
            values.append(float(token))
        except ValueError:
            continue
    return values


def _coordinate_targets(content: str) -> list[dict[str, float]]:
    targets: list[dict[str, float]] = []
    for match in COORD_PAIR_RE.finditer(content):
        try:
            lat = float(match.group(1))
            lng = float(match.group(2))
        except ValueError:
            continue
        if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
            targets.append({"lat": lat, "lng": lng})
    return targets[:3]


def _compile_shape(content: str, payload: dict[str, Any]) -> tuple[str, str, dict[str, Any], str, float, tuple[str, ...]]:
    if not content:
        return "unknown", "unknown", {}, "unknown", 0.0, ("unknown",)
    numbers = _numeric_values(content)
    has_clock = bool(CLOCK_RE.search(content))
    targets = _coordinate_targets(content)
    lower = content.lower()
    off_day_terms = (
        "off day",
        "free day",
        "complete day",
        "full day",
        "no orders",
        "no order",
        "整天",
        "自然月",
        "不接单",
    )
    field_terms = (
        "cargo category",
        "cargo label",
        "cargo type",
        "cargo name",
        "pickup city",
        "dropoff city",
        "start city",
        "end city",
        "visible field",
        "required field",
        "disallowed field",
        "forbidden field",
        "field value",
        "visible cargo value",
        "visible cargo values",
        "品类",
        "货源",
        "装货地",
        "卸货地",
        "城市",
    )
    amount = max(0.0, float(payload.get("amount", 0.0) or 0.0))
    cap = payload.get("cap")
    kind = "unknown"
    scope = "whole_period"
    repairability = "unknown"
    repair_actions: tuple[str, ...] = ("unknown",)
    if targets:
        kind = "location_relation"
        scope = "whole_period"
        repairability = "repairable_until_deadline"
        repair_actions = ("reposition_to_target", "take_towards_target")
    elif has_clock:
        kind = "time_window_constraint"
        scope = "day"
        repairability = "repairable_until_deadline"
        repair_actions = ("wait",)
    elif any(term in lower for term in off_day_terms):
        kind = "quota_constraint"
        scope = "whole_period"
        repairability = "repairable_by_quota"
        repair_actions = ("full_offday_wait", "wait")
    elif any(term in lower for term in field_terms):
        kind = "cargo_field_constraint"
        scope = "whole_period"
        repairability = "irreversible_after_action"
        repair_actions = ("avoid_take",)
    elif numbers:
        kind = "distance_budget"
        scope = "whole_period"
        repairability = "irreversible_after_action" if amount >= 5000.0 else "partially_repairable"
        repair_actions = ("avoid_take", "take_towards_target")
    condition = {
        "numeric_count": len(numbers),
        "numeric_min": min(numbers) if numbers else None,
        "numeric_max": max(numbers) if numbers else None,
        "has_clock": has_clock,
        "evidence_length": len(content),
        "penalty_amount": amount,
        "penalty_cap": cap,
        "target_coordinates": targets,
    }
    if kind == "quota_constraint":
        plausible_counts = [int(v) for v in numbers if 0 < v <= 31 and float(v).is_integer()]
        condition["required_count"] = min(plausible_counts) if plausible_counts else 1
        condition["quota_subject"] = "off_day"
    confidence = 0.34
    if amount > 0:
        confidence += 0.16
    if cap is not None:
        confidence += 0.08
    if numbers:
        confidence += 0.16
    if has_clock:
        confidence += 0.08
    if isinstance(cap, float) and amount > 0 and cap <= amount * 2.0:
        confidence += 0.04
    if repairability == "partially_repairable":
        repairability = "repairable_by_quota"
    return kind, scope, condition, repairability, min(0.82, confidence), repair_actions


def _predicate_spec(
    *,
    kind: str,
    scope: str,
    condition: dict[str, Any],
    amount_payload: dict[str, Any],
    evidence: str,
) -> dict[str, Any]:
    amount = float(amount_payload.get("amount", 0.0) or 0.0)
    cap = amount_payload.get("cap")
    evidence_hash = hashlib.sha256(evidence.encode("utf-8")).hexdigest()[:16] if evidence else ""
    if kind == "location_relation":
        predicate_type = "location_visit"
        fields = ("position_after",)
        operator = "near_target_then_wait"
        values = tuple(condition.get("target_coordinates") or ())
        coordinate_target = condition.get("target_coordinates") or "unknown"
        unresolved = "" if values else "unresolved_location_target"
    elif kind == "time_window_constraint":
        predicate_type = "continuous_wait"
        fields = ("wait_interval", "action_interval")
        operator = "ge_continuous_minutes"
        values = tuple(condition.get("time_window_minutes") or ())
        coordinate_target = "unknown"
        unresolved = ""
    elif kind == "distance_budget":
        predicate_type = "pickup_deadhead_limit"
        fields = ("pickup_deadhead_km",)
        operator = "<="
        values = tuple(v for v in (condition.get("numeric_min"), condition.get("numeric_max")) if v is not None)
        coordinate_target = "unknown"
        unresolved = ""
    elif kind == "quota_constraint":
        predicate_type = "off_day_quota"
        fields = ("day_action_count",)
        operator = ">="
        values = (condition.get("required_count", "unknown"),)
        coordinate_target = "unknown"
        unresolved = ""
    elif kind == "cargo_field_constraint":
        predicate_type = "cargo_field_match"
        fields = ("cargo_name", "start_city", "end_city")
        operator = "in_observed_vocab"
        values = ()
        coordinate_target = "unknown"
        unresolved = "needs_observed_vocab_link"
    else:
        predicate_type = "unknown"
        fields = ()
        operator = "unknown"
        values = ()
        coordinate_target = "unknown"
        unresolved = "no_executable_predicate"
    return {
        "predicate_type": predicate_type,
        "fields": fields,
        "operator": operator,
        "values": values,
        "time_scope": scope,
        "deadline": condition.get("deadline_day", "unknown"),
        "counter": condition.get("required_count", "unknown"),
        "coordinate_target": coordinate_target,
        "penalty_amount": amount,
        "penalty_cap": cap if isinstance(cap, float) else None,
        "evidence_hash": evidence_hash,
        "unresolved_reason": unresolved,
    }


def _contract_v2_fields(
    *,
    kind: str,
    scope: str,
    condition: dict[str, Any],
    repair_actions: tuple[str, ...],
    evidence: str,
) -> dict[str, Any]:
    observable_map = {
        "location_relation": "location",
        "time_window_constraint": "time_window",
        "distance_budget": "distance",
        "quota_constraint": "count",
        "cargo_field_constraint": "cargo_attribute",
    }
    metric_map = {
        "location_relation": "near",
        "time_window_constraint": "continuous_minutes",
        "distance_budget": "<=",
        "quota_constraint": ">=",
        "cargo_field_constraint": "match",
    }
    counting_map = {
        "location_relation": "once_if_failed",
        "time_window_constraint": "continuous_window",
        "distance_budget": "per_action",
        "quota_constraint": "month_end",
        "cargo_field_constraint": "per_action",
    }
    runtime_values = condition.get("target_coordinates") or []
    runtime_hashes = [
        hashlib.sha256(json.dumps(item, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
        for item in runtime_values
    ]
    return {
        "contract_version": "trident_v2_fallback",
        "polarity": "avoid" if kind in {"distance_budget", "cargo_field_constraint"} else "require",
        "observable": observable_map.get(kind, "unknown"),
        "metric": metric_map.get(kind, "unknown"),
        "counting": counting_map.get(kind, "unknown"),
        "slots": {
            "field": None,
            "operator": None,
            "runtime_values": [],
            "runtime_value_hashes": runtime_hashes,
            "time_window": condition.get("time_window_minutes"),
            "date_window": condition.get("date_window"),
            "duration_minutes": condition.get("duration_minutes"),
            "distance_km": condition.get("numeric_min") if kind == "distance_budget" else None,
            "count": condition.get("required_count"),
            "target_ref": None,
            "target_ref_hash": runtime_hashes[0] if runtime_hashes else "",
            "sequence_refs": [],
            "sequence_ref_hashes": [],
        },
        "repair": repair_actions,
        "uncertainty": tuple() if kind != "unknown" else ("no_executable_predicate",),
        "penalty_amount_source": "runtime_preference" if float(condition.get("penalty_amount", 0.0) or 0.0) > 0 else "unknown",
    }


def compile_if_changed(
    *,
    api: SimulationApiPort | None = None,
    status: DriverStatus,
    pref_hash: str,
    prev_rules: CompiledPreferenceSet | None,
) -> CompiledPreferenceSet:
    if prev_rules is not None and prev_rules.pref_hash == pref_hash:
        return prev_rules
    amount_payloads = [_amount_payload(item) for item in status.preferences]
    if config.ENABLE_QWEN_PREFERENCE_COMPILER:
        cached = qwen_preference_compiler.has_cached(pref_hash)
        if _COMPILE_BUDGET.allow_compile(status.driver_id, pref_hash, cached=cached):
            before = qwen_preference_compiler.STATS.compile_calls
            qwen_rules = qwen_preference_compiler.compile_with_qwen(
                api=api,
                pref_hash=pref_hash,
                preferences=status.preferences,
                fallback_amounts=amount_payloads,
            )
            if qwen_preference_compiler.STATS.compile_calls > before:
                _COMPILE_BUDGET.record_compile(status.driver_id, pref_hash)
        else:
            qwen_preference_compiler.record_budget_blocked()
            qwen_rules = None
        if qwen_rules is not None:
            return CompiledPreferenceSet(pref_hash=pref_hash, rules=qwen_rules)
    rules: list[CompiledPreferenceRule] = []
    for idx, item in enumerate(status.preferences):
        evidence = _preference_content(item)
        amount_payload = amount_payloads[idx]
        kind, scope, condition, repairability, confidence, repair_actions = _compile_shape(evidence, amount_payload)
        spec = _predicate_spec(kind=kind, scope=scope, condition=condition, amount_payload=amount_payload, evidence=evidence)
        contract_v2 = _contract_v2_fields(
            kind=kind,
            scope=scope,
            condition=condition,
            repair_actions=repair_actions,
            evidence=evidence,
        )
        rules.append(
            CompiledPreferenceRule(
                rule_id=f"pref_{idx}",
                kind=kind,
                scope=scope,
                condition=condition,
                repairability=repairability,
                reward_or_penalty=amount_payload,
                evidence=evidence,
                confidence=confidence,
                repair_action_kinds=repair_actions,
                **spec,
                **contract_v2,
            )
        )
    return CompiledPreferenceSet(pref_hash=pref_hash, rules=tuple(rules))
