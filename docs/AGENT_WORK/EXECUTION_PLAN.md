# Pref-Forge Execution Plan

1. Freeze public preference extraction privately and build redacted compile benchmark.
2. Validate primitive registry and scorer semantics.
3. Execute E0/E1/E2 no-op isolation on 20260529.
4. Execute E3-E13 mandatory 20260529 official rows.
5. If E5 gross gate passes, execute at least 60 focused full 20260529 search rows.
6. Execute 0509 sanity for B0 and top candidates.
7. Build penalty diff, package audit, final report, and run all mandatory verification commands.
8. Run read-only reviewer QA, fix blocking findings, then commit and push.

# CROWN-FUSE / RESCUE-SWITCH Execution Plan

## Current Branch

- `crown-fuse-rescue-switch`
- Continue from the existing repository and executed Surge evidence; do not rebuild from scratch.

## Fuse Stop States

- `FUSE_RECOMMENDED_SUBMISSION`: recommended score gates pass, final verifier passes, recommended package is generated and unpack-audited.
- `FUSE_EXPERIMENTAL_SUBMISSION`: experimental gates pass, final verifier passes, experimental package is generated and unpack-audited.
- `FUSE_REVIEW_PACKAGES_ONLY`: all required execution is complete, no submission gate passes, and at most one honest review-only package is generated.
- `DO_NOT_SUBMIT_WITH_FUSE_EVIDENCE`: all required execution is complete but no package gate passes.
- `EXTERNAL_BLOCKER_RESCUE_ISOLATION`: B0 cannot be evaluated because runner/data/eval/income infrastructure cannot run.
- `EXTERNAL_BLOCKER_EVAL_INFRA`: official-style evaluation is broken for infrastructure reasons.
- `EXTERNAL_BLOCKER_QWEN`: real Qwen compile/link cannot be called or cached despite valid environment and retries.

## Fuse Work Order

1. Create and push branch `crown-fuse-rescue-switch`.
2. Update durable rules and implement `tools/verify_fuse_completion.py`.
3. Reproduce B0 `best_rescue` on 20260529 and fix drift until the B0 gate passes.
4. Run B1/B2/B3 no-op isolation and fix any action/score drift before search.
5. Keep Qwen compile/link ON, Qwen numeric auditor OFF by default, and build targeted repair overlay plus B0 Shadow Guard.
6. Run current-branch B9c reference and generate `reports/fuse_rule_ledger.csv` with only generic family-level exports.
7. Execute at least 60 full 20260529 fuse grid runs; continue to at least 100 if the prompt's promising-signal trigger is met.
8. Run tiny graph diagnostic, auditor numeric off/low/high ablation, top 5 20260509 full sanity, and B10/B11 final selected runs.
9. Run read-only QA gates with concrete evidence, then final verifier.
10. Generate and unpack-audit exactly the allowed package class, or stop honestly with complete evidence.

## Required Commands Or Equivalents

- `python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --results-dir runs/fuse/b0_rescue`
- `python tools/verify_fuse_completion.py --phase isolation`
- `python tools/verify_fuse_completion.py --phase search`
- `python tools/verify_fuse_completion.py --phase final`
- `python -m compileall demo tools tests`
- `python -m pytest tests -q`
## Current CROWN-FUSE / RESCUE-SWITCH v10 Plan Status

- Branch and push: completed for `crown-fuse-rescue-switch`.
- Completion verifier: `tools/verify_fuse_completion.py` implemented and used for `--phase isolation`, `--phase search`, and final gate preparation.
- B0 rescue: reproduced and preserved after freeze.
- No-op isolation: completed after freeze; B1/B2/B3 match B0 exactly on score and action signature.
- Fuse search: completed 100 executed 20260529 TRIAL configs around the B0+B9c knee point; no eligible gross-preserving improvement found.
- Rule ledger: `reports/fuse_rule_ledger.csv` generated with only generic family-level columns.
- Graph diagnostic: completed G0/G1/G2/G3 and killed.
- Qwen auditor numeric ablation: completed A0/A1/A2; auditor numeric remains OFF.
- Top5 0509 sanity: completed 5 full rows; all have `income_abort_count=0`.
- Final selection: B11 is explicit `best_rescue` B0 fallback; B10 search-best rerun collapsed gross.
- Packaging: below score gates, create one review-only package only.
- Remaining before final response: write `reports/fuse_final_report.md`, run package/final verifier, commit/push if clean enough.

- `python tools/audit_guard.py --fail-on-p0`

## Current Progress

- Branch `crown-fuse-rescue-switch` was created and pushed.
- Long Fuse prompt read and adopted.
- Durable rule files are being updated before runtime strategy changes.
- `verify_fuse_completion.py` is being created before B0/no-op/search execution.

# CROWN-SURGE / LEDGER-HUNTER Execution Plan

## Current Branch

- `crown-surge-ledger-hunter`
- Work continues from existing repository and failed `crown-trident-gold2`; no from-scratch rebuild.

## Surge Stop States

- `SURGE_RECOMMENDED_SUBMISSION`: recommended score, final verifier, Qwen, graph, ablation, parameter search, compliance, package audit, commit, and push gates pass.
- `SURGE_EXPERIMENTAL_SUBMISSION`: experimental gates pass without claiming recommended status.
- `DO_NOT_SUBMIT_WITH_SURGE_EVIDENCE`: complete evidence exists but score/package gates fail.
- `DO_NOT_SUBMIT_WITH_INCOMPLETE_EXECUTION`: any required official matrix row, parameter trial set, Qwen effect, official/replan delta, graph evidence, reviewer transcript, report hygiene, or final verifier gate is incomplete.
- `EXTERNAL_BLOCKER_RESCUE_CORE`: B0 cannot run or reproduce because official runner/data/eval infrastructure is blocked.
- `EXTERNAL_BLOCKER_QWEN`: real Qwen path is unavailable for required full runs.
- `EXTERNAL_BLOCKER_EVAL_INFRA`: official-style evaluation cannot run for infrastructure reasons outside runtime strategy.

## Surge Score Gates

- B0 rescue: 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected.
- Experimental: official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 50000, 0 failure/abort/illegal/rejected, B0-B11 executed, 100+ real trials executed, auditor effective or killed by ablation, and `verify_surge_completion.py --phase final` PASS.
- Recommended: official_net >= 38000, preference_penalty <= 22000, gross_minus_cost >= 60000, clean package audit, default variant final selected strategy, and final verifier PASS.

## Surge Work Order

1. Create and push branch `crown-surge-ledger-hunter`.
2. Implement `tools/verify_surge_completion.py` before strategy changes.
3. Update `AGENTS.md`, `agent.md`, `PROJECT_MEMORY`, `EXPERIMENT_LOG`, and `EXECUTION_PLAN` to Surge rules.
4. Restore/run B0 immutable `best_rescue`; stop if B0 gate fails due to rescue core or eval infra.
5. Fix execution harness so Surge ablation/search tools default to execution and never create final planned/missing rows.
6. Run B0-B9c official 31-day matrix with required metrics.
7. Fix Qwen auditor parser/schema/numeric mapping; run off/low/high auditor evidence.
8. Build and run changed-decision official/replan delta lab for 60 selected decisions.
9. Build and run rule doctor for top 6 penalty rules and export only generic family-level scales.
10. Implement/run runtime-only Online Opportunity Graph attack with alpha 0.00/0.05/0.10/0.20/0.35 and B7/B8 evidence.
11. Distill only generic historical behavior stats; never copy ids, places, coordinates, routes, or future cargo.
12. Execute parameter search: Stage A 100 real 20260529 trials, Stage B top20 full, Stage C top5 0509, Stage D top10 confirmation.
13. Select final B11, build the five Surge reports, run reviewers, run final verifier, and package only if gates pass.

## Required Commands Or Equivalents

- `python -m pytest tests -q`
- `python -m compileall demo tools tests`
- `python tools/audit_guard.py --fail-on-p0`
- `python tools/fix_eval_round_bug.py`
- `python tools/qwen_preference_smoke_test.py`
- `python tools/run_local_eval.py --simulation-days 31 --variant best_rescue --results-dir runs/surge/b0_rescue`
- `python tools/run_surge_ablation_matrix.py --execute --phase base --simulation-days 31 --results-root runs/surge/ablations`
- `python tools/run_penalty_calibration_lab.py --execute --simulation-days 31 --results-root runs/surge/penalty_lab`
- `python tools/run_rule_doctor.py --execute --simulation-days 31 --results-root runs/surge/rule_doctor`
- `python tools/run_opportunity_graph_ablation.py --execute --simulation-days 31 --results-root runs/surge/opportunity_graph`
- `python tools/run_surge_param_search.py --execute --trials 100 --simulation-days 31 --results-root runs/surge/search`
- `python tools/run_surge_ablation_matrix.py --execute --phase final --simulation-days 31 --results-root runs/surge/ablations`
- `python tools/build_surge_reports.py --strict`
- `python tools/verify_surge_completion.py --phase final`

## Current Progress

- Local branch `crown-surge-ledger-hunter` created.
- Initial push failed due HTTPS TLS handshake; retry after commit.
- Long Surge prompt, previous reports, Qwen effect, and decision deltas read.
- `tools/verify_surge_completion.py` implemented and `--phase stage0` passed.
- Project rule files updated before runtime strategy changes.
- B0 immutable `best_rescue` ran and passed stage1 gate.
- B0-B9c base matrix ran and passed stage2 verifier.
- Qwen auditor numeric schema was repaired and validated by unit tests; patched B5 produced nonzero numeric adjustments but worsened official score, so auditor is killed by current evidence.
- Surge five reports were generated; old Trident reports were archived.
- Final verifier currently fails for missing B10/B11, 0 executed parameter trials, Qwen valid-rate gap from old auditor traces, and 0 replay-valid decision deltas.

## Current Stop Decision

- Do not submit and do not package.
- Current report first line: `DO NOT SUBMIT: DO_NOT_SUBMIT_WITH_INCOMPLETE_EXECUTION - missing executed rows: ['B10_parameter_search_best', 'B11_final_selected']`.
- Smallest next step if resuming: execute Stage A parameter trials or implement official suffix replay lab; either path must produce real official/replay-valid evidence before changing final strategy.

# Historical CROWN-TRIDENT / GOLD-2 Execution Plan

## Stop States

- `CROWN_TRIDENT_RECOMMENDED_SUBMISSION`: recommended score, Qwen, controller, ablation, compliance, reviewer, package, commit, and push gates pass.
- `CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION`: experimental gates pass without pretending recommendation.
- `DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE`: hard gates fail after complete evidence; no submission-shaped package if below experimental gate.
- `EXTERNAL_BLOCKER_QWEN`: real Qwen is unavailable for all relevant full runs.
- `EXTERNAL_BLOCKER_RESCUE_CORE`: required runner/data/eval infrastructure prevents B0 rescue reproduction.
- `EXTERNAL_BLOCKER_EVAL_INFRA`: official-style evaluation cannot run for infrastructure reasons.
- `DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE`: required real subagents or recorded named reviewer passes cannot be completed.

## Score Gates

- B0 rescue: 20260529 official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected.
- Experimental: 20260529 official_net >= 30000, preference_penalty <= 28000, gross_minus_cost >= 50000, 0 abort/illegal/rejected, nonzero auditor adjustment if auditor used, and clean controller/ablation evidence.
- Recommended: 20260529 official_net >= 38000, preference_penalty <= 22000, gross_minus_cost >= 60000, 0 abort/illegal/rejected, and 0509 clean enough for sanity.
- Crown target: official_net >= 40000, preference_penalty around 18000-22000 or lower, and gross_minus_cost around 58000-65000 or higher.

## Work Order

1. Create and push branch `crown-trident-gold2`.
2. Update persistent project rules and work records before runtime code changes.
3. Launch six required subagents/reviewer passes with disjoint ownership where possible.
4. Restore and verify immutable `best_rescue` as B0.
5. Inventory existing variants, runners, reports, and run artifacts; map equivalent commands to required Trident wrappers.
6. Implement missing Trident tools only when equivalent project commands do not exist.
7. Stage 0: reproduce score accounting table and confirm official_net = gross_minus_cost - preference_penalty.
8. Stage 1-2: generate rule ledger and changed-decision deltas before final strategy tuning.
9. Stage 3-5: implement Preference Contract V2, Qwen numeric auditor effect, and scorer microprobe alignment.
10. Stage 6-7: run B0-B11 ablations and rule doctor treatments.
11. Stage 8-10: distill high-score generic statistics, implement runtime-only graph if useful, and run parameter search.
12. Stage 11: select smallest score-positive final variant, build final reports, run verification, commit, push, and package only if gates allow.

## Required Commands Or Equivalents

- `python -m pytest tests -q`
- `python -m compileall demo tools tests`
- `python tools/audit_guard.py --fail-on-p0`
- `python tools/fix_eval_round_bug.py`
- `python tools/qwen_preference_smoke_test.py`
- `python tools/run_trident_baselines.py --simulation-days 31`
- `python tools/build_trident_penalty_ledger.py --simulation-days 31`
- `python tools/build_trident_decision_deltas.py --simulation-days 31`
- `python tools/run_trident_ablation_matrix.py --simulation-days 31`
- `python tools/run_trident_param_search.py --trials 100`
- `python tools/build_trident_reports.py`

If a required command is missing, implement it or record the exact equivalent command and output.

## Current Progress

- Branch `crown-trident-gold2` was created and pushed to origin.
- Long prompt and previous Gold project rules were read.
- Persistent Trident rules were written to `AGENTS.md`, `agent.md`, `docs/AGENT_WORK/PROJECT_MEMORY.md`, `docs/AGENT_WORK/EXPERIMENT_LOG.md`, and `docs/AGENT_WORK/EXECUTION_PLAN.md`.

## Keep/Kill Policy

- Keep only generic, non-driver-specific parameters and modules with official score-positive evidence or clear named regret reduction.
- Disable controllers, auditor adjustments, graph parameters, or repair bonuses that worsen official_net or are negative-delta dominated.
- Never hard-block or apply massive penalties without scorer-semantics alignment.
- Never use dummy keys, disabled runtime Qwen, smoke tests, synthetic tests, package shape, or zero-illegal status as success.

## Report / Package Policy

- Final reports are limited to `trident_final_report.md`, `trident_experiments.csv`, `trident_rule_ledger.csv`, `trident_decision_deltas.csv`, and `trident_qwen_effect.csv`.
- If final official_net < 30000, the final report begins with `DO NOT SUBMIT: <precise reason>` and no submission-shaped zip is created.
- If a package is generated, inspect root and exclusions before any submission claim.

# CROWN-DRAGON-ORCA v1.1 Execution Plan

1. Implement and run tools/verify_dragon_orca_completion.py setup before relying on strategy evidence.
2. Archive old report files outside reports/ and keep final reports to the five dragon_orca_* artifacts.
3. Execute D0-D4 no-op/query-noop isolation and block search on drift.
4. Execute A1-A3 archaeology references and M0-M13 mandatory strategy rows.
5. Execute at least 60 full 20260529 search rows, ReEvo/evolution rows, and B0 + top5 20260509 sanity.
6. Build regret attribution, value-model audit, reviewer QA, package audit, and final report.
7. Run pytest, compileall, audit_guard, all Dragon verifier phases, then commit and push.
