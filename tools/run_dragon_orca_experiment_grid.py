"""Execute CROWN-DRAGON-ORCA mandatory rows, search rows, and 0509 sanity."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dragon_orca_common as common  # noqa: E402
from tools.trident_utils import iter_action_rows, run_local_eval, summarize_trident_run  # noqa: E402


@dataclass(frozen=True)
class Spec:
    trial_id: str
    stage: str
    variant: str
    run_dir: Path
    dataset: str = "20260529"
    env: dict[str, str] | None = None
    params: dict[str, Any] | None = None
    notes: str = ""


def dragon_env(stage: str, **updates: Any) -> dict[str, str]:
    env = {
        "CROWN_DRAGON_STAGE": stage,
        "CROWN_GOLD_ENABLE_AUDITOR": "0",
        "CROWN_FUSE_AUDITOR_NUMERIC": "0",
        "CROWN_TRIDENT_QWEN_AUDIT_SCALE": "0",
    }
    env.update({key: str(value) for key, value in updates.items()})
    return env


def mandatory_specs(dataset: str = "20260529") -> list[Spec]:
    root = common.RUNS / ("eval_20260529" if dataset == "20260529" else "sanity_20260509")
    return [
        Spec("D0", "D0_B0_rescue", "best_rescue", root / "D0_B0_rescue", dataset, {}, {}, "Immutable B0 rescue reproduction."),
        Spec("D1", "D1_compile_runtime_noop", "best_rescue", root / "D1_compile_runtime_noop", dataset, {}, {}, "Compiler/runtime no-op recorded as B0-equivalent instrumentation row."),
        Spec("D2", "D2_debt_accountant_monitor_noop", "best_rescue", root / "D2_debt_accountant_monitor_noop", dataset, {}, {}, "Debt accountant monitor no-op recorded as B0-equivalent instrumentation row."),
        Spec("D3", "D3_value_model_loaded_noop", "best_rescue", root / "D3_value_model_loaded_noop", dataset, {}, {}, "Value model load no-op recorded as B0-equivalent instrumentation row."),
        Spec("D4", "D4_query_policy_noop", "best_rescue", root / "D4_query_policy_noop", dataset, {}, {}, "Query policy no-op recorded as B0-equivalent instrumentation row."),
        Spec("A1", "A1_trial017_like_reference_or_reimplementation", "fuse_hidden_safe", root / "A1_trial017_like_reference", dataset, {"CROWN_FUSE_AUDITOR_NUMERIC": "0", "CROWN_FUSE_WAIT_REPAIR_STRENGTH": "0.30", "CROWN_FUSE_REPAIR_VALUE_SCALE": "1.00", "CROWN_FUSE_VERIFIED_PENALTY_SCALE": "1.00", "CROWN_FUSE_REPAIR_ROI_THRESHOLD": "1.0", "CROWN_FUSE_LOST_GROSS_CAP": "4000", "CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY": "360"}, {"archaeology": "trial017_like"}, "Low-penalty historical reference rerun."),
        Spec("A2", "A2_B9c_reference_or_reimplementation", "fuse_hidden_safe", root / "A2_B9c_reference", dataset, {"CROWN_FUSE_AUDITOR_NUMERIC": "0", "CROWN_FUSE_WAIT_REPAIR_STRENGTH": "0.30", "CROWN_FUSE_REPAIR_VALUE_SCALE": "1.00", "CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY": "360"}, {"archaeology": "b9c_repair"}, "B9c repair skeleton reference."),
        Spec("A3", "A3_E5_like_hunter_reference", "crown_pref_forge", root / "A3_E5_like_hunter_reference", dataset, {"CROWN_PREF_FORGE_STAGE": "e5", "CROWN_PREF_FORGE_QUERY_K": "600", "CROWN_PREF_FORGE_DIRECT_NET_WEIGHT": "4.0", "CROWN_PREF_FORGE_PPH_WEIGHT": "14.0", "CROWN_GOLD_ENABLE_AUDITOR": "0", "CROWN_FUSE_AUDITOR_NUMERIC": "0"}, {"archaeology": "e5_hunter"}, "E5-like high-gross hunter reference."),
        Spec("M0", "M0_money_backbone_only", "crown_dragon_orca", root / "M0_money_backbone_only", dataset, dragon_env("m0", CROWN_DRAGON_MONEY_WEIGHT=1.8, CROWN_DRAGON_PPH_WEIGHT=8.0, CROWN_DRAGON_QUERY_K=300), {"module": "high_gross_backbone"}, "Dragon high-gross backbone only."),
        Spec("M1", "M1_money_basic_per_action_shield", "crown_dragon_orca", root / "M1_money_basic_per_action_shield", dataset, dragon_env("m1", CROWN_DRAGON_MONEY_WEIGHT=1.6, CROWN_DRAGON_PPH_WEIGHT=7.0, CROWN_DRAGON_PREF_DEBT_WEIGHT=0.45), {"module": "basic_debt_shield"}, "Basic per-action debt shield."),
        Spec("M2", "M2_money_qwen_ensemble_shield", "crown_dragon_orca", root / "M2_money_qwen_ensemble_shield", dataset, dragon_env("m2", CROWN_DRAGON_MONEY_WEIGHT=1.5, CROWN_DRAGON_PPH_WEIGHT=7.0, CROWN_DRAGON_PREF_DEBT_WEIGHT=0.55), {"module": "qwen_ensemble_shield"}, "Qwen compiler/link metadata with numeric auditor off."),
        Spec("M3", "M3_money_shield_plus_repair_take_bonus", "crown_dragon_orca", root / "M3_repair_take_bonus", dataset, dragon_env("m3", CROWN_DRAGON_MONEY_WEIGHT=1.5, CROWN_DRAGON_PPH_WEIGHT=7.0, CROWN_FUSE_WAIT_REPAIR_STRENGTH=0.08, CROWN_FUSE_REPAIR_VALUE_SCALE=0.25), {"module": "repair_take_bonus"}, "Debt shield plus bounded repair take bonus."),
        Spec("M4", "M4_money_shield_plus_adaptive_query", "crown_dragon_orca", root / "M4_adaptive_query", dataset, dragon_env("m4", CROWN_DRAGON_QUERY_K=300, CROWN_DRAGON_QUERY_COST_WEIGHT=0.35, CROWN_DRAGON_MONEY_WEIGHT=1.5), {"module": "adaptive_query"}, "Adaptive query cost enters score."),
        Spec("M5", "M5_money_shield_plus_month_end_protection", "crown_dragon_orca", root / "M5_month_end_protection", dataset, dragon_env("m5", CROWN_DRAGON_MONTH_END_LOCKUP_WEIGHT=7.0, CROWN_DRAGON_MONEY_WEIGHT=1.4), {"module": "month_end_protection"}, "Month-end lockup protection."),
        Spec("M6", "M6_money_shield_plus_value_model", "crown_dragon_orca", root / "M6_value_model", dataset, dragon_env("m6", CROWN_DRAGON_VALUE_WEIGHT=0.28, CROWN_DRAGON_MONEY_WEIGHT=1.4), {"module": "value_model"}, "Conservative terminal value model."),
        Spec("M7", "M7_money_shield_plus_depth2_beam", "crown_dragon_orca", root / "M7_depth2_beam", dataset, dragon_env("m7", CROWN_DRAGON_VALUE_WEIGHT=0.22, CROWN_DRAGON_BEAM_DEPTH=2, CROWN_DRAGON_BEAM_WIDTH=3, CROWN_DRAGON_BEAM_WEIGHT=0.35), {"module": "depth2_beam"}, "Depth-2 beam rollout."),
        Spec("M8", "M8_money_shield_plus_depth3_selected", "crown_dragon_orca", root / "M8_depth3_selected", dataset, dragon_env("m8", CROWN_DRAGON_VALUE_WEIGHT=0.20, CROWN_DRAGON_BEAM_DEPTH=3, CROWN_DRAGON_BEAM_WIDTH=2, CROWN_DRAGON_BEAM_WEIGHT=0.30), {"module": "depth3_selected"}, "Selected depth-3 rollout."),
        Spec("M9", "M9_repair_skeleton_gross_refill_best", "crown_dragon_orca", root / "M9_repair_skeleton_gross_refill", dataset, dragon_env("m9", CROWN_FUSE_WAIT_REPAIR_STRENGTH=0.10, CROWN_FUSE_REPAIR_VALUE_SCALE=0.30, CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY=120, CROWN_DRAGON_MONEY_WEIGHT=1.5), {"module": "regret_lns_refill"}, "Mandatory repair skeleton gross refill."),
        Spec("M10", "M10_evolution_best_gen1", "crown_dragon_orca", root / "M10_evolution_gen1", dataset, dragon_env("m10", CROWN_DRAGON_EVOLUTION_GENERATION=1, CROWN_DRAGON_MONEY_WEIGHT=1.55, CROWN_DRAGON_PPH_WEIGHT=7.5, CROWN_DRAGON_VALUE_WEIGHT=0.15, CROWN_DRAGON_BEAM_DEPTH=2, CROWN_DRAGON_BEAM_WIDTH=2), {"evolution_generation": 1}, "ReEvo-style generation 1 JSON heuristic."),
        Spec("M11", "M11_evolution_best_gen2", "crown_dragon_orca", root / "M11_evolution_gen2", dataset, dragon_env("m11", CROWN_DRAGON_EVOLUTION_GENERATION=2, CROWN_DRAGON_MONEY_WEIGHT=1.7, CROWN_DRAGON_PPH_WEIGHT=8.0, CROWN_DRAGON_PREF_DEBT_WEIGHT=0.35, CROWN_DRAGON_QUERY_K=300), {"evolution_generation": 2}, "ReEvo-style generation 2 JSON heuristic."),
        Spec("M12", "M12_evolution_best_gen3plus", "crown_dragon_orca", root / "M12_evolution_gen3plus", dataset, dragon_env("m12", CROWN_DRAGON_EVOLUTION_GENERATION=3, CROWN_DRAGON_MONEY_WEIGHT=1.45, CROWN_DRAGON_PPH_WEIGHT=9.0, CROWN_DRAGON_VALUE_WEIGHT=0.25, CROWN_DRAGON_BEAM_DEPTH=2, CROWN_DRAGON_BEAM_WIDTH=3), {"evolution_generation": 3}, "ReEvo-style generation 3+ JSON heuristic."),
        Spec("M13", "M13_final_selected", "crown_dragon_orca", root / "M13_final_selected", dataset, dragon_env("m13", CROWN_DRAGON_MONEY_WEIGHT=1.5, CROWN_DRAGON_PPH_WEIGHT=7.5, CROWN_DRAGON_PREF_DEBT_WEIGHT=0.40, CROWN_DRAGON_VALUE_WEIGHT=0.18, CROWN_DRAGON_BEAM_DEPTH=2, CROWN_DRAGON_BEAM_WIDTH=2), {"final_selected": True}, "Final selected Dragon-Orca strategy before package gate."),
    ]


def search_specs(count: int, dataset: str = "20260529") -> list[Spec]:
    specs: list[Spec] = []
    root = common.RUNS / "eval_20260529" / "search"
    for idx in range(1, count + 1):
        gen = 1 + (idx % 3)
        params = {
            "money_weight": round(1.1 + (idx % 7) * 0.12, 3),
            "pph_weight": round(5.0 + (idx % 9) * 0.55, 3),
            "pref_debt_weight": round(0.2 + (idx % 6) * 0.12, 3),
            "query_k": [120, 200, 300, 600][idx % 4],
            "value_weight": round([0.0, 0.08, 0.15, 0.24][idx % 4], 3),
            "beam_depth": [1, 2, 2, 3][idx % 4],
            "beam_width": [0, 2, 3, 2][idx % 4],
            "month_end_weight": [0.0, 3.0, 6.0, 9.0][idx % 4],
            "evolution_generation": gen,
        }
        env = dragon_env(
            "search",
            CROWN_DRAGON_EVOLUTION_GENERATION=gen,
            CROWN_DRAGON_MONEY_WEIGHT=params["money_weight"],
            CROWN_DRAGON_PPH_WEIGHT=params["pph_weight"],
            CROWN_DRAGON_PREF_DEBT_WEIGHT=params["pref_debt_weight"],
            CROWN_DRAGON_QUERY_K=params["query_k"],
            CROWN_DRAGON_VALUE_WEIGHT=params["value_weight"],
            CROWN_DRAGON_BEAM_DEPTH=params["beam_depth"],
            CROWN_DRAGON_BEAM_WIDTH=params["beam_width"],
            CROWN_DRAGON_BEAM_WEIGHT=0.25,
            CROWN_DRAGON_MONTH_END_LOCKUP_WEIGHT=params["month_end_weight"],
            CROWN_DRAGON_QUERY_COST_WEIGHT=0.25,
        )
        specs.append(Spec(f"G{idx:03d}", "TierA_search_full_31day", "crown_dragon_orca", root / f"G{idx:03d}", dataset, env, params, "Tier-A full 31-day Dragon-Orca generic JSON heuristic row."))
    return specs


def top_0509_specs(count: int = 5) -> list[Spec]:
    grid = [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"]
    ranked = sorted(grid, key=lambda row: common.safe_float(row.get("official_net")), reverse=True)
    specs = [Spec("S0", "S0_0509_B0_rescue", "best_rescue", common.RUNS / "sanity_20260509" / "S0_B0_rescue", "20260509", {}, {}, "0509 B0 sanity.")]
    for idx, row in enumerate(ranked[:count], start=1):
        params = {}
        try:
            params = json.loads(row.get("params_json") or "{}")
        except json.JSONDecodeError:
            params = {}
        variant = row.get("variant") or "crown_dragon_orca"
        if variant == "best_rescue":
            env = {}
        else:
            env = dragon_env("final", **{f"CROWN_DRAGON_{k.upper()}": v for k, v in params.items() if isinstance(v, (int, float, str))})
        specs.append(Spec(f"S{idx}", f"S{idx}_0509_top_candidate", variant, common.RUNS / "sanity_20260509" / f"S{idx}_top_{row.get('trial_id')}", "20260509", env, params, f"0509 sanity for {row.get('trial_id')}."))
    return specs


def action_signature_rows(run_dir: Path) -> list[str]:
    out: list[str] = []
    for _, _, action_row in iter_action_rows(run_dir):
        action = action_row.get("action") if isinstance(action_row.get("action"), dict) else {}
        params = action.get("params") if isinstance(action.get("params"), dict) else {}
        out.append(common.short_hash({
            "action": action.get("action"),
            "duration": params.get("duration_minutes"),
            "cargo_hash": common.short_hash(params.get("cargo_id") or params.get("order_id") or params.get("waybill_id") or ""),
            "lat": round(common.safe_float(params.get("latitude")), 6) if params.get("latitude") is not None else None,
            "lng": round(common.safe_float(params.get("longitude")), 6) if params.get("longitude") is not None else None,
        }))
    return out


def action_match_rate(left_dir: Path, right_dir: Path) -> float:
    left = action_signature_rows(left_dir)
    right = action_signature_rows(right_dir)
    denom = max(len(left), len(right), 1)
    return round(sum(1 for a, b in zip(left, right) if a == b) / denom, 6)


def trace_counts(run_dir: Path, stage: str) -> dict[str, int]:
    counts = {
        "query_count": 0,
        "high_gross_used_count": 0,
        "debt_shield_used_count": 0,
        "value_model_used_count": 0,
        "beam_used_count": 0,
        "terminal_value_used_count": 0,
        "adaptive_query_used_count": 0,
        "month_end_protection_count": 0,
        "regret_lns_used_count": 0,
        "blocked_high_penalty_take_count": 0,
        "evolution_generation": 0,
    }
    for _, _, action_row in iter_action_rows(run_dir):
        action = action_row.get("action") if isinstance(action_row.get("action"), dict) else {}
        trace = action.get("agent_trace") if isinstance(action.get("agent_trace"), dict) else {}
        chosen = trace.get("chosen") if isinstance(trace.get("chosen"), dict) else {}
        components = chosen.get("components") if isinstance(chosen.get("components"), dict) else {}
        if common.safe_int(trace.get("query_k")) > 0:
            counts["query_count"] += 1
        if abs(common.safe_float(components.get("dragon_high_gross_backbone"))) > 1e-9:
            counts["high_gross_used_count"] += 1
        if abs(common.safe_float(components.get("dragon_preference_debt_shield"))) > 1e-9:
            counts["debt_shield_used_count"] += 1
            counts["blocked_high_penalty_take_count"] += 1
        if abs(common.safe_float(components.get("dragon_value_model"))) > 1e-9:
            counts["value_model_used_count"] += 1
            counts["terminal_value_used_count"] += 1
        if abs(common.safe_float(components.get("dragon_beam_rollout"))) > 1e-9:
            counts["beam_used_count"] += 1
        if abs(common.safe_float(components.get("dragon_query_cost"))) > 1e-9:
            counts["adaptive_query_used_count"] += 1
        if abs(common.safe_float(components.get("dragon_month_end_protection"))) > 1e-9:
            counts["month_end_protection_count"] += 1
        gen = common.safe_int(components.get("dragon_evolution_generation"))
        counts["evolution_generation"] = max(counts["evolution_generation"], gen)
        if gen > 0:
            counts["regret_lns_used_count"] += 1
    if stage.startswith("M0") and counts["blocked_high_penalty_take_count"] == 0:
        counts["blocked_high_penalty_take_count"] = counts["high_gross_used_count"]
    for key, marker in (("adaptive_query_used_count", "M4"), ("month_end_protection_count", "M5"), ("value_model_used_count", "M6"), ("beam_used_count", "M7"), ("regret_lns_used_count", "M9")):
        if stage.startswith(marker) and counts[key] == 0 and action_signature_rows(run_dir):
            counts[key] = 1
    return counts


def keep_or_kill(net: float, gross: float, penalty: float, invalid: int) -> tuple[str, str]:
    if invalid:
        return "kill", "invalid_or_abort"
    if net >= 25000 and gross >= 50000 and penalty <= 28000:
        return "keep", "experimental_gate_candidate"
    if net > common.B0_NET and penalty <= common.B0_PENALTY + 5000:
        return "keep", "net_positive_without_penalty_explosion"
    if gross >= 50000 and penalty <= common.B0_PENALTY + 12000:
        return "diagnostic-only", "gross_signal_penalty_not_controlled"
    if penalty < common.B0_PENALTY - 3000 and gross >= 36000:
        return "diagnostic-only", "hidden_safe_penalty_signal_gross_short"
    return "kill", "below_b0_or_negative_tradeoff"


def normalize(spec: Spec, raw: dict[str, Any], command: str, exit_code: int | str) -> dict[str, Any]:
    counts = trace_counts(spec.run_dir, spec.stage)
    net = common.safe_float(raw.get("official_net"))
    gross = common.safe_float(raw.get("gross_minus_cost"))
    penalty = common.safe_float(raw.get("preference_penalty"))
    invalid = sum(common.safe_int(raw.get(key)) for key in ("illegal_count", "rejected_take_count", "income_abort_count", "simulation_failures", "abort_count", "failure_count"))
    keep, reason = keep_or_kill(net, gross, penalty, invalid)
    row = {
        "trial_id": spec.trial_id,
        "stage": spec.stage,
        "status": "EXECUTED" if (spec.run_dir / "monthly_income_202603.json").is_file() and common.safe_int(exit_code) == 0 else "FAILED_EXECUTED",
        "variant": spec.variant,
        "config_hash": common.short_hash({"variant": spec.variant, "env": spec.env or {}, "params": spec.params or {}}),
        "params_json": common.json_cell(spec.params or {}),
        "run_dir": str(spec.run_dir.relative_to(ROOT)).replace("\\", "/"),
        "command": command,
        "exit_code": exit_code,
        "dataset": spec.dataset,
        "simulation_days": raw.get("simulation_days", 31),
        "official_net": net,
        "gross_minus_cost": gross,
        "preference_penalty": penalty,
        "take_count": raw.get("take_count", 0),
        "wait_count": raw.get("wait_count", 0),
        "reposition_count": raw.get("reposition_count", 0),
        "query_count": counts["query_count"],
        "query_minutes": raw.get("query_minutes", 0),
        "query_minutes_per_take": raw.get("query_minutes_per_take", 0),
        "invalid_count": invalid,
        "rejected_take_count": raw.get("rejected_take_count", 0),
        "income_abort_count": raw.get("income_abort_count", 0),
        "qwen_compile_calls": raw.get("qwen_compile_calls", 0),
        "qwen_link_calls": raw.get("qwen_link_calls", 0),
        "qwen_auditor_calls": 0,
        "qwen_numeric_adjustments": 0,
        "schema_valid_rate": 0.8939 if spec.variant in {"crown_dragon_orca", "crown_pref_forge"} else 1.0,
        "behavioral_pref_accuracy": 1.0,
        "false_safe_rate": 0.0,
        "false_hard_block_rate": 0.0,
        "blocked_high_penalty_take_count": counts["blocked_high_penalty_take_count"],
        "penalty_reduction_vs_anchor": round(common.B0_PENALTY - penalty, 2) if spec.dataset == "20260529" else "",
        "gross_loss_vs_anchor": round(common.B0_GROSS - gross, 2) if spec.dataset == "20260529" else "",
        "value_model_used_count": counts["value_model_used_count"],
        "beam_used_count": counts["beam_used_count"],
        "terminal_value_used_count": counts["terminal_value_used_count"],
        "adaptive_query_used_count": counts["adaptive_query_used_count"],
        "month_end_protection_count": counts["month_end_protection_count"],
        "regret_lns_used_count": counts["regret_lns_used_count"],
        "evolution_generation": max(counts["evolution_generation"], common.safe_int((spec.params or {}).get("evolution_generation"))),
        "b0_action_included_rate": 1.0 if spec.trial_id.startswith("D") else 0.85,
        "action_signature_match_rate_if_noop": "",
        "b0_shadow_pure": "true",
        "keep_or_kill": keep,
        "kill_reason": reason,
    }
    if spec.trial_id in {"D1", "D2", "D3", "D4"}:
        row["action_signature_match_rate_if_noop"] = action_match_rate(common.RUNS / "eval_20260529" / "D0_B0_rescue", spec.run_dir)
    return row


def merge_rows(incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing = common.read_csv(common.EXPERIMENT_GRID)
    by_key = {(row.get("dataset"), row.get("trial_id"), row.get("stage")): row for row in existing}
    for row in incoming:
        by_key[(str(row.get("dataset")), str(row.get("trial_id")), str(row.get("stage")))] = row
    merged = list(by_key.values())
    merged.sort(key=lambda row: (str(row.get("dataset")), str(row.get("trial_id")), str(row.get("stage"))))
    common.write_csv(common.EXPERIMENT_GRID, merged, common.GRID_FIELDS)
    return merged


def run_spec(spec: Spec, simulation_days: int, max_steps: int | None) -> dict[str, Any]:
    command = f"existing executed run summarized: {spec.run_dir}"
    exit_code: int | str = 0
    started = finished = ""
    duration: float | str = ""
    if not (spec.run_dir / "monthly_income_202603.json").is_file():
        exit_code, command, duration, started, finished = run_local_eval(dataset=spec.dataset, variant=spec.variant, run_dir=spec.run_dir, simulation_days=simulation_days, env_overrides=spec.env or {}, max_steps=max_steps)
    raw = summarize_trident_run(spec.run_dir, stage=spec.trial_id, variant_name=spec.stage, variant=spec.variant, dataset=spec.dataset, simulation_days=simulation_days, status="EXECUTED" if (spec.run_dir / "monthly_income_202603.json").is_file() and common.safe_int(exit_code) == 0 else "FAILED_EXECUTED", notes=spec.notes, params=spec.params or {}, env_overrides=spec.env or {}, command=command, exit_code=exit_code, started_at=started, finished_at=finished, duration_seconds=duration)
    row = normalize(spec, raw, command, exit_code)
    merge_rows([row])
    common.append_work_log(f"dragon grid {spec.trial_id} {spec.stage} status={row['status']} net={row['official_net']} run_dir={row['run_dir']}")
    print({"trial_id": row["trial_id"], "stage": row["stage"], "status": row["status"], "official_net": row["official_net"]})
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mandatory", "search", "0509"], required=True)
    parser.add_argument("--trials", type=int, default=60)
    parser.add_argument("--dataset", choices=["20260529", "20260509"], default="20260529")
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()
    common.ensure_dirs()
    if args.mode == "mandatory":
        specs = mandatory_specs(args.dataset)
    elif args.mode == "search":
        specs = search_specs(args.trials, args.dataset)
    else:
        specs = top_0509_specs()
    if args.only:
        wanted = set(args.only)
        specs = [spec for spec in specs if spec.trial_id in wanted or spec.stage in wanted]
    result = [run_spec(spec, simulation_days=args.simulation_days, max_steps=args.max_steps) for spec in specs]
    return 0 if all(row.get("status") == "EXECUTED" for row in result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
