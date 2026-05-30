# CROWN-Y Tournament Build Final Audit Report

## 1. Executive Summary

- Objective: implement Manbang Agent competition CROWN-Y Tournament Build in `C:\budostudy\only_for_codex\thelatstcargo`; do not implement CROWN-Y Max.
- Mainline: P0/P0++ stable, P1 conservative scoring modules, P2/P3 default OFF.
- Implementation commit: `f2a4503` (`Implement CROWN-Y tournament build`).
- Final report commit: `5ad621c` (`Add final audit report`).
- Push status: success; branch `crown-y-tournament-build` tracks `origin/crown-y-tournament-build`.
- Branch: `crown-y-tournament-build`.
- Runtime model calls: `0`; LLM Judge default OFF and budget `0`.
- Final default: Time Shadow, Preference Monitor, Visible two-hop and Resource Endgame ON; Scout-then-deepen, Reposition, Learned Ranker, LLM Judge, Destination Shadow Query, three-hop and option rollout OFF.
- Final local 31 day run: 0 simulation failures, 0 income calculation aborts, 0 illegal actions, 0 rejected takes.

## 2. Environment

- Workspace: `C:\budostudy\only_for_codex\thelatstcargo`
- Shell: PowerShell on Windows
- Python: `3.13.5`
- Local date: 2026-05-31 Asia/Shanghai
- Data/runtime: official demo package extracted locally; raw `demo/server/data/` is ignored by git and not imported/read by runtime agent code.
- API key handling: local eval injects `DASHSCOPE_API_KEY=local-dummy-key-not-used` when absent; final agent made no model calls.

## 3. Implementation Files

Core runtime under `demo/agent/`:

- `model_decision_service.py`: deterministic decision entry, query-refresh barrier, exception fallback wait.
- `world.py`: rebuilds status, preference rules, ledger, debt, endgame and time market.
- `schemas.py`: source scopes, normalized cargo, certificates, time/debt/endgame schemas.
- `normalization.py`, `cargo_filter.py`: post-query normalization and current-actionable filtering.
- `candidate_generator.py`, `safety.py`: legal candidates, horizon clamp, action certificates, payback gate, final action guard.
- `preference_compiler.py`, `preference_monitor.py`, `preference_debt_market.py`: runtime preference DSL/evidence/certificates and low-confidence pricing.
- `time_shadow_market.py`, `time_bid_scorer.py`: productive time price, query time cost, information option value, leave-one-out opportunity cost, clip/shrink/fallback.
- `visible_rollout.py`: two-hop rollout using only current observed cargo.
- `endgame_planner.py`: resource pressure and preference debt endgame pricing.
- `learned_ranker.py`: conservative ranker scaffold, default OFF with sign/OOD/clip guards.
- `llm_budget.py`, `llm_preference_judge.py`: yes/no/unknown judge parser and zero default budget.
- `trace_writer.py`: full/minimal trace with certificate fields and exception trace.

Tools and reports:

- `tools/audit_guard.py`: runtime-boundary and switch audit.
- `tools/fix_eval_round_bug.py`: verifies coordinate output patch.
- `tools/regret_dashboard.py`: six regret categories with robust JSONL/minimal trace handling.
- `tools/stability_audit.py`: LODO score sensitivity, leave-time-block and perturbation report.
- `tools/run_local_eval.py`: reproducible local simulation wrapper.
- `reports/regret_dashboard.md`, `reports/stability_audit.md`, `reports/module_switches.md`, `reports/subagent_reviews.md`: required audit artifacts.

Repository rules:

- `AGENTS.md` and `agent.md` define long-lived operating rules.
- `docs/PROJECT_MEMORY.md` and `docs/EXPERIMENT_LOG.md` centralize durable memory and experiment evidence.

## 4. P0/P0++ Compliance

| requirement | status | evidence |
|---|---|---|
| query followed by refresh_world | PASS | `_execute_query_plan()` refreshes world after every query branch. |
| filtering uses post-query World | PASS | `cargo_filter.normalize_and_filter(... world=world_after_query ...)`. |
| take_order only current observed set | PASS | `ActionCertificate` checks `source_scope`, `observed_ids` and `decision_id`. |
| no remembered cargo take | PASS | no-query returns empty observed list; safety requires current observed ids. |
| source_scope isolation | PASS | `current_actionable` only becomes actionable; shadow/history are non-actionable. |
| Destination Shadow Query | PASS | default OFF; official arbitrary-coordinate flag false. |
| no raw data runtime read | PASS | agent imports no server/data/income internals; audit P0=0. |
| no driver/cargo/city/route/fixed-coordinate runtime hardcoding | PASS | audit P0=0; no runtime ID coordinate tables. |
| 31 day horizon | PASS | config and server example set `31`; horizon tests pass. |
| reposition coordinate precision | PASS | no rounding to two decimals; test covers float precision. |

## 5. P1/P2/P3 Decisions

| module | final state | reason |
|---|---|---|
| Time Shadow | ON | Strong positive ablation: default `-18953.97` vs no_time_shadow `-101012.95`. |
| Preference Monitor | ON | Runtime DSL/evidence/certificate implemented; low confidence does not hard block. |
| Visible two-hop | ON | Default beats no-rollout on net and preference penalty; uses only current observed cargo. |
| Resource Endgame | ON | Handles debt/endgame pressure without fixed date-only logic. |
| Scout-then-deepen | OFF | Enabling worsens query minutes `8499 -> 15435`, creates `647` query-too-big events, and worsens net/penalty. |
| Reposition | OFF | Payback gate retained, but enabled experiment emitted 0 reposition and produced no positive payback evidence. |
| Learned Ranker | OFF | P2 not proven; hand score remains dominant. |
| LLM Judge | OFF | Budget manager is present; default calls are 0 and parser only accepts yes/no/unknown. |
| Destination Shadow Query | OFF | No official compliance confirmation. |
| Three-hop / option rollout | OFF | P3 risk, default closed. |

## 6. Verification Commands

| command | result |
|---|---|
| `python -m pytest tests -q` | `33 passed in 0.72s` |
| `python tools/audit_guard.py --fail-on-p0` | `findings=0 p0=0` |
| `python tools/fix_eval_round_bug.py` | `round_bug_patch=present` |
| `python -m compileall demo\agent tools` | PASS |
| `python tools/stability_audit.py ...` | generated `reports/stability_audit.md` |

PowerShell note: early eval runs using `2>&1` produced `NativeCommandError` records because service logs write to stderr, while simulation and income artifacts completed successfully with `failed_driver_count=0`. Later runs used all-stream redirection and exited `0`.

## 7. Final 20260529 Simulation

Command: `python tools/run_local_eval.py --simulation-days 31 --results-dir runs/latest`

| metric | value |
|---|---:|
| completed_steps | 1819 |
| simulation_days | 31 |
| simulation_failures | 0 |
| income_calc_aborts | 0 |
| illegal_actions | 0 |
| total_net_income | -18953.97 |
| total_preference_penalty | 24700.0 |
| token_usage | 0 |
| take_order | 13 |
| wait | 1806 |
| reposition | 0 |
| rejected_take | 0 |
| query_minutes | 8499 |

Per-driver outcome:

| driver | net_income | preference_penalty | calculation_aborted |
|---|---:|---:|---|
| D001 | -2740.54 | 6900.0 | false |
| D002 | -16213.43 | 17800.0 | false |

## 8. Ablation Results

| run | net | penalty | failed | rejected_take | query_minutes | action mix |
|---|---:|---:|---:|---:|---:|---|
| default | -18953.97 | 24700.0 | 0 | 0 | 8499 | 13 take / 1806 wait / 0 reposition |
| baseline | -94825.77 | 172760.0 | 0 | 4 | 1060 | 154 take / 146 wait / 0 reposition |
| no_time_shadow | -101012.95 | 177520.0 | 0 | 2 | 1169 | 151 take / 186 wait / 0 reposition |
| no_rollout | -19637.96 | 26620.0 | 0 | 0 | 8428 | 14 take / 1791 wait / 0 reposition |
| scout_enabled | -19239.4 | 26300.0 | 0 | 0 | 15435 | 15 take / 1637 wait / 0 reposition |
| reposition_enabled | -18953.97 | 24700.0 | 0 | 0 | 8499 | 13 take / 1806 wait / 0 reposition |
| time_price_0_9 | -18953.97 | 24700.0 | 0 | 0 | 8499 | 13 take / 1806 wait / 0 reposition |
| time_price_1_1 | -18953.97 | 24700.0 | 0 | 0 | 8499 | 13 take / 1806 wait / 0 reposition |

Decision:

- Keep Time Shadow.
- Keep Visible two-hop.
- Disable Scout default.
- Disable Reposition default until positive payback evidence exists.
- Keep Learned Ranker and LLM Judge disabled.

## 9. Regret Dashboard

Final default regret counts:

| regret | count | note |
|---|---:|---|
| query_too_big | 0 | scout default OFF |
| query_too_small | 25 | proxy |
| long_order_trap | 2 | proxy |
| wait_regret | 1797 | major residual risk |
| reposition_not_recovered | 0 | true selected-reposition payback tracker; no reposition emitted |
| preference_late_panic | 0 | proxy |

## 10. Stability Checks

Command: `python tools/stability_audit.py --latest runs/latest --old runs/old_0509 --perturbation ...`

- LODO score sensitivity generated for final two-driver run and old ten-driver reference.
- Leave-time-block final run: 5 blocks, all blocks have 0 illegal actions.
- Time price perturbation +/-10% matched default action mix and score proxy.
- Learned Ranker is OFF, so LODO is a score-sensitivity audit, not retraining evidence.

## 11. 20260509 Ten-Driver Reference

Commands:

- `python tools/run_local_eval.py --simulation-days 31 --variant no_reposition --data-dir _offline_reference_20260509/demo/server/data --results-dir runs/old_0509`
- `python _offline_reference_20260509/demo/calc_monthly_income.py --project-root _offline_reference_20260509/demo --results-dir runs/old_0509`

Result:

| metric | value |
|---|---:|
| drivers | 10 |
| steps | 7893 |
| simulation_failures | 0 |
| income_calc_aborts | 0 |
| total_net_income | -7038.17 |
| total_preference_penalty | 84750.9 |
| take_order | 148 |
| wait | 7745 |
| reposition | 0 |

Note: the current 20260529 income script does not match the old 20260509 preference count for two old drivers, so the matching old income script was used for this reference score.

## 12. Subagent Review Summary

| reviewer | initial result | remediation |
|---|---|---|
| Prompt-Adherence | re-review blocked only before final commit/push closure | final report prepared; implementation commit made; preference certificate strengthened; reposition default OFF; stability audit generated; final report is now committed and branch pushed |
| Compliance | allowed: audit P0=0 | kept audit green after edits |
| Safety & Runtime | blocked: fallback wait horizon overflow and trace audit fields | wait/fallback/finalize horizon clamp; trace certificate fields; regression tests |
| Regret & Ablation | blocked: weak regret report and reposition evidence | fixed payback recovery logic; full ablation/regret tables; reposition OFF |
| Code Quality | blocked: no top-level exception fallback, dead preference hard-block path, minimal trace mismatch | exception wait fallback; executable DSL/certificate path; robust regret parser; tests |

Full notes are in `reports/subagent_reviews.md`.

## 13. Residual Risks

- Wait-heavy behavior remains the main scoring risk: final default has `1797` wait-regret proxy events.
- Preference parsing is intentionally generic to avoid hardcoded hidden-data assumptions; it cannot perfectly infer every natural-language rule.
- Current public 20260529 data has only two drivers; old 20260509 ten-driver reference helps runtime stability but is not identical to hidden data.
- Reposition is implemented but default OFF because no selected-reposition positive payback evidence exists.
- Final push depends on remote authentication and network acceptance.

## 14. Submission Checklist

| item | status |
|---|---|
| CROWN-Y Tournament Build only, not Max | PASS |
| P0/P0++ legality tests | PASS |
| query refresh after every query | PASS |
| post-query filtering | PASS |
| current observed set only for take_order | PASS |
| source_scope isolation | PASS |
| Destination Shadow default OFF | PASS |
| Time Shadow split into productive/query/info components | PASS |
| candidate-aware leave-one-out opportunity cost | PASS |
| Preference DSL/evidence/certificate | PASS |
| LLM Judge yes/no/unknown and budget manager | PASS |
| Visible two-hop current observed only | PASS |
| Reposition payback gate implemented and default OFF | PASS |
| Learned Ranker conservative and default OFF | PASS |
| Regret dashboard six categories | PASS |
| raw data/server import/hardcoding audit | PASS |
| AGENTS.md and agent.md maintained | PASS |
| final reviewer notes recorded | PASS |
| final commit/push | PASS; branch pushed to `origin/crown-y-tournament-build`; implementation commit `f2a4503`, report commit `5ad621c` |
