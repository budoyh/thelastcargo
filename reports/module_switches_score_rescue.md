# Module Switches Score Rescue

| module | status | reason |
|---|---|---|
| RescueScorer | ON | direct_net and profit/hour dominate action selection |
| SafeProfitGreedy query | ON | fixed current-position query with post-query refresh_world |
| repeated_wait_penalty | ON | lowers thresholds and raises k after wait lock |
| micro_reposition | ON for A2+ | only current visible pickup clusters; no fixed coordinates |
| preference_soft_penalty | ON for A3+ | unknown/low-confidence preference risk is capped soft cost |
| visible_twohop_lite | ON for A4+ | current observed cargo only, capped value |
| time_shadow_lite | ON for A5+ | capped soft time cost; never hard-kills positive cargo |
| Qwen preference compiler | ON for A6+/best_rescue | DSL only; no actions from LLM |
| LLM judge | OFF | compiler gives rules; judge remains non-authoritative |
| Destination Shadow Query | OFF | compliance risk; no actionable destination-shadow cargo |
| Learned Ranker | OFF in rescue | hand score remains primary; no unstable learned correction |
| CROWN-Y Max modules | OFF | out of scope for score rescue |
