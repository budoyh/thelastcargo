"""First-class preference repair candidates for CROWN-PCE."""

from __future__ import annotations

from . import config, preference_repair, safety
from .schemas import CandidateOption, World
from .time_utils import remaining_minutes


def _repair_trace(
    option: CandidateOption,
    *,
    kind: str,
    avoided_penalty: float,
    repair_value: float,
    lost_profit: float,
    deadline: str,
    feasibility: str,
    confidence: float,
) -> CandidateOption:
    option.trace.update(
        {
            "preference_repair": True,
            "repair_kind": kind,
            "avoided_penalty": round(float(avoided_penalty), 2),
            "expected_repair_value": round(float(repair_value), 2),
            "lost_profit": round(float(lost_profit), 2),
            "deadline": deadline,
            "feasibility": feasibility,
            "confidence": round(float(confidence), 4),
            "action_certificate_required": True,
            "redacted_rule_id": option.id.split(":", 2)[-1][:24],
        }
    )
    option.score_components["preference_repair_value"] = float(repair_value)
    option.score_components["lost_profit"] = -float(lost_profit)
    return option


def _rest_block(world: World, decision_id: str) -> CandidateOption | None:
    if not world.status.preferences:
        return None
    now = world.status.simulation_progress_minutes
    minute = now % 1440
    remaining = remaining_minutes(now, world.horizon.horizon_minutes)
    if remaining <= config.MIN_WAIT_MINUTES:
        return None
    rest_end = 8 * 60
    if minute >= rest_end:
        return None
    duration = min(rest_end - minute, remaining)
    option = CandidateOption(
        id=f"pce_repair:no_query_rest_block:{now}",
        action_type="wait",
        decision_id=decision_id,
        duration_minutes=int(duration),
        occupied_minutes=int(duration),
        finish_minutes=now + int(duration),
        direct_money=0.0,
    )
    return _repair_trace(
        option,
        kind="no_query_rest_block",
        avoided_penalty=min(4800.0, world.debt_market.debt_value + 1200.0),
        repair_value=min(4800.0, world.debt_market.debt_value + 1200.0),
        lost_profit=max(0.0, world.time_market.productive_time_shadow_price * duration),
        deadline="day_boundary",
        feasibility="feasible_without_query",
        confidence=0.72,
    )


def _full_offday_wait(world: World, decision_id: str) -> CandidateOption | None:
    if not world.status.preferences:
        return None
    now = world.status.simulation_progress_minutes
    day = now // 1440
    minute = now % 1440
    remaining = remaining_minutes(now, world.horizon.horizon_minutes)
    if remaining < 8 * 60:
        return None
    if day not in {6, 14, 22, 29} or minute > 60:
        return None
    duration = min(1440 - minute, remaining)
    option = CandidateOption(
        id=f"pce_repair:full_offday_wait:{day}",
        action_type="wait",
        decision_id=decision_id,
        duration_minutes=int(duration),
        occupied_minutes=int(duration),
        finish_minutes=now + int(duration),
        direct_money=0.0,
    )
    return _repair_trace(
        option,
        kind="full_offday_wait_to_boundary",
        avoided_penalty=10_000.0,
        repair_value=10_000.0,
        lost_profit=max(0.0, world.time_market.productive_time_shadow_price * duration),
        deadline="month_quota",
        feasibility="calendar_window_feasible",
        confidence=0.68,
    )


def build_repair_candidates(world: World, decision_id: str) -> list[CandidateOption]:
    if not config.ENABLE_PCE_REPAIR_FIRST:
        return []
    out: list[CandidateOption] = []
    for candidate in (_rest_block(world, decision_id), _full_offday_wait(world, decision_id)):
        if candidate is not None:
            out.append(candidate)
    target_candidate = preference_repair.build_repair_candidate(world, decision_id)
    if target_candidate is not None:
        target_candidate = _repair_trace(
            target_candidate,
            kind=str(target_candidate.trace.get("repair_kind", "reposition_to_runtime_target")),
            avoided_penalty=float(target_candidate.trace.get("expected_repair_value", 0.0) or 0.0),
            repair_value=float(target_candidate.trace.get("expected_repair_value", 0.0) or 0.0),
            lost_profit=abs(target_candidate.direct_money),
            deadline=str(target_candidate.trace.get("day_hint", "runtime_deadline")),
            feasibility="runtime_target_feasible",
            confidence=float(target_candidate.trace.get("urgency", 0.5) or 0.5),
        )
        out.append(target_candidate)
    for option in out:
        option.action_cert = safety._certificate_for(option, set())
    return out[:4]
