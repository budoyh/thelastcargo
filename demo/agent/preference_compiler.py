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


def _compile_shape(content: str, payload: dict[str, Any]) -> tuple[str, str, dict[str, Any], str, float]:
    if not content:
        return "unknown", "unknown", {}, "unknown", 0.0
    numbers = _numeric_values(content)
    has_clock = bool(CLOCK_RE.search(content))
    amount = max(0.0, float(payload.get("amount", 0.0) or 0.0))
    cap = payload.get("cap")
    kind = "unknown"
    scope = "monthly"
    repairability = "unknown"
    if has_clock:
        kind = "time_window"
        scope = "time"
        repairability = "partially_repairable"
    elif numbers:
        kind = "quantitative_limit"
        scope = "route_or_time"
        repairability = "irreversible_after_action" if amount >= 5000.0 else "partially_repairable"
    condition = {
        "numeric_count": len(numbers),
        "numeric_min": min(numbers) if numbers else None,
        "numeric_max": max(numbers) if numbers else None,
        "has_clock": has_clock,
        "evidence_length": len(content),
        "penalty_amount": amount,
        "penalty_cap": cap,
    }
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
    return kind, scope, condition, repairability, min(0.82, confidence)


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
                _COMPILE_BUDGET.record_compile(status.driver_id)
        else:
            qwen_preference_compiler.record_budget_blocked()
            qwen_rules = None
        if qwen_rules is not None:
            return CompiledPreferenceSet(pref_hash=pref_hash, rules=qwen_rules)
    rules: list[CompiledPreferenceRule] = []
    for idx, item in enumerate(status.preferences):
        evidence = _preference_content(item)
        amount_payload = amount_payloads[idx]
        kind, scope, condition, repairability, confidence = _compile_shape(evidence, amount_payload)
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
            )
        )
    return CompiledPreferenceSet(pref_hash=pref_hash, rules=tuple(rules))
