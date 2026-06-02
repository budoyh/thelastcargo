DO NOT SUBMIT: below experimental gate.

# CROWN-TRIDENT / GOLD-2 Final Report

- stop_state: `DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE`
- branch: `crown-trident-gold2`
- report_generated_from_git_head: `42ec8cb`
- runtime default variant: `crown_trident_gold2`
- best evidence row variant: `crown_gold_contract_mpc`
- final_recommendation: `below experimental gate`

## Score Table B0-B11
| stage | variant_name | status | official_net | gross_minus_cost | preference_penalty | official_net_delta_vs_b0 | keep_or_kill |
|---|---|---|---|---|---|---|---|
| B0 | B0_historical_rescue_restored | EXISTING | 5067.69 | 43207.69 | 38140.0 | 0.0 | keep_b0_reference |
| B1 | B1_contract_compile_logging_only | MISSING_RUN |  |  |  |  | kill_missing_run |
| B2 | B2_contract_monitor_no_score | MISSING_RUN |  |  |  |  | kill_missing_run |
| B3 | B3_controller_soft_scoring | MISSING_RUN |  |  |  |  | kill_missing_run |
| B4 | B4_verified_hard_firewall_only | MISSING_RUN |  |  |  |  | kill_missing_run |
| B5 | B5_qwen_auditor_nonzero_adjustment | MISSING_RUN |  |  |  |  | kill_missing_run |
| B6 | B6_observed_vocab_linker_only | MISSING_RUN |  |  |  |  | kill_missing_run |
| B7 | B7_opportunity_graph_only | MISSING_RUN |  |  |  |  | kill_missing_run |
| B8 | B8_opportunity_graph_plus_auditor | MISSING_RUN |  |  |  |  | kill_missing_run |
| B9 | B9_wait_repair_full | MISSING_RUN |  |  |  |  | kill_missing_run |
| B9 | B9_wait_repair_half | MISSING_RUN |  |  |  |  | kill_missing_run |
| B9 | B9_wait_repair_off | EXISTING | 6373.17 | 45993.17 | 39620.0 | 1305.48 | keep_score_positive_vs_b0 |
| B10 | B10_parameter_search_best | MISSING_RUN |  |  |  |  | kill_missing_run |
| B11 | B11_final_selected | MISSING_RUN |  |  |  |  | kill_missing_run |
| S0 | B0_historical_rescue_restored | EXISTING | 5067.69 | 43207.69 | 38140.0 | 0.0 | keep_b0_reference |
| S0 | current_gold_if_available | EXISTING | 6373.17 | 45993.17 | 39620.0 | 1305.48 | keep_score_positive_vs_b0 |
| S0 | money_greedy_no_pref | EXISTING | -122937.49 | 77602.52 | 200540.0 | -128005.18 | kill_below_b0 |
| S0 | safe_profit_greedy | EXISTING | -113176.86 | 79603.13 | 192780.0 | -118244.55 | kill_below_b0 |
| S0 | strict_pref | EXISTING | 2240.98 | 38900.98 | 36660.0 | -2826.71 | kill_below_b0 |
| S10 | trial_0000 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0001 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0002 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0003 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0004 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0005 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0006 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0007 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0008 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0009 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0010 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0011 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0012 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0013 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0014 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0015 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0016 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0017 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0018 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0019 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0020 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0021 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0022 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0023 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0024 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0025 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0026 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0027 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0028 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0029 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0030 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0031 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0032 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0033 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0034 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0035 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0036 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0037 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0038 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0039 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0040 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0041 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0042 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0043 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0044 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0045 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0046 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0047 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0048 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0049 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0050 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0051 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0052 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0053 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0054 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0055 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0056 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0057 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0058 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0059 | PLANNED |  |  |  |  | planned_not_evaluated |
| S10 | trial_0060 | PLANNED |  |  |  |  | planned_not_evaluated |

## Top Remaining Penalty Rules
| driver_hash | rule_id | official_penalty_final | official_penalty_delta_vs_b0 | keep_or_kill |
|---|---|---|---|---|
| e7a52d984e7e | 674070057b2f | 14400.0 | 8000.0 | kill_or_retune_penalty_worse_vs_b0 |
| e7a52d984e7e | cee0faecaf6b | 10000.0 | 0.0 | unresolved_existing_penalty_not_fixed |
| 3e0e35341231 | 048e665ca9b7 | 5000.0 | 0.0 | unresolved_existing_penalty_not_fixed |
| 3e0e35341231 | 69c10ceb2dd4 | 5000.0 | 0.0 | unresolved_existing_penalty_not_fixed |
| e7a52d984e7e | 4d7e4e30a7ba | 3000.0 | 3000.0 | kill_or_retune_penalty_worse_vs_b0 |
| e7a52d984e7e | 6235345edaf5 | 2100.0 | 0.0 | unresolved_existing_penalty_not_fixed |
| 3e0e35341231 | e90080a0e2da | 120.0 | -120.0 | keep_candidate_penalty_improved_vs_b0 |
| 3e0e35341231 | 355f8f7bf174 | 0.0 | -6000.0 | keep_candidate_penalty_improved_vs_b0 |
| 3e0e35341231 | 36e6d8533839 | 0.0 | 0.0 | neutral_no_final_penalty |
| 3e0e35341231 | 5898067122eb | 0.0 | -3400.0 | keep_candidate_penalty_improved_vs_b0 |
| 3e0e35341231 | 67a434f963f5 | 0.0 | 0.0 | neutral_no_final_penalty |
| e7a52d984e7e | 887d908c573d | 0.0 | 0.0 | neutral_no_final_penalty |

## Changed Decision Wins
| decision_index | b0_action_type | new_action_type | estimated_gross_delta | estimated_pref_delta | label_validity | reason_code |
|---|---|---|---|---|---|---|
| 111 | wait | take_order | 889.38 | 591.14 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 24 | wait | take_order | 819.65 | 591.14 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 37 | wait | reposition | 0.0 | -1.0 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_reposition |
| 41 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 58 | wait | reposition | 0.0 | -1.0 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_reposition |
| 59 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed |
| 72 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 119 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 17 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 21 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 25 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 33 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 45 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 112 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 117 | wait | wait | 0.0 | -1.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 108 | wait | take_order | 590.52 | 590.14 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 5 | wait | wait | 0.0 | 0.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 9 | wait | wait | 0.0 | 0.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 12 | wait | wait | 0.0 | 0.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 16 | wait | wait | 0.0 | 0.0 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |

## Changed Decision Losses
| decision_index | b0_action_type | new_action_type | estimated_gross_delta | estimated_pref_delta | label_validity | reason_code |
|---|---|---|---|---|---|---|
| 6 | take_order | take_order | -423.18 | 14898.74 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 95 | take_order | take_order | 390.94 | 14898.74 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 74 | wait | take_order | 421.76 | 14913.74 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 70 | wait | take_order | 571.67 | 14913.74 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 91 | wait | take_order | 637.17 | 14913.74 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 10 | take_order | take_order | -281.98 | 13937.14 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 78 | wait | take_order | 822.32 | 14913.74 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 2 | take_order | take_order | -87.68 | 13939.24 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 114 | take_order | take_order | 53.77 | 13941.14 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 14 | take_order | take_order | 111.35 | 13937.14 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 31 | take_order | take_order | 161.0 | 13941.14 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 57 | wait | take_order | 231.96 | 13956.14 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 99 | wait | take_order | 306.6 | 13956.14 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 40 | wait | take_order | 354.06 | 13943.33 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 19 | wait | take_order | 371.04 | 13956.61 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 120 | take_order | take_order | 360.72 | 13941.14 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 107 | wait | take_order | 385.46 | 13957.14 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 66 | wait | take_order | 384.59 | 13956.14 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |
| 27 | take_order | take_order | 388.79 | 13941.14 | diagnostic_not_official_counterfactual | same_action_type_signature_changed_with_controller_score |
| 62 | wait | take_order | 413.05 | 13956.14 | diagnostic_not_official_counterfactual | action_type_changed_wait_to_take_order |

## Qwen Audit Examples
| call_id | decision_index | output_relation | output_effect | applied_score_adjustment | json_valid | final_action_used |
|---|---|---|---|---|---|---|
| de660e8c5bfb | 1 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| 4f0f2602ffe0 | 2 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| b3c6e3f9edb1 | 3 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| 71835458482a | 4 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| a1d755d0956b | 5 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| 19a287cf8714 | 6 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| dc20113abf1a | 7 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| 09c5cba5f9ba | 8 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| 121fadc719c9 | 9 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| 405b266f4f70 | 10 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| 8e9147f61f11 | 11 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| 8a97a88c91a4 | 12 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| 1c0e9dac2961 | 13 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| db1e3e303161 | 14 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| cf8a29d79b63 | 15 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| ae1fa8745842 | 16 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| b9cf1f984662 | 17 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| ed5ef93b9ac2 | 18 | not_persisted_in_legacy_trace | unknown | 0.0 | False | wait |
| 65d80e2c0a8b | 19 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |
| 7f93b38e262c | 20 | not_persisted_in_legacy_trace | unknown | 0.0 | False | take_order |

## Missed High-Gross Safe Candidates
- Not yet backed by official suffix replay. Current evidence is diagnostic from changed-decision estimates and wait forensics only; these rows must not tune controller weights as official labels.

## Opportunity Graph Uplift
| variant_name | official_net | gross_minus_cost | preference_penalty | visible_graph_used_count | terminal_value_used_count | keep_or_kill |
|---|---|---|---|---|---|---|
| B7_opportunity_graph_only |  |  |  |  |  | kill_missing_run |
| B8_opportunity_graph_plus_auditor |  |  |  |  |  | kill_missing_run |

## Parameter Search Best
| variant_name | status | objective_score | official_net | gross_minus_cost | preference_penalty | keep_or_kill | env_json |
|---|---|---|---|---|---|---|---|
| trial_0009_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"100","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"0","CROWN_GOLD_ENABLE |
| trial_0019_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"100","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE |
| trial_0029_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"0","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_L |
| trial_0039_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"35","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_ |
| trial_0049_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"100","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"0","CROWN_GOLD_ENABLE |
| trial_0059_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"10","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"0","CROWN_GOLD_ENABLE_ |
| trial_0069_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"100","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE |
| trial_0079_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"-20","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"0","CROWN_GOLD_ENABLE |
| trial_0089_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"1","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_L |
| trial_0099_0509_sanity | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"-20","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE |
| trial_0000 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"100","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE |
| trial_0001 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"35","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_ |
| trial_0002 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"60","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_ |
| trial_0003 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"35","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_ |
| trial_0004 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"10","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_ |
| trial_0005 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"10","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_ |
| trial_0006 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"100","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE |
| trial_0007 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"35","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"0","CROWN_GOLD_ENABLE_ |
| trial_0008 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"35","CROWN_GOLD_ENABLE_AUDITOR":"1","CROWN_GOLD_ENABLE_FIREWALL":"1","CROWN_GOLD_ENABLE_ |
| trial_0009 | PLANNED |  |  |  |  | planned_not_evaluated | {"CROWN_GOLD_DIRECT_NET_FLOOR":"100","CROWN_GOLD_ENABLE_AUDITOR":"0","CROWN_GOLD_ENABLE_FIREWALL":"0","CROWN_GOLD_ENABLE |

## Keep/Kill Table
| keep_or_kill | count |
|---|---|
| planned_not_evaluated | 110 |
| keep_b0_reference | 2 |
| kill_missing_run | 12 |
| keep_score_positive_vs_b0 | 2 |
| kill_below_b0 | 3 |

## First Broken Link
| link | status | evidence |
|---|---|---|
| Qwen contract valid | True | 546 |
| observed vocab linked | True | 786 |
| candidate scored by controller | True | 11461 |
| score changed | True | 11461 |
| decision changed | True | 240 |
| official penalty reduced | False | 1480.0 |
| gross preserved | True | 2785.48 |
| official net improved | True | 1305.48 |
| Qwen auditor numeric effect | False | nonzero adjustment count |

## Command Evidence
- Branch creation and push completed before implementation.
- `python tools/run_trident_baselines.py --simulation-days 31` generated Stage 0 rows.
- `python tools/build_trident_penalty_ledger.py --simulation-days 31` generated rule ledger.
- `python tools/build_trident_decision_deltas.py --simulation-days 31` generated diagnostic decision deltas.
- `python tools/run_trident_ablation_matrix.py --simulation-days 31` generated B0-B11 matrix rows from existing/planned runs unless executed separately.
- `python tools/run_trident_param_search.py --trials 100` records planned or executed generic trials depending on `--execute`.
- `python tools/qwen_preference_smoke_test.py` verified the Trident V2 injected smoke path only; this is not full live-Qwen evaluation evidence.
- `python -m pytest tests -q`, `python -m compileall demo tools tests`, and `python tools/audit_guard.py --fail-on-p0 --require-final-evidence` passed before handoff.
- `python tools/build_trident_reports.py` generated this report and Qwen effect CSV.

## Package Audit
- No submission-shaped package is generated when below experimental gate.

## Residual Risks
- Per-decision `official_replay_delta_*` remains unavailable without suffix replay; current decision deltas are diagnostic.
- Full B1-B8/B10 trials are not proof unless rows show `status=OK` or `EXISTING` with official metrics.
- Existing Gold Qwen auditor evidence had calls but zero persisted adjustment; Trident runtime now records nonzero soft-risk adjustment, but it still requires full live-Qwen ablation evidence.
