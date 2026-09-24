# 硅基域 19.9 支付对接设计 v0.1（业务 API 五件之四·判据预注册版）

> 溯源：ledger P-2026-09-24-47 ④@BigDomain（业务 API 五件之四）+P-2026-09-24-53①（全速五件·自报 AC 证据随 commit）；D2 类目代决 2026-09-24（**非游戏类目小程序+虚拟支付**·T1 否决窗至 10-01·依据=集团 `cph4/research/R-20260924-category-review.md` §0/§2/§5——本件轨道与费率全按其引用·不复制）；BLUEPRINT §四 C0/C1/C2（入城出生证/19.9 算力包/三档月卡）、§五.1/3/7（合规四件套同源）、§五.4（代币隔离生死线）、§五.6（实名/未成年）、§四分工注记（店内闭环 vs BigCompute 外部通道）、§十.2（物理件）、§十一（法务定稿）；对接面=`docs/spec/token-ledger-spec.md` AC-LP1（订单回执=账本真实触发源）+`docs/spec/lobby-websocket-spec.md` §事件方言（pay.success 入公共流·六字段+evt_id）+sec_gate（闸引用·先例=ledger/ugc）。
> 本件性质=设计先行（**商户号=CEO 账号域物理件未到·永不代办**·开发与物理件并行=BLUEPRINT §七）；沙箱实现件=P-47-4b（次件·§六）。**定价确认/退款政策/换算比例/道具命名=CEO=[needs-CEO]·本件只锁机制与不变量，数值与政策全走配置数据件呈批面**。

## 〇、定位与边界

- 本件=**店内闭环支付对接**（BLUEPRINT §四分工注记：本司价目全为店内闭环；外部成交通道归 BigCompute·引用其 BLUEPRINT 边界节不复制）。双通道：
  - **虚拟支付通道（C 端虚拟商品主通道·D2 轨道乙）**：19.9 算力包/三档月卡/大厅增值件等端内虚拟商品——**强制走小程序虚拟支付**（category-review §2.1 强制律：端内虚拟商品不得走标准支付=违规）·虚拟支付专用商户号（AppID/OfferID/AppKey·安卓 1% T+3/iOS 12-17% 口径差以 MP 后台签约页为准【待证】）。
  - **标准商户通道（B 端真实服务对照轨）**：入驻年费/包场/冠名/数据报告等真实服务与实物——标准微信支付商户 API（泛行业 0.6%·T+1·对公结算·category-review §2.3）。
  - 通道差异只落在适配器层（§二）；订单域机制面通道无关。
- 外部渠道回流：抖音小店/直播购物车/视频号小店=BigCompute 通道（引用不复制）；其订单凭证回流本司权益面=**预留接口位·blocked on BigCompute 通道定案**（不代建）。
- **法币域/代币域双域隔离**：法币金额只存在于订单域（§二 orders/receipts）；代币账本零法币字段（token-ledger §五 结构性禁令同源双保险）。桥=**订单回执换算笔**（ref=order_id·ref_type='order'·type=share·**单向法币→代币·不可逆**·换算比例=[needs-CEO] 配置数据件·MVP 面=共创分成类如观测费 30% 代币分成）——账本侧只记代币数与订单引用，永不记法币金额。**直购返代币默认不做**（法币→代币直兑面=虚拟币合规敏感·如需另呈批·不自我膨胀）。
- 身份=census 化身 ID 引用（AC-L11/AC-S12 同源·零新增身份系统）；**付费入城=出生证**（§四 C0：19.9 或任意付费件→入城资格）——发放产物即入城凭证，lobby `E_ENTRANCE_REQUIRED` 判据源=本件 grants 查询面（跨件引用）。
- 权益目录（三档卡内容/次数明细/有效期）=**P-47-5 件定**（本件只管订单→权益记录机制·不预录目录防重复）。
- 物理件清单（账号域=CEO 永不代办·§十.2）：虚拟支付专用商户号开通（MP 后台·审核 5-7 工作日·**iOS 苹果支付开关须手动开启**+先配小程序简称）+标准商户号（1-5 工作日·对公打款验证）+回调域名与 HTTPS（服务器/ICP 备案前置）+AppID/OfferID/AppKey/商户密钥——**密钥只进 .env 不入 git**（server-governance 密钥律）。
- 无服务器期=本地沙箱 **mock 双通道网关**先行（真实通道接口细节以官方文档为准·接线日对齐·本件不预写死端点【待证·诚实律】）。

## 一、判据预注册（验收判据先于实现——实现件按本表逐条对验·失败如实记负）

### 沙箱判据（Y 系·Y=yuan 法币域·本地原生 Python 可全验·不依赖 Docker·不依赖真实商户号）

| # | 判据 | 验法 |
|---|---|---|
| AC-Y1 | 订单状态机：`created→pending→paid→granted→closed`（终态=granted/closed）；非法迁移/跳态/终态回退=库层触发器拒（与 UGC 状态机同法）；金额下单后锁定（改 amount=拒） | 直迁/跳态/回退/改价注入=拒断言 |
| AC-Y2 | 服务端定价律：金额/档位唯一真源=服务端价目表（config 数据件）；客户端携带金额=拒 `E_PRICE_TAINTED`；未知商品=拒 `E_PRODUCT_UNKNOWN` | 伪金额/伪商品用例 |
| AC-Y3 | 下单幂等：order_id 内容寻址（化身 ID+商品 ID+序数桶·与 evt_id 同法）；同化身+同商品+同序数桶二次提交=同单返回不重开 | 重复下单断言 |
| AC-Y4 | 回调四坏拒：坏签名/未知签名者/时间戳出 ±300s 窗/nonce 重放=拒+零状态迁移；回调金额≠订单金额=拒（改价注入）。沙箱=mock 网关本地测试钥（假钥·真钥只 .env） | 四坏+改价回调用例 |
| AC-Y5 | 回调幂等：合法回调二投=单次生效（receipts UNIQUE(order_id)）；已 paid 再收=零重发放零改态、按上游重试语义应答 | 二投断言 |
| AC-Y6 | 发放原子性：paid→granted 单事务（订单状态+权益行+换算笔同笔）；失败=整笔回滚·无「已付未发」悬空窗；重试入口幂等 | 中途失败注入=回滚断言 |
| AC-Y7 | 法币隔离：金额字段零出订单域（跨件联验：换算笔只携带代币数+order 引用·任何法币字段注入账本=拒）；账本表零法币字段交叉断言 | schema 交叉断言+坏注入=拒 |
| AC-Y8 | msgSecCheck 前置闸：订单携带的一句话需求文本未过闸=拒受理 `E_CONTENT_REJECTED`（引用 lobby `sec_gate` 件不复制·先例=ledger/ugc）；闸未接线=下单面拒启 `E_GATE_OFFLINE`（lobby AC-S4/ledger AC-L8/ugc AC-U2 三件同源·本件第四件） | 正反例+拒启用例 |
| AC-Y9 | AIGC 标识：订单详情/收据响应带固定 `ai_service:1` 字段（所购=AI 生成服务·服务端权威·客户端伪造忽略）；履约产物（回测报告页/Demo）source_ai 标识由既有管线承接（引用不复制） | 字段断言+伪造忽略断言 |
| AC-Y10 | 非投顾常驻：支付确认/订单详情/收据三面响应体带固定 `disclaimer` 字段（AI 算力与验证服务·非投资建议·历史回测研究展示·无任何收益承诺）·前端常驻渲染非折叠 | 三面响应体断言 |
| AC-Y11 | 文案违禁词表：商品文案/道具名配置过闸（禁荐股三要素=个股买卖建议/点位目标价/收益承诺——category-review §4.2 反推红线）；违禁文案=拒配置拒上架 | 违禁文案上架=拒用例 |
| AC-Y12 | 对账：reconcile 六查（§三）干净 PASS exit0；篡改注入（改金额/伪发放/删回执/凭空换算笔）→FAIL exit2 | 干净跑+四类注入跑 |
| AC-Y13 | 身份绑定：订单必绑 census 化身 ID；无绑定=拒受理（出生证发放前提·AC-L11 同源） | 无绑定下单=拒 |
| AC-Y14 | 事件方言：pay.success 落公共流（六字段核 `ts_utc/type/actor/repo/zone/summary`+evt_id 内容寻址 UNIQUE·R-2 §4 P3 同法·repo=`domain/BigDomain`·zone=`pay`）→ 重复 evt_id 二次插入被拒 | 落盘断言+重复投递拒 |

### 生产判据（YP 系·预注册不预执行·blocked on CEO 物理件/法务/呈批件）

| # | 判据 | 阻塞依赖 |
|---|---|---|
| AC-YP1 | 真实通道接线：mock 全撤·双通道下单/回调/查单全走官方 API（接口细节以官方文档为准·接线日对齐）；账本 AC-LP1 触发源切换=本件回执 | 物理件：双商户号+服务器/域名/备案 |
| AC-YP2 | 回调公网安全：HTTPS 端点+验签+防重放全开+证书/密钥轮换预案；密钥只 .env | 服务器（server-governance 密钥律） |
| AC-YP3 | 每日对账 cron：双通道官方交易账单下载 vs 本地订单·入夜报（AC-LP2 同节律） | 商户号 |
| AC-YP4 | iOS 虚拟支付：苹果支付开关开启（MP 后台手动）+iOS 费率单独核算（12-17% 口径差·以签约页为准【待证】） | 商户号 |
| AC-YP5 | 实名/未成年人消费合规扣（§五.6）随支付合规定稿 | 法务（§十一·AC-LP3 同源） |
| AC-YP6 | 退款政策锁定：虚拟商品退款规则（已消耗权益不可逆·如实呈批）呈批 CEO 后入配置；退款单=终态 closed 后追加审计行·不改历史 | [needs-CEO] |

## 二、订单域规格（SQLite·本仓单库分表·与大厅/账本同一 WAL 单写者纪律）

```sql
-- pay_orders：订单表（法币域·金额只在本域）
CREATE TABLE pay_orders (
  order_id         TEXT PRIMARY KEY,      -- 内容寻址（化身 ID+商品 ID+序数桶·AC-Y3）
  channel          TEXT NOT NULL CHECK (channel IN ('virtual','standard')),
  census_avatar_id TEXT NOT NULL,         -- AC-Y13：必绑 census 化身 ID
  product_id       TEXT NOT NULL,        -- 服务端价目表键（金额唯一真源·AC-Y2）
  amount_cent      INTEGER NOT NULL CHECK (amount_cent > 0),  -- 法币分·零出域（AC-Y7）
  demand_text      TEXT,                 -- 一句话需求（可空；携带即必过闸 AC-Y8）
  status           TEXT NOT NULL DEFAULT 'created'
                   CHECK (status IN ('created','pending','paid','granted','closed')),
  ts_utc           TEXT NOT NULL
);
-- 触发器 T1：状态机合法迁移表执法（AC-Y1·终态不可回退·同 UGC 状态机法）；T2：下单后 amount_cent 改动=拒

-- pay_receipts：回调回执表（验签留痕）
CREATE TABLE pay_receipts (
  receipt_id   TEXT PRIMARY KEY,         -- 回调内容寻址
  order_id     TEXT NOT NULL REFERENCES pay_orders(order_id),
  signer       TEXT NOT NULL,            -- 验签者标识（通道密钥指纹·沙箱=mock 钥 ID）
  nonce        TEXT NOT NULL,
  amount_cent  INTEGER NOT NULL,         -- 回调面额（与订单比对·AC-Y4 改价检出）
  sig_ok       INTEGER NOT NULL,         -- 1=验签过（0 行=四坏留痕·不触发状态迁移）
  verified_utc TEXT NOT NULL,
  UNIQUE (order_id, sig_ok)              -- AC-Y5：同订单有效回执权威唯一（二投幂等）
);

-- pay_grants：权益发放表（订单→权益记录·目录内容归 P-47-5 件）
CREATE TABLE pay_grants (
  grant_id         TEXT PRIMARY KEY,
  order_id         TEXT NOT NULL UNIQUE REFERENCES pay_orders(order_id),  -- AC-Y6 原子发放+UNIQUE 幂等
  census_avatar_id TEXT NOT NULL,
  entitlement      TEXT NOT NULL,        -- 权益记录（算力包次数/卡档位/入城出生证）·schema 归 P-47-5
  granted_utc      TEXT NOT NULL
);
```

- **状态机**：created（本地建单·价目表锁价）→ pending（通道下单成功·沙箱=mock 预支付凭据）→ paid（有效回调落账）→ granted（权益发放+换算笔提交·单事务 AC-Y6）→ closed（超时关单/退款关单·closed 单重购=新 order_id 序数桶递增）。created/pending 超窗（默认 15min·配置件）自动 closed。
- **回调处理序**：验签（AC-Y4）→ 幂等（AC-Y5）→ 状态迁移校验（AC-Y1）→ 金额比对（AC-Y4）→ 发放单事务（AC-Y6）→ pay.success 入公共流（AC-Y14）→ 应答上游（失败按重试语义应答·不误应答成功）。
- **双通道适配器**：`virtual`（C 端虚拟商品·OfferID/道具配置）与 `standard`（B 端真实服务·商户号验签口径）各自封装通道签名/凭据差异；**订单域只见统一回调契约**。沙箱=mock 双适配器（本地测试钥签名·四坏用例可造）。
- **换算桥（法币→代币·单向）**：granted 时按价目表换算列（比例=[needs-CEO]）向账本提交 share 笔（ref=order_id·ref_type='order'·AC-LP1 对接面）——代币数服务端算出，账本零法币字段（AC-Y7）；直购返币不走桥（§〇）。
- **入城资格**：granted 产物含出生证类 entitlement→lobby `E_ENTRANCE_REQUIRED` 判据源=grants 查询面（跨件引用·发放机制归本件·门禁执法归 lobby 件）。
- **配置数据件**：`src/sandbox/pay/config.json`（编码律：中文文案外置 JSON）——价目表/换算比例/订单超窗/违禁词表占位值全标 `[needs-CEO]`·开闸前呈批锁定。

## 三、对账脚本设计（reconcile·诚实律自检机核·纪律同 ledger 八查）

- 件：`src/sandbox/pay/reconcile.py`（原生 Python·零外采·exit 0=PASS/exit 2=FAIL·一行结论先行=token-economy §3.4 输出纪律）。
- 六查：①状态机合法性全表扫描（非法迁移路径零存在）②订单↔回执一致（paid/granted 必有 sig_ok=1 回执·孤儿回执点名）③订单↔发放一致（granted 必有发放行·未 granted 有发放行=FAIL）④金额一致（回执面额=订单金额·改价注入检出）⑤换算笔核（每笔 ref=真实 granted 订单·代币数=价目表换算值·无凭空换算）⑥法币出域扫描（账本表零法币字段交叉断言）。
- 节律：沙箱每轮自验必跑+部署后每日 cron 入夜报（AC-YP3）；**可独立复跑=实验室独立复核（P-53② 防线二·双窗验收范式）复验入口**。

## 四、合规四件套自检（每设计件必含·本件对照）

| 件 | 本件落位 |
|---|---|
| ① 判据预注册 | §一 AC-Y1~Y14+AC-YP1~YP6（先于实现注册） |
| ② AIGC 生成标识面 | AC-Y9+`ai_service` 服务端权威字段+履约产物 source_ai 由既有管线承接（引用不复制）+深度合成类目「AI 生成」标注义务同向（category-review §1.1 官方备注栏原文） |
| ③ msgSecCheck 前置闸 | AC-Y8+需求文本过闸受理+闸未接线拒启 `E_GATE_OFFLINE`（三件同源第四件·§五.3 生死线：未接内容安全=禁开门） |
| ④ 非投顾风险提示常驻面 | AC-Y10 三面 disclaimer 常驻+AC-Y11 荐股三要素文案禁律（category-review §4.2 反推红线）+商品/类目表述锚定「AI 生成工具/历史回测研究展示」（金融类目定性风险缓解·首提审实测） |

## 五、红线与不做清单（Non-goals）

- **金额永不信任客户端**（AC-Y2·服务端价目表唯一真源·改价双验=下单锁价+回调比对）。
- **法币/代币双域隔离**：法币金额零进代币账本（AC-Y7）；换算单向不可逆；代币永不兑法币（§五.4 生死线·token-ledger 结构性禁令同源双保险）；直购返代币默认不做。
- **账号域永不代办**：商户号开通/认证/协议签署/密钥=CEO 物理件（§十.2·category-review §5 A-D 清单）；密钥只 .env 不入 git。
- 不接真实支付 API 于沙箱（三问门如实过门=**过门但 blocked on 物理件**：法币收款无本地替代·集团 P-47 立项授权在册·商户号未到——mock 网关先行·未接线拒启与 msgSecCheck 同式·不绕闸）。
- 外部成交通道不建（BigCompute 唯一出口·引用其 BLUEPRINT 边界节）；打赏→代币=直播面后续件（blocked on BigCompute 通道·不预建）。
- 定价确认（§十.4 待 CEO 一句话）/退款政策/换算比例/道具正式命名=[needs-CEO] 呈批面不越权（道具名过审=提审实测项·category-review §F）。
- 不做自动退款/自动开票/税务自动化（人工流程·CEO 面）；不做分期借贷；不做代客实盘任何形态（§五.2/五.6 同源）。

## 六、实现件清单（P-47-4b·次件·下一轮自领）

`src/sandbox/pay/`：`orders.py`（状态机+下单/回调/发放 API·单写者）·`adapters.py`（mock_virtual/mock_standard 双适配器·回调签名与四坏用例可造）·`reconcile.py`（§三六查）·`test_pay.py`（AC-Y1~Y14 逐条断言·含四坏回调/改价/中途失败注入组）·`config.json`（价目表/换算比例/违禁词表占位值全标 [needs-CEO]）。闸件 import 复用 lobby `sec_gate`（先例=ledger/ugc）；跨件联验 import ledger（换算笔+法币隔离断言·AC-Y7）。依赖零外采：标准库为限（真实通道接线日才评估官方 SDK·三问门再过）。

---
版本：v0.1（2026-09-24·OSLoop R8·判据预注册版）；修订记录：本件判据变更须先改本表再动实现（预注册纪律·否决窗随集团 T2 例）。
