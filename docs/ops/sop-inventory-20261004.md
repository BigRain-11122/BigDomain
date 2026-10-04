# BigDomain SOP 盘点与补建清单（O-2026-0930-027 首窗回执件）

> 来源=集团 orders **O-2026-0930-027 全集团 SOP 建制令**（委员会通道·九司+CPH4 承接·盘点清单首窗回执·10-07 治理日委员会聚合审）。盘点窗=假期 7 天（10-01..10-08），本件=2026-10-04 首窗回执落盘（R1154）。三级口径=业务线/司内部门/开发模块（令 ①「在册清单化」）。
> 合规面前置注记：本件=人工治理盘点件（零生成内容呈现面=AIGC 标识律不触面）；纯仓内盘点零用户内容面（msgSecCheck 前置闸不涉）；零投资建议零收益承诺（非投顾常驻）。新外部 API 触点=零（三问门未涉）。
> 判据预注册（AC-SOPa..d·先立后写·执行回执=R1154 行）：**a**=§一 在册 16 项每项带盘上文件指针且机械验证在盘（qa/sop-inventory-R1154.log）；**b**=§二 缺口 4 项每项带对标依据指针+排期窗；**c**=轻量闸 ≤200 行/25KB 实测（令 ③a：SOP 单件 ≤200 行/25KB）；**d**=零新外部 API 触点。

## §一 在册盘点（16 项·反重复律：只盘点既有件，零新立法）

| # | 级 | 面 | 在册件与盘上指针 | 机器可验面 | 对标依据 |
|---|---|---|---|---|---|
| 1 | 开发模块 | 设计-沙箱判据前置产线 | `docs/spec/`（17 件）+`src/sandbox/`（14 模块·reconcile_all RUNNER 33 套件 363 判据） | 判据预注册先行+套件自验 exit 0+对账/篡改双态 | 集团判据前置冻结律+O-022 标杆定谳律 |
| 2 | 业务线 | 上线运营预演 SOP | `docs/ops/R-20260926-launch-ops-rehearsal.md`（开播前检查 7 项/值守巡检/事件处置/下播收账+封禁级应急面+上线日 checklist 四阶段） | AC-SD3a..e+可勾选 checklist | 平台直播新规（global-benchmarks §①·W12）+BigCompute 风控引用 |
| 3 | 业务线 | 长假 24h 值守就绪自检 | `docs/ops/R-20260930-holiday-24h-readiness.md`（七面真跑） | verdict READY·P0=0 机器门 | 集团值守轮令族（O-2026-0930-013） |
| 4 | 司内部门 | 每日值守 data 新鲜度核对 | `src/os/backlog.md` 常设行（O-2026-0930-013 ④）+`docs/status-export.json`（ceo_face 三行=当前活/最近实物/下个里程碑） | scan [EXPORT] 面+ConvertFrom-Json 解析门 | 产品优先律 5（CEO 过程可见面） |
| 5 | 司内部门 | OSLoop 轮次执行协议 | `src/os/iteration_prompt.txt`（开轮五步/五静/收账/铁律）+`src/os/iteration_loop.ps1`+`src/os/register_loop_task.ps1` | tick 台账+九面 scan exit 0 | 集团 executive-protocol 极简协议 |
| 6 | 司内部门 | 五静扫描+判读回归 | `tools/skills/bigdomain-loop-scan/scripts/scan_five_still.ps1`+`SKILL.md`+`src/os/test_scan_faces.ps1` | 23 断言回归 harness（源=装件 sha256 恒等） | 集团 scan 判读面正典（GORD/ORD/DEC 内容寻址） |
| 7 | 司内部门 | 单实例锁活性规程 | `src/os/test_lock.ps1`（PID 锁/四路探查/CreateNew 原子抢/30min 接管窗） | AC-D03 10/10 可复跑 | D-20260925-03 集团标准（本司先行实施在册） |
| 8 | 司内部门 | 台账水位整编律 | fold R1..R244 系列（`qa/reorg-*.log` 证据链+`logs/state-preop-*.bak` 备份律） | 轮首首测裁定+verify-then-write（拦截零写入） | P-2026-09-25-18 ④ token 止血令 |
| 9 | 司内部门 | 板规执法迁移律 | `src/os/backlog.md` 规约头+`docs/archive/backlog-done-2026-09.md`/`backlog-done-2026-10.md` | done 行 verbatim 迁档+逐行 md5 同一+pure-append 断言 | P-2026-09-25-18 ④ 配套件（token 止血） |
| 10 | 业务线 | 调研协议 | `docs/research/README.md`（商业化前沿调研部章程·周轮节律+三问门+hot 即报 24h）+`docs/research/intelligence-wall.md` 信号墙 | 信号带源链接+分级+消费落点 | 集团调研协议正典+global-benchmarks 7 天律 |
| 11 | 业务线 | OSS 借力五门评估 | `docs/oss-harvest/README.md`+`docs/oss-harvest/consumption-O-2026-0929-001.md` 消费件 | 五门（license/星数/活跃/安全/契合）+外部请求全录 | P-2026-09-26-08 OSS 借力令+P-2026-10-04-01 §6.4 认领制 |
| 12 | 业务线 | QA 每日 crawl 证据链 | `qa/smoke-*.log`+`qa/smoke-*.png`（真 log 渲染）+`docs/global-benchmarks.md` §④ 更新记录 | 当日 png+log+benchmarks_refreshed 三查门 | 集团 QA charter v1.0（每日 crawl+15h 律） |
| 13 | 合规面 | 设计件合规四件套纪律 | `BLUEPRINT.md` §五生死线（判据预注册+AIGC 标识+msgSecCheck 前置闸+非投顾常驻·docs/spec/ 17 件全带） | spec 逐件四件套对照 | 网信办《标识办法》+深度合成规定+生成式AI 办法（benchmarks §① A 级链） |
| 14 | 业务线 | 打包发布过闸纪律（预演态） | `src/sandbox/releasegate/rehearse.py`（司自建白名单打包）+集团 release-gate v1.0 闸 0~3（bootstrap 行挂闸） | 三器机检（release-scan/secret-scan/元数据扫）exit 门 | 集团 release-gate v1.0（P-2026-09-24-66） |
| 15 | 业务线 | 产品面前台活体规程 | `src/sandbox/frontdoor.py`+`src/sandbox/frontdoor_start.bat`+`preview/`（31 卡·http://127.0.0.1:8093/） | frontdoor 自检断言+RUNNER 回归+F3 派生零写死 | XL-16 前台令族（D-20260930-06③） |
| 16 | 合规面 | 未成年人守护与限频 | `src/sandbox/minors/`（四道 fail-closed 守护闸）+pay/member/liveroom 三面接线（`src/sandbox/reconcile_all.py` 回归面） | AC-MG1..MG7 19 断言+接线 AC-W1..W8 | 《未成年人网络保护条例》（benchmarks §①·W11） |

## §二 缺口清单（4 项·令 ①「缺口补建」·每项带对标依据+排期）

| # | 缺口 | 现状与堵点 | 对标依据 | 排期窗 |
|---|---|---|---|---|
| 1 | 部署/发布 SOP（bootstrap runbook） | 沙箱三器预演已具（在册 #14）·生产部署 runbook 缺；**gated on CEO 物理件**（服务器/域名/备案/商户号） | 集团 release-gate v1.0+部署律（BLUEPRINT §七：私库镜像禁 clone 源码） | 物理件到位窗首件（待件如实注·不造活） |
| 2 | 对账日常化 runbook | 沙箱 reconcile_all 33 套件已具（在册 #1）·生产期账本日对+异常处置升级链缺 | 微信支付回调查单指引（benchmarks §①在册·4012075249）+token-ledger-spec AC-L 族 | **10-05..10-11 窗首件**（夜窗/自驱轨·不占业务车道） |
| 3 | UGC 内容审核运营 runbook | spec 已具（ugc-pipeline-spec AC-U 族·在册 #13）·fail-closed 值守处置+复核流+违规阶梯执行面缺 | 平台运营规范族（benchmarks §①）+跟帖评论规定（W13） | 10-12..10-18 窗 |
| 4 | 用户增长/转化运营 SOP | 研究件已具（fan-growth-funnel/cold-start-strategy·docs/research/）·执行 SOP（动线落地+漏斗度量节律）缺 | O-022 Steam 爆款方法论+动线标杆件（R-20260927-venue-flow-benchmark） | 开闸前窗（跟 P1 呈批门联动） |

## §三 补建排期与建制纪律（令 ④「每司每窗 ≥1 件·不占业务车道=夜窗/自驱轨」）

- 排期汇总：缺口 2=10-05..10-11 窗；缺口 3=10-12..10-18 窗；缺口 1=物理件到位窗（gated）；缺口 4=开闸前窗。每件补建=判据前置冻结律先行（AC 预注册=板行先落）+对标依据指针必带（无对标=拍脑袋违例）+轻量闸（≤200 行/25KB·入口窄化三问）。
- 呈报面：本件随 10-07 治理日委员会聚合审（集团令节奏）；补建进度随 status-export results 行机器可见。

## §四 自验判据对照（AC-SOPa..d·证据=qa/sop-inventory-R1154.log）

- **AC-SOPa 过**：§一 16 项指针机械验证在盘（17 spec+14 sandbox 模块+全部文件路径逐项 os.path 存在性实测）。
- **AC-SOPb 过**：§二 4 项每项=现状+对标依据指针+排期窗三列齐（缺口 1 gated on CEO 物理件如实注）。
- **AC-SOPc 过**：轻量闸实测=本件 X 行/Y KB（≤200 行/25KB·实测值见证据 log）。
- **AC-SOPd 过**：零新外部 API 触点（纯仓内盘点·三问门未涉·雷达清单为只读过目）。
