# Agent Operating Rules

This lowercase rule file mirrors `AGENTS.md` for tools that look for `agent.md`.

## Active Build

- Branch: `crown-gold-contract-mpc`.
- Task: CROWN-GOLD = restored immutable rescue core + real Qwen Preference Contract + Observed Vocabulary Linker + top-candidate Auditor + Preference Firewall + profit backbone + Online Opportunity Graph MPC.
- Honest stop states: `CROWN_GOLD_RECOMMENDED_SUBMISSION`, `CROWN_GOLD_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`, `EXTERNAL_BLOCKER`.
- Success is official-score, gross, penalty, Qwen, controller, compliance, reviewer, and package gated. Tests, legal actions, Qwen smoke, reports, synthetic pass, macro counts, and package shape are insufficient.
- Default runtime/package variant must be `crown_gold_contract_mpc`, not `best_rescue`, `preference_firewall_profit`, PCE, Delta-MPC, or Exact.

## Long-Lived Compliance Rules

- Runtime under `demo/agent` must not read raw cargo/driver data, reports, oracle artifacts, exact labels, income calculators, benchmark internals, or future cargo availability.
- Runtime must not import `server.*`, `bench.*`, scoring internals, or income-calculation internals.
- Runtime must not hardcode driver ids, cargo ids, static place names, fixed route sequences, fixed coordinates, offline heatmaps, or scenario shortcuts.
- Protected example terms and scenario shortcut words must not be copied into repository files. Use `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash`.
- Real Qwen runtime calls remain ON for non-empty preferences when an API path is available.
- Do not set or rely on `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for final evaluation. Do not use dummy cache, smoke-only compile, fallback-only compile, or zero compile budget as success.
- Qwen roles are Preference Contract Compiler, Observed Vocabulary Linker, and gated Candidate Auditor only. Qwen must not output final actions.
- API priority is injected `SimulationApiPort.model_chat_completion`, then compatible endpoint using `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`.
- Qwen timeout is 120 seconds with up to 3 retries.
- Never print or commit keys. Dummy or missing keys are fallback evidence, not success.

## Runtime Action Rules

- `query_cargo` must be followed by `refresh_world`.
- Filtering, scoring, and certificates must use the post-query `World`.
- `take_order` may only use cargo from the current decision's post-query `current_actionable` observed set.
- `no_query` cannot take remembered cargo.
- Shadow or historical cargo must never enter actionable candidates.
- Destination Shadow Query is OFF.
- Reposition action coordinates must keep full precision and must not be rounded.

## CROWN-GOLD Rules

- Runtime order is refresh world, compile/cache Preference Contract rules, update controllers, preserve rescue macro commitments, query, refresh/filter, observed vocabulary linking, generate candidates, Preference Firewall, gated auditor, deterministic scoring, optional visible graph MPC, safety finalize.
- Preference Contract Compiler must emit `polarity`, `observable`, `scope`, `metric`, `counting`, `slots`, `severity`, `repair_actions`, `confidence`, `uncertainty`, and `evidence_hash`.
- Qwen must not invent penalty amount or cap; missing penalty is explicit `null` with source `unknown` and uses generic fallback scale.
- Observed Vocabulary Linker may use only current visible cargo field/value summaries.
- Candidate Auditor reviews high-conflict top candidates and outputs relation/effect/risk/repair/confidence/evidence only; it must not choose actions.
- T01-T18 controller coverage remains mandatory.
- Each controller exposes update, satisfied, failed, remaining slack, marginal cost, repair value, generate repair candidates, dynamic lambda, and final penalty lower bound.
- ScorerSemanticsAdapter gates hard blocks and massive penalties. Unverified semantics are soft risk only.
- UnknownSoft never hard-blocks high-gross actions.
- Preference Firewall must run before profit ranking and trace marginal penalty, repair value, lost repair-window cost, unknown-soft risk, Qwen audit adjustment, confidence, and decision.
- Profit backbone is restored rescue/safe-profit. Any preference module that collapses gross without enough penalty reduction must be disabled or retuned.
- Online Opportunity Graph MPC may use only current visible cargo and current-run same-driver legal observations; no offline heatmaps, fixed places, fixed coordinates, or future cargo.

## Records, Reports, Reviews

- Durable records live under `docs/AGENT_WORK/`.
- Final `reports/` contains at most five CROWN-GOLD artifacts:
  `gold_final_report.md`, `gold_experiments.csv`, `gold_qwen_contract_audit.csv`, `gold_decision_forensics.csv`, and `gold_package_audit.md`.
- Old reports are archived, not deleted.
- Required real subagent scopes: Prompt-Adherence, Compliance/Future-Info, Rescue-Core Reproduction, Qwen Preference Contract, Candidate Firewall/Scoring, Opportunity Graph/MPC, and Package Gatekeeper.
- If true subagents are unavailable, stop as `EXTERNAL_BLOCKER`.

## Packaging And Stop Honesty

- Recommended package may be built only if CROWN-GOLD recommended gates pass.
- Experimental package may be built only if CROWN-GOLD experimental gates pass and is labeled experimental.
- If gates fail, do not generate a submission-shaped zip.
- Submission ZIP root is `demo/`; include only `demo/agent/` and `demo/SUBMISSION.md`; exclude server, data, results, reports, runs, archive, docs, keys, local config, prompt docs, and pyc.
- `CROWN_GOLD_RECOMMENDED_SUBMISSION` requires 20260529 official_net >= 40000, preference_penalty <= 22000, gross_minus_cost >= 52000, real Qwen compile/link/audit > 0, controller_scored > 1000, score_changed > 100, changed_decision > 20, 0 failure/abort/illegal/rejected, 0509 no catastrophic regression, clean package inspection, complete reports, commit, and push.
- `CROWN_GOLD_EXPERIMENTAL_SUBMISSION` requires 20260529 official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 45000, and all Qwen/controller/compliance gates.
- If score or semantic gates are not reached, write `DO NOT SUBMIT: gold gates not reached.` as the first line of `reports/gold_final_report.md`.

## Resource Rules

- Keep local and cloud compute isolated to this project.
- Prefer cloud only when it is available without disrupting other users; check host load and GPU usage first.
- Avoid heavy local load that can freeze the PC.
- Use GPU only if materially useful and after checking availability.
- Never disrupt other users' jobs.
