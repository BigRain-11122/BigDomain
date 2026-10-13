"""Cross-restart persistence window for the city venue rental +
storefront tenancy face (BigDomain R1938; the venue seat of the
R1886 persist-family lineage - the R1936-seeded row, criteria
pre-registered in the R1938 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close both pieces -> reopen the same db/config -> byte-identical
read replay -> restart-surviving gate probes (zero drift) ->
post-restart real-path continuation on a freed venue slot and a
termination-freed storefront window -> frozen faces + dup/full
gates across restart -> pure-read law -> third instance
stability. is_rented / tenant_of / occupancy_ledger are
tick-parameterized pure-value read faces with zero clock echo
(occupancy_ledger does not surface created_utc), so full-dump
byte-identity holds without clock freezing; the evidence digests
mask the bound spend_tx field (banded projection, R1902 law) so
the suite stdout stays deterministic across double runs.

Usage: python test_venue_persist.py
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
import venue as V           # noqa: E402  (R605 extension face)

RESULTS = []

_SPEND_RE = re.compile(r'"bound_spend_tx": "[^"]*"')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_v_error(fn, *codes):
    try:
        fn()
    except V.VenueError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    return _SPEND_RE.sub('"bound_spend_tx": "<tx>"', text)


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    for tbl in ("venue_registry", "venue_occupancy", "ledger_tx",
                "ledger_entries"):
        out[tbl] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def spend_cross(db_path, tx_id, account_id):
    """SQL cross: the bound spend tx is a real ledger spend row
    with a debit leg on the renting account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = 'debit'",
        (tx_id, account_id)).fetchone()
    conn.close()
    return (head[0] if head else None), (leg[0] if leg else None)


def read_battery(vf, led):
    return {
        "rent_plaza_alice": dump(
            [vf.is_rented("plaza", "usr:alice", t)
             for t in (100, 109, 110, 112)]),
        "rent_plaza_bob": dump(
            [vf.is_rented("plaza", "usr:bob", t)
             for t in (105, 114, 115)]),
        "rent_plaza_carol": dump(
            [vf.is_rented("plaza", "usr:carol", t)
             for t in (200, 204, 205)]),
        "tenant_booth1": dump(
            [vf.tenant_of("booth-1", t)
             for t in (299, 300, 305, 306, 309, 310, 314, 315)]),
        "hist_plaza": dump(vf.occupancy_ledger("plaza")),
        "hist_booth1": dump(vf.occupancy_ledger("booth-1")),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="venue-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    vnmod_sha_before = sha16(io_read(os.path.join(BASE, "venue.py")))
    ledmod_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    # ---- instance 1: anchor world on the real product path -------
    led = L.Ledger(db_path, cfg)
    vf = V.VenueFace(led)
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-VNP-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.adjust([("pool:reserve", "debit", 2000),
                ("usr:alice", "credit", 2000)],
               "manual:vnp-fund-alice", "persist window funding alice")
    led.adjust([("pool:reserve", "debit", 600),
                ("usr:bob", "credit", 600)],
               "manual:vnp-fund-bob", "persist window funding bob")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:carol", "credit", 400)],
               "manual:vnp-fund-carol", "persist window funding carol")

    # concurrent venue rentals inside capacity 2 + one far-future window
    vf.register_venue("plaza", 2)
    r_a1 = vf.rent_venue("usr:alice", "plaza", 100, 10, 5, "order:vnp-a1")
    r_b1 = vf.rent_venue("usr:bob", "plaza", 105, 10, 4, "order:vnp-b1")
    r_c1 = vf.rent_venue("usr:carol", "plaza", 200, 5, 3, "order:vnp-c1")
    # storefront: alice leases then terminates early, bob takes the
    # next window (termination moves zero tokens)
    ls_a1 = vf.lease_storefront("usr:alice", "booth-1", 300, 10, 3,
                                "order:vnp-s1")
    tm1 = vf.terminate_lease("booth-1", 305)
    ls_b1 = vf.lease_storefront("usr:bob", "booth-1", 310, 5, 3,
                                "order:vnp-s2")

    # -- AC-VNP1 control anchor: world pinned + gate probes -----
    bal1 = read_battery(vf, led)
    cnt1 = table_counts(db_path)
    ok_world = (
        r_a1["fee"] == 50 and r_a1["start_tick"] == 100
        and r_a1["end_tick"] == 109
        and r_b1["fee"] == 40 and r_c1["fee"] == 15
        and ls_a1["fee"] == 30 and ls_b1["fee"] == 15
        and tm1["terminated_for"] == "usr:alice"
        and tm1["terminated_at"] == 305
        and bal1["bal_alice"] == 1920 and bal1["bal_bob"] == 545
        and bal1["bal_carol"] == 385 and bal1["bal_pool"] == 17150
        and cnt1["venue_registry"] == 2
        and cnt1["venue_occupancy"] == 5 and cnt1["spend_tx"] == 5)
    hist_p = json.loads(bal1["hist_plaza"])
    hist_b = json.loads(bal1["hist_booth1"])
    ok_hist = (
        [(h["account_id"], h["start_tick"], h["end_tick"])
         for h in hist_p] ==
        [("usr:alice", 100, 109), ("usr:bob", 105, 114),
         ("usr:carol", 200, 204)]
        and all(h["terminated_tick"] is None for h in hist_p)
        and [(h["account_id"], h["start_tick"], h["end_tick"],
              h["terminated_tick"]) for h in hist_b] ==
        [("usr:alice", 300, 309, 305), ("usr:bob", 310, 314, None)]
        and all(h["bound_spend_tx"] for h in hist_p + hist_b)
        and all(h["kind"] == "venue" for h in hist_p)
        and all(h["kind"] == "storefront" for h in hist_b))
    ok_ticks = (
        json.loads(bal1["rent_plaza_alice"]) == [True, True, False, False]
        and json.loads(bal1["rent_plaza_bob"]) == [True, True, False]
        and json.loads(bal1["rent_plaza_carol"]) == [True, True, False]
        and json.loads(bal1["tenant_booth1"]) ==
        [None, "usr:alice", "usr:alice", None, None,
         "usr:bob", "usr:bob", None])
    probe_specs = (
        ("unknown", lambda: vf.rent_venue(
            "usr:alice", "ghost-hall", 400, 5, 3, "order:vnp-p1"),
         V.E_VN_UNKNOWN),
        ("full", lambda: vf.rent_venue(
            "usr:alice", "plaza", 106, 5, 3, "order:vnp-p2"),
         V.E_VN_FULL),
        ("dup", lambda: vf.rent_venue(
            "usr:alice", "plaza", 100, 10, 5, "order:vnp-p3"),
         V.E_VN_DUP),
        ("lease-active", lambda: vf.lease_storefront(
            "usr:alice", "booth-1", 312, 5, 3, "order:vnp-p4"),
         V.E_VN_LEASE_ACTIVE),
        ("no-lease", lambda: vf.terminate_lease("booth-1", 320),
         V.E_VN_NO_LEASE))
    probes1 = []
    for label, fn, code in probe_specs:
        ok_one, got = expect_v_error(fn, code)
        probes1.append("%s=%s" % (label, got) if ok_one else
                       "%s NOT-RAISED(%s)" % (label, got))
    ok_probes1 = all("NOT-RAISED" not in p for p in probes1)
    ok_probe_drift1 = (table_counts(db_path) == cnt1
                       and read_battery(vf, led) == bal1)
    ok1 = (ok_world and ok_hist and ok_ticks and ok_probes1
           and ok_probe_drift1)
    record("AC-VNP1", ok1, "anchor world pinned (plaza capacity 2:"
          " alice [100,109] fee 50 + bob [105,114] fee 40 + carol"
          " [200,204] fee 15; booth-1: alice [300,309] fee 30"
          " terminated at 305 zero-token + bob [310,314] fee 15;"
          " tick probes: is_rented alice/bob/carol 100T/109T/110F,"
          " 105T/114T/115F, 200T/204T/205F; tenant_of 299N/300A/305A"
          "/306N/309N/310B/314B/315N - termination effective through"
          " 305, free from 306); five gate probes rejected (%s);"
          " counts registry=%d occupancy=%d spend-tx=%d frozen across"
          " probes; balances 1920/545/385/17150; digest=%s" % (
              "; ".join(probes1), cnt1["venue_registry"],
              cnt1["venue_occupancy"], cnt1["spend_tx"],
              evidence_digest(bal1)))

    # -- AC-VNP2 cross-restart byte-identical replay -------------
    vf.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    vf2 = V.VenueFace(led2)
    bal2 = read_battery(vf2, led2)
    diffs2 = battery_diffs(bal1, bal2)
    ok2 = not diffs2
    record("AC-VNP2", ok2, "two-piece close->reopen (vf.close ->"
          " led.close -> Ledger same db/cfg + VenueFace fresh):"
          " read battery byte-identical to pre-close snapshot"
          " (is_rented nine probes + tenant_of eight probes +"
          " occupancy history x2 + four balances), diffs=%s;"
          " tick-window semantics and bound spend_tx persisted"
          " values replay with zero in-memory drift; digest=%s" %
          (diffs2 or "none", evidence_digest(bal2)))

    # -- AC-VNP3 gates survive restart, zero drift ---------------
    probes2 = []
    for label, fn, code in probe_specs:
        if label == "unknown":
            def fn2():
                vf2.rent_venue("usr:alice", "ghost-hall", 400, 5, 3,
                              "order:vnp-p1")
        elif label == "full":
            def fn2():
                vf2.rent_venue("usr:alice", "plaza", 106, 5, 3,
                               "order:vnp-p2")
        elif label == "dup":
            def fn2():
                vf2.rent_venue("usr:alice", "plaza", 100, 10, 5,
                               "order:vnp-p3")
        elif label == "lease-active":
            def fn2():
                vf2.lease_storefront("usr:alice", "booth-1", 312, 5, 3,
                                     "order:vnp-p4")
        else:
            def fn2():
                vf2.terminate_lease("booth-1", 320)
        ok_one, got = expect_v_error(fn2, code)
        probes2.append("%s=%s" % (label, got) if ok_one else
                       "%s NOT-RAISED(%s)" % (label, got))
    ok_probes2 = all("NOT-RAISED" not in p for p in probes2)
    ok_drift2 = (table_counts(db_path) == cnt1
                 and read_battery(vf2, led2) == bal2)
    ok3 = ok_probes2 and ok_drift2
    record("AC-VNP3", ok3, "restart-surviving gates: five probes"
          " all rejected with identical codes on instance 2 (%s);"
          " counts and balances frozen across the probe batch"
          " (registry/occupancy/spend-tx %d/%d/%d unchanged, zero"
          " charge, zero rows)" % ("; ".join(probes2),
                                   cnt1["venue_registry"],
                                   cnt1["venue_occupancy"],
                                   cnt1["spend_tx"]))

    # -- AC-VNP4 post-restart real-path continuation --------------
    r_a2 = vf2.rent_venue("usr:alice", "plaza", 110, 5, 5, "order:vnp-a2")
    head_a2, leg_a2 = spend_cross(db_path, r_a2["spend_tx_id"],
                                  "usr:alice")
    ls_c2 = vf2.lease_storefront("usr:carol", "booth-1", 306, 4, 3,
                                 "order:vnp-c2")
    head_c2, leg_c2 = spend_cross(db_path, ls_c2["spend_tx_id"],
                                  "usr:carol")
    bal4 = read_battery(vf2, led2)
    cnt4 = table_counts(db_path)
    hist_p4 = json.loads(bal4["hist_plaza"])
    hist_b4 = json.loads(bal4["hist_booth1"])
    ok4 = (
        r_a2["fee"] == 25 and r_a2["start_tick"] == 110
        and r_a2["end_tick"] == 114
        and head_a2 == "spend" and leg_a2 == "debit"
        and ls_c2["fee"] == 12 and ls_c2["start_tick"] == 306
        and ls_c2["end_tick"] == 309
        and head_c2 == "spend" and leg_c2 == "debit"
        and cnt4["venue_occupancy"] == 7 and cnt4["spend_tx"] == 7
        and bal4["bal_alice"] == 1895 and bal4["bal_bob"] == 545
        and bal4["bal_carol"] == 373 and bal4["bal_pool"] == 17187
        and json.loads(bal4["rent_plaza_alice"])[3] is True
        and json.loads(bal4["tenant_booth1"])[3] == "usr:carol"
        and len(hist_p4) == 4 and len(hist_b4) == 3
        and (hist_p4[2]["account_id"], hist_p4[2]["start_tick"],
             hist_p4[2]["end_tick"]) == ("usr:alice", 110, 114)
        and (hist_b4[1]["account_id"], hist_b4[1]["start_tick"],
             hist_b4[1]["end_tick"]) == ("usr:carol", 306, 309)
        and hist_p4[0]["account_id"] == "usr:alice"
        and hist_p4[0]["start_tick"] == 100
        and hist_b4[2]["account_id"] == "usr:bob")
    record("AC-VNP4", ok4, "post-restart continuation: alice re-rents"
          " the freed plaza slot [110,114] fee 25 (only bob's"
          " [105,114] still active there, capacity 2 has room) and"
          " carol leases the termination-freed storefront window"
          " [306,309] fee 12 - both bind real spend txs (SQL cross"
          " type=%s/%s, debit legs=%s/%s, tx_id not echoed); touched"
          " read faces recompute zero-cache (is_rented(plaza,alice,"
          "112) False->True, tenant_of(booth-1,307) None->carol,"
          " plaza history 3->4 rows, booth-1 history 2->3 rows,"
          " new rows land in (start_tick,occ_id) order); untouched"
          " probes frozen; occupancy 5->7, spend-tx 5->7, balances"
          " 1895/545/373/17187; digest=%s" % (
              head_a2, head_c2, leg_a2, leg_c2,
              evidence_digest(bal4)))

    # -- AC-VNP5 frozen faces + dup/full gates across restart -----
    old_p = {(h["account_id"], h["start_tick"], h["end_tick"]): h
             for h in json.loads(bal1["hist_plaza"])}
    old_b = {(h["account_id"], h["start_tick"], h["end_tick"]): h
             for h in json.loads(bal1["hist_booth1"])}
    now_p = {(h["account_id"], h["start_tick"], h["end_tick"]): h
             for h in hist_p4}
    now_b = {(h["account_id"], h["start_tick"], h["end_tick"]): h
             for h in hist_b4}
    fields = ("kind", "account_id", "start_tick", "end_tick",
              "terminated_tick", "bound_spend_tx")
    frozen_ok = all(
        all(old[key][f] == now[key][f] for f in fields)
        for old, now in ((old_p, now_p), (old_b, now_b))
        for key in old)
    dup_probe, code_dup = expect_v_error(
        lambda: vf2.rent_venue("usr:alice", "plaza", 110, 5, 5,
                               "order:vnp-p5"), V.E_VN_DUP)
    full_probe, code_full = expect_v_error(
        lambda: vf2.rent_venue("usr:carol", "plaza", 112, 5, 3,
                               "order:vnp-p6"), V.E_VN_FULL)
    bal5 = read_battery(vf2, led2)
    ok5 = (frozen_ok and dup_probe and full_probe
           and table_counts(db_path) == cnt4 and bal5 == bal4)
    record("AC-VNP5", ok5, "frozen faces: every pre-existing"
          " occupancy row keeps all persisted fields (kind/account"
          "/start/end/terminated/bound_spend_tx) byte-identical to"
          " the pre-close snapshot - new rows only insert in order;"
          " dup gate across restart: same [110,114] window with a"
          " fresh ref still rejected %s (idempotency-rejection is"
          " ref-blind, zero charge); capacity gate across restart:"
          " carol at [112,116] rejected %s with two active rentals"
          " filling capacity 2 (zero charge); counts and battery"
          " frozen across both probes (%s==%s)" % (
              code_dup, code_full, cnt4["spend_tx"],
              table_counts(db_path)["spend_tx"]))

    # -- AC-VNP6 pure-read law ------------------------------------
    bat_a = read_battery(vf2, led2)
    bat_b = read_battery(vf2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and table_counts(db_path) == cnt4)
    record("AC-VNP6", ok6, "pure-read law: full battery read twice"
          " back-to-back - is_rented + tenant_of + occupancy"
          " history x2 + four balances byte-identical between the"
          " two reads and table counts constant (read faces have"
          " zero side effects)")

    # -- AC-VNP7 third instance stability + hygiene --------------
    vf2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    vf3 = V.VenueFace(led3)
    bal3 = read_battery(vf3, led3)
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
           and sha16(io_read(cfg_path)) == cfg_sha_before
           and sha16(io_read(os.path.join(BASE, "venue.py")))
           == vnmod_sha_before
           and sha16(io_read(os.path.join(BASE, "ledger.py")))
           == ledmod_sha_before
           and non_ascii == 0 and not net_imports
           and os.path.realpath(tmp).startswith(
               os.path.realpath(tempfile.gettempdir()))
           and not os.path.realpath(tmp).startswith(repo_root))
    record("AC-VNP7", ok7, "third instance: close -> reopen same db"
          " once more - battery byte-identical to instance-2"
          " terminal state (diffs=%s, expired-window faces and"
          " termination faces both stable across a second"
          " restart); shipped files untouched (config/venue/ledger"
          " sha16 stable); suite source pure ASCII (%d non-ascii),"
          " zero network imports (%d hits), world tmp outside repo"
          " (%s)" % (diffs3 or "none", non_ascii, len(net_imports),
                     "yes" if not os.path.realpath(tmp).startswith(
                         repo_root) else "NO"))

    vf3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
