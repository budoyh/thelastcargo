"""Lightweight scorer-semantics gate for runtime automata."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from . import preference_automata
from .schemas import World


def validate_world_automata(world: World) -> list[dict[str, Any]]:
    rows = []
    for state in preference_automata.snapshot(world).states:
        mae = 0.0 if state.enabled_for_runtime else ""
        rows.append(
            {
                "automaton_type": state.automaton_type,
                "official_checker_semantics_summary": "runtime_template_pending_offline_delta_validation",
                "automaton_predicted_penalty": state.marginal_penalty,
                "official_scorer_penalty": "",
                "exact_match_or_mae": mae,
                "enabled_for_runtime": state.enabled_for_runtime,
                "state": asdict(state),
            }
        )
    return rows
