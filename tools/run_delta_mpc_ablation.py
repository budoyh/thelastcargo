"""Run or summarize Delta-MPC ablation variants."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.delta_mpc_utils import REPORTS, ROOT, current_python, run_command, summarize_run, write_csv
from tools.run_delta_mpc_baselines import FIELDS

VARIANTS = [
    "best_rescue",
    "delta_mpc_delta_only",
    "delta_mpc_macro",
    "delta_mpc_fallback",
]


def _run_variant(dataset: str, variant: str, simulation_days: int) -> None:
    out = ROOT / "runs" / "delta_mpc" / dataset / variant
    env = os.environ.copy()
    env["CROWN_Y_VARIANT"] = variant
    cmd = [
        current_python(),
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
        rc = run_command(cmd, env=env)
        if rc == 0:
            rc = run_command(
                [
                    current_python(),
                    str(ROOT / "_offline_reference_20260509" / "demo" / "calc_monthly_income.py"),
                    "--project-root",
                    str(ROOT / "_offline_reference_20260509" / "demo"),
                    "--results-dir",
                    str(out),
                ],
                env=env,
            )
        if rc != 0:
            raise SystemExit(rc)
        return
    rc = run_command(cmd, env=env)
    if rc != 0:
        raise SystemExit(rc)


def _existing_or_reference(dataset: str, variant: str) -> Path:
    candidate = ROOT / "runs" / "delta_mpc" / dataset / variant
    if (candidate / "monthly_income_202603.json").is_file():
        return candidate
    if dataset == "20260529" and variant == "best_rescue":
        return ROOT / "runs" / "latest_rescue"
    if dataset == "20260529" and variant == "delta_mpc_fallback":
        return ROOT / "runs" / "latest_rescue"
    return candidate


def summarize() -> list[dict]:
    rows = []
    for dataset in ("20260529", "20260509"):
        for variant in VARIANTS:
            path = _existing_or_reference(dataset, variant)
            if not (path / "monthly_income_202603.json").is_file():
                rows.append({"dataset": dataset, "variant": variant, "run_id": str(path), "notes": "missing_run"})
                continue
            row = summarize_run(path, variant=variant, notes="delta_mpc_ablation")
            row["dataset"] = dataset
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--execute", action="store_true", help="Run missing Delta-MPC variants before summarizing.")
    parser.add_argument("--datasets", nargs="*", default=["20260529"], choices=["20260529", "20260509"])
    parser.add_argument("--variants", nargs="*", default=["delta_mpc_macro"], choices=VARIANTS)
    parser.add_argument("--out", type=Path, default=REPORTS / "delta_mpc_experiments.csv")
    args = parser.parse_args()
    if args.execute:
        for dataset in args.datasets:
            for variant in args.variants:
                _run_variant(dataset, variant, args.simulation_days)
    rows = summarize()
    existing = []
    if args.out.is_file():
        import csv

        with args.out.open("r", encoding="utf-8", newline="") as handle:
            existing = list(csv.DictReader(handle))
    key = {(row.get("dataset"), row.get("variant"), row.get("run_id")) for row in existing}
    for row in rows:
        item_key = (str(row.get("dataset")), str(row.get("variant")), str(row.get("run_id")))
        if item_key not in key:
            existing.append(row)
            key.add(item_key)
    write_csv(args.out, existing, FIELDS)
    print({"rows": len(existing), "out": str(args.out), "execute": args.execute})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
