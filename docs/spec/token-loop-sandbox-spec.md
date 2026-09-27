# 代币内循环沙盘（五幕桌面推演·dry-run）

> 令溯源：P-2026-09-27-07 闲置司自驱动员令 ②@BigDomain「M2 前预备三件 ≤48h」之二（代币内循环沙盘）·ledger L146 原文·R406 认领开工·判据预注册=src/os/backlog.md 顶行（AC-M2b·R405 排板先于撰写）。
> 定位：桌面推演剧本件（M2 预备）·**零新外部依赖零新代码零新 schema**——全部断言引用在册 token-ledger-spec（AC-L1..L11+§三八查对账）与沙箱件（src/sandbox/ledger/·test_ledger 11/11 全绿在案）；生产接线=bootstrap 期。

## 一、账本恒等式与账户模型（引用面）

- 四类账户（token-ledger §账户模型）：`equity:auth` 授权户（铸出唯一对手方·余额恒负）/`pool:reserve` 授权池（未发行额度+消费回流终点）/`pool:reward`·`pool:share` 激励池（铸出先入池·发放=池出账）/`usr:*` 用户余额户（绑定 census 化身）。
- **两恒等式**（AC-L6 正典）：①复式零和 Σ全部账户余额=0（AC-L1 双式平衡逐笔执法·违反笔落库即拒）；②授权恒等 Σ(usr+池余额)=Σ铸出（=−equity:auth 恒负余额·授权户转正=对账 FAIL——铸出无对手方即凭空造币）。
- **代币三不可条款闸**（BLUEPRINT L122 协议条款级原文）：不可退款、不可转让、不可兑换现金或任何法币、无现金价值——充值/购买/分成/余额呈现页常驻+AC-L10 disclaimer 固定字段（对标 Steam Subscriber Agreement 钱包条款协议层同构）。

## 二、五幕剧本（每幕=动作链+恒等式断言+三不可闸+dry-run 判据）

### 幕一 充值铸出（mint）
- 动作链：法币订单支付成功（pay AC-Y1..Y14·法币域）→换算桥同笔铸出（IF-5）`equity:auth debit → usr:*/pool:* credit`。
- 恒等式断言：铸出后 equity:auth 余额=−Σ铸出（恒负·AC-L2）；Σ(usr+池)=Σmint（恒等式②）；复式零和不破（恒等式①）。
- 三不可闸：充值呈现页条款常驻（L122 原文）+账单响应 disclaimer 固定字段。
- dry-run 判据：reconcile 八查（ledger §三八查）全 PASS exit0；坏账注入（不平衡笔）=落库拒（AC-L1 注入测试在案）。

### 幕二 购买入城（19.9→granted）
- 动作链：19.9 下单→回调验签→幂等 granted（AC-Y3/Y5·AC-M2 同周期零重发）→代币按支付侧价目表换算值显式传入（`Ledger.share_from_pool`·ref=order_id·AC-LP1 对接写入口）。
- 恒等式断言：ref 幂等无重复（AC-L4·同 order_id 二次=拒）；usr:* 落库后 ≥0（AC-L2 符号律）；usr:* 已绑 census 化身（AC-L11·无绑定=不发放不入账）。
- 三不可闸：购买呈现页条款常驻+金额只现订单域（AC-Y7 双域隔离·AC-M10 同源）。
- dry-run 判据：八查⑤ref 幂等行 PASS；无绑定发放注入测试=拒（AC-L11 用例）。

### 幕三 共创分成（share）
- 动作链：创意过三层筛选→adopted 终态→gate_receipts 只为 gate=pass 件开回执（AC-U10）→`pool:share debit → usr:* credit`（确权四判据=AA 登记制+署名完成才计分成+违规追回·BLUEPRINT L79）。
- 恒等式断言：分成 ref 过闸核（AC-L8·无回执 ref=对账 FAIL）；池余额 ≥0（AC-L2）；零和恒等不破。
- 三不可闸：分成回执呈现面条款常驻（分成=代币非现金·无现金价值）。
- dry-run 判据：八查⑥共创奖励 ref 过闸核 PASS；超上限发放扫描 PASS（AC-L7）。

### 幕四 算力消耗（spend）
- 动作链：特权消费（回测/小游戏 Demo/短视频·§四.1 三形态）→`usr:* debit → pool:reserve credit`（回池·平台再发行受 reserve 余额硬约束）。
- 恒等式断言：usr:* 花费后 ≥0（超额=拒 E_NO_CREDITS 且账面不变·AC-M4 同法）；reserve 余额=再发行硬上限。
- 三不可闸：余额扣减呈现面条款常驻+disclaimer 字段（AC-L10）。
- dry-run 判据：超额花费注入测试=拒（AC-L2 用例）；八查②非负全账户 PASS。

### 幕五 到期处理（sweep）
- 动作链：周期到期扫描 sweep（AC-M12 幂等可重跑）→特权面全关+余次作废+出生证保留；代币余额≠次数——两域隔离（AC-M11·次数≠代币·代币零作废跨周期保留）。
- 恒等式断言：sweep 幂等（重跑零重发）；代币账本零联动写（权益域永不写代币表·AC-M11 schema 交叉断言）；零和恒等不破。
- 三不可闸：到期呈现面条款常驻（代币保留≠退款·三不可原文承）。
- dry-run 判据：reconcile 六查（member §四）+八查双跑 PASS exit0；越界写注入=库层拒（AC-M11 用例）。

## 三、幕间闭环校验（内循环完整性）

- 幕一→幕五全链跑毕：Σ(usr+池)=Σmint（恒等式②口径全程不变）；Σ全部账户=0（恒等式①）。
- 回流再发行面：pool:reserve 出账再铸出=受 reserve 余额硬约束（不足=拒）——**封闭内循环**（纯内循环消费型虚拟权益·永不提现外流·不发币不融资不证券化·BLUEPRINT §四 4 代币条原文）。

## 四、合规四件套

1. **判据预注册**：AC-M2b（backlog 顶行·先于撰写）。
2. **AIGC 生成标识**：幕四消耗产物（回测报告/Demo/短视频）呈现面全标识（JV-6 同源·显式 ai_label+隐式盲水印 R321）。
3. **msgSecCheck 前置闸**：幕三分成前提=创意过闸（AC-U2/L8 五件同源拒启·未接线=禁开门非降级）。
4. **非投顾常驻**：幕一充值页三不可条款+全幕余额/账单响应 disclaimer 固定字段（AC-L10·前端常驻非折叠）。

## 五、结论应用表

| 项 | 落点 | 状态 |
|---|---|---|
| 本件五幕剧本 | M2 预备证据面+reconcile dry-run 场景清单（对账脚本扩用例引用面） | 已落盘 |
| 首档参数 | 分成比例/发放上限/宽限天数=[needs-CEO]（AC-LP4/AC-IP1 先例） | 呈批零执行 |

> 更新记录：2026-09-27 R406 首版（P-2026-09-27-07·M2 前预备三件之二·AC-M2b 自验对照=backlog done 行）。
