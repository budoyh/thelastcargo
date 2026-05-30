# Subagent Reviews

## Initial Interface / Compliance Explorer

- scope: official demo interface, action schema, runtime boundaries, 31 day config, round bug status.
- result: baseline needed replacement; query must refresh world after each query; `config.example.json` had to be 31 days; round bug patch was present.
- remediation: replaced baseline agent, enforced post-query `refresh_world`, updated config example, added round bug check.
- gate: allowed after fixes.

## Prompt-Adherence Reviewer

- scope: long prompt, P0/P0++/P1/P2/P3 requirements, reports, runs and git state.
- result before remediation: blocked because final report, commit/push, final reviewer table, stronger preference certificate, reposition default decision and stability checks were missing.
- remediation: added executable preference DSL/certificate path, default-disabled reposition due lack of positive payback evidence, generated regret and stability audits, prepared final report and commit/push steps.
- residual: commit hash and push result are filled only after final git operations.

## Compliance Reviewer

- scope: raw data/runtime boundary, source scope isolation, destination shadow, hardcoding, config switches.
- command: `python tools/audit_guard.py --fail-on-p0`
- result: `findings=0 p0=0`.
- remediation: none required beyond keeping scan green after later edits.
- gate: allowed.

## Safety & Runtime Reviewer

- scope: query refresh, post-query filtering, current observed set, no-query behavior, 31 day horizon, reposition precision and fallback wait.
- commands: `python -m pytest tests -q -p no:cacheprovider`, `python tools/audit_guard.py --fail-on-p0`.
- result before remediation: blocked by fallback wait horizon overflow when remaining minutes were below `MIN_WAIT_MINUTES`; trace needed more certificate fields.
- remediation: wait and fallback duration now clamp to remaining horizon; `finalize()` has a final horizon guard; trace records `cargo_id`, `source_scope`, `cert_decision_id`, safety reasons and score; added regression tests.
- gate after remediation: local tests and audit pass.

## Regret & Ablation Reviewer

- scope: regret dashboard, A/B/C and old-data ablations, reposition payback evidence and module decisions.
- result before remediation: blocked because regret report lacked all run tables, reposition recovery logic counted all selected reposition actions as unrecovered, and no positive payback evidence existed.
- remediation: fixed recovery-window logic, marked proxy regret categories explicitly, added final ablation table, disabled reposition by default, added candidate trace and stability audit.
- gate after remediation: module decisions are now tied to regret and ablation evidence.

## Code Quality Reviewer

- scope: decision service, query/filter/score/safety/trace/world/preferences, tools and tests.
- result before remediation: blocked by missing top-level exception fallback, dead preference hard-block path, and minimal trace/regret schema mismatch.
- remediation: `ModelDecisionService.decide()` now catches runtime exceptions and returns legal wait with trace; preference compiler now emits quantitative DSL rules and high-confidence irreversible certificates when evidence supports it; regret dashboard handles minimal trace and bad JSONL lines; added tests.
- gate after remediation: `33 passed`, audit green, compileall green.

## Final Re-Review Results

| reviewer | gate | final note |
|---|---|---|
| Prompt-Adherence | resolved after final commit/push | Function/compliance side passed; remaining blocker was only untracked final report, dirty worktree, and push not yet completed. Final report is now committed and branch is pushed. |
| Compliance | yes | `audit_guard.py --fail-on-p0` passed with `findings=0 p0=0`; no runtime raw-data/server import/hardcoding issue. |
| Safety & Runtime | yes | Query refresh, post-query filtering, current observed take, horizon clamp, exception fallback, trace fields and latest artifacts verified. |
| Regret & Ablation | yes | Six regret categories, module go/no-go decisions, reposition OFF and ablation honesty verified. |
| Code Quality | yes | Prior P1 issues fixed; one non-blocking stability-audit bad-line tolerance note was addressed after review. |
