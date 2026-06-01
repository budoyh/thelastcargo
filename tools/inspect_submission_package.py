"""Inspect a PTT submission ZIP for official package shape."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "runs" / "packages" / "ptt_package_audit.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    with zipfile.ZipFile(args.zip_path) as zf:
        names = zf.namelist()
        config_text = zf.read("demo/agent/config.py").decode("utf-8") if "demo/agent/config.py" in names else ""
    disallowed = [
        name
        for name in names
        if not name.startswith("demo/")
        or name.startswith(("demo/server/", "server/", "data/", "results/", "reports/", "runs/", "archive/", "docs/"))
        or "__pycache__" in name
        or name.endswith((".pyc", ".pyo"))
        or "prompt" in name.lower()
        or "key" in name.lower()
        or ".env" in name
    ]
    audit = {
        "zip_path": str(args.zip_path),
        "sha256": _sha256(args.zip_path),
        "size_bytes": args.zip_path.stat().st_size,
        "entry_count": len(names),
        "root_demo_only": all(name.startswith("demo/") for name in names),
        "contains_demo_agent": any(name.startswith("demo/agent/") for name in names),
        "contains_submission_md": "demo/SUBMISSION.md" in names,
        "default_variant_config_text": "preference_firewall_profit" in config_text,
        "best_rescue_default_absent": 'os.environ.get("CROWN_Y_VARIANT", "best_rescue")' not in config_text,
        "disallowed_entries": disallowed,
    }
    previous = {}
    if AUDIT_PATH.exists():
        try:
            previous = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}
    previous.update({"inspection": audit})
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(previous, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    ok = (
        audit["root_demo_only"]
        and audit["contains_demo_agent"]
        and audit["contains_submission_md"]
        and audit["default_variant_config_text"]
        and audit["best_rescue_default_absent"]
        and not disallowed
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
