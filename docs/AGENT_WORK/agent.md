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

# CROWN-DRAGON-ORCA v1.1 Active Work

- Branch: crown-dragon-orca-v1-1.
- Stop states: DRAGON_RECOMMENDED_SUBMISSION, DRAGON_EXPERIMENTAL_SUBMISSION, DO_NOT_SUBMIT_WITH_COMPLETE_NEGATIVE_EVIDENCE, DO_NOT_SUBMIT_WITH_REVIEW_ONLY_PACKAGE, DO_NOT_SUBMIT_WITH_INCOMPLETE_SEARCH, DO_NOT_SUBMIT_WITH_INTERNAL_COMPILER_FAILURE_BUT_SEARCH_COMPLETE, PROMPT_NONCOMPLIANCE_FAIL, EXTERNAL_BLOCKER_QWEN_API, EXTERNAL_BLOCKER_EVAL_INFRA, EXTERNAL_BLOCKER_REPO_OR_RESOURCE.
- Hard rule: no active-module claim without runtime code, deterministic test, trace used_count, 31-day full-run evidence, and score/ablation evidence.
- Qwen numeric auditor is OFF; schema weakness cannot stop strategy search.
- Runtime must stay inside SimulationApiPort, current post-query actionable cargo, current-run generic observations, and generic parameters.
- Final reports are exactly the five dragon_orca_* files; raw outputs stay under runs/dragon_orca and reviewer notes under runs/dragon_orca/reviewers.
