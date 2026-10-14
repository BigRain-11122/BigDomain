"""Cross-restart persistence window for the honor yearbook
certified-only roster read face (BigDomain R1981; the yearbook
seat of the persist-example family - R1889/R1900/R1902/R1923
precedents, canon = explore-queue honor-yearbook-persist claim
row, criteria AC-HYP1..AC-HYP6 pre-registered in that row before
this code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL.

The honor yearbook is a pure single-source derivation: it derives
from the honor_certs read face, which derives from the civic
honor board and the collectibles collection read faces. The
honorcert layer owns no storage (zero close), so its persistence
lives in two shipped stores - the civic.db earn rows and the
ledger.db certificate rows. Anchor world (five accounts, board
carol 12 / aaron 7 / bob 7 with the tie broken by account id /
dave 3, erin a zero-row face; top-2 grant lands two certificate
rows with zero token rows) -> three-piece close -> reopen the
same two dbs with the same config -> yearbook replay
byte-identical on both years -> post-restart live continuation
(erin earns so the board moves; the re-grant heals incrementally
- erin granted, carol and aaron already; aaron drops out of the
top-2 slice yet keeps his yearbook row at the new board rank -
the permanent-certificate law across a restart; dave opens the
2027 namespace so the cross-year isolation stays live) -> year
gate survives the restart with zero referenced-face calls ->
pure-read law with zero token rows across the whole window ->
third instance stability.

Usage: python test_honorcert_yearbook_persist.py
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

DISCLAIMER = ("sandbox stand-in disclaimer: the honor yearbook is a"
              " platform recognition roster, not investment advice,"
              " and carries no monetary value")

NETWORK_LIBS = ("urllib", "requests", "socket", "http")
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")
ACCOUNTS = ("usr:carol", "usr:aaron", "usr:bob", "usr:dave",
            "usr:erin")
BAD_YEARS = (2026, True, "206", "20261", "abcd", "20-6", " 202",
             "".join(chr(c) for c in (0xFF12, 0xFF10, 0xFF12,
                                      0xFF16)), None)
ENV_KEYS = {"year", "yearbook", "certified_count", "board_size",
            "disclaimer"}
ROW_KEYS = {"board_rank", "account_id", "points", "item_id"}


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


def yearbook_rows(res):
    return [(r["board_rank"], r["account_id"], r["points"],
             r["item_id"]) for r in res["yearbook"]]


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
    """Deterministic anchor world: three behaviors, five accounts,
    board carol 12 / aaron 7 / bob 7 (tie, id asc) / dave 3, erin
    with zero earn rows (absent from the board)."""
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
    return led, cv, cl


def rebuild(led_path, cv_path, cfg):
    led = L.Ledger(led_path, cfg)
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)
    return led, cv, cl, hc


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-ybpersist-")
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

    # ---- instance 1: anchor world on the real product path ----
    led, cv, cl = build_world(led_path, cv_path, cfg)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)

    # -- AC-HYP1 pre-restart anchor pin + composition law -------
    r1 = hc.grant_year_honors("2026", 2, "civic-honor-2026")
    y26 = hc.honor_yearbook("2026")
    y27 = hc.honor_yearbook("2027")
    y26b = hc.honor_yearbook("2026")
    comp = hc.honor_certs("2026")["honors"]
    cert_rows = [h for h in comp if h["certified"]]
    comp_ok = (len(cert_rows) == len(y26["yearbook"])
               and all(h["account_id"] == r["account_id"]
                       and h["rank"] == r["board_rank"]
                       and h["points"] == r["points"]
                       and h["item_id"] == r["item_id"]
                       for h, r in zip(cert_rows,
                                       y26["yearbook"])))
    rows1 = yearbook_rows(y26)
    ok1 = (
        r1["granted"] == 2 and r1["already"] == 0
        and rows1 == [(1, "usr:carol", 12, "civic-honor-2026"),
                     (2, "usr:aaron", 7, "civic-honor-2026")]
        and set(y26.keys()) == ENV_KEYS
        and all(set(r.keys()) == ROW_KEYS for r in y26["yearbook"])
        and y26["certified_count"] == 2 and y26["board_size"] == 4
        and y26["year"] == "2026"
        and y26["disclaimer"] == DISCLAIMER
        and y27["yearbook"] == [] and y27["certified_count"] == 0
        and y27["board_size"] == 0
        and y26 == y26b and comp_ok)
    record("AC-HYP1", ok1, "anchor world pinned: board carol 12 /"
          " aaron 7 / bob 7 (tie, id asc) / dave 3 with erin a"
          " zero-row face; top-2 grant granted=%d already=%d;"
          " yearbook rows=%s with full item_id echo; envelope"
          " keys=%s certified_count=%d board_size=%d; honest"
          " empty 2027 roster=%s with zero counts; double-call"
          " byte-identical=%s; composition law: yearbook rows"
          " == honor_certs certified subset (%d rows, per-row"
          " rank/points/item_id equal=%s)"
          % (r1["granted"], r1["already"], rows1,
             sorted(ENV_KEYS), y26["certified_count"],
             y26["board_size"], y27["yearbook"], y26 == y26b,
             len(cert_rows), comp_ok))

    # -- AC-HYP2 three-piece cross-restart byte-identical -------
    snap26 = dump(y26)
    snap27 = dump(y27)
    cnt1 = table_counts(led_path, cv_path)
    cl.close()
    cv.close()
    led.close()
    led2, cv2, cl2, hc2 = rebuild(led_path, cv_path, cfg)
    y26r = hc2.honor_yearbook("2026")
    y27r = hc2.honor_yearbook("2027")
    ok2 = (dump(y26r) == snap26 and dump(y27r) == snap27
           and y26r == y26 and y27r == y27
           and table_counts(led_path, cv_path) == cnt1)
    record("AC-HYP2", ok2, "three-piece close (cl.close + cv.close"
          " + led.close - the honorcert face owns no storage and"
          " carries no close) -> Ledger + CivicPointsFace +"
          " CollectiblesFace + HonorCertFace rebuilt on the same"
          " two dbs with the same config: yearbook 2026 replays"
          " byte-identical to the pre-close snapshot (sha16=%s) and"
          " the honest empty 2027 roster replays byte-identical too"
          " (sha16=%s) - the certified-only filter, the board ranks"
          " and the certificate provenance all re-derive from the"
          " persisted civic.db earn rows and ledger.db certificate"
          " rows with zero in-memory drift; table counts frozen"
          " across the restart"
          % (sha16(dump(y26r)), sha16(dump(y27r))))

    # -- AC-HYP3 post-restart live continuation ------------------
    for i in range(4):
        cv2.earn_civic("usr:erin", "city-poll", "2026-10-02",
                       "e-poll-%d" % (i + 1))
    r3 = hc2.grant_year_honors("2026", 2, "civic-honor-2026")
    y26c = hc2.honor_yearbook("2026")
    rows3 = yearbook_rows(y26c)
    cv2.earn_civic("usr:dave", "city-poll", "2027-03-01", "d27-1")
    r3b = hc2.grant_year_honors("2027", 1, "civic-honor-2027")
    y27c = hc2.honor_yearbook("2027")
    y26d = hc2.honor_yearbook("2026")
    hon3 = [(h["rank"], h["account_id"], h["status"])
            for h in r3["honorees"]]
    ok3 = (
        r3["granted"] == 1 and r3["already"] == 1
        and hon3 == [(1, "usr:erin", "granted"),
                     (2, "usr:carol", "already")]
        and rows3 == [(1, "usr:erin", 20, "civic-honor-2026"),
                      (2, "usr:carol", 12, "civic-honor-2026"),
                      (3, "usr:aaron", 7, "civic-honor-2026")]
        and y26c["certified_count"] == 3
        and y26c["board_size"] == 5
        and "usr:bob" not in [r["account_id"]
                             for r in y26c["yearbook"]]
        and "usr:dave" not in [r["account_id"]
                               for r in y26c["yearbook"]]
        and r3b["granted"] == 1
        and r3b["honorees"][0]["account_id"] == "usr:dave"
        and yearbook_rows(y27c) == [(1, "usr:dave", 5,
                                     "civic-honor-2027")]
        and y27c["certified_count"] == 1 and y27c["board_size"] == 1
        and y26d == y26c)
    record("AC-HYP3", ok3, "post-restart continuation: erin earns"
          " four poll events on the reopened civic face so the"
          " board moves (erin 20 -> rank 1); the re-grant heals"
          " incrementally across the restart - %s (granted=%d"
          " already=%d: the top-2 slice covers exactly the new"
          " top two, the newcomer costs one certificate row and"
          " carol converges to already; aaron sits at rank 3,"
          " outside the slice, yet keeps his yearbook row at the"
          " new board rank - permanent-certificate law across the"
          " restart); the yearbook grows to %d rows %s with bob"
          " and dave honestly absent; dave opens the 2027"
          " namespace (grant top-1) so the 2027 roster carries"
          " exactly %s while the 2026 roster reads byte-stable"
          " across the 2027 grant (cross-read isolation)"
          % (hon3, r3["granted"], r3["already"], len(rows3),
             [(r[0], r[1]) for r in rows3],
             yearbook_rows(y27c)))

    # -- AC-HYP4 year gate survives the restart ------------------
    ccv = CountingCivic(cv2)
    guard = HC.HonorCertFace(ccv, cl2, DISCLAIMER)
    before4 = table_counts(led_path, cv_path)
    rejected = []
    raised = True
    for form in BAD_YEARS:
        ok_one, got = expect_hc_error(
            lambda f=form: guard.honor_yearbook(f), HC.E_HC_BAD_ARGS)
        if ok_one:
            rejected.append(got)
        else:
            rejected.append("NOT-RAISED(%s)" % got)
            raised = False
    ok4 = (raised and ccv.board_calls == 0
           and table_counts(led_path, cv_path) == before4)
    record("AC-HYP4", ok4, "year gate survives the restart: all"
          " %d bad year forms (%s) reject with E_HC_BAD_ARGS on the"
          " reopened instance with zero honor_board calls (the"
          " front-door gate rides the module law, nothing"
          " in-memory to lose); both-db table snapshots frozen"
          " across the probe batch"
          % (len(BAD_YEARS), "/".join(str(r) for r in rejected[:4])))

    # -- AC-HYP5 pure-read law + zero token counts ----------------
    before5 = table_counts(led_path, cv_path)
    reads = [dump(hc2.honor_yearbook("2026")),
             dump(hc2.honor_yearbook("2026")),
             dump(hc2.honor_yearbook("2027")),
             dump(hc2.honor_certs("2026"))]
    after5 = table_counts(led_path, cv_path)
    ok5 = (before5 == after5 and reads[0] == reads[1]
           and reads[3] != reads[0]
           and before5["ledger_tx"] == 0
           and before5["ledger_entries"] == 0)
    record("AC-HYP5", ok5, "pure-read law: the read battery"
          " (yearbook 2026 twice + yearbook 2027 + honor_certs"
          " 2026) leaves both-db table counts constant (%s) with"
          " ledger_tx=%d ledger_entries=%d across the whole"
          " window - certificates are platform awards and the"
          " yearbook is a zero-token derivation (counts-vs-tokens"
          " isolation); yearbook double-call byte-identical=%s"
          % (sorted(k + "=" + str(before5[k])
                    for k in ("collectibles", "civic_earns",
                              "ledger_tx")),
             before5["ledger_tx"], before5["ledger_entries"],
             reads[0] == reads[1]))

    # -- AC-HYP6 third instance + sha proofs + hygiene ------------
    cl2.close()
    cv2.close()
    led2.close()
    led3, cv3, cl3, hc3 = rebuild(led_path, cv_path, cfg)
    z26a = dump(hc3.honor_yearbook("2026"))
    z26b = dump(hc3.honor_yearbook("2026"))
    z27a = dump(hc3.honor_yearbook("2027"))
    z27b = dump(hc3.honor_yearbook("2027"))
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in NETWORK_LIBS)]
    method_src = inspect.getsource(
        HC.HonorCertFace.honor_yearbook)
    write_hits = [t for t in ("INSERT", "UPDATE ", "DELETE")
                  if t in method_src]
    sha_ok = all(
        sha16(io_read(os.path.join(BASE, name + ".py"))) == sha_b
        for name, sha_b in mod_sha_before.items())
    tmp_outside = (not os.path.realpath(tmp).startswith(repo_root)
                   and os.path.realpath(tmp).startswith(
                       os.path.realpath(tempfile.gettempdir())))
    ok6 = (z26a == z26b == dump(y26d)
           and z27a == z27b == dump(y27c)
           and sha16(io_read(cfg_path)) == cfg_sha_before
           and sha_ok and non_ascii == 0 and not net_imports
           and not write_hits and tmp_outside)
    record("AC-HYP6", ok6, "third instance: three-piece close ->"
          " rebuild once more on the same two dbs - yearbook 2026"
          " and 2027 read twice back-to-back byte-identical to the"
          " instance-2 terminal state and to each other (re-read"
          " purity; 2026 sha16=%s, 2027 sha16=%s); shipped files"
          " untouched (config.json + honorcert/civicpoints/"
          "collectibles sha16 stable=%s); suite source pure ASCII"
          " (%d non-ascii), zero network imports (%d hits);"
          " honor_yearbook method source carries zero write"
          " statements (hits=%s); world tmp outside repo (%s)"
          % (sha16(z26a), sha16(z27a), sha_ok, non_ascii,
             len(net_imports), write_hits or "none",
             "yes" if tmp_outside else "NO"))

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
