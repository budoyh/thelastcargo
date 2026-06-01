# CROWN-Delta MPC Project Memory

## Current Objective

- Build and evaluate the `crown-delta-mpc` branch from existing work.
- The goal is official-net improvement supported by official-scorer delta evidence.
- Reports, tests, Qwen calls, and predicate recall are not success unless official net improves.

## Baseline Facts To Preserve

- Rescue reference for 20260529: official_net 5067.69, preference_penalty 38140, actions 89 take / 163 wait / 0 reposition.
- PCE reference for 20260529: official_net -3125.02, gross_minus_cost 34114.98, preference_penalty 37240, actions 117 take / 199 wait / 0 reposition.
- Strict preference reference for 20260529: official_net 2240.98, gross_minus_cost 38900.98, preference_penalty 36660.
- No-preference money reference is diagnostic only because preference penalty dominates official net.
- Prior oracle evidence suggests the public 20260529 strong threshold may exceed the best known offline repair frontier; this must be reported as score evidence, not hidden.

## Non-Negotiable Boundaries

- Runtime may use only `SimulationApiPort`; no raw datasets, no server/bench/scoring imports, no future cargo, no offline reports.
- `take_order` must come from current post-query `current_actionable` cargo.
- Every query must be followed by world refresh and post-query filtering.
- Qwen may compile automata, link current observed vocabulary, or audit gated candidates; it must not choose final actions.
- Protected literals remain redacted in committed files as `PROTECTED_LITERAL_REDACTED`.

## Implementation Direction

- First reuse and tighten the rescue line rather than replacing it.
- Add official-delta label tooling with validity flags even when replay labels are approximate.
- Add Preference Automata interfaces and scorer-semantics evaluation before trusting high lambda.
- Add macro repair candidates and macro commitment so repairs can actually execute.
- Emit top-5 action-value decomposition for audit.
- Keep terminal/ranker disabled unless ablation proves positive official-net delta.

## Failure Honesty

- If final 20260529 official net is below 20000, the branch cannot be partial success.
- If macro candidates exist but no macro completes with positive delta evidence, the branch cannot be success.
- If labels are mostly replay approximations, use `DO_NOT_SUBMIT_WITH_DELTA_EVIDENCE` and name the bottleneck.

## 2026-06-01 Delta-MPC Outcome

- Best runtime 20260529 baseline remains rescue_reference at official_net 5067.69.
- Best Delta-MPC 20260529 runtime row is `delta_mpc_fallback` at official_net -5112.02 with 32 macro completions and no measured positive macro official-delta gain.
- Best offline diagnostic frontier remains below the strong target and is not a submit result.
- 20260509 `delta_mpc_fallback` scored official_net 102265.64 with 0 failures, 0 income aborts, 0 illegal actions, and 0 rejected takes.
- Final stop state is `DO_NOT_SUBMIT_WITH_DELTA_EVIDENCE`; the named bottleneck is incomplete official-scorer action-level delta evidence plus macro variants failing to improve official_net over rescue.
