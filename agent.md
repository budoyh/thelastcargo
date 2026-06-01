# Agent Operating Rules

This lowercase rule file mirrors `AGENTS.md` for tools that look for `agent.md`.

## Active Build

- Branch: `crown-exact-rbt-mpc`.
- Task: CROWN-EXACT = Rule Bytecode Transducer + Scorer-Semantic Controllers + Visible Opportunity Graph MPC.
- Honest stop states: `CROWN_EXACT_RECOMMENDED_SUBMISSION`, `CROWN_EXACT_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE`, `EXTERNAL_BLOCKER`.
- Success is score-gated and semantics-gated. Tests, legal actions, Qwen smoke, reports, synthetic pass, and macro counts are insufficient.
- Default runtime/package variant must be `crown_exact_rbt_mpc`, not `best_rescue` or `preference_firewall_profit`.
- Do not lower-config the requested RBT/controller/MPC build.

## Long-Lived Compliance Rules

- Runtime under `demo/agent` must not read raw cargo/driver data, reports, oracle artifacts, exact labels, income calculators, benchmark internals, or future cargo availability.
- Runtime must not import `server.*`, `bench.*`, scoring internals, or income-calculation internals.
- Runtime must not hardcode driver ids, cargo ids, static place names, fixed route sequences, fixed coordinates, offline heatmaps, or scenario shortcuts.
- Protected example terms and scenario shortcut words must not be copied into repository files. Use `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash`.
- Qwen3.5-Flash Rule Bytecode Transducer stays ON for non-empty preferences when an API path is available.
- Do not set or rely on `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evaluation. Do not use dummy cache, smoke-only compile, fallback-only compile, or zero compile budget as success.
- Qwen roles are RBT compiler, observed-vocabulary linker, and gated candidate auditor only. Qwen must not output final actions.
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

## CROWN-EXACT Rules

- Runtime order is refresh world, compile/cache RBT bytecode rules, update controllers, macro commitments, query, refresh/filter, observed vocabulary linking, generate candidates, Preference Firewall, gated auditor, deterministic scoring, optional visible graph MPC, safety finalize.
- Qwen RBT pipeline is extract constraints, fill slots, generate bytecode, validate executability, critique/repair once, schema validate, and cache.
- Qwen must not invent penalty amount or cap; missing penalty is explicit unknown and uses generic fallback scale.
- T01-T18 controller coverage is mandatory: daily rest, scheduled quiet, inactive/no-order quotas, forbidden/required attributes, distance and count limits, deadline, location/dwell/order/window tasks, unknown soft, region, runtime entity, and daily work pattern.
- Each controller exposes update, satisfied, failed, remaining slack, marginal cost, repair value, generate repair candidates, dynamic lambda, and final penalty lower bound.
- ScorerSemanticsAdapter gates hard blocks and massive penalties. Unverified semantics are soft risk only.
- UnknownSoft never hard-blocks high-gross actions.
- Preference Firewall must run before profit ranking and trace marginal penalty, repair value, lost repair-window cost, future failure probability delta, confidence, and decision.
- Visible Graph MPC is default OFF until ablation proves score uplift or penalty reduction without gross collapse.

## Records, Reports, Reviews

- Durable records live under `docs/AGENT_WORK/`.
- Final `reports/` contains at most five CROWN-EXACT artifacts:
  `exact_final_report.md`, `exact_experiments.csv`, `scorer_semantics_probe.csv`, `rule_bytecode_coverage.csv`, and `decision_forensics.csv`.
- Old reports are archived, not deleted.
- Required real subagent scopes: Prompt-Adherence, Compliance/Future-Info, Qwen/RBT, Scorer-Semantics, Planner/Score, and Package Gatekeeper.
- If true subagents are unavailable, stop as `EXTERNAL_BLOCKER`.

## Packaging And Stop Honesty

- Recommended package may be built only if CROWN-EXACT gates pass.
- Failed-gate inspection zips must include `NOT_RECOMMENDED_DO_NOT_SUBMIT` in the filename and must not be recommended.
- Submission ZIP root is `demo/`; include only `demo/agent/` and `demo/SUBMISSION.md`; exclude server, data, results, reports, runs, archive, docs, keys, local config, prompt docs, and pyc.
- `CROWN_EXACT_RECOMMENDED_SUBMISSION` requires 20260529 official_net >= 30000, preference_penalty <= 22000, gross_minus_cost >= 45000, real Qwen compile/cache hit > 0, controller scored candidates > 0, scorer aligned controller > 0, P0 clean, 0509 no catastrophic regression, clean package inspection, complete reports, commit, and push.
- If score or semantic gates are not reached, write `DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE` as the first line of the final report.

## Resource Rules

- Keep local and cloud compute isolated to this project.
- Avoid heavy local load that can freeze the PC.
- Use GPU only if materially useful and after checking availability.
- Never disrupt other users' jobs.
