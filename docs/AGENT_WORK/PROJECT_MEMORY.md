# CROWN-EXACT RBT-MPC Project Memory

## Current Objective

- Build `crown-exact-rbt-mpc` from the existing legal rescue core.
- Default runtime/package variant must be `crown_exact_rbt_mpc`; do not default to `best_rescue` or `preference_firewall_profit`.
- The goal is official-net uplift through Rule Bytecode Transducer, scorer-semantic controllers, action-level Preference Firewall, and Visible Opportunity Graph MPC while preserving freight gross.

## Baseline Facts To Preserve

- Public 20260529 rescue reference: official_net 5067.69, preference_penalty 38140, actions 89 take / 163 wait / 0 reposition.
- Prior Delta-MPC best runtime did not improve over rescue; macro completion did not produce positive official-delta gain.
- First online B-list style submission using best_rescue default reportedly had hidden preference penalty explosion.
- Legal actions, Qwen calls, reports, predicate recall, and macro counts are not success without score-hard and semantics-hard gates.

## Current Known Failures

- `best_rescue` 20260529 reference is only official_net 5067.69 with preference_penalty 38140.
- Previous PTT 20260529 failed harder: official_net -8635.06, gross_minus_cost 33364.94, preference_penalty 42000.
- Previous PTT full 31-day traces had qwen_compile_calls=0 and ptt_compile_calls=0; synthetic T01-T18 passing did not prove real preference conversion.
- Previous PTT showed many massive-penalty traces but ptt_blocks=0, so the firewall did not become reliable action-level protection.
- Delta-MPC exact labels were too sparse and mostly replay/heuristic, so they are not a reliable value function target.
- Hidden/online preference penalty risk remains the primary submission risk; no low-score default can be packaged as success.

## Non-Negotiable Boundaries

- Runtime may use only `SimulationApiPort`; no raw datasets, no server/bench/scoring imports, no future cargo, no offline reports.
- `take_order` must come from current post-query `current_actionable` cargo.
- Every query must be followed by world refresh and post-query filtering.
- Qwen may compile PTT rules, link current observed vocabulary, or audit gated candidates; it must not choose final actions.
- Protected literals remain redacted in committed files as `PROTECTED_LITERAL_REDACTED`.

## CROWN-EXACT Implementation Direction

- Keep the best rescue legality core: query-refresh, current-actionable filtering, safety certificates, and positive freight scoring.
- Add RBT compile/cache and T01-T18 deterministic controllers.
- Run Observed Vocabulary Linker after every query when preferences exist and visible cargo exists.
- Run Preference Firewall before profit ranking.
- Use Qwen gated auditor only for high-risk uncertain candidates; auditor output is match/effect/confidence only.
- Keep Visible Graph MPC default OFF unless ablation proves positive official-net or penalty improvement without gross collapse.
- Terminal/ranker learned components remain OFF unless score evidence supports them.

## Failure Honesty

- If 20260529 official_net does not exceed rescue or preference_penalty is not materially lower, do not recommend submission.
- If synthetic T01-T18 tests fail, do not recommend submission.
- If linker never runs for field/region/attribute preferences, do not recommend submission.
- If final package is created after failed gates, filename must include `NOT_RECOMMENDED_DO_NOT_SUBMIT`.

## Current Stop State

- Allowed exact stop states: `CROWN_EXACT_RECOMMENDED_SUBMISSION`, `CROWN_EXACT_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE`, `EXTERNAL_BLOCKER`.
- If Qwen API, true subagents, or official local evaluation are unavailable, stop as `EXTERNAL_BLOCKER`.
- If score gates are not reached after exact evidence is produced, stop as `DO_NOT_SUBMIT_WITH_EXACT_EVIDENCE`.
