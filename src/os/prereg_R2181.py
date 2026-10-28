"""R2181 pre-registration: write the AC-MSC criteria into the R2178
explore-queue seed row (3/10) BEFORE any product code exists, and add
the claim row to the top of the backlog claim board.

Honesty law: this script touches only the two md boards.
"""

import io
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

CRITERIA = (
    "判据 AC-MSC1..AC-MSC8 预注册于本行且先于代码（\n"
    "  **AC-MSC1 契约与诚实空**=信封恰十二键 {month_count,seller_count,"
    "listing_event_count,relisting_event_count,relisting_seller_count,"
    "repeat_seller_count,repeat_rate,returning_event_count,first_month,"
    "last_month,disclaimer,months}·行恰九键 {month,seller_count,"
    "new_seller_count,returning_seller_count,listing_event_count,"
    "relisting_event_count,new_event_count,returning_event_count,"
    "avg_events_per_seller}·空市场诚实空（month_count 0 / months [] / "
    "first_month 与 last_month 均 None / repeat_rate None）；\n"
    "  **AC-MSC2 事件口径**=事件集由两个存储直读合成：每个 "
    "apimarket_listings 行的 listed_utc 计一条首挂事件、每个 "
    "apimarket_relistings 行的 relisted_utc 计一条复挂事件；卖家取事件行的 "
    "dev_account；relisting_event_count 是当月复挂事件数且恒 ≤ "
    "listing_event_count；\n"
    "  **AC-MSC3 队列归属**=卖家队列月=其全史最早事件月（含复挂，"
    "早于首挂戳的复挂按戳算）·当月 new_seller_count 为队列月==当月的 "
    "distinct 卖家数、returning_seller_count 为其余·每月 seller_count=="
    "new_seller_count+returning_seller_count·信封 repeat_seller_count 为事件跨 "
    "≥2 个不同月份的卖家数、repeat_rate==repeat_seller_count/seller_count"
    "（零卖家时 None）·relisting_seller_count 为至少有一条复挂事件的 "
    "distinct 卖家数；\n"
    "  **AC-MSC4 守恒**=每月 listing_event_count==new_event_count+"
    "returning_event_count 且 ==Σ(该月逐卖家事件数)；信封 "
    "listing_event_count==Σ 行 listing_event_count；信封 "
    "relisting_event_count==Σ 行且 ≤ listing_event_count；\n"
    "  **AC-MSC5 月度与排序**=月键取戳前 7 字（YYYY-MM）·rows 按 month 升序·"
    "只有发生过事件的月份出现（零事件月不造零行）·first_month/last_month 恒 "
    "== rows 首尾·退役与售罄不是事件（只有上架与复挂入队）；\n"
    "  **AC-MSC6 正交**=本面纯读、不新增表、不改任何既有面输出；"
    "调用前后 api_market_buyer_cohort / api_market_buyer_retention / "
    "api_relist_gap / api_listing_lifecycle 四面的同参输出逐字节同一；\n"
    "  **AC-MSC7 纯读与确定性**=三次同参调用逐字节同一·调用前后全部 "
    "apimarket_* 表摘要与 ledger_tx 集逐字节不变、零 token 移动·面体无 "
    "INSERT/UPDATE/DELETE·不接受参数（带参调用 TypeError 而非静默忽略）；\n"
    "  **AC-MSC8 跨重启与接线**=两次全栈重启后三实例（单卖家多月／多卖家含"
    "复挂／空市场）判据面逐字节同一；产品源 sha256 前后同一；接线 "
    "reconcile_all 在册 ledger-apimarket-sellercohort(8)；套件源纯 ASCII/LF；"
    "零新增第三方 import；shipped config 零改动。\n"
)

CLAIM = (
    "- [ ] P3 explore 队头认领（R2181·承 R2178 补种 3/10·判据 AC-MSC1..AC-MSC8 "
    "预注册于 state/queue/explore.md 同名行且先于代码）：apimarket **卖家首挂队列"
    "留存面**（api_market_seller_cohort）——买家侧队列（api_market_buyer_cohort／"
    "api_market_buyer_retention）做全了，卖家侧只有终身视角（api_repeat_purchase）"
    "与总额（dev_sales_board），没有任何一面回答「某月首次上架的卖家之后还在上架吗」。"
    "R2181 落产品面 + 套件 8/8 双跑 + 电池与矩阵收口（承 R2180 记账债）。\n"
)


def main():
    path = os.path.join(BASE, "state", "queue", "explore.md")
    text = io.open(path, encoding="utf-8").read()
    marker = "去重前置：api_market_seller_cohort"
    assert text.count(marker) == 1, "seed row marker not unique"
    idx = text.index(marker)
    text = text[:idx] + CRITERIA + text[idx:]
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)

    bpath = os.path.join(BASE, "src", "os", "backlog.md")
    btext = io.open(bpath, encoding="utf-8").read()
    lines = btext.split("\n")
    at = 0
    for i, line in enumerate(lines):
        if line.startswith("- ["):
            at = i
            break
    lines.insert(at, CLAIM.rstrip("\n"))
    io.open(bpath, "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines))
    print("preregistered AC-MSC1..8 and claimed backlog row at line %d"
          % (at + 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())