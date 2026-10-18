# trim_state_R2025.py - same-round wording compression of the
# R2025 round line just appended by gen555 (post-fold state
# measured 78595B, 95B over the 78500B line). Only the round line
# written this very round is touched - zero history rewrite. Each
# replacement must hit exactly once; json.loads validates before
# write-back. Pure ASCII source.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")

with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

pairs = [
    ("信封/块/行/totals 四键集恰定+单源交叉〔每块==honor_yearbook 去 disclaimer dumps 逐字节〕+双调 dumps 逐字节同一〕",
     "四键集恰定+单源交叉〔每块==honor_yearbook 去 disclaimer〕+双调同一〕"),
    ("重启后 2026 块活态续接〔erin 4×poll 20 分榜首·re-grant top-2 增量愈合 granted=1/already=1·2026 块 3 行 certified 3 board 5〔aaron 掉出 top-2 仍保年册行=永久证律跨重启存活〕+2027/2025/2028 块字节冻结+零缓存〕",
     "重启后 2026 块活态〔erin 4×poll 20 分榜首·re-grant 增量愈合 granted=1/already=1·2026 块 3 行 cert3 board5〔aaron 掉出 top-2 仍保年册行=永久证律〕+2027/2025/2028 块冻结+零缓存〕"),
    ("重启后 2027 块续接+2026 块冻结〔frank 4×poll 20 分 2027 榜首·re-grant granted=1/already=1·2027 块 3 行+2026 块字节冻结=跨读隔离+totals {4,6,8,4}〕",
     "重启后 2027 块续接〔frank 4×poll 20 分榜首·re-grant granted=1/already=1·2027 块 3 行+2026 块冻结=跨读隔离+totals {4,6,8,4}〕"),
    ("门族跨重启同码〔非 iterable 6/6+坏年 9/9+重复年全拒 E_HC_BAD_ARGS+board_calls==0 门前拒零引用调用+探针批表计数恒定〕",
     "门族跨重启同码〔非 iterable 6/6+坏年 9/9+重复年全拒 E_HC_BAD_ARGS+board_calls==0+探针批表计数恒定〕"),
    ("+卫生〔产品四件 sha 双证+套件纯 ASCII 0 非ascii+零网络 import+yearbooks_combined 方法体零写语句 inspect 机检+世界 tmp 仓外〕",
     "+卫生〔产品四件 sha 双证+套件纯 ASCII+零网络 import+方法体零写语句 inspect 机检+世界 tmp 仓外〕"),
    ("SUITE PASS 7/7 首跑一处证据格式化缺陷〔dict 行 tuple 下标〕同轮修后净跑·模块本体首验即净+双跑 stdout LF 归一逐字节同一 sha16 cee8e630e7bc27be bytes=4009〔evidence_R2025.py subprocess 字节捕获〕",
     "SUITE PASS 7/7 首跑一处证据格式化缺陷同轮修后净跑·模块本体首验即净+双跑 stdout LF 归一逐字节同一 sha16 cee8e630e7bc27be〔evidence_R2025.py 字节捕获〕"),
    ("GORD 尾行新于基线检出=集团 orders 尾 2026-10-18 17:20 CEO 定案行〔bm-d 算力大脑·硬件采购窗：CPU=E5-2696v2 ×2 已购定案+议题收窄令=之后硬件议题只讨论算力卡+算力卡队列·origin/main 面检出〔本地 worktree 尾 14:32 陈旧·scan GROUPSRC origin-main 口径〕·[via bm-a] 已收口行零 @BigDomain 执行面=知悉不动作·last_order 基线推进 17:20〕",
     "GORD 尾行新于基线检出=集团 orders 尾 17:20 CEO 定案行〔bm-d 算力大脑硬件采购窗：CPU=E5-2696v2 ×2 定案+议题收窄令=只讨论算力卡·origin/main 检出〔本地尾 14:32 陈旧〕·[via bm-a] 已收口零 @BigDomain 执行面=知悉·last_order 推进 17:20〕"),
]

for old, new in pairs:
    if text.count(old) != 1:
        sys.exit("FATAL: replacement target hit count %d for %r"
                 % (text.count(old), old[:60]))
    text = text.replace(old, new)

json.loads(text)  # raises on bad json

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)

final_bytes = len(text.encode("utf-8"))
print("TRIM-OK pairs=%d final=%dB" % (len(pairs), final_bytes))
if final_bytes >= 78500:
    sys.exit("FATAL: still over the 78500B line")
