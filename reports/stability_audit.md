# Stability Audit

Scope: post-run stability checks. The build has no trained ranker enabled, so LODO is a score-sensitivity audit rather than a retraining audit.

## Final Default

- results_dir: `C:\budostudy\only_for_codex\thelatstcargo\runs\latest`
- net: -18953.97
- penalty: 24700.0
- failed_driver_count: 0
- illegal_actions: 0
- query_minutes: 8499

## LODO Sensitivity

| source | omitted_driver | kept_drivers | net_without_driver | penalty_without_driver | aborted_without_driver |
|---|---|---:|---:|---:|---:|
| latest | D001 | 1 | -16213.43 | 17800.0 | 0 |
| latest | D002 | 1 | -2740.54 | 6900.0 | 0 |
| old_0509 | D001 | 9 | -7673.35 | 81350.9 | 0 |
| old_0509 | D002 | 9 | -17259.97 | 83400.9 | 0 |
| old_0509 | D003 | 9 | -10226.84 | 83100.0 | 0 |
| old_0509 | D004 | 9 | -11242.26 | 84150.9 | 0 |
| old_0509 | D005 | 9 | -11289.38 | 84150.9 | 0 |
| old_0509 | D006 | 9 | -16273.65 | 82250.9 | 0 |
| old_0509 | D007 | 9 | -10884.7 | 83750.9 | 0 |
| old_0509 | D008 | 9 | -13493.17 | 83250.9 | 0 |
| old_0509 | D009 | 9 | 18782.35 | 47400.9 | 0 |
| old_0509 | D010 | 9 | 16217.44 | 49950.9 | 0 |

## Leave Time Block

| block | steps | take | wait | reposition | illegal |
|---:|---:|---:|---:|---:|---:|
| 0 | 328 | 9 | 319 | 0 | 0 |
| 1 | 404 | 0 | 404 | 0 | 0 |
| 2 | 400 | 1 | 399 | 0 | 0 |
| 3 | 395 | 3 | 392 | 0 | 0 |
| 4 | 292 | 0 | 292 | 0 | 0 |

## Perturbations

| run | net | penalty | failed | query_minutes | illegal | take | wait | reposition |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| default | -18953.97 | 24700.0 | 0 | 8499 | 0 | 13 | 1806 | 0 |
| baseline | -94825.77 | 172760.0 | 0 | 1060 | 0 | 154 | 146 | 0 |
| no_time_shadow | -101012.95 | 177520.0 | 0 | 1169 | 0 | 151 | 186 | 0 |
| no_rollout | -19637.96 | 26620.0 | 0 | 8428 | 0 | 14 | 1791 | 0 |
| scout_enabled | -19239.4 | 26300.0 | 0 | 15435 | 0 | 15 | 1637 | 0 |
| reposition_enabled | -18953.97 | 24700.0 | 0 | 8499 | 0 | 13 | 1806 | 0 |
| time_price_0_9 | -18953.97 | 24700.0 | 0 | 8499 | 0 | 13 | 1806 | 0 |
| time_price_1_1 | -18953.97 | 24700.0 | 0 | 8499 | 0 | 13 | 1806 | 0 |
