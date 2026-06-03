# Agent Operating Rules

This lowercase rule file mirrors `AGENTS.md` for tools that look for `agent.md`.

## Current Fuse Build

- Branch: `crown-fuse-rescue-switch`.
- Task: CROWN-FUSE / RESCUE-SWITCH v10 = preserve immutable B0 `best_rescue` gross and apply only targeted repair that clears ROI/gross guards against B0 Shadow Guard.
- No `PLANNED` or `MISSING_RUN` rows are allowed in final required evidence.
- No parameter search without real execution. Grid rows must be full 20260529 31-day runs with `status=EXECUTED`, run_dir, command, exit_code, official_net, gross_minus_cost, preference_penalty, action mix, repair metrics, and Qwen counts.
- No final report or package claim without `python tools/verify_fuse_completion.py --phase final` PASS unless the stop state is a real external blocker.
- Qwen compile/link for real non-empty preferences stays ON; smoke tests do not count.
- Qwen auditor numeric adjustment defaults OFF because broad auditor scoring previously harmed official score.
- Subagents are read-only QA gates only and must cite concrete CSV rows, run dirs, commands, exit codes, and metrics.
- B0 rescue equivalence is the foundation; no module work or search before B1/B2/B3 no-op isolation passes.
- Runtime cannot read raw cargo/driver data, reports, oracle artifacts, exact labels, action traces, scorer outputs, income calculators, server/bench internals, or future cargo.
- Runtime cannot import `server.*`, `bench.*`, scorer internals, income-calculation internals, or local evaluation helpers.
- `take_order` only from current post-query `current_actionable` cargo.
- `query_cargo` must be followed by `refresh_world` before filtering/scoring.
- `no_query` cannot take remembered cargo.
- Destination Shadow Query remains OFF.
- Reposition coordinates keep full precision; no rounding in action output.
- No driver_id, cargo_id, static place, fixed coordinate, fixed route, route template, offline heatmap, future-cargo fact, or protected literal in runtime.
- Reports are limited to `fuse_final_report.md`, `fuse_grid.csv`, `fuse_noop_isolation.csv`, `fuse_rule_ledger.csv`, and `fuse_package_audit.md`.
- Valid stop states are `FUSE_RECOMMENDED_SUBMISSION`, `FUSE_EXPERIMENTAL_SUBMISSION`, `FUSE_REVIEW_PACKAGES_ONLY`, `DO_NOT_SUBMIT_WITH_FUSE_EVIDENCE`, `EXTERNAL_BLOCKER_RESCUE_ISOLATION`, `EXTERNAL_BLOCKER_EVAL_INFRA`, and `EXTERNAL_BLOCKER_QWEN`.

## Current Surge Build

- Branch: `crown-surge-ledger-hunter`.
- Task: CROWN-SURGE / LEDGER-HUNTER = Official Delta Drill + Penalty Calibration + BO Weight Attack + Online Opportunity Graph on top of immutable `best_rescue`.
- Continue from the existing repository and failed `crown-trident-gold2` evidence; do not rebuild from scratch.
- Valid stop states: `SURGE_RECOMMENDED_SUBMISSION`, `SURGE_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_SURGE_EVIDENCE`, `DO_NOT_SUBMIT_WITH_INCOMPLETE_EXECUTION`, `EXTERNAL_BLOCKER_RESCUE_CORE`, `EXTERNAL_BLOCKER_QWEN`, and `EXTERNAL_BLOCKER_EVAL_INFRA`.
- `tools/verify_surge_completion.py --phase final` must PASS before success or package. It must fail on missing/mocked evidence, all-zero Qwen auditor adjustment when auditor is enabled, diagnostic-only deltas used for tuning, fewer than 100 executed parameter trials, missing B7/B8 graph usage, report head mismatch, package gate violation, or final report hygiene violation.
- No `PLANNED`, `MISSING_RUN`, `planned_not_evaluated`, smoke-only, synthetic-only, diagnostic-only, report-only, or package-shape evidence can satisfy Surge completion.
- Final `reports/` must contain exactly `surge_final_report.md`, `surge_experiments.csv`, `surge_decision_deltas.csv`, `surge_rule_doctor.csv`, and `surge_qwen_effect.csv`.
- B0 rescue gate: 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected. If official runner/data/eval infrastructure cannot run B0, stop `EXTERNAL_BLOCKER_RESCUE_CORE`.
- Required official matrix rows: B0, B1, B2, B3, B4, B5, B6, B7, B8, B9a, B9b, B9c, B10, B11. Every row needs score, action mix, Qwen stats, controller stats, run_dir, command, and exit_code.
- Parameter search must execute 100+ real 20260529 trials and persist executed metrics; no planned trial can remain in final evidence.
- Real Qwen compile/link/audit stays ON for non-empty preferences when an API path exists. Do not set `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evidence. Timeout is 120 seconds with 3 retries.
- Qwen may compile/link/audit only; it must not choose or veto final action. Auditor JSON must be schema-valid relation/effect/risk_score/repair_score/confidence and deterministic runtime code maps it to numeric score adjustment.
- If auditor calls are >0 and nonzero adjustment count is 0, auditor is decoration and must be killed or final stop is incomplete execution with Qwen decoration as the precise reason.
- Changed-decision scaling requires `exact_suffix_replay` or `runtime_replan_valid` labels with state/visible/legal compatibility and no income abort. Diagnostic-only labels are failure analysis only.
- Online Opportunity Graph uses only current post-query `current_actionable` cargo and same-driver current-run legal observed summaries. No raw datasets, future cargo, offline heatmaps, fixed places, fixed coordinates, fixed routes, driver ids, or cargo ids.
- Subagents/reviewers are QA gates only. Required scopes: Prompt-Adherence, Qwen Auditor, Penalty Delta, Opportunity Graph, Compliance, and Completion Gatekeeper, all citing concrete commands, CSV rows/counts, and file paths.

## Active Build

- Branch: `crown-trident-gold2`.
- Task: CROWN-TRIDENT / GOLD-2 = Penalty Attribution Ledger + Changed-Decision Counterfactual Lab + Preference Contract V2 + verified preference overlay on immutable rescue core + runtime-only Online Opportunity Graph + parameter attack.
- Valid stop states: `CROWN_TRIDENT_RECOMMENDED_SUBMISSION`, `CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE`, `EXTERNAL_BLOCKER_QWEN`, `EXTERNAL_BLOCKER_RESCUE_CORE`, `EXTERNAL_BLOCKER_EVAL_INFRA`, and `DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE`.
- Success is official score, gross, penalty, changed-decision deltas, rule-level penalty deltas, full ablation, Qwen effect, compliance, reviewer/subagent, package, commit, and push gated.
- Tests, legal actions, Qwen smoke, synthetic pass, reports, package shape, macro counts, Qwen call counts, and controller counts are insufficient.
- Current first broken link from Gold: decision changed -> official preference penalty reduced.

## Long-Lived Compliance Rules

- Runtime under `demo/agent` must use only injected `SimulationApiPort` for state, cargo, history, and model calls.
- Runtime must not read raw cargo/driver data, reports, oracle artifacts, action traces, exact labels, income calculators, benchmark internals, scorer outputs, or future cargo availability.
- Runtime must not import `server.*`, `bench.*`, scorer internals, income-calculation internals, or local evaluation helpers.
- Runtime must not hardcode driver ids, cargo ids, static place names, fixed routes, fixed route sequences, fixed coordinates, route templates, offline heatmaps, or scenario shortcuts.
- Protected example terms and scenario shortcut words must not be copied into repository files. Use `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash`.
- Real Qwen runtime calls remain ON for non-empty preferences when an API path is available.
- Do not set or rely on `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evaluation. Do not use dummy cache, smoke-only compile, fallback-only compile, dummy key evidence, or zero Qwen budget as success.
- Qwen roles are Preference Contract Compiler, Observed Vocabulary Linker, and gated Candidate Auditor only. Qwen must not choose, veto, or output final actions.
- API priority is injected `SimulationApiPort.model_chat_completion`, then compatible endpoint using `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`.
- Qwen timeout is 120 seconds with up to 3 retries.
- Never print or commit keys, raw preference text, runtime cargo ids, driver ids, place names, coordinates, raw cargo fields, or protected literals.

## Runtime Action Rules

- `query_cargo` must be followed by `refresh_world`.
- Filtering, scoring, and certificates must use the post-query `World`.
- `take_order` may only use cargo from the current decision's post-query `current_actionable` observed set.
- `no_query` cannot take remembered cargo.
- Shadow or historical cargo must never enter actionable candidates.
- Destination Shadow Query is OFF.
- Reposition action coordinates must keep full precision and must not be rounded.

## CROWN-TRIDENT Rules

- Runtime order is refresh world, compile/cache Preference Contract V2, update rule-state controllers, preserve rescue macro commitments, query, refresh/filter, observed vocabulary linking, generate candidates, Preference Firewall, gated auditor, deterministic scoring, optional runtime-only online graph, safety finalize.
- Preference Contract V2 must emit `rule_id`, `polarity`, `observable`, `scope`, `metric`, `counting`, `slots`, `repair`, `confidence`, `evidence_hash`, and `uncertainty`.
- Qwen must not invent penalty amount or cap; missing penalty is explicit `null` with source `unknown` and uses generic fallback scale.
- Observed Vocabulary Linker may use only current visible cargo field/value summaries.
- Candidate Auditor reviews high-conflict/top candidates and outputs relation/effect/risk/repair/confidence/evidence only; deterministic code maps it to numeric score adjustment.
- Auditor calls with all zero `applied_score_adjustment` are considered not implemented unless ablation kills auditor OFF as better.
- T01-T18 controller coverage remains mandatory.
- Every controller exposes update, satisfied, failed, remaining slack, marginal cost, repair value, repair candidates, dynamic lambda, and final penalty lower bound.
- ScorerSemanticsAdapter gates hard blocks and massive penalties. Unverified semantics are soft risk or diagnostic-only.
- UnknownSoft never hard-blocks high-gross actions.
- Preference Firewall must trace past debt, candidate delta, future repairability delta, marginal penalty, repair value, lost repair-window cost, unknown-soft risk, Qwen audit adjustment, confidence, and decision.
- Already failed or capped rules must not repeatedly consume gross. Still-repairable high-penalty rules must price future repair windows.
- Profit backbone is restored rescue/safe-profit. Any preference module that worsens official_net or worsens penalty without enough gross improvement must be disabled or retuned.
- Online Opportunity Graph may use only current visible cargo and current-run same-driver legal observations; no offline heatmaps, fixed places, fixed coordinates, fixed routes, or future cargo.

## Evidence And Reports

- B0 rescue must reproduce 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected.
- `reports/trident_rule_ledger.csv` and `reports/trident_decision_deltas.csv` are mandatory before final selection.
- `reports/trident_qwen_effect.csv` must prove nonzero auditor adjustment when auditor is retained.
- B0-B11 official ablations are mandatory; do not skip B1-B8 because later runs fail.
- Top penalty rules require rule doctor ablations: ignore, soft scales, hard shield, repair bonuses, wait macro only, and repair take only.
- Final `reports/` contains only `trident_final_report.md`, `trident_experiments.csv`, `trident_rule_ledger.csv`, `trident_decision_deltas.csv`, and `trident_qwen_effect.csv`.
- Old reports are archived, not deleted. Raw runs stay under `runs/`.
- Required real subagent/reviewer scopes: Rescue Baseline Keeper, Penalty Attribution / Regret Lab, Preference Contract / Qwen Auditor Engineer, Profit Backbone / Online Graph Engineer, Parameter Search / Ablation Engineer, and Compliance / Package Gatekeeper.
- Each subagent/reviewer returns changed files, commands run, before/after metrics, pass/fail, blockers, and keep/kill.

## Packaging And Stop Honesty

- Recommended package may be built only if Trident recommended gates pass.
- Experimental package may be built only if Trident experimental gates pass and is labeled experimental.
- If official_net < 30000, do not generate a submission-shaped zip.
- Submission ZIP root is `demo/`; include only `demo/agent/` and `demo/SUBMISSION.md`; exclude server, data, results, reports, runs, archive, docs, keys, local config, prompt docs, and pyc.
- `CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION` requires 20260529 official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 50000, 0 abort/illegal/rejected, nonzero auditor adjustment if auditor used, and clean controller/ablation evidence.
- `CROWN_TRIDENT_RECOMMENDED_SUBMISSION` requires 20260529 official_net >= 38000, preference_penalty <= 22000, gross_minus_cost >= 60000, 0 abort/illegal/rejected, and 0509 clean enough for sanity.
- If score or evidence gates are not reached, write `DO NOT SUBMIT: <precise reason>` as the first line of `reports/trident_final_report.md`.

## Resource Rules

- Keep local and cloud compute isolated to this project.
- Prefer cloud only when it is available without disrupting other users; check host load, `nvidia-smi`, and active jobs first.
- Avoid heavy local load that can freeze the PC.
- Use GPU only if materially useful and after checking availability.
- Never disrupt other users' jobs.
