"""Cross-restart persistence window for the studio onboarding
annual-fee face (BigDomain R1949; the studio seat of the R1886
persist-family lineage - the R1944-seeded row, criteria
AC-STP1..AC-STP7 pre-registered in the R1949 tech.md claim row
BEFORE this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close all three pieces (studio face own-connection registry +
venue occupancy engine + ledger core) -> reopen the same
db/config -> byte-identical read replay -> restart-surviving gate
probes (zero drift) -> post-restart real-path continuation (new
account new seat + renewal advance booking, both binding real
spend txs) -> frozen faces + replay/idempotence gates across
restart -> pure-read law -> third instance stability. The read
faces (benefits / tenant / profile) are pure-value faces with
zero clock echo, so full-dump byte-identity holds without clock
freezing; the evidence digests mask the spend-tx fields (banded
projection, R1902 law) so the suite stdout stays deterministic
across double runs.

Usage: python test_studio_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L          # noqa: E402  (P-47-2b core)
import venue as V           # noqa: E402  (R605 occupancy engine)
import studio as S          # noqa: E402  (R625 onboarding face)

RESULTS = []

_SPEND_RE = re.compile(r'"(?:spend_tx|bound_spend_tx)": "[^"]*"')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_st_error(fn, *codes):
    try:
        fn()
    except S.StudioError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    return _SPEND_RE.sub(lambda m: m.group(0).split(":")[0] + ': "<tx>"',
                          text)


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


STUDIO_UNITS = ("studio:pixelforge", "studio:quantworks",
                "studio:indienest")


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    out["studio_products"] = int(conn.execute(
        "SELECT COUNT(*) FROM studio_products").fetchone()[0])
    out["studio_occupancy"] = int(conn.execute(
        "SELECT COUNT(*) FROM venue_occupancy WHERE unit_id IN"
        " (?,?,?)", STUDIO_UNITS).fetchone()[0])
    out["ledger_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def registry_rows(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT studio_id, st_kind, registered_utc FROM"
        " studio_products ORDER BY studio_id").fetchall()
    conn.close()
    return rows


def spend_cross(db_path, tx_id, account_id):
    """SQL cross: the bound spend tx is a real ledger spend row
    with a debit leg on the onboarding account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = 'debit'",
        (tx_id, account_id)).fetchone()
    conn.close()
    return (head[0] if head else None), (leg[0] if leg else None)


def read_battery(stf, led):
    return {
        "ben_pf": dump(stf.studio_benefits("studio:pixelforge")),
        "ben_qw": dump(stf.studio_benefits("studio:quantworks")),
        "ben_in": dump(stf.studio_benefits("studio:indienest")),
        "tenant_pf": dump([stf.studio_tenant("studio:pixelforge", y)
                           for y in (25, 26, 27, 28)]),
        "tenant_qw": dump([stf.studio_tenant("studio:quantworks", y)
                           for y in (26, 27)]),
        "tenant_in": dump([stf.studio_tenant("studio:indienest", y)
                           for y in (26, 27)]),
        "prof_alice_26": dump(stf.studio_profile("usr:alice", 26)),
        "prof_alice_27": dump(stf.studio_profile("usr:alice", 27)),
        "prof_bob_27": dump(stf.studio_profile("usr:bob", 27)),
        "prof_carol_26": dump(stf.studio_profile("usr:carol", 26)),
        "prof_dave_26": dump(stf.studio_profile("usr:dave", 26)),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_dave": led.balance("usr:dave")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def occupancy_history(ven):
    return {u: dump(ven.occupancy_ledger(u)) for u in STUDIO_UNITS}


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def probe_batch(stf):
    """The twelve-gate probe battery: returns a list of
    'label=code' strings (or 'label NOT-RAISED(...)'), zero
    charge / zero rows by construction (all rejects happen before
    the spend, and registration replays are kind-stable)."""
    out = []
    specs = (
        ("kind-drift", lambda: stf.register_studio(
            "studio:pixelforge", "quant_studio"), S.E_ST_KIND_MISMATCH),
        ("bad-kind", lambda: stf.register_studio(
            "studio:x", "film_studio"), S.E_ST_BAD_ARGS),
        ("dup", lambda: stf.onboard_studio(
            "usr:alice", "studio:pixelforge", 26, 9800, "order:stp-p1"),
         S.E_ST_DUP),
        ("taken", lambda: stf.onboard_studio(
            "usr:carol", "studio:pixelforge", 26, 9800, "order:stp-p2"),
         S.E_ST_TAKEN),
        ("unknown", lambda: stf.onboard_studio(
            "usr:bob", "studio:ghostworks", 26, 9800, "order:stp-p3"),
         S.E_ST_UNKNOWN),
        ("bad-acct", lambda: stf.onboard_studio(
            "corp:acme", "studio:pixelforge", 26, 9800, "order:stp-p4"),
         S.E_ST_BAD_ARGS),
        ("bad-price", lambda: stf.onboard_studio(
            "usr:bob", "studio:pixelforge", 26, 0, "order:stp-p5"),
         S.E_ST_BAD_ARGS),
        ("bad-year", lambda: stf.onboard_studio(
            "usr:bob", "studio:pixelforge", -1, 9800, "order:stp-p6"),
         S.E_ST_BAD_ARGS),
        ("bad-ref", lambda: stf.onboard_studio(
            "usr:bob", "studio:pixelforge", 26, 9800, "  "),
         S.E_ST_BAD_ARGS),
        ("ben-unknown", lambda: stf.studio_benefits(
            "studio:ghostworks"), S.E_ST_UNKNOWN),
        ("tenant-bad-year", lambda: stf.studio_tenant(
            "studio:pixelforge", -1), S.E_ST_BAD_ARGS),
        ("profile-bad-acct", lambda: stf.studio_profile(
            "corp:acme", 26), S.E_ST_BAD_ARGS),
    )
    for label, fn, code in specs:
        ok_one, got = expect_st_error(fn, code)
        out.append("%s=%s" % (label, got) if ok_one else
                   "%s NOT-RAISED(%s)" % (label, got))
    return out


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="studio-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    stmod_sha_before = sha16(io_read(os.path.join(BASE, "studio.py")))
    vnmod_sha_before = sha16(io_read(os.path.join(BASE, "venue.py")))
    ledmod_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    # ---- instance 1: anchor world on the real product path ------
    led = L.Ledger(db_path, cfg)
    ven = V.VenueFace(led)
    stf = S.StudioFace(led, ven)
    led.mint_to_pool("pool:reserve", 120000, "SETTLE-STP-A", "settlement")
    for who, av, amt in (("usr:alice", "alice", 50000),
                         ("usr:bob", "bob", 20000),
                         ("usr:carol", "carol", 10000),
                         ("usr:dave", "dave", 30000)):
        led.ensure_account(who, census_avatar_id=av)
        led.adjust([("pool:reserve", "debit", amt), (who, "credit", amt)],
                   "manual:stp-fund-%s" % av,
                   "persist window funding %s" % av)

    stf.register_studio("studio:pixelforge", "game_studio")
    stf.register_studio("studio:quantworks", "quant_studio")
    stf.register_studio("studio:indienest", "game_studio")
    r_a1 = stf.onboard_studio("usr:alice", "studio:pixelforge", 26,
                              9800, "order:stp-a1")
    r_a2 = stf.onboard_studio("usr:alice", "studio:quantworks", 26,
                              19800, "order:stp-a2")
    r_c1 = stf.onboard_studio("usr:carol", "studio:indienest", 26,
                              9800, "order:stp-a3")
    r_b1 = stf.onboard_studio("usr:bob", "studio:pixelforge", 27,
                              9800, "order:stp-b1")

    # -- AC-STP1 control anchor: world pinned + gate probes -------
    bal1 = read_battery(stf, led)
    hist1 = occupancy_history(ven)
    reg1 = registry_rows(db_path)
    cnt1 = table_counts(db_path)
    prof_a26 = json.loads(bal1["prof_alice_26"])
    ok_world = (
        r_a1["fee"] == 9800 and r_a1["window"] == [26, 26]
        and r_a1["st_kind"] == "game_studio"
        and r_a2["fee"] == 19800 and r_a2["st_kind"] == "quant_studio"
        and r_c1["fee"] == 9800 and r_b1["window"] == [27, 27]
        and bal1["bal_alice"] == 20400 and bal1["bal_bob"] == 10200
        and bal1["bal_carol"] == 200 and bal1["bal_dave"] == 30000
        and bal1["bal_pool"] == 59200
        and cnt1["studio_products"] == 3
        and cnt1["studio_occupancy"] == 4 and cnt1["spend_tx"] == 4
        and json.loads(bal1["ben_pf"])["benefits"] ==
        ["idea_pool_access", "player_traffic_boost", "studio_floor"]
        and json.loads(bal1["ben_qw"])["benefits"] ==
        ["stock_inspiration_feed", "co_create_observation_entry",
         "quant_screen_spotlight"]
        and json.loads(bal1["tenant_pf"]) ==
        [None, "usr:alice", "usr:bob", None]
        and json.loads(bal1["tenant_qw"]) == ["usr:alice", None]
        and json.loads(bal1["tenant_in"]) == ["usr:carol", None]
        and sorted(i["studio_id"] for i in prof_a26["subscriptions"]) ==
        ["studio:pixelforge", "studio:quantworks"]
        and all(i["spend_tx"] and i["year"] == 26
                for i in prof_a26["subscriptions"])
        and json.loads(bal1["prof_alice_27"])["subscriptions"] == []
        and json.loads(bal1["prof_dave_26"])["subscriptions"] == []
        and len(reg1) == 3)
    probes1 = probe_batch(stf)
    ok_probes1 = all("NOT-RAISED" not in p for p in probes1)
    ok_probe_drift1 = (table_counts(db_path) == cnt1
                      and read_battery(stf, led) == bal1)
    ok1 = ok_world and ok_probes1 and ok_probe_drift1
    record("AC-STP1", ok1, "anchor world pinned (three registry rows;"
          " four onboardings: alice pixelforge [26,26] fee 9800 +"
          " alice quantworks [26,26] fee 19800 (same account, two"
          " kinds, one year - legal) + carol indienest [26,26] fee"
          " 9800 + bob pixelforge [27,27] fee 9800 (independent"
          " year windows); balances 20400/10200/200/30000/59200"
          " (pool = 10,000 seeded + 49,200 fees recirculated);"
          " counts registry=3 studio-occupancy=4 spend-tx=4; tenant"
          " spectrum pixelforge 25N/26A/27B/28N, quantworks 26A/27N,"
          " indienest 26C/27N; alice profile@26 = two seats both"
          " carrying spend tx, @27 empty, dave @26 empty); twelve"
          " gate probes rejected (%s); counts and battery frozen"
          " across the probe batch; digest=%s" % (
              "; ".join(probes1), evidence_digest(bal1)))

    # -- AC-STP2 cross-restart byte-identical replay --------------
    stf.close()
    ven.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    ven2 = V.VenueFace(led2)
    stf2 = S.StudioFace(led2, ven2)
    bal2 = read_battery(stf2, led2)
    hist2 = occupancy_history(ven2)
    diffs2 = battery_diffs(bal1, bal2)
    hist_diffs2 = [u for u in hist1 if hist1[u] != hist2[u]]
    ok2 = not diffs2 and not hist_diffs2 and registry_rows(db_path) == reg1
    record("AC-STP2", ok2, "three-piece close->reopen (stf.close ->"
          " ven.close -> led.close -> Ledger same db/cfg + VenueFace"
          " + fresh StudioFace): read battery (benefits x3 + tenant"
          " spectra x3 + profiles x5 + five balances) AND the three"
          " studio occupancy histories AND the raw registry rows all"
          " byte-identical to pre-close snapshots, diffs=%s/%s/%s;"
          " registry rows, year windows and bound spend txs replay"
          " with zero in-memory drift; digest=%s" % (
              diffs2 or "none", hist_diffs2 or "none",
              "none" if registry_rows(db_path) == reg1 else "reg",
              evidence_digest(bal2)))

    # -- AC-STP3 gates survive restart, zero drift -----------------
    probes2 = probe_batch(stf2)
    ok_probes2 = all("NOT-RAISED" not in p for p in probes2)
    ok_drift2 = (table_counts(db_path) == cnt1
                 and read_battery(stf2, led2) == bal2
                 and occupancy_history(ven2) == hist2)
    ok3 = ok_probes2 and probes2 == probes1 and ok_drift2
    record("AC-STP3", ok3, "restart-surviving gates: all twelve probes"
          " rejected with identical codes on instance 2 and in the"
          " same order as instance 1 (%s); counts, battery and"
          " occupancy histories frozen across the probe batch"
          " (registry/studio-occupancy/spend-tx %d/%d/%d unchanged,"
          " zero charge, zero rows)" % (
              "; ".join(probes2), cnt1["studio_products"],
              cnt1["studio_occupancy"], cnt1["spend_tx"]))

    # -- AC-STP4 post-restart real-path continuation ---------------
    r_d2 = stf2.onboard_studio("usr:dave", "studio:quantworks", 27,
                               19800, "order:stp-d2")
    r_a3 = stf2.onboard_studio("usr:alice", "studio:pixelforge", 28,
                               9800, "order:stp-a4")
    head_d2, leg_d2 = spend_cross(db_path, r_d2["spend_tx"], "usr:dave")
    head_a3, leg_a3 = spend_cross(db_path, r_a3["spend_tx"], "usr:alice")
    dup_d2, code_dd2 = expect_st_error(
        lambda: stf2.onboard_studio(
            "usr:dave", "studio:quantworks", 27, 19800, "order:stp-p7"),
        S.E_ST_DUP)
    tk_qw27, code_tk27 = expect_st_error(
        lambda: stf2.onboard_studio(
            "usr:carol", "studio:quantworks", 27, 19800, "order:stp-p8"),
        S.E_ST_TAKEN)
    bal4 = read_battery(stf2, led2)
    cnt4 = table_counts(db_path)
    prof_d27 = json.loads(dump(stf2.studio_profile("usr:dave", 27)))
    prof_a28 = json.loads(dump(stf2.studio_profile("usr:alice", 28)))
    ok4 = (
        r_d2["fee"] == 19800 and r_d2["window"] == [27, 27]
        and r_a3["fee"] == 9800 and r_a3["window"] == [28, 28]
        and head_d2 == "spend" and leg_d2 == "debit"
        and head_a3 == "spend" and leg_a3 == "debit"
        and dup_d2 and code_dd2 == S.E_ST_DUP
        and tk_qw27 and code_tk27 == S.E_ST_TAKEN
        and cnt4["studio_products"] == 3
        and cnt4["studio_occupancy"] == 6 and cnt4["spend_tx"] == 6
        and bal4["bal_dave"] == 10200 and bal4["bal_alice"] == 10600
        and bal4["bal_pool"] == 88800
        and json.loads(bal4["tenant_qw"])[1] == "usr:dave"
        and json.loads(bal4["tenant_pf"])[3] == "usr:alice"
        and [i["studio_id"] for i in prof_d27["subscriptions"]] ==
        ["studio:quantworks"]
        and [i["studio_id"] for i in prof_a28["subscriptions"]] ==
        ["studio:pixelforge"]
        and all(i["spend_tx"] for i in
                prof_d27["subscriptions"] + prof_a28["subscriptions"]))
    record("AC-STP4", ok4, "post-restart continuation: dave onboards"
          " quantworks year 27 fee 19800 (new account, new seat) and"
          " alice renews pixelforge year 28 fee 9800 (advance"
          " booking) - both bind real spend txs (SQL cross"
          " type=%s/%s, debit legs=%s/%s, tx ids not echoed); new"
          " gates live on the new seats: dave replay y27 rejected"
          " %s, carol hitting quantworks y27 rejected %s (both zero"
          " charge); read faces recompute zero-cache (tenant"
          " quantworks@27 None->dave, pixelforge@28 None->alice,"
          " dave profile@27 one quant seat, alice profile@28 one"
          " game seat, all rows carrying spend tx); registry"
          " untouched by onboarding (still 3 rows); studio"
          " occupancy 4->6, spend-tx 4->6, balances dave 10200,"
          " alice 10600, pool 88800; digest=%s" % (
              head_d2, head_a3, leg_d2, leg_a3, code_dd2, code_tk27,
              evidence_digest(bal4)))

    # -- AC-STP5 frozen faces + replay/idempotence gates ----------
    # freeze-face prefix law (R1947 AC-EFP5 erratum family): the
    # continuation legitimately appends new occupancy rows, so the
    # freeze claim is that every pre-restart row survives as the
    # byte-identical PREFIX of the post-continuation history
    # (row-level prefix on the parsed row lists - the dumped
    # strings grow at the tail bracket, so the comparison must be
    # on rows, first-run erratum of this suite, same family).
    hist5 = occupancy_history(ven2)

    def hist_rows(hist):
        return {u: json.loads(hist[u]) for u in hist}

    rows1, rows5 = hist_rows(hist1), hist_rows(hist5)
    frozen_hist = all(
        rows5[u][:len(rows1[u])] == rows1[u] for u in rows1)
    ok_frozen_reg = registry_rows(db_path) == reg1
    dup_a1, code_da1 = expect_st_error(
        lambda: stf2.onboard_studio(
            "usr:alice", "studio:pixelforge", 26, 9800, "order:stp-p9"),
        S.E_ST_DUP)
    reg_idem = stf2.register_studio("studio:pixelforge", "game_studio")
    far_profile = stf2.studio_profile("usr:alice", 40)
    far_tenant = stf2.studio_tenant("studio:pixelforge", 40)
    bal5 = read_battery(stf2, led2)
    ok5 = (frozen_hist and ok_frozen_reg and dup_a1
           and code_da1 == S.E_ST_DUP and reg_idem["idempotent"] is True
           and far_profile["subscriptions"] == []
           and far_tenant is None
           and table_counts(db_path) == cnt4 and bal5 == bal4)
    record("AC-STP5", ok5, "frozen faces: every pre-restart occupancy"
          " row keeps all persisted fields byte-identical - the"
          " anchor histories replay as the exact byte-identical"
          " prefix of the post-continuation histories (kind/account"
          "/start/end/terminated/bound_spend_tx; the continuation"
          " only appended new rows, prefix law) - and the three"
          " registry rows are byte-identical including the"
          " registered_utc stamps (rows immutable, zero mutation"
          " surface); anchor-seat replay across restart: alice"
          " pixelforge y26 still rejected %s (zero new rows, zero"
          " charge); idempotent re-registration returns"
          " idempotent=True with the registry still at 3 rows;"
          " far-future faces honest-empty (alice profile@40 = [],"
          " tenant pixelforge@40 = None); counts and battery frozen"
          " (%d/%d/%d)" % (
              code_da1, cnt4["studio_products"],
              cnt4["studio_occupancy"], cnt4["spend_tx"]))

    # -- AC-STP6 pure-read law -------------------------------------
    bat_a = read_battery(stf2, led2)
    bat_b = read_battery(stf2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and occupancy_history(ven2) == hist5
           and table_counts(db_path) == cnt4)
    record("AC-STP6", ok6, "pure-read law: full battery (benefits +"
          " tenant spectra + profiles + balances) and the three"
          " occupancy histories read twice back-to-back - all"
          " byte-identical between the two reads and table counts"
          " constant (studio read faces have zero side effects,"
          " zero token movement)")

    # -- AC-STP7 third instance stability + hygiene ----------------
    stf2.close()
    ven2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    ven3 = V.VenueFace(led3)
    stf3 = S.StudioFace(led3, ven3)
    bal3 = read_battery(stf3, led3)
    diffs3 = battery_diffs(bal5, bal3)
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in
                          ("urllib", "requests", "socket", "http"))]
    ok7 = (not diffs3
           and occupancy_history(ven3) == hist5
           and sha16(io_read(cfg_path)) == cfg_sha_before
           and sha16(io_read(os.path.join(BASE, "studio.py")))
           == stmod_sha_before
           and sha16(io_read(os.path.join(BASE, "venue.py")))
           == vnmod_sha_before
           and sha16(io_read(os.path.join(BASE, "ledger.py")))
           == ledmod_sha_before
           and non_ascii == 0 and not net_imports
           and not os.path.realpath(tmp).startswith(repo_root))
    record("AC-STP7", ok7, "third instance: close all three once more"
          " -> reopen same db - battery AND occupancy histories"
          " byte-identical to the instance-2 terminal state"
          " (diffs=%s; registry, year-window seats, renewal"
          " bookings and gate behavior all stable across a second"
          " restart); shipped files untouched (config/studio/venue"
          "/ledger sha16 stable); suite source pure ASCII (%d"
          " non-ascii), zero network imports (%d hits), world tmp"
          " outside repo (%s)" % (
              diffs3 or "none", non_ascii, len(net_imports),
              "yes" if not os.path.realpath(tmp).startswith(
                  repo_root) else "NO"))

    stf3.close()
    ven3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
