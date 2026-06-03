DO NOT SUBMIT: EXTERNAL_BLOCKER_QWEN_API - compile benchmark below gate schema_valid_rate=0.894, primitive_family_accuracy=1.000
# Pref-Forge Final Report

stop_state: EXTERNAL_BLOCKER_QWEN_API
stop_reason: compile benchmark below gate schema_valid_rate=0.894, primitive_family_accuracy=1.000
branch: crown-pref-forge-v1
source_commit: 832919d81d8a091ad19c15737b0a480bed46bcba
evidence_commit: 832919d81d8a091ad19c15737b0a480bed46bcba
package_path: 
package_sha256: 

## one-paragraph decision
Pref-Forge evidence currently resolves to `EXTERNAL_BLOCKER_QWEN_API`. Best 20260529 candidate is `E0` with official_net=5067.69, gross_minus_cost=43207.69, preference_penalty=38140.0.

## baseline reproduction table
| trial | net | gross_minus_cost | penalty | take/wait/reposition | invalid |
|---|---:|---:|---:|---|---:|
| E0 | 5067.69 | 43207.69 | 38140.0 | 89/163/0 | 0 |
| E1 | 5067.69 | 43207.69 | 38140.0 | 89/163/0 | 0 |
| E2 | 5067.69 | 43207.69 | 38140.0 | 89/163/0 | 0 |

## preference compile benchmark summary
- metrics: `{"critical_slot_valid_rate":1.0,"monitor_sim_pass_rate":1.0,"primitive_family_accuracy":1.0,"qwen_calls":1058,"raw_literal_committed_count":0,"rows":66,"schema_valid_rate":0.8939}`

## raw literal / leakage audit summary
- raw literal audit and runtime leakage audit are recorded under `runs/pref_forge/`; committed benchmark stores hashes only.

## no-op isolation summary
- E1 action_signature_match_rate: `1.0`
- E2 action_signature_match_rate: `1.0`

## full experiment score table
| trial | stage | net | gross | penalty | mix | keep_or_kill |
|---|---|---:|---:|---:|---|---|
| E0 | E0_B0_rescue | 5067.69 | 43207.69 | 38140.0 | 89/163/0 | keep_b0_reference |
| E1 | E1_compile_log_only_noop | 5067.69 | 43207.69 | 38140.0 | 89/163/0 | diagnostic_retain_family |
| E2 | E2_monitor_update_only_noop | 5067.69 | 43207.69 | 38140.0 | 89/163/0 | diagnostic_retain_family |
| E5 | E5_high_quality_order_hunter_only | -1332.9 | 46887.1 | 48220.0 | 70/109/0 | diagnostic_retain_family |
| E3 | E3_preference_delta_scorer_only_no_repair | -38088.76 | 28951.25 | 67040.0 | 85/154/6 | kill_below_pref_forge_retention_gate |
| E4 | E4_avoid_limit_shield_only | -38088.76 | 28951.25 | 67040.0 | 85/154/6 | kill_below_pref_forge_retention_gate |

## best candidates: B0 vs hidden-safe vs pref-forge vs fill/refill
- best: `E0`; E0/B0 reference net=5067.69, gross=43207.69, penalty=38140.0.

## penalty-family diff summary
- rows: 76; generic family-level rows only.

## Qwen budget/calls/cache/latency summary
- benchmark_qwen_calls: 1058; runtime numeric auditor adjustments forced to 0.

## numeric auditor OFF proof
- `CROWN_FUSE_AUDITOR_NUMERIC=0`, `CROWN_GOLD_ENABLE_AUDITOR=0`, and `CROWN_TRIDENT_QWEN_AUDIT_SCALE=0` are set in Pref-Forge experiment envs.

## query policy summary
- Query k values searched: 100/300/600. Query cost is recorded as query_count/query_minutes_per_take in the grid.

## minimal repair stats
- E12 refill fields: refill_gross_gain=, penalty_reintroduced=.

## high-quality hunter stats
- keep_or_kill counts: `{"diagnostic_retain_family":3,"keep_b0_reference":1,"kill_below_pref_forge_retention_gate":2}`

## 0509 sanity summary
- executed 0509 rows: 0

## subagent reviewer findings
- See `docs/AGENT_WORK/reviewer_findings.md`.

## package path / sha256 / default variant
- package: ``
- sha256: ``

## final recommendation: submit / hidden-safe trial / do not submit
- recommendation: `do not submit`

## shortest next path
- If blocked, fix the first failing verifier phase and rerun the exact mandatory command list.
