# CROWN-TRIDENT / GOLD-2 Execution Plan

## Stop States

- `CROWN_TRIDENT_RECOMMENDED_SUBMISSION`: recommended score, Qwen, controller, ablation, compliance, reviewer, package, commit, and push gates pass.
- `CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION`: experimental gates pass without pretending recommendation.
- `DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE`: hard gates fail after complete evidence; no submission-shaped package if below experimental gate.
- `EXTERNAL_BLOCKER_QWEN`: real Qwen is unavailable for all relevant full runs.
- `EXTERNAL_BLOCKER_RESCUE_CORE`: required runner/data/eval infrastructure prevents B0 rescue reproduction.
- `EXTERNAL_BLOCKER_EVAL_INFRA`: official-style evaluation cannot run for infrastructure reasons.
- `DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE`: required real subagents or recorded named reviewer passes cannot be completed.

## Score Gates

- B0 rescue: 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected.
- Experimental: 20260529 official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 50000, 0 abort/illegal/rejected, nonzero auditor adjustment if auditor used, and clean controller/ablation evidence.
- Recommended: 20260529 official_net >= 38000, preference_penalty <= 22000, gross_minus_cost >= 60000, 0 abort/illegal/rejected, and 0509 clean enough for sanity.
- Crown target: official_net >= 40000, preference_penalty around 18000-22000 or lower, and gross_minus_cost around 58000-65000 or higher.

## Work Order

1. Create and push branch `crown-trident-gold2`.
2. Update persistent project rules and work records before runtime code changes.
3. Launch six required subagents/reviewer passes with disjoint ownership where possible.
4. Restore and verify immutable `best_rescue` as B0.
5. Inventory existing variants, runners, reports, and run artifacts; map equivalent commands to required Trident wrappers.
6. Implement missing Trident tools only when equivalent project commands do not exist.
7. Stage 0: reproduce score accounting table and confirm official_net = gross_minus_cost - preference_penalty.
8. Stage 1-2: generate rule ledger and changed-decision deltas before final strategy tuning.
9. Stage 3-5: implement Preference Contract V2, Qwen numeric auditor effect, and scorer microprobe alignment.
10. Stage 6-7: run B0-B11 ablations and rule doctor treatments.
11. Stage 8-10: distill high-score generic statistics, implement runtime-only graph if useful, and run parameter search.
12. Stage 11: select smallest score-positive final variant, build final reports, run verification, commit, push, and package only if gates allow.

## Required Commands Or Equivalents

- `python -m pytest tests -q`
- `python -m compileall demo tools tests`
- `python tools/audit_guard.py --fail-on-p0`
- `python tools/fix_eval_round_bug.py`
- `python tools/qwen_preference_smoke_test.py`
- `python tools/run_trident_baselines.py --simulation-days 31`
- `python tools/build_trident_penalty_ledger.py --simulation-days 31`
- `python tools/build_trident_decision_deltas.py --simulation-days 31`
- `python tools/run_trident_ablation_matrix.py --simulation-days 31`
- `python tools/run_trident_param_search.py --trials 100`
- `python tools/build_trident_reports.py`

If a required command is missing, implement it or record the exact equivalent command and output.

## Current Progress

- Branch `crown-trident-gold2` was created and pushed to origin.
- Long prompt and previous Gold project rules were read.
- Persistent Trident rules were written to `AGENTS.md`, `agent.md`, `docs/AGENT_WORK/PROJECT_MEMORY.md`, `docs/AGENT_WORK/EXPERIMENT_LOG.md`, and `docs/AGENT_WORK/EXECUTION_PLAN.md`.

## Keep/Kill Policy

- Keep only generic, non-driver-specific parameters and modules with official score-positive evidence or clear named regret reduction.
- Disable controllers, auditor adjustments, graph parameters, or repair bonuses that worsen official_net or are negative-delta dominated.
- Never hard-block or apply massive penalties without scorer-semantics alignment.
- Never use dummy keys, disabled runtime Qwen, smoke tests, synthetic tests, package shape, or zero-illegal status as success.

## Report / Package Policy

- Final reports are limited to `trident_final_report.md`, `trident_experiments.csv`, `trident_rule_ledger.csv`, `trident_decision_deltas.csv`, and `trident_qwen_effect.csv`.
- If final official_net < 30000, the final report begins with `DO NOT SUBMIT: <precise reason>` and no submission-shaped zip is created.
- If a package is generated, inspect root and exclusions before any submission claim.
