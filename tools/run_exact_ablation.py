"""Run or summarize CROWN-EXACT ablation variants."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.delta_mpc_utils import summarize_run, write_csv  # noqa: E402

ABLATIONS = [
    ("B0_rescue", "best_rescue", ROOT / "runs" / "latest_rescue", "rescue reference"),
    ("B1_adapter_only", "best_rescue", ROOT / "runs" / "latest_rescue", "adapter-only summarized by rescue reference"),
    ("B2_rbt_compiler", "crown_exact_rbt_mpc", ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc", "exact default"),
    ("B3_field_region_controller", "crown_exact_rbt_mpc", ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc", "included in exact default"),
    ("B4_rest_inactive_controller", "crown_exact_rbt_mpc", ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc", "included in exact default"),
    ("B5_distance_count_quota", "crown_exact_rbt_mpc", ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc", "included in exact default"),
    ("B6_location_dwell_sequence", "crown_exact_rbt_mpc", ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc", "included in exact default"),
    ("B7_visible_graph_mpc_2hop", "crown_exact_rbt_mpc", ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc_mpc", "requires CROWN_EXACT_ENABLE_VISIBLE_GRAPH_MPC=1"),
    ("B11_final_selected", "crown_exact_rbt_mpc", ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc", "final selected unless gates disable"),
]

FIELDS = [
    "stage",
    "variant",
    "dataset",
    "run_id",
    "official_net",
    "gross_minus_cost",
    "preference_penalty",
    "take_count",
    "wait_count",
    "reposition_count",
    "query_minutes_per_take",
    "qwen_compile_calls",
    "qwen_compile_or_cache_hit_count",
    "qwen_link_or_cache_hit_count",
    "qwen_audit_or_cache_hit_count",
    "blocks_or_massive",
    "controller_scored_candidate_count",
    "scorer_semantics_aligned_controller_count",
    "illegal_count",
    "rejected_take_count",
    "income_abort_count",
    "simulation_failures",
    "notes",
]


def _run_exact(out: Path, simulation_days: int, *, dataset: str = "20260529", mpc: bool = False) -> None:
    if (out / "monthly_income_202603.json").is_file():
        return
    env = os.environ.copy()
    env["CROWN_Y_VARIANT"] = "crown_exact_rbt_mpc"
    if mpc:
        env["CROWN_EXACT_ENABLE_VISIBLE_GRAPH_MPC"] = "1"
    env.pop("CROWN_Y_DISABLE_RUNTIME_QWEN", None)
    cmd = [
        sys.executable,
        "tools/run_local_eval.py",
        "--simulation-days",
        str(simulation_days),
        "--variant",
        "crown_exact_rbt_mpc",
        "--results-dir",
        str(out),
    ]
    if dataset == "20260509":
        cmd.extend(["--data-dir", str(ROOT / "_offline_reference_20260509" / "demo" / "server" / "data"), "--skip-income"])
    subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        check=True,
    )
    if dataset == "20260509":
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "_offline_reference_20260509" / "demo" / "calc_monthly_income.py"),
                "--project-root",
                str(ROOT / "_offline_reference_20260509" / "demo"),
                "--results-dir",
                str(out),
            ],
            cwd=str(ROOT),
            env=env,
            check=True,
        )


def _augment(row: dict, stage: str) -> dict:
    row["stage"] = stage
    qwen = int(row.get("qwen_compile_calls", 0) or 0)
    row["qwen_compile_or_cache_hit_count"] = qwen
    row["qwen_link_or_cache_hit_count"] = 0
    row["qwen_audit_or_cache_hit_count"] = int(row.get("qwen_auditor_calls", 0) or 0)
    row["blocks_or_massive"] = ""
    row["controller_scored_candidate_count"] = ""
    row["scorer_semantics_aligned_controller_count"] = ""
    return row


def build_rows(simulation_days: int, execute_final: bool) -> list[dict]:
    if execute_final:
        _run_exact(ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc", simulation_days, dataset="20260529", mpc=False)
        _run_exact(ROOT / "runs" / "exact" / "20260509" / "crown_exact_rbt_mpc", simulation_days, dataset="20260509", mpc=False)
    rows = []
    for stage, variant, path, notes in ABLATIONS:
        if not (path / "monthly_income_202603.json").is_file():
            rows.append({"stage": stage, "variant": variant, "dataset": "20260529", "run_id": str(path), "notes": "missing_run"})
            continue
        row = summarize_run(path, variant=variant, notes=notes)
        row["dataset"] = "20260529"
        rows.append(_augment(row, stage))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--summarize-only", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "exact_ablation.csv")
    args = parser.parse_args()
    rows = build_rows(args.simulation_days, execute_final=not args.summarize_only)
    write_csv(args.out, rows, FIELDS)
    print({"rows": len(rows), "out": str(args.out), "execute_final": not args.summarize_only})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
