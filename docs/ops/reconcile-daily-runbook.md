# 硅基域对账日常化 runbook v1.0（O-2026-0930-027 滚动窗 10-05..10-11 窗首件·SOP 盘点缺口 2 补建）

> 来源=集团 orders **O-2026-0930-027 全集团 SOP 建制令**（滚动窗每窗 ≥1 件·不占业务车道）+`docs/ops/sop-inventory-20261004.md` §二 表行 2 在册定档：沙箱 reconcile_all 33 套件已绿（在册 #1）·缺「日对账终端+异常告警当日闭环」两件——本件即两件收口。落盘轮=R1186（2026-10-05）。
> 合规面前置注记：纯仓内账务机制件零用户内容面（msgSecCheck 前置闸不涉）；零生成内容呈现面（AIGC 标识律不触面）；零投资建议零收益承诺（非投顾常驻）；零新外部 API 触点（三问门未涉）。

## §0 判据预注册（AC-RB1..RB4·先立后写·预注册册=src/os/backlog.md O-027 窗首件行·本节引用不复制）

- **AC-RB1**：runbook 在盘 ≤120 行，含本判据预注册节+微信支付回调对单指引引用（benchmarks §① 4012075249·引用不复制）+token-ledger-spec AC-L 面引用。
- **AC-RB2**：沙箱对账实跑证据当日落 qa/（reconcile 控制面复跑+篡改面 exit 2 双态在册口径）。
- **AC-RB3**：异常告警当日闭环路径成文（分级表+处置面+升级面）。
- **AC-RB4**：闭环回执三载体（state log 行+backlog done 标+commit 含 O-2026-0930-027）。

## §一 跑法（每日首个 OSLoop 轮次轮首执行·与 O-2026-0930-013 ④ data 新鲜度核对同段）

1. **沙箱态（现行）**：`python src/sandbox/reconcile_daily.py`——入口件自动派生当日证据路径 `qa/reconcile-daily-YYYYMMDD.log`（已存在则加 `-N` 序号，永不覆写旧证据），子进程调 `src/sandbox/reconcile_all.py <log>`（utf-8 tee 全保真），透传退出码。
2. 一次跑=33 套件（363 预注册判据）+三域对账控制面双态六控制：ledger 八查（clean → exit 0；篡改副本 balance+1 → exit 2）+ pay 六查（clean → exit 0；篡改 granted order amount_cent+1 → exit 2）+ member 六查（clean → exit 0；删 credits audit 行 → exit 2）。防篡改防线=tamper 面必须 exit 2（AC-RA8/RA9 在册口径）。
3. **生产态（bootstrap 后启用·CEO 物理件到位为前置）**：三域 reconcile CLI 传真实 db 路径（ledger/pay=positional argv·member=argparse flags——passthrough 已验 AC-RA10·零新 CLI 面）+微信支付 T+1 日对账（当日 10 点后账单逐笔核对四情况；查单判据=验签成功+trade_state=SUCCESS；前端返回即查单+未付再发起用原单号律——对单指引全文=`docs/global-benchmarks.md` §① 支付合规行〔**4012075249**·引用不复制〕+`docs/research/intelligence-wall.md` W2）；账本判据面锚=`docs/spec/token-ledger-spec.md` §一 **AC-L1..L11**（双式平衡/余额符号律/evt_id 幂等/对账八查·引用不复制）。

## §二 判读（一行定态）

| 出口信号 | 判读 |
|---|---|
| `RUNNER PASS (33/33 suites green, reconcile controls 6/6)` exit 0 | **G0 绿**——当日对账闭环，记账收轮（state log 附一行引用证据文件名） |
| `RUNNER FAIL` exit 1 | 套件回归破或控制面断言失——按 §三 分级 |
| reconcile clean 面 exit≠0 且非 2 | **G2**（数据面真不一致） |
| reconcile tamper 面 exit≠2 | **G3 防线失守**（最高级） |
| 生产期金额不一致 | **G4**（对单四情况处置） |

## §三 异常分级表（分级表+处置面+升级面=AC-RB3 三件）

| 级 | 现象 | 处置面（当日） | 升级面 |
|---|---|---|---|
| G0 | 全绿 | 记账收轮·证据留 qa/ | 无 |
| G1 | 单套件红/判据计数漂移（exit 1·控制面全绿） | 复跑单套件定位+`git log/diff` 近改回滚或修复+复跑全绿 | 当日不闭环→HQ-FEEDBACK P1 行（23:00 前） |
| G2 | clean 面红（账面真不一致） | 三步：复跑确认→按输出行逐查定位（八查/六查逐项）→修复+复跑绿 | 当日不闭环→HQ-FEEDBACK **P0** 行（账本面=open 风险） |
| G3 | tamper 面 exit≠2（防篡改防线失守） | **红线事件**：当日必修（触发器/约束复原+复跑双态全绿）·禁过夜 | HQ-FEEDBACK **P0** 行即写即报+state log 注红线 |
| G4 | 生产期支付对单不一致（四情况） | 按查单指引处置（原单号查单/关单/人工对账）·金额差永不静默调账 | 涉资损/重复支付→[needs-CEO] 当日呈批 |

## §四 当日闭环路径（值守联动）

- 每日首个轮次：§一 跑法 → §二 判读 → §三 分级处置 → 证据落 qa/ → 收账（state log 一行+export results 行）——当日 23:00 前全部闭环或升级，禁带红过夜（G0 除外）。
- 升级承载=本仓根 `HQ-FEEDBACK.md` 行级追加（P-32 日清律同通道）；G3/G4 P0=即写即报。
- 证据保留：当日 log 全保真入 qa/（git 追踪·`!qa/*.log` 白名单在册）；跨日复盘消费=scan [QA] 面与治理日聚合审。

## §五 自验判据对照（R1186·证据=qa/reconcile-daily-20261005.log+本件行数实测）

- **AC-RB1 过**：本件 50 行 ≤120（UTF-8 口径实测）；判据预注册节=§0；4012075249 引用=§一3；AC-L 面引用=§一3。
- **AC-RB2 过**：当日实跑证据 `qa/reconcile-daily-20261005.log`（RUNNER PASS 33/33+controls 6/6=clean exit 0/tamper exit 2 双态全过）。
- **AC-RB3 过**：§三 四级分级表+处置面+升级面三列齐。
- **AC-RB4 过**：三载体=state log R1186 行+backlog done 标+commit 消息含 O-2026-0930-027。
