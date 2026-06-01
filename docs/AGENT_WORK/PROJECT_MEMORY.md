# CROWN-PTT-GreedyMPC Project Memory

## Current Objective

- Build `crown-ptt-firewall-profit` from the existing legal rescue core.
- Default runtime/package variant must be `preference_firewall_profit`; do not default to `best_rescue`.
- The goal is hidden-preference penalty control through PTT controllers and action-level Preference Firewall while preserving freight gross.

## Baseline Facts To Preserve

- Public 20260529 rescue reference: official_net 5067.69, preference_penalty 38140, actions 89 take / 163 wait / 0 reposition.
- Prior Delta-MPC best runtime did not improve over rescue; macro completion did not produce positive official-delta gain.
- First online B-list style submission using best_rescue default reportedly had hidden preference penalty explosion.
- Legal actions, Qwen calls, reports, predicate recall, and macro counts are not success without score-hard and semantics-hard gates.

## Non-Negotiable Boundaries

- Runtime may use only `SimulationApiPort`; no raw datasets, no server/bench/scoring imports, no future cargo, no offline reports.
- `take_order` must come from current post-query `current_actionable` cargo.
- Every query must be followed by world refresh and post-query filtering.
- Qwen may compile PTT rules, link current observed vocabulary, or audit gated candidates; it must not choose final actions.
- Protected literals remain redacted in committed files as `PROTECTED_LITERAL_REDACTED`.

## PTT Implementation Direction

- Keep the best rescue legality core: query-refresh, current-actionable filtering, safety certificates, and positive freight scoring.
- Add PTT compile/cache and T01-T18 deterministic controllers.
- Run Observed Vocabulary Linker after every query when preferences exist and visible cargo exists.
- Run Preference Firewall before profit ranking.
- Use Qwen gated auditor only for high-risk uncertain candidates; auditor output is match/effect/confidence only.
- Terminal/ranker learned components remain OFF.

## Failure Honesty

- If 20260529 official_net does not exceed rescue or preference_penalty is not materially lower, do not recommend submission.
- If synthetic T01-T18 tests fail, do not recommend submission.
- If linker never runs for field/region/attribute preferences, do not recommend submission.
- If final package is created after failed gates, filename must include `NOT_RECOMMENDED_DO_NOT_SUBMIT`.

## Current Stop State

- The current branch is diagnostic only: `PTT_DIAGNOSTIC_SUCCESS_DO_NOT_SUBMIT`.
- 20260529 failed score gates: official_net did not exceed rescue, preference_penalty did not fall below rescue, and gross_minus_cost collapsed below the target floor.
- Full-run runtime Qwen was disabled for evaluation due to throughput stall, although Qwen smoke compile succeeds and default package keeps PTT Qwen enabled.
- Next shortest path is targeted repair of high-penalty target/dwell and stay-window controllers, plus bounded runtime Qwen caching/linking that does not stall 31-day runs.
