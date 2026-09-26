# BigDomain 任务板

> 认领制（venture 司内九件）。由 CPH4 Labs 巡检批代建（2026-09-24）。宿主会话接管后按 backlog 制自管。

- [x] P-47-1 业务 API 五件之一：大厅 WebSocket 规格+骨架（判据预注册先行）——规格半件 [done 2026-09-24]（docs/spec/lobby-websocket-spec.md）；骨架半件 [done 2026-09-24]（P-47-1b·AC-S1~S10 自验 10/10）；来源=ledger P-47
- [x] P-47-1b 大厅 WebSocket 沙箱骨架（docker-compose 本地沙箱·按 spec 判据 AC-S1~S10 实现自验）[done 2026-09-24]（docker 缺位=原生 Python 同判据直跑·10/10 全过·AC-S8b 100 并发×300s p95=32.3ms）；依赖：无（沙箱先行）；来源=ledger P-47
- [x] P-47-2 代币双式账本 schema+对账脚本设计——[done 2026-09-24]（docs/spec/token-ledger-spec.md·AC-L1~L11+AC-LP1~LP4 判据预注册先行+合规四件套齐）；来源=ledger P-47+P-53①
- [x] P-47-2b 代币双式账本沙箱骨架（按 spec AC-L1~L11 逐条自验）——[done 2026-09-24]（src/sandbox/ledger/ 五件·AC 自验 11/11 全过·reconcile 八查干净 PASS/篡改 exit2 双跑在案）；来源=P-47-2 规格
- [x] P-47-1c 大厅沙箱城市面扩展（AC-S11~S13·P-52① 吸收实现增量）——[done 2026-09-24]（city.py+city_data/ 样件+config city 节；判据自验 13/13：S11 白名单查询深水区零泄漏+荣誉席零渲染·S12 intake 队列+evt_id 回执·S13 HTTP 只读 API+405/404+只读副本写试拒）；来源=ledger P-52①
- [x] P-47-3 UGC+msgSecCheck 管道设计（前置闸合规面）——规格半件 [done 2026-09-24]（docs/spec/ugc-pipeline-spec.md·AC-U1~U12+AC-UP1~UP5 判据预注册先行+合规四件套齐）；骨架半件 [done 2026-09-24]（P-47-3b·src/sandbox/ugc/ 五件·AC-U1~U12 自验 12/12 全过·库层触发器执法四道+账本跨件联验）；来源=ledger P-47
- [x] P-47-4 19.9 支付对接设计（微信支付商户 API·商户号=CEO 物理件·类目已代决）——规格半件 [done 2026-09-24]（docs/spec/payment-integration-spec.md·AC-Y1~Y14+AC-YP1~YP6 判据预注册先行+合规四件套齐·双通道虚拟支付/标准商户+法币代币双域隔离）；骨架半件 [done 2026-09-24]（P-47-4b·src/sandbox/pay/ 五件·AC-Y1~Y14 自验 16/16 全过+reconcile 六查/四篡改族+账本对接面 share_from_pool 回归绿）；来源=ledger P-47
- [x] P-47-5 权益/月卡面设计——规格半件 [done 2026-09-24]（docs/spec/membership-spec.md·AC-M1~M16+AC-MP1~MP6 判据预注册先行+合规四件套齐·两域隔离〔次数≠代币〕+出生证永久+手动续费 MVP+优先筛选永不绕审）；骨架半件=P-47-5b 拆细行；来源=ledger P-47
- [x] P-47-5b 权益/月卡沙箱骨架（按 spec AC-M1~M16 逐条自验）——来源=P-47-5 规格 [done 2026-09-24]（src/sandbox/member/ 六件·判据自验 16/16 全过 25 断言；含 173402 死轮三残件接管复audit+两真 bug 修+三缺件补+pay 加法对接面两件；回归 pay 16/16+ledger 11/11+ugc 12/12 零回归；**P-47 五件全件收口**）
- [x] §四「无人值守慢直播」行注记（开播前必加平台政策风险注——封禁级·patrol-4 E2③）——本司宿主落 [done 2026-09-24]
- [x] P-47-3c AIGC 隐式标识能力验证件（guofei9987/blind_watermark 盲水印·P-2026-09-26-08 OSS 借力令首窗采用·五门评估=docs/oss-harvest/OH-20260926-bigdomain.md）——判据预注册认领轮先行（AC-W1 本地装+嵌入/提取往返+压缩/裁剪鲁棒两例/AC-W2 与 ugc 显式 ai_label 双轨并呈设计注记·零新代码零新 schema 纪律·生产接线=bootstrap 期/AC-W3 OH 件证据链锚/AC-W4 送达三载体）；来源=P-2026-09-26-08 首窗落点 [done 2026-09-26]（R321 当轮闭环：套件 src/sandbox/watermark/test_watermark.py SUITE PASS 5/5·设计件 docs/spec/implicit-watermark-verify.md·压缩例 q=90 exact+裁剪例 85% 直提退化如实记负+recover.py 恢复后 exact·显式轨锚 config L63/pipeline L332 机械验）
