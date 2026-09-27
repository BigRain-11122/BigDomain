# 店内体验 v2（入城后六触点面·J2 差分）

> 令溯源：P-2026-09-27-07 闲置司自驱动员令 ②@BigDomain「M2 前预备三件 ≤48h」之一（店内体验 v2）·ledger L146 原文·R406 认领开工·判据预注册=src/os/backlog.md 顶行（AC-M2a..e·R405 排板先于撰写）。
> v1 基线：integration-deepening-spec §三 J2 入城段+12 契约缝（IF-1..IF-12）+lobby spec（AC-S1..S13）=大厅呈现面现役正典。本件=入城后店内体验差分深化·零新缝零新 schema 零新 API（反重复律）。
> P1 边界：本件=体验面设计·定价/开闸零执行（BLUEPRINT §四 正典零改动）。

## 一、J2 触点差分六面表（J1 围观无之·J2 入城才有）

| # | 触点面 | 呈现内容（差分 vs J1） | 承载判据号 | 合规闸 | 文案红线 |
|---|---|---|---|---|---|
| F1 权益面 | 会员权益页（档位特权/月次数/署名券） | J1 不可见；J2 按 active 周期档位服务端裁定呈现 | member AC-M1（目录唯一真源）/M4（次数守恒）/M5（特权服务端权威）/M6（档位匹配执法）/M16（券账 UNIQUE） | 非投顾常驻=AC-M9 disclaimer 固定字段前端非折叠；AIGC=AC-M8 ai_generated 服务端权威 | 档位文案过 AC-M15 违禁词表（荐股三要素禁律·违禁=拒配置拒开档 fail-closed） |
| F2 价目面 | 价目区（19.9 算力包/体验卡/城主卡/身份件） | J1 只读参观快照；J2 可见可购价目区 | BLUEPRINT §四正典（§四.0 入城门票律/§四.1 19.9 锁价/§四.2 订阅梯 L53/§四.5 身份件 L58）+price-canon-amendment N1-N7 映射 | 调价走 T1 否决窗公告（gv 标准 4）；非投顾常驻 | 价目文案同过 AC-M15 词表；零收益承诺词 |
| F3 购买动线 | 购物车→下单→支付→granted 回执 | J1 无购物车；J2 动线开（JV-2/JV-3 同源） | pay AC-Y1..Y14（双通道+幂等+对账）；AC-Y7 法币/代币双域隔离；AC-Y3/Y5 幂等（AC-M2 同周期零重发） | 充值/购买页代币三不可条款常驻（BLUEPRINT L122 协议条款级原文：不可退款/不可转让/不可兑换现金或任何法币/无现金价值） | 零金融建议；金额只现订单域（AC-M10 法币零字段同源双保险） |
| F4 余额面 | 代币余额/账单查询 | J1 零余额户；J2 `usr:*` 账户可见 | ledger AC-L7（超上限拒）/L9/L10（balance/bill API+disclaimer 固定字段） | 非投顾常驻=AC-L10 前端常驻渲染非折叠；AI 产出行带标识 | disclaimer 原文承=平台内消费型虚拟权益·不可提现不可兑换法币·非投资品非证券·无任何收益承诺（AC-L10） |
| F5 共创入口 | idea 提交/提案池/城市编年史 | J1 只收不可发（AC-S2 E_ENTRANCE_REQUIRED）；J2 chat+idea 双通道开（AC-S10 分流） | ugc AC-U1..U12（单管线多入口/幂等/终审状态机）+lobby AC-S10；署名/分成=incentive 确权四判据（BLUEPRINT L79） | msgSecCheck 前置闸=五件同源拒启（AC-S4/L8/U2/Y8/M7·闸未接线=serve 拒启 E_GATE_OFFLINE·禁开门非降级）；AIGC 整理初版=AC-U7 producer 服务端权威 | 非投顾双面=AC-U8（闸2 非投顾词表全入口+查询响应 disclaimer 固定字段） |
| F6 身份面 | 出生证/化身/户籍/皮肤 | J1 参观 census 只读快照（AC-S13）；J2 出生证+化身注册+身份件呈现 | member AC-M3（出生证永久律）/M12（到期保出生证）；ledger AC-L11（usr:* 必绑 census 化身·无绑定不发放）；lobby AC-S12（avatar.register 双闸 intake） | 化身注册双闸=闸1 内容安全+闸2 非投顾词表（AC-S12）；AIGC 居民台词带标识=AC-S5 ai_generated 服务端权威覆写 | 零意识宣称；身份件呈现零金融属性 |

## 二、J1→J2 状态迁移执法面（差分开关）

- 入城判定=服务端凭证权威（IF-2 入城凭证缝）：无 granted 凭证→F3/F5/F6 写通道全关（AC-S2 同法拒 E_ENTRANCE_REQUIRED）；有凭证→六面全开。
- 差分单点律：六面开关只读 pay→member granted 状态单一真源（AC-M3 跨件联验 lobby 判据源查询面在册）——零第二真源（反重复律）。

## 三、合规四件套（全设计件必含）

1. **判据预注册**：AC-M2a（backlog 顶行·R405 排板先于撰写）。
2. **AIGC 生成标识**：F1 权益说明 AI 文案（AC-M8）/F4 AI 产出双轨（显式 ai_label+隐式盲水印 R321 5/5）/F5 整理初版（AC-U7）/F6 居民台词（AC-S5）——全呈现面标识（BLUEPRINT §五生死线）。
3. **msgSecCheck 前置闸**：F5 共创入口+F6 化身注册文本面单向依赖·五件同源拒启（未接线=禁开门非降级）。
4. **非投顾常驻**：F1/F2/F3/F4 全带 disclaimer 固定字段常驻（AC-M9/L10/U8/Y10 同源词表族）。

## 四、结论应用表（research-protocol §二.1 落点强制）

| 项 | 落点 | 状态 |
|---|---|---|
| 本件六面表 | lobby spec 下版吸收面（J2 差分引用）+前端实现=bootstrap 期 | 已落盘（吸收待下版） |
| 价目/开闸 | BLUEPRINT §四 正典零改动·增补走 price-canon §四呈批面 | [needs-CEO] 呈批零执行 |
| 物理件依赖 | 商户号/服务器/域名/备案（AC-YP1/AC-P1~P3） | blocked on CEO 物理件（如实待） |

> 更新记录：2026-09-27 R406 首版（P-2026-09-27-07 四议程之二·M2 前预备三件之一·AC-M2a 自验对照=backlog done 行）。
