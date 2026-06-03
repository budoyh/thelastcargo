# Pref-Forge Reviewer Findings

## Instruction Compliance Auditor

- mode: real read-only subagent `019e8e3e-8b74-7db0-b157-4662612d6cb1`.
- changed_files: `[]`.
- commands_run: `git status --short`; `python tools\pref_forge_verify_completion.py --phase benchmark`; `python tools\pref_forge_verify_completion.py --phase noop`; `python tools\pref_forge_verify_completion.py --phase experiments`; `python tools\pref_forge_verify_completion.py --phase final`; `Get-ChildItem reports`; CSV aggregation over `reports/pref_forge_compile_benchmark.csv`.
- metrics_before_after: E0/B0 reproduced net `5067.69`, gross `43207.69`, penalty `38140.0`; E1/E2 action_signature_match_rate `1.0`; compile benchmark schema valid `59/66=0.8939`, primitive family `66/66=1.0`, Qwen calls `1058`.
- pass_fail_against_task: FAIL for full prompt completion. `EXTERNAL_BLOCKER_QWEN_API` is a valid stop_state, reports shape is clean, and package policy correctly generated no zip, but mandatory E6-E13, E11, 60 search rows, and 0509 sanity rows are missing because earlier gates failed.
- unresolved_blockers: Qwen schema gate `0.8939 < 0.98`; E5 penalty_delta_vs_b0 `10080.0 > 8000`; missing E6-E13, E11, search, and 0509 evidence.
- recommend_keep_or_kill: keep E0/E1/E2 isolation evidence; kill submission/package claim; kill or retune E3/E4/E5 variants.

## Preference Compiler Auditor

- mode: real read-only subagent `019e8e3e-b369-71f1-955e-7e7324920751`.
- changed_files: `[]`.
- commands_run: `python tools\pref_forge_verify_completion.py --phase benchmark`; `python tools\pref_forge_qwen_prompt_ablation.py`; read-only CSV/JSONL aggregations over `reports/pref_forge_compile_benchmark.csv` and `.private/pref_forge/qwen_raw_io_untracked.jsonl`; `git check-ignore -v .private\pref_forge\qwen_raw_io_untracked.jsonl`.
- metrics_before_after: compile benchmark has 66 rows: 46 public, 15 synthetic holdout, 5 adversarial holdout. Row schema valid `59/66=0.893939`; primitive family `66/66=1.0`; raw JSONL `1058` valid JSON lines; call-level ok rate `1001/1058=0.9461`. Weakest steps were counterexample, critic, dimension tagger, and slot extractor.
- pass_fail_against_task: FAIL compiler benchmark. Primitive-family accuracy passes, but multi-step schema robustness fails `schema_valid_rate 0.894 < 0.980`.
- unresolved_blockers: 7 public rows fail row-level schema; schema gate is short by `0.086061`; ablation script appends to work log and should not be used as a read-only audit command without wrapping.
- recommend_keep_or_kill: kill current compiler evidence for pass/submission claims; keep raw/CSV evidence only as diagnostic evidence.

## Runtime Integration Auditor

- mode: real read-only subagent `019e8e3e-db52-7722-b1d8-c0d79d19eeec`.
- changed_files: `[]`.
- commands_run: `python tools\pref_forge_audit_runtime_leakage.py --fail-on-any`; `Get-Content runs\pref_forge\runtime_leakage_audit.md`; targeted `rg` over `demo/agent/config.py`, `demo/agent/rescue_scorer.py`, `demo/agent/qwen_preference_compiler.py`, `demo/agent/preference_primitives.py`.
- metrics_before_after: runtime leakage audit passed with findings `0`. Preference primitives are generic; Pref-Forge config keeps `ENABLE_PTT_AUDITOR=False`; Qwen compiler returns JSON-only metadata and hashes runtime refs.
- pass_fail_against_task: PASS_WITH_RESIDUAL_RISK. RuntimeRuleState, Preference Shield, Hunter, and Qwen compiler boundaries were acceptable, but reviewer noted shared rescue scoring could consume a stale `qwen_audit_adjustment`.
- unresolved_blockers: static leakage scan cannot prove the entire query/refresh/take call chain; Pref-Forge needed explicit numeric-auditor guard.
- follow-up_fix: added `demo/agent/rescue_scorer.py` guard so `crown_pref_forge` or disabled auditor ignores numeric `qwen_audit_adjustment`, and added `tests/test_crown_y_core.py::test_pref_forge_ignores_qwen_auditor_adjustment_in_rescue_score`.
- verification_after_fix: targeted auditor tests `3 passed`; full pytest `70 passed`; raw literal audit `findings=0`; runtime leakage audit `findings=0`; compileall passed.
- recommend_keep_or_kill: keep runtime boundary with guardrail; do not enable numeric auditor for Pref-Forge.

## Execution Evidence Auditor

- mode: real read-only subagent `019e8e3f-0358-75d2-a08c-f146bd262dec`.
- changed_files: `[]`.
- commands_run: `python tools/pref_forge_verify_completion.py --phase benchmark`; `--phase noop`; `--phase experiments`; `--phase final`; CSV/run_dir checks for `reports/pref_forge_experiment_grid.csv`, `reports/pref_forge_penalty_diff.csv`, and `runs/pref_forge/*`.
- metrics_before_after: E0 net `5067.69`, gross `43207.69`, penalty `38140.0`; E1/E2 exact no-op match; E3/E4 net `-38088.76`, penalty `67040.0`; E5 v13 net `-1332.9`, gross `46887.1`, penalty `48220.0`, penalty_delta_vs_b0 `10080.0`; E6-E13 absent; search rows `0`; 0509 rows `0`; penalty diff has 76 rows.
- pass_fail_against_task: FAIL. Full official ablation is incomplete and cannot be represented as successful evidence.
- unresolved_blockers: benchmark schema failure; E5 penalty explosion; E6-E13 missing; E11 missing; 60 search rows missing; 0509 sanity missing.
- recommend_keep_or_kill: keep only E0/E1/E2 baseline/isolation evidence; keep E3/E4/E5 as failure diagnostics; kill Pref-Forge submission path.

## Leakage / Package Gatekeeper

- mode: real read-only subagent `019e8e3f-2b2f-74b3-8e96-10ff5cec5c47`.
- changed_files: `[]`.
- commands_run: `Get-Content reports\pref_forge_package_audit.md`; `Get-Content runs\pref_forge\raw_literal_audit.md`; `Get-Content runs\pref_forge\runtime_leakage_audit.md`; `Get-Content runs\trident_compliance_audit.md`; `Get-ChildItem runs\packages -Recurse -File`; inspect archived zip under `archive\pref_forge_old_packages_20260604_001900`.
- metrics_before_after: package audit label `none`, package path empty, size `0`, entry_count `0`, forbidden_entries `0`, status `PASS_NO_PACKAGE_WEAK_GATE_NOT_MET`; raw literal audit findings `0`; runtime leakage audit findings `0`; compliance audit p0_findings `0`; `runs/packages` contains no zip.
- pass_fail_against_task: PASS for current no-package state. One old Fuse review zip was archived with first line `NOT RECOMMENDED FOR B榜 SUBMISSION`; it is not a current submission package.
- unresolved_blockers: 38 P2 manual-review items remain in compliance audit, but P0 is zero.
- recommend_keep_or_kill: keep no-package gate; keep archived zip only as historical archive; kill any claim that an active submission zip exists.
