"""Run CROWN-FUSE B0/B1/B2/B3 no-op isolation evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.trident_utils import (  # noqa: E402
    REPORTS,
    ROOT,
    RUNS,
    TRIDENT_EXPERIMENT_FIELDS,
    iter_action_rows,
    run_local_eval,
    summarize_trident_run,
)


FUSE_NOOP_FIELDS = [
    *TRIDENT_EXPERIMENT_FIELDS,
    "variant_key",
    "run_dir",
    "action_signature_hash",
    "action_signature_match_rate",
    "action_signature_mismatch_count",
    "action_signature_total",
    "net_delta_vs_b0",
    "penalty_delta_vs_b0",
]


@dataclass(frozen=True)
class NoopSpec:
    variant_key: str
    variant_name: str
    variant: str
    run_dir: Path
    env: dict[str, str] = field(default_factory=dict)
    notes: str = ""


def specs(results_root: Path) -> list[NoopSpec]:
    return [
        NoopSpec(
            "B0",
            "B0_rescue",
            "best_rescue",
            RUNS / "fuse" / "b0_rescue",
            notes="Immutable best_rescue B0 reference.",
        ),
        NoopSpec(
            "B1",
            "B1_all_overlays_off",
            "fuse_rescue_core",
            results_root / "B1_all_overlays_off",
            {"CROWN_FUSE_NOOP_STAGE": "all_overlays_off"},
            "Fuse rescue core alias; overlays off.",
        ),
        NoopSpec(
            "B2",
            "B2_contract_compile_logging_only",
            "fuse_rescue_core",
            results_root / "B2_contract_compile_logging_only",
            {"CROWN_FUSE_NOOP_STAGE": "contract_compile_logging_only"},
            "Contract compile/cache logging path; no scoring or action changes.",
        ),
        NoopSpec(
            "B3",
            "B3_contract_monitor_no_score",
            "fuse_rescue_core",
            results_root / "B3_contract_monitor_no_score",
            {"CROWN_FUSE_NOOP_STAGE": "contract_monitor_no_score"},
            "Contract monitor trace path; no scoring or action changes.",
        ),
    ]


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _round_coord(value: Any) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return ""


def action_signature(row: dict[str, Any]) -> str:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    params = action.get("params") if isinstance(action.get("params"), dict) else {}
    action_type = str(action.get("action", "")).strip()
    cargo_hash = _hash(params.get("cargo_id")) if action_type == "take_order" else ""
    wait_minutes = str(int(float(params.get("duration_minutes", 0) or 0))) if action_type == "wait" else ""
    reposition_target = ""
    if action_type == "reposition":
        reposition_target = f"{_round_coord(params.get('latitude'))},{_round_coord(params.get('longitude'))}"
    decision_time_bucket = str(row.get("simulation_end_time", ""))
    return "|".join(
        [
            str(row.get("driver_id", "")),
            str(row.get("step", "")),
            action_type,
            cargo_hash,
            wait_minutes,
            reposition_target,
            decision_time_bucket,
        ]
    )


def signatures(run_dir: Path) -> list[str]:
    return [action_signature(row) for _, _, row in iter_action_rows(run_dir)]


def signature_hash(sigs: list[str]) -> str:
    digest = hashlib.sha256()
    for sig in sigs:
        digest.update(sig.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def compare_signatures(base: list[str], candidate: list[str]) -> tuple[float, int, int]:
    total = max(len(base), len(candidate))
    if total == 0:
        return 1.0, 0, 0
    match = 0
    for idx in range(total):
        left = base[idx] if idx < len(base) else None
        right = candidate[idx] if idx < len(candidate) else None
        if left == right:
            match += 1
    mismatch = total - match
    return round(match / total, 6), mismatch, total


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _run_or_summarize(spec: NoopSpec, simulation_days: int, max_steps: int | None) -> dict[str, Any]:
    command = f"existing run summarized: {spec.run_dir}"
    exit_code: int | str = 0
    started = finished = ""
    duration: float | str = ""
    if not (spec.run_dir / "monthly_income_202603.json").is_file():
        exit_code, command, duration, started, finished = run_local_eval(
            dataset="20260529",
            variant=spec.variant,
            run_dir=spec.run_dir,
            simulation_days=simulation_days,
            env_overrides=spec.env,
            max_steps=max_steps,
        )
    status = "EXECUTED" if (spec.run_dir / "monthly_income_202603.json").is_file() and int(exit_code or 0) == 0 else "FAILED_EXECUTED"
    row = summarize_trident_run(
        spec.run_dir,
        stage=spec.variant_key,
        variant_name=spec.variant_name,
        variant=spec.variant,
        dataset="20260529",
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
    row["variant_key"] = spec.variant_key
    row["run_dir"] = row.get("run_id", str(spec.run_dir))
    row["keep_or_kill"] = "keep_noop_reference" if spec.variant_key == "B0" else "pending_isolation_compare"
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FUSE_NOOP_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--results-root", type=Path, default=RUNS / "fuse" / "noop")
    parser.add_argument("--out", type=Path, default=REPORTS / "fuse_noop_isolation.csv")
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for spec in specs(args.results_root):
        rows.append(_run_or_summarize(spec, args.simulation_days, args.max_steps))

    b0_row = next(row for row in rows if row["variant_key"] == "B0")
    b0_run_dir = ROOT / str(b0_row["run_dir"])
    b0_sigs = signatures(b0_run_dir)
    b0_net = _safe_float(b0_row.get("official_net"))
    b0_gross = _safe_float(b0_row.get("gross_minus_cost"))
    b0_penalty = _safe_float(b0_row.get("preference_penalty"))

    for row in rows:
        run_dir = ROOT / str(row["run_dir"])
        sigs = signatures(run_dir)
        match_rate, mismatch_count, total = compare_signatures(b0_sigs, sigs)
        row["action_signature_hash"] = signature_hash(sigs)
        row["action_signature_match_rate"] = 1.0 if row["variant_key"] == "B0" else match_rate
        row["action_signature_mismatch_count"] = 0 if row["variant_key"] == "B0" else mismatch_count
        row["action_signature_total"] = total
        row["net_delta_vs_b0"] = round(_safe_float(row.get("official_net")) - b0_net, 2)
        row["gross_delta_vs_b0"] = round(_safe_float(row.get("gross_minus_cost")) - b0_gross, 2)
        row["penalty_delta_vs_b0"] = round(_safe_float(row.get("preference_penalty")) - b0_penalty, 2)
        if row["variant_key"] != "B0":
            row["keep_or_kill"] = "keep_noop_equivalent" if match_rate >= 0.999 else "kill_noop_drift"
        row["params_json"] = json_cell({})

    write_csv(args.out, rows)
    print({"out": str(args.out), "rows": len(rows), "status": [row["status"] for row in rows]})
    return 0 if all(row["status"] == "EXECUTED" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
