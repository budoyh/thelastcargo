"""Runtime Preference Automata state estimates for Delta-MPC.

The automata here are conservative runtime estimators. They do not import or
read official scorer internals; offline tools validate them against scorer
outputs before high-lambda use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import CompiledPreferenceRule, World
from .time_utils import day_index


@dataclass(frozen=True)
class AutomatonState:
    rule_id: str
    automaton_type: str
    progress: dict[str, Any]
    is_satisfied: bool
    is_failed: bool
    remaining_slack: float
    next_deadline: int | None
    repair_actions: tuple[str, ...]
    destroy_actions: tuple[str, ...]
    marginal_penalty: float
    repair_value: float
    future_failure_probability: float
    confidence: float
    enabled_for_runtime: bool
    notes: str = ""


@dataclass
class AutomataSnapshot:
    states: list[AutomatonState] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        active = [state for state in self.states if not state.is_satisfied and not state.is_failed]
        urgent = [state for state in active if state.future_failure_probability >= 0.5]
        return {
            "automata_count": len(self.states),
            "active_count": len(active),
            "urgent_count": len(urgent),
            "enabled_count": sum(1 for state in self.states if state.enabled_for_runtime),
            "types": sorted({state.automaton_type for state in self.states}),
        }


def _amount(rule: CompiledPreferenceRule) -> float:
    value = rule.penalty_amount or rule.reward_or_penalty.get("amount", 0.0)
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def _automaton_type(rule: CompiledPreferenceRule) -> str:
    predicate = rule.predicate_type
    if predicate == "continuous_wait" or rule.kind in {"time_window_constraint", "rest_requirement"}:
        return "continuous_or_scheduled_rest"
    if predicate == "off_day_quota":
        return "full_inactive_day"
    if predicate == "cargo_field_match":
        return "cargo_field_avoid_or_require"
    if predicate == "count_distinct_days":
        return "cargo_field_quota_or_distinct_day"
    if predicate == "pickup_deadhead_limit":
        return "pickup_or_haul_distance_limit"
    if predicate == "location_visit":
        return "date_location_visit_or_dwell"
    if predicate == "route_sequence":
        return "ordered_target_or_route_like_task"
    if rule.kind == "location_relation":
        return "region_or_location_avoid_or_require"
    return "unknown_soft"


def _deadline(rule: CompiledPreferenceRule, world: World) -> int | None:
    now = world.status.simulation_progress_minutes
    deadline = rule.deadline
    if isinstance(deadline, int):
        if 1 <= deadline <= 31:
            return int(deadline - 1) * 1440
        return int(deadline)
    if isinstance(deadline, float):
        return int(deadline)
    if isinstance(deadline, str):
        stripped = deadline.strip()
        if stripped.isdigit():
            day = int(stripped)
            if 1 <= day <= 31:
                return (day - 1) * 1440
    auto_type = _automaton_type(rule)
    if auto_type in {"continuous_or_scheduled_rest", "full_inactive_day"}:
        return ((now // 1440) + 1) * 1440
    return world.horizon.horizon_minutes


def _future_failure_probability(rule: CompiledPreferenceRule, world: World, deadline: int | None) -> float:
    confidence = max(0.0, min(1.0, rule.confidence))
    if deadline is None:
        return min(0.45, 1.0 - confidence)
    slack = max(0, deadline - world.status.simulation_progress_minutes)
    pressure = 1.0 - min(1.0, slack / max(1, world.horizon.horizon_minutes))
    if _automaton_type(rule) in {"continuous_or_scheduled_rest", "full_inactive_day"}:
        pressure = max(pressure, 0.35 if world.status.simulation_progress_minutes % 1440 < 10 * 60 else 0.15)
    return round(max(0.05, min(0.95, pressure * max(0.25, confidence))), 4)


def state_for_rule(rule: CompiledPreferenceRule, world: World) -> AutomatonState:
    auto_type = _automaton_type(rule)
    amount = _amount(rule)
    deadline = _deadline(rule, world)
    slack = float(max(0, (deadline or world.horizon.horizon_minutes) - world.status.simulation_progress_minutes))
    confidence = max(0.0, min(1.0, rule.confidence))
    fail_prob = _future_failure_probability(rule, world, deadline)
    repair_actions = tuple(rule.repair_action_kinds or ("unknown",))
    destroy_actions: tuple[str, ...]
    if auto_type in {"continuous_or_scheduled_rest", "full_inactive_day"}:
        destroy_actions = ("query", "take_order", "reposition")
    elif auto_type in {"cargo_field_avoid_or_require", "pickup_or_haul_distance_limit"}:
        destroy_actions = ("take_order",)
    else:
        destroy_actions = ("take_order", "wait", "reposition")
    enabled = auto_type != "unknown_soft" and confidence >= 0.35
    repair_value = amount * confidence * fail_prob
    marginal_penalty = amount * confidence
    progress = {
        "day_index": day_index(world.status.simulation_progress_minutes),
        "completed_orders": world.status.completed_order_count,
        "action_counts": dict(world.ledger.action_counts),
        "remaining_minutes": world.endgame.remaining_minutes,
    }
    return AutomatonState(
        rule_id=rule.rule_id,
        automaton_type=auto_type,
        progress=progress,
        is_satisfied=False,
        is_failed=False,
        remaining_slack=round(slack, 2),
        next_deadline=deadline,
        repair_actions=repair_actions,
        destroy_actions=destroy_actions,
        marginal_penalty=round(marginal_penalty, 2),
        repair_value=round(repair_value, 2),
        future_failure_probability=fail_prob,
        confidence=round(confidence, 4),
        enabled_for_runtime=enabled,
        notes="" if enabled else "diagnostic_or_unknown_soft",
    )


def snapshot(world: World) -> AutomataSnapshot:
    return AutomataSnapshot([state_for_rule(rule, world) for rule in world.rules.rules])
