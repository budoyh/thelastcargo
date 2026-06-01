"""Qwen preference compiler adapter with deterministic fallback."""

from __future__ import annotations

import json
import hashlib
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from simkit.ports import SimulationApiPort

from . import config
from .schemas import CompiledPreferenceRule

ALLOWED_KINDS = {
    "time_window_constraint",
    "quota_constraint",
    "sequence_constraint",
    "location_relation",
    "rest_requirement",
    "count_target",
    "distance_budget",
    "unknown",
}
ALLOWED_SCOPES = {"single_action", "day", "rolling_window", "month", "date_specific", "whole_period", "unknown"}
ALLOWED_REPAIR = {"irreversible", "irreversible_after_action", "repairable_until_deadline", "repairable_by_quota", "always_soft", "unknown"}
ALLOWED_REPAIR_ACTIONS = {"wait", "reposition_to_target", "take_towards_target", "avoid_take", "none", "unknown"}
ALLOWED_PREDICATE_TYPES = {
    "cargo_field_match",
    "action_time_overlap",
    "continuous_wait",
    "off_day_quota",
    "pickup_deadhead_limit",
    "location_visit",
    "route_sequence",
    "count_distinct_days",
    "unknown",
}
ALLOWED_OPERATORS = {
    "contains_any",
    "<=",
    "overlaps",
    "ge_continuous_minutes",
    "count_distinct_days_ge",
    "near_target_then_wait",
    "sequence_before_deadline",
    "unknown",
}


@dataclass
class CompileStats:
    compile_calls: int = 0
    judge_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    fallback_unknown_count: int = 0
    api_error_count: int = 0
    preferences_nonempty_count: int = 0
    dummy_key_blocked_count: int = 0
    budget_blocked_count: int = 0
    linker_calls: int = 0
    auditor_calls: int = 0
    timeout_count: int = 0
    budget_exhausted_count: int = 0
    token_usage_input: int = 0
    token_usage_output: int = 0
    token_usage_total: int = 0
    last_error_type: str = ""
    last_model_name: str = "qwen3.5-flash"


STATS = CompileStats()
_CACHE: dict[str, tuple[CompiledPreferenceRule, ...]] = {}


def _active_api_key() -> tuple[str, str, str]:
    for name in ("DASHSCOPE_API_KEY", "BAILIAN_API_KEY", "ALIYUN_API_KEY", "TIANCHI_MODEL_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            lowered = value.lower()
            if "dummy" in lowered or "not-used" in lowered or "local-" in lowered:
                return name, "", "dummy"
            return name, value, "present"
    return "", "", "missing"


def _prompt(preferences: tuple[Any, ...] | list[Any]) -> str:
    return (
        "Compile runtime driver preferences into executable predicate JSON only. "
        "Do not choose actions. Use only abstract schema fields. Each rule needs "
        "predicate_type, fields, operator, values, time_scope, deadline, counter, "
        "coordinate_target, repair_action_kinds, penalty_amount, penalty_cap, "
        "confidence, evidence_hash, and unresolved_reason. predicate_type must be "
        "one of cargo_field_match, action_time_overlap, continuous_wait, "
        "off_day_quota, pickup_deadhead_limit, location_visit, route_sequence, "
        "count_distinct_days, unknown. values may include runtime values from "
        "preference evidence only; unresolved rules must use predicate_type unknown. "
        "repair_action_kinds must use abstract labels only from wait, "
        "reposition_to_target, take_towards_target, avoid_take, none, unknown. "
        "Return a JSON object with key rules. Preferences: "
        + json.dumps(list(preferences), ensure_ascii=False, sort_keys=True)
    )


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _usage_from_response(resp: dict[str, Any]) -> None:
    usage = resp.get("usage", {})
    if not isinstance(usage, dict):
        return
    STATS.token_usage_input += int(usage.get("prompt_tokens", 0) or 0)
    STATS.token_usage_output += int(usage.get("completion_tokens", 0) or 0)
    STATS.token_usage_total += int(usage.get("total_tokens", 0) or 0)


def _content_from_response(resp: dict[str, Any]) -> str:
    choices = resp.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    return str(message.get("content", "") if isinstance(message, dict) else "")


def _dashscope_compatible_completion(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def _repair_actions(raw: dict[str, Any]) -> tuple[str, ...]:
    value = raw.get("repair_action_kinds", ())
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = [str(item) for item in value]
    else:
        items = []
    out = []
    for item in items:
        normalized = item.strip()
        if normalized in ALLOWED_REPAIR_ACTIONS and normalized not in out:
            out.append(normalized)
    return tuple(out or ("unknown",))


def _tuple_strings(value: Any, allowed: set[str] | None = None) -> tuple[str, ...]:
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = [str(item) for item in value]
    else:
        items = []
    out: list[str] = []
    for item in items:
        normalized = item.strip()
        if allowed is not None and normalized not in allowed:
            continue
        if normalized not in out:
            out.append(normalized)
    return tuple(out)


def _evidence_hash(raw: dict[str, Any]) -> str:
    value = raw.get("evidence_hash")
    if isinstance(value, str) and len(value.strip()) >= 8:
        return value.strip()[:24]
    evidence = str(raw.get("evidence", ""))
    return hashlib.sha256(evidence.encode("utf-8")).hexdigest()[:16] if evidence else ""


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rule_from_payload(idx: int, raw: dict[str, Any], fallback_amount: dict[str, Any]) -> CompiledPreferenceRule:
    kind = str(raw.get("kind", "unknown")).strip()
    scope = str(raw.get("scope", "unknown")).strip()
    repair = str(raw.get("repairability", "unknown")).strip()
    if repair == "irreversible":
        repair = "irreversible_after_action"
    reward = raw.get("reward_or_penalty")
    penalty_amount = _float_or_default(raw.get("penalty_amount"), _float_or_default(fallback_amount.get("amount"), 0.0))
    cap_raw = raw.get("penalty_cap", fallback_amount.get("cap"))
    try:
        penalty_cap = None if cap_raw is None else float(cap_raw)
    except (TypeError, ValueError):
        penalty_cap = None
    predicate_type = str(raw.get("predicate_type", raw.get("kind", "unknown"))).strip()
    operator = str(raw.get("operator", "unknown")).strip()
    confidence = raw.get("confidence", 0.0)
    try:
        conf = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        conf = 0.0
    return CompiledPreferenceRule(
        rule_id=f"qwen_{idx}",
        kind=kind if kind in ALLOWED_KINDS else "unknown",
        scope=scope if scope in ALLOWED_SCOPES else "unknown",
        condition=raw.get("condition") if isinstance(raw.get("condition"), dict) else {},
        repairability=repair if repair in ALLOWED_REPAIR else "unknown",
        reward_or_penalty=reward if isinstance(reward, dict) else fallback_amount,
        evidence=str(raw.get("evidence", "")),
        confidence=conf,
        repair_action_kinds=_repair_actions(raw),
        predicate_type=predicate_type if predicate_type in ALLOWED_PREDICATE_TYPES else "unknown",
        fields=_tuple_strings(raw.get("fields")),
        operator=operator if operator in ALLOWED_OPERATORS else "unknown",
        values=tuple(raw.get("values", ())) if isinstance(raw.get("values"), list) else tuple(),
        time_scope=str(raw.get("time_scope", scope if scope in ALLOWED_SCOPES else "unknown")),
        deadline=raw.get("deadline", "unknown"),
        counter=raw.get("counter", "unknown"),
        coordinate_target=raw.get("coordinate_target", raw.get("target_coordinates", "unknown")),
        penalty_amount=penalty_amount,
        penalty_cap=penalty_cap,
        evidence_hash=_evidence_hash(raw),
        unresolved_reason=str(raw.get("unresolved_reason", "")),
    )


def has_cached(pref_hash: str) -> bool:
    return pref_hash in _CACHE


def record_budget_blocked() -> None:
    STATS.budget_blocked_count += 1
    STATS.budget_exhausted_count += 1
    STATS.fallback_unknown_count += 1
    STATS.last_error_type = "compile_budget_exhausted"


def record_linker_call() -> None:
    STATS.linker_calls += 1


def record_auditor_call() -> None:
    STATS.auditor_calls += 1


def compile_with_qwen(
    *,
    api: SimulationApiPort | None,
    pref_hash: str,
    preferences: tuple[Any, ...],
    fallback_amounts: list[dict[str, Any]],
) -> tuple[CompiledPreferenceRule, ...] | None:
    if not preferences:
        return None
    STATS.preferences_nonempty_count += 1
    if config.DISABLE_RUNTIME_QWEN:
        STATS.budget_blocked_count += 1
        STATS.fallback_unknown_count += 1
        STATS.last_error_type = "runtime_qwen_disabled"
        return None
    if pref_hash in _CACHE:
        STATS.cache_hits += 1
        return _CACHE[pref_hash]
    STATS.cache_misses += 1
    use_injected_api = api is not None and hasattr(api, "model_chat_completion")
    _, api_key, state = _active_api_key()
    if state == "dummy":
        STATS.dummy_key_blocked_count += 1
        STATS.fallback_unknown_count += 1
        STATS.last_error_type = "dummy_key_blocked"
        return None
    if not use_injected_api:
        if state == "missing":
            STATS.fallback_unknown_count += 1
            STATS.last_error_type = "api_key_missing"
            return None
    payload = {
        "model": STATS.last_model_name,
        "messages": [
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": _prompt(preferences)},
        ],
        "temperature": 0,
        "max_tokens": STATS.last_model_name and 512,
    }
    try:
        STATS.compile_calls += 1
        if use_injected_api:
            resp = api.model_chat_completion(payload)
        else:
            resp = _dashscope_compatible_completion(payload, api_key)
        _usage_from_response(resp)
        data = _extract_json(_content_from_response(resp))
        rules_raw = data.get("rules", []) if isinstance(data, dict) else []
        if not isinstance(rules_raw, list):
            raise ValueError("rules_not_list")
        rules: list[CompiledPreferenceRule] = []
        for idx, raw in enumerate(rules_raw):
            if isinstance(raw, dict):
                fallback = fallback_amounts[idx] if idx < len(fallback_amounts) else {"amount": 0.0, "cap": None, "direction": "unknown"}
                rules.append(_rule_from_payload(idx, raw, fallback))
        if not rules:
            raise ValueError("empty_rules")
        _CACHE[pref_hash] = tuple(rules)
        return _CACHE[pref_hash]
    except Exception as exc:  # pragma: no cover - exact failures depend on remote API.
        STATS.api_error_count += 1
        STATS.fallback_unknown_count += 1
        STATS.last_error_type = exc.__class__.__name__
        if exc.__class__.__name__.lower().endswith("timeout"):
            STATS.timeout_count += 1
        return None


def stats_payload() -> dict[str, Any]:
    return {
        "model_name": STATS.last_model_name,
        "compile_calls": STATS.compile_calls,
        "judge_calls": STATS.judge_calls,
        "cache_hits": STATS.cache_hits,
        "cache_misses": STATS.cache_misses,
        "fallback_unknown_count": STATS.fallback_unknown_count,
        "fallback_count": STATS.fallback_unknown_count,
        "api_error_count": STATS.api_error_count,
        "preferences_nonempty_count": STATS.preferences_nonempty_count,
        "dummy_key_blocked_count": STATS.dummy_key_blocked_count,
        "budget_blocked_count": STATS.budget_blocked_count,
        "linker_calls": STATS.linker_calls,
        "auditor_calls": STATS.auditor_calls,
        "timeout_count": STATS.timeout_count,
        "budget_exhausted_count": STATS.budget_exhausted_count,
        "token_usage_input": STATS.token_usage_input,
        "token_usage_output": STATS.token_usage_output,
        "token_usage_total": STATS.token_usage_total,
        "last_error_type": STATS.last_error_type,
    }
