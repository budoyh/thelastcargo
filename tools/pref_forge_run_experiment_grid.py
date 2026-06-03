"""Execute Pref-Forge mandatory official rows and focused search rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common  # noqa: E402
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


def _pref_env(stage: str, **updates: Any) -> dict[str, str]:
    env = {
        "CROWN_PREF_FORGE_STAGE": stage,
        "CROWN_GOLD_ENABLE_AUDITOR": "0",
        "CROWN_FUSE_AUDITOR_NUMERIC": "0",
        "CROWN_TRIDENT_QWEN_AUDIT_SCALE": "0",
    }
    env.update({key: str(value) for key, value in updates.items()})
    return env


def mandatory_specs(dataset: str = "20260529") -> list[Spec]:
    root = common.RUNS / ("eval_20260529" if dataset == "20260529" else "eval_20260509")
    return [
        Spec("E0", "E0_B0_rescue", "best_rescue", root / "E0_B0_rescue", dataset, {}, {}, "Immutable B0 rescue reproduction."),
        Spec("E1", "E1_compile_log_only_noop", "best_rescue", root / "E1_compile_log_only_noop", dataset, {}, {}, "No-op compile/log isolation; must match E0."),
        Spec("E2", "E2_monitor_update_only_noop", "best_rescue", root / "E2_monitor_update_only_noop", dataset, {}, {}, "No-op monitor isolation; must match E0."),
        Spec("E3", "E3_preference_delta_scorer_only_no_repair", "crown_pref_forge", root / "E3_preference_delta_scorer_only_no_repair", dataset, _pref_env("e3"), {}, "Preference delta scorer with repair off."),
        Spec("E4", "E4_avoid_limit_shield_only", "crown_pref_forge", root / "E4_avoid_limit_shield_only", dataset, _pref_env("e4"), {}, "Avoid/limit shield only; auditor numeric off."),
        Spec(
            "E5",
            "E5_high_quality_order_hunter_only",
            "crown_pref_forge",
            root / "E5_high_quality_order_hunter_only_v13",
            dataset,
            _pref_env(
                "e5",
                CROWN_PREF_FORGE_QUERY_K=600,
                CROWN_PREF_FORGE_DIRECT_NET_WEIGHT=4.0,
                CROWN_PREF_FORGE_PPH_WEIGHT=14.0,
                CROWN_PREF_FORGE_MAX_DURATION_HOURS=20,
                CROWN_PREF_FORGE_DEADHEAD_THRESHOLD_KM=110,
                CROWN_PREF_FORGE_REST_GUARD=1,
                CROWN_PREF_FORGE_SOFT_REST_GUARD=0,
                CROWN_PREF_FORGE_REST_ESCAPE_DIRECT_NET=1000,
                CROWN_PREF_FORGE_REST_ESCAPE_MIN_WAITS=1,
                CROWN_PREF_FORGE_REST_ESCAPE_MAX_HOURS=18,
                CROWN_PREF_FORGE_FORCE_TAKE_AFTER_WAITS=1,
                CROWN_PREF_FORGE_SOFT_PREF_CAP=300,
                CROWN_PREF_FORGE_PREF_DEBT_MULT=4,
                CROWN_PREF_FORGE_SOFT_PREF_MULT=8,
            ),
            {"hunter": "gross_gate_v13", "rest_guard": "hard_with_extreme_value_wait_escape", "soft_pref": "strong"},
            "High-Quality Hunter gross gate retune with hard rest guard and extreme-value wait escape.",
        ),
        Spec("E6", "E6_high_quality_order_hunter_plus_shield", "crown_pref_forge", root / "E6_high_quality_order_hunter_plus_shield", dataset, _pref_env("e6", CROWN_PREF_FORGE_QUERY_K=600), {}, "Hunter plus shield."),
        Spec("E7", "E7_E6_plus_repair_take_bonus_only", "crown_pref_forge", root / "E7_E6_plus_repair_take_bonus_only", dataset, _pref_env("e7", CROWN_PREF_FORGE_QUERY_K=600), {}, "Repair take bonus only."),
        Spec("E8", "E8_E7_plus_minimal_repair_planner", "crown_pref_forge", root / "E8_E7_plus_minimal_repair_planner", dataset, _pref_env("e8", CROWN_PREF_FORGE_QUERY_K=600, CROWN_FUSE_WAIT_REPAIR_STRENGTH=0.10, CROWN_FUSE_REPAIR_VALUE_SCALE=0.35, CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY=120), {}, "Minimal repair planner."),
        Spec("E9", "E9_E8_plus_adaptive_query_k", "crown_pref_forge", root / "E9_E8_plus_adaptive_query_k", dataset, _pref_env("e9", CROWN_PREF_FORGE_QUERY_K=600, CROWN_FUSE_WAIT_REPAIR_STRENGTH=0.10, CROWN_FUSE_REPAIR_VALUE_SCALE=0.35, CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY=120), {}, "Adaptive query k."),
        Spec("E10", "E10_E9_plus_small_terminal_value_only_if_positive", "crown_pref_forge", root / "E10_E9_plus_small_terminal_value_only_if_positive", dataset, _pref_env("e10", CROWN_PREF_FORGE_QUERY_K=600, CROWN_PREF_FORGE_TERMINAL_VALUE_WEIGHT=0.03), {}, "Small terminal value diagnostic."),
        Spec("E11", "E11_trial017_like_hidden_safe_reference", "fuse_hidden_safe", root / "E11_trial017_like_hidden_safe_reference", dataset, {"CROWN_FUSE_AUDITOR_NUMERIC": "0", "CROWN_FUSE_WAIT_REPAIR_STRENGTH": "0.30", "CROWN_FUSE_REPAIR_VALUE_SCALE": "1.00", "CROWN_FUSE_VERIFIED_PENALTY_SCALE": "1.00", "CROWN_FUSE_REPAIR_ROI_THRESHOLD": "1.0", "CROWN_FUSE_LOST_GROSS_CAP": "4000", "CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY": "360"}, {"seed": "trial017_like"}, "Current-branch hidden-safe reference rerun."),
        Spec("E12", "E12_repair_skeleton_gross_refill_mandatory", "crown_pref_forge", root / "E12_repair_skeleton_gross_refill_mandatory", dataset, _pref_env("e12", CROWN_PREF_FORGE_QUERY_K=600, CROWN_PREF_FORGE_DIRECT_NET_WEIGHT=2.6, CROWN_PREF_FORGE_PPH_WEIGHT=9.0, CROWN_FUSE_WAIT_REPAIR_STRENGTH=0.15, CROWN_FUSE_REPAIR_VALUE_SCALE=0.40, CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY=120), {"gross_refill": True}, "Mandatory repair skeleton gross refill."),
        Spec("E13", "E13_final_selected", "crown_pref_forge", root / "E13_final_selected", dataset, _pref_env("e13", CROWN_PREF_FORGE_QUERY_K=600, CROWN_PREF_FORGE_DIRECT_NET_WEIGHT=2.4, CROWN_PREF_FORGE_PPH_WEIGHT=8.0), {}, "Final selected before package policy."),
    ]


def _search_params(limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    query_values = [100, 300, 600]
    direct_weights = [1.4, 1.8, 2.2, 2.6]
    pph_weights = [5.0, 7.0, 9.0]
    max_hours = [10, 14, 18, 24]
    deadhead = [50, 75, 100, 140]
    shields = [0.35, 0.55, 0.80]
    repair_budgets = [0, 60, 120, 240]
    idx = 0
    seen: set[str] = set()
    while len(rows) < limit:
        params = {
            "query_k": query_values[idx % len(query_values)],
            "direct_weight": direct_weights[(idx // 2) % len(direct_weights)],
            "pph_weight": pph_weights[(idx // 3) % len(pph_weights)],
            "max_duration_hours": max_hours[(idx // 5) % len(max_hours)],
            "deadhead_threshold": deadhead[(idx // 7) % len(deadhead)],
            "unknown_soft_risk_cap": shields[(idx // 11) % len(shields)],
            "minimal_repair_budget": repair_budgets[(idx // 13) % len(repair_budgets)],
            "terminal_value_weight": 0.03 if idx % 17 == 0 else 0.0,
        }
        key = common.json_cell(params)
        idx += 1
        if key in seen:
            continue
        seen.add(key)
        rows.append(params)
    return rows


def search_specs(count: int, dataset: str = "20260529") -> list[Spec]:
    specs = []
    root = common.RUNS / "eval_20260529" / "search"
    for idx, params in enumerate(_search_params(count), start=1):
        trial = f"G{idx:03d}"
        stage_name = "GRID_pref_forge_full_31day"
        env = _pref_env(
            "grid",
            CROWN_PREF_FORGE_QUERY_K=params["query_k"],
            CROWN_PREF_FORGE_DIRECT_NET_WEIGHT=params["direct_weight"],
            CROWN_PREF_FORGE_PPH_WEIGHT=params["pph_weight"],
            CROWN_PREF_FORGE_MAX_DURATION_HOURS=params["max_duration_hours"],
            CROWN_PREF_FORGE_DEADHEAD_THRESHOLD_KM=params["deadhead_threshold"],
            CROWN_PREF_FORGE_TERMINAL_VALUE_WEIGHT=params["terminal_value_weight"],
            CROWN_FUSE_WAIT_REPAIR_STRENGTH=0.10 if params["minimal_repair_budget"] else 0.0,
            CROWN_FUSE_REPAIR_VALUE_SCALE=0.35,
            CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY=params["minimal_repair_budget"],
            CROWN_FUSE_UNKNOWN_SOFT_RISK=params["unknown_soft_risk_cap"],
        )
        specs.append(Spec(trial, stage_name, "crown_pref_forge", root / trial, dataset, env, params, "Focused Pref-Forge full 31-day search row."))
    return specs


def top_0509_specs(count: int = 5) -> list[Spec]:
    rows = [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"]
    candidates = sorted(rows, key=lambda row: common.safe_float(row.get("official_net")), reverse=True)
    specs = [Spec("S0", "S0_0509_B0_rescue", "best_rescue", common.RUNS / "eval_20260509" / "S0_0509_B0_rescue", "20260509", {}, {}, "0509 B0 sanity.")]
    for idx, row in enumerate(candidates[:count], start=1):
        params = {}
        try:
            params = json.loads(row.get("params_json") or "{}")
        except json.JSONDecodeError:
            params = {}
        if row.get("variant") == "best_rescue":
            variant = "best_rescue"
            env = {}
        else:
            variant = "crown_pref_forge"
            env = _pref_env(
                "grid",
                CROWN_PREF_FORGE_QUERY_K=params.get("query_k", 600),
                CROWN_PREF_FORGE_DIRECT_NET_WEIGHT=params.get("direct_weight", 2.4),
                CROWN_PREF_FORGE_PPH_WEIGHT=params.get("pph_weight", 8.0),
            )
        trial = f"S{idx}"
        specs.append(Spec(trial, f"S{idx}_0509_top_candidate", variant, common.RUNS / "eval_20260509" / f"S{idx}_0509_top_candidate", "20260509", env, params, "0509 sanity top candidate."))
    return specs


def _action_signature_rows(run_dir: Path) -> list[str]:
    rows = []
    for _, _, action_row in iter_action_rows(run_dir):
        action = action_row.get("action") if isinstance(action_row.get("action"), dict) else {}
        params = action.get("params") if isinstance(action.get("params"), dict) else {}
        payload = {
            "action": action.get("action"),
            "duration": params.get("duration_minutes"),
            "order": common.short_hash(params.get("cargo_id") or params.get("order_id") or params.get("waybill_id") or ""),
            "lat": round(common.safe_float(params.get("latitude")), 6) if params.get("latitude") is not None else None,
            "lng": round(common.safe_float(params.get("longitude")), 6) if params.get("longitude") is not None else None,
        }
        rows.append(common.short_hash(payload, 16))
    return rows


def action_match_rate(a: Path, b: Path) -> float:
    left = _action_signature_rows(a)
    right = _action_signature_rows(b)
    if not left and not right:
        return 1.0
    denom = max(len(left), len(right), 1)
    same = sum(1 for x, y in zip(left, right) if x == y)
    return round(same / denom, 6)


def normalize_row(spec: Spec, raw: dict[str, Any], command: str, exit_code: int | str) -> dict[str, Any]:
    net = common.safe_float(raw.get("official_net"))
    gross = common.safe_float(raw.get("gross_minus_cost"))
    penalty = common.safe_float(raw.get("preference_penalty"))
    invalid = sum(common.safe_int(raw.get(key)) for key in ("illegal_count", "rejected_take_count", "income_abort_count", "simulation_failures", "abort_count"))
    e11 = next((row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("trial_id") == "E11" and row.get("dataset") == spec.dataset), None)
    e11_net = common.safe_float(e11.get("official_net")) if e11 else 0.0
    row = {
        "trial_id": spec.trial_id,
        "stage": spec.stage,
        "status": "EXECUTED" if raw.get("status") in {"EXECUTED", "OK", "EXISTING"} and common.safe_int(exit_code) == 0 else "FAILED_EXECUTED",
        "run_dir": str(spec.run_dir.relative_to(ROOT)).replace("\\", "/"),
        "command": command,
        "exit_code": exit_code,
        "dataset": spec.dataset,
        "official_net": net,
        "gross_minus_cost": gross,
        "preference_penalty": penalty,
        "take_count": raw.get("take_count", 0),
        "wait_count": raw.get("wait_count", 0),
        "reposition_count": raw.get("reposition_count", 0),
        "query_count": raw.get("query_minutes", 0),
        "query_minutes_per_take": raw.get("query_minutes_per_take", 0),
        "qwen_compile_calls": raw.get("qwen_compile_calls", 0),
        "qwen_link_calls": raw.get("qwen_link_calls", 0),
        "qwen_auditor_calls": raw.get("qwen_auditor_calls", 0),
        "qwen_numeric_adjustments": 0,
        "invalid_count": invalid,
        "rejected_take_count": raw.get("rejected_take_count", 0),
        "income_abort_count": raw.get("income_abort_count", 0),
        "config_json_hash": common.short_hash({"variant": spec.variant, "env": spec.env or {}, "params": spec.params or {}}, 16),
        "notes": spec.notes,
        "simulation_days": raw.get("simulation_days", 31),
        "variant": spec.variant,
        "action_signature_match_rate": "",
        "net_delta_vs_b0": round(net - common.B0_NET, 2) if spec.dataset == "20260529" else "",
        "gross_delta_vs_b0": round(gross - common.B0_GROSS, 2) if spec.dataset == "20260529" else "",
        "penalty_delta_vs_b0": round(penalty - common.B0_PENALTY, 2) if spec.dataset == "20260529" else "",
        "refill_gross_gain": round(max(0.0, gross - (common.safe_float(e11.get("gross_minus_cost")) if e11 else gross)), 2) if spec.trial_id == "E12" else "",
        "penalty_reintroduced": round(max(0.0, penalty - (common.safe_float(e11.get("preference_penalty")) if e11 else penalty)), 2) if spec.trial_id == "E12" else "",
        "official_net_delta_vs_e11": round(net - e11_net, 2) if spec.trial_id == "E12" and e11 else "",
        "b0_shadow_pure": "true",
        "extra_api_calls_for_shadow": 0,
        "keep_or_kill": keep_or_kill(net, gross, penalty, invalid, spec.trial_id),
        "params_json": common.json_cell(spec.params or {}),
    }
    if spec.trial_id in {"E1", "E2"}:
        row["action_signature_match_rate"] = action_match_rate(common.RUNS / "eval_20260529" / "E0_B0_rescue", spec.run_dir)
    return row


def keep_or_kill(net: float, gross: float, penalty: float, invalid: int, trial_id: str) -> str:
    if invalid:
        return "kill_invalid_run"
    if trial_id == "E0":
        return "keep_b0_reference"
    if net >= 15000 and gross >= 42000 and penalty <= 32000:
        return "keep_experimental_candidate"
    if net > common.B0_NET and penalty < common.B0_PENALTY:
        return "keep_hidden_safe_candidate"
    if gross >= common.B0_GROSS or (gross - common.B0_GROSS >= -2000 and penalty - common.B0_PENALTY <= -5000):
        return "diagnostic_retain_family"
    return "kill_below_pref_forge_retention_gate"


def merge_rows(incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing = common.read_csv(common.EXPERIMENT_GRID)
    by_key = {(row.get("dataset"), row.get("trial_id"), row.get("stage")): row for row in existing}
    for row in incoming:
        by_key[(str(row.get("dataset")), str(row.get("trial_id")), str(row.get("stage")))] = row
    rows = list(by_key.values())
    rows.sort(key=lambda row: (str(row.get("dataset")), str(row.get("trial_id")), str(row.get("stage"))))
    common.write_csv(common.EXPERIMENT_GRID, rows, common.GRID_FIELDS)
    return rows


def run_spec(spec: Spec, *, simulation_days: int, max_steps: int | None) -> dict[str, Any]:
    command = f"existing run summarized: {spec.run_dir}"
    exit_code: int | str = 0
    if not (spec.run_dir / "monthly_income_202603.json").is_file():
        exit_code, command, _duration, _started, _finished = run_local_eval(
            dataset=spec.dataset,
            variant=spec.variant,
            run_dir=spec.run_dir,
            simulation_days=simulation_days,
            env_overrides=spec.env or {},
            max_steps=max_steps,
        )
    raw = summarize_trident_run(
        spec.run_dir,
        stage=spec.trial_id,
        variant_name=spec.stage,
        variant=spec.variant,
        dataset=spec.dataset,
        simulation_days=simulation_days,
        status="EXECUTED" if (spec.run_dir / "monthly_income_202603.json").is_file() and int(exit_code or 0) == 0 else "FAILED_EXECUTED",
        notes=spec.notes,
        params=spec.params or {},
        env_overrides=spec.env or {},
        command=command,
        exit_code=exit_code,
    )
    row = normalize_row(spec, raw, command, exit_code)
    merge_rows([row])
    common.append_ledger(
        {
            "stage": spec.stage,
            "command": command,
            "run_dir": row["run_dir"],
            "exit_code": exit_code,
            "official_net": row["official_net"],
            "gross_minus_cost": row["gross_minus_cost"],
            "preference_penalty": row["preference_penalty"],
            "decision": row["keep_or_kill"],
        }
    )
    print({"trial_id": spec.trial_id, "stage": spec.stage, "status": row["status"], "official_net": row["official_net"]})
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mandatory", "search", "0509"], required=True)
    parser.add_argument("--trials", type=int, default=60)
    parser.add_argument("--dataset", choices=["20260529", "20260509"], default="20260529")
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--only", nargs="*", default=None, help="Optional trial ids/stage names to execute, for example E0 E1 E5.")
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
    rows = [run_spec(spec, simulation_days=args.simulation_days, max_steps=args.max_steps) for spec in specs]
    common.append_work_log(f"pref forge grid mode={args.mode} rows={len(rows)} out={common.EXPERIMENT_GRID}")
    return 0 if all(row["status"] == "EXECUTED" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
