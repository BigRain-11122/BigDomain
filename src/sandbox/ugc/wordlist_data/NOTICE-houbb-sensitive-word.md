# NOTICE — sensitive_words_dict.txt 来源与许可声明（Apache-2.0 §4 携带件）

- **数据来源**：houbb/sensitive-word（https://github.com/houbb/sensitive-word）`src/test/resources/dict_v20240407.txt`（master 分支 commit `b86249ddfa381b426359a420623486e099c2092d`）
- **采时**：2026-10-01 ~21:0x +08:00（只读 raw.githubusercontent.com 直采·verbatim 未改动·1,180,575 字节与源仓 git trees API 报告一致）
- **许可**：Apache License 2.0（随件原文=同目录 `LICENSE-Apache-2.0.txt`·源仓 LICENSE.txt verbatim 20,966 字节·R837 API spdx + raw 原文双源验复引）
- **采用面**：仅词库数据面（65,143 行敏感词表）+ allow-word 豁免机制设计参照（源仓 `sensitive_word_allow.txt` 同概念）；**Java 库本体不采用**（Python 栈零引入·OH-20261002 五门「成本/安全」行在册）
- **接线面**：src/sandbox/ugc/wordlist.py（自写 Python trie 匹配器·stdlib 零依赖）→ ugc 管道 L1 本地预筛（生产序=L1 本地预筛→L2 msgSecCheck 三态·L2 真实接线仍 blocked on 平台资质=CEO 物理件 AC-UP1）
- **采用登记**：docs/oss-harvest/README.md 采用表（2026-10-01 行）·切片件=cph4/oss-harvest/OH-20261002-bigdomain.md（R837）·采用时点五门复验=qa/prefilter-R838.log
