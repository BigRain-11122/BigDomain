"""R2141 export refresh: merge the round payload into
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

EXPORT_TS = "2026-10-26T11:15:11+08:00"

CEO_FACE = {
    "current": "本轮把开发者 API 市场的「品类需求面」做出来了：哪个品类真的卖得动"
               "（成交/退款/净额/买家数）现在有一面可查，并与全市场统计逐项对得上。",
    "latest_artifact": "src/sandbox/ledger/apimarket.py 的 api_category_demand"
                       "（品类需求面）+ qa/apimarket-categorydemand-R2141-a.log"
                       "（8/8 双跑）+ docs/sandbox-suite-matrix.md（345 套件 /"
                       " 2868 判据）— 2026-10-26 11:15",
    "next_milestone": "48 小时内：把这面接进卖家侧看板（选品/定价用）并跑一轮全量回归；"
                      "商户号仍未到，支付与权益设计件继续先行。",
}

OUT_NAME = "apimarket per-category demand (api_category_demand)"

OUT_TEXT = (
    "R2141: api_categories answered the SUPPLY side of a category (listing"
    " counts plus the live price band) while api_market_stats aggregated the"
    " whole market, api_listing_demand one listing, dev_sales_board one seller"
    " and api_market_months one month - so no face answered which categories"
    " actually SELL. api_category_demand(include_uncategorized=True) closes that"
    " gap: listing-side row authority with the honest uncategorized bucket last,"
    " per-row and global partition conservation, per-row trade conservation"
    " (gross == net + refunded, net_purchase == purchase - refund) with"
    " cross-face identity against api_market_stats on the default call,"
    " buyer_count as a within-category distinct count while the envelope counts"
    " distinct buyers over the included rows, retirement and re-listing moving"
    " only the partition counters, a refund lowering the net side of one"
    " category only, avg_net_price = net_gross / net_purchase (None when nothing"
    " settled), and a bool gate that fails closed before any read. Suite"
    " SUITE PASS 8/8 double-run byte-identical sha16 2a1f5dbec1f1e160"
    " (qa/apimarket-categorydemand-R2141-a.log and -b.log); full battery RUNNER"
    " PASS 345/345 suites plus controls 7/7 in 961.8s"
    " (qa/reconcile-all-R2141.log); matrix 345 suites / 2868 criteria"
    " --check byte-identical.")

RESULT_TEXT = (
    "R2141: seeded and claimed a fresh P3 explore row in the same window with"
    " AC-AMCD1..AC-AMCD8 pre-registered BEFORE the code existed (six anchors git"
    " grep -F zero-occupancy, rc=1) and delivered the per-category demand face."
    " Product change in src/sandbox/ledger/apimarket.py (api_category_demand)."
    " Verification: new suite 8/8 double-run rc=0/0 with byte-identical criterion"
    " lines sha16 2a1f5dbec1f1e160 (qa/apimarket-categorydemand-R2141-a.log and"
    " -b.log, single-writer UTF-8 LF); registration ledger-apimarket-categorydemand(8);"
    " full battery RUNNER PASS 345/345 plus controls 7/7 in 961.8s with TMP RECLAIM"
    " 276.22 MiB (qa/reconcile-all-R2141.log); suite matrix 345 suites / 2868"
    " criteria --check byte-identical. Group acknowledgement: PT-20261026-01/02/03"
    " (patrol intake) - the BigDomain-relevant piece is the local-line liveness and"
    " push proof closed by this round. Honest disclosure: the AC-AMCD7 fixture"
    " expectation was first written as buyer_count 4 while the measurement was 5"
    " (u1 buys in both the tools category and the bucket); the pre-registered"
    " criterion speaks about the distinct buyer count over the INCLUDED rows, so the"
    " fixture expectation was corrected rather than the criterion weakened.")


def main():
    with io.open(EXPORT, "rb") as handle:
        data = json.loads(handle.read().decode("utf-8"))
    data["export_ts"] = EXPORT_TS
    data["ceo_face"] = dict(CEO_FACE)
    data["outs"].append([OUT_NAME, "on", OUT_TEXT])
    data["results"].append(["R2141", RESULT_TEXT])
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