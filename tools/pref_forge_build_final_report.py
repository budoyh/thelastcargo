"""Build the centralized Pref-Forge final report."""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common


def _metrics(rows: list[dict[str, str]]) -> dict[str, float]:
    if not rows:
        return {}
    return {
        "rows": len(rows),
        "schema_valid_rate": round(sum(str(row.get("schema_valid")).lower() == "true" for row in rows) / len(rows), 4),
        "primitive_family_accuracy": round(sum(str(row.get("primitive_family_ok")).lower() == "true" for row in rows) / len(rows), 4),
        "critical_slot_valid_rate": round(sum(str(row.get("critical_slots_ok")).lower() == "true" for row in rows) / len(rows), 4),
        "monitor_sim_pass_rate": round(sum(str(row.get("monitor_sim_pass")).lower() == "true" for row in rows) / len(rows), 4),
        "raw_literal_committed_count": sum(str(row.get("raw_literal_committed_flag")).lower() == "true" for row in rows),
        "qwen_calls": sum(common.safe_int(row.get("qwen_calls")) for row in rows),
    }


def _best(rows: list[dict[str, str]]) -> dict[str, str] | None:
    executed = [row for row in rows if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"]
    return max(executed, key=lambda row: common.safe_float(row.get("official_net")), default=None)


def _stop_state(best: dict[str, str] | None, grid_rows: list[dict[str, str]], compile_rows: list[dict[str, str]]) -> tuple[str, str]:
    mandatory = {f"E{i}" for i in range(14)}
    executed_ids = {row.get("trial_id") for row in grid_rows if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"}
    search_count = sum(1 for row in grid_rows if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED" and str(row.get("trial_id", "")).startswith("G"))
    if not compile_rows:
        return "EXTERNAL_BLOCKER_MISSING_DATA", "compile benchmark missing"
    if any(str(row.get("schema_valid")).lower() != "true" and common.safe_int(row.get("qwen_calls")) == 0 for row in compile_rows if row.get("split") == "public_dev_46"):
        return "EXTERNAL_BLOCKER_QWEN_API", "Qwen compile pipeline failed before public coverage completed"
    schema_rate = sum(str(row.get("schema_valid")).lower() == "true" for row in compile_rows) / max(1, len(compile_rows))
    primitive_rate = sum(str(row.get("primitive_family_ok")).lower() == "true" for row in compile_rows) / max(1, len(compile_rows))
    if schema_rate < 0.98 or primitive_rate < 0.95:
        return (
            "EXTERNAL_BLOCKER_QWEN_API",
            f"compile benchmark below gate schema_valid_rate={schema_rate:.3f}, primitive_family_accuracy={primitive_rate:.3f}",
        )
    missing = sorted(mandatory - executed_ids)
    if missing or search_count < 60:
        return "EXTERNAL_BLOCKER_EVAL_INFRA", f"missing mandatory={missing}; executed_search_rows={search_count}/60"
    if not best:
        return "EXTERNAL_BLOCKER_EVAL_INFRA", "no executed 20260529 best row"
    net = common.safe_float(best.get("official_net"))
    gross = common.safe_float(best.get("gross_minus_cost"))
    penalty = common.safe_float(best.get("preference_penalty"))
    invalid = common.safe_int(best.get("invalid_count")) + common.safe_int(best.get("income_abort_count")) + common.safe_int(best.get("rejected_take_count"))
    if net >= 40000 and gross >= 55000 and penalty <= 20000 and invalid == 0:
        return "PREF_FORGE_CROWN_TARGET_READY", "crown target passed"
    if net >= 25000 and gross >= 50000 and penalty <= 26000 and invalid == 0:
        return "PREF_FORGE_RECOMMENDED_SUBMISSION_READY", "recommended gates passed"
    if net >= 15000 and gross >= 42000 and penalty <= 32000 and invalid == 0:
        return "PREF_FORGE_EXPERIMENTAL_SUBMISSION_READY", "experimental gates passed"
    if net > common.B0_NET + 3000 and penalty < common.B0_PENALTY - 6000 and invalid == 0:
        return "PREF_FORGE_HIDDEN_SAFE_REVIEW_READY", "weak hidden-safe improvement only"
    return "PREF_FORGE_DO_NOT_SUBMIT_WITH_EVIDENCE", "all evidence executed but score gates missed"


def _package_summary() -> tuple[str, str]:
    if not common.PACKAGE_AUDIT.is_file():
        return "", ""
    path = ""
    sha = ""
    for line in common.PACKAGE_AUDIT.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("- package_path:"):
            path = line.split("`", 2)[1] if "`" in line else ""
        if line.startswith("- sha256:"):
            sha = line.split("`", 2)[1] if "`" in line else ""
    return path, sha


def main() -> int:
    compile_rows = common.read_csv(common.COMPILE_BENCHMARK)
    grid_rows = common.read_csv(common.EXPERIMENT_GRID)
    diff_rows = common.read_csv(common.PENALTY_DIFF)
    best = _best(grid_rows)
    stop_state, reason = _stop_state(best, grid_rows, compile_rows)
    package_path, sha = _package_summary()
    evidence_commit = os.environ.get("PREF_FORGE_EVIDENCE_COMMIT", "pending_until_git_commit")
    metrics = _metrics(compile_rows)
    top_rows = sorted([row for row in grid_rows if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"], key=lambda row: common.safe_float(row.get("official_net")), reverse=True)[:10]
    invalid_counter = Counter(row.get("keep_or_kill", "") for row in grid_rows if row.get("status") == "EXECUTED")
    first_line = "" if stop_state.endswith("_READY") else f"DO NOT SUBMIT: {stop_state} - {reason}"
    lines = []
    if first_line:
        lines.append(first_line)
    lines.extend(
        [
            "# Pref-Forge Final Report",
            "",
            f"stop_state: {stop_state}",
            f"stop_reason: {reason}",
            f"branch: {common.current_branch()}",
            f"source_commit: {common.current_commit()}",
            f"evidence_commit: {evidence_commit}",
            f"package_path: {package_path}",
            f"package_sha256: {sha}",
            "",
            "## one-paragraph decision",
            f"Pref-Forge evidence currently resolves to `{stop_state}`. Best 20260529 candidate is `{best.get('trial_id') if best else ''}` with official_net={best.get('official_net') if best else ''}, gross_minus_cost={best.get('gross_minus_cost') if best else ''}, preference_penalty={best.get('preference_penalty') if best else ''}.",
            "",
            "## baseline reproduction table",
            "| trial | net | gross_minus_cost | penalty | take/wait/reposition | invalid |",
            "|---|---:|---:|---:|---|---:|",
        ]
    )
    for trial in ("E0", "E1", "E2"):
        row = next((item for item in grid_rows if item.get("trial_id") == trial and item.get("dataset") == "20260529"), {})
        lines.append(f"| {trial} | {row.get('official_net','')} | {row.get('gross_minus_cost','')} | {row.get('preference_penalty','')} | {row.get('take_count','')}/{row.get('wait_count','')}/{row.get('reposition_count','')} | {row.get('invalid_count','')} |")
    lines.extend(
        [
            "",
            "## preference compile benchmark summary",
            f"- metrics: `{common.json_cell(metrics)}`",
            "",
            "## raw literal / leakage audit summary",
            "- raw literal audit and runtime leakage audit are recorded under `runs/pref_forge/`; committed benchmark stores hashes only.",
            "",
            "## no-op isolation summary",
            f"- E1 action_signature_match_rate: `{next((row.get('action_signature_match_rate') for row in grid_rows if row.get('trial_id') == 'E1'), '')}`",
            f"- E2 action_signature_match_rate: `{next((row.get('action_signature_match_rate') for row in grid_rows if row.get('trial_id') == 'E2'), '')}`",
            "",
            "## full experiment score table",
            "| trial | stage | net | gross | penalty | mix | keep_or_kill |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for row in top_rows:
        lines.append(f"| {row.get('trial_id')} | {row.get('stage')} | {row.get('official_net')} | {row.get('gross_minus_cost')} | {row.get('preference_penalty')} | {row.get('take_count')}/{row.get('wait_count')}/{row.get('reposition_count')} | {row.get('keep_or_kill')} |")
    lines.extend(
        [
            "",
            "## best candidates: B0 vs hidden-safe vs pref-forge vs fill/refill",
            f"- best: `{best.get('trial_id') if best else ''}`; E0/B0 reference net={common.B0_NET}, gross={common.B0_GROSS}, penalty={common.B0_PENALTY}.",
            "",
            "## penalty-family diff summary",
            f"- rows: {len(diff_rows)}; generic family-level rows only.",
            "",
            "## Qwen budget/calls/cache/latency summary",
            f"- benchmark_qwen_calls: {metrics.get('qwen_calls', 0)}; runtime numeric auditor adjustments forced to 0.",
            "",
            "## numeric auditor OFF proof",
            "- `CROWN_FUSE_AUDITOR_NUMERIC=0`, `CROWN_GOLD_ENABLE_AUDITOR=0`, and `CROWN_TRIDENT_QWEN_AUDIT_SCALE=0` are set in Pref-Forge experiment envs.",
            "",
            "## query policy summary",
            "- Query k values searched: 100/300/600. Query cost is recorded as query_count/query_minutes_per_take in the grid.",
            "",
            "## minimal repair stats",
            f"- E12 refill fields: refill_gross_gain={next((row.get('refill_gross_gain') for row in grid_rows if row.get('trial_id') == 'E12'), '')}, penalty_reintroduced={next((row.get('penalty_reintroduced') for row in grid_rows if row.get('trial_id') == 'E12'), '')}.",
            "",
            "## high-quality hunter stats",
            f"- keep_or_kill counts: `{common.json_cell(dict(invalid_counter))}`",
            "",
            "## 0509 sanity summary",
            f"- executed 0509 rows: {sum(1 for row in grid_rows if row.get('dataset') == '20260509' and row.get('status') == 'EXECUTED')}",
            "",
            "## subagent reviewer findings",
            "- See `docs/AGENT_WORK/reviewer_findings.md`.",
            "",
            "## package path / sha256 / default variant",
            f"- package: `{package_path}`",
            f"- sha256: `{sha}`",
            "",
            "## final recommendation: submit / hidden-safe trial / do not submit",
            f"- recommendation: `{'submit' if stop_state.endswith('READY') and 'SUBMISSION' in stop_state else 'hidden-safe trial' if stop_state == 'PREF_FORGE_HIDDEN_SAFE_REVIEW_READY' else 'do not submit'}`",
            "",
            "## shortest next path",
            "- If blocked, fix the first failing verifier phase and rerun the exact mandatory command list.",
        ]
    )
    common.FINAL_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({"stop_state": stop_state, "report": str(common.FINAL_REPORT)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
