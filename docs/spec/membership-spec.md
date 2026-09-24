# 硅基域 权益/月卡面设计 v0.1（业务 API 五件之五·判据预注册版）

> 溯源：ledger P-2026-09-24-47 ⑤@BigDomain（业务 API 五件之五·BLUEPRINT §七在册）+P-2026-09-24-53①（全速五件·自报 AC 证据随 commit）；BLUEPRINT §四 C0/C2（入城出生证/三档月卡）、§五.1/3/7（合规四件套同源）、§五.4（代币隔离）、§五.5（裂变按平台规则）、§五.6（实名/未成年）、§十二②（**身份即会员=census 户籍复用·零新增身份系统**）、§四分工注记（店内闭环）、§十.2（物理件）、§十一（法务定稿）；定价锚=委托决策令 v2 ②（**19.9 已锁**·2026-09-24）+三档价目=BLUEPRINT §四 C2 **初版正典·开闸前呈批面保留**；对接面=`docs/spec/payment-integration-spec.md`（**订单→发放机制归该件·权益目录/生命周期归本件**·其 §〇明文「权益目录=P-47-5 件定」）+`docs/spec/token-ledger-spec.md` AC-L11（身份绑定）+`docs/spec/lobby-websocket-spec.md`（呈现面/E_ENTRANCE_REQUIRED 判据源=grants 查询面）+`docs/spec/ugc-pipeline-spec.md`（共创优先筛选=入池权重·三层筛选不变）。
> 本件性质=设计先行（商户号=CEO 账号域物理件未到·永不代办）；沙箱实现件=P-47-5b（次件·§七）。**定价终值/退款与降级政策/宽限期/次数结转/档位正式命名=[needs-CEO] 呈批面不越权**——本件只锁机制与不变量，数值与政策全走配置数据件。

## 〇、定位与边界

- 本件=**店内闭环权益面**（BLUEPRINT §四分工注记）：订单→发放归 pay 件（AC-Y6 原子发放+AC-Y14 pay.success 事件），**本件=发放后的权益激活/配额/特权/生命周期域**。激活面：从 `pay_grants` 行读 entitlement 目录键（价目表配置·pay 件 §二 schema 归本件注记承接）→查档位矩阵→开周期+发月次数+开特权+开券（幂等·AC-M2）。
- **三档矩阵（BLUEPRINT §四 C2 原文锚·数值=[needs-CEO] 呈批面）**：
  - 体验卡 ¥19.9/月：**3 次算力包+基础身份+大厅普通表情**。
  - 城主卡 ¥49.9/月：**10 次算力包+专属居民陪伴+发言高亮+1 次/月建筑署名券**。
  - 共创者卡 ¥99/月：**30 次算力包+加急通道+共创优先筛选+私人房间+皮肤自由换**。
  - 免费态（非会员）：围观+已获出生证者的入城基础面（C0）——会员到期≠出城。
- **两域隔离律（次数≠代币）**：算力次数=**服务配额**（本域记账）；代币=**内循环消费型虚拟权益**（ledger 件记账·§五.4 生死线）。次数账零进代币账本·代币账本零次数字段（AC-M11 交叉断言）——与法币/代币双域隔离（AC-Y7）同为结构性双保险。代币奖励走 ugc/共创分成既有管线（引用·本域永不代发代币）。
- **出生证=永久（C0）**：任意付费件（19.9 算力包/任一档月卡）首笔 granted→birth_cert 权益行·**会员到期不回收**（只回收特权与余次）——入城资格一旦授予永不因到期吊销（AC-M3 跨件联验）。
- **订阅形态=按月手动续费（MVP）**：微信小程序虚拟支付之自动续费能力【待证·接线日核】——MVP=续费=下一周期新订单（订单序数桶防重开=AC-Y3 同法）；周期可叠（续费单激活 start=max(now, 当前活跃 end)·无缝连订）。
- **消费面诚实注记（blocked 引用不预建）**：①次数的实际执行面（一句话→策略/Demo/短视频）=BigMoney/Biggame 生产线引用（跨仓零复制）·沙箱只建配额账+消耗 API 预留位·零 LLM；②专属居民陪伴=BigLife 薄自我×共享城脑引用·呈现面随 lobby/参观端；③建筑署名券消费=FluxVerse DevLoop 承建面（M2-M3）；④私人房间/皮肤池=FluxVerse/参观端件。MVP=权益记录+券账+特权开关·下游系统到位即接线。
- **优先筛选≠优先采纳**：共创者卡「共创优先筛选」=ugc 入池**排序权重与整理批次优先**·永不绕 msgSecCheck、永不绕灰区人工复核、永不绕 CEO 终审（needs_ceo_review 纪律·§五补三层筛选零变更）；「加急通道」=服务队列**排队优先位**·非投资建议优先产出（非投顾边界·§六）。
- 物理件清单（账号域=CEO 永不代办·§十.2）：商户号/密钥只 .env（pay 件 §〇 同源）；服务器/域名/备案=部署前置（AC-MP2 cron 随其到）。

## 一、判据预注册（验收判据先于实现——实现件按本表逐条对验·失败如实记负）

### 沙箱判据（M 系·M=member 权益域·本地原生 Python 可全验·不依赖 Docker·不依赖真实商户号）

| # | 判据 | 验法 |
|---|---|---|
| AC-M1 | 目录唯一真源：档位矩阵（档位键/月次数/特权集/周期天数/宽限天数）唯一真源=服务端配置数据件；客户端声明档位/特权=忽略；目录坏配置（缺档位/月次数非正整数/未知特权键/缺文案/缺 disclaimer）=启动拒 rc2（AC-U2 同法） | 伪造档位用例+五坏配置拒启用例 |
| AC-M2 | 周期激活幂等：period=UNIQUE(化身,产品,周期序数)；同 grant 二次激活=同周期返回零重发（AC-Y3/Y5 同法）；周期叠续 start=max(now, 活跃 end)；非本司发放源激活=拒（grant 须真实存在于 pay_grants·伪造 grant_id=拒） | 重复激活+伪造 grant 用例 |
| AC-M3 | 出生证永久律：首笔付费件 granted→birth_cert 行；档位到期扫描后**入城判定仍过**（跨件联验：lobby 判据源查询面）；无 census 绑定=拒 E_NO_BINDING（AC-L11/AC-Y13 同源·零新增身份系统） | 到期后入城断言+无绑定用例 |
| AC-M4 | 次数守恒：Σ发放−Σ消耗−Σ作废=余额（对账恒等可机验）；超额消耗=拒 E_NO_CREDITS 且账面不变；非活跃周期消耗=拒 E_PERIOD_EXPIRED；周期切换未用次数作废记 expire 行（**结转=[needs-CEO]·默认不结转·如实呈现不掩饰**） | 三点踩界+作废扫描用例 |
| AC-M5 | 特权服务端权威：发言高亮/加急位/皮肤访问/表情包/优先筛选权重=服务端按 active 周期档位裁定；客户端伪造特权字段=忽略（AC-S5/AC-Y9 同法） | 伪造特权用例 |
| AC-M6 | 档位匹配执法：特权→档位查表；低档请求高档特权=拒 E_TIER_REQUIRED（体验卡请求加急=拒）；无 active 周期请求特权=拒 E_NO_ACTIVE_PERIOD | 越档用例矩阵 |
| AC-M7 | msgSecCheck 前置闸：会员文本输入面（署名券文本/房间名/铭牌/皮肤命名需求文本）未过闸=拒 E_CONTENT_REJECTED **零落账零开券**；闸未接线=文本输入面拒启 E_GATE_OFFLINE（lobby AC-S4/ledger AC-L8/ugc AC-U2/pay AC-Y8 **四件同源·本件第五件**）；闸件 import 复用 lobby `sec_gate`（先例=ledger/ugc/pay） | 正反例+拒启用例 |
| AC-M8 | AIGC 标识面：权益域一切 AI 产出呈现（居民陪伴台词/权益说明内 AI 文案）带服务端权威 `ai_generated` 字段（客户端伪造忽略）+呈现面显著标注「AI 生成」（BLUEPRINT §五.7 全呈现面律·BigLife M4 开门帧律同源引用）；会员购买页 `ai_service` 沿 pay AC-Y9 承接 | 字段断言+伪造忽略断言 |
| AC-M9 | 非投顾常驻：会员页/权益说明/含回测观测特权说明面带固定 `disclaimer` 字段常驻（AI 算力与验证服务·非投资建议·历史回测研究展示·无收益承诺·前端非折叠渲染）——AC-Y10/AC-L10 同源 | 响应体断言 |
| AC-M10 | 法币零字段：权益域全部表零金额字段（法币只在订单域·AC-Y7 同源**双保险**·schema 交叉断言·金额列注入=库层拒） | schema 断言+坏注入用例 |
| AC-M11 | 代币零越界：权益域永不写代币账本任何表；代币账本表零次数字段——两域 schema 交叉断言（次数≠代币·§〇 两域隔离律执法面）；代币奖励路径只经 ugc/分成既有管线 | 交叉断言+越界写用例 |
| AC-M12 | 生命周期状态机：period 状态 `active→expired`（终态）；到期扫描 sweep 幂等可重跑；到期后=特权面全关+余次作废+出生证保留+审计行留痕；宽限期天数=[needs-CEO] 配置（默认 0=即时降级·不假装宽限）；非法迁移/终态回退=拒（与 AC-Y1/AC-U9 状态机同法·库层触发器执法） | 到期扫描双跑幂等+回退注入用例 |
| AC-M13 | 事件零双写：会员购买/续费沿 pay.success 既有公共事件（六字段+evt_id·zone=pay·AC-Y14）——**本域零新增公共事件类型**（防双写断言：激活前后公共流行数不变）；域内变动（周期建立/到期/次数发放消耗作废/券变动）落 `member_audit` 审计行供对账 | 公共流计数断言+审计行断言 |
| AC-M14 | 对账：reconcile 六查（§四）干净 PASS exit0；篡改注入（伪发放周期/次数凭空+/删审计行/越权特权行/伪造 grant 源）→FAIL exit2 | 干净跑+五类注入跑 |
| AC-M15 | 文案违禁词表：档位权益文案/券文本模板配置过闸（荐股三要素禁律=个股买卖建议/点位目标价/收益承诺——AC-Y11 同源）；违禁文案=拒配置拒开档（fail-closed） | 违禁文案上架=拒用例 |
| AC-M16 | 券账：建筑署名券 1 次/月=UNIQUE(化身,周期,券型)；无 active 城主卡周期领券=拒 E_NO_ACTIVE_PERIOD；重复用券=拒 E_VOUCHER_USED；券文本未过闸=零开券（AC-M7 联动）；未用券随周期到期作废留痕 | 领券/复用/过期三向用例 |

### 生产判据（MP 系·预注册不预执行·blocked on CEO 物理件/法务/呈批件）

| # | 判据 | 阻塞依赖 |
|---|---|---|
| AC-MP1 | 真实通道订阅单接线：三档=虚拟支付通道商品（D2 轨道乙·pay AC-YP1 同源）；自动续费能力核【待证】——不支持则手动续费为终案如实呈现 | 商户号+服务器/域名/备案 |
| AC-MP2 | 到期/宽限每日 cron+入夜报（与 AC-YP3/AC-LP2 同节律）；入城判定切换=grants 查询面热数据 | 服务器 |
| AC-MP3 | 实名/未成年人消费合规扣（连续包月类目口径随支付合规定稿） | 法务（§十一·AC-YP5 同源） |
| AC-MP4 | 退款/升降档 prorate/结转政策锁定呈批（退款单=终态后审计行不改历史·AC-YP6 同法） | [needs-CEO] |
| AC-MP5 | 三档定价终值+权益数值呈批锁定：19.9 已锁（委托决策令 v2）；¥49.9/¥99 与月次数 3/10/30=§四 C2 初版正典·**开闸前呈批** | [needs-CEO] |
| AC-MP6 | 档位正式命名过审（体验卡/城主卡/共创者卡=现名·创造性保留面=CEO 一句话·勘误令口径） | [needs-CEO] |

## 二、权益域规格（SQLite·本仓单库分表·与大厅/账本/订单同一 WAL 单写者纪律）

```sql
-- member_periods：会员周期表（档位生命周期·法币零字段 AC-M10）
CREATE TABLE member_periods (
  period_id        TEXT PRIMARY KEY,     -- 内容寻址（化身+产品+周期序数·evt_id 同法）
  census_avatar_id TEXT NOT NULL,        -- AC-M3/AC-L11：必绑 census 化身 ID
  product_id       TEXT NOT NULL,        -- pay 价目表档位商品键（目录唯一真源·AC-M1）
  tier             TEXT NOT NULL,        -- 档位键（矩阵查表·AC-M6）
  period_no        INTEGER NOT NULL,     -- 周期序数（单调递增·续费叠新桶）
  start_utc        TEXT NOT NULL,        -- 叠续律 start=max(now, 活跃 end)
  end_utc          TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','expired')),
  source_grant_id  TEXT NOT NULL UNIQUE REFERENCES pay_grants(grant_id),  -- AC-M2：真实发放源
  UNIQUE (census_avatar_id, product_id, period_no)
);
-- 触发器：T1 状态机 active→expired 单向（终态回退拒·AC-M12）；T2 法币列注入拒（AC-M10）

-- member_credit_events：次数流水（append-only 日账+余额=视图·守恒可机验 AC-M4）
CREATE TABLE member_credit_events (
  event_id         TEXT PRIMARY KEY,     -- 内容寻址
  census_avatar_id TEXT NOT NULL,
  period_id        TEXT NOT NULL REFERENCES member_periods(period_id),
  delta            INTEGER NOT NULL,     -- 正=发放/负=消耗或作废
  reason           TEXT NOT NULL CHECK (reason IN ('grant','consume','expire')),
  ref              TEXT, ref_type        TEXT,   -- 消耗引用（服务单预留位）
  ts_utc           TEXT NOT NULL
);
-- 触发器 T3：关闭时按 (化身,period) 余额=Σdelta≥0 执法（负余额注入=拒+回滚·AC-L1 关账法同源）

-- member_vouchers：券账（署名券等月度单发券·AC-M16）
CREATE TABLE member_vouchers (
  voucher_id       TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  period_id        TEXT NOT NULL REFERENCES member_periods(period_id),
  voucher_type     TEXT NOT NULL,        -- 'building_naming'（后续券型入目录再扩）
  demand_text      TEXT,                 -- 券文本（过闸后落·AC-M7）
  status           TEXT NOT NULL DEFAULT 'unused' CHECK (status IN ('unused','used','expired')),
  consumed_utc     TEXT,
  UNIQUE (census_avatar_id, period_id, voucher_type)
);

-- member_audit：域内审计（周期/到期/次数/券变动·AC-M13 对账源·公共流零双写）
CREATE TABLE member_audit (
  audit_id         TEXT PRIMARY KEY,
  census_avatar_id TEXT NOT NULL,
  kind             TEXT NOT NULL,        -- period/expire/credits/voucher
  detail           TEXT NOT NULL,
  ts_utc           TEXT NOT NULL
);
```

- **激活处理序**：验 grant 真实性（pay_grants 存在+归属同化身·伪造拒）→查档位矩阵（AC-M1）→开周期（UNIQUE 幂等 AC-M2·叠续律）→发次数 grant 行→特权=查表派生（零特权表·active 周期即权·AC-M5/M6）→城主卡开署名券行→审计行（AC-M13）。
- **到期扫描**：`sweep(now)`——end_utc 过点周期→expired（触发器单向）+余次作废 expire 行+未用券 expired 留痕+审计行；幂等可重跑（AC-M12）。
- **特权呈现面（跨件引用）**：发言高亮=lobby 消息 envelope 服务端权威字段；表情包/皮肤=呈现层查 active 周期档位；优先筛选权重=ugc 入池排序参数——三面均「服务端裁权·客户端零话语权」（AC-M5）。
- **配置数据件**：`src/sandbox/member/config.json`（编码律：中文文案外置 JSON）——档位矩阵/周期天数/宽限/券型/文案/违禁词表占位值全标 `[needs-CEO]`·开闸前呈批锁定。

## 三、档位矩阵（三档·BLUEPRINT §四 C2 原文锚·数值与下游 blocked 面如实标注）

| 档位 | 价目锚（法币在订单域） | 月次数（配额） | 特权集 | 消费面依赖（引用·不预建） |
|---|---|---|---|---|
| 体验卡 | ¥19.9/月（19.9 已锁） | 3 次算力包 | 基础身份徽标+大厅普通表情包 | lobby 呈现面（既有件） |
| 城主卡 | ¥49.9/月（初版正典·开闸前呈批） | 10 次算力包 | 发言高亮+专属居民陪伴+建筑署名券 1 次/月 | lobby 高亮字段（既有件）；陪伴=BigLife 台词管线引用【blocked 其呈现面】；署名券消费=FluxVerse DevLoop【blocked M2-M3】 |
| 共创者卡 | ¥99/月（初版正典·开闸前呈批） | 30 次算力包 | 加急通道（排队优先位）+共创优先筛选（入池权重）+私人房间+皮肤自由换 | 加急=服务队列优先位【blocked 执行面 BigMoney 引用】；优先筛选=ugc 入池参数（既有件可接）；房间/皮肤池【blocked FluxVerse/参观端·皮肤目录 [needs-CEO]】 |
| 免费态（非会员） | — | 0 | 围观+出生证者入城基础面（C0） | lobby 既有面 |

- 升降档：变更=**次周期生效**（新订单新周期桶·AC-M2）；按比例折算（prorate）=[needs-CEO]（默认无·明示呈现）；同档续费=周期无缝叠续。
- 次数口径：1 次=1 项 AI 算力服务（一句话→策略回测/Demo/短视频·执行面引用·配额在本域先扣后执行·失败回补留审计行）。

## 四、对账脚本设计（reconcile·六查·纪律同 ledger 八查/pay 六查）

- 件：`src/sandbox/member/reconcile.py`（原生 Python·零外采·exit 0=PASS/exit 2=FAIL·一行结论先行）。
- 六查：①周期↔发放一致（每 period 必有真实 pay_grants 源·伪造/孤儿周期点名）②次数守恒（Σ发放−Σ消耗−Σ作废=逐周期余额·负余额零存在）③特权越权扫描（无 active 周期特权请求/低档高档特权行零存在）④法币零字段交叉断言（本域表+账本表双扫·AC-M10/M11）⑤审计完整性（周期建立/到期/次数变动/券变动各有审计行·删审计=FAIL）⑥到期扫描覆盖（end 过点周期零 active 残留）。
- 节律：沙箱每轮自验必跑+部署后每日 cron 入夜报（AC-MP2）；可独立复跑=实验室独立复核（P-53② 防线二）复验入口。

## 五、合规四件套自检（每设计件必含·本件对照）

| 件 | 本件落位 |
|---|---|
| ① 判据预注册 | §一 AC-M1~M16+AC-MP1~MP6（先于实现注册） |
| ② AIGC 生成标识面 | AC-M8+`ai_generated` 服务端权威字段（居民陪伴台词/权益说明 AI 文案全带）+BLUEPRINT §五.7 全呈现面律引用（BigLife M4 开门帧同源·截图即带标·不依赖后期补标） |
| ③ msgSecCheck 前置闸 | AC-M7+会员文本输入面过闸受理+闸未接线拒启 `E_GATE_OFFLINE`（**四件同源第五件**·§五.3 生死线：未接内容安全=禁开门） |
| ④ 非投顾风险提示常驻面 | AC-M9+AC-M15（会员权益文案荐股三要素禁律·「加急=排队优先位非投资建议优先产出」边界注记·AC-Y11 同源）+会员面锚定「AI 生成工具/历史回测研究展示」 |

## 六、红线与不做清单（Non-goals）

- **法币零出订单域**（AC-M10·pay AC-Y7 同源双保险）；**次数≠代币两域隔离**（AC-M11·代币账本结构性禁令同源双保险）；代币永不兑法币永不提现（§五.4 生死线引用）。
- **特权永不金融化**：会员特权零收益承诺、零荐股权益、零实盘通道（§五.1/2/6 同源）；「加急」=排队位·产出物同过非投顾 disclaimer 同过回测研究定性。
- **优先筛选永不绕审**：msgSecCheck/灰区人工复核/CEO 终审三层零变更（§五补）；needs_ceo_review 永不自动采纳律在本域特权下不变。
- **不预建 blocked 下游**：居民陪伴执行/署名券消费/私人房间/皮肤池/加急服务执行=引用与券账预留位·下游到位接线（§〇 诚实注记）；自动续费不预建（【待证】接线日核）。
- **账号域永不代办**：商户号/密钥/协议=CEO 物理件（§十.2·pay §〇 同源）；密钥只 .env 不入 git。
- 邀请裂变权益不预建（§五.5 平台规则面=后续件）；不做会员等级金融化证券化；不做会员数据对外变现（脱敏报告=B 端件另册）。
- 档位价目 ¥49.9/¥99 与次数 3/10/30=初版正典·**开闸前 [needs-CEO] 呈批**（委托决策令 v2 口径·19.9 已锁）；宽限/结转/退款/prorate/档位命名=[needs-CEO]。

## 七、实现件清单（P-47-5b·次件·下一轮自领）

`src/sandbox/member/`：`catalog.py`（档位矩阵加载+校验·五坏配置拒启）·`member.py`（周期激活/次数消耗/特权查裁/券账 API·单写者·BEGIN IMMEDIATE）·`sweep.py`（到期扫描·幂等）·`reconcile.py`（§四六查）·`test_member.py`（AC-M1~M16 逐条断言·含伪造 grant/越权特权/次数守恒注入组）·`config.json`（档位矩阵/宽限/券型/文案/违禁词表占位全标 [needs-CEO]）。闸件 import 复用 lobby `sec_gate`（先例=ledger/ugc/pay）；跨件联验 import pay（grant 源真实性·AC-M2）+lobby（出生证判据源·AC-M3）；法币/代币双域断言 import ledger schema（AC-M10/M11）。依赖零外采：标准库为限。

---
版本：v0.1（2026-09-24·OSLoop R11·判据预注册版）；修订记录：本件判据变更须先改本表再动实现（预注册纪律·否决窗随集团 T2 例）。
