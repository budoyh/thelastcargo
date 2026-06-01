"""Scorer semantics gate for PTT controller impacts."""

from __future__ import annotations

from dataclasses import dataclass

from .preference_controllers import ControllerImpact
from .ptt_types import PTTRule

DIRECT_ACTION_ALIGNED = {
    "forbidden_cargo_attribute",
    "pickup_deadhead_limit",
    "haul_distance_limit",
    "daily_order_count_limit",
}

SOFT_ONLY = {
    "unknown_soft",
    "region_avoid_or_require",
    "runtime_entity_task",
    "daily_work_pattern",
}


@dataclass(frozen=True)
class SemanticsDecision:
    hard_block_allowed: bool
    massive_penalty_allowed: bool
    counting_unit: str
    probe_status: str
    notes: str


def decision_for_rule(rule: PTTRule) -> SemanticsDecision:
    if rule.type in DIRECT_ACTION_ALIGNED and rule.counting_unit in {"per_take", "per_day", "unknown"}:
        return SemanticsDecision(
            hard_block_allowed=True,
            massive_penalty_allowed=True,
            counting_unit=rule.counting_unit,
            probe_status="runtime_direct_metric_aligned",
            notes="direct runtime metric; no raw scorer import",
        )
    if rule.type in SOFT_ONLY:
        return SemanticsDecision(
            hard_block_allowed=False,
            massive_penalty_allowed=False,
            counting_unit=rule.counting_unit,
            probe_status="unverified_soft",
            notes="mandatory fallback/generalization type",
        )
    return SemanticsDecision(
        hard_block_allowed=False,
        massive_penalty_allowed=False,
        counting_unit=rule.counting_unit,
        probe_status="unverified_soft",
        notes="controller available; hard block downgraded until scorer micro-probe aligns",
    )


def gate_impact(rule: PTTRule, impact: ControllerImpact) -> ControllerImpact:
    semantics = decision_for_rule(rule)
    if impact.decision == "block" and not semantics.hard_block_allowed:
        impact.decision = "massive_penalty" if semantics.massive_penalty_allowed else "pass"
        impact.reason = f"{impact.reason}|semantics_downgraded"
    if impact.decision == "massive_penalty" and not semantics.massive_penalty_allowed:
        impact.decision = "pass"
        impact.marginal_penalty = round(min(impact.marginal_penalty, rule.penalty_scale() * 0.45), 2)
        impact.reason = f"{impact.reason}|semantics_soft_only"
    return impact
