"""Build/audit Pref-Forge package only when evidence gates allow it."""

from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common

ZIP_NAMES = {
    "review-only": "CROWN_PREF_FORGE_REVIEW_ONLY_NOT_FOR_SUBMISSION.zip",
    "experimental": "CROWN_PREF_FORGE_EXPERIMENTAL_SUBMISSION.zip",
    "recommended": "CROWN_PREF_FORGE_RECOMMENDED_SUBMISSION.zip",
}


def _best_20260529() -> dict[str, str] | None:
    rows = [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"]
    return max(rows, key=lambda row: common.safe_float(row.get("official_net")), default=None)


def _label_for(best: dict[str, str] | None) -> str:
    if not best:
        return "none"
    net = common.safe_float(best.get("official_net"))
    gross = common.safe_float(best.get("gross_minus_cost"))
    penalty = common.safe_float(best.get("preference_penalty"))
    invalid = common.safe_int(best.get("invalid_count")) + common.safe_int(best.get("income_abort_count")) + common.safe_int(best.get("rejected_take_count"))
    weak = net > common.B0_NET + 3000 and penalty < common.B0_PENALTY - 6000 and invalid == 0
    if net >= 25000 and gross >= 50000 and penalty <= 26000 and invalid == 0:
        return "recommended"
    if net >= 15000 and gross >= 42000 and penalty <= 32000 and invalid == 0:
        return "experimental"
    if weak:
        return "review-only"
    return "none"


def _iter_package_files() -> list[Path]:
    files = [common.ROOT / "demo" / "SUBMISSION.md"]
    files.extend(sorted(path for path in (common.ROOT / "demo" / "agent").rglob("*") if path.is_file()))
    out = []
    for path in files:
        rel = path.relative_to(common.ROOT).as_posix().lower()
        if "__pycache__" in rel or rel.endswith((".pyc", ".pyo")):
            continue
        if "prompt" in rel or "key" in rel or ".private" in rel or "/cache/" in rel:
            continue
        out.append(path)
    return out


def _submission_line(label: str) -> str:
    if label == "recommended":
        return "RECOMMENDED FOR B榜 SUBMISSION"
    if label == "experimental":
        return "EXPERIMENTAL HIDDEN-SAFE SUBMISSION CANDIDATE"
    return "NOT RECOMMENDED FOR B榜 SUBMISSION"


def _audit_zip(path: Path, expected_label: str) -> tuple[list[str], list[str]]:
    findings = []
    with zipfile.ZipFile(path) as zf:
        names = [name.replace("\\", "/") for name in zf.namelist() if not name.endswith("/")]
        if any(not name.startswith("demo/") for name in names):
            findings.append("root_not_demo")
        if "demo/SUBMISSION.md" not in names:
            findings.append("missing_submission_md")
        if not any(name.startswith("demo/agent/") for name in names):
            findings.append("missing_demo_agent")
        forbidden_parts = {"/server/", "/data/", "/reports/", "/runs/", "/archive/", "/docs/", "/.private/", "/keys/"}
        for name in names:
            lower = f"/{name.lower()}"
            if any(part in lower for part in forbidden_parts) or lower.endswith((".pyc", ".pyo")) or "__pycache__" in lower:
                findings.append(f"forbidden_entry:{name}")
        if "demo/SUBMISSION.md" in names:
            first = zf.read("demo/SUBMISSION.md").decode("utf-8", errors="ignore").splitlines()[0].strip()
            if first != _submission_line(expected_label):
                findings.append("submission_label_mismatch")
    return findings, names


def _default_variant() -> str:
    os.environ.pop("CROWN_Y_VARIANT", None)
    sys.path.insert(0, str(common.ROOT / "demo"))
    from agent import config  # noqa: WPS433

    return str(config.RESCUE_VARIANT)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", choices=["auto", *ZIP_NAMES], default="auto")
    args = parser.parse_args()
    best = _best_20260529()
    label = _label_for(best) if args.label == "auto" else args.label
    common.PACKAGES.mkdir(parents=True, exist_ok=True)
    lines = ["# Pref-Forge Package Audit", ""]
    if label == "none":
        lines.extend(
            [
                "- package_label: `none`",
                "- package_path: ``",
                "- sha256: ``",
                "- size_bytes: 0",
                "- entry_count: 0",
                "- forbidden_entries: 0",
                "- package_audit_status: `PASS_NO_PACKAGE_WEAK_GATE_NOT_MET`",
            ]
        )
        common.PACKAGE_AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print({"label": label, "package": ""})
        return 0

    submission = common.ROOT / "demo" / "SUBMISSION.md"
    original = submission.read_text(encoding="utf-8", errors="ignore") if submission.is_file() else ""
    first = _submission_line(label)
    rest = "\n".join(original.splitlines()[1:]) if original else "Pref-Forge package generated from current runtime code."
    submission.write_text(first + "\n" + rest.strip() + "\n", encoding="utf-8")
    zip_path = common.PACKAGES / ZIP_NAMES[label]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in _iter_package_files():
            zf.write(path, path.relative_to(common.ROOT).as_posix())
    findings, names = _audit_zip(zip_path, label)
    digest = common.file_sha256(zip_path)
    size = zip_path.stat().st_size
    default_variant = _default_variant()
    lines.extend(
        [
            f"- package_label: `{label}`",
            f"- package_path: `{zip_path}`",
            f"- sha256: `{digest}`",
            f"- size_bytes: {size}",
            f"- entry_count: {len(names)}",
            "- root: `demo/`",
            f"- default_variant: `{default_variant}`",
            f"- forbidden_entries: {len(findings)}",
            f"- package_audit_status: `{'PASS' if not findings else 'FAIL'}`",
        ]
    )
    if findings:
        lines.append("")
        lines.append("## Findings")
        lines.extend(f"- {item}" for item in findings)
    common.PACKAGE_AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({"label": label, "package": str(zip_path), "sha256": digest, "findings": len(findings)})
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
