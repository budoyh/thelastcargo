# CROWN-GOLD Contract-MPC Project Memory

## Current Objective

- Build `crown-gold-contract-mpc` from the existing repository, not from scratch.
- Default runtime/package variant must be `crown_gold_contract_mpc`; do not default to `best_rescue`, `preference_firewall_profit`, PCE, Delta-MPC, or Exact.
- The target is official-net uplift through restored rescue legality/profit core plus real Qwen Preference Contract, Observed Vocabulary Linker, top-candidate Auditor, Preference Firewall, and Online Opportunity Graph MPC.

## Baseline Facts To Preserve

- Historical 20260529 rescue reference: official_net 5067.69, preference_penalty 38140.0, actions 89 take / 163 wait / 0 reposition.
- Current branch restored `best_rescue` to the historical reference on 20260529: official_net 5067.69, preference_penalty 38140.0, actions 89 take / 163 wait / 0 reposition.
- Previous PTT evidence failed the real-Qwen gate: qwen_compile_calls=0 and ptt_compile_calls=0 in full eval.
- Previous Exact evidence had real Qwen compile/link counts but controller_scored_candidate_count=0 and qwen_auditor_calls=0.
- Tests passing, legal actions, Qwen smoke, reports, synthetic pass, and macro counts are not success without official score, gross, penalty, Qwen, controller, compliance, reviewer, and package gates.

## Current Known Risks

- Gold modules can activate real controller scoring without reducing official preference penalty enough. Final 20260529 Gold net was only 6373.17 with penalty 39620.0.
- Repair/reposition loops are a known risk. Gold repair and visible-graph MPC are default OFF unless ablation proves positive official-net or named regret reduction without gross collapse.
- Qwen contract/link/audit calls are expensive in local full evals, but must remain real for final evidence. Gold total linker/auditor default caps were raised to 4096 after 0509 exposed old cap exhaustion.
- Raw local run outputs under ignored `runs/` are evidence artifacts and may contain benchmark-emitted raw ids/literals; do not treat them as package/report content.
- Cloud host `yinhhzzu` was reachable on 2026-06-02, but load was about 421 with multiple busy GPUs, so local execution continued to avoid disrupting other users.

## Non-Negotiable Boundaries

- Runtime may use only `SimulationApiPort`; no raw datasets, no server/bench/scoring imports, no future cargo, no offline reports.
- `take_order` must come from current post-query `current_actionable` cargo.
- Every query must be followed by world refresh and post-query filtering.
- `no_query` cannot take remembered cargo.
- Destination Shadow Query is OFF.
- Reposition coordinates must keep full precision.
- Qwen may compile contracts, link current observed vocabulary, or audit gated candidates; it must not choose final actions.
- Protected literals remain redacted in committed files as `PROTECTED_LITERAL_REDACTED`, `runtime_entity_hash`, or `runtime_value_hash`.

## Implementation Direction

- Keep the restored best-rescue legality core: query-refresh, current-actionable filtering, safety certificates, and positive freight scoring.
- Compile non-empty preferences into Gold Preference Contract JSON with polarity, observable, scope, metric, counting, slots, severity, repair_actions, confidence, uncertainty, and evidence_hash.
- Run Observed Vocabulary Linker after every query when preferences and visible cargo exist.
- Run Preference Firewall before profit ranking and trace marginal penalty, repair value, lost repair-window cost, unknown-soft risk, and Qwen audit adjustment.
- Run Qwen Candidate Auditor only for high-conflict top candidates; auditor output is relation/effect/risk/repair/confidence/evidence only.
- Use immutable rescue/safe-profit scoring as the profit backbone.
- Keep Online Opportunity Graph MPC default OFF unless ablation proves score uplift or regret reduction without gross collapse.

## Stop State Rules

- Allowed Gold stop states: `CROWN_GOLD_RECOMMENDED_SUBMISSION`, `CROWN_GOLD_EXPERIMENTAL_SUBMISSION`, `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`, `EXTERNAL_BLOCKER`.
- If Qwen API, true subagents, or official local evaluation are unavailable, stop as `EXTERNAL_BLOCKER`.
- If score gates are not reached after Gold evidence is produced, stop as `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`.
- If gates fail, do not create a submission-shaped zip and make `reports/gold_final_report.md` start with `DO NOT SUBMIT: gold gates not reached.`

## Final Gold Evidence Snapshot

- Stop state: `DO_NOT_SUBMIT_WITH_GOLD_EVIDENCE`.
- 20260529 B9 final selected: official_net 6373.17, gross_minus_cost 45993.17, preference_penalty 39620.0.
- 20260529 real Qwen compile/link/audit: 5 / 245 / 245.
- 20260529 controller metrics: controller_scored 11461, candidate_rule_eval 52909, score_changed 11461, changed_decision 240.
- 20260509 regression check: official_net 167347.15 and preference_penalty 0.0, but monthly income calculation aborted for 2 drivers; not clean no-regression evidence.
- No Gold package exists because score gates failed.
