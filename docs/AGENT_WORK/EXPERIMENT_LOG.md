# CROWN-TRIDENT / GOLD-2 Experiment Log

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
