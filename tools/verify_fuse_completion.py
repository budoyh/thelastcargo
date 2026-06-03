"""Verify CROWN-FUSE / RESCUE-SWITCH completion evidence.

The verifier is intentionally phase-aware.  Isolation mode checks only B0/B1/B2/B3
no-op evidence; search mode checks real executed fuse grid evidence; final mode
re-runs those checks and then enforces B10/B11, Qwen, graph, 0509, report, and
package gates.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs"
PACKAGES = RUNS / "packages"

FUSE_REPORTS = {
    "fuse_final_report.md",
    "fuse_grid.csv",
    "fuse_noop_isolation.csv",
    "fuse_rule_ledger.csv",
    "fuse_package_audit.md",
}

FORBIDDEN_STATUS_VALUES = {"PLANNED", "MISSING_RUN", "planned_not_evaluated", "proxy_only"}
EXECUTED_STATUS_VALUES = {"EXECUTED"}
VALID_STOP_STATES = {
    "FUSE_RECOMMENDED_SUBMISSION",
    "FUSE_EXPERIMENTAL_SUBMISSION",
    "FUSE_REVIEW_PACKAGES_ONLY",
    "DO_NOT_SUBMIT_WITH_FUSE_EVIDENCE",
    "EXTERNAL_BLOCKER_RESCUE_ISOLATION",
    "EXTERNAL_BLOCKER_EVAL_INFRA",
    "EXTERNAL_BLOCKER_QWEN",
}

B0_NAMES = {"B0", "B0_rescue", "B0_best_rescue", "fuse_rescue_core", "best_rescue"}
B1_NAMES = {"B1", "B1_all_overlays_off"}
B2_NAMES = {"B2", "B2_contract_compile_logging_only"}
B3_NAMES = {"B3", "B3_contract_monitor_no_score"}
B9C_NAMES = {"B9c", "B9c_reference_current_branch", "B9c_wait_repair_full"}
B10_NAMES = {"B10", "B10_parameter_search_best", "B10_targeted_search_best"}
B11_NAMES = {"B11", "B11_final_selected"}

IDENTITY_COLUMNS = ("stage", "variant_key", "variant", "variant_name", "run_id")
QWEN_COMPILE_COLUMNS = (
    "qwen_compile_or_cache_hit_count",
    "qwen_compile_count",
    "qwen_compile_calls",
    "qwen_contract_compile_count",
    "qwen_compile_cache_hit_count",
    "qwen_contract_cache_hit_count",
)
QWEN_LINK_COLUMNS = (
    "qwen_link_or_cache_hit_count",
    "qwen_link_count",
    "qwen_link_calls",
    "qwen_vocab_link_count",
    "qwen_link_cache_hit_count",
)
INVALID_COLUMNS = (
    "simulation_failures",
    "failure_count",
    "income_aborts",
    "income_abort_count",
    "abort_count",
    "illegal_actions",
    "illegal_count",
    "rejected_takes",
    "rejected_take_count",
)


@dataclass
class Finding:
    severity: str
    message: str
    path: Path | None = None


@dataclass
class Verifier:
    phase: str
    findings: list[Finding] = field(default_factory=list)

    def fail(self, message: str, path: Path | None = None) -> None:
        self.findings.append(Finding("FAIL", message, path))

    def warn(self, message: str, path: Path | None = None) -> None:
        self.findings.append(Finding("WARN", message, path))

    def info(self, message: str, path: Path | None = None) -> None:
        self.findings.append(Finding("INFO", message, path))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def as_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in {"", None}:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    if value in {"", None}:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def row_value(row: dict[str, str], *names: str, default: str = "") -> str:
    for name in names:
        value = row.get(name)
        if value not in {"", None}:
            return str(value)
    return default


def numeric_sum(row: dict[str, str], names: Iterable[str]) -> int:
    return sum(as_int(row.get(name)) for name in names)


def status(row: dict[str, str]) -> str:
    return row_value(row, "status").strip()


def row_identity(row: dict[str, str]) -> str:
    parts = [row_value(row, name) for name in IDENTITY_COLUMNS]
    return "/".join(part for part in parts if part) or "<unidentified>"


def row_has_any_name(row: dict[str, str], names: set[str]) -> bool:
    haystack = {row_value(row, name).strip() for name in IDENTITY_COLUMNS}
    return bool(haystack & names)


def find_row(rows: Iterable[dict[str, str]], names: set[str], *, dataset: str | None = "20260529") -> dict[str, str] | None:
    matches = []
    for row in rows:
        if dataset is not None and row_value(row, "dataset", default=dataset) != dataset:
            continue
        if row_has_any_name(row, names):
            matches.append(row)
    executed = [row for row in matches if status(row) in EXECUTED_STATUS_VALUES and has_score(row)]
    if executed:
        return max(executed, key=lambda row: as_float(row.get("official_net"), -10**9) or -10**9)
    return matches[-1] if matches else None


def has_score(row: dict[str, str]) -> bool:
    return all(row.get(name) not in {"", None} for name in ("official_net", "gross_minus_cost", "preference_penalty"))


def run_dir_exists(row: dict[str, str]) -> bool:
    run_dir = row_value(row, "run_dir", "results_dir")
    if not run_dir:
        return False
    path = Path(run_dir)
    if not path.is_absolute():
        path = ROOT / path
    return path.exists()


def command_disables_qwen(command: str) -> bool:
    return "CROWN_Y_DISABLE_RUNTIME_QWEN=1" in command or "CROWN_Y_DISABLE_RUNTIME_QWEN'='1" in command


def git_branch() -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=str(ROOT), text=True).strip()
    except Exception:
        return ""


def check_branch(verifier: Verifier) -> None:
    branch = git_branch()
    if branch != "crown-fuse-rescue-switch":
        verifier.fail(f"current branch is {branch!r}, expected crown-fuse-rescue-switch")
    else:
        verifier.info("current branch is crown-fuse-rescue-switch")


def check_required_file(verifier: Verifier, path: Path) -> None:
    if not path.is_file():
        verifier.fail(f"required file missing: {path.relative_to(ROOT)}", path)


def check_b0_gate(verifier: Verifier, row: dict[str, str], source: Path) -> None:
    if status(row) not in EXECUTED_STATUS_VALUES:
        verifier.fail(f"B0 is not EXECUTED: {status(row)!r} ({row_identity(row)})", source)
    if not has_score(row):
        verifier.fail(f"B0 missing official score fields ({row_identity(row)})", source)
        return
    net = as_float(row.get("official_net"), -10**9) or -10**9
    gross = as_float(row.get("gross_minus_cost"), -10**9) or -10**9
    penalty = as_float(row.get("preference_penalty"), 10**9) or 10**9
    invalid = numeric_sum(row, INVALID_COLUMNS)
    if net < 5000 or gross < 43000 or penalty > 38200 or invalid != 0:
        verifier.fail(
            "B0 rescue gate failed: "
            f"net={net}, gross_minus_cost={gross}, preference_penalty={penalty}, invalid={invalid}",
            source,
        )
    if abs((gross - penalty) - net) > 0.10:
        verifier.fail(f"B0 score accounting mismatch: gross-penalty={gross - penalty:.2f}, official_net={net:.2f}", source)


def check_noop_isolation(verifier: Verifier) -> dict[str, str] | None:
    path = REPORTS / "fuse_noop_isolation.csv"
    rows = read_csv(path)
    if not rows:
        verifier.fail("fuse_noop_isolation.csv is missing or empty", path)
        return None
    for idx, row in enumerate(rows, start=2):
        if status(row) in FORBIDDEN_STATUS_VALUES:
            verifier.fail(f"forbidden status at fuse_noop_isolation.csv row {idx}: {status(row)}", path)
        if row_value(row, "keep_or_kill") in FORBIDDEN_STATUS_VALUES:
            verifier.fail(f"forbidden keep_or_kill at fuse_noop_isolation.csv row {idx}", path)
        command = row_value(row, "command")
        if command_disables_qwen(command):
            verifier.fail(f"runtime Qwen disabled in isolation command at row {idx}", path)

    required = {
        "B0": B0_NAMES,
        "B1": B1_NAMES,
        "B2": B2_NAMES,
        "B3": B3_NAMES,
    }
    found: dict[str, dict[str, str]] = {}
    for key, names in required.items():
        row = find_row(rows, names)
        if not row:
            verifier.fail(f"{key} isolation row missing", path)
            continue
        found[key] = row
        if status(row) not in EXECUTED_STATUS_VALUES:
            verifier.fail(f"{key} isolation row not EXECUTED: {status(row)!r} ({row_identity(row)})", path)
        for column in ("run_dir", "command", "exit_code", "official_net", "gross_minus_cost", "preference_penalty"):
            if row.get(column) in {"", None}:
                verifier.fail(f"{key} isolation row missing {column}", path)
        if row.get("run_dir") and not run_dir_exists(row):
            verifier.fail(f"{key} run_dir does not exist: {row_value(row, 'run_dir')}", path)

    b0 = found.get("B0")
    if not b0:
        return None
    check_b0_gate(verifier, b0, path)
    b0_net = as_float(b0.get("official_net"), 0.0) or 0.0
    b0_gross = as_float(b0.get("gross_minus_cost"), 0.0) or 0.0
    b0_penalty = as_float(b0.get("preference_penalty"), 0.0) or 0.0
    b0_take = as_int(row_value(b0, "take_count", "take"))
    b0_wait = as_int(row_value(b0, "wait_count", "wait"))
    b0_reposition = as_int(row_value(b0, "reposition_count", "reposition"))

    for key in ("B1", "B2", "B3"):
        row = found.get(key)
        if not row:
            continue
        match = as_float(row.get("action_signature_match_rate"), None)
        if match is None:
            verifier.fail(f"{key} missing action_signature_match_rate", path)
        elif match < 0.999:
            verifier.fail(f"{key} action_signature_match_rate {match:.6f} < 0.999", path)
        net = as_float(row.get("official_net"), 0.0) or 0.0
        gross = as_float(row.get("gross_minus_cost"), 0.0) or 0.0
        penalty = as_float(row.get("preference_penalty"), 0.0) or 0.0
        if abs(net - b0_net) > 100 or abs(gross - b0_gross) > 100 or abs(penalty - b0_penalty) > 100:
            verifier.fail(
                f"{key} score drift exceeds no-op tolerance: "
                f"net_delta={net - b0_net:.2f}, gross_delta={gross - b0_gross:.2f}, penalty_delta={penalty - b0_penalty:.2f}",
                path,
            )
        take = as_int(row_value(row, "take_count", "take"))
        wait = as_int(row_value(row, "wait_count", "wait"))
        reposition = as_int(row_value(row, "reposition_count", "reposition"))
        if abs(take - b0_take) > 1 or abs(wait - b0_wait) > 1 or abs(reposition - b0_reposition) > 1:
            verifier.fail(
                f"{key} action mix drift exceeds tolerance: "
                f"take={take}/{b0_take}, wait={wait}/{b0_wait}, reposition={reposition}/{b0_reposition}",
                path,
            )

    b2_b3_compile = sum(numeric_sum(found[key], QWEN_COMPILE_COLUMNS) for key in ("B2", "B3") if key in found)
    b2_b3_link = sum(numeric_sum(found[key], QWEN_LINK_COLUMNS) for key in ("B2", "B3") if key in found)
    if b2_b3_compile <= 0:
        verifier.fail("Qwen compile/cache count is 0 across B2/B3 no-op rows", path)
    if b2_b3_link <= 0:
        verifier.fail("Qwen link/cache count is 0 across B2/B3 no-op rows", path)
    return b0


def check_grid_row(verifier: Verifier, row: dict[str, str], idx: int, path: Path) -> None:
    row_status = status(row)
    if row_status in FORBIDDEN_STATUS_VALUES or row_value(row, "keep_or_kill") in FORBIDDEN_STATUS_VALUES:
        verifier.fail(f"forbidden planned/missing/proxy status in fuse_grid.csv row {idx}: {row_identity(row)}", path)
    if row_status == "EXECUTED":
        for column in ("run_dir", "command", "exit_code", "official_net", "gross_minus_cost", "preference_penalty"):
            if row.get(column) in {"", None}:
                verifier.fail(f"EXECUTED grid row {idx} missing {column}: {row_identity(row)}", path)
        if row.get("run_dir") and not run_dir_exists(row):
            verifier.fail(f"grid row {idx} run_dir does not exist: {row_value(row, 'run_dir')}", path)
    command = row_value(row, "command")
    if command_disables_qwen(command):
        verifier.fail(f"runtime Qwen disabled in grid command at row {idx}", path)


def grid_executed_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if status(row) in EXECUTED_STATUS_VALUES
        and has_score(row)
        and row_value(row, "dataset", default="20260529") == "20260529"
    ]


def check_search(verifier: Verifier, *, require_final_ledger: bool = False) -> tuple[list[dict[str, str]], dict[str, str] | None]:
    path = REPORTS / "fuse_grid.csv"
    rows = read_csv(path)
    if not rows:
        verifier.fail("fuse_grid.csv is missing or empty", path)
        return [], None
    for idx, row in enumerate(rows, start=2):
        check_grid_row(verifier, row, idx, path)
    executed = grid_executed_rows(rows)
    if len(executed) < 60:
        verifier.fail(f"executed 20260529 fuse grid row count is {len(executed)}, expected >= 60", path)

    compile_total = sum(numeric_sum(row, QWEN_COMPILE_COLUMNS) for row in executed)
    link_total = sum(numeric_sum(row, QWEN_LINK_COLUMNS) for row in executed)
    if compile_total <= 0:
        verifier.fail("Qwen compile/cache total is 0 across executed fuse grid rows", path)
    if link_total <= 0:
        verifier.fail("Qwen link/cache total is 0 across executed fuse grid rows", path)

    b9c = find_row(rows, B9C_NAMES)
    ledger_path = REPORTS / "fuse_rule_ledger.csv"
    ledger_exists = ledger_path.is_file() and ledger_path.stat().st_size > 0
    if ledger_exists or require_final_ledger:
        if not b9c:
            verifier.fail("B9c_reference_current_branch row missing before fuse_rule_ledger.csv use", path)
        elif status(b9c) not in EXECUTED_STATUS_VALUES or not has_score(b9c):
            verifier.fail(f"B9c_reference_current_branch is not executed with score: {row_identity(b9c)}", path)
        if not ledger_exists:
            verifier.fail("fuse_rule_ledger.csv is missing or empty", ledger_path)
        else:
            check_rule_ledger(verifier)
    b0 = find_row(rows, B0_NAMES)
    if promising_signal(executed, b0) and len(executed) < 100:
        verifier.fail("promising signal trigger reached but executed 20260529 fuse grid rows are fewer than 100", path)
    return executed, b0


def check_rule_ledger(verifier: Verifier) -> None:
    path = REPORTS / "fuse_rule_ledger.csv"
    rows = read_csv(path)
    if not rows:
        verifier.fail("fuse_rule_ledger.csv is missing or empty", path)
        return
    required = {
        "rule_family",
        "b0_penalty",
        "b9c_penalty",
        "delta_penalty",
        "estimated_delta_gross_share",
        "repair_action_types",
        "repair_minutes",
        "repair_reposition_count",
        "candidate_keep_repair_for_family",
        "controller_family_scale",
        "primitive_family_scale",
        "counting_unit_scale",
        "deadline_curve",
        "repair_multiplier",
        "already_failed_discount",
        "cap_discount",
        "reason",
    }
    missing = required - set(rows[0].keys())
    if missing:
        verifier.fail(f"fuse_rule_ledger.csv missing required columns: {sorted(missing)}", path)
    forbidden_columns = {
        "rule_hash",
        "rule_hash_redacted",
        "driver_hash",
        "preference_hash",
        "cargo_id",
        "driver_id",
        "place",
        "city",
        "coordinate",
        "route",
    }
    present_forbidden = forbidden_columns & set(rows[0].keys())
    if present_forbidden:
        verifier.fail(f"fuse_rule_ledger.csv contains forbidden specificity columns: {sorted(present_forbidden)}", path)


def promising_signal(executed: list[dict[str, str]], b0: dict[str, str] | None) -> bool:
    if not b0:
        return False
    b0_net = as_float(b0.get("official_net"), 0.0) or 0.0
    b0_penalty = as_float(b0.get("preference_penalty"), 0.0) or 0.0
    for row in executed:
        if row_has_any_name(row, B0_NAMES):
            continue
        net = as_float(row.get("official_net"), -10**9) or -10**9
        gross = as_float(row.get("gross_minus_cost"), -10**9) or -10**9
        penalty = as_float(row.get("preference_penalty"), 10**9) or 10**9
        net_delta = as_float(row.get("net_delta_vs_b0"), None)
        penalty_delta_vs_b0 = as_float(row.get("penalty_delta_vs_b0"), None)
        net_improved = (net_delta is not None and net_delta >= 3000) or (net - b0_net >= 3000)
        penalty_reduced = (
            (penalty_delta_vs_b0 is not None and penalty_delta_vs_b0 <= -3000)
            or (b0_penalty - penalty >= 3000)
        )
        if net_improved or (penalty_reduced and gross >= 39000):
            return True
    return False


def check_final_rows(verifier: Verifier, executed: list[dict[str, str]], b0: dict[str, str] | None) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    path = REPORTS / "fuse_grid.csv"
    all_rows = read_csv(path)
    b10 = find_row(all_rows, B10_NAMES)
    b11 = find_row(all_rows, B11_NAMES)
    for key, row in (("B10", b10), ("B11", b11)):
        if not row:
            verifier.fail(f"{key} final required row missing", path)
            continue
        if status(row) not in EXECUTED_STATUS_VALUES:
            verifier.fail(f"{key} is not EXECUTED: {status(row)!r} ({row_identity(row)})", path)
        if not has_score(row):
            verifier.fail(f"{key} missing official score fields ({row_identity(row)})", path)
        if not run_dir_exists(row):
            verifier.fail(f"{key} run_dir missing or does not exist: {row_value(row, 'run_dir')}", path)
        run_dir = row_value(row, "run_dir").replace("\\", "/").lower()
        if "surge" in run_dir or "trident" in run_dir:
            verifier.fail(f"{key} appears to reference old run_dir instead of Fuse evidence: {run_dir}", path)

    if promising_signal(executed, b0) and len(executed) < 100:
        verifier.fail("promising signal trigger reached but executed 20260529 fuse grid rows are fewer than 100", path)

    if b11 and b0 and has_score(b11):
        b0_net = as_float(b0.get("official_net"), 0.0) or 0.0
        best_non_b0 = max(
            (
                as_float(row.get("official_net"), -10**9) or -10**9
                for row in executed
                if not row_has_any_name(row, B0_NAMES | B10_NAMES | B11_NAMES)
            ),
            default=-10**9,
        )
        b11_net = as_float(b11.get("official_net"), -10**9) or -10**9
        if best_non_b0 <= b0_net and b11_net <= b0_net:
            identity = row_identity(b11).lower()
            fallback = boolish(row_value(b11, "fallback_to_b0")) or "b0_fallback" in identity or "best_rescue" in identity or "fuse_rescue_core" in identity
            if not fallback:
                verifier.fail("no search variant beats B0, but B11 is not marked as explicit B0 fallback rerun", path)

    if b11:
        compile_count = numeric_sum(b11, QWEN_COMPILE_COLUMNS)
        link_count = numeric_sum(b11, QWEN_LINK_COLUMNS)
        if compile_count <= 0:
            verifier.fail("B11 Qwen compile/cache count is 0", path)
        if link_count <= 0:
            verifier.fail("B11 Qwen link/cache count is 0", path)
    return b10, b11


def auditor_numeric_enabled(row: dict[str, str] | None) -> bool:
    if not row:
        return False
    return (
        boolish(row_value(row, "qwen_auditor_numeric", "auditor_numeric_enabled"))
        or as_float(row_value(row, "qwen_auditor_numeric_weight", "auditor_weight"), 0.0) not in {0.0, None}
        or "auditor_score_on" in row_identity(row).lower()
    )


def check_auditor_ablation(verifier: Verifier, b11: dict[str, str] | None) -> None:
    if not auditor_numeric_enabled(b11):
        return
    path = REPORTS / "fuse_grid.csv"
    rows = read_csv(path)
    off = find_row(rows, {"A0", "A0_auditor_score_off", "auditor_score_off"})
    low = find_row(rows, {"A1", "A1_auditor_score_on_low_weight", "auditor_score_on_low_weight"})
    high = find_row(rows, {"A2", "A2_auditor_score_on_high_weight", "auditor_score_on_high_weight"})
    if not off or not (low or high):
        verifier.fail("auditor numeric enabled in B11 but A0/A1/A2 ablation rows are missing", path)
        return
    off_net = as_float(off.get("official_net"), -10**9) or -10**9
    off_gross = as_float(off.get("gross_minus_cost"), -10**9) or -10**9
    off_penalty = as_float(off.get("preference_penalty"), 10**9) or 10**9
    viable = False
    for row in (low, high):
        if not row:
            continue
        valid_rate = as_float(row_value(row, "json_valid_rate", "qwen_auditor_json_valid_rate"), 0.0) or 0.0
        nonzero = numeric_sum(row, ("applied_score_adjustment_nonzero_count", "auditor_adjustment_nonzero", "qwen_audit_adjustment_nonzero_count"))
        net = as_float(row.get("official_net"), -10**9) or -10**9
        gross = as_float(row.get("gross_minus_cost"), -10**9) or -10**9
        penalty = as_float(row.get("preference_penalty"), 10**9) or 10**9
        if net > off_net and penalty <= off_penalty + 1000 and gross >= off_gross - 2000 and valid_rate >= 0.90 and nonzero > 0:
            viable = True
    if not viable:
        verifier.fail("auditor numeric enabled but official A1/A2 ablation does not beat auditor OFF with required quality gates", path)


def graph_enabled(row: dict[str, str] | None) -> bool:
    if not row:
        return False
    identity = row_identity(row).lower()
    alpha = as_float(row_value(row, "graph_alpha", "opportunity_graph_alpha"), 0.0) or 0.0
    return "graph" in identity or alpha > 0


def check_graph_ablation(verifier: Verifier, b11: dict[str, str] | None) -> None:
    if not graph_enabled(b11):
        return
    path = REPORTS / "fuse_grid.csv"
    rows = read_csv(path)
    off = find_row(rows, {"G0", "G0_graph_off", "graph_off"})
    graph_rows = [
        find_row(rows, {"G1", "G1_graph_alpha_0.03", "graph_alpha_0.03"}),
        find_row(rows, {"G2", "G2_graph_alpha_0.05", "graph_alpha_0.05"}),
        find_row(rows, {"G3", "G3_graph_alpha_0.10", "graph_alpha_0.10"}),
    ]
    graph_rows = [row for row in graph_rows if row]
    if not off or not graph_rows:
        verifier.fail("graph enabled in B11 but G0/G1/G2/G3 ablation rows are missing", path)
        return
    off_net = as_float(off.get("official_net"), -10**9) or -10**9
    off_gross = as_float(off.get("gross_minus_cost"), -10**9) or -10**9
    off_penalty = as_float(off.get("preference_penalty"), 10**9) or 10**9
    viable = False
    for row in graph_rows:
        net = as_float(row.get("official_net"), -10**9) or -10**9
        gross = as_float(row.get("gross_minus_cost"), -10**9) or -10**9
        penalty = as_float(row.get("preference_penalty"), 10**9) or 10**9
        if net > off_net and gross > off_gross and penalty <= off_penalty + 1500:
            viable = True
    if not viable:
        verifier.fail("graph enabled in B11 but graph ablation lacks positive net/gross evidence without penalty explosion", path)


def check_0509(verifier: Verifier) -> None:
    path = REPORTS / "fuse_grid.csv"
    rows = read_csv(path)
    top5_rows = [
        row
        for row in rows
        if row_value(row, "dataset", default="20260529") == "20260509"
        and boolish(row_value(row, "top5_0509_sanity"))
    ]
    if len(top5_rows) < 5:
        verifier.fail(f"top5 20260509 sanity rows are {len(top5_rows)}, expected at least 5", path)
    for row in top5_rows:
        if status(row) not in EXECUTED_STATUS_VALUES or not has_score(row):
            verifier.fail(f"top5 0509 sanity row is not EXECUTED with score: {row_identity(row)}", path)
    package_candidates = [
        row
        for row in rows
        if row_value(row, "dataset", default="20260529") == "20260509"
        and (boolish(row_value(row, "package_candidate")) or boolish(row_value(row, "top5_0509_sanity")) or row_has_any_name(row, B11_NAMES))
    ]
    for row in package_candidates:
        invalid = numeric_sum(row, ("income_aborts", "income_abort_count", "abort_count"))
        if invalid > 0:
            verifier.fail(f"0509 package-candidate row has income abort: {row_identity(row)}", path)
    package_zips = list(PACKAGES.glob("CROWN_FUSE*.zip")) if PACKAGES.is_dir() else []
    if package_zips and not package_candidates:
        verifier.fail("package zip exists but no 20260509 package-candidate sanity row is recorded", path)


def final_score_gates(row: dict[str, str] | None) -> tuple[bool, bool]:
    if not row or not has_score(row):
        return False, False
    net = as_float(row.get("official_net"), -10**9) or -10**9
    gross = as_float(row.get("gross_minus_cost"), -10**9) or -10**9
    penalty = as_float(row.get("preference_penalty"), 10**9) or 10**9
    invalid = numeric_sum(row, INVALID_COLUMNS)
    recommended = net >= 30000 and penalty <= 28000 and gross >= 50000 and invalid == 0
    experimental = net >= 15000 and penalty <= 33000 and gross >= 40000 and invalid == 0
    return recommended, experimental


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_package(verifier: Verifier, zip_path: Path, audit_text: str, b11: dict[str, str] | None) -> None:
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = [name.replace("\\", "/") for name in zf.namelist()]
            if not names or any(not name.startswith("demo/") for name in names):
                verifier.fail(f"{zip_path.name} root is not exclusively demo/", zip_path)
            if not any(name.startswith("demo/agent/") for name in names):
                verifier.fail(f"{zip_path.name} missing demo/agent/", zip_path)
            if "demo/SUBMISSION.md" not in names:
                verifier.fail(f"{zip_path.name} missing demo/SUBMISSION.md", zip_path)
            forbidden = ("/server/", "/data/", "/reports/", "/runs/", "/archive/", "/docs/", "/prompts/", "/.git/")
            for name in names:
                probe = f"/{name}"
                lower = probe.lower()
                if any(token in lower for token in forbidden):
                    verifier.fail(f"{zip_path.name} contains forbidden path: {name}", zip_path)
                if lower.endswith((".pyc", ".pyo")) or "__pycache__" in lower or "/cache/" in lower or "key" in lower:
                    verifier.fail(f"{zip_path.name} contains forbidden cache/key/pyc path: {name}", zip_path)
            if "REVIEW_ONLY" in zip_path.name and "demo/SUBMISSION.md" in names:
                first_line = zf.read("demo/SUBMISSION.md").decode("utf-8", errors="replace").splitlines()[0].strip()
                if first_line != "NOT RECOMMENDED FOR B榜 SUBMISSION":
                    verifier.fail(f"{zip_path.name} review-only SUBMISSION.md first line is not the required warning", zip_path)
    except zipfile.BadZipFile:
        verifier.fail(f"{zip_path.name} is not a valid zip", zip_path)
        return
    digest = sha256_file(zip_path)
    size_text = str(zip_path.stat().st_size)
    if zip_path.name not in audit_text or digest not in audit_text or size_text not in audit_text:
        verifier.fail(f"fuse_package_audit.md does not record name/SHA256/size for {zip_path.name}", REPORTS / "fuse_package_audit.md")
    selected_identity = row_identity(b11).lower() if b11 else ""
    if b11 and "default" not in audit_text.lower():
        verifier.fail("fuse_package_audit.md does not report default variant", REPORTS / "fuse_package_audit.md")
    if b11 and selected_identity and row_value(b11, "variant", "variant_name", "variant_key") not in audit_text:
        verifier.warn("package audit does not literally include selected B11 variant token; verify default variant manually", REPORTS / "fuse_package_audit.md")


def check_packages(verifier: Verifier, b11: dict[str, str] | None) -> None:
    audit_path = REPORTS / "fuse_package_audit.md"
    audit_text = read_text(audit_path)
    package_zips = sorted(PACKAGES.glob("CROWN_FUSE*.zip")) if PACKAGES.is_dir() else []
    if package_zips and not audit_text:
        verifier.fail("package zip exists but fuse_package_audit.md is missing or empty", audit_path)
    recommended, experimental = final_score_gates(b11)
    review_only_count = 0
    recommended_count = 0
    experimental_count = 0
    for zip_path in package_zips:
        name = zip_path.name
        if "RECOMMENDED" in name and "NOT_RECOMMENDED" not in name and not recommended:
            verifier.fail(f"recommended package exists below recommended gates: {name}", zip_path)
        if "RECOMMENDED" in name and "NOT_RECOMMENDED" not in name:
            recommended_count += 1
        if "EXPERIMENTAL" in name and not experimental:
            verifier.fail(f"experimental package exists below experimental gates: {name}", zip_path)
        if "EXPERIMENTAL" in name:
            experimental_count += 1
        if "REVIEW_ONLY" in name:
            review_only_count += 1
        inspect_package(verifier, zip_path, audit_text, b11)
    if not package_zips:
        verifier.fail("no CROWN_FUSE package zip was generated", PACKAGES)
    if recommended and recommended_count < 1:
        verifier.fail("recommended score gates passed but no recommended package zip exists", PACKAGES)
    elif experimental and experimental_count < 1:
        verifier.fail("experimental score gates passed but no experimental package zip exists", PACKAGES)
    elif not recommended and not experimental and review_only_count != 1:
        verifier.fail(f"below submission gates requires exactly one review-only package, found {review_only_count}", PACKAGES)
    if review_only_count > 1:
        verifier.fail(f"more than one review-only package exists: {review_only_count}", PACKAGES)


def check_report_limit(verifier: Verifier) -> None:
    if not REPORTS.is_dir():
        verifier.fail("reports/ directory missing", REPORTS)
        return
    files = {path.name for path in REPORTS.iterdir() if path.is_file()}
    extras = files - FUSE_REPORTS
    if extras:
        verifier.fail(f"reports/ contains files outside Fuse final artifact set: {sorted(extras)}", REPORTS)
    if len(files) > 5:
        verifier.fail(f"reports/ contains {len(files)} files, expected at most 5", REPORTS)


def check_final_report(verifier: Verifier, b11: dict[str, str] | None) -> None:
    path = REPORTS / "fuse_final_report.md"
    text = read_text(path)
    if not text:
        verifier.fail("fuse_final_report.md is missing or empty", path)
        return
    first_line = text.splitlines()[0].strip() if text.splitlines() else ""
    if first_line not in VALID_STOP_STATES:
        verifier.fail(f"fuse_final_report.md first line is not an allowed Fuse stop state: {first_line!r}", path)
    recommended, experimental = final_score_gates(b11)
    if first_line == "FUSE_RECOMMENDED_SUBMISSION" and not recommended:
        verifier.fail("final report claims recommended submission below recommended gates", path)
    if first_line == "FUSE_EXPERIMENTAL_SUBMISSION" and not experimental:
        verifier.fail("final report claims experimental submission below experimental gates", path)
    if first_line == "FUSE_REVIEW_PACKAGES_ONLY" and (recommended or experimental):
        verifier.fail("final report claims review-only despite score gates passing", path)
    required_terms = [
        "git branch",
        "source_code_commit",
        "evidence_commit",
        "B10",
        "B11",
        "fuse grid",
        "package audit",
        "QA",
    ]
    for term in required_terms:
        if term.lower() not in text.lower():
            verifier.fail(f"fuse_final_report.md missing required report topic: {term}", path)


def check_final(verifier: Verifier) -> None:
    b0 = check_noop_isolation(verifier)
    executed, grid_b0 = check_search(verifier, require_final_ledger=True)
    if grid_b0:
        check_b0_gate(verifier, grid_b0, REPORTS / "fuse_grid.csv")
    if b0 is None:
        b0 = grid_b0
    b10, b11 = check_final_rows(verifier, executed, b0)
    check_auditor_ablation(verifier, b11)
    check_graph_ablation(verifier, b11)
    check_0509(verifier)
    check_report_limit(verifier)
    check_packages(verifier, b11)
    check_final_report(verifier, b11)


def print_findings(verifier: Verifier) -> None:
    if not verifier.findings:
        print(f"PASS phase={verifier.phase}")
        return
    for finding in verifier.findings:
        if finding.path:
            try:
                path_text = str(finding.path.relative_to(ROOT))
            except ValueError:
                path_text = str(finding.path)
            print(f"{finding.severity}: {finding.message} path={path_text}")
        else:
            print(f"{finding.severity}: {finding.message}")
    fail_count = sum(1 for finding in verifier.findings if finding.severity == "FAIL")
    warn_count = sum(1 for finding in verifier.findings if finding.severity == "WARN")
    if fail_count:
        print(f"FAIL phase={verifier.phase} failures={fail_count} warnings={warn_count}")
    else:
        print(f"PASS phase={verifier.phase} warnings={warn_count}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["isolation", "search", "final"], required=True)
    args = parser.parse_args(argv)
    verifier = Verifier(phase=args.phase)
    check_branch(verifier)
    check_required_file(verifier, ROOT / "tools" / "verify_fuse_completion.py")
    if args.phase == "isolation":
        check_noop_isolation(verifier)
    elif args.phase == "search":
        check_search(verifier)
    else:
        check_final(verifier)
    print_findings(verifier)
    return 1 if any(finding.severity == "FAIL" for finding in verifier.findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
