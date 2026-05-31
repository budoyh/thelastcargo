# Agent Operating Rules

This file mirrors `AGENTS.md` for tools that look for a lowercase agent rule file.

The durable project memory is in `docs/PROJECT_MEMORY.md`; experiment evidence is in `docs/EXPERIMENT_LOG.md`. `reports/final_audit_report.md` and score-rescue reports are legacy references, not the Next Build final handoff.

Legacy score rescue evidence belongs in the centralized score-rescue reports:
`reports/baseline_comparison.md`, `reports/score_forensic_audit.md`,
`reports/regret_dashboard_v2.md`, `reports/qwen_preference_compile_report.md`,
`reports/score_rescue_ablation.md`, `reports/module_switches_score_rescue.md`,
`reports/subagent_reviews_score_rescue.md` and
`reports/score_rescue_final_report.md`.

For rescue work, do not normalize wait-heavy negative-net behavior into success. The
agent must either meet the hard rescue gate or leave a forensic failure report with
the shortest next path.

## Next Build v4 Long-Lived Rules

- No future information in runtime code.
- No raw data runtime reads and no `server.*` imports in `demo/agent`.
- No driver id, cargo id, location, route, or fixed-coordinate hardcoding.
- Do not copy literal banned terms or example scenario shortcuts into repository files; write `literal banned terms redacted` when the category must be referenced.
- `query_cargo` must be followed by `refresh_world`; filtering, scoring, certificates, and `take_order` must use the post-query `World`.
- `take_order` can only target the current decision's observed `current_actionable` cargo; `no_query` cannot take remembered cargo.
- Destination Shadow Query remains OFF and is not needed for this build.
- Qwen3.5-Flash Preference Compiler is required for non-empty preferences when API access is available. It must use the official port first, then compatible endpoint fallback if needed, cache by preference hash, never print keys, never treat dummy keys as success, and emit DSL/evidence/confidence/repair kinds only.
- Wait is not a fallback. Before waiting, the trace must show why top take and top reposition are worse and what the wait contributes.
- Reports are centralized and limited to five Next Build artifacts: `reports/next_build_final_report.md`, `reports/next_build_experiments.csv`, `reports/score_accountant.csv`, `reports/preference_state_ledger.csv`, and `reports/forensics_samples.csv`.
- Reviewer checks are required after setup, diagnostics, minimal strategy probes, conditional modules, Pareto search, and final stop.
- Stop only as `SCORE_PUSH_SUCCESS`, `SCORE_PUSH_STRONG_SUCCESS`, `DO_NOT_SUBMIT_WITH_FRONTIER_EVIDENCE`, or `EXTERNAL_BLOCKER`.
- `SCORE_PUSH_SUCCESS` requires: 31 days confirmed; 0 simulation failures; 0 income aborts; 0 illegal actions; 0 rejected takes; Score Accountant explains official net and no double penalty; Qwen compile calls are positive when preferences exist; instruction files are complete; final reports are limited to the five Next Build artifacts; branch is committed and pushed; 20260529 official net is at least `40000`; preference penalty is below `25000`; gross-minus-cost retention is explained; 0509 reference is significantly above rescue reference without new failures; Pareto frontier evidence names the regret reduced.
- `SCORE_PUSH_STRONG_SUCCESS` requires all success gates plus 20260529 official net at least `70000`, preference penalty below `15000` or a rule-level unavoidable-penalty explanation, and value-positive reposition or strong no-reposition counterfactual evidence.
- If score thresholds are not met after diagnostics and frontier search, the final status must be `DO_NOT_SUBMIT_WITH_FRONTIER_EVIDENCE`; the first line of `reports/next_build_final_report.md` must be `DO NOT SUBMIT: score-push threshold not reached.`
- Cloud/local compute must stay inside this project, avoid disrupting other users, inspect resource load before heavy jobs, and use GPU only when it materially helps.
