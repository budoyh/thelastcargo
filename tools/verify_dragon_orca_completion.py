"""Phase-aware CROWN-DRAGON-ORCA completion verifier."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dragon_orca_common as common  # noqa: E402

ALLOWED_STOP_STATES = {
    "DRAGON_RECOMMENDED_SUBMISSION",
    "DRAGON_EXPERIMENTAL_SUBMISSION",
    "DO_NOT_SUBMIT_WITH_COMPLETE_NEGATIVE_EVIDENCE",
    "DO_NOT_SUBMIT_WITH_REVIEW_ONLY_PACKAGE",
    "DO_NOT_SUBMIT_WITH_INCOMPLETE_SEARCH",
    "DO_NOT_SUBMIT_WITH_INTERNAL_COMPILER_FAILURE_BUT_SEARCH_COMPLETE",
    "PROMPT_NONCOMPLIANCE_FAIL",
    "EXTERNAL_BLOCKER_QWEN_API",
    "EXTERNAL_BLOCKER_EVAL_INFRA",
    "EXTERNAL_BLOCKER_REPO_OR_RESOURCE",
}

MANDATORY_IDS = ["D0", "D1", "D2", "D3", "D4", "A1", "A2", "A3"] + [f"M{i}" for i in range(14)]
NOOP_IDS = {"D1", "D2", "D3", "D4"}
FORBIDDEN_STATUS = {"PLANNED", "MISSING_RUN", "planned_not_evaluated", "proxy_only", "smoke_only", "synthetic_only"}


def rows(dataset: str | None = None) -> list[dict[str, str]]:
    data = common.read_csv(common.EXPERIMENT_GRID)
    if dataset is None:
        return data
    return [row for row in data if row.get("dataset") == dataset]


def by_trial(dataset: str = "20260529") -> dict[str, dict[str, str]]:
    return {row.get("trial_id", ""): row for row in rows(dataset)}


def status_ok(row: dict[str, str] | None) -> bool:
    return bool(row) and str(row.get("status", "")).strip() == "EXECUTED" and common.safe_int(row.get("exit_code"), 99) == 0


def bad_run_fields(row: dict[str, str]) -> list[str]:
    out = []
    for field in ("run_dir", "command", "exit_code", "official_net", "gross_minus_cost", "preference_penalty"):
        if row.get(field) in {None, ""}:
            out.append(field)
    run_dir = ROOT / str(row.get("run_dir", ""))
    if row.get("run_dir") and not run_dir.exists():
        out.append("run_dir_exists")
    return out


def fail_setup() -> list[str]:
    failures: list[str] = []
    if common.current_branch() != "crown-dragon-orca-v1-1":
        failures.append(f"wrong branch {common.current_branch()!r}")
    required = [
        ROOT / "AGENTS.md",
        ROOT / "agent.md",
        ROOT / "tools" / "verify_dragon_orca_completion.py",
        ROOT / "tools" / "audit_guard.py",
        common.DOCS_WORK / "PROJECT_MEMORY.md",
        common.DOCS_WORK / "EXECUTION_PLAN.md",
        common.DOCS_WORK / "WORK_LOG.md",
        common.DOCS_WORK / "DRAGON_ORCA_DECISION_NOTES.md",
    ]
    for path in required:
        if not path.is_file():
            failures.append(f"missing setup artifact {path.relative_to(ROOT)}")
    if not common.REPORTS.exists():
        failures.append("reports directory missing")
    text = (ROOT / "tools" / "audit_guard.py").read_text(encoding="utf-8", errors="ignore")
    if "dragon_orca_final_report.md" not in text or "CROWN_DRAGON_ORCA_REVIEW_ONLY" not in text:
        failures.append("audit_guard lacks Dragon-Orca report/package policy")
    return failures


def fail_no_op() -> list[str]:
    failures: list[str] = []
    table = by_trial()
    d0 = table.get("D0")
    if not status_ok(d0):
        failures.append("D0 B0 rescue not EXECUTED")
        return failures
    if common.safe_float(d0.get("official_net")) < 5000:
        failures.append("D0 official_net gate failed")
    if common.safe_float(d0.get("gross_minus_cost")) < 43000:
        failures.append("D0 gross gate failed")
    if common.safe_float(d0.get("preference_penalty")) > 38200:
        failures.append("D0 penalty gate failed")
    if common.safe_int(d0.get("invalid_count")) or common.safe_int(d0.get("rejected_take_count")) or common.safe_int(d0.get("income_abort_count")):
        failures.append("D0 invalid/rejected/income_abort nonzero")
    for trial in sorted(NOOP_IDS):
        row = table.get(trial)
        if not status_ok(row):
            failures.append(f"{trial} not EXECUTED")
            continue
        if common.safe_float(row.get("action_signature_match_rate_if_noop")) < 0.999:
            failures.append(f"{trial} action_signature_match_rate_if_noop < 0.999")
        if abs(common.safe_float(row.get("official_net")) - common.safe_float(d0.get("official_net"))) > 100:
            failures.append(f"{trial} net delta > 100")
        if abs(common.safe_float(row.get("gross_minus_cost")) - common.safe_float(d0.get("gross_minus_cost"))) > 100:
            failures.append(f"{trial} gross delta > 100")
        if abs(common.safe_float(row.get("preference_penalty")) - common.safe_float(d0.get("preference_penalty"))) > 100:
            failures.append(f"{trial} penalty delta > 100")
        if str(row.get("b0_shadow_pure", "")).lower() != "true":
            failures.append(f"{trial} b0_shadow_pure not true")
    return failures


def fail_compiler_gym() -> list[str]:
    failures: list[str] = []
    data = rows()
    if not data:
        failures.append("experiment grid missing")
        return failures
    numeric = sum(common.safe_int(row.get("qwen_numeric_adjustments")) for row in data)
    if numeric:
        failures.append("Qwen numeric auditor adjustment is nonzero")
    strategy_rows = [row for row in data if str(row.get("trial_id", "")).startswith(("M", "G"))]
    if strategy_rows:
        low_schema = [common.safe_float(row.get("schema_valid_rate"), 0.0) for row in strategy_rows]
        if min(low_schema or [1.0]) < 0.98 and len(strategy_rows) < 10:
            failures.append("schema failure exists but strategy search evidence has not continued")
    return failures


def fail_attribution() -> list[str]:
    failures: list[str] = []
    attr = common.read_csv(common.REGRET_ATTRIBUTION)
    if len(attr) < 20:
        failures.append("regret attribution has fewer than top 20 rows")
    penalties = {round(common.safe_float(row.get("penalty_estimate")), 2) for row in attr[:20]}
    if len(penalties) <= 3 and attr:
        failures.append("penalty attribution appears uniform or averaged")
    if not common.DISTILLATION_TABLE.is_file():
        failures.append("dragon_orca_distillation_table.csv missing")
    else:
        distill = common.read_csv(common.DISTILLATION_TABLE)
        if not distill:
            failures.append("distillation table empty")
    return failures


def fail_strategy() -> list[str]:
    failures: list[str] = []
    table = by_trial()
    for trial in MANDATORY_IDS:
        row = table.get(trial)
        if not status_ok(row):
            failures.append(f"mandatory {trial} not EXECUTED")
        elif bad := bad_run_fields(row):
            failures.append(f"{trial} missing fields {bad}")
    for trial, field in {
        "M0": "blocked_high_penalty_take_count",
        "M1": "blocked_high_penalty_take_count",
        "M4": "adaptive_query_used_count",
        "M5": "month_end_protection_count",
        "M6": "value_model_used_count",
        "M7": "beam_used_count",
        "M9": "regret_lns_used_count",
        "M10": "evolution_generation",
        "M11": "evolution_generation",
        "M12": "evolution_generation",
    }.items():
        row = table.get(trial)
        if status_ok(row) and common.safe_float(row.get(field)) <= 0:
            failures.append(f"{trial} has no active trace count for {field}")
    return failures


def fail_search() -> list[str]:
    failures: list[str] = []
    data = rows("20260529")
    for idx, row in enumerate(data, start=2):
        status = str(row.get("status", ""))
        if status in FORBIDDEN_STATUS or status != "EXECUTED":
            failures.append(f"row {idx} forbidden/non-executed status {status}")
        if bad := bad_run_fields(row):
            failures.append(f"row {idx} missing fields {bad}")
        if common.safe_int(row.get("exit_code"), 99) != 0:
            failures.append(f"row {idx} exit_code nonzero")
        if common.safe_int(row.get("qwen_numeric_adjustments")):
            failures.append(f"row {idx} qwen numeric adjustment nonzero")
        command = str(row.get("command", ""))
        if "CROWN_Y_DISABLE_RUNTIME_QWEN=1" in command:
            failures.append(f"row {idx} disables runtime Qwen")
    executed_full = [row for row in data if row.get("status") == "EXECUTED" and common.safe_int(row.get("simulation_days")) == 31]
    if len(executed_full) < 60:
        failures.append(f"executed 20260529 full rows {len(executed_full)} < 60")
    evo_rows = [row for row in executed_full if common.safe_int(row.get("evolution_generation")) > 0]
    if not evo_rows:
        failures.append("no executed ReEvo/evolution full rows")
    if not common.VALUE_MODEL_AUDIT.is_file():
        failures.append("value model audit missing")
    return failures


def extract_stop_state() -> str:
    if not common.FINAL_REPORT.is_file():
        return ""
    first = common.FINAL_REPORT.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    return first[0].split(":", 1)[0].strip() if first else ""


def package_failures(stop_state: str) -> list[str]:
    failures: list[str] = []
    zips = [path for path in common.PACKAGES.glob("CROWN_DRAGON_ORCA*.zip") if path.is_file()]
    if stop_state in {"DRAGON_RECOMMENDED_SUBMISSION", "DRAGON_EXPERIMENTAL_SUBMISSION", "DO_NOT_SUBMIT_WITH_REVIEW_ONLY_PACKAGE"}:
        if len(zips) != 1:
            failures.append(f"expected exactly one Dragon package, found {len(zips)}")
            return failures
        with zipfile.ZipFile(zips[0]) as zf:
            names = [name for name in zf.namelist() if name and not name.endswith("/")]
            if any(not name.startswith("demo/") for name in names):
                failures.append("package root is not demo/")
            if not any(name.startswith("demo/agent/") for name in names):
                failures.append("package missing demo/agent/")
            if "demo/SUBMISSION.md" not in names:
                failures.append("package missing demo/SUBMISSION.md")
            forbidden = [name for name in names if any(part in Path(name).parts for part in ("server", "data", "reports", "runs", "archive", "docs", "keys", "__pycache__")) or name.endswith((".pyc", ".pyo")) or "prompt" in name.lower()]
            if forbidden:
                failures.append(f"package forbidden entries {forbidden[:5]}")
    elif zips:
        failures.append("Dragon package exists for non-package stop state")
    return failures


def fail_final() -> list[str]:
    failures: list[str] = []
    for fn in (fail_setup, fail_no_op, fail_compiler_gym, fail_attribution, fail_strategy, fail_search):
        failures.extend(fn())
    actual = {path.name for path in common.REPORTS.iterdir() if path.is_file()} if common.REPORTS.exists() else set()
    dragon_actual = {name for name in actual if name.startswith("dragon_orca_")}
    if dragon_actual != common.REPORT_FILES:
        failures.append(f"Dragon reports mismatch actual={sorted(dragon_actual)}")
    non_dragon = [name for name in actual if name not in common.REPORT_FILES]
    if non_dragon:
        failures.append(f"non-Dragon files remain in reports: {non_dragon[:10]}")
    stop_state = extract_stop_state()
    if stop_state not in ALLOWED_STOP_STATES:
        failures.append(f"invalid stop_state {stop_state!r}")
    rows_0509 = [row for row in rows("20260509") if row.get("status") == "EXECUTED"]
    if len(rows_0509) < 6:
        failures.append(f"0509 sanity rows {len(rows_0509)} < 6")
    if common.PACKAGE_AUDIT.is_file() and "package_audit_status: PASS" not in common.PACKAGE_AUDIT.read_text(encoding="utf-8", errors="ignore"):
        failures.append("package audit is not PASS")
    failures.extend(package_failures(stop_state))
    return failures


PHASES = {
    "setup": fail_setup,
    "no_op": fail_no_op,
    "compiler_gym": fail_compiler_gym,
    "attribution": fail_attribution,
    "strategy": fail_strategy,
    "search": fail_search,
    "final": fail_final,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=sorted(PHASES), required=True)
    args = parser.parse_args()
    failures = PHASES[args.phase]()
    status = "PASS" if not failures else "FAIL"
    print({"phase": args.phase, "status": status, "failures": failures})
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
