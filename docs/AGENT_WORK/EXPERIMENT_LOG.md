# CROWN-GOLD Contract-MPC Experiment Log

## 2026-06-02 Gold Kickoff

- Branch created and pushed: `crown-gold-contract-mpc`.
- Long prompt adopted as controlling workflow with stop states `CROWN_GOLD_RECOMMENDED_SUBMISSION`, `CROWN_GOLD_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`, and `EXTERNAL_BLOCKER`.
- Previous failure evidence carried forward:
  - PTT full eval had qwen_compile_calls=0 and ptt_compile_calls=0.
  - Exact full eval had Qwen compile/link counts but controller_scored_candidate_count=0 and qwen_auditor_calls=0.
- Working rule: no synthetic pass, Qwen smoke, legal-action count, report completeness, or package shape can substitute for official score and real runtime metrics.

## 2026-06-02 Rescue Reproduction

- Current un-restored `best_rescue` initially matched Exact failure shape on 20260529: official_net -163.93, gross_minus_cost 41296.06, preference_penalty 41460.0.
- Separate historical worktree at `f96786a` reproduced the rescue reference on 20260529: official_net 5067.69, gross_minus_cost 43207.69, preference_penalty 38140.0.
- Current branch restored immutable `best_rescue` behavior:
  - Run: `runs/gold/B0_best_rescue_restored_20260529`
  - official_net 5067.69
  - gross_minus_cost 43207.69
  - preference_penalty 38140.0
  - actions 89 take / 163 wait / 0 reposition
  - rejected/abort/failure observed as 0 in the available run artifacts.

## 2026-06-02 Implementation Evidence

- Default variant changed to `crown_gold_contract_mpc`.
- `best_rescue` and legacy rescue variants keep historical Qwen compiler behavior to preserve B0.
- Gold Preference Contract Compiler emits contract fields and maps them into existing runtime controllers.
- Qwen timeout set to 120 seconds with retry backoff.
- Preference Firewall traces canonical components: marginal penalty, repair value, lost repair-window cost, unknown-soft risk, and Qwen audit adjustment.
- Candidate Auditor reviews high-conflict/top candidates and emits relation/effect/risk/repair/confidence/evidence, not actions.
- Trace output redacts or hashes agent diagnostic driver/candidate/decision ids.
- Tests completed before full Gold run: `python -m compileall demo\agent tests\test_crown_y_core.py` passed; `python -m pytest tests\test_crown_y_core.py -q` reported 57 passed.

## 2026-06-02 Resource Check

- SSH to `yinhhzzu` succeeded.
- Host load was about 421 and multiple GPUs were heavily used, including two GPUs near full memory/high utilization.
- Decision: continue local execution and do not disrupt shared cloud jobs.

## 2026-06-02 Running Gold Evaluation

- Run: `runs/gold/B9_gold_default_20260529`.
- Variant: `crown_gold_contract_mpc`.
- Runtime Qwen: enabled.
- Gold repair and visible-graph MPC: default OFF pending ablation evidence.
- Status at log inspection: full eval was progressing with real Qwen token usage and no observed rejected/abort in the tail.

## 2026-06-02 Gold Final Evidence

- B9 initial schema run failed badly: official_net -8771.94, gross_minus_cost 32788.06, preference_penalty 41560.0.
- After 4096 output tokens and strict Gold schema validation, 20260529 final selected run reached:
  - official_net 6373.17
  - gross_minus_cost 45993.17
  - preference_penalty 39620.0
  - Qwen compile/link/audit 5 / 245 / 245
  - controller_scored_candidate_count 11461
  - candidate_rule_eval_count 52909
  - score_changed_by_controller_count 11461
  - changed_decision_count 240
  - rejected/abort/failure observed as 0
- The real Qwen/controller chain is active, but score gates fail: official_net is below 30000 and preference_penalty is above 28000.
- 20260509 simulation loop completed with 10 drivers, official_net 167347.15, gross_minus_cost 167347.14, and preference_penalty 0.0, but official monthly income calculation aborted for 2 drivers. This is not clean no-regression evidence.
- 20260509 exposed old Qwen total caps: qwen_budget_exhausted_count 1592. Gold default total linker/auditor budgets were raised to 4096 afterward.
- Strict Gold contract validation was tightened after final reviewer found malformed contracts could pass field-presence-only checks.
- Linker and auditor were routed through shared Qwen retry/fallback order after final reviewer found they did not share the compiler's compatibility path.
- Injected Qwen API priority was fixed so dummy/local compatible endpoint state cannot block an available injected `SimulationApiPort.model_chat_completion`.
- Gold contract schema now rejects model-reported `severity.source='explicit'` penalty provenance.
- Old package zips were moved out of `submissions/`; no Gold submission package was generated.
- Package builder now requires explicit `--recommended` or `--not-recommended` to avoid accidental zip creation after failed gates.
- No Gold submission package was generated. Stop state is `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`.
