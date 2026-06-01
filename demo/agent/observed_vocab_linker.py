"""Link runtime preferences to the current query's observed vocabulary."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from simkit.ports import SimulationApiPort

from . import config, qwen_preference_compiler
from .schemas import CompiledPreferenceRule, NormalizedCargo

MAX_VALUES_PER_FIELD = 30
_CACHE: dict[str, tuple["ObservedVocabLink", ...]] = {}


@dataclass(frozen=True)
class ObservedVocabLink:
    field: str
    value: str
    value_hash: str
    relation: str
    confidence: float
    rule_id: str
    evidence_hash: str
    source: str = "current_observed_vocab"


def _hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _cap_values(values: set[str]) -> list[str]:
    clean = sorted(v for v in values if v)[:MAX_VALUES_PER_FIELD]
    return clean


def _vocabulary(visible: list[NormalizedCargo]) -> dict[str, list[str]]:
    fields = {
        "cargo_name": _cap_values({c.cargo_name for c in visible}),
        "start_city": _cap_values({c.start_city for c in visible}),
        "end_city": _cap_values({c.end_city for c in visible}),
    }
    clusters = []
    for cargo in visible[:MAX_VALUES_PER_FIELD]:
        clusters.append(f"{round(cargo.start_lat, 2)},{round(cargo.start_lng, 2)}")
        clusters.append(f"{round(cargo.end_lat, 2)},{round(cargo.end_lng, 2)}")
    fields["coordinate_cluster"] = sorted(set(clusters))[:MAX_VALUES_PER_FIELD]
    return fields


def observed_vocab_hash(visible: list[NormalizedCargo]) -> str:
    return _hash(_vocabulary(visible))


def _prompt(preferences: tuple[Any, ...], rules: tuple[CompiledPreferenceRule, ...], vocab: dict[str, list[str]]) -> str:
    compact_rules = [
        {
            "rule_id": rule.rule_id,
            "predicate_type": rule.predicate_type,
            "fields": list(rule.fields),
            "operator": rule.operator,
            "time_scope": rule.time_scope,
            "repair_action_kinds": list(rule.repair_action_kinds),
            "evidence_hash": rule.evidence_hash,
        }
        for rule in rules
    ]
    return (
        "Link runtime preference predicates to current observed cargo vocabulary. "
        "Return compact JSON only; no explanation. "
        "Use only values in observed_vocab. Return JSON with links: field, value, "
        "relation violation|repair|neutral|unknown, confidence, rule_id, evidence_hash. "
        "Do not choose actions. Preferences and vocabulary are runtime input. "
        + json.dumps(
            {"preferences": list(preferences), "rules": compact_rules, "observed_vocab": vocab},
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _parse_links(raw: dict[str, Any], rules: tuple[CompiledPreferenceRule, ...], vocab: dict[str, list[str]]) -> tuple[ObservedVocabLink, ...]:
    rule_ids = {rule.rule_id for rule in rules}
    out: list[ObservedVocabLink] = []
    items = raw.get("links", []) if isinstance(raw, dict) else []
    if not isinstance(items, list):
        return tuple()
    for item in items:
        if not isinstance(item, dict):
            continue
        field = str(item.get("field", "")).strip()
        value = str(item.get("value", "")).strip()
        relation = str(item.get("relation", "unknown")).strip()
        rule_id = str(item.get("rule_id", "")).strip()
        if field not in vocab or value not in vocab[field] or relation not in {"violation", "repair", "neutral", "unknown"}:
            continue
        if rule_id not in rule_ids:
            continue
        try:
            conf = max(0.0, min(1.0, float(item.get("confidence", 0.0))))
        except (TypeError, ValueError):
            conf = 0.0
        out.append(
            ObservedVocabLink(
                field=field,
                value=value,
                value_hash=_hash(value),
                relation=relation,
                confidence=conf,
                rule_id=rule_id,
                evidence_hash=str(item.get("evidence_hash", ""))[:24],
            )
        )
    return tuple(out)


def _deterministic_links(preferences: tuple[Any, ...], rules: tuple[CompiledPreferenceRule, ...], vocab: dict[str, list[str]]) -> tuple[ObservedVocabLink, ...]:
    pref_text = json.dumps(list(preferences), ensure_ascii=False)
    out: list[ObservedVocabLink] = []
    for rule in rules:
        rule_text = rule.evidence or pref_text
        for field in ("cargo_name", "start_city", "end_city"):
            for value in vocab.get(field, []):
                if value and value in rule_text:
                    relation = "repair" if rule.predicate_type in {"location_visit", "count_distinct_days"} else "violation"
                    out.append(
                        ObservedVocabLink(
                            field=field,
                            value=value,
                            value_hash=_hash(value),
                            relation=relation,
                            confidence=max(0.55, min(0.85, rule.confidence)),
                            rule_id=rule.rule_id,
                            evidence_hash=rule.evidence_hash,
                        )
                    )
    return tuple(out)


def link_current_observed_vocab(
    *,
    api: SimulationApiPort | None,
    pref_hash: str,
    preferences: tuple[Any, ...],
    rules: tuple[CompiledPreferenceRule, ...],
    visible: list[NormalizedCargo],
) -> tuple[ObservedVocabLink, ...]:
    if not preferences or not visible:
        return tuple()
    vocab = _vocabulary(visible)
    key = pref_hash + ":" + _hash(vocab)
    if key in _CACHE:
        qwen_preference_compiler.STATS.cache_hits += 1
        return _CACHE[key]
    qwen_preference_compiler.STATS.cache_misses += 1
    if (
        not config.DISABLE_RUNTIME_QWEN
        and qwen_preference_compiler.STATS.linker_calls < config.LLM_MAX_LINKER_CALLS_TOTAL
        and qwen_preference_compiler.runtime_completion_available(api)
    ):
        try:
            qwen_preference_compiler.record_linker_call()
            resp = qwen_preference_compiler.completion_with_runtime_order(
                api=api,
                payload={
                    "model": qwen_preference_compiler.STATS.last_model_name,
                    "messages": [
                        {"role": "system", "content": "Return valid JSON only."},
                        {"role": "user", "content": _prompt(preferences, rules, vocab)},
                    ],
                    "temperature": 0,
                    "max_tokens": 128,
                    "enable_thinking": False,
                    "thinking_budget": 0,
                },
            )
            qwen_preference_compiler._usage_from_response(resp)
            data = qwen_preference_compiler._extract_json(qwen_preference_compiler._content_from_response(resp)) or {}
            links = _parse_links(data, rules, vocab)
            if links:
                _CACHE[key] = links
                return links
        except Exception as exc:  # pragma: no cover - remote API failures vary.
            qwen_preference_compiler.STATS.api_error_count += 1
            qwen_preference_compiler.STATS.last_error_type = exc.__class__.__name__
    elif qwen_preference_compiler.runtime_completion_available(api) and not config.DISABLE_RUNTIME_QWEN:
        qwen_preference_compiler.STATS.budget_exhausted_count += 1
    links = _deterministic_links(preferences, rules, vocab)
    _CACHE[key] = links
    return links
