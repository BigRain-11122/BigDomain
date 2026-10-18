"""Cross-restart persistence window for the multi-year combined
honor yearbook read face (BigDomain R2025; the yearbooks_combined
seat of the persist-example family - R1889/R1900/R1902/R1981
precedents, canon = explore-queue honorcert multiyear persist
claim row, criteria AC-HYCP1..AC-HYCP7 pre-registered in that
row before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero on
any FAIL.

The combined face is a pure single-source derivation: every
per-year block derives from the honor_yearbook read face, which
derives from the civic honor board and the collectibles
collection read faces. The honorcert layer owns no storage (zero
close), so its persistence lives in two shipped stores - the
civic.db earn rows and the ledger.db certificate rows. Anchor
multi-year world (six accounts; 2026 board carol 12 / aaron 7 /
bob 7 with the tie broken by account id / dave 3, erin a
zero-row face; top-2 grant both years; 2025 and 2028 zero-earn
honest empty blocks) -> scrambled request canonicalized to the
ascending year axis -> three-piece close -> reopen the same two
dbs with the same config -> combined replay byte-identical ->
post-restart live continuation (erin earns so the 2026 board
moves and the re-grant heals incrementally; frank opens 2027 so
the 2027 block grows while the 2026 block stays frozen - the
permanent-certificate and cross-read isolation laws across a
restart) -> front-door gate survives the restart with zero
referenced-face calls -> pure-read law with zero token rows
across the whole window -> third instance stability.

Usage: python test_honorcert_yearbooks_persist.py
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

import ledger as L                    # noqa: E402 (P-47-2b core)
import civicpoints as CV              # noqa: E402 (R1752 face)
import collectibles as CL             # noqa: E402 (R619 face)
import honorcert as HC                # noqa: E402 (R1755 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the multi-year honor"
              " yearbook is a platform recognition roster, not"
              " investment advice, and carries no monetary value")

NETWORK_LIBS = ("urllib", "requests", "socket", "http")
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")
ACCOUNTS = ("usr:carol", "usr:aaron", "usr:bob", "usr:dave",
            "usr:erin", "usr:frank")
BAD_YEARS = (2026, True, "206", "20261", "abcd", "20-6", " 202",
             "".join(chr(c) for c in (0xFF12, 0xFF10, 0xFF12,
                                      0xFF16)), None)
NON_ITERABLES = (2026, True, 2.5, None, "2026", b"2026")
ITEM26 = "civic-honor-2026"
ITEM27 = "civic-honor-2027"
SCRAMBLED = ("2028", "2026", "2025", "2027")
ASCENDING = ["2025", "2026", "2027", "2028"]
ENV_KEYS = {"years", "yearbooks", "totals", "disclaimer"}
BLOCK_KEYS = {"year", "yearbook", "certified_count", "board_size"}
ROW_KEYS = {"board_rank", "account_id", "points", "item_id"}
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


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class CountingCivic(object):
    """Delegating wrapper counting honor_board calls (zero-call
    proof for the bad-args front door)."""

    def __init__(self, inner):
        self.inner = inner
        self.board_calls = 0

    def honor_board(self, year):
        self.board_calls += 1
        return self.inner.honor_board(year)


def block_rows(res):
    """Per-year block tuple view for value pinning."""
    out = []
    for block in res["yearbooks"]:
        rows = [(r["board_rank"], r["account_id"], r["points"],
                 r["item_id"]) for r in block["yearbook"]]
        out.append((block["year"], rows, block["certified_count"],
                    block["board_size"]))
    return out


def table_counts(led_path, cv_path):
    conn = sqlite3.connect(led_path)
    out = {
        "collectibles": int(conn.execute(
            "SELECT COUNT(*) FROM collectibles").fetchone()[0]),
        "ledger_tx": int(conn.execute(
            "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]),
        "ledger_entries": int(conn.execute(
            "SELECT COUNT(*) FROM ledger_entries").fetchone()[0]),
    }
    conn.close()
    cvconn = sqlite3.connect(cv_path)
    for table in CIVIC_TABLES:
        out[table] = int(cvconn.execute(
            "SELECT COUNT(*) FROM " + table).fetchone()[0])
    cvconn.close()
    return out


def build_world(led_path, cv_path, cfg):
    """Deterministic multi-year anchor world: three behaviors, six
    accounts; 2026 board carol 12 / aaron 7 / bob 7 (tie, id asc)
    / dave 3 with erin and frank zero-row faces; 2027 side board
    carol 5 / aaron 2; 2025 and 2028 carry zero earn rows."""
    led = L.Ledger(led_path, cfg)
    for acct in ACCOUNTS:
        led.ensure_account(acct, census_avatar_id=acct[4:])
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    cv.register_behavior("city-poll", "Community Poll", 5, 20, False)
    cv.register_behavior("street-clean", "Street Cleanup", 2, 20,
                         False)
    cv.register_behavior("harvest", "Harvest Help", 3, 20, False)
    cv.earn_civic("usr:carol", "city-poll", "2026-10-01", "c-poll-1")
    cv.earn_civic("usr:carol", "city-poll", "2026-10-01", "c-poll-2")
    cv.earn_civic("usr:carol", "street-clean", "2026-10-01",
                  "c-sc-1")
    cv.earn_civic("usr:aaron", "city-poll", "2026-10-01", "a-poll-1")
    cv.earn_civic("usr:aaron", "street-clean", "2026-10-01",
                  "a-sc-1")
    cv.earn_civic("usr:bob", "city-poll", "2026-10-01", "b-poll-1")
    cv.earn_civic("usr:bob", "street-clean", "2026-10-01",
                  "b-sc-1")
    cv.earn_civic("usr:dave", "harvest", "2026-10-01", "d-hv-1")
    cv.earn_civic("usr:carol", "city-poll", "2027-03-01", "c27-p-1")
    cv.earn_civic("usr:aaron", "street-clean", "2027-03-01",
                  "a27-s-1")
    return led, cv, cl


def rebuild(led_path, cv_path, cfg):
    led = L.Ledger(led_path, cfg)
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)
    return led, cv, cl, hc


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-ybcomb-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    mod_sha_before = dict(
        (name, sha16(io_read(os.path.join(BASE, name + ".py"))))
        for name in ("honorcert", "civicpoints", "collectibles"))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    led_path = os.path.join(tmp, "ledger.db")
    cv_path = os.path.join(tmp, "civic.db")

    # ---- instance 1: multi-year anchor world --------------------
    led, cv, cl = build_world(led_path, cv_path, cfg)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)
    hc.grant_year_honors("2026", 2, ITEM26)
    hc.grant_year_honors("2027", 2, ITEM27)

    # -- AC-HYCP1 pre-restart anchor pin + canonical year axis ----
    r1 = hc.yearbooks_combined(SCRAMBLED)
    r1b = hc.yearbooks_combined(SCRAMBLED)
    src_ok = True
    for block in r1["yearbooks"]:
        direct = hc.honor_yearbook(block["year"])
        stripped = {k: v for k, v in direct.items()
                    if k != "disclaimer"}
        if dump(stripped) != dump(block):
            src_ok = False
    ok1 = (
        r1["years"] == ASCENDING
        and [b["year"] for b in r1["yearbooks"]] == ASCENDING
        and block_rows(r1) == [
            ("2025", [], 0, 0),
            ("2026", [(1, "usr:carol", 12, ITEM26),
                      (2, "usr:aaron", 7, ITEM26)], 2, 4),
            ("2027", [(1, "usr:carol", 5, ITEM27),
                      (2, "usr:aaron", 2, ITEM27)], 2, 2),
            ("2028", [], 0, 0)]
        and set(r1.keys()) == ENV_KEYS
        and all(set(b.keys()) == BLOCK_KEYS
                for b in r1["yearbooks"])
        and all(set(r.keys()) == ROW_KEYS
                for b in r1["yearbooks"]
                for r in b["yearbook"])
        and set(r1["totals"].keys()) == TOTALS_KEYS
        and r1["totals"] == {"years_count": 4,
                             "certified_count": 4,
                             "board_size": 6,
                             "distinct_accounts": 2}
        and r1["disclaimer"] == DISCLAIMER
        and src_ok
        and dump(r1) == dump(r1b))
    record("AC-HYCP1", ok1, "anchor multi-year world pinned:"
          " scrambled request %s -> ascending years %s; per-block"
          " values pinned (2025/2028 honest empty blocks, 2026"
          " board carol 12 / aaron 7 with full item_id echo, 2027"
          " carol 5 / aaron 2); totals=%s (carol/aaron overlap in"
          " both rosters yet distinct_accounts=2); envelope keys"
          "=%s; per-block == honor_yearbook minus disclaimer"
          " (dumps)=%s; double-call byte-identical=%s"
          % (list(SCRAMBLED), r1["years"], r1["totals"],
             sorted(ENV_KEYS), src_ok, dump(r1) == dump(r1b)))

    # -- AC-HYCP2 three-piece cross-restart byte-identical --------
    snap1 = dump(r1)
    cnt1 = table_counts(led_path, cv_path)
    cl.close()
    cv.close()
    led.close()
    led2, cv2, cl2, hc2 = rebuild(led_path, cv_path, cfg)
    r2a = hc2.yearbooks_combined(SCRAMBLED)
    r2b = hc2.yearbooks_combined(SCRAMBLED)
    ok2 = (dump(r2a) == snap1 and r2a == r1
           and dump(r2b) == snap1
           and table_counts(led_path, cv_path) == cnt1)
    record("AC-HYCP2", ok2, "three-piece close (cl.close +"
          " cv.close + led.close - the honorcert face owns no"
          " storage and carries no close) -> Ledger +"
          " CivicPointsFace + CollectiblesFace + HonorCertFace"
          " rebuilt on the same two dbs with the same config: the"
          " combined multi-year envelope replays byte-identical"
          " to the pre-close snapshot (sha16=%s) and a second"
          " same-params read re-confirms it (sha16=%s) - the"
          " ascending year axis, the certified-only rosters, the"
          " board ranks, the certificate provenance and the"
          " totals all re-derive from the persisted civic.db earn"
          " rows and ledger.db certificate rows with zero"
          " in-memory drift; table counts frozen across the"
          " restart"
          % (sha16(dump(r2a)), sha16(dump(r2b))))

    # -- AC-HYCP3 post-restart 2026 continuation --------------------
    for i in range(4):
        cv2.earn_civic("usr:erin", "city-poll", "2026-10-02",
                       "e-poll-%d" % (i + 1))
    r3g = hc2.grant_year_honors("2026", 2, ITEM26)
    r3 = hc2.yearbooks_combined(SCRAMBLED)
    hon3 = [(h["rank"], h["account_id"], h["status"])
            for h in r3g["honorees"]]
    blocks3 = dict((b["year"], b) for b in r3["yearbooks"])
    ok3 = (
        r3g["granted"] == 1 and r3g["already"] == 1
        and hon3 == [(1, "usr:erin", "granted"),
                     (2, "usr:carol", "already")]
        and block_rows(r3)[1] == (
            "2026", [(1, "usr:erin", 20, ITEM26),
                     (2, "usr:carol", 12, ITEM26),
                     (3, "usr:aaron", 7, ITEM26)], 3, 5)
        and blocks3["2025"]["yearbook"] == []
        and blocks3["2028"]["yearbook"] == []
        and dump(blocks3["2027"]) == dump(
            dict((b["year"], b)
                 for b in r2a["yearbooks"])["2027"])
        and dump(r3) != snap1)
    record("AC-HYCP3", ok3, "post-restart continuation: erin earns"
          " four poll events on the reopened civic face so the"
          " 2026 board moves (erin 20 -> rank 1); the re-grant"
          " heals incrementally across the restart - honorees=%s"
          " (granted=%d already=%d: the top-2 slice covers exactly"
          " the new top two, erin costs one certificate row and"
          " carol converges to already; aaron sits at rank 3,"
          " outside the slice, yet keeps his yearbook row at the"
          " new board rank - permanent-certificate law across the"
          " restart); the 2026 block grows to %d rows %s; the 2027"
          " block stays frozen=%s and the 2025/2028 honest empty"
          " blocks stay empty; the fresh combined read differs"
          " from the pre-restart snapshot (zero-cache live"
          " recompute)=%s"
          % (hon3, r3g["granted"], r3g["already"],
             len(blocks3["2026"]["yearbook"]),
             [(r["board_rank"], r["account_id"])
              for r in blocks3["2026"]["yearbook"]],
             dump(blocks3["2027"]) == dump(
                 dict((b["year"], b)
                      for b in r2a["yearbooks"])["2027"]),
             dump(r3) != snap1))

    # -- AC-HYCP4 post-restart 2027 continuation + 2026 freeze ------
    for i in range(4):
        cv2.earn_civic("usr:frank", "city-poll", "2027-04-01",
                       "f-poll-%d" % (i + 1))
    r4g = hc2.grant_year_honors("2027", 2, ITEM27)
    r4 = hc2.yearbooks_combined(SCRAMBLED)
    hon4 = [(h["rank"], h["account_id"], h["status"])
            for h in r4g["honorees"]]
    blocks4 = dict((b["year"], b) for b in r4["yearbooks"])
    frozen26 = dump(blocks3["2026"])
    ok4 = (
        r4g["granted"] == 1 and r4g["already"] == 1
        and hon4 == [(1, "usr:frank", "granted"),
                     (2, "usr:carol", "already")]
        and block_rows(r4)[2] == (
            "2027", [(1, "usr:frank", 20, ITEM27),
                     (2, "usr:carol", 5, ITEM27),
                     (3, "usr:aaron", 2, ITEM27)], 3, 3)
        and dump(blocks4["2026"]) == frozen26
        and r4["totals"] == {"years_count": 4,
                             "certified_count": 6,
                             "board_size": 8,
                             "distinct_accounts": 4}
        and blocks4["2026"]["yearbook"][0]["item_id"] == ITEM26
        and all(r["item_id"] == ITEM27
                for r in blocks4["2027"]["yearbook"]))
    record("AC-HYCP4", ok4, "post-restart new-window continuation:"
          " frank earns four poll events in 2027 so the 2027 board"
          " moves (frank 20 -> rank 1); the re-grant heals across"
          " the restart - honorees=%s (granted=%d already=%d); the"
          " 2027 block grows to %d rows %s; the 2026 block stays"
          " byte-frozen across the 2027 grant (cross-read"
          " isolation)=%s; totals=%s (distinct accounts now %d:"
          " carol/aaron/erin/frank); item_id provenance clean"
          " (2026 rows echo %s, 2027 rows echo %s)"
          % (hon4, r4g["granted"], r4g["already"],
             len(blocks4["2027"]["yearbook"]),
             [(r["board_rank"], r["account_id"])
              for r in blocks4["2027"]["yearbook"]],
             dump(blocks4["2026"]) == frozen26, r4["totals"],
             r4["totals"]["distinct_accounts"], ITEM26, ITEM27))

    # -- AC-HYCP5 front-door gate survives the restart --------------
    ccv = CountingCivic(cv2)
    guard = HC.HonorCertFace(ccv, cl2, DISCLAIMER)
    before5 = table_counts(led_path, cv_path)
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
    ok5 = (all(s == HC.E_HC_BAD_ARGS for s in shape_bad)
           and all(s == HC.E_HC_BAD_ARGS for s in elem_bad)
           and dup_bad[0]
           and ccv.board_calls == 0
           and table_counts(led_path, cv_path) == before5)
    record("AC-HYCP5", ok5, "front-door gate survives the restart:"
          " non-iterable %d/%d forms rejected (str/bytes caught at"
          " the door); bad element forms %d/%d rejected; duplicate"
          " year rejected=%s; zero honor_board calls across the"
          " whole probe batch=%d (every reject lands before any"
          " referenced-face call - the gate rides the module law,"
          " nothing in-memory to lose); both-db table snapshots"
          " frozen across the probe batch"
          % (sum(1 for s in shape_bad if s == HC.E_HC_BAD_ARGS),
             len(NON_ITERABLES),
             sum(1 for s in elem_bad if s == HC.E_HC_BAD_ARGS),
             len(BAD_YEARS), dup_bad[0], ccv.board_calls))

    # -- AC-HYCP6 second restart + pure-read law --------------------
    snap4 = dump(r4)
    cl2.close()
    cv2.close()
    led2.close()
    led3, cv3, cl3, hc3 = rebuild(led_path, cv_path, cfg)
    before6 = table_counts(led_path, cv_path)
    z1 = dump(hc3.yearbooks_combined(SCRAMBLED))
    z2 = dump(hc3.yearbooks_combined(SCRAMBLED))
    z3 = dump(hc3.yearbooks_combined(("2026", "2027")))
    after6 = table_counts(led_path, cv_path)
    ok6 = (z1 == z2 == snap4
           and json.loads(z3)["years"] == ["2026", "2027"]
           and before6 == after6
           and before6["ledger_tx"] == 0
           and before6["ledger_entries"] == 0)
    record("AC-HYCP6", ok6, "second restart: three-piece close ->"
          " rebuild once more on the same two dbs - the combined"
          " multi-year envelope reads twice back-to-back"
          " byte-identical to the instance-2 terminal state"
          " (sha16=%s) and to each other (re-read purity); a"
          " two-year subset request returns exactly the 2026+2027"
          " axis (subset law); the read battery leaves both-db"
          " table counts constant with ledger_tx=%d and"
          " ledger_entries=%d across the whole window -"
          " certificates are platform awards and the combined"
          " face is a zero-token derivation"
          % (sha16(z1), before6["ledger_tx"],
             before6["ledger_entries"]))

    # -- AC-HYCP7 hygiene + sha proofs + delivery ------------------
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in NETWORK_LIBS)]
    method_src = inspect.getsource(
        HC.HonorCertFace.yearbooks_combined)
    write_hits = [t for t in ("INSERT", "UPDATE ", "DELETE")
                  if t in method_src]
    sha_ok = all(
        sha16(io_read(os.path.join(BASE, name + ".py"))) == sha_b
        for name, sha_b in mod_sha_before.items())
    tmp_outside = (not os.path.realpath(tmp).startswith(repo_root)
                   and os.path.realpath(tmp).startswith(
                       os.path.realpath(tempfile.gettempdir())))
    prior = len(RESULTS)
    ok7 = (sha16(io_read(cfg_path)) == cfg_sha_before
           and sha_ok and non_ascii == 0 and not net_imports
           and not write_hits and tmp_outside and prior == 6)
    record("AC-HYCP7", ok7, "hygiene: shipped files untouched"
          " (config.json + honorcert/civicpoints/collectibles"
          " sha16 stable=%s); suite source pure ASCII (%d"
          " non-ascii chars), zero network imports (%d hits);"
          " yearbooks_combined method source carries zero write"
          " statements (hits=%s); world tmp outside repo (%s);"
          " criteria registered=%d"
          % (sha_ok, non_ascii, len(net_imports),
             write_hits or "none",
             "yes" if tmp_outside else "NO", prior + 1))

    cl3.close()
    cv3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
