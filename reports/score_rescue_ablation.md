# Score Rescue Ablation

- results_root: `C:\budostudy\only_for_codex\thelatstcargo\runs\score_rescue_ablation`

| run | net | penalty | proxy | take | wait | repo | rejected | wait_ratio | q_min/take | positive_wait | qwen_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| a0 | -113176.86 | 192780.0 | -305956.86 | 167 | 17 | 0 | 0 | 0.0924 | 12.96 | 0 | 0 |
| a1 | -113176.86 | 192780.0 | -305956.86 | 167 | 17 | 0 | 0 | 0.0924 | 12.96 | 0 | 0 |
| a2 | -113176.86 | 192780.0 | -305956.86 | 167 | 17 | 0 | 0 | 0.0924 | 12.96 | 0 | 0 |
| a3 | -113702.22 | 194380.0 | -308082.22 | 168 | 17 | 0 | 0 | 0.0919 | 12.96 | 0 | 0 |
| a4 | -113702.22 | 194380.0 | -308082.22 | 168 | 17 | 0 | 0 | 0.0919 | 12.96 | 0 | 0 |
| a5 | -113881.81 | 194580.0 | -308461.81 | 166 | 17 | 0 | 0 | 0.0929 | 12.97 | 0 | 0 |
| a6 | 5067.69 | 38140.0 | -33072.31 | 89 | 163 | 0 | 0 | 0.6468 | 37.15 | 0 | 5 |
| a7 | 5067.69 | 38140.0 | -33072.31 | 89 | 163 | 0 | 0 | 0.6468 | 37.15 | 0 | 5 |

Conclusion: choose `best_rescue` / `a7` because it is the only tested rescue line that turns net income positive while preserving 0 illegal actions and Qwen preference compilation.
