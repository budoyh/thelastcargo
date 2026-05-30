"""CROWN-Y Tournament Build decision service."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from simkit.ports import SimulationApiPort

from . import (
    candidate_generator,
    cargo_filter,
    endgame_planner,
    learned_ranker,
    llm_preference_judge,
    preference_monitor,
    query_policy,
    safety,
    time_bid_scorer,
    trace_writer,
    world as world_module,
)
from .llm_budget import LLMBudgetManager
from .memory import DriverMemory
from .schemas import CURRENT_ACTIONABLE, CandidateOption, NormalizedCargo, World


@dataclass
class DriverRuntime:
    memory: DriverMemory = field(default_factory=DriverMemory)
    prev_world: World | None = None
    decision_seq: int = 0


class ModelDecisionService:
    """Deterministic runtime agent using only the injected simulation API."""

    def __init__(self, api: SimulationApiPort) -> None:
        self._api = api
        self._logger = logging.getLogger("agent.crown_y")
        self._runtime_by_driver: dict[str, DriverRuntime] = {}
        self._llm_budget = LLMBudgetManager()

    def decide(self, driver_id: str) -> dict[str, Any]:
        runtime = self._runtime_by_driver.setdefault(driver_id, DriverRuntime())
        runtime.decision_seq += 1
        decision_id = f"{driver_id}:{runtime.decision_seq}"
        last_world = runtime.prev_world

        try:
            world0 = world_module.refresh_world(
                self._api,
                driver_id,
                memory=runtime.memory,
                prev_world=runtime.prev_world,
            )
            last_world = world0
            plan = query_policy.choose(world0)
            observed, world_after_query, query_minutes = self._execute_query_plan(driver_id, runtime, world0, plan, decision_id)
            last_world = world_after_query

            visible = cargo_filter.normalize_and_filter(
                raw_cargos=observed,
                world=world_after_query,
                source_scope=CURRENT_ACTIONABLE,
                decision_id=decision_id,
            )
            runtime.memory.update_current_observation(world_after_query, visible, query_minutes)

            options = candidate_generator.build_options(world_after_query, visible, decision_id)
            observed_ids = {cargo.cargo_id for cargo in visible}
            options = safety.pre_filter_and_attach_action_certificate(options, world_after_query, observed_ids)
            options = self._score_options(options, world_after_query, visible)
            if self._llm_budget.allow_judge(driver_id, world_after_query, options):
                options = llm_preference_judge.apply_limited(options, world_after_query)
                self._llm_budget.record_judge(driver_id, world_after_query)
            options = learned_ranker.adjust_if_enabled(options, world_after_query)
            options = endgame_planner.adjust(options, world_after_query)

            chosen = safety.choose_best_with_certificates(options, world_after_query)
            action = safety.finalize(chosen, world_after_query)
            action = trace_writer.attach_trace(
                action,
                world=world_after_query,
                query_plan=plan,
                visible_cargos=visible,
                chosen=chosen,
                options=options,
                query_minutes=query_minutes,
            )
            runtime.prev_world = world_after_query
            self._logger.info(
                "decision driver=%s seq=%s plan=%s observed=%s visible=%s chosen=%s action=%s",
                driver_id,
                runtime.decision_seq,
                plan.kind,
                len(observed),
                len(visible),
                chosen.id,
                action.get("action"),
            )
            return action
        except Exception as exc:  # pragma: no cover - exact exception types depend on the host API.
            self._logger.exception("decision fallback driver=%s seq=%s", driver_id, runtime.decision_seq)
            return trace_writer.attach_exception_trace(
                {"action": "wait", "params": {"duration_minutes": 1}},
                decision_id=decision_id,
                world=last_world,
                reason=exc.__class__.__name__,
            )

    def _execute_query_plan(
        self,
        driver_id: str,
        runtime: DriverRuntime,
        world0: World,
        plan: query_policy.QueryPlan,
        decision_id: str,
    ) -> tuple[list[dict[str, Any]], World, int]:
        observed: list[dict[str, Any]] = []
        world_current = world0
        start_minutes = world0.status.simulation_progress_minutes
        if plan.kind == "no_query":
            return observed, world_current, 0
        if plan.kind == "current_small_query":
            observed.extend(self._query_here(driver_id, world_current, plan.k))
            world_current = world_module.refresh_world(self._api, driver_id, memory=runtime.memory, prev_world=world_current)
            return observed, world_current, world_current.status.simulation_progress_minutes - start_minutes
        if plan.kind == "scout_then_deepen":
            observed.extend(self._query_here(driver_id, world_current, plan.scout_k))
            world_current = world_module.refresh_world(self._api, driver_id, memory=runtime.memory, prev_world=world_current)
            scout_visible = cargo_filter.fast_normalize_and_filter(observed, world_current, decision_id)
            if query_policy.should_deepen(world_current, scout_visible):
                observed.extend(self._query_here(driver_id, world_current, plan.deepen_k))
                world_current = world_module.refresh_world(self._api, driver_id, memory=runtime.memory, prev_world=world_current)
            return observed, world_current, world_current.status.simulation_progress_minutes - start_minutes
        if plan.kind == "current_large_query":
            observed.extend(self._query_here(driver_id, world_current, plan.k))
            world_current = world_module.refresh_world(self._api, driver_id, memory=runtime.memory, prev_world=world_current)
            return observed, world_current, world_current.status.simulation_progress_minutes - start_minutes
        return observed, world_current, 0

    def _query_here(self, driver_id: str, world_current: World, k: int) -> list[dict[str, Any]]:
        response = self._api.query_cargo(
            driver_id=driver_id,
            latitude=world_current.status.current_lat,
            longitude=world_current.status.current_lng,
            k=int(k),
        )
        items = response.get("items", [])
        return items if isinstance(items, list) else []

    def _score_options(
        self,
        options: list[CandidateOption],
        world_current: World,
        visible: list[NormalizedCargo],
    ) -> list[CandidateOption]:
        first_cut = sorted(
            options,
            key=lambda o: o.direct_money / max(1.0, o.occupied_minutes),
            reverse=True,
        )[: max(1, 80)]
        for option in first_cut:
            option.pref_cert = preference_monitor.certify(option, world_current)
            option.rollout = visible_rollout_value(option, world_current, visible)
        for option in first_cut:
            time_bid_scorer.score(option, world_current, first_cut)
        return first_cut


def visible_rollout_value(option: CandidateOption, world_current: World, visible: list[NormalizedCargo]):
    from . import visible_rollout

    return visible_rollout.evaluate(option, world_current, visible)
