# Anti-Shell Source Auditor

- reviewer_name: Anti-Shell Source Auditor
- scope: CROWN-PIVOT-REDLINE v1 read-only source review for Dragon/Rescue shell layering, runtime invocation, candidate/score/action effect, Rescue dependency, and trace authenticity.
- changed_files_seen: none by reviewer; existing untracked files were observed.
- source_files_checked: `demo/agent/model_decision_service.py`, `demo/agent/rescue_scorer.py`, `demo/agent/config.py`, `demo/agent/query_policy.py`, `demo/agent/candidate_generator.py`, `demo/agent/preference_monitor.py`, `demo/agent/preference_debt_market.py`, `demo/agent/visible_rollout.py`, `demo/agent/visible_graph_mpc.py`, `demo/agent/learned_ranker.py`, `tools/run_dragon_orca_experiment_grid.py`, `tools/verify_dragon_orca_completion.py`, `tools/evolve_dragon_heuristics.py`, `tools/build_dragon_regret_analyzer.py`, plus `demo/agent/trace_writer.py` and `tools/dragon_orca_common.py`.
- commands_run: `git branch --show-current`; `git status --short`; multiple read-only `rg`, `Get-Content`, `Import-Csv`, `ConvertFrom-Json`, and `Select-String` inspections.
- csv_rows_checked: `reports/dragon_orca_experiment_grid.csv` has 66 rows, including 60 executed 20260529 rows and 6 executed 20260509 rows; `reports/dragon_orca_regret_attribution.csv` has 50 rows.
- run_dirs_checked: `runs/dragon_orca/eval_20260529/M13_final_selected`, `runs/dragon_orca/eval_20260529/M9_repair_skeleton_gross_refill`, and `runs/dragon_orca/eval_20260529/search/G001`.
- metrics_before_after: read-only snapshot; M13 `official_net=-22750.93`, `gross_minus_cost=29549.07`, `preference_penalty=52300.0`; M7 `official_net=-28676.55`, `gross_minus_cost=35363.45`, `preference_penalty=64040.0`.
- pass_fail_against_prompt: FAIL

## Blocking Findings

1. Dragon/Orca is a Rescue runtime overlay. `config.py` enables `ENABLE_RESCUE_SCORER` for `crown_dragon_orca`; `model_decision_service.py` enters `_decide_rescue`, where candidates are scored and chosen through `rescue_scorer`.
2. Dragon components can alter `option.score`, but action generation and final choice are still routed through Rescue/Fuse structures rather than an independent planner.
3. Some components are disabled or weakly connected. `visible_graph_mpc` is called but disabled in sampled Dragon runs; `learned_ranker` is outside the Rescue/Dragon path.
4. Trace evidence is mixed. Some action trace components are real, but `run_dragon_orca_experiment_grid.py` also contains fallback counts and hard-coded schema/B0 fields that cannot satisfy runtime evidence gates.
5. `evolve_dragon_heuristics.py` writes recipe JSON without showing runtime ingestion; `build_dragon_regret_analyzer.py` derives regret from grid rows rather than real action traces.
6. `verify_dragon_orca_completion.py` is tied to the Dragon branch and cannot prove Pivot-Redline compliance.

## Required Fix

Create an independent `crown_pivot_redline_v1` runtime path that does not call `_decide_rescue`, `rescue_scorer.score_options`, or `rescue_scorer.choose` as the pivot main path. Verifier evidence must separate real runtime effect from tool-derived and synthetic fields.
