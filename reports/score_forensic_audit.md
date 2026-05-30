# Score Forensic Audit

- results_dir: `C:\budostudy\only_for_codex\thelatstcargo\runs\latest_rescue`
- net: 5067.69
- penalty: 38140.0
- take/wait/reposition: 89 / 163 / 0
- query_minutes_per_take: 37.15
- feasible_positive_cargo_but_wait: 0
- max_consecutive_wait: 6

## Wait Reason Distribution

| wait_reason | count |
|---|---|
| positive_orders_failed_threshold_or_soft_risk | 91 |
| daily_rest_guard | 58 |
| no_safe_positive_net_cargo | 10 |
| periodic_full_rest_guard | 4 |

## Hard Block Reason Counts

| hard_block_reason | count |
|---|---|
| filter_load_window_unreachable | 14373 |
| rest_window_overlap | 10193 |
| filter_remove_slack_too_short | 4004 |
| filter_not_online | 2126 |
| filter_normalize_failed | 150 |
| below_direct_net_threshold | 142 |
| severe_negative_net | 72 |
| filter_finish_after_horizon | 56 |

## Top Rejected Take Snapshots

| candidate | direct_net | profit_per_hour | hard_filter_reason | score |
|---|---|---|---|---|
| take:220556 | 371.77 | 7.47 | rest_window_overlap | -53058.81 |
| take:309533 | 91.74 | 18.11 | rest_window_overlap | -13451.21 |
| take:308012 | 339.48 | 64.87 | rest_window_overlap | -13808.41 |
| take:309452 | 47.22 | 8.83 | rest_window_overlap | -14892.85 |
| take:308407 | 145.7 | 24.02 | rest_window_overlap | -18173.6 |
| take:223623 | 270.72 | 43.31 | rest_window_overlap | -18851.39 |
| take:226381 | 79.83 | 17.54 | rest_window_overlap | -23942.76 |
| take:308012 | 339.48 | 64.87 | rest_window_overlap | -26773.81 |
| take:224629 | 868.43 | 84.73 | rest_window_overlap | -33816.23 |
| take:191 | 374.04 | 37.72 | rest_window_overlap | -34497.05 |
