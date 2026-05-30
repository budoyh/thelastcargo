# Regret Dashboard V2

- runs_root: `C:\budostudy\only_for_codex\thelatstcargo\runs\score_rescue_ablation`
- categories: query_too_big, query_too_small, long_order_trap, wait_regret, reposition_not_recovered, preference_late_panic
- v2 additions: feasible_positive_cargo_but_wait, query_minutes_per_take, wait_ratio, rejected_take, illegal_actions

| run | net | take | wait | repo | wait_ratio | q_min/take | wait_regret_v2 | positive_wait | rejected | illegal | query_too_big | query_too_small | long_order_trap | wait_regret | reposition_not_recovered | preference_late_panic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a0 | -113176.86 | 167 | 17 | 0 | 0.0924 | 12.96 | 8 | 0 | 0 | 0 | 1 | 4 | 7 | 7 | 0 | 0 |
| a1 | -113176.86 | 167 | 17 | 0 | 0.0924 | 12.96 | 8 | 0 | 0 | 0 | 1 | 4 | 7 | 7 | 0 | 0 |
| a2 | -113176.86 | 167 | 17 | 0 | 0.0924 | 12.96 | 8 | 0 | 0 | 0 | 1 | 4 | 7 | 7 | 0 | 0 |
| a3 | -113702.22 | 168 | 17 | 0 | 0.0919 | 12.96 | 8 | 0 | 0 | 0 | 1 | 4 | 8 | 7 | 0 | 0 |
| a4 | -113702.22 | 168 | 17 | 0 | 0.0919 | 12.96 | 8 | 0 | 0 | 0 | 1 | 4 | 8 | 7 | 0 | 0 |
| a5 | -113881.81 | 166 | 17 | 0 | 0.0929 | 12.97 | 8 | 0 | 0 | 0 | 1 | 4 | 7 | 7 | 0 | 0 |
| a6 | 5067.69 | 89 | 163 | 0 | 0.6468 | 37.15 | 104 | 0 | 0 | 0 | 6 | 4 | 0 | 103 | 0 | 0 |
| a7 | 5067.69 | 89 | 163 | 0 | 0.6468 | 37.15 | 104 | 0 | 0 | 0 | 6 | 4 | 0 | 103 | 0 | 0 |

Best net run: `a6` with net `5067.69`, wait_ratio `0.6468`, wait_regret_v2 `104`, positive_wait `0`.
