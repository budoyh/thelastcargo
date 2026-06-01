"""Build the Delta-MPC baseline score table from existing and fresh runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.delta_mpc_utils import REPORTS, ROOT, summarize_run, write_csv

BASELINE_RUNS = [
    ("20260529", "rescue_reference", ROOT / "runs" / "latest_rescue", "prior rescue reference"),
    ("20260529", "pce_final", ROOT / "runs" / "pce" / "20260529" / "pce_final", "prior PCE failure"),
    ("20260529", "strict_pref", ROOT / "runs" / "next_build" / "20260529" / "strict_pref", "strict preference reference"),
    ("20260529", "money_greedy_no_pref", ROOT / "runs" / "next_build" / "20260529" / "money_greedy_no_pref", "diagnostic gross reference"),
    ("20260529", "money_trajectory_repair", ROOT / "runs" / "pce" / "20260529" / "money_trajectory_repair", "offline diagnostic repair frontier"),
    ("20260529", "visibility_k600_oracle", ROOT / "runs" / "pce" / "20260529" / "visibility_k600_oracle", "online visibility oracle diagnostic"),
    ("20260509", "strict_pref", ROOT / "runs" / "next_build" / "20260509" / "strict_pref", "0509 sanity reference"),
    ("20260509", "money_greedy_no_pref", ROOT / "runs" / "next_build" / "20260509" / "money_greedy_no_pref", "0509 money diagnostic"),
]

FIELDS = [
    "variant",
    "dataset",
    "sim_days",
    "gross_income",
    "distance_cost",
    "gross_minus_cost",
    "preference_penalty",
    "official_net",
    "expected_official_net",
    "score_accounting_ok",
    "take_count",
    "wait_count",
    "reposition_count",
    "query_minutes",
    "query_minutes_per_take",
    "illegal_count",
    "rejected_take_count",
    "income_abort_count",
    "simulation_failures",
    "qwen_compile_calls",
    "qwen_auditor_calls",
    "macro_started_count",
    "macro_completed_count",
    "official_delta_measured_macro_gain",
    "top5_decomposition_steps",
    "run_id",
    "notes",
]


def build_rows() -> list[dict]:
    rows = []
    for dataset, variant, path, notes in BASELINE_RUNS:
        if not (path / "monthly_income_202603.json").is_file():
            rows.append({"dataset": dataset, "variant": variant, "run_id": str(path), "notes": "missing_run"})
            continue
        row = summarize_run(path, variant=variant, notes=notes)
        row["dataset"] = dataset
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--out", type=Path, default=REPORTS / "delta_mpc_experiments.csv")
    args = parser.parse_args()
    rows = build_rows()
    write_csv(args.out, rows, FIELDS)
    print({"rows": len(rows), "out": str(args.out), "simulation_days": args.simulation_days})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
