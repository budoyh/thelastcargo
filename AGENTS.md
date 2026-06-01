# CROWN-PTT-GreedyMPC Build Rules

- Active build: CROWN-PTT-GreedyMPC on branch `crown-ptt-firewall-profit`.
- Stop states are only `PTT_SUBMISSION_READY`, `PTT_DIAGNOSTIC_SUCCESS_DO_NOT_SUBMIT`, or `EXTERNAL_BLOCKER`.
- Do not present tests passing, legality, Qwen smoke, report completeness, predicate recall, or macro counts as success.
- Default runtime/package variant must be `preference_firewall_profit`; it must not default to `best_rescue`.
- The build is Preference Type Transducer, deterministic controllers, action-level Preference Firewall, macro calendar commitments, and profit-greedy freight MPC. Do not build Delta-MPC or TCM Max.

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

## Qwen Roles

- Qwen3.5-Flash Preference Type Transducer must remain ON for non-empty preferences when an API path is available.
- API order is injected `SimulationApiPort.model_chat_completion`, then compatible endpoint using `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`.
- Never print, commit, synthesize, or treat dummy keys as success.
- Qwen roles are limited to Preference Type Transducer, Observed Vocabulary Linker, and gated Candidate Auditor.
- Qwen must not output or choose the final action.
- PTT compile pipeline is extract constraints, fill slots, validate executability, critique/repair once, schema validate, and cache.
- Qwen must not invent penalty amount or cap; missing penalty is marked unknown and priced by generic fallback scale.

## PTT Runtime Order

- Runtime order must be: refresh world, compile/cache PTT rules, update controllers, macro commitments, query, refresh/filter, observed vocabulary linking, candidate generation, Preference Firewall, gated auditor, deterministic scoring, safety finalize.
- Observed Vocabulary Linker may use only the current query result's visible vocabulary. Committed artifacts must hash or redact values.
- Preference Firewall runs before profit ranking and must score every take, wait, reposition, and macro candidate with marginal penalty, repair value, lost repair-window cost, failure-probability delta, confidence, and decision.
- High-confidence per-action violations must be blocked or massively penalized when scorer semantics are aligned. Unverified semantics are soft risk only.
- Required/repair candidates get repair value. UnknownSoft never hard-blocks high-gross actions but cannot be priced as tiny risk when penalty scale is high.

## Controller Coverage

- T01-T18 must remain available: daily continuous rest, scheduled quiet window, full inactive day quota, no order day quota, forbidden cargo attribute, required cargo attribute distinct days, pickup deadhead limit, haul distance limit, cumulative deadhead budget, daily order count limit, first order start deadline, location visit or dwell, ordered multi-stop task, stay target window, unknown soft, region avoid/require, runtime entity task, daily work pattern.
- Every controller must expose update, satisfied, failed, remaining slack, marginal cost, repair value, generate repair candidates, dynamic lambda, and final penalty lower bound.
- ScorerSemanticsAdapter gates hard blocks and massive penalties. Unverified controller semantics downgrade to soft risk.
- Hidden-style behavioral synthetic tests must cover compile, controller state, positive/negative/repair trajectories, paraphrase stability, runtime value replacement, and firewall score impact.

## Reports And Records

- Final `reports/` artifacts are limited to:
  - `reports/ptt_final_report.md`
  - `reports/ptt_experiments.csv`
  - `reports/ptt_compiler_coverage.csv`
  - `reports/ptt_decision_forensics.csv`
  - `reports/ptt_submission_audit.md`
- Old reports go under `archive/`; run outputs stay under `runs/`.
- Durable working records live in `docs/AGENT_WORK/PROJECT_MEMORY.md`, `docs/AGENT_WORK/EXPERIMENT_LOG.md`, and `docs/AGENT_WORK/EXECUTION_PLAN.md`.
- Reviewer checks are mandatory for prompt adherence, compliance/future-info, PTT semantics, controller/firewall, runtime score, packaging, and final audit. If true subagents are unavailable, perform simulated read-only reviews and record them.

## Packaging

- Build a recommended submission package only if PTT gates pass.
- If an inspection zip is produced after failed gates, its filename must include `NOT_RECOMMENDED_DO_NOT_SUBMIT`.
- ZIP root must be `demo/`, include `demo/agent/` and `demo/SUBMISSION.md`, and exclude server, data, results, reports, runs, archive, docs, local config, keys, prompts, and pyc files.
- Package inspection must confirm default variant is `preference_firewall_profit`.

## Verification

- Required checks before final handoff include pytest, compileall, audit guard, round-bug check, Qwen smoke, 20260529 and 20260509 31-day evaluations, PTT synthetic tests, PTT reports, package build/inspection if allowed, commit, and push.
- `PTT_SUBMISSION_READY` requires score-hard and semantics-hard gates, including 20260529 official net above rescue, preference penalty materially lower than rescue, gross-minus-cost not collapsed, 0509 no catastrophic regression, all T01-T18 tests, default PTT variant, clean package inspection, complete reports, commit, and push.
- If gates are not met, first line of final report must be `DO NOT SUBMIT: PTT gates not reached.` and stop as `PTT_DIAGNOSTIC_SUCCESS_DO_NOT_SUBMIT`.

## Resource Rules

- Keep local and cloud compute isolated to this project.
- Avoid heavy local load that can freeze the PC.
- Use GPU only if materially useful and after checking availability.
- Never disrupt other users' jobs.
