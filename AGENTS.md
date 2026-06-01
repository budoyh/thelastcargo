# CROWN-GOLD Contract-MPC Build Rules

- Active build: CROWN-GOLD on branch `crown-gold-contract-mpc`.
- Stop states are only `CROWN_GOLD_RECOMMENDED_SUBMISSION`, `CROWN_GOLD_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`, or `EXTERNAL_BLOCKER`.
- Do not present tests passing, legality, Qwen smoke, synthetic pass, reports, package shape, or macro counts as success.
- Default runtime/package variant must be `crown_gold_contract_mpc`; it must not default to `best_rescue`, `preference_firewall_profit`, PCE, Delta-MPC, or Exact.
- CROWN-GOLD is immutable rescue legality core plus real Qwen Preference Contract, Observed Vocabulary Linker, top-candidate Auditor, Preference Firewall, profit backbone, and Online Opportunity Graph MPC.

## Runtime Boundary

- Runtime code under `demo/agent` may use only injected `SimulationApiPort` for state, cargo, history, and model calls.
- Runtime code must not read raw cargo or driver datasets, reports, oracle artifacts, exact-label artifacts, benchmark internals, income calculators, or future cargo availability.
- Runtime code must not import `server.*`, `bench.*`, scoring internals, or income-calculation internals.
- Runtime code must not hardcode driver ids, cargo ids, static place names, fixed routes, fixed route sequences, fixed coordinates, offline heatmaps, or scenario shortcuts.
- Protected example terms and scenario shortcut words are read-only context. Repository files must use `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash` instead of literal values.
- Every `query_cargo` call must be followed by `refresh_world`.
- Filtering, scoring, action certificates, and `take_order` must use the post-query world and the current post-query `current_actionable` observed set.
- `no_query` cannot take remembered cargo.
- Shadow or historical cargo must never enter actionable candidates.
- Destination Shadow Query is OFF.
- Reposition coordinates must keep full precision; do not round action coordinates.

## Qwen Contract Roles

- Real Qwen runtime calls are mandatory for non-empty driver preferences when an API path is available.
- Do not set or rely on `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evaluation, do not set Qwen budget to 0, and do not use smoke-only compile evidence as success.
- API order is injected `SimulationApiPort.model_chat_completion`, then compatible endpoint using `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`.
- Qwen timeout is 120 seconds with up to 3 retries; use cache and batching instead of lowering the requirement.
- Qwen roles are limited to Preference Contract Compiler, Observed Vocabulary Linker, and gated Candidate Auditor.
- Qwen must not output or choose the final action.
- Preference Contract Compiler output must include `polarity`, `observable`, `scope`, `metric`, `counting`, `slots`, `severity`, `repair_actions`, `confidence`, `uncertainty`, and `evidence_hash`.
- Qwen must not invent penalty amount or cap; if API/preference metadata does not state a penalty, record `null` with source `unknown`.
- Every non-empty `preference_hash` must be compiled by real Qwen or served from a real Qwen-derived cache.

## Gold Runtime Order

- Runtime order is refresh world, compile/cache Preference Contract rules, update controllers, preserve rescue macro commitments, query, refresh/filter, observed vocabulary linking, candidate generation, Preference Firewall, gated auditor, deterministic scoring, optional visible graph MPC, safety finalize.
- Observed Vocabulary Linker runs after each query when preferences and visible cargo exist; it may use only the current query result's visible vocabulary.
- Committed linker and contract artifacts must hash or redact runtime values.
- Preference Firewall runs before profit ranking and must score take, wait, reposition, and repair candidates.
- Every candidate score must account for marginal penalty, repair value, lost repair-window cost, unknown-soft risk, Qwen audit adjustment, time/query/reposition cost, and execution risk.
- High-confidence per-action violations may be blocked or dominate-negative only when scorer semantics are verified and penalty scale is explicit or calibrated.
- Required or repair candidates receive repair value.
- UnknownSoft never hard-blocks high-gross actions, but high-penalty low-confidence risk must not be priced as tiny risk.

## Controller And Scoring Coverage

- T01-T18 controller coverage must remain available: daily continuous rest, scheduled quiet window, full inactive day quota, no order day quota, forbidden cargo attribute, required cargo attribute distinct days, pickup deadhead limit, haul distance limit, cumulative deadhead budget, daily order count limit, first order start deadline, location visit or dwell, ordered multi-stop task, stay target window, unknown soft, region avoid/require, runtime entity task, and daily work pattern.
- Every controller must expose update, satisfied, failed, remaining slack, marginal cost, repair value, generate repair candidates, dynamic lambda, and final penalty lower bound.
- ScorerSemanticsAdapter gates hard blocks and massive penalties. Unverified controller semantics downgrade to soft risk.
- Hard metrics for success include controller-scored candidates, candidate-rule evaluations, score changes, and decision changes; zero values are failure evidence.
- Profit backbone is the immutable rescue/safe-profit core. Preference layers that reduce penalty while collapsing gross must be retuned or disabled.

## Online Opportunity Graph MPC

- Online Opportunity Graph MPC may use only current query `current_actionable` cargo and same-driver legal observed summaries from the current run.
- It may evaluate single take, visible A-to-B pairs, wait-then-A, A-then-rest, route-start reposition-then-A, and preference reposition-then-wait/take.
- Execute only the first step, then query and revalidate next round.
- Offline heatmaps, fixed cities, fixed coordinates, fixed routes, future cargo, and driver/cargo shortcuts are forbidden.
- MPC remains default OFF unless ablation proves score uplift or named regret reduction without gross collapse.

## Reports And Records

- Final `reports/` artifacts are limited to at most:
  - `reports/gold_final_report.md`
  - `reports/gold_experiments.csv`
  - `reports/gold_qwen_contract_audit.csv`
  - `reports/gold_decision_forensics.csv`
  - `reports/gold_package_audit.md`
- Old reports go under `archive/`; run outputs stay under `runs/`.
- Durable working records live in `docs/AGENT_WORK/PROJECT_MEMORY.md`, `docs/AGENT_WORK/EXPERIMENT_LOG.md`, and `docs/AGENT_WORK/EXECUTION_PLAN.md`.
- Real reviewer checks are mandatory for Prompt-Adherence, Compliance/Future-Info, Rescue-Core Reproduction, Qwen Preference Contract, Candidate Firewall/Scoring, Opportunity Graph/MPC, and Package Gatekeeper.
- If true subagents are unavailable, stop as `EXTERNAL_BLOCKER`; do not simulate reviewer success.

## Packaging

- Build a recommended submission package only if CROWN-GOLD gates pass.
- Build an experimental package only if CROWN-GOLD experimental gates pass and label it experimental.
- If gates fail, do not create a submission-shaped zip; write `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`.
- ZIP root must be `demo/`, include `demo/agent/` and `demo/SUBMISSION.md`, and exclude server, data, results, reports, runs, archive, docs, local config, keys, prompts, and pyc files.
- Package inspection must confirm default variant is `crown_gold_contract_mpc`.

## Verification

- Required checks before final handoff include pytest, compileall, audit guard, Qwen smoke or real-call evidence, baselines, ablation evidence, package audit or no-package rationale, reviewer gate, commit, and push.
- `CROWN_GOLD_RECOMMENDED_SUBMISSION` requires 20260529 official_net >= 40000, preference_penalty <= 22000, gross_minus_cost >= 52000, real Qwen compile/link/audit > 0, controller_scored > 1000, score_changed > 100, changed_decision > 20, 0 failure/abort/illegal/rejected, 0509 no catastrophic regression, default variant `crown_gold_contract_mpc`, clean package audit, complete reports, commit, and push.
- `CROWN_GOLD_EXPERIMENTAL_SUBMISSION` requires 20260529 official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 45000, and all Qwen/controller/compliance gates.
- If gates are not met, first line of `reports/gold_final_report.md` must be `DO NOT SUBMIT: gold gates not reached.`

## Resource Rules

- Keep local and cloud compute isolated to this project.
- Prefer cloud only when available without disrupting other users; first check `nvidia-smi`, CPU load, and active jobs.
- Avoid heavy local load that can freeze the PC.
- Use GPU only if materially useful and after checking availability.
- Never disrupt other users' jobs or kill unrelated processes.
