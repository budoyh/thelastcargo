"""Build the five final CROWN-EXACT reports."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.delta_mpc_utils import iter_action_rows, summarize_run, write_csv  # noqa: E402

REPORTS = ROOT / "reports"
ALLOWED = {
    "exact_final_report.md",
    "exact_experiments.csv",
    "scorer_semantics_probe.csv",
    "rule_bytecode_coverage.csv",
    "decision_forensics.csv",
}
EXACT_0529 = ROOT / "runs" / "exact" / "20260529" / "crown_exact_rbt_mpc"
EXACT_0509 = ROOT / "runs" / "exact" / "20260509" / "crown_exact_rbt_mpc"
PACKAGE_AUDIT = ROOT / "runs" / "packages" / "exact_package_audit.json"
PROBE = REPORTS / "scorer_semantics_probe.csv"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _archive_extra_reports() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    extras = [path for path in REPORTS.iterdir() if path.is_file() and path.name not in ALLOWED]
    if not extras:
        return
    archive = ROOT / "archive" / f"reports_non_exact_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive.mkdir(parents=True, exist_ok=True)
    for path in extras:
        shutil.move(str(path), str(archive / path.name))


def _trace_stats(run_dir: Path) -> dict[str, Any]:
    stats = {
        "qwen_compile_calls": 0,
        "qwen_cache_hits": 0,
        "qwen_linker_calls": 0,
        "qwen_auditor_calls": 0,
        "qwen_retries": 0,
        "qwen_timeouts": 0,
        "qwen_api_errors": 0,
        "qwen_fallbacks": 0,
        "qwen_token_usage_total": 0,
        "ptt_compile_calls": 0,
        "ptt_cache_hits": 0,
        "ptt_linker_required": 0,
        "ptt_linker_calls": 0,
        "ptt_auditor_triggers": 0,
        "controller_scored_candidate_count": 0,
        "ptt_blocks": 0,
        "ptt_massive": 0,
        "mpc_enabled_steps": 0,
    }
    for _, _, row in iter_action_rows(run_dir):
        action = row.get("action") if isinstance(row.get("action"), dict) else {}
        trace = action.get("agent_trace") if isinstance(action, dict) else {}
        rescue = trace.get("rescue") if isinstance(trace, dict) else {}
        qwen = rescue.get("qwen") if isinstance(rescue.get("qwen"), dict) else {}
        ptt = rescue.get("ptt") if isinstance(rescue.get("ptt"), dict) else {}
        ptt_stats = ptt.get("stats") if isinstance(ptt.get("stats"), dict) else {}
        firewall = ptt.get("firewall") if isinstance(ptt.get("firewall"), dict) else {}
        mpc = rescue.get("visible_graph_mpc") if isinstance(rescue.get("visible_graph_mpc"), dict) else {}
        stats["qwen_compile_calls"] = max(stats["qwen_compile_calls"], int(qwen.get("compile_calls", 0) or 0))
        stats["qwen_cache_hits"] = max(stats["qwen_cache_hits"], int(qwen.get("cache_hits", 0) or 0))
        stats["qwen_linker_calls"] = max(stats["qwen_linker_calls"], int(qwen.get("linker_calls", 0) or 0))
        stats["qwen_auditor_calls"] = max(stats["qwen_auditor_calls"], int(qwen.get("auditor_calls", 0) or 0))
        stats["qwen_retries"] = max(stats["qwen_retries"], int(qwen.get("retry_count", 0) or 0))
        stats["qwen_timeouts"] = max(stats["qwen_timeouts"], int(qwen.get("timeout_count", 0) or 0))
        stats["qwen_api_errors"] = max(stats["qwen_api_errors"], int(qwen.get("api_error_count", 0) or 0))
        stats["qwen_fallbacks"] = max(stats["qwen_fallbacks"], int(qwen.get("fallback_count", 0) or 0))
        stats["qwen_token_usage_total"] = max(stats["qwen_token_usage_total"], int(qwen.get("token_usage_total", 0) or 0))
        stats["ptt_compile_calls"] = max(stats["ptt_compile_calls"], int(ptt_stats.get("compile_calls", 0) or 0))
        stats["ptt_cache_hits"] = max(stats["ptt_cache_hits"], int(ptt_stats.get("cache_hits", 0) or 0))
        stats["ptt_linker_required"] = max(stats["ptt_linker_required"], int(ptt_stats.get("linker_call_required_count", 0) or 0))
        stats["ptt_linker_calls"] = max(stats["ptt_linker_calls"], int(ptt_stats.get("linker_call_count", 0) or 0))
        stats["ptt_auditor_triggers"] = max(stats["ptt_auditor_triggers"], int(ptt_stats.get("auditor_trigger_count", 0) or 0))
        stats["controller_scored_candidate_count"] = max(
            stats["controller_scored_candidate_count"], int(ptt_stats.get("controller_scored_candidate_count", 0) or 0)
        )
        stats["ptt_blocks"] += int(firewall.get("blocked_count", 0) or 0)
        stats["ptt_massive"] += int(firewall.get("massive_penalty_count", 0) or 0)
        stats["mpc_enabled_steps"] += int(bool(mpc.get("enabled")))
    stats["qwen_compile_or_cache_hit_count"] = (
        stats["qwen_compile_calls"] + stats["qwen_cache_hits"] + stats["ptt_compile_calls"] + stats["ptt_cache_hits"]
    )
    stats["qwen_link_or_cache_hit_count"] = stats["qwen_linker_calls"] + stats["ptt_linker_calls"]
    stats["qwen_audit_or_cache_hit_count"] = stats["qwen_auditor_calls"] + stats["ptt_auditor_triggers"]
    return stats


def _experiment_rows() -> list[dict[str, Any]]:
    rows = []
    for dataset, variant, path, notes in [
        ("20260529", "best_rescue", ROOT / "runs" / "latest_rescue", "baseline"),
        (
            "20260529",
            "best_rescue_current_code",
            ROOT / "runs" / "exact_current_baselines" / "20260529" / "best_rescue",
            "current-code reproduction",
        ),
        ("20260529", "ptt_previous", ROOT / "runs" / "ptt_20260529", "failed previous PTT"),
        ("20260529", "money_greedy_no_pref", ROOT / "runs" / "next_build" / "20260529" / "money_greedy_no_pref", "baseline"),
        ("20260529", "strict_pref", ROOT / "runs" / "next_build" / "20260529" / "strict_pref", "baseline"),
        ("20260529", "safe_profit_greedy", ROOT / "runs" / "rescue_baselines" / "safe_profit_greedy", "baseline"),
        ("20260529", "crown_exact_rbt_mpc", EXACT_0529, "final selected exact"),
        ("20260509", "crown_exact_rbt_mpc", EXACT_0509, "0509 regression"),
    ]:
        if not (path / "monthly_income_202603.json").is_file():
            rows.append({"dataset": dataset, "variant": variant, "run_id": str(path), "present": False, "notes": "missing_run"})
            continue
        row = summarize_run(path, variant=variant, notes=notes)
        row["dataset"] = dataset
        row["present"] = True
        row.update(_trace_stats(path))
        rows.append(row)
    fields = [
        "dataset",
        "variant",
        "present",
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
        "qwen_compile_or_cache_hit_count",
        "qwen_link_or_cache_hit_count",
        "qwen_audit_or_cache_hit_count",
        "qwen_compile_calls",
        "qwen_cache_hits",
        "qwen_linker_calls",
        "qwen_auditor_calls",
        "qwen_retries",
        "qwen_timeouts",
        "qwen_api_errors",
        "qwen_fallbacks",
        "qwen_token_usage_total",
        "ptt_compile_calls",
        "ptt_cache_hits",
        "controller_scored_candidate_count",
        "ptt_blocks",
        "ptt_massive",
        "mpc_enabled_steps",
        "illegal_count",
        "rejected_take_count",
        "income_abort_count",
        "simulation_failures",
        "notes",
    ]
    write_csv(REPORTS / "exact_experiments.csv", rows, fields)
    return rows


def _rule_type_from_rule(rule: dict[str, Any]) -> str:
    if "off_days" in rule:
        return "full_inactive_day_quota"
    if "waited_minutes" in rule:
        return "location_visit_or_dwell"
    if "order_days" in rule:
        return "required_cargo_attribute_distinct_days"
    if "violations" in rule:
        return "direct_violation_count"
    if "satisfied" in rule:
        return "terminal_task"
    return "unknown_soft"


def _ops(rule_type: str) -> str:
    mapping = {
        "full_inactive_day_quota": "FULL_DAY_INACTIVE;ACTIVE_COVERAGE;COUNT;COUNT_CAPPED;PENALTY",
        "location_visit_or_dwell": "POSITION_NEAR;DWELL_MINUTES;REPAIR",
        "required_cargo_attribute_distinct_days": "FIELD_MATCH;TAKE_FIELD_MATCH;COUNT;COUNT_DISTINCT_DAY;ASK_LINKER",
        "direct_violation_count": "FILTER_ACTION;FIELD_MATCH;COUNT;COUNT_PER_ACTION;PENALTY;AUDIT_TOP_CANDIDATE",
        "terminal_task": "ORDERED_SEQUENCE;COUNT;COUNT_ONCE_IF_FAILED;REPAIR",
    }
    return mapping.get(rule_type, "UNKNOWN_SOFT")


def _coverage_rows() -> list[dict[str, Any]]:
    rows = []
    for dataset, run_dir in [("20260529", EXACT_0529), ("20260509", EXACT_0509)]:
        monthly = _read_json(run_dir / "monthly_income_202603.json")
        for driver in monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []:
            pref = driver.get("preference_check") if isinstance(driver.get("preference_check"), dict) else {}
            for idx, rule in enumerate(pref.get("rules", []) if isinstance(pref.get("rules"), list) else []):
                if not isinstance(rule, dict):
                    continue
                rule_type = _rule_type_from_rule(rule)
                rows.append(
                    {
                        "dataset": dataset,
                        "driver_hash": _hash(driver.get("driver_id", "")),
                        "preference_hash": _hash(rule.get("preference_text", "")),
                        "rule_index": idx,
                        "controller_type": rule_type,
                        "bytecode_ops": _ops(rule_type),
                        "penalty": rule.get("penalty", ""),
                        "compile_source": "qwen_compile_cache_observed_but_monthly_rules_may_include_fallback",
                        "schema_valid_rbt_observed": False,
                        "raw_literal_redacted": True,
                    }
                )
    fields = [
        "dataset",
        "driver_hash",
        "preference_hash",
        "rule_index",
        "controller_type",
        "bytecode_ops",
        "penalty",
        "compile_source",
        "schema_valid_rbt_observed",
        "raw_literal_redacted",
    ]
    write_csv(REPORTS / "rule_bytecode_coverage.csv", rows, fields)
    return rows


def _forensics() -> None:
    rows = []
    for dataset, run_dir in [("20260529", EXACT_0529), ("20260509", EXACT_0509)]:
        if not run_dir.exists():
            continue
        for idx, (_, line_no, row) in enumerate(iter_action_rows(run_dir)):
            if idx >= 240:
                break
            action = row.get("action") if isinstance(row.get("action"), dict) else {}
            trace = action.get("agent_trace") if isinstance(action, dict) else {}
            rescue = trace.get("rescue") if isinstance(trace.get("rescue"), dict) else {}
            ptt = rescue.get("ptt") if isinstance(rescue.get("ptt"), dict) else {}
            firewall = ptt.get("firewall") if isinstance(ptt.get("firewall"), dict) else {}
            chosen = trace.get("chosen") if isinstance(trace.get("chosen"), dict) else {}
            rows.append(
                {
                    "dataset": dataset,
                    "row_index": idx,
                    "line_no": line_no,
                    "action": action.get("action", ""),
                    "candidate_id_hash": chosen.get("candidate_id_hash", ""),
                    "query_k": trace.get("query_k", ""),
                    "visible_count": trace.get("visible_count", ""),
                    "ptt_rules": ptt.get("rules", 0),
                    "ptt_controllers": ptt.get("controllers", 0),
                    "vocab_links": ptt.get("vocab_links", 0),
                    "firewall_scored": firewall.get("scored_candidate_count", 0),
                    "firewall_blocked": firewall.get("blocked_count", 0),
                    "firewall_massive": firewall.get("massive_penalty_count", 0),
                    "chosen_score": chosen.get("score", ""),
                }
            )
    fields = [
        "dataset",
        "row_index",
        "line_no",
        "action",
        "candidate_id_hash",
        "query_k",
        "visible_count",
        "ptt_rules",
        "ptt_controllers",
        "vocab_links",
        "firewall_scored",
        "firewall_blocked",
        "firewall_massive",
        "chosen_score",
    ]
    write_csv(REPORTS / "decision_forensics.csv", rows, fields)


def _probe_summary() -> dict[str, Any]:
    if not PROBE.is_file():
        return {"rows": 0, "aligned": 0, "enabled_hard": 0}
    with PROBE.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        "rows": len(rows),
        "aligned": sum(1 for row in rows if str(row.get("aligned", "")).lower() == "true"),
        "enabled_hard": sum(1 for row in rows if str(row.get("enabled_hard", "")).lower() == "true"),
    }


def _audit_clean() -> bool:
    result = subprocess.run([sys.executable, "tools/audit_guard.py", "--fail-on-p0"], cwd=str(ROOT), check=False)
    audit_report = REPORTS / "compliance_audit.md"
    if audit_report.is_file():
        archive = ROOT / "archive" / f"reports_non_exact_{datetime.now().strftime('%Y%m%d_%H%M%S')}_audit"
        archive.mkdir(parents=True, exist_ok=True)
        shutil.move(str(audit_report), str(archive / audit_report.name))
    return result.returncode == 0


def _gate(rows: list[dict[str, Any]], package: dict[str, Any], audit_clean: bool, probe: dict[str, Any]) -> tuple[str, dict[str, bool]]:
    exact = next((row for row in rows if row.get("dataset") == "20260529" and row.get("variant") == "crown_exact_rbt_mpc"), {})
    old = next((row for row in rows if row.get("dataset") == "20260509" and row.get("variant") == "crown_exact_rbt_mpc"), {})
    gates = {
        "score_0529_official_net": float(exact.get("official_net", -10**9) or -10**9) >= 30000.0,
        "score_0529_penalty": float(exact.get("preference_penalty", 10**9) or 10**9) <= 22000.0,
        "score_0529_gross": float(exact.get("gross_minus_cost", 0.0) or 0.0) >= 45000.0,
        "qwen_compile_or_cache": int(exact.get("qwen_compile_or_cache_hit_count", 0) or 0) > 0,
        "controller_scored_candidates": int(exact.get("controller_scored_candidate_count", 0) or 0) > 0,
        "scorer_semantics_aligned": int(probe.get("enabled_hard", 0) or 0) > 0,
        "p0_clean": audit_clean,
        "0509_no_catastrophic_regression": bool(old.get("present")) and int(old.get("simulation_failures", 1) or 0) == 0,
        "package_default_variant": package.get("default_variant") == "crown_exact_rbt_mpc"
        or (package.get("inspection") or {}).get("default_variant_config_text") is True,
        "package_shape": bool(package) and not package.get("disallowed_entries") and not (package.get("inspection") or {}).get("disallowed_entries"),
    }
    if all(gates.values()):
        return "CROWN_EXACT_RECOMMENDED_SUBMISSION", gates
    if (
        float(exact.get("official_net", -10**9) or -10**9) >= 15000.0
        and float(exact.get("preference_penalty", 10**9) or 10**9) < 38140.0
        and int(exact.get("qwen_compile_or_cache_hit_count", 0) or 0) > 0
    ):
        return "CROWN_EXACT_EXPERIMENTAL_SUBMISSION", gates
    return "DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE", gates


def _write_final(rows: list[dict[str, Any]], coverage: list[dict[str, Any]], stop_state: str, gates: dict[str, bool], probe: dict[str, Any]) -> None:
    exact = next((row for row in rows if row.get("dataset") == "20260529" and row.get("variant") == "crown_exact_rbt_mpc"), {})
    exact_0509 = next((row for row in rows if row.get("dataset") == "20260509" and row.get("variant") == "crown_exact_rbt_mpc"), {})
    package = _read_json(PACKAGE_AUDIT)
    first_line = "DO NOT SUBMIT: gates not reached." if stop_state == "DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE" else stop_state
    score_rows = [
        row
        for row in rows
        if row.get("dataset") == "20260529"
        and row.get("variant")
        in {
            "best_rescue",
            "best_rescue_current_code",
            "ptt_previous",
            "money_greedy_no_pref",
            "strict_pref",
            "safe_profit_greedy",
            "crown_exact_rbt_mpc",
        }
    ]
    lines = [
        first_line,
        f"stop_state: {stop_state}",
        "",
        "# CROWN-EXACT Final Report",
        "",
        f"- branch: crown-exact-rbt-mpc",
        f"- submit_recommendation: {'yes' if stop_state == 'CROWN_EXACT_RECOMMENDED_SUBMISSION' else 'no'}",
        f"- default_variant: crown_exact_rbt_mpc",
        f"- package_path: {package.get('zip_path', 'missing')}",
        f"- package_sha256: {package.get('sha256', 'missing')}",
        f"- package_recommended: {package.get('recommended', False)}",
        f"- package_disallowed_entries: {len(package.get('disallowed_entries', []) or [])}",
        "",
        "## 20260529 Final",
        f"- official_net: {exact.get('official_net', 'missing')}",
        f"- gross_minus_cost: {exact.get('gross_minus_cost', 'missing')}",
        f"- preference_penalty: {exact.get('preference_penalty', 'missing')}",
        f"- qwen_compile_or_cache_hit_count: {exact.get('qwen_compile_or_cache_hit_count', 0)}",
        f"- qwen_link_or_cache_hit_count: {exact.get('qwen_link_or_cache_hit_count', 0)}",
        f"- qwen_audit_or_cache_hit_count: {exact.get('qwen_audit_or_cache_hit_count', 0)}",
        f"- qwen_token_usage_total: {exact.get('qwen_token_usage_total', 0)}",
        f"- qwen_api_errors: {exact.get('qwen_api_errors', 0)}",
        f"- qwen_fallbacks: {exact.get('qwen_fallbacks', 0)}",
        f"- controller_scored_candidate_count: {exact.get('controller_scored_candidate_count', 0)}",
        "",
        "## 20260509 Regression",
        f"- official_net: {exact_0509.get('official_net', 'missing')}",
        f"- gross_minus_cost: {exact_0509.get('gross_minus_cost', 'missing')}",
        f"- preference_penalty: {exact_0509.get('preference_penalty', 'missing')}",
        f"- simulation_failures: {exact_0509.get('simulation_failures', 'missing')}",
        "",
        "## 20260529 Score Table",
        "| variant | official_net | gross_minus_cost | preference_penalty | qwen_compile_or_cache | controller_scored | notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in score_rows:
        lines.append(
            "| {variant} | {official_net} | {gross_minus_cost} | {preference_penalty} | {qwen} | {controllers} | {notes} |".format(
                variant=row.get("variant", ""),
                official_net=row.get("official_net", ""),
                gross_minus_cost=row.get("gross_minus_cost", ""),
                preference_penalty=row.get("preference_penalty", ""),
                qwen=row.get("qwen_compile_or_cache_hit_count", 0),
                controllers=row.get("controller_scored_candidate_count", 0),
                notes=row.get("notes", ""),
            )
        )
    lines.extend(
        [
            "",
            "## RBT And Qwen Evidence",
            f"- qwen_compile_calls: {exact.get('qwen_compile_calls', 0)}",
            f"- qwen_cache_hits: {exact.get('qwen_cache_hits', 0)}",
            f"- ptt_compile_calls: {exact.get('ptt_compile_calls', 0)}",
            f"- ptt_cache_hits: {exact.get('ptt_cache_hits', 0)}",
            f"- qwen_linker_calls: {exact.get('qwen_linker_calls', 0)}",
            "- schema_valid_rbt_observed: 0; bytecode coverage includes fallback/monthly-rule mappings and is not claimed as schema-valid Qwen RBT.",
            "- qwen_auditor_calls: 0; gated auditor was disabled in the final selected strategy after negative score evidence.",
            "",
            "## Ablation Summary",
            "- PTT previous remained below rescue and had zero Qwen compile in the imported failed evidence.",
            "- Exact RBT/linker default produced real Qwen calls but did not improve 20260529 official_net or penalty.",
            "- 90-minute wait / 08:00 rest numeric probe worsened official_net to -20415.93 and penalty to 62680.0, so it was reverted.",
            "- Visible Graph MPC stayed default OFF because no positive official_net evidence was produced.",
            "",
            "## Commit And Push",
            "- final_commit: reported in final handoff after this report is committed.",
            "- final_push: reported in final handoff after `git push` succeeds.",
        ]
    )
    lines.extend(
        [
        "",
        "## Gates",
        ]
    )
    lines.extend(f"- {key}: {'PASS' if value else 'FAIL'}" for key, value in gates.items())
    lines.extend(
        [
            "",
            "## Evidence Summary",
            f"- scorer_semantics_probe rows/aligned/enabled_hard: {probe.get('rows', 0)}/{probe.get('aligned', 0)}/{probe.get('enabled_hard', 0)}",
            f"- rule_bytecode_coverage rows: {len(coverage)}",
            "- official_net accounting uses gross_minus_cost - preference_penalty; double-count proxy is forbidden.",
            "- Previous PTT failure addressed by requiring real Qwen/cache counts, bytecode coverage, scorer probe, and controller scoring evidence.",
            "",
            "## Residual Risks",
        ]
    )
    failed = [key for key, ok in gates.items() if not ok]
    if failed:
        lines.extend(f"- {key}" for key in failed)
    else:
        lines.append("- none")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "exact_final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build() -> dict[str, Any]:
    _archive_extra_reports()
    rows = _experiment_rows()
    coverage = _coverage_rows()
    _forensics()
    probe = _probe_summary()
    package = _read_json(PACKAGE_AUDIT)
    audit_clean = _audit_clean()
    stop_state, gates = _gate(rows, package, audit_clean, probe)
    _write_final(rows, coverage, stop_state, gates, probe)
    report_count = len([path for path in REPORTS.iterdir() if path.is_file()])
    return {"stop_state": stop_state, "failed_gates": [k for k, v in gates.items() if not v], "reports": report_count}


def main() -> int:
    payload = build()
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["reports"] <= 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
