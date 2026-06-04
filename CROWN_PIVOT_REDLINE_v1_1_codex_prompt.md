# CROWN-PIVOT-REDLINE v1.1 Codex Prompt

> 任务目标：在满帮 Agent 大赛仓库中停止旧 rescue 外壳叠插件路线，创建并验证一个真正独立的新决策器 `crown_pivot_redline_v1`。本轮必须真实落实用户提出的全部核心想法：高毛利主线、偏好债务、动作级风险、轻量价值模型、depth=2/3 beam/rollout、query 预算优化、卸货地价值、合法在线探针、月底保护、反事实回放、Regret-LNS、ReEvo/启发式进化、Qwen 多步偏好编译与多角色审计。任何模块如果没有真实代码、测试、runtime trace、31-day full-run 使用证据、消融分数证据，禁止声称已实现。

---

## v1.1 修订总则：防止再次伪实现和误提交

本 v1.1 在 v1 基础上只做硬约束修补，不改变主线。所有与本节冲突的旧文字均以本节和后续修订为准：

1. `best_rescue/B0` 只允许作为 baseline、no-op oracle、shadow comparison，不得成为 final runtime fallback 或默认提交策略。若最终策略实质上等于 B0，必须 `DO_NOT_SUBMIT`，不得打包成 submission/probe。
2. subagent 是 QA gate，不是实现者，也不能成为停工口。若真实 subagent 调用失败，先关闭旧 subagent/释放槽位后重试；仍不可用时，执行严格 named read-only reviewer passes。只有连文件/命令/run_dir/CSV 都无法审查时才允许 `EXTERNAL_BLOCKER_SUBAGENT_INFRA`。
3. `scorer_probe`、counterfactual、run trace、attribution 输出只能存在于 `tools/` 和 `runs/`，runtime 不得 import 或读取。runtime 只能携带抽象 `SemanticProfile` 和通用参数。
4. 历史高分锚点只有当前分支 exact/near reproduction 或存在 action trace 时，才可导出数值阈值；artifact-only 只能生成假设，不能进入 runtime 权重。
5. Clean Money 先恢复历史 high-gross 行为，再谈偏好/价值/beam/evolution。若 money backbone 没恢复，后续 120/200 行搜索只是在坏空间空跑。
6. Bulk search 必须冻结真实 Qwen contract/link artifacts；top candidates 再用 live-Qwen path 确认，避免 Qwen 随机性污染搜索。
7. ReEvo/BO/Beam/Value/Risk 必须有真实 runtime 链路、trace、训练/验证、ON/OFF full-run 消融。配置表、used_count、capped scalar、stage name 不算实现。
8. 低分 review/probe 包会误导 B 榜提交。低于 experimental gate 不生成 submission-shaped zip；低于 weak review gate 不生成任何 zip，只生成报告。

---

## 0. 当前接手事实与本轮根因判断

你接手的是 `budoyh/thelastcargo` 仓库。上一轮 `crown-dragon-orca-v1-1` 已失败：

- 最终 stop_state 是 `DO_NOT_SUBMIT_WITH_INCOMPLETE_SEARCH`。
- 20260529 full 31-day executed rows 为 60。
- 最优仍是 B0 `best_rescue`：`official_net=5067.69`, `gross_minus_cost=43207.69`, `preference_penalty=38140.0`, `take/wait/reposition=89/163/0`。
- 最优非 B0 行 `A3_E5_like_hunter_reference` 只有 `official_net=1882.36`, `gross=43382.35`, `penalty=41500.0`。
- `value_model_used_count`, `beam_used_count`, `adaptive_query_used_count`, `regret_lns_used_count` 有数，但没有任何正收益。
- 旧 Dragon 的模块多数是 rescue_scorer 里的 overlay/capped bonus/usage counter，而不是真正独立的 DP/value/beam/evolution planner。

本轮不允许继续在 `rescue_scorer` 上小修小补。可以大幅重构，必要时新建干净 package，旧模块只允许作为对照或 fallback。

核心判断：之前失败不是用户想法失败，而是想法没有真正落实。你必须把以下想法做成完整工程闭环：

```text
自然语言偏好 -> 多步 Qwen ensemble contract -> scorer probe 校准 -> Preference Debt Accountant
当前状态/可见货源 -> clean candidate buckets -> money backbone
合法观测市场/轨迹数据 -> RiskModel(s,a) + ValueModel(s')
候选动作 -> depth=2/3 beam rollout + query 成本 + 卸货地价值 + 月底保护
full-run 轨迹 -> 反事实回放 -> Regret-LNS repair/refill -> ReEvo 公式进化
最终策略 -> official 31-day 分数提升 -> package gate
```

---

## 1. 最高优先级规则：禁止空实现、浅实现、伪实现

### 1.1 REAL_IMPLEMENTATION_GATE

任何模块只有同时满足以下 7 条，才允许在 final report 中写作 `ACTIVE_AND_VALIDATED`：

1. 有真实 runtime 代码，不是 stub、placeholder、TODO、pass、常量返回、只写文件名、只写 used_count。
2. 有 deterministic unit/integration test，且 test 断言行为而不是只 import。
3. 接入 `demo/agent` 的实际决策链，能够改变候选生成、候选打分、query/wait/reposition/take 选择中的至少一项。
4. 在 trace 中有真实逐决策记录，trace 字段来自实际 runtime，不得由 trial stage name、配置名、for-loop index 或 report builder 合成。
5. 至少一个 20260529 full 31-day official-style run 中该模块实际参与评分/候选/动作选择。
6. 有该模块 ON/OFF 或 weight 0/nonzero 的 ablation，报告 official_net/gross/penalty 差异。
7. 有 read-only subagent reviewer 检查源代码、trace、CSV、run_dir、命令、exit_code，并给出 PASS/FAIL。

缺任何一条，模块只能标为：

```text
DIAGNOSTIC_ONLY
IMPLEMENTED_BUT_NOT_ACTIVE
ACTIVE_BUT_NO_POSITIVE_EVIDENCE
FAILED_INTEGRATION
```

禁止写“初步实现”“浅层实现”“scaffold”“prototype”当作完成。用户明确要求完整形态落地。

### 1.2 禁止用假指标替代真实算法

以下证据无效：

- `used_count > 0` 但无法追溯到真实决策 trace。
- report 中有表，但表由总分均摊或静态权重合成。
- value model 没训练，只是手写 capped scalar。
- beam 没展开树，只是 two-hop/capped bonus。
- ReEvo 只生成 JSON recipe，不基于 full-run 反馈选择/反思/变异。
- trial_017-like / B9c-like / money-like 只是新配置名，未复现历史 row。
- no-op row 实际 variant 是 `best_rescue`，不是新 planner with weights=0。
- subagent 泛泛 PASS，未引用文件/命令/CSV行/分数。

### 1.3 每阶段必须 subagent 审核

每完成一个 Stage，必须调用一个或多个 read-only subagent 质检。subagent 不能改代码，只能检查证据。每个 reviewer 必须输出：

```text
reviewer_name
scope
changed_files_seen
source_files_checked
commands_run
csv_rows_checked
run_dirs_checked
metrics_before_after
pass_fail_against_prompt
blocking_findings
required_fix
```

如果 reviewer FAIL，主 Codex 必须修复并 rerun 对应 Stage 和 reviewer。不得带着 reviewer FAIL 进入最终成功状态。

Subagent 使用规则：

1. Stage -1 必须做 subagent/reviewer infrastructure preflight。
2. 如果真实 subagent 工具可用，必须使用真实 read-only subagent；subagent 只审查，不写代码。
3. 如果调用 subagent 失败，必须先检查是否达到并发上限；若有旧 subagent 未关闭，先关闭/释放旧 subagent，再重试。
4. 如果真实 subagent 仍不可用，不得立刻停工；必须运行 named independent read-only reviewer passes，每个 reviewer 必须重新检查 source files、git diff、commands、run_dir、CSV rows、metrics before/after，并输出 PASS/FAIL。
5. 泛泛自我评价无效。若连 named reviewer pass 都无法检查文件/命令/run_dir/CSV，才允许 `EXTERNAL_BLOCKER_SUBAGENT_INFRA`。
6. `EXTERNAL_BLOCKER_SUBAGENT_INFRA` 不能在写了大量代码/报告后才发现；preflight 必须在 Stage 0 前完成。

---

## 2. 分支、目录和报告约束

### 2.1 分支

新建并推送分支：

```bash
git switch -c crown-pivot-redline-v1
```

如果分支已存在，切换并确认不是脏状态。不得直接污染 `crown-dragon-orca-v1-1`。

### 2.2 新 Agent 目录

必须新建独立 planner package：

```text
demo/agent/pivot_redline/
  __init__.py
  planner.py
  b0_shadow.py
  world_adapter.py
  candidate_bucket.py
  money_backbone.py
  qwen_contract_ensemble.py
  preference_state.py
  scorer_semantics_profile.py
  risk_labeler.py
  risk_model.py
  value_model.py
  beam_rollout.py
  query_optimizer.py
  macro_commitment.py
  month_end_guard.py
  online_probe.py
  trace_schema.py
  scoring_formula.py
  safety_gate.py
```

允许重构 `model_decision_service.py`，但必须满足：

- `variant == crown_pivot_redline_v1` 时直接调用 `PivotRedlinePlanner.decide()`。
- `crown_pivot_redline_v1` 不得调用 `_decide_rescue()`。
- `crown_pivot_redline_v1` 不得调用 `rescue_scorer.score()`、`rescue_scorer.choose()` 作为主排序。
- `best_rescue/B0` 只作为 frozen baseline、no-op oracle、pure shadow comparison，不作为新 planner 的内部 overlay，也不得作为 final runtime fallback/default variant。
- 可以复制/复用合法性、安全证书、距离、时间工具，但不能复用旧 rescue 的 hard wall、rest loop、wait threshold、query lock 作为主策略。

### 2.3 报告数量限制

最终 `reports/` 只保留本轮 5 个正式文件：

```text
reports/pivot_redline_final_report.md
reports/pivot_redline_experiment_grid.csv
reports/pivot_redline_forensics.csv
reports/pivot_redline_model_and_trace_audit.csv
reports/pivot_redline_package_audit.md
```

其它原始 trace、模型、reviewer transcript、debug 表放在：

```text
runs/pivot_redline/
runs/pivot_redline/reviewers/
runs/pivot_redline/private/
runs/pivot_redline/models/
runs/pivot_redline/traces/
archive/
```

不要把 raw preference、raw Qwen IO、cargo_id、driver_id、公开地点/货类字面量写入正式报告或 runtime。

---

## 3. 合规边界

### 3.1 Runtime 禁止

`demo/agent` runtime 禁止：

- 读 raw data、reports、runs、archive、oracle artifacts、scorer outputs、server/bench internals、income internals。
- import `server.*`、`bench.*`、calc income、official scorer。
- 使用 cargo_id、driver_id、preference_hash、rule_hash 做策略特化。
- 使用固定城市、固定坐标热点、固定路线、公开偏好原文字面词、示例领域词。
- 使用离线完整货源热力图、未来货源可用性。
- 无 query 接 remembered cargo。
- Qwen 输出最终动作或 cargo_id。

### 3.2 Runtime 允许

允许：

- 通过注入的 `SimulationApiPort` 获取当前状态、偏好、当前 post-query actionable cargo。
- 使用当前 query 的 visible cargo vocabulary 做 observed-vocab linking。
- 使用同一司机同一 simulation 中合法 query 得到的聚合市场摘要。
- 使用离线训练出的通用权重/模型参数/阈值/抽象 primitive，不含具体 ID/地点/路线/未来货源。
- 使用 Qwen3.5-Flash 做多步偏好编译、visible vocab linker、top-conflict risk audit。

---

## 4. Stop states

只允许以下 stop states：

```text
PIVOT_RECOMMENDED_SUBMISSION
PIVOT_EXPERIMENTAL_SUBMISSION
PIVOT_REVIEW_ONLY_NOT_FOR_SUBMISSION
DO_NOT_SUBMIT_WITH_COMPLETE_NEGATIVE_EVIDENCE
DO_NOT_SUBMIT_WITH_INCOMPLETE_IMPLEMENTATION
DO_NOT_SUBMIT_WITH_INCOMPLETE_SEARCH
PROMPT_NONCOMPLIANCE_FAIL
EXTERNAL_BLOCKER_EVAL_INFRA
EXTERNAL_BLOCKER_REPO_OR_RESOURCE
EXTERNAL_BLOCKER_QWEN_API
EXTERNAL_BLOCKER_SUBAGENT_INFRA
```

`PIVOT_HIDDEN_SAFE_PROBE_PACKAGE` 和低分 `B0 fallback package` 被删除。hidden-safe 低罚候选只能作为人工报告证据，不得自动打 submission-shaped zip。

禁止使用：

```text
EXTERNAL_BLOCKER_QWEN_API
```

来表示 schema_valid_rate 不达标。只有 Qwen API 完全不可调用、环境变量缺失且重试无效，才是 Qwen 外部阻塞。弱模型输出差属于内部 compiler/strategy 问题，必须用 ensemble、repair、UnknownSoft 继续。

---

## 5. Stage 0：强制代码审计和旧系统断点定位

### 5.1 目标

先审代码，不先写新算法。必须真实检查上一轮为什么是外壳。

### 5.2 必查文件

至少检查：

```text
demo/agent/model_decision_service.py
demo/agent/rescue_scorer.py
demo/agent/config.py
demo/agent/query_policy.py
demo/agent/candidate_generator.py
demo/agent/preference_monitor.py
demo/agent/preference_debt_market.py
demo/agent/visible_rollout.py
demo/agent/visible_graph_mpc.py
demo/agent/learned_ranker.py
tools/run_dragon_orca_experiment_grid.py
tools/verify_dragon_orca_completion.py
tools/evolve_dragon_heuristics.py
tools/build_dragon_regret_analyzer.py
```

### 5.3 输出

写入 `reports/pivot_redline_forensics.csv` 的 `code_audit` rows：

```text
component
claimed_role
actual_source_file
actually_called_by_runtime yes/no
changes_candidate_generation yes/no
changes_score yes/no
changes_action yes/no
uses_rescue_path yes/no
trace_source actual/synthetic/stage_name
is_shell yes/no
fix_required
```

### 5.4 Reviewer

调用 `Anti-Shell Source Auditor`。它必须直接读取源码，禁止只读报告。

---

## 6. Stage 1：冻结 B0 和真 no-op gate

### 6.1 B0 frozen baseline

必须复现：

```text
variant=best_rescue
dataset=20260529
simulation_days=31
official_net ~= 5067.69
gross_minus_cost ~= 43207.69
preference_penalty ~= 38140.0
take/wait/reposition ~= 89/163/0
invalid/rejected/income_abort = 0
```

B0 文件、配置、scorer、query policy 不得被新 planner 污染。

### 6.2 新 planner no-op 必须是真 no-op

实现 `crown_pivot_redline_v1` 的 no-op 模式，统一命名如下，不得再混用 P/R/D 前缀：

```text
R0_B0_best_rescue
R1_pivot_noop_compile_all_weights_zero
R2_pivot_noop_debt_monitor_score_zero
R3_pivot_noop_value_model_loaded_weight_zero
R4_pivot_noop_query_logger_exact_b0_query
R5_pivot_noop_candidate_bucket_b0_action_forced
R6_pivot_noop_unforced_full_planner_all_new_weights_zero
```

这些 row 必须使用 `variant=crown_pivot_redline_v1`，不得使用 `best_rescue` 冒充 no-op。

重要：`R5_pivot_noop_candidate_bucket_b0_action_forced` 只能证明候选桶 instrumentation 不污染 B0，不能证明 Pivot planner 主路径可用。必须另有 `R6_pivot_noop_unforced_full_planner_all_new_weights_zero`：新 planner 完整生成候选、评分、选择，但所有新增权重为 0，最终 action 与 B0 等价。

验收：

```text
action_signature_match_rate >= 0.999
score deltas <= 100
invalid = 0
```

如果 no-op 漂移，停止策略开发，修 no-op。不得像 Dragon 一样先漂移后又用 best_rescue row 覆盖。

### 6.3 Pure B0 Shadow

实现：

```text
demo/agent/pivot_redline/b0_shadow.py
```

要求：

- `score_b0_pure(options, world, wait_lock)` 或等价纯函数无副作用。
- 不 query、不 refresh、不修改 options、不读新 planner config。
- 每个 pivot 决策 trace 必须记录：`b0_pure_action`, `new_action`, `override_reason`, `override_score_delta`。
- B0 shadow 只做诊断和对照，不是 final fallback。新 planner 可以把 B0 action 作为普通候选，但不能因低置信直接默认回退 B0；如果最终策略实质上等于 B0 或 override_count 低且本地不胜 B0，必须判定为 failed integration，不得打包。

### 6.4 Reviewer

调用 `B0 Isolation Auditor`。必须检查新 planner no-op 不是 `best_rescue` 冒充。

---

## 7. Stage 2：高分轨迹考古与复现

### 7.1 必找历史锚点

在 git history、archive、reports、runs、tools、branches 中强制定位：

```text
money_greedy_no_pref: gross_minus_cost≈77602.52, preference_penalty≈200540
trial_017 fuse row: official_net=8142.11, gross=37562.11, penalty=29420
B9c wait_repair_full: official_net=-157.97, gross=29142.03, penalty=29300
money_trajectory_repair: official_net≈35849.85, gross≈53169.85, penalty≈17320
visibility_k600_oracle: official_net≈30960.95, gross≈48400.96, penalty≈17440
Gold final: official_net≈6373.17, gross≈45993.17, penalty≈39620
```

### 7.2 必须区分 exact reproduction 和 artifact-only

对每个锚点输出：

```text
anchor_name
claimed_net/gross/penalty
source_report/source_csv/source_run_dir/source_commit
generating_command_found yes/no
action_trace_found yes/no
current_head_rerun_possible yes/no
current_head_rerun_net/gross/penalty
reproduction_status exact/near/fail/artifact_only
missing_piece
can_distill_generic_patterns yes/no
```

禁止使用 `trial017-like`、`B9c-like`、`money-like` 这种名字当复现。必须 exact reproduction 或明确 forensic fail。

### 7.3 高分行为蒸馏

如果某高分/低罚锚点可复现或有 action trace，生成 distillation rows：

```text
pattern_id
source_anchor
pattern_type
trigger_condition_generic
action_bias
gross_effect_observed
penalty_effect_observed
net_effect_observed
runtime_features_used
exportable_parameter
forbidden_nonexportable_fields
confidence
```

必须输出硬产物：

```text
runs/pivot_redline/dragon_orca_distillation_table.csv
runs/pivot_redline/redline_runtime_transfer_checklist.csv
```

`dragon_orca_distillation_table.csv` 每行必须包含：

```text
source_variant, pattern_type, condition, action_bias, expected_effect_on_gross, expected_effect_on_penalty, legal_runtime_features_used, exportable_parameter, not_exportable_fields, reproduction_status
```

`redline_runtime_transfer_checklist.csv` 必须把 archaeology 转成 M0/M1/M2 初始参数或明确 `not_transferable`：accepted order profit/hour quantile target、duration/lockup cap、query_k distribution、wait budget、take_count range、penalty family avoided、gross-preserving repair pattern。

可蒸馏泛化特征包括：

- profit_per_hour quantile
- duration quantile
- wait distribution by hour/day
- query_k distribution by context
- take_count range
- long_lockup avoidance
- high-risk skip pattern
- rest/window repair pattern
- destination/terminal value pattern from legal observations

禁止导出：cargo_id、driver_id、preference_hash、地点名、固定坐标、固定路线、具体货源顺序。

### 7.4 Reviewer

调用 `High-Score Archaeology Auditor`。没有完成考古不得进入 final package 选择。

---

## 8. Stage 3：Clean Money Backbone 重建

### 8.1 目标

先证明新 planner 能赚钱。Dragon 的 M0 gross 只有 45051，不是 high-gross backbone。本阶段唯一目标是恢复 clean money gross。

20260529 clean money gate：

```text
minimum: gross_minus_cost >= 65000
strong: gross_minus_cost >= 70000
historical target: gross_minus_cost >= 76000
```

本阶段不要求 penalty 低。

### 8.2 独立 clean_money_backbone

必须新建独立 path：

```text
variant=crown_pivot_redline_money_clean
```

流程：

```text
refresh_world
choose query/no-query/k
query if needed
refresh_world after query
normalize/filter post-query current_actionable
build bucketed candidates
legal filter
rank by direct_net/profit_per_hour/finish_before_horizon
execute best positive take
if no positive take: short wait 15/30/60 or small legal reposition only if current visible cluster justifies
```

默认关闭：

```text
preference_soft
preference_repair
rest_guard beyond legality
rescue wait loops
time_shadow
twohop_lite
Qwen auditor numeric
visible graph old module
beam old module
value old module
macro old module
```

### 8.3 Candidate bucket，禁止 top80 单一截断

必须实现分桶候选保留：

```text
top_direct_net
top_profit_per_hour
top_short_duration
top_low_pickup_deadhead
top_low_total_lockup
top_good_dropoff_terminal_proxy
top_potential_repair_take
top_low_pref_risk
B0 action
wait 15/30/60/120/240/overnight boundary
reposition to current visible pickup clusters 3~5
reposition to current visible high-value dropoff clusters 3~5
```

去重后统一评分。禁止在 preference/value/repair 评分前用单一 profit/hour top80 截断所有候选。

### 8.4 Money grid

至少跑 40 个 full 20260529 31-day clean money configs：

```text
query_k in {50,100,200,300,600}
ranker in {direct_net, profit_per_hour, direct_net_plus_pph, direct_net_plus_pph_minus_lockup}
duration_cap in {none, 8h, 12h, 18h, 24h}
pickup_deadhead_cap in {none, 50, 100, 200}
wait_minutes_when_empty in {15,30,60}
force_take_after_waits in {1,2,3}
month_end_finish_guard in {off,on}
```

如果 current-branch 无法复现 `money_greedy_no_pref` 且 best gross < 65000，必须做 `money_recovery_forensics`，定位退化层：

```text
query_k/query_time/current_actionable filtering/direct_net calculation/candidate pruning/rest guard/finish horizon/score floor/take threshold
```

不得把 gross=45k 称为 high-gross。

### 8.5 Reviewer

调用 `Clean Money Backbone Auditor`。它必须确认 clean money path 不经过 rescue_scorer。

---

## 9. Stage 4：Qwen 多步 ensemble 偏好编译，但不让 schema gate 卡死策略

### 9.1 Qwen 角色

Qwen 只允许做：

```text
Preference Contract Compiler
Observed Visible Vocabulary Linker
Top-Conflict Risk Auditor
```

Qwen 禁止：

```text
直接输出最终动作
直接输出 cargo_id
直接输出 numeric score adjustment
一票否决高毛利动作
```

Qwen numeric auditor 继续 OFF。

### 9.2 多步 ensemble pipeline

每条偏好至少走：

```text
splitter_A, splitter_B
primitive_tagger_A, primitive_tagger_B
polarity_scope_aggregation_A, polarity_scope_aggregation_B
slot_extractor_A, slot_extractor_B
contract_composer_A, contract_composer_B
critic_A, critic_B
counterexample_generator_A, counterexample_generator_B
deterministic_schema_repair
deterministic_contradiction_check
ensemble_vote
```

输出多个 hypotheses，而不是强行选一个真理：

```json
{
  "preference_hash": "...",
  "contract_hypotheses": [
    {
      "hypothesis_id": "...",
      "primitive_family": "...",
      "polarity": "avoid|require|limit|prefer|unknown",
      "trigger_actions": ["take", "wait", "reposition", "query", "arrival", "dwell", "whole_day"],
      "aggregation": "per_action|per_day|month_end|capped|continuous_window|distinct_day|cumulative|once_if_failed|unknown",
      "slots": {},
      "confidence": 0.0,
      "hard_block_allowed": false,
      "unknown_soft_reason": null
    }
  ]
}
```

### 9.3 Runtime 风险判定产品

对于每个 candidate，不要求 Qwen 给完整 contract 真理，只要求输出：

```text
all_hypotheses_safe yes/no/unknown
any_high_confidence_violation yes/no
all_hypotheses_violation yes/no/unknown
candidate_repairs_required_rule yes/no/unknown
unsafe_for_hard_block_reason
```

分歧时：UnknownSoft + bounded risk + optional top-conflict audit，不得 hard block。

### 9.4 Preference Contract Repair Gym

建立本地 gym：

```text
public 46 preferences + synthetic hidden mutations
positive trajectory
negative trajectory
repair trajectory
ambiguous trajectory
```

评估指标：

```text
behavioral_accuracy
false_safe_rate
false_hard_block_rate
unknown_rate
high_confidence_executable_rate
runtime_score_delta_when_used
```

Schema valid rate 只是质量指标，不是策略搜索 stop gate。schema 低只能触发 repair/UnknownSoft，不得停止 money/value/beam/evolution。

### 9.5 Qwen artifacts freeze policy

Bulk search 阶段必须冻结真实 Qwen artifacts：

1. 先对当前 drivers/preferences 运行 live Qwen multi-step compile/link/ensemble，生成 contract/link artifact cache。
2. 缓存必须记录 model_name、prompt_version、preference_hash、vocab_hash、artifact_hash、redacted_response_hash。
3. money/risk/value/beam/evolution/search 阶段冻结这些 artifacts，只搜索 generic weights、thresholds、query policy、beam policy、macro policy。
4. Top 5 / package candidates 必须用 live-Qwen path 重新跑确认，并报告 frozen-cache score 与 live-Qwen confirmation score 差异。
5. Qwen schema / behavior benchmark fail 不能阻止 ValueModel、Beam、Query、ReEvo、LNS、full search；弱 Qwen 只能降级为 UnknownSoft / lower confidence / diagnostic-only。只有 API 完全不可调用才是 `EXTERNAL_BLOCKER_QWEN_API`。

### 9.6 Clause private reference

Clause splitter 输出必须保留可执行的 private reference：

- `source_span_hash` 可进入报告；
- atomic clause text / span offset 只能写入 `.private` 或 runtime private cache；
- 下游 step 通过 `clause_private_ref` 读取 atomic_clause_text；
- committed reports 只存 hash/redacted，不得存 raw text。

### 9.7 Reviewer

调用 `Qwen Ensemble Compiler Auditor`。它必须检查 raw Qwen IO 在 private 目录，正式报告只写 hash/抽象标签。

---

## 10. Stage 5：Scorer Probe 与 Preference Debt Accountant

### 10.1 先校准 scorer semantics

必须实现离线工具，不得把 scorer probe 放进 runtime：

```text
tools/pivot_scorer_probe_offline.py
tools/run_pivot_scorer_probe_lab.py
```

离线 probe 输出只能写入 `runs/pivot_redline/scorer_probe/semantic_profile.json` 或对应 run artifacts。runtime 只能包含：

```text
demo/agent/pivot_redline/scorer_semantics_profile.py
```

该 runtime 文件只能包含抽象、通用、人工/工具校准后的 semantic profile 和数字参数；不得 import server/bench/scorer/income，不得读取 tools/runs/reports/probe outputs，不得包含 public literal、driver_id、cargo_id、rule_hash 特化。

对每个启用 primitive family 构造最小 metamorphic trajectories，验证：

```text
per_action
per_day
month_end
capped
continuous_window
distinct_day
once_failed
wait 是否算 inactive
query 是否打断 rest
reposition 是否打断 rest
start day vs finish day
finish_after_horizon income risk
```

未通过 scorer probe 的规则：

```text
hard_block_allowed = false
large_penalty_weight_allowed = false
only_soft_risk_or_diagnostic = true
```

Penalty attribution / scorer probe / counterfactual outputs 只能校准 generic family-level curves。`demo/agent` runtime 不得读取 `pivot_redline_forensics.csv`、run traces、scorer probe outputs、exact labels、regret attribution 文件；verifier 必须扫描 demo/agent 是否读取 reports/runs/probe/trace。

### 10.2 真 Preference Debt Accountant

实现 per-rule/per-contract debt state，不得再用 rule_count/amount_mass 粗算。

每条 rule state 至少包含：

```text
status: active|fulfilled|violated|capped|unrepairable|unknown
debt_so_far
shadow_price_now
cap_remaining
slack_remaining
remaining_days
current_count
distinct_day_count
continuous_minutes
dwell_minutes
sequence_progress
deadline_remaining_minutes
minimal_repair_plan
minimal_repair_cost
repairability
marginal_penalty_active
lost_window_risk
last_update_event_hash
confidence
```

每个 candidate 必须计算：

```text
immediate_penalty_delta
minimal_repair_cost_delta
lost_repair_window_cost
deadline_shadow_price_delta
confirmed_repair_credit
unknown_soft_risk
already_capped_discount
irreversibility_cost
```

总偏好项：

```text
preference_delta_cost =
    immediate_penalty_delta
  + minimal_repair_cost_delta
  + lost_repair_window_cost
  + deadline_shadow_price_delta
  + irreversibility_cost
  + bounded_unknown_soft_risk
  - confirmed_repair_credit
```

### 10.3 High-confidence shield scope

默认只允许 high-confidence per-action avoid/limit 影响强：

```text
cargo_attribute avoid/require when visible linker high confidence
pickup deadhead / haul distance / cumulative distance budget
scheduled active window avoid if scorer probe confirms
first-event deadline / daily count if deterministic
required matching cargo -> repair_take_bonus
```

默认关闭或低权重：

```text
full inactive day 强制修复
location dwell 强制修复
ordered sequence 强制修复
long wait/reposition repair
```

这些只有 scorer probe + full-run ablation 正收益才可打开。

### 10.4 Reviewer

调用 `Preference Debt & Scorer Semantics Auditor`。它必须反查 debt state 是否真实 per-rule，不得是合成 family table。

---

## 11. Stage 6：动作级风险数据集与轻量模型训练

### 11.1 Action-level dataset

必须实现：

```text
tools/build_redline_action_dataset.py
```

从以下来源生成训练/验证样本：

```text
B0 traces
clean money traces
trial_017 exact trace if found
B9c exact trace
Gold trace
E5/A3 hunter trace
randomized legal policy traces
clean money grid traces
pivot search traces
```

每行样本：

```text
state_features
candidate_action_features
candidate_type
immediate_direct_net
profit_per_hour
duration_minutes
pickup_deadhead_km
haul_km
finish_time_bucket
dropoff_coarse_cell_relative
visible_market_stats
recent_query_stats
preference_debt_vector_by_primitive
short_suffix_gross_return_6h/12h/24h
short_suffix_penalty_delta_6h/12h/24h
month_end_outcome_if_executed_when_replay_valid
label_validity
continuation_policy
visibility_valid
legality_valid
state_compatibility_ok
```

禁止使用特征：

```text
cargo_id
driver_id
preference_hash
rule_hash
fixed city/place name
fixed coordinate hotspot
route template
future cargo availability
raw public preference literal
```

### 11.2 Counterfactual label validity

反事实必须分层：

```text
immediate_checker_delta
completed_suffix_replay_delta
paired_receding_policy_rollout_delta
macro_completion_delta
heuristic_estimate_only
```

invalid replay labels 只能诊断，不能训练 risk/value 权重。

### 11.3 Label construction hard rules

RiskModel / ValueModel 若没有真实 fit/training 和 holdout validation，不得命名为 model，只能叫 `heuristic_score_component`。

禁止标签：

```text
- 把 full-month final score 复制给每个 decision；
- 使用未来 cargo count / future market density；
- 使用 cargo_id / driver_id / exact coordinate / fixed route / rule_hash / preference_hash；
- 使用 month_end 之后的信息作为每步标签。
```

必须输出：

```text
train_rows, valid_rows, label_definition, feature_list, top_feature_importance, holdout_error, ablation_delta_net
```

Value label 必须来自同一 trace 的 next 6h/12h/24h short-window suffix return；month-end label 只能使用 t 之后 suffix，不能复制整月分数。验证必须按 run_family/dataset/timeblock 分开，不能只在同一轨迹族 train/test。默认不使用 raw lat/lng；只允许 coarse relative cell/time bucket。若坐标类特征进入 top importance 或表现出固定 hotspot 行为，必须禁用或降级为线性/clip 模型。

### 11.4 RiskModel(s,a)

训练轻量风险模型：

```text
Ridge / LogisticRegression / RandomForest / HistGradientBoosting / ExtraTrees
fallback: pure numpy linear model
```

输出：

```text
expected_penalty_risk_bucket
expected_penalty_delta_6h/24h
high_confidence_violation_probability
unknown_soft_risk
```

### 11.4 ValueModel(s')

训练轻量价值模型：

```text
future_6h_gross
future_12h_gross
future_24h_gross
future_to_month_gross
future_penalty_risk
terminal_cell_time_value
```

特征：

```text
hour_of_day
day_of_month
weekday
remaining_days
remaining_minutes_today
coarse relative cell or geohash bucket with anti-hotspot audit
current visible market density
current topN direct_net/profit_per_hour stats
recent query yield
candidate after-action time/location summary
preference debt summary
today rest/work state
recent action mix
query_minutes_per_take
```

部署必须保守：

```text
terminal_bonus = clip(model_pred, -cap, +cap) * weight
weight in {0, 0.03, 0.05, 0.10, 0.20}
```

### 11.5 Conservative offline RL / IQL-CQL-lite lane

用户明确提出 IQL/CQL 思路。必须至少实现一个 conservative action ranker 实验，不得只写 TODO：

```text
tools/train_conservative_action_ranker.py
```

可采用简化实现：

- IQL-like：学习 V(s)、Q(s,a) 后，用 advantage-weighted rank score。
- CQL-like：对 dataset 外候选加 conservative penalty，避免 OOD 高估。
- 如果样本不足，仍要跑 deterministic feasibility test，并在 report 中标为 `KILLED_BY_DATA_INSUFFICIENCY`，不得称 active。

只有 ablation 提升 official_net 时才允许 runtime 启用。

### 11.6 Feature leakage audit

必须输出：

```text
uses_driver_id false
uses_cargo_id false
uses_fixed_coordinate false
uses_future_cargo false
coordinate_dominance_check pass/fail
hotspot_behavior_check pass/fail
feature_importance_top10
LODO_or_timeblock_validation if possible
```

### 11.7 Reviewer

调用 `Model Training & Feature Audit Auditor`。它必须检查训练脚本、模型文件、feature list、ablation_delta_net。

---

## 12. Stage 7：独立 Pivot Planner 完整实现

### 12.1 Runtime 主流程

`PivotRedlinePlanner.decide()` 必须是独立完整流程：

```text
refresh_world
load/update runtime preference contracts and debt state
check active macro commitment
if macro requires next action:
    execute macro step without query unless macro explicitly permits query
    trace macro step
    return action

choose query plan / no-query / k
execute legal query if needed
refresh_world after query
normalize/filter post-query current_actionable
update current-run legal market memory
build observed vocab and link preference slots
build bucketed candidates
score candidates with full decomposition
run depth=2/3 beam/rollout when enabled
apply safety finalize
trace top-5 and b0_shadow comparison
return action
```

### 12.2 Unified candidate scoring

每个 candidate 记录：

```text
candidate_id_hash
candidate_type take|wait|reposition|macro_step
freight_direct_net
profit_per_hour
pickup_deadhead_cost
duration_lockup_cost
query_cost
terminal_value
risk_model_penalty
preference_delta_cost
confirmed_repair_credit
lost_repair_window_cost
month_end_horizon_cost
unknown_soft_risk
online_probe_value
beam_continuation_value
b0_shadow_bonus_or_guard
final_score
chosen_flag
why_not_chosen
```

核心公式：

```text
score(a) =
    direct_net(a)
  + profit_per_hour_bonus(a)
  + terminal_value_weight * V(s_after_a)
  + confirmed_repair_credit(a)
  - preference_delta_weight * preference_delta_cost(a)
  - risk_model_weight * RiskModel(s,a)
  - duration_lockup_weight * lockup_cost(a)
  - query_cost_weight * query_cost(a)
  - month_end_risk_weight * horizon_cost(a)
  - unknown_soft_weight * unknown_soft_risk(a)
  + distilled_frontier_bonus(a)
```

### 12.3 B0-safe override

新策略覆盖 B0 必须满足：

```text
score(new) > score(B0) + override_margin
or new action materially reduces high-confidence debt at bounded gross cost
or new action opens high terminal value according to trained V and not high preference risk
```

每次 override 必须有 `override_reason`，final report 统计 top 50 overrides。

### 12.4 Reviewer

调用 `Independent Planner Integration Auditor`。它必须确认 `crown_pivot_redline_v1` 不走 `_decide_rescue()`。

---

## 13. Stage 8：Query 预算优化与合法在线探针

### 13.1 Query policy is first-class

实现：

```text
demo/agent/pivot_redline/query_optimizer.py
```

动态 k：

```text
k in {50, 80, 100, 200, 300, 600}
```

选择依据：

```text
current candidate quality
visible density
recent query yield
preference matching need
deadline/debt pressure
month_end risk
large_k repeat count
query_minutes_per_positive_candidate
```

报告指标：

```text
query_count
query_minutes
query_minutes_per_take
query_minutes_per_positive_candidate
large_k_usage
large_k_repeat_count
query_after_wait_count
no_query_rest_count
query_skipped_due_to_macro
```

任何策略若 `query_minutes_per_take > 2 * B0` 且 net 不涨，kill。

### 13.2 Legal online probe

如果 API 支持当前位置外的合法探针查询，则对少量候选 probe 点小 k 查询；如果 API 不支持，禁止假 probe。此时只能把 probe 落地为两步 scout macro：

```text
reposition_to_visible_cluster -> next decision query
```

允许 probe/reposition 目标：

```text
current visible pickup clusters
current visible high-value dropoff clusters
runtime-linked preference target if actionable
same-simulation legal observed market aggregates
```

禁止固定城市、固定坐标、离线热力图。

### 13.3 Reviewer

调用 `Query & Probe Auditor`。

---

## 14. Stage 9：Macro Commitment 和偏好修复

### 14.1 必须实现 commitment，不只是候选

实现：

```text
demo/agent/pivot_redline/macro_commitment.py
```

active macro 字段：

```text
active_macro_id
macro_type
source_contract_ids
start_time
deadline
target_position_hash
required_duration
completed_duration
next_required_action
query_allowed
abort_conditions
expected_avoided_penalty
expected_lost_gross
confidence
scorer_probe_status
```

在普通决策前检查 active macro。对于 no-query rest / full inactive / dwell，macro 执行期间禁止普通 query，除非 macro explicitly permits query。

### 14.2 可用 macro

```text
no_query_rest_block
full_inactive_day
wait_at_target
target_or_dwell_reposition_then_wait
ordered_task_progress
quota_day_plan
repair_take_sequence
```

默认只有 scorer probe + positive full-run ablation 的 macro 可以高权重执行。

### 14.3 Macro report

必须报告：

```text
macro_started_count
macro_completed_count
macro_aborted_count
macro_broken_by_query_count
query_skipped_due_to_macro
official_delta_measured_macro_gain
```

如果有 macro candidates 但没有 macro commitment 实际执行，不能称成功。

### 14.4 Reviewer

调用 `Macro Commitment Auditor`。

---

## 15. Stage 10：真正 depth=2/3 beam / rollout

### 15.1 禁止 fake beam

禁止把 beam 写成 capped scalar bonus。必须有真实 branch expansion data structure：

```text
BeamNode(state_summary, action_sequence, score, debt_state, query_state, terminal_value)
```

### 15.2 Runtime beam

每个决策点生成：

```text
Top 20 take by full score
Top 10 take by direct_net
Top 10 take by profit_per_hour
Top 10 low risk / repair take
wait 15/30/60/120/to next time bucket/to repair window
reposition 3~5 visible clusters or preference target if actionable
B0 action
```

Depth=2 default for close/high-risk/high-debt/long-lockup states；Depth=3 只在：

```text
top candidates close
month-end
high preference debt
long lockup candidate
```

第二层不能假装查询未来货源。可用：

```text
current visible candidates still compatible
value model V(s_after)
preference debt continuation
legal observed market memory aggregate
```

### 15.3 Offline rollout labels

离线训练/评估可以在 local simulator 中做 receding policy rollout，但必须标注 validity，不得把未来货源直接导入 runtime。

### 15.4 Reviewer

调用 `Beam Rollout Auditor`。它必须检查代码中有真实 tree expansion，不是 bonus。

---

## 16. Stage 11：Month-end horizon protection

实现：

```text
demo/agent/pivot_redline/month_end_guard.py
```

最后 5 天增强：

```text
finish_after_horizon block or heavy penalty
long_order_lockup_cost up
pickup_deadhead threshold stricter
protect daily/monthly repair feasibility
avoid new irreversible high-penalty actions
reduce useless large-k query
```

必须检测收入资格：如果订单完成超过仿真 horizon 且收入无效风险，强惩罚或 block。

Reviewer：`Month-End Guard Auditor`。

---

## 17. Stage 12：Regret Analyzer 与 Regret-LNS repair/refill

### 17.1 真反事实，不再合成 debt 表

实现：

```text
tools/build_pivot_regret_analyzer.py
tools/run_pivot_counterfactual_lab.py
```

每次 full run 后输出 top regret：

```text
top 50 high-penalty accepted actions
top 50 skipped high-net actions
top 50 long-lockup actions
top 50 query-waste intervals
top 50 B0 vs pivot changed decisions
top 30 wait/reposition candidates with suspected repair value
```

每条必须包含：

```text
state_time_bucket
action_chosen
action_alternative
candidate_rank
score_decomposition
actual_suffix_outcome
counterfactual_label_type
validity_flags
gross_delta
penalty_delta
net_delta
confidence
```

禁止总分均摊、family fixed weights、stage-name inference。

### 17.2 Regret-LNS

实现 destroy-repair-refill：

```text
destroy: remove high-penalty/low-value/long-lockup segments
repair: insert repair_take / short wait / reposition / rest macro if scorer-probe valid
refill: insert high gross-per-hour take in unprotected gaps
```

每个 LNS candidate 必须 full-run ablation。不能只生成 JSON。

Reviewer：`Regret & LNS Auditor`。

---

## 18. Stage 13：ReEvo / Heuristic Evolution 真实闭环

### 18.0 ReEvo 启动条件

ReEvo/LNS 是扩展正向趋势的工具，不是从坏底座中随机拯救一切的工具。启动 120+ full rows 前必须满足至少一个：

```text
1. clean money gross >= 65000；
2. usable money backbone gross >= 52000 且 candidate_pool_quality 明显高于 B0；
3. risk_model_only 比 money_clean 降 penalty >= 10000 且 gross >= 50000；
4. value_model_only 或 depth2_rollout 相对 B0 official_net 提升 >= 3000；
5. high-score archaeology 当前分支可复现并生成 redline_policy_prior.json。
```

若不满足，禁止启动大规模 ReEvo；先修 candidate bucket / money recovery / risk labels / value labels。若 money+model 基础已完成但无任何正信号，允许转入 `DO_NOT_SUBMIT_WITH_COMPLETE_NEGATIVE_EVIDENCE`，不得用 120 行坏空间搜索包装成猛攻。


### 18.1 禁止静态 recipe 冒充 evolution

必须实现反馈迭代：

```text
tools/evolve_pivot_redline_heuristics.py
```

每个 heuristic 是受限 JSON，不生成任意 runtime code：

```json
{
  "weights": {
    "direct_net": 1.0,
    "profit_per_hour": 0.0,
    "preference_delta": 0.0,
    "risk_model": 0.0,
    "terminal_value": 0.0,
    "lockup": 0.0,
    "query_cost": 0.0,
    "month_end": 0.0,
    "repair_credit": 0.0
  },
  "query_policy": {},
  "wait_policy": {},
  "reposition_policy": {},
  "beam_depth": 1,
  "caps": {}
}
```

### 18.2 必须真实 generation loop

至少：

```text
population=20
generations>=5
full 20260529 for all gen1 configs
select top 5
reflect on table
mutate/crossover
repeat
```

如果前 20 clean configs 全部低于 B0，不能继续随机搜坏空间，必须回到 candidate/risk/value 修复，然后重启 evolution。

目标至少 200 个 executed 20260529 full rows，最低不可少于 120。所有 rows 必须 `EXECUTED`。

### 18.3 Objective

搜索目标：

```text
primary: official_net
secondary: lower preference_penalty
tertiary: gross_minus_cost
stability: 0509 sanity and no invalid
```

禁止用 gross floor 杀掉 official_net 更高且 penalty 更低的 hidden-safe candidate。

### 18.4 Reviewer

调用 `Heuristic Evolution Auditor`。它必须检查 generation feedback 是由 full-run 分数驱动，而不是静态 grid。

---

## 19. Stage 14：实验矩阵

必须执行以下 full 31-day 20260529 rows。所有 `status=EXECUTED`，不得 PLANNED/MISSING_RUN/proxy/smoke。

### 19.1 Baseline / no-op

```text
R0_B0_best_rescue
R1_pivot_noop_compile_all_weights_zero
R2_pivot_noop_debt_monitor_score_zero
R3_pivot_noop_value_model_loaded_weight_zero
R4_pivot_noop_query_logger_exact_b0_query
R5_pivot_noop_candidate_bucket_b0_action_forced
R6_pivot_noop_unforced_full_planner_all_new_weights_zero
```

All no-op rows must use `variant=crown_pivot_redline_v1`; no no-op row may use `variant=best_rescue` except R0 baseline. R5 forced-B0 is isolation only; R6 unforced full planner proves the main path is wired.

### 19.2 Archaeology / anchors

```text
A0_money_greedy_no_pref_exact_or_forensic
A1_trial017_exact_or_forensic
A2_B9c_exact_or_forensic
A3_Gold_exact_or_forensic
A4_money_trajectory_repair_exact_or_forensic
A5_visibility_k600_oracle_exact_or_forensic
```

### 19.3 Clean money

至少 40 rows：

```text
MONEY001..MONEY040
```

### 19.4 Module ablations

```text
P0_clean_candidate_bucket_no_score_change
P1_pure_high_quality_hunter
P2_preference_debt_only
P3_risk_model_only
P4_value_model_only
P5_risk_plus_value
P6_query_optimizer_only
P7_month_end_guard_only
P8_macro_commitment_only
P9_depth2_beam
P10_depth3_beam
P11_regret_lns_best
P12_conservative_ranker_iql_cql_lite
P13_full_pivot_without_evolution
```

### 19.5 Mandatory chain tests before large full-run search

在 full-run search 前必须完成以下 deterministic chain tests；否则后续 row 只能 diagnostic：

```text
T1_candidate_bucket_diversity: 同一 query world 下证明候选包含 direct_net top、pph top、short duration、low risk、terminal value、repair_take、B0 action。
T2_risk_model_known_bad_action: 输入已标注高罚动作，RiskModel 必须把它排在安全替代之上。
T3_value_model_terminal_choice: 两个 direct_net 接近但 terminal value 不同的候选，ValueModel 必须提升高 terminal 候选。
T4_beam_branch_expansion: BeamNode tree depth >=2，child_count>1，selected action 使用 continuation score。
T5_b0_shadow_side_effect: 调用 b0_shadow 不改变 query_count/world/candidate scores/cache。
T6_end_to_end_trace: 一次 live decision trace 含 top-5 候选和所有 score components、why_not_chosen。
T7_full_precision_reposition: runtime action、trace-to-action、package 输出中 reposition lat/lng 不被 round。
```

### 19.6 Evolution

至少 120 total executed rows，目标 200+：

```text
EVO_G1_001..020
EVO_G2_001..020
EVO_G3_001..020
EVO_G4_001..020
EVO_G5_001..020
... continue to >=120, target >=200
```

### 19.6 Confirmation and sanity

```text
C0_final_selected_20260529_rerun
C1_hidden_safe_candidate_20260529_rerun
C2_profit_candidate_20260529_rerun
C3_B0_rerun_after_all_changes
```

Top 20 20260529 candidates must run 20260509 sanity if any of these holds:

```text
net > B0 + 3000
penalty < B0 - 6000
gross > B0 + 8000
official_net >= 10000
```

---

## 20. Score gates and package policy

### 20.1 Weak / experimental / recommended gates

```text
weak_breakthrough:
  official_net >= 10000
  or official_net > B0 + 3000 and preference_penalty <= B0

hidden_safe_probe:
  official_net > B0 + 3000
  preference_penalty <= 32000
  gross_minus_cost >= 35000
  invalid/rejected/income_abort = 0

experimental:
  official_net >= 15000
  preference_penalty <= 33000
  gross_minus_cost >= 43000
  invalid/rejected/income_abort = 0

recommended:
  official_net >= 25000
  preference_penalty <= 28000
  gross_minus_cost >= 50000
  0509 sanity not catastrophic
  invalid/rejected/income_abort = 0

crown_target:
  official_net >= 38000
  preference_penalty <= 22000
  gross_minus_cost >= 58000
```

### 20.2 Package

只有达到 `recommended` 或 `experimental`，才生成 submission/probe zip：

```text
runs/packages/CROWN_PIVOT_REDLINE_<label>.zip
```

要求：

- root 必须是 `demo/`。
- 包含 `demo/agent/` 和 `demo/SUBMISSION.md`。
- 不包含 server/data/reports/runs/archive/docs/prompts/private/cache/pyc/keys。
- `SUBMISSION.md` 第一行必须对应 package label。
- 记录 SHA256、size、entry_count、default_variant。
- default_variant 必须是 pivot variant，不能是 `best_rescue`。

`hidden_safe_probe` 只生成报告/config evidence，不生成 demo-root zip。

低于 `experimental` 不生成 submission/probe zip。若 official_net >= 15000、penalty/gross/invalid gates 达到 weak review gate，可生成醒目 review-only 包，文件名必须含 `NOT_RECOMMENDED_DO_NOT_SUBMIT`，`SUBMISSION.md` 第一行必须写：

```text
NOT RECOMMENDED FOR B榜 SUBMISSION
```

official_net < 15000 时不生成任何 zip，只生成报告和分支证据。若 final selected effectively B0 fallback，不生成 package。

---

## 21. Verifier 必须先写后用

先实现：

```text
tools/verify_pivot_redline_completion.py
```

Verifier 必须是 phase-aware，不得早期 phase 查最终 artifacts，也不得为了 early pass 写水。阶段定义：

```text
setup: 只查目录、规则、verifier、自身可运行、subagent preflight。
noop: 只查 R0-R6 no-op、B0 shadow、audit_pivot_runtime_path。
archaeology: 只查 anchors status、distillation table、artifact-only 不导出数值先验。
money: 只查 clean money recovery、money grid、candidate bucket diversity、money forensics。
compiler: 只查 Qwen cache/freeze、gym、schema/behavior，不阻断 strategy search。
scorer_probe: 只查 offline probe 输出和 runtime semantic profile 边界。
models: 只查 label construction、feature audit、model train/valid/ablation。
planner: 只查 independent planner path、no rescue main path、trace decomposition、beam expansion。
search: 只查真实 full-run rows、无 planned/missing/proxy、ReEvo/BO 行构成。
final: 查所有 final gates、package、0509 sanity、reports<=5、stop_state consistency。
```

必须检查：

```text
branch is crown-pivot-redline-v1
reports exactly five pivot files
B0 reproduced
R1-R4 true pivot no-op and action match
crown_pivot_redline_v1 does not call _decide_rescue/rescue_scorer as main path
automated tools/audit_pivot_runtime_path.py proves _decide_rescue_call_count==0, rescue_scorer_score_call_count==0, rescue_scorer_choose_call_count==0, pivot_decide_call_count>0 for pivot variants
pure B0 shadow trace exists
high-score archaeology rows exist and label exact/forensic honestly
clean money grid >=40 executed rows
if clean money gross<65000, money forensics exists
Qwen schema weakness does not stop strategy search
scorer probe rows exist for enabled preference families
preference debt state is per-rule/per-contract, not family synthetic
risk/value models have feature audit and ablation rows
beam code has branch expansion evidence
query optimizer has query cost metrics
macro commitment has started/completed/aborted stats
regret table not synthetic total-score allocation
ReEvo rows are generation-feedback full-run rows, not static recipe
20260529 executed rows >=120, target >=200 if time/resources allow
0509 sanity rows for top candidates
no PLANNED/MISSING_RUN/proxy/smoke counted
subagent reviewer transcripts exist for every Stage
package audit consistent with score gate
runtime/offline leakage audit P0=0
Qwen numeric auditor off
```

Final verifier must fail if any active module lacks REAL_IMPLEMENTATION_GATE evidence.

---

## 22. Mandatory reviewers

Launch these read-only reviewers at the required points:

```text
0. Anti-Shell Source Auditor
1. B0 Isolation Auditor
2. High-Score Archaeology Auditor
3. Clean Money Backbone Auditor
4. Qwen Ensemble Compiler Auditor
5. Preference Debt & Scorer Semantics Auditor
6. Model Training & Feature Audit Auditor
7. Independent Planner Integration Auditor
8. Query & Probe Auditor
9. Macro Commitment Auditor
10. Beam Rollout Auditor
11. Month-End Guard Auditor
12. Regret & LNS Auditor
13. Heuristic Evolution Auditor
14. Execution Evidence Auditor
15. Leakage & Package Gatekeeper
16. Final Anti-Shell Auditor
```

Reviewer 必须引用具体文件和指标。泛泛 PASS 无效。

---

## 23. Final report 必须包含

`reports/pivot_redline_final_report.md` 第一行必须是：

```text
<STOP_STATE>: <one sentence reason>
```

正文必须包含：

```text
branch / commit / push status
score accounting table
B0 reproduction
true pivot no-op table
code audit shell findings and fixes
high-score archaeology table
clean money backbone result
Qwen compiler gym behavioral metrics
scorer probe semantics results
preference debt active families
risk/value model training data and feature audit
query policy metrics
macro commitment stats
beam rollout usage and ablation
Regret-LNS evidence
ReEvo generation table
20260529 experiment summary
20260509 sanity summary
candidate comparison: B0 fallback / hidden_safe / profit / pivot_best
package path / sha256 / default variant
reviewer findings summary
shortest next path if no submission
```

如果没有突破，必须列出：

```text
top 20 exact changed decisions that hurt
first broken link among: money, preference debt, value, beam, query, macro, evolution
which user ideas were truly implemented, killed, or still blocked
```

---

## 24. 用户想法落实 checklist

Final report 必须逐项填写：

```text
idea_id
user_idea
implementation_file
test_file
runtime_trace_field
full_run_rows_used
ablation_delta_net
reviewer_status
keep_or_kill
```

必须覆盖：

1. 带偏好的在线 DP / 月度动态规划思想。
2. 轻量价值模型 V(s) 训练。
3. 动作评分公式和偏好评分公式。
4. depth=2/3 beam search / rollout。
5. ReEvo / evolutionary heuristic search。
6. query budget optimization。
7. preference debt shadow price。
8. unload/dropoff terminal value。
9. legal online probe / scout reposition。
10. month-end income/horizon protection。
11. counterfactual replay diagnostics。
12. IQL/CQL-lite conservative offline ranker。
13. heuristic evolution as hyper-heuristic。
14. dynamic freight routing as MDP / ADP value approximation。
15. anticipatory time budgeting / time budget price。
16. ML + combinatorial optimization layer。
17. ToT/LATS-style deterministic multi-path search with LLM only for semantic conflict.
18. Qwen3.5-Flash 多步小任务 + executor/auditor ensemble。
19. finite primitive preference state representation。
20. preference-to-decision tradeoff via debt/value/RiskModel。

任何一项不能写“完成”除非满足 REAL_IMPLEMENTATION_GATE。

---

## 25. Required command families

你必须根据仓库实际路径实现并运行等价命令：

```bash
python -m pytest tests -q
python -m compileall demo tools tests
python tools/audit_guard.py --fail-on-p0
python tools/verify_pivot_redline_completion.py --phase setup
python tools/verify_pivot_redline_completion.py --phase noop
python tools/verify_pivot_redline_completion.py --phase archaeology
python tools/verify_pivot_redline_completion.py --phase money
python tools/verify_pivot_redline_completion.py --phase compiler
python tools/verify_pivot_redline_completion.py --phase scorer_probe
python tools/verify_pivot_redline_completion.py --phase models
python tools/verify_pivot_redline_completion.py --phase planner
python tools/verify_pivot_redline_completion.py --phase search
python tools/verify_pivot_redline_completion.py --phase final
python tools/audit_pivot_runtime_path.py --variant crown_pivot_redline_v1 --fail-on-rescue-path
python tools/audit_pivot_runtime_path.py --variant crown_pivot_redline_money_clean --fail-on-rescue-path
```

所有 eval rows 必须有：

```text
command
exit_code
run_dir
status=EXECUTED
dataset
simulation_days
official_net
gross_minus_cost
preference_penalty
take/wait/reposition
query_count/query_minutes
invalid/rejected/income_abort
trace_path
config_hash
```

---

## 26. 资源策略

可使用云端 8 卡 4090 服务器和本机 4060。仿真主要 CPU；模型训练可用 GPU但不强制。使用云端时：

- 以本机公钥 `yinhhzzu` 登录。
- 在云端 home 下建立本项目独立目录。
- 不污染环境，使用 venv/conda。
- 先看 `nvidia-smi`，不 kill 他人进程。
- 优先空闲卡；无空闲用本机；再无则 CPU/轻量模型。
- 本机 CPU 占用高时改云端，防止电脑死机。
- 硬盘不足先清理本项目目录，不动他人文件。

所有资源使用写入 work log。

---

## 27. 最终执行原则

1. 不是修 Dragon，不是修 Fuse，不是修 Pref-Forge，而是创建独立 `crown_pivot_redline_v1`。
2. B0 是 frozen fallback，不是新 planner 内核。
3. 用户想法必须以真实代码和分数闭环落实，不能做成文件名。
4. 先复现高 gross / 低 penalty 锚点，再蒸馏泛化规律。
5. 先 recover money backbone，再加 preference risk；没有 gross 的偏好修复不能夺冠。
6. 偏好不是 if-else，是随时间变化的 debt shadow price。
7. ValueModel 只估值，不直接决定动作；动作由 combinatorial/beam/scorer 层选择。
8. Qwen 只做语义，不做数值裁判。
9. Query 是有成本的信息购买，不是免费输入。
10. ReEvo 必须由 full-run 分数反馈驱动，不是静态配置列表。
11. subagent 不是摆设，每阶段都必须审到代码和证据。
12. 若失败，必须失败得有用：指出第一个真实断点，而不是再交漂亮报告。
---

## 28. v1.1 最终硬补丁：防止执行层再次造成失败

本节覆盖全文所有冲突内容。Codex 必须逐条执行。

### 28.1 Subagent QA 不是停工借口

- 先做 subagent preflight。若真实 subagent 调用失败，先关闭旧 subagent / 释放并发槽位后重试。
- 真实 subagent 不可用时，运行 named independent read-only reviewer passes；每个 reviewer 必须引用 source files、git diff、commands、run_dir、CSV row、metric before/after。
- 不得因为 subagent primitive 不可用而跳过 coding/search，也不得用泛泛 PASS 替代证据。

### 28.2 B0 不得进入 final runtime fallback

- B0 只能是 baseline、no-op oracle、shadow comparison。
- Final default variant 必须是 `crown_pivot_redline_v1` 或明确 pivot 子 variant。
- 如果 final policy 大部分低置信场景直接回 B0，或者本地未超过 B0，必须 `DO_NOT_SUBMIT`，不得生成 zip。

### 28.3 Clean Money 是第一断点

- 先尝试 current-branch 复现 `money_greedy_no_pref` high-gross 行为。
- 若 clean money best gross <52000，停止后续策略开发，first_broken_link=`high_gross_backbone_not_recovered`。
- 若 52000<=gross<65000，只能跑有限 shield/value/beam 诊断，不得启动 120-row ReEvo。
- 若 gross>=65000，才允许 full shield/value/beam/ReEvo 搜索。

### 28.4 历史高分不能凭旧报告导出参数

- money_trajectory_repair、visibility_k600_oracle、trial_017、B9c、Gold 等只有 current-branch exact/near reproduction 或可用 action trace 时，才可导出数值先验。
- artifact-only/fail 只能生成 hypothesis，不得导出阈值、权重、query policy、wait pattern、route pattern、action bias。

### 28.5 搜索前必须冻结 Qwen artifacts

- bulk search 前先 live Qwen compile/link/ensemble，一次生成 artifact cache。
- search 阶段冻结 artifacts，只调 generic weights/thresholds/query/beam/macro。
- top 5 candidates 再用 live-Qwen path 确认。

### 28.6 Risk/Value/Beam 必须是真实现

- 没有训练/fit/valid/feature audit 的 RiskModel/ValueModel 不得叫 model。
- 没有 BeamNode tree、depth>=2、child_count>1、continuation score 的 beam 不得叫 beam。
- 没有 ON/OFF full-run 消融的模块不得标 `ACTIVE_AND_VALIDATED`。

### 28.7 Search rows 质量底线

- 只有 true pivot no-op pass、clean money usable gate pass、Qwen artifacts frozen、trace schema verified、leakage audit P0=0 之后产生的 full-run rows 才计入 >=120。
- 120-row minimum 构成：>=40 ReEvo，>=40 BO/CMA/coordinate，>=20 beam/value/query joint configs。
- 若这些行缺失且 eval infra 正常，是 `PROMPT_NONCOMPLIANCE_FAIL` 或 `DO_NOT_SUBMIT_WITH_INCOMPLETE_SEARCH`，不是成功。

### 28.8 Verifier 与 package

- `verify_pivot_redline_completion.py` 必须 phase-aware；early phases 不查 final artifacts，final phase 不得放水。
- 低于 experimental gate 不生成 submission/probe zip。official_net<15000 不生成任何 zip。
- review-only zip 只能用于代码检查，且必须 `NOT_RECOMMENDED_DO_NOT_SUBMIT`，default_variant 不能是 best_rescue。

### 28.9 Full precision reposition

- 所有 reposition action 输出、trace-to-action、package 均保留全精度 float 坐标，不得 round。
- 必须添加 test 检测 accidental rounding。
