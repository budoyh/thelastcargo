# CROWN-Delta MPC Build Rules

- Active build: CROWN-Delta MPC on branch `crown-delta-mpc`.
- Stop states are only `DELTA_MPC_STRONG_SUCCESS`, `DELTA_MPC_PARTIAL_SUCCESS`, `DO_NOT_SUBMIT_WITH_DELTA_EVIDENCE`, or `EXTERNAL_BLOCKER`.
- Do not present tests passing, legal actions, Qwen calls, report completeness, predicate recall, or a low positive score as success.
- The score objective is official net: `official_net = gross_income - distance_cost - preference_penalty`. Do not subtract preference penalty a second time.
- Runtime action value must serve: direct freight value, route continuation, terminal value, preference repair value, preference destruction cost, lost repair-window cost, time/query/reposition cost, and execution/OOD risk.
- Modules without positive official-net delta or named regret reduction must be disabled or reported as diagnostic only.

## Runtime Boundary

- Runtime code under `demo/agent` may use only the injected `SimulationApiPort` for state, cargo, history, and model calls.
- Runtime code must not read raw cargo or driver datasets, reports, oracle artifacts, exact-label artifacts, benchmark internals, income calculators, or future cargo availability.
- Runtime code must not import `server.*`, `bench.*`, scoring internals, or income-calculation internals.
- Runtime code must not hardcode driver ids, cargo ids, static place names, fixed routes, fixed route sequences, fixed coordinates, offline heatmaps, or scenario shortcuts.
- Protected example terms and scenario shortcut words are read-only context. Repository files must use `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash` instead of literal values.
- Every `query_cargo` call must be followed by `refresh_world`.
- Filtering, scoring, action certificates, and `take_order` must use the post-query world and the current post-query `current_actionable` observed set.
- `no_query` cannot take remembered cargo.
- `shadow_liquidity_only` and `historical_summary_only` cargo must never enter actionable candidates.
- Destination Shadow Query remains OFF unless official organizer guidance changes.
- Reposition coordinates must keep full precision; do not round action coordinates.

## Qwen Roles

- Qwen3.5-Flash Preference Automata Compiler must remain ON for non-empty preferences when an API path is available.
- API order is `SimulationApiPort.model_chat_completion`, then compatible endpoint with `DASHSCOPE_API_KEY`, `BAILIAN_API_KEY`, `ALIYUN_API_KEY`.
- Never print, commit, synthesize, or treat dummy keys as success.
- Qwen roles are limited to Preference Automata Compiler, Observed Vocabulary Linker, and gated Candidate Auditor.
- Qwen must not output or choose the final action.
- Compile cache key is the preference hash. Linker cache key is preference hash plus current observed-vocabulary hash.
- Observed Vocabulary Linker may use only the latest query result's visible vocabulary. Committed artifacts must hash or redact values.
- UnknownSoft rules are soft risk only and must not hard-block high-gross actions.

## Delta Labels, Automata, And Macros

- Official-scorer delta evidence is the core success metric, not self-generated predicate recall.
- Delta label modes must distinguish completed trajectory replacement, action knockout, macro repair insertion, and high-penalty replay.
- Each label must state whether it is exact official evidence, whether replay is valid, continuation policy, visibility validity, legality validity, state compatibility, and confidence.
- Preference Automata must expose progress, satisfied, failed, remaining slack, next deadline, repair actions, destroy actions, marginal penalty, repair value, future failure probability, and confidence.
- Implement high-impact automata first: rest windows, full inactive day, cargo field avoid/require, quota/distinct day, distance limits, visit/dwell, ordered target, region/location require/avoid, and UnknownSoft.
- Macro repair candidates must enter the runtime candidate set and carry avoided penalty, repair value, lost gross, deadline, feasibility, confidence, and an action certificate.
- Macro commitments must be persisted for multi-step repairs. No-query rest, full inactive day, and wait-at-target commitments must not query inside protected intervals unless an explicit abort condition fires.
- Reposition classes are preference reposition, route-start reposition, and escape reposition. If final reposition is zero while target/dwell/order/location automata exist, the final report must give delta evidence for why not moving is better or unresolved.

## Reports And Records

- Final `reports/` artifacts are limited to:
  - `reports/delta_mpc_final_report.md`
  - `reports/delta_mpc_experiments.csv`
  - `reports/delta_mpc_labels.csv`
  - `reports/delta_mpc_automata_eval.csv`
  - `reports/delta_mpc_forensics.csv`
- Old reports go under `archive/`; old run outputs stay under `runs/`.
- Durable working records live in `docs/AGENT_WORK/PROJECT_MEMORY.md`, `docs/AGENT_WORK/EXPERIMENT_LOG.md`, and `docs/AGENT_WORK/EXECUTION_PLAN.md`.
- Reviewer checks are mandatory for prompt adherence, compliance/future-info, official delta labels, automata/Qwen, runtime planner, and code/test quality. If real subagents are unavailable, perform read-only simulated reviews and record them in the final report.

## Verification

- Required local checks before final handoff:
  - `python -m pytest tests -q`
  - `python -m compileall demo tools tests`
  - `python tools/audit_guard.py --fail-on-p0`
  - `python tools/fix_eval_round_bug.py`
  - `python tools/qwen_preference_smoke_test.py`
  - `python tools/run_delta_mpc_baselines.py --simulation-days 31`
  - `python tools/build_official_delta_labels.py --simulation-days 31`
  - `python tools/evaluate_preference_automata.py`
  - `python tools/run_delta_mpc_ablation.py --simulation-days 31`
  - `python tools/build_delta_mpc_reports.py`
- Run 20260529 and 20260509 31-day evaluations or record the exact blocker.
- Commit and push branch `crown-delta-mpc` to `origin/crown-delta-mpc` unless blocked by repository or network state.

## Resource Rules

- Keep heavy local or cloud compute isolated to this project.
- Do not freeze the local PC. Prefer existing run outputs and light sweeps before heavy evaluation.
- Use GPU only when materially useful and after checking availability; never disrupt other users' jobs.
- If no score target is reached, the final state must be `DO_NOT_SUBMIT_WITH_DELTA_EVIDENCE` with a concrete bottleneck.
