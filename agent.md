# Agent Operating Rules

This lowercase rule file mirrors `AGENTS.md` for tools that look for `agent.md`.

## Active Build

- Branch: `crown-delta-mpc`.
- Task: CROWN-Delta MPC.
- Honest stop states: `DELTA_MPC_STRONG_SUCCESS`, `DELTA_MPC_PARTIAL_SUCCESS`, `DO_NOT_SUBMIT_WITH_DELTA_EVIDENCE`, `EXTERNAL_BLOCKER`.
- Success is score-gated. Tests, legality, Qwen calls, reports, and predicate recall are insufficient without official-net improvement.
- Score accounting is `official_net = gross_income - distance_cost - preference_penalty`; never use a double-penalty proxy.

## Long-Lived Compliance Rules

- Runtime under `demo/agent` must not read raw cargo/driver data, reports, oracle artifacts, exact labels, income calculators, benchmark internals, or future cargo availability.
- Runtime must not import `server.*`, `bench.*`, scoring internals, or income-calculation internals.
- Runtime must not hardcode driver ids, cargo ids, static place names, fixed route sequences, fixed coordinates, offline heatmaps, or scenario shortcuts.
- Protected example terms and scenario shortcut words must not be copied into repository files. Use `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash`.
- Qwen3.5-Flash Preference Automata Compiler stays ON for non-empty preferences when an API path is available.
- Qwen roles are compiler, observed-vocabulary linker, and gated candidate auditor only. Qwen must not output final actions.
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
- Reposition target sources are runtime preference evidence, current visible clusters, route-start candidates from current visibility, escape moves from legal same-simulation memory, or current observed summaries only.

## Delta-MPC Rules

- Every runtime module must serve the action value model: freight direct net, route continuation, terminal value, preference repair value, preference destruction cost, lost repair-window cost, time/query/reposition cost, execution risk, and OOD/low-confidence risk.
- Official-scorer counterfactual delta labels drive keep/kill decisions.
- Label validity fields are mandatory: exact official label, replay validity, continuation policy, visibility validity, legality validity, state compatibility, and confidence.
- Preference Automata must maintain progress, satisfied, failed, remaining slack, next deadline, repair actions, destroy actions, marginal penalty, repair value, future failure probability, and confidence.
- UnknownSoft never hard-blocks high-gross actions.
- Macro repair actions must be runtime candidates with avoided penalty, repair value, lost gross, deadline, feasibility, confidence, and action certificates.
- Macro commitments must persist across decisions when a repair takes multiple steps. No-query rest, full inactive day, and wait-at-target commitments must not query inside protected intervals unless explicitly aborted.
- Terminal value and ranker are default OFF. They may be enabled only with positive official-net ablation and clean feature audit.

## Records, Reports, Reviews

- Durable records live under `docs/AGENT_WORK/`.
- Final `reports/` contains at most the five Delta-MPC artifacts:
  `delta_mpc_final_report.md`, `delta_mpc_experiments.csv`, `delta_mpc_labels.csv`, `delta_mpc_automata_eval.csv`, and `delta_mpc_forensics.csv`.
- Old reports are archived, not deleted.
- Required review scopes: prompt adherence, compliance/future-info, official delta, automata/Qwen, runtime planner, and code/test.
- If true subagents are unavailable, run simulated read-only reviews and record the findings in the final report.

## Stop Honesty

- Strong success requires all hard gates, 20260529 official net at least 45000, preference penalty at most 15000, gross-minus-cost at least 55000 or proven lower ceiling, positive macro delta, 0509 sanity, clean audits, commit, and push.
- Partial success requires at least useful public improvement, positive macro commitment evidence, clean legality/audits, and final report marked do-not-submit-yet.
- If score targets are not reached, write `DO NOT SUBMIT: Delta-MPC target not reached.` as the first line of the final report and classify the bottleneck precisely.

## Resource Rules

- Keep local and cloud compute isolated to this project.
- Avoid heavy local load that can freeze the PC.
- Use GPU only if materially useful and after checking availability.
- Never disrupt other users' jobs.
