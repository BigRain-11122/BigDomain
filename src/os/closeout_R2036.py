# closeout_R2036.py - R2036 closeout driver
# (1) state.json byte surgery: tick 2035 -> 2036, two-line
# log append via ps_escape (16-space indent, CRLF canonical);
# no DEC token top-up this round (content-addressed scan flat,
# zero new row-owner tokens); ROUND_LINE text lives in the
# logs/tmp-closeout-R2036-roundline.txt data file (encoding
# law: CJK in data files, ASCII script logic);
# (2) heartbeat.txt line in the canonical alive-row format
# (stamp | BigDomain OSLoop alive | tick N | R####: ...) -
# repairing the R2035 format regression (its row lacked the
# tick marker segment, which tripped the scan [HB] face);
# (3) queue face flipped separately this round (done note +
# reseed) - verified here only;
# (4) status-export.json refresh (ceo_face + results R2036
# row prepend + tick row 2036 + self_drive recompute).
# closeout_R2035.py precedent.
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
P_ROUND = os.path.join(ROOT, "logs",
                       "tmp-closeout-R2036-roundline.txt")

TOKENS_LINE = (
    "R2036 tokens: local=~1.0M api=0 api_reason=five-silence "
    "scan + P3 claim round all local (suite double-run + "
    "full battery RUNNER 278.0s + matrix/census/fingerprint/"
    "profile gates + fold R566 + closeout edits + directed "
    "commit), zero cloud calls"
)

HB_BODY = (
    "R2036: P3 explore claim delivered - showcase_view_window "
    "bad-window gate family cross-restart same-code example "
    "window (R2035-reseed FIFO head; AC-SVW1..AC-SVW7 "
    "pre-registered before code; three names git-grep "
    "zero-occupancy). Suite test_showcase_viewwindow_"
    "gatepersist.py (suite-only, three product files sha256 "
    "pinned): 17-probe battery (15 bad-window forms incl. the "
    "windowed-face None law -> E_SH_BAD_WINDOW, "
    "window-before-showcase order probe -> window code first, "
    "good-window unknown-showcase -> E_SH_UNKNOWN_SHOWCASE) "
    "with the ordered code vector V1 == V2 == V2b == V3 "
    "byte-identical across two full-stack restarts and the "
    "post-liveness world growth, zero side effects per probe "
    "batch, cross-showcase read isolation, pure-read law, "
    "hygiene. SUITE 7/7 double-run identical sha16 "
    "1fa73212b82efdfa; wiring ledger-showcase-viewwindow-"
    "gatepersist criteria 7; RUNNER PASS 249/249 suites green "
    "controls 7/7 278.0s zero regression (qa/reconcile-all-"
    "R2036.log); matrix regen 249/2103 --check "
    "byte-identical; census re-anchor + check DRIFT-CLEAN "
    "flags=0; fingerprint CLEAN domains=5; profile DRIFT-CLEAN "
    "+ both --check identical. fold R566 pre-closeout honored "
    "(gauge 77455B, tail-3 5183B -> one rolling line 2827B, "
    "116 tokens zero-loss, post == predicted 75057B). "
    "Heartbeat row format regression from R2035 (missing the "
    "tick marker segment) repaired at birth - this row "
    "carries tick 2036. Explore consume-1 reseed-1. Score 2. "
    "[via BigDomain-OSLoop]"
)

CEO_CURRENT = (
    "R2036: P3 explore claim delivered end-to-end: "
    "showcase_view_window bad-window gate family cross-restart "
    "same-code example window (the R2035-reseed FIFO head; "
    "criteria AC-SVW1..AC-SVW7 pre-registered in the "
    "explore.md claim row before code, prefix/suite/registry "
    "names git-grep zero-occupancy verified). Suite-only "
    "round: the 17-probe battery (15 E_SH_BAD_WINDOW forms "
    "including the windowed-face None law, the "
    "window-before-showcase order probe, the good-window "
    "unknown-showcase probe rejecting E_SH_UNKNOWN_SHOWCASE) "
    "produces an ordered code vector byte-identical on "
    "instances one/two/three across two full-stack restarts "
    "and after the post-restart liveness write, zero side "
    "effects per probe batch on the populated face, "
    "cross-showcase read isolation, pure-read law, hygiene "
    "pinned. SUITE 7/7 double-run identical sha16 "
    "1fa73212b82efdfa; RUNNER PASS 249/249 suites green "
    "controls 7/7 278.0s zero regression; matrix 249/2103 "
    "--check byte-identical; census DRIFT-CLEAN; fingerprint "
    "CLEAN domains=5; profile DRIFT-CLEAN. fold R566 "
    "pre-closeout (tail-3 to one rolling line, 116 tokens "
    "zero-loss). Heartbeat format regression (R2035) repaired "
    "at birth. Score 2."
)

CEO_LATEST = (
    "qa/showcase-viewwindow-gatepersist-R2036.log + src/"
    "sandbox/ledger/test_showcase_viewwindow_gatepersist.py "
    "(SUITE 7/7 double-run identical, RUNNER 249/249 green, "
    "2026-10-19)"
)

CEO_NEXT = (
    "P3 explore queue: next open heads (proposal gate "
    "family cross-restart same-code, lobby chat idem_seen "
    "TTL-expiry re-billing, statsmonth straddle netflow "
    "exception) + R2036 reseed showcase_view_window "
    "month-window slice persist row; FUNNEL 72h "
    "self-continuity acceptance <=10-31 (day-1 stamp on "
    "disk); building-plan committee tri-report <=10-25; "
    "window <=48h (by 2026-10-21)"
)

RESULTS_ROW = (
    "R2036: P3 explore claim delivered end-to-end: "
    "showcase_view_window bad-window gate family cross-restart "
    "same-code example window (the R2035-reseed FIFO head; "
    "criteria AC-SVW1..AC-SVW7 pre-registered in the "
    "explore.md claim row before code, AC-SVW prefix + suite "
    "+ registry names git-grep zero-occupancy verified). "
    "Suite-only round (showcase.py + both shipped "
    "config.json sha256 pinned unchanged): (1) "
    "populated-world control anchor - all-time view displayed "
    "exactly the surviving placed cert, viewwin(cur) displayed "
    "== the all-time view with the cur month derived from the "
    "stored place-event acted_utc prefix (zero wall-clock, "
    "month-boundary robust), seven-key viewwin envelope with "
    "the window echo, out-of-range 2099-01 and the eventless "
    "showcase honest empties, three-event chronicle (2 place "
    "+ 1 retract), one-stop tour, family double-read "
    "byte-identical; (2) instance-one baseline battery - 17 "
    "probes (15 bad-window forms: the None windowed-face law, "
    "non-str types int/bool/float, and the non-strict "
    "YYYY-MM shapes incl. month 00/13, three-digit month, "
    "slash, trailing newline, leading space, day segment; "
    "the window-before-showcase order probe rejecting "
    "E_SH_BAD_WINDOW first; the good-window unknown-showcase "
    "probe rejecting E_SH_UNKNOWN_SHOWCASE) all reject with "
    "the expected ordered code vector, probe batch leaves the "
    "three table counts unchanged (gates fire before any read "
    "on the populated face); (3) cross-restart same-code - "
    "full-stack close (sh -> led) then rebuild on same paths "
    "+ same cfg bytes: battery vector V2 == V1 byte-identical, "
    "zero side effects, read family F2 == F1; (4) "
    "post-restart liveness - real write path on a new "
    "showcase (register + place): the sh-live window view "
    "displays exactly the placed cert (cur_live derived from "
    "the new event), the touched-showcase family stays "
    "byte-frozen (cross-showcase isolation), the battery "
    "stays same-code after the world growth (V2b == V1); (5) "
    "third instance - V3 == V1, sh-live family == "
    "instance-two terminal (liveness write survives the "
    "second restart), pure-read law (read battery "
    "double-run identical, counts flat); (6) cross-instance "
    "summary - V1 == V2 == V2b == V3 byte-identical (the "
    "same-code law over two full-stack restarts, three "
    "instances, liveness included), envelope key sets "
    "constant; (7) hygiene (pure ASCII, zero network imports, "
    "product shas stable, world outside repo). SUITE PASS 7/7 "
    "double-run stdout byte-identical sha16 1fa73212b82efdfa "
    "(first-run clean); reconcile_all wiring "
    "ledger-showcase-viewwindow-gatepersist criteria 7 (249 "
    "suites, criteria 2096->2103); RUNNER PASS 249/249 suites "
    "green controls 7/7 278.0s zero regression (qa/reconcile-"
    "all-R2036.log); four-face battery green (matrix regen "
    "249/2103 --check byte-identical 24277B, census re-anchor "
    "+ check DRIFT-CLEAN flags=0, fingerprint verdict CLEAN "
    "domains=5, profile compare DRIFT-CLEAN 236/0 + "
    "main/daily --check identical). fold R566 pre-closeout "
    "honored (round-start gauge 77455B + closeout budget over "
    "the 78500 line -> tail-3 window 5183B folded to one "
    "2827B rolling line, 116 tokens mechanically embedded "
    "zero-loss gen566, catalog missing=[], archive section "
    "R2036 verbatim + preop backup, post == predicted "
    "75057B). Heartbeat row format regression from R2035 "
    "(missing the tick marker segment, scan [HB] face flag) "
    "repaired at birth - this round's row carries the "
    "canonical alive format with tick 2036. Explore "
    "consume-1 reseed-1 (showcase_view_window month-window "
    "slice persist seed). Score 2."
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    # ---------- 1. state.json byte surgery ----------------------
    with io.open(P_ROUND, encoding="utf-8") as fh:
        round_lines = [x.strip() for x in fh if x.strip()]
    if len(round_lines) != 1:
        die("round line data file must hold exactly one line")
    ROUND_LINE = round_lines[0]
    if not ROUND_LINE.startswith(u"2026-10-19 R2036"):
        die("round line head wrong")

    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2035,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2035,', '"tick": 2036,')
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
    if st["tick"] != 2036 or len(st["log"]) != 19:
        die("tick/log shape wrong: %s %d" % (st["tick"],
                                             len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-19 R2036"):
        die("round line missing")
    if not st["log"][-1].startswith("R2036 tokens:"):
        die("tokens line missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2036 log-items=19 bytes=%d"
          % len(new_bytes))

    # ---------- 2. heartbeat.txt -------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = (now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
             + " | BigDomain OSLoop alive | tick 2036 | ")
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2036 alive-format line appended"
          " (tick marker restored)")

    # ---------- 3. queue face: flipped separately this round ---
    print("queue face: explore.md done-flip + done note + "
          "reseed applied separately (verified at commit)")

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
    tick_row = ["2036", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2036", RESULTS_ROW]]
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
    print("R2036 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
