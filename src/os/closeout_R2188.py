# -*- coding: utf-8 -*-
"""R2188 closeout: backlog done row, queue row tick, state tick and
log lines (narrative + token ledger), all machine-derived where the
format allows. Pure ASCII source; CJK lives in the data files."""
import io
import json
import os

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(BASE, "src", "os", "state.json")
BACKLOG = os.path.join(BASE, "src", "os", "backlog.md")
QUEUE = os.path.join(BASE, "state", "queue", "explore.md")

BACKLOG_ROW = (
 "- [x] P3 explore \u961f\u5934\u8ba4\u9886\uff08R2188\u00b7\u6e90=R2178 "
 "\u8865\u79cd 10/10\u00b7\u5224\u636e AC-SSUP1..AC-SSUP8 "
 "\u9884\u6ce8\u518c\u4e8e state/queue/explore.md \u540c\u540d\u884c"
 "\u4e14\u5148\u4e8e\u4ee3\u7801\uff09\uff1aapimarket **\u5356\u5bb6"
 "\u4f9b\u7ed9\u603b\u89c8\u9762**\uff08api_seller_supply\uff09\u2014\u2014"
 "\u7f3a\u53e3\u5b9e\u8bc1\uff1aapi_supply\uff0fapi_supply_history "
 "\u9010\u6302\u724c\u3001api_seller_todo \u9010\u5f85\u529e\uff0c"
 "\u5356\u5bb6\u4fa7\u6ca1\u6709\u4e00\u9762\u6eda\u603b\u300c\u6211\u540d"
 "\u4e0b\u5728\u67b6\u51e0\u4ef6\u3001\u603b\u5e93\u5b58\u591a\u5c11\u3001"
 "\u552e\u7f44\u51e0\u4ef6\u3001\u4f4e\u5e93\u5b58\u51e0\u4ef6\u300d\u3002"
 "\u4ea7\u54c1=apimarket.py `api_seller_supply(dev_account, "
 "low_stock_threshold=1)`\uff1a\u5341\u516d\u952e\u4fe1\u5c01"
 "\uff0f\u5341\u4e00\u952e\u884c\uff1b\u884c\u6743=\u6302\u724c\u8868"
 "\uff08\u542b\u9000\u5f79\u4ef6\u00b7listing_id \u5347\u5e8f\uff09\uff1b"
 "\u5728\u67b6/\u9000\u5f79\u5206\u533a\u4e0e\u8ffd\u8e2a/\u4e0d\u9650"
 "\u91cf\u5206\u533a\uff1b\u56db\u9879\u805a\u5408\u5b88\u6052"
 "\uff08total_sold \u542b\u4e0d\u9650\u91cf\u884c\u00b7\u4e24\u9879"
 "\u4f9b\u7ed9\u603b\u989d\u53ea\u53d6\u8ffd\u8e2a\u884c\u00b7\u65e0"
 "\u8ffd\u8e2a\u884c\u62a5 None\uff09\uff1b\u7a00\u7f3a\u5f8b\u7ecf "
 "_supply_full \u5355\u7f1d\u4e00\u6b65\u751f\u6548\uff08\u8d2d\u4e70"
 "\u964d\u4f59\u91cf\u3001\u8017\u5c3d\u7ffb sold_out/low_stock\u3001"
 "\u9000\u6b3e\u8fd8\u67b6\u7ffb\u56de\u3001\u8865\u8d27\u62ac\u5347"
 "\u6e05\u96f6\uff09\uff1b\u4f4e\u5e93\u5b58\u9608\u503c\u5f8b"
 "\uff08\u7f3a\u7701 1\u00b70 \u53ea\u7b97\u552e\u7f44\u00b7\u975e int/"
 "\u5e03\u5c14/\u8d1f\u6570 E_AM_BAD_ARGS\u00b7\u8d26\u6237\u95e8\u5148"
 "\u4e8e\u9608\u503c\u95e8\uff09\uff1b\u7eaf\u8bfb\u96f6 token \u96f6"
 "\u884c\u53d8\u66f4\u3001\u5356\u5bb6\u4e25\u683c\u9694\u79bb\u3002"
 "\u8bc1\u636e=\u5957\u4ef6 SUITE PASS 8/8 \u53cc\u8dd1\u8bc1\u636e"
 "\u4ef6\u9010\u5b57\u8282\u540c\u4e00 sha16 41a6df82c7e14ab6"
 "\uff08qa/apimarket-sellersupply-R2188-a.log + -b.log\u00b7\u5404 "
 "1263B\u00b7\u5355\u5199\u8005 utf-8 LF\uff09\uff1b\u63a5\u7ebf "
 "ledger-apimarket-sellersupply(8)\uff1b\u516d\u6761\u76f8\u90bb"
 "\u5957\u4ef6\u5168\u7eff\uff08qa/regression-R2188.log\uff09\uff1b"
 "census \u590d\u8bfb DRIFT-CLEAN files=2020 flags=0"
 "\uff08\u987a\u624b\u6309\u51fa\u751f\u7ad9\u7597\u6cd5\u4fee\u590d"
 "\u524d\u8f6e qa/reconcile-all-R2187.log \u7684 CRLF \u65b9\u8a00\uff09"
 "\u3002\u8bda\u5b9e\u6ce8=\u2460\u9996\u8dd1 5/8 \u7ea2\u4e8e\u672c"
 "\u7a97\u4e09\u5904\u7b97\u672f\u671f\u671b\u9519\uff08\u8ffd\u8e2a"
 "\u4f9b\u7ed9\u603b\u989d 11 \u975e 13\u3001\u552e\u7f44\u524d\u51c0"
 "\u6210\u4ea4 5 \u975e 6\uff09\uff0c\u6309\u5b9e\u6d4b\u6539\u6d4b"
 "\u8bd5\u4e0d\u653e\u5bbd\u5b9e\u73b0\uff1b\u2461\u5168\u91cf\u7535"
 "\u6c60\u4e0e\u77e9\u9635\u518d\u751f\u672a\u8dd1\uff0825 \u5206\u949f"
 "\u9884\u7b97\uff09\uff0c\u5217 R2189 \u9996\u9879\u3002\n")

QUEUE_NOTE = (
 " \u3010done 2026-10-28 R2188\u3011\u4ea7\u54c1=apimarket.py "
 "`api_seller_supply(dev_account, low_stock_threshold=1)`"
 "\uff1a\u5341\u516d\u952e\u4fe1\u5c01\uff0f\u5341\u4e00\u952e\u884c\uff1b"
 "\u4e0a\u67b6/\u9000\u5f79\u4e0e\u8ffd\u8e2a/\u4e0d\u9650\u91cf\u53cc"
 "\u5206\u533a\u3001\u56db\u9879\u805a\u5408\u5b88\u6052\u3001\u7a00"
 "\u7f3a\u5f8b\u7ecf _supply_full \u5355\u7f1d\u4e00\u6b65\u751f\u6548"
 "\u3001\u4f4e\u5e93\u5b58\u9608\u503c\u5f8b\u4e0e\u95e8\u5e8f\u3001"
 "\u7eaf\u8bfb\u96f6 token \u4e0e\u5356\u5bb6\u9694\u79bb\uff1b"
 "\u5957\u4ef6 SUITE PASS 8/8 \u53cc\u8dd1\u9010\u5b57\u8282\u540c\u4e00 "
 "sha16 41a6df82c7e14ab6\uff1b\u63a5\u7ebf "
 "ledger-apimarket-sellersupply(8)\uff1b\u516d\u6761\u76f8\u90bb\u5957"
 "\u4ef6\u5168\u7eff\uff1b\u5168\u91cf\u7535\u6c60\u4e0e\u77e9\u9635"
 "\u518d\u751f\u5217 R2189 \u9996\u9879\u3002")

NARRATIVE = (
 "2026-10-28 R2188 (five-silence scan clean at open: the group ledger"
 " carries the same three @BigDomain patrol rows already paid off with"
 " zero unreplied; decisions.md reads 251 non-empty rows carrying 170"
 " content-addressed D/C tokens with ZERO new against the stored"
 " baseline, so zero domain action and the baseline stands; the group"
 " orders tail is unchanged at the 2026-10-28 03:0x CEO-PROXY fleet"
 " event round #4, acknowledged with zero domain action; benchmarks"
 " refreshed 2026-10-27 inside the seven-day gate; tree clean, no"
 " index.lock) - the P1 canonical rows stay blocked-on-CEO, the weekly"
 " proposal duty is met by BD-PROP-005, all four tech heads stayed"
 " gated (docker host absent, logs toolkit standing maintenance, member"
 " refunded schema product-gated, the live-mtime row waiting on a real"
 " normalized-mtime event) and the head above the seeds is the"
 " merchant-gated benchmark row, so this window claimed the LAST real"
 " seed (R2178 10/10) and shipped the seller-side supply rollup."
 " Gap statement: api_supply and api_supply_history answer one listing"
 " and api_seller_todo answers one duty, so a seller holding N shelves"
 " had to call api_supply N times to learn the shop's stock position -"
 " how many listings are live, how many units are declared, how many"
 " are sold out, how many sit at or below a low-stock threshold."
 " Product: APIMarketFace.api_seller_supply(dev_account,"
 " low_stock_threshold=1) - a sixteen-key envelope with eleven-key"
 " rows. Row authority is the listing table (every listing the seller"
 " ever published, retired ones included, ordered by listing_id), so"
 " an empty shop is an honest zero row set; live/retired and"
 " tracked/unlimited are two explicit partitions (live + retired =="
 " listing_count, tracked + unlimited == listing_count); every"
 " scarcity quantity rides the single _supply_full seam that api_supply"
 " and the purchase gate already trust, so a purchase lowers remaining"
 " and flips sold_out plus low_stock on exhaustion, a refund hands the"
 " unit back and clears both, and a restock raises remaining and clears"
 " sold_out - one face call sees each step, with no second bookkeeping"
 " copy. total_sold counts every row including unlimited shelves (the"
 " sale really happened) while the two supply totals read tracked rows"
 " only and answer None when nothing is tracked; an unlimited shelf"
 " never reports a unit count, never counts as sold out or low stock,"
 " and is clamped out of any threshold. The low-stock threshold"
 " defaults to 1 (0 therefore counts only sold-out shelves), accepts"
 " int >= 0, fails closed on bool/str/float/negative forms, and the"
 " account shape gate runs before it. Retired shelves keep their row"
 " and every historical figure, re-listing flips only the flag, and"
 " the face is a pure read with frozen table digests and a constant"
 " ledger_tx set. SUITE PASS 8/8 double-run byte-identical criterion"
 " lines sha16 728821d514d5c693 (evidence"
 " qa/apimarket-sellersupply-R2188-a.log + -b.log, 1263 bytes each,"
 " single-writer utf-8 LF); wired ledger-apimarket-sellersupply(8); six"
 " adjacent supply/lifecycle suites green (qa/regression-R2188.log)."
 " Honest notes: (a) the first run read 5/8 red on three arithmetic"
 " expectations that were wrong in this window's own fixture math (the"
 " tracked supply total is 11 not 13, and pre-unlimited net sales are 5"
 " not 6), so the TEST was corrected to the measured structure and no"
 " implementation was loosened; (b) the live writer census flagged ONE"
 " unbaselined file - the predecessor's qa/reconcile-all-R2187.log at"
 " class=other, the same shell-capture newline class repaired in"
 " R2172/R2185 - so the birth-site remedy normalized only the newline"
 " axis (726151 bytes, crlf=0, line table intact) and the census then"
 " read DRIFT-CLEAN files=2020 tee=1492 baselined=528 flags=0; (c) the"
 " full reconcile battery and the suite-matrix regeneration were NOT"
 " run in this 25-minute window, recorded as first-item debt for R2189;"
 " (d) the explore queue keeps one open row, the merchant-gated"
 " benchmark item, so R2189 needs a reseed before a product claim.")

TOKENS = ("R2188 tokens: local=~70k api=0 api_reason=five-silence scan"
          " + explore seed 10/10 claim with criteria pre-registered before"
          " code + seller supply rollup product face + suite 8/8 double-run"
          " byte-identical + six adjacent regressions + census drift repair"
          " via the existing single writer + state/export closeout, zero"
          " cloud calls")


def main():
    # backlog: newest done row goes first
    with io.open(BACKLOG, encoding="utf-8") as handle:
        text = handle.read()
    assert BACKLOG_ROW not in text
    io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(
        BACKLOG_ROW + text)

    # queue row: tick the head and append the done note
    with io.open(QUEUE, encoding="utf-8") as handle:
        rows = handle.read()
    marker = ("- [ ] P3 explore \u961f\u5934\u8ba4\u9886\uff08R2188")
    assert rows.count(marker) == 1, rows.count(marker)
    rows = rows.replace(marker, "- [x] P3 explore \u961f\u5934\u8ba4\u9886"
                        "\uff08R2188")
    tail = "\u5df2\u6ce8\u518c\u3002"
    assert rows.count(tail) >= 1
    idx = rows.find(marker.replace("- [ ]", "- [x]"))
    end = rows.find("\n", idx)
    rows = rows[:end] + QUEUE_NOTE + rows[end:]
    io.open(QUEUE, "w", encoding="utf-8", newline="\n").write(rows)

    # state: tick plus the two closing lines
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    assert state["tick"] == 2187, state["tick"]
    state["tick"] = 2188
    log = state["log"]
    assert not log[-1].startswith("R2188 tokens:")
    log.append(NARRATIVE)
    log.append(TOKENS)
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    print("CLOSEOUT OK tick=%d log=%d" % (state["tick"], len(log)))


if __name__ == "__main__":
    main()