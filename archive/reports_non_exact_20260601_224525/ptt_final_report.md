DO NOT SUBMIT: PTT gates not reached.

# CROWN-PTT-GreedyMPC Final Report

## Decision
- recommended_submission: no
- stop_state: PTT_DIAGNOSTIC_SUCCESS_DO_NOT_SUBMIT
- default_variant: `preference_firewall_profit`

## 20260529 Score
- official_net: -8635.06
- gross_minus_cost: 33364.94
- preference_penalty: 42000.0
- illegal_actions: 0
- rejected_takes: 0
- qwen_compile_calls: 0
- ptt_compile_calls: 0
- ptt_linker_required/called: 192/192
- macro_started/completed: 48/40

## 20260509 Regression
- official_net: 87591.66
- preference_penalty: 99530.0
- failed_driver_count: 0

## Synthetic PTT
- total_types: 18
- passed_types: 18
- failed_types: none

## Remaining Blockers
- score_0529_net_above_rescue
- score_0529_penalty_below_rescue
- score_0529_gross_not_collapsed
- qwen_ptt_compile_called

## Evidence Files
- `reports/ptt_experiments.csv`
- `reports/ptt_compiler_coverage.csv`
- `reports/ptt_decision_forensics.csv`
- `reports/ptt_submission_audit.md`
