"""CROWN-Y Tournament Build decision service."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from simkit.ports import SimulationApiPort

from . import (
    candidate_generator,
    cargo_filter,
    config,
    endgame_planner,
    learned_ranker,
    llm_preference_judge,
    micro_reposition,
    preference_repair,
    preference_monitor,
    query_policy,
    qwen_preference_compiler,
    rescue_scorer,
    safety,
    time_bid_scorer,
    trace_writer,
    world as world_module,
)
from .llm_budget import LLMBudgetManager
from .memory import DriverMemory
from .schemas import CURRENT_ACTIONABLE, CandidateOption, NormalizedCargo, World
from .time_utils import day_index, remaining_minutes
from .wait_lock import WaitLockState, query_k


@dataclass
class DriverRuntime:
    memory: DriverMemory = field(default_factory=DriverMemory)
    prev_world: World | None = None
    decision_seq: int = 0
    wait_lock: WaitLockState = field(default_factory=WaitLockState)


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
            if config.ENABLE_RESCUE_SCORER:
                action = self._decide_rescue(driver_id, runtime, world0, decision_id)
                runtime.prev_world = self._runtime_by_driver[driver_id].prev_world or world0
                return action
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
                observed_count=len(observed),
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

    def _decide_rescue(self, driver_id: str, runtime: DriverRuntime, world0: World, decision_id: str) -> dict[str, Any]:
        pre_rest_option, pre_rest_reason = self._rescue_rest_option(runtime, world0, decision_id)
        if config.ENABLE_NEXT_NO_QUERY_REST_BLOCK and pre_rest_option is not None:
            action = safety.finalize(pre_rest_option, world0)
            stats = rescue_scorer.RescueStats(0, 0, 0.0, 0.0, {})
            wait_forensic = rescue_scorer.wait_forensic(pre_rest_option, [pre_rest_option], stats, runtime.wait_lock)
            wait_forensic.update(
                {
                    "wait_reason": pre_rest_reason,
                    "why_not_take": "no_query_rest_block",
                    "why_not_reposition": "no_query_rest_block",
                    "contributes_continuous_rest": True,
                    "contributes_full_rest_day": pre_rest_reason == "periodic_full_rest_guard",
                    "contributes_market_timing": False,
                    "wait_lock_bug": False,
                    "no_query_rest_block_used": True,
                }
            )
            action = trace_writer.attach_trace(
                action,
                world=world0,
                query_plan=query_policy.QueryPlan(kind="no_query_rest_block", k=0, reason=config.RESCUE_VARIANT),
                visible_cargos=[],
                chosen=pre_rest_option,
                options=[pre_rest_option],
                query_minutes=0,
                observed_count=0,
                rescue={
                    "variant": config.RESCUE_VARIANT,
                    "wait_lock": runtime.wait_lock.snapshot(),
                    "query_k": 0,
                    "returned_count": 0,
                    "actionable_after_query": 0,
                    "positive_net_count": 0,
                    "missed_window_risk": 0,
                    "query_reward": 0.0,
                    "positive_count": 0,
                    "safe_positive_count": 0,
                    "best_order_net": 0.0,
                    "best_order_per_hour": 0.0,
                    "hard_block_reason_counts": {},
                    "filter_rejection_counts": {},
                    "wait_forensic": wait_forensic,
                    "qwen": qwen_preference_compiler.stats_payload(),
                },
            )
            runtime.prev_world = world0
            runtime.wait_lock.record(
                "wait",
                0,
                0,
                pre_rest_reason,
                day=day_index(world0.status.simulation_progress_minutes),
                wait_minutes=int((action.get("params") or {}).get("duration_minutes", 0) or 0),
            )
            return action
        k = query_k(runtime.wait_lock, world0)
        kind = "rescue_dynamic_query" if config.ENABLE_NEXT_DYNAMIC_QUERY_K and k else ("rescue_fixed_query" if k else "no_query")
        plan = query_policy.QueryPlan(kind=kind, k=k, reason=config.RESCUE_VARIANT)
        observed: list[dict[str, Any]] = []
        world_after_query = world0
        query_minutes = 0
        if k > 0:
            start_minutes = world0.status.simulation_progress_minutes
            observed.extend(self._query_here(driver_id, world0, k))
            world_after_query = world_module.refresh_world(self._api, driver_id, memory=runtime.memory, prev_world=world0)
            query_minutes = world_after_query.status.simulation_progress_minutes - start_minutes
        visible = cargo_filter.normalize_and_filter(
            raw_cargos=observed,
            world=world_after_query,
            source_scope=CURRENT_ACTIONABLE,
            decision_id=decision_id,
        )
        filter_rejections = cargo_filter.rejection_summary(decision_id)
        runtime.memory.update_current_observation(world_after_query, visible, query_minutes)
        options = candidate_generator.build_options(world_after_query, visible, decision_id)
        micro = micro_reposition.build_candidate(world_after_query, visible, decision_id, runtime.wait_lock)
        if micro is not None:
            options.append(micro)
        repair = preference_repair.build_repair_candidate(world_after_query, decision_id)
        if repair is not None:
            options.append(repair)
        observed_ids = {cargo.cargo_id for cargo in visible}
        options = safety.pre_filter_and_attach_action_certificate(options, world_after_query, observed_ids)
        options, rescue_stats = rescue_scorer.score_options(options, world_after_query, runtime.wait_lock)
        rest_option, rest_reason = self._rescue_rest_option(runtime, world_after_query, decision_id)
        chosen = rest_option if rest_option is not None else rescue_scorer.choose(options, rescue_stats, runtime.wait_lock)
        action = safety.finalize(chosen, world_after_query)
        wait_forensic = {}
        if action.get("action") == "wait":
            wait_forensic = rescue_scorer.wait_forensic(chosen, options, rescue_stats, runtime.wait_lock)
            if rest_reason:
                wait_forensic["wait_reason"] = rest_reason
                wait_forensic["why_not_take"] = "rest_guard_after_query"
                wait_forensic["why_not_reposition"] = "rest_guard_after_query"
                wait_forensic["contributes_continuous_rest"] = True
                wait_forensic["contributes_full_rest_day"] = rest_reason == "periodic_full_rest_guard"
                wait_forensic["contributes_market_timing"] = False
                wait_forensic["wait_lock_bug"] = False
                wait_forensic["why_wait_won"] = {
                    "rest_guard": rest_reason,
                    "safe_positive_count": rescue_stats.safe_positive_count,
                    "positive_count": rescue_stats.positive_count,
                    "consecutive_wait": runtime.wait_lock.consecutive_wait,
                }
            if filter_rejections:
                wait_forensic["filter_rejection_counts"] = dict(filter_rejections)
        hard_block_counts = dict(rescue_stats.hard_block_reason_counts)
        for reason, count in filter_rejections.items():
            hard_block_counts[f"filter_{reason}"] = hard_block_counts.get(f"filter_{reason}", 0) + count
        if wait_forensic:
            wait_forensic["hard_block_reason_counts"] = hard_block_counts
        action = trace_writer.attach_trace(
            action,
            world=world_after_query,
            query_plan=plan,
            visible_cargos=visible,
            chosen=chosen,
            options=options,
            query_minutes=query_minutes,
            observed_count=len(observed),
            rescue={
                "variant": config.RESCUE_VARIANT,
                "wait_lock": runtime.wait_lock.snapshot(),
                "query_k": k,
                "returned_count": len(observed),
                "actionable_after_query": len(visible),
                "positive_net_count": rescue_stats.positive_count,
                "missed_window_risk": int(filter_rejections.get("remove_slack_too_short", 0)) + int(filter_rejections.get("load_window_unreachable", 0)),
                "query_reward": round(float(rescue_stats.best_order_net) - float(query_minutes) * 1.5, 2),
                "positive_count": rescue_stats.positive_count,
                "safe_positive_count": rescue_stats.safe_positive_count,
                "best_order_net": rescue_stats.best_order_net,
                "best_order_per_hour": rescue_stats.best_order_per_hour,
                "hard_block_reason_counts": hard_block_counts,
                "filter_rejection_counts": dict(filter_rejections),
                "wait_forensic": wait_forensic,
                "qwen": qwen_preference_compiler.stats_payload(),
            },
        )
        runtime.prev_world = world_after_query
        runtime.wait_lock.record(
            str(action.get("action", "")),
            query_minutes,
            rescue_stats.safe_positive_count,
            wait_forensic.get("wait_reason", ""),
            day=day_index(world_after_query.status.simulation_progress_minutes),
            wait_minutes=int((action.get("params") or {}).get("duration_minutes", 0) or 0),
        )
        self._logger.info(
            "rescue decision driver=%s seq=%s variant=%s observed=%s visible=%s chosen=%s action=%s positive=%s safe_positive=%s",
            driver_id,
            runtime.decision_seq,
            config.RESCUE_VARIANT,
            len(observed),
            len(visible),
            chosen.id,
            action.get("action"),
            rescue_stats.positive_count,
            rescue_stats.safe_positive_count,
        )
        return action

    def _rescue_rest_option(self, runtime: DriverRuntime, world0: World, decision_id: str) -> tuple[CandidateOption | None, str]:
        if not config.ENABLE_RESCUE_REST_GUARD or not world0.status.preferences:
            return None, ""
        now = world0.status.simulation_progress_minutes
        day = day_index(now)
        minute_of_day = now % 1440
        remaining = remaining_minutes(now, world0.horizon.horizon_minutes)
        if remaining <= 0:
            return None, ""
        duration = 0
        reason = ""
        if config.RESCUE_FULL_REST_PERIOD_DAYS > 0 and (day + 1) % config.RESCUE_FULL_REST_PERIOD_DAYS == 0:
            duration = min(1440 - minute_of_day, remaining)
            reason = "periodic_full_rest_guard"
        elif minute_of_day < config.RESCUE_DAILY_REST_UNTIL_MINUTE:
            waited = runtime.wait_lock.day_wait_minutes.get(day, 0)
            needed = max(0, config.RESCUE_DAILY_REST_UNTIL_MINUTE - waited)
            duration = min(config.RESCUE_DAILY_REST_UNTIL_MINUTE - minute_of_day, needed, remaining)
            reason = "daily_rest_guard"
        if duration <= 0:
            return None, ""
        option = CandidateOption(
            id=f"rescue_rest:{reason}:{duration}",
            action_type="wait",
            decision_id=decision_id,
            duration_minutes=int(duration),
            occupied_minutes=int(duration),
            finish_minutes=now + int(duration),
            score=0.0,
        )
        option.score_components["rest_guard"] = 1.0
        option.action_cert = safety._certificate_for(option, set())
        return option, reason

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
