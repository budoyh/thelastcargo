"""Qwen preference compiler adapter with deterministic fallback."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from simkit.ports import SimulationApiPort

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
    token_usage_input: int = 0
    token_usage_output: int = 0
    token_usage_total: int = 0
    last_error_type: str = ""
    last_model_name: str = "qwen3.5-flash"


STATS = CompileStats()
_CACHE: dict[str, tuple[CompiledPreferenceRule, ...]] = {}


def _key_state() -> str:
    for name in ("DASHSCOPE_API_KEY", "BAILIAN_API_KEY", "ALIYUN_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            lowered = value.lower()
            if "dummy" in lowered or "not-used" in lowered or "local-" in lowered:
                return "dummy"
            return "present"
    return "missing"


def _prompt(preferences: tuple[Any, ...] | list[Any]) -> str:
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


def _rule_from_payload(idx: int, raw: dict[str, Any], fallback_amount: dict[str, Any]) -> CompiledPreferenceRule:
    kind = str(raw.get("kind", "unknown")).strip()
    scope = str(raw.get("scope", "unknown")).strip()
    repair = str(raw.get("repairability", "unknown")).strip()
    if repair == "irreversible":
        repair = "irreversible_after_action"
    reward = raw.get("reward_or_penalty")
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
    )


def has_cached(pref_hash: str) -> bool:
    return pref_hash in _CACHE


def record_budget_blocked() -> None:
    STATS.budget_blocked_count += 1
    STATS.fallback_unknown_count += 1
    STATS.last_error_type = "compile_budget_exhausted"


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
    if pref_hash in _CACHE:
        STATS.cache_hits += 1
        return _CACHE[pref_hash]
    STATS.cache_misses += 1
    state = _key_state()
    if state == "missing":
        STATS.fallback_unknown_count += 1
        STATS.last_error_type = "api_key_missing"
        return None
    if state == "dummy":
        STATS.dummy_key_blocked_count += 1
        STATS.fallback_unknown_count += 1
        STATS.last_error_type = "dummy_key_blocked"
        return None
    if api is None or not hasattr(api, "model_chat_completion"):
        STATS.fallback_unknown_count += 1
        STATS.last_error_type = "api_method_unavailable"
        return None
    payload = {
        "model": STATS.last_model_name,
        "messages": [
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": _prompt(preferences)},
        ],
        "temperature": 0,
    }
    try:
        STATS.compile_calls += 1
        resp = api.model_chat_completion(payload)
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
        return None


def stats_payload() -> dict[str, Any]:
    return {
        "model_name": STATS.last_model_name,
        "compile_calls": STATS.compile_calls,
        "judge_calls": STATS.judge_calls,
        "cache_hits": STATS.cache_hits,
        "cache_misses": STATS.cache_misses,
        "fallback_unknown_count": STATS.fallback_unknown_count,
        "api_error_count": STATS.api_error_count,
        "preferences_nonempty_count": STATS.preferences_nonempty_count,
        "dummy_key_blocked_count": STATS.dummy_key_blocked_count,
        "budget_blocked_count": STATS.budget_blocked_count,
        "token_usage_input": STATS.token_usage_input,
        "token_usage_output": STATS.token_usage_output,
        "token_usage_total": STATS.token_usage_total,
        "last_error_type": STATS.last_error_type,
    }
