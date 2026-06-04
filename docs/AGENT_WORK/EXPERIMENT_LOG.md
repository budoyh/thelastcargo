# CROWN-FUSE / RESCUE-SWITCH Experiment Log

## 2026-06-02 Fuse Kickoff

- Long prompt read: `crown_fuse_rescue_switch_codex_prompt.md`.
- Local branch created: `crown-fuse-rescue-switch`.
- Push command: `git push -u origin crown-fuse-rescue-switch` exited 0 and set upstream.
- Worktree already contained uncommitted Surge-era changes; they were preserved and not reverted.
- Controlling objective: find B0+B9c knee point with targeted repair overlay, not a new architecture.
- Hard gate to implement first: `tools/verify_fuse_completion.py`.
- Durable Fuse rules added to `AGENTS.md`, `agent.md`, `PROJECT_MEMORY.md`, `EXPERIMENT_LOG.md`, and `EXECUTION_PLAN.md`.
- Current required next checks: B0 `best_rescue` reproduction, B1/B2/B3 no-op isolation, then fuse grid only after isolation passes.

## 2026-06-02 Fuse B0 And No-op Isolation

- `python tools\run_local_eval.py --simulation-days 31 --variant best_rescue --results-dir runs\fuse\b0_rescue` exited 0.
- B0 result: official_net `5067.69`, gross_minus_cost `43207.69`, preference_penalty `38140.0`, take/wait/reposition `89/163/0`, invalid/failure/rejected `0`.
- Implemented `tools/verify_fuse_completion.py`; compile check exited 0.
- Implemented `tools/run_fuse_noop_isolation.py`; B1/B2/B3 use the `fuse_rescue_core` alias with no scoring/action overlays.
- `python tools\run_fuse_noop_isolation.py --simulation-days 31 --results-root runs\fuse\noop --out reports\fuse_noop_isolation.csv` exited 0.
- B1/B2/B3 result: action_signature_match_rate `1.0`, action_signature_mismatch_count `0`, official_net/gross/penalty/action mix identical to B0.
- `python tools\verify_fuse_completion.py --phase isolation` exited 0 with PASS.
- Implemented initial `demo/agent/fuse_repair.py` and B0 Shadow Guard integration; smoke command `python tools\run_local_eval.py --simulation-days 31 --max-steps 20 --variant fuse_targeted_repair --results-dir runs\fuse\smoke_targeted_repair --skip-income` exited 0.

# CROWN-SURGE / LEDGER-HUNTER Experiment Log

## 2026-06-02 Surge Kickoff

## 2026-06-03 CROWN-FUSE / RESCUE-SWITCH v10 Completion Evidence

- Branch `crown-fuse-rescue-switch` is active and pushed.
- `python tools\verify_fuse_completion.py --phase search` passed after the executed grid, graph, auditor, B10/B11, and 0509 rows were present.
- Frozen no-op rerun command: `python tools\run_fuse_noop_isolation.py`; after archiving stale pre-freeze/timeout partial run dirs, B0/B1/B2/B3 all executed and `python tools\verify_fuse_completion.py --phase isolation` passed.
- No-op metrics: B0/B1/B2/B3 official_net `5067.69`, gross_minus_cost `43207.69`, preference_penalty `38140.0`, action_signature_match_rate `1.0` for B1/B2/B3.
- Grid evidence in `reports/fuse_grid.csv`: 116 total rows, 111 executed 20260529 rows, 100 executed TRIAL rows, 5 executed 20260509 sanity rows.
- B0 row: `runs/fuse/b0_rescue`, command `tools/run_local_eval.py --variant best_rescue`, exit_code `0`, official_net `5067.69`, gross `43207.69`, penalty `38140.0`.
- B9c row: `runs/fuse/b9c_reference`, official_net `-157.97`, gross `29142.03`, penalty `29300.0`.
- Best search row: `trial_017`, run_dir `runs/fuse/search/20260529/trial_017`, official_net `8142.11`, gross `37562.11`, penalty `29420.0`, killed because gross was below `39000`.
- B10 final row: `runs/fuse/final/20260529/B10_parameter_search_best`, official_net `-4348.69`, gross `18551.32`, penalty `22900.0`, killed.
- B11 final row: `runs/fuse/final/20260529/B11_final_selected_b0_fallback`, variant `best_rescue`, official_net `5067.69`, gross `43207.69`, penalty `38140.0`, fallback_to_b0 `true`, default_variant_verified `true`.
- Qwen auditor ablation: A0 official_net `-630.73`; A1 official_net `-17992.01`, json_valid_rate `1.0`, qwen_auditor_calls `174`, nonzero adjustments `675`; A2 official_net `-11014.39`, json_valid_rate `1.0`, qwen_auditor_calls `178`, nonzero adjustments `693`. Numeric auditor remains OFF.
- Graph diagnostic: G0/G1/G2 official_net `2350.86`, G3 official_net `2153.82`; graph killed.
- Top5 20260509 sanity rows `trial_017_0509`, `trial_001_0509`, `trial_002_0509`, `trial_003_0509`, `trial_004_0509` all `EXECUTED` with `income_abort_count=0`.
- Review-only package generated: `runs/packages/CROWN_FUSE_REVIEW_ONLY_NOT_FOR_SUBMISSION.zip`, SHA256 `5cf71af50e1a7459de3eb474ceb4bc5537a53c3bcb93227e829cb1033d8c410a`, size `99806`, package audit PASS.

- Branch created locally: `crown-surge-ledger-hunter`.
- Push attempt: `git push -u origin crown-surge-ledger-hunter` failed with `schannel: failed to receive handshake, SSL/TLS connection failed`; retry after local commit.
- Controlling prompt adopted from `crown_surge_ledger_hunter_codex_prompt.md`.
- Current failed carry-forward evidence: B1-B8/B10/B11 were `MISSING_RUN`, parameter trials were `PLANNED` / `planned_not_evaluated`, Qwen auditor adjustment was all zero, and changed-decision delta labels were diagnostic-only.
- New hard gate implemented: `tools/verify_surge_completion.py`.
- Verification run: `python tools\verify_surge_completion.py --phase stage0` exited 0 with branch check PASS.
- Compile run: `python -m compileall tools\verify_surge_completion.py` exited 0.
- Surge final completion remains unproved until B0-B9c/B10/B11, 100+ real trials, Qwen effect, decision deltas, rule doctor, graph ablations, reviewers, final reports, and `--phase final` all pass.

## 2026-06-02 Executed Surge Evidence

- B0 command: `python tools\run_local_eval.py --simulation-days 31 --variant best_rescue --results-dir runs\surge\b0_rescue`.
- B0 result: official_net `5067.69`, gross_minus_cost `43207.69`, preference_penalty `38140.0`, invalid/failure/rejected `0`; `python tools\verify_surge_completion.py --phase stage1` passed.
- Base matrix command: `python tools\run_surge_ablation_matrix.py --execute --phase base --simulation-days 31 --results-root runs\surge\ablations`.
- Base matrix result: B0-B9c all executed in `reports/surge_experiments.csv`; `python tools\verify_surge_completion.py --phase stage2` passed with command-transcript warnings.
- Best base non-B0 result remained below B0: B9c official_net `-157.97`, gross_minus_cost `29142.03`, preference_penalty `29300.0`.
- Opportunity graph rows executed but killed: B7 official_net `-1321.92`; B8 official_net `-11080.66`; both below B0.
- Qwen auditor was repaired to schema-valid numeric adjustment in patched B5 (`runs/surge/ablations_patched3/20260529/B5_qwen_auditor_numeric_adjustment`): qwen_auditor_calls `257`, qwen_audit_adjustment_nonzero_count `1022`, qwen effect rows `1024/1024` json-valid for that run, but official_net worsened to `-19535.83` and preference_penalty to `50800.0`; auditor should be killed unless future official evidence reverses this.
- `python tools\build_surge_reports.py --archive-extra-reports` generated the five Surge reports and archived old Trident reports under `archive/reports_non_surge/`.
- `python tools\verify_surge_completion.py --phase final` failed with remaining hard gaps: missing B10/B11, executed parameter trial count `0`, overall Qwen valid rate `0.068` due old auditor traces, and valid official/replan delta count `0`.
- `python -m compileall demo tools tests` exited 0.
- `python tools\audit_guard.py --fail-on-p0` exited 0 after adapting report-file hygiene to the Surge five-file set; findings `9`, P0 `0`.
- `git push -u origin crown-surge-ledger-hunter` succeeded and created/tracked the remote branch; current evidence files remain uncommitted local changes.

## 2026-06-02 Stop-State Evidence

- Current stop state in `reports/surge_final_report.md`: `DO NOT SUBMIT: DO_NOT_SUBMIT_WITH_INCOMPLETE_EXECUTION - missing executed rows: ['B10_parameter_search_best', 'B11_final_selected']`.
- No submission-shaped ZIP was generated.
- Diagnostic decision deltas and rule doctor rows were written only as failure evidence; they must not tune weights.

## Surge Required Evidence

- B0 rescue official 31-day reproduction on 20260529.
- B0-B9c base official ablations, including B7/B8 graph variants and wait repair off/half/full.
- B5 auditor off/low/high evidence with JSON-valid, nonzero numeric adjustment or auditor killed.
- 60 changed-decision paired suffix/replan labels with official/replan-valid deltas and compatibility fields.
- Top 6 rule doctor official ablations and generic family-level exports only.
- Opportunity Graph alpha executions for 0.00/0.05/0.10/0.20/0.35 with visible/terminal use counts >0 if retained.
- Parameter search: Stage A 100 real 20260529 trials, Stage B top20 full 31-day, Stage C top5 0509 sanity, Stage D top10 confirmation.
- Final reports limited to five Surge artifacts; package only if score and verifier gates pass.

# Historical CROWN-TRIDENT / GOLD-2 Experiment Log

## 2026-06-02 Trident Kickoff

- Branch created and pushed: `crown-trident-gold2`.
- Controlling prompt adopted from `crown_trident_gold2_codex_prompt.md`.
- Required stop states: `CROWN_TRIDENT_RECOMMENDED_SUBMISSION`, `CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE`, `EXTERNAL_BLOCKER_QWEN`, `EXTERNAL_BLOCKER_RESCUE_CORE`, `EXTERNAL_BLOCKER_EVAL_INFRA`, and `DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE`.
- Working diagnosis: Gold changed many decisions but did not reduce official preference penalty. The first broken link is decision changed -> official penalty reduced.
- Working rule: no synthetic pass, Qwen smoke, legal-action count, report completeness, call count, controller count, or package shape can substitute for official score and causal delta evidence.

## Baseline Facts Carried Forward

- Historical B0 rescue target for 20260529:
  - official_net 5067.69
  - gross_minus_cost 43207.69
  - preference_penalty 38140.00
  - actions 89 take / 163 wait / 0 reposition
- Gold final selected on 20260529:
  - official_net 6373.17
  - gross_minus_cost 45993.17
  - preference_penalty 39620.00
  - Qwen compile/link/audit 5 / 245 / 245
  - controller_scored_candidate_count 11461
  - changed_decision_count 240
- Trident B0 must reproduce official_net >= 5000, gross_minus_cost >= 43000, preference_penalty <= 38200, and 0 failure/abort/illegal/rejected before final tuning evidence is meaningful.

## 2026-06-02 Required Evidence Plan

- Stage 0: reproduce rescue, money, strict, safe-profit, and current Gold score table; confirm official_net = gross_minus_cost - preference_penalty.
- Stage 1: build `reports/trident_rule_ledger.csv`.
- Stage 2: build `reports/trident_decision_deltas.csv`.
- Stage 3: implement Preference Contract V2 rule-state delta.
- Stage 4: build `reports/trident_qwen_effect.csv` with nonzero auditor adjustment if auditor is retained.
- Stage 5: run scorer microprobe farm before hard blocks or massive penalties.
- Stage 6: run B0-B11 official ablation matrix.
- Stage 7: run rule-level doctor ablations.
- Stage 8: distill only generic statistics from high-score historical trajectories.
- Stage 9: implement runtime-only Online Opportunity Graph and alpha tests.
- Stage 10: run parameter attack over generic parameters.
- Stage 11: choose smallest score-positive final variant and gate packaging.

## 2026-06-02 Subagent Requirement

- Real multi-agent tooling is available in this environment.
- Required named subagents/reviewer passes will be launched for:
  - Rescue Baseline Keeper
  - Penalty Attribution / Regret Lab
  - Preference Contract / Qwen Auditor Engineer
  - Profit Backbone / Online Graph Engineer
  - Parameter Search / Ablation Engineer
  - Compliance / Package Gatekeeper
- Each pass must report changed files, commands run, before/after metrics, pass/fail, blockers, and keep/kill.

## Running Command Ledger

- `git switch -c crown-trident-gold2` exited 0.
- `git push -u origin crown-trident-gold2` exited 0.
- Long prompt and project rule files were read before code edits.
- `AGENTS.md`, `agent.md`, and durable work records were updated to Trident rules before runtime code changes.
