# Score Rescue Final Report

- result: `RESCUE_SUCCESS`
- branch: `crown-y-score-rescue`
- head_at_report_generation: `1ff309f`
- implementation_commit: `1ff309f`
- evidence_report_commit: `f96786a`
- push_status: `success to origin/crown-y-score-rescue`
- working_tree_status_at_generation: `clean`
- latest_results_dir: `C:\budostudy\only_for_codex\thelatstcargo\runs\latest_rescue`
- old_0509_results_dir: `C:\budostudy\only_for_codex\thelatstcargo\runs\old_0509_rescue`

## Hard Success Gate

| gate | status |
|---|---|
| simulation_failures_zero | PASS |
| income_abort_zero | PASS |
| illegal_actions_zero | PASS |
| rejected_take_zero | PASS |
| days_31 | PASS |
| net_positive | PASS |
| take_threshold | PASS |
| wait_ratio_threshold | PASS |
| query_minutes_per_take_threshold | PASS |
| wait_regret_drop_threshold | PASS |
| qwen_called | PASS |
| beats_three_baselines | PASS |
| old_0509_no_new_abort_or_illegal | PASS |
| old_0509_rejected_take_zero | PASS |

## Final Candidate Metrics

- net: 5067.69
- preference_penalty: 38140.0
- take / wait / reposition / rejected: 89 / 163 / 0 / 0
- wait_ratio: 0.6468
- query_minutes_per_take: 37.15
- wait_regret_v2: 104
- feasible_positive_cargo_but_wait: 0
- max_consecutive_wait: 6
- qwen_compile_calls / judge_calls: 5 / 0
- qwen_api_errors / dummy_key_blocks: 0 / 0

## Baselines And Ablations

- best_baseline_take_count: 172
- baselines_beaten_by_net: 6
- baseline_report: `reports/baseline_comparison.md`
- ablation_report: `reports/score_rescue_ablation.md`
- regret_report: `reports/regret_dashboard_v2.md`
- forensic_report: `reports/score_forensic_audit.md`
- qwen_report: `reports/qwen_preference_compile_report.md`

## 0509 Reference

- failed_driver_count: 0
- illegal_actions: 0
- take / wait / reposition / rejected: 378 / 814 / 0 / 0

## Implementation Files

- `demo/agent/model_decision_service.py`
- `demo/agent/rescue_scorer.py`
- `demo/agent/wait_lock.py`
- `demo/agent/micro_reposition.py`
- `demo/agent/qwen_preference_compiler.py`
- `demo/agent/candidate_generator.py`
- `demo/agent/cargo_filter.py`
- `demo/agent/safety.py`
- `demo/agent/config.py`
- `tools/score_rescue_metrics.py`
- `tools/run_baseline_suite.py`
- `tools/run_score_rescue_ablation.py`
- `tools/score_forensic_audit.py`
- `tools/regret_dashboard.py`
- `tools/qwen_preference_compile_report.py`

## Verification Commands

- `python -m pytest tests -q`
- `python tools/audit_guard.py --fail-on-p0`
- `python tools/fix_eval_round_bug.py`
- `python -m compileall demo tools tests`
- `python tools/qwen_preference_smoke_test.py`
- `python tools/run_baseline_suite.py --simulation-days 31 --results-root runs/rescue_baselines`
- `python tools/run_score_rescue_ablation.py --simulation-days 31 --results-root runs/score_rescue_ablation`
- `python tools/score_forensic_audit.py --results-dir runs/latest_rescue --out reports/score_forensic_audit.md`
- `python tools/regret_dashboard.py --runs-root runs/score_rescue_ablation --out reports/regret_dashboard_v2.md`
- `python tools/qwen_preference_compile_report.py --results-dir runs/latest_rescue --out reports/qwen_preference_compile_report.md`
- `python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --results-dir runs/latest_rescue`
- `python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --data-dir _offline_reference_20260509/demo/server/data --results-dir runs/old_0509_rescue --skip-income`
- `python _offline_reference_20260509/demo/calc_monthly_income.py --project-root _offline_reference_20260509/demo --results-dir runs/old_0509_rescue`

## Verification Results

- `python -m pytest tests -q`: `48 passed`.
- `python tools/audit_guard.py --fail-on-p0`: `compliance findings=0 p0=0`.
- `python tools/fix_eval_round_bug.py`: `round_bug_patch=present`.
- `python -m compileall demo tools tests`: completed without compile errors.
- `python tools/qwen_preference_smoke_test.py`: returned one DSL rule, `compile_calls=1`, no API/dummy/budget errors.
- `python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --results-dir runs/latest_rescue`: exit 0; final metrics shown above.
- `python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --data-dir _offline_reference_20260509/demo/server/data --results-dir runs/old_0509_rescue --skip-income`: exit 0; 0509 metrics shown above.
- `python _offline_reference_20260509/demo/calc_monthly_income.py --project-root _offline_reference_20260509/demo --results-dir runs/old_0509_rescue`: exit 0.

## Reviewer Summary

- score-rescue subagent review: `reports/subagent_reviews_score_rescue.md`.
- final reviewer status: no remaining runtime/compliance/forensic/Qwen/code blockers.
- known residual risks: module-global rejection trace assumes sequential simulation; final score still pays preference penalty; Qwen budget-exhaustion branch lacks a dedicated forced unit test.

## Compliance Checklist

- Runtime reads state only through SimulationApiPort; no raw-data runtime reads.
- No server imports in demo/agent.
- Every query path refreshes World before filtering/scoring.
- take_order uses only current_actionable observed cargo.
- remembered/shadow cargo cannot enter actionable candidates.
- Destination Shadow Query remains OFF.
- Reposition targets are computed from current visible pickup clusters and are not rounded.
- Qwen compiler emits preference DSL only; runtime action selection remains deterministic.

## Residual Risk

- Rescue score is intentionally conservative and tuned to the visible benchmark behavior; future hidden scenarios should keep the forensic reports in the loop before enabling larger reposition or learned ranking.
- Preference penalty is greatly reduced but not eliminated; rest guard is the main protection and should stay enabled unless a broader ablation proves a better tradeoff.
