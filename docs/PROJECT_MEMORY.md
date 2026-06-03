# PROJECT MEMORY

## CROWN-PCE Oracle Gap Memory

- Active branch is `crown-pce-oracle-gap`; this branch continues from the existing Next Build work rather than rebuilding from scratch.
- Current evidence says legal runs, Qwen calls, and complete reports are not enough: the 20260529 Next Build frontier topped out at official net `2240.98`, while rescue reference was `5067.69`.
- Dominant failure is the high-gross/high-penalty versus strict-preference/low-gross split. CROWN-PCE must first prove the reachable score space with offline oracles, then close the executable preference predicate gap.
- Score Accountant conclusion from prior evidence: official net already equals gross income minus distance cost minus preference penalty. Do not use any net-minus-penalty proxy.
- PCE final stop states are `PCE_STRONG_SUCCESS`, `PCE_PARTIAL_SUCCESS`, `DO_NOT_SUBMIT_WITH_ORACLE_EVIDENCE`, or `EXTERNAL_BLOCKER`.
- PCE final artifacts are limited to `reports/pce_final_report.md`, `reports/pce_experiments.csv`, `reports/oracle_gap.csv`, `reports/predicate_eval.csv`, and `reports/action_forensics.csv`.
- Runtime P0 boundary remains strict: only `SimulationApiPort`, no raw data reads, no `server.*` or `bench.*`, no future information, no hardcoded driver/cargo/place/route/fixed-coordinate features, no Destination Shadow Query, no remembered-cargo take after `no_query`.
- Qwen3.5-Flash remains ON for non-empty preferences when available, but only for Preference Compiler v2, Observed Vocabulary Linker, and gated Candidate Auditor. It must not choose final actions.
- Protected example terms and scenario shortcut words must remain redacted in committed files.
- Offline oracle and label tools may read public debug data and official scoring code, but runtime must not read or reference oracle artifacts, exact-label outputs, money-repair trajectories, full-info trajectories, raw ids, static places, fixed coordinates, fixed routes, or future availability.

## Next Build v4 Memory

- Starting branch for this work is `crown-y-score-rescue` at `0f2af10`; work branch is `crown-y-next-build`.
- Rescue baseline is legal but not a score-push submission: 20260529 net `5067.69`, preference penalty `38140.0`, take/wait/reposition `89/163/0`, wait ratio `0.6468`, Qwen compile calls `5`.
- Next Build v4 must diagnose score accounting, wait counterfactuals, query survivability, and preference state before enabling larger strategy modules.
- Final status is score-gated: under `40000` 20260529 official net must be `DO_NOT_SUBMIT_WITH_FRONTIER_EVIDENCE`, not success.
- Final artifacts for this build are limited to five Next Build files under `reports/`.
- Existing tournament/rescue reports are legacy references. The Next Build final handoff must be exactly the five v4 artifacts, with no new scattered reports.
- Literal banned terms and example scenario shortcuts must remain redacted in repository files.

## Score Rescue Memory

- The 20260529 tournament build is a failed reference, not a success: negative net, high wait ratio, very low take count and zero Qwen calls.
- Rescue mode must stay simple and current-observed: fixed current query, post-query World refresh, current_actionable filtering, direct positive net scoring and deterministic certificates.
- Wait-lock forensic traces are first-class evidence. Every wait in rescue mode needs a machine-readable reason and the rejected top take candidates.
- Hard blocks are intentionally narrow. Unknown preference, time shadow, endgame and two-hop risk are soft capped costs unless a high-confidence irreversible preference violation or legal/actionability issue exists.
- Qwen is a preference DSL compiler only. Missing or dummy API keys are forensic fallback evidence, not successful model use.
- Final rescue handoff evidence is centralized in `reports/*score_rescue*.md`, `reports/regret_dashboard_v2.md`, `reports/qwen_preference_compile_report.md` and `reports/score_rescue_final_report.md`.

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
