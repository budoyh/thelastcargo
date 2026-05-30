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

## Score Rescue Mode

- Treat the prior `crown-y-tournament-build` result as a failed baseline until reports prove otherwise.
- Rescue variants must be legal, current-observed, positive-net oriented agents rather than wait-heavy audit builds.
- Every rescue wait needs forensic trace fields: `wait_reason`, top rejected take candidates, best order net/per-hour, hard filter reasons, score decomposition and why wait won.
- Hard blocks in rescue mode are limited to source illegality, online/window/reachability/horizon illegality, severe negative direct net and high-confidence irreversible preference violations.
- Unknown preference risk, time shadow, endgame and two-hop signals are capped soft costs; they must not hard-kill safe positive cargo.
- Qwen preference compilation is allowed only as DSL compilation through `SimulationApiPort.model_chat_completion`; it must not output actions, and missing/dummy keys must be reported as fallback rather than success.
- Rescue success requires the hard score gate in `reports/score_rescue_final_report.md`; negative net, extreme wait ratio or zero Qwen calls with preferences must be reported as forensic failure.
