"""Build the five final PTT reports from synthetic checks and local runs."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "demo"))

from agent.ptt_types import PTT_TYPES  # noqa: E402
from tools.score_rescue_metrics import iter_rows, summarize_run  # noqa: E402

REPORTS = ROOT / "reports"
ALLOWED_REPORTS = {
    "ptt_final_report.md",
    "ptt_experiments.csv",
    "ptt_compiler_coverage.csv",
    "ptt_decision_forensics.csv",
    "ptt_submission_audit.md",
}
EVALS = {
    "20260529": ROOT / "runs" / "ptt_20260529",
    "20260509": ROOT / "runs" / "ptt_20260509",
}
SYNTHETIC_PATH = ROOT / "runs" / "ptt_synthetic" / "ptt_synthetic_results.json"
PACKAGE_AUDIT = ROOT / "runs" / "packages" / "ptt_package_audit.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _hash_value(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _archive_extra_reports() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    extras = [path for path in REPORTS.iterdir() if path.is_file() and path.name not in ALLOWED_REPORTS]
    if not extras:
        return
    archive = ROOT / "archive" / f"reports_non_ptt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive.mkdir(parents=True, exist_ok=True)
    for path in extras:
        shutil.move(str(path), str(archive / path.name))


def _gross_minus_cost(results_dir: Path) -> float:
    data = _read_json(results_dir / "monthly_income_202603.json", {})
    total = 0.0
    for driver in data.get("drivers", []) if isinstance(data, dict) else []:
        income = driver.get("income", {}) if isinstance(driver, dict) else {}
        total += float(income.get("gross_income", 0.0) or 0.0) - float(income.get("cost", 0.0) or 0.0)
    return round(total, 2)


def _trace_stats(results_dir: Path) -> dict[str, Any]:
    stats = {
        "qwen_compile_calls": 0,
        "qwen_linker_calls": 0,
        "qwen_auditor_calls": 0,
        "ptt_compile_calls": 0,
        "ptt_linker_required": 0,
        "ptt_linker_calls": 0,
        "ptt_auditor_triggers": 0,
        "ptt_blocks": 0,
        "ptt_massive": 0,
        "macro_started": 0,
        "macro_completed": 0,
    }
    for row in iter_rows(results_dir):
        action = row.get("action") if isinstance(row.get("action"), dict) else {}
        trace = action.get("agent_trace") if isinstance(action, dict) else {}
        rescue = trace.get("rescue") if isinstance(trace, dict) else {}
        if not isinstance(rescue, dict):
            continue
        qwen = rescue.get("qwen") if isinstance(rescue.get("qwen"), dict) else {}
        ptt = rescue.get("ptt") if isinstance(rescue.get("ptt"), dict) else {}
        ptt_stats = ptt.get("stats") if isinstance(ptt.get("stats"), dict) else {}
        firewall = ptt.get("firewall") if isinstance(ptt.get("firewall"), dict) else {}
        macro = rescue.get("macro") if isinstance(rescue.get("macro"), dict) else {}
        stats["qwen_compile_calls"] = max(stats["qwen_compile_calls"], int(qwen.get("compile_calls", 0) or 0))
        stats["qwen_linker_calls"] = max(stats["qwen_linker_calls"], int(qwen.get("linker_calls", 0) or 0))
        stats["qwen_auditor_calls"] = max(stats["qwen_auditor_calls"], int(qwen.get("auditor_calls", 0) or 0))
        stats["ptt_compile_calls"] = max(stats["ptt_compile_calls"], int(ptt_stats.get("compile_calls", 0) or 0))
        stats["ptt_linker_required"] = max(stats["ptt_linker_required"], int(ptt_stats.get("linker_call_required_count", 0) or 0))
        stats["ptt_linker_calls"] = max(stats["ptt_linker_calls"], int(ptt_stats.get("linker_call_count", 0) or 0))
        stats["ptt_auditor_triggers"] = max(stats["ptt_auditor_triggers"], int(ptt_stats.get("auditor_trigger_count", 0) or 0))
        stats["ptt_blocks"] += int(firewall.get("blocked_count", 0) or 0)
        stats["ptt_massive"] += int(firewall.get("massive_penalty_count", 0) or 0)
        stats["macro_started"] = max(stats["macro_started"], int(macro.get("macro_started_count", 0) or 0))
        stats["macro_completed"] = max(stats["macro_completed"], int(macro.get("macro_completed_count", 0) or 0))
    return stats


def _eval_row(dataset: str, results_dir: Path) -> dict[str, Any]:
    if not (results_dir / "monthly_income_202603.json").exists():
        return {"dataset": dataset, "variant": "preference_firewall_profit", "results_dir": str(results_dir), "present": False}
    summary = summarize_run(results_dir)
    trace = _trace_stats(results_dir)
    sim_failures = summary.get("simulation_failures", {})
    counts = summary.get("counts", {})
    return {
        "dataset": dataset,
        "variant": "preference_firewall_profit",
        "results_dir": str(results_dir),
        "present": True,
        "official_net": round(float(summary.get("net", 0.0) or 0.0), 2),
        "gross_minus_cost": _gross_minus_cost(results_dir),
        "preference_penalty": round(float(summary.get("penalty", 0.0) or 0.0), 2),
        "failed_driver_count": int(summary.get("failed_driver_count", 0) or 0),
        "simulation_failures": len(sim_failures) if isinstance(sim_failures, dict) else 0,
        "illegal_actions": int(summary.get("illegal_actions", 0) or 0),
        "rejected_takes": int(counts.get("rejected_take", 0) or 0),
        "take": int(counts.get("take_order", 0) or 0),
        "wait": int(counts.get("wait", 0) or 0),
        "reposition": int(counts.get("reposition", 0) or 0),
        "query_minutes_per_take": summary.get("query_minutes_per_take", 0),
        **trace,
    }


def _coverage_rows(synthetic: dict[str, Any]) -> list[dict[str, Any]]:
    by_type = {row.get("ptt_type"): row for row in synthetic.get("rows", []) if isinstance(row, dict)}
    rows = []
    for rule_type in PTT_TYPES:
        row = by_type.get(rule_type, {})
        checks = row.get("checks", {}) if isinstance(row.get("checks"), dict) else {}
        rows.append(
            {
                "ptt_type": rule_type,
                "controller_class": row.get("controller_class", ""),
                "paraphrase_count": len(row.get("paraphrase_hashes", []) if isinstance(row.get("paraphrase_hashes"), list) else []),
                "compiler_schema_pass": bool(row),
                "positive_pass": checks.get("positive_pass", False),
                "negative_pass": checks.get("negative_pass", False),
                "repair_pass": checks.get("repair_pass", False),
                "linker_behavior_pass": checks.get("linker_behavior_pass", False),
                "firewall_pass": checks.get("firewall_pass", False),
                "status": "pass" if row.get("passed") else "fail",
            }
        )
    return rows


def _forensic_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset, results_dir in EVALS.items():
        if not results_dir.exists():
            continue
        for idx, row in enumerate(iter_rows(results_dir)):
            if len(rows) >= 240:
                return rows
            action = row.get("action") if isinstance(row.get("action"), dict) else {}
            trace = action.get("agent_trace") if isinstance(action, dict) else {}
            rescue = trace.get("rescue") if isinstance(trace, dict) else {}
            ptt = rescue.get("ptt") if isinstance(rescue, dict) and isinstance(rescue.get("ptt"), dict) else {}
            firewall = ptt.get("firewall") if isinstance(ptt.get("firewall"), dict) else {}
            chosen = trace.get("chosen") if isinstance(trace, dict) and isinstance(trace.get("chosen"), dict) else {}
            rows.append(
                {
                    "dataset": dataset,
                    "row_index": idx,
                    "action": action.get("action", ""),
                    "chosen_candidate_hash": _hash_value(chosen.get("candidate_id", "")),
                    "ptt_rules": ptt.get("rules", 0),
                    "ptt_controllers": ptt.get("controllers", 0),
                    "vocab_links": ptt.get("vocab_links", 0),
                    "firewall_scored": firewall.get("scored_candidate_count", 0),
                    "firewall_blocked": firewall.get("blocked_count", 0),
                    "firewall_massive": firewall.get("massive_penalty_count", 0),
                    "macro_started": (rescue.get("macro") or {}).get("macro_started_count", 0) if isinstance(rescue, dict) else 0,
                    "macro_completed": (rescue.get("macro") or {}).get("macro_completed_count", 0) if isinstance(rescue, dict) else 0,
                }
            )
    return rows


def _gate_summary(experiments: list[dict[str, Any]], synthetic: dict[str, Any], package: dict[str, Any]) -> dict[str, bool]:
    by_dataset = {row["dataset"]: row for row in experiments}
    row_0529 = by_dataset.get("20260529", {})
    row_0509 = by_dataset.get("20260509", {})
    package_inspection = package.get("inspection", {}) if isinstance(package.get("inspection"), dict) else {}
    package_ok = bool(package) and not package.get("disallowed_entries") and (
        not package_inspection or not package_inspection.get("disallowed_entries")
    )
    return {
        "synthetic_t01_t18_pass": bool((synthetic.get("summary") or {}).get("all_passed")),
        "eval_20260529_present": bool(row_0529.get("present")),
        "eval_20260509_present": bool(row_0509.get("present")),
        "score_0529_net_above_rescue": float(row_0529.get("official_net", 0.0) or 0.0) > 5067.69,
        "score_0529_penalty_below_rescue": float(row_0529.get("preference_penalty", 10**9) or 10**9) < 38140.0,
        "score_0529_gross_not_collapsed": float(row_0529.get("gross_minus_cost", 0.0) or 0.0) >= 40000.0,
        "zero_0529_failures": int(row_0529.get("failed_driver_count", 1) or 0) == 0
        and int(row_0529.get("simulation_failures", 1) or 0) == 0,
        "zero_0529_illegal_or_rejected": int(row_0529.get("illegal_actions", 1) or 0) == 0
        and int(row_0529.get("rejected_takes", 1) or 0) == 0,
        "qwen_ptt_compile_called": int(row_0529.get("ptt_compile_calls", 0) or 0) > 0
        or int(row_0529.get("qwen_compile_calls", 0) or 0) > 0,
        "linker_called_when_required": int(row_0529.get("ptt_linker_required", 0) or 0) == 0
        or int(row_0529.get("ptt_linker_calls", 0) or 0) >= int(row_0529.get("ptt_linker_required", 0) or 0),
        "macro_completed": int(row_0529.get("macro_completed", 0) or 0) > 0,
        "eval_0509_no_catastrophic_failure": bool(row_0509.get("present"))
        and int(row_0509.get("failed_driver_count", 1) or 0) == 0
        and int(row_0509.get("simulation_failures", 1) or 0) == 0,
        "default_variant_package_ok": package.get("default_variant") == "preference_firewall_profit" or package_inspection.get("default_variant_config_text") is True,
        "package_shape_ok": package_ok,
    }


def _write_audit(gates: dict[str, bool], package: dict[str, Any]) -> None:
    lines = [
        "# PTT Submission Audit",
        "",
        "## Gate Status",
    ]
    for key, value in gates.items():
        lines.append(f"- {key}: {'PASS' if value else 'FAIL'}")
    lines.extend(["", "## Package"])
    if package:
        lines.append(f"- path: `{package.get('zip_path', '')}`")
        lines.append(f"- sha256: `{package.get('sha256', '')}`")
        lines.append(f"- size_bytes: {package.get('size_bytes', '')}")
        lines.append(f"- recommended_flag: {package.get('recommended', False)}")
        lines.append(f"- default_variant: `{package.get('default_variant', '')}`")
        inspection = package.get("inspection", {}) if isinstance(package.get("inspection"), dict) else {}
        if inspection:
            lines.append(f"- inspection_root_demo_only: {inspection.get('root_demo_only', False)}")
            lines.append(f"- inspection_disallowed_entries: {len(inspection.get('disallowed_entries', []))}")
    else:
        lines.append("- package_audit: missing")
    lines.extend(
        [
            "",
            "## Reviewer Checks",
            "- Plato read-only reviewer: flagged default fallback, missing PTT controllers/firewall/linker, and trace raw-id risk before this patch set.",
            "- Huygens read-only reviewer: flagged old generic compiler, missing deterministic controller interface, missing action firewall, and non-PTT package defaults before this patch set.",
            "- Final simulated audit scopes: prompt adherence, compliance/future-info, PTT semantic, controller/firewall, runtime score, packaging.",
        ]
    )
    (REPORTS / "ptt_submission_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_final(experiments: list[dict[str, Any]], synthetic: dict[str, Any], gates: dict[str, bool]) -> None:
    ready = all(gates.values())
    first = "PTT_SUBMISSION_READY" if ready else "DO NOT SUBMIT: PTT gates not reached."
    row_0529 = next((row for row in experiments if row["dataset"] == "20260529"), {})
    row_0509 = next((row for row in experiments if row["dataset"] == "20260509"), {})
    failed = [key for key, value in gates.items() if not value]
    lines = [
        first,
        "",
        "# CROWN-PTT-GreedyMPC Final Report",
        "",
        "## Decision",
        "- recommended_submission: " + ("yes" if ready else "no"),
        "- stop_state: " + ("PTT_SUBMISSION_READY" if ready else "PTT_DIAGNOSTIC_SUCCESS_DO_NOT_SUBMIT"),
        "- default_variant: `preference_firewall_profit`",
        "",
        "## 20260529 Score",
        f"- official_net: {row_0529.get('official_net', 'missing')}",
        f"- gross_minus_cost: {row_0529.get('gross_minus_cost', 'missing')}",
        f"- preference_penalty: {row_0529.get('preference_penalty', 'missing')}",
        f"- illegal_actions: {row_0529.get('illegal_actions', 'missing')}",
        f"- rejected_takes: {row_0529.get('rejected_takes', 'missing')}",
        f"- qwen_compile_calls: {row_0529.get('qwen_compile_calls', 0)}",
        f"- ptt_compile_calls: {row_0529.get('ptt_compile_calls', 0)}",
        f"- ptt_linker_required/called: {row_0529.get('ptt_linker_required', 0)}/{row_0529.get('ptt_linker_calls', 0)}",
        f"- macro_started/completed: {row_0529.get('macro_started', 0)}/{row_0529.get('macro_completed', 0)}",
        "",
        "## 20260509 Regression",
        f"- official_net: {row_0509.get('official_net', 'missing')}",
        f"- preference_penalty: {row_0509.get('preference_penalty', 'missing')}",
        f"- failed_driver_count: {row_0509.get('failed_driver_count', 'missing')}",
        "",
        "## Synthetic PTT",
        f"- total_types: {(synthetic.get('summary') or {}).get('total_types', 'missing')}",
        f"- passed_types: {(synthetic.get('summary') or {}).get('passed_types', 'missing')}",
        f"- failed_types: {', '.join((synthetic.get('summary') or {}).get('failed_types', [])) or 'none'}",
        "",
        "## Remaining Blockers",
    ]
    if failed:
        lines.extend(f"- {key}" for key in failed)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Evidence Files",
            "- `reports/ptt_experiments.csv`",
            "- `reports/ptt_compiler_coverage.csv`",
            "- `reports/ptt_decision_forensics.csv`",
            "- `reports/ptt_submission_audit.md`",
        ]
    )
    (REPORTS / "ptt_final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    _archive_extra_reports()
    synthetic = _read_json(SYNTHETIC_PATH, {"summary": {"all_passed": False}, "rows": []})
    package = _read_json(PACKAGE_AUDIT, {})
    experiments = [_eval_row(dataset, path) for dataset, path in EVALS.items()]
    coverage = _coverage_rows(synthetic)
    forensics = _forensic_rows()
    _write_csv(
        REPORTS / "ptt_experiments.csv",
        experiments,
        [
            "dataset",
            "variant",
            "results_dir",
            "present",
            "official_net",
            "gross_minus_cost",
            "preference_penalty",
            "failed_driver_count",
            "simulation_failures",
            "illegal_actions",
            "rejected_takes",
            "take",
            "wait",
            "reposition",
            "query_minutes_per_take",
            "qwen_compile_calls",
            "qwen_linker_calls",
            "qwen_auditor_calls",
            "ptt_compile_calls",
            "ptt_linker_required",
            "ptt_linker_calls",
            "ptt_auditor_triggers",
            "ptt_blocks",
            "ptt_massive",
            "macro_started",
            "macro_completed",
        ],
    )
    _write_csv(
        REPORTS / "ptt_compiler_coverage.csv",
        coverage,
        [
            "ptt_type",
            "controller_class",
            "paraphrase_count",
            "compiler_schema_pass",
            "positive_pass",
            "negative_pass",
            "repair_pass",
            "linker_behavior_pass",
            "firewall_pass",
            "status",
        ],
    )
    _write_csv(
        REPORTS / "ptt_decision_forensics.csv",
        forensics,
        [
            "dataset",
            "row_index",
            "action",
            "chosen_candidate_hash",
            "ptt_rules",
            "ptt_controllers",
            "vocab_links",
            "firewall_scored",
            "firewall_blocked",
            "firewall_massive",
            "macro_started",
            "macro_completed",
        ],
    )
    gates = _gate_summary(experiments, synthetic, package)
    _write_audit(gates, package)
    _write_final(experiments, synthetic, gates)
    report_count = len([path for path in REPORTS.iterdir() if path.is_file()])
    print(json.dumps({"ready": all(gates.values()), "failed_gates": [k for k, v in gates.items() if not v], "report_count": report_count}, sort_keys=True))
    return 0 if report_count <= 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
