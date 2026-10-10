# 硅基域对账日常化 runbook v1.0（O-2026-0930-027 滚动窗 10-05..10-11 窗首件·SOP 盘点缺口 2 补建）

> 来源=集团 orders **O-2026-0930-027 全集团 SOP 建制令**（滚动窗每窗 ≥1 件·不占业务车道）+`docs/ops/sop-inventory-20261004.md` §二 表行 2 在册定档：沙箱 reconcile_all 33 套件已绿（在册 #1）·缺「日对账终端+异常告警当日闭环」两件——本件即两件收口。落盘轮=R1186（2026-10-05）。
> 合规面前置注记：纯仓内账务机制件零用户内容面（msgSecCheck 前置闸不涉）；零生成内容呈现面（AIGC 标识律不触面）；零投资建议零收益承诺（非投顾常驻）；零新外部 API 触点（三问门未涉）。

## §0 判据预注册（AC-RB1..RB4·先立后写·预注册册=src/os/backlog.md O-027 窗首件行·本节引用不复制）

- **AC-RB1**：runbook 在盘 ≤120 行，含本判据预注册节+微信支付回调对单指引引用（benchmarks §① 4012075249·引用不复制）+token-ledger-spec AC-L 面引用。
- **AC-RB2**：沙箱对账实跑证据当日落 qa/（reconcile 控制面复跑+篡改面 exit 2 双态在册口径）。
- **AC-RB3**：异常告警当日闭环路径成文（分级表+处置面+升级面）。
- **AC-RB4**：闭环回执三载体（state log 行+backlog done 标+commit 含 O-2026-0930-027）。

## §一 跑法（每日首个 OSLoop 轮次轮首执行·与 O-2026-0930-013 ④ data 新鲜度核对同段）

1. **沙箱态（现行）**：`python src/sandbox/reconcile_daily.py`——入口件自动派生当日证据路径 `qa/reconcile-daily-YYYYMMDD.log`（已存在则加 `-N` 序号，永不覆写旧证据），子进程调 `src/sandbox/reconcile_all.py <log>`（utf-8 tee 全保真）。
2. **runner 段**：全量套件+三域对账控制面双态六控制：ledger 八查（clean → exit 0；篡改副本 balance+1 → exit 2）+ pay 六查（clean → exit 0；篡改 granted order amount_cent+1 → exit 2）+ member 六查（clean → exit 0；删 credits audit 行 → exit 2）。套件数与判据数随 SUITES 注册表现值增长（写死计数已 stale·以当日 RUNNER 行实测为准）。防篡改防线=tamper 面 must exit 2（AC-RA8/RA9 在册口径）。
3. **schema 漂移哨兵步（R1714 起随跑·零配置）**：runner 段毕后入口件自动跑 `src/sandbox/fingerprint_regen.py --chain migration_chains.json --check`，stdout/stderr 追加进同一当日证据 log——分节行 `--- sentinel: fingerprint-regen --check ---` 先行、`sentinel exit=N` 尾行（追加模式零覆写·同日 -N 后缀件语义不变）。哨兵=五域构造器活体指纹对 `migration_chains.json` 冻结基线逐域比对，漂移（exit 2）=基线与活体分叉。
3b. **daily 剖面步（R1733 起随跑·观察窗）**：哨兵步毕后入口件自动跑 `src/sandbox/runner_profile.py --daily --check`（daily 基线 staleness 检测·R1715 daily 变体），输出追加同一当日证据 log——分节行 `--- profile: runner-profile --daily --check ---` 先行、`profile exit=N (observation-window: recorded, not gating)` 尾行。**观察窗期 profile exit 恒记账不参当日判定**（`PROFILE_OBSERVATION_WINDOW=True`）；转正（升 G5 同级门控）=漂移阈值回访窗定夺（tech.md R1733 认领行 AC-PD2）。
4. **当日退出码聚合**：runner 非零=传播 runner 码（哨兵仍跑仍记账=失败日不漏检漂移面）；runner 零=哨兵承接（漂移即当日 FAIL）；profile 步观察窗期恒不参判定（终行 `profile=ok|flag(exit=N)` 字段=记账面）。终行 `RECONCILE-DAILY <date> verdict=… exit=N log=… runner_exit=N sentinel=ok|drift(exit=N) profile=ok|flag(exit=N)` 打 stdout——判读以终行为准，证据细节在当日 log。
5. **生产态（bootstrap 后启用·CEO 物理件到位为前置）**：三域 reconcile CLI 传真实 db 路径（ledger/pay=positional argv·member=argparse flags——passthrough 已验 AC-RA10·零新 CLI 面）+微信支付 T+1 日对账（当日 10 点后账单逐笔核对四情况；查单判据=验签成功+trade_state=SUCCESS；前端返回即查单+未付再发起用原单号律——对单指引全文=`docs/global-benchmarks.md` §① 支付合规行〔**4012075249**·引用不复制〕+`docs/research/intelligence-wall.md` W2）；账本判据面锚=`docs/spec/token-ledger-spec.md` §一 **AC-L1..L11**（双式平衡/余额符号律/evt_id 幂等/对账八查·引用不复制）。

## §二 判读（一行定态）

| 出口信号 | 判读 |
|---|---|
| `RECONCILE-DAILY <当日> verdict=PASS exit=0 … runner_exit=0 sentinel=ok`（runner 段与哨兵节双绿） | **G0 绿**——当日对账闭环，记账收轮（state log 附一行引用证据文件名） |
| `RECONCILE-DAILY … runner_exit≠0`（runner 段红·哨兵仍跑仍记账） | 套件回归破或控制面断言失——按 §三 分级 |
| `RECONCILE-DAILY … verdict=FAIL` 而 runner_exit=0（sentinel=drift） | **G5 漂移面**——按 §三 G5 行处置 |
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
| G5 | 哨兵漂移（sentinel=drift·runner_exit=0·当日 verdict=FAIL） | 读证据 log 哨兵节漂移域+_fp_diff 细节→`git log/diff` 定位构造器/链改动→合法 schema 变更=追加迁移链步〔schema_migrate〕+`fingerprint_regen --update` 再冻结〔steps 非空时 --update 拒=先过迁移链〕→复跑哨兵绿+当日复跑全绿 | 当日不闭环→HQ-FEEDBACK P1 行（基线契约 open 风险） |

## §四 当日闭环路径（值守联动）

- 每日首个轮次：§一 跑法 → §二 判读 → §三 分级处置 → 证据落 qa/ → 收账（state log 一行+export results 行）——当日 23:00 前全部闭环或升级，禁带红过夜（G0 除外）。
- 升级承载=本仓根 `HQ-FEEDBACK.md` 行级追加（P-32 日清律同通道）；G3/G4 P0=即写即报。
- 证据保留：当日 log 全保真入 qa/（git 追踪·`!qa/*.log` 白名单在册）；跨日复盘消费=scan [QA] 面与治理日聚合审。

## §五 自验判据对照（R1186·证据=qa/reconcile-daily-20261005.log+本件行数实测）

- **AC-RB1 过**：本件 50 行 ≤120（UTF-8 口径实测）；判据预注册节=§0；4012075249 引用=§一3；AC-L 面引用=§一3。
- **AC-RB2 过**：当日实跑证据 `qa/reconcile-daily-20261005.log`（RUNNER PASS 33/33+controls 6/6=clean exit 0/tamper exit 2 双态全过）。
- **AC-RB3 过**：§三 四级分级表+处置面+升级面三列齐。
- **AC-RB4 过**：三载体=state log R1186 行+backlog done 标+commit 消息含 O-2026-0930-027。
- **R1715 哨兵节补文对照**：§一3/4 哨兵步+聚合语义、§二 G0 双绿口径+runner 红行+G5 漂移行、§三 G5 处置行、§一2 活性计数口径=tech.md R1715 认领行 AC-RK1..RK3 全对照（判据预注册先于成文）；行数 ≤120 实测（AC-RB1 线不破）。
