# BigDomain 认领工作板（backlog）

> 认领制：自正典任务板 `tasks.md` 迁六件起版（CPH4 Labs 巡检批 2026-09-24 代迁）。取最上一条未完成项为当轮焦点；完成标 `[done 日期]` 并同步勾选 `tasks.md` 对应项；做不完拆细、剩余部分写回顶行；全部依赖 CEO 物理件的项=不可认领（如实待物理件，不造活）。
> 双板律：本板=认领/进度工作面；`tasks.md`=正典任务板。两板同六件起版，完成态两板同步。
> 集团转办扫描（见 `iteration_prompt.txt` 开轮五步②）新入项排顶行——ledger 未回执行 @BigDomain 转办（如 P-2026-09-24-42 的 §四价目「成交执行面」分工注记半项）由扫描步入板，不在此预录。
> 历史完成项归档：09-24/25 done 行全量迁 `docs/archive/backlog-done-2026-09.md`（原文全量保全·token 止血令 ④ AC-T3 配套件·R193）+09-26/27 done 行 27 条同档补迁（§R410 节·P-2026-09-25-18 ④第二刀·R410）+R410/R411 done 行 2 条再补迁（§R412 节·板规执法第三刀·R412）+R412 done 行 1 条再迁（§R413 节·板规执法第四刀·R413）+R413 done 行 1 条再迁（§R414 节·板规执法第五刀·R414）+R414 done 行 1 条再迁（§R415 节·板规执法第六刀·R415）；本板此后只留未完项与当轮完成项。

- [x] R552 认领：blind_watermark 鲁棒性扩展三例（tech 队列「鲁棒性扩展三例」项·P-47-3c 直接后继·纯本地沙箱·判据预注册先于执行——本行先落再动手）：AC-EX0=控制锚〔同 256-bit 标签嵌入→干净抽取往返须 exact·embed/extract 机能前提·此锚败=全套判负不采信扰动例读数〕；AC-EX1=缩放族〔0.5×与 2.0× bilinear 各一例·每例 exact 布尔+BER 双记·判负留痕合法〕；AC-EX2=椒盐族〔d=5% 一例·同标准双记〕；AC-EX3=二次重压缩族〔JPEG q90→重开→再存 q90 一例·同标准双记〕；AC-EX4=证据落盘〔qa/watermark-robust-R552.log 全输出+逐例判读行〔判负例同行带 BER·零静默跳例〕+套件 exit 码在册+tech 行标 done+state log 回执〕——[done 2026-09-29]（R552 当轮落成·SUITE PASS 6/6·exit=0·AC-EX0 控制锚 exact 全绿；四扰动例全判负留痕：缩放 0.5×/2.0× ber=0.5195/0.5000·椒盐 d=5% ber=0.0273·二次重压缩 q90×2 ber=0.0156〔vs W1b 单次 q90 exact〕；证据 qa/watermark-robust-R552.log 在盘·首跑 harness bug〔AC-EX4 证据面取值错〕修复后净跑·两跑测量逐位一致=确定性复验；详见 tech 行 done 注）
- [ ] bootstrap 对外打包件（**blocked on CEO 物理件**：服务器/域名/备案/商户号——到位后启动·如实待物理件不造活）：打包/镜像一律过集团 release-gate v1.0 闸 0~3（白名单产物树七禁+secret-scan+`Tools/release-scan.ps1` 三器 FAIL 即阻断+CEO 明示批准门）·部署律=服务器只拉私库镜像禁 clone 源码仓+城市数据 sparse-checkout 仅公开路径·首真实包=部署日回访（集团周轮执法抽查）——来源=ledger P-2026-09-24-66 转办①（2026-09-24 晚对外发布安全门立法·「各司打包脚本一律过本门」·R25 入册）；落点=部署链（bootstrap·BLUEPRINT §七 注记在案）
