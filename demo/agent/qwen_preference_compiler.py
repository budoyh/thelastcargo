"""Qwen preference compiler adapter with deterministic fallback."""

from __future__ import annotations

import json
import hashlib
import os
import re
import time
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
GOLD_CONTRACT_REQUIRED_FIELDS = {
    "polarity",
    "observable",
    "scope",
    "metric",
    "counting",
    "slots",
    "severity",
    "repair_actions",
    "confidence",
    "uncertainty",
    "evidence_hash",
}
GOLD_ALLOWED_POLARITIES = {"prefer", "avoid", "require", "forbid", "neutral", "unknown"}
GOLD_ALLOWED_OBSERVABLES = {
    "cargo_attribute",
    "time_window",
    "duration",
    "distance",
    "count",
    "location",
    "sequence",
    "work_pattern",
    "unknown",
}
GOLD_ALLOWED_COUNTING = {
    "per_action",
    "per_take",
    "per_order",
    "per_day",
    "distinct_days",
    "continuous_minutes",
    "capped_count",
    "month_end",
    "whole_period",
    "unknown",
}
GOLD_ALLOWED_SEVERITY_SOURCES = {"runtime_preference", "runtime_metadata", "unknown"}


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
    retry_count: int = 0
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
        "Compile runtime driver preferences into Preference Contract JSON only. "
        "Return compact valid JSON only; no explanation and no final action. "
        "The top object must contain contract_version='gold_v1' and rules. "
        "Each rule must include polarity, observable, scope, metric, counting, "
        "slots, severity, repair_actions, confidence, uncertainty, evidence_hash, "
        "plus executable predicate fields predicate_type, fields, operator, values, "
        "time_scope, deadline, counter, coordinate_target. Allowed observables are "
        "cargo_attribute,time_window,duration,distance,count,location,sequence,"
        "work_pattern,unknown. Do not invent penalty_amount or penalty_cap; use "
        "null and severity.source='unknown' when missing from runtime input. "
        "Runtime values may appear only in slots/values for this in-memory call; "
        "evidence_hash must hash evidence. Preferences: "
        + json.dumps(list(preferences), ensure_ascii=False, sort_keys=True)
    )


def _legacy_rescue_prompt(preferences: tuple[Any, ...] | list[Any]) -> str:
    return (
        "Compile runtime driver preferences into abstract JSON DSL only. "
        "Do not choose actions. Use only abstract fields: time windows, counts, "
        "location relations, sequence, rest, reward/penalty, evidence span and confidence. "
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
    with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT_SECONDS) as resp:
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
    if isinstance(value, str):
        cleaned = value.strip()
        if re.fullmatch(r"[0-9a-fA-F]{8,64}", cleaned):
            return cleaned[:24].lower()
        if cleaned:
            return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:16]
    evidence = str(raw.get("evidence", ""))
    return hashlib.sha256(evidence.encode("utf-8")).hexdigest()[:16] if evidence else ""


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_number_or_null(value: Any) -> bool:
    return value is None or (isinstance(value, (int, float)) and not isinstance(value, bool))


def _is_string_or_null(value: Any) -> bool:
    return value is None or isinstance(value, str)


def _runtime_penalty_from_fallback(fallback_amount: dict[str, Any]) -> tuple[float | None, float | None, str]:
    amount_raw = fallback_amount.get("amount")
    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        amount = 0.0
    if amount <= 0.0 or fallback_amount.get("direction") != "penalty":
        return None, None, "unknown"
    cap_raw = fallback_amount.get("cap")
    try:
        cap = None if cap_raw is None else float(cap_raw)
    except (TypeError, ValueError):
        cap = None
    return amount, cap, "runtime_preference"


def _runtime_reward_payload(fallback_amount: dict[str, Any]) -> dict[str, Any]:
    amount, cap, source = _runtime_penalty_from_fallback(fallback_amount)
    if source == "runtime_preference" and amount is not None:
        return {"amount": amount, "cap": cap, "direction": "penalty"}
    return {"amount": None, "cap": None, "direction": "unknown"}


def _rule_from_payload(idx: int, raw: dict[str, Any], fallback_amount: dict[str, Any]) -> CompiledPreferenceRule:
    if "polarity" in raw or "observable" in raw:
        raw = _payload_from_gold_contract(raw)
    kind = str(raw.get("kind", "unknown")).strip()
    scope = str(raw.get("scope", "unknown")).strip()
    repair = str(raw.get("repairability", "unknown")).strip()
    if repair == "irreversible":
        repair = "irreversible_after_action"
    reward = _runtime_reward_payload(fallback_amount)
    penalty_amount, penalty_cap, penalty_source = _runtime_penalty_from_fallback(fallback_amount)
    unresolved = str(raw.get("unresolved_reason", ""))
    if raw.get("penalty_amount") is not None and penalty_source != "runtime_preference":
        unresolved = (unresolved + "|qwen_penalty_ignored_without_runtime_source").strip("|")
    if raw.get("penalty_cap") is not None and penalty_cap is None:
        unresolved = (unresolved + "|qwen_cap_ignored_without_runtime_source").strip("|")
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
        reward_or_penalty=reward,
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
        unresolved_reason=unresolved,
    )


def _payload_from_gold_contract(raw: dict[str, Any]) -> dict[str, Any]:
    observable = str(raw.get("observable", "unknown")).strip()
    polarity = str(raw.get("polarity", "unknown")).strip()
    metric = str(raw.get("metric", "unknown")).strip()
    slots = raw.get("slots") if isinstance(raw.get("slots"), dict) else {}
    severity = raw.get("severity") if isinstance(raw.get("severity"), dict) else {}
    repairs = raw.get("repair_actions") if isinstance(raw.get("repair_actions"), list) else ["unknown"]
    uncertainty_raw = raw.get("uncertainty")
    if isinstance(uncertainty_raw, list):
        uncertainty = [str(item) for item in uncertainty_raw if item not in (None, "")]
    elif uncertainty_raw in (None, ""):
        uncertainty = []
    else:
        uncertainty = [str(uncertainty_raw)]
    predicate_map = {
        "cargo_attribute": "cargo_field_match",
        "time_window": "continuous_wait",
        "duration": "continuous_wait",
        "distance": "pickup_deadhead_limit",
        "count": "off_day_quota",
        "location": "location_visit",
        "sequence": "route_sequence",
        "work_pattern": "continuous_wait",
    }
    kind_map = {
        "cargo_attribute": "unknown",
        "time_window": "time_window_constraint",
        "duration": "time_window_constraint",
        "distance": "distance_budget",
        "count": "quota_constraint",
        "location": "location_relation",
        "sequence": "sequence_constraint",
        "work_pattern": "rest_requirement",
    }
    fields = []
    field_ref = slots.get("field_ref")
    if isinstance(field_ref, str) and field_ref:
        fields.append(field_ref)
    elif observable == "cargo_attribute":
        fields.extend(["cargo_name", "start_city", "end_city"])
    return {
        "kind": kind_map.get(observable, "unknown"),
        "scope": raw.get("scope", "unknown"),
        "condition": {
            "gold_contract": {
                "polarity": polarity,
                "observable": observable,
                "metric": metric,
                "counting": raw.get("counting", "unknown"),
                "slots_hash": hashlib.sha256(json.dumps(slots, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16],
                "severity_source": severity.get("source", "unknown"),
            },
            "duration_minutes": slots.get("duration_minutes"),
            "time_window": slots.get("time_window"),
            "deadline": slots.get("deadline"),
            "count": slots.get("count"),
            "distance_km": slots.get("distance_km"),
            "coordinate_target": slots.get("location_ref"),
            "sequence_refs": slots.get("sequence_refs") if isinstance(slots.get("sequence_refs"), list) else [],
        },
        "repairability": "irreversible_after_action" if raw.get("counting") == "per_action" else "repairable_until_deadline",
        "reward_or_penalty": {"amount": severity.get("penalty_amount"), "cap": severity.get("penalty_cap"), "direction": "penalty" if severity.get("penalty_amount") is not None else "unknown"},
        "evidence": "runtime_contract",
        "confidence": raw.get("confidence", 0.0),
        "repair_action_kinds": repairs,
        "predicate_type": predicate_map.get(observable, "unknown"),
        "fields": fields,
        "operator": metric if metric in ALLOWED_OPERATORS else "unknown",
        "values": [slots.get("field_ref"), slots.get("location_ref")],
        "time_scope": raw.get("scope", "unknown"),
        "deadline": slots.get("deadline", "unknown"),
        "counter": slots.get("count", "unknown"),
        "coordinate_target": slots.get("location_ref", "unknown"),
        "evidence_hash": raw.get("evidence_hash", ""),
        "unresolved_reason": ";".join(uncertainty),
    }


def _valid_gold_rule(rule: Any) -> bool:
    if not isinstance(rule, dict) or not GOLD_CONTRACT_REQUIRED_FIELDS <= set(rule):
        return False
    if not isinstance(rule.get("polarity"), str) or rule["polarity"] not in GOLD_ALLOWED_POLARITIES:
        return False
    if not isinstance(rule.get("observable"), str) or rule["observable"] not in GOLD_ALLOWED_OBSERVABLES:
        return False
    if not isinstance(rule.get("scope"), str) or rule["scope"] not in ALLOWED_SCOPES:
        return False
    if not isinstance(rule.get("metric"), str):
        return False
    if not isinstance(rule.get("counting"), str) or rule["counting"] not in GOLD_ALLOWED_COUNTING:
        return False
    if not isinstance(rule.get("slots"), dict):
        return False
    severity = rule.get("severity")
    if not isinstance(severity, dict):
        return False
    source = severity.get("source")
    if not isinstance(source, str) or source not in GOLD_ALLOWED_SEVERITY_SOURCES:
        return False
    if not _is_number_or_null(severity.get("penalty_amount")) or not _is_number_or_null(severity.get("penalty_cap")):
        return False
    if source == "unknown" and (severity.get("penalty_amount") is not None or severity.get("penalty_cap") is not None):
        return False
    repairs = rule.get("repair_actions")
    if not isinstance(repairs, list) or not repairs:
        return False
    if any(not isinstance(item, str) or item not in ALLOWED_REPAIR_ACTIONS for item in repairs):
        return False
    confidence = rule.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not (0.0 <= float(confidence) <= 1.0):
        return False
    uncertainty = rule.get("uncertainty")
    if not isinstance(uncertainty, list) or any(not isinstance(item, str) for item in uncertainty):
        return False
    evidence_hash = rule.get("evidence_hash")
    if not isinstance(evidence_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{8,64}", evidence_hash.strip()):
        return False
    optional_strings = ("predicate_type", "operator", "time_scope")
    if any(key in rule and not isinstance(rule.get(key), str) for key in optional_strings):
        return False
    if "fields" in rule and not (
        isinstance(rule.get("fields"), list) and all(isinstance(item, str) for item in rule.get("fields", []))
    ):
        return False
    for key in ("deadline", "counter", "coordinate_target"):
        if key in rule and not _is_string_or_null(rule.get(key)) and not _is_number_or_null(rule.get(key)):
            return False
    return True


def _valid_gold_contract(data: dict[str, Any]) -> bool:
    if data.get("contract_version") != "gold_v1":
        return False
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        return False
    return all(_valid_gold_rule(rule) for rule in rules)


def _completion_with_retries(
    *,
    api: SimulationApiPort | None,
    payload: dict[str, Any],
    api_key: str,
    use_injected_api: bool,
) -> dict[str, Any]:
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            if use_injected_api:
                return api.model_chat_completion(payload) if api is not None else {}
            return _dashscope_compatible_completion(payload, api_key)
        except Exception as exc:  # pragma: no cover - transport errors vary.
            last_exc = exc
            if attempt < 2:
                STATS.retry_count += 1
                time.sleep(float(2**attempt))
    assert last_exc is not None
    raise last_exc


def completion_with_runtime_order(
    *,
    api: SimulationApiPort | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Try injected runtime API first, then compatible endpoint with the same retry policy."""

    use_injected_api = api is not None and hasattr(api, "model_chat_completion")
    last_exc: Exception | None = None
    if use_injected_api:
        try:
            return _completion_with_retries(api=api, payload=payload, api_key="", use_injected_api=True)
        except Exception as exc:  # pragma: no cover - transport failures vary.
            last_exc = exc
    _, api_key, state = _active_api_key()
    if state == "dummy":
        STATS.dummy_key_blocked_count += 1
        STATS.last_error_type = "dummy_key_blocked"
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("dummy_key_blocked")
    if state == "missing":
        STATS.last_error_type = "api_key_missing"
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("api_key_missing")
    return _completion_with_retries(api=None, payload=payload, api_key=api_key, use_injected_api=False)


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


def runtime_completion_available(api: SimulationApiPort | None) -> bool:
    if api is not None and hasattr(api, "model_chat_completion"):
        return True
    _, _, state = _active_api_key()
    return state == "present"


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
    if state == "dummy" and not use_injected_api:
        STATS.dummy_key_blocked_count += 1
        STATS.fallback_unknown_count += 1
        STATS.last_error_type = "dummy_key_blocked"
        return None
    if not use_injected_api:
        if state == "missing":
            STATS.fallback_unknown_count += 1
            STATS.last_error_type = "api_key_missing"
            return None
    if config.ENABLE_LEGACY_RESCUE_QWEN:
        payload = {
            "model": STATS.last_model_name,
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": _legacy_rescue_prompt(preferences)},
            ],
            "temperature": 0,
        }
    else:
        payload = {
            "model": STATS.last_model_name,
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": _prompt(preferences)},
            ],
            "temperature": 0,
            "max_tokens": config.LLM_MAX_OUTPUT_TOKENS,
            "enable_thinking": False,
            "thinking_budget": 0,
        }
    try:
        STATS.compile_calls += 1
        resp = completion_with_runtime_order(api=api, payload=payload)
        _usage_from_response(resp)
        data = _extract_json(_content_from_response(resp))
        if not config.ENABLE_LEGACY_RESCUE_QWEN and (not isinstance(data, dict) or not _valid_gold_contract(data)):
            raise ValueError("invalid_gold_contract_schema")
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
        "retry_count": STATS.retry_count,
        "budget_exhausted_count": STATS.budget_exhausted_count,
        "token_usage_input": STATS.token_usage_input,
        "token_usage_output": STATS.token_usage_output,
        "token_usage_total": STATS.token_usage_total,
        "last_error_type": STATS.last_error_type,
    }
