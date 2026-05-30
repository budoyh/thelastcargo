# Baseline Comparison

- results_root: `C:\budostudy\only_for_codex\thelatstcargo\runs\rescue_baselines`

| run | net | penalty | proxy | take | wait | repo | rejected | wait_ratio | q_min/take | aborts |
|---|---|---|---|---|---|---|---|---|---|---|
| current_crown_y | -18953.97 | 24700.0 | -43653.97 | 13 | 1806 | 0 | 0 | 0.9929 | 653.77 | 0 |
| fixed_k50_positive_net | -131943.64 | 203400.0 | -335343.64 | 169 | 21 | 0 | 0 | 0.1105 | 5.66 | 0 |
| fixed_k100_profit_per_hour | -124918.99 | 203180.0 | -328098.99 | 168 | 21 | 0 | 0 | 0.1111 | 10.97 | 0 |
| fixed_k200_direct_profit_with_slack | -116567.7 | 194280.0 | -310847.7 | 157 | 10 | 0 | 0 | 0.0599 | 20.42 | 0 |
| simple_balanced_greedy | -113231.6 | 190760.0 | -303991.6 | 172 | 13 | 0 | 0 | 0.0703 | 12.64 | 0 |
| safe_profit_greedy | -113176.86 | 192780.0 | -305956.86 | 167 | 17 | 0 | 0 | 0.0924 | 12.96 | 0 |
