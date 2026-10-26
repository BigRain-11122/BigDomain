"""R2143 export refresh: merge the round payload into
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

EXPORT_TS = "2026-10-26T12:47:00+08:00"

CEO_FACE = {
    "current": "\u672c\u8f6e\u628a\u5f00\u53d1\u8005 API \u5e02\u573a"
               "\u7684\u4fe1\u4efb\u9762\u8865\u4e0a\u4e86\u6700\u540e"
               "\u4e00\u6761\u6551\u6d4e\u8def\uff1a\u5356\u5bb6\u5bf9"
               "\u8bc4\u4ef7\u7684\u56de\u5e94\u4e0d\u518d\u662f\u4e00"
               "\u9524\u5b50\u4e70\u5356\uff0c\u4e70\u5bb6\u6539\u661f"
               "\u540e\u5356\u5bb6\u80fd\u91cd\u65b0\u8bf4\u8bdd\uff0c"
               "\u4e14\u6bcf\u6b21\u4fee\u8ba2\u90fd\u7559\u5e95\u3002",
    "latest_artifact": "src/sandbox/ledger/apimarket.py \u7684 revise_reply + "
                       "api_reply_history + qa/apimarket-replyrev-R2143-a.log"
                       "\uff088/8 \u53cc\u8dd1\uff09+ qa/regress-replyrev-"
                       "R2143.log\uff08\u4e03\u5957\u4ef6\u96f6\u56de\u5f52"
                       "\uff09 \u2014 2026-10-26 12:45",
    "next_milestone": "48 \u5c0f\u65f6\u5185\uff1a\u8fd9\u6761\u56de\u5e94"
                      "\u4fee\u8ba2\u8f74\u63a5\u8fdb\u7ed3\u7b97\u62a5"
                      "\u544a\u4e0e\u5e02\u573a\u6d3b\u52a8\u6d41\uff0c"
                      "\u5e76\u8ba9\u5168\u91cf\u7535\u6c60\u8986\u76d6"
                      "\u672c\u8f6e\u6700\u7ec8\u4ee3\u7801\uff1b\u5546"
                      "\u6237\u53f7\u4ecd\u672a\u5230\uff0c\u652f\u4ed8"
                      "\u4e0e\u6743\u76ca\u8bbe\u8ba1\u4ef6\u7ee7\u7eed"
                      "\u5148\u884c\u3002",
}

OUT_NAME = "apimarket seller reply-revision leg (revise_reply)"

OUT_TEXT = (
    "R2143: reply_to_rating was write-once behind UNIQUE(rating_id) and"
    " E_AM_REPLY_DUP, while the rating revision door (R2094) lets the buyer"
    " change the stars at any time, so a seller who answered under five stars"
    " stayed welded to that sentence when the same rating became one star - the"
    " last write-once axis on the trust face without a remedy leg (price,"
    " metadata, supply, rating and provider identity all grew one, and the"
    " review face got a cycle law in R2133). apimarket.py now grows an"
    " append-only apimarket_reply_revisions table and revise_reply, with the"
    " pinned gate order account shape, reply-id shape, text shape, existence,"
    " ownership, unchanged state; the unchanged gate is judged against the"
    " EFFECTIVE text so a revise-back stays legal while the first stamp is never"
    " rewritten; a retired listing keeps its reply leg revisable; and one seam"
    " (_effective_reply) feeds api_rating_replies so the conversation face and"
    " the new api_reply_history can never disagree. Laws pinned by"
    " AC-AMRY1..AC-AMRY8: the append-only contract with a byte-frozen base row,"
    " every refusal fail-closed with all table digests, the ledger tx set and"
    " the four account balances frozen, the history envelope and its ordered"
    " revision rows, the pure-read law, orthogonality with the buyer-side rating"
    " revision in both directions, and cross-restart byte identity on three"
    " instances. Suite SUITE PASS 8/8 double-run rc=0/0 with identical"
    " per-criterion verdicts (qa/apimarket-replyrev-R2143-a.log and -b.log,"
    " single-writer UTF-8 LF); seven adjacent suites rc=0 each; matrix"
    " regenerated and --check byte-identical.")

RESULT_TEXT = (
    "R2143: honoured the R2142 battery carry-over, then seeded and claimed a"
    " fresh P3 explore row in the same window with AC-AMRY1..AC-AMRY8"
    " pre-registered BEFORE the code existed (eight anchors git grep -F"
    " zero-occupancy, rc=1) and delivered the seller reply-revision leg."
    " Product change in src/sandbox/ledger/apimarket.py (append-only"
    " apimarket_reply_revisions + revise_reply + api_reply_history + the"
    " _effective_reply seam into api_rating_replies). Verification: new suite"
    " 8/8 double-run rc=0/0 with identical per-criterion verdicts"
    " (qa/apimarket-replyrev-R2143-a.log and -b.log); registration"
    " ledger-apimarket-replyrev(8); seven adjacent suites rc=0 each"
    " (ratingreply, ratingrev, ratingagg, sellerinbox, sellerquality,"
    " marketfeed, purchasedossier) = qa/regress-replyrev-R2143.log; suite"
    " matrix regenerated and --check byte-identical. Honest disclosures: (a)"
    " the first cut expected the bare 'usr:' account form to fail the shape"
    " gate, but it passes that gate by the R2077/R2078 prefix precedent and is"
    " then stopped by the ownership gate, so the test expectation was"
    " corrected instead of the criteria being loosened; (b) the"
    " rating-revision orthogonality probe first compared whole envelopes, which"
    " necessarily move when the star value moves, and now compares the reply"
    " row itself; (c) the two suite runs report different envelope sha16 values"
    " because each run seeds its own world with its own wall-clock stamps, so"
    " the double-run caliber is the per-criterion verdict list, not whole-file"
    " bytes; (d) a first battery launched before the product diff landed was"
    " killed once its mixed baseline was spotted and produced no evidence"
    " file, and the battery quoted above was run on the final content; (e) the"
    " public activity feed keeps the historical rating_replied event with the"
    " wording said at that moment and a reply revision is deliberately not a"
    " new feed kind in this slice, so the feed is history while the history and"
    " conversation faces carry the current text - stated as a boundary, not"
    " left as a silent gap.")


def main():
    with io.open(EXPORT, "rb") as handle:
        data = json.loads(handle.read().decode("utf-8"))
    data["export_ts"] = EXPORT_TS
    data["ceo_face"] = dict(CEO_FACE)
    data["outs"].append([OUT_NAME, "on", OUT_TEXT])
    data["results"].append(["R2143", RESULT_TEXT])
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