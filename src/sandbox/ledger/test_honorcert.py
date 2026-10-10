"""Acceptance suite for the annual civic honor certificate grant
face (BigDomain R1755; canon = explore-queue honor-certificate
line). Asserts the pre-registered criteria AC-HC1..HC7 from the
R1755 explore-queue row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Usage: python test_honorcert.py
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

import ledger as L                    # noqa: E402 (P-47-2b core)
import civicpoints as CV              # noqa: E402 (R1752 face)
import collectibles as CL             # noqa: E402 (R619 face)
import honorcert as HC                # noqa: E402 (R1755 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: civic honor certificates"
              " are a platform recognition feature, not investment"
              " advice, and carry no monetary value")

BANNED_VERBS = ("trade", "sell", "buy", "auction", "swap", "gift")
NETWORK_LIBS = ("urllib", "requests", "socket", "http")
SQL_TOKENS = ("INSERT", "UPDATE", "DELETE", "SELECT", "CREATE")
BAD_YEARS = (2026, True, "206", "20261", "abcd", "20-6", " 202",
             "２０２６", None)
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")


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


class CountingCollectibles(object):
    """Delegating wrapper that counts award-verb calls (zero-call
    proof for the bad-args face)."""

    def __init__(self, inner):
        self.inner = inner
        self.issue_calls = 0

    def issue_certificate(self, account_id, event_ref, item_id):
        self.issue_calls += 1
        return self.inner.issue_certificate(account_id, event_ref,
                                             item_id)

    def collection(self, account_id):
        return self.inner.collection(account_id)


class _Bare(object):
    pass


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-ac-")
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
    baseline_tx = _count(conn, "ledger_tx")

    # -- AC-HC1 constructor fail-closed + zero-storage structure --------
    ok_none_c, code_none_c = expect_hc_error(
        lambda: HC.HonorCertFace(None, cl, DISCLAIMER), HC.E_HC_BAD_ARGS)
    ok_none_l, code_none_l = expect_hc_error(
        lambda: HC.HonorCertFace(cv, None, DISCLAIMER), HC.E_HC_BAD_ARGS)
    ok_attr_c, code_attr_c = expect_hc_error(
        lambda: HC.HonorCertFace(_Bare(), cl, DISCLAIMER),
        HC.E_HC_BAD_ARGS)
    ok_attr_l, code_attr_l = expect_hc_error(
        lambda: HC.HonorCertFace(cv, _Bare(), DISCLAIMER),
        HC.E_HC_BAD_ARGS)
    ok_disc, code_disc = expect_hc_error(
        lambda: HC.HonorCertFace(cv, cl, "  "), HC.E_HC_NO_DISCLAIMER)
    with open(os.path.join(BASE, "honorcert.py"), "rb") as fh:
        mod_bytes = fh.read()
    mod_src = mod_bytes.decode("utf-8")
    mod_low = mod_src.lower()
    import_lines = [ln for ln in mod_src.splitlines()
                    if ln.startswith("import ") or ln.startswith("from ")]
    ok1 = (ok_none_c and ok_none_l and ok_attr_c and ok_attr_l and ok_disc
           and code_disc == HC.E_HC_NO_DISCLAIMER
           and len(import_lines) == 0
           and "sqlite" not in mod_low
           and "SecGate" not in mod_src
           and all(tok not in mod_src for tok in SQL_TOKENS))
    record("AC-HC1", ok1,
           "constructor rejects None civic=%s None collectibles=%s"
           " missing-attr civic=%s collectibles=%s empty disclaimer=%s;"
           " module source carries zero import lines (zero own storage,"
           " zero driver, zero SQL tokens, zero gate reference)"
           % (code_none_c, code_none_l, code_attr_c, code_attr_l,
              code_disc))

    # -- AC-HC2 strict args, zero referenced-face calls -------------------
    ccv = CountingCivic(cv)
    ccl = CountingCollectibles(cl)
    guard = HC.HonorCertFace(ccv, ccl, DISCLAIMER)
    civic_before_bad = _civic_snapshot(cvconn)
    year_bad = []
    raised_y = True
    for form in BAD_YEARS:
        ok_one, got = expect_hc_error(
            lambda f=form: guard.grant_year_honors(f, 2, "x"),
            HC.E_HC_BAD_ARGS)
        if ok_one:
            year_bad.append(got)
        else:
            year_bad.append("NOT-RAISED(%s)" % got)
            raised_y = False
    top_bad = []
    raised_t = True
    for form in (True, "2", 2.5, 0, -1):
        ok_one, got = expect_hc_error(
            lambda f=form: guard.grant_year_honors("2026", f, "x"),
            HC.E_HC_BAD_ARGS)
        if ok_one:
            top_bad.append(got)
        else:
            top_bad.append("NOT-RAISED(%s)" % got)
            raised_t = False
    item_bad = []
    raised_i = True
    for form in ("", "   ", None):
        ok_one, got = expect_hc_error(
            lambda f=form: guard.grant_year_honors("2026", 2, f),
            HC.E_HC_BAD_ARGS)
        if ok_one:
            item_bad.append(got)
        else:
            item_bad.append("NOT-RAISED(%s)" % got)
            raised_i = False
    cl_rows_after_bad = _count(conn, "collectibles")
    ok2 = (raised_y and raised_t and raised_i
           and ccv.board_calls == 0 and ccl.issue_calls == 0
           and cl_rows_after_bad == 0
           and _civic_snapshot(cvconn) == civic_before_bad)
    record("AC-HC2", ok2,
           "year %d/%d bad forms rejected; top_n %d/5 rejected; item_id"
           " %d/3 rejected; zero honor_board calls=%d zero award"
           " calls=%d; collectibles rows=%d"
           % (len(year_bad), len(BAD_YEARS), len(top_bad),
              len(item_bad), ccv.board_calls, ccl.issue_calls,
              cl_rows_after_bad))

    # -- AC-HC3 top-N grant chain + deterministic slice + idempotent rerun
    r3 = hc.grant_year_honors("2026", 2, "civic-honor-2026")
    rows3 = conn.execute(
        "SELECT account_id FROM collectibles WHERE kind = 'certificate'"
        " AND event_ref = 'civic-honor:2026' ORDER BY account_id"
    ).fetchall()
    slice_ok = ([(h["rank"], h["account_id"], h["points"], h["status"])
                 for h in r3["honorees"]]
                == [(1, "usr:carol", 12, "granted"),
                    (2, "usr:aaron", 7, "granted")])
    cert_carol = cl.collection("usr:carol")["certificates"]
    r3b = hc.grant_year_honors("2026", 2, "civic-honor-2026")
    rows3b = conn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE kind = 'certificate'"
        " AND event_ref = 'civic-honor:2026'").fetchone()[0]
    ok3 = (r3["granted"] == 2 and r3["already"] == 0 and slice_ok
           and [r[0] for r in rows3] == ["usr:aaron", "usr:carol"]
           and any(c["event_ref"] == "civic-honor:2026"
                   and c["item_id"] == "civic-honor-2026"
                   for c in cert_carol)
           and r3b["granted"] == 0 and r3b["already"] == 2
           and all(h["status"] == "already" for h in r3b["honorees"])
           and rows3b == 2)
    record("AC-HC3", ok3,
           "top-2 slice = %s; granted=%d already=%d; cert rows=%d;"
           " collection cross-check ok; rerun granted=%d already=%d"
           " rows stay %d"
           % ([(h["account_id"], h["status"]) for h in r3["honorees"]],
              r3["granted"], r3["already"], len(rows3),
              r3b["granted"], r3b["already"], rows3b))

    # -- AC-HC4 live board incremental grant ------------------------------
    for i in range(4):
        cv.earn_civic("usr:erin", "city-poll", "2026-10-02",
                      "e-poll-%d" % (i + 1))
    r4 = hc.grant_year_honors("2026", 2, "civic-honor-2026")
    year_certs = conn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE kind = 'certificate'"
        " AND event_ref = 'civic-honor:2026'").fetchone()[0]
    aaron_row = conn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE account_id ="
        " 'usr:aaron' AND kind = 'certificate' AND event_ref ="
        " 'civic-honor:2026'").fetchone()[0]
    r4_honorees = [(h["rank"], h["account_id"], h["status"])
                   for h in r4["honorees"]]
    ok4 = (r4_honorees == [(1, "usr:erin", "granted"),
                           (2, "usr:carol", "already")]
           and r4["granted"] == 1 and r4["already"] == 1
           and year_certs == 3 and aaron_row == 1)
    record("AC-HC4", ok4,
           "board moved (erin 20 -> rank1); incremental grant=%d"
           " already=%d honorees=%s; year cert total=%d; aaron's"
           " out-of-top certificate persists=%d"
           % (r4["granted"], r4["already"], r4_honorees, year_certs,
              aaron_row))

    # -- AC-HC5 honest over-cap + zero-earn year ---------------------------
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
    r5a = hc2.grant_year_honors("2026", 10, "civic-honor-2026")
    r5b = hc2.grant_year_honors("2027", 5, "civic-honor-2027")
    conn2 = sqlite3.connect(led2_path)
    w2_rows = conn2.execute(
        "SELECT COUNT(*) FROM collectibles WHERE kind ="
        " 'certificate' AND event_ref LIKE 'civic-honor:%'"
    ).fetchone()[0]
    w2_2027 = conn2.execute(
        "SELECT COUNT(*) FROM collectibles WHERE event_ref ="
        " 'civic-honor:2027'").fetchone()[0]
    ok5 = (r5a["granted"] == 3 and len(r5a["honorees"]) == 3
           and r5b["granted"] == 0 and r5b["honorees"] == []
           and w2_rows == 3 and w2_2027 == 0)
    record("AC-HC5", ok5,
           "cap 10 over 3-account board -> honest full grant=%d;"
           " zero-earn year 2027 grant=%d honorees=%s; rows 2026=%d"
           " rows 2027=%d"
           % (r5a["granted"], r5b["granted"], r5b["honorees"],
              w2_rows, w2_2027))

    # -- AC-HC6 read face derivation + pure-read law -----------------------
    snap_before = (_civic_snapshot(cvconn),
                   _count(conn, "collectibles"),
                   _count(conn, "ledger_tx"))
    r6 = hc.honor_certs("2026")
    hc.honor_certs("2026")
    snap_after = (_civic_snapshot(cvconn),
                  _count(conn, "collectibles"),
                  _count(conn, "ledger_tx"))
    env_keys = set(r6.keys())
    row_keys = set(r6["honors"][0].keys()) if r6["honors"] else set()
    by_acct = {h["account_id"]: h for h in r6["honors"]}
    uncertified = [a for a, h in by_acct.items() if not h["certified"]]
    read_bad = []
    raised_r = True
    for form in BAD_YEARS:
        ok_one, got = expect_hc_error(
            lambda f=form: hc.honor_certs(f), HC.E_HC_BAD_ARGS)
        if ok_one:
            read_bad.append(got)
        else:
            read_bad.append("NOT-RAISED(%s)" % got)
            raised_r = False
    ok6 = (env_keys == {"year", "honors", "certified_count",
                        "disclaimer"}
           and row_keys == {"rank", "account_id", "points", "certified",
                            "item_id"}
           and r6["certified_count"] == 3
           and by_acct["usr:aaron"]["certified"]
           and by_acct["usr:erin"]["certified"]
           and by_acct["usr:carol"]["certified"]
           and sorted(uncertified) == ["usr:bob", "usr:dave"]
           and all(by_acct[a]["item_id"] is None for a in uncertified)
           and all(by_acct[a]["item_id"] == "civic-honor-2026"
                   for a in ("usr:aaron", "usr:erin", "usr:carol"))
           and raised_r and snap_before == snap_after
           and _count(conn, "ledger_tx") == baseline_tx)
    record("AC-HC6", ok6,
           "envelope keys=%s; row keys=%s; certified_count=%d (aaron"
           " keeps flag at rank %d after board move); uncertified=%s"
           " item_id None; read bad-year %d/%d rejected; pure-read"
           " snapshot equal; ledger_tx=%d==baseline"
           % (sorted(env_keys), sorted(row_keys),
              r6["certified_count"], by_acct["usr:aaron"]["rank"],
              sorted(uncertified), len(read_bad), len(BAD_YEARS),
              _count(conn, "ledger_tx")))

    # -- AC-HC7 hard laws --------------------------------------------------
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
    record("AC-HC7", ok7,
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
