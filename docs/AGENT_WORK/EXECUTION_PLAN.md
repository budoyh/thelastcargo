# CROWN-GOLD Contract-MPC Execution Plan

## Stop States

- `CROWN_GOLD_RECOMMENDED_SUBMISSION`: all score, Qwen, controller, compliance, reviewer, package, commit, and push gates pass.
- `CROWN_GOLD_EXPERIMENTAL_SUBMISSION`: explicit experimental gates pass without pretending recommendation.
- `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`: one or more hard gates fail and the final report explains the evidence.
- `EXTERNAL_BLOCKER`: required external service, true reviewer capability, or runnable official local evaluation is unavailable.

## Recommended Submission Gates

- 20260529 official_net >= 40000.
- 20260529 preference_penalty <= 22000.
- 20260529 gross_minus_cost >= 52000.
- Real Qwen compile/link/audit > 0; runtime Qwen must not be disabled.
- controller_scored_candidate_count > 1000.
- candidate_rule_eval_count > 1000.
- score_changed_by_controller_count > 100.
- changed_decision_count > 20.
- 0 simulation failure, abort, illegal, rejected.
- 20260509 has no catastrophic regression.
- Package audit confirms root `demo/`, default variant `crown_gold_contract_mpc`, and no disallowed entries.
- Reviewer subagents return PASS or their failures are recorded as DO_NOT evidence.

## Experimental Gates

- 20260529 official_net >= 30000.
- 20260529 preference_penalty <= 28000.
- 20260529 gross_minus_cost >= 45000.
- All Qwen, controller, compliance, reviewer, default-variant, and package gates pass.

## Work Order

1. Create and push branch `crown-gold-contract-mpc`.
2. Restore immutable `best_rescue` core and verify 20260529 historical rescue reference.
3. Add `crown_gold_contract_mpc` as default variant without changing `best_rescue` behavior.
4. Implement/verify real Qwen Preference Contract Compiler, Observed Vocabulary Linker, Candidate Auditor, and Preference Firewall score components.
5. Keep repair and visible-graph MPC default OFF until ablation proves they help without gross collapse.
6. Run 20260529 Gold full eval with runtime Qwen enabled.
7. Run 20260509 non-catastrophic check when practical.
8. Archive old Exact reports and keep `reports/` limited to the five Gold artifacts.
9. Run compile/test/audit guard/Qwen evidence checks.
10. Run real reviewers, fix actionable blockers when feasible, then commit and push.

## Current Progress

- Branch `crown-gold-contract-mpc` was created and pushed.
- Historical rescue worktree `f96786a` reproduced 20260529 official_net 5067.69, preference_penalty 38140.0.
- Current branch restored `best_rescue` to the same 20260529 result: official_net 5067.69, preference_penalty 38140.0, 89 take / 163 wait / 0 reposition.
- `crown_gold_contract_mpc` is the default variant and keeps runtime Qwen enabled.
- Cloud host was checked and skipped because high shared load made local continuation safer.
- B9 Gold 20260529 full eval completed with real Qwen calls and controller scoring, but failed score gates:
  - official_net 6373.17
  - gross_minus_cost 45993.17
  - preference_penalty 39620.0
  - Qwen compile/link/audit 5 / 245 / 245
  - controller_scored_candidate_count 11461
  - changed_decision_count 240
- 20260509 simulation loop completed with official_net 167347.15 and preference_penalty 0.0, but official monthly income calculation aborted for 2 drivers. This does not satisfy a clean no-regression gate.
- Final reports were written under `reports/`; no Gold submission zip was generated.
- Final reviewer issues fixed where practical: 0509 abort reporting, strict Gold schema validation, injected API priority before dummy key state, linker/auditor retry/fallback path, explicit penalty-source rejection, recursive trace id sanitization, old `submissions/` zip archival, and explicit package build gating.
- Current stop state: `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`.

## Keep/Kill Policy

- Keep only generic, non-driver-specific parameters and modules with official score evidence.
- Disable modules that reduce official_net below rescue without materially reducing preference_penalty.
- Never hard-block or apply massive penalties without scorer-semantics alignment.
- Never use dummy keys, disabled runtime Qwen, synthetic tests, package shape, or zero-illegal status as success.
