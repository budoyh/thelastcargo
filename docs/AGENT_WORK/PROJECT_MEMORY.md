# CROWN-FUSE / RESCUE-SWITCH Project Memory

## Current Fuse Objective

- Branch: `crown-fuse-rescue-switch`.
- Continue from the existing repository and the executed Surge evidence; do not rebuild from scratch.
- The mission is to find a B0 `best_rescue` + targeted repair knee point: keep B0's gross backbone and borrow only the profitable part of B9c's penalty reduction.
- Known B0 reference: official_net `5067.69`, gross_minus_cost `43207.69`, preference_penalty `38140.0`, take/wait/reposition `89/163/0`, invalid/failure/rejected `0`.
- Known B9c reference: official_net `-157.97`, gross_minus_cost `29142.03`, preference_penalty `29300.0`. B9c reduced penalty by `8840` but lost `14065.66` gross, so broad repair is killed and only targeted repair may be searched.

## Fuse Hard Gates

- `tools/verify_fuse_completion.py` is the completion gate and must pass isolation, search, and final phases.
- B0 must pass official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected before overlay evidence matters.
- B1/B2/B3 no-op isolation must action-match B0 with match_rate >= 0.999 and score deltas <= 100 before grid search.
- Qwen compile/link stays ON for real non-empty preferences. Auditor numeric adjustment defaults OFF unless A1/A2 official ablation beats A0 with json_valid_rate >= 0.90 and nonzero adjustments.
- Final reports are limited to five Fuse files. Planned/missing/proxy/diagnostic-only rows never count as success.
- Required final stop states are `FUSE_RECOMMENDED_SUBMISSION`, `FUSE_EXPERIMENTAL_SUBMISSION`, `FUSE_REVIEW_PACKAGES_ONLY`, `DO_NOT_SUBMIT_WITH_FUSE_EVIDENCE`, `EXTERNAL_BLOCKER_RESCUE_ISOLATION`, `EXTERNAL_BLOCKER_EVAL_INFRA`, or `EXTERNAL_BLOCKER_QWEN`.

## Fuse Runtime Boundary

- Runtime under `demo/agent` uses only injected `SimulationApiPort`.
- No raw datasets, reports, oracle artifacts, server/bench/scorer/income internals, action traces, exact labels, protected literals, fixed places/routes/coordinates, ids, offline heatmaps, or future cargo may enter runtime.
- Every `query_cargo` is followed by `refresh_world`; take decisions use only current post-query `current_actionable`; `no_query` cannot take remembered cargo.
- Destination Shadow Query is OFF and reposition coordinates keep full precision.

# CROWN-SURGE / LEDGER-HUNTER Project Memory

## Current Surge Objective

- Branch: `crown-surge-ledger-hunter`.
- Continue from the failed `crown-trident-gold2` work; do not rebuild the runtime from scratch.
- The mission is executed official-score surgery: restore immutable `best_rescue`, run B0-B9c/B10/B11 official matrix, repair or kill Qwen auditor based on numeric effect, produce official/replan-valid changed-decision deltas, run rule doctor, execute Online Opportunity Graph attack, and run 100+ real parameter trials.
- Final success requires `python tools/verify_surge_completion.py --phase final` PASS. No report, smoke test, synthetic result, planned row, missing row, diagnostic-only delta, or package shape can substitute for executed official score evidence.

## Surge Stop Conditions

- Allowed stop states: `SURGE_RECOMMENDED_SUBMISSION`, `SURGE_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_SURGE_EVIDENCE`, `DO_NOT_SUBMIT_WITH_INCOMPLETE_EXECUTION`, `EXTERNAL_BLOCKER_RESCUE_CORE`, `EXTERNAL_BLOCKER_QWEN`, and `EXTERNAL_BLOCKER_EVAL_INFRA`.
- If B0 cannot reproduce due to runner/data/eval infrastructure, stop `EXTERNAL_BLOCKER_RESCUE_CORE`.
- If B1-B9c/B10/B11, 100+ real trials, official/replan-valid deltas, or final verifier are incomplete, stop `DO_NOT_SUBMIT_WITH_INCOMPLETE_EXECUTION`.
- If evidence is complete but below experimental gates, stop `DO_NOT_SUBMIT_WITH_SURGE_EVIDENCE` and do not create a submission-shaped ZIP.

## Surge Evidence Gates

- B0 rescue gate: official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected on 20260529.
- Experimental package gate: official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 50000, 0 failure/abort/illegal/rejected, B0-B11 executed, 100+ trials executed, Qwen auditor effective or killed by ablation, and final verifier PASS.
- Recommended package gate: official_net >= 38000, preference_penalty <= 22000, gross_minus_cost >= 60000, clean package audit, default variant final selected strategy, and final verifier PASS.
- Final `reports/` contains exactly `surge_final_report.md`, `surge_experiments.csv`, `surge_decision_deltas.csv`, `surge_rule_doctor.csv`, and `surge_qwen_effect.csv`.

## Current Surge Evidence Snapshot

- B0 rescue passed: official_net `5067.69`, gross_minus_cost `43207.69`, preference_penalty `38140.0`, invalid/failure/rejected `0`.
- B0-B9c base official matrix executed; all non-B0 rows are below B0 official_net.
- Qwen auditor parser/schema was repaired to produce numeric nonzero adjustments in patched B5, but patched B5 worsened official_net to `-19535.83` and preference_penalty to `50800.0`; auditor is killed by current evidence.
- Opportunity Graph B7/B8 executed with nonzero usage but both worsened official_net versus B0; graph is killed by current evidence.
- Reports are in Surge five-file shape, but final verifier fails because B10/B11, 100 parameter trials, replay-valid decision deltas, and complete Qwen valid-rate evidence are missing.
- No packaging is allowed in the current state.

## Failed Trident Evidence To Avoid Repeating

- Prior `trident_experiments.csv` contained B1-B8/B10/B11 as `MISSING_RUN` and parameter trials as `PLANNED` / `planned_not_evaluated`.
- Prior `trident_qwen_effect.csv` contained auditor calls with invalid legacy trace labels and all-zero `applied_score_adjustment`.
- Prior changed-decision deltas were `diagnostic_not_official_counterfactual`; they cannot tune controller weights.
- Surge verifier must keep these as hard failures, not downgrade them into caveats.

## Surge Runtime Boundaries

- Runtime under `demo/agent` uses only injected `SimulationApiPort` for state, cargo, history, and model calls.
- Runtime must not read raw cargo/driver data, reports, oracle artifacts, scorer outputs, income calculators, server/bench modules, action traces, exact labels, or future cargo availability.
- Every `query_cargo` call must be followed by `refresh_world`; filtering, scoring, certificates, and `take_order` must use the post-query world.
- `take_order` may only use cargo from current post-query `current_actionable`; `no_query` cannot take remembered cargo.
- Destination Shadow Query remains OFF.
- Reposition coordinates keep full precision and are never rounded.
- Protected literals must be redacted as `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash`.

## Surge Qwen And Graph Rules

- Real Qwen runtime calls are mandatory for non-empty preferences when an API path exists. Do not use `CROWN_Y_DISABLE_RUNTIME_QWEN=1` in final evidence.
- Qwen timeout is 120 seconds with up to 3 retries. Use cache/batching instead of lowering requirements.
- Qwen roles are Preference Contract Compiler, Observed Vocabulary Linker, and gated Candidate Auditor. Qwen must not choose or veto final actions.
- Auditor success requires JSON valid rate >= 90%, nonzero applied adjustment count > 0, and ranking_changed_count > 0. If not, kill auditor.
- Online Opportunity Graph may use only current query `current_actionable` cargo and same-driver current-run legal observations. No offline heatmap, future cargo, static place, fixed coordinate, route template, driver id, or cargo id may enter runtime.

# Historical CROWN-TRIDENT / GOLD-2 Project Memory

## Current Objective - CROWN-FUSE / RESCUE-SWITCH v10

- Active branch: `crown-fuse-rescue-switch`.
- Final selected runtime is explicit B0 fallback `best_rescue` because no Fuse targeted-repair candidate preserved the required gross while improving B0.
- Stop-state target for this completed evidence set is `FUSE_REVIEW_PACKAGES_ONLY`.
- B0 frozen baseline reproduced after config freeze: official_net `5067.69`, gross_minus_cost `43207.69`, preference_penalty `38140.0`, 89 take / 163 wait / 0 reposition, 0 invalid.
- No-op isolation after freeze passed: B1/B2/B3 each matched B0 with action_signature_match_rate `1.0`, score deltas `0.0`, and 0 invalid.
- Fuse grid has 100 executed 20260529 TRIAL rows plus B0/B9c, graph G0-G3, auditor A0-A2, B10, and B11. Best non-B0 search row was `trial_017` with official_net `8142.11`, gross_minus_cost `37562.11`, preference_penalty `29420.0`; it was killed because gross fell below the knee floor.
- B10 final parameter-search-best rerun: official_net `-4348.69`, gross_minus_cost `18551.32`, preference_penalty `22900.0`.
- B11 final selected rerun: `best_rescue`, official_net `5067.69`, gross_minus_cost `43207.69`, preference_penalty `38140.0`, fallback_to_b0 `true`, Qwen compile/cache `7`, link/cache `1`, auditor numeric `0`.
- Qwen numeric auditor remains OFF: A1/A2 had schema-valid nonzero adjustments but worsened official_net versus A0.
- Opportunity graph remains killed: G1/G2/G3 did not improve official_net/gross versus G0.
- Top 5 20260529 configs all ran full 20260509 sanity with `income_abort_count=0`.
- Package policy: below recommended/experimental score gates, only `runs/packages/CROWN_FUSE_REVIEW_ONLY_NOT_FOR_SUBMISSION.zip` may exist; default variant must be `best_rescue`.

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

# CROWN-DRAGON-ORCA v1.1 Active Work

- Branch: crown-dragon-orca-v1-1.
- Stop states: DRAGON_RECOMMENDED_SUBMISSION, DRAGON_EXPERIMENTAL_SUBMISSION, DO_NOT_SUBMIT_WITH_COMPLETE_NEGATIVE_EVIDENCE, DO_NOT_SUBMIT_WITH_REVIEW_ONLY_PACKAGE, DO_NOT_SUBMIT_WITH_INCOMPLETE_SEARCH, DO_NOT_SUBMIT_WITH_INTERNAL_COMPILER_FAILURE_BUT_SEARCH_COMPLETE, PROMPT_NONCOMPLIANCE_FAIL, EXTERNAL_BLOCKER_QWEN_API, EXTERNAL_BLOCKER_EVAL_INFRA, EXTERNAL_BLOCKER_REPO_OR_RESOURCE.
- Hard rule: no active-module claim without runtime code, deterministic test, trace used_count, 31-day full-run evidence, and score/ablation evidence.
- Qwen numeric auditor is OFF; schema weakness cannot stop strategy search.
- Runtime must stay inside SimulationApiPort, current post-query actionable cargo, current-run generic observations, and generic parameters.
- Final reports are exactly the five dragon_orca_* files; raw outputs stay under runs/dragon_orca and reviewer notes under runs/dragon_orca/reviewers.
