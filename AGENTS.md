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
