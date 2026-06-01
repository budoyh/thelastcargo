"""Build the CROWN-EXACT baseline score table."""

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

BASELINES = [
    ("20260529", "best_rescue", ROOT / "runs" / "latest_rescue", "existing rescue reference"),
    ("20260529", "ptt_previous", ROOT / "runs" / "ptt_20260529", "existing failed PTT reference"),
    ("20260529", "money_greedy_no_pref", ROOT / "runs" / "next_build" / "20260529" / "money_greedy_no_pref", "existing money-only diagnostic"),
    ("20260529", "strict_pref", ROOT / "runs" / "next_build" / "20260529" / "strict_pref", "existing strict preference reference"),
    ("20260529", "safe_profit_greedy", ROOT / "runs" / "rescue_baselines" / "safe_profit_greedy", "existing safe-profit baseline"),
    ("20260509", "best_rescue", ROOT / "runs" / "old_0509_rescue", "existing 0509 rescue reference"),
    ("20260509", "ptt_previous", ROOT / "runs" / "ptt_20260509", "existing failed PTT 0509 reference"),
    ("20260509", "money_greedy_no_pref", ROOT / "runs" / "next_build" / "20260509" / "money_greedy_no_pref", "existing 0509 money-only diagnostic"),
    ("20260509", "strict_pref", ROOT / "runs" / "next_build" / "20260509" / "strict_pref", "existing 0509 strict preference reference"),
]

FIELDS = [
    "dataset",
    "variant",
    "run_id",
    "official_net",
    "gross_minus_cost",
    "preference_penalty",
    "expected_official_net",
    "score_accounting_ok",
    "take_count",
    "wait_count",
    "reposition_count",
    "query_minutes_per_take",
    "qwen_compile_calls",
    "qwen_compile_or_cache_hit_count",
    "qwen_link_or_cache_hit_count",
    "qwen_audit_or_cache_hit_count",
    "illegal_count",
    "rejected_take_count",
    "income_abort_count",
    "simulation_failures",
    "notes",
]


def _run_missing(dataset: str, variant: str, out: Path, simulation_days: int) -> None:
    if (out / "monthly_income_202603.json").is_file():
        return
    cmd = [
        sys.executable,
        "tools/run_local_eval.py",
        "--simulation-days",
        str(simulation_days),
        "--variant",
        variant,
        "--results-dir",
        str(out),
    ]
    if dataset == "20260509":
        cmd.extend(["--data-dir", str(ROOT / "_offline_reference_20260509" / "demo" / "server" / "data"), "--skip-income"])
    env = os.environ.copy()
    env["CROWN_Y_VARIANT"] = variant
    subprocess.run(cmd, cwd=str(ROOT), env=env, check=True)
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


def build_rows(simulation_days: int, execute_missing: bool = False) -> list[dict]:
    rows = []
    for dataset, variant, path, notes in BASELINES:
        if execute_missing and not (path / "monthly_income_202603.json").is_file() and variant != "ptt_previous":
            _run_missing(dataset, "safe_profit_greedy" if variant == "safe_profit_greedy" else variant, path, simulation_days)
        if not (path / "monthly_income_202603.json").is_file():
            rows.append({"dataset": dataset, "variant": variant, "run_id": str(path), "notes": "missing_run"})
            continue
        row = summarize_run(path, variant=variant, notes=notes)
        row["dataset"] = dataset
        qwen_total = int(row.get("qwen_compile_calls", 0) or 0)
        row["qwen_compile_or_cache_hit_count"] = qwen_total
        row["qwen_link_or_cache_hit_count"] = 0
        row["qwen_audit_or_cache_hit_count"] = int(row.get("qwen_auditor_calls", 0) or 0)
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--execute-missing", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "exact_baselines.csv")
    args = parser.parse_args()
    rows = build_rows(args.simulation_days, execute_missing=args.execute_missing)
    write_csv(args.out, rows, FIELDS)
    print({"rows": len(rows), "out": str(args.out), "execute_missing": args.execute_missing})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
