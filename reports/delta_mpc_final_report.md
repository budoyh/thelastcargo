DO NOT SUBMIT: Delta-MPC target not reached.

# CROWN-Delta MPC Final Report

- stop_state: DO_NOT_SUBMIT_WITH_DELTA_EVIDENCE
- recommendation: official-scorer delta labels incomplete
- branch: crown-delta-mpc
- commit: generated before final handoff commit; see git history for exact submitted commit
- final_reports: delta_mpc_final_report.md, delta_mpc_experiments.csv, delta_mpc_labels.csv, delta_mpc_automata_eval.csv, delta_mpc_forensics.csv
- protected_literal_audit: no literal list committed; repository uses redacted placeholders only

## Score Accounting

- Confirmed official net is gross_minus_cost minus preference_penalty; double-penalty proxy is forbidden.
- Best runtime 20260529 row: rescue_reference official_net=5067.69, gross_minus_cost=43207.69, preference_penalty=38140.0.
- Best Delta-MPC 20260529 row: delta_mpc_fallback official_net=-5112.02, gross_minus_cost=41347.98, preference_penalty=46460.0, macro_completed=32.
- Best offline diagnostic 20260529 frontier: money_trajectory_repair official_net=35849.85; this is not a runtime submit result.

## Baselines And Ablations

| dataset | variant | official_net | gross_minus_cost | preference_penalty | take_count | wait_count | reposition_count | macro_completed_count | notes |
|---|---|---|---|---|---|---|---|---|---|
| 20260529 | rescue_reference | 5067.69 | 43207.69 | 38140.0 | 89 | 163 | 0 | 0 | prior rescue reference |
| 20260529 | pce_final | -3125.02 | 34114.98 | 37240.0 | 117 | 199 | 0 | 0 | prior PCE failure |
| 20260529 | strict_pref | 2240.98 | 38900.98 | 36660.0 | 73 | 180 | 0 | 0 | strict preference reference |
| 20260529 | money_greedy_no_pref | -122937.49 | 77602.52 | 200540.0 | 144 | 6 | 0 | 0 | diagnostic gross reference |
| 20260529 | money_trajectory_repair | 35849.85 | 53169.85 | 17320.0 | 69 | 147 | 0 | 0 | offline diagnostic repair frontier |
| 20260529 | visibility_k600_oracle | 30960.95 | 48400.96 | 17440.0 | 63 | 146 | 0 | 0 | online visibility oracle diagnostic |
| 20260509 | strict_pref | 93518.61 | 195318.63 | 101800.0 | 422 | 866 | 0 | 0 | 0509 sanity reference |
| 20260509 | money_greedy_no_pref | 220151.2 | 388361.25 | 168210.0 | 740 | 70 | 0 | 0 | 0509 money diagnostic |
| 20260529 | best_rescue | 5067.69 | 43207.69 | 38140.0 | 89 | 163 | 0 | 0 | delta_mpc_ablation |
| 20260529 | delta_mpc_delta_only | -91646.84 | 62633.16 | 154280.0 | 124 | 60 | 0 | 29 | delta_mpc_ablation |
| 20260529 | delta_mpc_macro | -10620.7 | 35299.31 | 45920.0 | 109 | 259 | 0 | 31 | delta_mpc_ablation |
| 20260529 | delta_mpc_fallback | -5112.02 | 41347.98 | 46460.0 | 86 | 186 | 1 | 32 | delta_mpc_ablation |
| 20260509 | best_rescue |  |  |  |  |  |  |  | missing_run |
| 20260509 | delta_mpc_delta_only |  |  |  |  |  |  |  | missing_run |
| 20260509 | delta_mpc_macro |  |  |  |  |  |  |  | missing_run |
| 20260509 | delta_mpc_fallback | 102265.64 | 201985.65 | 99720.0 | 423 | 821 | 0 | 31 | delta_mpc_ablation |

## Delta Labels

- labels_total: 103
- exact_official_labels: 3
- replay_or_heuristic_labels: 100
- Label validity fields include exact official flag, replay validity, continuation policy, visibility, legality, state compatibility, and confidence.
- Approximate replay labels are diagnostic only and do not pass the strong gate.

## Preference Automata

| automaton_type | label_count | high_penalty_recall | unknown_rate | official_net_delta_if_enabled | keep_or_disable |
|---|---|---|---|---|---|
| continuous_or_scheduled_rest | 103 | 0.45 | 0.25 | 0.0 | disable_high_lambda |
| full_inactive_day | 103 | 0.5 | 0.23 | 0.0 | disable_high_lambda |
| cargo_field_avoid_or_require | 103 | 0.55 | 0.21 | 0.0 | disable_high_lambda |
| cargo_field_quota_or_distinct_day | 103 | 0.6 | 0.19 | 0.0 | disable_high_lambda |
| pickup_or_haul_distance_limit | 103 | 0.65 | 0.17 | 0.0 | disable_high_lambda |
| date_location_visit_or_dwell | 103 | 0.7 | 0.15 | 0.0 | disable_high_lambda |
| ordered_target_or_route_like_task | 101 | 0.0 | 0.75 | 0.0 | disable_runtime |
| region_or_location_avoid_or_require | 101 | 0.0 | 0.75 | 0.0 | disable_runtime |
| unknown_soft | 101 | 0.0 | 1.0 | 0.0 | keep_soft_only |

## Macro And Scorer

- Runtime now has macro commitment state for no-query rest, full inactive day, target/dwell reposition, wait-at-target, and escape-style reposition candidates.
- Every traced decision can expose top-5 Delta-MPC decomposition with freight, route, terminal, macro repair, preference cost, lost window, time/query/reposition cost, execution risk, low-confidence risk, and final score.
- forensics_rows: 500

## Terminal And Ranker

- Terminal value and learned ranker remain disabled unless official-net ablation proves positive. No black-box route or coordinate model was deployed.

## Qwen

- Qwen role remains compiler/linker/auditor only. It does not output final actions.
- Qwen smoke test completed with compile_calls=1 and rules_returned=1 when a non-empty preference was present.
- Missing or dummy key paths are fallback evidence and not success.

## Reviewer Findings

- Prompt adherence reviewer: long prompt and emergency patch were followed; stop state remains score-gated.
- Compliance reviewer: no P0 runtime boundary violation found; Qwen HTTP fallback is a low-risk project-allowed fallback; final reports must not copy raw trace cargo ids.
- Evaluation reviewer: dedicated Delta-MPC scripts were added because required commands were absent.
- Official-delta reviewer: exact run-pair labels exist, but action-level labels remain replay/heuristic approximations.
- Runtime planner reviewer: macro candidates and commitments now enter runtime; score target still requires 31-day evidence.

## Remaining Risks

- Strong public score target may exceed the best known public offline repair frontier.
- Current labels are not yet enough for learned terminal value.
- Macro commitments entered runtime, but the measured Delta-MPC variants did not produce positive official-net delta over the rescue reference.
- The active bottleneck is official-scorer action-level delta evidence: exact run-pair labels exist, while most action labels are still replay/heuristic diagnostics.

## Commands Run

- python tools/run_delta_mpc_baselines.py --simulation-days 31
- python tools/build_official_delta_labels.py --simulation-days 31
- python tools/evaluate_preference_automata.py
- python tools/run_delta_mpc_ablation.py --simulation-days 31
- python tools/run_delta_mpc_ablation.py --simulation-days 31 --execute --datasets 20260529 --variants delta_mpc_macro
- python tools/run_delta_mpc_ablation.py --simulation-days 31 --execute --datasets 20260529 --variants delta_mpc_fallback delta_mpc_delta_only
- python tools/run_delta_mpc_ablation.py --simulation-days 31 --execute --datasets 20260509 --variants delta_mpc_fallback
- python tools/delta_mpc_synthetic_paraphrase_tests.py
- python tools/qwen_preference_smoke_test.py
- python -m pytest tests -q
- python tools/audit_guard.py --fail-on-p0
- python tools/fix_eval_round_bug.py
- python tools/build_delta_mpc_reports.py
