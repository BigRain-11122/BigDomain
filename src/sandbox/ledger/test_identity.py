"""Acceptance suite for the metaverse identity paid face
(BigDomain R624; canon = BLUEPRINT sec-4 C5 identity price row).
Asserts the pre-registered criteria AC-ID1..AC-ID7 from the R624
backlog row (criteria were registered before this code existed;
honesty law). Each criterion prints PASS/FAIL with evidence; the
process exits non-zero on any FAIL.

Usage: python test_identity.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L      # noqa: E402  (P-47-2b core)
import venue as V       # noqa: E402  (R605 occupancy engine)
import props as P       # noqa: E402  (R599 inventory engine)
import identity as ID   # noqa: E402  (R624 identity face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_id_error(fn, *codes):
    try:
        fn()
    except ID.IdentityError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def main():
    tmp = tempfile.mkdtemp(prefix="identity-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    ven = V.VenueFace(led)
    prp = P.PropsFace(led)
    idf = ID.IdentityFace(led, ven, prp)

    led.mint_to_pool("pool:reserve", 7000, "SETTLE-ID-A", "settlement")
    for who, av, amt in (("usr:alice", "alice", 2000),
                         ("usr:bob", "bob", 2000),
                         ("usr:carol", "carol", 2000)):
        led.ensure_account(who, census_avatar_id=av)
        led.adjust([("pool:reserve", "debit", amt), (who, "credit", amt)],
                   "manual:fund-%s" % av, "suite funding %s" % av)
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731

    # -- AC-ID1 reference law: one registry table, writes via engines --
    reg_room = idf.register_identity_product("room:sky-villa", "private_room")
    reg_idem = idf.register_identity_product("room:sky-villa", "private_room")
    ok_kind, code_km = expect_id_error(
        lambda: idf.register_identity_product("room:sky-villa",
                                              "avatar_skin"),
        ID.E_ID_KIND_MISMATCH)
    ok_badk, code_bk = expect_id_error(
        lambda: idf.register_identity_product("prod:x", "spaceship"),
        ID.E_ID_BAD_ARGS)
    for pid, kind in (("skin:neon-fox", "avatar_skin"),
                      ("plaque:co-creator", "creator_plaque"),
                      ("plaque:floor-88", "floor_plaque")):
        idf.register_identity_product(pid, kind)
    conn = sqlite3.connect(db_path)
    my_tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
        " AND name LIKE 'identity%'").fetchall()]
    cap_row = conn.execute(
        "SELECT capacity FROM venue_registry WHERE venue_id = ?",
        ("room:sky-villa",)).fetchone()
    conn.close()
    with open(os.path.join(BASE, "identity.py"), encoding="utf-8") as h:
        src = h.read()
    no_direct_writes = ("INSERT INTO props_inventory" not in src
                        and "INSERT INTO venue_occupancy" not in src)
    venue_echo = ven.register_venue("room:sky-villa", 1)
    ok1 = (reg_room["idempotent"] is False and reg_idem["idempotent"] is True
           and ok_kind and code_km == ID.E_ID_KIND_MISMATCH
           and ok_badk and code_bk == ID.E_ID_BAD_ARGS
           and my_tables == ["identity_products"] and no_direct_writes
           and cap_row is not None and int(cap_row[0]) == 1
           and venue_echo["capacity"] == 1)
    record("AC-ID1", ok1, "registry = identity_products only (%s);"
          " re-register idempotent; kind-drift %s; bad kind %s;"
          " module source has zero direct INSERT INTO props_inventory /"
          " venue_occupancy; room registration landed in the venue"
          " registry with capacity 1 (venue echo %s)"
          % (my_tables, code_km, code_bk, venue_echo))

    # -- AC-ID2 private room: one spend per month window, gates ------------
    b_al0 = bal("usr:alice")
    r1 = idf.rent_private_room("usr:alice", "room:sky-villa", 5, 99,
                               "order:id2a")
    b_al1 = bal("usr:alice")
    occ = ven.occupancy_ledger("room:sky-villa")
    ok_dup, code_dp = expect_id_error(
        lambda: idf.rent_private_room("usr:alice", "room:sky-villa", 5, 99,
                                      "order:id2b"),
        ID.E_ID_DUP)
    b_al2 = bal("usr:alice")
    r2 = idf.rent_private_room("usr:alice", "room:sky-villa", 6, 99,
                               "order:id2c")
    b_al3 = bal("usr:alice")
    b_bob0 = bal("usr:bob")
    ok_taken, code_tk = expect_id_error(
        lambda: idf.rent_private_room("usr:bob", "room:sky-villa", 6, 99,
                                      "order:id2d"),
        ID.E_ID_TAKEN)
    ok2 = (b_al1 == b_al0 - 99 and len(occ) == 1
           and occ[0]["account_id"] == "usr:alice"
           and occ[0]["start_tick"] == 5 and occ[0]["end_tick"] == 5
           and occ[0]["bound_spend_tx"] == r1["spend_tx"]
           and r1["window"] == [5, 5]
           and ok_dup and code_dp == ID.E_ID_DUP and b_al2 == b_al1
           and b_al3 == b_al2 - 99 and r2["spend_tx"] != r1["spend_tx"]
           and ok_taken and code_tk == ID.E_ID_TAKEN
           and bal("usr:bob") == b_bob0
           and idf.room_holder("room:sky-villa", 5) == "usr:alice"
           and idf.room_holder("room:sky-villa", 6) == "usr:alice"
           and idf.room_holder("room:sky-villa", 7) is None)
    record("AC-ID2", ok2, "month-5 rental = one spend (%d->%d) bound into"
          " the venue occupancy row (window %s); same-month replay %s"
          " zero charge (%d==%d); month-6 renewal is a separate legal"
          " spend with a distinct tx; bob in month 6 rejected %s zero"
          " charge (%d==%d); holder reads: m5/m6=alice, m7=None"
          % (b_al0, b_al1, r1["window"], code_dp, b_al1, b_al2, code_tk,
             b_bob0, bal("usr:bob")))

    # -- AC-ID3 permanent kinds: one spend each, one per account ----------
    b_al4 = bal("usr:alice")
    s1 = idf.claim_permanent("usr:alice", "skin:neon-fox", 299, "order:id3a")
    b_al5 = bal("usr:alice")
    ok_sdup, code_sd = expect_id_error(
        lambda: idf.claim_permanent("usr:alice", "skin:neon-fox", 299,
                                   "order:id3b"),
        ID.E_ID_DUP)
    b_al_dup = bal("usr:alice")
    p1 = idf.claim_permanent("usr:alice", "plaque:co-creator", 499,
                             "order:id3c")
    p2 = idf.claim_permanent("usr:alice", "plaque:floor-88", 199,
                             "order:id3d")
    b_al6 = bal("usr:alice")
    inv = prp.inventory("usr:alice")
    txs = {s1["spend_tx"], p1["spend_tx"], p2["spend_tx"]}
    ok3 = (b_al5 == b_al4 - 299 and ok_sdup and code_sd == ID.E_ID_DUP
           and b_al_dup == b_al5
           and b_al6 == b_al5 - 499 - 199
           and s1["id_kind"] == "avatar_skin"
           and p1["id_kind"] == "creator_plaque"
           and p2["id_kind"] == "floor_plaque"
           and sorted(inv["cosmetics"]) == ["plaque:co-creator",
                                            "plaque:floor-88",
                                            "skin:neon-fox"]
           and len(txs) == 3
           and all(inv["bound_spend_tx"][c] in txs
                   for c in inv["cosmetics"]))
    record("AC-ID3", ok3, "skin claim = one spend (%d->%d); duplicate %s"
          " rejected before the spend (balance still %d); plaque claims"
          " independent (%d after both); all three live in props_inventory"
          " as cosmetics with three distinct bound spend txs"
          % (b_al4, b_al5, code_sd, b_al_dup, b_al6))

    # -- AC-ID4 registry gates ----------------------------------------------
    b_bob1 = bal("usr:bob")
    ok_unk_rent, code_ur = expect_id_error(
        lambda: idf.rent_private_room("usr:bob", "room:ghost", 5, 99,
                                      "order:id4a"),
        ID.E_ID_UNKNOWN)
    ok_unk_claim, code_uc = expect_id_error(
        lambda: idf.claim_permanent("usr:bob", "skin:ghost", 299,
                                    "order:id4b"),
        ID.E_ID_UNKNOWN)
    ok_xrent, code_xr = expect_id_error(
        lambda: idf.rent_private_room("usr:bob", "skin:neon-fox", 5, 99,
                                      "order:id4c"),
        ID.E_ID_KIND_MISMATCH)
    ok_xclaim, code_xc = expect_id_error(
        lambda: idf.claim_permanent("usr:bob", "room:sky-villa", 99,
                                    "order:id4d"),
        ID.E_ID_KIND_MISMATCH)
    ok_xread, code_xr2 = expect_id_error(
        lambda: idf.room_holder("skin:neon-fox", 5),
        ID.E_ID_KIND_MISMATCH)
    ok4 = (ok_unk_rent and code_ur == ID.E_ID_UNKNOWN
           and ok_unk_claim and code_uc == ID.E_ID_UNKNOWN
           and ok_xrent and code_xr == ID.E_ID_KIND_MISMATCH
           and ok_xclaim and code_xc == ID.E_ID_KIND_MISMATCH
           and ok_xread and code_xr2 == ID.E_ID_KIND_MISMATCH
           and bal("usr:bob") == b_bob1)
    record("AC-ID4", ok4, "unregistered room %s / product %s rejected;"
          " cross-kind calls rejected (rent on skin %s, claim on room"
          " %s, holder read on skin %s); bob zero charge (%d==%d)"
          % (code_ur, code_uc, code_xr, code_xc, code_xr2, b_bob1,
             bal("usr:bob")))

    # -- AC-ID5 profile read face: derived view, zero token movement ------
    b_all = (bal("usr:alice"), bal("usr:bob"), bal("usr:carol"))
    prof5 = idf.identity_profile("usr:alice", 5)
    prof7 = idf.identity_profile("usr:alice", 7)
    prof_bob = idf.identity_profile("usr:bob", 7)
    perm_ids = [p["product_id"] for p in prof5["permanents"]]
    ok5 = (b_all == (bal("usr:alice"), bal("usr:bob"), bal("usr:carol"))
           and [r["room_id"] for r in prof5["rooms"]] == ["room:sky-villa"]
           and prof5["rooms"][0]["spend_tx"] == r1["spend_tx"]
           and prof7["rooms"] == []
           and perm_ids == ["plaque:co-creator", "plaque:floor-88",
                            "skin:neon-fox"]
           and all(p["spend_tx"] in txs for p in prof5["permanents"])
           and prof_bob["rooms"] == [] and prof_bob["permanents"] == [])
    record("AC-ID5", ok5, "profile at m5 shows the held room with its"
          " spend tx; at m7 no room (window expired); permanents ="
          " %s all with purchase tx provenance; bob's profile empty;"
          " reads moved zero tokens (%s unchanged)"
          % (perm_ids, b_all))

    # -- AC-ID6 isolation: one spend per purchase, reads clean ------------
    conn = sqlite3.connect(db_path)
    alice_spends = conn.execute(
        "SELECT COUNT(*) FROM ledger_entries WHERE account_id = ?"
        " AND direction = 'debit'", ("usr:alice",)).fetchone()[0]
    conn.close()
    alice_purchases = 5  # room m5 + room m6 + skin + 2 plaques
    ok6 = (alice_spends == alice_purchases
           and all(inv["bound_spend_tx"][c] in txs
                   for c in inv["cosmetics"])
           and len(occ) >= 1 and occ[0]["bound_spend_tx"] == r1["spend_tx"])
    record("AC-ID6", ok6, "alice debit legs == purchases (%d == %d:"
          " 2 room months + 3 permanents); every entitlement / occupancy"
          " row binds its own spend tx; registry / holder / profile faces"
          " touched zero tokens (AC-ID5 balance check)"
          % (alice_spends, alice_purchases))

    # -- AC-ID7 bad args zero side effects + hard-law source scan ---------
    b7 = (bal("usr:alice"), bal("usr:bob"), bal("usr:carol"))
    inv7 = len(prp.inventory("usr:alice")["cosmetics"])
    occ7 = len(ven.occupancy_ledger("room:sky-villa"))
    raised_all = True
    bad = []
    for label, fn, code in (
            ("non-usr buyer", lambda: idf.claim_permanent(
                "svc:x", "skin:neon-fox", 299, "order:id7a"),
             ID.E_ID_BAD_ARGS),
            ("zero price", lambda: idf.claim_permanent(
                "usr:carol", "skin:neon-fox", 0, "order:id7b"),
             ID.E_ID_BAD_ARGS),
            ("bool price", lambda: idf.rent_private_room(
                "usr:carol", "room:sky-villa", 5, True, "order:id7c"),
             ID.E_ID_BAD_ARGS),
            ("bool month", lambda: idf.rent_private_room(
                "usr:carol", "room:sky-villa", True, 99, "order:id7d"),
             ID.E_ID_BAD_ARGS),
            ("neg month", lambda: idf.rent_private_room(
                "usr:carol", "room:sky-villa", -1, 99, "order:id7e"),
             ID.E_ID_BAD_ARGS),
            ("empty ref", lambda: idf.claim_permanent(
                "usr:carol", "skin:neon-fox", 299, "  "),
             ID.E_ID_BAD_ARGS),
            ("empty product", lambda: idf.register_identity_product(
                "  ", "avatar_skin"),
             ID.E_ID_BAD_ARGS),
            ("non-usr profile", lambda: idf.identity_profile(
                "svc:x", 5), ID.E_ID_BAD_ARGS),
            ("neg month profile", lambda: idf.identity_profile(
                "usr:carol", -2), ID.E_ID_BAD_ARGS)):
        ok_one, got = expect_id_error(fn, code)
        if ok_one:
            bad.append("%s=%s" % (label, got))
        else:
            bad.append("%s NOT-RAISED(%s)" % (label, got))
            raised_all = False
    with open(os.path.join(BASE, "identity.py"), encoding="utf-8") as h:
        src = h.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    no_update = ("UPDATE identity_products" not in src
                 and "UPDATE props_inventory" not in src
                 and "UPDATE venue_occupancy" not in src)
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    ok7 = (raised_all and non_ascii == 0 and no_update
           and cfg_after == cfg_bytes
           and b7 == (bal("usr:alice"), bal("usr:bob"), bal("usr:carol"))
           and inv7 == len(prp.inventory("usr:alice")["cosmetics"])
           and occ7 == len(ven.occupancy_ledger("room:sky-villa")))
    record("AC-ID7", ok7, "all bad args rejected (%s); zero side effects"
          " (balances %s unchanged; inventory %d and occupancy %d"
          " unchanged); module pure ASCII (%d non-ascii); zero UPDATE"
          " surface; config.json byte-stable"
          % ("; ".join(bad), b7, inv7, occ7, non_ascii))

    idf.close()
    prp.close()
    ven.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
