# CROWN-Y Tournament Build

This repository implements the Manbang Agent competition CROWN-Y Tournament Build, not CROWN-Y Max. The default line is compliance-first: P0/P0++ stable, P1 core enabled where ablation supports it, P2 conservative, P3 closed.

## Runtime Flow

1. `ModelDecisionService.decide()` calls `refresh_world()` to rebuild status, preference DSL rules, ledger, debt market, endgame state and time market.
2. Query policy either skips query near horizon or queries the current location. Every `query_cargo` is followed immediately by `refresh_world()`.
3. `cargo_filter` normalizes only post-query, still-online `current_actionable` cargo into candidates.
4. `candidate_generator` builds take and wait options; reposition remains behind an experimental switch and payback gate.
5. `safety` attaches action certificates and enforces current observed set, source scope, decision id and horizon constraints.
6. `preference_monitor`, `visible_rollout`, `time_bid_scorer`, `endgame_planner` and optional ranker gates score only legal candidate objects.
7. `trace_writer` records enough certificate fields for offline audit without enabling raw data access.

## Commands

```powershell
python -m pytest tests -q
python tools/audit_guard.py --fail-on-p0
python tools/fix_eval_round_bug.py
python tools/run_local_eval.py --simulation-days 31 --results-dir runs/latest
python tools/regret_dashboard.py --results-dir runs/latest
python tools/stability_audit.py --latest runs/latest --old runs/old_0509
```

## Default Switches

ON: Time Shadow, Preference Monitor, Visible two-hop, Resource Endgame.

OFF: Scout-then-deepen, Reposition, Learned Ranker, LLM Judge, Destination Shadow Query, three-hop, option rollout.
