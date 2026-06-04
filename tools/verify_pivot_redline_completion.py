"""Phase-aware CROWN-PIVOT-REDLINE completion verifier."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pivot_redline_common as common  # noqa: E402


def _rows(dataset: str | None = None) -> list[dict[str, str]]:
    rows = common.read_csv(common.EXPERIMENT_GRID)
    if dataset is None:
        return rows
    return [row for row in rows if row.get("dataset") == dataset]


def _by_trial(dataset: str = "20260529") -> dict[str, dict[str, str]]:
    return {row.get("trial_id", ""): row for row in _rows(dataset)}


def _missing_fields(row: dict[str, str]) -> list[str]:
    missing = []
    for field in (
        "run_dir",
        "command",
        "exit_code",
        "dataset",
        "simulation_days",
        "official_net",
        "gross_minus_cost",
        "preference_penalty",
        "take_count",
        "wait_count",
        "reposition_count",
        "query_count",
        "query_minutes",
        "invalid_count",
        "rejected_take_count",
        "income_abort_count",
        "trace_path",
        "config_hash",
    ):
        if row.get(field) in {"", None}:
            missing.append(field)
    run_dir = row.get("run_dir") or ""
    if run_dir and not (common.ROOT / run_dir).exists():
        missing.append("run_dir_exists")
    trace_path = row.get("trace_path") or ""
    if trace_path and not (common.ROOT / trace_path).exists():
        missing.append("trace_path_exists")
    return missing


def _reviewer_texts() -> str:
    if not common.REVIEWERS.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in common.REVIEWERS.glob("*.md"))


def fail_setup() -> list[str]:
    failures: list[str] = []
    common.ensure_dirs()
    if common.current_branch() != "crown-pivot-redline-v1":
        failures.append(f"wrong branch {common.current_branch()!r}")
    required = [
        common.ROOT / "CROWN_PIVOT_REDLINE_v1_1_codex_prompt.md",
        common.ROOT / "AGENTS.md",
        common.ROOT / "agent.md",
        common.ROOT / "tools" / "verify_pivot_redline_completion.py",
        common.ROOT / "tools" / "audit_pivot_runtime_path.py",
        common.PIVOT_AGENT,
        common.SUBAGENT_PREFLIGHT,
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing setup artifact {path.relative_to(common.ROOT)}")
    if (common.ROOT / "tools" / "verify_pivot_redline_completion.py").read_text(encoding="utf-8", errors="ignore").count("def fail_") < 10:
        failures.append("verifier is not phase-aware")
    if common.SUBAGENT_PREFLIGHT.exists():
        text = common.SUBAGENT_PREFLIGHT.read_text(encoding="utf-8", errors="ignore")
        if "Anti-Shell Source Auditor" not in text or "agent_id" not in text:
            failures.append("subagent preflight does not record real reviewer attempt")
    return failures


def fail_noop() -> list[str]:
    failures: list[str] = []
    table = _by_trial()
    b0 = table.get("R0_B0_best_rescue")
    if not common.row_status_ok(b0):
        failures.append("R0_B0_best_rescue missing or not EXECUTED")
        return failures
    if common.safe_float(b0.get("official_net")) < 5000:
        failures.append("B0 official_net gate failed")
    if common.safe_float(b0.get("gross_minus_cost")) < 43000:
        failures.append("B0 gross gate failed")
    if common.safe_float(b0.get("preference_penalty")) > 38200:
        failures.append("B0 penalty gate failed")
    if sum(common.safe_int(b0.get(k)) for k in ("invalid_count", "rejected_take_count", "income_abort_count")):
        failures.append("B0 invalid/rejected/income_abort nonzero")
    for trial_id in (
        "R1_pivot_noop_compile_all_weights_zero",
        "R2_pivot_noop_debt_monitor_score_zero",
        "R3_pivot_noop_value_model_loaded_weight_zero",
        "R4_pivot_noop_query_logger_exact_b0_query",
        "R5_pivot_noop_candidate_bucket_b0_action_forced",
        "R6_pivot_noop_unforced_full_planner_all_new_weights_zero",
    ):
        row = table.get(trial_id)
        if not common.row_status_ok(row):
            failures.append(f"{trial_id} missing or not EXECUTED")
            continue
        if row.get("variant") != "crown_pivot_redline_v1":
            failures.append(f"{trial_id} did not use pivot variant")
        if common.safe_float(row.get("action_signature_match_rate_if_noop")) < 0.999:
            failures.append(f"{trial_id} action match < 0.999")
        if abs(common.safe_float(row.get("official_net")) - common.safe_float(b0.get("official_net"))) > 100:
            failures.append(f"{trial_id} net delta > 100")
        if str(row.get("b0_shadow_pure", "")).lower() != "true":
            failures.append(f"{trial_id} lacks pure B0 shadow evidence")
    audit = _read_runtime_audit()
    if audit:
        if audit.get("_decide_rescue_call_count", 1) != 0:
            failures.append("pivot runtime path calls _decide_rescue")
        if audit.get("rescue_scorer_score_call_count", 1) != 0:
            failures.append("pivot runtime path calls rescue_scorer scoring")
        if audit.get("rescue_scorer_choose_call_count", 1) != 0:
            failures.append("pivot runtime path calls rescue_scorer choose")
        if common.safe_int(audit.get("pivot_decide_call_count")) <= 0:
            failures.append("pivot runtime path did not call PivotRedlinePlanner.decide")
    else:
        failures.append("missing audit_pivot_runtime_path output")
    return failures


def fail_archaeology() -> list[str]:
    failures: list[str] = []
    rows = [row for row in common.read_csv(common.FORENSICS) if row.get("stage") == "archaeology"]
    required = {
        "money_greedy_no_pref",
        "trial_017",
        "B9c_wait_repair_full",
        "Gold_final",
        "money_trajectory_repair",
        "visibility_k600_oracle",
    }
    seen = {row.get("component") for row in rows}
    missing = sorted(required - seen)
    if missing:
        failures.append(f"missing archaeology anchors {missing}")
    if common.DISTILLATION_TABLE.exists():
        for row in common.read_csv(common.DISTILLATION_TABLE):
            if row.get("reproduction_status") in {"artifact_only", "fail"} and row.get("exportable_parameter") not in {"", "not_transferable", "none"}:
                failures.append(f"artifact-only anchor exported parameter: {row.get('source_variant')}")
    else:
        failures.append("missing dragon_orca_distillation_table.csv")
    if not common.TRANSFER_CHECKLIST.is_file():
        failures.append("missing redline_runtime_transfer_checklist.csv")
    return failures


def fail_money() -> list[str]:
    failures: list[str] = []
    money_rows = [row for row in _rows("20260529") if str(row.get("trial_id", "")).startswith("MONEY")]
    executed = [row for row in money_rows if common.row_status_ok(row)]
    if len(executed) < 40:
        failures.append(f"clean money executed rows {len(executed)} < 40")
    best_gross = max((common.safe_float(row.get("gross_minus_cost")) for row in executed), default=0.0)
    if best_gross < 52000 and not _has_forensic("high_gross_backbone_not_recovered"):
        failures.append("clean money gross < 52000 without money forensics")
    if not _has_chain_test("T1_candidate_bucket_diversity"):
        failures.append("missing candidate bucket diversity chain test")
    return failures


def fail_compiler() -> list[str]:
    failures: list[str] = []
    audit_rows = common.read_csv(common.MODEL_TRACE_AUDIT)
    qwen = [row for row in audit_rows if row.get("module") == "qwen_contract_ensemble"]
    if not qwen:
        failures.append("missing Qwen compiler audit rows")
    elif all(row.get("status") != "PASS" for row in qwen):
        failures.append("Qwen compiler gym has not passed")
    gym = common.RUNS / "qwen_contract_gym.json"
    if not gym.is_file():
        failures.append("missing qwen_contract_gym.json")
    if sum(common.safe_int(row.get("qwen_numeric_adjustments")) for row in _rows()) > 0:
        failures.append("Qwen numeric auditor adjustment is nonzero")
    return failures


def fail_scorer_probe() -> list[str]:
    failures: list[str] = []
    rows = [row for row in common.read_csv(common.MODEL_TRACE_AUDIT) if row.get("module") in {"scorer_semantics_profile", "preference_state"}]
    if len(rows) < 2:
        failures.append("missing scorer probe / preference debt audit rows")
    if not (common.RUNS / "scorer_probe_semantic_profile.json").is_file():
        failures.append("missing scorer probe semantic profile")
    return failures


def fail_models() -> list[str]:
    failures: list[str] = []
    rows = common.read_csv(common.MODEL_TRACE_AUDIT)
    for module in ("risk_model", "value_model", "conservative_ranker"):
        matches = [row for row in rows if row.get("module") == module]
        if not matches:
            failures.append(f"missing {module} model audit row")
        elif all(common.safe_int(row.get("full_run_rows_used")) <= 0 for row in matches):
            failures.append(f"{module} lacks full-run usage evidence")
    return failures


def fail_planner() -> list[str]:
    failures: list[str] = []
    audit = _read_runtime_audit()
    if not audit:
        failures.append("missing runtime path audit")
    else:
        for key in ("_decide_rescue_call_count", "rescue_scorer_score_call_count", "rescue_scorer_choose_call_count"):
            if common.safe_int(audit.get(key), 1) != 0:
                failures.append(f"{key} is nonzero")
        if common.safe_int(audit.get("pivot_decide_call_count")) <= 0:
            failures.append("pivot_decide_call_count is zero")
    for test in (
        "T4_beam_branch_expansion",
        "T5_b0_shadow_side_effect",
        "T6_end_to_end_trace",
        "T7_full_precision_reposition",
    ):
        if not _has_chain_test(test):
            failures.append(f"missing chain test {test}")
    return failures


def fail_search() -> list[str]:
    failures: list[str] = []
    data = _rows("20260529")
    for idx, row in enumerate(data, start=2):
        status = str(row.get("status", ""))
        if status in common.FORBIDDEN_STATUS or status != "EXECUTED":
            failures.append(f"row {idx} forbidden/non-executed status {status}")
        if common.safe_int(row.get("simulation_days")) != 31:
            failures.append(f"row {idx} is not a 31-day full run")
        if common.safe_int(row.get("exit_code"), 99) != 0:
            failures.append(f"row {idx} exit_code nonzero")
        if bad := _missing_fields(row):
            failures.append(f"row {idx} missing fields {bad}")
    counted = [row for row in data if common.row_status_ok(row) and common.safe_int(row.get("simulation_days")) == 31]
    if len(counted) < 120:
        failures.append(f"executed 20260529 full rows {len(counted)} < 120")
    if len([r for r in counted if common.safe_int(r.get("reevo_generation")) > 0]) < 40:
        failures.append("ReEvo executed rows < 40")
    if len([r for r in counted if str(r.get("stage", "")).lower().startswith(("bo", "cma", "coordinate"))]) < 40:
        failures.append("BO/CMA/coordinate executed rows < 40")
    if len([r for r in counted if common.safe_int(r.get("beam_used_count")) > 0 or common.safe_int(r.get("value_model_used_count")) > 0 or common.safe_int(r.get("query_optimizer_used_count")) > 0]) < 20:
        failures.append("beam/value/query joint executed rows < 20")
    return failures


def fail_final() -> list[str]:
    failures: list[str] = []
    for fn in (
        fail_setup,
        fail_noop,
        fail_archaeology,
        fail_money,
        fail_compiler,
        fail_scorer_probe,
        fail_models,
        fail_planner,
        fail_search,
    ):
        failures.extend(fn())
    if common.REPORTS.exists():
        actual = {path.name for path in common.REPORTS.iterdir() if path.is_file()}
    else:
        actual = set()
    if actual != common.REPORT_FILES:
        failures.append(f"reports must contain exactly pivot files actual={sorted(actual)}")
    stop_state = common.extract_stop_state()
    if stop_state not in common.ALLOWED_STOP_STATES:
        failures.append(f"invalid stop_state {stop_state!r}")
    rows_0509 = [row for row in _rows("20260509") if common.row_status_ok(row)]
    if _top_candidate_requires_0509() and len(rows_0509) < 20:
        failures.append(f"0509 sanity rows {len(rows_0509)} < 20")
    failures.extend(_package_failures(stop_state))
    reviewer_text = _reviewer_texts()
    for name in (
        "Anti-Shell Source Auditor",
        "B0 Isolation Auditor",
        "High-Score Archaeology Auditor",
        "Clean Money Backbone Auditor",
        "Final Anti-Shell Auditor",
    ):
        if name not in reviewer_text:
            failures.append(f"missing reviewer transcript {name}")
    return failures


def _read_runtime_audit() -> dict[str, object]:
    if not common.RUNTIME_PATH_AUDIT.is_file():
        return {}
    try:
        data = json.loads(common.RUNTIME_PATH_AUDIT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _has_forensic(component: str) -> bool:
    return any(row.get("component") == component for row in common.read_csv(common.FORENSICS))


def _has_chain_test(test_name: str) -> bool:
    return any(row.get("artifact") == test_name and row.get("status") == "PASS" for row in common.read_csv(common.MODEL_TRACE_AUDIT))


def _top_candidate_requires_0509() -> bool:
    b0_net = common.B0_NET
    b0_penalty = common.B0_PENALTY
    b0_gross = common.B0_GROSS
    for row in _rows("20260529"):
        if not common.row_status_ok(row):
            continue
        if common.safe_float(row.get("official_net")) > b0_net + 3000:
            return True
        if common.safe_float(row.get("preference_penalty")) < b0_penalty - 6000:
            return True
        if common.safe_float(row.get("gross_minus_cost")) > b0_gross + 8000:
            return True
        if common.safe_float(row.get("official_net")) >= 10000:
            return True
    return False


def _package_failures(stop_state: str) -> list[str]:
    failures: list[str] = []
    packages = [path for path in common.PACKAGES.glob("CROWN_PIVOT_REDLINE*.zip") if path.is_file()]
    submission_states = {"PIVOT_RECOMMENDED_SUBMISSION", "PIVOT_EXPERIMENTAL_SUBMISSION"}
    if stop_state in submission_states:
        if len(packages) != 1:
            failures.append(f"expected exactly one pivot package, found {len(packages)}")
            return failures
    elif packages:
        failures.append("pivot package exists for non-submission stop state")
        return failures
    for package in packages:
        with zipfile.ZipFile(package) as zf:
            names = [name for name in zf.namelist() if name and not name.endswith("/")]
            if any(not name.startswith("demo/") for name in names):
                failures.append("package root is not demo/")
            if not any(name.startswith("demo/agent/") for name in names):
                failures.append("package missing demo/agent/")
            if "demo/SUBMISSION.md" not in names:
                failures.append("package missing demo/SUBMISSION.md")
            forbidden = [
                name
                for name in names
                if any(part in Path(name).parts for part in ("server", "data", "reports", "runs", "archive", "docs", "keys", "__pycache__"))
                or name.endswith((".pyc", ".pyo"))
                or "prompt" in name.lower()
            ]
            if forbidden:
                failures.append(f"package forbidden entries {forbidden[:5]}")
    return failures


PHASES: dict[str, Callable[[], list[str]]] = {
    "setup": fail_setup,
    "noop": fail_noop,
    "archaeology": fail_archaeology,
    "money": fail_money,
    "compiler": fail_compiler,
    "scorer_probe": fail_scorer_probe,
    "models": fail_models,
    "planner": fail_planner,
    "search": fail_search,
    "final": fail_final,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=sorted(PHASES), required=True)
    args = parser.parse_args()
    failures = PHASES[args.phase]()
    status = "PASS" if not failures else "FAIL"
    print({"phase": args.phase, "status": status, "failures": failures})
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
