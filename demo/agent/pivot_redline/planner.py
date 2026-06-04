"""Independent Pivot-Redline runtime planner."""

from __future__ import annotations

from typing import Any

from .. import cargo_filter, safety, world as world_module
from ..schemas import CURRENT_ACTIONABLE, CandidateOption, World
from ..time_utils import day_index
from . import (
    b0_shadow,
    beam_rollout,
    candidate_bucket,
    macro_commitment,
    money_backbone,
    month_end_guard,
    online_probe,
    preference_state,
    query_optimizer,
    qwen_contract_ensemble,
    scoring_formula,
    trace_schema,
    value_model,
    world_adapter,
)
from .risk_model import PivotRiskModel


class PivotRedlinePlanner:
    """Runtime planner on the pivot-specific decision path."""

    def __init__(self, api: Any) -> None:
        self._api = api
        self._risk_model = PivotRiskModel()
        self._value_model = value_model.PivotValueModel()

    def decide(self, driver_id: str, runtime: Any, world0: World, decision_id: str) -> dict[str, Any]:
        money_clean = _variant() == "crown_pivot_redline_money_clean"
        weights = scoring_formula.PivotWeights.from_env(money_clean=money_clean)
        plan = query_optimizer.choose_query_plan(
            world0,
            money_clean=money_clean,
            noop_exact_b0=weights.all_new_weights_zero,
        )
        observed = world_adapter.query_here(self._api, driver_id, world0, plan.k)
        world_after_query = world_module.refresh_world(self._api, driver_id, memory=runtime.memory, prev_world=world0)
        query_minutes = world_after_query.status.simulation_progress_minutes - world0.status.simulation_progress_minutes
        visible = cargo_filter.normalize_and_filter(
            raw_cargos=observed,
            world=world_after_query,
            source_scope=CURRENT_ACTIONABLE,
            decision_id=decision_id,
        )
        runtime.memory.update_current_observation(world_after_query, visible, query_minutes)

        seed_options, _ = candidate_bucket.build_bucketed_candidates(world_after_query, visible, decision_id)
        observed_ids = {cargo.cargo_id for cargo in visible}
        seed_options = safety.pre_filter_and_attach_action_certificate(seed_options, world_after_query, observed_ids)
        b0_result = b0_shadow.score_b0_pure(seed_options, world_after_query, runtime.wait_lock)
        options, buckets = candidate_bucket.build_bucketed_candidates(
            world_after_query,
            visible,
            decision_id,
            b0_option=b0_result.option,
        )
        options = safety.pre_filter_and_attach_action_certificate(options, world_after_query, observed_ids)
        if not options:
            options = [b0_result.option]
        chosen = self._score_and_choose(
            options=options,
            visible=visible,
            world=world_after_query,
            query_minutes=query_minutes,
            weights=weights,
            b0_option=b0_result.option,
        )
        if not hasattr(runtime, "pivot_macro_stats"):
            runtime.pivot_macro_stats = macro_commitment.PivotMacroStats()
        macro_commitment.mark_if_macro(chosen, runtime.pivot_macro_stats)
        action = safety.finalize(chosen, world_after_query)
        action = trace_schema.attach_pivot_trace(
            action,
            world=world_after_query,
            query_plan=plan,
            visible=visible,
            chosen=chosen,
            options=options,
            query_minutes=query_minutes,
            observed_count=len(observed),
            b0_action=b0_result.option,
            b0_score=b0_result.score,
            bucket_counts=buckets.bucket_counts,
            weights=weights,
            macro_stats=runtime.pivot_macro_stats.payload(),
        )
        action["agent_trace"]["pivot_redline"]["qwen_contract_ensemble"] = qwen_contract_ensemble.stats_payload(world_after_query)
        runtime.prev_world = world_after_query
        runtime.wait_lock.record(
            str(action.get("action", "")),
            query_minutes,
            sum(1 for option in options if option.action_type == "take_order" and option.direct_money > 0),
            "pivot_redline",
            day=day_index(world_after_query.status.simulation_progress_minutes),
            wait_minutes=int((action.get("params") or {}).get("duration_minutes", 0) or 0),
        )
        return action

    def _score_and_choose(
        self,
        *,
        options: list[CandidateOption],
        visible: list[Any],
        world: World,
        query_minutes: int,
        weights: scoring_formula.PivotWeights,
        b0_option: CandidateOption,
    ) -> CandidateOption:
        if weights.all_new_weights_zero:
            b0_option.score = 0.0
            b0_option.score_components["pivot_noop_b0_oracle"] = 1.0
            return b0_option
        for option in options:
            components = {}
            components.update(money_backbone.components(option))
            components.update(preference_state.attach_preference_debt(option, world))
            risk = self._risk_model.score(option, world)
            components["pivot_risk_model"] = -risk.value
            components["pivot_terminal_value"] = self._value_model.terminal_value(option, visible)
            components["pivot_query_cost"] = -float(query_minutes)
            components["pivot_month_end_guard"] = -month_end_guard.penalty(option, world)
            components["pivot_online_probe_value"] = online_probe.probe_value(option)
            option.score_components.update(components)
            option.score = scoring_formula.weighted_score(option.score_components, weights)
        if weights.beam > 0 and weights.beam_width > 0:
            for option in options:
                bonus, node = beam_rollout.rollout_bonus(
                    option,
                    options,
                    visible,
                    depth=weights.beam_depth,
                    width=weights.beam_width,
                    value_model=self._value_model,
                )
                option.score_components["pivot_beam_rollout"] = bonus
                option.trace["pivot_beam_tree"] = _node_payload(node)
                option.score = scoring_formula.weighted_score(option.score_components, weights)
        return safety.choose_best_with_certificates(options, world)


def _node_payload(node: beam_rollout.BeamNode) -> dict[str, Any]:
    return {
        "candidate_id": node.candidate_id,
        "depth": node.depth,
        "local_score": round(float(node.local_score), 4),
        "continuation_score": round(float(node.continuation_score), 4),
        "child_count": len(node.children),
        "children": [_node_payload(child) for child in node.children[:4]],
    }


def _variant() -> str:
    from .. import config

    return config.RESCUE_VARIANT
