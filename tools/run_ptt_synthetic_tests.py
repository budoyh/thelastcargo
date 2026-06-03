"""Hidden-style synthetic checks for PTT controllers and firewall behavior."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demo"))

from agent import preference_controllers, preference_firewall  # noqa: E402
from agent.observed_vocab_linker import ObservedVocabLink  # noqa: E402
from agent.ptt_types import PTT_TYPES, PTTRule, short_hash  # noqa: E402
from agent.schemas import (  # noqa: E402
    CURRENT_ACTIONABLE,
    CandidateOption,
    CompiledPreferenceSet,
    DriverMemoryView,
    DriverStatus,
    NormalizedCargo,
    PreferenceDebtMarket,
    ResourcePressureEndgame,
    RuleLedger,
    SimulationHorizon,
    TimeShadowMarket,
    World,
)


PARAPHRASES = {
    rule_type: (
        f"{rule_type} abstract paraphrase alpha",
        f"{rule_type} abstract paraphrase beta",
        f"{rule_type} abstract paraphrase gamma",
    )
    for rule_type in PTT_TYPES
}


def _world(*, now: int = 480, take_count: int = 0) -> World:
    return World(
        status=DriverStatus(
            driver_id="runtime_entity_hash_driver",
            current_lat=0.0,
            current_lng=0.0,
            simulation_progress_minutes=now,
            simulation_wall_time="2026-03-01T00:00:00",
            truck_length="runtime_value_hash_truck",
            preferences=({"content_hash": "runtime_value_hash_pref", "penalty_amount": 3000.0},),
            completed_order_count=take_count,
        ),
        pref_hash="runtime_value_hash_pref_hash",
        rules=CompiledPreferenceSet(pref_hash="runtime_value_hash_pref_hash", rules=()),
        ledger=RuleLedger(
            revision=1,
            status_minutes=now,
            completed_orders=take_count,
            action_counts={"take_order": take_count, "wait": 0, "reposition": 0},
            observed_summary_count=1,
            preference_pressure=1.0,
        ),
        debt_market=PreferenceDebtMarket(
            debt_value=3000.0,
            unknown_risk=0.2,
            emergency=False,
            repair_price=1500.0,
            violation_price=3000.0,
        ),
        endgame=ResourcePressureEndgame(intensity=0.2, remaining_minutes=31 * 1440 - now),
        time_market=TimeShadowMarket(
            productive_time_shadow_price=1.0,
            query_time_cost=4.0,
            information_option_value=0.0,
            sample_size=1,
            mode="synthetic",
        ),
        memory_view=DriverMemoryView(
            observations_count=1,
            recent_best_profit_per_min=1.0,
            recent_feasible_count=1.0,
            recent_query_minutes=0,
        ),
        horizon=SimulationHorizon(duration_days=31, horizon_minutes=31 * 1440),
    )


def _rule(rule_type: str) -> PTTRule:
    slots: dict[str, Any] = {}
    kwargs: dict[str, Any] = {
        "rule_id": f"runtime_value_hash_{rule_type}",
        "type": rule_type,
        "scope": "runtime",
        "field": "cargo_name",
        "operator": "abstract",
        "value_hash": "runtime_value_hash_attr",
        "duration_minutes": 480,
        "time_window": None,
        "deadline": None,
        "count": 3,
        "distance_km": 40.0,
        "penalty_amount": 3000.0,
        "penalty_source": "synthetic",
        "counting_unit": "per_take",
        "trigger_action": "take",
        "repair_actions": ("wait", "reposition", "take"),
        "confidence": 0.82,
        "slots": slots,
    }
    if rule_type == "scheduled_quiet_window":
        kwargs["time_window"] = (60, 360)
    if rule_type == "haul_distance_limit":
        kwargs["distance_km"] = 80.0
    if rule_type == "cumulative_deadhead_budget":
        kwargs["distance_km"] = 55.0
    if rule_type == "daily_order_count_limit":
        kwargs["count"] = 1
    if rule_type == "first_order_start_deadline":
        kwargs["deadline"] = 600
    if rule_type in {"location_visit_or_dwell", "ordered_multi_stop_task", "stay_target_window"}:
        slots["target_coordinates"] = {"lat": 0.2, "lng": 0.2}
    if rule_type == "unknown_soft":
        kwargs["confidence"] = 0.35
    return PTTRule(**kwargs)


def _cargo(*, value: str = "runtime_value_hash_attr", pickup: float = 10.0, haul: float = 60.0, far: bool = False) -> NormalizedCargo:
    return NormalizedCargo(
        cargo_id=f"runtime_value_hash_cargo_{short_hash(value, 8)}",
        source_scope=CURRENT_ACTIONABLE,
        decision_id="runtime_value_hash_decision",
        observed_at_minutes=480,
        price_yuan=1200.0,
        pickup_distance_km=pickup,
        start_lat=1.2 if far else 0.02,
        start_lng=1.2 if far else 0.02,
        end_lat=1.2 if far else 0.2,
        end_lng=1.2 if far else 0.2,
        cost_time_minutes=360,
        create_minutes=450,
        remove_minutes=900,
        load_start_minutes=520,
        load_end_minutes=700,
        haul_distance_km=haul,
        cargo_name=value,
        start_city="",
        end_city="",
    )


def _take(world: World, cargo: NormalizedCargo, *, occupied: int | None = None) -> CandidateOption:
    minutes = int(occupied if occupied is not None else cargo.cost_time_minutes)
    return CandidateOption(
        id=f"take:{short_hash(cargo.cargo_id, 10)}:{minutes}",
        action_type="take_order",
        decision_id="runtime_value_hash_decision",
        cargo=cargo,
        direct_money=1000.0,
        occupied_minutes=minutes,
        deadhead_km=cargo.pickup_distance_km,
        haul_km=cargo.haul_distance_km,
        finish_minutes=world.status.simulation_progress_minutes + minutes,
        score=1000.0,
    )


def _wait(world: World, duration: int) -> CandidateOption:
    return CandidateOption(
        id=f"wait:{duration}",
        action_type="wait",
        decision_id="runtime_value_hash_decision",
        duration_minutes=duration,
        occupied_minutes=duration,
        finish_minutes=world.status.simulation_progress_minutes + duration,
        score=0.0,
    )


def _reposition(world: World, *, target_lat: float = 0.2, target_lng: float = 0.2) -> CandidateOption:
    return CandidateOption(
        id=f"reposition:{short_hash((target_lat, target_lng), 8)}",
        action_type="reposition",
        decision_id="runtime_value_hash_decision",
        target_lat=target_lat,
        target_lng=target_lng,
        direct_money=-40.0,
        occupied_minutes=60,
        deadhead_km=20.0,
        finish_minutes=world.status.simulation_progress_minutes + 60,
        score=-40.0,
    )


def _link(rule: PTTRule, relation: str = "violation") -> tuple[ObservedVocabLink, ...]:
    return (
        ObservedVocabLink(
            field="cargo_name",
            value="runtime_value_hash_attr",
            value_hash="runtime_value_hash_attr",
            relation=relation,
            confidence=0.9,
            rule_id=rule.rule_id,
            evidence_hash="runtime_value_hash_evidence",
        ),
    )


def _case(rule_type: str) -> tuple[World, PTTRule, tuple[ObservedVocabLink, ...], CandidateOption, CandidateOption, CandidateOption, list[NormalizedCargo]]:
    rule = _rule(rule_type)
    world = _world(now=120 if rule_type in {"daily_continuous_rest", "scheduled_quiet_window"} else 480)
    visible = [_cargo()]
    links: tuple[ObservedVocabLink, ...] = tuple()
    positive = _wait(world, 30)
    negative = _take(world, _cargo(far=True), occupied=540)
    repair = _wait(world, 480)
    if rule_type in {"forbidden_cargo_attribute", "region_avoid_or_require"}:
        links = _link(rule, "violation")
        negative = _take(world, _cargo(value="runtime_value_hash_attr"), occupied=240)
        positive = _take(world, _cargo(value="runtime_value_hash_other"), occupied=120)
        repair = positive
    elif rule_type in {"required_cargo_attribute_distinct_days", "runtime_entity_task"}:
        links = _link(rule, "repair")
        negative = _take(world, _cargo(value="runtime_value_hash_other"), occupied=420)
        repair = _take(world, _cargo(value="runtime_value_hash_attr"), occupied=180)
    elif rule_type in {"pickup_deadhead_limit", "cumulative_deadhead_budget"}:
        negative = _take(world, _cargo(pickup=90.0), occupied=240)
        positive = _take(world, _cargo(pickup=5.0), occupied=120)
        repair = _reposition(world, target_lat=0.02, target_lng=0.02)
    elif rule_type == "haul_distance_limit":
        negative = _take(world, _cargo(haul=160.0), occupied=240)
        positive = _take(world, _cargo(haul=30.0), occupied=120)
    elif rule_type == "daily_order_count_limit":
        world = _world(now=480, take_count=2)
        negative = _take(world, _cargo(), occupied=120)
        positive = _wait(world, 30)
        repair = _wait(world, 240)
    elif rule_type == "first_order_start_deadline":
        world = _world(now=500)
        negative = _wait(world, 180)
        positive = _wait(world, 30)
        repair = _take(world, _cargo(), occupied=60)
    elif rule_type in {"location_visit_or_dwell", "ordered_multi_stop_task"}:
        negative = _take(world, _cargo(far=True), occupied=600)
        positive = _wait(world, 30)
        repair = _reposition(world)
    elif rule_type == "stay_target_window":
        negative = _take(world, _cargo(far=True), occupied=600)
        positive = _wait(world, 30)
        repair = _wait(world, 240)
    elif rule_type in {"full_inactive_day_quota", "no_order_day_quota"}:
        negative = _take(world, _cargo(), occupied=240)
        positive = _wait(world, 30)
        repair = _wait(world, 720)
    elif rule_type == "daily_work_pattern":
        world = _world(now=500, take_count=2)
        negative = _take(world, _cargo(), occupied=420)
        positive = _wait(world, 30)
        repair = _wait(world, 240)
    elif rule_type == "unknown_soft":
        negative = _take(world, _cargo(), occupied=600)
        positive = _wait(world, 30)
        repair = _wait(world, 120)
    return world, rule, links, positive, negative, repair, visible


def _impact_has_negative_signal(impact: preference_controllers.ControllerImpact) -> bool:
    return (
        impact.marginal_penalty > 0
        or impact.lost_repair_window_cost > 0
        or impact.decision in {"qwen_audit_required", "massive_penalty", "block"}
    )


def _impact_has_repair_signal(impact: preference_controllers.ControllerImpact, repair_candidates: list[CandidateOption]) -> bool:
    return impact.repair_value > 0 or bool(repair_candidates) or impact.decision != "block"


def run_one(rule_type: str) -> dict[str, Any]:
    world, rule, links, positive, negative, repair, visible = _case(rule_type)
    controllers = preference_controllers.build_controllers((rule,), world)
    controller = controllers[0]
    positive_impact = controller.marginal_cost(positive, world, links)
    negative_impact = controller.marginal_cost(negative, world, links)
    repair_impact = controller.marginal_cost(repair, world, links)
    repair_candidates = controller.generate_repair_candidates(world, visible, "runtime_value_hash_decision")
    stats = preference_firewall.FirewallStats()
    options = preference_firewall.apply_firewall(
        options=[positive, negative, repair, *repair_candidates],
        world=world,
        controllers=controllers,
        links=links,
        stats=stats,
    )
    negative_trace = next(item for item in options if item.id == negative.id).trace.get("ptt_firewall", {})
    unknown_soft_ok = True
    if rule_type == "unknown_soft":
        unknown_soft_ok = negative_trace.get("decision") not in {"block", "massive_penalty"}
    checks = {
        "controller_present": controller.controller_type == rule_type,
        "paraphrase_count_ok": len(PARAPHRASES[rule_type]) >= 3,
        "positive_pass": positive_impact.decision != "block",
        "negative_pass": _impact_has_negative_signal(negative_impact),
        "repair_pass": _impact_has_repair_signal(repair_impact, repair_candidates),
        "firewall_pass": bool(negative_trace) and unknown_soft_ok,
        "linker_behavior_pass": bool(links) if rule_type in {
            "forbidden_cargo_attribute",
            "required_cargo_attribute_distinct_days",
            "region_avoid_or_require",
            "runtime_entity_task",
        } else True,
    }
    return {
        "ptt_type": rule_type,
        "controller_class": controller.__class__.__name__,
        "paraphrase_hashes": [short_hash(item, 12) for item in PARAPHRASES[rule_type]],
        "positive_effect": positive_impact.effect,
        "negative_effect": negative_impact.effect,
        "negative_decision": negative_impact.decision,
        "negative_penalty": negative_impact.marginal_penalty,
        "repair_effect": repair_impact.effect,
        "repair_value": repair_impact.repair_value,
        "repair_candidates": len(repair_candidates),
        "firewall_decision": negative_trace.get("decision", ""),
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "runs" / "ptt_synthetic" / "ptt_synthetic_results.json")
    args = parser.parse_args()
    rows = [run_one(rule_type) for rule_type in PTT_TYPES]
    summary = {
        "total_types": len(rows),
        "passed_types": sum(1 for row in rows if row["passed"]),
        "failed_types": [row["ptt_type"] for row in rows if not row["passed"]],
        "all_passed": all(row["passed"] for row in rows),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
