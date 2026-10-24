"""Grant slice-width axis on the already-granted honor world
(BigDomain R2074; canon = the explore-queue honorcert successor
row, criteria AC-HYGW1..AC-HYGW8 pre-registered in that row
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Suite-only round: the shipped grant_year_honors face is NOT
touched. R2029 pinned the same-width replay, the incremental heal
and the eight-form front-door battery across restarts. This window
pins the axis R2029 left open: the SLICE WIDTH on a world whose
certificates are already on the board - a narrower re-run
(top_n=1), a wider re-run (top_n=4), an out-of-range cap that must
CLAMP instead of reject (top_n=9 over a four-member board), the
first-grant item_id permanence under a replay with a different
item_id, the certificate row-set constancy around the gate battery
(the idempotency axis and the front-door rejects are orthogonal),
and the same width answers replayed byte-identical across two full
stack restarts.

Usage: python test_honorcert_grantwidthworld.py
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

DISCLAIMER = ("sandbox stand-in disclaimer: the annual honor"
              " certificate is a platform recognition award, not"
              " investment advice, and carries no monetary value")
NETWORK_LIBS = ("urllib", "requests", "socket", "http")
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")
ACCOUNTS = ("usr:alice", "usr:bob", "usr:carol", "usr:dave")
ITEM26 = "civic-honor-2026"
ITEM_ALT = "civic-honor-2026-alt"
FEST_REF = "festival:opening-2026"
FEST_ITEM = "fest-opening-medal"
HONOR_REF = "civic-honor:2026"
YEAR = "2026"
POLL = "city-poll"
CLEAN = "street-clean"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def table_counts(led_path, cv_path):
    out = {}
    conn = sqlite3.connect(led_path)
    out["collectibles"] = int(conn.execute(
        "SELECT COUNT(*) FROM collectibles").fetchone()[0])
    out["ledger_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    out["ledger_entries"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_entries").fetchone()[0])
    conn.close()
    cvconn = sqlite3.connect(cv_path)
    for table in CIVIC_TABLES:
        out[table] = int(cvconn.execute(
            "SELECT COUNT(*) FROM " + table).fetchone()[0])
    cvconn.close()
    return out


def honor_rows(led_path):
    """Certificate row SET in the civic-honor namespace, ordered
    account:item so a row-set comparison catches a silent rewrite
    that keeps the count."""
    conn = sqlite3.connect(led_path)
    rows = conn.execute(
        "SELECT account_id, item_id FROM collectibles WHERE"
        " event_ref = ? ORDER BY account_id", (HONOR_REF,)).fetchall()
    fest = int(conn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE event_ref = ?",
        (FEST_REF,)).fetchone()[0])
    conn.close()
    return rows, fest


def build_world(led_path, cv_path, cfg):
    """Positive-earn world with four board members and the two
    honor certificates issued by the anchor grant: the board is
    carol 12, alice 7, bob 7, dave 2 (points down, account id up)
    and one festival certificate stays isolated outside the honor
    namespace."""
    led = L.Ledger(led_path, cfg)
    for acct in ACCOUNTS:
        led.ensure_account(acct, census_avatar_id=acct[4:])
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    cv.register_behavior(POLL, "Community Poll", 5, 20, False)
    cv.register_behavior(CLEAN, "Street Cleanup", 2, 20, True)
    cv.earn_civic("usr:carol", POLL, "2026-10-01", "boot-cp1")
    cv.earn_civic("usr:carol", POLL, "2026-10-02", "boot-cp2")
    cv.earn_civic("usr:carol", CLEAN, "2026-10-03", "boot-cc1")
    cv.earn_civic("usr:alice", POLL, "2026-10-01", "boot-ap1")
    cv.earn_civic("usr:alice", CLEAN, "2026-10-02", "boot-ac1")
    cv.earn_civic("usr:bob", POLL, "2026-10-02", "boot-bp1")
    cv.earn_civic("usr:bob", CLEAN, "2026-10-03", "boot-bc1")
    cv.earn_civic("usr:dave", CLEAN, "2026-10-01", "boot-dc1")
    cl.issue_certificate("usr:dave", FEST_REF, FEST_ITEM)
    return led, cv, cl


def rebuild(led_path, cv_path, cfg):
    led = L.Ledger(led_path, cfg)
    cv = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl = CL.CollectiblesFace(led)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)
    return led, cv, cl, hc


class CountingCivic:
    """Read-counting wrapper proving the front-door rejects perform
    zero referenced honor_board calls (R2029 counting-civic
    precedent; per-instance counter)."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    def honor_board(self, year):
        self.calls += 1
        return self.inner.honor_board(year)


def expect_hc_error(func, *args):
    try:
        func(*args)
        return None
    except HC.HonorCertError as exc:
        return exc.code


def probe_battery(gate):
    """The R2029 eight-form front-door battery, replayed on the
    already-granted world (bad year, six bad top_n forms, blank
    item_id)."""
    return [
        expect_hc_error(gate.grant_year_honors, "20x6", 2,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, YEAR, True,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, YEAR, 0,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, YEAR, -1,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, YEAR, "2",
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, YEAR, 2.5,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, YEAR, None,
                        ITEM26),
        expect_hc_error(gate.grant_year_honors, YEAR, 2,
                        "   "),
    ]


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-grantwidth-")
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

    led, cv, cl = build_world(led_path, cv_path, cfg)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)
    counts0 = table_counts(led_path, cv_path)

    # -- instance 1: anchor grant, same-width replay --------------
    g_first = hc.grant_year_honors(YEAR, 2, ITEM26)
    g_replay = hc.grant_year_honors(YEAR, 2, ITEM26)
    rows_s0, fest0 = honor_rows(led_path)
    yb_s0 = dump(hc.honor_yearbook(YEAR))
    certs_s0 = dump(hc.honor_certs(YEAR))
    counts_s0 = table_counts(led_path, cv_path)

    ok_anchor = (
        g_first["granted"] == 2 and g_first["already"] == 0
        and [(h["rank"], h["account_id"], h["points"], h["status"])
             for h in g_first["honorees"]]
        == [(1, "usr:carol", 12, "granted"),
            (2, "usr:alice", 7, "granted")]
        and g_replay["granted"] == 0 and g_replay["already"] == 2
        and all(h["status"] == "already"
                for h in g_replay["honorees"]))
    ok_s0 = (rows_s0 == [("usr:alice", ITEM26),
                         ("usr:carol", ITEM26)]
             and fest0 == 1 and counts_s0["collectibles"] == 3
             and counts_s0["ledger_tx"] == 0)
    record("AC-HYGW1", ok_anchor and ok_s0,
           "already-granted anchor: first top-2 grant answers"
           " granted=2/already=0 with [(1,carol,12),(2,alice,7)]"
           " both granted and the same-width replay converges to"
           " already=2; certificate row SET S0 == %s (civic-honor"
           " namespace, item=%s), the festival row stays isolated"
           " (%d), collectibles=%d, ledger_tx=%d"
           % (rows_s0, ITEM26, fest0, counts_s0["collectibles"],
              counts_s0["ledger_tx"]))

    # -- AC-HYGW2 narrower slice ----------------------------------
    g_narrow = hc.grant_year_honors(YEAR, 1, ITEM26)
    rows_n, fest_n = honor_rows(led_path)
    counts_n = table_counts(led_path, cv_path)
    certs_n = json.loads(dump(hc.honor_certs(YEAR)))
    yb_n = dump(hc.honor_yearbook(YEAR))
    narrow_alice = [e for e in certs_n["honors"]
                    if e["account_id"] == "usr:alice"][0]
    ok_narrow = (
        g_narrow["granted"] == 0 and g_narrow["already"] == 1
        and [(h["rank"], h["account_id"], h["points"], h["status"])
             for h in g_narrow["honorees"]]
        == [(1, "usr:carol", 12, "already")]
        and rows_n == rows_s0 and fest_n == fest0
        and counts_n == counts_s0
        and narrow_alice["certified"] is True
        and narrow_alice["rank"] == 2
        and yb_n == yb_s0)
    record("AC-HYGW2", ok_narrow,
           "narrower slice law: re-running the grant with top_n=1 on"
           " the already-granted world answers granted=0/already=1"
           " with exactly [(1,carol,12,already)] - the slice simply"
           " narrows, zero new rows (row set == S0 %s, counts"
           " frozen at %d collectibles); alice leaves the slice but"
           " keeps certified=True at rank 2 and her yearbook row"
           " (certificate permanence), yearbook byte-identical=%s"
           % ("unchanged" if rows_n == rows_s0 else "DRIFTED",
              counts_n["collectibles"], yb_n == yb_s0))

    # -- AC-HYGW3 wider slice --------------------------------------
    g_wide = hc.grant_year_honors(YEAR, 4, ITEM26)
    rows_w, fest_w = honor_rows(led_path)
    counts_w = table_counts(led_path, cv_path)
    certs_w = json.loads(dump(hc.honor_certs(YEAR)))
    ok_wide = (
        g_wide["granted"] == 2 and g_wide["already"] == 2
        and [(h["rank"], h["account_id"], h["status"])
             for h in g_wide["honorees"]]
        == [(1, "usr:carol", "already"),
            (2, "usr:alice", "already"),
            (3, "usr:bob", "granted"),
            (4, "usr:dave", "granted")]
        and rows_w == [("usr:alice", ITEM26), ("usr:bob", ITEM26),
                       ("usr:carol", ITEM26), ("usr:dave", ITEM26)]
        and fest_w == 1
        and counts_w["collectibles"] == 5
        and counts_w["ledger_tx"] == 0
        and certs_w["certified_count"] == 4)
    record("AC-HYGW3", ok_wide,
           "wider slice law: top_n=4 grants exactly the two members"
           " the narrower runs never touched (bob and dave) while"
           " the two existing holders converge to already -"
           " row set == S0 + {bob,dave} (%d rows), collectibles=%d"
           " (4 honor + 1 festival), certified_count=%d, zero token"
           " movement"
           % (len(rows_w), counts_w["collectibles"],
              certs_w["certified_count"]))

    # -- AC-HYGW4 out-of-range cap clamps, never rejects -----------
    g_clamp = hc.grant_year_honors(YEAR, 9, ITEM26)
    rows_c, fest_c = honor_rows(led_path)
    counts_c = table_counts(led_path, cv_path)
    ok_clamp = (
        g_clamp["granted"] == 0 and g_clamp["already"] == 4
        and len(g_clamp["honorees"]) == 4
        and [h["account_id"] for h in g_clamp["honorees"]]
        == ["usr:carol", "usr:alice", "usr:bob", "usr:dave"]
        and rows_c == rows_w and fest_c == 1
        and counts_c == counts_w)
    record("AC-HYGW4", ok_clamp,
           "out-of-range cap clamp law: top_n=9 over a four-member"
           " board is NOT a cap-boundary reject - it answers"
           " already=4 with exactly board-length honorees %s (the"
           " top_n gate only rejects non-int/<1 forms; slicing"
           " clamps to the board), row set and counts frozen"
           % [h["account_id"] for h in g_clamp["honorees"]])

    # -- AC-HYGW5 first-grant item_id permanence -------------------
    g_alt = hc.grant_year_honors(YEAR, 2, ITEM_ALT)
    certs_alt = json.loads(dump(hc.honor_certs(YEAR)))
    rows_a, _fest_a = honor_rows(led_path)
    counts_a = table_counts(led_path, cv_path)
    ok_item = (
        g_alt["granted"] == 0 and g_alt["already"] == 2
        and all(e["item_id"] == ITEM26
                for e in certs_alt["honors"] if e["certified"])
        and rows_a == rows_w and counts_a == counts_w)
    record("AC-HYGW5", ok_item,
           "first-grant item_id permanence: a replay carrying a"
           " DIFFERENT item_id (%s) converges to already and every"
           " certified row still echoes the first-grant item %s -"
           " the duplicate law keeps the original award, zero rows"
           " rewritten (%s)"
           % (ITEM_ALT, ITEM26,
              "row set frozen" if rows_a == rows_w else "DRIFTED"))

    # -- AC-HYGW6 row-set constancy around the gate battery --------
    gate = HC.HonorCertFace(CountingCivic(cv), cl, DISCLAIMER)
    codes = probe_battery(gate)
    reject_calls = gate.civic.calls
    control = gate.grant_year_honors(YEAR, 4, ITEM26)
    control_calls = gate.civic.calls - reject_calls
    rows_g, fest_g = honor_rows(led_path)
    counts_g = table_counts(led_path, cv_path)
    all_bad = all(code == HC.E_HC_BAD_ARGS for code in codes)
    ok_gate = (all_bad and reject_calls == 0 and control_calls == 1
               and control["granted"] == 0
               and control["already"] == 4
               and rows_g == rows_w and fest_g == 1
               and counts_g == counts_w)
    record("AC-HYGW6", ok_gate,
           "row-set constancy x gate orthogonality: the eight-form"
           " front-door battery on the ALREADY-GRANTED world answers"
           " E_HC_BAD_ARGS 8/8 with zero honor_board calls (%d),"
           " every reject landing before the idempotency path; the"
           " wrapped valid control grant sees exactly one board read"
           " (%d) and converges to already=4; certificate row set"
           " and all table counts are byte-identical before and"
           " after the batch (%s)"
           % (reject_calls, control_calls,
              "frozen" if (rows_g == rows_w and counts_g == counts_c)
              else "DRIFTED"))

    yb_pre_close = dump(hc.honor_yearbook(YEAR))
    certs_pre_close = dump(hc.honor_certs(YEAR))

    # -- restart 1 -> instance 2 ----------------------------------
    cl.close()
    cv.close()
    led.close()
    led2, cv2, cl2, hc2 = rebuild(led_path, cv_path, cfg)
    yb2 = dump(hc2.honor_yearbook(YEAR))
    certs2 = dump(hc2.honor_certs(YEAR))
    g_n2 = hc2.grant_year_honors(YEAR, 1, ITEM26)
    g_w2 = hc2.grant_year_honors(YEAR, 4, ITEM26)
    g_c2 = hc2.grant_year_honors(YEAR, 9, ITEM26)
    rows2, fest2 = honor_rows(led_path)
    counts2 = table_counts(led_path, cv_path)
    ok_r2 = (
        yb2 == yb_pre_close and certs2 == certs_pre_close
        and (g_n2["granted"], g_n2["already"],
             [h["account_id"] for h in g_n2["honorees"]])
        == (0, 1, ["usr:carol"])
        and (g_w2["granted"], g_w2["already"],
             len(g_w2["honorees"])) == (0, 4, 4)
        and (g_c2["granted"], g_c2["already"],
             len(g_c2["honorees"])) == (0, 4, 4)
        and rows2 == rows_w and fest2 == 1
        and counts2 == counts_w)
    # -- restart 2 -> instance 3: stability + pure reads -----------
    cl2.close()
    cv2.close()
    led2.close()
    led3, cv3, cl3, hc3 = rebuild(led_path, cv_path, cfg)
    g_n3 = hc3.grant_year_honors(YEAR, 1, ITEM26)
    g_w3 = hc3.grant_year_honors(YEAR, 9, ITEM26)
    yb3 = dump(hc3.honor_yearbook(YEAR))
    certs3 = dump(hc3.honor_certs(YEAR))
    storm = []
    for _ in range(2):
        storm.append(dump(hc3.honor_yearbook(YEAR)))
        storm.append(dump(hc3.honor_certs(YEAR)))
    rows3, fest3 = honor_rows(led_path)
    counts3 = table_counts(led_path, cv_path)
    ok_r3 = (
        (g_n3["granted"], g_n3["already"],
         [h["account_id"] for h in g_n3["honorees"]])
        == (0, 1, ["usr:carol"])
        and (g_w3["granted"], g_w3["already"],
             len(g_w3["honorees"])) == (0, 4, 4)
        and yb3 == yb2 == yb_pre_close
        and certs3 == certs2
        and storm[0] == yb3 and storm[1] == certs3
        and storm[2] == storm[0] and storm[3] == storm[1]
        and rows3 == rows_w and fest3 == 1
        and counts3 == counts_w)
    pinned = {"civic_behaviors": 2, "civic_earns": 8,
              "civic_rewards": 0, "civic_redeems": 0,
              "civic_grants": 0, "collectibles": 5,
              "ledger_tx": 0, "ledger_entries": 0}
    ok_pinned = all(counts3[k] == v for k, v in pinned.items())
    record("AC-HYGW7", ok_r2 and ok_r3 and ok_pinned,
           "cross-restart width axis (two full-stack restarts):"
           " instance 2 replays the narrow/wide/clamp trio"
           " identically (top_n=1 -> already=1 [carol]; top_n=4 ->"
           " already=4; top_n=9 -> already=4 clamped) and instance"
           " 3 replays both width forms identically, the row set"
           " stays %d rows with the festival row isolated, both"
           " read faces replay the pre-close snapshots"
           " byte-identical across BOTH restarts (yearbook=%s,"
           " certs=%s), and the read storm replays byte-identical"
           " twice; the window freezes at the pinned counts"
           " (civic_earns=%d, collectibles=%d = 4 honor + 1"
           " festival, ledger_tx=%d, ledger_entries=%d) with zero"
           " token movement end to end (%s)"
           % (len(rows2), yb2 == yb_pre_close,
              certs2 == certs_pre_close,
              counts3["civic_earns"], counts3["collectibles"],
              counts3["ledger_tx"], counts3["ledger_entries"],
              "pinned" if ok_pinned else "DRIFTED"))


    # -- hygiene + delivery ---------------------------------------
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in NETWORK_LIBS)]
    method_src = inspect.getsource(
        HC.HonorCertFace.grant_year_honors)
    write_hits = [t for t in ("INSERT", "UPDATE ", "DELETE")
                  if t in method_src]
    sha_ok = all(
        sha16(io_read(os.path.join(BASE, name + ".py"))) == sha_b
        for name, sha_b in mod_sha_before.items())
    tmp_outside = (not os.path.realpath(tmp).startswith(repo_root)
                   and os.path.realpath(tmp).startswith(
                       os.path.realpath(tempfile.gettempdir())))
    prior = len(RESULTS)
    ok_hyg = (sha16(io_read(cfg_path)) == cfg_sha_before
              and sha_ok and non_ascii == 0 and not net_imports
              and not write_hits and tmp_outside and prior == 7)
    record("AC-HYGW8", ok_hyg,
           "hygiene: shipped files untouched (config.json +"
           " honorcert/civicpoints/collectibles sha16 stable=%s);"
           " suite source pure ASCII (%d non-ascii chars), zero"
           " network imports (%d hits); grant_year_honors carries"
           " zero write statements (hits=%s); world tmp outside the"
           " repo (%s); criteria registered=%d"
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