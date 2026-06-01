"""Deterministic PTT controllers used by the runtime Preference Firewall."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import config, macro_commitment
from .geo import haversine_km
from .observed_vocab_linker import ObservedVocabLink
from .ptt_types import PTT_TYPES, PTTRule
from .schemas import CandidateOption, World
from .time_utils import day_index, remaining_minutes


@dataclass
class ControllerImpact:
    rule_id: str
    controller_type: str
    marginal_penalty: float
    repair_value: float
    lost_repair_window_cost: float
    future_failure_probability_delta: float
    confidence: float
    effect: str
    decision: str
    reason: str


class PreferenceController:
    def __init__(self, rule: PTTRule) -> None:
        self.rule = rule
        self._progress: dict[str, Any] = {}
        self.scored_candidate_count = 0

    @property
    def controller_type(self) -> str:
        return self.rule.type

    def update(self, world: World) -> None:
        now = world.status.simulation_progress_minutes
        self._progress = {
            "day_index": day_index(now),
            "minute_of_day": now % 1440,
            "completed_orders": world.status.completed_order_count,
            "remaining_minutes": remaining_minutes(now, world.horizon.horizon_minutes),
        }

    def progress(self) -> dict[str, Any]:
        return dict(self._progress)

    def satisfied(self) -> bool:
        return False

    def failed(self) -> bool:
        return False

    def remaining_slack(self, world: World) -> float:
        return float(remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes))

    def marginal_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> ControllerImpact:
        self.scored_candidate_count += 1
        return _impact(self.rule, option, effect="neutral")

    def marginal_penalty(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...] = tuple()) -> float:
        return self.marginal_cost(option, world, links).marginal_penalty

    def repair_value(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> float:
        return self.marginal_cost(option, world, links).repair_value

    def lost_window_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...] = tuple()) -> float:
        return self.marginal_cost(option, world, links).lost_repair_window_cost

    def generate_repair_candidates(self, world: World, visible_cargos: list[Any], decision_id: str) -> list[CandidateOption]:
        return []

    def dynamic_lambda(self, world: World) -> float:
        slack = max(1.0, self.remaining_slack(world))
        pressure = 1.0 + max(0.0, 1.0 - slack / max(1.0, world.horizon.horizon_minutes))
        return self.rule.penalty_scale() * max(0.1, self.rule.confidence) * pressure

    def final_penalty_lower_bound(self, world: World) -> float:
        return 0.0 if self.satisfied() else self.rule.penalty_scale() * 0.2


class TimeWindowController(PreferenceController):
    def marginal_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> ControllerImpact:
        self.scored_candidate_count += 1
        if option.action_type == "wait":
            repair = min(self.rule.penalty_scale(), max(0, option.duration_minutes) / 480.0 * self.rule.penalty_scale())
            return _impact(self.rule, option, repair=repair, effect="repairs", decision="pass", reason="wait_repairs_rest_window")
        if option.action_type in {"take_order", "reposition"}:
            overlap = _protected_overlap(world.status.simulation_progress_minutes, option.finish_minutes, self.rule)
            if overlap > 0:
                penalty = min(self.rule.penalty_scale(), overlap / 120.0 * self.rule.penalty_scale())
                return _impact(self.rule, option, penalty=penalty, lost=penalty * 0.25, effect="violates", reason="protected_window_overlap")
            if option.occupied_minutes >= 480:
                penalty = self.rule.penalty_scale() * 0.15
                return _impact(self.rule, option, penalty=penalty, lost=penalty * 0.4, effect="reduces_repairability", reason="long_action_reduces_rest_slack")
        return _impact(self.rule, option, effect="neutral")

    def generate_repair_candidates(self, world: World, visible_cargos: list[Any], decision_id: str) -> list[CandidateOption]:
        minute = world.status.simulation_progress_minutes % 1440
        duration_cap = min(self.rule.duration_minutes or 360, 480)
        if self.rule.type == "daily_continuous_rest":
            if minute >= config.RESCUE_DAILY_REST_UNTIL_MINUTE:
                return []
            duration_cap = min(duration_cap, max(0, config.RESCUE_DAILY_REST_UNTIL_MINUTE - minute))
        if self.rule.type == "scheduled_quiet_window" and self.rule.time_window is not None:
            start, end = self.rule.time_window
            in_window = start <= minute < end if end >= start else (minute >= start or minute < end)
            if not in_window:
                return []
        remaining = remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)
        duration = min(max(duration_cap, 180), remaining)
        if duration <= 0:
            return []
        option = CandidateOption(
            id=f"ptt_rest:{self.rule.rule_id}:{duration}",
            action_type="wait",
            decision_id=decision_id,
            duration_minutes=int(duration),
            occupied_minutes=int(duration),
            finish_minutes=world.status.simulation_progress_minutes + int(duration),
            score=0.0,
        )
        macro_commitment.mark_macro_candidate(
            option,
            macro_type="daily_rest_commitment" if self.rule.type == "daily_continuous_rest" else "scheduled_quiet_commitment",
            avoided_penalty=self.rule.penalty_scale(),
            repair_value=self.rule.penalty_scale() * max(0.4, self.rule.confidence),
            lost_gross=0.0,
            deadline_minutes=option.finish_minutes,
            feasibility="no_query_wait_block",
            confidence=max(0.4, self.rule.confidence),
            required_duration=int(duration),
            permits_query=False,
        )
        option.trace["ptt_repair_candidate"] = True
        return [option]


class DayQuotaController(TimeWindowController):
    def marginal_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> ControllerImpact:
        self.scored_candidate_count += 1
        if option.action_type == "wait" and option.duration_minutes >= 480:
            return _impact(self.rule, option, repair=self.rule.penalty_scale() * 0.65, effect="repairs", decision="pass", reason="wait_repairs_day_quota")
        if option.action_type == "take_order":
            pressure = 0.10 if option.occupied_minutes >= 600 else 0.04
            penalty = self.rule.penalty_scale() * pressure
            return _impact(self.rule, option, penalty=penalty, lost=penalty * 0.35, effect="reduces_repairability", decision="qwen_audit_required", reason="take_softly_consumes_quota_day")
        if option.action_type == "reposition" and self.rule.type == "full_inactive_day_quota":
            penalty = self.rule.penalty_scale() * 0.03
            return _impact(self.rule, option, penalty=penalty, effect="reduces_repairability", reason="reposition_consumes_inactive_day")
        return _impact(self.rule, option, effect="neutral")

    def generate_repair_candidates(self, world: World, visible_cargos: list[Any], decision_id: str) -> list[CandidateOption]:
        return []


class AttributeController(PreferenceController):
    def marginal_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> ControllerImpact:
        self.scored_candidate_count += 1
        if option.action_type != "take_order" or option.cargo is None:
            return _impact(self.rule, option, effect="neutral")
        best = _matching_link(option, {self.rule.rule_id, self.rule.source_rule_id}, links)
        if best is None:
            if self.rule.type in {"required_cargo_attribute_distinct_days", "runtime_entity_task"}:
                if option.occupied_minutes >= 240:
                    penalty = self.rule.penalty_scale() * 0.16
                    return _impact(
                        self.rule,
                        option,
                        penalty=penalty,
                        lost=penalty * 1.5,
                        effect="reduces_repairability",
                        decision="qwen_audit_required",
                        reason="required_attribute_repair_window_unknown",
                    )
                return _impact(self.rule, option, effect="unknown", decision="qwen_audit_required", reason="required_attribute_match_unknown")
            if self.rule.type in {"forbidden_cargo_attribute", "region_avoid_or_require"}:
                risk = self.rule.penalty_scale() * 0.12 * max(0.3, 1.0 - self.rule.confidence)
                return _impact(self.rule, option, penalty=risk, effect="unknown", decision="qwen_audit_required", reason="attribute_match_unknown")
            return _impact(self.rule, option, effect="neutral")
        if self.rule.type in {"required_cargo_attribute_distinct_days", "runtime_entity_task"} or best.relation == "repair":
            repair = self.rule.penalty_scale() * max(best.confidence, self.rule.confidence)
            return _impact(self.rule, option, repair=repair, effect="repairs", decision="pass", reason="required_attribute_match")
        penalty = self.rule.penalty_scale() * max(best.confidence, self.rule.confidence)
        return _impact(self.rule, option, penalty=penalty, effect="violates", reason="forbidden_attribute_match")

    def generate_repair_candidates(self, world: World, visible_cargos: list[Any], decision_id: str) -> list[CandidateOption]:
        if self.rule.type not in {"required_cargo_attribute_distinct_days", "runtime_entity_task"}:
            return []
        for cargo in visible_cargos:
            option = CandidateOption(
                id=f"ptt_required_take:{self.rule.rule_id}",
                action_type="take_order",
                decision_id=decision_id,
                cargo=cargo,
                direct_money=float(getattr(cargo, "price_yuan", 0.0) or 0.0),
                occupied_minutes=int(getattr(cargo, "cost_time_minutes", 0) or 0),
                deadhead_km=float(getattr(cargo, "pickup_distance_km", 0.0) or 0.0),
                haul_km=float(getattr(cargo, "haul_distance_km", 0.0) or 0.0),
                finish_minutes=world.status.simulation_progress_minutes + int(getattr(cargo, "cost_time_minutes", 0) or 0),
                score=0.0,
            )
            macro_commitment.mark_macro_candidate(
                option,
                macro_type="required_matching_take",
                source_automaton_ids=(self.rule.rule_id,),
                avoided_penalty=self.rule.penalty_scale(),
                repair_value=self.rule.penalty_scale() * max(0.45, self.rule.confidence),
                lost_gross=0.0,
                deadline_minutes=option.finish_minutes,
                feasibility="current_actionable_required_match_candidate",
                confidence=max(0.45, self.rule.confidence),
                required_duration=option.occupied_minutes,
                permits_query=False,
            )
            option.trace["ptt_repair_candidate"] = True
            return [option]
        return []


class DistanceController(PreferenceController):
    def marginal_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> ControllerImpact:
        self.scored_candidate_count += 1
        if option.action_type != "take_order":
            return _impact(self.rule, option, effect="neutral")
        threshold = self.rule.distance_km
        if threshold is None:
            threshold = 55.0 if self.rule.type == "pickup_deadhead_limit" else 180.0
        observed = option.deadhead_km
        if self.rule.type == "haul_distance_limit":
            observed = option.haul_km
        if self.rule.type == "cumulative_deadhead_budget":
            observed = option.deadhead_km + float(self._progress.get("completed_orders", 0)) * 8.0
        if observed > threshold:
            over = max(0.0, observed - threshold)
            penalty = min(self.rule.penalty_scale() * 2.0, self.rule.penalty_scale() * (0.65 + over / max(1.0, threshold)))
            return _impact(self.rule, option, penalty=penalty, effect="violates", reason="distance_limit_exceeded")
        return _impact(self.rule, option, repair=self.rule.penalty_scale() * 0.04, effect="neutral", decision="pass", reason="distance_within_limit")

    def generate_repair_candidates(self, world: World, visible_cargos: list[Any], decision_id: str) -> list[CandidateOption]:
        return []


class CountDeadlineController(PreferenceController):
    def marginal_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> ControllerImpact:
        self.scored_candidate_count += 1
        if self.rule.type == "daily_order_count_limit" and option.action_type == "take_order":
            limit = self.rule.count or 6
            count_today = int(world.ledger.action_counts.get("take_order", 0))
            if count_today >= limit:
                return _impact(self.rule, option, penalty=self.rule.penalty_scale(), effect="violates", reason="daily_count_limit_exceeded")
        if self.rule.type == "first_order_start_deadline":
            deadline = self.rule.deadline or 10 * 60
            minute = world.status.simulation_progress_minutes % 1440
            if option.action_type == "take_order" and minute <= deadline:
                return _impact(self.rule, option, repair=self.rule.penalty_scale() * 0.6, effect="repairs", decision="pass", reason="early_take_repairs_deadline")
            if option.action_type == "wait" and minute + option.duration_minutes > deadline:
                return _impact(self.rule, option, penalty=self.rule.penalty_scale() * 0.7, lost=self.rule.penalty_scale() * 0.4, effect="reduces_repairability", reason="wait_misses_first_order_deadline")
        if self.rule.type == "daily_work_pattern":
            if option.action_type == "wait" and option.duration_minutes >= 120:
                return _impact(self.rule, option, repair=self.rule.penalty_scale() * 0.35, effect="repairs", decision="pass", reason="wait_repairs_work_pattern")
            if option.action_type == "take_order" and option.occupied_minutes >= 360:
                penalty = self.rule.penalty_scale() * 0.28
                return _impact(self.rule, option, penalty=penalty, lost=penalty * 0.5, effect="reduces_repairability", decision="qwen_audit_required", reason="long_take_risks_work_pattern")
        return _impact(self.rule, option, effect="neutral")


class LocationTaskController(PreferenceController):
    def marginal_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> ControllerImpact:
        self.scored_candidate_count += 1
        if option.action_type == "wait" and self.rule.type in {"location_visit_or_dwell", "stay_target_window"}:
            return _impact(self.rule, option, repair=self.rule.penalty_scale() * min(0.5, option.duration_minutes / 240.0), effect="repairs", decision="pass", reason="wait_may_satisfy_dwell")
        if option.action_type in {"take_order", "reposition"}:
            target = _target_from_rule_or_visible(self.rule, option)
            if target is None:
                risk = self.rule.penalty_scale() * 0.15
                return _impact(self.rule, option, penalty=risk, effect="unknown", decision="qwen_audit_required", reason="location_target_unresolved")
            points = []
            if option.cargo is not None:
                points.extend([(option.cargo.start_lat, option.cargo.start_lng), (option.cargo.end_lat, option.cargo.end_lng)])
            if option.target_lat is not None and option.target_lng is not None:
                points.append((option.target_lat, option.target_lng))
            nearest = min((haversine_km(a, b, target[0], target[1]) for a, b in points), default=9999.0)
            if nearest <= 12.0:
                return _impact(self.rule, option, repair=self.rule.penalty_scale() * 0.75, effect="repairs", decision="pass", reason="moves_towards_runtime_target")
            if option.occupied_minutes >= 480:
                return _impact(self.rule, option, penalty=self.rule.penalty_scale() * 0.35, lost=self.rule.penalty_scale() * 0.35, effect="reduces_repairability", reason="long_action_reduces_target_slack")
        return _impact(self.rule, option, effect="neutral")

    def generate_repair_candidates(self, world: World, visible_cargos: list[Any], decision_id: str) -> list[CandidateOption]:
        target = _target_from_rule_or_visible(self.rule, None)
        if target is None:
            return []
        distance = haversine_km(world.status.current_lat, world.status.current_lng, target[0], target[1])
        if distance <= 5.0:
            duration = min(240, max(30, remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)))
            option = CandidateOption(
                id=f"ptt_wait_at_target:{self.rule.rule_id}",
                action_type="wait",
                decision_id=decision_id,
                duration_minutes=duration,
                occupied_minutes=duration,
                finish_minutes=world.status.simulation_progress_minutes + duration,
                score=0.0,
            )
            macro_type = "wait_at_target"
        else:
            duration = max(1, int(distance / 60.0 * 60.0 + 0.999999))
            option = CandidateOption(
                id=f"ptt_preference_reposition:{self.rule.rule_id}",
                action_type="reposition",
                decision_id=decision_id,
                target_lat=target[0],
                target_lng=target[1],
                direct_money=-(distance * 1.5),
                occupied_minutes=duration,
                deadhead_km=distance,
                finish_minutes=world.status.simulation_progress_minutes + duration,
                score=0.0,
            )
            macro_type = "preference_reposition" if self.rule.type != "ordered_multi_stop_task" else "ordered_sequence"
        macro_commitment.mark_macro_candidate(
            option,
            macro_type=macro_type,
            source_automaton_ids=(self.rule.rule_id,),
            avoided_penalty=self.rule.penalty_scale(),
            repair_value=self.rule.penalty_scale() * max(0.45, self.rule.confidence),
            lost_gross=abs(option.direct_money),
            deadline_minutes=option.finish_minutes,
            feasibility="runtime_target_repair",
            confidence=max(0.45, self.rule.confidence),
            required_duration=duration,
            permits_query=False,
        )
        option.trace["ptt_repair_candidate"] = True
        return [option]


class UnknownSoftController(PreferenceController):
    def marginal_cost(self, option: CandidateOption, world: World, links: tuple[ObservedVocabLink, ...]) -> ControllerImpact:
        self.scored_candidate_count += 1
        if option.action_type == "take_order" and option.occupied_minutes >= 540:
            penalty = max(120.0, self.rule.penalty_scale() * 0.18)
            return _impact(self.rule, option, penalty=penalty, lost=penalty * 0.25, effect="unknown", decision="qwen_audit_required", reason="unknown_soft_long_action_risk")
        return _impact(self.rule, option, penalty=self.rule.penalty_scale() * 0.04, effect="unknown", decision="pass", reason="unknown_soft_small_risk")


def build_controllers(rules: tuple[PTTRule, ...], world: World) -> list[PreferenceController]:
    controllers: list[PreferenceController] = []
    for rule in rules:
        cls: type[PreferenceController]
        if rule.type in {"daily_continuous_rest", "scheduled_quiet_window"}:
            cls = TimeWindowController
        elif rule.type in {"full_inactive_day_quota", "no_order_day_quota"}:
            cls = DayQuotaController
        elif rule.type in {"forbidden_cargo_attribute", "required_cargo_attribute_distinct_days", "region_avoid_or_require", "runtime_entity_task"}:
            cls = AttributeController
        elif rule.type in {"pickup_deadhead_limit", "haul_distance_limit", "cumulative_deadhead_budget"}:
            cls = DistanceController
        elif rule.type in {"daily_order_count_limit", "first_order_start_deadline", "daily_work_pattern"}:
            cls = CountDeadlineController
        elif rule.type in {"location_visit_or_dwell", "ordered_multi_stop_task", "stay_target_window"}:
            cls = LocationTaskController
        else:
            cls = UnknownSoftController
        controller = cls(rule)
        controller.update(world)
        controllers.append(controller)
    present = {controller.controller_type for controller in controllers}
    for rule_type in PTT_TYPES:
        if rule_type not in present:
            continue
    return controllers


def _impact(
    rule: PTTRule,
    option: CandidateOption,
    *,
    penalty: float = 0.0,
    repair: float = 0.0,
    lost: float = 0.0,
    effect: str,
    decision: str = "",
    reason: str = "",
) -> ControllerImpact:
    if not decision:
        if effect == "violates" and penalty >= rule.penalty_scale() * 0.55 and rule.confidence >= 0.55:
            decision = "massive_penalty"
        else:
            decision = "pass"
    return ControllerImpact(
        rule_id=rule.rule_id,
        controller_type=rule.type,
        marginal_penalty=round(max(0.0, penalty), 2),
        repair_value=round(max(0.0, repair), 2),
        lost_repair_window_cost=round(max(0.0, lost), 2),
        future_failure_probability_delta=round(min(1.0, max(0.0, (penalty + lost) / max(1.0, rule.penalty_scale() * 2.0))), 4),
        confidence=round(max(0.0, min(1.0, rule.confidence)), 4),
        effect=effect,
        decision=decision,
        reason=reason,
    )


def _protected_overlap(start: int, finish: int, rule: PTTRule) -> int:
    if finish <= start:
        return 0
    if rule.time_window is not None:
        a, b = rule.time_window
        total = 0
        for day in range(start // 1440, finish // 1440 + 1):
            ws = day * 1440 + a
            we = day * 1440 + b if b >= a else (day + 1) * 1440 + b
            total += max(0, min(finish, we) - max(start, ws))
        return total
    rest_end = max(360, min(720, rule.duration_minutes or 480))
    total = 0
    for day in range(start // 1440, finish // 1440 + 1):
        total += max(0, min(finish, day * 1440 + rest_end) - max(start, day * 1440))
    return total


def _matching_link(option: CandidateOption, rule_ids: set[str], links: tuple[ObservedVocabLink, ...]) -> ObservedVocabLink | None:
    if option.cargo is None:
        return None
    for link in links:
        if link.rule_id not in rule_ids:
            continue
        value = str(getattr(option.cargo, link.field, "") or "")
        if value and value == link.value:
            return link
    return None


def _target_from_rule_or_visible(rule: PTTRule, option: CandidateOption | None) -> tuple[float, float] | None:
    raw = rule.slots.get("target_coordinates") or rule.slots.get("coordinate_target")
    if isinstance(raw, dict):
        try:
            return float(raw["lat"]), float(raw["lng"])
        except (KeyError, TypeError, ValueError):
            return None
    if option is None:
        return None
    if option.target_lat is not None and option.target_lng is not None:
        return option.target_lat, option.target_lng
    return None
