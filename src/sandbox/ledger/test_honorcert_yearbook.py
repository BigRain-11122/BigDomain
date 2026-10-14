"""Acceptance suite for the honor yearbook certified-only roster
read face (BigDomain R1979; canon = explore-queue honorcert
successor row). Asserts the pre-registered criteria AC-HY1..HY7
from the R1979 explore-queue claim row (criteria were registered
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Usage: python test_honorcert_yearbook.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                     # noqa: E402 (P-47-2b core)
import civicpoints as CV               # noqa: E402 (R1752 face)
import collectibles as CL             # noqa: E402 (R619 face)
import honorcert as HC                 # noqa: E402 (R1755 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the honor yearbook is a"
              " platform recognition roster, not investment advice,"
              " and carries no monetary value")

BANNED_VERBS = ("trade", "sell", "buy", "auction", "swap", "gift")
NETWORK_LIBS = ("urllib", "requests", "socket", "http")
SQL_TOKENS = ("INSERT", "UPDATE", "DELETE", "SELECT", "CREATE")
BAD_YEARS = (2026, True, "206", "20261", "abcd", "20-6", " 202",
             "２０２６", None)
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")
ROW_KEYS = {"board_rank", "account_id", "points", "item_id"}
ENV_KEYS = {"year", "yearbook", "certified_count", "board_size",
            "disclaimer"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_hc_error(fn, *codes):
    try:
        fn()
    except HC.HonorCertError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _civic_snapshot(cvconn):
    return [_count(cvconn, t) for t in CIVIC_TABLES]


class CountingCivic(object):
    """Delegating wrapper that counts honor_board calls (zero-call
    proof for the bad-args face)."""

    def __init__(self, inner):
        self.inner = inner
        self.board_calls = 0

    def honor_board(self, year):
        self.board_calls += 1
        return self.inner.honor_board(year)


class _Bare(object):
    pass


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-yearbook-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    led_path = os.path.join(tmp, "ledger.db")
    cv_path = os.path.join(tmp, "civic.db")

    led = L.Ledger(led_path, cfg)
    for acct in ("usr:carol", "usr:aaron", "usr:bob", "usr:dave",
                 "usr:erin"):
        led.ensure_account(acct, census_avatar_id=acct[4:])
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    conn = sqlite3.connect(led_path)
    cvconn = sqlite3.connect(cv_path)

    # World 1 board: carol 12, aaron 7, bob 7 (tie -> id asc), dave 3.
    cv.register_behavior("city-poll", "Community Poll", 5, 20, False)
    cv.register_behavior("street-clean", "Street Cleanup", 2, 20, False)
    cv.register_behavior("harvest", "Harvest Help", 3, 20, False)
    cv.earn_civic("usr:carol", "city-poll", "2026-10-01", "c-poll-1")
    cv.earn_civic("usr:carol", "city-poll", "2026-10-01", "c-poll-2")
    cv.earn_civic("usr:carol", "street-clean", "2026-10-01", "c-sc-1")
    cv.earn_civic("usr:aaron", "city-poll", "2026-10-01", "a-poll-1")
    cv.earn_civic("usr:aaron", "street-clean", "2026-10-01", "a-sc-1")
    cv.earn_civic("usr:bob", "city-poll", "2026-10-01", "b-poll-1")
    cv.earn_civic("usr:bob", "street-clean", "2026-10-01", "b-sc-1")
    cv.earn_civic("usr:dave", "harvest", "2026-10-01", "d-hv-1")

    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)

    # -- AC-HY1 face registration + module posture ------------------------
    with open(os.path.join(BASE, "honorcert.py"), "rb") as fh:
        mod_bytes = fh.read()
    mod_src = mod_bytes.decode("utf-8")
    mod_low = mod_src.lower()
    import_lines = [ln for ln in mod_src.splitlines()
                    if ln.startswith("import ") or ln.startswith("from ")]
    ok1 = (callable(getattr(hc, "honor_yearbook", None))
           and "def honor_yearbook" in mod_src
           and len(import_lines) == 0
           and "sqlite" not in mod_low
           and "SecGate" not in mod_src
           and all(tok not in mod_src for tok in SQL_TOKENS))
    record("AC-HY1", ok1,
           "honor_yearbook callable=%s; module import lines=%d;"
           " zero driver/zero SQL tokens=%s; SecGate-free=%s"
           % (callable(getattr(hc, "honor_yearbook", None)),
              len(import_lines),
              "sqlite" not in mod_low
              and all(tok not in mod_src for tok in SQL_TOKENS),
              "SecGate" not in mod_src))

    # -- AC-HY2 strict year gate + zero referenced-face calls --------------
    ccv = CountingCivic(cv)
    guard = HC.HonorCertFace(ccv, cl, DISCLAIMER)
    civic_before_bad = _civic_snapshot(cvconn)
    read_bad = []
    raised = True
    for form in BAD_YEARS:
        ok_one, got = expect_hc_error(
            lambda f=form: guard.honor_yearbook(f), HC.E_HC_BAD_ARGS)
        if ok_one:
            read_bad.append(got)
        else:
            read_bad.append("NOT-RAISED(%s)" % got)
            raised = False
    ok2 = (raised and ccv.board_calls == 0
           and _civic_snapshot(cvconn) == civic_before_bad)
    record("AC-HY2", ok2,
           "bad-year %d/%d rejected (all %s); zero honor_board"
           " calls=%d; civic snapshot unchanged=%s"
           % (len(read_bad), len(BAD_YEARS), read_bad[:3],
              ccv.board_calls,
              _civic_snapshot(cvconn) == civic_before_bad))

    # -- AC-HY3 certified-only filter + provenance echo --------------------
    hc.grant_year_honors("2026", 2, "civic-honor-2026")
    r3 = hc.honor_yearbook("2026")
    rows3 = [(r["board_rank"], r["account_id"], r["points"],
              r["item_id"]) for r in r3["yearbook"]]
    ok3 = (set(r3.keys()) == ENV_KEYS
           and all(set(r.keys()) == ROW_KEYS for r in r3["yearbook"])
           and rows3 == [(1, "usr:carol", 12, "civic-honor-2026"),
                         (2, "usr:aaron", 7, "civic-honor-2026")]
           and r3["certified_count"] == 2
           and r3["board_size"] == 4
           and r3["year"] == "2026"
           and r3["disclaimer"] == DISCLAIMER
           and all(r["item_id"] == "civic-honor-2026"
                   for r in r3["yearbook"]))
    record("AC-HY3", ok3,
           "envelope keys=%s; yearbook rows=%s; certified_count=%d"
           " board_size=%d; uncertified bob/dave excluded=%s"
           % (sorted(set(r3.keys())), rows3, r3["certified_count"],
              r3["board_size"],
              "usr:bob" not in [r["account_id"]
                                for r in r3["yearbook"]]
              and "usr:dave" not in [r["account_id"]
                                      for r in r3["yearbook"]]))

    # -- AC-HY4 live-board movement permanence -----------------------------
    for i in range(4):
        cv.earn_civic("usr:erin", "city-poll", "2026-10-02",
                      "e-poll-%d" % (i + 1))
    hc.grant_year_honors("2026", 2, "civic-honor-2026")
    r4 = hc.honor_yearbook("2026")
    rows4 = [(r["board_rank"], r["account_id"]) for r in r4["yearbook"]]
    ok4 = (rows4 == [(1, "usr:erin"), (2, "usr:carol"),
                     (3, "usr:aaron")]
           and r4["certified_count"] == len(r4["yearbook"]) == 3
           and r4["board_size"] == 5
           and all(r["item_id"] == "civic-honor-2026"
                   for r in r4["yearbook"]))
    record("AC-HY4", ok4,
           "board moved (erin 20 rank1); yearbook=%s;"
           " certified_count=%d == len=%d; board_size=%d; aaron"
           " keeps row at new board rank after dropping from top-2"
           % (rows4, r4["certified_count"], len(r4["yearbook"]),
              r4["board_size"]))

    # -- AC-HY5 multi-year isolation + over-cap + honest empty -------------
    r5a = hc.honor_yearbook("2027")
    led2_path = os.path.join(tmp, "ledger2.db")
    cv2_path = os.path.join(tmp, "civic2.db")
    led2 = L.Ledger(led2_path, cfg)
    for acct in ("usr:amy", "usr:ben", "usr:cara"):
        led2.ensure_account(acct, census_avatar_id=acct[4:])
    cv2 = CV.CivicPointsFace(DISCLAIMER, cv2_path)
    cl2 = CL.CollectiblesFace(led2)
    cv2.register_behavior("city-poll", "Community Poll", 5, 20, False)
    cv2.earn_civic("usr:amy", "city-poll", "2026-05-01", "w-a1")
    cv2.earn_civic("usr:ben", "city-poll", "2026-05-01", "w-b1")
    cv2.earn_civic("usr:cara", "city-poll", "2026-05-01", "w-c1")
    hc2 = HC.HonorCertFace(cv2, cl2, DISCLAIMER)
    hc2.grant_year_honors("2026", 10, "civic-honor-2026-alt")
    r5b = hc2.honor_yearbook("2026")
    conn2 = sqlite3.connect(led2_path)
    w2_rows = conn2.execute(
        "SELECT COUNT(*) FROM collectibles WHERE kind ="
        " 'certificate' AND event_ref = 'civic-honor:2027'"
    ).fetchone()[0]
    ok5 = (r5a["yearbook"] == [] and r5a["certified_count"] == 0
           and r5a["board_size"] == 0 and r5a["year"] == "2027"
           and r5a["disclaimer"] == DISCLAIMER
           and len(r5b["yearbook"]) == 3 and r5b["board_size"] == 3
           and r5b["certified_count"] == 3
           and [r["account_id"] for r in r5b["yearbook"]]
           == ["usr:amy", "usr:ben", "usr:cara"]
           and all(r["item_id"] == "civic-honor-2026-alt"
                   for r in r5b["yearbook"])
           and w2_rows == 0)
    record("AC-HY5", ok5,
           "zero-earn year 2027 yearbook=%s count=%d board_size=%d"
           " (honest empty); over-cap world yearbook size=%d=="
           "board_size=%d with own item_id echo; 2027 cert rows=%d"
           % (r5a["yearbook"], r5a["certified_count"],
              r5a["board_size"], len(r5b["yearbook"]),
              r5b["board_size"], w2_rows))

    # -- AC-HY6 pure-read law + composition law ----------------------------
    snap_before = (_civic_snapshot(cvconn),
                   _count(conn, "collectibles"),
                   _count(conn, "ledger_tx"))
    r6a = hc.honor_yearbook("2026")
    r6b = hc.honor_yearbook("2026")
    snap_after = (_civic_snapshot(cvconn),
                  _count(conn, "collectibles"),
                  _count(conn, "ledger_tx"))
    honors = hc.honor_certs("2026")["honors"]
    cert_honors = [h for h in honors if h["certified"]]
    comp_ok = (len(cert_honors) == len(r6a["yearbook"])
               and all(h["account_id"] == y["account_id"]
                       and h["rank"] == y["board_rank"]
                       and h["points"] == y["points"]
                       and h["item_id"] == y["item_id"]
                       for h, y in zip(cert_honors, r6a["yearbook"])))
    ok6 = (snap_before == snap_after and r6a == r6b and comp_ok)
    record("AC-HY6", ok6,
           "double-call snapshot equal=%s; envelope repeat equal=%s;"
           " composition: certified subset of honor_certs honors"
           "==%d yearbook rows, per-row rank/points/item_id equal=%s"
           % (snap_before == snap_after, r6a == r6b,
              len(r6a["yearbook"]), comp_ok))

    # -- AC-HY7 hard laws --------------------------------------------------
    net_mod = [ln for ln in import_lines
               for lib in NETWORK_LIBS if lib in ln]
    verb_hits = [v for v in BANNED_VERBS if v in mod_low]
    with open(os.path.abspath(__file__), encoding="utf-8") as fh:
        test_src = fh.read()
    test_imports = [ln for ln in test_src.splitlines()
                    if ln.startswith("import ") or ln.startswith("from ")]
    net_test = [ln for ln in test_imports
                for lib in NETWORK_LIBS if lib in ln]
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    ascii_ok = all(b < 128 for b in mod_bytes)
    prior = len(RESULTS)
    ok7 = (ascii_ok and not net_mod and not verb_hits
           and "random" not in mod_low and not net_test
           and cfg_after == cfg_bytes and prior == 6)
    record("AC-HY7", ok7,
           "module ascii=%s zero network imports=%d zero circulation"
           " verbs=%s zero dice lib=%s; suite true-import network"
           " lines=%d; shipped config.json byte-stable=%s; criteria"
           " registered=%d"
           % (ascii_ok, len(net_mod), verb_hits,
              "random" not in mod_low, len(net_test),
              cfg_after == cfg_bytes, prior + 1))

    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
