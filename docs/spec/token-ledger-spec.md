# 硅基域代币双式账本 schema+对账脚本设计 v0.1（业务 API 五件之二·判据预注册版）

> 溯源：ledger P-2026-09-24-47 ②@BigDomain（业务 API 五件之二）+P-2026-09-24-53①（全速五件·自报 AC 证据随 commit）+P-2026-09-24-52①（城市面吸收：账户身份绑定=census 化身 ID 引用·零新增身份系统）；BLUEPRINT §四（代币内循环/共创分成机制）、§三智能体6（用户激励）、§五.4（生死线：纯内循环）、§五.1/3/7（合规四件套同源）；存储纪律=`docs/spec/lobby-websocket-spec.md` §二事件方言（本仓单库 SQLite WAL 分表·同一单写者）。
> 本件性质=设计先行（判据预注册先于实现·诚实律）；沙箱实现件=P-47-2b（次件·§六）。**代币参数面（获取分值/上限/分成比例）=定价确认权 CEO=[needs-CEO]·本件只锁机制与不变量，数值全走配置数据件**。

## 〇、定位与边界

- 代币=**纯内循环消费型虚拟权益**（BLUEPRINT §五.4 生死线）：只可内部消费（皮肤/房间/加急/特效/数字藏品），**永不提现、永不外流、不发币、不融资、不证券化**——本件结构性保证=账本无 withdraw/transfer-out 类型、无任何法币兑换路径、schema 层不存在外流动词。
- **双式=复式记账**：每笔交易必有借（debit）贷（credit）两向分录且 Σdebit=Σcredit——代币不凭空出现/消失，任何变动都可指认对手方账户。
- 账户模型（四类）：`equity:auth` 授权户（铸出唯一对手方·余额恒负=−Σ铸出·教科书式权益账户）；`pool:reserve` 授权池（未发行额度+消费回流终点·平台再发行受其余额硬约束）；`pool:*` 激励池（`pool:reward` 行为挖矿预算池/`pool:share` 共创分成池——铸出先入池、发放=池出账）；`usr:*` 用户余额户（绑定 census 化身 ID）。
- 获取=行为挖矿（登录/共创/拉新/大厅活跃·BLUEPRINT §四）+共创分成（20% 落地分成/30% 观测费分成/10% IAA 分成走 Biggame 结算）；消耗=特权消费回 `pool:reserve`（代币永不离开内循环·再发行受池余额与日上限双闸硬约束——防通胀）。
- 法币边界：真金与对外结算=BigCompute 唯一出口（ledger P-47 ③·引用不复制）；本账本零法币字段零法币接口；分成上限=生态内循环额（BLUEPRINT §四规则）。
- 正式代币名=[needs-CEO]（命名面·呈批）；本件内部代号 `DT`（domain token·纯技术标识）。

## 一、判据预注册（验收判据先于实现——实现件按本表逐条对验·失败如实记负）

### 沙箱判据（L 系·本地原生 Python 可全验·不依赖 Docker）

| # | 判据 | 验法 |
|---|---|---|
| AC-L1 | 双式平衡：每笔 tx ≥2 分录且 Σdebit=Σcredit；违反笔=落库即拒（约束+触发器） | 坏账注入测试（不平衡笔）=拒 |
| AC-L2 | 余额符号律：usr/pool 落库后 ≥0（负=整笔回滚）；equity:auth ≤0 恒负（转正=对账 FAIL——铸出无对手方即凭空造币） | 超额花费注入测试=拒且余额不变 |
| AC-L3 | evt_id 内容寻址去重：tx_id=交易内容哈希·UNIQUE；同笔二次提交=拒（幂等·与大厅事件方言同源） | 重复投递断言 |
| AC-L4 | 来源幂等：mint/share 类 tx 必带 `ref`（来源事件/订单引用）·UNIQUE(ref, ref_type)；同源二次发放=拒（防重复挖矿/重复分成） | 同 ref 二发断言 |
| AC-L5 | 账户对账：物化余额=分录派生余额（全账户逐户相等）·对账脚本 exit 0/PASS | 人为篡改一行余额→FAIL/exit 2 |
| AC-L6 | 零和恒等：Σ全部账户余额=0（复式零和）+授权恒等 Σ(usr+池余额)=Σ铸出（=−equity:auth 恒负余额）；凭空造币/篡改任何一行=对账 FAIL | 篡改注入测试 |
| AC-L7 | 挖矿上限：行为挖矿按用户按日上限（配置数据件驱动·改配置不改代码）；超限=拒 `E_TOKEN_CAP` | 上限边界用例（-1/0/+1） |
| AC-L8 | msgSecCheck 前置闸：共创/脑洞类奖励 mint 的 `ref` 必须指向**已过闸事件**（事件行带 gate=pass 标记·引用大厅闸管道产物）；未过闸引用=发放拒+对账 FAIL；闸未接线=serve 拒启（与大厅 AC-S4 `E_GATE_OFFLINE` 同源自检） | 未过闸 ref 发放断言 |
| AC-L9 | AIGC 标识：AI 判定产出的发放（聊天挖掘智能体评优/AI 整理采纳奖励）tx 带 `source_ai:1` 审计标记（服务端权威·客户端不可传）；账单呈现面同笔带「AI 判定」标识 | 字段断言+客户端伪造忽略断言 |
| AC-L10 | 非投顾常驻提示：余额/账单查询响应体带固定 `disclaimer` 字段（代币=平台内消费型虚拟权益·不可提现不可兑换法币·非投资品非证券·无任何收益承诺）；前端常驻渲染非折叠（生产验收项·本机验字段到位） | 响应体断言 |
| AC-L11 | 身份绑定：`usr:*` 账户必绑 census 化身 ID（`avatar.register` intake 产物引用·server-city §1 面5·T-04 受理归 BigLife·零新增身份系统）；绑定缺位=不发放不入账 | 无绑定发放测试=拒 |

### 生产判据（LP 系·预注册不预执行·blocked on CEO 物理件/呈批件）

| # | 判据 | 阻塞依赖 |
|---|---|---|
| AC-LP1 | 入账触发源全换真实回执：19.9 支付/算力包消耗（P-47-4 对接）/Biggame IAA 结算/观测费分成——mock 全撤 | 物理件：微信支付商户号+P-47-4 |
| AC-LP2 | 账本与流水日志留存 ≥6 个月（等保口径）+每日对账 cron 入夜报 | 等保/服务器 |
| AC-LP3 | 实名与未成年人合规扣（获取面实名档位/未成年人消费上限）随支付合规定稿 | 法务定稿（BLUEPRINT §十一） |
| AC-LP4 | 参数正式版锁定（获取分值/日上限/分成比例）呈批 CEO 后冻结入配置 | 定价确认权=[needs-CEO] |

## 二、Schema 规格（SQLite·本仓单库分表·与大厅事件同一 WAL 单写者）

```sql
-- accounts：账户表（余额物化·对账脚本与派生值互证）
CREATE TABLE ledger_accounts (
  account_id    TEXT PRIMARY KEY,            -- 'usr:<avatar_id>' | 'pool:reserve' | 'pool:reward' | 'pool:share' | 'equity:auth'
  census_avatar_id TEXT UNIQUE,              -- 仅 usr:* 账户绑定（census 化身注册 intake 产物·引用不复制）
  balance       INTEGER NOT NULL DEFAULT 0,  -- 符号律按类分层：usr/pool >=0 / equity:auth <=0（触发器执法·AC-L2）
  status        TEXT NOT NULL DEFAULT 'active',
  created_utc   TEXT NOT NULL
);

-- tx：交易表（一意图一笔·双式头部）
CREATE TABLE ledger_tx (
  tx_id      TEXT PRIMARY KEY,               -- 内容寻址（sha256 六字段核+分录摘要·与事件方言 evt_id 同法）
  type       TEXT NOT NULL CHECK (type IN ('mint','spend','share','adjust')),
                                            -- mint=铸出入池；share=池→创作者分成；spend=消费销毁；
                                            -- adjust=人工更正（必带审批 memo·对账点名行）
  ref        TEXT NOT NULL,                 -- 来源引用（事件 evt_id/订单号/结算单号）
  ref_type   TEXT NOT NULL,                 -- 'event' | 'order' | 'settlement' | 'manual'
  source_ai  INTEGER NOT NULL DEFAULT 0,    -- AC-L9：AI 判定产出=1（服务端权威）
  memo       TEXT,
  ts_utc     TEXT NOT NULL,
  UNIQUE (ref, ref_type)                    -- AC-L4 来源幂等
);

-- entries：分录表（双式主体·每笔 ≥2 行·借贷必平）
CREATE TABLE ledger_entries (
  entry_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  tx_id      TEXT NOT NULL REFERENCES ledger_tx(tx_id),
  account_id TEXT NOT NULL REFERENCES ledger_accounts(account_id),
  direction  TEXT NOT NULL CHECK (direction IN ('debit','credit')),
  amount     INTEGER NOT NULL CHECK (amount > 0),
  ts_utc     TEXT NOT NULL
);
-- 触发器 T1：余额联动（全账户 credit 加 debit 减）→ usr/pool 余额<0 或 equity:auth 余额>0 即 RAISE ABORT（AC-L2）
-- 视图 V1：派生余额（每账户 Σcredit-Σdebit）与物化 balance 互证（AC-L5）
-- CHECK/触发器兜底 Σdebit=Σcredit（AC-L1·应用层先校验·库层兜底）
```

- **记账范式**（每笔=纯账户间转移·零和内生）：授权铸出（mint）=`equity:auth debit → pool:*/usr:* credit`（铸出唯一对手方·授权户恒负）；发放/分成（share）=`pool:share/reward debit → usr:* credit`；消费（spend）=`usr:* debit → pool:reserve credit`（回池·再发行受 reserve 余额硬约束）。恒等式：**Σ全部账户=0**（复式零和）+**Σ(usr+池)=Σmint**（=−equity:auth·AC-L6）。
- **配置数据件**：`src/sandbox/ledger/config.json`（编码律：中文文案外置 JSON）——动作分值/每日上限/分成比例初版占位值·全标 `[needs-CEO]`·开闸前呈批锁定（AC-LP4）。
- **API 面**（沙箱 stub）：`ledger.balance` / `ledger.bill`（含 disclaimer 字段·AC-L10）/ `token.grant_sandbox`（mock 挖矿/分成/消费入口）——生产触发源接 P-47-4 后全换（AC-LP1）。**AC-LP1 对接写入口已落**（P-47-4b·2026-09-24）：加法性 API `Ledger.share_from_pool`（pool:* debit→usr credit·ref=order_id·ref_type='order'·代币数=支付侧价目表换算值显式传入·判据零变更）——账本回归 test_ledger 11/11 全绿在案。

## 三、对账脚本设计（reconcile·诚实律的自检机核）

- 件：`src/sandbox/ledger/reconcile.py`（原生 Python·零外采依赖·exit 0=PASS/exit 2=FAIL）。
- 八查（每查一行 PASS/FAIL 明细+末行总判）：①双式平衡逐笔（AC-L1）②非负全账户（AC-L2）③物化 vs 派生逐户（AC-L5）④铸出恒等式（AC-L6）⑤ref 幂等无重复（AC-L4）⑥共创奖励 ref 过闸核（AC-L8）⑦孤儿分录（tx 缺/账户缺）⑧超上限发放扫描（AC-L7）+adjust 笔逐笔点名。
- 节律：沙箱每轮自验必跑+部署后每日 cron 入夜报（AC-LP2）；**可独立复跑=实验室独立复核（ledger P-53② 防线二·双窗验收范式）的复验入口**。
- 输出纪律：一行结论先行（脚本只打印必须看的行·token-economy §3.4 脚本产出纪律）。

## 四、合规四件套自检（每设计件必含·本件对照）

| 件 | 本件落位 |
|---|---|
| ① 判据预注册 | §一 AC-L1~L11+AC-LP1~LP4（先于实现注册） |
| ② AIGC 生成标识面 | AC-L9+`source_ai` 服务端权威字段+账单呈现面「AI 判定」标识 |
| ③ msgSecCheck 前置闸 | AC-L8+奖励 ref 过闸核+闸未接线 serve 拒启（与大厅 AC-S4 同源） |
| ④ 非投顾风险提示常驻面 | AC-L10+`ledger.bill` disclaimer 固定字段+禁收益承诺词表同源（§五.1） |

## 五、红线与不做清单（Non-goals）

- **结构性禁令**：无 withdraw 类型、无 transfer-out 类型、无任何法币字段/兑换/提现/出金接口——代币外流在 schema 与 API 两层均不存在动词（§五.4 生死线·双保险）。
- 不发币不融资不证券化；不碰法币结算（真金面=BigCompute 唯一出口·引用其 BLUEPRINT 边界节）。
- 参数数值本件不定版（定价确认权 CEO·AC-LP4 呈批件）；正式命名=[needs-CEO]。
- 不建链上/NFT 技术设施（数字收藏品=证书式内循环印记·BLUEPRINT §四 C6·发链=远期另呈批）。

## 六、实现件清单（P-47-2b·次件·下一轮自领）

`src/sandbox/ledger/`：`schema.sql`（§二 DDL+触发器+视图）·`ledger.py`（单写者记账 API：校验→tx+entries 原子落库）·`reconcile.py`（§三八查）·`test_ledger.py`（AC-L1~L11 逐条断言·含坏账注入组）·`config.json`（参数数据件·占位值标 [needs-CEO]）。依赖零外采：标准库为限（三问门：无必要·无授权·不接外部 API）。

---
版本：v0.1（2026-09-24·OSLoop R3·判据预注册版）；修订记录：本件判据变更须先改本表再动实现（预注册纪律·否决窗随集团 T2 例）。
