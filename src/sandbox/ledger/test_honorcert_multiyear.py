"""Acceptance suite for the multi-year combined honor yearbook
read face (BigDomain R2007; canon = explore-queue honorcert
successor row). Asserts the pre-registered criteria AC-HYM1..HYM7
from the R2007 explore-queue claim row (criteria were registered
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Usage: python test_honorcert_multiyear.py
"""

import hashlib
import inspect
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
import collectibles as CL              # noqa: E402 (R619 face)
import honorcert as HC                 # noqa: E402 (R1755 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the multi-year honor"
              " yearbook is a platform recognition roster, not"
              " investment advice, and carries no monetary value")

BANNED_VERBS = ("trade", "sell", "buy", "auction", "swap", "gift")
NETWORK_LIBS = ("urllib", "requests", "socket", "http")
SQL_WRITE_TOKENS = ("INSERT", "UPDATE", "DELETE", "CREATE", "ALTER")
BAD_YEARS = (2026, True, "206", "20261", "abcd", "20-6", " 202",
             "２０２６", None)
NON_ITERABLES = (2026, True, 2.5, None, "2026", b"2026")
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")
ROW_KEYS = {"board_rank", "account_id", "points", "item_id"}
ENV_KEYS = {"years", "yearbooks", "totals", "disclaimer"}
BLOCK_KEYS = {"year", "yearbook", "certified_count", "board_size"}
TOTALS_KEYS = {"years_count", "certified_count", "board_size",
               "distinct_accounts"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


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


def _dumps(obj):
    return json.dumps(obj, sort_keys=True)


def _combined_years(env):
    return env["years"]


class CountingCivic(object):
    """Delegating wrapper that counts honor_board calls (zero-call
    proof for the front-door face)."""

    def __init__(self, inner):
        self.inner = inner
        self.board_calls = 0

    def honor_board(self, year):
        self.board_calls += 1
        return self.inner.honor_board(year)


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-multiyear-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(BASE, "civicpoints.py"), "rb") as fh:
        cv_sha_before = hashlib.sha256(fh.read()).hexdigest()
    with open(os.path.join(BASE, "collectibles.py"), "rb") as fh:
        cl_sha_before = hashlib.sha256(fh.read()).hexdigest()
    led_path = os.path.join(tmp, "ledger.db")
    cv_path = os.path.join(tmp, "civic.db")

    led = L.Ledger(led_path, cfg)
    for acct in ("usr:carol", "usr:aaron", "usr:bob", "usr:dave",
                 "usr:erin", "usr:frank"):
        led.ensure_account(acct, census_avatar_id=acct[4:])
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    conn = sqlite3.connect(led_path)
    cvconn = sqlite3.connect(cv_path)

    # World 1 board (2026): carol 12, aaron 7, bob 7 (tie -> id
    # asc), dave 3; grant top-2 -> carol + aaron certified.
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
    hc.grant_year_honors("2026", 2, "civic-honor-2026")

    # -- AC-HYM1 contract + honest states ----------------------------------
    r1 = hc.yearbooks_combined(("2027", "2026"))
    blocks = {b["year"]: b for b in r1["yearbooks"]}
    rows26 = [(r["board_rank"], r["account_id"], r["points"],
               r["item_id"]) for r in blocks["2026"]["yearbook"]]
    empty_env = hc.yearbooks_combined(())
    ok1 = (set(r1.keys()) == ENV_KEYS
           and _combined_years(r1) == ["2026", "2027"]
           and [b["year"] for b in r1["yearbooks"]] == ["2026",
                                                         "2027"]
           and all(set(b.keys()) == BLOCK_KEYS
                   for b in r1["yearbooks"])
           and all(set(r.keys()) == ROW_KEYS
                   for b in r1["yearbooks"]
                   for r in b["yearbook"])
           and set(r1["totals"].keys()) == TOTALS_KEYS
           and rows26 == [(1, "usr:carol", 12, "civic-honor-2026"),
                          (2, "usr:aaron", 7, "civic-honor-2026")]
           and blocks["2026"]["certified_count"] == 2
           and blocks["2026"]["board_size"] == 4
           and blocks["2027"]["yearbook"] == []
           and blocks["2027"]["certified_count"] == 0
           and blocks["2027"]["board_size"] == 0
           and r1["totals"] == {"years_count": 2,
                                "certified_count": 2,
                                "board_size": 4,
                                "distinct_accounts": 2}
           and r1["disclaimer"] == DISCLAIMER
           and empty_env == {"years": [], "yearbooks": [],
                             "totals": {"years_count": 0,
                                        "certified_count": 0,
                                        "board_size": 0,
                                        "distinct_accounts": 0},
                             "disclaimer": DISCLAIMER})
    record("AC-HYM1", ok1,
           "envelope keys=%s; years=%s (scrambled request"
           " canonicalized); block keys=%s; row keys=%s; totals=%s;"
           " zero-earn 2027 block honest empty=%s; empty years"
           " request honest envelope=%s"
           % (sorted(set(r1.keys())), _combined_years(r1),
              sorted(BLOCK_KEYS), sorted(ROW_KEYS), r1["totals"],
              blocks["2027"]["yearbook"] == [],
              empty_env["yearbooks"] == []))

    # -- AC-HYM2 single-source cross + overlap distinct law ----------------
    src_ok = True
    for year in ("2026", "2027"):
        direct = hc.honor_yearbook(year)
        stripped = {k: v for k, v in direct.items()
                    if k != "disclaimer"}
        if _dumps(stripped) != _dumps(blocks[year]):
            src_ok = False
    cv.earn_civic("usr:carol", "city-poll", "2027-03-01", "w2-c-1")
    cv.earn_civic("usr:aaron", "street-clean", "2027-03-01",
                  "w2-a-1")
    hc.grant_year_honors("2027", 2, "civic-honor-2027")
    r2 = hc.yearbooks_combined(("2026", "2027"))
    blocks2 = {b["year"]: b for b in r2["yearbooks"]}
    accts26 = [r["account_id"] for r in blocks2["2026"]["yearbook"]]
    accts27 = [r["account_id"] for r in blocks2["2027"]["yearbook"]]
    ok2 = (src_ok
           and r2["totals"]["certified_count"] == 4
           and r2["totals"]["board_size"] == 6
           and r2["totals"]["distinct_accounts"] == 2
           and accts26 == ["usr:carol", "usr:aaron"]
           and accts27 == ["usr:carol", "usr:aaron"]
           and all(r["item_id"] == "civic-honor-2027"
                   for r in blocks2["2027"]["yearbook"]))
    record("AC-HYM2", ok2,
           "per-year block == honor_yearbook minus disclaimer"
           " (dumps sort_keys)=%s; overlap world certified=%d"
           " board=%d distinct=%d (carol/aaron in both rosters,"
           " counted once each)=%s"
           % (src_ok, r2["totals"]["certified_count"],
              r2["totals"]["board_size"],
              r2["totals"]["distinct_accounts"],
              accts26 == accts27 == ["usr:carol", "usr:aaron"]))

    # -- AC-HYM3 ascending year axis + determinism -------------------------
    r3 = hc.yearbooks_combined(("2027", "2025", "2026"))
    r3b = hc.yearbooks_combined(("2027", "2025", "2026"))
    blocks3 = {b["year"]: b for b in r3["yearbooks"]}
    ok3 = (_combined_years(r3) == ["2025", "2026", "2027"]
           and [b["year"] for b in r3["yearbooks"]]
           == ["2025", "2026", "2027"]
           and blocks3["2025"]["yearbook"] == []
           and blocks3["2025"]["certified_count"] == 0
           and blocks3["2025"]["board_size"] == 0
           and _dumps(r3) == _dumps(r3b)
           and _dumps(r2) == _dumps(
               hc.yearbooks_combined(("2026", "2027"))))
    record("AC-HYM3", ok3,
           "scrambled request -> ascending years=%s; zero-earn"
           " 2025 honest empty block=%s; double-call dumps"
           " byte-identical=%s; stable request==repeat read=%s"
           % (_combined_years(r3),
              blocks3["2025"]["yearbook"] == [],
              _dumps(r3) == _dumps(r3b),
              _dumps(r2) == _dumps(
                  hc.yearbooks_combined(("2026", "2027")))))

    # -- AC-HYM4 front door fail-closed ------------------------------------
    ccv = CountingCivic(cv)
    guard = HC.HonorCertFace(ccv, cl, DISCLAIMER)
    civic_before_bad = _civic_snapshot(cvconn)
    shape_bad = []
    for form in NON_ITERABLES:
        ok_one, got = expect_hc_error(
            lambda f=form: guard.yearbooks_combined(f),
            HC.E_HC_BAD_ARGS)
        shape_bad.append(got if ok_one else "NOT-RAISED(%s)" % got)
    elem_bad = []
    for form in BAD_YEARS:
        ok_one, got = expect_hc_error(
            lambda f=form: guard.yearbooks_combined(("2026", f)),
            HC.E_HC_BAD_ARGS)
        elem_bad.append(got if ok_one else "NOT-RAISED(%s)" % got)
    dup_bad = expect_hc_error(
        lambda: guard.yearbooks_combined(("2026", "2026")),
        HC.E_HC_BAD_ARGS)
    ok4 = (all(s == HC.E_HC_BAD_ARGS for s in shape_bad)
           and all(s == HC.E_HC_BAD_ARGS for s in elem_bad)
           and dup_bad[0]
           and ccv.board_calls == 0
           and _civic_snapshot(cvconn) == civic_before_bad)
    record("AC-HYM4", ok4,
           "non-iterable %d/%d rejected (str/bytes caught at"
           " door); bad element forms %d/%d rejected; duplicate"
           " year rejected=%s; zero honor_board calls on reject"
           " batch=%d; civic snapshot unchanged=%s"
           % (sum(1 for s in shape_bad if s == HC.E_HC_BAD_ARGS),
              len(NON_ITERABLES),
              sum(1 for s in elem_bad if s == HC.E_HC_BAD_ARGS),
              len(BAD_YEARS), dup_bad[0], ccv.board_calls,
              _civic_snapshot(cvconn) == civic_before_bad))

    # -- AC-HYM5 cross-year isolation + live recompute ----------------------
    frozen26 = _dumps(blocks2["2026"])
    cv.earn_civic("usr:frank", "city-poll", "2027-04-01", "w5-f-1")
    r5a = hc.yearbooks_combined(("2026", "2027"))
    blocks5a = {b["year"]: b for b in r5a["yearbooks"]}
    live27 = blocks5a["2027"]
    ok5a = (live27["board_size"] == 3
            and _dumps(blocks5a["2026"]) == frozen26
            and [r["board_rank"] for r in live27["yearbook"]]
            == [1, 3]
            and len(live27["yearbook"]) == 2)
    for i in range(4):
        cv.earn_civic("usr:erin", "city-poll", "2026-10-02",
                      "e-poll-%d" % (i + 1))
    hc.grant_year_honors("2026", 2, "civic-honor-2026")
    r5b = hc.yearbooks_combined(("2026", "2027"))
    blocks5b = {b["year"]: b for b in r5b["yearbooks"]}
    live26 = blocks5b["2026"]
    rows5b = [(r["board_rank"], r["account_id"])
              for r in live26["yearbook"]]
    ok5 = (ok5a
           and rows5b == [(1, "usr:erin"), (2, "usr:carol"),
                          (3, "usr:aaron")]
           and live26["certified_count"] == 3
           and live26["board_size"] == 5
           and _dumps(blocks5b["2027"]) == _dumps(live27))
    record("AC-HYM5", ok5,
           "2027 continuation: board_size 2->3 with frank entering"
           " (aaron board_rank 2->3)=%s, 2026 block frozen=%s;"
           " 2026 continuation: erin 20pts moves board, yearbook"
           " rows=%s certified=%d board_size=%d, 2027 block"
           " frozen=%s"
           % (ok5a, _dumps(blocks5a["2026"]) == frozen26, rows5b,
              live26["certified_count"], live26["board_size"],
              _dumps(blocks5b["2027"]) == _dumps(live27)))

    # -- AC-HYM6 pure-read law ---------------------------------------------
    snap_before = (_civic_snapshot(cvconn),
                   _count(conn, "collectibles"),
                   _count(conn, "ledger_tx"))
    r6a = hc.yearbooks_combined(("2026", "2027"))
    r6b = hc.yearbooks_combined(("2025", "2026", "2027"))
    hc.honor_yearbook("2026")
    hc.honor_certs("2026")
    snap_after = (_civic_snapshot(cvconn),
                  _count(conn, "collectibles"),
                  _count(conn, "ledger_tx"))
    method_src = inspect.getsource(
        HC.HonorCertFace.yearbooks_combined)
    write_hits = [tok for tok in SQL_WRITE_TOKENS
                  if tok in method_src]
    ok6 = (snap_before == snap_after
           and r6a == r5b
           and not write_hits
           and r6b["totals"]["years_count"] == 3)
    record("AC-HYM6", ok6,
           "read batch (combined x2 + direct reads) civic/collect"
           "ibles/ledger_tx snapshot equal=%s; combined repeat =="
           " prior read=%s; method-source write tokens=%s (zero"
           " hits)=%s"
           % (snap_before == snap_after, r6a == r5b, write_hits,
              not write_hits))

    # -- AC-HYM7 hygiene + delivery posture ---------------------------------
    with open(os.path.join(BASE, "honorcert.py"), "rb") as fh:
        mod_bytes = fh.read()
    mod_src = mod_bytes.decode("utf-8")
    mod_low = mod_src.lower()
    import_lines = [ln for ln in mod_src.splitlines()
                    if ln.startswith("import ")
                    or ln.startswith("from ")]
    net_mod = [ln for ln in import_lines
               for lib in NETWORK_LIBS if lib in ln]
    verb_hits = [v for v in BANNED_VERBS if v in mod_low]
    with open(os.path.abspath(__file__), encoding="utf-8") as fh:
        test_src = fh.read()
    test_imports = [ln for ln in test_src.splitlines()
                    if ln.startswith("import ")
                    or ln.startswith("from ")]
    net_test = [ln for ln in test_imports
                for lib in NETWORK_LIBS if lib in ln]
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    with open(os.path.join(BASE, "civicpoints.py"), "rb") as fh:
        cv_sha_after = hashlib.sha256(fh.read()).hexdigest()
    with open(os.path.join(BASE, "collectibles.py"), "rb") as fh:
        cl_sha_after = hashlib.sha256(fh.read()).hexdigest()
    ascii_ok = all(b < 128 for b in mod_bytes)
    additive_ok = (callable(getattr(hc, "grant_year_honors", None))
                   and callable(getattr(hc, "honor_certs", None))
                   and callable(getattr(hc, "honor_yearbook",
                                        None))
                   and callable(getattr(hc,
                                        "yearbooks_combined",
                                        None)))
    prior = len(RESULTS)
    ok7 = (ascii_ok and len(import_lines) == 0 and not net_mod
           and not verb_hits and "random" not in mod_low
           and not net_test and cfg_after == cfg_bytes
           and cv_sha_before == cv_sha_after
           and cl_sha_before == cl_sha_after
           and additive_ok and prior == 6)
    record("AC-HYM7", ok7,
           "module ascii=%s import lines=%d network=%d banned"
           " verbs=%s dice lib=%s; suite true-import network"
           " lines=%d; shipped config byte-stable=%s;"
           " civicpoints/collectibles sha untouched=%s/%s; face"
           " set additive (4 methods callable)=%s; criteria"
           " registered=%d"
           % (ascii_ok, len(import_lines), len(net_mod),
              verb_hits, "random" not in mod_low, len(net_test),
              cfg_after == cfg_bytes,
              cv_sha_before == cv_sha_after,
              cl_sha_before == cl_sha_after, additive_ok,
              prior + 1))

    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
