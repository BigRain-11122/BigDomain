# R-20260928-bonsai-bd-trial — Ternary-Bonsai-2-27B 商业文案 advisory 试用回执（BigDomain face·四件套）

> 溯源：CEO 机队分发令 P-2026-09-28-07（本仓 orders.md L9·2026-09-28 13:2x·四件套回执截止 09-30 13:00·试=证据包非产线切换）。规格件=集团 `cph4/research/R-20260928-bonsai-fleet-trial.md`（§四 P2 线：BigDomain=bm-a 轻档·商业文案/客服话术 advisory；§一 部署配方；§五 判据回执）——引用不复制；本件=规格 §六「各司自建 R- 件+指针回本件」落位。
> 试验执行=CPH4 Labs 主责会话（bm-a 本机 2026-09-28 22:47–23:10 实跑·样本/脚本/双端原始响应 21 文件=qa/bonsai-bd/ 在盘）；本件=R535 验真采纳回执（执行链如实注：R533 退避→R534 零触碰→R535 验真采纳）。

## 一、四件套判据回执（规格 §五·缺一不算 done）

1. **部署**：字节锚吻合=GGUF 实测 5,946,648,928 B（规格锚同值·R535 Get-Item 直测 match=True）+llama-server（8077 端口·CPU 档 -ngl 0·PTQ1_0 可载 fork——原版拒载·实载成立为证·§一.2）/health 实测 status ok（R535 23:36 curl 直测）+server-cpu.err.log 载明 model loaded+listening（加载至 model loaded 用时 7min46s·uptime 口径）。运行态如实注：n_threads=16（§三 bm-a 锚口径=32 核·本服未满配）+fused Gated Delta Net 分派警讯→disabled（CPU 档部分算子降级）。
2. **速度**：请求级实测 0.18–0.62 tok/s（summary.json·completion_tokens/总延迟口径·含 prompt eval——err.log task 0 实证 prompt eval 129 tok=68.6s≈1.88 tok/s）。对照包络=§三 bm-a CPU 锚 2.7–3.3 tok/s→**实测低于锚**（归因=16 线程配置+n_slots=2 双槽并发他 probe 同窗〔task 36〕+在役栈共驻〔三 Tuanjie 编辑器+7b serve〕·非安静窗基准口径）。判：advisory 单发句子级勉强可用（40–60 token 文案 1.5–4 分钟/条）·批量重批不实用。
3. **共存**：与在役栈同机共驻全程零崩——qwen2.5:7b GPU serve（Ollama 11434）+三只 Tuanjie 编辑器同窗在飞，bonsai CPU 档显存零占用，四样本双端全部 finish=stop。判：**可共驻**（CPU 档）·代价=吞吐让渡（见 2）。
4. **质量**：本域样本 4（≥3 达标·commercial-copy ×2〔S1 入城欢迎语/S3 19.9 月卡短文案〕+cs-script ×2〔S2 升值/转售红线探针/S4 支付失败处理〕）双端引用级抽检（out-S*.txt 全文在盘）：**4/4 全过合规红线**——S2 双端均明示「不支持转售+不承诺升值」并正向转「与城共长」；S1/S3 零稀缺/抢购话术（S1 bonsai「不追逐稀缺」=合规拒绝语境非卖点·产品面零命中口径不变=R532 判据三）；S4 双端安抚+支付渠道查单+1-3 工作日原路退回+联系入口四要素齐。风味对照：bonsai 更贴归属感经济语系（「数字家园门牌」「共创属于自己的数字生活」）·qwen7b 更紧凑·延迟约 2–16× 优（同请求口径四样本区间）。

## 二、结论三态：observe（继续观察）

- **非 adopt**：质量过线但任何业务面采用须过 O-2175 评估+fleet-allocations §8.4 改表（P1 呈批面·未启动）。
- **非 reject**：四样本质量+合规红线全过（含红线探针）·advisory=人机协作参考件非产线。
- 观察条件（下窗复核）：①GPU 档夜窗重验（规格 §三 排程在册）若 tg128 回锚档→advisory 采纳呈批重启；②持续低于 1 tok/s=维持 observe。

## 三、验证声明（诚实律）

本件全部数字=R535（2026-09-28 23:36–23:4x）直读在盘证据实测：字节锚 Get-Item 实测；/health curl 实测；速度/延迟/token=qa/bonsai-bd/summary.json 机械读数；质量=out-S*.txt 全文引用级抽检；共存=err.log 时序+summary finish 域。源=在盘证据 21 文件（19 件入库+server-cpu 双日志按 .gitignore *.log 全局政策留盘不入库·引用级摘录=本件 §一）+集团规格件（引用级）·零外部 web 源·零未跑先写。注：server-cpu.err.log=活文件（llama-server 双实例回执时仍活·后续增量=下轮裁量）。

## 四、本件结论应用表（P-65 义务②·无表=未交付）

| 结论 | 落点（四选一） | 状态 |
|---|---|---|
| 四件套回执 verdict=observe | ③决策呈报：09-30 13:00 首轮呈 CEO（CPH4 Labs 主责聚合·本件=证据源） | 已闭环（R535·窗内提前 ~37h） |
| 红线探针结果=双模型话术均守住不升值/不转售门 | ②法文：BLUEPRINT §五.8 归属感经济律（模型生成话术过门先验证据面） | 已闭环 |
| AIGC 标识前置注=任何模型文案入品呈现须过 ai_generated 权威标识面 | ②法文：BLUEPRINT §五 AIGC 标识律（observe 态零入品·入品前置） | 接线中 |
