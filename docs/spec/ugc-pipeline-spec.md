# 硅基域 UGC+msgSecCheck 管道设计 v0.1（业务 API 五件之三·判据预注册版）

> 溯源：ledger P-2026-09-24-47 ②@BigDomain（业务 API 五件之三）+P-2026-09-24-53①（全速五件·自报 AC 证据随 commit）；BLUEPRINT §五补（UGC 总纲·全集团开放·统一三层筛选）、§三智能体1/3（聊天挖掘/游戏共创）、§四 C0（免费围观付费入城）与共创分成机制、§五.1/3/7（合规生死线三件）；闸件复用=本仓 `src/sandbox/lobby/sec_gate.py`（同仓自产件·import 引用不复制·先例=ledger 件）；事件方言/存储纪律=`docs/spec/lobby-websocket-spec.md` §二（六字段核超集+evt_id·本仓单库 SQLite WAL 分表·单写者）；奖励过闸核联动=`docs/spec/token-ledger-spec.md` AC-L8/L9；回流通道与零 token 服务器律=`cph4/research/R-20260924-server-city.md` §2/§3（引用不复制）。
> 本件性质=设计先行（判据预注册先于实现·诚实律）；沙箱实现件=P-47-3b（次件·§三）。**本件=五件中唯一真实外部 API 触点（msgSecCheck）——三问门自检见 §〇**。

## 〇、定位与边界

- UGC 管道=全集团用户共创入口的**机制面**（§五补「UGC 不是某条业务线的功能，是全集团的用户共创入口」）：采集→安全闸→分类→整理→终审→权益，一条管线服务六业务线；提案池=分流终点，各线自取消化（**反重复律：用户脑洞是增量，不是替代 AI 产线**）。
- **三层筛选正典映射**（§五补）：L1 AI 初审=闸1 内容安全（生产=msgSecCheck/沙箱=违禁词+灰区词表）+闸2 非投顾词表+分类路由；L2 AI 整理=提案池入档+整理初版；L3 终审=状态机 final_review——落地级=[needs-CEO] 呈批**永不自动采纳**（P1 级只呈批），小创意 L0 自决（配置阈值）。
- **前置闸生死线**（§五.3）：未接内容安全=UGC 管道禁开门——serve 拒启 `E_GATE_OFFLINE`（与大厅 AC-S4/账本 AC-L8 三件同源）；大厅+直播弹幕先接 msgSecCheck 再开门。
- **三问门自检（msgSecCheck·如实过门）**：①必要=合规强制（§五.3 生死线+微信平台内容安全规则·本地词表 mock 不满足合规）②无本地替代=平台合规接口（平台侧判定义务不可自免）③CEO 授权=账号域物理件（小程序/公众号资质）**未到=不接线**（AC-UP1 blocked·账号域永不代办）。结论=过门但 blocked——现状如实：沙箱 mock 闸，生产接线待物理件。
- **零 token 服务器律**（server-city §3 引用）：管道服务器面永禁跑 LLM——AI 整理层 v0.1=规则+模板起版（producer=rule_template）；LLM 升级位预留=本地 LLM 离线批→git 只读通道入服（producer=local_llm·另呈批·不在本件范围）。
- 发入口须入城凭证（§四 C0 免费围观付费入城·与大厅 AC-S2 同源）；`avatar.register` intake 面=围观可受理（公面·AC-S12 同源·T-04 受理归 BigLife）。

## 一、判据预注册（验收判据先于实现——实现件按本表逐条对验·失败如实记负）

### 沙箱判据（U 系·本地原生 Python 可全验·不依赖 Docker）

| # | 判据 | 验法 |
|---|---|---|
| AC-U1 | 单管线多入口统一受理：`ugc.submit`（直提）+大厅 `idea.submit` 分流件（lobby AC-S10 stub 的真消费方·单库分表读取）+`avatar.register` intake 面（AC-S12 引用）→统一过闸→落 UGC 事件行（六字段核超集+evt_id）+受理回执（含 evt_id）；source 枚举=direct/lobby_idea/avatar_intake/live_danmaku（弹幕=预留位·AC-UP3 推流桥后启用）；发入口须入城凭证（围观态=拒 `E_ENTRANCE_REQUIRED`·AC-S2 同源），intake 面围观可受理；直提速率限=大厅 AC-S9 同参数（配置驱动·超限 `E_RATE_LIMIT`） | 各入口正反例+凭证反例断言 |
| AC-U2 | 前置闸自检：闸配置缺失/未接线=serve 模式拒绝启动 `E_GATE_OFFLINE`（三件同源：AC-S4/AC-L8）；沙箱闸=词表 mock（import 引用 `sec_gate.py`·同仓复用不复制） | 启动自检+词表正反例 |
| AC-U3 | 灰区人工复核通道：灰区件（沙箱=配置 gray 词表；生产=msgSecCheck suggest=review）→落 review_queue 状态挂起（不入池·不放行·不产生初版·零回执）；复核裁定 pass→过闸入流/risky→拒 `E_CONTENT_REJECTED`；**无裁定=永挂起（默认不放行）**；裁定留痕（裁定者/时间/结论） | 灰区件注入+两向裁定用例 |
| AC-U4 | 分类路由：过闸净件按配置路由六业务线（biggame/bigmoney/bigstream/biglife/fluxverse/bigdomain）+unsorted 兜底；路由=配置数据件驱动（改配置不改代码）；bigdomain 线产物=决策轮提案面（P1 只呈批） | 六线各一例+unsorted 例+改配置重路由例 |
| AC-U5 | 水帖过滤：噪音规则（纯表情/超短/重复灌水·配置驱动）→noise 档：原始事件行保留（诚实律：只分流不销毁）·不入提案池·不产生初版 | 噪音正反例断言 |
| AC-U6 | 幂等去重：同源同内容二投=拒 `E_DUPLICATE`（evt_id 内容寻址 UNIQUE·与 AC-S7/AC-L3 同法）；跨源同内容=两行+`duplicate_of` 标记（整理层去重档） | 重复投递断言 |
| AC-U7 | 整理初版诚实标识：draft 带 `producer`（rule_template/local_llm/human·服务端权威·客户端传值忽略）；`ai_generated=true` **当且仅当** producer=local_llm；沙箱=纯 rule_template（零 LLM·零 token）；LLM 升级=本地离线批（服务器面永禁 LLM） | 字段断言+伪造忽略断言 |
| AC-U8 | 非投顾双面：闸2 非投顾词表（禁收益承诺/保本保收益·复用 lobby `advisory_ban_words`）对一切 UGC 入口生效；提案池/编年史查询响应带 `disclaimer` 固定字段（常驻非折叠——用户创意为研究/创作思路·非投资建议·采纳与否与收益无关） | 词表正反例+响应体断言 |
| AC-U9 | 终审状态机：pooled→drafted→final_review→{adopted（终态）\|rejected→chronicled（终态）\|needs_ceo_review（呈批支路→裁定→adopted\|rejected→chronicled）}；**落地级件（越配置呈批阈值）永不自动 adopted——自动标记 needs_ceo_review 走呈批**；小创意 L0 自决=阈值内；状态迁移合法性=库层触发器执法（终态不可回退·needs_ceo 件 adopted 前必须有呈批回执行） | 状态迁移断言+越权自动采纳注入=拒 |
| AC-U10 | 过闸回执纪律：gate_receipts 只为 gate=pass 件开回执（risky/review 挂起/noise/未采纳=零回执）——回执=账本 share 发放的 ref 消费面（AC-L8 联动·reconcile check6 同源）；坏 ref 发放在账本件拒（跨件联验） | 回执正反例断言 |
| AC-U11 | 跨仓零写：回流=导出件三面落本仓 export 目录（proposal_feed/chronicle/hot_index·git 只读通道语义同源 server-city §2·各线自取）；**路径闸：导出目录配置越出本仓=拒启**（与 E_GATE_OFFLINE 同族启动自检） | 导出件落盘断言+越仓路径拒启断言 |
| AC-U12 | 城市编年史：全终态件（adopted+chronicled·「未采纳也进城市编年史」§五补）→chronicle.jsonl（evt_id+创意摘要+裁定+署名位）；rejected 零代币零署名承诺（只编年史） | 导出断言 |

### 生产判据（UP 系·预注册不预执行·blocked on CEO 物理件/合规定稿）

| # | 判据 | 阻塞依赖 |
|---|---|---|
| AC-UP1 | msgSecCheck 真实接线：资质=CEO 物理件（小程序/公众号·账号域永不代办）；出参 suggest 三态映射 pass→过闸/review→复核队列/risky→拒（接口现役细节以接线轮平台文档实勘为准·本件只锁三态映射与前置闸纪律）；未接线=管道禁开门 | 物理件：平台资质 |
| AC-UP2 | 人工复核运营就位：复核员/时限 SLA/复核记录留存 ≥6 个月（等保口径·与 AC-P4 同源） | 运营面+等保 |
| AC-UP3 | 直播弹幕 UGC 面：弹幕先接 msgSecCheck 再开门（§五.3）——随 FluxVerse 推流桥接线（本件只预留 source 位·不预实现） | 推流桥（FluxVerse 面外件） |
| AC-UP4 | 法务定稿：UGC 社区条款/用户协议/内容安全呈报随平台上线（BLUEPRINT §十一）；实名与未成年人合规扣与 AC-LP3 联动 | 法务（集团呈批面） |
| AC-UP5 | 热门 UGC→BigStream 素材线：hot 判定（配置分值）→hot_index 导出件生产接线（BigStream 自取） | 各线消化面就位 |

## 二、管道规格

### 管道顺序（顺序即宪法·大厅闸管道同族扩展）
```
intake（direct/lobby_idea/avatar_intake/live_danmaku*）
→【闸1 内容安全：msgSecCheck（生产）/违禁词+灰区词表（沙箱）→pass|review|risky 三态】
→【闸2 非投顾词表（复用 lobby advisory_ban_words）】
→【分类路由：六业务线+unsorted（配置驱动）】
→【水帖过滤：noise 档（只分流不销毁）】
→ pooled（提案池·六线分档+unsorted）
→ drafted（整理初版：规则模板·producer 诚实标注·零 LLM）
→ final_review（小创意 L0 自决｜落地级 needs_ceo_review 呈批）
→ adopted（→账本 share 发放=AC-U10 过闸回执纪律+署名/世界印记回流体）｜rejected
→ chronicled（全终态进城市编年史）
```
\*live_danmaku=预留 source 位（AC-UP3 接推流桥后启用）。

### 三层筛选正典映射（§五补）
| 层 | 本件机制面 |
|---|---|
| L1 AI 初审 | 闸1+闸2+分类路由（聊天挖掘智能体机制面·§三智能体1「过滤水帖→归类入提案池」） |
| L2 AI 整理 | 提案池入档+整理初版（规则模板起步·LLM 离线升级位=另呈批） |
| L3 终审 | final_review 状态机：小创意 L0 自决（阈值配置）/落地级 needs_ceo_review 呈批（P1 只呈批·不代办） |

### Schema（SQLite·本仓单库分表·与大厅事件/账本同库·WAL 单写者纪律同源）
```sql
CREATE TABLE ugc_events (      -- 原始受理行（六字段核超集+evt_id·与大厅事件方言同法）
  evt_id   TEXT PRIMARY KEY,   -- 内容寻址（source+actor+content 摘要·sha256·AC-U6 UNIQUE）
  ts_utc   TEXT NOT NULL, type TEXT NOT NULL,
  actor    TEXT NOT NULL,      -- census 化身 ID（账户绑定纪律=AC-L11 同源）
  repo     TEXT NOT NULL,      -- 'domain/BigDomain'
  zone     TEXT NOT NULL,      -- source 枚举（direct/lobby_idea/avatar_intake/live_danmaku）
  summary  TEXT NOT NULL       -- 超集字段载体：content/gate/route/noise 标记等
);
CREATE TABLE ugc_items (       -- 状态机主体（1:1=evt_id）
  item_id  TEXT PRIMARY KEY, line TEXT NOT NULL,
  state    TEXT NOT NULL CHECK (state IN ('pooled','drafted','final_review',
              'needs_ceo_review','adopted','rejected','chronicled')),
  gate_status TEXT NOT NULL CHECK (gate_status IN ('pass','review','risky')),
  producer TEXT NOT NULL DEFAULT 'rule_template'
              CHECK (producer IN ('rule_template','local_llm','human')),
  ai_generated INTEGER NOT NULL DEFAULT 0,   -- =1 iff producer='local_llm'（服务端权威）
  needs_ceo INTEGER NOT NULL DEFAULT 0,      -- 越呈批阈值自动标（AC-U9）
  duplicate_of TEXT, decision TEXT, ts_utc TEXT NOT NULL
);
CREATE TABLE review_queue (    -- 灰区人工复核（AC-U3）
  evt_id TEXT PRIMARY KEY,
  verdict TEXT CHECK (verdict IN ('pass','risky')),   -- NULL=挂起
  reviewer TEXT, ts_utc TEXT NOT NULL
);
CREATE TABLE gate_receipts (   -- 过闸回执（AC-U10·账本 AC-L8 的消费面）
  evt_id TEXT PRIMARY KEY, gate TEXT NOT NULL, ts_utc TEXT NOT NULL
);
-- 触发器：状态迁移合法性（终态不可回退）+needs_ceo 件 adopted 前必须存在呈批回执行（AC-U9）
```
- API 面（沙箱 stub）：`ugc.submit`（入城凭证校验+双闸+路由）/`ugc.pool_query`（含 disclaimer·AC-U8）/`ugc.review_verdict`（复核裁定）/`ugc.export`（导出三面）。
- 配置数据件：`src/sandbox/ugc/config.json`（编码律：中文文案/路由词表/灰区词表/噪音规则/呈批阈值外置 JSON·阈值与分值占位标 [needs-CEO]）。
- 沙箱机械表（P-47-3b 实现注记·判据零变更）：`ugc_ingest_log`（分流件幂等登记）/`ugc_entrance`（mock 入城凭证·生产=P-47-4 支付回执）/`ugc_drafts`（整理初版载体）/`ceo_receipts`（呈批回执行·AC-U9 触发器依赖）——四判据表照本节原样落码，机械表只承载机制；触发器执法面四条：入池态锁定（INSERT 非 pooled 拒）/合法迁移图+终态不可回退/落地标记走合法图两跳并在单事务（进 needs_ceo_review 后 needs_ceo 冻结不可清标）/回执只对 adopted 开。

### 回流件（跨仓零写·导出三面·各线自取消化）
- `proposal_feed/<line>.jsonl`：过闸+drafted 提案池导出（Biggame 排产/BigMoney 回测/BigStream 选题/BigLife 人设/FluxVerse 承建/BigDomain 决策轮——各线自取·反重复律）。
- `chronicle.jsonl`：全终态编年史（AC-U12·「你的脑洞被城记住了」）。
- `hot_index.jsonl`：热门件索引（生产接 BigStream 素材线·AC-UP5·沙箱=分值排序导出）。

## 三、沙箱骨架实现规格（P-47-3b 执行面·本轮只注册不实现）
- 件清单：`src/sandbox/ugc/`：`pipeline.py`（intake→双闸→路由→水帖→池→初版→状态机）·`store.py`（SQLite 分表+导出三面+路径闸）·`review.py`（复核队列+裁定 stub）·`test_ugc.py`（AC-U1~U12 逐条断言·含越权采纳/坏回执/越仓路径注入组）·`config.json`（数据件·占位标 [needs-CEO]）。
- 闸件复用：import 引用 `src/sandbox/lobby/sec_gate.py`（同仓自产件·sys.path 先例=ledger 件·不复制）。
- 依赖零外采：标准库为限（三问门：msgSecCheck 过门但 blocked on 物理件·沙箱零外接）。

## 四、合规四件套自检（每设计件必含·本件对照）

| 件 | 本件落位 |
|---|---|
| ① 判据预注册 | §一 AC-U1~U12+AC-UP1~UP5（先于实现注册） |
| ② AIGC 生成标识面 | AC-U7 `producer` 诚实标注+`ai_generated` 服务端权威（=1 iff local_llm）+整理初版呈现标识 |
| ③ msgSecCheck 前置闸 | AC-U2 未接线拒启+AC-U3 灰区复核通道+AC-UP1 真实接线+AC-U10 过闸回执纪律 |
| ④ 非投顾风险提示常驻面 | AC-U8 闸2 全入口生效+池/编年史查询 disclaimer 常驻字段 |

## 五、红线与不做清单（Non-goals）
- 反重复律：提案池=增量不替代生产线（§五补·各线自取消化·禁双建）。
- 不代办 CEO 终审（落地级=needs_ceo_review 呈批·P1 只呈批不执行）；不代办账号域（msgSecCheck 资质=CEO 物理件·永不代办）。
- 跨仓零写：回流只走本仓导出件（git 只读通道语义·server-city §2 同源）；越仓路径=拒启。
- 服务器面永禁 LLM（零 token 服务器律·server-city §3）；LLM 整理升级=本地离线批另呈批。
- 真金零触碰（真金面=BigCompute 唯一出口·引用其 BLUEPRINT 边界节）；代币发放只走账本件（AC-L8 联动·参数=[needs-CEO]）。
- 弹幕面=预留位不预实现（推流桥归 FluxVerse 线）。

## 六、生产开闸前置清单（物理件/定稿到位后依序）
平台资质（msgSecCheck 接线·AC-UP1）→ 人工复核运营（AC-UP2）→ 法务定稿（AC-UP4）→ 弹幕随推流桥（AC-UP3）→ **呈批开门（CEO 一句话·P1 级）**。

---
版本：v0.1（2026-09-24·OSLoop R6·判据预注册版）；修订记录：本件判据变更须先改本表再动实现（预注册纪律·否决窗随集团 T2 例）。
