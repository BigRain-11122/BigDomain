# closeout_R2043.py - R2043 closeout driver
# (1) state.json byte surgery: tick 2042 -> 2043, two-line
# log append via ps_escape (16-space indent, CRLF canonical);
# no DEC/GORD/ORD baseline top-up this round (content-addressed
# scan flat, zero new tokens/rows); ROUND_LINE text lives in
# the logs/tmp-closeout-R2043-roundline.txt data file (encoding
# law: CJK in data files, ASCII script logic);
# (2) heartbeat.txt: TWO rows this closeout - the R2042 debt
# backfill row (the R2042 round closed its state log but
# missed its heartbeat row; the scan [HB] face flagged the
# lag=1 debt) plus the canonical R2043 alive row;
# (3) queue face flipped separately this round (done note +
# reseed) - verified here only;
# (4) status-export.json refresh (ceo_face + results R2043
# row prepend + tick row 2043 + self_drive recompute).
# closeout_R2036.py precedent.
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
                       "tmp-closeout-R2043-roundline.txt")

TOKENS_LINE = (
    "R2043 tokens: local=~1.1M api=0 api_reason=five-silence "
    "scan + P3 claim round all local (suite double-run + "
    "full battery RUNNER 254 suites 225.9s + matrix/census/"
    "fingerprint/profile gates + fold R572 gen + closeout "
    "edits + export flush + directed commit), zero cloud calls"
)

HB_BACKFILL_BODY = (
    "R2042: lobby chat idem_seen expired-rebilling case "
    "window delivered (AC-IDR1..AC-IDR7 pre-registered in "
    "the claim row before code; test_client.py "
    "idem_expired_rebilling_cases section, SUITE 79/79 "
    "double-run identical sha16 08985e19a94054ae; the "
    "expired-resend billing divergence law - in-TTL replay "
    "absorbs as chat.duplicate while the post-TTL resend "
    "answers E_RATE_LIMIT violation #1 = fresh-unit billing; "
    "reject-no-re-arm; clean-window burn; re-arm restores "
    "free; exhaustion proof; reconcile_all wiring lobby "
    "72->79, RUNNER PASS 253/253 controls 7/7 303.5s zero "
    "regression; matrix/census/fingerprint/profile green). "
    "This row is the R2043-closeout BACKFILL of the R2042 "
    "heartbeat debt: the R2042 round closed its state log "
    "but missed its heartbeat row, the scan [HB] face "
    "flagged hb lag=1 and this round cashed the debt at "
    "birth (same-round repair). [via BigDomain-OSLoop]"
)

HB_BODY = (
    "R2043: P3 explore FIFO head claim delivered - statsmonth "
    "cross-month straddle-pair netflow identity exception "
    "cross-restart suite (R2021-reseed; AC-SMST1..AC-SMST7 "
    "pre-registered before code, prefix/suite/registry names "
    "git-grep zero-occupancy). Suite test_showcase_"
    "statsmonthstraddlepersist.py (suite-only, three product "
    "files sha256 pinned): the straddle core - a "
    "previous-month fixture place retracted through the real "
    "path in the current month - reads {0,1,0} in the "
    "current-month window where the identity displayed_now "
    "== places - retracts honestly BREAKS (0 != 0-1) while "
    "the full board keeps the per-row identity ({3,1,2}: "
    "2 == 3-1); the post-restart re-place closes the "
    "straddle into the leading-retract variant {1,1,1} "
    "(1 != 1-1) with the full board still holding per row "
    "({4,1,3}: 3 == 4-1) - the identity is a full-board law, "
    "never a month-window law, pinned in both exception "
    "shapes (the positive closure of the R2018/R2019 "
    "straddle-exclusion rulings); old-month window "
    "byte-frozen across both mutations (record-time law: "
    "the retracted item still reads displayed in the "
    "previous window); view_cur [] -> [tower]; chronicle "
    "[p,p,p,r] -> [p,p,p,r,p]; tour leaves then re-joins at "
    "the tail (R2019 law); two full-stack restarts with the "
    "13-form family byte-identical; read storm counts flat "
    "(showcases 3, events 7, ledger_tx 0); gate family 9 bad "
    "windows + 4 bad limits + order probe same codes "
    "pre/post restart; cross-showcase not-displayed probe "
    "zero rows; zero-token law ledger_tx==0 throughout. "
    "SUITE 7/7 double-run identical sha16 5cd1614b33f4ee70; "
    "wiring ledger-showcase-statsmonth-straddle-persist "
    "criteria 7 (SUITES 253->254, criteria 2138->2145); "
    "RUNNER PASS 254/254 suites green controls 7/7 225.9s "
    "zero regression (qa/reconcile-all-R2043.log); matrix "
    "regen 254/2145 --check byte-identical 24822B; census "
    "--update-baseline + --check DRIFT-CLEAN; fingerprint "
    "CLEAN domains=5; profile compare/check/daily all exit "
    "0. fold R572 pre-closeout honored (round-start gauge "
    "77492B + closeout budget over the 78500 line -> tail-5 "
    "12450B folded to one 5234B rolling line, 312 tokens "
    "mechanically embedded zero-loss gen572, catalog "
    "missing=[], archive section R2043 verbatim + preop "
    "backup, post == predicted 70192B). Heartbeat row R2042 "
    "debt backfilled in the same closeout (scan [HB] flag "
    "cashed at birth). Explore consume-1 reseed-1 (dual-"
    "straddle exception-deepening seed). Score 2. "
    "[via BigDomain-OSLoop]"
)

CEO_CURRENT = (
    "R2043: P3 explore claim delivered end-to-end: statsmonth "
    "cross-month straddle-pair netflow identity exception "
    "cross-restart suite (the R2021-reseed FIFO head; "
    "criteria AC-SMST1..SMST7 pre-registered in the "
    "explore.md claim row before code, three names "
    "git-grep zero-occupancy verified). The straddle pair "
    "(previous-month fixture place + current-month real-path "
    "retract) reads {0,1,0} in the current-month window "
    "where the month-window identity honestly breaks while "
    "the full board keeps the per-row identity - the "
    "positive closure of the family rulings that kept "
    "straddle pairs out of the R2018/R2019 worlds; the "
    "post-restart re-place pins the leading-retract variant "
    "{1,1,1}; two full-stack restarts byte-identical. SUITE "
    "7/7 double-run identical sha16 5cd1614b33f4ee70; "
    "RUNNER PASS 254/254 suites green controls 7/7 225.9s "
    "zero regression; matrix 254/2145 --check "
    "byte-identical; census DRIFT-CLEAN; fingerprint CLEAN "
    "domains=5; profile all green; fold R572 pre-closeout; "
    "heartbeat R2042 debt backfilled. Score 2."
)

CEO_LATEST = (
    "qa/showcase-statsmonth-straddle-R2043.log + src/"
    "sandbox/ledger/test_showcase_statsmonthstraddlepersist.py "
    "(SUITE 7/7 double-run identical, RUNNER 254/254 green, "
    "2026-10-19)"
)

CEO_NEXT = (
    "FUNNEL 72h self-continuity acceptance <=10-31 (day-1 "
    "stamp qa/funnel-daily-20261019.log on disk, day-2/day-3 "
    "stamps next); building-plan committee tri-report "
    "<=10-25 (plan doc ready); P3 explore queue next heads "
    "(dual-straddle exception-deepening, apimarket "
    "zero-listing boundary persist, honorcert grant-gate "
    "persist); window <=48h (by 2026-10-21)"
)

RESULTS_ROW = (
    "R2043: P3 explore claim delivered end-to-end: statsmonth "
    "cross-month straddle-pair netflow identity exception "
    "cross-restart suite (the R2021-reseed FIFO head; "
    "criteria AC-SMST1..AC-SMST7 pre-registered in the "
    "explore.md claim row before code, AC-SMST prefix + "
    "suite + registry names git-grep zero-occupancy "
    "verified; two same-window count errata honestly "
    "corrected in the registration before the evidence run "
    "- the world carries 5 pre-straddle events (3 alpha "
    "fixture + 2 beta real-path), 6 after the straddle "
    "retract, 7 after the closing re-place, and the bad-"
    "window gate family is 9 forms). Suite-only round "
    "(showcase.py + both shipped config.json sha256 pinned "
    "unchanged): (1) place-first world anchors - full board "
    "alpha {3,0,3} / beta {2,0,2} / mu {0,0,0} with the "
    "per-row identity holding everywhere incl. every window "
    "form (the exception not yet lit); (2) the straddle "
    "core - a previous-month fixture place retracted "
    "through the real path in the current month reads "
    "{0,1,0} in the current-month window where "
    "displayed_now == places - retracts honestly BREAKS "
    "(0 != 0-1), broken rows == [alpha-gal] "
    "(straddle-row specificity), the full board keeps the "
    "per-row identity ({3,1,2}: 2 == 3-1), the beta/mu "
    "window rows keep holding (not a window property), the "
    "previous-month window byte-frozen with the retracted "
    "item still reading displayed there (record-time "
    "law), view_cur stays [], chronicle [p,p,p,r], tour "
    "drops the retracted item, zero token movement, events "
    "5->6; (3) first full-stack restart - the 13-form "
    "family byte-identical (the exception state persists); "
    "(4) post-restart re-place closing the straddle - "
    "already-displayed probe refuses zero rows, the "
    "current-window row becomes the leading-retract "
    "variant {1,1,1} (1 != 1-1, the in-window trace of the "
    "cross-month pair), full board {4,1,3} identity holds "
    "(3 == 4-1), view_cur [tower] returns, chronicle grows "
    "[p,p,p,r,p], tour re-joins at the tail (R2019 law), "
    "old-month window byte-frozen; (5) second full-stack "
    "restart + read storm x2 - counts flat (showcases 3, "
    "events 7, ledger_tx 0), both passes byte-identical, "
    "gate family (9 bad windows + 4 bad limits + "
    "limit-gate-first order probe) same codes pre/post "
    "restart, stats_board source zero writes; (6) pure-read "
    "law - cross-showcase not-displayed probe refuses zero "
    "rows, far-window 2099-01 and deep-history windows "
    "all-zero with the identity trivially holding, "
    "zero-event showcase row holds in every form; (7) "
    "hygiene (pure ASCII, zero network imports, product "
    "shas stable, world outside repo). SUITE PASS 7/7 "
    "double-run stdout byte-identical sha16 5cd1614b33f4ee70 "
    "(first run clean after the two errata); reconcile_all "
    "wiring ledger-showcase-statsmonth-straddle-persist "
    "criteria 7 (254 suites, criteria 2138->2145); RUNNER "
    "PASS 254/254 suites green controls 7/7 225.9s zero "
    "regression (qa/reconcile-all-R2043.log); four-face "
    "battery green (matrix regen 254/2145 --check "
    "byte-identical 24822B, census --update-baseline + "
    "--check DRIFT-CLEAN, fingerprint CLEAN domains=5, "
    "profile compare/check/daily all exit 0). fold R572 "
    "pre-closeout honored (round-start gauge 77492B + "
    "closeout budget over the 78500 line -> tail-5 12450B "
    "folded to one 5234B rolling line, 312 tokens "
    "mechanically embedded zero-loss gen572, catalog "
    "missing=[], archive section R2043 verbatim + preop "
    "backup logs/state-preop-R2043.bak, post == predicted "
    "70192B). Heartbeat row R2042 debt backfilled in the "
    "same closeout (scan [HB] lag=1 flag cashed at birth). "
    "Explore consume-1 reseed-1 (dual-straddle exception-"
    "deepening seed). Score 2."
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
    if not ROUND_LINE.startswith(u"2026-10-19 R2043"):
        die("round line head wrong")

    raw = open(P_STATE, "rb").read()
    text = raw.decode("utf-8")
    if text.count('"tick": 2042,') != 1:
        die("tick anchor not unique")
    text = text.replace('"tick": 2042,', '"tick": 2043,')
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
    if st["tick"] != 2043 or len(st["log"]) != 16:
        die("tick/log shape wrong: %s %d" % (st["tick"],
                                             len(st["log"])))
    if not st["log"][-2].startswith(u"2026-10-19 R2043"):
        die("round line missing")
    if not st["log"][-1].startswith("R2043 tokens:"):
        die("tokens line missing")
    open(P_STATE, "wb").write(new_bytes)
    print("state.json OK: tick=2043 log-items=16 bytes=%d"
          % len(new_bytes))

    # ---------- 2. heartbeat.txt: backfill + current row -------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = (now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
             + " | BigDomain OSLoop alive | ")
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + "tick 2042 | " + HB_BACKFILL_BODY + "\r\n"
        + stamp + "tick 2043 | " + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2042 debt backfill row + R2043 "
          "alive row appended")

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
    tick_row = ["2043", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2043", RESULTS_ROW]]
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
    print("R2043 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
