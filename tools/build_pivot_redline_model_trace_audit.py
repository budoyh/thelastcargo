"""Record deterministic Pivot-Redline chain-test and module audit evidence."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pivot_redline_common as common  # noqa: E402


CHAIN_ROWS = [
    ("T1_candidate_bucket_diversity", "candidate_bucket", "PASS", "demo/agent/pivot_redline/candidate_bucket.py", "tests/test_pivot_redline_core.py", "pivot_redline.candidate_bucket_counts", "bucketed candidates include direct, pph, short duration, low deadhead, terminal proxy, wait"),
    ("T2_risk_model_known_bad_action", "risk_model", "PASS", "demo/agent/pivot_redline/risk_model.py", "tests/test_pivot_redline_core.py", "pivot_redline.score_components.pivot_risk_model", "long lockup/deadhead/month-end action ranks riskier than safe alternative"),
    ("T3_value_model_terminal_choice", "value_model", "PASS", "demo/agent/pivot_redline/value_model.py", "tests/test_pivot_redline_core.py", "pivot_redline.score_components.pivot_terminal_value", "near terminal visible opportunity receives higher value"),
    ("T4_beam_branch_expansion", "beam_rollout", "PASS", "demo/agent/pivot_redline/beam_rollout.py", "tests/test_pivot_redline_core.py", "pivot_redline.score_components.pivot_beam_rollout", "BeamNode depth 2 creates children and continuation score"),
    ("T5_b0_shadow_side_effect", "b0_shadow", "PASS", "demo/agent/pivot_redline/b0_shadow.py", "tests/test_pivot_redline_core.py", "pivot_redline.b0_pure_action", "pure shadow scoring leaves option score/trace unchanged"),
    ("T6_end_to_end_trace", "planner", "PASS", "demo/agent/pivot_redline/planner.py", "tests/test_pivot_redline_core.py", "pivot_redline.top5_candidates", "fake API end-to-end decision emits top candidates and B0 shadow fields"),
    ("T7_full_precision_reposition", "safety_gate", "PASS", "demo/agent/safety.py", "tests/test_pivot_redline_core.py", "action.params.latitude/action.params.longitude", "finalize preserves full precision reposition coordinates"),
]

MODULE_ROWS = [
    ("pivot_runtime_path", "planner", "IMPLEMENTED_BUT_NOT_ACTIVE", "demo/agent/pivot_redline/planner.py", "tests/test_pivot_redline_core.py", "pivot_redline", "needs 31-day full-run and ablation"),
    ("qwen_contract_ensemble", "qwen_contract_ensemble", "IMPLEMENTED_BUT_NOT_ACTIVE", "demo/agent/pivot_redline/qwen_contract_ensemble.py", "", "pivot_redline.qwen_contract_ensemble", "semantic-only boundary present; no live Qwen gym evidence yet"),
    ("scorer_semantics_profile", "scorer_semantics_profile", "DIAGNOSTIC_ONLY", "demo/agent/pivot_redline/scorer_semantics_profile.py", "", "pivot_redline.semantic_profile", "offline scorer probes not executed yet"),
    ("preference_debt_accountant", "preference_state", "IMPLEMENTED_BUT_NOT_ACTIVE", "demo/agent/pivot_redline/preference_state.py", "", "pivot_preference_debt", "runtime path exists; no full-run/ablation evidence yet"),
    ("risk_model_runtime", "risk_model", "IMPLEMENTED_BUT_NOT_ACTIVE", "demo/agent/pivot_redline/risk_model.py", "tests/test_pivot_redline_core.py", "pivot_risk_model", "generic runtime model only; no trained labels/full-run evidence yet"),
    ("value_model_runtime", "value_model", "IMPLEMENTED_BUT_NOT_ACTIVE", "demo/agent/pivot_redline/value_model.py", "tests/test_pivot_redline_core.py", "pivot_terminal_value", "runtime estimator only; no trained labels/full-run evidence yet"),
    ("conservative_ranker", "conservative_ranker", "DIAGNOSTIC_ONLY", "demo/agent/pivot_redline/scoring_formula.py", "", "pivot_redline.weights", "IQL/CQL-lite training not executed yet"),
]


def main() -> int:
    common.ensure_dirs()
    rows = []
    for artifact, module, status, impl, test, trace, notes in CHAIN_ROWS + MODULE_ROWS:
        rows.append(
            {
                "artifact": artifact,
                "module": module,
                "status": status,
                "implementation_file": impl,
                "test_file": test,
                "runtime_trace_field": trace,
                "full_run_rows_used": 0,
                "ablation_delta_net": "",
                "reviewer_status": "pending_read_only_reviewer" if status != "PASS" else "unit_verified",
                "keep_or_kill": status,
                "notes": notes,
            }
        )
    common.write_csv(common.MODEL_TRACE_AUDIT, rows, common.MODEL_TRACE_FIELDS)
    print({"rows": len(rows), "path": str(common.MODEL_TRACE_AUDIT.relative_to(common.ROOT))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
