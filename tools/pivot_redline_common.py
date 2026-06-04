"""Shared CROWN-PIVOT-REDLINE paths and CSV helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs" / "pivot_redline"
PACKAGES = ROOT / "runs" / "packages"
REVIEWERS = RUNS / "reviewers"
PRIVATE = RUNS / "private"
MODELS = RUNS / "models"
TRACES = RUNS / "traces"
PIVOT_AGENT = ROOT / "demo" / "agent" / "pivot_redline"

FINAL_REPORT = REPORTS / "pivot_redline_final_report.md"
EXPERIMENT_GRID = REPORTS / "pivot_redline_experiment_grid.csv"
FORENSICS = REPORTS / "pivot_redline_forensics.csv"
MODEL_TRACE_AUDIT = REPORTS / "pivot_redline_model_and_trace_audit.csv"
PACKAGE_AUDIT = REPORTS / "pivot_redline_package_audit.md"

SUBAGENT_PREFLIGHT = REVIEWERS / "subagent_preflight.md"
DISTILLATION_TABLE = RUNS / "dragon_orca_distillation_table.csv"
TRANSFER_CHECKLIST = RUNS / "redline_runtime_transfer_checklist.csv"
RUNTIME_PATH_AUDIT = RUNS / "audit_pivot_runtime_path.json"

B0_NET = 5067.69
B0_GROSS = 43207.69
B0_PENALTY = 38140.0

REPORT_FILES = {
    "pivot_redline_final_report.md",
    "pivot_redline_experiment_grid.csv",
    "pivot_redline_forensics.csv",
    "pivot_redline_model_and_trace_audit.csv",
    "pivot_redline_package_audit.md",
}

ALLOWED_STOP_STATES = {
    "PIVOT_RECOMMENDED_SUBMISSION",
    "PIVOT_EXPERIMENTAL_SUBMISSION",
    "PIVOT_REVIEW_ONLY_NOT_FOR_SUBMISSION",
    "DO_NOT_SUBMIT_WITH_COMPLETE_NEGATIVE_EVIDENCE",
    "DO_NOT_SUBMIT_WITH_INCOMPLETE_IMPLEMENTATION",
    "DO_NOT_SUBMIT_WITH_INCOMPLETE_SEARCH",
    "PROMPT_NONCOMPLIANCE_FAIL",
    "EXTERNAL_BLOCKER_EVAL_INFRA",
    "EXTERNAL_BLOCKER_REPO_OR_RESOURCE",
    "EXTERNAL_BLOCKER_QWEN_API",
    "EXTERNAL_BLOCKER_SUBAGENT_INFRA",
}

GRID_FIELDS = [
    "trial_id",
    "stage",
    "status",
    "variant",
    "config_hash",
    "params_json",
    "run_dir",
    "command",
    "exit_code",
    "dataset",
    "simulation_days",
    "official_net",
    "gross_minus_cost",
    "preference_penalty",
    "take_count",
    "wait_count",
    "reposition_count",
    "query_count",
    "query_minutes",
    "invalid_count",
    "rejected_take_count",
    "income_abort_count",
    "trace_path",
    "qwen_compile_calls",
    "qwen_link_calls",
    "qwen_auditor_calls",
    "qwen_numeric_adjustments",
    "schema_valid_rate",
    "action_signature_match_rate_if_noop",
    "b0_shadow_pure",
    "b0_pure_action_trace_count",
    "pivot_decide_trace_count",
    "money_backbone_used_count",
    "candidate_bucket_used_count",
    "preference_debt_used_count",
    "risk_model_used_count",
    "value_model_used_count",
    "beam_used_count",
    "query_optimizer_used_count",
    "terminal_value_used_count",
    "online_probe_used_count",
    "month_end_guard_used_count",
    "macro_commitment_used_count",
    "regret_lns_used_count",
    "reevo_generation",
    "counterfactual_regret_rows",
    "reviewer_status",
    "keep_or_kill",
    "kill_reason",
]

FORENSICS_FIELDS = [
    "stage",
    "component",
    "claimed_role",
    "actual_source_file",
    "actually_called_by_runtime",
    "changes_candidate_generation",
    "changes_score",
    "changes_action",
    "uses_rescue_path",
    "trace_source",
    "is_shell",
    "fix_required",
]

MODEL_TRACE_FIELDS = [
    "artifact",
    "module",
    "status",
    "implementation_file",
    "test_file",
    "runtime_trace_field",
    "full_run_rows_used",
    "ablation_delta_net",
    "reviewer_status",
    "keep_or_kill",
    "notes",
]

FORBIDDEN_STATUS = {"PLANNED", "MISSING_RUN", "planned_not_evaluated", "proxy_only", "smoke_only", "synthetic_only"}


def ensure_dirs() -> None:
    for path in (REPORTS, RUNS, PACKAGES, REVIEWERS, PRIVATE, MODELS, TRACES, PIVOT_AGENT):
        path.mkdir(parents=True, exist_ok=True)


def short_hash(value: Any, length: int = 16) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str, separators=(",", ":"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value not in (None, "") else default)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value if value not in (None, "") else default))
    except (TypeError, ValueError):
        return default


def current_branch() -> str:
    proc = subprocess.run(["git", "branch", "--show-current"], cwd=str(ROOT), text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def current_commit() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def extract_stop_state() -> str:
    if not FINAL_REPORT.is_file():
        return ""
    first = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    return first[0].split(":", 1)[0].strip() if first else ""


def row_status_ok(row: dict[str, str] | None) -> bool:
    return bool(row) and row.get("status") == "EXECUTED" and safe_int(row.get("exit_code"), 99) == 0
