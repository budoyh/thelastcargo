# CROWN-GOLD Package Audit

Status: NO PACKAGE GENERATED.

Reason: 20260529 final selected run did not reach `CROWN_GOLD_EXPERIMENTAL_SUBMISSION` score gates. The build therefore must stop as `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE` and must not create a submission-shaped zip.

Package facts checked from repository state:

- Default runtime variant in `demo/agent/config.py`: `crown_gold_contract_mpc`.
- Gold report set is limited to the five allowed files under `reports/`.
- Old Exact/PTT package artifacts and the previous Delta zip from `submissions/` were moved under `archive/`.
- `tools/build_submission_package.py` and `tools/inspect_submission_package.py` were updated for Gold naming/default-variant checks, but were not used to create a zip because score gates failed.
- `tools/build_submission_package.py` now refuses to build any Gold package unless `--recommended` or `--not-recommended` is explicitly supplied.

Residual package risk: no unpack audit was run for Gold because no Gold zip exists.
