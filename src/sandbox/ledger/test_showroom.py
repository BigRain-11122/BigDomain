"""Acceptance suite for the enterprise-showroom SaaS package
face (BigDomain R1695; canon = explore-queue enterprise-showroom
SaaS row: the annual package bundles an exclusive showroom
storefront lease + a QUANT giant-screen carousel rotation share +
a visitor-tour stop, riding the ads/venue B3 schedule-window
structure). Asserts the pre-registered criteria AC-SR1..AC-SR7
from the R1695 explore-queue row (criteria were registered
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

The venue and ads faces are the real products injected by
reference (no copy); the showroom module reaches them only
through their public APIs. This test source stays pure ASCII per
the encoding discipline.

Usage: python test_showroom.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ledger as L                      # noqa: E402 (P-47-2b core)
import venue as V                       # noqa: E402 (R605 product)
import ads as A                         # noqa: E402 (R622 product)
import showroom as S                    # noqa: E402 (R1695 face)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: enterprise showroom"
             " packages are city showcase space, not investment"
             " advice; the platform stands in the ad-publisher"
             " posture of Advertising Law Article 56")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_sr_error(fn, *codes):
    try:
        fn()
    except S.ShowroomError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


class _WrongDbVenue(object):
    """Wiring probe: a venue surface with a foreign db_path - the
    face must refuse construction (shared-file law, AC-SR6)."""

    db_path = "not-the-ledger.db"

    def lease_storefront(self, *args, **kwargs):
        raise AssertionError("must not be called")


class _WrongDbAds(object):
    """Wiring probe: an ads surface whose venue rides a foreign DB."""

    class _ven(object):
        db_path = "not-the-ledger.db"

    ven = _ven()

    def book(self, *args, **kwargs):
        raise AssertionError("must not be called")

    def carousel_lineup(self, *args, **kwargs):
        raise AssertionError("must not be called")


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="showroom-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    ven = V.VenueFace(led)
    adz = A.AdsFace(led, ven)
    sf = S.ShowroomFace(led, ven, adz, DISCLAIMER)

    adz.register_ad_unit("quant-screen-1", "quant_screen_carousel",
                         rotation_slots=2)
    adz.register_ad_unit("quant-screen-solo", "quant_screen_carousel",
                         rotation_slots=1)

    led.mint_to_pool("pool:reserve", 4000, "SETTLE-SR-A", "settlement")
    for who, amount, tag in (("alice", 300, "a"), ("bob", 300, "b"),
                             ("carol", 300, "c"), ("dave", 300, "d")):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    bal = lambda who: led.balance("usr:" + who)["balance"]  # noqa: E731
    conn = sqlite3.connect(db_path)
    people = ("alice", "bob", "carol", "dave")

    # -- AC-SR1 package registry face ---------------------------------------
    pkg_a = sf.register_package("ent-showroom-a", "Enterprise Hall A",
                                4, 10, "quant-screen-1", 2, 5, 2, False)
    n_pkg0 = _count(conn, "showroom_packages")
    ok_dup, code_dup = expect_sr_error(
        lambda: sf.register_package("ent-showroom-a", "Again", 4, 10,
                                    "quant-screen-1", 2, 5, 2, False),
        S.E_SR_DUP_PKG)
    n_pkg1 = _count(conn, "showroom_packages")
    pkg_b = sf.register_package("ent-showroom-b", "Showroom B",
                                2, 3, "quant-screen-1", 1, 4, 1, True, 2)
    n_pkg2 = _count(conn, "showroom_packages")
    bad1 = []
    raised1 = True
    for label, fn, code in (
            ("empty key", lambda: sf.register_package(
                " ", "t", 1, 1, "u", 1, 1, 1, False), S.E_SR_BAD_PKG),
            ("none key", lambda: sf.register_package(
                None, "t", 1, 1, "u", 1, 1, 1, False), S.E_SR_BAD_PKG),
            ("empty title", lambda: sf.register_package(
                "k", "  ", 1, 1, "u", 1, 1, 1, False), S.E_SR_BAD_PKG),
            ("term 0", lambda: sf.register_package(
                "k", "t", 0, 1, "u", 1, 1, 1, False), S.E_SR_BAD_PKG),
            ("bool term", lambda: sf.register_package(
                "k", "t", True, 1, "u", 1, 1, 1, False), S.E_SR_BAD_PKG),
            ("zero lease price", lambda: sf.register_package(
                "k", "t", 1, 0, "u", 1, 1, 1, False), S.E_SR_BAD_PKG),
            ("bool lease price", lambda: sf.register_package(
                "k", "t", 1, True, "u", 1, 1, 1, False), S.E_SR_BAD_PKG),
            ("empty rotation unit", lambda: sf.register_package(
                "k", "t", 1, 1, "  ", 1, 1, 1, False), S.E_SR_BAD_PKG),
            ("rotation windows 0", lambda: sf.register_package(
                "k", "t", 1, 1, "u", 0, 1, 1, False), S.E_SR_BAD_PKG),
            ("zero rotation price", lambda: sf.register_package(
                "k", "t", 1, 1, "u", 1, 0, 1, False), S.E_SR_BAD_PKG),
            ("circuits 0", lambda: sf.register_package(
                "k", "t", 1, 1, "u", 1, 1, 0, False), S.E_SR_BAD_PKG),
            ("cap 0", lambda: sf.register_package(
                "k", "t", 1, 1, "u", 1, 1, 1, False, 0), S.E_SR_BAD_PKG),
            ("non-bool ai flag", lambda: sf.register_package(
                "k", "t", 1, 1, "u", 1, 1, 1, "yes"), S.E_SR_BAD_PKG)):
        ok_one, got = expect_sr_error(fn, code)
        if ok_one:
            bad1.append("%s=%s" % (label, got))
        else:
            bad1.append("%s NOT-RAISED(%s)" % (label, got))
            raised1 = False
    n_pkg3 = _count(conn, "showroom_packages")
    ok1 = (pkg_a["ai_label"] == 0 and pkg_b["ai_label"] == 1
           and pkg_a["subscriber_cap"] is None
           and pkg_b["subscriber_cap"] == 2
           and pkg_a["tour_circuits"] == 2 and pkg_b["tour_circuits"] == 1
           and ok_dup and code_dup == S.E_SR_DUP_PKG
           and n_pkg0 == 1 and n_pkg1 == 1 and n_pkg2 == 2
           and n_pkg3 == 2 and raised1)
    record("AC-SR1", ok1, "one row per pkg_key: %d rows after 2 legal"
          " registrations; same-key re-registration rejected %s with"
          " zero rows (%d==%d); declared labels persist (a=%d b=%d);"
          " cap None legal / cap 2 legal; circuits 2/1; all %d bad"
          " params rejected (%s)"
          % (n_pkg2, code_dup, n_pkg1, n_pkg2, pkg_a["ai_label"],
             pkg_b["ai_label"], len(bad1), "; ".join(bad1)))

    # -- AC-SR2 bundle grant through the two public APIs ---------------------
    b_alice0 = bal("alice")
    sub_a = sf.subscribe_enterprise("usr:alice", "ent-showroom-a", 100,
                                    "order:sr2a")
    b_alice1 = bal("alice")
    lease_row = conn.execute(
        "SELECT bound_spend_tx FROM venue_occupancy"
        " WHERE kind = 'storefront' AND unit_id = ?"
        " AND account_id = 'usr:alice'",
        ("showroom:ent-showroom-a:usr:alice",)).fetchall()
    rot_row = conn.execute(
        "SELECT bound_spend_tx FROM venue_occupancy"
        " WHERE kind = 'venue' AND unit_id = 'quant-screen-1'"
        " AND account_id = 'usr:alice'").fetchall()
    lineup = adz.carousel_lineup("quant-screen-1", 101)
    lineup_ids = [r["account_id"] for r in lineup["advertisers"]]
    tx_types = [conn.execute(
        "SELECT type FROM ledger_tx WHERE tx_id = ?",
        (tx,)).fetchone() for tx in (sub_a["lease_spend_tx"],
                                     sub_a["rotation_spend_tx"])]
    tx_legs = [conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:alice'", (tx,)).fetchone()
        for tx in (sub_a["lease_spend_tx"], sub_a["rotation_spend_tx"])]
    n_contract = _count(conn, "showroom_contracts")
    with open(os.path.join(BASE, "showroom.py"), encoding="utf-8") as h:
        src = h.read()
    ok2 = (sub_a["lease_fee"] == 40 and sub_a["rotation_fee"] == 10
           and sub_a["tour_circuits"] == 2 and sub_a["ai_label"] == 0
           and b_alice1 == b_alice0 - 50
           and len(lease_row) == 1
           and lease_row[0][0] == sub_a["lease_spend_tx"]
           and len(rot_row) == 1
           and rot_row[0][0] == sub_a["rotation_spend_tx"]
           and lineup_ids == ["usr:alice"]
           and all(t is not None and t[0] == "spend" for t in tx_types)
           and all(g is not None and g[0] == "debit" for g in tx_legs)
           and n_contract == 1
           and "INSERT INTO venue_occupancy" not in src
           and "INSERT INTO ad_units" not in src
           and "INSERT INTO venue_registry" not in src
           and sub_a["disclaimer"] == DISCLAIMER)
    record("AC-SR2", ok2, "bundle granted through the two public APIs:"
          " lease component -> VenueFace.lease_storefront (storefront"
          " row on showroom:ent-showroom-a:usr:alice bound to spend %s)"
          " + rotation component -> AdsFace.book (venue row on"
          " quant-screen-1 bound to spend %s; carousel_lineup(101)"
          " = %s); package charge = lease 40 + rotation 10 = 50"
          " exactly (%d->%d); both txs type=spend with debit legs;"
          " contract row binds both txs (%d row); module source"
          " writes zero venue/ad rows (no second engine)"
          % (sub_a["lease_spend_tx"], sub_a["rotation_spend_tx"],
             lineup_ids, b_alice0, b_alice1, n_contract))

    # -- AC-SR3 replay + active-contract gates --------------------------------
    b0 = bal("alice")
    ok_replay, code_rp = expect_sr_error(
        lambda: sf.subscribe_enterprise("usr:alice", "ent-showroom-a",
                                        105, "order:sr2a"),
        S.E_SR_DUP_SUB)
    ok_overlap, code_ov = expect_sr_error(
        lambda: sf.subscribe_enterprise("usr:alice", "ent-showroom-a",
                                        103, "order:sr3a"),
        S.E_SR_ACTIVE_CONTRACT)
    b1 = bal("alice")
    sub_a2 = sf.subscribe_enterprise("usr:alice", "ent-showroom-a", 200,
                                     "order:sr3b")
    b2 = bal("alice")
    four_txs = (sub_a["lease_spend_tx"], sub_a["rotation_spend_tx"],
                sub_a2["lease_spend_tx"], sub_a2["rotation_spend_tx"])
    ok3 = (ok_replay and code_rp == S.E_SR_DUP_SUB
           and ok_overlap and code_ov == S.E_SR_ACTIVE_CONTRACT
           and b1 == b0
           and sub_a2["contract_id"] != sub_a["contract_id"]
           and b2 == b1 - 50
           and len(set(four_txs)) == 4)
    record("AC-SR3", ok3, "same-(enterprise,ref) replay rejected %s"
          " BEFORE any spend (balance %d==%d); overlapping"
          " active contract on the same package rejected %s"
          " before any spend (lease windows 100..103 vs 103..106;"
          " balance %d==%d); a non-overlapping later window is a"
          " legal second contract (distinct id, four distinct"
          " txs, charged once more %d->%d)"
          % (code_rp, b0, b1, code_ov, b0, b1, b1, b2))

    # -- AC-SR4 subscriber cap + rotation pre-read gate -----------------------
    pkg_c = sf.register_package("ent-showroom-c", "Showroom C",
                                3, 2, "quant-screen-solo", 4, 3, 1, False)
    pkg_d = sf.register_package("ent-showroom-d", "Showroom D",
                                2, 2, "ghost-screen", 1, 2, 1, False)
    sub_bb = sf.subscribe_enterprise("usr:bob", "ent-showroom-b", 10,
                                      "order:sr4a")
    sub_cb = sf.subscribe_enterprise("usr:carol", "ent-showroom-b", 12,
                                     "order:sr4b")
    b_dave0 = bal("dave")
    ok_sold, code_sd = expect_sr_error(
        lambda: sf.subscribe_enterprise("usr:dave", "ent-showroom-b",
                                        14, "order:sr4c"),
        S.E_SR_SOLD_OUT)
    b_dave1 = bal("dave")
    sub_bc = sf.subscribe_enterprise("usr:bob", "ent-showroom-c", 300,
                                      "order:sr4d")
    b_carol0 = bal("carol")
    ok_full, code_fl = expect_sr_error(
        lambda: sf.subscribe_enterprise("usr:carol", "ent-showroom-c",
                                        301, "order:sr4e"),
        S.E_SR_ROTATION_FULL)
    b_carol1 = bal("carol")
    carol_c_rows = conn.execute(
        "SELECT COUNT(*) FROM showroom_contracts"
        " WHERE enterprise_id = 'usr:carol' AND pkg_id = ?",
        (pkg_c["pkg_id"],)).fetchone()[0]
    carol_solo_rows = conn.execute(
        "SELECT COUNT(*) FROM venue_occupancy"
        " WHERE unit_id = 'quant-screen-solo'"
        " AND account_id = 'usr:carol'").fetchone()[0]
    sub_cc = sf.subscribe_enterprise("usr:carol", "ent-showroom-c", 310,
                                     "order:sr4f")
    ok_unit, code_un = expect_sr_error(
        lambda: sf.subscribe_enterprise("usr:dave", "ent-showroom-d",
                                        20, "order:sr4g"),
        S.E_SR_ROTATION_UNIT)
    b_dave2 = bal("dave")
    n_pkgA_contracts = conn.execute(
        "SELECT COUNT(*) FROM showroom_contracts WHERE pkg_id = ?",
        (pkg_a["pkg_id"],)).fetchone()[0]
    ok4 = (sub_bb["lease_fee"] == 6 and sub_bb["rotation_fee"] == 4
           and ok_sold and code_sd == S.E_SR_SOLD_OUT
           and b_dave1 == b_dave0
           and ok_full and code_fl == S.E_SR_ROTATION_FULL
           and b_carol1 == b_carol0
           and carol_c_rows == 0 and carol_solo_rows == 0
           and sub_cc["contract_id"] != sub_bc["contract_id"]
           and ok_unit and code_un == S.E_SR_ROTATION_UNIT
           and b_dave2 == b_dave0
           and n_pkgA_contracts == 2)
    record("AC-SR4", ok4, "cap-2 package: two distinct enterprises"
          " (bob, carol) subscribed, a third (dave) rejected %s"
          " before any spend with zero charge (%d==%d); rotation"
          " pre-read gate on the single-slot screen: bob's booking"
          " 300..303 fills it, carol's overlapping 301..304 rejected"
          " %s before any spend (zero charge %d==%d, zero contract"
          " rows, zero venue rows) while her non-overlapping 310"
          " window books legally (window-aware gate); missing"
          " rotation unit rejected %s zero charge (%d==%d); the"
          " uncapped package legally holds %d contracts"
          % (code_sd, b_dave0, b_dave1, code_fl, b_carol0, b_carol1,
             code_un, b_dave0, b_dave2, n_pkgA_contracts))

    # -- AC-SR5 visitor-tour itinerary face -----------------------------------
    b5 = {who: bal(who) for who in people}
    it_a1 = sf.tour_itinerary(pkg_a["pkg_id"], 1)
    it_a2 = sf.tour_itinerary(pkg_a["pkg_id"], 2)
    it_b1 = sf.tour_itinerary(pkg_b["pkg_id"], 1)
    stops_a1 = [(s["stop_position"], s["enterprise_id"], s["contract_ref"])
                for s in it_a1["stops"]]
    stops_a2 = [(s["stop_position"], s["enterprise_id"], s["contract_ref"])
                for s in it_a2["stops"]]
    stops_b1 = [(s["stop_position"], s["enterprise_id"])
                for s in it_b1["stops"]]
    sub_a_view = sf.contract_view(sub_a["contract_id"])
    sub_a2_view = sf.contract_view(sub_a2["contract_id"])
    ok_circ0, code_c0 = expect_sr_error(
        lambda: sf.tour_itinerary(pkg_a["pkg_id"], 0), S.E_SR_BAD_ARGS)
    ok_circ3, code_c3 = expect_sr_error(
        lambda: sf.tour_itinerary(pkg_a["pkg_id"], 3), S.E_SR_BAD_ARGS)
    ok_circx, code_cx = expect_sr_error(
        lambda: sf.tour_itinerary(pkg_a["pkg_id"], "x"), S.E_SR_BAD_ARGS)
    b5b = {who: bal(who) for who in people}
    ok5 = (stops_a1 == [(1, "usr:alice", "order:sr2a"),
                        (2, "usr:alice", "order:sr3b")]
           and stops_a2 == [(1, "usr:alice", "order:sr2a"),
                            (2, "usr:alice", "order:sr3b")]
           and stops_b1 == [(1, "usr:bob"), (2, "usr:carol")]
           and sub_a_view["tour_stops"] == [
               {"circuit_no": 1, "stop_position": 1},
               {"circuit_no": 2, "stop_position": 1}]
           and sub_a2_view["tour_stops"] == [
               {"circuit_no": 1, "stop_position": 2},
               {"circuit_no": 2, "stop_position": 2}]
           and ok_circ0 and ok_circ3 and ok_circx
           and b5 == b5b)
    record("AC-SR5", ok5, "each contract gets exactly one stop per"
          " circuit (pkg a: circuits 1 and 2, positions 1 then 2 in"
          " subscription order = %s / %s; pkg b single circuit:"
          " bob pos 1, carol pos 2); contract_view surfaces the"
          " stops (first %s, second %s); bad circuit numbers"
          " rejected %s/%s/%s; itinerary reads move zero tokens"
          " (balances unchanged)"
          % (stops_a1, stops_a2, sub_a_view["tour_stops"],
             sub_a2_view["tour_stops"], code_c0, code_c3, code_cx))

    # -- AC-SR6 AIGC label + disclaimer + platform posture + wiring ----------
    ok_no_dis, code_nd = expect_sr_error(
        lambda: S.ShowroomFace(led, ven, adz, "  "),
        S.E_SR_NO_DISCLAIMER)
    ok_no_ven, code_nv = expect_sr_error(
        lambda: S.ShowroomFace(led, None, adz, DISCLAIMER),
        S.E_SR_NO_VENUE)
    ok_wrong_ven, code_wv = expect_sr_error(
        lambda: S.ShowroomFace(led, _WrongDbVenue(), adz, DISCLAIMER),
        S.E_SR_NO_VENUE)
    ok_no_ads, code_na = expect_sr_error(
        lambda: S.ShowroomFace(led, ven, None, DISCLAIMER),
        S.E_SR_NO_ADS)
    ok_wrong_ads, code_wa = expect_sr_error(
        lambda: S.ShowroomFace(led, ven, _WrongDbAds(), DISCLAIMER),
        S.E_SR_NO_ADS)
    pv = sf.package_view(pkg_b["pkg_id"])
    line_a = sf.showroom_lineup(pkg_a["pkg_id"], 100)
    line_none = sf.showroom_lineup(pkg_a["pkg_id"], 500)
    cv = sf.contract_view(sub_bb["contract_id"])
    label_rejected = False
    try:
        conn.execute(
            "INSERT INTO showroom_packages (pkg_key, title,"
            " lease_term_windows, lease_price_per_window, rotation_unit,"
            " rotation_windows, rotation_price_per_window,"
            " tour_circuits, subscriber_cap, ai_label, registered_utc)"
            " VALUES ('x-key','t',1,1,'u',1,1,1,NULL,2,'t')")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        label_rejected = True
    ok6 = (ok_no_dis and code_nd == S.E_SR_NO_DISCLAIMER
           and ok_no_ven and code_wv and code_nv == S.E_SR_NO_VENUE
           and ok_wrong_ven
           and ok_no_ads and code_wa and code_na == S.E_SR_NO_ADS
           and ok_wrong_ads
           and pv["ai_label"] == 1 and pv["disclaimer"] == DISCLAIMER
           and pv["contract_count"] == 2 and pv["enterprise_count"] == 2
           and line_a["disclaimer"] == DISCLAIMER
           and [c["enterprise_id"] for c in line_a["contracts"]]
           == ["usr:alice"]
           and all(c["ai_label"] in (0, 1)
                   for c in line_a["contracts"])
           and line_none["contracts"] == []
           and it_a1["disclaimer"] == DISCLAIMER
           and cv["disclaimer"] == DISCLAIMER and cv["ai_label"] == 1
           and sub_a["ai_label"] == 0 and sub_bb["ai_label"] == 1
           and sub_a["disclaimer"] == DISCLAIMER
           and label_rejected
           and "check_text" not in src and "msgSecCheck" not in src)
    record("AC-SR6", ok6, "empty disclaimer refuses construction %s;"
          " unwired venue/ads or foreign-DB faces refuse construction"
          " (%s/%s, %s/%s); declared AIGC label on every presentation"
          " face (package_view %d, subscribe returns %d/%d, lineup rows,"
          " contract_view %d); direct SQL ai_label=2 refused by the"
          " CHECK (%s); all four view envelopes + the subscribe return"
          " carry the resident disclaimer; platform-side posture holds"
          " - zero resident text enters the module (no content gate"
          " wired, festival/ads precedent; Advertising-Law Article 56"
          " ad-publisher posture -> enterprise qualification"
          " verification is a bootstrap-window [needs-CEO] gate, any"
          " future enterprise-content face wires the SecGate pre-gate"
          " first)"
          % (code_nd, code_nv, code_wv, code_na, code_wa,
             pv["ai_label"], sub_a["ai_label"], sub_bb["ai_label"],
             cv["ai_label"], label_rejected))

    # -- AC-SR7 hard law: bad args, hygiene, byte-stable config ---------------
    b7 = {who: bal(who) for who in people}
    counts0 = (_count(conn, "showroom_packages"),
               _count(conn, "showroom_contracts"),
               _count(conn, "showroom_tour_stops"))
    bad7 = []
    raised7 = True
    for label, fn, code in (
            ("pool enterprise", lambda: sf.subscribe_enterprise(
                "pool:reserve", "ent-showroom-a", 300, "order:sr7a"),
             S.E_SR_BAD_ACCOUNT),
            ("empty ref", lambda: sf.subscribe_enterprise(
                "usr:dave", "ent-showroom-a", 300, "  "),
             S.E_SR_BAD_ARGS),
            ("empty pkg key", lambda: sf.subscribe_enterprise(
                "usr:dave", " ", 300, "order:sr7b"), S.E_SR_BAD_ARGS),
            ("bool tick", lambda: sf.subscribe_enterprise(
                "usr:dave", "ent-showroom-a", True, "order:sr7c"),
             S.E_SR_BAD_ARGS),
            ("negative tick", lambda: sf.subscribe_enterprise(
                "usr:dave", "ent-showroom-a", -1, "order:sr7d"),
             S.E_SR_BAD_ARGS),
            ("unknown pkg", lambda: sf.subscribe_enterprise(
                "usr:dave", "ghost-pkg", 300, "order:sr7e"),
             S.E_SR_UNKNOWN_PKG),
            ("bad lineup tick", lambda: sf.showroom_lineup(
                pkg_a["pkg_id"], "x"), S.E_SR_BAD_ARGS),
            ("unknown pkg view", lambda: sf.package_view(999),
             S.E_SR_UNKNOWN_PKG),
            ("str pkg view", lambda: sf.package_view("x"),
             S.E_SR_BAD_ARGS),
            ("bool pkg view", lambda: sf.package_view(True),
             S.E_SR_BAD_ARGS),
            ("unknown contract", lambda: sf.contract_view(999),
             S.E_SR_UNKNOWN_CONTRACT),
            ("str contract", lambda: sf.contract_view("x"),
             S.E_SR_BAD_ARGS)):
        ok_one, got = expect_sr_error(fn, code)
        if ok_one:
            bad7.append("%s=%s" % (label, got))
        else:
            bad7.append("%s NOT-RAISED(%s)" % (label, got))
            raised7 = False
    counts1 = (_count(conn, "showroom_packages"),
               _count(conn, "showroom_contracts"),
               _count(conn, "showroom_tour_stops"))
    with open(os.path.join(BASE, "showroom.py"), encoding="utf-8") as h:
        src7 = h.read()
    non_ascii = sum(1 for ch in src7 if ord(ch) > 127)
    net_imports = [ln for ln in src7.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    bal7 = {who: bal(who) for who in people}
    ok7 = (raised7 and counts0 == counts1 and b7 == bal7
           and non_ascii == 0 and not net_imports
           and "UPDATE showroom_" not in src7
           and "INSERT INTO venue_occupancy" not in src7
           and "INSERT INTO ad_units" not in src7
           and "random" not in src7 and cfg_after == cfg_bytes)
    record("AC-SR7", ok7, "all %d bad args rejected (%s); zero side"
          " effects (rows %s unchanged, all balances unchanged);"
          " module pure ASCII (%d non-ascii); zero network imports"
          " (%d); zero UPDATE surface; zero venue/ad-table writes;"
          " zero RNG (no random in source); config.json byte-stable"
          % (len(bad7), "; ".join(bad7), counts0, non_ascii,
             len(net_imports)))

    conn.close()
    sf.close()
    adz.close()
    ven.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
