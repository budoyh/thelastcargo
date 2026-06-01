# CROWN-Delta MPC Experiment Log

## 2026-06-01 Setup

- Read `crown_delta_mpc_codex_prompt.md` and `补丁.md`.
- Created branch `crown-delta-mpc`.
- Loaded existing reports and run outputs instead of rebuilding from scratch.
- Identified old PCE reports in `reports/`; these must be archived before final handoff.
- Confirmed existing scorer output treats `net_income` as official net, already subtracting preference penalty.

## Initial Baseline Evidence

| dataset | variant | official_net | gross_minus_cost | preference_penalty | take | wait | reposition | notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 20260529 | rescue reference | 5067.69 | 43207.69 | 38140.00 | 89 | 163 | 0 | failed baseline to beat |
| 20260529 | PCE final | -3125.02 | 34114.98 | 37240.00 | 117 | 199 | 0 | report-complete but score failed |
| 20260529 | strict preference | 2240.98 | 38900.98 | 36660.00 | 73 | 180 | 0 | lower gross, still high penalty |
| 20260529 | money trajectory repair oracle | 35849.85 | 53169.85 | 17320.00 | 69 | 147 | 0 | diagnostic frontier, not runtime |

## Reviewer Notes

- Compliance reviewer found no P0 runtime boundary violation.
- Low-risk notes: Qwen HTTP fallback is allowed by current project rule but should stay budgeted; non-submit traces can contain real cargo ids and must not be copied into final reports.

## Delta-MPC Runtime Results

| dataset | variant | official_net | gross_minus_cost | preference_penalty | take | wait | reposition | macro_completed | notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 20260529 | delta_mpc_macro | -10620.70 | 35299.31 | 45920.00 | 109 | 259 | 0 | 31 | macro entered runtime but official net worsened |
| 20260529 | delta_mpc_fallback | -5112.02 | 41347.98 | 46460.00 | 86 | 186 | 1 | 32 | best Delta-MPC runtime row, still below rescue |
| 20260509 | delta_mpc_fallback | 102265.64 | 201985.65 | 99720.00 | 423 | 821 | 0 | 31 | no catastrophic 0509 regression |

## Final Verification

- Delta labels: 103 rows, 3 exact run-pair labels, 100 replay/heuristic diagnostic labels.
- Automata eval: high-lambda runtime enablement disabled because official-net ablation did not prove positive delta.
- Qwen smoke: compile_calls=1, rules_returned=1, dummy key blocked count 0, fallback count 0.
- Synthetic paraphrase checks: 8/8 passed after adding abstract visible-field terms to the deterministic compiler.
- Local checks: compileall passed, `python -m pytest tests -q` passed with 57 tests, audit guard reported P0=0, round bug patch present.
- Final stop state: `DO_NOT_SUBMIT_WITH_DELTA_EVIDENCE`; bottleneck is incomplete official-scorer action-level delta evidence and macro variants not producing positive official-net delta.
