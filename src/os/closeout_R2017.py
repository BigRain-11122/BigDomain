# closeout_R2017.py - R2017 (34th-case takeover closeout)
# driver: (1) state.json byte surgery (tick 2016 -> 2017,
# two-line log append via ps_escape; baselines unchanged:
# last_order 13:5x / DEC 356 / GORD 455 all held flat this
# round), (2) heartbeat.txt line, (3) state/queue/explore.md
# done-flip + done note + consume-1 reseed-1 conservation,
# (4) status-export.json refresh (ceo_face + results R2017
# row prepend + tick row 2017 + self_drive recompute).
# ASCII script logic; CJK content lives in the constants
# (closeout_R2016.py precedent).
import io
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_QUEUE = os.path.join(ROOT, "state", "queue", "explore.md")

ROUND_LINE = (
    u"2026-10-17 R2017\uff08\u4e94\u9759\u68c0\u51fa=[TREE] FLAG \u810f\u6811 8 "
    u"\u4ef6=R2017 \u5d29\u8f6e\u5b64\u513f\u8f7d\u8377\u3014LEDGER @BigDomain "
    u"\u96f6\u65b0\u884c+DEC 356 \u57fa\u7ebf\u6301\u5e73+ORD \u5c3e 13:5x \u6301\u5e73+"
    u"GORD 455 \u6301\u5e73 gord_new_rows=0+benchmarks \u5f53\u65e5\u5df2\u5237+"
    u"export 2.8h \u65b0\u9c9c+HB \u65d7=\u5d29\u8f6e\u672a\u6536\u8d26\u9762\u3015\u2192"
    u"\u7b2c 34 \u4f8b\u5d29\u8f6e\u63a5\u7ba1\u6536\u53e3\u8f6e\uff1a\u5d29\u6e83\u8f6e\u5b8c\u6210"
    u"\u4ea7\u54c1\u9762+\u5957\u4ef6\u53cc\u8dd1\u8bc1\u636e+\u7535\u6c60\u4e00\u8dd1 RUNNER FAIL "
    u"\u5b9a\u8c2d+baseline \u5408\u6cd5\u91cd\u951a+\u7535\u6c60\u4e8c\u8dd1\u81f3 184/234 "
    u"\u5904\u6b7b\u4e8e\u4f1a\u8bdd\u8fde\u5e26\u51fb\u6740\u3014\u8f7d\u8377\u5728\u76d8\u4fdd\u5168="
    u"R1924/R1976/R2015/R2016 \u63a5\u7ba1\u5148\u4f8b\u65cf\u3015\u2014\u2014\u4ea7\u54c1\u4ef6="
    u"test_showcase_statsmonthboundarypersist.py\u3014suite-only\u00b7AC-SSMZ1..SSMZ7 "
    u"\u5224\u636e\u9884\u6ce8\u518c\u5148\u4e8e\u5957\u4ef6\u4ee3\u7801\u00b7\u5d29\u6e83\u8f6e\u4ea4"
    u"\u4ed8\u3015\uff1a\u96f6\u6ce8\u518c\u8fb9\u754c\u4e16\u754c\u4e03\u5f62\u7a97\u8bfb\u65cf\u5168"
    u"\u5f62\u8bda\u5b9e\u7a7a\u4fe1\u5c01\u9489\u6b7b\u3014full \u6070\u4e24\u952e rows==[]/cap2 "
    u"\u516d\u952e total=0/\u56db\u7a97\u4e09\u952e\u5e26\u7a97\u56de\u58f0/wcap2 \u4e03\u952e\u5168"
    u"\u96f6\u5757\u3015+\u7a7a\u4e16\u754c\u95e8\u65cf\u5148\u4e8e\u4efb\u4f55\u8bfb\u30149 \u574f\u7a97 "
    u"E_SH_BAD_WINDOW+5 \u574f limit E_SH_BAD_LIMIT+\u95e8\u5e8f\u63a2\u9488\u5148\u62d2+"
    u"\u63a2\u9488\u6279\u8ba1\u6570\u6052\u5b9a\u3015+\u5168\u6808\u8de8\u91cd\u542f\u4e03\u5f62"
    u"\u9010\u5b57\u8282\u540c\u4e00\u3014sh\u2192led close \u540c\u8def\u5f84\u91cd\u5efa\u96f6"
    u"\u5185\u5b58\u6001\u6f02\u79fb\u3015+\u91cd\u542f\u540e\u9996\u6ce8\u518c dense \u7eed\u63a5"
    u"\u96f6\u5e7b\u5f71\u3014\u5168\u5f62\u8bda\u5b9e\u96f6\u884c+cap total 0\u21921+\u699c\u884c"
    u"==\u6ce8\u518c\u884c\u6070\u4e00\u3015+\u91cd\u542f\u540e\u9996\u6536\u7f6e\u73b0\u6708\u7a97"
    u"\u5206\u88c2\u3014\u771f\u8def\u5f84 place SecGate \u8fc7\u95f8+\u51c0\u6d41\u6052\u7b49\u5f0f+"
    u"SQL substr(acted_utc,1,7) \u4ea4\u53c9+\u65e7\u7a97\u5b57\u8282\u51bb\u7ed3\u3015+\u7b2c"
    u"\u4e09\u5b9e\u4f8b\u7a33\u5b9a+\u7eaf\u8bfb\u5f8b+\u536b\u751f\u3014\u4ea7\u54c1\u4e09\u4ef6 "
    u"sha256 \u53cc\u8bc1\u96f6\u6539\u52a8\u3015\u2014\u2014\u63a5\u7ba1\u8005\u4eb2\u9a8c=SUITE "
    u"\u590d\u8dd1\u53cc\u8dd1 stdout \u9010\u5b57\u8282\u540c\u4e00 sha16 429ba7dd168113ed "
    u"\u951a\u5408\u5d29\u6e83\u8f6e\u53cc\u8dd1+RUNNER \u7535\u6c60\u91cd\u8dd1 PASS 234/234 "
    u"\u5224\u636e 1990\u21921997\u3014SUITES 233\u2192234\u3015controls 7/7 283.2s=qa/"
    u"reconcile-all-R2017-3.log+\u56db\u7535\u6c60\u9762 VERDICT PASS\u3014\u77e9\u9635\u518d"
    u"\u751f 234/1997 --check byte-identical+\u6307\u7eb9+profile daily+main \u53cc\u9762+"
    u"census --check DRIFT-CLEAN\u3015\u2014\u2014\u5d29\u6e83\u8f6e\u7535\u6c60\u4e00\u8dd1 "
    u"RUNNER FAIL \u5355\u56e0\u5b9a\u8c2d=census cd7 \u6d3b\u6811\u9762 R2016.log \u672a\u5165 "
    u"baseline\uff08\u4e0a\u4e00\u8f6e\u6536\u53e3\u9057\u7559\u00b7\u975e\u4ea7\u54c1\u56de\u5f52"
    u"\uff09\u00b7\u5d29\u6e83\u8f6e\u540c\u8f6e\u81ea\u4fee=--update-baseline \u5408\u6cd5\u91cd"
    u"\u951a\uff08R2010/R1996 \u5148\u4f8b\u65cf\uff09\u00b7\u4e8c\u8dd1\u8bda\u5b9e\u4e2d\u65ad"
    u"\u4ef6\u4fdd\u5168\u3014qa/reconcile-all-R2017.log+R2017-2.log\u3015\u2014\u2014explore "
    u"\u6d88\u8d39 1 \u8865\u79cd 1 \u5b88\u6052\u3014\u6536\u7f6e\u56de\u64a4\u540e\u73b0\u6708"
    u"\u7a97\u6d3b\u6001\u8de8\u91cd\u542f\u4f8b\u7a97\u79cd\u5b50\u5165\u5217\u3015\u00b7\u8bc1"
    u"\u636e=qa/showcase-statsmonthboundary-R2017.log\u2014\u2014fold R547 \u6536\u8d26\u524d"
    u"\u7f6e\u5151\u73b0\u3014\u8f6e\u9996 gauge 77114B+R2017 round+tokens \u6536\u8d26\u9884\u7b97"
    u"\u5fc5\u8d8a 78500B \u7ebf\u00b7tail-3 \u7a97\u538b 1 \u6eda\u7a97\u884c kept=0\u00b7token "
    u"\u673a\u68b0\u5d4c\u5165\u96f6\u4e22\u5931 gen547\u00b7archive \u00a7R2017 3 \u884c "
    u"verbatim+preop logs/state-preop-R2017.bak\u3015\u2014\u2014score 2\u3014\u5d29\u8f6e\u4ea7"
    u"\u54c1\u4ef6+\u8bc1\u636e+\u6ce8\u518c\u884c\u63a5\u7ba1\u4e0a\u94fe\u3015\uff09"
)

TOKENS_LINE = (
    "R2017 tokens: local=~1.4M api=0 api_reason=34th-case "
    "takeover closeout all local (five-silence scan + orphan "
    "payload triage + census standalone check + suite "
    "double-run re-verify anchor-matched + full battery "
    "RUNNER re-run 283.2s + four-face followup + fold R547 "
    "gen/execute + state/queue/heartbeat/export edits + "
    "directed commit), zero cloud calls"
)

HB_BODY = (
    "R2017: 34th-case takeover closeout - the crashed round's "
    "statsmonth zero-registry boundary persist suite landed "
    "on-chain with personal re-verification. Suite "
    "test_showcase_statsmonthboundarypersist.py (AC-SSMZ1.."
    "SSMZ7 pre-registered before code): zero-registry world "
    "seven-form month-window family pinned honest-empty, "
    "gates fire before any read on the empty world, "
    "full-stack close/reopen byte-identical, post-restart "
    "first registration dense-continues with zero phantom, "
    "post-restart first current-month place splits the "
    "current window (netflow identity, SQL cross, old "
    "windows byte-frozen), third instance stable, pure-read "
    "+ hygiene (three product sha pinned). SUITE 7/7 "
    "double-run identical sha16 429ba7dd168113ed; crashed "
    "battery attempt1 FAIL root-caused to census cd7 "
    "live-tree single cause (R2016.log un-baselined - "
    "crashed round self-fixed via legal re-anchor, "
    "non-product), attempt2 died at 184/234 on session kill "
    "(honest incomplete preserved); takeover battery re-run "
    "RUNNER PASS 234/234 criteria 1990->1997 controls 7/7 "
    "283.2s (qa/reconcile-all-R2017-3.log); four-face "
    "battery VERDICT PASS (matrix 234/1997 --check "
    "byte-identical, fingerprint, profile daily+main, "
    "census DRIFT-CLEAN). fold R547 closeout-precedent "
    "honored. Score 2."
)

CEO_CURRENT = (
    "R2017: 34th-case takeover closeout - the crashed "
    "round's P3 explore claim landed end-to-end: showcase "
    "stats_board month-window zero-registry boundary persist "
    "example window (criteria AC-SSMZ1..SSMZ7 pre-registered "
    "in the explore.md claim row before code by the crashed "
    "round; prefix/suite/registry names git-grep "
    "zero-occupancy verified). Suite "
    "test_showcase_statsmonthboundarypersist.py (suite-only, "
    "three product files sha256 pinned unchanged): the "
    "zero-registry world (ledger domain has data, registry "
    "axis empty) pins the seven-form window read family "
    "honest-empty with exact envelope key sets, the gate "
    "family still fires before any read on the empty world "
    "(9 malformed windows + 5 bad limits + gate-order "
    "probe), full-stack close/reopen byte-identical (zero "
    "in-memory drift, boundary state included), post-restart "
    "first registration dense-continues every window form "
    "with zero phantom, post-restart first current-month "
    "place recomputes only the current window (netflow "
    "identity, SQL substr cross, other windows "
    "byte-frozen), third instance stable, pure-read + "
    "hygiene. Takeover personal verification: suite re-run "
    "double-run byte-identical sha16 429ba7dd168113ed "
    "anchor-matched; battery re-run RUNNER PASS 234/234 "
    "criteria 1990->1997 controls 7/7 283.2s; four-face "
    "battery VERDICT PASS (matrix --check byte-identical, "
    "fingerprint, profile daily+main, census DRIFT-CLEAN). "
    "Crashed round attempt1 battery FAIL root-caused to "
    "census cd7 single cause (R2016.log un-baselined, "
    "crashed round self-fixed via legal re-anchor, "
    "non-product); attempt2 died at 184/234 on session kill, "
    "honest incomplete preserved. fold R547 "
    "closeout-precedent honored. Score 2."
)

CEO_LATEST = (
    "qa/showcase-statsmonthboundary-R2017.log + "
    "src/sandbox/ledger/test_showcase_statsmonthboundary"
    "persist.py (SUITE 7/7 double-run identical, RUNNER "
    "234/234 green, 2026-10-17)"
)

CEO_NEXT = (
    "P3 explore queue: next open heads (dev_sales_board "
    "month-window, dev_sales_board zero-listing boundary "
    "persist, yearbooks_combined multi-year persist, "
    "coverage-dual month-roll) + R2017 reseed statsmonth "
    "post-retract current-window liveness persist row; P2 "
    "tech gated rows unchanged, window <=48h (by "
    "2026-10-19)"
)

RESULTS_ROW = (
    "R2017: 34th-case takeover closeout landed the crashed "
    "round's P3 explore claim end-to-end: showcase "
    "stats_board month-window zero-registry boundary "
    "persist example window (the R2016-reseed row, strict "
    "topmost-open claim; criteria AC-SSMZ1..AC-SSMZ7 "
    "pre-registered in the explore.md claim row before "
    "code, AC-SSMZ prefix + suite + registry names "
    "git-grep zero-occupancy verified by the crashed "
    "round). Suite-only round (showcase.py + both shipped "
    "config.json sha256 pinned unchanged): (1) "
    "zero-registry control anchor - the seven-form window "
    "read family {full, cap2, wcur, wcap2, wprev, whist, "
    "wzero-2099} all honest-empty with exact envelope key "
    "sets (2/6/3/7 keys, window echoes intact), family "
    "double-call byte-identical; (2) the empty world "
    "still gates first: 9 malformed windows E_SH_BAD_WINDOW "
    "+ 5 bad limits E_SH_BAD_LIMIT + gate-order probe "
    "(E_SH_BAD_LIMIT first), probe batch row counts flat "
    "(gates independent of the empty data face); (3) "
    "full-stack close (sh -> led) then rebuild on the same "
    "db/cfg/sh paths: all seven forms byte-identical "
    "(derived month-window face carries zero in-memory "
    "state across restart, boundary state included); (4) "
    "post-restart first registration: full face one "
    "honest-zero row, cap total 0->1, every window form "
    "carries the same dense zero-count row (registry axis "
    "survives every window), zero phantom (board rows == "
    "registry rows == 1); (5) post-restart first "
    "current-month place (real path: collectibles dock "
    "reconnect + SecGate pass): current-window row "
    "recomputes {places=1, displayed_now=1} with the "
    "netflow identity and the independent SQL "
    "substr(acted_utc,1,7) cross, other window boards "
    "byte-frozen, cross-face displayed_now == "
    "len(showcase_view displayed); (6) third instance == "
    "second-instance final state byte-identical; (7) "
    "pure-read law + hygiene (read battery counts flat, "
    "method source zero write statements zero RNG, suite "
    "pure ASCII zero network imports, world db outside "
    "the repo, product shas stable). SUITE PASS 7/7 "
    "double-run stdout byte-identical sha16 "
    "429ba7dd168113ed (takeover re-verification "
    "anchor-matched to the crashed round's own double "
    "run); reconcile_all wiring "
    "ledger-showcase-statsmonthboundary-persist criteria 7 "
    "(234 suites, criteria 1990->1997); takeover battery "
    "re-run RUNNER PASS 234/234 suites green controls 7/7 "
    "283.2s zero regression (qa/reconcile-all-R2017-3.log); "
    "four-face battery VERDICT PASS (matrix regen "
    "234/1997 --check byte-identical, fingerprint, "
    "runner_profile --daily and main --check PASS, "
    "qa-writer census --check DRIFT-CLEAN). Crashed-round "
    "forensics honestly preserved: attempt1 battery RUNNER "
    "FAIL (2 assertions) root-caused to the census cd7 "
    "live-tree single cause (R2016.log un-baselined - the "
    "previous round's closeout left its battery log "
    "unregistered; the crashed round self-fixed via "
    "--update-baseline legal re-anchor, R2010/R1996 "
    "precedent, non-product-regression), attempt2 died at "
    "184/234 suites on the session-kill (honest incomplete "
    "preserved: qa/reconcile-all-R2017.log, "
    "qa/reconcile-all-R2017-2.log). fold R547 "
    "closeout-precedent honored (tail-3 window folded to "
    "one rolling line kept=0, tokens mechanically embedded "
    "zero-loss, archive verbatim + preop backup "
    "logs/state-preop-R2017.bak). Explore consume-1 "
    "reseed-1 (statsmonth post-retract current-window "
    "liveness persist seed). Score 2."
)

QUEUE_FLIP_OLD = (
    u"- [ ] \u5c55\u793a\u6a71\u7a97\u7edf\u8ba1\u699c\u6708\u4efd\u7a97\u96f6"
    u"\u6ce8\u518c\u8fb9\u754c\u4e16\u754c\u8de8\u91cd\u542f\u4f8b\u7a97\u63a2\u7d22"
)
QUEUE_END_ANCHOR = (
    u"\u8bc1\u636e qa/showcase-statsmonthboundary-R2017.log\uff08\u5957\u4ef6"
    u"\u53cc\u8dd1+RUNNER \u5168\u91cf+\u77e9\u9635\u4e09\u8282\uff09"
)
QUEUE_DONE_NOTE = (
    u"\u2014\u2014\u3014done 2026-10-17 R2017\u00b734th-case \u5d29\u8f6e\u63a5\u7ba1"
    u"\u6536\u53e3\uff1aAC-SSMZ1..SSMZ7 \u5168\u8fc7\u2014\u2014SUITE 7/7 \u53cc\u8dd1 "
    u"stdout \u9010\u5b57\u8282\u540c\u4e00 sha16 429ba7dd168113ed\uff08\u63a5\u7ba1"
    u"\u8005\u4eb2\u9a8c\u951a\u5408\u5d29\u6e83\u8f6e\u53cc\u8dd1\uff09+\u63a5\u7ba1\u8005 "
    u"RUNNER \u91cd\u8dd1 PASS 234/234 \u5224\u636e 1990\u21921997 controls 7/7 "
    u"283.2s=qa/reconcile-all-R2017-3.log+\u56db\u7535\u6c60\u9762 VERDICT PASS\uff08"
    u"\u77e9\u9635 234/1997 --check byte-identical+\u6307\u7eb9+profile \u53cc\u9762+"
    u"census DRIFT-CLEAN\uff09\u00b7\u5d29\u6e83\u8f6e\u7535\u6c60\u4e00\u8dd1 FAIL="
    u"census cd7 \u6d3b\u6811\u5355\u56e0\uff08R2016.log \u672a\u5165 baseline\u00b7"
    u"\u5d29\u6e83\u8f6e\u540c\u8f6e\u81ea\u4fee\u5408\u6cd5\u91cd\u951a\u00b7\u975e\u4ea7"
    u"\u54c1\u56de\u5f52\uff09\u00b7\u4e8c\u8dd1\u6b7b\u4e8e\u4f1a\u8bdd\u8fde\u5e26\u51fb"
    u"\u6740 184/234 \u5904\uff08\u8bda\u5b9e\u4e2d\u65ad\u4ef6\u4fdd\u5168\uff09\u3015"
)
QUEUE_RESEED = (
    u"- [ ] \u5c55\u793a\u6a71\u7a97\u7edf\u8ba1\u699c\u6708\u4efd\u7a97\u6536\u7f6e"
    u"\u56de\u64a4\u540e\u73b0\u6708\u7a97\u6d3b\u6001\u8de8\u91cd\u542f\u4f8b\u7a97\u63a2"
    u"\u7d22\uff08statsmonth \u65cf retract persist \u540e\u7ee7\uff1aclose\u2192\u65b0"
    u"\u5b9e\u4f8b\u540c db/cfg \u8def\u5f84\u91cd\u5f00\u00b7\u91cd\u542f\u540e\u9996 "
    u"retract \u73b0\u6708\u7a97\u51c0\u6d41\u6052\u7b49\u5f0f\u3014displayed_now=="
    u"places\u2212retracts\u3015\u4e0e\u65e7\u7a97\u51bb\u7ed3\u4f8b\u3014R2016 "
    u"AC-SSMP3/R2017 AC-SSMZ5 place \u6d3b\u6001\u5148\u4f8b\u00b7retract \u8bfb\u9762="
    u"R2015 AC-SSM4 straddle \u5728\u518c\u00b7AC \u524d\u7f00\u8ba4\u9886\u65f6 git "
    u"grep \u96f6\u5360\u7528\u518d\u9a8c\u3015\u2014\u2014\u79cd\u5b50=test_showcase_"
    u"statsmonthboundarypersist.py R2017 \u5728\u518c\u00b7R2017 \u6536\u8d26\u8865"
    u"\u79cd\uff09"
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    # ---------- 1. state.json byte surgery ----------------------
    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2016,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2016,', '"tick": 2017,')
    tail = '"\r\n  ]\r\n}\r\n'
    if not text.endswith(tail):
        die("state tail layout unexpected")
    import logs_toolkit as LT                     # noqa: E402
    lit1 = " " * 16 + LT.ps_escape(ROUND_LINE)
    lit2 = " " * 16 + LT.ps_escape(TOKENS_LINE)
    text = (text[:-len(tail)] + '",\r\n' + lit1 + ',\r\n' + lit2
            + '\r\n  ]\r\n}\r\n')
    new_bytes = text.encode("utf-8")
    if len(new_bytes) >= 78500:
        die("state over the line: %d" % len(new_bytes))
    st = json.loads(text)
    if st["tick"] != 2017 or len(st["log"]) != 19:
        die("tick/log shape wrong: %s %d" % (st["tick"],
                                             len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-17 R2017"):
        die("round line missing")
    if not st["log"][-1].startswith("R2017 tokens:"):
        die("tokens line missing")
    if st["log"][-3].find(u"fold R547") < 0:
        die("fold rolling line missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2017 log-items=19 bytes=%d"
          % len(new_bytes))

    # ---------- 2. heartbeat.txt -------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2017 line appended")

    # ---------- 3. state/queue/explore.md ----------------------
    q = io.open(P_QUEUE, encoding="utf-8", newline="").read()
    if q.count(QUEUE_FLIP_OLD) != 1:
        die("queue claim line not unique")
    q = q.replace(QUEUE_FLIP_OLD, QUEUE_FLIP_OLD.replace(
        "- [ ]", "- [x]"), 1)
    if q.count(QUEUE_END_ANCHOR) != 1:
        die("queue end anchor not unique")
    q = q.replace(
        QUEUE_END_ANCHOR,
        QUEUE_END_ANCHOR + QUEUE_DONE_NOTE + "\r\n" + QUEUE_RESEED,
        1)
    io.open(P_QUEUE, "w", encoding="utf-8", newline="").write(q)
    print("queue OK: done-flip + done note + reseed line")

    # ---------- 4. status-export.json --------------------------
    import check_export_consistency as cec          # noqa: E402
    derived, _state, _exp, pat = cec.recompute()
    exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
    exp["export_ts"] = now.astimezone().isoformat(timespec="seconds")
    exp["ceo_face"] = {
        "current": CEO_CURRENT,
        "latest_artifact": CEO_LATEST,
        "next_milestone": CEO_NEXT,
    }
    results = exp["results"]
    label = pat["tick_row_label"]
    tick_row = ["2017", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2017", RESULTS_ROW]]
                   + rrows[:38] + [tick_row])
    exp["results"] = new_results
    sd = dict(derived)
    sd["method"] = ("machine-derived from state.json log per "
                    "BD-PROP-001 caliber (check_export_consistency"
                    ".recompute)")
    exp["self_drive"] = sd
    io.open(P_EXPORT, "w", encoding="utf-8", newline="").write(
        json.dumps(exp, ensure_ascii=False, indent=2) + "\n")
    print("status-export.json OK: results=%d self_drive window=%s"
          % (len(new_results), sd.get("window")))
    print("R2017 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
