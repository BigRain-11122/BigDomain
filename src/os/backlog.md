# BigDomain 认领工作板（backlog）

> 认领制：自正典任务板 `tasks.md` 迁六件起版（CPH4 Labs 巡检批 2026-09-24 代迁）。取最上一条未完成项为当轮焦点；完成标 `[done 日期]` 并同步勾选 `tasks.md` 对应项；做不完拆细、剩余部分写回顶行；全部依赖 CEO 物理件的项=不可认领（如实待物理件，不造活）。
> 双板律：本板=认领/进度工作面；`tasks.md`=正典任务板。两板同六件起版，完成态两板同步。
> 集团转办扫描（见 `iteration_prompt.txt` 开轮五步②）新入项排顶行——ledger 未回执行 @BigDomain 转办（如 P-2026-09-24-42 的 §四价目「成交执行面」分工注记半项）由扫描步入板，不在此预录。

- [x] P-47-1b 大厅 WebSocket 沙箱骨架（docker-compose 本地沙箱·按 `docs/spec/lobby-websocket-spec.md` 判据 AC-S1~S10 逐条实现+自验·Python websockets 首选）[done 2026-09-24] 判据自验 10/10 全过（AC-S3 往返 0.1/0.3ms≤500ms；AC-S4 闸配置缺失=rc2 拒启 E_GATE_OFFLINE+命中不广播不落公共流；AC-S5 ai_generated 服务端权威；AC-S8a 心跳 30/60 配置+无 pong 断开机制 3.0s 验；AC-S8b 100 并发×300s 全窗压测 p95=32.3ms≤200ms·0 断连）；docker 本机缺位=按判据表原生 Python 同判据直跑·compose 可选件未落（docker 到机再补）；未验路径如实记：60s 解禁不等待（muted_until 未来时戳断言）；件=src/sandbox/lobby/{server,sec_gate,store,test_client}.py+config.json（闸词表/风险文案/AI 标识=JSON 数据件·遵编码律）；依赖：无；来源=ledger P-2026-09-24-47；落点=src/sandbox/lobby/
- [x] P-2026-09-24-42 转办半项①：BLUEPRINT §四价目「成交执行面」分工注记（全部价目=店内闭环+外部成交与算力经济归 BigCompute·引用其 BLUEPRINT 边界节不复制）——扫描步入板即执行 [done 2026-09-24]
- [x] P-47-1 业务 API 五件之一：大厅 WebSocket 规格+骨架（判据预注册先行）——规格半件 [done 2026-09-24]（`docs/spec/lobby-websocket-spec.md`·判据预注册 AC-S1~S10+AC-P1~P5+合规四件套齐）；骨架半件 [done 2026-09-24]（P-47-1b·判据自验 10/10 全过）；来源=ledger P-2026-09-24-47
- [x] P-47-2b 代币双式账本沙箱骨架（`src/sandbox/ledger/`：schema.sql+ledger.py+reconcile.py+test_ledger.py·按 `docs/spec/token-ledger-spec.md` AC-L1~L11 逐条实现+自验·原生 Python 直跑；config.json 参数占位值全标 [needs-CEO]；AC-L8 闸引用=大厅闸产物 AC-S4）——来源=P-47-2 规格；落点=src/sandbox/ledger/ [done 2026-09-24] 判据自验 11/11 全过：AC-L1 应用层+库层双验（raw SQL 绕应用注不平衡笔=关账触发器 T2 拒+整笔回滚·1 分录笔拒）；AC-L2 超额花费触发器拒且余额不变+equity:auth=−300 恒负；AC-L3 同笔重放拒（内容寻址 tx_id·SQLite 先报 UNIQUE(ref,ref_type)=E_REF_DUPLICATE·幂等机制同源·rows-kept=1）；AC-L4 同源二发拒；AC-L7 cap=用户×动作×日口径 −1/0/+1 三点踩界（score1/cap11·11 落 1 拒）；AC-L8 未过闸 ref 拒+过闸后放行+闸未接线 serve 拒启 E_GATE_OFFLINE（引用 lobby sec_gate 件不复制）；AC-L9 source_ai 服务端权威+账单「AI 判定」标识；AC-L10 balance/bill disclaimer 常驻；AC-L11 无 census 绑定不建户不发放；AC-L5/6 reconcile 八查干净 PASS exit0+篡改注入（余额+7/删过闸回执）→check3/4/6 FAIL exit2；过程如实记：修 ensure_account 绑定校验次序 bug+AC-L7 用例改单动作踩点，两处修后全绿；依赖：零外采（纯标准库·三问门未涉）
- [ ] P-47-1c 大厅沙箱城市面扩展（AC-S11~S13：census 查询白名单断言/化身注册 intake 队列+受理回执/参观只读 read API+`:ro` 写试拒——ledger P-2026-09-24-52① 吸收件的实现增量）——来源=lobby spec v0.2；落点=src/sandbox/lobby/
- [x] P-47-2 代币双式账本 schema+对账脚本设计（纯内循环·不提现不外流·BLUEPRINT §五.4）——规格半件 [done 2026-09-24]（`docs/spec/token-ledger-spec.md`·AC-L1~L11+AC-LP1~LP4 判据预注册先行+合规四件套齐；双式=equity:auth 权益账户法·零和+授权两恒等式可机验；结构性禁令=无 withdraw/transfer-out/法币动词双保险；身份绑定 AC-L11=census 化身 ID 引用·P-52① 吸收；骨架半件=P-47-2b 拆细顶行）；来源=ledger P-2026-09-24-47+P-53①；落点=docs/spec/
- [ ] P-47-3 UGC+msgSecCheck 管道设计（前置闸合规面·未接内容安全=大厅禁开门·BLUEPRINT §五.3）——来源=ledger P-20260924-47；落点=docs/spec/
- [ ] P-47-4 19.9 支付对接设计（微信支付商户 API·商户号=CEO 物理件未到=设计先行·类目已代决 D2=非游戏类目小程序+虚拟支付）——来源=ledger P-2026-09-24-47；落点=docs/spec/
- [ ] P-47-5 权益/月卡面设计（体验卡 ¥19.9/城主卡 ¥49.9/共创者卡 ¥99 三档·BLUEPRINT §四 C2）——来源=ledger P-2026-09-24-47；落点=docs/spec/
- [x] §四「无人值守慢直播」行注记（BLUEPRINT §四 直播形态 1——开播前必加平台政策风险注=封禁级·patrol-4 E2③：无人值守挂播=平台严禁，改有人值守/开播策略以 BigCompute 风控为准）——本司宿主落（=ledger P-2026-09-24-42 @BigDomain 转办半项）[done 2026-09-24]
