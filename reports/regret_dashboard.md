# Regret Dashboard

All regret counts are deterministic post-run proxies unless noted. `reposition_not_recovered` uses a selected-reposition payback tracker with a 12 hour recovery window; the final build emits no reposition actions.

## Final Default

- results_dir: `C:\budostudy\only_for_codex\thelatstcargo\runs\latest`
- status: 31 day run, 0 simulation failures, 0 income calculation aborts
- actions: take `13`, wait `1806`, reposition `0`, rejected take `0`
- query_minutes: `8499`
- illegal_actions: `0`

| regret | count | interpretation |
|---|---:|---|
| query_too_big | 0 | fixed scout avoids large-query overuse |
| query_too_small | 25 | small-query scarcity proxy |
| long_order_trap | 2 | take orders with action time over 720 minutes |
| wait_regret | 1797 | repeated waits; major residual scoring risk |
| reposition_not_recovered | 0 | true selected-reposition payback tracker; no reposition emitted |
| preference_late_panic | 0 | high debt near endgame proxy |

## Ablations

| run | net | penalty | steps | take | wait | reposition | rejected_take | query_minutes | key regret |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| default | -18953.97 | 24700.0 | 1819 | 13 | 1806 | 0 | 0 | 8499 | wait_regret 1797 |
| baseline | -94825.77 | 172760.0 | 300 | 154 | 146 | 0 | 4 | 1060 | long_order_trap 31 |
| no_time_shadow | -101012.95 | 177520.0 | 337 | 151 | 186 | 0 | 2 | 1169 | long_order_trap 31 |
| no_rollout | -19637.96 | 26620.0 | 1805 | 14 | 1791 | 0 | 0 | 8428 | penalty +1920 vs default |
| scout_enabled | -19239.4 | 26300.0 | 1652 | 15 | 1637 | 0 | 0 | 15435 | query_too_big 647 |
| reposition_enabled | -18953.97 | 24700.0 | 1819 | 13 | 1806 | 0 | 0 | 8499 | identical to default; gate released nothing |
| time_price_0_9 | -18953.97 | 24700.0 | 1819 | 13 | 1806 | 0 | 0 | 8499 | stable under -10% time price |
| time_price_1_1 | -18953.97 | 24700.0 | 1819 | 13 | 1806 | 0 | 0 | 8499 | stable under +10% time price |

## 20260509 Reference

| run | net | penalty | steps | take | wait | reposition | rejected_take | query_minutes | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| old_0509 with matching 0509 income script | -7038.17 | 84750.9 | 7893 | 148 | 7745 | 0 | 0 | 67152 | 10 drivers, 0 aborts |

## Module Decisions

- Time Shadow stays ON: removing it collapses net from `-18953.97` to `-101012.95` and increases preference penalty from `24700.0` to `177520.0`.
- Visible two-hop stays ON: default beats no-rollout on net and preference penalty, while using only current observed cargo.
- Scout-then-deepen is OFF by default: enabling it raises query minutes from `8499` to `15435`, produces `647` query-too-big events, and worsens net and penalty.
- Reposition is OFF by default: even when experimentally enabled, the payback gate emits no reposition; there is no positive payback evidence to keep it active.
- Learned Ranker and LLM Judge remain OFF: no ablation supports enabling P2/P3 risk.
