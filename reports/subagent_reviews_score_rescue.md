# Subagent Reviews Score Rescue

## Final Reviewer Status

All final read-only reviewer blockers were closed before this report was written. Remaining items are documented as residual risks, not stop-condition blockers.

## Prompt-Adherence / Hard Gates

- reviewer: `019e7a97-749c-7cc0-8ad7-136aea050f5f`
- final status: PASS after final report/module report generation.
- evidence checked: `runs/latest_rescue`, `runs/old_0509_rescue`, `reports/baseline_comparison.md`, `reports/score_rescue_ablation.md`, `reports/score_forensic_audit.md`, `reports/regret_dashboard_v2.md`, `reports/qwen_preference_compile_report.md`.
- hard gate evidence: 31 days, 0 simulation failures, 0 income aborts, 0 illegal, final net `5067.69`, take `89`, wait_ratio `0.6468`, query_minutes_per_take `37.15`, wait_regret_v2 `104`, Qwen compile calls `5`, 0509 reference clean.

## Compliance / Safety

- reviewer: `019e7a97-9ce4-7bf3-ae26-27173770b024`
- final status: PASS.
- checked: no runtime raw-data reads, no `server.*` imports in `demo/agent`, query-after-refresh boundary, current_actionable take isolation, no-query cannot take remembered cargo, Destination Shadow OFF, reposition coordinates kept as full floats.
- residual risk: `CROWN_Y_ENABLE_REPOSITION=1` can enable the older payback-gated reposition path; final rescue runs leave it unset.

## Wait-Lock Forensic / Regret

- reviewer: `019e7a97-b7b3-7f92-af7c-b9a1e3347551`
- final status: PASS after fixes.
- fixed blockers: exception fallback wait now has `rescue.wait_forensic`; `regret_dashboard_v2` now includes the six requested regret category counts and only A0-A7.
- latest trace check: 163 waits, forensic missing `0`, unknown wait reasons `0`, feasible_positive_cargo_but_wait `0`.
- residual risk: `cargo_filter._last_rejections` is module-level mutable state and assumes sequential simulation.

## Score Rescue / Runtime Robustness

- reviewer: `019e7a98-1be7-75f1-9d0f-f2bbe54d9083`
- final status: PASS after fixes.
- fixed blockers: force-take cannot bypass rest/scheduled hard blocks; rest guard wait runs after query and includes rejected-take forensic evidence; filter-level rejections are counted in trace/report; invalid explicit load windows are rejected before actionability.
- residual risk: threshold reasons are stored in `hard_block_reason` for reporting, while loop breaker treats threshold-only reasons as soft relaxable constraints.

## Qwen Preference Compiler

- reviewer: `019e7a97-ed63-7980-a36f-e2b39b7d2bd7`
- final status: PASS after fixes.
- fixed blockers: Qwen `irreversible` maps to `irreversible_after_action` and is consumed by preference certificates; compile attempts are gated by `LLMBudgetManager`; fallback env keys and dummy-key blocking are tested; Qwen report matches latest trace.
- latest Qwen evidence: `compile_calls=5`, `judge_calls=0`, `fallback_unknown_count=0`, `api_error_count=0`, `dummy_key_blocked_count=0`, `budget_blocked_count=0`.

## Final Residual Risks

- The final strategy still carries preference penalty `38140.0`; it is positive-net and legal, not a fully optimized preference solution.
- Rest guard dominates wait decisions. This is intentional for score rescue because lower rest protection produced higher take counts but negative net due preference penalties.
- Qwen budget exhaustion has source-review coverage but no dedicated unit test that forces the budget-exhausted branch.
