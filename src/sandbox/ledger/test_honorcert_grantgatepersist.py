"""Grant idempotency axis + top_n gate-family cross-restart
same-code window for the annual honor certificate grant face
(BigDomain R2029; canon = the explore-queue grant idempotency
axis claim row, criteria AC-HYGG1..AC-HYGG7 pre-registered in
that row before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero on
any FAIL.

Suite-only round: the shipped grant_year_honors face is NOT
touched. The window pins the two faces the zero-earn boundary
gate suite (R2028) left open on a POSITIVE-earn world: (a) the
already-granted idempotency axis - a replayed grant converges
every honoree to "already" with zero new rows, and that
convergence survives both full-stack restarts because the
duplicate law lives in the collectibles domain; a post-restart
new-earner incremental heal re-grants exactly the newcomer while a
demoted member keeps the yearbook row (certificate permanence
x on-board derivation); (b) the top_n cap-boundary probe family
- the eight front-door rejects (bad year, six bad top_n forms,
blank item_id) answer with the identical code vector on the
pre-close instance and on both restart instances, each reject
happening before any referenced honor_board call lands.

Usage: python test_honorcert_grantgatepersist.py
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
ACCOUNTS = ("usr:alice", "usr:bob", "usr:carol", "usr:dave",
            "usr:erin")
ITEM26 = "civic-honor-2026"
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


def build_world(led_path, cv_path, cfg):
    """Positive-earn world (R2025 posture): the ledger and
    collectibles domains hold data - five ensured accounts, two
    registered behaviors, four accounts with 2026 earn rows and
    one festival-namespace certificate - and the first grant
    lands two honor certificates before any restart. The
    idempotency axis needs real grants on the board, so this
    world is the zero-earn boundary's positive twin."""
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
    """Read-counting wrapper proving the front-door rejects
    perform zero referenced honor_board calls (R2025 AC-HYCP4
    counting-civic precedent; per-instance counter)."""

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
    """The 8-probe front-door rejection battery: one bad-year
    probe, six bad top_n cap-boundary forms and one blank
    item_id probe, every one expected to raise E_HC_BAD_ARGS
    before any referenced read lands."""
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


def run_gate_face(cv, cl):
    """Fresh CountingCivic-wrapped gate + the 8-probe battery +
    the one valid control grant. Returns (codes, reject_calls,
    control_calls, control_receipt)."""
    gate = HC.HonorCertFace(CountingCivic(cv), cl, DISCLAIMER)
    codes = probe_battery(gate)
    reject_calls = gate.civic.calls
    control = gate.grant_year_honors(YEAR, 2, ITEM26)
    control_calls = gate.civic.calls - reject_calls
    return codes, reject_calls, control_calls, control


def honor_cross(led_path):
    """Manual SQL cross: the civic-honor namespace rows and the
    festival isolation row straight from the collectibles
    table."""
    conn = sqlite3.connect(led_path)
    honor = [r[0] for r in conn.execute(
        "SELECT account_id FROM collectibles WHERE event_ref ="
        " ?", (HONOR_REF,)).fetchall()]
    fest = int(conn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE event_ref = ?",
        (FEST_REF,)).fetchone()[0])
    total = int(conn.execute(
        "SELECT COUNT(*) FROM collectibles").fetchone()[0])
    conn.close()
    return honor, fest, total


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-grantgate-")
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

    # -- instance 1: first grant, idempotent replay, read pin,
    #    probe battery, control grant ---------------------------
    g_first = hc.grant_year_honors(YEAR, 2, ITEM26)
    e_first = dump(g_first)
    g_replay1 = hc.grant_year_honors(YEAR, 2, ITEM26)
    e_replay1 = dump(g_replay1)
    yb1 = dump(hc.honor_yearbook(YEAR))
    certs1 = dump(hc.honor_certs(YEAR))
    counts_a = table_counts(led_path, cv_path)
    codes1, rej1, ctl1, ctrl1 = run_gate_face(cv, cl)
    counts_b = table_counts(led_path, cv_path)
    honor1, fest1, total1 = honor_cross(led_path)

    # -- AC-HYGG1 instance-1 grant axis anchor ---------------------
    ok_first = (g_first["granted"] == 2 and g_first["already"] == 0
                and [(h["rank"], h["account_id"],
                      h["status"]) for h in
                     g_first["honorees"]]
                == [(1, "usr:carol", "granted"),
                    (2, "usr:alice", "granted")])
    ok_replay = (g_replay1["granted"] == 0
                 and g_replay1["already"] == 2
                 and [(h["rank"], h["account_id"], h["points"],
                       h["status"]) for h in
                      g_replay1["honorees"]]
                 == [(1, "usr:carol", 12, "already"),
                     (2, "usr:alice", 7, "already")])
    ok_ctrl = (ctrl1["granted"] == 0 and ctrl1["already"] == 2)
    ok_sql = (sorted(honor1) == ["usr:alice", "usr:carol"]
              and fest1 == 1 and total1 == 3)
    ok_tokens = (counts_a["ledger_tx"] == 0
                 and counts_a["ledger_entries"] == 0
                 and counts_a["collectibles"] == 3)
    ok1 = (ok_first and ok_replay and ok_sql and ok_tokens
           and ok_ctrl)
    record("AC-HYGG1", ok1, "instance-1 grant axis anchor on the"
          " positive-earn world: first grant top-2 answers"
          " granted=2/already=0 with honorees [(1,carol),"
          "(2,alice)] both granted; the same-window replay"
          " answers granted=0/already=2 with every honoree"
          " converged to 'already' (rank/points frozen"
          " byte-for-byte - the already-granted idempotency"
          " gate pinned single-instance); manual SQL cross:"
          " civic-honor:2026 rows==%d exactly {carol,alice}, the"
          " festival certificate stays isolated (festival rows"
          "=%d, total=%d); zero token movement (ledger_tx=%d,"
          " ledger_entries=%d); the wrapped control grant is"
          " idempotent too (%s)"
          % (len(honor1), fest1, total1,
             counts_a["ledger_tx"], counts_a["ledger_entries"],
             "already=2" if ok_ctrl else "DRIFTED"))

    # -- restart 1 -> instance 2 ----------------------------------
    cl.close()
    cv.close()
    led.close()
    led2, cv2, cl2, hc2 = rebuild(led_path, cv_path, cfg)
    yb2_pre = dump(hc2.honor_yearbook(YEAR))
    g_cross2 = hc2.grant_year_honors(YEAR, 2, ITEM26)
    certs2_pre = dump(hc2.honor_certs(YEAR))
    counts_c = table_counts(led_path, cv_path)
    honor2, fest2, total2 = honor_cross(led_path)

    # -- AC-HYGG2 cross-restart idempotency axis -------------------
    ok_rc = (g_cross2["granted"] == 0
             and g_cross2["already"] == 2
             and all(h["status"] == "already"
                     for h in g_cross2["honorees"]))
    ok_counts = (counts_c["collectibles"] == 3
                 and counts_c["ledger_tx"] == 0)
    ok_reads = (yb2_pre == yb1 and certs2_pre == certs1)
    ok2 = (ok_rc and ok_counts and ok_reads and total2 == 3
           and sorted(honor2) == ["usr:alice", "usr:carol"]
           and fest2 == 1)
    record("AC-HYGG2", ok2, "cross-restart idempotency axis: the"
          " three-piece close (cl -> cv -> led) and same-path"
          " same-config rebuild replay the top-2 grant with"
          " granted=%d/already=%d and every honoree 'already'"
          " (%s) - zero new certificate rows across the restart"
          " (collectibles frozen at %d, civic-honor rows==%d,"
          " festival isolated at %d); the post-restart yearbook"
          " and honor_certs reads replay the pre-close snapshots"
          " byte-identical (%s - derived faces carry zero"
          " in-memory drift)"
          % (g_cross2["granted"], g_cross2["already"],
             "converged" if ok_rc else "DRIFTED",
             counts_c["collectibles"], len(honor2), fest2,
             "byte-equal" if ok_reads else "DRIFTED"))

    # -- instance 2: incremental heal + cert permanence -------------
    for idx in range(4):
        cv2.earn_civic("usr:erin", POLL, "2026-10-05",
                       "boot-ep%d" % idx)
    g_heal2 = hc2.grant_year_honors(YEAR, 2, ITEM26)
    certs2_post = dump(hc2.honor_certs(YEAR))
    yb2 = dump(hc2.honor_yearbook(YEAR))
    codes2, rej2, ctl2, ctrl2 = run_gate_face(cv2, cl2)
    counts_d = table_counts(led_path, cv_path)

    # -- AC-HYGG3 incremental heal + permanence-on-board ------------
    ok_heal = (g_heal2["granted"] == 1
               and g_heal2["already"] == 1
               and [(h["rank"], h["account_id"],
                     h["status"]) for h in g_heal2["honorees"]]
               == [(1, "usr:erin", "granted"),
                   (2, "usr:carol", "already")])
    yb_obj = json.loads(yb2)
    ok_yb = ([(r["board_rank"], r["account_id"], r["points"])
              for r in yb_obj["yearbook"]]
             == [(1, "usr:erin", 20), (2, "usr:carol", 12),
                 (3, "usr:alice", 7)]
             and yb_obj["certified_count"] == 3
             and yb_obj["board_size"] == 5)
    certs_obj = json.loads(certs2_post)
    ok_persist = ([e["account_id"] for e in certs_obj["honors"]
                   if e["certified"]]
                  == ["usr:erin", "usr:carol", "usr:alice"]
                  and all(e["item_id"] == ITEM26
                          for e in certs_obj["honors"]
                          if e["certified"]))
    ok_counts2 = (counts_d["civic_earns"] == 12
                  and counts_d["collectibles"] == 4
                  and counts_d["ledger_tx"] == 0)
    ok3 = (ok_heal and ok_yb and ok_persist and ok_counts2)
    record("AC-HYGG3", ok3, "post-restart incremental heal +"
          " certificate permanence: instance 2 earns erin 4 poll"
          " rows (20 points, board head), the re-grant answers"
          " granted=1/already=1 with honorees [(1,erin,granted),"
          "(2,carol,already)] - the interrupted-batch heal law"
          " survives the restart; alice falls out of the top-2"
          " slice yet keeps her certified flag and her yearbook"
          " row at board_rank=3 (certificate permanence x"
          " on-board derivation - the R1979 honest-derivation"
          " limit on its positive face); pinned yearbook ="
          " [(1,erin,20),(2,carol,12),(3,alice,7)] with"
          " certified_count=3/board_size=5 and the tie law keeps"
          " bob behind alice (id-ascending, zero insertion"
          " keys); earns==12, collectibles==4, zero token"
          " movement (%s)"
          % ("frozen" if ok_counts2 else "DRIFTED"))

    # -- restart 2 -> instance 3 ----------------------------------
    cl2.close()
    cv2.close()
    led2.close()
    led3, cv3, cl3, hc3 = rebuild(led_path, cv_path, cfg)
    yb3 = dump(hc3.honor_yearbook(YEAR))
    certs3 = dump(hc3.honor_certs(YEAR))
    g_replay3 = hc3.grant_year_honors(YEAR, 2, ITEM26)
    codes3, rej3, ctl3, ctrl3 = run_gate_face(cv3, cl3)
    counts_e = table_counts(led_path, cv_path)

    # -- AC-HYGG4 top_n gate family same-code across restarts ------
    base_vec = codes1
    same12 = codes2 == base_vec
    same13 = codes3 == base_vec
    all_bad = all(code == HC.E_HC_BAD_ARGS for code in base_vec)
    ok_wrappers = (rej1 == 0 and rej2 == 0 and rej3 == 0
                   and ctl1 == 1 and ctl2 == 1 and ctl3 == 1)
    ok_probes_clean = (counts_b == counts_a and counts_e
                       == counts_d)
    ok4 = (all_bad and same12 and same13 and ok_wrappers
           and ok_probes_clean)
    record("AC-HYGG4", ok4, "top_n cap-boundary gate family"
          " cross-restart same-code: the 8-probe battery (bad"
          " year '20x6'; top_n bool/zero/negative/str/float/"
          "None - the six cap-boundary forms; blank item_id)"
          " rejects E_HC_BAD_ARGS on all three instances with the"
          " IDENTICAL code vector (%s 8/8, restart-2 %s); the"
          " CountingCivic wrapper sees zero honor_board calls"
          " across every reject batch (%d/%d/%d) and exactly one"
          " call on each valid control grant (%d/%d/%d -"
          " per-instance counter stays live across restarts);"
          " every probe batch leaves the table counts identical"
          " (%s) - rejects happen before any referenced read"
          % ("byte-equal" if same12 else "DRIFTED",
             "byte-equal" if same13 else "DRIFTED",
             rej1, rej2, rej3, ctl1, ctl2, ctl3,
             "frozen" if ok_probes_clean else "DRIFTED"))

    # -- AC-HYGG5 second-restart stability --------------------------
    ok_replay3 = (g_replay3["granted"] == 0
                  and g_replay3["already"] == 2
                  and all(h["status"] == "already"
                          for h in g_replay3["honorees"]))
    ok_reads3 = (yb3 == yb2 and certs3 == certs2_post)
    ok_counts3 = (counts_e["collectibles"] == 4
                  and counts_e["ledger_tx"] == 0)
    ok5 = (ok_replay3 and ok_reads3 and ok_counts3)
    record("AC-HYGG5", ok5, "second-restart stability: instance"
          " 3 replays the instance-2 final yearbook and"
          " honor_certs snapshots byte-identical (%s) and the"
          " top-2 grant answers granted=0/already=2 again"
          " (idempotency carries zero drift across the second"
          " full-stack restart); collectibles stay at %d rows"
          " with zero token movement"
          % ("byte-equal" if ok_reads3 else "DRIFTED",
             counts_e["collectibles"]))

    # -- AC-HYGG6 pure-read law + zero-token account ----------------
    storm = []
    for _ in range(2):
        storm.append(dump(hc3.honor_yearbook(YEAR)))
        storm.append(dump(hc3.honor_certs(YEAR)))
    counts_f = table_counts(led_path, cv_path)
    pinned_final = {"civic_behaviors": 2, "civic_earns": 12,
                    "civic_rewards": 0, "civic_redeems": 0,
                    "civic_grants": 0, "collectibles": 4,
                    "ledger_tx": 0, "ledger_entries": 0}
    ok_pinned = all(counts_f[k] == v
                    for k, v in pinned_final.items())
    ok_storm = (storm[0] == yb3 and storm[1] == certs3
                and storm[2] == storm[0] and storm[3] == storm[1])
    ok6 = (ok_pinned and ok_storm and counts_f == counts_e)
    record("AC-HYGG6", ok6, "pure-read law + zero-token account:"
          " the instance-3 read storm replays both faces"
          " byte-identical across two rounds (replay purity); the"
          " whole window freezes at the pinned final counts"
          " (civic_earns=%d, civic_behaviors=%d, zero reward/"
          " redeem/grant rows, collectibles=%d = 3 honor + 1"
          " festival, ledger_tx=%d, ledger_entries=%d) - the"
          " ensure, earn, reject and certificate axes all bypass"
          " the token ledger end to end (%s)"
          % (counts_f["civic_earns"], counts_f["civic_behaviors"],
             counts_f["collectibles"], counts_f["ledger_tx"],
             counts_f["ledger_entries"],
             "pinned" if ok_pinned else "DRIFTED"))

    # -- AC-HYGG7 hygiene + sha proofs + delivery --------------------
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
    ok7 = (sha16(io_read(cfg_path)) == cfg_sha_before
           and sha_ok and non_ascii == 0 and not net_imports
           and not write_hits and tmp_outside and prior == 6)
    record("AC-HYGG7", ok7, "hygiene: shipped files untouched"
          " (config.json + honorcert/civicpoints/collectibles"
          " sha16 stable=%s); suite source pure ASCII (%d"
          " non-ascii chars), zero network imports (%d hits);"
          " the grant_year_honors method source carries zero"
          " write statements (hits=%s - every write happens"
          " inside the referenced collectibles transaction);"
          " world tmp outside repo (%s); criteria registered=%d"
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
