FUSE_REVIEW_PACKAGES_ONLY

# CROWN-FUSE / RESCUE-SWITCH v10 Final Report

- git branch: `crown-fuse-rescue-switch`
- source_code_commit: `d53c05ca4db4d9bd08021641247a911869c9d55d`
- evidence_commit: `working-tree-final-evidence-before-commit`
- stop_state_reason: no targeted-repair knee preserved B0 gross enough to become a submission candidate; B11 is explicit B0 fallback.

## Decision

No recommended or experimental submission was produced. The only package is review-only:

- package audit: `reports/fuse_package_audit.md`
- zip: `runs/packages/CROWN_FUSE_REVIEW_ONLY_NOT_FOR_SUBMISSION.zip`
- SHA256: `5cf71af50e1a7459de3eb474ceb4bc5537a53c3bcb93227e829cb1033d8c410a`
- size_bytes: `99806`
- default variant: `best_rescue`

## Core Rows

| row | run_dir | command evidence | exit_code | official_net | gross_minus_cost | preference_penalty | mix |
|---|---|---|---:|---:|---:|---:|---|
| B0 | `runs/fuse/b0_rescue` | `tools/run_local_eval.py --variant best_rescue` | 0 | 5067.69 | 43207.69 | 38140.0 | 89 take / 163 wait / 0 reposition |
| B9c | `runs/fuse/b9c_reference` | `--variant crown_gold_contract_mpc --results-dir runs\fuse\b9c_reference` | 0 | -157.97 | 29142.03 | 29300.0 | 79 take / 254 wait / 47 reposition |
| B10 | `runs/fuse/final/20260529/B10_parameter_search_best` | `--variant fuse_targeted_repair --results-dir runs\fuse\final\20260529\B10_parameter_search_best` | 0 | -4348.69 | 18551.32 | 22900.0 | 34 take / 175 wait / 2 reposition |
| B11 | `runs/fuse/final/20260529/B11_final_selected_b0_fallback` | `--variant best_rescue --results-dir runs\fuse\final\20260529\B11_final_selected_b0_fallback` | 0 | 5067.69 | 43207.69 | 38140.0 | 89 take / 163 wait / 0 reposition |

B11 has `fallback_to_b0=true`, `default_variant_verified=true`, Qwen compile/cache `7`, Qwen link/cache `1`, and auditor numeric `0`.

## fuse grid

- `reports/fuse_grid.csv` contains 116 rows total.
- 20260529 executed rows: 111.
- 20260529 TRIAL rows: 100, all `status=EXECUTED`.
- No `PLANNED`, `MISSING_RUN`, proxy-only, smoke-only, or diagnostic-only row is used for completion.
- Best raw search row was `trial_017`: official_net `8142.11`, gross_minus_cost `37562.11`, preference_penalty `29420.0`, run_dir `runs/fuse/search/20260529/trial_017`, exit_code `0`. It improved net and penalty but failed the gross-preservation knee because gross was below `39000`.
- Eligible knee candidates found: `0`.

## Rule Ledger

`reports/fuse_rule_ledger.csv` is aggregated by `rule_family` only. It exports generic parameters: `controller_family_scale`, `primitive_family_scale`, `counting_unit_scale`, `deadline_curve`, `repair_multiplier`, `already_failed_discount`, and `cap_discount`. It does not export rule hashes, driver hashes, preference hashes, cargo ids, places, coordinates, or routes.

## Graph And Auditor

- Graph diagnostic rows G0/G1/G2/G3 all executed. G1/G2 did not improve over G0, and G3 was worse: G0/G1/G2 official_net `2350.86`, G3 `2153.82`. Graph remains killed.
- Auditor rows A0/A1/A2 all executed. A1/A2 had json_valid_rate `1.0` and nonzero adjustments, but official score worsened versus A0:
  - A0: official_net `-630.73`, penalty `26540.0`, auditor calls `0`.
  - A1: official_net `-17992.01`, penalty `41040.0`, auditor calls `174`, nonzero adjustments `675`.
  - A2: official_net `-11014.39`, penalty `34540.0`, auditor calls `178`, nonzero adjustments `693`.
- Final Qwen numeric auditor adjustment is OFF.

## 20260509 Sanity

Top 5 20260529 configs were run as full 20260509 sanity rows. All have `status=EXECUTED`, `exit_code=0`, and `income_abort_count=0`:

| trial_id | official_net | gross_minus_cost | preference_penalty |
|---|---:|---:|---:|
| trial_017_0509 | 63092.22 | 147352.22 | 84260.0 |
| trial_001_0509 | 86900.14 | 185150.15 | 98250.0 |
| trial_002_0509 | 86900.14 | 185150.15 | 98250.0 |
| trial_003_0509 | 86900.14 | 185150.15 | 98250.0 |
| trial_004_0509 | 87849.47 | 187069.48 | 99220.0 |

These sanity rows are clean for aborts, but they do not make B11 a recommended or experimental package because B11's 20260529 score is below submission gates.

## QA

- Execution Evidence Auditor: PASS for B0, B9c, B10, B11, G0-G3, A0-A2, 100 TRIAL rows, and top5 0509 rows; cited run_dirs, commands, exit codes, scores, action mixes, and Qwen counts. The noted missing final report is resolved by this file; the noted ledger specificity was fixed by aggregating to family-only rows.
- Rescue Isolation Auditor: PASS. `reports/fuse_noop_isolation.csv` shows B0/B1/B2/B3 all `EXECUTED`, score deltas `0.0`, action_signature_match_rate `1.0`, identical action mix, and 0 invalid counters.
- Fuse Grid Auditor: PASS. 100 full 20260529 TRIAL rows exist; the 100-run trigger was satisfied by `trial_017`; no eligible gross-preserving knee candidate exists.
- Qwen Auditor Reviewer: PASS. B11 has nonzero compile/cache and link/cache; A1/A2 do not beat A0 despite valid nonzero adjustments, so numeric auditor remains OFF.
- Package Gatekeeper: PASS. One review-only zip exists; root is `demo/`, includes `demo/agent/` and `demo/SUBMISSION.md`, excludes forbidden paths, records SHA256/size, default variant is `best_rescue`, and `SUBMISSION.md` first line is exactly `NOT RECOMMENDED FOR B榜 SUBMISSION`.

## Verification

- `python tools\verify_fuse_completion.py --phase isolation`: PASS.
- `python tools\verify_fuse_completion.py --phase search`: PASS.
- `python tools\audit_guard.py --fail-on-p0`: PASS, P0 `0`.
- `python -m compileall demo tools tests`: PASS.
- Final gate to run after this report is written: `python tools\verify_fuse_completion.py --phase final`.
