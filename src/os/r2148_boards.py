"""R2148 board closeout: tick the claimed explore row and add the
backlog line with the measured verification numbers."""

import io
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"

QUEUE = os.path.join(ROOT, "state", "queue", "explore.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")

HEAD = "- [ ] P3 explore 自补种并同窗认领（R2148）"

DONE_NOTE = (
    " [done 2026-10-27 R2148] 产品=apimarket.py `api_similar_listings"
    "(listing_id, limit=None, include_delisted=False)`："
    "候选集=head 生效品类桶减自身，全序 (价格距离升, 现价升, listing_id 升)；"
    "十二键信封 + 十三键行（price_delta/abs_price_delta 派生）；head 永不在自身行内；"
    "价走 _current_price、均分走 _agg_rating、净售出走 _supply_full、标题走 "
    "_metadata_state 四缝，改价/改评/退款/补货/改标题即刻改邻居集且挂牌行零改写；"
    "未分类 head 只招未分类件；退役候选缺省排除、开关保留带戳、退役 head 仍可读；"
    "limit 取最近 head 的 N 件而 total 报全量、越界钳制；门序 挂牌形→存在→limit 形→"
    "include_delisted 形（未知挂牌叠坏 limit/坏 flag 仍答 UNKNOWN_LISTING）；"
    "拒绝零行零 token；纯读跨重启字节同一。"
    "证据=套件 SUITE PASS 8/8 双跑 rc=0/0 证据件逐字节同一 sha16 "
    "`de2a2967933737d1`（qa/apimarket-similar-R2148-a.log / -b.log·2052B each·"
    "单写者 utf-8 LF 零 CR 无 BOM）；接线 ledger-apimarket-similar(8)；"
    "六条相邻套件回归全绿（search/searchstock/category/categoryrev/"
    "listingposition/supply 各 8/8）；全量电池 RUNNER PASS 351/351 套件 + 控制 7/7 "
    "636.6s（qa/reconcile-all-R2148.log·4192 行·688996B）并回收 803 个世界 287.53 MiB"
    "（本窗同时兑现 R2147 遗留的电池窗）；矩阵 351/2916 --check 逐字节同一。"
    "诚实注=①首版套件把「退役 head 的缺省邻居集」写成空集，实测在架邻居正确留存，"
    "故修测试不改判据；②电池经流式驱动带 scratch stdout tee 启动，那份 scratch 不作证据，"
    "权威证据为上面引用的单写者件；③本窗套件未发现产品缺陷。\n"
)

BACKLOG_ROW = (
    "- [x] P3 explore 自补种并同窗认领（R2148）apimarket **同类近邻面**"
    "（api_similar_listings）——缺口实证：所有发现门都要求调用方先说清条件"
    "（api_search 要关键词/卖家/价带/品类，api_categories 答桶的构成，"
    "api_category_demand 答卖不卖得动，api_listing_position 答桶内排第几），"
    "没有任何一面回答买家看完一件之后最自然的「还有哪些跟这件差不多」，"
    "调用方只能自己取品类与现价再拼搜索再手工排序。"
    "判据 AC-AMSI1..AC-AMSI8 预注册于 state/queue/explore.md 同名行（"
    "**先于代码**：六锚 git grep -F 对 HEAD 零占用 rc=1 实测 2026-10-27）。"
    "[done 2026-10-27 R2148] 产品=apimarket.py `api_similar_listings`："
    "生效品类桶减自身的候选集、按价格距离全序（距离升→现价升→id 升）、"
    "四缝联动（现价/生效星/净售出/生效标题）、未分类零跨桶、退役开关与退役 head 可读、"
    "limit 取最近 N 而 total 报全量、门序挂牌→存在→limit→flag、拒绝零行零 token、"
    "纯读跨重启同一。证据=套件 SUITE PASS 8/8 双跑证据件逐字节同一 sha16 "
    "`de2a2967933737d1`（qa/apimarket-similar-R2148-a.log / -b.log·单写者 utf-8 LF）；"
    "接线 ledger-apimarket-similar(8)；六条相邻套件全绿；"
    "全量电池 RUNNER PASS 351/351 + 控制 7/7 636.6s（qa/reconcile-all-R2148.log·"
    "同时兑现 R2147 遗留电池窗）+ TMP RECLAIM 803 世界 287.53 MiB；"
    "矩阵 351 套件 / 2916 判据 --check 逐字节同一。"
    "诚实注=首版套件把退役 head 的缺省邻居集误写成空集，实测在架邻居正确留存，"
    "修测试不放宽判据。\n"
)

text = io.open(QUEUE, encoding="utf-8").read()
idx = text.rfind(HEAD)
if idx < 0:
    raise SystemExit("queue row not found")
end = text.index("\n", idx)
row = text[idx:end]
if not row.startswith(HEAD):
    raise SystemExit("unexpected row head")
new_row = row.replace("- [ ]", "- [x]", 1) + DONE_NOTE.rstrip("\n")
text = text[:idx] + new_row + text[end:]
io.open(QUEUE, "w", encoding="utf-8", newline="\n").write(text)

board = io.open(BACKLOG, encoding="utf-8").read()
marker = "# BigDomain 认领工作板（backlog）\n"
pos = board.index(marker) + len(marker)
board = board[:pos] + BACKLOG_ROW + board[pos:]
io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(board)

print("queue row ticked, backlog row inserted")