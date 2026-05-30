# Final Audit Report

This file is the durable handoff pointer for the current branch. The earlier CROWN-Y tournament build was a failed baseline and has been superseded by Score Rescue Mode.

Primary final report:

- `reports/score_rescue_final_report.md`

Score rescue result:

- status: `RESCUE_SUCCESS`
- implementation_commit: `1ff309f`
- evidence_report_commit: `f96786a`
- push_status: `success to origin/crown-y-score-rescue`
- final run: `runs/latest_rescue`
- net: `5067.69`
- preference_penalty: `38140.0`
- take / wait / reposition / rejected: `89 / 163 / 0 / 0`
- wait_ratio: `0.6468`
- query_minutes_per_take: `37.15`
- wait_regret_v2: `104`
- feasible_positive_cargo_but_wait: `0`
- Qwen compile calls: `5`
- 0509 reference: 0 simulation failures, 0 income aborts, 0 illegal actions, 0 rejected takes

Supporting reports:

- `reports/baseline_comparison.md`
- `reports/score_rescue_ablation.md`
- `reports/score_forensic_audit.md`
- `reports/regret_dashboard_v2.md`
- `reports/qwen_preference_compile_report.md`
- `reports/module_switches_score_rescue.md`
- `reports/subagent_reviews_score_rescue.md`
