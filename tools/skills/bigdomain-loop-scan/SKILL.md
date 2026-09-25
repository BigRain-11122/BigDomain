---
name: bigdomain-loop-scan
description: BigDomain OSLoop 自迭代轮的五静扫描与收账作业规程（idle-fast 快道与全任务书两态共用）。触发场景：作为 BigDomain 宿主 OSLoop 执行者开轮扫描（state/转办/decisions/双 orders/任务板/git 五静判定）、每 ~10 分钟 tick 轮启动、用户要求跑一轮 OSLoop/巡检/收账/回执集团转办/P-32 日清判定；集团层与兄弟司文件一律只读（跨仓写禁令），回执只落本仓 src/os/state.json log。
---

# BigDomain OSLoop 五静扫描与收账

## 0 铁律（每轮先读）

- 只写本仓 `domain/BigDomain`；集团层与兄弟司仓只读引用（跨仓写禁令）；回执只落 `src/os/state.json` log。
- 一切行数计数=UTF-8 口径（`[System.Text.Encoding]::UTF8`；PowerShell 5.1 默认 GBK 少读中文行=R131 教训）。
- 诚实律：一切宣称带证据；判据预注册先行；完成态=文件在盘+可验证。
- 空转快速路径：开轮先走五静判定；五静全过=一行收账即出不进全任务书；任一异常=转全任务书 `src/os/iteration_prompt.txt` 照走。
- 禁自我膨胀式立法；空转轮不为凑工作量造活。

## 1 机械扫描（先跑脚本·禁再手写逐项命令）

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools/skills/bigdomain-loop-scan/scripts/scan_five_still.ps1
```

- 输出每行 `[AREA] PASS|FLAG|INFO`；只处置 FLAG 与 INFO 决策面，PASS 面不复述不重查（已判过的检查不再检查）。
- 脚本失败=按脚本尾部注释块同口径命令手跑兜底（口径不变）。

## 2 FLAG/INFO 判读与处置

- `[STATE] FLAG`：state.json 解析失败=他执行体写盘迹象→单执行体退避，本轮只读不动、如实记录。
- `[LEDGER]`：lastp 与 state.json log 已回执行比对（同号=已回执非新行；状态列变化=集团面闭口更新如实记）；未回执行=照转办执行+新项排 backlog 顶行+毕 log 记回执一行（引用该编号）。八线群发令可不带 @BigDomain 字样→按派工面判本司执行面/知悉（P-56 教训）。conflict>0=FLAG。
- `[DEC] FLAG`（行数≠last_decision_rows）：新决策行=科学判断闸逐行——过审→执行+回执（log 一行·引用决策号）；存疑→驳回写理由（log 一行）；非本司执行面→知悉不动作（log 一行）；毕更新 last_decision_rows 基线。
- `[GORD] INFO`：集团 orders 尾新行与既往扫描态比对=新令兜底检出；新司令照令执行（新令推翻旧模式·集团律）；按派工面判本司执行面/知悉。
- `[ORD] FLAG`（司级 orders 顶行时间戳≠last_order）：新司令=照令执行；毕更新 last_order。
- `[BENCH] FLAG`（benchmarks_refreshed 距今>7 天）：排刷新轮（刷新项排 backlog 顶行·web 直采优先·毕更新该字段+`docs/global-benchmarks.md` ④更新记录行）；硬约束域（法规/平台规则变更类集团令）=事件即时刷。
- `[TASKS] INFO`：backlog 顶行可认领=认领执行（认领动作落 backlog 行）；全部依赖 CEO 物理件=不可认领·如实记录待物理件不造活。
- `[EXPORT] FLAG`（export_ts ≥24h）：刷新 `docs/status-export.json`（export_ts ISO8601+do/depts/outs/results 全派生自实际状态·F3 律禁写死）。
- `[TREE] FLAG`（脏树/index.lock）：index.lock 或他执行体写盘=同仓单执行体退避（只读不动如实记录）；脏树仅本 loop 自身收账产物=正常收账不退避。

## 3 收账（两态同律·毕必全走）

1. `src/os/state.json`：tick+1；log 追加本轮实况一行+轮账本一行「tokens: local=N api=N api_reason=<一行理由>」；基线字段随实况更新（last_order/last_decision_rows/benchmarks_refreshed）；编辑后必过 ConvertFrom-Json 校验·log 末项禁尾逗号（R189 教训）。
2. `docs/status-export.json`：实况有变即刷；无变且 <24h 新鲜度闸可跳。
3. backlog 完成项标 `[done 日期]`+`tasks.md` 对应项勾选（tasks.md=正典板）。
4. 定向 git add 相关文件（禁全量 add）→commit（一行英文 ≤500 字符·尾标 `[via BigDomain-OSLoop]`·含当轮回执令号=P-51 送达判据）→push；push 失败=只记录不修下轮再看。
5. P-32 日清：当日有集团层面 open 问题/待决策项=23:00 前写本仓根 `HQ-FEEDBACK.md` 一行；无=不写（零膨胀）。

## 4 基线口径（判新标准·防误判）

- 已回执行判据=state.json log 中已记该 P-/D- 号；同号重现行非新行。
- decisions/orders 基线=state.json 顶置字段，只比增量；历史行不重判（时间早于骨架安装=知悉回执一行入 log）。
- 五静全过=①无新转办（ledger 无未回执行+双 orders 无新令+benchmarks 未超 7 天）②decisions 无新行③任务板顶行不可认领④树净无 index.lock⑤无其他会话活跃写盘迹象。
