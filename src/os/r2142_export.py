"""R2142 export refresh: merge the round payload into
docs/status-export.json and recompute the self_drive derived face with
the checker caliber (F3: derived counters come from the checker).

ASCII source, stdlib only, no network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

if BASE not in sys.path:
    sys.path.insert(0, BASE)
import check_export_consistency as C   # noqa: E402

EXPORT_TS = "2026-10-26T12:09:35+08:00"

CEO_FACE = {
    "current": "本轮把开发者 API 市场的发现面补齐了「只给我还能买的」这条轴："
               "售罄与有货不再同形，买家搜完可直接过滤到可买件或售罄件（后者正是"
               "卖家的补货队列）。",
    "latest_artifact": "src/sandbox/ledger/apimarket.py 的 api_search in_stock 过滤"
                       "+ qa/apimarket-searchstock-R2142-a.log（8/8 双跑）"
                       "+ docs/sandbox-suite-matrix.md（346 套件 / 2876 判据）"
                       " — 2026-10-26 12:09",
    "next_milestone": "48 小时内：跑完整全量电池（本轮预算未及），并把这轴接进"
                      "结算报告/看板；商户号仍未到，支付与权益设计件继续先行。",
}

OUT_NAME = "apimarket discovery availability axis (api_search in_stock)"

OUT_TEXT = (
    "R2142: the discovery face could filter by keyword, seller, price band,"
    " category and retired state, order by five modes and page, but a sold-out"
    " listing and a buyable one were byte-identical, so a buyer had to read"
    " every row and call api_supply per listing. api_search now accepts an"
    " optional bool-only in_stock that keeps the buyable rows (True) or the"
    " sold-out rows (False, the seller's restock queue) through the one scarcity"
    " seam, so a purchase, a refund and a restock move a listing across the"
    " filter in exactly the step they move api_supply.sold_out. Laws pinned by"
    " AC-AMAV1..AC-AMAV8: the legacy contract stays byte-identical when the"
    " filter is absent, the bool gate sits after the category gate and before"
    " paging/sort and fails closed with every table digest and the ledger tx set"
    " frozen, True plus False partitions the unfiltered set exactly, the axis"
    " composes with every other filter while paging totals derive from the"
    " filtered set, all five sort modes keep their total order over the subset,"
    " and honest empties, the retired-listing rule, cross-restart byte identity"
    " and the pure-read law all hold. Suite SUITE PASS 8/8 double-run"
    " byte-identical sha16 001304dcd96edb53"
    " (qa/apimarket-searchstock-R2142-a.log and -b.log); five adjacent suites"
    " rc=0 each; matrix 346 suites / 2876 criteria --check byte-identical.")

RESULT_TEXT = (
    "R2142: seeded and claimed a fresh P3 explore row in the same window with"
    " AC-AMAV1..AC-AMAV8 pre-registered BEFORE the code existed (four anchors git"
    " grep -F zero-occupancy, rc=1) and delivered the discovery availability"
    " axis. Product change in src/sandbox/ledger/apimarket.py (api_search"
    " in_stock). Verification: new suite 8/8 double-run rc=0/0 with"
    " byte-identical criterion lines sha16 001304dcd96edb53"
    " (qa/apimarket-searchstock-R2142-a.log and -b.log, single-writer UTF-8 LF);"
    " registration ledger-apimarket-searchstock(8); five adjacent suites rc=0"
    " each (search, searchpaging, searchsort, category, supply); suite matrix 346"
    " suites / 2876 criteria --check byte-identical. Honest disclosures: (a) the"
    " first filter cut compared the sold-out flag against the wrong polarity and"
    " kept exactly the sold-out rows, caught by AC-AMAV3 before any evidence was"
    " written; (b) the first identity view included the retired row whose"
    " delisted_utc is a wall-clock stamp, so the digest varied between processes"
    " rather than between restarts, and the view now uses the non-retired filter;"
    " (c) the evidence driver pins PYTHONHASHSEED=0 because three evidence lines"
    " echo set reprs; (d) the full battery was NOT run this round (25-minute"
    " budget) and is the first item of the next round.")


def main():
    with io.open(EXPORT, "rb") as handle:
        data = json.loads(handle.read().decode("utf-8"))
    data["export_ts"] = EXPORT_TS
    data["ceo_face"] = dict(CEO_FACE)
    data["outs"].append([OUT_NAME, "on", OUT_TEXT])
    data["results"].append(["R2142", RESULT_TEXT])
    label = C._load_patterns()["tick_row_label"]
    state = json.loads(io.open(C.P_STATE, "rb").read().decode("utf-8"))
    tick = str(state["tick"])
    hit = 0
    for row in data["results"]:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = tick
            hit += 1
    if hit != 1:
        raise SystemExit("tick row count %d" % hit)
    out = json.dumps(data, ensure_ascii=False, indent=2)
    with io.open(EXPORT, "wb") as handle:
        handle.write((out + "\n").encode("utf-8"))
    derived, _state, _export, _pat = C.recompute()
    with io.open(EXPORT, "rb") as handle:
        fresh = json.loads(handle.read().decode("utf-8"))
    fresh["self_drive"] = dict(derived)
    with io.open(EXPORT, "wb") as handle:
        handle.write((json.dumps(fresh, ensure_ascii=False, indent=2)
                      + "\n").encode("utf-8"))
    print("export_ts=%s tick=%s outs=%d results=%d self_drive=%d"
          % (EXPORT_TS, tick, len(fresh["outs"]),
             len(fresh["results"]), len(fresh["self_drive"])))


if __name__ == "__main__":
    main()