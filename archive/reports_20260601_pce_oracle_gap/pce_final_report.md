DO NOT SUBMIT: PCE target not reached.

# CROWN-PCE Final Report

- stop_state: DO_NOT_SUBMIT_WITH_ORACLE_EVIDENCE
- branch: crown-pce-oracle-gap
- commit: final branch commit created after this report is staged; see git HEAD
- final_artifacts: reports/pce_final_report.md, reports/pce_experiments.csv, reports/oracle_gap.csv, reports/predicate_eval.csv, reports/action_forensics.csv
- redaction: raw ids, raw coordinates, raw preference literals, and protected example terms are redacted or hashed.

## Score Accounting

Stage 0 result: official_net is already gross_minus_cost minus preference_penalty. No proxy net-minus-penalty metric is used.

- 20260529 pce_final: 34114.98 - 37240.00 = -3125.02.
- 20260529 full_info_oracle: 52081.18 - 17080.00 = 35001.19.
- 20260529 no_pref_money_oracle: 67887.63 - 171520.00 = -103632.37.
- Score accountant output was written outside final reports in runs/pce_score_accountant; proxy_double_count_forbidden is true.

## Oracle Evidence

- full_information exact offline oracle: official_net 35001.19, gross_minus_cost 52081.18, preference_penalty 17080.00.
- online_visibility oracle k=100/300/600: official_net 29767.84 / 29843.65 / 30960.95.
- no_preference money oracle: gross_minus_cost 67887.63 but preference_penalty 171520.00, official_net -103632.37.
- money trajectory deletion/repair experiment: official_net 35849.85, gross_minus_cost 53169.85, preference_penalty 17320.00.
- conclusion: the current offline oracle upper bound appears below the strong target, and runtime remains far below the best oracle. The dominant gap is exact target/field/time preference execution, not legality or score accounting.

## Runtime Result

20260529, current checker:

- official_net: -3125.02
- gross_minus_cost: 34114.98
- preference_penalty: 37240.00
- simulation_failures / income_aborts / illegal_actions / rejected_takes: 0 / 0 / 0 / 0
- take_order / wait / reposition: 117 / 199 / 0
- Qwen compile calls: 5

20260509 reference data, matching checker:

- official_net: 92486.65
- gross_minus_cost: 193386.65
- preference_penalty: 100900.00
- simulation_failures / income_aborts / illegal_actions / rejected_takes: 0 / 0 / 0 / 0
- take_order / wait / reposition: 430 / 849 / 0
- Qwen compile calls: 12
- status: comparable generalization sanity, but not clean; target-home and time-bound repair predicates remain unresolved.

## Predicate And Repair

- Predicate compiler v2 now emits executable predicate specs with predicate_type, fields, operator, values, scope, deadline/counter/target fields, repair kinds, penalty, confidence, and evidence hash.
- Observed vocabulary linker uses only the current post-query visible vocabulary; cache key is preference_hash plus vocab_hash; report values are hashed/redacted.
- Candidate verifier scores top candidates with predicate_match, marginal_effect, predicted_marginal_penalty, predicted_repair_value, and confidence.
- Repair planner emits no-query rest, full off-day wait-to-boundary, and runtime-target repair candidates with avoided_penalty, repair_value, lost_profit, feasibility, confidence, and action certificates.
- Reposition stayed at zero. This is not proven optimal: unresolved runtime target predicates mean preference reposition value is still under-executed.

Predicate metrics from predicate_eval.csv:

- top20 candidate violation recall: 1.00
- high-penalty violation recall: 1.00
- repair task recall: 1.00
- unknown rate: 0.0393
- false hard-block rate: 0.00
- synthetic paraphrase gates: 7/7 passed

## Compliance And Qwen

- audit_guard: PASS, 0 P0 findings after redaction guard and report scan.
- Runtime/offline separation: offline oracle and exact-label tools live under tools; runtime agent code does not read offline oracle artifacts.
- P0 runtime checks: no raw debug data reads, no server or bench imports in demo/agent, no Destination Shadow Query, query followed by refresh/filter, take_order only from current post-query current_actionable, no remembered take after no_query.
- Qwen3.5-Flash remained ON for non-empty preferences when API was available. Smoke test returned compile_calls=1 and no dummy-key success; runtime Qwen calls were used only for compiler/linker roles, not final action selection.

## Reviews

- Sagan explorer review: confirmed local eval/scorer paths and score accountant workflow; no substitute scorer should be used for final status.
- Confucius explorer review: confirmed runtime boundary files and current-actionable safety paths; flagged raw-id forensics, which was patched.
- Simulated final reviewers: prompt adherence, compliance/future-info, oracle/score accounting, predicate compiler, runtime planner, and code/test passes all converge on the same result: legal and report-complete, but not a submit candidate.

## Recommendation

Do not submit this branch. It does not beat the rescue reference and misses all PCE score gates.

Named regret reduced: broad preference-penalty explosion was reduced versus the high-gross no-preference trajectory, but the policy paid for it by collapsing gross_minus_cost and still failed exact target/time predicates. The remaining dominant regret is executable repair of target-home, visit-count, and field/region constraints under legal online visibility.

Shortest next path:

1. Build an exact completed-replacement labeler for target-home, visit-count, and field/region predicates.
2. Distill those labels into deterministic runtime predicates that do not require raw offline data.
3. Make preference reposition use only runtime evidence or current visible clusters, with avoided_penalty plus repair_value overriding ordinary market payback when justified.
4. Re-run the 0529 oracle frontier and only then attempt conservative weight search.
