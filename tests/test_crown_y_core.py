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
    micro_reposition,
    observed_vocab_linker,
    candidate_preference_verifier,
    preference_repair_planner,
    preference_repair,
    preference_firewall,
    macro_commitment,
    preference_automata,
    preference_monitor,
    ptt_transducer,
    qwen_preference_compiler,
    query_policy,
    rescue_scorer,
    safety,
    time_bid_scorer,
    time_shadow_market,
    trace_writer,
    visible_graph_mpc,
    wait_lock,
    world as world_module,
)
from agent.model_decision_service import ModelDecisionService  # noqa: E402
from agent.memory import DriverMemory  # noqa: E402
from agent.normalization import normalize_cargo_item  # noqa: E402
from agent.preference_compiler import hash_preferences  # noqa: E402
from agent.schemas import CURRENT_ACTIONABLE, SHADOW_LIQUIDITY_ONLY, CandidateOption, CompiledPreferenceRule, CompiledPreferenceSet  # noqa: E402
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
    forensic = action["agent_trace"]["rescue"]["wait_forensic"]
    assert forensic["wait_reason"] == "decision_exception"
    assert "why_wait_won" in forensic


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


def test_visible_graph_alpha_entrypoints_configured():
    assert config.VISIBLE_GRAPH_ALPHA_TEST_VALUES == (0.05, 0.10, 0.20, 0.35)


def test_visible_graph_mpc_uses_current_actionable_and_alpha(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_VISIBLE_GRAPH_MPC", True)
    world1, memory, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[
            cargo_item("A", price=900, end_lat=23.5, end_lng=113.5, cost=60),
            cargo_item("B", price=900, start_lat=23.5, start_lng=113.5, end_lat=23.7, end_lng=113.7, cost=60),
        ],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    memory.update_current_observation(world1, visible, query_minutes=5)

    def bonus_for_alpha(alpha):
        monkeypatch.setattr(config, "VISIBLE_GRAPH_ALPHA", alpha)
        options = candidate_generator.build_options(world1, visible, "d1")
        take_a = next(option for option in options if option.cargo and option.cargo.cargo_id == "A")
        stats = visible_graph_mpc.apply_visible_graph_mpc(
            options,
            world1,
            visible,
            online_summary=memory.online_graph_snapshot(),
        )
        return take_a.score_components["visible_graph_mpc"], take_a.trace["visible_graph_mpc"], stats

    bonus_low, trace_low, stats_low = bonus_for_alpha(0.05)
    bonus_high, trace_high, stats_high = bonus_for_alpha(0.35)
    assert bonus_low > 0
    assert bonus_high > bonus_low
    assert trace_low["plan_type"] == "visible_A_to_B_pair"
    assert trace_low["alpha"] == 0.05
    assert trace_low["uses_current_actionable_only"] is True
    assert trace_low["uses_same_driver_online_summary"] is True
    assert stats_low.visible_pair_count > 0
    assert stats_high.payload()["alpha"] == 0.35


def test_visible_graph_terminal_filters_scope_and_decision(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_VISIBLE_GRAPH_MPC", True)
    monkeypatch.setattr(config, "VISIBLE_GRAPH_ALPHA", 0.10)
    world1, _, _ = build_world()
    current = normalize_cargo_item(cargo_item("A", price=200), world_minutes=0, source_scope=CURRENT_ACTIONABLE, decision_id="d1")
    stale = normalize_cargo_item(cargo_item("OLD", price=20000), world_minutes=0, source_scope=CURRENT_ACTIONABLE, decision_id="d2")
    shadow = normalize_cargo_item(cargo_item("SHADOW", price=20000), world_minutes=0, source_scope=SHADOW_LIQUIDITY_ONLY, decision_id="d1")
    option = CandidateOption(id="wait:graph", action_type="wait", decision_id="d1", duration_minutes=30, occupied_minutes=30, finish_minutes=30)
    stats = visible_graph_mpc.apply_visible_graph_mpc([option], world1, [current, stale, shadow], online_summary={})
    trace = option.trace["visible_graph_mpc"]
    assert trace["plan_type"] == "wait_then_A"
    assert trace["current_actionable_count"] == 1
    assert trace["uses_current_actionable_only"] is True
    assert stats.terminal_value_used_count == 1


def test_online_graph_memory_snapshot_is_aggregate_only():
    world1, memory, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item("A", price=700), cargo_item("B", price=500)],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    memory.update_current_observation(world1, visible, query_minutes=5)
    snapshot = memory.online_graph_snapshot()
    assert snapshot["cell_count"] > 0
    assert snapshot["observations"] == 1
    assert "A" not in repr(snapshot)
    assert "B" not in repr(snapshot)


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


def test_regret_dashboard_v2_writes_six_categories(tmp_path):
    from tools import regret_dashboard

    run_dir = tmp_path / "a7"
    run_dir.mkdir()
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
        "result": {"accepted": True, "simulation_progress_minutes": 800},
    }
    (run_dir / "actions_202603_D001.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    (run_dir / "monthly_income_202603.json").write_text(json.dumps({"summary": {"total_net_income_all_drivers": 1}}), encoding="utf-8")
    out = tmp_path / "regret.md"
    regret_dashboard.write_rescue_report(tmp_path, out)
    text = out.read_text(encoding="utf-8")
    for key in regret_dashboard.REGRET_KEYS:
        assert key in text


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
    assert chosen["cargo_id"] is None
    assert chosen["cargo_id_hash"]
    assert chosen["source_scope"] == CURRENT_ACTIONABLE
    assert chosen["cert_decision_id"] is None
    assert chosen["cert_decision_id_hash"]


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


def test_rescue_scorer_takes_safe_positive_net(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_RESCUE_SCORER", True)
    monkeypatch.setattr(config, "ENABLE_RESCUE_PREFERENCE_SOFT", True)
    monkeypatch.setattr(config, "RESCUE_DIRECT_NET_FLOOR", 1.0)
    monkeypatch.setattr(config, "RESCUE_PROFIT_PER_HOUR_FLOOR", 0.0)
    world1, _, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item(price=600, cost=60)],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    options = candidate_generator.build_options(world1, visible, "d1")
    options = safety.pre_filter_and_attach_action_certificate(options, world1, {visible[0].cargo_id})
    options, stats = rescue_scorer.score_options(options, world1, wait_lock.WaitLockState())
    chosen = rescue_scorer.choose(options, stats, wait_lock.WaitLockState())
    assert chosen.action_type == "take_order"
    assert chosen.direct_money > 0


def test_pref_forge_ignores_qwen_auditor_adjustment_in_rescue_score(monkeypatch):
    monkeypatch.setattr(config, "RESCUE_VARIANT", "crown_pref_forge")
    monkeypatch.setattr(config, "ENABLE_PTT_AUDITOR", True)
    monkeypatch.setattr(config, "ENABLE_RESCUE_PREFERENCE_SOFT", False)
    monkeypatch.setattr(config, "ENABLE_RESCUE_REST_GUARD", False)
    monkeypatch.setattr(config, "ENABLE_NEXT_MARGINAL_PREF", False)
    monkeypatch.setattr(config, "ENABLE_RESCUE_TWOHOP_LITE", False)
    monkeypatch.setattr(config, "ENABLE_RESCUE_TIME_SHADOW_LITE", False)
    monkeypatch.setattr(config, "ENABLE_PREF_FORGE_HUNTER", False)
    monkeypatch.setattr(config, "RESCUE_DIRECT_NET_FLOOR", 1.0)
    monkeypatch.setattr(config, "RESCUE_PROFIT_PER_HOUR_FLOOR", 0.0)
    world1, _, _ = build_world()
    option = CandidateOption(
        id="take:pref-forge-auditor-guard",
        action_type="take_order",
        decision_id="d1",
        direct_money=100.0,
        occupied_minutes=60,
        finish_minutes=60,
        score_components={"qwen_audit_adjustment": 9999.0},
    )
    scored, _ = rescue_scorer.score_options([option], world1, wait_lock.WaitLockState())
    take = scored[0]
    assert take.score_components["qwen_audit_adjustment_applied"] == 0.0
    assert take.score_components["qwen_audit_adjustment_ignored"] == 9999.0
    assert take.score < 9999.0


def test_wait_forensic_contains_required_fields(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_RESCUE_SCORER", True)
    monkeypatch.setattr(config, "RESCUE_DIRECT_NET_FLOOR", 35.0)
    world1, _, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item(price=5, cost=60)],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    options = candidate_generator.build_options(world1, visible, "d1")
    options = safety.pre_filter_and_attach_action_certificate(options, world1, {visible[0].cargo_id})
    state = wait_lock.WaitLockState()
    options, stats = rescue_scorer.score_options(options, world1, state)
    chosen = rescue_scorer.choose(options, stats, state)
    forensic = rescue_scorer.wait_forensic(chosen, options, stats, state)
    assert forensic["wait_reason"]
    assert "best_order_net" in forensic
    assert "best_order_per_hour" in forensic
    assert forensic["top_5_rejected_take"]
    assert forensic["top20_rejected_take"]
    assert "best_take_delta_official_net_estimate" in forensic
    assert "best_reposition_delta_estimate" in forensic
    assert "wait_lock_bug" in forensic
    assert "score_components" in forensic["top_5_rejected_take"][0]


def test_unknown_preference_risk_is_soft_not_hard(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_RESCUE_PREFERENCE_SOFT", True)
    monkeypatch.setattr(config, "ENABLE_RESCUE_REST_GUARD", False)
    monkeypatch.setattr(config, "RESCUE_DIRECT_NET_FLOOR", 1.0)
    monkeypatch.setattr(config, "RESCUE_PROFIT_PER_HOUR_FLOOR", 0.0)
    world1, _, _ = build_world(preferences=[{"content": "abstract runtime constraint", "penalty_amount": 100}])
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item(price=700, cost=90)],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    options = candidate_generator.build_options(world1, visible, "d1")
    options = safety.pre_filter_and_attach_action_certificate(options, world1, {visible[0].cargo_id})
    options, stats = rescue_scorer.score_options(options, world1, wait_lock.WaitLockState())
    take = next(o for o in options if o.action_type == "take_order")
    assert take.trace.get("hard_block_reason", "") == ""
    assert rescue_scorer.choose(options, stats, wait_lock.WaitLockState()).action_type == "take_order"


def test_query_wait_loop_breaker_lowers_thresholds(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_RESCUE_WAIT_PENALTY", True)
    monkeypatch.setattr(config, "RESCUE_DIRECT_NET_FLOOR", 35.0)
    monkeypatch.setattr(config, "RESCUE_PROFIT_PER_HOUR_FLOOR", 18.0)
    world1, _, _ = build_world()
    state = wait_lock.WaitLockState(consecutive_wait=3, consecutive_query_wait=3)
    direct, per_hour = wait_lock.lowered_thresholds(state)
    assert wait_lock.query_k(state, world1) == config.RESCUE_QUERY_K_HIGH
    assert direct < 35.0
    assert per_hour < 18.0


def test_micro_reposition_uses_current_visible_cluster(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_RESCUE_MICRO_REPOSITION", True)
    world1, _, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item(price=800, start_lat=23.2, start_lng=113.0, cost=90)],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    option = micro_reposition.build_candidate(
        world1,
        visible,
        "d1",
        wait_lock.WaitLockState(consecutive_wait=config.RESCUE_MICRO_REPOSITION_TRIGGER_WAITS),
    )
    assert option is not None
    assert option.trace["target_source"] == "current_visible_pickup_cluster"
    assert config.RESCUE_MICRO_REPOSITION_MIN_KM <= option.deadhead_km <= config.RESCUE_MICRO_REPOSITION_MAX_KM + 0.01


def test_rescue_negative_net_hard_block():
    option = CandidateOption(
        id="take:negative",
        action_type="take_order",
        decision_id="d1",
        direct_money=-100.0,
        occupied_minutes=60,
    )
    assert rescue_scorer.hard_block_reason(option, min_direct=1.0, min_per_hour=0.0) == "severe_negative_net"


def test_force_take_does_not_bypass_rest_guard(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_RESCUE_REST_GUARD", True)
    monkeypatch.setattr(config, "RESCUE_DIRECT_NET_FLOOR", 1.0)
    monkeypatch.setattr(config, "RESCUE_PROFIT_PER_HOUR_FLOOR", 0.0)
    world1, _, _ = build_world(preferences=[{"content": "abstract runtime constraint", "penalty_amount": 10000}])
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item(price=700, cost=60)],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    options = candidate_generator.build_options(world1, visible, "d1")
    options = safety.pre_filter_and_attach_action_certificate(options, world1, {visible[0].cargo_id})
    state = wait_lock.WaitLockState(consecutive_wait=config.RESCUE_FORCE_TAKE_AFTER_WAITS)
    options, stats = rescue_scorer.score_options(options, world1, state)
    take = next(o for o in options if o.action_type == "take_order")
    assert take.trace["hard_block_reason"] == "rest_window_overlap"
    assert rescue_scorer.choose(options, stats, state).action_type == "wait"


def test_rest_guard_wait_has_post_query_forensic(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_RESCUE_SCORER", True)
    monkeypatch.setattr(config, "ENABLE_RESCUE_REST_GUARD", True)
    monkeypatch.setattr(config, "ENABLE_NEXT_NO_QUERY_REST_BLOCK", False)
    monkeypatch.setattr(config, "ENABLE_QWEN_PREFERENCE_COMPILER", False)
    monkeypatch.setattr(config, "RESCUE_DIRECT_NET_FLOOR", 1.0)
    monkeypatch.setattr(config, "RESCUE_PROFIT_PER_HOUR_FLOOR", 0.0)
    api = FakeApi()
    api.preferences = [{"content": "abstract runtime constraint", "penalty_amount": 10000}]
    api.items = [cargo_item(price=700, cost=60)]
    action = ModelDecisionService(api).decide("D_TEST")
    trace = action["agent_trace"]
    forensic = trace["rescue"]["wait_forensic"]
    assert action["action"] == "wait"
    assert trace["query_minutes"] > 0
    assert forensic["wait_reason"] == "daily_rest_guard"
    assert forensic["top_5_rejected_take"]
    assert forensic["best_order_net"] > 0


def test_filter_rejection_summary_includes_rescue_reasons(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_RESCUE_SCORER", True)
    world1, _, _ = build_world(now=5)
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item(remove="2026-03-01 00:10:00")],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="filter-d1",
    )
    assert visible == []
    assert cargo_filter.rejection_summary("filter-d1")["remove_slack_too_short"] == 1


def test_invalid_explicit_load_window_rejected():
    item = cargo_item()
    item["cargo"]["load_time"] = ["2026-03-02 00:00:00", "2026-03-01 00:00:00"]
    assert normalize_cargo_item(item, world_minutes=0, source_scope=CURRENT_ACTIONABLE, decision_id="d1") is None


def test_qwen_compiler_calls_model_for_new_pref_hash(monkeypatch):
    class CompilerApi:
        def __init__(self):
            self.calls = 0

        def model_chat_completion(self, payload):
            self.calls += 1
            assert payload["model"] == "qwen3.5-flash"
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "contract_version": "gold_v1",
                                    "rules": [
                                        {
                                            "polarity": "prefer",
                                            "observable": "unknown",
                                            "scope": "whole_period",
                                            "metric": "unknown",
                                            "counting": "unknown",
                                            "slots": {},
                                            "severity": {"source": "unknown", "penalty_amount": None, "penalty_cap": None},
                                            "repair_actions": ["wait"],
                                            "confidence": 0.3,
                                            "uncertainty": [],
                                            "evidence_hash": "0123456789abcdef",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }

    monkeypatch.setenv("DASHSCOPE_API_KEY", "unit-test-key")
    api = CompilerApi()
    before = qwen_preference_compiler.STATS.compile_calls
    rules = qwen_preference_compiler.compile_with_qwen(
        api=api,
        pref_hash="unit-qwen-new-pref",
        preferences=({"content": "abstract runtime preference", "penalty_amount": 10},),
        fallback_amounts=[{"amount": 10.0, "cap": None, "direction": "penalty"}],
    )
    assert rules is not None
    assert api.calls == 1
    assert rules[0].repair_action_kinds == ("wait",)
    assert qwen_preference_compiler.STATS.compile_calls == before + 1


def test_qwen_trident_v2_contract_fields_and_redacted_slots(monkeypatch):
    class CompilerApi:
        def model_chat_completion(self, payload):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "contract_version": "trident_v2",
                                    "rules": [
                                        {
                                            "rule_id": "abcdef0123456789",
                                            "polarity": "avoid",
                                            "observable": "cargo_attribute",
                                            "scope": "action",
                                            "metric": "match",
                                            "counting": "per_action",
                                            "slots": {
                                                "field": "cargo_name",
                                                "operator": "contains_any",
                                                "runtime_values": ["private-runtime-value"],
                                            },
                                            "repair": ["avoid_take"],
                                            "confidence": 0.8,
                                            "uncertainty": [],
                                            "evidence_hash": "abcdef0123456789",
                                        }
                                    ],
                                }
                            )
                        }
                    }
                ],
                "usage": {},
            }

    monkeypatch.setenv("DASHSCOPE_API_KEY", "unit-test-key")
    rules = qwen_preference_compiler.compile_with_qwen(
        api=CompilerApi(),
        pref_hash="unit-qwen-trident-v2-pref",
        preferences=({"content": "abstract runtime preference", "penalty_amount": 10},),
        fallback_amounts=[{"amount": 10.0, "cap": None, "direction": "penalty"}],
    )
    assert rules is not None
    rule = rules[0]
    assert rule.contract_version == "trident_v2"
    assert rule.polarity == "avoid"
    assert rule.observable == "cargo_attribute"
    assert rule.counting == "per_action"
    assert rule.repair == ("avoid_take",)
    assert rule.penalty_amount == 10.0
    assert rule.penalty_amount_source == "runtime_preference"
    slots_text = json.dumps(rule.slots, ensure_ascii=False, sort_keys=True)
    assert "private-runtime-value" not in slots_text
    assert rule.slots["runtime_values"] == []
    assert rule.slots["runtime_value_hashes"]


def test_qwen_trident_v2_rejects_invented_unknown_penalty():
    invented_penalty = {
        "contract_version": "trident_v2",
        "rules": [
            {
                "rule_id": "1111222233334444",
                "polarity": "avoid",
                "observable": "distance",
                "scope": "action",
                "metric": "<=",
                "counting": "per_action",
                "slots": {"distance_km": 100},
                "repair": ["avoid_take"],
                "severity": {"source": "unknown", "penalty_amount": 1200, "penalty_cap": None},
                "confidence": 0.9,
                "uncertainty": [],
                "evidence_hash": "1111222233334444",
            }
        ],
    }
    assert not qwen_preference_compiler._valid_gold_contract(invented_penalty)


def test_qwen_gold_contract_rejects_malformed_schema():
    malformed = {
        "contract_version": "gold_v1",
        "rules": [
            {
                "polarity": "prefer",
                "observable": "unknown",
                "scope": "whole_period",
                "metric": "unknown",
                "counting": "unknown",
                "slots": {},
                "severity": "not-a-dict",
                "repair_actions": ["wait"],
                "confidence": "bad",
                "uncertainty": [],
                "evidence_hash": 123,
            }
        ],
    }
    assert not qwen_preference_compiler._valid_gold_contract(malformed)


def test_qwen_gold_contract_requires_unknown_penalty_null():
    invented_penalty = {
        "contract_version": "gold_v1",
        "rules": [
            {
                "polarity": "avoid",
                "observable": "distance",
                "scope": "whole_period",
                "metric": "<=",
                "counting": "per_action",
                "slots": {"distance_km": 100},
                "severity": {"source": "unknown", "penalty_amount": 1200, "penalty_cap": None},
                "repair_actions": ["avoid_take"],
                "confidence": 0.9,
                "uncertainty": [],
                "evidence_hash": "1111222233334444",
            }
        ],
    }
    assert not qwen_preference_compiler._valid_gold_contract(invented_penalty)


def test_qwen_gold_contract_rejects_model_reported_explicit_penalty():
    explicit_penalty = {
        "contract_version": "gold_v1",
        "rules": [
            {
                "polarity": "avoid",
                "observable": "distance",
                "scope": "whole_period",
                "metric": "<=",
                "counting": "per_action",
                "slots": {"distance_km": 100},
                "severity": {"source": "explicit", "penalty_amount": 1200, "penalty_cap": None},
                "repair_actions": ["avoid_take"],
                "confidence": 0.9,
                "uncertainty": [],
                "evidence_hash": "1111222233334444",
            }
        ],
    }
    assert not qwen_preference_compiler._valid_gold_contract(explicit_penalty)


def test_qwen_compiler_env_priority_fallback_keys(monkeypatch):
    class CompilerApi:
        def model_chat_completion(self, payload):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "contract_version": "gold_v1",
                                    "rules": [
                                        {
                                            "polarity": "prefer",
                                            "observable": "unknown",
                                            "scope": "whole_period",
                                            "metric": "unknown",
                                            "counting": "unknown",
                                            "slots": {},
                                            "severity": {"source": "unknown", "penalty_amount": None, "penalty_cap": None},
                                            "repair_actions": ["wait"],
                                            "confidence": 0.3,
                                            "uncertainty": [],
                                            "evidence_hash": "abcdef0123456789",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ],
                "usage": {},
            }

    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("BAILIAN_API_KEY", "unit-test-key")
    rules = qwen_preference_compiler.compile_with_qwen(
        api=CompilerApi(),
        pref_hash="unit-qwen-bailian-pref",
        preferences=({"content": "abstract runtime preference", "penalty_amount": 10},),
        fallback_amounts=[{"amount": 10.0, "cap": None, "direction": "penalty"}],
    )
    assert rules is not None


def test_qwen_compiler_does_not_treat_dummy_key_as_success(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "local-dummy-key-not-used")
    before = qwen_preference_compiler.STATS.dummy_key_blocked_count
    rules = qwen_preference_compiler.compile_with_qwen(
        api=None,
        pref_hash="unit-qwen-dummy-pref",
        preferences=({"content": "abstract runtime preference", "penalty_amount": 10},),
        fallback_amounts=[{"amount": 10.0, "cap": None, "direction": "penalty"}],
    )
    assert rules is None
    assert qwen_preference_compiler.STATS.dummy_key_blocked_count == before + 1


def test_qwen_compiler_prefers_injected_api_over_dummy_key(monkeypatch):
    class InjectedApi:
        def __init__(self):
            self.calls = 0

        def model_chat_completion(self, payload):
            self.calls += 1
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "contract_version": "gold_v1",
                                    "rules": [
                                        {
                                            "polarity": "prefer",
                                            "observable": "unknown",
                                            "scope": "whole_period",
                                            "metric": "unknown",
                                            "counting": "unknown",
                                            "slots": {},
                                            "severity": {"source": "unknown", "penalty_amount": None, "penalty_cap": None},
                                            "repair_actions": ["wait"],
                                            "confidence": 0.3,
                                            "uncertainty": [],
                                            "evidence_hash": "0123456789abcdef",
                                        }
                                    ],
                                }
                            )
                        }
                    }
                ],
                "usage": {},
            }

    monkeypatch.setenv("DASHSCOPE_API_KEY", "local-dummy-key-not-used")
    api = InjectedApi()
    rules = qwen_preference_compiler.compile_with_qwen(
        api=api,
        pref_hash="unit-qwen-dummy-with-injected-pref",
        preferences=({"content": "abstract runtime preference", "penalty_amount": 10},),
        fallback_amounts=[{"amount": 10.0, "cap": None, "direction": "penalty"}],
    )
    assert rules is not None
    assert api.calls == 1


def test_qwen_irreversible_repairability_reaches_certificate(monkeypatch):
    class CompilerApi:
        def model_chat_completion(self, payload):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "contract_version": "gold_v1",
                                    "rules": [
                                        {
                                            "polarity": "avoid",
                                            "observable": "distance",
                                            "scope": "whole_period",
                                            "metric": "<=",
                                            "counting": "per_action",
                                            "slots": {"distance_km": 100},
                                            "severity": {"source": "unknown", "penalty_amount": None, "penalty_cap": None},
                                            "repair_actions": ["avoid_take"],
                                            "confidence": 0.9,
                                            "uncertainty": [],
                                            "evidence_hash": "1111222233334444",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ],
                "usage": {},
            }

    monkeypatch.setenv("DASHSCOPE_API_KEY", "unit-test-key")
    rules = qwen_preference_compiler.compile_with_qwen(
        api=CompilerApi(),
        pref_hash="unit-qwen-irreversible-pref",
        preferences=({"content": "abstract runtime preference", "penalty_amount": 10000},),
        fallback_amounts=[{"amount": 10000.0, "cap": None, "direction": "penalty"}],
    )
    assert rules is not None
    assert rules[0].repairability == "irreversible_after_action"
    from dataclasses import replace
    from agent.schemas import CompiledPreferenceSet

    world1, _, _ = build_world()
    world2 = replace(world1, rules=CompiledPreferenceSet(pref_hash="unit-qwen-irreversible-pref", rules=rules))
    option = CandidateOption(
        id="take:qwen-risk",
        action_type="take_order",
        decision_id="d1",
        direct_money=500,
        occupied_minutes=900,
        deadhead_km=300,
        haul_km=400,
        finish_minutes=900,
    )
    cert = preference_monitor.certify(option, world2)
    assert cert.high_confidence_irreversible_violation


def test_qwen_auditor_records_nonzero_trident_effect_trace(monkeypatch):
    class AuditorApi:
        def model_chat_completion(self, payload):
            content = payload["messages"][1]["content"]
            assert "Do not choose an action" in content
            assert "final action" in content
            data = json.loads(content.split("Input is current runtime-only visible data: ", 1)[1])
            candidate_hash = data[0]["candidate_hash"]
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "assessments": [
                                        {
                                            "candidate_id": candidate_hash,
                                            "rule_id": "runtime-rule-id",
                                            "relation": "violation",
                                            "effect": "violates",
                                            "risk_level": "high",
                                            "repair_level": "none",
                                            "confidence": 0.9,
                                            "evidence": "private auditor evidence",
                                        }
                                    ],
                                    "final_action": "take_order",
                                }
                            )
                        }
                    }
                ],
                "usage": {},
            }

    monkeypatch.setattr(config, "ENABLE_PTT_AUDITOR", True)
    monkeypatch.setattr(config, "RESCUE_VARIANT", "crown_trident_gold2")
    monkeypatch.setattr(config, "TRIDENT_QWEN_AUDIT_SCALE", 1.0)
    monkeypatch.setattr(config, "DISABLE_RUNTIME_QWEN", False)
    world1, _, _ = build_world(preferences=[{"content": "abstract runtime preference", "penalty_amount": 1000}])
    risky = CandidateOption(
        id="take:audited",
        action_type="take_order",
        decision_id="D_TEST:7",
        direct_money=100,
        occupied_minutes=60,
        finish_minutes=60,
        score=100,
    )
    risky.trace["ptt_firewall"] = {
        "decision": "qwen_audit_required",
        "marginal_penalty": 900.0,
        "future_repairability_delta": 200.0,
        "top_impacts": [{"rule_hash": "abc123", "effect": "violates"}],
    }
    other = CandidateOption(
        id="take:other",
        action_type="take_order",
        decision_id="D_TEST:7",
        direct_money=50,
        occupied_minutes=60,
        finish_minutes=60,
        score=50,
    )
    stats = preference_firewall.FirewallStats()
    before = qwen_preference_compiler.STATS.audit_adjustment_nonzero_count
    preference_firewall.maybe_audit_high_risk(
        api=AuditorApi(),
        world=world1,
        options=[risky, other],
        stats=stats,
        limit=2,
    )
    adjustment = risky.score_components["qwen_audit_adjustment"]
    assert adjustment < 0
    risky.score += adjustment
    chosen = other
    preference_firewall.finalize_auditor_effect_trace(options=[risky, other], chosen=chosen, stats=stats)
    rows = stats.payload()["qwen_effect_rows"]
    assert rows
    row = next(item for item in rows if item["candidate_hash"] == preference_firewall._hash("take:audited"))
    assert row["applied_score_adjustment"] != 0
    assert row["ranking_changed"] is True
    assert row["action_changed"] is True
    assert row["final_action_used"] is False
    assert row["affected_rule_ids"]
    assert "private auditor evidence" not in json.dumps(rows, ensure_ascii=False)
    assert qwen_preference_compiler.STATS.audit_adjustment_nonzero_count == before + 1


def test_qwen_auditor_accepts_numeric_scores_with_positional_candidate(monkeypatch):
    class PositionalAuditorApi:
        def model_chat_completion(self, payload):
            content = payload["messages"][1]["content"]
            assert "risk_score" in content
            assert "repair_score" in content
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "assessments": [
                                        {
                                            "relation": "violation",
                                            "effect": "violates",
                                            "risk_score": 0.8,
                                            "repair_score": 0.0,
                                            "confidence": 0.85,
                                            "evidence": "runtime-only evidence",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ],
                "usage": {},
            }

    monkeypatch.setattr(config, "ENABLE_PTT_AUDITOR", True)
    monkeypatch.setattr(config, "RESCUE_VARIANT", "crown_trident_gold2")
    monkeypatch.setattr(config, "TRIDENT_QWEN_AUDIT_SCALE", 1.0)
    monkeypatch.setattr(config, "DISABLE_RUNTIME_QWEN", False)
    world1, _, _ = build_world(preferences=[{"content": "abstract runtime preference", "penalty_amount": 1000}])
    risky = CandidateOption(
        id="take:numeric-audited",
        action_type="take_order",
        decision_id="D_TEST:8",
        direct_money=300,
        occupied_minutes=60,
        finish_minutes=60,
        score=200,
    )
    risky.trace["ptt_firewall"] = {
        "decision": "qwen_audit_required",
        "marginal_penalty": 600.0,
        "future_repairability_delta": 200.0,
        "top_impacts": [{"rule_hash": "abc123", "effect": "violates"}],
    }
    stats = preference_firewall.FirewallStats()
    preference_firewall.maybe_audit_high_risk(
        api=PositionalAuditorApi(),
        world=world1,
        options=[risky],
        stats=stats,
        limit=1,
    )
    row = stats.payload()["qwen_effect_rows"][0]
    assert row["json_valid"] is True
    assert row["output_relation"] == "violation"
    assert row["raw_risk_score"] > 0
    assert row["applied_score_adjustment"] < 0


def test_score_accountant_no_double_count_and_redacts_preferences(tmp_path):
    from tools import score_accountant

    run_dir = tmp_path / "20260529" / "money_greedy_no_pref"
    run_dir.mkdir(parents=True)
    monthly = {
        "drivers": [
            {
                "driver_id": "D_TEST",
                "income": {
                    "gross_income": 1000.0,
                    "cost": 250.0,
                    "preference_penalty": 100.0,
                    "net_income": 650.0,
                },
                "calculation_aborted": False,
                "preference_check": {
                    "rules": [
                        {
                            "rule": "raw rule label",
                            "preference_text": "private preference text",
                            "penalty": 100.0,
                            "violations": 1,
                        }
                    ]
                },
            }
        ],
        "summary": {"total_net_income_all_drivers": 650.0, "total_preference_penalty": 100.0},
    }
    (run_dir / "monthly_income_202603.json").write_text(json.dumps(monthly), encoding="utf-8")
    (run_dir / "run_summary_202603.json").write_text(
        json.dumps({"simulation_duration_days": 31, "completed_steps": 1, "driver_simulation_failures": {}}),
        encoding="utf-8",
    )
    action_row = {
        "step": 1,
        "driver_id": "D_TEST",
        "step_elapsed_minutes": 10,
        "query_scan_cost_minutes": 5,
        "action_exec_cost_minutes": 5,
        "action": {
            "action": "wait",
            "agent_trace": {
                "query_k": 50,
                "returned_count": 20,
                "visible_count": 3,
                "debt_value": 10,
                "rescue": {
                    "positive_count": 2,
                    "safe_positive_count": 1,
                    "best_order_net": 88.0,
                    "best_order_per_hour": 20.0,
                    "wait_forensic": {
                        "wait_reason": "unit_wait_reason",
                        "best_take_id_hash": "abc",
                        "best_take_delta_official_net_estimate": 12.0,
                        "best_reposition_delta_estimate": -4.0,
                        "wait_lock_bug": True,
                        "top20_rejected_take": [{"cargo_id_hash": "h1", "hard_filter_reason": "soft"}],
                    },
                    "qwen": {"compile_calls": 1},
                },
            },
        },
        "result": {"simulation_progress_minutes": 10},
    }
    (run_dir / "actions_202603_D_TEST_unit.jsonl").write_text(json.dumps(action_row) + "\n", encoding="utf-8")

    out_dir = tmp_path / "reports"
    payload = score_accountant.build_reports(tmp_path, out_dir)
    assert payload["runs"] == 1
    score_text = (out_dir / "score_accountant.csv").read_text(encoding="utf-8")
    ledger_text = (out_dir / "preference_state_ledger.csv").read_text(encoding="utf-8")
    forensic_text = (out_dir / "forensics_samples.csv").read_text(encoding="utf-8")
    assert "True" in score_text
    assert "private preference text" not in ledger_text
    assert "raw rule label" not in ledger_text
    assert "unit_wait_reason" in forensic_text


def test_preference_repair_uses_runtime_dsl_target(monkeypatch):
    from dataclasses import replace

    monkeypatch.setattr(config, "ENABLE_NEXT_PREFERENCE_STATE_MACHINE", True)
    world1, _, _ = build_world()
    rule = CompiledPreferenceRule(
        rule_id="runtime_target",
        kind="location_relation",
        scope="date_specific",
        condition={"target_coordinates": [{"lat": 23.2, "lng": 113.2}], "date_day": 1},
        repairability="repairable_until_deadline",
        reward_or_penalty={"amount": 5000, "direction": "penalty"},
        evidence="abstract",
        confidence=0.9,
        repair_action_kinds=("reposition_to_target", "take_towards_target"),
    )
    world2 = replace(world1, rules=CompiledPreferenceSet(pref_hash="runtime", rules=(rule,)))
    option = preference_repair.build_repair_candidate(world2, "d1")
    assert option is not None
    assert option.action_type == "reposition"
    assert option.trace["target_source_kind"] == "runtime_preference_dsl_target"
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item(price=700, start_lat=23.19, start_lng=113.19, cost=60)],
        world=world2,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    take = candidate_generator.build_options(world2, visible, "d1")[0]
    assert preference_repair.take_repair_bonus(take, world2) > 0


def test_fallback_compiler_emits_executable_predicate_spec():
    world1, _, _ = build_world(preferences=[{"content": "limit 55 km", "penalty_amount": 120}])
    rule = world1.rules.rules[0]
    assert rule.predicate_type == "pickup_deadhead_limit"
    assert rule.operator == "<="
    assert "pickup_deadhead_km" in rule.fields
    assert rule.evidence_hash


def test_observed_vocab_linker_uses_current_visible_vocab_only():
    world1, _, _ = build_world(preferences=[{"content": "abstract alpha", "penalty_amount": 100}])
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item("A") | {"cargo": cargo_item("A")["cargo"] | {"cargo_name": "alpha"}}],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    links = observed_vocab_linker.link_current_observed_vocab(
        api=None,
        pref_hash=world1.pref_hash,
        preferences=world1.status.preferences,
        rules=world1.rules.rules,
        visible=visible,
    )
    assert links
    assert links[0].source == "current_observed_vocab"
    assert links[0].value_hash


def test_candidate_verifier_prices_deadhead_predicate():
    world1, _, _ = build_world(preferences=[{"content": "limit 55 km", "penalty_amount": 120}])
    option = CandidateOption(
        id="take:long-deadhead",
        action_type="take_order",
        decision_id="d1",
        direct_money=500,
        occupied_minutes=120,
        deadhead_km=70,
        haul_km=10,
        finish_minutes=120,
    )
    checks = candidate_preference_verifier.verify_candidate(option, world1, tuple())
    assert any(item.marginal_effect == "violates" and item.predicted_marginal_penalty > 0 for item in checks)


def test_pce_repair_planner_builds_no_query_rest_block(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_PCE_REPAIR_FIRST", True)
    world1, _, _ = build_world(now=0, preferences=[{"content": "abstract rest", "penalty_amount": 1000}])
    repairs = preference_repair_planner.build_repair_candidates(world1, "d1")
    assert repairs
    assert repairs[0].action_type == "wait"
    assert repairs[0].trace["repair_kind"] == "no_query_rest_block"
    assert repairs[0].trace["action_certificate_required"] is True


def test_delta_mpc_top5_decomposition_present(monkeypatch):
    monkeypatch.setattr(config, "SUBMIT_MODE", False)
    world1, _, _ = build_world()
    visible = cargo_filter.normalize_and_filter(
        raw_cargos=[cargo_item(price=700, cost=60)],
        world=world1,
        source_scope=CURRENT_ACTIONABLE,
        decision_id="d1",
    )
    options = candidate_generator.build_options(world1, visible, "d1")
    options = safety.pre_filter_and_attach_action_certificate(options, world1, {visible[0].cargo_id})
    chosen = options[0]
    action = trace_writer.attach_trace(
        {"action": "take_order", "params": {"cargo_id": visible[0].cargo_id}},
        world=world1,
        query_plan=query_policy.QueryPlan("current_small_query", k=50),
        visible_cargos=visible,
        chosen=chosen,
        options=options,
        query_minutes=5,
    )
    top5 = action["agent_trace"]["top5_delta_mpc_decomposition"]
    assert top5
    assert {"freight_direct_net", "macro_task_repair_value", "final_score"} <= set(top5[0])


def test_macro_commitment_waits_without_query():
    world1, _, _ = build_world()
    active = macro_commitment.MacroCommitment(
        active_macro_id="m1",
        macro_type="wait_at_target",
        source_automaton_ids=("r1",),
        start_time=0,
        deadline=600,
        required_duration=120,
        expected_avoided_penalty=1000,
        confidence=0.8,
    )
    stats = macro_commitment.MacroStats()
    option, remaining = macro_commitment.next_committed_option(active, stats, world1, "d1")
    assert option is not None
    assert option.action_type == "wait"
    assert option.trace["macro_candidate"] is True
    assert stats.query_skipped_due_to_macro == 1
    assert remaining is None


def test_preference_automata_snapshot_has_high_impact_type():
    world1, _, _ = build_world(preferences=[{"content": "limit 55 km", "penalty_amount": 120}])
    snap = preference_automata.snapshot(world1)
    assert snap.states
    assert snap.states[0].automaton_type == "pickup_or_haul_distance_limit"
    assert "automata_count" in snap.summary()
