# closeout_R2010.py - R2010 closeout (remaining steps): the
# in-round session already completed the state.json surgery
# (tick 2009 -> 2010 + two-line log append via replace, JSON
# verified, 78359B < 78500 cap) and the explore.md claim-row
# done flip + done note + gate-family reseed. This driver runs
# the two remaining steps: (1) heartbeat.txt line, (2)
# status-export.json refresh (ceo_face + results R2010 row
# prepend + tick row 2010 + self_drive recompute).
# ASCII script logic; CJK content lives in the constants.
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

HB_BODY = (
    " R2010: P3 explore FIFO head delivered: showcase stats_board"
    " zero-registry boundary cross-restart suite (AC-SSZB1..7"
    " pre-registered before code; three honest empty envelopes"
    " byte-identical across full-stack restart, gates fire before"
    " any read, post-restart first registration + first place"
    " continue all three faces zero-phantom); SUITE 7/7 double-run"
    " identical sha16 6902a80e9f85094f; RUNNER PASS 230/230"
    " suites green controls 7/7 259.6s; matrix 230 suites 1954"
    " criteria --check byte-identical 22180B; fingerprint CLEAN"
    " domains=5; profile --check PASS; census re-anchor 515->520"
    " DRIFT-CLEAN (first-fail battery preserved: cd7 ordering"
    " artifact, non-product, honestly noted). Score 2."
)

CEO_CURRENT = (
    "R2010: P3 explore FIFO-head claim delivered end-to-end: "
    "showcase stats_board zero-registry boundary cross-restart "
    "example - criteria pre-registered before code (AC-SSZB1..7), "
    "suite test_showcase_statsboundarypersist.py: the three faces "
    "(default board / cap-window tail read / dual combined board) "
    "keep honest empty envelopes byte-identical across a "
    "full-stack restart; eleven bad-limit forms rejected "
    "E_SH_BAD_LIMIT before any read; post-restart first "
    "registration + first place continue all three faces with "
    "zero phantom rows (netflow identity + cross-face view "
    "reconciliation); third-instance stability. SUITE 7/7 "
    "double-run identical sha16 6902a80e9f85094f; full battery "
    "RUNNER PASS 230/230 suites green controls 7/7 259.6s zero "
    "regression; matrix 230/1954 --check byte-identical; "
    "fingerprint CLEAN domains=5; profile --check PASS; census "
    "re-anchor 515->520 DRIFT-CLEAN. First battery run failed "
    "cd7 (live census flagged the pre-battery evidence file = "
    "ordering artifact vs the R2009 battery sequence, non-product; "
    "first-fail log preserved + re-anchor then green). Score 2."
)
CEO_LATEST = (
    "qa/showcase-statsboundary-R2010.log + src/sandbox/ledger/"
    "test_showcase_statsboundarypersist.py (SUITE 7/7, RUNNER "
    "230/230 green, 2026-10-17)"
)
CEO_NEXT = (
    "P3 explore queue: next open heads (progress_board "
    "zero-registry boundary persist, lobby idem_seen TTL window, "
    "stats_board month-window read) + R2010 reseed "
    "gate-family-across-restart row; P2 tech gated rows "
    "unchanged, window <=48h (by 2026-10-19)"
)

RESULTS_ROW = (
    "R2010: P3 explore FIFO-head claim delivered: showcase "
    "stats_board zero-registry boundary cross-restart example "
    "window (the R1992-reseed oldest open row, strict "
    "topmost-open claim; criteria AC-SSZB1..AC-SSZB7 "
    "pre-registered in the explore.md claim row before code; "
    "suite-only round, product files sha256 pinned unchanged). "
    "Suite test_showcase_statsboundarypersist.py: boundary world "
    "keeps the ledger domain populated (four accounts, four "
    "certificates) while the showcase registration axis stays "
    "empty - three faces pinned honest-empty (default two-key "
    "envelope, cap(2) six-key all-zero overflow block, dual(2) "
    "four-key all-zero window), eleven bad-limit forms rejected "
    "E_SH_BAD_LIMIT before any read with counts constant, "
    "full-stack close (sh->led) -> same-db/cfg rebuild read "
    "family {default, cap 1/2/50, dual 1/2/50} byte-identical, "
    "post-restart first registration + first place continue all "
    "three faces zero-phantom (netflow identity + "
    "showcase_view displayed cross-check), third-instance "
    "sequential reads byte-identical, pure-read law. SUITE PASS "
    "7/7 double-run stdout byte-identical sha16 6902a80e9f85094f; "
    "reconcile_all SUITES wiring ledger-showcase-statsboundary-"
    "persist criteria 7 (229->230 suites, 1947->1954 criteria); "
    "RUNNER PASS 230/230 suites green controls 7/7 259.6s zero "
    "regression (qa/reconcile-all-R2010.log); first battery FAIL "
    "preserved (qa/reconcile-all-R2010-firstfail.log: cd7 live "
    "census flagged the pre-battery evidence file - ordering "
    "artifact vs the R2009 battery sequence which lands evidence "
    "after the battery, non-product defect; census --update-"
    "baseline legal re-anchor 515->519 (+two R2009 leftover "
    "files debt cleaned) then re-run green); matrix regen 230 "
    "suites 1954 criteria --check byte-identical 22180B; "
    "fingerprint CLEAN domains=5; profile --daily --check PASS; "
    "census final 515->520 DRIFT-CLEAN flags=0. Radar: no new OH "
    "list since the R2009 window-8 sweep (radar row continues "
    "waiting). Explore consume-1 reseed-1 (gate-family-across-"
    "restart seed). Score 2."
)


def die(msg):
    print("ABORT: %s" % msg)
    sys.exit(2)


def main():
    # ---------- gate: in-round work must be present -------------
    st = json.loads(io.open(P_STATE, encoding="utf-8").read())
    if st["tick"] != 2010:
        die("tick not bumped: %s" % st["tick"])
    if len(st["log"]) != 21:
        die("log shape wrong: %d" % len(st["log"]))
    if not st["log"][-2].startswith(u"2026-10-17 R2010"):
        die("round line missing")
    if not st["log"][-1].startswith("R2010 tokens:"):
        die("tokens line missing")
    sz = os.path.getsize(P_STATE)
    if sz >= 78500:
        die("state over the line: %d" % sz)
    print("gate ok: tick=2010 log-items=21 bytes=%d" % sz)

    # ---------- 1. heartbeat.txt -------------------------------
    hb = io.open(P_HEART, encoding="utf-8", newline="").read()
    if not hb.endswith("\r\n"):
        hb += "\r\n"
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")[:-1] + "x +08:00"
    io.open(P_HEART, "w", encoding="utf-8", newline="").write(
        hb + stamp + HB_BODY + "\r\n")
    print("heartbeat.txt OK: R2010 line appended")

    # ---------- 2. status-export.json --------------------------
    import check_export_consistency as cec  # noqa: E402
    derived, _state, _exp, pat = cec.recompute()
    exp = json.loads(io.open(P_EXPORT, encoding="utf-8").read())
    exp["export_ts"] = now.astimezone().isoformat(
        timespec="seconds")
    exp["ceo_face"] = {
        "current": CEO_CURRENT,
        "latest_artifact": CEO_LATEST,
        "next_milestone": CEO_NEXT,
    }
    results = exp["results"]
    label = pat["tick_row_label"]
    tick_row = ["2010", label]
    rrows = [r for r in results
             if isinstance(r, list) and len(r) >= 2
             and r[1] != label]
    new_results = ([["R2010", RESULTS_ROW]]
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
    print("R2010 CLOSEOUT DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
