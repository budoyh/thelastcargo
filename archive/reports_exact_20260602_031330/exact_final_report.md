DO NOT SUBMIT: gates not reached.
stop_state: DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE

# CROWN-EXACT Final Report

- branch: crown-exact-rbt-mpc
- submit_recommendation: no
- default_variant: crown_exact_rbt_mpc
- package_path: C:\budostudy\only_for_codex\thelatstcargo\runs\packages\crown_exact_NOT_RECOMMENDED_DO_NOT_SUBMIT.zip
- package_sha256: e74c6afe777c1bd70bd4d549e4a740cd839fa54156093cb03924d524fee62780
- package_recommended: False
- package_disallowed_entries: 0

## 20260529 Final
- official_net: -163.93
- gross_minus_cost: 41296.06
- preference_penalty: 41460.0
- qwen_compile_or_cache_hit_count: 521
- qwen_link_or_cache_hit_count: 486
- qwen_audit_or_cache_hit_count: 0
- qwen_token_usage_total: 402988
- qwen_api_errors: 7
- qwen_fallbacks: 109
- controller_scored_candidate_count: 0

## 20260509 Regression
- official_net: 86900.14
- gross_minus_cost: 185150.15
- preference_penalty: 98250.0
- simulation_failures: 0

## 20260529 Score Table
| variant | official_net | gross_minus_cost | preference_penalty | qwen_compile_or_cache | controller_scored | notes |
|---|---:|---:|---:|---:|---:|---|
| best_rescue | 5067.69 | 43207.69 | 38140.0 | 7 | 0 | baseline |
| best_rescue_current_code | -163.93 | 41296.06 | 41460.0 | 7 | 0 | current-code reproduction |
| ptt_previous | -8635.06 | 33364.94 | 42000.0 | 609 | 8696 | failed previous PTT |
| money_greedy_no_pref | -122937.49 | 77602.52 | 200540.0 | 7 | 0 | baseline |
| strict_pref | 2240.98 | 38900.98 | 36660.0 | 7 | 0 | baseline |
| safe_profit_greedy | -113176.86 | 79603.13 | 192780.0 | 0 | 0 | baseline |
| crown_exact_rbt_mpc | -163.93 | 41296.06 | 41460.0 | 521 | 0 | final selected exact |

## RBT And Qwen Evidence
- qwen_compile_calls: 12
- qwen_cache_hits: 0
- ptt_compile_calls: 5
- ptt_cache_hits: 504
- qwen_linker_calls: 243
- schema_valid_rbt_observed: 0; bytecode coverage includes fallback/monthly-rule mappings and is not claimed as schema-valid Qwen RBT.
- qwen_auditor_calls: 0; gated auditor was disabled in the final selected strategy after negative score evidence.

## Ablation Summary
- PTT previous remained below rescue and had zero Qwen compile in the imported failed evidence.
- Exact RBT/linker default produced real Qwen calls but did not improve 20260529 official_net or penalty.
- 90-minute wait / 08:00 rest numeric probe worsened official_net to -20415.93 and penalty to 62680.0, so it was reverted.
- Visible Graph MPC stayed default OFF because no positive official_net evidence was produced.

## Commit And Push
- final_commit: reported in final handoff after this report is committed.
- final_push: reported in final handoff after `git push` succeeds.

## Gates
- score_0529_official_net: FAIL
- score_0529_penalty: FAIL
- score_0529_gross: FAIL
- qwen_compile_or_cache: PASS
- controller_scored_candidates: FAIL
- scorer_semantics_aligned: PASS
- p0_clean: PASS
- 0509_no_catastrophic_regression: PASS
- package_default_variant: PASS
- package_shape: PASS

## Evidence Summary
- scorer_semantics_probe rows/aligned/enabled_hard: 10/9/2
- rule_bytecode_coverage rows: 46
- official_net accounting uses gross_minus_cost - preference_penalty; double-count proxy is forbidden.
- Previous PTT failure addressed by requiring real Qwen/cache counts, bytecode coverage, scorer probe, and controller scoring evidence.

## Residual Risks
- score_0529_official_net
- score_0529_penalty
- score_0529_gross
- controller_scored_candidates
