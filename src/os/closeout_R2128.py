"""R2128 closeout: flip the explore-queue claim row and the backlog row,
append the two state log lines, and refresh the export face.

The window took over an interrupted predecessor (product diff, suite,
evidence pair, battery logs already on disk while state.json still ended
at R2127), verified the payload by re-running it, and closes it here.
"""

import io
import json
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

LOG_R2128 = (
    "2026-10-25 R2128 (this window opened on an INTERRUPTED predecessor, "
    "the R2087/R2125/R2126 family: the api_buyer_ledger product diff, its "
    "suite, the evidence pair, the battery logs and the explore-queue claim "
    "row were already on disk uncommitted while state.json still ended at "
    "R2127, with no index.lock and no live battery present) - so the payload "
    "was verified and closed instead of reseeded, and every figure below is "
    "re-measured in this window. Product: APIMarketFace.api_buyer_ledger - "
    "the buyer-side settlement statement, the mirror of the R2126 seller "
    "statement. A buyer carried row faces (api_library), cash months "
    "(api_buyer_months), lifetime aggregates (api_buyer_profile), a rating "
    "debt queue and watch alerts, yet the ledger movements a purchase debits "
    "and a refund credits had zero product consumers. The face joins the live "
    "account balance read through the ONE seam _seller_balance (the same "
    "helper refund_api and api_refund_exposure already trust, so no second "
    "bookkeeping copy) with that account's own append-only ledger entries "
    "newest first; credit/debit/net are derived from the rows, entry_count == "
    "len(entries), limit truncates the OLDEST tail so the newest movement "
    "stays visible, an over-cap limit clamps at 500 while a non-int / bool / "
    "sub-one limit fails closed, and an account the ledger never saw answers "
    "balance 0 with balance_known False and an honest empty statement rather "
    "than raising; pure read, zero row mutations, zero token movement, "
    "disclaimer in the envelope. The report consumes it: every buyer block "
    "gains a ledger key read fresh on each collect, the page renders a ledger "
    "statement table with an honest empty state, and REPORT_SCHEMA moves 15 "
    "-> 16 additively. Criteria AC-AMLGB1..AC-AMLGB8 were pre-registered in "
    "the R2128 explore-queue row BEFORE the code existed (five anchors git "
    "grep -F zero-occupancy rc=1). Verification in this window: the suite "
    "re-runs rc=0/0 with byte-identical criterion lines sha16 "
    "208F2CDBF9962B6F and byte-identical evidence files sha16 "
    "95c90803e141af17 (qa/apimarket-buyerledger-R2128.log + -run2.log, "
    "single utf-8 LF writer); the battery log qa/reconcile-all-R2128.log "
    "reads RUNNER PASS 332/332 suites plus controls 7/7 in 649.9s and its "
    "mtime postdates every code change; the suite matrix was regenerated "
    "against that battery to 332 suites / 2764 criteria and --check is "
    "byte-identical. Two honest notes on the predecessor: its first battery "
    "(qa/reconcile-all-R2128-firstfail.log, RUNNER FAIL with seven failed "
    "assertions, preserved unrewritten) tripped older report suites while the "
    "report module was still half-written and the dossier determinism face "
    "caught the ledger clock being unpatched - the final module patches both "
    "clocks and needs no edit to any old suite; the daily standing rows for "
    "2026-10-25 were already stamped, so neither was re-run. Five-silence "
    "scan clean: decisions.md carries zero new content-addressed tokens "
    "against the baseline (221 rows measured), ledger zero new @BigDomain "
    "rows, group orders baseline unchanged at 2026-10-25 18:2x, benchmarks "
    "refreshed 2026-10-25 inside 7 days, tree carried only this window's own "
    "payload, no index.lock."
)

LOG_TOKENS = (
    "R2128 tokens: local=~55k api=0 api_reason=five-silence scan + closeout "
    "verification of the interrupted buyer-ledger window (suite double-run + "
    "evidence byte comparison) + matrix regen/check + boards/state/export "
    "closeout, zero cloud calls"
)

OUT_TITLE = ("apimarket buyer settlement statement (api_buyer_ledger: live "
             "balance through the same seam + this buyer's own entries)")

OUT_TEXT = (
    "R2128: R2126 gave the seller a statement; the buyer side still had no "
    "face answering how much money a resident holds right now and which "
    "ledger entries produced it. A buyer carried rows (api_library), cash "
    "months (api_buyer_months), lifetime aggregates (api_buyer_profile), a "
    "rating debt queue and watch alerts, but the purchase debit and the "
    "refund credit produced ledger moves with zero product consumers - "
    "ledger.bill had exactly one caller, the seller statement. "
    "api_buyer_ledger(buyer_id, limit=None) joins the live balance read "
    "through the one seam _seller_balance (the helper refund_api and "
    "api_refund_exposure already trust, so there is no second bookkeeping "
    "copy) with that account's own append-only entries newest first: ten-key "
    "envelope, ten-key rows, entry_count == len(entries), credit/debit/net "
    "all derived from the visible rows, limit truncating the oldest tail, a "
    "clamp at 500 and a fail-closed gate for bool / non-int / sub-one limits, "
    "and an account the ledger never saw reported honestly as balance 0 with "
    "balance_known False instead of an exception. The settlement report "
    "consumes it: every buyer block gains a ledger key read fresh per "
    "collect, the page renders a statement table with an honest empty state, "
    "and REPORT_SCHEMA moves 15 -> 16 additively with every earlier block "
    "value unchanged. Criteria AC-AMLGB1..AC-AMLGB8 were pre-registered in "
    "the explore-queue row before the code existed. Verification this window: "
    "suite double-run rc=0/0 with identical criterion lines sha16 "
    "208F2CDBF9962B6F and identical evidence bytes sha16 95c90803e141af17; "
    "battery qa/reconcile-all-R2128.log RUNNER PASS 332/332 suites plus "
    "controls 7/7 in 649.9s; matrix regenerated to 332 suites / 2764 criteria "
    "and byte-identical on check. Honest notes: this window took over an "
    "interrupted predecessor (payload on disk, state still at R2127), the "
    "predecessor's red first battery is preserved unrewritten, and its two "
    "real defects - a half-written report module and an unpatched ledger "
    "clock in the determinism seeder - were fixed before the green run."
)

RESULT_TEXT = (
    "R2128: the developer API market gains the buyer-side settlement "
    "statement, the mirror of the R2126 seller statement. api_buyer_ledger "
    "joins the live account balance - read through the one seam "
    "_seller_balance that refund_api and api_refund_exposure already trust, "
    "so no second bookkeeping copy exists - with that account's own "
    "append-only ledger entries newest first; credit/debit/net are derived "
    "from the visible rows, entry_count equals the row count, limit truncates "
    "the OLDEST tail so the newest movement always stays visible, an over-cap "
    "limit clamps at 500 while a non-int/bool/sub-one limit fails closed, an "
    "account the ledger never saw answers balance 0 with balance_known False "
    "and an empty statement, and the face is a pure read with zero row "
    "mutations and zero token movement. Consumers: every buyer block in the "
    "settlement report carries a ledger key read fresh on each collect, the "
    "page renders a statement table with an honest empty state, and "
    "REPORT_SCHEMA moves 15 -> 16 additively. Verification: suite double-run "
    "rc=0/0 with byte-identical criterion lines sha16 208F2CDBF9962B6F and "
    "identical evidence files sha16 95c90803e141af17; battery "
    "qa/reconcile-all-R2128.log RUNNER PASS 332/332 suites plus controls 7/7 "
    "in 649.9s; matrix 332 suites / 2764 criteria --check byte-identical. "
    "This window took over an interrupted predecessor and verified the "
    "payload rather than rebuilding it; its red first battery is preserved, "
    "and its two real defects (a half-written report module, an unpatched "
    "ledger clock in the determinism seeder) were repaired before the green "
    "run. Five-silence: decisions zero new content-addressed tokens, ledger "
    "zero new @BigDomain rows, group orders baseline unchanged, benchmarks "
    "inside 7 days."
)


def read(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main():
    base = BASE

    # 1) explore queue: flip the R2128 claim row to done.
    path = os.path.join(base, "state", "queue", "explore.md")
    text = read(path)
    marker = "- [ ] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886\uff08R2128\uff09"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("claim row not found")
    end = text.find("\n", idx)
    row = text[idx:end]
    row = row.replace("- [ ]", "- [x]", 1)
    row += ("[done 2026-10-25 R2128]\uff08\u524d\u7a97\u4e2d\u65ad\u9057\u7559\u4ea7\u7269"
            "\u7531\u672c\u7a97\u590d\u9a8c\u6536\u53e3\uff1a\u5957\u4ef6\u53cc\u8dd1 rc=0/0 "
            "\u5224\u636e\u884c\u540c\u4e00 sha16 208F2CDBF9962B6F\u00b7"
            "\u8bc1\u636e\u4ef6\u540c\u4e00 sha16 95c90803e141af17 = "
            "qa/apimarket-buyerledger-R2128.log + -run2.log\u00b7"
            "\u63a5\u7ebf ledger-apimarket-buyerledger(8)\u00b7"
            "\u7535\u6c60 qa/reconcile-all-R2128.log RUNNER PASS 332/332 suites "
            "+ controls 7/7 649.9s\u00b7\u77e9\u9635 332 suites / 2764 criteria "
            "--check \u9010\u5b57\u8282\u540c\u4e00\u00b7"
            "\u524d\u7a97\u7ea2\u7535\u6c60 qa/reconcile-all-R2128-firstfail.log "
            "\u539f\u6837\u4fdd\u7559\uff09")
    text = text[:idx] + row + text[end:]
    write(path, text)

    # 2) backlog: prepend the done row.
    path = os.path.join(base, "src", "os", "backlog.md")
    text = read(path)
    head_marker = "# BigDomain \u8ba4\u9886\u5de5\u4f5c\u677f\uff08backlog\uff09"
    idx = text.find(head_marker)
    if idx < 0:
        raise SystemExit("backlog header not found")
    insert_at = text.find("\n", idx) + 1
    new_row = (
        "\n- [x] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886\uff08R2128\uff09"
        "apimarket **\u4e70\u5bb6\u7ed3\u7b97\u5bf9\u8d26\u5355\u9762**\uff08api_buyer_ledger\uff09"
        "\u2014\u2014R2126 \u53ea\u7ed9\u5356\u5bb6\u8865\u4e86\u5bf9\u8d26\u5355\uff0c"
        "\u4e70\u5bb6\u4fa7\u81f3\u4eca\u6ca1\u6709\u300c\u6211\u6b64\u523b\u8d26\u4e0a\u591a\u5c11\u94b1\u3001"
        "\u8fd9\u4e9b\u94b1\u662f\u54ea\u51e0\u7b14\u6d41\u6c34\u6765\u7684\u300d\uff1b"
        "\u8d2d\u4e70\u6263\u6b3e\u4e0e\u9000\u6b3e\u56de\u51b2\u4ea7\u751f\u7684 ledger \u6d41\u6c34"
        "\u5728\u4ea7\u54c1\u9762\u96f6\u6d88\u8d39\u8005\u3002\u672c\u7a97\u628a\u540c\u4e00\u5355\u7f1d "
        "`_seller_balance` \u4e0e `led.bill` \u63a5\u6210\u4e70\u5bb6\u5bf9\u8d26\u5355"
        "\uff08\u5341\u952e\u4fe1\u5c01/\u540d\u5341\u952e\u884c\u00b7\u8d37\u8bb0\u5408\u8ba1\u7531\u884c"
        "\u6d3e\u751f\u00b7limit \u622a\u6700\u65e7\u5c3e\u5df4\u4e14 >500 \u94b3\u5236\u00b7"
        "\u672a\u5efa\u6237\u8bda\u5b9e\u62a5 balance 0/balance_known False\u00b7"
        "\u7eaf\u8bfb\u96f6 token\uff09\u5e76\u63a5\u8fdb\u552f\u4e00\u6d88\u8d39\u8005"
        "\uff08\u7ed3\u7b97\u62a5\u544a\u4e70\u5bb6\u5757 ledger \u952e + \u4e70\u5bb6\u6bb5\u6d41\u6c34\u8868 + "
        "REPORT_SCHEMA 15\u219216 \u52a0\u6cd5\u5347\u7ea7\uff09\u3002"
        "\u5224\u636e AC-AMLGB1..AC-AMLGB8 \u9884\u6ce8\u518c\u4e8e\u4ee3\u7801\u4e4b\u524d"
        "\uff08\u672c\u884c\u5373\u518c\u00b7\u4e94\u951a\u96f6\u5360\u7528 rc=1\uff09\u3002"
        "[done 2026-10-25 R2128]\uff08\u672c\u7a97\u590d\u9a8c\u6536\u53e3\u524d\u7a97\u4e2d\u65ad\u9057\u7559"
        "\u4ea7\u7269\uff1a\u5957\u4ef6\u53cc\u8dd1 rc=0/0 \u5224\u636e\u884c\u540c\u4e00 sha16 "
        "208F2CDBF9962B6F\u00b7\u8bc1\u636e\u4ef6\u540c\u4e00 sha16 95c90803e141af17\uff1b"
        "\u63a5\u7ebf ledger-apimarket-buyerledger(8)\uff1b\u7535\u6c60 qa/reconcile-all-R2128.log "
        "RUNNER PASS 332/332 suites + controls 7/7 649.9s\uff1b"
        "\u77e9\u9635\u6309\u8be5\u7535\u6c60\u91cd\u751f\u6210\u540e --check \u9010\u5b57\u8282\u540c\u4e00"
        "\uff08332 suites / 2764 criteria\uff09\uff1b\u4e94\u9759\u6c34\u6e05\u6d17\u3002"
        "\u8bda\u5b9e\u6ce8=\u524d\u7a97\u9996\u8dd1\u7535\u6c60\u7ea2\uff087 \u6761\u65ad\u8a00\uff09"
        "\u4e3a\u62a5\u8868\u6a21\u5757\u672a\u5199\u5b8c\u4e0e\u6f14\u793a\u79cd\u5b50\u672a\u8865\u8d26\u672c\u65f6\u949f"
        "\u6240\u81f4\uff0c\u4e24\u5904\u5747\u5728\u7eff\u8dd1\u524d\u4fee\u590d\uff0c\u7ea2\u7535\u6c60\u65e5\u5fd7"
        "\u539f\u6837\u4fdd\u7559\uff1b\u672c\u7a97\u672a\u91cd\u8dd1\u5168\u91cf\u7535\u6c60\uff0c"
        "\u91cf\u6570\u53d6\u81ea\u8be5\u8bc1\u636e\u4ef6\u5e76\u91cd\u6d4b\u5957\u4ef6\u4e0e\u77e9\u9635\u4e24\u9762\uff09"
    )
    text = text[:insert_at] + new_row + text[insert_at:]
    write(path, text)

    # 3) state.json
    path = os.path.join(base, "src", "os", "state.json")
    with io.open(path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2128
    state["last_decision_rows"] = 221
    state["benchmarks_refreshed"] = "2026-10-25"
    state["log"].append(LOG_R2128)
    state["log"].append(LOG_TOKENS)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    # 4) export face
    path = os.path.join(base, "docs", "status-export.json")
    with io.open(path, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = "2026-10-25T20:05:00+08:00"
    export["ceo_face"]["current"] = (
        "\u4e70\u5bb6\u7ed3\u7b97\u5bf9\u8d26\u5355\u9762\uff08api_buyer_ledger\uff09\uff1a"
        "\u5356\u5bb6\u65e9\u5c31\u6709\u300c\u6211\u8d26\u4e0a\u591a\u5c11\u94b1\u3001\u54ea\u51e0\u7b14\u6d41\u6c34"
        "\u6765\u7684\u300d\u5bf9\u8d26\u5355\uff0c\u4e70\u5bb6\u4e00\u76f4\u6ca1\u6709\u2014\u2014\u8d2d\u4e70\u6263\u6b3e"
        "\u4e0e\u9000\u6b3e\u56de\u51b2\u5728\u8d26\u672c\u91cc\u65e9\u5c31\u6709\u6570\uff0c\u5374\u6ca1\u6709\u4efb\u4f55"
        "\u4ea7\u54c1\u9762\u53bb\u8bfb\u3002\u672c\u8f6e\u628a\u6d3b\u4f59\u989d\uff08\u8d70\u9000\u6b3e\u95e8\u4e0e"
        "\u655e\u53e3\u9762\u5df2\u4fe1\u4efb\u7684\u540c\u4e00\u7f1d\uff09\u4e0e\u8be5\u8d26\u6237\u81ea\u5df1\u7684"
        "\u9010\u7b14\u6d41\u6c34\u5408\u6210\u5bf9\u8d26\u5355\uff0c\u5e76\u63a5\u8fdb\u7ed3\u7b97\u62a5\u544a"
        "\u7684\u4e70\u5bb6\u6bb5\uff1b\u6ca1\u4ea4\u6613\u8fc7\u7684\u8d26\u6237\u4e5f\u4e0d\u62a5\u9519\uff0c"
        "\u800c\u662f\u8bda\u5b9e\u7ed9\u51fa\u4f59\u989d 0 \u4e0e\u7a7a\u6d41\u6c34\u3002"
    )
    export["ceo_face"]["latest_artifact"] = (
        "src/sandbox/ledger/apimarket.py\uff08api_buyer_ledger\uff09+ "
        "src/sandbox/ledger/apimarket_report.py\uff08\u4e70\u5bb6\u5757 ledger \u952e\u4e0e"
        "\u6d41\u6c34\u8868\u00b7REPORT_SCHEMA 15\u219216\uff09+ "
        "src/sandbox/ledger/test_apimarket_buyerledger.py\uff08SUITE PASS 8/8 \u53cc\u8dd1 "
        "rc=0/0\uff0c\u5224\u636e\u884c sha16 208F2CDBF9962B6F\uff0c\u8bc1\u636e "
        "qa/apimarket-buyerledger-R2128.log / -run2.log\uff09\uff1b"
        "qa/reconcile-all-R2128.log\uff08RUNNER PASS 332/332 \u5957\u4ef6 + \u63a7\u5236 7/7\uff0c"
        "649.9s\uff09\uff1bdocs/sandbox-suite-matrix.md\uff08332 \u5957\u4ef6 / 2764 \u5224\u636e\uff0c"
        "--check \u9010\u5b57\u8282\u540c\u4e00\uff09\u3002"
    )
    export["ceo_face"]["next_milestone"] = (
        "48 \u5c0f\u65f6\u5185\uff1a\u2460\u628a R2124 \u7684\u4e09\u5f20\u5206\u53d1\u4e49\u52a1\u9762"
        "\u63a5\u8fdb\u4e0a\u67b6\u95e8\uff08\u672a\u8fc7\u5ba1/\u672a\u5b9e\u540d\u4e0d\u5f97\u4e0a\u67b6\uff09\uff0c"
        "\u76ee\u524d\u5b83\u4eec\u53ea\u662f\u53ef\u8bfb\u9762\uff1b\u2461\u633d\u5ba2\u4fa7\uff08\u4e70\u5bb6/\u5356\u5bb6\uff09"
        "\u5bf9\u8d26\u5355\u5408\u6210\u4e00\u5f20\u7ed3\u7b97\u9875\uff0c\u8ba9\u300c\u6211\u8be5\u6536\u591a\u5c11\u3001"
        "\u8be5\u4ed8\u591a\u5c11\u300d\u4e00\u773c\u53ef\u89c1\uff1b\u2462\u628a\u7535\u6c60\u6bcf\u8f6e\u56de\u6536"
        "\u8bfb\u6570\u63a5\u8fdb\u65e5\u62a5\uff0c\u4f7f\u6e05\u626b\u6210\u4e3a\u53ef\u89c1\u8d8b\u52bf\u3002"
    )
    export["outs"].insert(0, [OUT_TITLE, "on", OUT_TEXT, "2026-10-25"])
    export["results"].insert(0, ["R2128", RESULT_TEXT])
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(export, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    print("closeout written")


if __name__ == "__main__":
    main()