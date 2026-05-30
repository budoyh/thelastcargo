"""Attach compact trace metadata to the returned action."""

from __future__ import annotations

from typing import Any

from . import config
from .schemas import CandidateOption, NormalizedCargo, World
from .time_utils import remaining_minutes


def _cert_payload(option: CandidateOption) -> dict[str, Any]:
    action_cert = option.action_cert
    cargo_id = action_cert.cargo_id if action_cert else (option.cargo.cargo_id if option.cargo else None)
    source_scope = action_cert.source_scope if action_cert else (option.cargo.source_scope if option.cargo else None)
    return {
        "candidate_id": option.id,
        "action_type": option.action_type,
        "cert_decision_id": action_cert.decision_id if action_cert else option.decision_id,
        "cargo_id": cargo_id,
        "source_scope": source_scope,
        "action_safe": bool(action_cert.safe) if action_cert else False,
        "action_reasons": list(action_cert.reasons) if action_cert else [],
        "score": round(float(option.score), 4),
        "components": {k: round(float(v), 4) for k, v in option.score_components.items()},
        "rollout_value": round(float(option.rollout.value), 4) if option.rollout else 0.0,
    }


def attach_trace(
    action: dict[str, Any],
    *,
    world: World,
    query_plan: Any,
    visible_cargos: list[NormalizedCargo],
    chosen: CandidateOption,
    options: list[CandidateOption] | None = None,
    query_minutes: int,
) -> dict[str, Any]:
    if config.SUBMIT_MODE:
        action["agent_trace"] = {
            "trace_level": "minimal",
            "decision_id": chosen.decision_id,
            "chosen": _cert_payload(chosen),
        }
        return action
    reposition_candidates = []
    for option in options or []:
        if option.action_type != "reposition":
            continue
        reposition_candidates.append(
            {
                "candidate_id": option.id,
                "score": round(float(option.score), 4),
                "action_safe": bool(option.action_cert.safe) if option.action_cert else False,
                "reasons": list(option.action_cert.reasons) if option.action_cert else [],
                "gate": dict(option.trace),
            }
        )
    action["agent_trace"] = {
        "trace_level": config.TRACE_LEVEL,
        "decision_id": chosen.decision_id,
        "query_plan": getattr(query_plan, "kind", "unknown"),
        "query_minutes": int(query_minutes),
        "visible_count": len(visible_cargos),
        "time_market": {
            "productive_time_shadow_price": round(world.time_market.productive_time_shadow_price, 4),
            "query_time_cost": round(world.time_market.query_time_cost, 4),
            "information_option_value": round(world.time_market.information_option_value, 4),
        },
        "endgame_intensity": round(world.endgame.intensity, 4),
        "debt_value": round(world.debt_market.debt_value, 4),
        "chosen": _cert_payload(chosen),
        "reposition_gate": dict(chosen.trace) if chosen.action_type == "reposition" else {},
        "reposition_candidates": reposition_candidates,
    }
    return action


def attach_exception_trace(
    action: dict[str, Any],
    *,
    decision_id: str,
    world: World | None,
    reason: str,
) -> dict[str, Any]:
    if world is not None:
        remaining = remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)
        action["params"]["duration_minutes"] = 0 if remaining <= 0 else min(1, remaining)
    action["agent_trace"] = {
        "trace_level": "minimal" if config.SUBMIT_MODE else "full",
        "decision_id": decision_id,
        "query_plan": "exception_fallback",
        "visible_count": 0,
        "chosen": {
            "candidate_id": "exception_fallback_wait",
            "action_type": "wait",
            "cert_decision_id": decision_id,
            "cargo_id": None,
            "source_scope": None,
            "action_safe": True,
            "action_reasons": ["decision_exception", reason],
            "score": 0.0,
            "components": {},
        },
    }
    return action
