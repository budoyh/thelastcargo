# Agent Operating Rules

This file mirrors the active local project rules for tools that look for a lowercase agent rule file.

## CROWN-PCE Oracle Gap Build

- Active branch: `crown-pce-oracle-gap`.
- Stop only as `PCE_STRONG_SUCCESS`, `PCE_PARTIAL_SUCCESS`, `DO_NOT_SUBMIT_WITH_ORACLE_EVIDENCE`, or `EXTERNAL_BLOCKER`.
- Do not present tests passing, legal action logs, Qwen calls, report completeness, or a low positive score as success.
- Final PCE artifacts are limited to:
  - `reports/pce_final_report.md`
  - `reports/pce_experiments.csv`
  - `reports/oracle_gap.csv`
  - `reports/predicate_eval.csv`
  - `reports/action_forensics.csv`

## P0 Runtime Boundary

- Runtime code may use only the injected `SimulationApiPort` for state, cargo, history, and model calls.
- Runtime code under `demo/agent` must not read raw data files, import `server.*`, `bench.*`, income/scoring internals, or use future cargo information.
- Runtime code must not hardcode driver ids, cargo ids, static place names, route sequences, fixed coordinates, offline heatmaps, or scenario shortcuts.
- `query_cargo` must be followed by `refresh_world`; filtering, scoring, certificates, and actions must use the post-query `World`.
- `take_order` can only target the current decision's post-query `current_actionable` observed cargo.
- `shadow_liquidity_only` and `historical_summary_only` cargo must never enter actionable candidates.
- `no_query` cannot take remembered cargo.
- Destination Shadow Query is OFF unless official evidence changes the rule.
- Reposition coordinates must keep full precision.

## Preference System

- Qwen3.5-Flash Preference Compiler is required for non-empty runtime preferences when an API path is available.
- Model access order is `SimulationApiPort.model_chat_completion`, then compatible endpoint fallback using `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`.
- Never print, commit, or synthesize API keys. Dummy or missing keys are fallback evidence, not success.
- Qwen roles are limited to Preference Compiler v2, Observed Vocabulary Linker, and gated Candidate Auditor.
- Qwen must not choose or emit final actions.
- Preference Compiler v2 must emit executable predicate specs with predicate type, fields, operator, runtime values, time scope, deadline, counter, coordinate target, repair kinds, penalty, confidence, and redacted evidence hash.
- Rules without executable predicates are unresolved and may only become soft risk.
- Observed Vocabulary Linker may use only the current visible cargo vocabulary from the latest query. Committed reports must contain hashes or redacted counts, never raw values.
- Candidate-level verification must report predicate match, marginal effect, predicted marginal penalty, predicted repair value, confidence, and source for high-impact candidates.
- Repair candidates are first-class actions and must carry avoided penalty, repair value, lost profit, deadline, feasibility, confidence, and an action certificate.

## Redaction And Offline Boundary

- Protected example terms and scenario shortcut words are read-only context. Repository files must write only `literal banned terms redacted`, `scenario shortcuts redacted`, or `raw value redacted`.
- Offline tools may read public debug data and official scoring code for diagnosis, oracle bounds, labels, and reports only.
- Runtime must not import or read oracle reports, exact-label artifacts, money-repair trajectories, full-info trajectories, raw cargo ids, raw driver ids, static places, fixed coordinates, fixed routes, or future availability.
- Exported runtime parameters may only be generic weights, thresholds, abstract predicate templates, and redacted calibration constants.

## Records, Review, And Resources

- Keep durable notes in `docs/PROJECT_MEMORY.md` and `docs/EXPERIMENT_LOG.md`.
- Final PCE evidence belongs only in the five PCE report files listed above.
- Required reviews cover prompt adherence, compliance/future-info, oracle/score-accounting, marginal penalty dataset, predicate compiler, runtime planner, code/test, and final audit. If subagents are unavailable, perform a read-only simulated review and record it.
- Heavy local or cloud compute must stay isolated to this project and must not disrupt local stability. Use GPU only when materially useful.
