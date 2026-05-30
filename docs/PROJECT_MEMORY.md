# PROJECT MEMORY

## 长期目标

实现 CROWN-Y Tournament Build，不做 Max 版。主线是 P0/P0++ 合规与稳定，P1 使用 Time Shadow、Preference Certificate、Visible two-hop、Resource-pressure Endgame、Scout Query、Payback-gated Reposition 与 Regret Dashboard。

## 资料理解摘要

- `赛事简介(4).txt` 与 `赛题详情(1).txt`：任务是完整自然月的连续决策，动作只有 take/wait/reposition；每一步动作推进时间和位置，目标是净收益与个性化偏好的综合结果。
- `技术分享与主办法回复整理.md`：最关键约束是信息边界、偏好不硬编码、query 接口语义、31 天仿真、round bug、B 榜提交只交 agent 代码目录。偏好以运行时接口返回为准，隐藏数据会变化。
- `demo_docs_release_20260529.zip`：作为最新代码基座，包含 `SimulationApiPort`、评测编排、收益脚本和 2 个司机 smoke 数据。
- `demo_docs_release_20260509.zip`：作为旧版 10 司机离线参考，保留在 `_offline_reference_20260509/`，不提交。
- 当前基座中 query 会按返回条数推进时间，因此 query 后必须重建 World；`config.example.json` 已改为 31 天。

## 合规红线

- agent 运行时禁止读取 `cargo_dataset.jsonl`、`drivers.json` 或等价 raw data。
- 禁止 `server` / `bench` 依赖和裁判侧状态类依赖。
- 禁止司机、货源、城市、路线、固定坐标、示例偏好词硬编码。
- `take_order` 只允许当前决策 observed set 中的 `current_actionable` cargo。
- shadow 和 historical summary 只能形成聚合特征，永不成为可执行货源。

## 当前最佳配置

- P0/P0++：全部开启并有测试覆盖。
- P1：Time Shadow、Preference Certificate、Visible two-hop、Endgame、Scout-then-deepen、Payback-gated Reposition、Regret Dashboard 已实现。
- P2：Learned Ranker 代码存在但默认关闭；只提供 sign/OOD/clip 测试。
- P3：Destination Shadow、three-hop、option rollout、高频 LLM Judge 默认关闭。

## 重要修复与教训

- baseline agent 使用大模型输出动作，包含运行时 prompt 和高风险自由输出；已替换为确定性主流程。
- `query_cargo` 推进时间，不能用 query 前状态过滤。
- 本地评测 round bug 当前基座已有坐标保护，`tools/fix_eval_round_bug.py` 会检查。
- 远端 GitHub refs 查询失败，后续 push 可能受远端可访问性阻塞，最终报告必须记录。

