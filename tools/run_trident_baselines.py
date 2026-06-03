"""Build the Trident Stage-0 baseline score table.

Default mode only summarizes existing official-style runs.  Use
``--execute-missing`` to run missing baselines through ``tools/run_local_eval.py``.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.trident_utils import (  # noqa: E402
    REPORTS,
    ROOT,
    RUNS,
    run_local_eval,
    summarize_trident_run,
    write_merged_experiments,
)


@dataclass(frozen=True)
class BaselineSpec:
    stage: str
    variant_name: str
    variant: str
    dataset: str
    run_dir: Path
    notes: str
    env: dict[str, str] = field(default_factory=dict)
    fallbacks: tuple[Path, ...] = ()


BASELINES = [
    BaselineSpec(
        stage="S0",
        variant_name="B0_historical_rescue_restored",
        variant="best_rescue",
        dataset="20260529",
        run_dir=RUNS / "trident_baselines" / "20260529" / "B0_historical_rescue_restored",
        notes="B0 rescue gate; immutable rescue reference.",
        fallbacks=(
            RUNS / "trident_b0_best_rescue_verify",
            RUNS / "gold" / "B0_best_rescue_restored_20260529",
            RUNS / "gold" / "B0_best_rescue_20260529",
            RUNS / "latest_rescue",
        ),
    ),
    BaselineSpec(
        stage="S0",
        variant_name="money_greedy_no_pref",
        variant="money_greedy_no_pref",
        dataset="20260529",
        run_dir=RUNS / "trident_baselines" / "20260529" / "money_greedy_no_pref",
        notes="Stage-0 gross diagnostic; not a submit strategy.",
        fallbacks=(RUNS / "next_build" / "20260529" / "money_greedy_no_pref",),
    ),
    BaselineSpec(
        stage="S0",
        variant_name="strict_pref",
        variant="strict_pref",
        dataset="20260529",
        run_dir=RUNS / "trident_baselines" / "20260529" / "strict_pref",
        notes="Stage-0 strict preference diagnostic.",
        fallbacks=(RUNS / "next_build" / "20260529" / "strict_pref",),
    ),
    BaselineSpec(
        stage="S0",
        variant_name="safe_profit_greedy",
        variant="safe_profit_greedy",
        dataset="20260529",
        run_dir=RUNS / "trident_baselines" / "20260529" / "safe_profit_greedy",
        notes="Stage-0 safe-profit reference.",
        fallbacks=(RUNS / "rescue_baselines" / "safe_profit_greedy",),
    ),
    BaselineSpec(
        stage="S0",
        variant_name="current_gold_if_available",
        variant="crown_gold_contract_mpc",
        dataset="20260529",
        run_dir=RUNS / "trident_baselines" / "20260529" / "current_gold_if_available",
        notes="Prior Gold comparison row when available.",
        fallbacks=(
            RUNS / "gold" / "B9_gold_current_20260529",
            RUNS / "gold" / "B9_gold_default_20260529",
            RUNS / "gold" / "B9_gold_contract_4096_20260529",
        ),
    ),
]


def _result_dir(spec: BaselineSpec) -> tuple[Path, str]:
    if (spec.run_dir / "monthly_income_202603.json").is_file():
        return spec.run_dir, "EXISTING"
    for fallback in spec.fallbacks:
        if (fallback / "monthly_income_202603.json").is_file():
            return fallback, "EXISTING"
    return spec.run_dir, "MISSING_RUN"


def build_rows(*, simulation_days: int, execute_missing: bool, max_steps: int | None) -> list[dict]:
    rows = []
    for spec in BASELINES:
        run_dir, status = _result_dir(spec)
        command = ""
        exit_code: int | str = ""
        started = finished = ""
        duration: float | str = ""
        if status == "MISSING_RUN" and execute_missing:
            exit_code, command, duration, started, finished = run_local_eval(
                dataset=spec.dataset,
                variant=spec.variant,
                run_dir=spec.run_dir,
                simulation_days=simulation_days,
                env_overrides=spec.env,
                max_steps=max_steps,
            )
            run_dir = spec.run_dir
            status = "OK" if exit_code == 0 else "INTERNAL_RUN_FAILURE"
        rows.append(
            summarize_trident_run(
                run_dir,
                stage=spec.stage,
                variant_name=spec.variant_name,
                variant=spec.variant,
                dataset=spec.dataset,
                simulation_days=simulation_days,
                status=status,
                notes=spec.notes,
                env_overrides=spec.env,
                command=command,
                exit_code=exit_code,
                started_at=started,
                finished_at=finished,
                duration_seconds=duration,
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--execute-missing", action="store_true")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--out", type=Path, default=REPORTS / "trident_experiments.csv")
    args = parser.parse_args()
    rows = build_rows(
        simulation_days=args.simulation_days,
        execute_missing=args.execute_missing,
        max_steps=args.max_steps,
    )
    merged = write_merged_experiments(args.out, rows)
    print(
        {
            "rows_written": len(rows),
            "rows_total": len(merged),
            "out": str(args.out),
            "execute_missing": args.execute_missing,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
