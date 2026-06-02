"""Compliance scanner for the CROWN-TRIDENT agent boundary."""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "runs" / "trident_compliance_audit.md"
AGENT_DIR = ROOT / "demo" / "agent"

RAW_DATA_MARKERS = ("cargo_dataset.jsonl", "drivers.json")
BLOCKED_IMPORT_PREFIXES = ("server", "bench", "calc_monthly_income", "monthly_income")
BLOCKED_STATE_IMPORTS = ("simkit.cargo_repository", "simkit.driver_state_manager")
ID_PATTERN = re.compile(r"(['\"])(D\\d{3}|C\\d{3,}|cargo_[^'\"]+)\\1")
COORD_TABLE_PATTERN = re.compile(r"\[(?:\s*[-+]?\d{1,3}\.\d{3,}\s*,\s*[-+]?\d{1,3}\.\d{3,}\s*,?){3,}\s*\]")
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
ORACLE_ARTIFACT_MARKERS = (
    "reports/oracle_gap.csv",
    "reports/predicate_eval.csv",
    "reports/pce_experiments.csv",
    "reports/action_forensics.csv",
    "tools/offline_",
    "tools/exact_marginal_penalty_dataset.py",
    "tools/money_trajectory_repair.py",
    "full_info_trajectory",
    "money_repair_trajectory",
    "cargo_dataset",
    "driver_dataset",
    "drivers.json",
    "oracle_artifact",
    "exact_label",
    "action_trace",
    "scorer_output",
    "server/data",
    "benchmark_internal",
    "calc_monthly_income",
    "monthly_income",
)
LEGACY_REPORTS = (
    "pce_final_report.md",
    "pce_experiments.csv",
    "oracle_gap.csv",
    "predicate_eval.csv",
    "action_forensics.csv",
    "gold_final_report.md",
    "gold_experiments.csv",
    "gold_qwen_contract_audit.csv",
    "gold_decision_forensics.csv",
    "gold_package_audit.md",
)
ALLOWED_TRIDENT_REPORTS = {
    "trident_final_report.md",
    "trident_experiments.csv",
    "trident_rule_ledger.csv",
    "trident_decision_deltas.csv",
    "trident_qwen_effect.csv",
}
REQUIRED_TRIDENT_REPORTS = set(ALLOWED_TRIDENT_REPORTS)
SUBMISSION_STOP_STATES = {
    "CROWN_TRIDENT_RECOMMENDED_SUBMISSION",
    "CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION",
}
DISALLOWED_PACKAGE_DEFAULT_VARIANTS = {
    "best_rescue",
    "preference_firewall_profit",
    "pce_final",
    "pce_repair_first",
    "delta_mpc",
    "delta_mpc_delta_only",
    "delta_mpc_macro",
    "delta_mpc_fallback",
    "crown_exact_rbt_mpc",
    "crown_gold_contract_mpc",
}
PACKAGE_FORBIDDEN_PARTS = {
    "server",
    "data",
    "results",
    "reports",
    "runs",
    "archive",
    "docs",
    "keys",
    "__pycache__",
}
PACKAGE_FORBIDDEN_NAME_SUBSTRINGS = ("prompt", ".env", "secret", "key")
RAW_ID_PATTERN = re.compile(r"\b(?:D\d{3}|C\d{3,}|cargo_[0-9A-Fa-f]{6,}|cargo-[A-Za-z0-9_-]+)\b")
RAW_COORD_PATTERN = re.compile(r"(?<![\w.-])-?\d{1,2}\.\d{4,}\s*,\s*-?\d{2,3}\.\d{4,}(?![\w.-])")
CONFIG_DEFAULT_VARIANT_PATTERN = re.compile(r"CROWN_Y_VARIANT\"\s*,\s*\"([^\"]+)\"")
FORBIDDEN_TERM_HASHES = {
    "5974c91c514b3c069594619015dc3a63d26e0eaeea21e4a6e572fc9bf599157b",
    "710e6b10f5d6fc3558261af1d831346a17727f2de4c8dbff923117e08fad7676",
    "2b0d4debd40aaa6db83c0e8407a41ac3fc930d584e589a717c8a73bcd4004511",
    "bfa2d34b46c1a8c21d97af27052965c63c50355f9c98eae36d285ebe446f502a",
    "d2d3a3cc12aa2c3b93c07e1affea267345f24f8e05d4492bead57978e79c041d",
    "2e4360e3a4d0d8caf92b0362ba1b373f1d46767d1773c7d522290adb758fbf3f",
}


@dataclass
class Finding:
    severity: str
    path: Path
    line: int
    code: str
    detail: str


def iter_runtime_files() -> list[Path]:
    if not AGENT_DIR.exists():
        return []
    return sorted(p for p in AGENT_DIR.rglob("*.py") if "__pycache__" not in p.parts)


def iter_scanned_files() -> list[Path]:
    files: list[Path] = []
    for base in (AGENT_DIR, ROOT / "tests"):
        if not base.exists():
            continue
        files.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    for name in ("AGENTS.md", "agent.md", "README_CROWN_Y.md", "crown_trident_gold2_codex_prompt.md"):
        path = ROOT / name
        if path.is_file():
            files.append(path)
    work_dir = ROOT / "docs" / "AGENT_WORK"
    if work_dir.exists():
        files.extend(p for p in work_dir.rglob("*.md") if "__pycache__" not in p.parts)
    audit_guard = ROOT / "tools" / "audit_guard.py"
    if audit_guard.is_file():
        files.append(audit_guard)
    return sorted(files)


def iter_legacy_report_files() -> list[Path]:
    reports = ROOT / "reports"
    if not reports.exists():
        return []
    return sorted(path for name in LEGACY_REPORTS if (path := reports / name).is_file())


def iter_report_files() -> list[Path]:
    reports = ROOT / "reports"
    if not reports.exists():
        return []
    return sorted(path for path in reports.iterdir() if path.is_file())


def iter_submission_zips() -> list[Path]:
    out: list[Path] = []
    for path in ROOT.rglob("*.zip"):
        if ".git" in path.parts:
            continue
        if path.name.startswith("demo_docs_release_"):
            continue
        if "archive" in path.relative_to(ROOT).parts:
            continue
        out.append(path)
    return sorted(out)


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _contains_forbidden_term(text: str) -> tuple[bool, int]:
    compact = "".join(ch for ch in text if not ch.isspace())
    for width in range(2, 6):
        if len(compact) < width:
            continue
        for idx in range(0, len(compact) - width + 1):
            digest = hashlib.sha256(compact[idx : idx + width].encode("utf-8")).hexdigest()
            if digest in FORBIDDEN_TERM_HASHES:
                needle = compact[idx : idx + width]
                return True, _line_for_offset(text, text.find(needle))
    return False, 0


def scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    if path != ROOT / "tools" / "audit_guard.py":
        for marker in RAW_DATA_MARKERS:
            idx = text.find(marker)
            if idx >= 0:
                findings.append(Finding("P0", path, _line_for_offset(text, idx), "raw_data_marker", marker))
    hit, line = _contains_forbidden_term(text)
    if hit:
        findings.append(Finding("P0", path, line, "forbidden_preference_term", "hashed preference term present"))
    if ID_PATTERN.search(text):
        match = ID_PATTERN.search(text)
        findings.append(Finding("P1", path, _line_for_offset(text, match.start()), "hardcoded_id_pattern", match.group(2)))
    if COORD_TABLE_PATTERN.search(text):
        match = COORD_TABLE_PATTERN.search(text)
        findings.append(Finding("P1", path, _line_for_offset(text, match.start()), "coordinate_table_risk", "large coordinate literal table"))
    return findings


def scan_runtime_literals(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        path.relative_to(AGENT_DIR)
    except ValueError:
        return findings
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [Finding("P0", path, exc.lineno or 0, "syntax_error", str(exc))]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        value = node.value
        if value in {"PROTECTED_LITERAL_REDACTED", "runtime_entity_hash", "runtime_value_hash"}:
            continue
        if RAW_ID_PATTERN.search(value):
            findings.append(
                Finding("P0", path, node.lineno, "runtime_hardcoded_id", "raw driver/cargo id literal in runtime")
            )
        if RAW_COORD_PATTERN.search(value):
            findings.append(
                Finding("P0", path, node.lineno, "runtime_hardcoded_coordinate", "fixed coordinate literal in runtime")
            )
        if CJK_PATTERN.search(value):
            findings.append(
                Finding(
                    "P2",
                    path,
                    node.lineno,
                    "runtime_cjk_literal_review",
                    "manual review needed; protected literal hash scan remains the P0 gate",
                )
            )
    return findings


def scan_runtime_oracle_boundary(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        path.relative_to(AGENT_DIR)
    except ValueError:
        return findings
    normalized = text.replace("\\", "/")
    for marker in ORACLE_ARTIFACT_MARKERS:
        idx = normalized.find(marker)
        if idx >= 0:
            findings.append(
                Finding(
                    "P0",
                    path,
                    _line_for_offset(normalized, idx),
                    "runtime_oracle_artifact_reference",
                    marker,
                )
            )
    return findings


def scan_legacy_report_redaction(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    if path.name not in LEGACY_REPORTS:
        return findings
    for match in RAW_ID_PATTERN.finditer(text):
        findings.append(
            Finding(
                "P0",
                path,
                _line_for_offset(text, match.start()),
                "pce_report_raw_id",
                "raw id redaction required",
            )
        )
    for match in RAW_COORD_PATTERN.finditer(text):
        findings.append(
            Finding(
                "P0",
                path,
                _line_for_offset(text, match.start()),
                "pce_report_raw_coordinate",
                "raw coordinate redaction required",
            )
        )
    return findings


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        base = _attr_base_name(func.value)
        return f"{base}.{func.attr}" if base else func.attr
    return ""


def _attr_base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _attr_base_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _stmt_has_call(stmt: ast.stmt, needles: tuple[str, ...]) -> bool:
    for node in ast.walk(stmt):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if any(name == needle or name.endswith(f".{needle}") for needle in needles):
                return True
    return False


def _stmt_has_query(stmt: ast.stmt) -> bool:
    return _stmt_has_call(stmt, ("_query_here", "query_cargo"))


def _stmt_has_refresh(stmt: ast.stmt) -> bool:
    return _stmt_has_call(stmt, ("refresh_world",))


def _stmt_has_action_consumer(stmt: ast.stmt) -> bool:
    return _stmt_has_call(
        stmt,
        (
            "normalize_and_filter",
            "fast_normalize_and_filter",
            "build_options",
            "pre_filter_and_attach_action_certificate",
            "finalize",
            "choose",
            "choose_best_with_certificates",
        ),
    )


def _scan_query_block(path: Path, func_name: str, block: list[ast.stmt]) -> list[Finding]:
    findings: list[Finding] = []
    for idx, stmt in enumerate(block):
        nested_blocks: list[list[ast.stmt]] = []
        if isinstance(stmt, ast.If):
            nested_blocks.extend([stmt.body, stmt.orelse])
        elif isinstance(stmt, (ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith)):
            nested_blocks.append(stmt.body)
        elif isinstance(stmt, ast.Try):
            nested_blocks.extend([stmt.body, stmt.orelse, stmt.finalbody])
            nested_blocks.extend(handler.body for handler in stmt.handlers)
        if nested_blocks:
            for nested in nested_blocks:
                findings.extend(_scan_query_block(path, func_name, nested))
            continue

        if not _stmt_has_query(stmt):
            continue
        if func_name == "_query_here" and _stmt_has_call(stmt, ("query_cargo",)):
            continue
        refreshed = False
        for next_stmt in block[idx + 1 :]:
            if _stmt_has_refresh(next_stmt):
                refreshed = True
                break
            if _stmt_has_action_consumer(next_stmt) or isinstance(next_stmt, ast.Return):
                break
        if not refreshed:
            findings.append(
                Finding(
                    "P0",
                    path,
                    getattr(stmt, "lineno", 0),
                    "query_without_refresh_barrier",
                    "query_cargo/_query_here must be followed by refresh_world before filtering/scoring/action",
                )
            )
    return findings


def scan_query_refresh_order(path: Path, text: str) -> list[Finding]:
    if path != AGENT_DIR / "model_decision_service.py":
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [Finding("P0", path, exc.lineno or 0, "syntax_error", str(exc))]
    findings: list[Finding] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    findings.extend(_scan_query_block(path, item.name, item.body))
        elif isinstance(node, ast.FunctionDef):
            findings.extend(_scan_query_block(path, node.name, node.body))
    return findings


def scan_action_contracts() -> list[Finding]:
    findings: list[Finding] = []
    safety = AGENT_DIR / "safety.py"
    service = AGENT_DIR / "model_decision_service.py"
    cargo_filter = AGENT_DIR / "cargo_filter.py"
    safety_text = safety.read_text(encoding="utf-8")
    service_text = service.read_text(encoding="utf-8")
    filter_text = cargo_filter.read_text(encoding="utf-8")
    required_safety_patterns = {
        "certificate_source_scope": "cargo.source_scope != CURRENT_ACTIONABLE",
        "certificate_current_observed_set": "cargo.cargo_id not in observed_ids",
        "certificate_decision_id": "cargo.decision_id != option.decision_id",
        "finalize_take_safe_cert": "option.action_cert and option.action_cert.safe",
        "finalize_reposition_full_precision_lat": '"latitude": float(option.target_lat)',
        "finalize_reposition_full_precision_lng": '"longitude": float(option.target_lng)',
    }
    for code, needle in required_safety_patterns.items():
        if needle not in safety_text:
            findings.append(Finding("P0", safety, 0, code, f"missing required safety pattern: {needle}"))
    if re.search(r"round\s*\(\s*option\.target_(?:lat|lng)", safety_text):
        findings.append(
            Finding("P0", safety, 0, "rounded_reposition_action_coordinate", "final action coordinates must not be rounded")
        )
    if "observed_ids = {cargo.cargo_id for cargo in visible}" not in service_text:
        findings.append(
            Finding("P0", service, 0, "missing_observed_id_gate", "take_order gate must use current post-query visible cargo ids")
        )
    if "pre_filter_and_attach_action_certificate(options, world_after_query, observed_ids)" not in service_text:
        findings.append(
            Finding("P0", service, 0, "missing_post_query_action_certificate", "options must be certified after query refresh/filter")
        )
    if 'if plan.kind == "no_query":' not in service_text or "return observed, world_current, 0" not in service_text:
        findings.append(
            Finding("P0", service, 0, "no_query_may_use_remembered_cargo", "no_query must return an empty current observation set")
        )
    if "source_scope != CURRENT_ACTIONABLE" not in filter_text:
        findings.append(
            Finding("P0", cargo_filter, 0, "missing_current_actionable_filter", "filter must reject non-current-actionable cargo")
        )
    return findings


def scan_imports(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    if path.suffix != ".py":
        return findings
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [Finding("P0", path, exc.lineno or 0, "syntax_error", str(exc))]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.split(".")[0] in BLOCKED_IMPORT_PREFIXES or name in BLOCKED_STATE_IMPORTS:
                    findings.append(Finding("P0", path, node.lineno, "blocked_import", name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] in BLOCKED_IMPORT_PREFIXES or module in BLOCKED_STATE_IMPORTS:
                findings.append(Finding("P0", path, node.lineno, "blocked_import", module))
    return findings


def check_config() -> list[Finding]:
    path = AGENT_DIR / "config.py"
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    required_false = {
        "OFFICIAL_ALLOW_ARBITRARY_COORD_QUERY": False,
        "ENABLE_DESTINATION_SHADOW_QUERY": False,
        "ENABLE_THREE_HOP": False,
        "ENABLE_OPTION_ROLLOUT": False,
    }
    namespace: dict[str, object] = {}
    exec(compile(text, str(path), "exec"), namespace)
    for key, expected in required_false.items():
        if namespace.get(key) is not expected:
            findings.append(Finding("P0", path, 0, "bad_switch", f"{key} must be {expected}"))
    if int(namespace.get("SIMULATION_DURATION_DAYS", 0)) != 31:
        findings.append(Finding("P0", path, 0, "bad_horizon", "SIMULATION_DURATION_DAYS must be 31"))
    if float(namespace.get("LLM_TIMEOUT_SECONDS", 0.0)) != 120.0:
        findings.append(Finding("P0", path, 0, "bad_qwen_timeout", "LLM_TIMEOUT_SECONDS must be 120"))
    if int(namespace.get("LLM_MAX_COMPILE_CALLS_PER_DRIVER", 0)) <= 0:
        findings.append(Finding("P0", path, 0, "bad_qwen_compile_budget", "compile budget must be positive"))
    if int(namespace.get("LLM_MAX_LINKER_CALLS_TOTAL", 0)) <= 0:
        findings.append(Finding("P0", path, 0, "bad_qwen_link_budget", "link budget must be positive"))
    if int(namespace.get("PTT_MAX_AUDITOR_CALLS_TOTAL", 0)) <= 0:
        findings.append(Finding("P0", path, 0, "bad_qwen_auditor_budget", "auditor budget must be positive"))
    if namespace.get("DISABLE_RUNTIME_QWEN") is True:
        findings.append(Finding("P0", path, 0, "runtime_qwen_disabled", "CROWN_Y_DISABLE_RUNTIME_QWEN=1 is not allowed"))
    match = CONFIG_DEFAULT_VARIANT_PATTERN.search(text)
    if match and match.group(1) in DISALLOWED_PACKAGE_DEFAULT_VARIANTS:
        findings.append(
            Finding(
                "P2",
                path,
                _line_for_offset(text, match.start(1)),
                "default_variant_pending_trident_selection",
                f"default CROWN_Y_VARIANT is historical variant {match.group(1)!r}; package gate will fail until final Trident default is selected",
            )
        )
    return findings


def check_final_reports(*, require_final_evidence: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    report_files = iter_report_files()
    report_names = {path.name for path in report_files}
    for path in report_files:
        if path.name not in ALLOWED_TRIDENT_REPORTS:
            findings.append(
                Finding(
                    "P0",
                    path,
                    0,
                    "forbidden_report_file",
                    "Trident final reports may contain only the five trident_* artifacts",
                )
            )
    if require_final_evidence:
        for name in sorted(REQUIRED_TRIDENT_REPORTS - report_names):
            findings.append(Finding("P0", ROOT / "reports" / name, 0, "missing_final_report", "required Trident report missing"))

    final_report = ROOT / "reports" / "trident_final_report.md"
    if not final_report.is_file():
        return findings
    text = final_report.read_text(encoding="utf-8", errors="ignore")
    first_line = text.splitlines()[0].strip() if text.splitlines() else ""
    stop_state = _extract_stop_state(text)
    net = _extract_numeric_metric(text, "official_net")
    if net is not None and net < 30000 and not first_line.startswith("DO NOT SUBMIT:"):
        findings.append(
            Finding(
                "P0",
                final_report,
                1,
                "missing_do_not_submit_prefix",
                "official_net below experimental gate requires DO NOT SUBMIT first line",
            )
        )
    if stop_state in SUBMISSION_STOP_STATES and require_final_evidence:
        missing = REQUIRED_TRIDENT_REPORTS - report_names
        if missing:
            findings.append(
                Finding("P0", final_report, 0, "submission_state_missing_reports", ",".join(sorted(missing)))
            )
    return findings


def _extract_stop_state(text: str) -> str:
    for line in text.splitlines()[:80]:
        if "CROWN_TRIDENT_" in line or "DO_NOT_SUBMIT" in line or "EXTERNAL_BLOCKER" in line:
            for token in re.split(r"[^A-Z0-9_]+", line):
                if token in SUBMISSION_STOP_STATES or token.startswith("DO_NOT_SUBMIT") or token.startswith("EXTERNAL_BLOCKER"):
                    return token
    return ""


def _extract_numeric_metric(text: str, metric: str) -> float | None:
    match = re.search(rf"\b{re.escape(metric)}\b\s*[:=]\s*(-?\d+(?:\.\d+)?)", text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def check_submission_packages(*, require_final_evidence: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    packages = iter_submission_zips()
    final_report = ROOT / "reports" / "trident_final_report.md"
    final_text = final_report.read_text(encoding="utf-8", errors="ignore") if final_report.is_file() else ""
    first_line = final_text.splitlines()[0].strip() if final_text.splitlines() else ""
    stop_state = _extract_stop_state(final_text)
    if require_final_evidence and stop_state in SUBMISSION_STOP_STATES and not packages:
        findings.append(
            Finding("P0", ROOT, 0, "submission_state_without_package", "submission stop state requires inspected package")
        )
    for package in packages:
        findings.extend(_check_one_package(package, first_line=first_line, stop_state=stop_state))
    return findings


def _check_one_package(package: Path, *, first_line: str, stop_state: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        with zipfile.ZipFile(package) as zf:
            names = [name for name in zf.namelist() if name and not name.endswith("/")]
            if not _looks_like_submission_package(names):
                return []
            if first_line.startswith("DO NOT SUBMIT:"):
                findings.append(
                    Finding("P0", package, 0, "package_created_for_do_not_submit", "DO NOT SUBMIT state must not ship a submission zip")
                )
            if stop_state and stop_state not in SUBMISSION_STOP_STATES:
                findings.append(
                    Finding("P0", package, 0, "package_created_for_non_submission_state", stop_state)
                )
            if any(not name.startswith("demo/") for name in names):
                findings.append(Finding("P0", package, 0, "bad_package_root", "all zip entries must be rooted under demo/"))
            if not any(name.startswith("demo/agent/") for name in names):
                findings.append(Finding("P0", package, 0, "missing_demo_agent", "package must include demo/agent/"))
            if "demo/SUBMISSION.md" not in names:
                findings.append(Finding("P0", package, 0, "missing_submission_md", "package must include demo/SUBMISSION.md"))
            for name in names:
                lowered = name.lower()
                parts = set(part.lower() for part in Path(name).parts)
                if parts & PACKAGE_FORBIDDEN_PARTS:
                    findings.append(Finding("P0", package, 0, "forbidden_package_path", name))
                if lowered.endswith((".pyc", ".pyo")) or any(part in lowered for part in PACKAGE_FORBIDDEN_NAME_SUBSTRINGS):
                    findings.append(Finding("P0", package, 0, "forbidden_package_file", name))
            if "demo/agent/config.py" in names:
                config_text = zf.read("demo/agent/config.py").decode("utf-8", errors="ignore")
                match = CONFIG_DEFAULT_VARIANT_PATTERN.search(config_text)
                if match and match.group(1) in DISALLOWED_PACKAGE_DEFAULT_VARIANTS:
                    findings.append(
                        Finding(
                            "P0",
                            package,
                            0,
                            "package_default_variant_not_trident_final",
                            f"default variant is {match.group(1)!r}",
                        )
                    )
            else:
                findings.append(Finding("P0", package, 0, "package_missing_config", "cannot inspect default runtime variant"))
    except zipfile.BadZipFile:
        findings.append(Finding("P0", package, 0, "bad_zip", "cannot read package zip"))
    return findings


def _looks_like_submission_package(names: list[str]) -> bool:
    return any(name.startswith("demo/agent/") for name in names) or "demo/SUBMISSION.md" in names


def run_scan(*, require_final_evidence: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_scanned_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        findings.extend(scan_text(path, text))
        findings.extend(scan_imports(path, text))
        findings.extend(scan_runtime_literals(path, text))
        findings.extend(scan_runtime_oracle_boundary(path, text))
        findings.extend(scan_query_refresh_order(path, text))
    for path in iter_legacy_report_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        findings.extend(scan_text(path, text))
        findings.extend(scan_legacy_report_redaction(path, text))
    findings.extend(scan_action_contracts())
    findings.extend(check_config())
    findings.extend(check_final_reports(require_final_evidence=require_final_evidence))
    findings.extend(check_submission_packages(require_final_evidence=require_final_evidence))
    return findings


def write_report(findings: list[Finding]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    p0 = [f for f in findings if f.severity == "P0"]
    lines = [
        "# Compliance Audit",
        "",
        f"- scanned_files: {len(iter_scanned_files())}",
        f"- findings_total: {len(findings)}",
        f"- p0_findings: {len(p0)}",
        f"- status: {'PASS' if not p0 else 'FAIL'}",
        "",
        "| severity | file | line | code | detail |",
        "|---|---:|---:|---|---|",
    ]
    for item in findings:
        try:
            rel = item.path.relative_to(ROOT)
        except ValueError:
            rel = item.path
        lines.append(
            f"| {_escape_md(item.severity)} | {_escape_md(str(rel))} | {item.line} | {_escape_md(item.code)} | {_escape_md(item.detail)} |"
        )
    if not findings:
        lines.append("| note | - | - | none | no findings |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _escape_md(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-p0", action="store_true")
    parser.add_argument(
        "--require-final-evidence",
        action="store_true",
        help="treat missing final reports/package evidence as P0 instead of mid-run diagnostics",
    )
    args = parser.parse_args()
    findings = run_scan(require_final_evidence=args.require_final_evidence)
    write_report(findings)
    p0 = [f for f in findings if f.severity == "P0"]
    print(f"compliance findings={len(findings)} p0={len(p0)} report={REPORT}")
    return 1 if args.fail_on_p0 and p0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
