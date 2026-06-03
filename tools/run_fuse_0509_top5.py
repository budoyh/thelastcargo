"""Run full 20260509 sanity for the top five executed Fuse 20260529 configs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.run_fuse_grid import (  # noqa: E402
    REPORTS,
    RUNS,
    FuseSpec,
    apply_b0_deltas,
    fuse_env_from_params,
    merge_rows,
    read_csv,
    run_spec,
    write_csv,
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value not in {"", None} else default)
    except (TypeError, ValueError):
        return default


def _params(row: dict[str, Any]) -> dict[str, Any]:
    try:
        data = json.loads(str(row.get("params_json") or "{}"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def top5_specs(out: Path, results_root: Path) -> list[FuseSpec]:
    rows = [
        row
        for row in read_csv(out)
        if str(row.get("status")) == "EXECUTED"
        and str(row.get("dataset", "20260529")) == "20260529"
        and str(row.get("variant_key")) == "TRIAL"
        and row.get("params_json") not in {"", None}
    ]
    rows.sort(
        key=lambda row: (
            -_safe_float(row.get("official_net"), -10**9),
            -_safe_float(row.get("gross_minus_cost"), -10**9),
            _safe_float(row.get("preference_penalty"), 10**9),
            str(row.get("trial_id", "")),
        )
    )
    specs: list[FuseSpec] = []
    for rank, source in enumerate(rows[:5], start=1):
        source_trial = str(source.get("trial_id") or f"rank_{rank}")
        params = _params(source)
        params_for_row = dict(params)
        params_for_row["source_20260529_trial"] = source_trial
        params_for_row["source_20260529_official_net"] = source.get("official_net", "")
        specs.append(
            FuseSpec(
                "S0509",
                f"S0509_top5_rank_{rank}_{source_trial}",
                "fuse_targeted_repair",
                results_root / "20260509" / f"top{rank}_{source_trial}",
                fuse_env_from_params(params),
                trial_id=f"{source_trial}_0509",
                params=params_for_row,
                notes="Full 20260509 sanity for a top-five executed 20260529 Fuse config.",
                dataset="20260509",
                top5_0509_sanity=True,
                package_candidate=True,
                selected_reason=f"top5_20260529_rank_{rank}",
            )
        )
    return specs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--results-root", type=Path, default=RUNS / "fuse" / "sanity0509")
    parser.add_argument("--out", type=Path, default=REPORTS / "fuse_grid.csv")
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    specs = top5_specs(args.out, args.results_root)
    if len(specs) < 5:
        raise SystemExit(f"need 5 executed 20260529 configs for 0509 sanity, found {len(specs)}")

    rows: list[dict[str, Any]] = []
    for spec in specs:
        row = run_spec(spec, args.simulation_days, args.max_steps)
        rows.append(row)
        merged = merge_rows(read_csv(args.out), [row])
        apply_b0_deltas(merged)
        write_csv(args.out, merged)
    print({"mode": "top5_0509", "rows_written": len(rows), "rows_total": len(read_csv(args.out)), "out": str(args.out)})
    return 0 if all(str(row.get("status")) == "EXECUTED" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
