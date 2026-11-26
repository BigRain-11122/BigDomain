# 重放凭据可否豁免 history-split（判据法决策件 v0）

- 轮次：R3521（2026-11-27）
- 面：`tools/preview_pair_census.py --admissibility`
- 现役律：`version-drift` 只解释、不豁免；只有 `one-derivation` 凭据可把 split 转 `channel-receipt`
- 本件性质：**提案 / 待裁**。本窗不改律、不改计数、不重派生落地页

## 一、现象（盘上实测，非推断）

四条 apimarket 面的两半落在不同提交：html 半全部来自 `700dd89a`（R3461 前门轮批量注入通道），json 半来自各自更早的生产器提交。

| 面 | json 提交 | html 提交 | 间隔 |
|---|---|---|---|
| apimarket-report-refunds | 6fb6c40b | 700dd89a | 749.7h |
| apimarket-report-buyerquestions | d3faa192 | 700dd89a | 742.4h |
| apimarket-report-questions | e0fd7251 | 700dd89a | 743.8h |
| apimarket-report-selleranswers | ce3583ca | 700dd89a | 742.2h |

四条全部已在 R3514..R3518 完成**历史生产器重放**：按 json 半所属提交的那棵树跑它自己的生产器，再用 `700dd89a` 当轮的通道注入，落地 html **逐字节相等（零归一化）**，json 半逐字节相等。凭据记录在 `preview/face-pair-receipt.json`，含 `historical.commit` / `json_byte_identical` / `landed_digests_agree` / `landed_html_sha256`（全 64 位绑定落地字节）。

**结论**：这四条不是「半派生落地」，是**生产器演化 + 后一提交统一注入通道**。清点面把它们计为 4 条历史分裂，是因为判据只认 `one-derivation`，不是因为证据缺失。

## 二、本窗测得的数字（一条命令可复核）

```
python tools/preview_pair_census.py --admissibility
PPC-ADMIT VERDICT PASS read_only=True splits=4 admitted=4 if_admitted=0 controls=3 checks=5
```

即：若律承认「逐字节重放凭据」，`history_split` 由 4 → 0；本窗**没有**改动清点面的 `history_split=4`（`--check` 仍报 `history_split=4 ... explained=11`）。

## 三、负控（证明判据不是装饰）

同一面在真实记录上跑三条负控，每条都是「只挪一个字段，其余照旧」：

| 负控 | 改动 | 必须读回 | 实测 |
|---|---|---|---|
| binding-digest-moved-one-hex | 把凭据 `landed_html_sha256` 首字符改掉 | `receipt-not-bound-to-landed-bytes` | PASS |
| json-claim-dropped | 把 `historical.json_byte_identical` 置 false | `json-not-byte-identical` | PASS |
| no-receipt-at-all | 没有凭据记录 | `no-receipt` | PASS |

再加上两条成立性闸：被豁免的行必须带 `historical.commit`（证据存在性），且其落地摘要必须等于**现在**盘上的文件摘要（凭据随字节失效）。五条检查任一不过，该面 `rc=2` 且不打印 PASS。

## 四、两个选项

**A（维持现律）**：4 条继续计为 split，`explained=11` 只作说明。代价：清点面永久显示 4 条「两半不同批落地」，而读者无法从计数分辨「未解释的分裂」与「已逐字节复现的分裂」。

**B（新增 `replay-reproduced` 类）**：承认「凭据 verdict=`version-drift` + `historical.commit` 非空 + `json_byte_identical` + `landed_digests_agree` + 全 64 位摘要绑定落地字节」为可豁免，split 4 → 0。前置条件：
1. 上述五条件缺一即驳回，驳回理由按名打印（本窗负控已证可达）；
2. 只认**记录在凭据件里**的重放，不认窗口口头宣称；
3. 一旦落地字节移动，凭据失效、该行自动回落到 split（绑定律现成）；
4. 冻结登记册（11 条 `frozen-excused`）语义不变，两条豁免路径互不覆盖。

## 五、为什么不能靠重派生「修」掉

重派生就是把今天的渲染器输出写到这两半上。落地页带着 `700dd89a` 那轮加入的通道块（7 条面共有的出厂面），而 HEAD 渲染器 schema 17 对落地 schema 6/11 —— 重派生会**删掉通道新增**，把一条可解释的历史差异换成一条真实的内容损失。故 B 是唯一不毁盘的收口路径。

## 六、裁决建议与边界

建议走 **B**，但它是「改一条已发布判据」的动作，按本板纪律（禁直接改判据凑绿）不在窗口内自行生效：须 L3 决策轮签发，签发后由窗口落一条带负控的判据臂并同窗重派生清点页与入口索引。

在签发前，本面保持只读、`if_admitted` 只报数不生效；任何人要复核只需跑第二节那一行命令。

非投顾提示：本页是构建状态面，不构成投资建议。
