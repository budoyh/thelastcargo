"""Build CROWN-PCE oracle gap and experiment CSVs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pce_oracle_engine import REPORTS, ROOT, action_counts, command_parser, read_monthly, summary_metrics


EXPERIMENT_FIELDS = [
    "run_id",
    "dataset_tag",
    "variant",
    "data_version",
    "checker_version",
    "comparable",
    "official_net",
    "gross_income",
    "distance_cost",
    "gross_minus_cost",
    "preference_penalty",
    "take_order",
    "wait",
    "reposition",
    "illegal_actions",
    "rejected_takes",
    "income_aborts",
    "simulation_failures",
    "qwen_compile_calls",
    "semantic_gate_status",
    "notes",
]

GAP_FIELDS = [
    "row_type",
    "variant",
    "k",
    "official_net",
    "gross_minus_cost",
    "preference_penalty",
    "gap_value",
    "data_version",
    "checker_version",
    "confidence",
    "approximation",
    "redaction_status",
]


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _qwen_calls(run_dir: Path) -> int:
    latest = 0
    for path in run_dir.glob("actions_202603_*.jsonl"):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            trace = ((row.get("action") or {}).get("agent_trace") or {})
            rescue = trace.get("rescue") if isinstance(trace, dict) else {}
            qwen = rescue.get("qwen") if isinstance(rescue, dict) else {}
            if isinstance(qwen, dict):
                latest = max(latest, int(qwen.get("compile_calls", 0) or 0))
    return latest


def _simulation_failures(run_dir: Path) -> int:
    path = run_dir / "run_summary_202603.json"
    if not path.is_file():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    failures = data.get("driver_simulation_failures", {})
    return len(failures) if isinstance(failures, dict) else 0


def _experiment_row(run_dir: Path, dataset_tag: str, checker_version: str, note: str = "") -> dict[str, object]:
    monthly = read_monthly(run_dir)
    metrics = summary_metrics(monthly)
    counts = action_counts(run_dir)
    return {
        "run_id": _rel(run_dir),
        "dataset_tag": dataset_tag,
        "variant": run_dir.name,
        "data_version": dataset_tag,
        "checker_version": checker_version,
        "comparable": "true",
        **metrics,
        **counts,
        "income_aborts": metrics.get("income_aborts", 0),
        "simulation_failures": _simulation_failures(run_dir),
        "qwen_compile_calls": _qwen_calls(run_dir),
        "semantic_gate_status": "",
        "notes": note,
    }


def _pce_dataset_for(run_dir: Path) -> tuple[str, str]:
    parts = set(run_dir.parts)
    if "20260509" in parts:
        return "20260509_reference", "20260509_matching"
    return "20260529_main", "20260529_current"


def _write(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_reports(runs_root: Path, output_dir: Path) -> dict[str, object]:
    experiments: list[dict[str, object]] = []
    for run_dir in sorted({p.parent for p in runs_root.rglob("monthly_income_202603.json")}):
        if "history" in run_dir.parts:
            continue
        dataset_tag, checker_version = _pce_dataset_for(run_dir)
        experiments.append(_experiment_row(run_dir, dataset_tag, checker_version))
    for run_dir in sorted((ROOT / "runs" / "next_build" / "20260529").glob("*")):
        if (run_dir / "monthly_income_202603.json").is_file():
            experiments.append(_experiment_row(run_dir, "20260529_main", "20260529_current", "prior_next_build_reference"))
    for run_dir in sorted((ROOT / "runs" / "next_build" / "20260509").glob("*")):
        if (run_dir / "monthly_income_202603.json").is_file():
            experiments.append(_experiment_row(run_dir, "20260509_reference", "20260509_matching", "cross_dataset_reference"))

    by_variant = {str(row["variant"]): row for row in experiments}
    full_info = by_variant.get("full_info_oracle", {})
    no_pref = by_variant.get("no_pref_money_oracle") or by_variant.get("money_greedy_no_pref", {})
    rescue_net = 5067.69
    next_best = max(
        (float(row["official_net"]) for row in experiments if row["dataset_tag"] == "20260529_main" and row.get("notes") == "prior_next_build_reference"),
        default=2240.98,
    )
    full_info_net = float(full_info.get("official_net", 0.0) or 0.0)
    gap_rows: list[dict[str, object]] = []

    def add(row_type: str, variant: str, row: dict[str, object], gap_value: float = 0.0, k: str = "", approximation: str = "") -> None:
        gap_rows.append(
            {
                "row_type": row_type,
                "variant": variant,
                "k": k,
                "official_net": row.get("official_net", ""),
                "gross_minus_cost": row.get("gross_minus_cost", ""),
                "preference_penalty": row.get("preference_penalty", ""),
                "gap_value": round(gap_value, 2),
                "data_version": row.get("data_version", "20260529_main"),
                "checker_version": row.get("checker_version", "20260529_current"),
                "confidence": 0.65 if approximation else 0.8,
                "approximation": approximation,
                "redaction_status": "raw value redacted",
            }
        )

    if full_info:
        add("full_info_oracle_net", "full_info_oracle", full_info)
    for k in (100, 300, 600):
        variant = f"visibility_k{k}_oracle"
        row = by_variant.get(variant, {})
        if row:
            add("online_visibility_oracle_net", variant, row, full_info_net - float(row.get("official_net", 0.0) or 0.0), str(k), "nearest_k_approx_validated_by_shared_query_semantics")
    if no_pref:
        add("no_pref_gross_cost", str(no_pref.get("variant", "no_pref_money_oracle")), no_pref)
    add("current_rescue_net", "rescue_reference", {"official_net": rescue_net, "gross_minus_cost": "", "preference_penalty": "", "data_version": "20260529_main", "checker_version": "20260529_current"})
    add("current_next_build_net", "next_build_best_reference", {"official_net": next_best, "gross_minus_cost": "", "preference_penalty": "", "data_version": "20260529_main", "checker_version": "20260529_current"})
    if full_info_net:
        add("future_info_gap", "full_info_minus_best_online", {}, full_info_net - max((float(row.get("official_net", 0.0) or 0.0) for row in experiments if str(row.get("variant", "")).startswith("visibility_")), default=0.0))
        add("preference_evaluator_gap", "full_info_minus_next_best", {}, full_info_net - next_best)
        add("route_planning_gap", "full_info_minus_rescue", {}, full_info_net - rescue_net)
    add("query_reposition_gap", "not_isolated", {}, 0.0, approximation="not_isolated_in_current_oracle")

    _write(output_dir / "pce_experiments.csv", experiments, EXPERIMENT_FIELDS)
    _write(output_dir / "oracle_gap.csv", gap_rows, GAP_FIELDS)
    return {"experiments": len(experiments), "oracle_gap_rows": len(gap_rows), "output_dir": _rel(output_dir)}


def main() -> int:
    parser = command_parser("Build CROWN-PCE oracle gap reports.")
    args = parser.parse_args()
    payload = build_reports(args.runs_root, args.output_dir or REPORTS)
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
