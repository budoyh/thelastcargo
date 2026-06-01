"""Macro repair commitment controller for PTT runtime repair tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import config, safety
from .geo import haversine_km
from .schemas import CandidateOption, World


@dataclass
class MacroCommitment:
    active_macro_id: str
    macro_type: str
    source_automaton_ids: tuple[str, ...]
    start_time: int
    deadline: int
    target_lat: float | None = None
    target_lng: float | None = None
    required_duration: int = 0
    completed_duration: int = 0
    next_required_action: str = "wait"
    expected_avoided_penalty: float = 0.0
    expected_lost_gross: float = 0.0
    confidence: float = 0.0

    def payload(self) -> dict[str, Any]:
        return {
            "active_macro_id": self.active_macro_id,
            "macro_type": self.macro_type,
            "source_automaton_ids": list(self.source_automaton_ids),
            "start_time": self.start_time,
            "deadline": self.deadline,
            "target_or_position_hash": _target_hash(self.target_lat, self.target_lng),
            "required_duration": self.required_duration,
            "completed_duration": self.completed_duration,
            "next_required_action": self.next_required_action,
            "expected_avoided_penalty": round(self.expected_avoided_penalty, 2),
            "expected_lost_gross": round(self.expected_lost_gross, 2),
            "confidence": round(self.confidence, 4),
        }


@dataclass
class MacroStats:
    macro_started_count: int = 0
    macro_completed_count: int = 0
    macro_aborted_count: int = 0
    macro_broken_by_query_count: int = 0
    query_skipped_due_to_macro: int = 0
    official_delta_measured_macro_gain: float = 0.0

    def payload(self) -> dict[str, Any]:
        return {
            "macro_started_count": self.macro_started_count,
            "macro_completed_count": self.macro_completed_count,
            "macro_aborted_count": self.macro_aborted_count,
            "macro_broken_by_query_count": self.macro_broken_by_query_count,
            "query_skipped_due_to_macro": self.query_skipped_due_to_macro,
            "official_delta_measured_macro_gain": round(self.official_delta_measured_macro_gain, 2),
        }


def _target_hash(lat: float | None, lng: float | None) -> str:
    if lat is None or lng is None:
        return ""
    import hashlib

    return hashlib.sha256(f"{lat:.6f},{lng:.6f}".encode("utf-8")).hexdigest()[:12]


def mark_macro_candidate(
    option: CandidateOption,
    *,
    macro_type: str,
    source_automaton_ids: tuple[str, ...] = (),
    avoided_penalty: float = 0.0,
    repair_value: float = 0.0,
    lost_gross: float = 0.0,
    deadline_minutes: int | None = None,
    feasibility: str = "runtime_feasible",
    confidence: float = 0.5,
    required_duration: int = 0,
    permits_query: bool = False,
) -> CandidateOption:
    deadline = deadline_minutes if deadline_minutes is not None else option.finish_minutes
    option.trace.update(
        {
            "macro_candidate": True,
            "macro_type": macro_type,
            "source_automaton_ids": list(source_automaton_ids),
            "avoided_penalty": round(float(avoided_penalty), 2),
            "repair_value": round(float(repair_value), 2),
            "lost_gross": round(float(lost_gross), 2),
            "deadline": deadline,
            "feasibility": feasibility,
            "confidence": round(float(confidence), 4),
            "required_duration": int(required_duration),
            "permits_query": bool(permits_query),
            "action_certificate_required": True,
        }
    )
    option.score_components["macro_task_repair_value"] = float(repair_value) * max(0.0, min(1.0, confidence))
    return option


def is_macro_candidate(option: CandidateOption) -> bool:
    return bool(option.trace.get("macro_candidate") or option.trace.get("preference_repair"))


def _float_trace(option: CandidateOption, name: str, default: float = 0.0) -> float:
    try:
        return float(option.trace.get(name, default) or default)
    except (TypeError, ValueError):
        return default


def _source_ids(option: CandidateOption) -> tuple[str, ...]:
    raw = option.trace.get("source_automaton_ids") or option.trace.get("rule_id") or ()
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, list):
        return tuple(str(item) for item in raw)
    return tuple()


def record_selection(
    active: MacroCommitment | None,
    stats: MacroStats,
    option: CandidateOption,
    world: World,
) -> MacroCommitment | None:
    if not is_macro_candidate(option):
        return active
    macro_type = str(option.trace.get("macro_type") or option.trace.get("repair_kind") or option.action_type)
    stats.macro_started_count += 1
    if option.action_type == "wait":
        stats.macro_completed_count += 1
        if not bool(option.trace.get("permits_query")):
            stats.query_skipped_due_to_macro += 1
        return None
    if option.action_type != "reposition":
        return active
    if option.deadhead_km > 120.0:
        stats.macro_aborted_count += 1
        return active
    required = int(_float_trace(option, "required_duration", 120.0))
    if required <= 0:
        required = 120
    deadline_raw = option.trace.get("deadline", option.finish_minutes + required)
    try:
        deadline = int(deadline_raw)
    except (TypeError, ValueError):
        deadline = option.finish_minutes + required
    return MacroCommitment(
        active_macro_id=option.id,
        macro_type=macro_type,
        source_automaton_ids=_source_ids(option),
        start_time=world.status.simulation_progress_minutes,
        deadline=max(deadline, option.finish_minutes + required),
        target_lat=option.target_lat,
        target_lng=option.target_lng,
        required_duration=required,
        completed_duration=0,
        next_required_action="wait_at_target",
        expected_avoided_penalty=_float_trace(option, "avoided_penalty", _float_trace(option, "expected_repair_value")),
        expected_lost_gross=_float_trace(option, "lost_gross", abs(option.direct_money)),
        confidence=_float_trace(option, "confidence", 0.5),
    )


def next_committed_option(
    active: MacroCommitment | None,
    stats: MacroStats,
    world: World,
    decision_id: str,
) -> tuple[CandidateOption | None, MacroCommitment | None]:
    if active is None:
        return None, None
    now = world.status.simulation_progress_minutes
    if now > active.deadline or world.endgame.remaining_minutes <= config.MIN_WAIT_MINUTES:
        stats.macro_aborted_count += 1
        return None, None
    if active.target_lat is not None and active.target_lng is not None:
        distance = haversine_km(world.status.current_lat, world.status.current_lng, active.target_lat, active.target_lng)
        if distance > 120.0:
            stats.macro_aborted_count += 1
            return None, None
        if distance > 5.0:
            duration = max(1, int(distance / config.REPOSITION_SPEED_KM_PER_HOUR * 60.0 + 0.999999))
            if now + duration > world.horizon.horizon_minutes:
                stats.macro_aborted_count += 1
                return None, None
            option = CandidateOption(
                id=f"active_macro_reposition:{active.active_macro_id}",
                action_type="reposition",
                decision_id=decision_id,
                target_lat=float(active.target_lat),
                target_lng=float(active.target_lng),
                direct_money=-(distance * config.DEFAULT_COST_PER_KM),
                occupied_minutes=duration,
                deadhead_km=distance,
                finish_minutes=now + duration,
                score=active.expected_avoided_penalty * active.confidence - distance * config.DEFAULT_COST_PER_KM,
            )
            mark_macro_candidate(
                option,
                macro_type=active.macro_type,
                source_automaton_ids=active.source_automaton_ids,
                avoided_penalty=active.expected_avoided_penalty,
                repair_value=active.expected_avoided_penalty,
                lost_gross=active.expected_lost_gross,
                deadline_minutes=active.deadline,
                feasibility="active_macro_reposition",
                confidence=active.confidence,
                required_duration=active.required_duration,
            )
            option.action_cert = safety._certificate_for(option, set())
            stats.query_skipped_due_to_macro += 1
            return option, active
    duration = min(
        max(config.MIN_WAIT_MINUTES, active.required_duration - active.completed_duration),
        world.endgame.remaining_minutes,
    )
    if duration <= 0:
        stats.macro_completed_count += 1
        return None, None
    option = CandidateOption(
        id=f"active_macro_wait:{active.active_macro_id}:{duration}",
        action_type="wait",
        decision_id=decision_id,
        duration_minutes=int(duration),
        occupied_minutes=int(duration),
        finish_minutes=now + int(duration),
        score=active.expected_avoided_penalty * active.confidence,
    )
    mark_macro_candidate(
        option,
        macro_type="wait_at_target" if active.target_lat is not None else active.macro_type,
        source_automaton_ids=active.source_automaton_ids,
        avoided_penalty=active.expected_avoided_penalty,
        repair_value=active.expected_avoided_penalty,
        lost_gross=active.expected_lost_gross,
        deadline_minutes=active.deadline,
        feasibility="active_macro_wait_without_query",
        confidence=active.confidence,
        required_duration=int(duration),
    )
    option.action_cert = safety._certificate_for(option, set())
    stats.query_skipped_due_to_macro += 1
    stats.macro_completed_count += 1
    return option, None
