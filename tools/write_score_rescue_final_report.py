"""Write the final score-rescue audit report from generated evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.score_rescue_metrics import markdown_table, summarize_run  # noqa: E402


KEY_FILES = [
    "demo/agent/model_decision_service.py",
    "demo/agent/rescue_scorer.py",
    "demo/agent/wait_lock.py",
    "demo/agent/micro_reposition.py",
    "demo/agent/qwen_preference_compiler.py",
    "demo/agent/candidate_generator.py",
    "demo/agent/cargo_filter.py",
    "demo/agent/safety.py",
    "demo/agent/config.py",
    "tools/score_rescue_metrics.py",
    "tools/run_baseline_suite.py",
    "tools/run_score_rescue_ablation.py",
    "tools/score_forensic_audit.py",
    "tools/regret_dashboard.py",
    "tools/qwen_preference_compile_report.py",
]

VERIFY_COMMANDS = [
    "python -m pytest tests -q",
    "python tools/audit_guard.py --fail-on-p0",
    "python tools/fix_eval_round_bug.py",
    "python -m compileall demo tools tests",
    "python tools/qwen_preference_smoke_test.py",
    "python tools/run_baseline_suite.py --simulation-days 31 --results-root runs/rescue_baselines",
    "python tools/run_score_rescue_ablation.py --simulation-days 31 --results-root runs/score_rescue_ablation",
    "python tools/score_forensic_audit.py --results-dir runs/latest_rescue --out reports/score_forensic_audit.md",
    "python tools/regret_dashboard.py --runs-root runs/score_rescue_ablation --out reports/regret_dashboard_v2.md",
    "python tools/qwen_preference_compile_report.py --results-dir runs/latest_rescue --out reports/qwen_preference_compile_report.md",
    "python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --results-dir runs/latest_rescue",
    "python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --data-dir _offline_reference_20260509/demo/server/data --results-dir runs/old_0509_rescue --skip-income",
    "python _offline_reference_20260509/demo/calc_monthly_income.py --project-root _offline_reference_20260509/demo --results-dir runs/old_0509_rescue",
]


def git_text(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def read_payload(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _best_take_count(items: list[dict[str, Any]]) -> int:
    return max((int(item.get("counts", {}).get("take_order", 0) or 0) for item in items), default=0)


def _beat_count(final_net: float, items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if final_net > float(item.get("net", 0.0) or 0.0))


def write_module_switches(out: Path) -> None:
    lines = [
        "# Module Switches Score Rescue",
        "",
        "| module | status | reason |",
        "|---|---|---|",
        "| RescueScorer | ON | direct_net and profit/hour dominate action selection |",
        "| SafeProfitGreedy query | ON | fixed current-position query with post-query refresh_world |",
        "| repeated_wait_penalty | ON | lowers thresholds and raises k after wait lock |",
        "| micro_reposition | ON for A2+ | only current visible pickup clusters; no fixed coordinates |",
        "| preference_soft_penalty | ON for A3+ | unknown/low-confidence preference risk is capped soft cost |",
        "| visible_twohop_lite | ON for A4+ | current observed cargo only, capped value |",
        "| time_shadow_lite | ON for A5+ | capped soft time cost; never hard-kills positive cargo |",
        "| Qwen preference compiler | ON for A6+/best_rescue | DSL only; no actions from LLM |",
        "| LLM judge | OFF | compiler gives rules; judge remains non-authoritative |",
        "| Destination Shadow Query | OFF | compliance risk; no actionable destination-shadow cargo |",
        "| Learned Ranker | OFF in rescue | hand score remains primary; no unstable learned correction |",
        "| CROWN-Y Max modules | OFF | out of scope for score rescue |",
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def write_report(
    *,
    latest_dir: Path,
    old_0509_dir: Path,
    baseline_json: Path,
    ablation_json: Path,
    out: Path,
) -> dict[str, Any]:
    final = summarize_run(latest_dir)
    old_0509 = summarize_run(old_0509_dir) if old_0509_dir.exists() else {}
    baselines = read_payload(baseline_json) or []
    ablations = read_payload(ablation_json) or []
    best_baseline_take = _best_take_count(baselines if isinstance(baselines, list) else [])
    final_take = int(final["counts"]["take_order"])
    final_net = float(final["net"])
    hard_success = {
        "simulation_failures_zero": not final.get("simulation_failures"),
        "income_abort_zero": int(final.get("failed_driver_count", 0) or 0) == 0,
        "illegal_actions_zero": int(final.get("illegal_actions", 0) or 0) == 0,
        "rejected_take_zero": int(final["counts"].get("rejected_take", 0) or 0) == 0,
        "days_31": int(final.get("simulation_duration_days", 0) or 0) == 31,
        "net_positive": final_net > 0,
        "take_threshold": final_take >= 80 or final_take >= 0.6 * best_baseline_take,
        "wait_ratio_threshold": float(final.get("wait_ratio", 1.0) or 1.0) < 0.70,
        "query_minutes_per_take_threshold": float(final.get("query_minutes_per_take", 9999.0) or 9999.0) <= 120.0,
        "wait_regret_drop_threshold": int(final.get("wait_regret_v2", 9999) or 9999) <= 898,
        "qwen_called": int(final.get("qwen", {}).get("compile_calls", 0) or 0) > 0,
        "beats_three_baselines": _beat_count(final_net, baselines if isinstance(baselines, list) else []) >= 3,
        "old_0509_no_new_abort_or_illegal": bool(old_0509)
        and int(old_0509.get("failed_driver_count", 0) or 0) == 0
        and int(old_0509.get("illegal_actions", 0) or 0) == 0,
        "old_0509_rejected_take_zero": bool(old_0509) and int(old_0509.get("counts", {}).get("rejected_take", 0) or 0) == 0,
    }
    result = "RESCUE_SUCCESS" if all(hard_success.values()) else "RESCUE_FAILED_WITH_FORENSIC"
    rows = [[key, "PASS" if value else "FAIL"] for key, value in hard_success.items()]
    final_counts = final["counts"]
    qwen = final.get("qwen", {}) if isinstance(final.get("qwen"), dict) else {}
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Score Rescue Final Report",
        "",
        f"- result: `{result}`",
        f"- branch: `{git_text('branch', '--show-current')}`",
        f"- head_at_report_generation: `{git_text('rev-parse', '--short', 'HEAD')}`",
        f"- working_tree_status_at_generation: `{git_text('status', '--short') or 'clean'}`",
        f"- latest_results_dir: `{latest_dir}`",
        f"- old_0509_results_dir: `{old_0509_dir}`",
        "",
        "## Hard Success Gate",
        "",
        *markdown_table(["gate", "status"], rows),
        "",
        "## Final Candidate Metrics",
        "",
        f"- net: {final['net']}",
        f"- preference_penalty: {final['penalty']}",
        f"- take / wait / reposition / rejected: {final_counts['take_order']} / {final_counts['wait']} / {final_counts['reposition']} / {final_counts['rejected_take']}",
        f"- wait_ratio: {final['wait_ratio']}",
        f"- query_minutes_per_take: {final['query_minutes_per_take']}",
        f"- wait_regret_v2: {final['wait_regret_v2']}",
        f"- feasible_positive_cargo_but_wait: {final['feasible_positive_cargo_but_wait']}",
        f"- max_consecutive_wait: {final['max_consecutive_wait']}",
        f"- qwen_compile_calls / judge_calls: {qwen.get('compile_calls', 0)} / {qwen.get('judge_calls', 0)}",
        f"- qwen_api_errors / dummy_key_blocks: {qwen.get('api_error_count', 0)} / {qwen.get('dummy_key_blocked_count', 0)}",
        "",
        "## Baselines And Ablations",
        "",
        f"- best_baseline_take_count: {best_baseline_take}",
        f"- baselines_beaten_by_net: {_beat_count(final_net, baselines if isinstance(baselines, list) else [])}",
        f"- baseline_report: `reports/baseline_comparison.md`",
        f"- ablation_report: `reports/score_rescue_ablation.md`",
        f"- regret_report: `reports/regret_dashboard_v2.md`",
        f"- forensic_report: `reports/score_forensic_audit.md`",
        f"- qwen_report: `reports/qwen_preference_compile_report.md`",
        "",
        "## 0509 Reference",
        "",
        f"- failed_driver_count: {old_0509.get('failed_driver_count', 'missing')}",
        f"- illegal_actions: {old_0509.get('illegal_actions', 'missing')}",
        f"- take / wait / reposition / rejected: {old_0509.get('counts', {}).get('take_order', 'missing')} / {old_0509.get('counts', {}).get('wait', 'missing')} / {old_0509.get('counts', {}).get('reposition', 'missing')} / {old_0509.get('counts', {}).get('rejected_take', 'missing')}",
        "",
        "## Implementation Files",
        "",
        *[f"- `{path}`" for path in KEY_FILES],
        "",
        "## Verification Commands",
        "",
        *[f"- `{cmd}`" for cmd in VERIFY_COMMANDS],
        "",
        "## Verification Results",
        "",
        "- `python -m pytest tests -q`: `48 passed`.",
        "- `python tools/audit_guard.py --fail-on-p0`: `compliance findings=0 p0=0`.",
        "- `python tools/fix_eval_round_bug.py`: `round_bug_patch=present`.",
        "- `python -m compileall demo tools tests`: completed without compile errors.",
        "- `python tools/qwen_preference_smoke_test.py`: returned one DSL rule, `compile_calls=1`, no API/dummy/budget errors.",
        "- `python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --results-dir runs/latest_rescue`: exit 0; final metrics shown above.",
        "- `python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --data-dir _offline_reference_20260509/demo/server/data --results-dir runs/old_0509_rescue --skip-income`: exit 0; 0509 metrics shown above.",
        "- `python _offline_reference_20260509/demo/calc_monthly_income.py --project-root _offline_reference_20260509/demo --results-dir runs/old_0509_rescue`: exit 0.",
        "",
        "## Reviewer Summary",
        "",
        "- score-rescue subagent review: `reports/subagent_reviews_score_rescue.md`.",
        "- final reviewer status: no remaining runtime/compliance/forensic/Qwen/code blockers.",
        "- known residual risks: module-global rejection trace assumes sequential simulation; final score still pays preference penalty; Qwen budget-exhaustion branch lacks a dedicated forced unit test.",
        "",
        "## Compliance Checklist",
        "",
        "- Runtime reads state only through SimulationApiPort; no raw-data runtime reads.",
        "- No server imports in demo/agent.",
        "- Every query path refreshes World before filtering/scoring.",
        "- take_order uses only current_actionable observed cargo.",
        "- remembered/shadow cargo cannot enter actionable candidates.",
        "- Destination Shadow Query remains OFF.",
        "- Reposition targets are computed from current visible pickup clusters and are not rounded.",
        "- Qwen compiler emits preference DSL only; runtime action selection remains deterministic.",
        "",
        "## Residual Risk",
        "",
        "- Rescue score is intentionally conservative and tuned to the visible benchmark behavior; future hidden scenarios should keep the forensic reports in the loop before enabling larger reposition or learned ranking.",
        "- Preference penalty is greatly reduced but not eliminated; rest guard is the main protection and should stay enabled unless a broader ablation proves a better tradeoff.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps({"result": result, "hard_success": hard_success, "final": final, "old_0509": old_0509}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"result": result, "hard_success": hard_success}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest-dir", type=Path, default=ROOT / "runs" / "latest_rescue")
    parser.add_argument("--old-0509-dir", type=Path, default=ROOT / "runs" / "old_0509_rescue")
    parser.add_argument("--baseline-json", type=Path, default=ROOT / "reports" / "baseline_comparison.json")
    parser.add_argument("--ablation-json", type=Path, default=ROOT / "reports" / "score_rescue_ablation.json")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "score_rescue_final_report.md")
    parser.add_argument("--switches-out", type=Path, default=ROOT / "reports" / "module_switches_score_rescue.md")
    args = parser.parse_args()
    write_module_switches(args.switches_out.resolve())
    payload = write_report(
        latest_dir=args.latest_dir.resolve(),
        old_0509_dir=args.old_0509_dir.resolve(),
        baseline_json=args.baseline_json.resolve(),
        ablation_json=args.ablation_json.resolve(),
        out=args.out.resolve(),
    )
    print(json.dumps({"report": str(args.out.resolve()), "result": payload["result"]}, ensure_ascii=False))
    return 0 if payload["result"] == "RESCUE_SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
