"""Audit Pref-Forge runtime/package boundary for forbidden reads/imports."""

from __future__ import annotations

import argparse
import ast
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common

FORBIDDEN_MARKERS = (
    "server/data",
    "cargo_dataset.jsonl",
    "drivers.json",
    "reports/",
    "runs/",
    "oracle",
    "scorer_output",
    "calc_monthly_income",
    "monthly_income",
    "rule_hash_specific",
    "driver_hash_specific",
    "preference_hash_specific",
)
FORBIDDEN_IMPORT_ROOTS = {"server", "bench"}


def _scan_python(path: Path, text: str) -> list[dict[str, str]]:
    findings = []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [{"path": str(path), "line": str(exc.lineno or 0), "kind": "syntax_error", "detail": str(exc)}]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                    findings.append({"path": str(path), "line": str(node.lineno), "kind": "forbidden_import", "detail": alias.name})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                findings.append({"path": str(path), "line": str(node.lineno), "kind": "forbidden_import", "detail": module})
    return findings


def _scan_text(path: Path, text: str) -> list[dict[str, str]]:
    normalized = text.replace("\\", "/")
    findings = []
    for marker in FORBIDDEN_MARKERS:
        idx = normalized.find(marker)
        if idx >= 0:
            findings.append({"path": str(path), "line": str(normalized.count("\n", 0, idx) + 1), "kind": "forbidden_marker", "detail": marker})
    return findings


def _iter_runtime_files() -> list[Path]:
    base = common.ROOT / "demo" / "agent"
    return sorted(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)


def _scan_packages() -> list[dict[str, str]]:
    findings = []
    for package in common.PACKAGES.glob("*.zip"):
        try:
            with zipfile.ZipFile(package) as zf:
                for name in zf.namelist():
                    if name.endswith("/"):
                        continue
                    lower = name.lower()
                    if any(part in lower for part in ("/server/", "/data/", "/reports/", "/runs/", "/archive/", "/docs/", ".private")):
                        findings.append({"path": f"{package.name}:{name}", "line": "0", "kind": "forbidden_package_entry", "detail": name})
                    if name.endswith(".py"):
                        text = zf.read(name).decode("utf-8", errors="ignore")
                        findings.extend(_scan_text(Path(package.name) / name, text))
                        findings.extend(_scan_python(Path(package.name) / name, text))
        except zipfile.BadZipFile:
            findings.append({"path": str(package), "line": "0", "kind": "bad_zip", "detail": ""})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-any", action="store_true")
    args = parser.parse_args()
    findings = []
    for path in _iter_runtime_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        findings.extend(_scan_text(path.relative_to(common.ROOT), text))
        findings.extend(_scan_python(path.relative_to(common.ROOT), text))
    findings.extend(_scan_packages())
    report = common.RUNS / "runtime_leakage_audit.md"
    lines = ["# Pref-Forge Runtime Leakage Audit", "", f"- findings: {len(findings)}", f"- status: {'PASS' if not findings else 'FAIL'}", "", "| path | line | kind | detail |", "|---|---:|---|---|"]
    lines.extend(f"| {item['path']} | {item['line']} | {item['kind']} | {item['detail']} |" for item in findings)
    if not findings:
        lines.append("| - | - | none | - |")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({"findings": len(findings), "report": str(report)})
    return 1 if args.fail_on_any and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
