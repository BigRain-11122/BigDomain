"""Cross-restart persistence window for the enterprise-showroom
SaaS package face (BigDomain R1950; the showroom seat of the
R1886 persist-family lineage - the R1945-seeded row, criteria
AC-SHWP1..AC-SHWP7 pre-registered in the R1950 tech.md claim row
BEFORE this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Four-instance-piece world on the real product path: anchor world
(ledger + venue + ads + showroom face, the bundle granted only
through the venue/ads public APIs) -> close all four pieces ->
reopen the same db/config -> byte-identical read replay ->
restart-surviving gate probes (twelve, zero drift) ->
post-restart real-path continuation (a fresh enterprise first
contract + a same-package third-window renewal advance booking,
both binding two real spend txs each) -> frozen rows + replay
gates across restart -> pure-read law -> third instance
stability. The read battery spans all six showroom read faces
plus the two referenced products' public read faces
(carousel_lineup, occupancy_ledger); evidence digests mask the
spend-tx ids and the package registered_utc stamps (banded
projection, R1902/R1949 law) so the suite stdout stays
deterministic across double runs while full dumps still carry
the fields for the in-process byte-identity comparisons.

Usage: python test_showroom_persist.py
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
import ads as A             # noqa: E402  (R622 ads product)
import showroom as S        # noqa: E402  (R1695 showroom face)

RESULTS = []

_MASK_RE = re.compile(
    r'"(?:[a-z_]*spend_tx|bound_spend_tx|registered_utc)": "[^"]*"')

DISCLAIMER = ("sandbox stand-in disclaimer: enterprise showroom"
             " packages are city showcase space, not investment"
             " advice; the platform stands in the ad-publisher"
             " posture of Advertising Law Article 56")

UNITS = ("showroom:ent-showroom-a:usr:alice",
         "showroom:ent-showroom-b:usr:bob",
         "showroom:ent-showroom-b:usr:carol",
         "showroom:ent-showroom-c:usr:bob",
         "showroom:ent-showroom-c:usr:carol",
         "quant-screen-1", "quant-screen-solo")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_sr_error(fn, *codes):
    try:
        fn()
    except S.ShowroomError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    return _MASK_RE.sub(
        lambda m: m.group(0).split(":")[0] + ': "<masked>"', text)


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
    out["packages"] = int(conn.execute(
        "SELECT COUNT(*) FROM showroom_packages").fetchone()[0])
    out["contracts"] = int(conn.execute(
        "SELECT COUNT(*) FROM showroom_contracts").fetchone()[0])
    out["stops"] = int(conn.execute(
        "SELECT COUNT(*) FROM showroom_tour_stops").fetchone()[0])
    out["occupancy"] = int(conn.execute(
        "SELECT COUNT(*) FROM venue_occupancy WHERE unit_id LIKE"
        " 'showroom:%' OR unit_id IN ('quant-screen-1',"
        " 'quant-screen-solo')").fetchone()[0])
    out["ledger_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def raw_rows(db_path):
    """Raw persistence semantics: the three showroom tables'
    full rows, ordered, plus the occupancy rows of the world
    units (tuple lists; registered_utc kept - in-process law)."""
    conn = sqlite3.connect(db_path)
    pkgs = conn.execute(
        "SELECT pkg_id, pkg_key, title, lease_term_windows,"
        " lease_price_per_window, rotation_unit, rotation_windows,"
        " rotation_price_per_window, tour_circuits, subscriber_cap,"
        " ai_label, registered_utc FROM showroom_packages"
        " ORDER BY pkg_id").fetchall()
    contracts = conn.execute(
        "SELECT contract_id, pkg_id, enterprise_id, contract_ref,"
        " start_tick, lease_end_tick, lease_unit, rotation_unit,"
        " lease_fee, rotation_fee, lease_spend_tx, rotation_spend_tx,"
        " subscribed_utc FROM showroom_contracts ORDER BY"
        " contract_id").fetchall()
    stops = conn.execute(
        "SELECT stop_id, contract_id, pkg_id, circuit_no,"
        " stop_position, created_utc FROM showroom_tour_stops"
        " ORDER BY stop_id").fetchall()
    occ = conn.execute(
        "SELECT kind, unit_id, account_id, start_tick, end_tick,"
        " terminated_tick, bound_spend_tx FROM venue_occupancy"
        " WHERE unit_id IN (?,?,?,?,?,?,?) ORDER BY occ_id",
        UNITS).fetchall()
    conn.close()
    return {"pkgs": pkgs, "contracts": contracts, "stops": stops,
            "occ": occ}


def spend_cross(db_path, tx_id, account_id):
    """SQL cross: the bound spend tx is a real ledger spend row
    with a debit leg on the subscribing account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = 'debit'",
        (tx_id, account_id)).fetchone()
    conn.close()
    return (head[0] if head else None), (leg[0] if leg else None)


def read_battery(sf, adz, ven, led):
    return {
        "pv_a": dump(sf.package_view(1)),
        "pv_b": dump(sf.package_view(2)),
        "pv_c": dump(sf.package_view(3)),
        "pv_d": dump(sf.package_view(4)),
        "line_a100": dump(sf.showroom_lineup(1, 100)),
        "line_a102": dump(sf.showroom_lineup(1, 102)),
        "line_a200": dump(sf.showroom_lineup(1, 200)),
        "line_a500": dump(sf.showroom_lineup(1, 500)),
        "line_b11": dump(sf.showroom_lineup(2, 11)),
        "line_b12": dump(sf.showroom_lineup(2, 12)),
        "line_c301": dump(sf.showroom_lineup(3, 301)),
        "line_c311": dump(sf.showroom_lineup(3, 311)),
        "it_a1": dump(sf.tour_itinerary(1, 1)),
        "it_a2": dump(sf.tour_itinerary(1, 2)),
        "it_b1": dump(sf.tour_itinerary(2, 1)),
        "it_c1": dump(sf.tour_itinerary(3, 1)),
        "cv1": dump(sf.contract_view(1)),
        "cv2": dump(sf.contract_view(2)),
        "cv3": dump(sf.contract_view(3)),
        "cv4": dump(sf.contract_view(4)),
        "cv5": dump(sf.contract_view(5)),
        "cv6": dump(sf.contract_view(6)),
        "cl1_100": dump(adz.carousel_lineup("quant-screen-1", 100)),
        "cl1_10": dump(adz.carousel_lineup("quant-screen-1", 10)),
        "cl1_12": dump(adz.carousel_lineup("quant-screen-1", 12)),
        "cls_301": dump(adz.carousel_lineup("quant-screen-solo", 301)),
        "cls_311": dump(adz.carousel_lineup("quant-screen-solo", 311)),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_dave": led.balance("usr:dave")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def occupancy_history(ven):
    return {u: dump(ven.occupancy_ledger(u)) for u in UNITS}


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def probe_batch(sf):
    """The twelve-gate probe battery: returns 'label=code' strings
    (or 'label NOT-RAISED(...)'), zero charge / zero rows by
    construction (every showroom gate rejects BEFORE the first
    spend)."""
    out = []
    specs = (
        ("dup-sub", lambda: sf.subscribe_enterprise(
            "usr:alice", "ent-showroom-a", 105, "order:shp1"),
         S.E_SR_DUP_SUB),
        ("overlap", lambda: sf.subscribe_enterprise(
            "usr:alice", "ent-showroom-a", 103, "order:shpX1"),
         S.E_SR_ACTIVE_CONTRACT),
        ("sold-out", lambda: sf.subscribe_enterprise(
            "usr:dave", "ent-showroom-b", 14, "order:shpX2"),
         S.E_SR_SOLD_OUT),
        ("rotation-full", lambda: sf.subscribe_enterprise(
            "usr:carol", "ent-showroom-c", 301, "order:shpX3"),
         S.E_SR_ROTATION_FULL),
        ("rotation-unit", lambda: sf.subscribe_enterprise(
            "usr:dave", "ent-showroom-d", 20, "order:shpX4"),
         S.E_SR_ROTATION_UNIT),
        ("bad-account", lambda: sf.subscribe_enterprise(
            "pool:reserve", "ent-showroom-a", 300, "order:shpX5"),
         S.E_SR_BAD_ACCOUNT),
        ("empty-ref", lambda: sf.subscribe_enterprise(
            "usr:dave", "ent-showroom-a", 300, "  "),
         S.E_SR_BAD_ARGS),
        ("bool-tick", lambda: sf.subscribe_enterprise(
            "usr:dave", "ent-showroom-a", True, "order:shpX6"),
         S.E_SR_BAD_ARGS),
        ("unknown-pkg", lambda: sf.subscribe_enterprise(
            "usr:dave", "ghost-pkg", 300, "order:shpX7"),
         S.E_SR_UNKNOWN_PKG),
        ("unknown-contract", lambda: sf.contract_view(999),
         S.E_SR_UNKNOWN_CONTRACT),
        ("bad-lineup-tick", lambda: sf.showroom_lineup(1, "x"),
         S.E_SR_BAD_ARGS),
        ("bad-circuit", lambda: sf.tour_itinerary(1, 3),
         S.E_SR_BAD_ARGS),
    )
    for label, fn, code in specs:
        ok_one, got = expect_sr_error(fn, code)
        out.append("%s=%s" % (label, got) if ok_one else
                   "%s NOT-RAISED(%s)" % (label, got))
    return out


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="showroom-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    srmod_sha_before = sha16(io_read(os.path.join(BASE, "showroom.py")))
    vnmod_sha_before = sha16(io_read(os.path.join(BASE, "venue.py")))
    admod_sha_before = sha16(io_read(os.path.join(BASE, "ads.py")))
    ledmod_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    # ---- instance 1: anchor world on the real product path ------
    led = L.Ledger(db_path, cfg)
    ven = V.VenueFace(led)
    adz = A.AdsFace(led, ven)
    sf = S.ShowroomFace(led, ven, adz, DISCLAIMER)

    adz.register_ad_unit("quant-screen-1", "quant_screen_carousel",
                         rotation_slots=2)
    adz.register_ad_unit("quant-screen-solo", "quant_screen_carousel",
                         rotation_slots=1)

    led.mint_to_pool("pool:reserve", 4000, "SETTLE-SHWP-A", "settlement")
    for who, tag in (("alice", "a"), ("bob", "b"), ("carol", "c"),
                     ("dave", "d")):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:shwp-fund-" + tag,
                   "persist window funding " + who)

    sf.register_package("ent-showroom-a", "Enterprise Hall A", 4, 10,
                        "quant-screen-1", 2, 5, 2, False)
    sf.register_package("ent-showroom-b", "Showroom B", 2, 3,
                        "quant-screen-1", 1, 4, 1, True, 2)
    sf.register_package("ent-showroom-c", "Showroom C", 3, 2,
                        "quant-screen-solo", 4, 3, 1, False)
    sf.register_package("ent-showroom-d", "Showroom D", 2, 2,
                        "ghost-screen", 1, 2, 1, False)

    sub1 = sf.subscribe_enterprise("usr:alice", "ent-showroom-a", 100,
                                   "order:shp1")
    sub2 = sf.subscribe_enterprise("usr:alice", "ent-showroom-a", 200,
                                   "order:shp2")
    sub3 = sf.subscribe_enterprise("usr:bob", "ent-showroom-b", 10,
                                   "order:shp3")
    sub4 = sf.subscribe_enterprise("usr:carol", "ent-showroom-b", 12,
                                   "order:shp4")
    sub5 = sf.subscribe_enterprise("usr:bob", "ent-showroom-c", 300,
                                   "order:shp5")
    sub6 = sf.subscribe_enterprise("usr:carol", "ent-showroom-c", 310,
                                   "order:shp6")

    # -- AC-SHWP1 control anchor: world pinned + gate probes ------
    bat1 = read_battery(sf, adz, ven, led)
    hist1 = occupancy_history(ven)
    rows1 = raw_rows(db_path)
    cnt1 = table_counts(db_path)
    fees = [(s["lease_fee"], s["rotation_fee"], s["ai_label"])
            for s in (sub1, sub2, sub3, sub4, sub5, sub6)]
    ent_ids = {s["contract_id"]: s["enterprise_id"]
              for s in (sub1, sub2, sub3, sub4, sub5, sub6)}
    ok_world = (
        fees == [(40, 10, 0), (40, 10, 0), (6, 4, 1), (6, 4, 1),
                 (6, 12, 0), (6, 12, 0)]
        and all(s["disclaimer"] == DISCLAIMER
                for s in (sub1, sub2, sub3, sub4, sub5, sub6))
        and ent_ids == {1: "usr:alice", 2: "usr:alice", 3: "usr:bob",
                        4: "usr:carol", 5: "usr:bob", 6: "usr:carol"}
        and bat1["bal_alice"] == 200 and bat1["bal_bob"] == 272
        and bat1["bal_carol"] == 272 and bat1["bal_dave"] == 300
        and bat1["bal_pool"] == 2956
        and cnt1 == {"packages": 4, "contracts": 6, "stops": 8,
                     "occupancy": 12, "ledger_tx": 17,
                     "spend_tx": 12}
        and [c["enterprise_id"] for c in
             json.loads(bat1["line_a100"])["contracts"]] == ["usr:alice"]
        and [c["enterprise_id"] for c in
             json.loads(bat1["line_b11"])["contracts"]] == ["usr:bob"]
        and [c["enterprise_id"] for c in
             json.loads(bat1["line_b12"])["contracts"]] == ["usr:carol"]
        and json.loads(bat1["line_a500"])["contracts"] == []
        and [s["stop_position"] for s in
             json.loads(bat1["it_a1"])["stops"]] == [1, 2]
        and [s["stop_position"] for s in
             json.loads(bat1["it_b1"])["stops"]] == [1, 2]
        and json.loads(bat1["cv1"])["tour_stops"] == [
            {"circuit_no": 1, "stop_position": 1},
            {"circuit_no": 2, "stop_position": 1}]
        and [a["account_id"] for a in
             json.loads(bat1["cl1_100"])["advertisers"]] == ["usr:alice"]
        and [a["account_id"] for a in
             json.loads(bat1["cl1_10"])["advertisers"]] == ["usr:bob"]
        and [a["account_id"] for a in
             json.loads(bat1["cls_301"])["advertisers"]] == ["usr:bob"]
        and [a["account_id"] for a in
             json.loads(bat1["cls_311"])["advertisers"]] == ["usr:carol"]
        and len(rows1["pkgs"]) == 4 and len(rows1["contracts"]) == 6
        and len(rows1["stops"]) == 8 and len(rows1["occ"]) == 12)
    probes1 = probe_batch(sf)
    ok_probes1 = all("NOT-RAISED" not in p for p in probes1)
    ok_probe_drift1 = (table_counts(db_path) == cnt1
                       and read_battery(sf, adz, ven, led) == bat1
                       and raw_rows(db_path) == rows1)
    ok1 = ok_world and ok_probes1 and ok_probe_drift1
    record("AC-SHWP1", ok1, "anchor world pinned (four packages:"
          " a lease 4x10 + rotation 2x5 two circuits uncapped,"
          " b 2x3 + 1x4 one circuit cap-2 ai=1, c 3x2 + 4x3 on the"
          " single-slot screen, d ghost rotation unit; six"
          " contracts: alice a@100 + a@200 (same package, distinct"
          " windows), bob b@10 + c@300, carol b@12 + c@310; fees"
          " (lease,rotation) = 40+10/40+10/6+4/6+4/6+12/6+12;"
          " balances 200/272/272/300/2956; counts packages=4"
          " contracts=6 stops=8 occupancy=12 spend-tx=12 of"
          " ledger-tx=17; lineup/itinerary/contract/carousel"
          " faces all pinned; all rows carry the disclaimer);"
          " twelve gate probes rejected (%s); counts, battery and"
          " raw rows frozen across the probe batch; digest=%s" % (
              "; ".join(probes1), evidence_digest(bat1)))

    # -- AC-SHWP2 cross-restart byte-identical replay --------------
    sf.close()
    adz.close()
    ven.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    ven2 = V.VenueFace(led2)
    adz2 = A.AdsFace(led2, ven2)
    sf2 = S.ShowroomFace(led2, ven2, adz2, DISCLAIMER)
    bat2 = read_battery(sf2, adz2, ven2, led2)
    hist2 = occupancy_history(ven2)
    rows2 = raw_rows(db_path)
    diffs2 = battery_diffs(bat1, bat2)
    hist_diffs2 = [u for u in hist1 if hist1[u] != hist2[u]]
    ok2 = (not diffs2 and not hist_diffs2 and rows2 == rows1)
    record("AC-SHWP2", ok2, "four-piece close->reopen (sf.close ->"
          " adz.close -> ven.close -> led.close -> Ledger same"
          " db/cfg + VenueFace + AdsFace + fresh ShowroomFace): the"
          " full read battery (four package views + eight lineups"
          " + four itineraries + six contract views + five carousel"
          " reads + five balances), all seven occupancy histories"
          " AND the raw three-table rows replay byte-identical to"
          " the pre-close snapshots, diffs=%s/%s/%s; packages,"
          " contract rows (windows, both bound spend txs), tour"
          " stops and the twelve occupancy rows all persist with"
          " zero in-memory drift; digest=%s" % (
              diffs2 or "none", hist_diffs2 or "none",
              "none" if rows2 == rows1 else "rows",
              evidence_digest(bat2)))

    # -- AC-SHWP3 gates survive restart, zero drift ----------------
    probes2 = probe_batch(sf2)
    ok_probes2 = all("NOT-RAISED" not in p for p in probes2)
    ok_drift2 = (table_counts(db_path) == cnt1
                 and read_battery(sf2, adz2, ven2, led2) == bat2
                 and occupancy_history(ven2) == hist2
                 and raw_rows(db_path) == rows2)
    ok3 = ok_probes2 and probes2 == probes1 and ok_drift2
    record("AC-SHWP3", ok3, "restart-surviving gates: all twelve"
          " probes rejected with identical codes on instance 2 and"
          " in the same order as instance 1 (%s); counts, battery,"
          " occupancy histories and raw rows frozen across the"
          " probe batch (packages/contracts/stops/occupancy"
          " %d/%d/%d/%d unchanged, zero charge, zero rows)" % (
              "; ".join(probes2), cnt1["packages"],
              cnt1["contracts"], cnt1["stops"], cnt1["occupancy"]))

    # -- AC-SHWP4 post-restart real-path continuation ---------------
    sub7 = sf2.subscribe_enterprise("usr:dave", "ent-showroom-a", 300,
                                    "order:shp7")
    sub8 = sf2.subscribe_enterprise("usr:alice", "ent-showroom-a", 400,
                                    "order:shp8")
    head_l7, leg_l7 = spend_cross(db_path, sub7["lease_spend_tx"],
                                  "usr:dave")
    head_r7, leg_r7 = spend_cross(db_path, sub7["rotation_spend_tx"],
                                  "usr:dave")
    head_l8, leg_l8 = spend_cross(db_path, sub8["lease_spend_tx"],
                                  "usr:alice")
    head_r8, leg_r8 = spend_cross(db_path, sub8["rotation_spend_tx"],
                                  "usr:alice")
    dup7, code_d7 = expect_sr_error(
        lambda: sf2.subscribe_enterprise(
            "usr:dave", "ent-showroom-a", 305, "order:shp7"),
        S.E_SR_DUP_SUB)
    sold13, code_s13 = expect_sr_error(
        lambda: sf2.subscribe_enterprise(
            "usr:bob", "ent-showroom-b", 13, "order:shpX8"),
        S.E_SR_SOLD_OUT)
    ov11, code_o11 = expect_sr_error(
        lambda: sf2.subscribe_enterprise(
            "usr:carol", "ent-showroom-c", 311, "order:shpX9"),
        S.E_SR_ACTIVE_CONTRACT)
    bat4 = read_battery(sf2, adz2, ven2, led2)
    cnt4 = table_counts(db_path)
    it_a1_after = json.loads(dump(sf2.tour_itinerary(1, 1)))
    ok4 = (
        sub7["contract_id"] == 7 and sub8["contract_id"] == 8
        and sub7["lease_fee"] == 40 and sub7["rotation_fee"] == 10
        and sub8["lease_fee"] == 40 and sub8["rotation_fee"] == 10
        and head_l7 == "spend" and leg_l7 == "debit"
        and head_r7 == "spend" and leg_r7 == "debit"
        and head_l8 == "spend" and leg_l8 == "debit"
        and head_r8 == "spend" and leg_r8 == "debit"
        and dup7 and code_d7 == S.E_SR_DUP_SUB
        and sold13 and code_s13 == S.E_SR_SOLD_OUT
        and ov11 and code_o11 == S.E_SR_ACTIVE_CONTRACT
        and cnt4 == {"packages": 4, "contracts": 8, "stops": 12,
                     "occupancy": 16, "ledger_tx": 21,
                     "spend_tx": 16}
        and bat4["bal_dave"] == 250 and bat4["bal_alice"] == 150
        and bat4["bal_pool"] == 3056
        and [c["enterprise_id"] for c in
             json.loads(bat4["line_a500"])["contracts"]] == []
        and [(s["stop_position"], s["enterprise_id"])
             for s in it_a1_after["stops"]] ==
        [(1, "usr:alice"), (2, "usr:alice"), (3, "usr:dave"),
         (4, "usr:alice")]
        and json.loads(dump(sf2.contract_view(7)))["tour_stops"] ==
        [{"circuit_no": 1, "stop_position": 3},
         {"circuit_no": 2, "stop_position": 3}]
        and [a["account_id"] for a in
             json.loads(bat4["cl1_100"])["advertisers"]] == ["usr:alice"])
    record("AC-SHWP4", ok4, "post-restart continuation: dave"
          " subscribes a@300 (fresh enterprise first contract, fee"
          " 50) and alice subscribes a@400 (same-package third"
          " window renewal advance booking, fee 50) - both bind two"
          " real spend txs each (SQL cross type=spend with debit"
          " legs on the right accounts, tx ids not echoed); the"
          " three restart-surviving gates live on the new state:"
          " dave same-ref replay rejected %s, bob hitting the"
          " cap-2 package at a fresh window rejected %s (cap"
          " persists across restart), carol self-overlap on c"
          " rejected %s (all zero charge); read faces recompute"
          " zero-cache (itinerary a circuit 1 grew to positions"
          " 1/2/3/4 = alice,alice,dave,alice; contract 7 carries"
          " its two circuit stops); registry untouched by"
          " subscribing (still 4 packages); contracts 6->8, stops"
          " 8->12, occupancy 12->16, spend-tx 12->16; balances"
          " dave 250, alice 150, pool 3056; digest=%s" % (
              code_d7, code_s13, code_o11, evidence_digest(bat4)))

    # -- AC-SHWP5 frozen rows + replay/idempotence gates ----------
    # prefix law (R1947 AC-EFP5 family): the continuation
    # legitimately appends new occupancy rows, so the freeze claim
    # is that every pre-restart row survives as the byte-identical
    # prefix of the post-continuation history (row-level prefix on
    # the parsed row lists).
    hist5 = occupancy_history(ven2)

    def hist_rows(hist):
        return {u: json.loads(hist[u]) for u in hist}

    rows_h1, rows_h5 = hist_rows(hist1), hist_rows(hist5)
    frozen_hist = all(
        rows_h5[u][:len(rows_h1[u])] == rows_h1[u] for u in rows_h1)
    rows5 = raw_rows(db_path)
    frozen_tables = (rows5["pkgs"] == rows1["pkgs"]
                     and rows5["contracts"][:6] == rows1["contracts"]
                     and rows5["stops"][:8] == rows1["stops"])
    dup_pkg, code_dp = expect_sr_error(
        lambda: sf2.register_package(
            "ent-showroom-a", "Again", 4, 10, "quant-screen-1",
            2, 5, 2, False),
        S.E_SR_DUP_PKG)
    far_line = sf2.showroom_lineup(1, 9000)
    ok5 = (frozen_hist and frozen_tables and dup_pkg
           and code_dp == S.E_SR_DUP_PKG
           and far_line["contracts"] == []
           and table_counts(db_path) == cnt4
           and read_battery(sf2, adz2, ven2, led2) == bat4)
    record("AC-SHWP5", ok5, "frozen faces: every pre-restart"
          " occupancy row keeps all persisted fields byte-identical"
          " - the anchor histories replay as the exact byte-identical"
          " prefix of the post-continuation histories (kind/account"
          "/start/end/terminated/bound_spend_tx; the continuation"
          " only appended new rows, prefix law) - and the raw"
          " package rows, the six anchor contract rows and the"
          " eight anchor stop rows are byte-identical including"
          " their registered_utc/subscribed_utc/created_utc stamps"
          " (rows immutable, zero mutation surface); package"
          " re-registration across restart rejected %s (zero new"
          " rows); far-future lineup honest-empty (a@9000 = []);"
          " counts and battery frozen (%d/%d/%d/%d)" % (
              code_dp, cnt4["packages"], cnt4["contracts"],
              cnt4["stops"], cnt4["occupancy"]))

    # -- AC-SHWP6 pure-read law -------------------------------------
    bat_a = read_battery(sf2, adz2, ven2, led2)
    bat_b = read_battery(sf2, adz2, ven2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and occupancy_history(ven2) == hist5
           and table_counts(db_path) == cnt4)
    record("AC-SHWP6", ok6, "pure-read law: full battery (package"
          " views + lineups + itineraries + contract views +"
          " carousel reads + balances) and the seven occupancy"
          " histories read twice back-to-back - all byte-identical"
          " between the two reads and table counts constant"
          " (showroom read faces have zero side effects, zero"
          " token movement)")

    # -- AC-SHWP7 third instance stability + hygiene ----------------
    sf2.close()
    adz2.close()
    ven2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    ven3 = V.VenueFace(led3)
    adz3 = A.AdsFace(led3, ven3)
    sf3 = S.ShowroomFace(led3, ven3, adz3, DISCLAIMER)
    bat3 = read_battery(sf3, adz3, ven3, led3)
    diffs3 = battery_diffs(bat_b, bat3)
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
           and sha16(io_read(os.path.join(BASE, "showroom.py")))
           == srmod_sha_before
           and sha16(io_read(os.path.join(BASE, "venue.py")))
           == vnmod_sha_before
           and sha16(io_read(os.path.join(BASE, "ads.py")))
           == admod_sha_before
           and sha16(io_read(os.path.join(BASE, "ledger.py")))
           == ledmod_sha_before
           and non_ascii == 0 and not net_imports
           and not os.path.realpath(tmp).startswith(repo_root))
    record("AC-SHWP7", ok7, "third instance: close all four pieces"
          " once more -> reopen same db - battery AND occupancy"
          " histories byte-identical to the instance-2 terminal"
          " state (diffs=%s; packages, contract windows, tour"
          " stops, gate behavior all stable across a second"
          " restart); shipped files untouched (config/showroom"
          "/venue/ads/ledger sha16 stable); suite source pure"
          " ASCII (%d non-ascii), zero network imports (%d hits),"
          " world tmp outside repo (%s)" % (
              diffs3 or "none", non_ascii, len(net_imports),
              "yes" if not os.path.realpath(tmp).startswith(
                  repo_root) else "NO"))

    sf3.close()
    adz3.close()
    ven3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
