"""Phase-aware Pref-Forge completion verifier."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common

ALLOWED_STOP_STATES = {
    "PREF_FORGE_CROWN_TARGET_READY",
    "PREF_FORGE_RECOMMENDED_SUBMISSION_READY",
    "PREF_FORGE_EXPERIMENTAL_SUBMISSION_READY",
    "PREF_FORGE_HIDDEN_SAFE_REVIEW_READY",
    "PREF_FORGE_DO_NOT_SUBMIT_WITH_EVIDENCE",
    "EXTERNAL_BLOCKER_EVAL_INFRA",
    "EXTERNAL_BLOCKER_QWEN_API",
    "EXTERNAL_BLOCKER_GIT_OR_NETWORK",
    "EXTERNAL_BLOCKER_MISSING_DATA",
}


def _failures_benchmark() -> list[str]:
    failures = []
    if not common.RAW_PREFS.is_file():
        failures.append("private raw preference extraction missing")
    if not common.GOLD_LABELS.is_file():
        failures.append("private frozen gold labels missing")
    rows = common.read_csv(common.COMPILE_BENCHMARK)
    if not rows:
        failures.append("compile benchmark csv missing or empty")
        return failures
    public = [row for row in rows if row.get("split") == "public_dev_46"]
    if len(public) != 46:
        failures.append(f"public_dev_46 rows {len(public)} != 46")
    splits = {row.get("split") for row in rows}
    for split in ("public_dev_46", "synthetic_hidden_holdout", "adversarial_ambiguous_holdout"):
        if split not in splits:
            failures.append(f"missing split {split}")
    qwen_calls = sum(common.safe_int(row.get("qwen_calls")) for row in public)
    if qwen_calls <= 0:
        failures.append("public benchmark has zero Qwen calls")
    if any(str(row.get("raw_literal_committed_flag")).lower() == "true" for row in rows):
        failures.append("raw literal committed flag present")
    schema_rate = sum(str(row.get("schema_valid")).lower() == "true" for row in rows) / max(1, len(rows))
    primitive_rate = sum(str(row.get("primitive_family_ok")).lower() == "true" for row in rows) / max(1, len(rows))
    if schema_rate < 0.98:
        failures.append(f"schema_valid_rate {schema_rate:.3f} < 0.980")
    if primitive_rate < 0.95:
        failures.append(f"primitive_family_accuracy {primitive_rate:.3f} < 0.950")
    return failures


def _rows_20260529() -> list[dict[str, str]]:
    return [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260529"]


def _failures_noop() -> list[str]:
    failures = []
    rows = _rows_20260529()
    by_id = {row.get("trial_id"): row for row in rows}
    for trial in ("E0", "E1", "E2"):
        row = by_id.get(trial)
        if not row or row.get("status") != "EXECUTED":
            failures.append(f"{trial} not EXECUTED")
    e0 = by_id.get("E0")
    if e0:
        if common.safe_float(e0.get("official_net")) < 5000:
            failures.append("E0 B0 official_net gate failed")
        if common.safe_float(e0.get("gross_minus_cost")) < 43000:
            failures.append("E0 B0 gross gate failed")
        if common.safe_float(e0.get("preference_penalty")) > 38200:
            failures.append("E0 B0 penalty gate failed")
        if common.safe_int(e0.get("invalid_count")):
            failures.append("E0 invalid_count nonzero")
    for trial in ("E1", "E2"):
        row = by_id.get(trial)
        if not row:
            continue
        if common.safe_float(row.get("action_signature_match_rate")) < 0.999:
            failures.append(f"{trial} action_signature_match_rate < 0.999")
        if e0 and abs(common.safe_float(row.get("official_net")) - common.safe_float(e0.get("official_net"))) > 100:
            failures.append(f"{trial} official_net delta > 100")
        if e0 and abs(common.safe_float(row.get("gross_minus_cost")) - common.safe_float(e0.get("gross_minus_cost"))) > 100:
            failures.append(f"{trial} gross delta > 100")
        if e0 and abs(common.safe_float(row.get("preference_penalty")) - common.safe_float(e0.get("preference_penalty"))) > 100:
            failures.append(f"{trial} penalty delta > 100")
    if any(str(row.get("b0_shadow_pure")).lower() != "true" for row in rows if row.get("trial_id") in {"E0", "E1", "E2"}):
        failures.append("B0 shadow pure flag missing")
    return failures


def _failures_experiments() -> list[str]:
    failures = []
    rows = _rows_20260529()
    by_id = {row.get("trial_id"): row for row in rows}
    for idx in range(14):
        trial = f"E{idx}"
        if by_id.get(trial, {}).get("status") != "EXECUTED":
            failures.append(f"mandatory {trial} not EXECUTED")
    bad_status = [row.get("trial_id") for row in rows if row.get("status") in {"PLANNED", "MISSING_RUN", "proxy_only", "smoke_only"}]
    if bad_status:
        failures.append(f"illegal non-executed statuses present: {bad_status[:5]}")
    e5 = by_id.get("E5")
    if e5 and e5.get("status") == "EXECUTED":
        gross = common.safe_float(e5.get("gross_minus_cost"))
        penalty_delta = common.safe_float(e5.get("penalty_delta_vs_b0"))
        if gross < common.B0_GROSS + 3000 and gross < 48000:
            failures.append(f"E5 gross gate failed gross={gross}")
        if penalty_delta > 8000:
            failures.append(f"E5 penalty explosion gate failed delta={penalty_delta}")
    if by_id.get("E11", {}).get("status") != "EXECUTED":
        failures.append("E11 current-branch full run missing")
    e12 = by_id.get("E12")
    if e12 and e12.get("status") == "EXECUTED":
        for field in ("refill_gross_gain", "penalty_reintroduced", "official_net_delta_vs_e11"):
            if e12.get(field) in {"", None}:
                failures.append(f"E12 missing {field}")
    search_count = sum(1 for row in rows if row.get("status") == "EXECUTED" and str(row.get("trial_id", "")).startswith("G"))
    if search_count < 60:
        failures.append(f"executed 20260529 search rows {search_count} < 60")
    if not common.PENALTY_DIFF.is_file():
        failures.append("pref_forge_penalty_diff.csv missing")
    return failures


def _extract_stop_state() -> str:
    if not common.FINAL_REPORT.is_file():
        return ""
    text = common.FINAL_REPORT.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"stop_state:\s*([A-Z0-9_]+)", text)
    return match.group(1) if match else ""


def _failures_final() -> list[str]:
    failures = []
    failures.extend(_failures_benchmark())
    failures.extend(_failures_noop())
    failures.extend(_failures_experiments())
    required = {
        "pref_forge_final_report.md",
        "pref_forge_compile_benchmark.csv",
        "pref_forge_experiment_grid.csv",
        "pref_forge_penalty_diff.csv",
        "pref_forge_package_audit.md",
    }
    actual = {path.name for path in common.REPORTS.iterdir() if path.is_file()} if common.REPORTS.exists() else set()
    pref_actual = {name for name in actual if name.startswith("pref_forge_")}
    if pref_actual != required:
        failures.append(f"Pref-Forge reports mismatch actual={sorted(pref_actual)}")
    stop_state = _extract_stop_state()
    if stop_state not in ALLOWED_STOP_STATES:
        failures.append(f"invalid or missing stop_state {stop_state!r}")
    rows_0509 = [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260509" and row.get("status") == "EXECUTED"]
    if not rows_0509:
        failures.append("0509 sanity rows missing")
    audit_text = common.PACKAGE_AUDIT.read_text(encoding="utf-8", errors="ignore") if common.PACKAGE_AUDIT.is_file() else ""
    if "package_audit_status: `PASS" not in audit_text:
        failures.append("package audit not PASS")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["benchmark", "noop", "experiments", "final"], required=True)
    args = parser.parse_args()
    if args.phase == "benchmark":
        failures = _failures_benchmark()
    elif args.phase == "noop":
        failures = _failures_noop()
    elif args.phase == "experiments":
        failures = _failures_experiments()
    else:
        failures = _failures_final()
    status = "PASS" if not failures else "FAIL"
    print({"phase": args.phase, "status": status, "failures": failures})
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
