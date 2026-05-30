from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
if str(DEMO) not in sys.path:
    sys.path.insert(0, str(DEMO))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent import (  # noqa: E402
    cargo_filter,
    candidate_generator,
    config,
    endgame_planner,
    learned_ranker,
    llm_preference_judge,
    preference_monitor,
    query_policy,
    safety,
    time_bid_scorer,
    time_shadow_market,
    trace_writer,
    world as world_module,
)
from agent.model_decision_service import ModelDecisionService  # noqa: E402
from agent.memory import DriverMemory  # noqa: E402
from agent.normalization import normalize_cargo_item  # noqa: E402
from agent.preference_compiler import hash_preferences  # noqa: E402
from agent.schemas import CURRENT_ACTIONABLE, SHADOW_LIQUIDITY_ONLY, CandidateOption  # noqa: E402
from tools import audit_guard  # noqa: E402


def cargo_item(
    cargo_id: str = "X1",
    *,
    create: str = "2026-03-01 00:00:00",
    remove: str = "2026-03-02 00:00:00",
    price: float = 1000.0,
    start_lat: float = 23.0,
    start_lng: float = 113.0,
    end_lat: float = 23.5,
    end_lng: float = 113.5,
    cost: int = 120,
):
    return {
        "distance_km": 10.0,
        "cargo": {
            "cargo_id": cargo_id,
            "price": price,
            "create_time": create,
            "remove_time": remove,
            "load_time": ["2026-03-01 00:00:00", "2026-03-02 00:00:00"],
            "start": {"lat": start_lat, "lng": start_lng},
            "end": {"lat": end_lat, "lng": end_lng},
            "cost_time_minutes": cost,
        },
    }


class FakeApi:
    def __init__(self):
        self.now = 0
        self.preferences = []
        self.items = [cargo_item()]

    def get_driver_status(self, driver_id):
        return {
            "driver_id": driver_id,
            "current_lat": 23.0,
            "current_lng": 113.0,
            "simulation_progress_minutes": self.now,
            "simulation_wall_time": "2026-03-01 00:00:00",
            "truck_length": "9.6",
            "preferences": list(self.preferences),
            "completed_order_count": 0,
        }

    def query_cargo(self, driver_id, latitude, longitude, k=100):
        self.now += 5
        return {"items": list(self.items[:k])}

    def query_decision_history(self, driver_id, step):
        return {"records": []}

    def model_chat_completion(self, payload):
        raise AssertionError("judge/model must not be called in default build")


def build_world(now=0, preferences=None):
    api = FakeApi()
    api.now = now
    api.preferences = preferences or []
    memory = DriverMemory()
    return world_module.refresh_world(api, "D_TEST", memory=memory), memory, api


def test_refresh_world_after_query():
    world0, memory, api = build_world()
    api.query_cargo("D_TEST", world0.status.current_lat, world0.status.current_lng, k=50)
    world1 = world_module.refresh_world(api, "D_TEST", memory=memory, prev_world=world0)
    assert world1.status.simulation_progress_minutes == 5
    assert world1.ledger.revision == world0.ledger.revision + 1
    assert world1.debt_market is not world0.debt_market
    assert world1.endgame is not world0.endgame
    assert world1.time_market is not world0.time_market


def test_filter_uses_world_after_query():
    world0, memory, api = build_world()
    api.items = [cargo_item(remove="2026-03-01 00:01:00")]
    observed = api.query_cargo("D_TEST", 23.0, 113.0, k=50)["items"]
    world1 = world_module.refresh_world(api, "D_TEST", memory=memory, prev_world=world0)
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=observed,
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    assert visible == []


def test_action_certificate_current_query_source():
    world1, _, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item()],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    options = candidate_generator.build_options(world1, visible, "d1")
    options = safety.pre_filter_and_attach_action_certificate(options, world1, {visible[0].cargo_id})
    take = next(o for o in options if o.action_type == "take_order")
    assert take.action_cert.safe
    assert take.action_cert.source_scope == CURRENT_ACTIONABLE


def test_source_scope_isolation():
    world1, _, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item()],
        world=world1,
        source_scope=SHADOW_LIQUIDITY_ONLY,
        decision_id="d1",
    )
    assert visible == []


def test_preference_hash_change_recompiles():
    world0, memory, api = build_world(preferences=[{"content": "alpha", "penalty_amount": 10}])
    old_hash = world0.pref_hash
    api.preferences = [{"content": "beta", "penalty_amount": 10}]
    world1 = world_module.refresh_world(api, "D_TEST", memory=memory, prev_world=world0)
    assert world1.pref_hash != old_hash
    assert world1.rules.pref_hash == hash_preferences(tuple(api.preferences))


def test_no_query_cannot_take_remembered_cargo():
    world1, _, _ = build_world(now=config.SIMULATION_HORIZON_MINUTES)
    plan = query_policy.choose(world1)
    assert plan.kind == "no_query"
    options = candidate_generator.build_options(world1, [], "d1")
    assert {o.action_type for o in options} == {"wait"}


def test_safety_fallback_wait():
    world1, _, _ = build_world()
    chosen = safety.choose_best_with_certificates([], world1)
    action = safety.finalize(chosen, world1)
    assert action["action"] == "wait"
    assert action["params"]["duration_minutes"] > 0


def test_fallback_wait_clamps_to_horizon():
    world1, _, _ = build_world(now=config.SIMULATION_HORIZON_MINUTES - 1)
    wait_option = candidate_generator.build_options(world1, [], "d1")[0]
    assert wait_option.duration_minutes == 1
    chosen = safety.choose_best_with_certificates([], world1)
    action = safety.finalize(chosen, world1)
    assert action["params"]["duration_minutes"] == 1
    assert world1.status.simulation_progress_minutes + action["params"]["duration_minutes"] <= world1.horizon.horizon_minutes


def test_decide_returns_wait_on_runtime_exception():
    class QueryFailApi(FakeApi):
        def query_cargo(self, driver_id, latitude, longitude, k=100):
            raise RuntimeError("query failed")

    action = ModelDecisionService(QueryFailApi()).decide("D_TEST")
    assert action["action"] == "wait"
    assert action["params"]["duration_minutes"] == 1
    assert "decision_exception" in action["agent_trace"]["chosen"]["action_reasons"]


def test_no_server_import():
    bad = []
    for path in (ROOT / "demo" / "agent").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "server":
                bad.append(path)
            if isinstance(node, ast.Import):
                bad.extend(path for alias in node.names if alias.name.split(".")[0] == "server")
    assert bad == []


def test_no_raw_data_access():
    findings = audit_guard.run_scan()
    assert [f for f in findings if f.code == "raw_data_marker" and f.severity == "P0"] == []


def test_no_forbidden_prompt_terms():
    findings = audit_guard.run_scan()
    assert [f for f in findings if f.code == "forbidden_preference_term" and f.severity == "P0"] == []


def test_reposition_precision():
    world1, _, _ = build_world()
    option = CandidateOption(
        id="r",
        action_type="reposition",
        decision_id="d1",
        target_lat=23.123456,
        target_lng=113.654321,
        duration_minutes=10,
        occupied_minutes=10,
        finish_minutes=20,
        score=10,
        direct_money=-1,
    )
    option.action_cert = safety._certificate_for(option, set())
    option.trace.update({"expected_gain": 100, "payback_time_p50": 60, "payback_time_p80": 120})
    action = safety.finalize(option, world1)
    assert action["params"]["latitude"] == 23.123456
    assert action["params"]["longitude"] == 113.654321


def test_horizon_31_days_confirmed():
    assert config.SIMULATION_DURATION_DAYS == 31
    assert config.SIMULATION_HORIZON_MINUTES == 31 * 24 * 60


def test_normalization_layer():
    world1, _, _ = build_world()
    try:
        time_bid_scorer.score({"raw": True}, world1, [])
    except TypeError:
        pass
    else:
        raise AssertionError("raw dict should not be scored")


def test_time_shadow_candidate_aware():
    world1, _, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item("A", price=2000), cargo_item("B", price=500)],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    options = candidate_generator.build_options(world1, visible, "d1")
    take_options = [o for o in options if o.action_type == "take_order"]
    top = max(take_options, key=lambda o: o.direct_money / max(1, o.occupied_minutes))
    other = min(take_options, key=lambda o: o.direct_money / max(1, o.occupied_minutes))
    assert time_shadow_market.productive_time_shadow_price_excluding(top, world1, options) <= time_shadow_market.productive_time_shadow_price_excluding(other, world1, options)


def test_query_information_not_penalizing_query():
    world1, _, _ = build_world()
    score = time_shadow_market.query_plan_score(200, 5, world1, missed_window_risk=0)
    assert score > 0


def test_visible_rollout_uses_only_current_actionable():
    from agent import visible_rollout

    world1, _, _ = build_world()
    current = normalize_cargo_item(cargo_item("B"), world_minutes=0, source_scope=CURRENT_ACTIONABLE, decision_id="d1")
    shadow = normalize_cargo_item(cargo_item("S"), world_minutes=0, source_scope=SHADOW_LIQUIDITY_ONLY, decision_id="d1")
    visible = [current, shadow]
    option = candidate_generator.build_options(world1, [current], "d1")[0]
    rollout = visible_rollout.evaluate(option, world1, visible)
    assert "S" not in rollout.used_second_hop_ids


def test_resource_pressure_endgame():
    world1, _, _ = build_world(preferences=[{"content": "alpha", "penalty_amount": 10000}])
    high = endgame_planner.price_resource_pressure(
        status_minutes=world1.status.simulation_progress_minutes,
        horizon_minutes=world1.horizon.horizon_minutes,
        ledger=world1.ledger,
        debt_market=world1.debt_market,
        market_liquidity=0,
    )
    assert high.intensity > 0.1


def test_reposition_payback_gate():
    world1, _, _ = build_world()
    option = CandidateOption(
        id="r",
        action_type="reposition",
        decision_id="d1",
        target_lat=23.1,
        target_lng=113.1,
        direct_money=-100,
        occupied_minutes=20,
        deadhead_km=30,
        finish_minutes=30,
    )
    option.action_cert = safety._certificate_for(option, set())
    option.trace.update({"expected_gain": 100, "payback_time_p50": 60, "payback_time_p80": 120})
    assert not safety.reposition_payback_allowed(option, world1)


def test_reposition_default_closed_without_payback_evidence():
    assert config.ENABLE_REPOSITION is False


def test_preference_certificate_can_hard_block_high_confidence_irreversible():
    world1, _, _ = build_world(preferences=[{"content": "limit 100 km 8 h", "penalty_amount": 10000, "penalty_cap": 10000}])
    option = CandidateOption(
        id="take:pref-risk",
        action_type="take_order",
        decision_id="d1",
        deadhead_km=220,
        haul_km=520,
        occupied_minutes=900,
        finish_minutes=900,
    )
    cert = preference_monitor.certify(option, world1)
    assert cert.high_confidence_irreversible_violation


def test_reposition_blocked_by_preference_damage():
    world1, _, _ = build_world(preferences=[{"content": "limit 100 km 8 h", "penalty_amount": 10000, "penalty_cap": 10000}])
    option = CandidateOption(
        id="r",
        action_type="reposition",
        decision_id="d1",
        target_lat=23.1,
        target_lng=113.1,
        direct_money=-10,
        occupied_minutes=900,
        deadhead_km=520,
        finish_minutes=900,
        score=999,
    )
    option.action_cert = safety._certificate_for(option, set())
    option.trace.update({"expected_gain": 1000, "payback_time_p50": 60, "payback_time_p80": 120})
    option.pref_cert = preference_monitor.certify(option, world1)
    chosen = safety.choose_best_with_certificates([option], world1)
    assert chosen.action_type == "wait"


def test_trace_dashboard_regret_categories(tmp_path):
    from tools import regret_dashboard

    row = {
        "driver_id": "D_TEST",
        "query_scan_cost_minutes": 20,
        "action_exec_cost_minutes": 800,
        "simulation_end_time": "2026-03-25 00:00",
        "action": {
            "action": "take_order",
            "agent_trace": {
                "visible_count": 1,
                "debt_value": 300,
                "chosen": {"score": -1},
            },
        },
    }
    p = tmp_path / "actions_202603_D_TEST_x.jsonl"
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")
    stats = regret_dashboard.build_stats(tmp_path)
    assert set(regret_dashboard.REGRET_KEYS) <= set(stats.counts)
    assert stats.counts["query_too_big"] == 1
    assert stats.counts["long_order_trap"] == 1


def test_regret_dashboard_handles_minimal_trace_and_bad_lines(tmp_path):
    from tools import regret_dashboard

    row = {
        "driver_id": "D_TEST",
        "query_scan_cost_minutes": 0,
        "action_exec_cost_minutes": 5,
        "action": {"action": "wait", "agent_trace": {"chosen": "wait:5"}},
        "result": {"simulation_progress_minutes": 5},
    }
    p = tmp_path / "actions_202603_D_TEST_x.jsonl"
    p.write_text("{bad json\n" + json.dumps(row) + "\n", encoding="utf-8")
    stats = regret_dashboard.build_stats(tmp_path)
    assert stats.steps == 1
    assert stats.skipped_lines == 1
    assert stats.illegal_actions == 0


def test_regret_reposition_not_recovered_uses_payback_window(tmp_path):
    from tools import regret_dashboard

    recovered = [
        {
            "driver_id": "D_TEST",
            "query_scan_cost_minutes": 0,
            "action_exec_cost_minutes": 10,
            "action": {"action": "reposition", "agent_trace": {"reposition_gate": {"reposition_cost": 100}}},
            "result": {"simulation_progress_minutes": 10},
        },
        {
            "driver_id": "D_TEST",
            "query_scan_cost_minutes": 0,
            "action_exec_cost_minutes": 120,
            "action": {"action": "take_order", "agent_trace": {"chosen": {"components": {"direct_money": 120}}}},
            "result": {"simulation_progress_minutes": 120, "accepted": True},
        },
    ]
    p = tmp_path / "actions_202603_D_TEST_x.jsonl"
    p.write_text("\n".join(json.dumps(row) for row in recovered) + "\n", encoding="utf-8")
    assert regret_dashboard.build_stats(tmp_path).counts["reposition_not_recovered"] == 0


def test_trace_records_certificate_fields_in_minimal_mode(monkeypatch):
    world1, _, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item()],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    option = candidate_generator.build_options(world1, visible, "d1")[0]
    option.action_cert = safety._certificate_for(option, {visible[0].cargo_id})
    monkeypatch.setattr(config, "SUBMIT_MODE", True)
    action = trace_writer.attach_trace(
        {"action": "take_order", "params": {"cargo_id": visible[0].cargo_id}},
        world=world1,
        query_plan=query_policy.QueryPlan("current_small_query", k=50),
        visible_cargos=visible,
        chosen=option,
        options=[option],
        query_minutes=5,
    )
    chosen = action["agent_trace"]["chosen"]
    assert chosen["cargo_id"] == visible[0].cargo_id
    assert chosen["source_scope"] == CURRENT_ACTIONABLE
    assert chosen["cert_decision_id"] == "d1"


def test_learned_ranker_sign_constraints():
    assert learned_ranker.validate_sign_constraints(learned_ranker.LinearWeights(deadhead_km=-1, execution_risk=-1, preference_violation_debt=-1, direct_net_profit=1))
    assert not learned_ranker.validate_sign_constraints(learned_ranker.LinearWeights(deadhead_km=1))


def test_learned_ranker_ood_shrink():
    world1, _, _ = build_world()
    option = CandidateOption(id="x", action_type="wait", decision_id="d1", deadhead_km=200, occupied_minutes=10, score=0)
    assert learned_ranker.is_ood(option, world1)


def test_destination_shadow_off_by_default():
    assert config.OFFICIAL_ALLOW_ARBITRARY_COORD_QUERY is False
    assert config.ENABLE_DESTINATION_SHADOW_QUERY is False


def test_shadow_cargo_never_actionable():
    world1, _, _ = build_world()
    shadow = normalize_cargo_item(cargo_item("S"), world_minutes=0, source_scope=SHADOW_LIQUIDITY_ONLY, decision_id="d1")
    option = CandidateOption(id="bad", action_type="take_order", decision_id="d1", cargo=shadow)
    option.action_cert = safety._certificate_for(option, {"S"})
    assert not option.action_cert.safe


def test_llm_judge_never_outputs_action():
    content = json.dumps({"candidate_id": "x", "violates_preference": "no", "action": "take_order"})
    parsed = llm_preference_judge.parse_judge_response(content)
    assert parsed["violates_preference"] == "unknown"


def test_llm_json_failure_unknown():
    parsed = llm_preference_judge.parse_judge_response("{")
    assert parsed["violates_preference"] == "unknown"
    assert parsed["confidence"] == 0.0
