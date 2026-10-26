"""R2143 closeout: state.json tick/log/baseline, the explore-queue row
flip with its done note, and the status-export refresh.

Reads the battery evidence so the round line quotes the real runner
result instead of a claim. ASCII source, stdlib only, no network.

Usage: python src/os/r2143_closeout.py [--dry]
"""

import hashlib
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
QUEUE = os.path.join(ROOT, "state", "queue", "explore.md")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BATTERY = os.path.join(ROOT, "qa", "reconcile-all-R2143.log")
SUITE_A = os.path.join(ROOT, "qa", "apimarket-replyrev-R2143-a.log")
SUITE_B = os.path.join(ROOT, "qa", "apimarket-replyrev-R2143-b.log")
REGRESS = os.path.join(ROOT, "qa", "regress-replyrev-R2143.log")

if BASE not in sys.path:
    sys.path.insert(0, BASE)
import check_export_consistency as C   # noqa: E402

NEW_TOKENS = ["D-20261026-10", "D-20261026-11", "D-20261026-12",
              "D-20261026-13", "D-20261026-14"]

EXPORT_TS = "2026-10-26T13:20:00+08:00"

DONE_NOTE = (
    " \u3014done 2026-10-26 R2143\u3015\u4ea7\u54c1=apimarket.py "
    "\u65b0\u589e append-only `apimarket_reply_revisions`\uff08\u57fa\u7840"
    "\u56de\u5e94\u884c\u6c38\u4e0d\u6539\u5199\uff09+ `revise_reply`\uff08"
    "\u95e8\u5e8f \u8d26\u6237\u5f62\u2192\u56de\u5e94\u53f7\u5f62\u2192"
    "\u6587\u5f62\u2192\u5b58\u5728\u2192\u5f52\u5c5e\u2192\u65e0\u53d8"
    "\u5316\uff1b\u4e24\u4e2a\u65b0\u7801 E_AM_UNKNOWN_REPLY / "
    "E_AM_REPLY_UNCHANGED\uff1b\u62d2\u7edd\u96f6\u884c\u96f6 token\uff09+ "
    "`api_reply_history`\uff08\u5341\u4e8c\u952e\u4fe1\u5c01\u00b7\u57fa"
    "\u7840\u5bf9\u751f\u6548\u5206\u5217\u00b7\u4fee\u8ba2\u5e8f\u5217"
    "\uff09+ \u5355\u7f1d `_effective_reply` \u4f9b api_rating_replies "
    "\u5171\u7528\u3002\u8bc1\u636e=\u5957\u4ef6 SUITE PASS 8/8 \u53cc\u8dd1"
    " rc=0/0 \u5224\u636e\u884c\u9010\u6761\u4e00\u81f4\uff08qa/apimarket-"
    "replyrev-R2143-a.log + -b.log\uff0c\u5355\u5199\u8005 utf-8 LF\uff09\uff1b"
    "\u63a5\u7ebf ledger-apimarket-replyrev(8)\uff1b\u76f8\u90bb\u4e03\u5957"
    "\u4ef6\u56de\u5f52 rc=0\uff08qa/regress-replyrev-R2143.log\uff09\u3002"
    "\u8bda\u5b9e\u6ce8\u4e24\u5904\uff1a\u2460\u9996\u8dd1\u4e24\u5904\u7ea2"
    "\u5747\u4e3a\u6d4b\u8bd5\u4fa7\u671f\u671b\u7f3a\u9677\uff08\u88f8 "
    "'usr:' \u524d\u7f00\u5f62\u6309 R2077/R2078 \u5148\u4f8b\u8fc7\u5f62"
    "\u72b6\u95e8\u540e\u7531\u5f52\u5c5e\u95e8\u62e6\uff1b\u661f\u503c"
    "\u4fee\u8ba2\u4f1a\u8ba9\u6574\u5c01\u4fe1\u53d8\u5316\u800c\u56de"
    "\u5e94\u884c\u672c\u8eab\u4e0d\u53d8\uff09\uff0c\u4fee\u6d4b\u8bd5"
    "\u4e0d\u653e\u5bbd\u5224\u636e\uff1b\u2461\u4e24\u8dd1\u7684 sha16 "
    "\u4e0d\u540c\u5c5e\u9884\u671f\uff08\u6bcf\u8dd1\u65b0\u79cd\u4e16\u754c"
    "\u5404\u81ea\u76d6\u58c1\u949f\u6233\uff09\uff0c\u56e0\u6b64\u53cc\u8dd1"
    "\u5bf9\u6bd4\u53e3\u5f84=\u9010\u6761\u5224\u636e\u7ed3\u8bba\uff08\u516b"
    "\u6761\u5168\u540c\uff09\u800c\u975e\u6574\u6587\u5b57\u8282\u3002\n")


def read(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def battery_line():
    text = read(BATTERY)
    hits = [ln for ln in text.splitlines() if ln.startswith("RUNNER")]
    return hits[-1].strip() if hits else "RUNNER LINE MISSING"


def verdicts(path):
    return [ln.split(":")[0] for ln in read(path).splitlines()
            if ln.startswith(("PASS", "FAIL"))]


def main(argv=None):
    dry = bool(argv and "--dry" in argv)
    run_line = battery_line()
    va = verdicts(SUITE_A)
    vb = verdicts(SUITE_B)
    regress = [ln.strip() for ln in read(REGRESS).splitlines() if ln.strip()]
    regress_ok = all("rc=0" in ln for ln in regress)

    state = json.loads(read(STATE))
    tick = int(state["tick"]) + 1

    field_line = (
        "2026-10-26 R%d (five-silence scan: decisions.md carried five new"
        " content-addressed tokens D-20261026-10..14 against the stored"
        " baseline - the BigMoney patrol stand-down, the BigCompute alignment"
        " receipt, the worktree merge-push split, the BigLife GBK repair and"
        " the MiniGame structural-gap escalation are all other seats'"
        " execution faces (acknowledged, zero action, baseline advanced); the"
        " ledger carries the same two @BigDomain patrol rows already paid off"
        " and zero unreplied; the group orders baseline is unchanged at the"
        " 2026-10-26 09:30 patrol row; benchmarks refreshed 2026-10-26 inside"
        " the seven-day gate; tree clean, no index.lock; all four tech heads"
        " stayed gated - docker host absent, logs toolkit standing"
        " maintenance, member refunded schema product-gated, the live-mtime"
        " row waiting on a real normalized-mtime event - and the single"
        " explore row is gated on the merchant id) - this window first"
        " honoured the R2142 carry-over (its own log line said the full"
        " battery was NOT run and was the first item of the next round), then"
        " seeded and claimed a fresh P3 row in the SAME window with"
        " AC-AMRY1..AC-AMRY8 pre-registered BEFORE the code existed (AC-AMRY,"
        " revise_reply, api_reply_history, apimarket_reply_revisions,"
        " E_AM_REPLY_UNCHANGED, E_AM_UNKNOWN_REPLY, the suite name and the"
        " runner label were all git grep -F zero-occupancy anchored"
        " 2026-10-26, rc=1) - the seller reply-revision leg. Gap statement:"
        " reply_to_rating (R2093) is write-once behind UNIQUE(rating_id) and"
        " E_AM_REPLY_DUP, while R2094 let the buyer revise the stars at any"
        " time, so a seller who answered 'glad it worked' under five stars"
        " stayed welded to that sentence when the same rating became one"
        " star; every other write-once axis already grew a remedy leg (price"
        " R2079, metadata R2083, supply R2095, rating R2094, provider"
        " identity R2136) and the review face got a cycle law (R2133), which"
        " made the reply the last unremedied axis on the trust face. Product:"
        " apimarket.py grows an append-only apimarket_reply_revisions table"
        " and revise_reply, whose pinned gate order is account shape,"
        " reply-id shape, text shape, reply existence, ownership, unchanged"
        " state; the unchanged gate compares against the EFFECTIVE text so"
        " revising back to an earlier wording stays legal while the first"
        " stamp is never rewritten, a retired listing keeps its reply leg"
        " revisable (retirement freezes the shelf, not the duty to answer),"
        " and the effective-text seam is single (_effective_reply feeds"
        " api_rating_replies) so api_reply_history and the conversation face"
        " can never disagree. Suite"
        " src/sandbox/ledger/test_apimarket_replyrev.py SUITE PASS 8/8"
        " double-run rc=0/0 with per-criterion verdicts identical"
        " (qa/apimarket-replyrev-R2143-a.log + -b.log, single-writer UTF-8"
        " LF), wired as ledger-apimarket-replyrev(8); seven adjacent suites"
        " rc=0 each (ratingreply, ratingrev, ratingagg, sellerinbox,"
        " sellerquality, marketfeed, purchasedossier) ="
        " qa/regress-replyrev-R2143.log; suite matrix regenerated and --check"
        " byte-identical; full battery %s. Two defects found during the"
        " window, both test-side and disclosed: (a) the first cut expected the"
        " bare 'usr:' account form to fail the shape gate, but it passes that"
        " gate by the R2077/R2078 prefix precedent and is then stopped by the"
        " ownership gate, so the expectation was corrected rather than the"
        " criteria loosened; (b) the rating-revision orthogonality probe first"
        " compared whole envelopes, which move because the star value moves,"
        " and now compares the reply row itself. Honest note: the two suite"
        " runs report different envelope sha16 values because each run seeds"
        " its own world with its own wall-clock stamps, so the double-run"
        " comparison caliber is the per-criterion verdict list (8/8 both"
        " runs), not whole-file bytes. A first battery launched before the"
        " product diff landed was killed once its mixed baseline was spotted;"
        " it produced no evidence file. Boundary stated rather than hidden:"
        " the public activity feed keeps the historical rating_replied event"
        " with the wording that was said at that moment, and a reply revision"
        " is deliberately NOT a new feed kind in this slice (the feed kind set"
        " and its rank order are pinned by its own suite), so the feed is"
        " history while api_reply_history and api_rating_replies are the"
        " current text."
        % (tick, run_line))

    token_line = ("R%d tokens: local=~%dk api=0 api_reason=five-silence scan"
                  " + answer to the R2142 battery carry-over + reply-revision"
                  " product change (table + door + history face + one seam) +"
                  " suite 8/8 double-run + seven adjacent regressions + matrix"
                  " regen/check + evidence logs + state/export closeout, zero"
                  " cloud calls" % (tick, 120))

    body = read(QUEUE)
    if "AC-AMRY1" not in body:
        raise SystemExit("claim row missing")
    if "done 2026-10-26 R2143" in body:
        print("queue row already closed")
    else:
        head = "- [ ] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97"
        idx = body.find(head)
        if idx < 0:
            raise SystemExit("claim row head missing")
        end = body.find("\n- [", idx)
        if end < 0:
            raise SystemExit("claim row tail missing")
        body = (body[:idx] + "- [x]" + body[idx + len(head):end]
                + DONE_NOTE + body[end:])
        if not dry:
            with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
        print("queue row closed")

    state["tick"] = tick
    state["last_decision_rows"] = 252
    tokens = state.get("last_dec_tokens", "").split(",")
    for tok in NEW_TOKENS:
        if tok not in tokens:
            tokens.append(tok)
    state["last_dec_tokens"] = ",".join(tokens)
    state.setdefault("log", []).append(field_line)
    state["log"].append(token_line)

    if not dry:
        with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    print("tick=%d tokens=%d verdicts=%d/%d regress_ok=%r"
          % (tick, len(tokens), len(va), len(vb), regress_ok))
    print(run_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))