# Agent Operating Rules

This lowercase rule file mirrors `AGENTS.md` for tools that look for `agent.md`.

## Active Build

- Branch: `crown-ptt-firewall-profit`.
- Task: CROWN-PTT-GreedyMPC.
- Honest stop states: `PTT_SUBMISSION_READY`, `PTT_DIAGNOSTIC_SUCCESS_DO_NOT_SUBMIT`, `EXTERNAL_BLOCKER`.
- Success is score-gated and semantics-gated. Tests, legal actions, Qwen smoke, reports, predicate recall, and macro counts are insufficient.
- Default runtime/package variant must be `preference_firewall_profit`, not `best_rescue`.
- Do not lower-config the requested T01-T18 build.

## Long-Lived Compliance Rules

- Runtime under `demo/agent` must not read raw cargo/driver data, reports, oracle artifacts, exact labels, income calculators, benchmark internals, or future cargo availability.
- Runtime must not import `server.*`, `bench.*`, scoring internals, or income-calculation internals.
- Runtime must not hardcode driver ids, cargo ids, static place names, fixed route sequences, fixed coordinates, offline heatmaps, or scenario shortcuts.
- Protected example terms and scenario shortcut words must not be copied into repository files. Use `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash`.
- Qwen3.5-Flash Preference Type Transducer stays ON for non-empty preferences when an API path is available.
- Qwen roles are PTT compiler, observed-vocabulary linker, and gated candidate auditor only. Qwen must not output final actions.
- API priority is injected `SimulationApiPort.model_chat_completion`, then compatible endpoint using `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`.
- Never print or commit keys. Dummy or missing keys are fallback evidence, not success.

## Runtime Action Rules

- `query_cargo` must be followed by `refresh_world`.
- Filtering, scoring, and certificates must use the post-query `World`.
- `take_order` may only use cargo from the current decision's post-query `current_actionable` observed set.
- `no_query` cannot take remembered cargo.
- Shadow or historical cargo must never enter actionable candidates.
- Destination Shadow Query is OFF.
- Reposition action coordinates must keep full precision and must not be rounded.

## PTT Rules

- Runtime order is refresh world, compile/cache PTT rules, update controllers, macro commitments, query, refresh/filter, observed vocabulary linking, generate candidates, Preference Firewall, gated auditor, deterministic scoring, safety finalize.
- Qwen PTT pipeline is extract constraints, fill slots, validate executability, critique/repair once, schema validate, and cache.
- Qwen must not invent penalty amount or cap; missing penalty is explicit unknown and uses generic fallback scale.
- T01-T18 controller coverage is mandatory: daily rest, scheduled quiet, inactive/no-order quotas, forbidden/required attributes, distance and count limits, deadline, location/dwell/order/window tasks, unknown soft, region, runtime entity, and daily work pattern.
- Each controller exposes update, satisfied, failed, remaining slack, marginal cost, repair value, generate repair candidates, dynamic lambda, and final penalty lower bound.
- ScorerSemanticsAdapter gates hard blocks and massive penalties. Unverified semantics are soft risk only.
- UnknownSoft never hard-blocks high-gross actions.
- Preference Firewall must run before profit ranking and trace marginal penalty, repair value, lost repair-window cost, future failure probability delta, confidence, and decision.

## Records, Reports, Reviews

- Durable records live under `docs/AGENT_WORK/`.
- Final `reports/` contains at most five PTT artifacts:
  `ptt_final_report.md`, `ptt_experiments.csv`, `ptt_compiler_coverage.csv`, `ptt_decision_forensics.csv`, and `ptt_submission_audit.md`.
- Old reports are archived, not deleted.
- Required review scopes: prompt adherence, compliance/future-info, PTT semantic, controller/firewall, runtime score, packaging, and final audit.
- If true subagents are unavailable, run simulated read-only reviews and record findings in the final report.

## Packaging And Stop Honesty

- Recommended package may be built only if PTT gates pass.
- Failed-gate inspection zips must include `NOT_RECOMMENDED_DO_NOT_SUBMIT` in the filename and must not be recommended.
- Submission ZIP root is `demo/`; include only `demo/agent/` and `demo/SUBMISSION.md`; exclude server, data, results, reports, runs, archive, docs, keys, local config, prompt docs, and pyc.
- `PTT_SUBMISSION_READY` requires score-hard and semantics-hard gates, clean package inspection, complete reports, commit, and push.
- If score or semantic gates are not reached, write `DO NOT SUBMIT: PTT gates not reached.` as the first line of the final report.

## Resource Rules

- Keep local and cloud compute isolated to this project.
- Avoid heavy local load that can freeze the PC.
- Use GPU only if materially useful and after checking availability.
- Never disrupt other users' jobs.
