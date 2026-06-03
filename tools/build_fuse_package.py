"""Build and audit the CROWN-FUSE review/submission package."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "demo" / "agent"
SUBMISSION = ROOT / "demo" / "SUBMISSION.md"
PACKAGES = ROOT / "runs" / "packages"
AUDIT_PATH = ROOT / "reports" / "fuse_package_audit.md"

ZIP_NAMES = {
    "recommended": "CROWN_FUSE_RECOMMENDED_SUBMISSION.zip",
    "experimental": "CROWN_FUSE_EXPERIMENTAL_SUBMISSION.zip",
    "review-only": "CROWN_FUSE_REVIEW_ONLY_NOT_FOR_SUBMISSION.zip",
}


def default_variant() -> str:
    os.environ.pop("CROWN_Y_VARIANT", None)
    sys.path.insert(0, str(ROOT / "demo"))
    from agent import config  # noqa: WPS433

    return str(config.RESCUE_VARIANT)


def iter_package_files() -> list[Path]:
    files = [SUBMISSION]
    files.extend(sorted(path for path in AGENT_DIR.rglob("*") if path.is_file()))
    allowed: list[Path] = []
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        lower = rel.lower()
        if "__pycache__" in lower or lower.endswith((".pyc", ".pyo")):
            continue
        if any(part in path.name for part in (".env", "local_config.py")):
            continue
        if "prompt" in lower or "key" in lower or "/cache/" in lower:
            continue
        allowed.append(path)
    return allowed


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_zip(zip_path: Path, expected_default: str) -> tuple[list[str], list[str]]:
    findings: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        names = [name.replace("\\", "/") for name in zf.namelist()]
        if not names or any(not name.startswith("demo/") for name in names):
            findings.append("root is not exclusively demo/")
        if not any(name.startswith("demo/agent/") for name in names):
            findings.append("missing demo/agent/")
        if "demo/SUBMISSION.md" not in names:
            findings.append("missing demo/SUBMISSION.md")
        forbidden_tokens = ("/server/", "/data/", "/reports/", "/runs/", "/archive/", "/docs/", "/prompts/", "/.git/")
        for name in names:
            lower = f"/{name}".lower()
            if any(token in lower for token in forbidden_tokens):
                findings.append(f"forbidden path: {name}")
            if lower.endswith((".pyc", ".pyo")) or "__pycache__" in lower or "/cache/" in lower or "key" in lower:
                findings.append(f"forbidden cache/key/pyc path: {name}")
        if "REVIEW_ONLY" in zip_path.name and "demo/SUBMISSION.md" in names:
            first_line = zf.read("demo/SUBMISSION.md").decode("utf-8", errors="replace").splitlines()[0].strip()
            if first_line != "NOT RECOMMENDED FOR B榜 SUBMISSION":
                findings.append("review-only SUBMISSION.md first line mismatch")
    actual_default = default_variant()
    if expected_default and actual_default != expected_default:
        findings.append(f"default variant {actual_default!r} != expected {expected_default!r}")
    return findings, names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", choices=sorted(ZIP_NAMES), required=True)
    parser.add_argument("--expected-default", default="")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    out = args.out or (PACKAGES / ZIP_NAMES[args.label])
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in iter_package_files():
            zf.write(path, path.relative_to(ROOT).as_posix())

    findings, names = audit_zip(out, args.expected_default)
    digest = sha256_file(out)
    size = out.stat().st_size
    actual_default = default_variant()
    lines = [
        "# Fuse Package Audit",
        "",
        f"- package_label: `{args.label}`",
        f"- zip_name: `{out.name}`",
        f"- zip_path: `{out}`",
        f"- sha256: `{digest}`",
        f"- size_bytes: {size}",
        f"- entry_count: {len(names)}",
        f"- root: `demo/`",
        f"- contains_demo_agent: {str(any(name.startswith('demo/agent/') for name in names)).lower()}",
        f"- contains_submission_md: {str('demo/SUBMISSION.md' in names).lower()}",
        f"- default variant: `{actual_default}`",
        f"- expected_default_variant: `{args.expected_default}`",
        f"- forbidden_entries: {len(findings)}",
    ]
    if findings:
        lines.append("")
        lines.append("## Findings")
        lines.extend(f"- {finding}" for finding in findings)
    else:
        lines.append("- package_audit_status: `PASS`")
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
