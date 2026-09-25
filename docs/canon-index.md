# BigDomain 正典速查索引（canon-index）

> 溯源：集团 docs/orders.md **GL204 清理整合令**（CEO 台 2026-09-25 ~14:08「集团组织一次清理整合工作，把各个流程规则文档等全面梳理清理一下」）·09-30 治理日 U178 首窗 M5 落地率对账件。方法=集团 U188 指令整合判例四则（同义簇归并/冲突终谳/时限态回落/上位吸收）+**原文保全铁律**（判例层=本索引·原行永不删改·过时规则=标已回落/已超越+指针·非删除）。
> 范围=本司流程/规则/协议文档全集；台账/日志/工作板类（state.json log、orders.md、HQ-FEEDBACK 行、backlog done 行）=append-only 数据件·历史提及=记录非规则·豁免清理（指针见 §一 15~18）。
> 判据预注册（开工前先定·`src/os/backlog.md` GL204 行在册）：**AC-C1** 索引落盘=域入口一屏各规则→权威指针｜**AC-C2** 过时回落清单逐文档过闸点名｜**AC-C3** 冲突终谳清单同件两说逐条｜**AC-C4** 四计数报告行落盘｜**AC-C5** 原文保全零违（git diff 可证）。

## 一、速查正典索引（AC-C1·20 规则域·每域唯一权威面）

| # | 规则域 | 权威文件（唯一） | 现役状态 |
|---|---|---|---|
| 1 | 商业化蓝图（定位/价目/分成/直播/UGC 总纲/双螺旋/待裁项） | `BLUEPRINT.md` §〇~§十二 | v1.0 现役（CEO 全案拆解正典） |
| 2 | 合规护栏（非投顾/AIGC 标识/内容安全前置闸/代币三不可/裂变/真金隔离） | `BLUEPRINT.md` §五+§五补 | 生死线 7 项+§五.4 协议条款升格在册 |
| 3 | 服务器与对外发布（服务器律 v2/release-gate） | `BLUEPRINT.md` §七 | 引用 `cph4/server-governance.md`+`release-gate.md` v1.0 |
| 4 | 大厅与城市面（WebSocket/census 白名单/化身 intake/只读 API） | `docs/spec/lobby-websocket-spec.md` | v0.2·AC-S1..S13 沙箱自验 13/13 |
| 5 | 代币内循环账本（双式记账/两恒等式/结构性禁令） | `docs/spec/token-ledger-spec.md` | AC-L1..L11+LP1..LP4 沙箱 11/11 |
| 6 | UGC 管道（三层筛选/msgSecCheck 前置/灰区永挂/编年史） | `docs/spec/ugc-pipeline-spec.md` | AC-U1..U12+UP1..UP5 沙箱 12/12 |
| 7 | 19.9 支付（双通道/订单状态机/法币代币双域隔离/对账） | `docs/spec/payment-integration-spec.md` | AC-Y1..Y14+YP1..YP6 沙箱 16/16 |
| 8 | 会员权益/月卡（两域隔离/出生证永久/手动续费 MVP） | `docs/spec/membership-spec.md` | AC-M1..M16+MP1..MP6 沙箱 16/16 |
| 9 | 激励分配层（参数+公示+协议三面·20/30/10 呈批） | `docs/spec/incentive-agent-spec.md` | AC-I1..I13 结构 13/13·参数 [needs-CEO] |
| 10 | 调研律（面声明/结论应用表/源分级） | `docs/research/README.md`+R-件 3 份 | 引用 `cph4/research-protocol.md` v1.0·存量指针 7 |
| 11 | 全球基准面（微信生态/支付合规/会员对标） | `docs/global-benchmarks.md` | 下次刷新 2026-09-29（P-74）·U195 四列口径吸收=刷新轮待办 |
| 12 | 自迭代 mandate（开轮五步/空转快道/铁律/P-32 两步） | `src/os/iteration_prompt.txt` | 现役（L6/L19 两处回落标记见 §四） |
| 13 | 单实例锁（D-20260925-03 PID 范式） | `src/os/iteration_loop.ps1`+`src/os/test_lock.ps1` | 接管窗 30min=1.2×轮预算·AC-D03 10/10 |
| 14 | 计划任务注册（BigDomain-OSLoop·:x4 车道） | `src/os/register_loop_task.ps1` | 幂等 -Force·10min beat |
| 15 | 任务双板（正典板+认领板·双板律） | `tasks.md`+`src/os/backlog.md` | 六件同源起版·完成态两板同步 |
| 16 | 轮账本（tick/log/基线时钟） | `src/os/state.json` | append-only·三基线字段+benchmarks_refreshed |
| 17 | CEO 上行面（P-32 日清/回执） | `HQ-FEEDBACK.md` | P0/P1/P2 行级追加 |
| 18 | 司令台账 | `orders.md` | 只追加（顶行基线 2026-09-24 13:57） |
| 19 | 观测窗接口（P-61） | `docs/status-export.json` | F3 律全派生·export_ts 24h 新鲜度闸 |
| 20 | 用户增长部（L1·P-76 设立） | `BLUEPRINT.md` §六注记+`docs/research/R-20260924-fan-growth-funnel.md` | 三线分工+漏斗四段承接映射在案 |

## 二、同义簇归并（U188 判例一·7 簇）

| # | 簇（同一规则多文件散布） | 散布面（归并前） | 唯一权威指针 |
|---|---|---|---|
| 1 | 内容安全前置闸（msgSecCheck·未接禁开门） | §五.3+五件套闸面 AC（S4/L8/U2/Y8/M7）+benchmarks ②-3 | `BLUEPRINT.md` §五.3（法文层）→各 spec AC（执法层） |
| 2 | AIGC 生成标识全呈现面 | §五.7+五件套 AC（S5/L9/U7/Y9/M8）+benchmarks ②-4 | `BLUEPRINT.md` §五.7 |
| 3 | 非投顾 disclaimer 常驻 | §五.1+AC（Y10/L10/M9）+benchmarks ②-6 | `BLUEPRINT.md` §五.1 |
| 4 | 判据预注册先行（诚实律） | mandate 铁律+六 spec AC 表+test_lock AC-D03+benchmarks 三件齐备 | `src/os/iteration_prompt.txt` 铁律·诚实律条 |
| 5 | [needs-CEO] 只呈批不越权 | mandate 铁律 P1 条+六 spec/config 呈批面+backlog blocked 项 | `src/os/iteration_prompt.txt` 铁律·P1 呈批条 |
| 6 | 零 token 服务器律（生产面永禁跑 LLM） | §三自进化注记+lobby spec §五+`server-city` §3 引用链 | `BLUEPRINT.md` §三 自进化注记 |
| 7 | 法币/代币双域隔离 | §五.4+token-ledger §五+AC（Y7/M10/M11）+benchmarks ②-5 | `BLUEPRINT.md` §五.4（法文）→token-ledger spec §五（结构） |

## 三、冲突终谳清单（U188 判例二·AC-C3·5 条）

| # | 两说 | 终谳（唯一有效口径） | 状态 |
|---|---|---|---|
| 1 | 智能体计数：§三=七大智能体（P-62 计数卫生·表实 7 行）vs §八 Phase 0「六智能体差距清单」+§九 接线表行 5「六智能体底座挂载」 | **七大**（§三 权威·2026-09-24 P-62 拍板）；两处残留=旧计数叙述行——R12 计数卫生注记「仓内唯一引用处」覆盖面=「六大智能体」精确字样·两处「六智能体」系本轮 GL204 grep 补检新检出 | 本轮终谳·原行保全不删改·以本行为准 |
| 2 | 服务器律演进：§七 v2 现行 vs §十条目 1 划线历史（A/B 裁决+再演进注记） | 服务器律 v2（§七 权威·2026-09-24 午后 CEO 令废止死命令）·§十划线行=演进链记录非现役法 | 已终谳同件自洽（R2 巡检批改写） |
| 3 | 观测付费归属：§四注记（D-10）vs §八补二交叉点表 BigMoney 行 | 19.9 算力包族归本司·履约引擎=BigMoney·出口=BigCompute（D-10 原文·助能链行已按其改写） | 已终谳 R12（同件两说已修） |
| 4 | 直播号归属：§四直播业务行 vs 账号运营面 | 每平台唯一账号=BigStream 资产面·开播执行=BigCompute 直播运营部·本司零开号零管号（D-08 同号口径） | 已终谳 R12（注记在案·全仓无反述） |
| 5 | 无人值守挂播：§四形态 1 vs 平台政策（封禁级） | 改有人值守·开播策略以 BigCompute 风控为准（patrol-4 E2③+risk-register E1） | 已终谳 R1（封禁级注记在案） |

## 四、过时回落清单（U188 判例三·AC-C2·7 条·原文保全=标记非删除）

| # | 原文位置 | 过时内容 | 回落判定 | 现行权威指针 |
|---|---|---|---|---|
| 1 | `src/os/iteration_prompt.txt` L6 | 定位节名「§七零服务器红线」+「已裁决=方案 B」注记 | 已回落 | §七=服务器律 v2（`BLUEPRINT.md` §七·旧法名随死命令废止） |
| 2 | `src/os/iteration_prompt.txt` L19 | 优先级条款「P-47 业务件五件按序」（五件 2026-09-24 R14 全件收口） | 已超越（完成态） | 现役活面=`src/os/backlog.md` 顶行（双板律）·条款尾部纪律（四件套/沙箱先行/闲时台账）仍立 |
| 3 | `iteration_prompt.txt` L19+`docs/spec/lobby-websocket-spec.md` L12+`docs/spec/payment-integration-spec.md` L17 | 「无服务器期」术语 3 处 | 已回落（术语） | 义保留=生产开闸前本地沙箱先行（CEO 物理件 gated）·术语正典=服务器律 v2（无「禁做期」概念） |
| 4 | `src/os/README.md`（代建报告·历史快照件） | 「单实例锁 15min 陈旧接管」+六件清单+「本仓现无 .gitignore」+state 字段清单 | 已超越（快照） | 锁律=D-20260925-03 PID 范式（`iteration_loop.ps1` 现役·30min 窗·AC-D03 10/10）·src/os 现役 7 件（+test_lock.ps1）·.gitignore 在册（R2/R7/R9）·state 含 benchmarks_refreshed |
| 5 | `README.md`（根）「## 结构」块 | 开线日快照（仅列 2 件） | 已超越（快照） | 现役全域结构=本索引 §一（域入口指针行已追加） |
| 6 | `docs/research/README.md` §一引导句 | 「开线至今零独立 R-件」（R20 时点真） | 已超越（时点陈述） | 现役 R-件 3 份在盘（user-value-paths/eigen-product-face/fan-growth-funnel）·存量指针表 7 行仍有效为记录 |
| 7 | `docs/global-benchmarks.md` §④ 首行 | 「下次到期=2026-10-01」（v0.1 首版记录行） | 时限态回落（同件已自记） | 现值=2026-09-29（§④ P-74 压缩行终谳·web 直采刷新轮 09-29 前触发） |

> T2/T1 否决窗到期项过闸点名：截至 2026-09-25 **无已过期未处理窗**（在册窗=research-protocol T2→10-01/流转提速律 T1→10-02/P-74 T1→10-01·到期后随轮扫描自然回落入本表）。

## 五、清理整合报告（AC-C4·四计数·随 09-30 治理日 U178 首窗呈 CEO）

- 冗余并簇数=**7**（§二）
- 冲突终谳数=**5**（§三·1 条本轮新检出终谳+4 条在案归档）
- 过时回落数=**7**（§四）
- 指针化计数=**39**（§一 20+§二 7+§三 5+§四 7·每行一条权威指针）
- 上位吸收在案：本司规则面全数引用集团正典（`cph4/` server-governance/research-protocol/release-gate/global-vision/cadence/decision.md）·零复制零双建（跨仓写禁令+反重复律同源）
- AC-C5 自验（2026-09-25 OSLoop R158）：清理范围规则文档 git diff=**0 删除 0 改写**——BLUEPRINT/tasks/iteration_prompt/src-os-README/六 spec/research-README/global-benchmarks 零触碰（diff 无条目）·README=纯追加 2 行（分隔空行+域入口指针行）+新增本索引件 1；轮内另有 HQ-FEEDBACK P2 更新 1 条=P-32 上报机制动作非清理动作、state.json/backlog=轮账本与工作板常规记账（豁免类）。原行保全零违·commit 可证。

## 六、更新记录

- 2026-09-25 v1.0 首版（GL204 执行·OSLoop R158·提前 4 天）：索引 20+簇 7+终谳 5+回落 7+四计数；新检出=「六智能体」计数残留 2 处（BLUEPRINT §八/§九）；09-30 治理日呈报=当日轮随行呈送本件 §五。
