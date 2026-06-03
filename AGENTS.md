# CROWN-PREF-FORGE v1.1 Active Build Rules

- Active build: CROWN-PREF-FORGE v1.1 on branch `crown-pref-forge-v1`.
- Continue from the existing repository and executed Fuse/Surge/Trident evidence; do not rebuild from scratch and do not treat report shape, smoke, proxy, synthetic, planned, or copied historical rows as success.
- Mission: multi-step Qwen Preference Compiler, RuntimeRuleState/Monitor primitives, Preference Shield, High-Quality Order Hunter, minimal ROI-positive repair, full official ablation, and phase-aware completion proof.
- Valid stop states are only `PREF_FORGE_CROWN_TARGET_READY`, `PREF_FORGE_RECOMMENDED_SUBMISSION_READY`, `PREF_FORGE_EXPERIMENTAL_SUBMISSION_READY`, `PREF_FORGE_HIDDEN_SAFE_REVIEW_READY`, `PREF_FORGE_DO_NOT_SUBMIT_WITH_EVIDENCE`, `EXTERNAL_BLOCKER_EVAL_INFRA`, `EXTERNAL_BLOCKER_QWEN_API`, `EXTERNAL_BLOCKER_GIT_OR_NETWORK`, or `EXTERNAL_BLOCKER_MISSING_DATA`.
- Final `reports/` artifacts are limited to exactly `pref_forge_final_report.md`, `pref_forge_compile_benchmark.csv`, `pref_forge_experiment_grid.csv`, `pref_forge_penalty_diff.csv`, and `pref_forge_package_audit.md`.
- Mandatory verifier commands: `python tools/pref_forge_verify_completion.py --phase benchmark`, `--phase noop`, `--phase experiments`, and `--phase final`. Final mode must fail on incomplete mandatory rows, fewer than 60 executed full 20260529 grid rows, wrong package policy, raw literal leakage, or stop-state inconsistency.
- B0 rescue gate: 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected. If B0 fails due to code/config drift, fix it before continuing.
- No-op isolation gate: E1/E2 must match E0 with action_signature_match_rate >= 0.999, score deltas <= 100, and 0 failure/abort/illegal/rejected before strategy search.
- E5 High-Quality Hunter is a hard gate: if gross_minus_cost is below both B0_gross + 3000 and 48000, stop to fix Hunter rather than expanding E6-E13. If penalty_delta_vs_B0 > 8000, kill or retune Hunter.
- Mandatory rows E0-E13 and at least 60 additional full 20260529 executed grid rows are required unless a true external eval-infra blocker is documented.
- Qwen numeric auditor remains OFF by default. Qwen may compile preferences, link observed vocabulary, and perform gated relation/match audits only; it must not choose, veto, output final actions, or invent penalty amounts/caps.
- Real Qwen compile/link is required for non-empty preferences when an injected or environment API path exists. Do not set `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evidence.
- Public preference raw text, raw driver/cargo ids, raw place/category literals, fixed coordinates, future cargo, offline heatmaps, reports, scorer outputs, and raw Qwen IO must stay out of committed runtime/reports/packages. Use hashes, `.private/pref_forge/`, and abstract primitive family names.
- Runtime under `demo/agent` must not read raw cargo/driver data, reports, oracle artifacts, scorer internals, income calculators, server/bench internals, or future cargo.
- `query_cargo` must be followed by `refresh_world`; filtering, scoring, action certificates, B0 shadow, and `take_order` must use the same post-query `current_actionable` observed set. B0 shadow must be pure with no extra API calls or Qwen calls.
- Packages are forbidden unless weak improvement is reached. Weak-but-not-experimental may create only `CROWN_PREF_FORGE_REVIEW_ONLY_NOT_FOR_SUBMISSION.zip`; otherwise no zip.
- Subagents/reviewers are read-only QA gates. Required scopes: Instruction Compliance Auditor, Preference Compiler Auditor, Runtime Integration Auditor, Execution Evidence Auditor, and Leakage/Package Gatekeeper; findings must cite files, CSV rows, commands, exit codes, and metrics.

---

# Historical Build Rules

# CROWN-FUSE / RESCUE-SWITCH v10 Active Build Rules

- Active build: CROWN-FUSE / RESCUE-SWITCH v10 on branch `crown-fuse-rescue-switch`.
- Continue from the existing repository and the executed Surge evidence; do not rebuild from scratch and do not extend Delta-MPC, TCM, PTT, Trident, or broad new architecture names.
- Mission: find the B0 `best_rescue` + B9c targeted-repair knee point, preserving most B0 gross while taking only profitable penalty reduction.
- Known reference: B0 official_net `5067.69`, gross_minus_cost `43207.69`, preference_penalty `38140.0`, 89 take / 163 wait / 0 reposition, 0 failure/abort/illegal/rejected.
- Known reference: B9c_wait_repair_full official_net `-157.97`, gross_minus_cost `29142.03`, preference_penalty `29300.0`; it reduced penalty by `8840` but lost `14065.66` gross.
- Valid stop states are only `FUSE_RECOMMENDED_SUBMISSION`, `FUSE_EXPERIMENTAL_SUBMISSION`, `FUSE_REVIEW_PACKAGES_ONLY`, `DO_NOT_SUBMIT_WITH_FUSE_EVIDENCE`, `EXTERNAL_BLOCKER_RESCUE_ISOLATION`, `EXTERNAL_BLOCKER_EVAL_INFRA`, or `EXTERNAL_BLOCKER_QWEN`.
- No `PLANNED`, `MISSING_RUN`, `planned_not_evaluated`, proxy-only, diagnostic-only, smoke-only, synthetic-only, or report-only row may satisfy completion.
- `tools/verify_fuse_completion.py` is mandatory. It must pass `--phase isolation`, `--phase search`, and `--phase final` before any success claim or package claim.
- Final `reports/` artifacts are limited to at most `fuse_final_report.md`, `fuse_grid.csv`, `fuse_noop_isolation.csv`, `fuse_rule_ledger.csv`, and `fuse_package_audit.md`.
- B0 rescue gate: 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected. If B0 fails due to code/config drift, fix it before continuing.
- No-op isolation gate: `B1_all_overlays_off`, `B2_contract_compile_logging_only`, and `B3_contract_monitor_no_score` must match B0 with action_signature_match_rate >= 0.999, score deltas <= 100, and take/wait/reposition counts within deterministic tolerance <= 1.
- Do not run fuse search until B0/B1/B2/B3 no-op isolation passes.
- Qwen preference contract compile/link stays ON for real non-empty preferences when an API path exists. Do not set `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evidence.
- Qwen numeric auditor score adjustment defaults OFF. Only enable it if A1/A2 official ablation beats auditor OFF with json_valid_rate >= 0.90 and nonzero adjustment > 0.
- Qwen may compile contracts, link observed vocabulary, and log/explain gated candidate audits only; it must not choose, veto, or output final actions.
- Targeted repair overlay may override B0 only when expected_avoided_penalty >= lost_gross * repair_roi_threshold, daily repair budget is available, gross floor is intact, and the B0 action is not high-profit high-confidence.
- B0 Shadow Guard is mandatory for non-B0 Fuse variants: compute B0_action and new_action from the same post-query world/current_actionable snapshot, then fall back to B0 unless ROI/gross/legality guards pass.
- Runtime under `demo/agent` must not read raw cargo/driver data, reports, oracle artifacts, exact labels, scorer outputs, income calculators, server/bench internals, or future cargo.
- Runtime must not import `server.*`, `bench.*`, scorer internals, income-calculation internals, or local evaluation helpers.
- `query_cargo` must be followed by `refresh_world`; filtering, scoring, action certificates, and `take_order` must use the post-query world.
- `take_order` can only use cargo from the current post-query `current_actionable` observed set. `no_query` cannot take remembered cargo.
- Destination Shadow Query remains OFF.
- Reposition coordinates keep full precision and must not be rounded in action output.
- Runtime must not hardcode driver ids, cargo ids, static place names, fixed coordinates, fixed routes, route templates, offline heatmaps, public protected literals, or future-cargo facts.
- `reports/fuse_rule_ledger.csv` may export only generic family-level parameters: controller_family_scale, primitive_family_scale, counting_unit_scale, deadline_curve, repair_multiplier, already_failed_discount, and cap_discount.
- Fuse grid must include at least 60 complete 20260529 31-day official runs, all `status=EXECUTED`. If any variant improves net by >= 3000 or lowers penalty by >= 3000 with gross >= 39000, continue to at least 100 full configs.
- Opportunity graph is tiny diagnostic only: alpha 0/0.03/0.05/0.10, take ranking only, no graph-driven wait/reposition, no auditor numeric, no preference controller change. Keep only if official net improves without penalty explosion.
- Top 5 20260529 configs must run full 20260509 sanity before package recommendation. Any income abort disqualifies recommended packaging.
- B10 and B11 are mandatory executed rows. B11 must be a fresh full 31-day run after code/config freeze; if no search variant beats B0, B11 is an explicit B0 fallback rerun.
- Subagents/reviewers are read-only QA gates only: Execution Evidence Auditor, Rescue Isolation Auditor, Fuse Grid Auditor, Qwen Auditor Reviewer, and Package Gatekeeper. Each must cite CSV rows, run_dir, commands, exit codes, and metrics.
- Packages go under `runs/packages/`, must be unpack-audited, root must be `demo/`, include `demo/agent/` and `demo/SUBMISSION.md`, exclude server/data/reports/runs/archive/docs/keys/prompts/pyc/cache, and record SHA256/size.
- If no recommended or experimental gate passes, create at most one `REVIEW_ONLY_NOT_FOR_SUBMISSION` zip and make `demo/SUBMISSION.md` start with `NOT RECOMMENDED FOR B榜 SUBMISSION`.

# CROWN-SURGE / LEDGER-HUNTER Build Rules

- Active build: CROWN-SURGE / LEDGER-HUNTER on branch `crown-surge-ledger-hunter`.
- This round continues from the existing repository and the failed `crown-trident-gold2` evidence. Do not rebuild from scratch.
- The only valid proof is executed official-score evidence: no `PLANNED`, `MISSING_RUN`, `planned_not_evaluated`, smoke-only, synthetic-only, diagnostic-only, or report-only completion may be treated as success.
- Valid stop states are only `SURGE_RECOMMENDED_SUBMISSION`, `SURGE_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_SURGE_EVIDENCE`, `DO_NOT_SUBMIT_WITH_INCOMPLETE_EXECUTION`, `EXTERNAL_BLOCKER_RESCUE_CORE`, `EXTERNAL_BLOCKER_QWEN`, or `EXTERNAL_BLOCKER_EVAL_INFRA`.
- Final `reports/` artifacts are limited to exactly `surge_final_report.md`, `surge_experiments.csv`, `surge_decision_deltas.csv`, `surge_rule_doctor.csv`, and `surge_qwen_effect.csv`.
- `tools/verify_surge_completion.py --phase final` must PASS before any success claim or package creation. Final mode must fail on missing B0-B9c/B10/B11 evidence, fewer than 100 executed parameter trials, all-zero Qwen auditor adjustment when auditor is enabled, diagnostic-only decision deltas used for tuning, missing B7/B8 graph usage, report head mismatch, package gate violation, or final report hygiene violation.
- B0 immutable rescue must reproduce 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected before any Surge overlay evidence is meaningful.
- Required official matrix rows are B0, B1, B2, B3, B4, B5, B6, B7, B8, B9a, B9b, B9c, B10, and B11; every row must include official_net, gross_minus_cost, preference_penalty, action mix, Qwen stats, controller stats, run_dir, command, and exit_code.
- Parameter search must execute Stage A 100 real 20260529 trials, Stage B top20 full 31-day, Stage C top5 0509 sanity, and Stage D top10 rerun confirmation. No trial row may be planned.
- Qwen runtime calls are mandatory for non-empty preferences when an API path exists. Do not set `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evidence. Qwen timeout is 120 seconds with up to 3 retries; use cache/batching rather than disabling Qwen.
- Qwen may compile contracts, link observed vocabulary, and audit gated candidates only. It must output schema-valid JSON relation/effect/risk_score/repair_score/confidence and must not choose or veto final actions.
- If Qwen auditor calls are present but numeric adjustment is all zero, stop `DO_NOT_SUBMIT_WITH_QWEN_DECORATION` as the reason inside `DO_NOT_SUBMIT_WITH_INCOMPLETE_EXECUTION`; kill auditor unless an ablation proves it useful.
- Changed-decision tuning requires official or runtime-replan-valid delta labels. Diagnostic-only labels must never tune controller scale.
- Rule doctor may export only controller_family, primitive_family, counting_unit, deadline curve, repair multiplier, cap discount, and already-failed discount level parameters. Never export rule_hash, driver_hash, preference_hash, cargo_id, place, coordinate, route, or future-cargo facts.
- Online Opportunity Graph may use only current post-query `current_actionable` cargo and same-driver current-run legal observations. It must not use offline heatmaps, future cargo, fixed places, fixed coordinates, fixed routes, route templates, driver ids, or cargo ids. B7/B8 and terminal_value_alpha 0.00/0.05/0.10/0.20/0.35 must be executed before retaining graph.
- Subagents/reviewers are QA gates only, not parallel implementers. Required reviewer scopes are Prompt-Adherence, Qwen Auditor, Penalty Delta, Opportunity Graph, Compliance, and Completion Gatekeeper, each with concrete file paths, CSV row/count evidence, commands, and pass/fail findings.
- Low score or incomplete evidence forbids a submission-shaped ZIP. If final official_net < 30000 or evidence is incomplete, the first line of `reports/surge_final_report.md` must be `DO NOT SUBMIT: <precise reason>`.

# CROWN-TRIDENT / GOLD-2 Build Rules

- Active build: CROWN-TRIDENT / GOLD-2 on branch `crown-trident-gold2`.
- The objective is official-score causality, not architecture appearance: every retained rule, controller, Qwen auditor adjustment, decision change, and online graph parameter must prove positive official-net or named regret reduction.
- Valid stop states are only `CROWN_TRIDENT_RECOMMENDED_SUBMISSION`, `CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE`, `EXTERNAL_BLOCKER_QWEN`, `EXTERNAL_BLOCKER_RESCUE_CORE`, `EXTERNAL_BLOCKER_EVAL_INFRA`, or `DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE`.
- Tests passing, legal actions, Qwen smoke, synthetic pass, reports, package shape, macro counts, Qwen call counts, controller counts, and 0 illegal are not success.
- Default runtime/package variant must be the final selected Trident strategy only after full ablation evidence. It must preserve immutable rescue legality/profit behavior unless a generic, runtime-only overlay proves score-positive.
- First broken link to diagnose: decision changed -> official preference penalty reduced. Gold had official_net 6373.17, gross_minus_cost 45993.17, preference_penalty 39620.00, and worsened penalty versus rescue.

## Runtime Boundary

- Runtime code under `demo/agent` may use only injected `SimulationApiPort` for state, cargo, history, and model calls.
- Runtime code must not read raw cargo or driver datasets, reports, oracle artifacts, exact-label artifacts, benchmark internals, income calculators, scorer outputs, action traces, or future cargo availability.
- Runtime code must not import `server.*`, `bench.*`, scoring internals, income-calculation internals, or local evaluation helpers.
- Runtime code must not hardcode driver ids, cargo ids, static place names, fixed routes, fixed route sequences, fixed coordinates, offline heatmaps, scenario shortcuts, or route templates.
- Protected example terms and scenario shortcut words are read-only context. Repository files must use `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash` instead of literal values.
- Every `query_cargo` call must be followed by `refresh_world`.
- Filtering, scoring, action certificates, and `take_order` must use the post-query world and the current post-query `current_actionable` observed set.
- `take_order` can only use cargo from the current decision's post-query `current_actionable` set.
- `no_query` cannot take remembered cargo.
- Shadow or historical cargo must never enter actionable candidates.
- Destination Shadow Query is OFF.
- Reposition coordinates must keep full precision and must not be rounded.
- Unknown or low-confidence preferences are soft risk unless scorer-aligned controller evidence proves high-confidence violation. UnknownSoft never hard-blocks high-gross actions.

## Qwen Contract Rules

- Real Qwen runtime calls are mandatory for non-empty driver preferences when an API path is available.
- Do not set or rely on `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evaluation. Do not set Qwen budget to 0. Do not use smoke-only compile evidence, dummy cache, fallback-only compile, or dummy key state as success.
- API order is injected `SimulationApiPort.model_chat_completion`, then compatible endpoint using `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`.
- Qwen timeout is 120 seconds with up to 3 retries. Use cache and batching instead of lowering the requirement.
- Qwen roles are limited to Preference Contract Compiler, Observed Vocabulary Linker, and gated Candidate Auditor.
- Qwen must not output, veto, or choose final actions; it may only compile/link/audit and produce numeric score adjustments through deterministic runtime mapping.
- Preference Contract V2 output must include `rule_id`, `polarity`, `observable`, `scope`, `metric`, `counting`, `slots`, `repair`, `confidence`, `evidence_hash`, and `uncertainty`.
- Qwen must not invent penalty amount or cap. Unknown penalty scale must be recorded as `null` with source `unknown`.
- Every non-empty `preference_hash` must be compiled by real Qwen or served from a real Qwen-derived cache.
- Final full runs require qwen compile/cache > 0, link/cache > 0, auditor calls > 0, and nonzero auditor adjustments unless an ablation explicitly kills auditor OFF as better.
- Runtime Qwen inputs may transiently contain current preference text and current visible cargo vocabulary, but persistent logs/reports/code must hash or redact runtime values.

## Trident Runtime Order

- Runtime order is refresh world, compile/cache Preference Contract V2, update rule-state controllers, preserve rescue macro commitments, query, refresh/filter, observed vocabulary linking, candidate generation, Preference Firewall, gated auditor, deterministic scoring, optional runtime-only online graph, safety finalize.
- Observed Vocabulary Linker runs after each query when preferences and visible cargo exist; it may use only current query visible vocabulary.
- Committed linker, auditor, and contract artifacts must hash or redact runtime values.
- Preference Firewall runs before profit ranking and must score take, wait, reposition, and repair candidates.
- Every candidate score must account for past debt, candidate delta, future repairability delta, marginal penalty, repair value, lost repair-window cost, unknown-soft risk, Qwen audit adjustment, time/query/reposition cost, and execution risk.
- Already failed or capped rules must not repeatedly destroy gross. Still-repairable high-penalty rules must price future repair windows.
- High-confidence per-action violations may be blocked or dominate-negative only when scorer semantics are verified and penalty scale is explicit or calibrated.
- Profit backbone is the immutable rescue/safe-profit core. Preference overlays that reduce penalty while collapsing gross must be retuned or disabled.

## Scorer And Controller Coverage

- T01-T18 controller coverage must remain available: daily continuous rest, scheduled quiet window, full inactive day quota, no-order day quota, forbidden cargo attribute, required cargo attribute distinct days, pickup deadhead limit, haul distance limit, cumulative deadhead budget, daily order count limit, first order start deadline, location visit or dwell, ordered multi-stop task, stay target window, unknown soft, region avoid/require, runtime entity task, and daily work pattern.
- Every controller must expose update, satisfied, failed, remaining slack, marginal cost, repair value, repair candidates, dynamic lambda, and final penalty lower bound.
- Scorer microprobes are mandatory before hard blocks, massive penalties, large repair values, or commitments.
- Required probe families include wait/rest, scheduled quiet/rest, inactive/no-order day, field avoid/required distinct days, location/dwell/stay, ordered sequence, distance/count/deadline, cap/already_failed behavior, query inside wait/rest, and reposition active behavior.
- ScorerSemanticsAdapter gates hard blocks and massive penalties. Unverified controller semantics downgrade to soft risk or diagnostic-only.
- Hard metrics for success include controller-scored candidates, candidate-rule evaluations, score changes, decision changes, and official counterfactual deltas. Zero or negative causal effect is failure evidence.

## Online Opportunity Graph

- Online Opportunity Graph may use only current query `current_actionable` cargo and same-driver legal observed summaries from the current run.
- Cell statistics start empty for each driver and are built online only from numeric lat/lng cells; no static city names, offline-seeded priors, cell whitelists, future cargo, or route shortcuts.
- It may evaluate single take, visible A-to-B pairs, wait-then-A, A-then-rest, route-start reposition-then-A, and preference reposition-then-wait/take.
- Execute only the first step, then query and revalidate next round.
- Only generic smoothing, decay, alpha, thresholds, and weights may be exported. Test alpha 0.05, 0.10, 0.20, and 0.35.
- Graph remains OFF unless ablation proves gross uplift without preference penalty explosion and official-net improvement.

## Required Evidence

- Stage 0 must reproduce score accounting for B0 rescue, money greedy, strict preference, safe-profit greedy, and current Gold if available; confirm official_net = gross_minus_cost - preference_penalty and forbid proxy double counting.
- B0 rescue gate: 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected. If runner/data/eval infrastructure is unavailable, stop `EXTERNAL_BLOCKER_RESCUE_CORE`.
- Stage 1 must produce `reports/trident_rule_ledger.csv` with rule-level official penalty, deltas, state, score usage, missed repair, best counterfactual fix, and keep/kill.
- Stage 2 must produce `reports/trident_decision_deltas.csv` with official replay/counterfactual deltas, validity labels, Qwen/controller reasons, win/loss/unknown, and top good/bad changes.
- Stage 4 must produce `reports/trident_qwen_effect.csv`; auditor calls with all zero adjustments are not implemented.
- Stage 6 must run B0-B11 official ablations; do not skip B1-B8 because a later variant fails.
- Stage 7 must run rule-level doctor ablations for top penalty rules.
- Stage 8 may distill only generic statistics from high-score trajectories; do not copy ids, fixed locations, coordinates, routes, or future cargo facts into runtime.
- Stage 10 must run 100 parameter trials when feasible, or record infrastructure limitations and strongest completed evidence.

## Reports And Records

- Final `reports/` artifacts are limited to exactly:
  - `reports/trident_final_report.md`
  - `reports/trident_experiments.csv`
  - `reports/trident_rule_ledger.csv`
  - `reports/trident_decision_deltas.csv`
  - `reports/trident_qwen_effect.csv`
- Old reports go under `archive/`; raw outputs stay under `runs/`.
- Durable working records live in `docs/AGENT_WORK/PROJECT_MEMORY.md`, `docs/AGENT_WORK/EXPERIMENT_LOG.md`, and `docs/AGENT_WORK/EXECUTION_PLAN.md`.
- Final report must include the first broken link table: Qwen contract valid -> observed vocab linked -> candidate scored -> score changed -> decision changed -> official penalty reduced -> gross preserved -> official net improved.
- If final score is below experimental gate, the first line of `reports/trident_final_report.md` must be `DO NOT SUBMIT: <precise reason>`.

## Subagents And Reviewers

- Real Codex subagents or recorded independent reviewer passes are mandatory.
- Required named scopes: Rescue Baseline Keeper, Penalty Attribution / Regret Lab, Preference Contract / Qwen Auditor Engineer, Profit Backbone / Online Graph Engineer, Parameter Search / Ablation Engineer, and Compliance / Package Gatekeeper.
- Each subagent/reviewer must return `changed_files`, `commands_run`, `metrics_before_after`, `pass_fail_against_task`, `unresolved_blockers`, and `recommend_keep_or_kill`.
- If neither real subagents nor recorded named reviewer passes exist for required missions, stop `DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE`.

## Packaging

- Build a submission package only if experimental or recommended Trident gates pass.
- If final official_net < 30000, do not create a submission-shaped zip; write DO NOT SUBMIT evidence.
- ZIP root must be `demo/`, include `demo/agent/` and `demo/SUBMISSION.md`, and exclude server, data, results, reports, runs, archive, docs, local config, keys, prompts, and pyc files.
- Package inspection must confirm default variant is final selected strategy.

## Score Gates

- Experimental submission requires 20260529 official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 50000, 0 abort/illegal/rejected, nonzero Qwen auditor adjustment if auditor is used, and clean controller/ablation/compliance evidence.
- Recommended submission requires 20260529 official_net >= 38000, preference_penalty <= 22000, gross_minus_cost >= 60000, 0 abort/illegal/rejected, and 0509 clean enough for sanity.
- Crown target is official_net >= 40000, preference_penalty around 18000-22000 or lower, and gross_minus_cost around 58000-65000 or higher.

## Resource Rules

- Keep local and cloud compute isolated to this project.
- Prefer cloud only when available without disrupting other users; first check `nvidia-smi`, CPU load, and active jobs.
- Avoid heavy local load that can freeze the PC.
- Use GPU only if materially useful and after checking availability.
- Never disrupt other users' jobs or kill unrelated processes.
