"""Build a restricted official-style submission ZIP for the CROWN-EXACT runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "demo" / "agent"
SUBMISSION = ROOT / "demo" / "SUBMISSION.md"
AUDIT_PATH = ROOT / "runs" / "packages" / "exact_package_audit.json"


def _default_variant() -> str:
    os.environ.pop("CROWN_Y_VARIANT", None)
    sys.path.insert(0, str(ROOT / "demo"))
    from agent import config  # noqa: WPS433

    return str(config.RESCUE_VARIANT)


def _iter_files() -> list[Path]:
    files = [SUBMISSION]
    files.extend(
        path
        for path in sorted(AGENT_DIR.rglob("*"))
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
        and path.name not in {".env", "local_config.py"}
    )
    return files


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recommended", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    default_name = (
        "crown_exact_rbt_mpc_submission.zip"
        if args.recommended
        else "crown_exact_NOT_RECOMMENDED_DO_NOT_SUBMIT.zip"
    )
    out = args.out or (ROOT / "runs" / "packages" / default_name)
    out.parent.mkdir(parents=True, exist_ok=True)
    files = _iter_files()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, path.relative_to(ROOT).as_posix())
    names = zipfile.ZipFile(out).namelist()
    disallowed = [
        name
        for name in names
        if not name.startswith("demo/")
        or name.startswith(("demo/server/", "reports/", "runs/", "archive/", "docs/"))
        or "__pycache__" in name
        or name.endswith((".pyc", ".pyo"))
        or "prompt" in name.lower()
        or "key" in name.lower()
    ]
    audit = {
        "zip_path": str(out),
        "recommended": bool(args.recommended),
        "sha256": _sha256(out),
        "size_bytes": out.stat().st_size,
        "entry_count": len(names),
        "contains_demo_agent": any(name.startswith("demo/agent/") for name in names),
        "contains_submission_md": "demo/SUBMISSION.md" in names,
        "default_variant": _default_variant(),
        "disallowed_entries": disallowed,
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    ok = (
        audit["contains_demo_agent"]
        and audit["contains_submission_md"]
        and audit["default_variant"] == "crown_exact_rbt_mpc"
        and not disallowed
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
