"""Compliance scanner for the CROWN-Y agent boundary."""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "compliance_audit.md"
AGENT_DIR = ROOT / "demo" / "agent"

RAW_DATA_MARKERS = ("cargo_dataset.jsonl", "drivers.json")
BLOCKED_IMPORT_PREFIXES = ("server", "bench", "calc_monthly_income")
BLOCKED_STATE_IMPORTS = ("simkit.cargo_repository", "simkit.driver_state_manager")
ID_PATTERN = re.compile(r"(['\"])(D\\d{3}|C\\d{3,}|cargo_[^'\"]+)\\1")
COORD_TABLE_PATTERN = re.compile(r"\[(?:\s*[-+]?\d{1,3}\.\d{3,}\s*,\s*[-+]?\d{1,3}\.\d{3,}\s*,?){3,}\s*\]")
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


def iter_scanned_files() -> list[Path]:
    files: list[Path] = []
    for base in (AGENT_DIR, ROOT / "tests"):
        if not base.exists():
            continue
        files.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    for name in ("AGENTS.md", "agent.md", "README_CROWN_Y.md"):
        path = ROOT / name
        if path.is_file():
            files.append(path)
    return sorted(files)


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
    return findings


def run_scan() -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_scanned_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        findings.extend(scan_text(path, text))
        findings.extend(scan_imports(path, text))
    findings.extend(check_config())
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
        rel = item.path.relative_to(ROOT)
        lines.append(f"| {item.severity} | {rel} | {item.line} | {item.code} | {item.detail} |")
    if not findings:
        lines.append("| note | - | - | none | no findings |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-p0", action="store_true")
    args = parser.parse_args()
    findings = run_scan()
    write_report(findings)
    p0 = [f for f in findings if f.severity == "P0"]
    print(f"compliance findings={len(findings)} p0={len(p0)} report={REPORT}")
    return 1 if args.fail_on_p0 and p0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
