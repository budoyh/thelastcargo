# EXPERIMENT LOG

## EXP-007 Next Build v4 Start

- branch: `crown-y-next-build`
- start point: `crown-y-score-rescue` commit `0f2af10`
- rescue baseline reference: 20260529 net `5067.69`, preference penalty `38140.0`, take/wait/reposition `89/163/0`, wait ratio `0.6468`, Qwen compile calls `5`.
- stage order: setup guardrails, four diagnostics, six minimal strategies, conditional module only for the largest named regret, compact Pareto frontier, final verification.
- final score gate: official net under `40000` must be reported as `DO_NOT_SUBMIT_WITH_FRONTIER_EVIDENCE`.
- final artifacts: `reports/next_build_final_report.md`, `reports/next_build_experiments.csv`, `reports/score_accountant.csv`, `reports/preference_state_ledger.csv`, `reports/forensics_samples.csv`.
- existing report files from older branches are legacy references; Next Build must not add reports outside the five v4 artifacts.

## EXP-006 Score Rescue Workstream

- branch: `crown-y-score-rescue`
- baseline failure reference: 20260529 31-day run had net `-18953.97`, preference penalty `24700`, take `13`, wait `1806`, query minutes `8499`, wait_regret `1797`, Qwen runtime calls `0`.
- implemented rescue line: SafeProfitGreedy query, post-query World refresh, RescueScorer, wait-lock forensic trace, repeated-wait loop breaker, current-visible micro-reposition candidate, capped soft preference/time/two-hop scoring, Qwen preference DSL compiler.
- final evidence files: `reports/baseline_comparison.md`, `reports/score_rescue_ablation.md`, `reports/score_forensic_audit.md`, `reports/regret_dashboard_v2.md`, `reports/qwen_preference_compile_report.md`, `reports/subagent_reviews_score_rescue.md`, `reports/score_rescue_final_report.md`.
- final result is determined only by `reports/score_rescue_final_report.md`; negative-net or wait-heavy rescue variants remain forensic failures.

## EXP-001 Unit and Compliance Baseline

- time: 2026-05-31 local
- commit: pending until final commit
- command: `python -m pytest tests -q`
- result: 33 passed
- command: `python tools/audit_guard.py --fail-on-p0`
- result: 0 findings, 0 P0
- command: `python tools/fix_eval_round_bug.py`
- result: round bug patch present

## EXP-002 20260529 Final Default

- command: `python tools/run_local_eval.py --simulation-days 31 --results-dir runs/latest`
- result: 2 drivers, 1819 steps, 31 days, 0 simulation failures, 0 income calculation aborts, 0 rejected take.
- score proxy: total net income `-18953.97`; preference penalty `24700.0`; token usage `0`.
- actions: take `13`, wait `1806`, reposition `0`.
- regret: query too big `0`, query too small `25`, long-order trap `2`, wait regret `1797`, reposition not recovered `0`, preference late panic `0`.
- conclusion: legal and stable; repeated wait remains the main scoring risk.

## EXP-003 Module Ablations On 20260529

| run | command / switch | net | penalty | failed | rejected_take | action mix |
|---|---|---:|---:|---:|---:|---|
| baseline | `--variant baseline` | -94825.77 | 172760.0 | 0 | 4 | 154 take / 146 wait / 0 reposition |
| no_time_shadow | `--variant no_time_shadow` | -101012.95 | 177520.0 | 0 | 2 | 151 take / 186 wait / 0 reposition |
| no_rollout | `--variant no_rollout` | -19637.96 | 26620.0 | 0 | 0 | 14 take / 1791 wait / 0 reposition |
| scout_enabled | `CROWN_Y_ENABLE_SCOUT_THEN_DEEPEN=1` | -19239.4 | 26300.0 | 0 | 0 | 15 take / 1637 wait / 0 reposition |
| reposition_enabled | `CROWN_Y_ENABLE_REPOSITION=1` | -18953.97 | 24700.0 | 0 | 0 | 13 take / 1806 wait / 0 reposition |

- decision: keep Time Shadow and Visible two-hop; disable Scout and Reposition by default; keep Learned Ranker and LLM Judge off.

## EXP-004 Stability And Perturbation

- command: `CROWN_Y_TIME_PRICE_MULT=0.9 python tools/run_local_eval.py --simulation-days 31 --results-dir runs/perturb_time_price_0_9`
- command: `CROWN_Y_TIME_PRICE_MULT=1.1 python tools/run_local_eval.py --simulation-days 31 --results-dir runs/perturb_time_price_1_1`
- result: both perturbations matched default action mix and score proxy exactly; no failures.
- command: `python tools/stability_audit.py ...`
- result: `reports/stability_audit.md` generated with LODO score sensitivity, leave-time-block, and perturbation tables.

## EXP-005 20260509 Ten-Driver Reference

- command: `python tools/run_local_eval.py --simulation-days 31 --variant no_reposition --data-dir _offline_reference_20260509/demo/server/data --results-dir runs/old_0509`
- note: current 20260529 income script mismatched old preference counts for D001/D002, so final old-data score uses the matching 20260509 income script.
- command: `python _offline_reference_20260509/demo/calc_monthly_income.py --project-root _offline_reference_20260509/demo --results-dir runs/old_0509`
- result: 10 drivers, 7893 steps, 31 days, 0 simulation failures, 0 income calculation aborts.
- score proxy: total net `-7038.17`; preference penalty `84750.9`; token usage `0`.
- actions: take `148`, wait `7745`, reposition `0`.
