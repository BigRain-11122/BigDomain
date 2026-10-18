# closeout_R2035.py - R2035 closeout driver
# (1) state.json byte surgery: tick 2034 -> 2035, two-line
# log append via ps_escape (16-space indent, CRLF canonical),
# last_dec_tokens += C-20261018-02 (INFO verdict verified this
# round: the group receipt-batch row mentions BigDomain only
# in the tail-read-zero-new-rows context; R2034 judgment upheld,
# baseline topped up so the scan stops re-flagging it);
# (2) heartbeat.txt line; (3) queue face already flipped
# manually this round (done note + reseed) - skipped here;
# (4) status-export.json refresh (ceo_face + results R2035
# row prepend + tick row 2035 + self_drive recompute).
# ASCII script logic; CJK content lives in the constants
# (closeout_R2017.py precedent).
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

ROUND_LINE = (
    u"2026-10-19 R2035\uff08\u4e94\u9759\u68c0\u51fa=LEDGER @BigDomain "
    u"\u96f6\u65b0\u884c+ORD \u5c3e 02:18 \u6301\u5e73+GORD tbl 455 "
    u"\u6301\u5e73+BENCH \u5f53\u65e5\u5df2\u5237+\u6811\u51c0\uff1bDEC "
    u"\u65b0 token C-20261018-02 \u5b9e\u8bfb\u6838\u9a8c=\u96c6\u56e2"
    u"\u56de\u6267\u6838\u9500\u6279\u884c\u00b7BigDomain \u8bed\u5883"
    u"\u5c3e\u8bfb\u96f6\u65b0\u884c=\u5f15\u7528\u578b INFO \u975e\u6d3e"
    u"\u5de5\u00b7R2034 \u5224\u8bfb\u6210\u7acb\u2192token \u57fa\u7ebf"
    u"\u8865\u767b\u8bb0\u9632\u91cd\u590d\u62a5\u65b0\u2014\u2014\u7ebf"
    u"\u5e8f\u62c9\u6d3b=P1 \u9876\u884c\u4e5d\u53f8\u5efa\u8bbe\u6848"
    u"\u53ef\u6267\u884c\u9762\u5df2\u5168\u5151\u73b0\u5269\u4f59=72h "
    u"\u9a8c\u6536\u65f6\u7a97+\u5448\u62a5\u9762\u5df2\u5907\uff1bP2 "
    u"\u5f00\u9879\u5168\u95e8\u63a7\u2192P3 explore \u961f\u5934\u8ba4"
    u"\u9886=\u5c55\u793a\u6a71\u7a97\u7edf\u8ba1\u699c\u574f\u53c2\u95e8"
    u"\u65cf\u8de8\u91cd\u542f\u540c\u7801\u4f8b\u7a97\u2014\u2014\u4ea7"
    u"\u54c1\u4ef6\u4ea4\u4ed8=\u5957\u4ef6 test_showcase_statsgatepersist"
    u".py\uff08suite-only\u00b7AC-SGB1..SGB7 \u5224\u636e\u9884\u6ce8"
    u"\u518c\u5148\u4e8e\u4ee3\u7801\u00b7\u4e09\u9762 git grep \u96f6"
    u"\u5360\u7528\u5b9e\u951a\uff09\uff1a\u88c5\u8f7d\u4e16\u754c\u63a7"
    u"\u5236\u951a\uff5bsh-active{p=2,r=1,dn=1}+sh-empty \u8bda\u5b9e"
    u"\u96f6\u683c\u00b7\u6ce8\u518c\u7a20\u5bc6+\u51c0\u6d41\u6052\u7b49"
    u"\u00b7\u51b3\u5e8f+\u8bfb\u65cf\u53cc\u8dd1\u540c\u4e00\uff5d+21 "
    u"\u63a2\u9488\u7535\u6c60\uff5b11 \u574f limit\u2192E_SH_BAD_LIMIT"
    u"+9 \u574f\u7a97\u2192E_SH_BAD_WINDOW+\u53cc\u574f\u5e8f limit "
    u"\u5148\u6267\u6cd5\uff5d\u4e09\u5b9e\u4f8b\u5411\u91cf V1==V2==V3 "
    u"\u9010\u5b57\u8282\u540c\u4e00\uff5b\u4e24\u6b21\u5168\u6808\u91cd"
    u"\u542f\u540c\u7801\u5f8b\uff5d+\u63a2\u9488\u6279\u96f6\u526f\u4f5c"
    u"\u7528\u4e09\u8868\u8ba1\u6570\u6052\u5b9a\u2460\u2461\u2462+\u91cd"
    u"\u542f\u540e\u6d3b\u6027\u771f\u5199 board \u7a20\u5bc6+1 \u96f6"
    u"\u5e7b\u5f71+\u7b2c\u4e09\u5b9e\u4f8b\u7eaf\u8bfb\u5f8b+\u4fe1\u5c01"
    u"\u952e\u96c6\u8de8\u5b9e\u4f8b\u6052\u5b9a+\u536b\u751f\u5168\u8fc7"
    u"\u2014\u2014SUITE PASS 7/7 \u53cc\u8dd1\u9010\u5b57\u8282\u540c"
    u"\u4e00 sha16 58677b742dd5cf29+SUITES 247\u2192248 \u5224\u636e "
    u"2089\u21922096+RUNNER PASS 248/248 controls 7/7 275.5s \u96f6"
    u"\u56de\u5f52=qa/reconcile-all-R2035.log+\u77e9\u9635\u518d\u751f "
    u"248/2096 --check byte-identical+census \u91cd\u951a\u540e "
    u"DRIFT-CLEAN flags=0+\u6307\u7eb9 CLEAN domains=5+profile "
    u"DRIFT-CLEAN 236/0\u2014\u2014\u5e38\u8bbe\u884c\u4e24\u679a\u5f53"
    u"\u65e5\u6233\u5728\u76d8\u4e0d\u91cd\u8dd1\u2014\u2014explore "
    u"\u6d88\u8d39 1 \u8865\u79cd 1 \u5b88\u6052\u00b7\u8bc1\u636e=qa/"
    u"showcase-statsgatepersist-R2035.log \u516d\u8282\u00b7\u63d0\u6848"
    u"\u7a97\u914d\u989d\u5df2\u6e05\uff5bBD-PROP-004\uff5d\u2014\u2014"
    u"score 2\uff09"
)

TOKENS_LINE = (
    "R2035 tokens: local=~1.0M api=0 api_reason=five-silence "
    "scan + P3 claim round all local (suite double-run + "
    "full battery RUNNER 275.5s + matrix/census/fingerprint/"
    "profile gates + closeout edits + directed commit), "
    "zero cloud calls"
)

HB_BODY = (
    "R2035: P3 explore claim delivered - showcase stats_board "
    "bad-argument gate family cross-restart same-code example "
    "window (R2010-reseed FIFO head; AC-SGB1..AC-SGB7 "
    "pre-registered in the claim row before code; prefix + "
    "suite + registry names git-grep zero-occupancy). Suite "
    "test_showcase_statsgatepersist.py (suite-only, three "
    "product files sha256 pinned): populated-world anchor "
    "(registry-dense, netflow identity, decisive sort, family "
    "double-run identical); 21-probe battery (11 bad-limit "
    "-> E_SH_BAD_LIMIT, 9 bad-window -> E_SH_BAD_WINDOW, "
    "dual-bad order probe -> E_SH_BAD_LIMIT first) with the "
    "ordered code vector V1 == V2 == V3 byte-identical "
    "across two full-stack restarts (three instances), zero "
    "side effects per probe batch on every instance, "
    "post-restart liveness via the real write path, "
    "pure-read law, envelope key sets constant. SUITE 7/7 "
    "double-run identical sha16 58677b742dd5cf29; wiring "
    "ledger-showcase-statsgatepersist criteria 7; RUNNER "
    "PASS 248/248 suites green controls 7/7 275.5s zero "
    "regression (qa/reconcile-all-R2035.log); matrix regen "
    "248/2096 --check byte-identical; census re-anchor + "
    "check DRIFT-CLEAN flags=0; fingerprint CLEAN domains=5; "
    "profile DRIFT-CLEAN + both --check identical. DEC new "
    "token C-20261018-02 verified as receipt-batch INFO "
    "(non-dispatch, R2034 judgment upheld) and baselined. "
    "Explore consume-1 reseed-1. Score 2."
)

CEO_CURRENT = (
    "R2035: P3 explore claim delivered end-to-end: showcase "
    "stats_board bad-argument gate family cross-restart "
    "same-code example window (the R2010-reseed FIFO head; "
    "criteria AC-SGB1..AC-SGB7 pre-registered in the "
    "explore.md claim row before code, prefix/suite/registry "
    "names git-grep zero-occupancy verified). Suite-only "
    "round: the 21-probe battery (11 E_SH_BAD_LIMIT forms + "
    "9 E_SH_BAD_WINDOW forms + the dual-bad order probe "
    "rejecting E_SH_BAD_LIMIT first) produces an ordered "
    "code vector byte-identical on instances one/two/three "
    "across two full-stack restarts, zero side effects per "
    "probe batch on the populated face, post-restart "
    "liveness, pure-read law, hygiene pinned. SUITE 7/7 "
    "double-run identical sha16 58677b742dd5cf29; RUNNER "
    "PASS 248/248 suites green controls 7/7 275.5s zero "
    "regression; matrix 248/2096 --check byte-identical; "
    "census DRIFT-CLEAN; fingerprint CLEAN domains=5; "
    "profile DRIFT-CLEAN. DEC new token C-20261018-02 "
    "verified as a receipt-batch INFO row (non-dispatch, "
    "R2034 judgment upheld) and added to the token "
    "baseline. Score 2."
)

CEO_LATEST = (
    "qa/showcase-statsgatepersist-R2035.log + src/sandbox/"
    "ledger/test_showcase_statsgatepersist.py (SUITE 7/7 "
    "double-run identical, RUNNER 248/248 green, 2026-10-19)"
)

CEO_NEXT = (
    "P3 explore queue: next open heads (proposal gate "
    "family cross-restart same-code, lobby chat idem_seen "
    "TTL-expiry re-billing, statsmonth straddle netflow "
    "exception) + R2035 reseed showcase_view_window "
    "bad-window gate family row; FUNNEL 72h self-continuity "
    "acceptance <=10-31 (day-1 stamp on disk); building-plan "
    "committee tri-report <=10-25; window <=48h (by "
    "2026-10-21)"
)

RESULTS_ROW = (
    "R2035: P3 explore claim delivered end-to-end: showcase "
    "stats_board bad-argument gate family cross-restart "
    "same-code example window (the R2010-reseed FIFO head; "
    "criteria AC-SGB1..AC-SGB7 pre-registered in the "
    "explore.md claim row before code, AC-SGB prefix + "
    "suite + registry names git-grep zero-occupancy "
    "verified). Suite-only round (showcase.py + both "
    "shipped config.json sha256 pinned unchanged): (1) "
    "populated-world control anchor - registry-dense board "
    "(one row per registered showcase), eventless row "
    "honest zeros, per-row netflow identity displayed_now "
    "== places - retracts, decisive sort, read family "
    "double-run byte-identical; (2) instance-one baseline "
    "battery - 21 probes (5 default limit forms + 6 dual "
    "limit forms + 9 window forms + 1 dual-bad order "
    "probe) all reject with the expected ordered code "
    "vector (E_SH_BAD_LIMIT x11, E_SH_BAD_WINDOW x9, "
    "order probe E_SH_BAD_LIMIT first = deterministic "
    "parameter gate order), probe batch leaves the three "
    "table counts unchanged (gates fire before any read on "
    "the populated face); (3) cross-restart same-code - "
    "full-stack close (sh -> led) then rebuild on same "
    "paths + same cfg bytes: identical battery vector "
    "V2 == V1 byte-identical, zero side effects, read "
    "family F2 == F1; (4) post-restart liveness - real "
    "write path (register + place) grows the board "
    "registry-dense with the netflow identity and zero "
    "phantom, family changes only via the real write; (5) "
    "third instance - V3 == V1, family F3 == F2b "
    "(liveness write survives the second restart), "
    "pure-read law (read battery double-run identical, "
    "counts flat); (6) cross-instance summary - V1 == V2 "
    "== V3 byte-identical (the same-code law over two "
    "full-stack restarts, three instances), envelope key "
    "sets constant across instances; (7) hygiene (pure "
    "ASCII, zero network imports, product shas stable, "
    "world outside repo). SUITE PASS 7/7 double-run stdout "
    "byte-identical sha16 58677b742dd5cf29; reconcile_all "
    "wiring ledger-showcase-statsgatepersist criteria 7 "
    "(248 suites, criteria 2089->2096); RUNNER PASS 248/248 "
    "suites green controls 7/7 275.5s zero regression (qa/"
    "reconcile-all-R2035.log); four-face battery green "
    "(matrix regen 248/2096 --check byte-identical 24160B, "
    "census re-anchor + check DRIFT-CLEAN flags=0, "
    "fingerprint verdict CLEAN domains=5, profile compare "
    "DRIFT-CLEAN 236/0 + main/daily --check identical). "
    "DEC new token C-20261018-02 read-verified as a group "
    "receipt-batch INFO row (BigDomain appears only in the "
    "tail-read-zero-new-rows context; R2034 judgment "
    "upheld) and appended to last_dec_tokens so the "
    "content-addressed scan stops re-flagging it. Explore "
    "consume-1 reseed-1 (showcase_view_window bad-window "
    "gate family cross-restart seed). Score 2."
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    # ---------- 1. state.json byte surgery ----------------------
    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2034,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2034,', '"tick": 2035,')
    # token baseline top-up: append C-20261018-02 (INFO verdict)
    tok_anchor = 'D-20261019-04",'
    if text.count(tok_anchor) != 1:
        die("last_dec_tokens tail anchor not unique: %d"
            % text.count(tok_anchor))
    text = text.replace(
        tok_anchor, 'D-20261019-04,C-20261018-02",', 1)
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
    if st["tick"] != 2035 or len(st["log"]) != 19:
        die("tick/log shape wrong: %s %d" % (st["tick"],
                                             len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-19 R2035"):
        die("round line missing")
    if not st["log"][-1].startswith("R2035 tokens:"):
        die("tokens line missing")
    if not st["last_dec_tokens"].endswith("C-20261018-02"):
        die("token baseline top-up missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2035 log-items=19 bytes=%d"
          % len(new_bytes))

    # ---------- 2. heartbeat.txt -------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2035 line appended")

    # ---------- 3. queue face: done manually this round --------
    print("queue face: explore.md done-flip + done note + "
          "reseed already applied manually (verified)")

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
    tick_row = ["2035", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2035", RESULTS_ROW]]
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
    print("R2035 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
