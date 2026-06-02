# CROWN-TRIDENT / GOLD-2 Project Memory

## Current Objective

- Build `crown-trident-gold2` from the existing repository, not from scratch.
- The target is official-net uplift through causal evidence: rule-level penalty deltas, changed-decision counterfactual deltas, Qwen auditor numeric effects, controller alignment, online graph uplift, and parameter ablations.
- Final selected runtime must be the smallest score-positive combination: immutable rescue core plus only overlays that improve official_net or reduce a named regret without unacceptable gross collapse.

## Baseline Facts To Preserve

- Historical 20260529 rescue reference: official_net 5067.69, gross_minus_cost 43207.69, preference_penalty 38140.00, actions 89 take / 163 wait / 0 reposition.
- B0 Trident gate requires official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected.
- CROWN-GOLD final selected: official_net 6373.17, gross_minus_cost 45993.17, preference_penalty 39620.00, Qwen compile/link/audit 5/245/245, controller_scored_candidate_count 11461, changed_decision_count 240.
- Gold lifted net only through gross and worsened preference_penalty. First broken link is decision changed -> official preference penalty reduced.
- Previous PTT failed real-Qwen gate with qwen_compile_calls=0 and ptt_compile_calls=0 in full eval.
- Previous Exact had Qwen compile/link but controller scoring did not enter final decision path.
- Tests passing, legal actions, Qwen smoke, reports, synthetic pass, macro counts, Qwen call counts, and controller counts are not success without official score and causal deltas.

## Current Known Risks

- Preference controllers may be directionally wrong: changed decisions can raise gross while increasing official penalty.
- Auditor calls may be present but ineffective if all score adjustments are zero.
- Hard shields and large repair bonuses are unsafe until scorer microprobes prove alignment.
- Already failed or capped rules can destroy gross repeatedly if rule-state delta is missing.
- Online graph can import future/offline signal by accident; it must start empty per driver and use only current-run observed market summaries.
- Parameter search can overfit driver/rule ids; only generic numeric parameters may be exported.
- Qwen calls are expensive but cannot be disabled for final evidence.

## Non-Negotiable Runtime Boundaries

- Runtime may use only `SimulationApiPort`; no raw datasets, no server/bench/scoring imports, no future cargo, no offline reports, no income calculator internals.
- `take_order` must come from current post-query `current_actionable` cargo.
- Every query must be followed by world refresh and post-query filtering.
- `no_query` cannot take remembered cargo.
- Destination Shadow Query is OFF.
- Reposition coordinates must keep full precision.
- Qwen may compile contracts, link current observed vocabulary, or audit gated candidates; it must not choose final actions.
- Protected literals remain redacted in committed files as `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash`.

## Implementation Direction

- Restore and lock immutable best-rescue behavior as B0 before evaluating overlays.
- Build Trident ledgers first: `trident_rule_ledger.csv`, `trident_decision_deltas.csv`, and `trident_qwen_effect.csv`.
- Preference Contract V2 must model rule state with past debt, candidate delta, future repairability delta, marginal penalty, repair value, and lost repair-window cost.
- Controller strength must be gated by scorer microprobe alignment.
- Qwen auditor must produce numeric score adjustments and record ranking/action change effects; if it does not improve official_net, kill it.
- Online Opportunity Graph must be runtime-only and default OFF until alpha/weight ablations prove official-net uplift.
- Parameter search freezes real Qwen artifacts after a true pass, searches only generic parameters, and re-runs top configs through live Qwen before final selection.

## Required Subagents / Reviewers

- Rescue Baseline Keeper.
- Penalty Attribution / Regret Lab.
- Preference Contract / Qwen Auditor Engineer.
- Profit Backbone / Online Graph Engineer.
- Parameter Search / Ablation Engineer.
- Compliance / Package Gatekeeper.
- Each must return changed files, commands run, before/after metrics, pass/fail, blockers, and keep/kill.
- If real subagents or recorded named reviewer passes cannot cover all required missions, stop `DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE`.

## Stop State Rules

- Allowed Trident stop states: `CROWN_TRIDENT_RECOMMENDED_SUBMISSION`, `CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE`, `EXTERNAL_BLOCKER_QWEN`, `EXTERNAL_BLOCKER_RESCUE_CORE`, `EXTERNAL_BLOCKER_EVAL_INFRA`, and `DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE`.
- If Qwen is unavailable for all relevant full runs, stop as `EXTERNAL_BLOCKER_QWEN`.
- If official runner/data/eval infrastructure cannot run B0, stop as `EXTERNAL_BLOCKER_RESCUE_CORE` or `EXTERNAL_BLOCKER_EVAL_INFRA` as appropriate.
- If gates are not reached after evidence is produced, stop as `DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE`.
- If official_net < 30000, do not create a submission-shaped zip and make `reports/trident_final_report.md` start with `DO NOT SUBMIT: <precise reason>`.

## Report And Package Limits

- Final `reports/` contains only `trident_final_report.md`, `trident_experiments.csv`, `trident_rule_ledger.csv`, `trident_decision_deltas.csv`, and `trident_qwen_effect.csv`.
- Old reports move to `archive/`; raw run outputs remain under `runs/`.
- Build a package only after experimental or recommended gates pass.
- Package root must be `demo/`; it must exclude server, data, reports, runs, docs, archive, keys, pyc, and prompt documents.

## Resource Notes

- Keep local and cloud compute isolated to this project.
- Check cloud load and `nvidia-smi` before using shared GPU resources.
- Avoid heavy local load that can freeze the PC.
- Never kill unrelated jobs.
