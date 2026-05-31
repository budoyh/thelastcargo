DO NOT SUBMIT: score-push threshold not reached.

# CROWN-Y Next Build v4 Final Audit

## Stop State

- Stop condition: `DO_NOT_SUBMIT_WITH_FRONTIER_EVIDENCE`.
- Branch: `crown-y-next-build`.
- Base rescue commit: `0f2af10bd3a35754ee198ee83c053a6d17797714`.
- Final handoff commit: recorded by `git rev-parse HEAD` after the final commit/push step.
- Reason: the best 20260529 official net is `2240.98`, below the required `40000` score-push gate and below the rescue reference `5067.69`.

## Environment

- Workspace: `C:\budostudy\only_for_codex\thelatstcargo`.
- Date: 2026-05-31.
- Python entrypoints: `tools/run_local_eval.py`, `demo/calc_monthly_income.py`, `_offline_reference_20260509/demo/calc_monthly_income.py`.
- Runtime LLM: `qwen3.5-flash`; `DASHSCOPE_API_KEY` detected by smoke test, key not printed.
- Runtime compliance boundary: agent code uses `SimulationApiPort`; no raw-data reads, no `server.*` import, no Destination Shadow Query.

## Implemented Files

- Runtime strategy and trace: `demo/agent/config.py`, `demo/agent/model_decision_service.py`, `demo/agent/rescue_scorer.py`, `demo/agent/trace_writer.py`, `demo/agent/wait_lock.py`.
- Preference compiler/state: `demo/agent/qwen_preference_compiler.py`, `demo/agent/preference_compiler.py`, `demo/agent/preference_monitor.py`, `demo/agent/preference_repair.py`.
- Reposition source trace: `demo/agent/micro_reposition.py`, `demo/agent/safety.py`.
- Diagnostics and tests: `tools/score_accountant.py`, `tests/test_crown_y_core.py`.
- Long-lived rules updated: `AGENTS.md`, `agent.md`, `docs/PROJECT_MEMORY.md`, `docs/EXPERIMENT_LOG.md`.

## Stage 1 Diagnostics

- Score Accountant is in `reports/score_accountant.csv`.
- Wait and query forensics are in `reports/forensics_samples.csv`; wait rows include top-20 rejected take hashes, best take/reposition deltas, contribution flags and `wait_lock_bug`.
- Query survivability rows include `query_k`, `query_minutes`, `returned_count`, `actionable_after_query`, `positive_net_count`, missed-window proxy and query reward.
- Preference State Ledger is in `reports/preference_state_ledger.csv`; it redacts raw preference text and records rule progress/debt/deadline/repair fields and daily rest matrix rows.
- Accounting conclusion: official `net_income` already equals `gross_minus_cost - preference_penalty`; any `net - penalty` proxy is forbidden.

## Stage 2 / Stage 3 Frontier

20260529 two-driver frontier:

| Variant | Official Net | Gross-Cost | Preference Penalty | Take / Wait / Repo | qmin/take |
|---|---:|---:|---:|---:|---:|
| `strict_pref` | 2240.98 | 38900.98 | 36660.00 | 73 / 180 / 0 | 42.59 |
| `calendar_rest_only` | -2856.18 | 39483.81 | 42340.00 | 77 / 178 / 0 | 28.39 |
| `preference_state_machine` | -101251.29 | 51908.71 | 153160.00 | 129 / 64 / 0 | 7.39 |
| `marginal_pref_only` | -113959.51 | 74240.49 | 188200.00 | 164 / 6 / 0 | 10.20 |
| `money_greedy_no_pref` | -122937.49 | 77602.52 | 200540.00 | 144 / 6 / 0 | 10.08 |
| `dynamic_query_k` | -128251.07 | 64868.92 | 193120.00 | 168 / 13 / 0 | 7.04 |
| `dynamic_query_reposition` | -130736.14 | 65423.86 | 196160.00 | 169 / 16 / 0 | 7.03 |

20260509 ten-driver cross-check:

| Variant | Official Net | Gross-Cost | Preference Penalty | Take / Wait / Repo | qmin/take |
|---|---:|---:|---:|---:|---:|
| `money_greedy_no_pref` | 220151.20 | 388361.25 | 168210.00 | 740 / 70 / 0 | 10.86 |
| `marginal_pref_only` | 199861.77 | 370771.77 | 170910.00 | 859 / 32 / 0 | 10.18 |
| `dynamic_query_k` | 174300.44 | 339300.46 | 165000.00 | 902 / 75 / 0 | 7.45 |
| `dynamic_query_reposition` | 174300.44 | 339300.46 | 165000.00 | 902 / 75 / 0 | 7.45 |
| `calendar_rest_only` | 99762.54 | 196442.52 | 96680.00 | 418 / 788 / 0 | 22.30 |
| `strict_pref` | 93518.61 | 195318.63 | 101800.00 | 422 / 866 / 0 | 36.40 |

## Named Regret Findings

- Largest 20260529 regret is preference-state failure, not query cost. Greedy variants preserve gross but violation-count penalties dominate.
- `strict_pref` cuts violation penalties to `10660` but loses too much gross and still leaves full-rest, quota and date-specific penalties.
- `preference_state_machine` target repair was implemented from runtime DSL targets only, but it did not reduce penalties enough and destroyed the 20260529 frontier; it is disabled by evidence.
- Dynamic query-k improves query minutes but does not solve the dominant penalty chain.
- Observation-shaping reposition did not produce a positive 20260529 frontier point; keep it off for submission.

## Hard Gates

- 31-day 20260529 simulation: completed for 7 variants.
- 31-day 20260509 simulation: completed for 6 required Stage 2 variants.
- Simulation failures: 0 across `reports/score_accountant.csv`.
- Income calculation aborts: 0.
- Illegal actions: 0.
- Rejected takes: 0.
- Qwen compile calls: >0 for all preference runs in `reports/next_build_experiments.csv`.
- Score gate failed: best 20260529 official net `2240.98` < `40000`.
- Preference penalty gate failed: best 20260529 penalty `36660` > `25000`.

## Verification Commands

- `python -m pytest tests -q`: `50 passed`.
- `python -m compileall demo tools tests`: success.
- `python tools/audit_guard.py --fail-on-p0`: `compliance findings=0 p0=0`.
- `python tools/fix_eval_round_bug.py`: `round_bug_patch=present`.
- `python tools/qwen_preference_smoke_test.py`: `compile_calls=1`, `rules_returned=1`, no dummy-key or API error.
- `python tools/score_accountant.py --runs-root runs/next_build --output-dir reports`: `runs=13`, `score_rows=74`, `ledger_rows=2561`, `forensic_rows=9905`.

## Subagent / Reviewer Notes

- Stage 0 real reviewer blockers were addressed: AGENTS/agent gate completeness, no double-count score proxy, Stage 1 diagnostic entrypoints, Qwen repair DSL, reposition value trace, and report-limit cleanup.
- Stage 1 review requests were sent to Prompt-Adherence, Compliance/Future-Info, Score-Accounting, Preference-State, Route/Reposition and Code/Test reviewers after diagnostics passed.
- Stage 2/3 review requests were sent after all required 20260529/20260509 runs completed.
- Final self-review result: DO NOT SUBMIT; the evidence is complete enough to reject the build rather than dress it up as success.

## Final Artifact Set

Only these five report files should remain committed:

- `reports/next_build_final_report.md`
- `reports/next_build_experiments.csv`
- `reports/score_accountant.csv`
- `reports/preference_state_ledger.csv`
- `reports/forensics_samples.csv`

## Shortest Next Path

The next shortest path is not another query-k sweep. It is a stronger, still-compliant preference compiler/evaluator that can convert runtime DSL into verifiable cargo-level predicates and repair schedules without hardcoded scenario terms. The current build can diagnose the failure chain, but it cannot yet legally avoid the dominant violation-count penalties on 20260529 while preserving enough gross income.
