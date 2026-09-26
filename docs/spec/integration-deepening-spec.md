# 硅基域 P-47 五件跨件集成设计深化件 v0.1（全用户旅程集成规格·判据预注册版）

> 溯源：集团 orders L220 禁待命·自主运转令（P-2026-09-26-03 ⑤派发本司面「BigDomain 等 M2→策略研究/设计深化/运营预演」）自驱单 BD-SD2（R267 认领·判据预注册=src/os/backlog.md 本行）；基础=现役五 spec（`lobby-websocket-spec.md`/`token-ledger-spec.md`/`ugc-pipeline-spec.md`/`payment-integration-spec.md`/`membership-spec.md`·判据在册 68 条全绿）+分配层件（`incentive-agent-spec.md` AC-I1..I13）+沙箱对接面行级实勘（本件 §二「沙箱实证」列=文件+行号在案）；事件方言=集团 `cph4/research/R-20260924-infra-2-events.md` §4 P3；城市面=`cph4/research/R-20260924-server-city.md` §0/§2（引用不复制）。
> 本件性质=**集成设计件**（非实现件非研究件）：五件间契约缝普查+全用户旅程串接+边界/故障/降级三面深化——**零推倒零双建**（本件零新代码件零新 schema 零新 API·全部缝引用现役件判据·反重复律）。

## 〇、定位与边界

- 五件现况=规格 5/5+沙箱 5/5 判据自验全绿（AC-S13+L11+U12+Y14+M16=68 条·R14 收口）——**集成缝在此之前只散在各件「对接面」注记里，未有一张缝登记总表**；本件=第一张跨件契约总表（普查+深化），为 bootstrap 生产接线（blocked on CEO 物理件）预铺接线图。
- 用户旅程主线（本件串接对象）：围观 → 入城 → 发言/共创 → 过闸采纳 → 分成/消费 → 到期续费（六段·§三）。
- 生产接线 blocked 面如实标注（§七归并）；本件不代办任何物理件/参数/呈批面（[needs-CEO] 纪律同五件）。

## 一、判据预注册（验收判据先于撰写——判据册=src/os/backlog.md BD-SD2 行·执行结果对验见该行 done 段）

| # | 判据 | 验法 |
|---|---|---|
| AC-SD2a | 对接面普查完备：跨件契约缝登记表每缝五列（生产者/消费者/载体接口/在册判据号/沙箱实证）齐；用户旅程六段每段所涉缝全在表；零凭空新缝零无判据缝 | §二表+§三表交叉断言 |
| AC-SD2b | 三面深化各一节：边界（三域隔离/判据源单点/库拓扑单写者）·故障（缝级模式-现役防线-残余处置）·降级（fail-closed 清单）——每条带出处（spec 节/判据号/沙箱件行级） | §四/§五/§六逐条出处断言 |
| AC-SD2c | 合规四件套跨缝自检节：AIGC 标识链五件+msgSecCheck 五件同源拒启+非投顾 disclaimer 常驻面清单+判据预注册 | §七结构断言 |
| AC-SD2d | 零推倒零双建：本件零新代码件零新 schema 零新 API——全部缝引用现役件在册判据 | §二判据列全非空+Non-goals 断言 |
| AC-SD2e | 送达三载体：commit 含 P-2026-09-26-03+backlog done 行+state log 一行（P-51 口径） | commit 消息 grep+板面/log 断言 |

## 二、跨件对接面普查（契约缝登记表·IF 系）

**沙箱实证=2026-09-26 R267 行级实勘**（证据在盘可复核；生产接线面以各件 AC-P/LP/UP/YP/MP 系为准）。

| 缝 | 契约面 | 生产者 → 消费者 | 载体/接口 | 在册判据 | 沙箱实证（件+行） |
|---|---|---|---|---|---|
| IF-1 | 身份链 | BigLife T-04 census（引用不复制）→ 全件 | `census_avatar_id` 同名字段贯穿：`usr:*` 账户绑定/订单/周期/事件 actor | AC-L11/AC-Y13/AC-M3/AC-S12 | ledger.py `ensure_account(usr:*, census_avatar_id=…)`；pay_orders.census_avatar_id；member_periods.census_avatar_id；ugc_events.actor |
| IF-2 | 入城凭证 | pay → lobby/ugc/member | `Pay.grants_for(avatar)` 查询面=入城判定**唯一真源**（发放机制归 pay·门禁执法归各入口） | AC-Y6/AC-S2/AC-U1/AC-M3 | pay/orders.py `grants_for()`（L621）；lobby/server.py `E_ENTRANCE_REQUIRED`（L181 chat.send/L247 idea.submit）；ugc 入城=沙箱 mock `grant_entrance_sandbox`（pipeline.py L153·生产=P-47-4 支付回执）；member.py 出生证判定源 `self.pay.grants_for(avatar)`（L447·judgement_source 注记） |
| IF-3 | 共创分流 | lobby → ugc | 同库 `events` 表 `idea.submit`/`avatar.intake` 行 → `ingest_lobby()` 分流消费+`ugc_ingest_log` origin_evt_id 幂等；防御纵深=ugc 重跑自家闸 | AC-S10/AC-S12→AC-U1 | ugc/store.py `lobby_intake_rows()`+`mark_ingest()`；ugc/pipeline.py `ingest_lobby()`（「the lobby already enforced entrance + gates upstream; this face re-runs its own gates anyway」注记） |
| IF-4 | 过闸回执 | ugc → ledger | `gate_receipts`（触发器只对 adopted 开）→ 发放笔 `ref=evt_id, ref_type='event'`+ledger 侧 `gate_events` gate='pass' 在册方可入账 | AC-U10/AC-L8（reconcile check6） | ugc/store.py `adopt_with_receipt()`（事务内开回执）；ledger.py `record_gate_pass()`（L152·沙箱替位=lobby 闸管道产物登记位）+`grant()` content_gate 强制查询（L260） |
| IF-5 | 换算桥（法币→代币·单向） | pay → ledger | `_grant()` pay 库事务内调 `Ledger.share_from_pool(pool, usr:*, tokens, ref=order_id, ref_type='order')`；代币数=服务端价目表换算列；`E_REF_DUPLICATE` 容忍=幂等愈合 | AC-Y6/AC-Y7/AC-LP1 | pay/orders.py L553 调用点+`_grant()` 注记（「a ledger failure rolls the whole grant back…UNIQUE(ref, ref_type) heals the reverse window on retry」）；ledger.py `share_from_pool()`（L280） |
| IF-6 | 权益激活 | pay → member | `pay_grants` 行=激活真实源（source_grant_id REFERENCES+归属同化身校验）→ 周期/次数/券三账 | AC-M1/M2/M3/M16 | member.py 激活验 grant；member/reconcile.py check1 伪造/孤儿周期点名（L88-91） |
| IF-7 | 事件方言 | lobby/pay/ugc → 公共流/回城 inbox | 六字段核+`evt_id` 内容寻址 UNIQUE·按日导出 jsonl=回城摘要源 | AC-S7/AC-Y14/AC-U6 | lobby/store.py events 表；pay/orders.py `_emit_pay_success()`（deterministic ts=重试同 evt_id）；ugc `compute_evt_id` |
| IF-8 | 安全闸单源 | lobby `sec_gate.py` → 五件 import | `E_GATE_OFFLINE` 拒启五面独立（一件坏不传染他件）+灰区 review_queue=ugc 域专有 | AC-S4/AC-L8/AC-U2/AC-Y8/AC-M7（五件同源） | import 实勘：ledger.py L36/ugc-pipeline.py L51/pay-orders.py L67/member.py L89/lobby-server.py L30 |
| IF-9 | 特权呈现 | member → lobby/ugc | 服务端裁权三面：发言高亮=lobby envelope 字段；共创优先筛选=ugc 入池排序权重（三层筛选零变更·永不绕审）；表情/皮肤=呈现层查 active 周期档位 | AC-M5/AC-M6/AC-U9 | member.py 特权查裁（零特权表·active 周期即权·「服务端裁权·客户端零话语权」） |
| IF-10 | 城市面 | city_data（git 只读 `:ro`）→ lobby read API/census 查询/avatar intake → BigLife T-04 | HTTP `/city/snapshot`·`/census/<id>`（白名单+`as_of`）+WS `census.query`/`avatar.register`→受理回执 | AC-S11/AC-S12/AC-S13 | lobby/city.py+city_data/（citizens-light.jsonl+world-public.json） |
| IF-11 | 导出回流（跨仓零写） | ugc → 六线（各线自取） | `proposal_feed/<line>.jsonl`/`chronicle.jsonl`/`hot_index.jsonl` 三面+越仓路径拒启 | AC-U11/AC-U12/AC-UP5 | ugc/store.py 导出三面+路径闸拒启自检 |
| IF-12 | 对账复验 | 三 reconcile+判据自验 | ledger 八查/pay 六查/member 六查·exit 0=PASS/2=FAIL·独立复跑=实验室复核入口（P-53② 防线二） | AC-L5/AC-L6/AC-Y12/AC-M14 | ledger/reconcile.py+pay/reconcile.py+member/reconcile.py 在盘·篡改注入族 exit2 在案 |

- 分配层件（incentive-agent）跨缝引用：路径②分成链=IF-4（ref 过闸核）+AC-U12 署名（确权=收益开关）；路径③参数公示=ledger config+AC-L7 cap；路径④身份权益=IF-1/IF-9——**零新管道**（AC-I2/I12 在册·本件不重复定义）。

## 三、全用户旅程串接（六段·J 系）

| 段 | 用户动作 | 件链（缝引用） | 判据锚 | blocked 面（如实） |
|---|---|---|---|---|
| J1 围观 | ws 连接→`sys.hello`+`sys.risk_warning`→订阅只读；参观城市快照/census | lobby（IF-8 闸源·IF-10 城市只读面·IF-7 事件流） | AC-S1/S2/S6/S11/S13 | — |
| J2 入城 | 19.9 下单→回调验签→granted（换算桥同笔）→出生证→入城判定开闸 | pay→ledger→member→lobby（IF-5/IF-6/IF-2/IF-1） | AC-Y1~Y6/AC-M3/AC-S2→AC-S3 | 商户号/服务器/备案（AC-YP1/AC-P1~P3） |
| J3 发言/共创 | chat 过三闸→广播→落事件；`idea.submit`→events 表→ugc 分流入池 | lobby→ugc（IF-3/IF-7/IF-8） | AC-S3~S10/AC-U1 | msgSecCheck 真实接线（AC-UP1·闸未接=拒启） |
| J4 过闸采纳 | 三层筛选（灰区挂起/落地级呈批）→adopted→回执→share 发放→署名+编年史 | ugc→ledger（IF-4/IF-1） | AC-U3/U9/U10/U12/AC-L4/L8 | 落地级 needs_ceo_review 呈批（P1 只呈批） |
| J5 分成/消费 | balance/bill（disclaimer 常驻）→特权消费 spend→次数消耗 | ledger/member（IF-5 回流池·IF-9 特权面） | AC-L7/L9/L10/AC-M4 | 参数首档=[needs-CEO]（AC-LP4/AC-IP1） |
| J6 到期续费 | sweep→expired（特权面全关+出生证保留）→续费=新订单新周期桶无缝叠续 | member→pay→lobby（IF-2/IF-6/IF-7） | AC-M12/M2/AC-Y3 | 自动续费能力【待证】（AC-MP1·MVP=手动续费） |

## 四、边界深化（职责分界·写权·库拓扑）

### 4.1 三域隔离（结构性双保险的集成视图）
| 域 | 唯一写权件 | 载体表 | 隔离判据（交叉断言） |
|---|---|---|---|
| 法币域 | pay | pay_orders/pay_receipts（amount_cent 唯一落点） | AC-Y7（金额零出订单域）+AC-M10（权益域零金额字段） |
| 代币域 | ledger | ledger_accounts/tx/entries | AC-M11（次数≠代币·权益域永不写账本）+token-ledger §五结构性禁令（无 withdraw/transfer-out 动词） |
| 次数域 | member | member_credit_events（append-only+Σdelta≥0 触发器） | AC-M11 双向（账本表零次数字段） |

跨域唯二通道：**IF-5 换算桥**（法币订单→代币 share·单向不可逆）与**IF-4 分成缝**（过闸事件→代币 share）——两缝均为「单向进代币域·代币永不回流法币」（§五.4 生死线）。

### 4.2 判据源单点律（防双写/防第二真源）
- 入城判定唯一真源=pay `grants_for` 查询面（lobby/ugc/member 三消费面只读引用·零副本缓存）。
- 价目唯一真源=服务端 config 数据件（AC-Y2 服务端定价律+AC-M1 目录唯一真源）；客户端携带金额/档位=拒或忽略。
- 身份唯一真源=census（T-04 引用·零新增身份系统）；`usr:*`/订单/周期/事件 actor 全件同名字段直引。
- 事件唯一真源=落库行（evt_id 内容寻址）——呈现面/导出面/回城面全派生自库行，零旁路直写。

### 4.3 库拓扑与单写者纪律
- 生产目标=**本仓单库分表·同一 WAL 单写者**（五件 spec §〇 同源纪律）；沙箱实况=lobby+ugc 同库（IF-3 events 表共享）+ledger/pay/member 各自库文件——**跨库缝仅 IF-5/IF-6**（pay↔ledger/pay↔member），其余缝皆同库或经导出件。
- IF-5 跨库事务序（沙箱实证·orders.py `_grant` 注记原文）：pay 库 `BEGIN IMMEDIATE` 包裹「pay_grants 插入+状态迁移+ledger 写入」于 COMMIT 前——ledger 失败=pay 整笔回滚（无「已付未发」窗）；反向窗（pay COMMIT 前崩溃而 ledger 已记）=重试路径 `E_REF_DUPLICATE` 容忍+`UNIQUE(ref, ref_type)` 幂等愈合。生产单库化后此序退化为同库单事务（接线更简·纪律不变）。
- 单写者=每域一个写者进程（三域+lobby 事件面各持 `BEGIN IMMEDIATE` 串行）；生产部署形态归 bootstrap 件（blocked 物理件·本件只锁纪律）。

### 4.4 跨仓边界（引用不复制）
- 回流=IF-11 导出三面（git 只读通道语义·路径闸执法）；城市数据=IF-10 git 只读 `:ro`。
- 真金/对外结算=BigCompute 唯一出口；外部渠道订单凭证回流权益面=**预留接口位**（blocked on BigCompute 通道定案·不代建）。
- census 受理/城市承建/署名券消费/房间皮肤池/加急执行/陪伴呈现=BigLife/FluxVerse/BigMoney 面（blocked 引用·membership §〇 诚实注记同源）。

## 五、故障深化（缝级故障登记：模式-现役防线-残余处置）

| 缝 | 故障模式 | 现役防线（在册判据/机制） | 残余风险与处置 |
|---|---|---|---|
| IF-2 | 已付未入城（判定源滞后/服务重启丢会话） | granted 原子（AC-Y6·无悬空窗）+出生证永久（AC-M3·判定源永不过期）+判定=只读查询零缓存 | 降级为围观态（非错误态）·重连即愈；AC-MP2 热数据=服务器面优化项 |
| IF-5 | 双窗崩溃（ledger 已记/pay 未 COMMIT；或反向） | `E_REF_DUPLICATE` 容忍+UNIQUE(ref,ref_type) 幂等愈合+ledger 失败=pay 回滚 | 两 reconcile 交叉点名（pay check5 换算笔核+ledger check5 ref 幂等）+日 cron 兜底（AC-YP3/AC-LP2） |
| IF-3 | 分流重复投递/处理中断 | `ugc_ingest_log` origin_evt_id 幂等+mark_ingest 全状态留痕（含 gate 拒收行·只分流不销毁） | 重启重入=零重复入池零重复发放（evt_id 同法去重） |
| IF-4 | 坏 ref 发放/未过闸内容入账 | `grant()` 强制 ref_type='event'+gate_events pass 在册（L260 查询）+回执触发器只对 adopted 开+reconcile check6 复扫 | 审计线=对账 FAIL exit2 点名·adjust 更正必带 memo |
| IF-8 | 闸半失效（一件闸配置坏） | 五面独立拒启（一件坏不传染他件·同名防线各自生效）+灰区无裁定=永挂起 | 运维=五面各自告警；禁「无闸降级运行」档（§六） |
| IF-6 | 重复激活/伪造 grant 源 | UNIQUE(化身,产品,周期序数)幂等（AC-M2）+source_grant_id REFERENCES+reconcile check1 伪造源点名 | — |
| J5/J6 | 到期扫描与消耗并发 | BEGIN IMMEDIATE 串行+到期后消耗拒 `E_PERIOD_EXPIRED`+sweep 幂等可重跑（AC-M4/M12） | — |
| IF-7 | 事件重复投递 | evt_id 内容寻址 UNIQUE 三件同法（AC-S7/L3/U6/Y14）+pay deterministic ts | — |
| 回调面 | 四坏回调/改价注入 | 验签+±300s 时窗+nonce+金额比对（AC-Y4）+UNIQUE(order_id,sig_ok) 幂等（AC-Y5） | 失败按上游重试语义应答·不误应答成功 |

## 六、降级深化（fail-closed 清单·无「静默放行」档）

1. 闸离线=**拒启非降级**（`E_GATE_OFFLINE`·五件同源）——生死线 §五.3：无「无闸运行」降级档。
2. 灰区复核积压=**永挂起**（AC-U3·无裁定=不放行）——无超时自动放行档。
3. census 源滞后=`as_of` 如实呈现（≤20min=异步生活感设计态非故障）；源断=旧快照+as_of 继续呈现·不伪造新鲜。
4. 会员到期=特权面全关+**出生证保留**（AC-M12/M3·入城资格永不降级收回）。
5. 消费面 blocked（陪伴/署名券/房间/皮肤/加急执行）=配额账+券账先立·下游到位接线（不预建不伪造可用态）。
6. BigCompute 外部回流=预留接口位·通道未定案不代建（零假数据）。
7. 城市数据 `:ro`：写试=拒（AC-S13）；intake 面外无任何写端点（405/404）。
8. 零 token 服务器律：LLM 整理升级=本地离线批→git 只读通道（服务器面永禁 LLM·producer=local_llm 另呈批）。
9. 直播弹幕=`E_SOURCE_BLOCKED` 预留位（AC-UP3 推流桥后启用·沙箱实证 pipeline.py `_validate_source`）。

## 七、合规四件套自检（跨缝呈现·本件对照）

| 件 | 跨缝落位 |
|---|---|
| ① 判据预注册 | §一 AC-SD2a~e+全部缝引用在册判据（AC-SD2d 零新判据面外判据） |
| ② AIGC 生成标识面 | **标识链五件**：lobby `ai_generated`（AC-S5·服务端权威）→ugc `producer`/`ai_generated`（AC-U7·=1 iff local_llm）→ledger `source_ai`（AC-L9·AI 判定发放审计）→pay `ai_service`（AC-Y9）→member `ai_generated`（AC-M8）——全缝「服务端权威·客户端伪造忽略」同律 |
| ③ msgSecCheck 前置闸 | **五件同源拒启**：AC-S4/L8/U2/Y8/M7（IF-8 单源 import 实勘在案）+发放链 ref 过闸核（IF-4）+未接线=禁开门（非降级） |
| ④ 非投顾风险提示常驻面 | **disclaimer 常驻面清单**：lobby `sys.risk_warning` 连接首帧（AC-S6）+ledger `bill`（AC-L10）+pay 支付确认/订单/收据三面（AC-Y10）+member 会员页/权益说明（AC-M9）+ugc 池/编年史查询（AC-U8）+分配层公示三面（AC-I9）——常驻非折叠·呈现面全锚「AI 算力与验证服务/历史回测研究展示·非投资建议·无收益承诺」 |

## 八、生产接线序（blocked 面归并·物理件到位后依序·P1 只呈批）

商户号+服务器/域名/备案 → msgSecCheck 真实接线（AC-UP1·五面换 mock）→ 支付真实回执=入城凭证换 mock（AC-P3/AC-LP1/AC-YP1 三面同窗切换）→ 单库化 bootstrap（§4.3 纪律不变）→ 日对账 cron 三件入夜报（AC-LP2/YP3/MP2）→ 等保留存 ≥6 个月 → 云压测（AC-P5）→ **呈批开门（CEO 一句话）**。

## 九、红线与不做清单（Non-goals）

- 零新代码件零新 schema 零新 API（AC-SD2d·本件=集成设计引用面）；不重构不推倒任何现役件。
- 不代办账号域/物理件/参数定值/呈批面（[needs-CEO] 纪律·AC-LP4 先例）；不预建 blocked 下游（BigCompute 通道/FluxVerse 承建面/BigLife 陪伴呈现）。
- 跨仓零写（回流只走导出件）；代币永不兑法币（三域隔离 §4.1 结构性保证）；真金面=BigCompute 唯一出口。
- 单库化/部署形态=bootstrap 件范围（本件只锁纪律与接线序·不越权设计部署）。

---
版本：v0.1（2026-09-26·OSLoop R267·禁待令自驱单 BD-SD2 判据预注册版）；修订记录：本件判据变更须先改 §一 再动对接面（预注册纪律·否决窗随集团 T2 例）；缝表增删=须先在 backlog 判据册扩 AC-SD2a 再改 §二。
