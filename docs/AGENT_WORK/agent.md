# Pref-Forge Agent Rules

- Active branch: `crown-pref-forge-v1`.
- Stop only with a Pref-Forge allowed stop_state from the prompt.
- Use executed official rows only; no planned, proxy, smoke, copied historical, or diagnostic-only row can satisfy completion.
- Keep raw preferences and raw Qwen IO only in `.private/pref_forge/`.
- Qwen roles are compiler, observed-vocabulary linker, and gated relationship auditor only; numeric auditor scoring remains off.
- Runtime code must not read raw data, reports, runs, scorer outputs, income internals, future cargo, or server/bench internals.
- Runtime may use current injected state, post-query current_actionable cargo, same-driver current-run legal summaries, generic weights, and abstract primitive families.
- Final reports in `reports/` are limited to the five `pref_forge_*` files.
- Packages are forbidden unless weak improvement is proven; weak-only packages are review-only and not for submission.
- Reviewers are read-only QA gates and must cite concrete files, rows, commands, exit codes, and metrics.
