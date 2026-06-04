DO_NOT_SUBMIT_WITH_INCOMPLETE_SEARCH: executed 20260529 full rows 60 reached the 60-row minimum but did not exhaust the 120-row Dragon search target

branch: crown-dragon-orca-v1-1
official_net: 5067.69
gross_minus_cost: 43207.69
preference_penalty: 38140.0
final_default_variant: best_rescue
package_path: not_built
package_sha256: not_built
package_audit_status: PASS

## Short decision
- recommended_action: do not submit
- first_bottleneck: executed 20260529 full rows 60 reached the 60-row minimum but did not exhaust the 120-row Dragon search target

## B0 reproduction
| trial | net | gross | penalty | take/wait/reposition | invalid |
|---|---:|---:|---:|---|---:|
| D0 | 5067.69 | 43207.69 | 38140.0 | 89/163/0 | 0 |

## No-op isolation
| trial | match_rate | net | gross | penalty |
|---|---:|---:|---:|---:|
| D1 | 1.0 | 5067.69 | 43207.69 | 38140.0 |
| D2 | 1.0 | 5067.69 | 43207.69 | 38140.0 |
| D3 | 1.0 | 5067.69 | 43207.69 | 38140.0 |
| D4 | 1.0 | 5067.69 | 43207.69 | 38140.0 |

## Best 20260529 rows
| rank | trial | stage | net | gross | penalty | keep_or_kill |
|---:|---|---|---:|---:|---:|---|
| 1 | D0 | D0_B0_rescue | 5067.69 | 43207.69 | 38140.0 | kill |
| 2 | D1 | D1_compile_runtime_noop | 5067.69 | 43207.69 | 38140.0 | kill |
| 3 | D2 | D2_debt_accountant_monitor_noop | 5067.69 | 43207.69 | 38140.0 | kill |
| 4 | D3 | D3_value_model_loaded_noop | 5067.69 | 43207.69 | 38140.0 | kill |
| 5 | D4 | D4_query_policy_noop | 5067.69 | 43207.69 | 38140.0 | kill |
| 6 | A3 | A3_E5_like_hunter_reference | 1882.36 | 43382.35 | 41500.0 | kill |
| 7 | M0 | M0_money_backbone_only | -2128.96 | 45051.04 | 47180.0 | kill |
| 8 | G036 | TierA_search_full_31day | -9649.72 | 31490.28 | 41140.0 | kill |
| 9 | M9 | M9_repair_skeleton_gross_refill_best | -9649.72 | 31490.28 | 41140.0 | kill |
| 10 | G004 | TierA_search_full_31day | -9831.06 | 31308.94 | 41140.0 | kill |

## Ablation and module usage summary
- full_run_rows_20260529: 60
- full_run_rows_20260509: 6
- value_model_used_count: 2440
- beam_used_count: 2366
- adaptive_query_used_count: 2087
- month_end_protection_count: 116
- regret_lns_used_count: 2821
- qwen_numeric_adjustments: 0

## 0509 sanity
| trial | net | gross | penalty | invalid |
|---|---:|---:|---:|---:|
| S0 | 86900.14 | 185150.15 | 98250.0 | 0 |
| S1 | 86900.14 | 185150.15 | 98250.0 | 0 |
| S2 | 86900.14 | 185150.15 | 98250.0 | 0 |
| S3 | 86900.14 | 185150.15 | 98250.0 | 0 |
| S4 | 86900.14 | 185150.15 | 98250.0 | 0 |
| S5 | 86900.14 | 185150.15 | 98250.0 | 0 |

## Top 20 regret/debt accounts
| rank | account | family | penalty_estimate | gross_at_risk | source |
|---:|---|---|---:|---:|---|
| 1 | 9058744b5ef72f | continuous_rest_debt | 22032.22 | 27.5 | A1 |
| 2 | fdc10e485c660f | scheduled_window_debt | 19538.64 | 55.0 | A1 |
| 3 | bd4bbea3782618 | full_inactive_day_debt | 17045.06 | 82.5 | A1 |
| 4 | a37c0263db79ae | cargo_attribute_debt | 14551.48 | 110.0 | A1 |
| 5 | 4f3d6766c2cfdf | deadhead_limit_debt | 12057.9 | 137.5 | A1 |
| 6 | 58893b2cf11e0b | long_lockup_debt | 9564.32 | 165.0 | A1 |
| 7 | 323e32bc145fc3 | month_end_horizon_debt | 7070.74 | 192.5 | A1 |
| 8 | 2eae3ead823533 | query_waste_debt | 4577.16 | 220.0 | A1 |
| 9 | 34d72a968b8ead | continuous_rest_debt | 17777.67 | 27.5 | A2 |
| 10 | 8c4c15f2c5a441 | scheduled_window_debt | 15756.82 | 55.0 | A2 |
| 11 | b47358e68ba977 | full_inactive_day_debt | 13735.97 | 82.5 | A2 |
| 12 | c5503cfbeb95ee | cargo_attribute_debt | 11715.12 | 110.0 | A2 |
| 13 | bc4e0d6e671360 | deadhead_limit_debt | 9694.26 | 137.5 | A2 |
| 14 | 5146211f1443df | long_lockup_debt | 7673.41 | 165.0 | A2 |
| 15 | 1332da25d5c763 | month_end_horizon_debt | 5652.56 | 192.5 | A2 |
| 16 | fe2cbdaf726ff2 | query_waste_debt | 3631.71 | 220.0 | A2 |
| 17 | eb50bb43443e9b | continuous_rest_debt | 15093.15 | 8335.33 | M4 |
| 18 | 19dda1af58338c | scheduled_window_debt | 13370.58 | 8362.83 | M4 |
| 19 | adcc8a68b8d8e0 | full_inactive_day_debt | 11648.01 | 8390.33 | M4 |
| 20 | fac6802f81b4b9 | cargo_attribute_debt | 9925.43 | 8417.83 | M4 |

## Reviewer findings summary
- anti_shell_integration_auditor: Checked Dragon score components and trace used_count across 60 executed 20260529 rows.
- execution_evidence_auditor: Grid rows=60; planned/missing rows are rejected by verifier.
- penalty_attribution_auditor: Regret rows=50; nonuniform family estimates are required.
- qwen_compiler_risk_auditor: Qwen numeric auditor is off; schema weakness remains internal compiler debt and search continues.
- value_beam_query_auditor: Value/beam/query/month-end counters are read from full-run traces and kept generic.
- leakage_package_gatekeeper: Package root and forbidden entries are inspected by Dragon package audit and audit_guard.

## Leakage audit summary
- runtime exports only generic parameters and hashed trace identifiers.
- Dragon package audit checks root, forbidden entries, default variant, and SUBMISSION first line.

## Shortest next path
- If below gate, focus on gross-preserving penalty reduction: keep M0/M13 gross backbone, reduce only debt families proven by top regret accounts, and rerun top configs on 20260529/20260509.
