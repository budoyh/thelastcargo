# CROWN-Y Tournament Build Rules

- Current build is CROWN-PCE Oracle Gap Build on branch `crown-pce-oracle-gap`.
- CROWN-PCE stop states are only `PCE_STRONG_SUCCESS`, `PCE_PARTIAL_SUCCESS`, `DO_NOT_SUBMIT_WITH_ORACLE_EVIDENCE`, or `EXTERNAL_BLOCKER`.
- Do not frame test pass, legal action logs, Qwen availability, report completeness, or low positive score as success.
- PCE final artifacts are limited to `reports/pce_final_report.md`, `reports/pce_experiments.csv`, `reports/oracle_gap.csv`, `reports/predicate_eval.csv`, and `reports/action_forensics.csv`.
- Score accounting must use official net directly: `official_net = gross_income - distance_cost - preference_penalty`. Never use a proxy that subtracts preference penalty twice.
- Before runtime strategy changes, produce offline oracle evidence, predicate evaluation evidence, and a redaction/compliance scan.
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

## Next Build v4 Rules

- Branch work starts from `crown-y-score-rescue` on `crown-y-next-build`; final status is score-gated, not test/report-gated.
- Diagnose before modules: score accounting, wait counterfactuals, query survivability, and preference state ledger must exist before broad strategy changes.
- Runtime P0 boundaries remain strict: no future information, no raw data runtime reads, no `server.*` imports in `demo/agent`, no driver/cargo/location/route/fixed-coordinate special cases, and no Destination Shadow Query.
- `take_order` must come only from the current post-query `current_actionable` observed set; `no_query` cannot take remembered cargo.
- Do not copy literal banned terms or example scenario shortcuts into repository files; use redacted generic phrasing only.
- Qwen3.5-Flash preference compilation is required for non-empty preferences when an API path is available; never print keys and never treat dummy keys as success.
- Final Next Build handoff artifacts are limited to five files: `reports/next_build_final_report.md`, `reports/next_build_experiments.csv`, `reports/score_accountant.csv`, `reports/preference_state_ledger.csv`, and `reports/forensics_samples.csv`.
- Required stop states are `SCORE_PUSH_SUCCESS`, `SCORE_PUSH_STRONG_SUCCESS`, `DO_NOT_SUBMIT_WITH_FRONTIER_EVIDENCE`, or `EXTERNAL_BLOCKER`; below-threshold score must not be presented as success.
- `SCORE_PUSH_SUCCESS` requires 31 days, 0 simulation failures, 0 income aborts, 0 illegal actions, 0 rejected takes, Score Accountant no-double-count conclusion, Qwen compile calls when preferences exist, complete instruction files, committed/pushed branch, 20260529 official net at least `40000`, preference penalty below `25000`, 0509 above rescue reference without new failures, and Pareto frontier evidence.
- `SCORE_PUSH_STRONG_SUCCESS` additionally requires 20260529 official net at least `70000`, preference penalty below `15000` or a rule-level unavoidable-penalty explanation, and value-positive reposition or strong no-reposition counterfactual evidence.
- If score thresholds are not met after diagnostics and Pareto search, the first line of `reports/next_build_final_report.md` must be `DO NOT SUBMIT: score-push threshold not reached.` and the status must be `DO_NOT_SUBMIT_WITH_FRONTIER_EVIDENCE`.
- Cloud or local heavy compute must stay isolated to this project, avoid disrupting other users or local stability, and use GPU resources only when materially useful.

## CROWN-PCE Long-Lived Rules

- Runtime code under `demo/agent` must not read raw datasets, import `server.*`, `bench.*`, scoring internals, or use future cargo availability.
- Runtime code must not hardcode driver ids, cargo ids, static place names, fixed route sequences, fixed coordinates, offline heatmaps, or scenario shortcuts.
- Protected example terms and scenario shortcut words are read-only context; repository files must refer to them only as `literal banned terms redacted`, `scenario shortcuts redacted`, or `raw value redacted`.
- Qwen3.5-Flash Preference Compiler must stay ON for non-empty preferences when an API path is available. Use `SimulationApiPort.model_chat_completion` first, then the compatible endpoint with env priority `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`; never print keys and never treat dummy keys as success.
- Qwen roles are limited to Preference Compiler v2, Observed Vocabulary Linker, and gated Candidate Auditor. Qwen must not output the final action.
- Preference Compiler v2 must emit executable predicate specs or mark rules unresolved. Unresolved rules are soft risk only and must not hard block.
- Observed Vocabulary Linker may use only the current query result's visible vocabulary. Reports and caches committed to git must hash or redact values.
- Candidate Preference Verifier must label top candidates as predicate match yes/no/unknown and marginal effect violates/repairs/neutral/reduces_repairability/unknown before scoring high-impact choices.
- Repair candidates are first-class actions. Each repair action needs avoided penalty, repair value, lost profit, deadline, feasibility, confidence, and an action certificate.
- Preference reposition can bypass the generic market payback gate only when runtime preference target evidence and repair value cover cost. Targets must come from runtime preference evidence or current visible clusters; no geocoding or static target tables.
- Offline oracle, exact-label, and money-repair artifacts are diagnostic only. Runtime code must not import, read, cache, or reference reports, oracle trajectories, exact-label files, cargo ids, driver ids, static places, fixed coordinates, fixed routes, or future availability.
- Required reviewers: prompt adherence, compliance/future-info, oracle/score-accounting, predicate compiler, marginal penalty dataset, runtime planner, code/test, and final audit. If true subagents are unavailable, perform read-only simulated reviews and record them in the final report.
- Cloud or local heavy compute must remain isolated to this project, avoid disrupting other users or local stability, and use GPU only when materially useful.
