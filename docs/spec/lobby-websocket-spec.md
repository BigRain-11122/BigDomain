# 硅基域交易大厅 WebSocket 规格 v0.1（业务 API 五件之一·判据预注册版）

> 溯源：ledger P-2026-09-24-47 ②@BigDomain（业务 API 五件之一）；BLUEPRINT §三（智能体1 聊天挖掘）、§四 C0-C3（入城门票/大厅增值）、§五合规护栏（生死线）、§七（零服务器红线=已裁决 B 自建后端）；事件方言=集团 `cph4/research/R-20260924-infra-2-events.md` §4 P3（公共面事件=内部六字段核+evt_id 超集·SQLite WAL 主案）。
> 本件性质=设计先行（服务器未购/CEO 物理件未到·BLUEPRINT §七：开发与物理件并行）；沙箱骨架代码=P-47-1b（次件）。**判据预注册=先定验收判据再动手（诚实律·本 §一 先于一切实现存在）**。

## 〇、定位与边界

- 大厅=交易大厅实时消息面（聊天/行情讨论/灵感/氛围/共创入口），**非投顾**（§五.1 生死线：卖的是 AI 算力与验证服务·不是投资建议·结果=历史回测研究展示）。
- **免费围观，付费入城**（§四 C0）：围观=只读连接（收广播）；入城（19.9 算力包或任意付费件=出生证）→ 才可发言/共创/交易。入城户籍=census 注册面复用（引用 BigLife census 正典·不复制）。
- 红线护栏（§七裁决 B）：公共商业面自建后端允许；**内部面功能永禁迁上本服务**（FluxVerse world/ 直写/内部总线/内部件一律不进）。
- 无服务器期=本地沙箱（docker-compose）先行实现与验证；生产开闸另过 §六 前置清单（P1 级=只呈批）。

## 一、判据预注册（验收判据先于实现——实现轮按本表逐条对验·失败如实记负）

### 沙箱判据（S 系·本地可全验·不依赖 Docker 在机：compose 缺位=本机原生 Python 同判据直跑）

| # | 判据 | 验法 |
|---|---|---|
| AC-S1 | 客户端连 `ws://localhost:8091/ws` 握手成功；服务端首条=`sys.hello`（协议版本/房间列表/风险提示文案指针） | 测试客户端断言首帧字段 |
| AC-S2 | 围观态（无入城凭证）可收广播不可发：发 `chat.send`→拒 `E_ENTRANCE_REQUIRED`，不广播 | 双客户端对照（一入城一围观） |
| AC-S3 | 入城态（沙箱 mock 凭证 `pay.grant_sandbox`）发 chat 经安全闸→全房间广播；本机往返 ≤500ms | 时间戳断言 |
| AC-S4 | 安全闸（沙箱=违禁词表 mock 闸）命中→拒 `E_CONTENT_REJECTED`，不广播、不落公共事件流；**闸配置缺失/未接线=serve 模式拒绝启动**（前置闸自检·§五.3 未接内容安全=禁开门） | 启动自检用例+词表正反例 |
| AC-S5 | AI 生成消息（居民台词/AI 整理产物/AI 系统发言）体带 `ai_generated:true`+呈现标识字段；人工消息该字段服务端权威覆写 false（客户端传值忽略·不可伪造） | 消息体断言 |
| AC-S6 | 连接建立即下发 `sys.risk_warning`（非投顾定性+风险提示常驻文案）；本规格要求前端常驻渲染非折叠（生产验收项·本机验消息到位） | 首帧序列断言 |
| AC-S7 | 一切公共面事件落 SQLite WAL 单写者（BEGIN IMMEDIATE）；行=六字段核超集 `ts_utc/type/actor/repo/zone/summary`+`evt_id`（内容寻址·UNIQUE 去重）；按日导出 jsonl 兼容层可读 | 落盘行核验+重复 evt_id 二次插入被拒 |
| AC-S8 | 心跳 ping/pong 30s；60s 无 pong 服务端断开；100 并发连接 5 分钟稳定，广播 p95 ≤200ms（本机口径） | 压测脚本 |
| AC-S9 | 单连接 chat 限速 5 条/10s：超限→`E_RATE_LIMIT`；连续超限 3 次→临时禁言 60s（`sec.reject` 告知） | 限速用例 |
| AC-S10 | 消息分流：`chat`（大厅聊天）/`idea`（脑洞→提案池队列 stub·三层共创筛选第一入口）；沙箱=关键词路由 | 分流用例 |

### 生产判据（P 系·预注册不预执行·blocked on CEO 物理件）

| # | 判据 | 阻塞依赖 |
|---|---|---|
| AC-P1 | wss+TLS+域名；ICP 备案完成才可公网 serve | 物理件：服务器/域名/备案 |
| AC-P2 | msgSecCheck 真实接口接线（微信资质）+违禁词库+人工复核队列；未接线=大厅禁开门 | 物理件：小程序/公众号资质（账号域=CEO 物理件·永不代办） |
| AC-P3 | 入城凭证=真实 19.9 支付回执签发（对接 P-47-4 后换掉 mock） | 物理件：微信支付商户号+P-47-4 |
| AC-P4 | 日志留存 ≥6 个月（等保口径）；公测前等保测评呈报 | 等保 |
| AC-P5 | 云上 1000 并发压测广播 p95 ≤500ms | 服务器到位后 |

## 二、协议规格

### 传输与帧
- RFC 6455 WebSocket；生产 wss·沙箱 ws；JSON 单行帧·UTF-8。
- 消息封套：`{v, type, ts_utc, room, actor, payload, ai_generated, evt_id?, trace_id?}`。`ai_generated` 与 `actor` 为服务端权威字段（客户端传值忽略）。
- type 初版枚举：`sys.hello / sys.risk_warning / sys.notice / chat.send / chat.broadcast / idea.submit / room.subscribe / room.unsubscribe / sec.reject / err.rate_limit / pay.grant_sandbox`。
- 错误码表：`E_ENTRANCE_REQUIRED / E_CONTENT_REJECTED / E_RATE_LIMIT / E_ROOM_UNKNOWN / E_BAD_FRAME / E_GATE_OFFLINE`。

### 房间模型
- `lobby`（大厅主频道·默认）/`quant`（QUANT 城围观·回测演出事件流）/`cocreate`（共创房）；订阅制，跨房间消息不串流。

### 身份与入城
- 围观=匿名只读；入城=付费凭证签发 token（生产=支付回执；沙箱=mock）；凭证过期/吊销→降级围观态。入城动作接 census 户籍注册面（引用不复制·§四 C0）。

### 安全闸管道（顺序即宪法·三道闸串行）
```
connect → sys.hello + sys.risk_warning → room.subscribe
→ chat.send / idea.submit
→【闸1 内容安全：msgSecCheck（生产）/违禁词表（沙箱）+人工复核队列】
→【闸2 非投顾词表：禁收益承诺/保本保收益类表述（§五.1）】
→【闸3 速率限（AC-S9）】
→ chat.broadcast（全房间）→ 落盘（§事件方言）
```
- **闸 1 生产未接线=serve 拒绝启动**（自检 `E_GATE_OFFLINE`）——§五.3 生死线：未接内容安全=大厅/直播间禁上线。

### AIGC 生成标识（§五.7 全呈现面律）
- 居民台词/AI 整理产物/AI 系统发言一律 `ai_generated:true`+呈现层显著标识（「AI 生成」）；**标识从源头带**（消息级字段·服务端权威），不依赖前端后期补标；CityWatch/切片外流画面同源带标。

### 事件方言（对齐集团 R-20260924-infra-2-events §4 P3）
- 公共面事件行=内部六字段核 `ts_utc / type / actor / repo / zone / summary` 超集+`evt_id`（内容寻址去重）；`repo` 固定 `domain/BigDomain`·`zone`=房间名。
- 存储=SQLite WAL 单写者+UNIQUE(evt_id)+按日导出 jsonl 兼容层——与 P-47-2 代币双式账本同一存储纪律（本仓单库分表·账本 schema 归 P-47-2 件定）。

## 三、沙箱骨架实现规格（P-47-1b 执行面·本轮只注册不实现）
- 选型：首选 Python 3.11+ `websockets` 库（零编译·单文件可读·集团 Python 工具链亲和）；备选 Node `ws`。定夺判据=实现轮本机运行时可用性实勘。
- 件清单：`src/sandbox/lobby/server.py`（入口/闸/限速/心跳）、`sec_gate.py`（沙箱词表闸+非投顾词表）、`store.py`（SQLite WAL+evt_id+日导出）、`docker-compose.yml`（沙箱编排·可选）、`test_client.py`（AC-S1~S10 逐条断言）。
- 依赖零外采：标准库+websockets 为限；不接任何外部 API（三问门：无必要·无授权）。

## 四、合规四件套自检（每设计件必含·本件对照）

| 件 | 本件落位 |
|---|---|
| ① 判据预注册 | §一 AC-S1~S10+AC-P1~P5（先于实现注册） |
| ② AIGC 生成标识面 | §二 AIGC 节+`ai_generated` 服务端权威字段+AC-S5 |
| ③ msgSecCheck 前置闸 | §二 安全闸管道闸1+AC-S4+生产未接线禁开门 |
| ④ 非投顾风险提示常驻面 | §二 `sys.risk_warning` 常驻+AC-S6+闸2 禁收益承诺词表 |

## 五、红线与不做清单（Non-goals）
- 不代客实盘·不承诺收益（§五.1/2）；围观=看研究过程不是跟单。
- 代币不提现不外流（§五.4）——大厅内代币消息面归 P-47-2 设计件。
- 内部面功能永禁迁上本服务（§七护栏）。
- 真金执行面=BigCompute 唯一出口（ledger P-47 ③）·本件零触碰。
- 公网开门=P1 级只呈批（HQ-FEEDBACK/backlog 标 [needs-CEO]）·不自行上线。

## 六、生产开闸前置清单（物理件到位后依序）
ICP 备案 → wss/域名 → msgSecCheck 真实接线 → 支付回执凭证（P-47-4）→ 日志留存/等保测评呈报 → 云上压测（AC-P5）→ **呈批开门（CEO 一句话）**。

---
版本：v0.1（2026-09-24·OSLoop R1·判据预注册版）；修订记录：本件判据变更须先改本表再动实现（预注册纪律·否决窗随集团 T2 例）。
