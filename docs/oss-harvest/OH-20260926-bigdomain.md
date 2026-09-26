# OH-20260926-bigdomain — OSS 借力首窗切片件（BigDomain）

- **窗**：首窗 2026-09-26 21:40 → 2026-09-29 21:40（P-2026-09-26-08·正典=cph4/oss-harvest.md v1.0·T2 否决窗至 10-03）·交付 2026-09-26 ~22:10 +08:00（窗内提前 ~71h）
- **实搜面**（2 处实录·采时 2026-09-26 ~22:06 +08:00·UA=BigDomain-OSLoop·礼貌节流 3 次外部请求零登录墙）：
  - ①GitHub API search `q=invisible-watermark&sort=stars&per_page=5` → 5 结果全录：guofei9987/blind_watermark（14793★）/wiltodelta/remove-ai-watermarks（5681★）/ShieldMnt/invisible-watermark（1982★·2023-09 停更）/guofei9987/text_blind_watermark（1959★）/fire-keeper/BlindWatermark（1679★·GPL-3.0）
  - ②GitHub API search `q=wechat+pay+python&sort=stars&per_page=5` → **死面如实记录**：top5 全为无关污染结果（政治敏感件×3+组织主页+fork）·支付 SDK 线不硬闯留下窗直查
  - 许可验证面：`raw.githubusercontent.com/guofei9987/blind_watermark/master/LICENSE` 原文直采（MIT·头 400 字在案）
- **候选**：guofei9987/blind_watermark（https://github.com/guofei9987/blind_watermark · MIT · 14793★ · 契合点=AIGC 隐式标识盲水印·补 sandbox 隐式面零实现缺口）
- **采用→落点**：采用→①任务单 P-47-3c「AIGC 隐式标识能力验证件」（tasks.md+backlog 顶行·判据预注册认领轮先行）②司级采用登记簿首行（docs/oss-harvest/README.md）③集团注册表行（cph4/README.md）=跨仓写禁令·挂 P2 台账落位三选一裁决（HQ-FEEDBACK R318 在册）如实注
- **parked+理由**：text_blind_watermark（量产生成文本面未立项·现役 UGC 生成面显式 ai_label 已覆）｜ShieldMnt/invisible-watermark（2023-09 停更·健康门弃）｜fire-keeper/BlindWatermark（GPL-3.0·许可门禁入产品交付链）｜remove-ai-watermarks（反向件·移除 AI 水印与合规目标相逆）｜FACE2 支付 SDK 线（查询面污染+商户号=CEO 物理件未到+sandbox pay mock 自足〔AC-Y4 四坏例自造〕·留支付对接轮）
- **下窗指针**：次窗 09-29 21:40→10-02 21:40·线索=①支付线直查 wechatpayv3 仓绕开污染查询词②msgSecCheck 本地预筛词库面（降 API 调用成本）③城市共创区块图像素材工具线

## 一 五门评估（采用件：guofei9987/blind_watermark）

| 门 | 判定 | 证据 |
|---|---|---|
| 1 契合 | 过 | 替未来生产后端省自研盲水印轮子（CEO 三律②）；补隐式标识实现缺口——src/sandbox 实勘 grep `watermark\|隐式\|invisible`=零命中·ugc 显式面在册（config.json L63 ai_label_text「AI 整理」+pipeline.py L332 ai_label）·《标识办法》3-6 条隐式标识=全设计件合规必含面（BLUEPRINT §五生死线·T2 件 AC-H4 显式+隐式双轨面在册） |
| 2 反重复 | 过 | 三面查证：cph4/README.md 能力注册表 09-26 实勘无水印工具行+Art Assets 池（gaming/MiniGame/Art Assets·美术资产类非工具·oss-harvest §一定义）+司内清单（tools/skills 仅技能件·sandbox 五件无水印）=真缺口非双建 |
| 3 许可 | 过 | License 原文逐件直验=MIT（raw…/LICENSE·「MIT License Copyright (c) 2019…Permission is hereby granted, free of charge」）→直用类（CC0/MIT/Apache/BSD） |
| 4 健康 | 过 | stars=14,793·pushed=2026-03-25（半年内活跃）·open_issues=52（对 1.48 万★=低占比）非死项目 |
| 5 成本/安全 | 过 | 本地 Python 库纯本地图像运算零外发零网络调用（本地优先三问过）·非模型类 P-17 矩阵不涉零显存·依赖=常规科学计算栈·MIT 开源可审·后门面粗审无异常 |

三问门（OSS 寻源 web 直采）：必要=令文自证（P-2026-09-26-08「寻找开源社区」）；无本地替代（外部寻源无本地等效面）；宿主既有 urllib/curl 通道非新 API 接入——过门在案（BD-SD1 R266 先例口径）。

## 二 结论应用表（research-protocol §二.1 落点强制·无表=未交付）

| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 采用 blind_watermark（AIGC 隐式标识盲水印能力） | ①任务单 P-47-3c（tasks.md+backlog·被认领才算数）+司级登记簿行 | 接线中 |
| FACE2「wechat pay python」查询面污染 | ④判负留痕（弃用查询词·下窗直查仓） | 已闭环 |
| text_blind_watermark 等四件不采 | ④判负留痕（parked 理由见上行） | 已闭环 |
| 集团注册表行无法自写（跨仓写禁令） | ③决策呈报（HQ-FEEDBACK R318 P2 三选一连带） | 接线中 |

## 三 验证声明

读源：GitHub API search 2 查询+raw LICENSE 直采 1 次=3 次外部请求（2026-09-26 ~22:06 +08:00·UA=BigDomain-OSLoop·礼貌节流零翻页）。分级：候选五门证据=A 级直采（GitHub 官方 API 字段+raw 文件原文）；「查询面污染」=🟡存疑待证（top5 描述面判断·未深翻页）；本仓/集团在册锚=cph4/README.md·oss-harvest.md·BLUEPRINT §五·src/sandbox grep 实勘。判据=AC-OH1..OH5（backlog 本行预注册·自验全过）。
