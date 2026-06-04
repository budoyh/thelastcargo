"""Build and audit Dragon-Orca submission or review-only package."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dragon_orca_common as common  # noqa: E402

SUBMISSION_STATES = {"DRAGON_RECOMMENDED_SUBMISSION", "DRAGON_EXPERIMENTAL_SUBMISSION"}
REVIEW_STATE = "DO_NOT_SUBMIT_WITH_REVIEW_ONLY_PACKAGE"


def stop_state() -> str:
    if not common.FINAL_REPORT.is_file():
        return ""
    first = common.FINAL_REPORT.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    return first[0].split(":", 1)[0].strip() if first else ""


def best_variant() -> str:
    rows = [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"]
    if not rows:
        return "crown_dragon_orca"
    best = max(rows, key=lambda row: common.safe_float(row.get("official_net")))
    return best.get("variant") or "crown_dragon_orca"


def submission_text(state: str) -> str:
    if state == "DRAGON_EXPERIMENTAL_SUBMISSION":
        first = "EXPERIMENTAL: USER DECISION REQUIRED"
    elif state == "DRAGON_RECOMMENDED_SUBMISSION":
        first = "RECOMMENDED: DRAGON ORCA SUBMISSION"
    else:
        first = "NOT RECOMMENDED FOR B榜 SUBMISSION"
    return "\n".join([
        first,
        "",
        "# CROWN-DRAGON-ORCA Package Notes",
        "",
        "- ZIP root is demo/.",
        "- Included: demo/agent/ and demo/SUBMISSION.md only.",
        "- Runtime default policy is crown_dragon_orca unless CROWN_Y_VARIANT overrides it for local experiments.",
        "- Qwen may compile/link preferences, but numeric auditor score adjustment is disabled.",
        "- Runtime does not read reports, runs, raw datasets, server internals, scorer outputs, income calculators, raw Qwen IO, or future cargo.",
        "- take_order uses only current post-query actionable cargo after refresh_world.",
        "",
    ])


def iter_package_files(staging_demo: Path) -> list[Path]:
    files = [staging_demo / "SUBMISSION.md"]
    agent = staging_demo / "agent"
    files.extend(path for path in sorted(agent.rglob("*")) if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"})
    return files


def inspect_zip(path: Path, state: str) -> tuple[bool, list[str], str]:
    sha = common.file_sha256(path)
    failures: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = [name for name in zf.namelist() if name and not name.endswith("/")]
        if any(not name.startswith("demo/") for name in names):
            failures.append("bad_root")
        if not any(name.startswith("demo/agent/") for name in names):
            failures.append("missing_demo_agent")
        if "demo/SUBMISSION.md" not in names:
            failures.append("missing_submission_md")
        forbidden = [name for name in names if any(part in Path(name).parts for part in ("server", "data", "reports", "runs", "archive", "docs", "keys", "__pycache__")) or name.endswith((".pyc", ".pyo")) or "prompt" in name.lower() or ".env" in name.lower()]
        if forbidden:
            failures.append("forbidden_entries=" + ",".join(forbidden[:5]))
        config_text = zf.read("demo/agent/config.py").decode("utf-8", errors="ignore") if "demo/agent/config.py" in names else ""
        if "crown_dragon_orca" not in config_text:
            failures.append("default_variant_not_dragon")
        first = zf.read("demo/SUBMISSION.md").decode("utf-8", errors="ignore").splitlines()[0].strip() if "demo/SUBMISSION.md" in names else ""
        if state == REVIEW_STATE and first != "NOT RECOMMENDED FOR B榜 SUBMISSION":
            failures.append("review_submission_first_line_wrong")
        if state == "DRAGON_EXPERIMENTAL_SUBMISSION" and first != "EXPERIMENTAL: USER DECISION REQUIRED":
            failures.append("experimental_submission_first_line_wrong")
    return not failures, failures, sha


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-review", action="store_true")
    args = parser.parse_args()
    common.ensure_dirs()
    state = stop_state()
    if args.force_review and state not in SUBMISSION_STATES:
        state = REVIEW_STATE
    variant = best_variant()
    common.PACKAGES.mkdir(parents=True, exist_ok=True)
    for old in common.PACKAGES.glob("CROWN_DRAGON_ORCA*.zip"):
        old.unlink()
    if state not in SUBMISSION_STATES | {REVIEW_STATE}:
        common.PACKAGE_AUDIT.write_text("\n".join(["# Dragon-Orca Package Audit", "", "- package_audit_status: PASS", "- package_path: not_built", "- sha256: not_built", f"- reason: stop_state {state} does not allow a package", ""]), encoding="utf-8")
        print({"state": state, "package": "not_built"})
        return 0
    with tempfile.TemporaryDirectory(prefix="dragon_orca_pkg_") as tmp:
        staging = Path(tmp) / "demo"
        shutil.copytree(ROOT / "demo" / "agent", staging / "agent", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".env", "local_config.py"))
        (staging / "SUBMISSION.md").write_text(submission_text(state), encoding="utf-8")
        token = re.sub(r"[^A-Za-z0-9_]+", "_", variant).strip("_") or "crown_dragon_orca"
        if state == REVIEW_STATE:
            out = common.PACKAGES / f"CROWN_DRAGON_ORCA_REVIEW_ONLY_NOT_RECOMMENDED_DO_NOT_SUBMIT_{token}_{common.short_hash(common.current_commit(), 8)}.zip"
        else:
            out = common.PACKAGES / f"CROWN_DRAGON_ORCA_{state}_{token}_{common.short_hash(common.current_commit(), 8)}.zip"
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in iter_package_files(staging):
                zf.write(path, path.relative_to(Path(tmp)).as_posix())
    ok, failures, sha = inspect_zip(out, state)
    common.PACKAGE_AUDIT.write_text("\n".join(["# Dragon-Orca Package Audit", "", f"- package_audit_status: {'PASS' if ok else 'FAIL'}", f"- stop_state: {state}", f"- package_path: {out}", f"- sha256: {sha}", f"- default_variant: {variant}", f"- failures: {failures}", ""]), encoding="utf-8")
    (ROOT / "demo" / "SUBMISSION.md").write_text(submission_text(state), encoding="utf-8")
    common.append_work_log(f"dragon package state={state} ok={ok} path={out} sha={sha}")
    print({"state": state, "ok": ok, "package": str(out), "sha256": sha, "failures": failures})
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
