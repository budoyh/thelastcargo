# CROWN-EXACT RBT-MPC Execution Plan

## Stop States

- `CROWN_EXACT_RECOMMENDED_SUBMISSION`: all score, Qwen, semantics, compliance, reviewer, package, commit, and push gates pass.
- `CROWN_EXACT_EXPERIMENTAL_SUBMISSION`: explicit experimental gates pass without pretending recommendation.
- `DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE`: one or more hard gates fail and the final report explains the evidence.
- `EXTERNAL_BLOCKER`: required external service or true reviewer capability is unavailable.

## Recommended Submission Gates

- 20260529 official_net >= 30000.
- 20260529 preference_penalty <= 22000.
- 20260529 gross_minus_cost >= 45000.
- Full eval has real Qwen compile/cache evidence for non-empty preferences.
- Controller scored candidates > 0 and scorer-semantics aligned controller evidence > 0.
- P0 compliance clean: no raw data reads, no server/bench/scorer imports in runtime, no future cargo, current-actionable take only.
- 20260509 has no catastrophic regression.
- Package audit confirms root `demo/`, default variant `crown_exact_rbt_mpc`, and no disallowed entries.
- Reviewer subagents return PASS or their failures are recorded as DO_NOT evidence.

## Work Order

1. Keep `best_rescue` legality core as the base; add `crown_exact_rbt_mpc` as the default runtime/package variant.
2. Archive non-exact final reports and keep `reports/` limited to five exact files.
3. Add/maintain CROWN-EXACT long-lived records in `AGENTS.md`, `agent.md`, and `docs/AGENT_WORK/*`.
4. Run Stage 0 baseline table for rescue, previous PTT, money-greedy, strict-pref, and safe-profit.
5. Run scorer semantics probe and downgrade any unaligned semantics to soft risk.
6. Run real Qwen RBT compile/cache and observed-vocabulary linking in full eval; do not use smoke as a substitute.
7. Keep Candidate Auditor, controller scoring, and Visible Graph MPC default OFF unless ablation improves official score or materially reduces penalty without gross collapse.
8. Run 20260529 and 20260509 31-day exact evaluations with runtime Qwen enabled.
9. Build package audit; if score gates fail, only produce `NOT_RECOMMENDED_DO_NOT_SUBMIT` inspection zip.
10. Build final five exact reports, run reviewers, commit, and push.

## Current Result

- Final selected exact strategy did not reach recommendation or experimental gates.
- 20260529 exact: official_net -163.93, gross_minus_cost 41296.06, preference_penalty 41460.0.
- 20260509 exact: official_net 86900.14, simulation_failures 0.
- Real Qwen compile/link evidence exists, but auditor/controller scoring and schema-valid Qwen RBT evidence are insufficient.
- Current stop state is `DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE`; the package is an inspection package only.

## Keep/Kill Policy

- Keep only generic, non-driver-specific parameters and modules with official score evidence.
- Disable modules that reduce official_net below rescue without materially reducing preference_penalty.
- Never hard-block or apply massive penalties without scorer-semantics alignment.
- Never use dummy keys, disabled runtime Qwen, synthetic tests, package shape, or zero-illegal status as success.
