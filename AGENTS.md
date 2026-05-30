# CROWN-Y Tournament Build Rules

- Build CROWN-Y Tournament Build only; do not build CROWN-Y Max.
- Runtime agent code may use only the injected `SimulationApiPort` for state, cargo, history and model calls. It must not read raw data files or import server, bench or income-calculation internals.
- Every `query_cargo` call must be followed by `refresh_world`; filtering, scoring and action certificates must use the post-query `World`.
- `take_order` may only use cargo from the current decision's `current_actionable` observed set. `shadow_liquidity_only` and `historical_summary_only` cargo must never enter actionable candidates.
- Destination Shadow Query, LLM Judge, Learned Ranker, three-hop and option rollout are default OFF unless a report-backed switch change is made.
- Time Shadow must keep productive time price, query time cost and information option value separate, with candidate-aware leave-one-out opportunity cost, clipping, shrinkage and fallback.
- Preference handling must use runtime `status.preferences` through abstract DSL, evidence and certificates. Low confidence rules price risk but do not hard block.
- Reposition is default OFF until payback is proven positive. If enabled experimentally, it must pass the payback gate and preference safety gate before execution.
- Maintain centralized records in `docs/PROJECT_MEMORY.md`, `docs/EXPERIMENT_LOG.md`, `reports/regret_dashboard.md`, `reports/stability_audit.md` and `reports/final_audit_report.md`.
- Required local checks before final handoff: `python -m pytest tests -q`, `python tools/audit_guard.py --fail-on-p0`, `python tools/fix_eval_round_bug.py`, 31 day simulation, regret dashboard, stability audit, final reviewer notes, commit and push attempt.
