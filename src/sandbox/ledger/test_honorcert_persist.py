"""Cross-restart persistence window for the annual civic honor
certificate orchestration face (BigDomain R1948; the honorcert
seat of the R1886 persist family - the R1943-seeded row, criteria
AC-HCP1..AC-HCP7 pre-registered in the R1948 tech.md claim row
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Three-piece restart world on the real product path: the honorcert
face is a pure orchestration layer that owns no storage (zero
close, zero own db), so its persistence semantics live in two
shipped stores - the civic.db honor-board rows and the ledger.db
collectibles certificate rows. Anchor world (five accounts, three
behaviors, deterministic board carol 12 / aaron 7 / bob 7 with
the tie broken by account id / dave 3, erin a zero-row face; the
top-3 grant lands three certificate rows with zero token rows)
-> close all three pieces -> reopen the same two dbs -> read
battery byte-identical replay -> constructor and arg gates survive
the restart with zero referenced-face calls -> post-restart
real-path continuation (erin earns four poll events so the board
moves; the re-grant heals incrementally - erin granted, carol and
aaron already - the interrupted-batch heal law live across a
restart; bob drops out of the top slice yet keeps his certified
flag - the permanent-certificate law; dave earns in 2027 so a
second event namespace opens) -> frozen rows and replay gates ->
pure-read law -> third instance stability.

Usage: python test_honorcert_persist.py
"""

import hashlib
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

NETWORK_LIBS = ("urllib", "requests", "socket", "http")
CIVIC_TABLES = ("civic_behaviors", "civic_earns", "civic_rewards",
                "civic_redeems", "civic_grants")
ACCOUNTS = ("usr:carol", "usr:aaron", "usr:bob", "usr:dave",
            "usr:erin")


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


def evidence_digest(bat):
    return sha16("\n".join(bat[k] if isinstance(bat[k], str)
                          else str(bat[k])
                          for k in sorted(bat)))


class CountingCivic(object):
    """Delegating wrapper counting honor_board calls (zero-call
    proof for the bad-args faces)."""

    def __init__(self, inner):
        self.inner = inner
        self.board_calls = 0

    def honor_board(self, year):
        self.board_calls += 1
        return self.inner.honor_board(year)


class CountingCollectibles(object):
    """Delegating wrapper counting award-verb and collection calls
    (zero-call proof for the bad-args faces)."""

    def __init__(self, inner):
        self.inner = inner
        self.issue_calls = 0
        self.collection_calls = 0

    def issue_certificate(self, account_id, event_ref, item_id):
        self.issue_calls += 1
        return self.inner.issue_certificate(account_id, event_ref,
                                            item_id)

    def collection(self, account_id):
        self.collection_calls += 1
        return self.inner.collection(account_id)


class _Bare(object):
    pass


def read_battery(hc, cv, cl):
    bat = {
        "certs_2026": dump(hc.honor_certs("2026")),
        "certs_2027": dump(hc.honor_certs("2027")),
        "certs_2028": dump(hc.honor_certs("2028")),
        "board_2026": dump(cv.honor_board("2026")),
    }
    for acct in ACCOUNTS:
        bat["col_" + acct[4:]] = dump(cl.collection(acct))
    return bat


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


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


def full_rows(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


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
    cv.earn_civic("usr:bob", "street-clean", "2026-10-01", "b-sc-1")
    cv.earn_civic("usr:dave", "harvest", "2026-10-01", "d-hv-1")
    return led, cv, cl


def run_gate_probes(cv, cl, label):
    """Constructor rejects + arg rejects on counting wrappers.
    Returns (lines, all_ok, wrappers) - zero referenced-face calls
    is asserted by the caller via the wrappers."""
    lines = []
    ok_all = True
    ok_none_c, code_none_c = expect_hc_error(
        lambda: HC.HonorCertFace(None, cl, DISCLAIMER),
        HC.E_HC_BAD_ARGS)
    ok_none_l, code_none_l = expect_hc_error(
        lambda: HC.HonorCertFace(cv, None, DISCLAIMER),
        HC.E_HC_BAD_ARGS)
    ok_attr_c, code_attr_c = expect_hc_error(
        lambda: HC.HonorCertFace(_Bare(), cl, DISCLAIMER),
        HC.E_HC_BAD_ARGS)
    ok_attr_l, code_attr_l = expect_hc_error(
        lambda: HC.HonorCertFace(cv, _Bare(), DISCLAIMER),
        HC.E_HC_BAD_ARGS)
    ok_disc, code_disc = expect_hc_error(
        lambda: HC.HonorCertFace(cv, cl, "  "),
        HC.E_HC_NO_DISCLAIMER)
    ctor_ok = (ok_none_c and ok_none_l and ok_attr_c and ok_attr_l
               and ok_disc
               and code_disc == HC.E_HC_NO_DISCLAIMER)
    lines.append("ctor %s/%s/%s/%s disc=%s" % (
        code_none_c, code_none_l, code_attr_c, code_attr_l,
        code_disc))
    ok_all = ok_all and ctor_ok

    ccv = CountingCivic(cv)
    ccl = CountingCollectibles(cl)
    guard = HC.HonorCertFace(ccv, ccl, DISCLAIMER)
    year_bad = []
    for form in (2026, "206", None):
        ok_one, got = expect_hc_error(
            lambda f=form: guard.grant_year_honors(f, 2, "x"),
            HC.E_HC_BAD_ARGS)
        year_bad.append(got if ok_one else "NOT-RAISED(%s)" % got)
        ok_all = ok_all and ok_one
    top_bad = []
    for form in (True, "2", 0):
        ok_one, got = expect_hc_error(
            lambda f=form: guard.grant_year_honors("2026", f, "x"),
            HC.E_HC_BAD_ARGS)
        top_bad.append(got if ok_one else "NOT-RAISED(%s)" % got)
        ok_all = ok_all and ok_one
    item_bad = []
    for form in ("", "   ", None):
        ok_one, got = expect_hc_error(
            lambda f=form: guard.grant_year_honors("2026", 2, f),
            HC.E_HC_BAD_ARGS)
        item_bad.append(got if ok_one else "NOT-RAISED(%s)" % got)
        ok_all = ok_all and ok_one
    read_bad = []
    for form in (2026, "206", None):
        ok_one, got = expect_hc_error(
            lambda f=form: guard.honor_certs(f), HC.E_HC_BAD_ARGS)
        read_bad.append(got if ok_one else "NOT-RAISED(%s)" % got)
        ok_all = ok_all and ok_one
    lines.append("year %s; top %s; item %s; read-year %s"
                 % ("/".join(year_bad), "/".join(top_bad),
                    "/".join(item_bad), "/".join(read_bad)))
    zero_calls = (ccv.board_calls == 0 and ccl.issue_calls == 0
                  and ccl.collection_calls == 0)
    lines.append("referenced-face calls board=%d issue=%d"
                 " collection=%d" % (ccv.board_calls,
                                     ccl.issue_calls,
                                     ccl.collection_calls))
    return lines, ok_all and zero_calls, (ccv, ccl)


def main():
    tmp = tempfile.mkdtemp(prefix="honorcert-persist-")
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
    led = None
    cv = None
    cl = None
    led, cv, cl = build_world(led_path, cv_path, cfg)
    hc = HC.HonorCertFace(cv, cl, DISCLAIMER)

    # -- AC-HCP1 anchor world + gate probes, zero drift ----------
    r1 = hc.grant_year_honors("2026", 3, "civic-honor-2026")
    r1b = hc.grant_year_honors("2026", 3, "civic-honor-2026")
    hon1 = [(h["rank"], h["account_id"], h["points"], h["status"])
            for h in r1["honorees"]]
    bat1 = read_battery(hc, cv, cl)
    cnt1 = table_counts(led_path, cv_path)
    snap_cl = full_rows(
        led_path, "SELECT * FROM collectibles ORDER BY cl_id")
    snap_earn = full_rows(
        cv_path, "SELECT * FROM civic_earns ORDER BY rowid")
    probe_lines1, ok_probes1, _wr1 = run_gate_probes(cv, cl, "i1")
    cert_2026 = full_rows(
        led_path, "SELECT account_id, item_id FROM collectibles"
        " WHERE kind = 'certificate' AND event_ref ="
        " 'civic-honor:2026' ORDER BY account_id")
    ok_world = (
        r1["granted"] == 3 and r1["already"] == 0
        and hon1 == [(1, "usr:carol", 12, "granted"),
                     (2, "usr:aaron", 7, "granted"),
                     (3, "usr:bob", 7, "granted")]
        and r1b["granted"] == 0 and r1b["already"] == 3
        and all(h["status"] == "already" for h in r1b["honorees"])
        and cnt1["collectibles"] == 3 and cnt1["ledger_tx"] == 0
        and cnt1["ledger_entries"] == 0
        and cnt1["civic_earns"] == 8 and cnt1["civic_behaviors"] == 3
        and cert_2026 == [("usr:aaron", "civic-honor-2026"),
                          ("usr:bob", "civic-honor-2026"),
                          ("usr:carol", "civic-honor-2026")]
        and '"certified_count": 3' in bat1["certs_2026"]
        and '"certified_count": 0' in bat1["certs_2027"]
        and '"honors": []' in bat1["certs_2028"])
    ok_drift1 = (table_counts(led_path, cv_path) == cnt1
                 and read_battery(hc, cv, cl) == bat1)
    ok1 = ok_world and ok_probes1 and ok_drift1
    record("AC-HCP1", ok1, "anchor world pinned: deterministic"
          " board carol 12 / aaron 7 / bob 7 (tie, id asc) / dave"
          " 3 with erin a zero-row face; top-3 grant = %s"
          " (granted=%d), idempotent replay granted=%d already=%d"
          " with zero new rows; three certificate rows land in"
          " ledger.db with ledger_tx=%d ledger_entries=%d (zero"
          " token law - counts stay counts); battery 9 faces"
          " snapshotted (certs 2026/2027/2028 + board + five"
          " collections), civic tables earns=%d behaviors=%d;"
          " gate probes (%s) all rejected with zero referenced-"
          " face calls; counts and battery frozen across the"
          " probe batch; digest=%s"
          % (hon1, r1["granted"], r1b["granted"], r1b["already"],
             cnt1["ledger_tx"], cnt1["ledger_entries"],
             cnt1["civic_earns"], cnt1["civic_behaviors"],
             "; ".join(probe_lines1), evidence_digest(bat1)))

    # -- AC-HCP2 cross-restart byte-identical replay -------------
    cl.close()
    cv.close()
    led.close()
    led2 = L.Ledger(led_path, cfg)
    cv2 = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl2 = CL.CollectiblesFace(led2)
    hc2 = HC.HonorCertFace(cv2, cl2, DISCLAIMER)
    bat2 = read_battery(hc2, cv2, cl2)
    diffs2 = battery_diffs(bat1, bat2)
    ok2 = not diffs2
    record("AC-HCP2", ok2, "three-piece close (cl.close + cv.close"
          " + led.close - the honorcert face itself owns no storage"
          " and carries no close) -> Ledger + CivicPointsFace +"
          " CollectiblesFace reopened on the same two dbs with the"
          " same config and a fresh HonorCertFace: the read battery"
          " (certs 2026/2027/2028 + board + five collections)"
          " replays byte-identical to the pre-close snapshot"
          " (diffs=%s) - the certified flags, the honor order and"
          " the collection provenance all re-derive from the"
          " persisted civic.db earn rows and ledger.db certificate"
          " rows with zero in-memory drift; digest=%s"
          % (diffs2 or "none", evidence_digest(bat2)))

    # -- AC-HCP3 gates survive the restart, zero drift ----------
    probe_lines2, ok_probes2, _wr2 = run_gate_probes(cv2, cl2, "i2")
    ok_drift2 = (table_counts(led_path, cv_path) == cnt1
                 and read_battery(hc2, cv2, cl2) == bat2)
    ok3 = ok_probes2 and ok_drift2
    record("AC-HCP3", ok3, "restart-surviving gates: constructor"
          " rejects (None faces, missing-attr faces, empty"
          " disclaimer) and arg gates (bad years, bad top_n,"
          " empty item_id, bad read years) all reject with the"
          " identical codes on instance 2 (%s); zero"
          " referenced-face calls across the probe batch (the"
          " year gate rides the module law, the constructor gates"
          " ride the attr checks - nothing in-memory to lose);"
          " counts and battery frozen across the probe batch"
          % "; ".join(probe_lines2))

    # -- AC-HCP4 post-restart real-path continuation --------------
    for i in range(4):
        cv2.earn_civic("usr:erin", "city-poll", "2026-10-02",
                       "e-poll-%d" % (i + 1))
    r4 = hc2.grant_year_honors("2026", 3, "civic-honor-2026")
    hon4 = [(h["rank"], h["account_id"], h["status"])
            for h in r4["honorees"]]
    cv2.earn_civic("usr:dave", "city-poll", "2027-03-01", "d27-1")
    r4b = hc2.grant_year_honors("2027", 1, "civic-honor-2027")
    # terminal battery of the continuation (post 2027 grant) - the
    # AC-HCP5 replay probes must freeze against THIS state, not the
    # pre-2027 one (first-run erratum: snapshot point corrected
    # same round, R1883 family; assertion target, zero product
    # defect).
    bat4 = read_battery(hc2, cv2, cl2)
    cnt4 = table_counts(led_path, cv_path)
    cert_2026b = full_rows(
        led_path, "SELECT account_id, item_id FROM collectibles"
        " WHERE kind = 'certificate' AND event_ref ="
        " 'civic-honor:2026' ORDER BY account_id")
    cert_2027 = full_rows(
        led_path, "SELECT account_id, item_id FROM collectibles"
        " WHERE kind = 'certificate' AND event_ref ="
        " 'civic-honor:2027' ORDER BY account_id")
    cert_2026_rows = [(r[0], r[1]) for r in cert_2026b]
    board_post = [(e["rank"], e["account_id"], e["points"])
                  for e in cv2.honor_board("2026")["honor_board"]]
    bob_row = [h for h in json.loads(bat4["certs_2026"])["honors"]
               if h["account_id"] == "usr:bob"][0]
    dave27 = [h for h in json.loads(
        read_battery(hc2, cv2, cl2)["certs_2027"])["honors"]]
    ok4 = (
        r4["granted"] == 1 and r4["already"] == 2
        and hon4 == [(1, "usr:erin", "granted"),
                     (2, "usr:carol", "already"),
                     (3, "usr:aaron", "already")]
        and board_post == [(1, "usr:erin", 20),
                           (2, "usr:carol", 12),
                           (3, "usr:aaron", 7),
                           (4, "usr:bob", 7),
                           (5, "usr:dave", 3)]
        and bob_row["rank"] == 4 and bob_row["certified"]
        and bob_row["item_id"] == "civic-honor-2026"
        and r4b["granted"] == 1 and len(r4b["honorees"]) == 1
        and r4b["honorees"][0]["account_id"] == "usr:dave"
        and cert_2026_rows == [
            ("usr:aaron", "civic-honor-2026"),
            ("usr:bob", "civic-honor-2026"),
            ("usr:carol", "civic-honor-2026"),
            ("usr:erin", "civic-honor-2026")]
        and cert_2027 == [("usr:dave", "civic-honor-2027")]
        and len(dave27) == 1 and dave27[0]["certified"]
        and cnt4["collectibles"] == 5
        and cnt4["ledger_tx"] == 0 and cnt4["ledger_entries"] == 0
        and cnt4["civic_earns"] == 13)
    record("AC-HCP4", ok4, "post-restart continuation: erin earns"
          " four poll events on the reopened civic face so the"
          " board moves (erin 20 -> rank 1); the re-grant heals"
          " incrementally across the restart - %s (granted=%d"
          " already=%d, the interrupted-batch heal law live:"
          " only the newcomer costs a row, every pre-restart"
          " certificate converges to already with zero new rows);"
          " bob drops to rank 4, out of the top-3 slice, yet keeps"
          " certified=true with his item_id (permanent-certificate"
          " law survives the restart - the flag re-derives from"
          " the persisted certificate rows, not the live slice);"
          " dave earns in 2027 so a second event namespace opens:"
          " grant 2027 top-1 lands dave's row (SQL cross:"
          " civic-honor:2026 = %d rows aaron/bob/carol/erin,"
          " civic-honor:2027 = %s, item_id pinned); collectibles"
          " 3->%d, civic_earns 8->%d, ledger_tx stays %d"
          " (zero token law across the whole window)"
          % (hon4, r4["granted"], r4["already"],
             len(cert_2026_rows), cert_2027[0],
             cnt4["collectibles"], cnt4["civic_earns"],
             cnt4["ledger_tx"]))

    # -- AC-HCP5 frozen rows + replay gates across restart -------
    rows_cl_now = full_rows(
        led_path, "SELECT * FROM collectibles ORDER BY cl_id")
    rows_earn_now = full_rows(
        cv_path, "SELECT * FROM civic_earns ORDER BY rowid")
    frozen_cl = rows_cl_now[:3] == snap_cl
    frozen_earn = rows_earn_now[:len(snap_earn)] == snap_earn
    r5 = hc2.grant_year_honors("2026", 3, "civic-honor-2026")
    r5b = hc2.grant_year_honors("2028", 5, "civic-honor-2028")
    bat5 = read_battery(hc2, cv2, cl2)
    ok5 = (
        frozen_cl and frozen_earn
        and r5["granted"] == 0 and r5["already"] == 3
        and all(h["status"] == "already" for h in r5["honorees"])
        and r5b["granted"] == 0 and r5b["already"] == 0
        and r5b["honorees"] == []
        and table_counts(led_path, cv_path) == cnt4
        and bat5 == bat4
        and full_rows(led_path, "SELECT * FROM collectibles"
                      " ORDER BY cl_id") == rows_cl_now)
    record("AC-HCP5", ok5, "frozen faces: every pre-restart"
          " certificate row (carol/aaron/bob 2026) keeps all its"
          " columns byte-identical across the restart AND the"
          " continuation (collectibles rows are immutable - the"
          " module's only UPDATE surface is the edition counter,"
          " untouched here); the pre-restart civic_earn rows stay"
          " byte-identical as a frozen prefix (append-only earns:"
          " only new rows land, %d->%d); replay gates across the"
          " restart: the terminal re-grant returns granted=%d"
          " already=%d with zero new rows (the collectibles"
          " duplicate law converges to already), and the"
          " zero-earn year 2028 grants honestly empty"
          " (granted=%d honorees=%s) with zero rows; counts and"
          " battery frozen across both replay probes"
          % (len(snap_earn), len(rows_earn_now), r5["granted"],
             r5["already"], r5b["granted"], r5b["honorees"]))

    # -- AC-HCP6 pure-read law -----------------------------------
    bat_a = read_battery(hc2, cv2, cl2)
    bat_b = read_battery(hc2, cv2, cl2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and table_counts(led_path, cv_path) == cnt4)
    record("AC-HCP6", ok6, "pure-read law: the full battery"
          " (certs 2026/2027/2028 + board + five collections)"
          " reads twice back-to-back byte-identical and both-db"
          " table counts stay constant - the honor_certs and"
          " honor_board derivations are zero-side-effect reads"
          " over the two persisted stores")

    # -- AC-HCP7 third instance stability + hygiene --------------
    cl2.close()
    cv2.close()
    led2.close()
    led3 = L.Ledger(led_path, cfg)
    cv3 = CV.CivicPointsFace(DISCLAIMER, cv_path)
    cl3 = CL.CollectiblesFace(led3)
    hc3 = HC.HonorCertFace(cv3, cl3, DISCLAIMER)
    bat3 = read_battery(hc3, cv3, cl3)
    diffs3 = battery_diffs(bat5, bat3)
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                   if l.strip().startswith("import ")
                   or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in NETWORK_LIBS)]
    sha_ok = all(
        sha16(io_read(os.path.join(BASE, name + ".py"))) == sha_b
        for name, sha_b in mod_sha_before.items())
    tmp_outside = (not os.path.realpath(tmp).startswith(repo_root)
                   and os.path.realpath(tmp).startswith(
                       os.path.realpath(tempfile.gettempdir())))
    ok7 = (not diffs3
           and sha16(io_read(cfg_path)) == cfg_sha_before
           and sha_ok
           and non_ascii == 0 and not net_imports
           and tmp_outside)
    record("AC-HCP7", ok7, "third instance: three-piece close ->"
          " reopen the same two dbs once more - battery"
          " byte-identical to the instance-2 terminal state"
          " (diffs=%s; certified flags, honor order and collection"
          " provenance stable across a second restart); shipped"
          " files untouched (config.json + honorcert/civicpoints/"
          "collectibles sha16 stable); suite source pure ASCII"
          " (%d non-ascii), zero network imports (%d hits), world"
          " tmp outside repo (%s)"
          % (diffs3 or "none", non_ascii, len(net_imports),
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
