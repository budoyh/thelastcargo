"""Build Pivot-Redline source forensics tables from code inspection."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pivot_redline_common as common  # noqa: E402


CODE_AUDIT_SPECS: list[dict[str, Any]] = [
    {
        "component": "model_decision_service_rescue_path",
        "claimed_role": "runtime decision entrypoint",
        "actual_source_file": "demo/agent/model_decision_service.py",
        "actually_called_by_runtime": "yes",
        "changes_candidate_generation": "yes",
        "changes_score": "yes",
        "changes_action": "yes",
        "uses_rescue_path": "yes for Dragon/Rescue; no for pivot branch",
        "trace_source": "actual",
        "is_shell": "yes for Dragon-Orca overlay",
        "fix_required": "pivot branch must enter PivotRedlinePlanner before ENABLE_RESCUE_SCORER",
    },
    {
        "component": "rescue_scorer",
        "claimed_role": "B0 rescue scoring and Dragon overlay scoring",
        "actual_source_file": "demo/agent/rescue_scorer.py",
        "actually_called_by_runtime": "yes for rescue variants",
        "changes_candidate_generation": "no",
        "changes_score": "yes",
        "changes_action": "yes via choose",
        "uses_rescue_path": "yes",
        "trace_source": "actual",
        "is_shell": "yes for prior Dragon modules",
        "fix_required": "must not be pivot main sorter",
    },
    {
        "component": "config_variant_switches",
        "claimed_role": "variant routing",
        "actual_source_file": "demo/agent/config.py",
        "actually_called_by_runtime": "yes",
        "changes_candidate_generation": "yes",
        "changes_score": "yes",
        "changes_action": "yes",
        "uses_rescue_path": "yes for historical variants",
        "trace_source": "n/a",
        "is_shell": "yes for Dragon-Orca rescue enablement",
        "fix_required": "pivot variants must keep ENABLE_RESCUE_SCORER false",
    },
    {
        "component": "query_policy",
        "claimed_role": "non-rescue query policy",
        "actual_source_file": "demo/agent/query_policy.py",
        "actually_called_by_runtime": "yes outside rescue; rescue uses query_k wait_lock path",
        "changes_candidate_generation": "yes",
        "changes_score": "no",
        "changes_action": "yes via observed set",
        "uses_rescue_path": "partially",
        "trace_source": "actual",
        "is_shell": "no",
        "fix_required": "pivot uses pivot_redline/query_optimizer.py instead",
    },
    {
        "component": "candidate_generator",
        "claimed_role": "visible cargo candidate generation",
        "actual_source_file": "demo/agent/candidate_generator.py",
        "actually_called_by_runtime": "yes",
        "changes_candidate_generation": "yes",
        "changes_score": "no",
        "changes_action": "yes",
        "uses_rescue_path": "shared utility",
        "trace_source": "actual",
        "is_shell": "no",
        "fix_required": "pivot must add bucketed retention before scoring",
    },
    {
        "component": "preference_monitor",
        "claimed_role": "preference certificate",
        "actual_source_file": "demo/agent/preference_monitor.py",
        "actually_called_by_runtime": "yes",
        "changes_candidate_generation": "no",
        "changes_score": "yes",
        "changes_action": "yes via hard block/score",
        "uses_rescue_path": "shared utility",
        "trace_source": "actual",
        "is_shell": "no",
        "fix_required": "pivot wraps as per-contract debt, not family synthetic status",
    },
    {
        "component": "preference_debt_market",
        "claimed_role": "world debt pricing",
        "actual_source_file": "demo/agent/preference_debt_market.py",
        "actually_called_by_runtime": "yes via world.refresh_world",
        "changes_candidate_generation": "no",
        "changes_score": "yes if consumed",
        "changes_action": "indirect",
        "uses_rescue_path": "shared world utility",
        "trace_source": "actual world field",
        "is_shell": "no",
        "fix_required": "pivot trace must show per-rule/per-contract use",
    },
    {
        "component": "visible_rollout",
        "claimed_role": "two-hop visible value",
        "actual_source_file": "demo/agent/visible_rollout.py",
        "actually_called_by_runtime": "yes in rescue scorer when enabled",
        "changes_candidate_generation": "no",
        "changes_score": "yes",
        "changes_action": "indirect",
        "uses_rescue_path": "yes for Dragon",
        "trace_source": "actual when component nonzero",
        "is_shell": "partial",
        "fix_required": "pivot beam must expose real BeamNode tree",
    },
    {
        "component": "visible_graph_mpc",
        "claimed_role": "online opportunity graph",
        "actual_source_file": "demo/agent/visible_graph_mpc.py",
        "actually_called_by_runtime": "called in rescue path but disabled in sampled Dragon rows",
        "changes_candidate_generation": "no",
        "changes_score": "only when enabled",
        "changes_action": "indirect",
        "uses_rescue_path": "yes",
        "trace_source": "actual/disabled",
        "is_shell": "diagnostic-only in Dragon evidence",
        "fix_required": "pivot online probe must use current visible market only",
    },
    {
        "component": "learned_ranker",
        "claimed_role": "learned ranking",
        "actual_source_file": "demo/agent/learned_ranker.py",
        "actually_called_by_runtime": "not in rescue/Dragon path",
        "changes_candidate_generation": "no",
        "changes_score": "no for Dragon path",
        "changes_action": "no for Dragon path",
        "uses_rescue_path": "no",
        "trace_source": "none in Dragon path",
        "is_shell": "implemented_but_not_active",
        "fix_required": "pivot conservative ranker needs training and full-run ablation before active claim",
    },
    {
        "component": "run_dragon_orca_experiment_grid",
        "claimed_role": "Dragon evidence runner",
        "actual_source_file": "tools/run_dragon_orca_experiment_grid.py",
        "actually_called_by_runtime": "no",
        "changes_candidate_generation": "no",
        "changes_score": "no",
        "changes_action": "no",
        "uses_rescue_path": "summarizes rescue runs",
        "trace_source": "actual plus synthetic fallback counts",
        "is_shell": "yes for some evidence fields",
        "fix_required": "pivot runner must not count fallback/synthetic trace fields",
    },
    {
        "component": "verify_dragon_orca_completion",
        "claimed_role": "Dragon completion gate",
        "actual_source_file": "tools/verify_dragon_orca_completion.py",
        "actually_called_by_runtime": "no",
        "changes_candidate_generation": "no",
        "changes_score": "no",
        "changes_action": "no",
        "uses_rescue_path": "n/a",
        "trace_source": "CSV/report",
        "is_shell": "not pivot-compatible",
        "fix_required": "use verify_pivot_redline_completion.py",
    },
    {
        "component": "evolve_dragon_heuristics",
        "claimed_role": "ReEvo heuristic generation",
        "actual_source_file": "tools/evolve_dragon_heuristics.py",
        "actually_called_by_runtime": "no",
        "changes_candidate_generation": "no",
        "changes_score": "no",
        "changes_action": "no",
        "uses_rescue_path": "n/a",
        "trace_source": "static recipe",
        "is_shell": "yes",
        "fix_required": "pivot evolution must be full-run feedback driven",
    },
    {
        "component": "build_dragon_regret_analyzer",
        "claimed_role": "regret attribution",
        "actual_source_file": "tools/build_dragon_regret_analyzer.py",
        "actually_called_by_runtime": "no",
        "changes_candidate_generation": "no",
        "changes_score": "no",
        "changes_action": "no",
        "uses_rescue_path": "n/a",
        "trace_source": "tool-derived grid formula",
        "is_shell": "yes",
        "fix_required": "pivot regret analyzer must read real action traces/counterfactual labels",
    },
]


def main() -> int:
    common.ensure_dirs()
    rows = [{"stage": "code_audit", **row} for row in CODE_AUDIT_SPECS]
    common.write_csv(common.FORENSICS, rows, common.FORENSICS_FIELDS)
    print({"rows": len(rows), "path": str(common.FORENSICS.relative_to(common.ROOT))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
