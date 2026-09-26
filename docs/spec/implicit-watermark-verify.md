# implicit-watermark-verify — AIGC 隐式标识能力验证件（P-47-3c）

> 溯源：P-2026-09-26-08 开源借力机制令首窗采用落点任务单 P-47-3c（tasks.md+src/os/backlog.md）；OSS 采用件=guofei9987/blind_watermark 0.4.4（MIT·14793★·五门评估+司级采用登记=docs/oss-harvest/：OH-20260926-bigdomain.md §一 + README.md 采用行）。
> 判据预注册：AC-W1..AC-W4=src/os/backlog.md P-47-3c 行（R320 开单预注册草案·R321 认领轮定稿即册）。本件=docs/spec/ 第 9 设计件。
> 铁律注：**零生产代码零 schema**——本件=沙箱能力验证+设计注记；生产接线=bootstrap 期（§二），本件不动生产管道。

## 一、验证定位与结论（AC-W1）

- 验证环境：Windows 本机 Python 3.14.4·pip 本地装 blind_watermark 0.4.4（依赖 numpy 2.5.2+opencv(cv2) 5.0.0·本地纯图像运算零外发——OH 件五门之「成本/安全」门实证延续）。
- 水印载荷：256-bit 标签（SHA-256("BigDomain-AIGC-implicit-label-v1")·mode='bit'）；载体=确定性生成测试图 640×480（seed 固定可复跑）。
- 判据套件：src/sandbox/watermark/test_watermark.py（实跑结果=§五 对照行）。

**结论（校准+套件实测）**：
1. **清洁往返（AC-W1a）**：嵌入→提取精确一致（exact·bit 级零误码）。
2. **压缩鲁棒例（AC-W1b）**：JPEG 再存 q=90 → 提取精确一致；校准实测 q=70 起 ber=0.027 退化、q=50 ber=0.0625、q=30 ber=0.3359（如实记：强压缩下非无损）。
3. **裁剪鲁棒例（AC-W1c）**：中央裁剪保 85% → **直接提取退化**（校准 ber≈0.52·块网格被破坏·诚实负结果如实记）；经库官方 recover.py 路径（模板匹配定位 score=1.000+原图画布重建）→ 恢复后提取精确一致；校准 70% 裁剪同过（loc 定位全对·两档皆 exact）。
- **诚实注**：裁剪直提不成立；recover 路径前提=验证方持有嵌入原图（平台溯源场景成立——平台即嵌入方持库；第三方无原图直提裁剪件不保证）。隐式标识定位=**溯源辅助面非唯一防线**，显式轨（§二）恒在。

## 二、双轨并呈设计注记（AC-W2）

- **显式轨（在册）**：ugc 沙箱 config.json L63 `ai_label_text`「AI 整理」+ pipeline.py L332 `ai_label` 草稿字段——《标识办法》第 3-5 条显式标识面（呈现面文案/角标）。
- **隐式轨（本件）**：blind_watermark 盲水印嵌入图像素材——第 3-6 条隐式标识能力面补缺（OH 反重复门实证：src/sandbox grep `watermark|隐式|invisible` 零命中=真缺口非双建）。
- **双轨并呈律**：生产后端图像素材输出面=显式（呈现面标识）+隐式（盲水印）**同呈**；文本面显式轨已覆（text_blind_watermark parked 理由沿用 OH 件·量产生成文本面未立项）。
- **生产接线=bootstrap 期**：接线点候选=生产后端图像输出管道（P-47-3 UGC 图像素材面/T2 呈现面/城市共创区块素材面）；本件零新代码零新 schema（反重复律·禁双建）——物理件到位后另开生产接线任务单，不在本件越权。

## 三、OH 证据链锚（AC-W3）

| 锚 | 位置 | 机械可验 |
|---|---|---|
| 候选+许可 | OH-20260926-bigdomain.md 头部（guofei9987/blind_watermark·MIT·raw LICENSE 原文直采验） | test_watermark.py AC-W3 |
| 五门评估 | OH 件 §一 表行 1..5（契合/反重复/许可/健康/成本安全逐门带证） | 同上 |
| 采用登记 | docs/oss-harvest/README.md 采用行（2026-09-26·落点=任务单 P-47-3c） | 同上 |
| 台账落位 | 集团注册表行=跨仓写禁令·挂 P2 三选一裁决（HQ-FEEDBACK R318 在册） | 不涉（集团面只读） |

## 四、合规四件套

1. **判据预注册**：AC-W1..W4=src/os/backlog.md P-47-3c 行（开工前先行注册；执行后自验对照见 §五）。
2. **AIGC 生成标识面**：本件主题=隐式标识能力（第 3-6 条）+与显式轨双轨并呈（§二）；全呈现面标识义务沿用 BLUEPRINT §五生死线（生成内容全呈现面标识）。
3. **msgSecCheck 前置闸**：本件零文本内容产出（纯图像能力验证）不新开内容面；生产接线时图像素材输入/输出仍走五件同源拒启闸（AC-S4/L8/U2/Y8/M7·IF-8 单源——**未接线=禁开门非降级**）。
4. **非投顾常驻面**：不涉（无金融建议面）；disclaimer 常驻口径沿用 integration-deepening-spec §七清单。

## 五、判据自验对照（执行后如实记·AC-W4 送达=本表+backlog done 行+state log R321 行+commit 含 P-2026-09-26-08）

| AC | 自验 | 过 |
|---|---|---|
| AC-W1 | W1a 清洁往返 exact；W1b JPEG q=90 提取 exact（q≥70 退化阈值如实记）；W1c 裁剪 85% 直提退化如实记负+recover.py 定位 score=1.000 重建后提取 exact（套件实跑 SUITE PASS） | ✓ |
| AC-W2 | §二 双轨注记+显式轨行级锚（config L63/pipeline L332·套件机械验）+bootstrap 期接线注+零新代码零新 schema 断言 | ✓ |
| AC-W3 | §三 锚表+套件机械验（OH 五门行 1..5+候选 MIT+登记行 P-47-3c） | ✓ |
| AC-W4 | 送达三载体=backlog P-47-3c 行 [done 2026-09-26]+state log R321 行引用 P-2026-09-26-08+commit 消息含 P-2026-09-26-08 | ✓ |

**结论应用表**（research-protocol §二.1 落点强制·四选一）：

| 结论 | 落点 | 状态 |
|---|---|---|
| blind_watermark 能力验证通过（清洁往返+压缩/裁剪两鲁棒例·沙箱件在盘） | ②本司 backlog（R321 done 行）+P-2026-09-26-08 回执链（state log+commit·P-51 口径） | 已闭环 |
| 生产接线（图像输出管道挂盲水印） | ②bootstrap 期任务面（CEO 物理件到位后另开单）·零新代码纪律本件不接线 | 挂 bootstrap |
| 集团注册表行（cph4/README.md） | ③HQ-FEEDBACK P2 三选一裁决（R318 在册·跨仓写禁令如实注） | 待集团裁 |

- 更新记录：2026-09-26 首版（R321 当轮闭环·P-2026-09-26-08 首窗落点任务单·窗内提前 ~69h）。
