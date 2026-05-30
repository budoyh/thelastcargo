# Module Switches

| module | status | reason | rollback / enable path |
|---|---|---|---|
| Time Shadow v1 | ON | P1 core; candidate-aware with leave-one-out opportunity cost, clip, shrink and fallback | `ENABLE_TIME_SHADOW = False` or `CROWN_Y_VARIANT=no_time_shadow` |
| Preference Monitor | ON | DSL/evidence/certificate; low confidence prices risk but does not hard block | keep ON unless compliance audit requires disabling |
| Visible two-hop | ON | P1 core; uses current observed cargo only | `ENABLE_VISIBLE_TWO_HOP = False` or `CROWN_Y_VARIANT=no_rollout` |
| Resource Endgame | ON | pressure-based and not date-only | `ENABLE_RESOURCE_ENDGAME = False` |
| Scout-then-deepen | OFF | ablation showed query-too-big and worse net/penalty | `CROWN_Y_ENABLE_SCOUT_THEN_DEEPEN=1` for experiments |
| Reposition | OFF | no positive payback evidence; payback gate retained behind experimental switch | `CROWN_Y_ENABLE_REPOSITION=1` for experiments |
| Learned Ranker | OFF | P2 not proven; default hand score dominates | `ENABLE_LEARNED_RANKER = False` |
| LLM Judge | OFF | budget is zero; parser restricted to yes/no/unknown | `ENABLE_LLM_JUDGE = False` |
| Destination Shadow Query | OFF | no official compliance confirmation | keep `OFFICIAL_ALLOW_ARBITRARY_COORD_QUERY = False` |
| Three-hop / option rollout | OFF | P3 risk | keep switches false |
