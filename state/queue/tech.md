# P2 技术深耕线队列（state/queue/tech.md·Self-Drive v2.0·常备 ≥10 条·2026-09-28 R532 建面）

- [x] state.json 再整编 R31（轮首 82,832B 越线在案·P-2026-09-25-18 ④第三十一刀·次轮首项）——[done 2026-09-28]（R532 当轮执行 82,832B→74,062B·复选框漏翻=R549 修账如实注·后继 R32/R33 已列 export results 在册）
- [x] 五沙箱判据复跑+对账 dry-run 节律件（68/68 全绿基线·D-7 预演复跑 R420 先例）——[done 2026-09-29]（R549 复跑 68/68 全绿复现〔ledger 11/11+ugc 12/12+pay 16/16+member 16 判据 25 断言+lobby 13/13·对账+篡改面套内实测 AC-L5/Y12/M14〕·S8b 全保真负载复测拆分至 backlog 顶行并窗 #4）
- [ ] docker-compose 五沙箱一键联跑（docker 缺位期=原生 Python 直跑基线在册·docker 到位切换）
- [x] lobby WebSocket 阶梯压测剖面（AC-S8b 100 并发 p95=32.3ms 基线→250/500 并发扩展例）·R549 承接注=S8b 100×300s 基线复测（共驻 llama 负载漂移面·backlog 顶行拆分行）与 250/500 扩展同窗执行——[done 2026-09-29]（R550 后台链三跑全保真落成·qa/load-S8b-R550.log：N=100 p50=42.6ms p95=304.0ms max=635.3ms alive=100 closed=0·N=250 p50=178.5ms p95=262.6ms max=804.1ms alive=250 closed=0·N=500 p50=771.9ms p95=1061.9ms max=2098.7ms alive=500 closed=0·三跑全越 p95≤200ms 闸判负留痕合法〔AC-TQ2a..c〕·稳定面全保〔alive==N·closed=0·500 并发零断连〕·N=250 p95 反低于 N=100=尾部主因共驻 CPU 调度非并发数〔AC-TQ2e 判负归因观察〕·逐跑 exit=1 在册〔AC-TQ2d〕·AC-TQ2f 收账六面由 R551 补齐〔R550 会话 03:49 截断·兑现滞后一轮如实注〕）
- [ ] S8b 静机控制复测归因件（R550 判负行归因观察直接后继·静机复跑 N=100 基线比对=漂移主因共驻 CPU 调度 vs 并发数裁定·窗控=bonsai 呈批窗 09-30 13:00 后·判负留痕合法）
- [ ] 支付 V3 回调验签沙箱实测件（benchmarks 4012791902/4012075249 采集面→pay 沙箱验签器接线）
- [x] blind_watermark 鲁棒性扩展三例（缩放/椒盐/二次重压缩·P-47-3c 后继·判负留痕合法）——[done 2026-09-29]（R552 落成·扩展套件 src/sandbox/watermark/test_watermark_robust.py 复用既有套件 helpers·AC-EX0..4 预注册先于执行〔backlog R552 行〕：控制锚干净往返 exact 前提下四扰动例全测量〔SUITE PASS 6/6·exit=0〕·判负读数=缩放 0.5×/2.0× ber=0.5195/0.5000〔DCT 块同步双双向毁伤〕·椒盐 d=5% ber=0.0273〔近存活〕·二次重压缩 q90×2 ber=0.0156〔近存活·vs W1b 单次 q90 exact=漂移由二次量化引入〕·证据 qa/watermark-robust-R552.log·首跑 harness bug〔AC-EX4 证据面取值错〕修复后净跑·两跑测量逐位一致=确定性复验在案）
- [ ] release-gate 三器打包预演（secret-scan+release-scan+白名单产物树·bootstrap 前置留窗项）
- [ ] scan_five_still.ps1 判读面回归用例固化（[ORD]/[TREE]/[QA] 三新面用例·R531/R530 改型后继）
- [ ] status-export self_drive 派生面回归维护（BD-PROP-001 实施后继·F3 零写死校验复跑）
- [ ] logs/ 整编工具链复用维护（压缩脚本族先例沿用·R31 起继续·archive append marker 链）
