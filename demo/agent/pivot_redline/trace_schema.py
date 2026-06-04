"""Trace payload construction for Pivot-Redline."""

from __future__ import annotations

import hashlib
from typing import Any

from .. import trace_writer
from ..schemas import CandidateOption, NormalizedCargo, World
from .safety_gate import explain_why_not_chosen


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def attach_pivot_trace(
    action: dict[str, Any],
    *,
    world: World,
    query_plan: Any,
    visible: list[NormalizedCargo],
    chosen: CandidateOption,
    options: list[CandidateOption],
    query_minutes: int,
    observed_count: int,
    b0_action: CandidateOption,
    b0_score: float,
    bucket_counts: dict[str, int],
    weights: Any,
    macro_stats: dict[str, int],
) -> dict[str, Any]:
    action = trace_writer.attach_trace(
        action,
        world=world,
        query_plan=query_plan,
        visible_cargos=visible,
        chosen=chosen,
        options=options,
        query_minutes=query_minutes,
        observed_count=observed_count,
    )
    trace = action.setdefault("agent_trace", {})
    trace["pivot_redline"] = {
        "variant": "crown_pivot_redline_v1",
        "b0_pure_action": b0_action.action_type,
        "b0_pure_candidate_hash": _hash(b0_action.id),
        "b0_pure_score": round(float(b0_score), 4),
        "new_action": chosen.action_type,
        "new_candidate_hash": _hash(chosen.id),
        "override_reason": "same_as_b0" if chosen.id == b0_action.id else "pivot_score_selected",
        "override_score_delta": round(float(chosen.score - b0_score), 4),
        "candidate_bucket_counts": dict(bucket_counts),
        "top5_candidates": explain_why_not_chosen(options, chosen),
        "score_components": {key: round(float(value), 4) for key, value in chosen.score_components.items()},
        "weights": {key: value for key, value in vars(weights).items() if key != "all_new_weights_zero"},
        "all_new_weights_zero": bool(getattr(weights, "all_new_weights_zero", False)),
        "macro": macro_stats,
    }
    return action
