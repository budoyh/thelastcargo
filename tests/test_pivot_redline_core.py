from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))

from demo.agent.memory import DriverMemory
from demo.agent.pivot_redline.planner import PivotRedlinePlanner
from demo.agent import safety
from demo.agent.pivot_redline import b0_shadow, beam_rollout, candidate_bucket, risk_model, value_model
from demo.agent.wait_lock import WaitLockState
from demo.agent.schemas import (
    CURRENT_ACTIONABLE,
    ActionCertificate,
    CompiledPreferenceSet,
    DriverMemoryView,
    DriverStatus,
    PreferenceDebtMarket,
    ResourcePressureEndgame,
    RuleLedger,
    SimulationHorizon,
    TimeShadowMarket,
    NormalizedCargo,
    CandidateOption,
    World,
)


def _world(minutes: int = 0) -> World:
    return World(
        status=DriverStatus(
            driver_id="driver",
            current_lat=30.123456789,
            current_lng=120.987654321,
            simulation_progress_minutes=minutes,
            simulation_wall_time="2026-03-01T00:00:00",
            truck_length="9.6m",
            preferences=(),
            completed_order_count=0,
        ),
        pref_hash="empty",
        rules=CompiledPreferenceSet(pref_hash="empty", rules=()),
        ledger=RuleLedger(0, minutes, 0, {}, 0, 0.0),
        debt_market=PreferenceDebtMarket(0.0, 0.0, False, 0.0, 0.0),
        endgame=ResourcePressureEndgame(0.0, 31 * 24 * 60 - minutes),
        time_market=TimeShadowMarket(0.1, 1.0, 0.0, 0, "test"),
        memory_view=DriverMemoryView(0, 0.0, 0.0, 0),
        horizon=SimulationHorizon(31, 31 * 24 * 60),
    )


def _cargo(idx: int, price: float, minutes: int, start_offset: float, end_offset: float) -> NormalizedCargo:
    return NormalizedCargo(
        cargo_id=f"cargo-{idx}",
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
        observed_at_minutes=0,
        price_yuan=price,
        pickup_distance_km=5.0 + idx,
        start_lat=30.0 + start_offset,
        start_lng=120.0 + start_offset,
        end_lat=30.5 + end_offset,
        end_lng=120.5 + end_offset,
        cost_time_minutes=minutes,
        create_minutes=0,
        remove_minutes=2000,
        load_start_minutes=None,
        load_end_minutes=None,
        haul_distance_km=80.0 + idx,
    )


def test_candidate_bucket_keeps_diverse_candidate_families() -> None:
    world = _world()
    visible = [_cargo(idx, 500 + idx * 20, 120 + idx * 15, idx * 0.01, idx * 0.02) for idx in range(12)]
    options, stats = candidate_bucket.build_bucketed_candidates(world, visible, "d1")
    assert options
    for bucket in {
        "top_direct_net",
        "top_profit_per_hour",
        "top_short_duration",
        "top_low_pickup_deadhead",
        "top_good_dropoff_terminal_proxy",
        "wait_options",
    }:
        assert stats.bucket_counts.get(bucket, 0) > 0
    assert any(option.action_type == "wait" and option.duration_minutes == 240 for option in options)


def test_risk_model_penalizes_known_bad_long_lockup_action() -> None:
    world = _world(minutes=30 * 24 * 60)
    safe = CandidateOption("safe", "take_order", "d1", occupied_minutes=120, finish_minutes=30 * 24 * 60 + 120)
    bad = CandidateOption("bad", "take_order", "d1", occupied_minutes=22 * 60, deadhead_km=160, finish_minutes=31 * 24 * 60 - 60)
    model = risk_model.PivotRiskModel()
    assert model.score(bad, world).value > model.score(safe, world).value


def test_value_model_lifts_better_terminal_choice() -> None:
    vm = value_model.PivotValueModel()
    near_terminal = _cargo(1, 1000, 120, 0.0, 0.0)
    far_terminal = _cargo(2, 1000, 120, 0.0, 4.0)
    future = [_cargo(3, 900, 90, 0.51, 0.0), _cargo(4, 700, 90, 0.52, 0.0)]
    high = CandidateOption("high", "take_order", "d1", cargo=near_terminal, direct_money=500, occupied_minutes=120)
    low = CandidateOption("low", "take_order", "d1", cargo=far_terminal, direct_money=500, occupied_minutes=120)
    assert vm.terminal_value(high, future) > vm.terminal_value(low, future)


def test_beam_branch_expansion_uses_continuation_score() -> None:
    vm = value_model.PivotValueModel()
    visible = [_cargo(idx, 600 + idx * 50, 100, idx * 0.01, idx * 0.01) for idx in range(5)]
    candidates = [
        CandidateOption(f"c{idx}", "take_order", "d1", cargo=cargo, direct_money=300 + idx * 20, occupied_minutes=100)
        for idx, cargo in enumerate(visible)
    ]
    for candidate in candidates:
        candidate.score = candidate.direct_money
    bonus, node = beam_rollout.rollout_bonus(candidates[0], candidates, visible, depth=2, width=3, value_model=vm)
    assert bonus > 0
    assert node.children
    assert node.children[0].depth == 2


def test_b0_shadow_is_side_effect_free_for_options() -> None:
    world = _world()
    options = [
        CandidateOption("take", "take_order", "d1", direct_money=300, occupied_minutes=120, deadhead_km=10),
        CandidateOption("wait", "wait", "d1", duration_minutes=30, occupied_minutes=30),
    ]
    before = deepcopy(options)
    result = b0_shadow.score_b0_pure(options, world, None)
    assert result.option.id == "take"
    assert [(o.id, o.score, o.trace) for o in options] == [(o.id, o.score, o.trace) for o in before]


def test_full_precision_reposition_survives_finalize() -> None:
    world = _world()
    option = CandidateOption(
        "rep",
        "reposition",
        "d1",
        target_lat=30.123456789,
        target_lng=120.987654321,
        direct_money=-10.0,
        deadhead_km=10.0,
        occupied_minutes=10,
        finish_minutes=10,
    )
    option.action_cert = ActionCertificate("rep", "reposition", "d1", None, None, True, [])
    option.trace["preference_repair"] = True
    option.trace["expected_repair_value"] = 1000.0
    action = safety.finalize(option, world)
    assert action["action"] == "reposition"
    assert action["params"]["latitude"] == 30.123456789
    assert action["params"]["longitude"] == 120.987654321


def test_end_to_end_pivot_trace_contains_top5_and_shadow(monkeypatch) -> None:
    monkeypatch.setenv("CROWN_PIVOT_DIRECT_NET_WEIGHT", "1.0")
    monkeypatch.setenv("CROWN_PIVOT_PPH_WEIGHT", "1.0")
    api = _FakeApi()
    runtime = SimpleNamespace(memory=DriverMemory(), wait_lock=WaitLockState(), prev_world=None)
    planner = PivotRedlinePlanner(api)
    action = planner.decide("driver", runtime, _world(), "d1")
    trace = action["agent_trace"]["pivot_redline"]
    assert action["action"] == "take_order"
    assert trace["b0_pure_action"] in {"take_order", "wait", "reposition"}
    assert trace["new_action"] == "take_order"
    assert trace["top5_candidates"]
    assert "pivot_direct_net" in trace["score_components"]


class _FakeApi:
    def get_driver_status(self, driver_id: str):
        return {
            "driver_id": driver_id,
            "current_lat": 30.123456789,
            "current_lng": 120.987654321,
            "simulation_progress_minutes": 1,
            "simulation_wall_time": "2026-03-01T00:01:00",
            "truck_length": "9.6m",
            "preferences": [],
            "completed_order_count": 0,
        }

    def query_cargo(self, **_: object):
        items = []
        for idx in range(6):
            items.append(
                {
                    "distance_km": 5.0 + idx,
                    "cargo": {
                        "cargo_id": f"cargo-{idx}",
                        "price": 800 + idx * 50,
                        "cost_time_minutes": 120 + idx * 10,
                        "start": {"lat": 30.1 + idx * 0.01, "lng": 120.1 + idx * 0.01},
                        "end": {"lat": 30.5 + idx * 0.01, "lng": 120.5 + idx * 0.01},
                    },
                }
            )
        return {"items": items}
