"""Run or plan Trident generic parameter search trials.

The search is intentionally generic: it only sets numeric/toggle environment
variables consumed by ``demo/agent/config.py`` and does not export driver,
cargo, route, place, coordinate, or future-cargo facts.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.trident_utils import (  # noqa: E402
    REPORTS,
    RUNS,
    objective_score,
    run_local_eval,
    summarize_trident_run,
    write_merged_experiments,
)


PARAM_SPACE = {
    "CROWN_GOLD_QUERY_K": ["80", "120", "160", "200", "300", "450", "600"],
    "CROWN_GOLD_DIRECT_NET_FLOOR": ["-20", "0", "1", "10", "35", "60", "100"],
    "CROWN_GOLD_PROFIT_PER_HOUR_FLOOR": ["-5", "0", "10", "18", "25", "40"],
    "CROWN_Y_REST_UNTIL_MINUTE": ["480", "540", "600", "660"],
    "CROWN_Y_FULL_REST_PERIOD_DAYS": ["0", "10", "12", "15", "20"],
    "CROWN_GOLD_ENABLE_FIREWALL": ["0", "1"],
    "CROWN_GOLD_ENABLE_LINKER": ["0", "1"],
    "CROWN_GOLD_ENABLE_AUDITOR": ["0", "1"],
    "CROWN_GOLD_ENABLE_REPAIR": ["0", "1"],
    "CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC": ["0", "1"],
    "CROWN_GOLD_MAX_AUDITOR_CALLS_TOTAL": ["128", "512", "1024", "4096"],
    "CROWN_GOLD_MAX_LINKER_CALLS_TOTAL": ["512", "1024", "4096"],
    "CROWN_Y_TIME_PRICE_MULT": ["0.8", "1.0", "1.2"],
}
TRIDENT_VARIANT = "crown_trident_gold2"


def _trial_env(index: int, seed: int) -> dict[str, str]:
    rng = random.Random(seed + index * 7919)
    env = {name: rng.choice(values) for name, values in PARAM_SPACE.items()}

    # Keep invalid combinations out of the official queue.  Auditor needs the
    # firewall path, and linker has no effect when all preference modules are off.
    if env["CROWN_GOLD_ENABLE_AUDITOR"] == "1":
        env["CROWN_GOLD_ENABLE_FIREWALL"] = "1"
        env["CROWN_GOLD_ENABLE_LINKER"] = "1"
    if env["CROWN_GOLD_ENABLE_FIREWALL"] == "0":
        env["CROWN_GOLD_ENABLE_AUDITOR"] = "0"
    env.update(
        {
            "CROWN_TRIDENT_ENABLE_VISIBLE_GRAPH_MPC": env["CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC"],
            "CROWN_TRIDENT_QUERY_K": env["CROWN_GOLD_QUERY_K"],
            "CROWN_TRIDENT_DIRECT_NET_FLOOR": env["CROWN_GOLD_DIRECT_NET_FLOOR"],
            "CROWN_TRIDENT_PROFIT_PER_HOUR_FLOOR": env["CROWN_GOLD_PROFIT_PER_HOUR_FLOOR"],
        }
    )
    return env


def _trial_name(index: int) -> str:
    return f"trial_{index:04d}"


def _trial_run_dir(dataset: str, index: int) -> Path:
    return RUNS / "trident_param_search" / dataset / _trial_name(index)


def _summarize_trial(
    *,
    dataset: str,
    index: int,
    simulation_days: int,
    env: dict[str, str],
    status: str,
    notes: str,
    command: str = "",
    exit_code: int | str = "",
    started_at: str = "",
    finished_at: str = "",
    duration_seconds: float | str = "",
) -> dict[str, Any]:
    row = summarize_trident_run(
        _trial_run_dir(dataset, index),
        stage="S10" if dataset == "20260529" else "S10_SANITY",
        variant_name=_trial_name(index) if dataset == "20260529" else f"{_trial_name(index)}_0509_sanity",
        variant=TRIDENT_VARIANT,
        dataset=dataset,
        simulation_days=simulation_days,
        status=status,
        notes=notes,
        params=env,
        env_overrides=env,
        command=command,
        exit_code=exit_code,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
    )
    if row.get("official_net") not in {"", None}:
        row["objective_score"] = objective_score(row)
    return row


def _run_or_plan_trial(
    *,
    dataset: str,
    index: int,
    simulation_days: int,
    env: dict[str, str],
    execute: bool,
    plan_missing: bool,
    max_steps: int | None,
    notes: str,
) -> dict[str, Any] | None:
    run_dir = _trial_run_dir(dataset, index)
    if (run_dir / "monthly_income_202603.json").is_file():
        return _summarize_trial(
            dataset=dataset,
            index=index,
            simulation_days=simulation_days,
            env=env,
            status="EXISTING",
            notes=notes,
        )
    if not execute:
        if not plan_missing:
            return None
        return _summarize_trial(
            dataset=dataset,
            index=index,
            simulation_days=simulation_days,
            env=env,
            status="PLANNED",
            notes=notes + "; not executed",
        )
    rc, command, duration, started, finished = run_local_eval(
        dataset=dataset,
        variant=TRIDENT_VARIANT,
        run_dir=run_dir,
        simulation_days=simulation_days,
        env_overrides=env,
        max_steps=max_steps,
    )
    return _summarize_trial(
        dataset=dataset,
        index=index,
        simulation_days=simulation_days,
        env=env,
        status="OK" if rc == 0 else "INTERNAL_RUN_FAILURE",
        notes=notes,
        command=command,
        exit_code=rc,
        started_at=started,
        finished_at=finished,
        duration_seconds=duration,
    )


def _write_best_params(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        row
        for row in rows
        if row.get("dataset") == "20260529"
        and str(row.get("stage")) == "S10"
        and str(row.get("status")) in {"OK", "EXISTING"}
        and str(row.get("keep_or_kill")) not in {"kill_invalid_run", "kill_internal_failure", "kill_missing_run"}
        and row.get("objective_score") not in {"", None}
    ]
    if not candidates:
        return None
    best = max(candidates, key=lambda row: float(row.get("objective_score", 0.0) or 0.0))
    try:
        env = json.loads(str(best.get("env_json") or "{}"))
    except json.JSONDecodeError:
        env = {}
    payload = {
        "variant_name": best.get("variant_name"),
        "run_id": best.get("run_id"),
        "objective_score": best.get("objective_score"),
        "official_net": best.get("official_net"),
        "gross_minus_cost": best.get("gross_minus_cost"),
        "preference_penalty": best.get("preference_penalty"),
        "env": env,
    }
    out = RUNS / "trident_param_search" / "best_params.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def build_rows(
    *,
    trials: int,
    trial_offset: int,
    seed: int,
    execute: bool,
    plan_missing: bool,
    simulation_days: int,
    max_steps: int | None,
    sanity_every: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(trial_offset, trial_offset + trials):
        env = _trial_env(index, seed)
        row = _run_or_plan_trial(
            dataset="20260529",
            index=index,
            simulation_days=simulation_days,
            env=env,
            execute=execute,
            plan_missing=plan_missing,
            max_steps=max_steps,
            notes="generic parameter search; objective=official_net minus gross/penalty/invalid-run penalties",
        )
        if row is not None:
            rows.append(row)
        if sanity_every > 0 and (index + 1) % sanity_every == 0:
            sanity_row = _run_or_plan_trial(
                dataset="20260509",
                index=index,
                simulation_days=simulation_days,
                env=env,
                execute=execute,
                plan_missing=plan_missing,
                max_steps=max_steps,
                notes="0509 sanity check for the same generic parameter set",
            )
            if sanity_row is not None:
                rows.append(sanity_row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--trial-offset", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260602)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--no-plan-missing", action="store_true")
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--sanity-every", type=int, default=10)
    parser.add_argument("--out", type=Path, default=REPORTS / "trident_experiments.csv")
    args = parser.parse_args()
    rows = build_rows(
        trials=args.trials,
        trial_offset=args.trial_offset,
        seed=args.seed,
        execute=args.execute,
        plan_missing=not args.no_plan_missing,
        simulation_days=args.simulation_days,
        max_steps=args.max_steps,
        sanity_every=args.sanity_every,
    )
    merged = write_merged_experiments(args.out, rows)
    best = _write_best_params(merged)
    print(
        {
            "rows_written": len(rows),
            "rows_total": len(merged),
            "out": str(args.out),
            "execute": args.execute,
            "trials": args.trials,
            "best": best,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
