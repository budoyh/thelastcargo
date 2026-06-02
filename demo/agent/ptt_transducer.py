"""Preference Type Transducer runtime adapter.

The module attempts a Qwen typed compile for real preferences, then validates
and downgrades to deterministic mappings where needed. Qwen never selects an
action and never invents missing penalty amounts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from simkit.ports import SimulationApiPort

from . import config, qwen_preference_compiler
from .ptt_types import COUNTING_UNITS, PTT_TYPES, PTTRule, TRIGGER_ACTIONS, from_compiled_rules, short_hash
from .schemas import World

_CACHE: dict[str, tuple[PTTRule, ...]] = {}

RBT_OPS = {
    "DATE_WINDOW",
    "DAILY_WINDOW",
    "INTERVAL_OVERLAP",
    "WAIT_COVERAGE",
    "ACTIVE_COVERAGE",
    "FULL_DAY_INACTIVE",
    "NO_ORDER_DAY",
    "FILTER_ACTION",
    "FIELD_MATCH",
    "TAKE_FIELD_MATCH",
    "START_END_REGION_MATCH",
    "DISTANCE",
    "PICKUP_DEADHEAD_LE",
    "HAUL_DISTANCE_LE",
    "CUMULATIVE_DISTANCE_BUDGET",
    "ORDER_COUNT_LE",
    "ORDER_COUNT_GE",
    "POSITION_NEAR",
    "ARRIVE_BEFORE",
    "DWELL_MINUTES",
    "ORDERED_SEQUENCE",
    "TAKE_TOWARDS_TARGET",
    "REPOSITION_TO_TARGET",
    "COUNT_PER_ACTION",
    "COUNT",
    "COUNT_DISTINCT_DAY",
    "COUNT_ONCE_IF_FAILED",
    "COUNT_CAPPED",
    "PENALTY",
    "PENALTY_AMOUNT",
    "PENALTY_CAP",
    "REPAIR",
    "UNKNOWN_SOFT",
    "ASK_LINKER",
    "AUDIT_TOP_CANDIDATE",
}


@dataclass
class PTTStats:
    compile_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    schema_valid_count: int = 0
    schema_mismatch_count: int = 0
    penalty_known_count: int = 0
    penalty_unknown_count: int = 0
    unknown_soft_count: int = 0
    controller_scored_candidate_count: int = 0
    candidate_rule_eval_count: int = 0
    score_changed_by_controller_count: int = 0
    changed_decision_count: int = 0
    hard_block_count: int = 0
    soft_penalty_count: int = 0
    repair_value_count: int = 0
    unknown_soft_risk_count: int = 0
    linker_call_required_count: int = 0
    linker_call_count: int = 0
    auditor_trigger_count: int = 0
    audited_candidate_count: int = 0
    auditor_changed_match_count: int = 0
    auditor_changed_score_count: int = 0
    auditor_changed_decision_count: int = 0
    auditor_changed_action_count: int = 0
    auditor_unknown_count: int = 0

    def payload(self) -> dict[str, Any]:
        return dict(self.__dict__)


STATS = PTTStats()


def _record_compiled_rule_stats(rules: tuple[PTTRule, ...]) -> None:
    for rule in rules:
        STATS.schema_valid_count += 1
        if rule.penalty_amount is None:
            STATS.penalty_unknown_count += 1
        else:
            STATS.penalty_known_count += 1
        if rule.type == "unknown_soft":
            STATS.unknown_soft_count += 1


def _prompt(preferences: tuple[Any, ...]) -> str:
    schema = {
        "type": list(PTT_TYPES),
        "counting_unit": list(COUNTING_UNITS),
        "trigger_action": list(TRIGGER_ACTIONS),
        "bytecode_ops": sorted(RBT_OPS),
    }
    return (
        "Compile runtime driver preferences into Rule Bytecode Transducer JSON. "
        "Return compact JSON only; no explanation. "
        "Do not choose final actions. Pipeline: extract constraints; fill slots; "
        "generate bytecode and validate executability; critique and repair JSON once. "
        "Do not invent penalty_amount or penalty_cap; use null and penalty_source unknown "
        "when missing from runtime input. Values that name runtime entities may be used "
        "for reasoning but committed output must use hashes or redaction. Return "
        "{\"rules\": [...]} with fields rule_id,type,scope,field,operator,value_hash,"
        "duration_minutes,time_window,deadline,count,distance_km,program,slots,"
        "penalty_amount,penalty_cap,penalty_source,counting_unit,trigger_action,"
        "repair_actions,confidence,uncertainty. Allowed schema: "
        + json.dumps(schema, sort_keys=True)
        + " Preferences: "
        + json.dumps(list(preferences), ensure_ascii=False, sort_keys=True)
    )


def _sanitize_program(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        return tuple()
    out: list[dict[str, Any]] = []
    for item in value[:24]:
        if not isinstance(item, dict):
            continue
        op = str(item.get("op", "")).strip()
        if op not in RBT_OPS:
            continue
        args = item.get("args")
        out.append({"op": op, "args": args if isinstance(args, dict) else {}})
    return tuple(out)


def _type_from_program(program: tuple[dict[str, Any], ...]) -> str:
    ops = {str(item.get("op", "")) for item in program}
    if "FULL_DAY_INACTIVE" in ops:
        return "full_inactive_day_quota"
    if "NO_ORDER_DAY" in ops:
        return "no_order_day_quota"
    if "WAIT_COVERAGE" in ops or "DAILY_WINDOW" in ops:
        return "daily_continuous_rest"
    if "TAKE_FIELD_MATCH" in ops or "START_END_REGION_MATCH" in ops:
        return "forbidden_cargo_attribute"
    if "PICKUP_DEADHEAD_LE" in ops:
        return "pickup_deadhead_limit"
    if "HAUL_DISTANCE_LE" in ops:
        return "haul_distance_limit"
    if "CUMULATIVE_DISTANCE_BUDGET" in ops:
        return "cumulative_deadhead_budget"
    if "COUNT_DISTINCT_DAY" in ops:
        return "required_cargo_attribute_distinct_days"
    if "ORDERED_SEQUENCE" in ops:
        return "ordered_multi_stop_task"
    if "POSITION_NEAR" in ops or "DWELL_MINUTES" in ops:
        return "location_visit_or_dwell"
    if "ORDER_COUNT_LE" in ops or "ORDER_COUNT_GE" in ops:
        return "daily_order_count_limit"
    return "unknown_soft"


def _penalty_from_pref(pref: Any) -> tuple[float | None, float | None, str, list[str]]:
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
    uncertainty: list[str] = []
    source = "runtime_preference" if amount is not None else "unknown"
    if amount is None:
        uncertainty.append("missing_penalty_amount")
    return amount, cap, source, uncertainty


def _rule_from_payload(idx: int, raw: dict[str, Any], pref: Any, pref_hash: str) -> PTTRule | None:
    program = _sanitize_program(raw.get("program"))
    rule_type = str(raw.get("type") or _type_from_program(program)).strip()
    if rule_type not in PTT_TYPES:
        STATS.schema_mismatch_count += 1
        return None
    fallback_amount, fallback_cap, penalty_source, uncertainty = _penalty_from_pref(pref)
    raw_amount = raw.get("penalty_amount")
    amount = fallback_amount
    if fallback_amount is None and raw_amount is not None:
        uncertainty.append("qwen_penalty_ignored_without_runtime_source")
    raw_cap = raw.get("penalty_cap")
    cap = fallback_cap
    if fallback_cap is None and raw_cap is not None:
        uncertainty.append("qwen_cap_ignored_without_runtime_source")
    counting_unit = str(raw.get("counting_unit", "unknown")).strip()
    trigger = str(raw.get("trigger_action", "unknown")).strip()
    repairs_raw = raw.get("repair_actions") or raw.get("repair_action_kinds") or []
    if isinstance(repairs_raw, str):
        repairs = (repairs_raw,)
    elif isinstance(repairs_raw, list):
        repairs = tuple(str(item) for item in repairs_raw[:5])
    else:
        repairs = ("unknown",)
    try:
        confidence = max(0.0, min(1.0, float(raw.get("confidence", 0.35))))
    except (TypeError, ValueError):
        confidence = 0.35
    STATS.schema_valid_count += 1
    if amount is None:
        STATS.penalty_unknown_count += 1
    else:
        STATS.penalty_known_count += 1
    if rule_type == "unknown_soft":
        STATS.unknown_soft_count += 1
    uncertainty_out = list(dict.fromkeys([*uncertainty, *[str(x) for x in raw.get("uncertainty", []) if isinstance(raw.get("uncertainty"), list)]]))
    slots = raw.get("slots") if isinstance(raw.get("slots"), dict) else {}
    slots = {
        **slots,
        "schema_validated": True,
        "bytecode_program": list(program),
        "bytecode_ops": [item["op"] for item in program],
    }
    return PTTRule(
        rule_id=short_hash({"pref_hash": pref_hash, "idx": idx, "type": rule_type}, 12),
        type=rule_type,
        scope=str(raw.get("scope", "unknown")),
        field=str(raw.get("field", "unknown")),
        operator=str(raw.get("operator", "unknown")),
        value_hash=str(raw.get("value_hash") or short_hash(idx, 12)),
        duration_minutes=_int_or_none(raw.get("duration_minutes")),
        time_window=_window(raw.get("time_window")),
        deadline=_int_or_none(raw.get("deadline")),
        count=_int_or_none(raw.get("count")),
        distance_km=_float_or_none(raw.get("distance_km")),
        penalty_amount=amount,
        penalty_cap=cap,
        penalty_source=penalty_source,
        counting_unit=counting_unit if counting_unit in COUNTING_UNITS else "unknown",
        trigger_action=trigger if trigger in TRIGGER_ACTIONS else "unknown",
        repair_actions=repairs,
        confidence=confidence,
        uncertainty=tuple(uncertainty_out),
        source_rule_id=f"qwen_{idx}",
        ptt_compile_source="qwen_ptt",
        slots=slots,
    )


def _int_or_none(value: Any) -> int | None:
    try:
        return None if value in {None, ""} else int(float(value))
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    try:
        return None if value in {None, ""} else float(value)
    except (TypeError, ValueError):
        return None


def _window(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        start = _int_or_none(value[0])
        end = _int_or_none(value[1])
        if start is not None and end is not None:
            return start, end
    return None


def compile_ptt_rules(api: SimulationApiPort | None, world: World) -> tuple[PTTRule, ...]:
    if not world.status.preferences:
        return tuple()
    if world.pref_hash in _CACHE:
        STATS.cache_hits += 1
        return _CACHE[world.pref_hash]
    STATS.cache_misses += 1
    if config.ENABLE_GOLD_CONTRACT_MPC:
        STATS.compile_calls += 1
        compiled = from_compiled_rules(world, compile_source="gold_contract")
        _record_compiled_rule_stats(compiled)
        _CACHE[world.pref_hash] = compiled
        return compiled
    compiled: tuple[PTTRule, ...] = tuple()
    payload = {
        "model": qwen_preference_compiler.STATS.last_model_name,
        "messages": [
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": _prompt(world.status.preferences)},
        ],
        "temperature": 0,
        "max_tokens": 512,
        "enable_thinking": False,
    }
    if config.DISABLE_RUNTIME_QWEN:
        qwen_preference_compiler.STATS.budget_blocked_count += 1
        qwen_preference_compiler.STATS.fallback_unknown_count += 1
        qwen_preference_compiler.STATS.last_error_type = "runtime_qwen_disabled"
    elif api is not None and hasattr(api, "model_chat_completion"):
        try:
            STATS.compile_calls += 1
            qwen_preference_compiler.STATS.compile_calls += 1
            compiled = _compile_from_response(
                qwen_preference_compiler._completion_with_retries(
                    api=api,
                    payload=payload,
                    api_key="",
                    use_injected_api=True,
                ),
                world,
            )
        except Exception as exc:  # pragma: no cover - remote API failures vary.
            qwen_preference_compiler.STATS.api_error_count += 1
            qwen_preference_compiler.STATS.last_error_type = exc.__class__.__name__
    else:
        _, key, key_status = qwen_preference_compiler._active_api_key()
        if key_status == "present":
            try:
                STATS.compile_calls += 1
                qwen_preference_compiler.STATS.compile_calls += 1
                compiled = _compile_from_response(
                    qwen_preference_compiler._completion_with_retries(
                        api=None,
                        payload=payload,
                        api_key=key,
                        use_injected_api=False,
                    ),
                    world,
                )
            except Exception as exc:  # pragma: no cover - remote API failures vary.
                qwen_preference_compiler.STATS.api_error_count += 1
                qwen_preference_compiler.STATS.last_error_type = exc.__class__.__name__
        elif key_status == "dummy":
            qwen_preference_compiler.STATS.dummy_key_blocked_count += 1
    if not compiled:
        compiled = from_compiled_rules(world, compile_source="deterministic_fallback")
        _record_compiled_rule_stats(compiled)
    _CACHE[world.pref_hash] = compiled
    return compiled


def _compile_from_response(resp: dict[str, Any], world: World) -> tuple[PTTRule, ...]:
    qwen_preference_compiler._usage_from_response(resp)
    data = qwen_preference_compiler._extract_json(qwen_preference_compiler._content_from_response(resp)) or {}
    raw_rules = data.get("rules", [])
    if not isinstance(raw_rules, list):
        STATS.schema_mismatch_count += 1
        return tuple()
    prefs = list(world.status.preferences)
    items = []
    for idx, raw in enumerate(raw_rules):
        if not isinstance(raw, dict):
            STATS.schema_mismatch_count += 1
            continue
        rule = _rule_from_payload(idx, raw, prefs[idx] if idx < len(prefs) else {}, world.pref_hash)
        if rule is not None:
            items.append(rule)
    return tuple(items)


def stats_payload() -> dict[str, Any]:
    return STATS.payload()
