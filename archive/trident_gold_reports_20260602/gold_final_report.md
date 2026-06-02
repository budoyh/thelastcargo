DO NOT SUBMIT: gold gates not reached.

# CROWN-GOLD Final Evidence

Stop state: DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE.

## Score Gates

- 20260529 final selected run: official_net 6373.17, gross_minus_cost 45993.17, preference_penalty 39620.0.
- Recommended gate requires official_net >= 40000, preference_penalty <= 22000, gross_minus_cost >= 52000: FAIL.
- Experimental gate requires official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 45000: FAIL.
- Historical rescue B0 was restored: official_net 5067.69, gross_minus_cost 43207.69, preference_penalty 38140.0.
- 20260509 regression run: official_net 167347.15, gross_minus_cost 167347.14, preference_penalty 0.0, income calculation aborts 2. This is not clean non-catastrophic-regression evidence.

## Real Qwen And Controller Evidence

- 20260529 Qwen compile/link/audit: 5 / 245 / 245.
- 20260529 Qwen fallback/api_error/timeout: 0 / 0 / 0.
- 20260529 controller_scored_candidate_count: 11461.
- 20260529 candidate_rule_eval_count: 52909.
- 20260529 score_changed_by_controller_count: 11461.
- 20260529 changed_decision_count: 240.
- These meet the real-chain hard metrics, but the score/penalty gates fail.

## Implementation Summary

- Default variant is `crown_gold_contract_mpc`.
- Restored immutable `best_rescue` behavior for B0.
- Added Gold Preference Contract schema validation and contract-to-controller bridge.
- Added Qwen retry/backoff with 120 second timeout and 4096 output tokens.
- Added Observed Vocabulary Linker, top-candidate Auditor, and firewall score components before profit ranking.
- Added hashed/redacted decision and macro traces.
- Fixed non-default scout-then-deepen current-actionable boundary so final candidates use the latest post-query observation set.
- Raised Gold Qwen linker/auditor total-budget defaults to 4096 after the 0509 multi-driver run exposed old cap exhaustion.
- Added stricter Gold contract schema checks and shared Qwen completion retry/fallback order for compiler/linker/auditor paths.
- Fixed Qwen API priority so injected `SimulationApiPort.model_chat_completion` is tried before dummy/local compatible endpoint state can block execution.
- Rejected model-reported `severity.source='explicit'` penalty provenance in Gold contract validation.
- Added recursive trace payload sanitization for diagnostic ids in option trace payloads.

## Package Decision

No Gold submission zip was generated. Because the 20260529 score is below experimental gates, creating a submission-shaped package would violate the Gold stop rules.

## Residual Risks

- B1-B8 full ablations were not completed as separate official runs after B9 failed the score gate; `gold_experiments.csv` records this explicitly.
- Visible Opportunity Graph MPC remains default OFF because no positive official-net or penalty-reduction ablation was proven.
- 0509 was run before raising the Gold total Qwen budget constants, and official monthly income calculation aborted for 2 drivers. Treat it as failure evidence, not clean regression evidence or package evidence.
- Raw local run outputs remain under ignored `runs/` as evidence artifacts and may contain benchmark-emitted ids/literals. They are not included in reports or package output, and no Gold package was generated.
