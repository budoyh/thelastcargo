"""Unified action-value decomposition helpers."""

from __future__ import annotations

import hashlib
from typing import Any

from .schemas import CandidateOption

DECOMPOSITION_KEYS = (
    "freight_direct_net",
    "route_segment_value",
    "terminal_value",
    "macro_task_repair_value",
    "predicted_marginal_preference_cost",
    "broken_macro_task_cost",
    "lost_repair_window_cost",
    "time_cost",
    "query_cost",
    "reposition_cost",
    "execution_risk",
    "low_confidence_risk",
)


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _component(option: CandidateOption, *names: str) -> float:
    total = 0.0
    for name in names:
        value = option.score_components.get(name)
        if isinstance(value, (int, float)):
            total += float(value)
    return total


def _trace_float(option: CandidateOption, name: str, default: float = 0.0) -> float:
    value = option.trace.get(name, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def decompose(option: CandidateOption, *, chosen: bool = False, rank: int | None = None) -> dict[str, Any]:
    """Return a stable audit decomposition using runtime-visible candidate fields."""

    freight = option.direct_money
    route_value = _component(option, "twohop_lite", "rollout_value", "visible_rollout", "visible_graph_route_value")
    terminal = _component(option, "terminal_value", "learned_ranker")
    macro_repair = _component(option, "preference_repair_value", "pce_predicted_repair_value")
    macro_repair += _component(option, "ptt_repair_value")
    if option.trace.get("preference_repair"):
        macro_repair = max(macro_repair, _trace_float(option, "expected_repair_value"))
    pref_cost = -_component(
        option,
        "preference_soft_penalty",
        "rest_window_penalty",
        "pce_predicted_marginal_penalty",
        "ptt_marginal_penalty",
        "ptt_marginal_penalty_applied",
    )
    broken_macro = -_component(option, "broken_macro_task_cost")
    lost_window = -_component(option, "lost_repair_window_cost", "ptt_lost_repair_window_cost", "ptt_lost_repair_window_applied")
    time_cost = -_component(option, "time_shadow_lite", "duration_penalty")
    query_cost = -_component(option, "query_cost")
    reposition_cost = 0.0
    if option.action_type == "reposition":
        reposition_cost = abs(option.direct_money)
    reposition_cost += max(0.0, -_component(option, "micro_reposition_cost"))
    execution_risk = -_component(option, "execution_risk", "deadhead_penalty")
    low_conf = -_component(option, "low_confidence_risk", "ptt_low_confidence_risk", "ptt_low_confidence_applied")
    if option.pref_cert is not None:
        low_conf += max(0.0, option.pref_cert.unknown_risk)
    audit_adjustment = _component(option, "qwen_audit_adjustment", "qwen_audit_adjustment_applied", "ptt_auditor_adjustment")
    audit_items = option.trace.get("ptt_auditor") if isinstance(option.trace.get("ptt_auditor"), list) else []
    audit_first = audit_items[0] if audit_items and isinstance(audit_items[0], dict) else {}

    final_score = float(option.score)
    payload = {
        "rank": rank,
        "candidate_hash": _short_hash(option.id),
        "candidate_type": option.action_type,
        "freight_direct_net": round(freight, 4),
        "route_segment_value": round(route_value, 4),
        "terminal_value": round(terminal, 4),
        "macro_task_repair_value": round(macro_repair, 4),
        "predicted_marginal_preference_cost": round(pref_cost, 4),
        "broken_macro_task_cost": round(broken_macro, 4),
        "lost_repair_window_cost": round(lost_window, 4),
        "time_cost": round(time_cost, 4),
        "query_cost": round(query_cost, 4),
        "reposition_cost": round(reposition_cost, 4),
        "execution_risk": round(execution_risk, 4),
        "low_confidence_risk": round(low_conf, 4),
        "qwen_audit_adjustment": round(audit_adjustment, 4),
        "qwen_audit_relation": str(audit_first.get("relation", "")),
        "qwen_audit_effect": str(audit_first.get("effect", "")),
        "qwen_audit_risk": str(audit_first.get("risk_level", "")),
        "qwen_audit_repair": str(audit_first.get("repair_level", "")),
        "qwen_audit_confidence": audit_first.get("confidence", ""),
        "final_score": round(final_score, 4),
        "chosen_flag": bool(chosen),
        "why_not_chosen": "" if chosen else _why_not_chosen(option),
    }
    return payload


def _why_not_chosen(option: CandidateOption) -> str:
    if option.action_cert is not None and not option.action_cert.safe:
        return "action_certificate_unsafe"
    reason = option.trace.get("hard_block_reason")
    if reason:
        return str(reason)
    if option.action_type == "reposition":
        return "lower_ptt_score_or_reposition_gate"
    if option.action_type == "wait":
        return "lower_ptt_score_or_no_macro_commitment"
    return "lower_ptt_score"


def top_decompositions(
    options: list[CandidateOption],
    chosen: CandidateOption,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    ranked = sorted(options, key=lambda item: item.score, reverse=True)[: max(1, limit)]
    if chosen not in ranked:
        ranked = [chosen, *ranked[: max(0, limit - 1)]]
    out = []
    for idx, option in enumerate(ranked, start=1):
        out.append(decompose(option, chosen=option is chosen, rank=idx))
    return out
