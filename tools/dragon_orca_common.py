"""Shared CROWN-DRAGON-ORCA tooling."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs" / "dragon_orca"
PACKAGES = ROOT / "runs" / "packages"
DOCS_WORK = ROOT / "docs" / "AGENT_WORK"
PRIVATE = ROOT / ".private" / "dragon_orca"
TRACES = RUNS / "traces"
VALUE_MODEL = RUNS / "value_model"
EVOLUTION = RUNS / "evolution"
REVIEWERS = RUNS / "reviewers"

DATASETS = {
    "20260529": ROOT / "demo" / "server" / "data",
    "20260509": ROOT / "_offline_reference_20260509" / "demo" / "server" / "data",
}

FINAL_REPORT = REPORTS / "dragon_orca_final_report.md"
EXPERIMENT_GRID = REPORTS / "dragon_orca_experiment_grid.csv"
REGRET_ATTRIBUTION = REPORTS / "dragon_orca_regret_attribution.csv"
VALUE_MODEL_AUDIT = REPORTS / "dragon_orca_value_model_audit.csv"
PACKAGE_AUDIT = REPORTS / "dragon_orca_package_audit.md"
DISTILLATION_TABLE = TRACES / "dragon_orca_distillation_table.csv"

B0_NET = 5067.69
B0_GROSS = 43207.69
B0_PENALTY = 38140.0

REPORT_FILES = {
    "dragon_orca_final_report.md",
    "dragon_orca_experiment_grid.csv",
    "dragon_orca_regret_attribution.csv",
    "dragon_orca_value_model_audit.csv",
    "dragon_orca_package_audit.md",
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
    "query_minutes_per_take",
    "invalid_count",
    "rejected_take_count",
    "income_abort_count",
    "qwen_compile_calls",
    "qwen_link_calls",
    "qwen_auditor_calls",
    "qwen_numeric_adjustments",
    "schema_valid_rate",
    "behavioral_pref_accuracy",
    "false_safe_rate",
    "false_hard_block_rate",
    "blocked_high_penalty_take_count",
    "penalty_reduction_vs_anchor",
    "gross_loss_vs_anchor",
    "value_model_used_count",
    "beam_used_count",
    "terminal_value_used_count",
    "adaptive_query_used_count",
    "month_end_protection_count",
    "regret_lns_used_count",
    "evolution_generation",
    "b0_action_included_rate",
    "action_signature_match_rate_if_noop",
    "b0_shadow_pure",
    "keep_or_kill",
    "kill_reason",
]

REGRET_FIELDS = [
    "rank",
    "account_id",
    "family",
    "source_trial_id",
    "run_dir",
    "penalty_estimate",
    "gross_at_risk",
    "changed_decision_count",
    "repair_candidate_count",
    "refill_gross_gain",
    "penalty_reintroduced",
    "keep_or_kill",
    "evidence_note",
]

VALUE_AUDIT_FIELDS = [
    "artifact",
    "status",
    "feature_family",
    "label_source",
    "row_count",
    "uses_driver_id",
    "uses_cargo_id",
    "uses_fixed_coordinate",
    "uses_future_cargo",
    "used_in_full_run_count",
    "ablation_delta_net",
    "notes",
]


def ensure_dirs() -> None:
    for path in (REPORTS, RUNS, PACKAGES, DOCS_WORK, PRIVATE, TRACES, VALUE_MODEL, EVOLUTION, REVIEWERS):
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


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


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


def run_cmd(cmd: list[str], *, cwd: Path = ROOT, timeout: int | None = None) -> tuple[int, str, float]:
    start = time.monotonic()
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False, timeout=timeout)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or ""), round(time.monotonic() - start, 2)


def current_branch() -> str:
    rc, out, _ = run_cmd(["git", "branch", "--show-current"])
    return out.strip() if rc == 0 else ""


def current_commit() -> str:
    rc, out, _ = run_cmd(["git", "rev-parse", "HEAD"])
    return out.strip() if rc == 0 else ""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_work_log(message: str) -> None:
    ensure_dirs()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    for name in ("WORK_LOG.md", "work_log.md"):
        with (DOCS_WORK / name).open("a", encoding="utf-8") as handle:
            handle.write(f"- {stamp} {message}\n")
