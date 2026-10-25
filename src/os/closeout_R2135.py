"""R2135 closeout: finish the interrupted purchase-dossier window.

The predecessor left the product diff, the suite, the evidence pair, the
explore-queue claim row and two red battery logs on disk while state.json
still ended at R2134. This window re-measured everything, ran a green
battery, regenerated the matrix, re-anchored the evidence census, and
closes the boards, state and export faces here.
"""

import io
import json
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

LOG_R2135 = (
    "2026-10-26 R2135 (this window opened on an INTERRUPTED predecessor, the "
    "R2087/R2125/R2126/R2128 family: the api_purchase_dossier product diff, "
    "its suite, the evidence pair, the explore-queue claim row and two red "
    "battery logs were already on disk uncommitted while state.json still "
    "ended at R2134 and HEAD was b6f99a35, with no index.lock and no live "
    "battery process present) - so the payload was verified and closed "
    "instead of reseeded, and every figure below is re-measured in this "
    "window. Product: APIMarketFace.api_purchase_dossier - one trade's whole "
    "story behind one party-gated read face. Every existing face answers one "
    "corner (api_library a buyer's rows, api_refund one refund row, "
    "api_claims the claim queue, api_seller_ledger/api_buyer_ledger the cash "
    "movements), so a support ticket or a settlement dispute had to be "
    "assembled by hand from four faces. The dossier carries a twenty-one key "
    "envelope with the integer split identity price_paid == dev_share + "
    "platform_share, the stored category echoed (None when uncategorized), "
    "the buyer of record answering viewer_role buyer and the seller of record "
    "answering seller with the two payloads byte-identical apart from that "
    "one key, a third party refused E_AM_NOT_PARTY before any further read; "
    "the three nested blocks are honest absences (refund/rating/claim are "
    "None until their row exists, never empty shells), claim.status follows "
    "the api_claims precedence refunded > withdrawn > answered > open "
    "recomputed from the same append-only tables, and ticket_state is the "
    "single-word summary with the pinned precedence refunded > withdrawn > "
    "answered > open > rated > settled; the gate order is purchase-id shape, "
    "account shape, purchase existence, party membership, and the face is a "
    "pure read (zero row mutations, zero token movement, a retired and "
    "repriced listing keeps its dossier with price_paid as the historical "
    "charge). Criteria AC-AMPD1..AC-AMPD8 were pre-registered in the R2135 "
    "explore-queue row BEFORE the code existed (six anchors git grep -F "
    "zero-occupancy rc=1). Verification in this window: the suite re-runs "
    "rc=0/0 with byte-identical criterion lines sha16 087fc5576174bbbf over "
    "identical 1191-byte evidence files (qa/apimarket-purchasedossier-R2135b-a.log "
    "+ -b.log, single utf-8 LF writer); the battery qa/reconcile-all-R2135b.log "
    "reads RUNNER PASS 339/339 suites plus controls 7/7 in 1192.8s; the suite "
    "matrix was regenerated against that battery to 339 suites / 2820 "
    "criteria and --check is byte-identical (qa/matrix-gen-R2135.log + "
    "qa/matrix-check-R2135.log); the evidence census is DRIFT-CLEAN at 1862 "
    "files and zero flags. Honest notes on the predecessor and on this "
    "window: its two red batteries are preserved unrewritten - "
    "qa/reconcile-all-R2135.log (ledger-apimarket-buyerhistory AC-AMBD8) and "
    "qa/reconcile-all-R2135v.log (reconcile-daily-census cd7 live-tree drift "
    "plus a contended ledger-demo control) - and neither failure reproduced "
    "in the green run; the cd7 red had a real cause, the predecessor's new "
    "evidence files were not yet in the census baseline, which self-healed "
    "once this window rewrote its evidence with a single utf-8 LF writer (my "
    "own first capture was the known ps-utf16/pwsh-capture dialect trap, "
    "caught at the birth station by the census before any log was baselined); "
    "the daily standing rows for 2026-10-26 were already stamped so neither "
    "was re-run. Five-silence scan: decisions.md carries zero new "
    "content-addressed tokens against the stored baseline (228 non-empty rows "
    "measured), the ledger carries two patrol rows naming @BigDomain "
    "HQ-FEEDBACK freshness (acknowledged, our file mtime 2026-10-25 23:10, "
    "P-32 line appended this round), group orders baseline unchanged at "
    "2026-10-25 22:4x, benchmarks refreshed 2026-10-25 inside 7 days, tree "
    "carried only this window's own payload, no index.lock."
)

LOG_TOKENS = (
    "R2135 tokens: local=~95k api=0 api_reason=five-silence scan + closeout "
    "verification of the interrupted purchase-dossier window (suite "
    "double-run + evidence byte comparison + census re-anchor) + full battery "
    "339/339 + matrix regen/check + boards/state/export closeout, zero cloud "
    "calls"
)

OUT_TITLE = ("apimarket single-purchase dossier (api_purchase_dossier: buyer "
             "and seller see one trade's whole story)")

OUT_TEXT = (
    "R2135: the market had faces for each corner of a trade - api_library "
    "lists a buyer's purchases, api_refund returns one refund row, "
    "api_claims returns the claim queue, api_seller_ledger and "
    "api_buyer_ledger return the cash movements - but no face answered 'what "
    "actually happened to THIS purchase', so a support ticket or a settlement "
    "dispute had to be assembled by hand from four faces. "
    "api_purchase_dossier(purchase_id, account) is that assembly: a "
    "twenty-one key envelope with the integer split identity price_paid == "
    "dev_share + platform_share, the stored category echoed, and the buyer of "
    "record answering viewer_role buyer while the seller of record answers "
    "seller - the two payloads byte-identical apart from that one key - and a "
    "third party refused E_AM_NOT_PARTY before any further read. The three "
    "nested blocks are honest absences (refund/rating/claim are None until "
    "their row exists), claim.status uses the api_claims precedence refunded "
    "> withdrawn > answered > open, and ticket_state is the single-word "
    "summary refunded > withdrawn > answered > open > rated > settled. The "
    "gate order is purchase-id shape, account shape, purchase existence, "
    "party membership; the face is a pure read with zero row mutations and "
    "zero token movement, and a retired repriced listing keeps its dossier "
    "with price_paid as the historical charge. Criteria AC-AMPD1..AC-AMPD8 "
    "were pre-registered in the explore-queue row before the code existed. "
    "Verification this window: suite double-run rc=0/0 with identical "
    "criterion lines sha16 087fc5576174bbbf over identical 1191-byte evidence "
    "files; battery qa/reconcile-all-R2135b.log RUNNER PASS 339/339 suites "
    "plus controls 7/7 in 1192.8s; matrix 339 suites / 2820 criteria and "
    "byte-identical on check; census DRIFT-CLEAN at 1862 files and zero "
    "flags. Honest notes: this window took over an interrupted predecessor "
    "and verified its payload rather than rebuilding it; both predecessor red "
    "batteries are preserved unrewritten and neither failure reproduced on "
    "the green run (the census cd7 red was the predecessor's un-baselined "
    "evidence files, which healed once this window rewrote its evidence with "
    "a single utf-8 LF writer)."
)

RESULT_TEXT = (
    "R2135: the developer API market gains a single-purchase dossier, the one "
    "face that answers what happened to one trade end to end. "
    "api_purchase_dossier(purchase_id, account) returns a twenty-one key "
    "envelope with the integer split identity price_paid == dev_share + "
    "platform_share and the stored category echoed; the buyer of record sees "
    "viewer_role buyer and the seller viewer_role seller with payloads "
    "identical apart from that key, while a third party is refused "
    "E_AM_NOT_PARTY; refund, rating and claim are honest absences (None until "
    "the row exists), claim.status recomputes the api_claims precedence and "
    "ticket_state summarises it as refunded > withdrawn > answered > open > "
    "rated > settled; the gate order is purchase-id shape, account shape, "
    "existence, party membership, and the face is a pure read with zero "
    "token movement. Verification: suite double-run rc=0/0 with identical "
    "criterion lines sha16 087fc5576174bbbf and identical 1191-byte evidence "
    "files (qa/apimarket-purchasedossier-R2135b-a.log + -b.log); battery "
    "qa/reconcile-all-R2135b.log RUNNER PASS 339/339 suites plus controls 7/7 "
    "in 1192.8s; matrix 339 suites / 2820 criteria --check byte-identical; "
    "census DRIFT-CLEAN 1862 files zero flags. This window took over an "
    "interrupted predecessor and verified the payload rather than rebuilding "
    "it; its red batteries are preserved and neither failure reproduced. "
    "Five-silence: decisions zero new content-addressed tokens, ledger two "
    "patrol rows naming our HQ-FEEDBACK freshness (paid off with a P-32 "
    "line), group orders baseline unchanged, benchmarks inside 7 days."
)

# The ledger patrol point-naming: our HQ-FEEDBACK went stale on the group
# board. One P-32 line, appended at the tail, no rewrite of history.
HQ_LINE = (
    "- （2026-10-26 R2135，P2 回执行·非催办）**集团巡检点名「BigDomain "
    "HQ-FEEDBACK >24h 未更新」回执行**：本司现行无 P0/P1 待 CEO 决事项变化"
    "（平台名/服务器/域名/备案/微信支付商户号仍未到位，bootstrap/开闸/收费"
    "前台全部按纪律停在其后），P1 呈报面不变；本司产品线本窗把 R2135 单笔"
    "交易档案读面（api_purchase_dossier：双当事方授权·三元组嵌套·"
    "ticket_state 单缝判定）验证收口——套件 SUITE PASS 8/8 双跑判据行逐字节"
    "同一 sha16 087fc5576174bbbf，电池 RUNNER PASS 339/339 套件 + 控制 7/7 "
    "1192.8s，矩阵 339 套件/2820 判据 --check 逐字节同一，census "
    "DRIFT-CLEAN。另有 open 面仍在内部：bootstrap 打包件等物理件、"
    "软著正式申请双前置（平台名 CEO 定谳 + 物理件），零催办。送达="
    "本行 + state log R2135 行 + 本轮 commit 消息。"
)


def read(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main():
    base = BASE

    # 1) explore queue: append the done note to the R2135 claim row.
    path = os.path.join(base, "state", "queue", "explore.md")
    text = read(path)
    marker = "- [x] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886\uff08R2135\uff09"
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("claim row not found")
    end = text.find("\n", idx)
    row = text[idx:end]
    row += (
        "\u3014done 2026-10-26 R2135 \u6536\u53e3\u3015\u4ea7\u54c1="
        "apimarket.py \u65b0\u589e api_purchase_dossier\uff08\u4e8c\u5341\u4e00"
        "\u952e\u4fe1\u5c01\u00b7\u53cc\u5f53\u4e8b\u65b9 viewer_role \u4e70\u5bb6/"
        "\u5356\u5bb6\u4e14\u4f59\u952e\u9010\u5b57\u8282\u540c\u4e00\u00b7\u7b2c\u4e09\u65b9 "
        "E_AM_NOT_PARTY\u00b7\u4e09\u5143\u7ec4\u8bda\u5b9e\u7f3a\u5e2d\u00b7"
        "claim.status \u4e0e ticket_state \u5355\u7f1d\u5224\u5b9a\u00b7\u95e8\u5e8f "
        "\u8d2d\u4e70\u53f7\u5f62\u2192\u8d26\u6237\u5f62\u2192\u5b58\u5728\u2192"
        "\u5f53\u4e8b\u65b9\u00b7\u7eaf\u8bfb\u96f6 token\uff09\uff1b\u5957\u4ef6 "
        "SUITE PASS 8/8 \u53cc\u8dd1\u5224\u636e\u884c\u9010\u5b57\u8282\u540c\u4e00 sha16 "
        "087fc5576174bbbf\uff08qa/apimarket-purchasedossier-R2135b-a.log + "
        "-b.log\u00b7\u5404 1191B \u540c\u4e00\u5b57\u8282\uff09\uff1b\u63a5\u7ebf "
        "ledger-apimarket-purchasedossier(8)\uff1b\u7535\u6c60 "
        "qa/reconcile-all-R2135b.log RUNNER PASS 339/339 suites + controls 7/7 "
        "1192.8s\uff1b\u77e9\u9635 339 suites / 2820 criteria --check "
        "\u9010\u5b57\u8282\u540c\u4e00\uff1bcensus DRIFT-CLEAN files=1862 "
        "flags=0\u3002\u8bda\u5b9e\u6ce8=\u524d\u7a97\u4e2d\u65ad\uff08HEAD \u4ecd\u5728 "
        "R2134\u3001\u6811\u5185\u4ea7\u7269\u672a\u63d0\u4ea4\u3001\u65e0 index.lock\u3001"
        "\u65e0\u6d3b\u7535\u6c60\uff09\uff0c\u672c\u7a97\u590d\u9a8c\u6536\u53e3\uff1b"
        "\u524d\u7a97\u7ea2\u7535\u6c60\u4e24\u4ef6\uff08qa/reconcile-all-R2135.log "
        "\u552f\u4e00\u7ea2 ledger-apimarket-buyerhistory AC-AMBD8\uff1b"
        "qa/reconcile-all-R2135v.log \u7ea2 reconcile-daily-census cd7 "
        "live-tree drift \u4e0e\u4e00\u6b21\u53d7\u6270 ledger-demo \u63a7\u5236\uff09"
        "\u539f\u6837\u4fdd\u7559\uff0c\u7eff\u8dd1\u672a\u590d\u73b0\uff1bcd7 \u7ea2\u7684"
        "\u771f\u56e0=\u524d\u7a97\u65b0\u589e\u8bc1\u636e\u4ef6\u672a\u5165 census "
        "\u57fa\u7ebf\uff0c\u672c\u7a97\u4ee5 LF \u5355\u5199\u8005\u91cd\u51fa\u8bc1\u636e\u540e"
        "\u81ea\u6108\uff08\u672c\u7a97\u9996\u6b21\u91c7\u96c6=ps-utf16/"
        "pwsh-capture \u65b9\u8a00\u5751\uff0c\u51fa\u751f\u7ad9\u62e6\u4e0b\uff09\u3002"
    )
    text = text[:idx] + row + text[end:]
    write(path, text)

    # 2) backlog: prepend the done row under the board header.
    path = os.path.join(base, "src", "os", "backlog.md")
    text = read(path)
    head_marker = "# BigDomain \u8ba4\u9886\u5de5\u4f5c\u677f\uff08backlog\uff09"
    idx = text.find(head_marker)
    if idx < 0:
        raise SystemExit("backlog header not found")
    insert_at = text.find("\n", idx) + 1
    new_row = (
        "\n- [x] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886\uff08R2135\uff09"
        "apimarket **\u5355\u7b14\u4ea4\u6613\u6863\u6848\u8bfb\u9762**"
        "\uff08api_purchase_dossier\uff09\u2014\u2014\u73b0\u884c\u9762\u5404\u7b54\u4e00\u89d2"
        "\uff08api_library \u4e70\u5bb6\u5168\u90e8\u8d2d\u4e70\u3001api_refund \u4e00\u7b14"
        "\u9000\u6b3e\u884c\u3001api_claims \u7d22\u8d54\u961f\u5217\u3001\u4e24\u5f20\u5bf9\u8d26"
        "\u5355\u7b54\u8d44\u91d1\u6d41\uff09\uff0c\u6ca1\u6709\u4efb\u4f55\u9762\u56de\u7b54"
        "\u300c\u8fd9\u4e00\u7b14\u4ea4\u6613\u4ece\u5934\u5230\u5c3e\u53d1\u751f\u4e86\u4ec0\u4e48"
        "\u300d\u2014\u2014\u4e70\u5bb6\u5f00\u5ba2\u670d\u5355\u3001\u5356\u5bb6\u5bf9\u8d26\u4e89\u8bae"
        "\u65f6\u987b\u8de8\u56db\u9762\u624b\u5de5\u62fc\u88c5\u3002\u5224\u636e "
        "AC-AMPD1..AC-AMPD8 \u9884\u6ce8\u518c\u4e8e\u672c\u884c\uff08\u5148\u4e8e\u4ee3\u7801\u00b7"
        "\u516d\u951a git grep -F \u96f6\u5360\u7528 rc=1\uff09\u3002"
        "[done 2026-10-26 R2135]\uff08\u672c\u7a97\u590d\u9a8c\u6536\u53e3\u524d\u7a97\u4e2d\u65ad"
        "\u9057\u7559\u4ea7\u7269\uff1a\u5957\u4ef6 SUITE PASS 8/8 \u53cc\u8dd1\u5224\u636e\u884c"
        "\u9010\u5b57\u8282\u540c\u4e00 sha16 087fc5576174bbbf\uff1b\u63a5\u7ebf "
        "ledger-apimarket-purchasedossier(8)\uff1b\u7535\u6c60 "
        "qa/reconcile-all-R2135b.log RUNNER PASS 339/339 suites + controls 7/7 "
        "1192.8s\uff1b\u77e9\u9635 339 suites / 2820 criteria --check "
        "\u9010\u5b57\u8282\u540c\u4e00\uff1bcensus DRIFT-CLEAN files=1862 flags=0\uff1b"
        "\u524d\u7a97\u7ea2\u7535\u6c60\u4e24\u4ef6\u539f\u6837\u4fdd\u7559\u4e14\u7eff\u8dd1"
        "\u672a\u590d\u73b0\uff09"
    )
    text = text[:insert_at] + new_row + text[insert_at:]
    write(path, text)

    # 3) state.json
    path = os.path.join(base, "src", "os", "state.json")
    with io.open(path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2135
    state["last_decision_rows"] = 228
    state["benchmarks_refreshed"] = "2026-10-25"
    state["log"].append(LOG_R2135)
    state["log"].append(LOG_TOKENS)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    # 4) export face
    path = os.path.join(base, "docs", "status-export.json")
    with io.open(path, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = "2026-10-26T05:20:00+08:00"
    export["ceo_face"]["current"] = (
        "\u5355\u7b14\u4ea4\u6613\u6863\u6848\u9762\uff08api_purchase_dossier\uff09\uff1a"
        "\u5e02\u573a\u628a\u4e70\u5bb6\u3001\u5356\u5bb6\u3001\u9000\u6b3e\u3001\u7d22\u8d54\u3001"
        "\u8d44\u91d1\u6d41\u90fd\u5206\u5f00\u7b54\u4e86\uff0c\u5374\u6ca1\u6709\u4e00\u9762\u56de\u7b54"
        "\u300c\u8fd9\u4e00\u7b14\u4ea4\u6613\u5230\u5e95\u53d1\u751f\u4e86\u4ec0\u4e48\u300d\u3002"
        "\u672c\u8f6e\u628a\u8fd9\u56db\u89d2\u62fc\u6210\u4e00\u5f20\u53cc\u5f53\u4e8b\u65b9\u53ef\u8bfb"
        "\u7684\u6863\u6848\uff1a\u4e70\u5bb6\u770b\u5230\u300c\u6211\u4e70\u7684\u300d\u89c6\u89d2\u3001"
        "\u5356\u5bb6\u770b\u5230\u300c\u6211\u5356\u7684\u300d\u89c6\u89d2\u3001\u4e24\u8fb9\u5185\u5bb9"
        "\u9010\u5b57\u8282\u76f8\u540c\uff0c\u7b2c\u4e09\u65b9\u4e00\u5f8b\u62d2\u7edd\uff1b"
        "\u4e00\u4e2a\u5b57\u6982\u62ec\u5f53\u524d\u72b6\u6001\uff08\u5df2\u9000\u6b3e/\u5df2\u64a4"
        "\u8bc9/\u5df2\u5e94\u7b54/\u5f85\u5e94\u7b54/\u5df2\u8bc4\u4ef7/\u5df2\u7ed3\u7b97\uff09\u3002"
    )
    export["ceo_face"]["latest_artifact"] = (
        "src/sandbox/ledger/apimarket.py\uff08api_purchase_dossier\uff09+ "
        "src/sandbox/ledger/test_apimarket_purchasedossier.py\uff08SUITE PASS "
        "8/8 \u53cc\u8dd1 rc=0/0\uff0c\u5224\u636e\u884c sha16 087fc5576174bbbf\uff0c"
        "\u8bc1\u636e qa/apimarket-purchasedossier-R2135b-a.log / -b.log\uff09\uff1b"
        "qa/reconcile-all-R2135b.log\uff08RUNNER PASS 339/339 \u5957\u4ef6 + "
        "\u63a7\u5236 7/7\uff0c1192.8s\uff09\uff1bdocs/sandbox-suite-matrix.md"
        "\uff08339 \u5957\u4ef6 / 2820 \u5224\u636e\uff0c--check \u9010\u5b57\u8282\u540c\u4e00\uff09\u3002"
    )
    export["ceo_face"]["next_milestone"] = (
        "48 \u5c0f\u65f6\u5185\uff1a\u2460\u628a\u300c\u5df2\u4e0a\u4ea4\u3001\u672a\u5b9e\u540d"
        "\u62ab\u9732\u3001\u88ab\u5ba1\u62d2\u300d\u4e09\u5f20\u5206\u53d1\u4e49\u52a1\u9762\u63a5\u6210"
        "\u4e0a\u67b6\u786c\u95e8\uff08\u73b0\u5728\u53ea\u662f\u53ef\u8bfb\u9762\uff09\uff1b"
        "\u2461\u628a\u4e70\u5bb6/\u5356\u5bb6\u4e24\u5f20\u5bf9\u8d26\u5355\u5408\u6210\u4e00\u5f20"
        "\u7ed3\u7b97\u9875\uff0c\u300c\u8be5\u6536\u591a\u5c11\u3001\u8be5\u4ed8\u591a\u5c11\u300d"
        "\u4e00\u773c\u53ef\u89c1\uff1b\u2462\u628a\u7535\u6c60\u56de\u6536\u8bfb\u6570\u63a5\u8fdb"
        "\u6bcf\u65e5\u62a5\u544a\uff0c\u4f7f\u6e05\u626b\u6210\u4e3a\u53ef\u89c1\u8d8b\u52bf\u3002"
    )
    export["outs"].insert(0, [OUT_TITLE, "on", OUT_TEXT, "2026-10-26"])
    export["results"].insert(0, ["R2135", RESULT_TEXT])
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(export, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    # 5) HQ-FEEDBACK: one P-32 line for the group point-naming.
    path = os.path.join(base, "HQ-FEEDBACK.md")
    text = read(path)
    if not text.endswith("\n"):
        text += "\n"
    text += HQ_LINE + "\n"
    write(path, text)

    print("closeout written")


if __name__ == "__main__":
    main()