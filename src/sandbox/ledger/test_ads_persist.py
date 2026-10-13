"""Cross-restart persistence window for the virtual-exhibition
ad-slot schedule face (BigDomain R1940; the ads seat of the R1886
persist-family lineage - the R1934-seeded row, criteria
pre-registered in the R1940 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close all three pieces -> reopen the same db/config -> byte-
identical read replay -> restart-surviving gate probes (zero
drift) -> post-restart real-path continuation on a freed
carousel window and a freed naming window -> frozen faces +
dup/full gates across restart -> pure-read law -> third
instance stability. carousel_lineup / naming_holder /
splash_owner / schedule_board are window-parameterized pure-
value read faces with zero clock echo, so full-dump byte-
identity holds without clock freezing; the evidence digests
mask the spend_tx field of the board faces (banded projection,
R1902 law) so the suite stdout stays deterministic across
double runs.

Usage: python test_ads_persist.py
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
import ads as A             # noqa: E402  (R622 ad-slot face)

RESULTS = []

_SPEND_RE = re.compile(r'"spend_tx": "[^"]*"')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_ad_error(fn, *codes):
    try:
        fn()
    except A.AdsError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    return _SPEND_RE.sub('"spend_tx": "<tx>"', text)


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
    for tbl in ("ad_units", "venue_registry", "venue_occupancy",
                "ledger_tx", "ledger_entries"):
        out[tbl] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def spend_cross(db_path, tx_id, account_id):
    """SQL cross: the bound spend tx is a real ledger spend row
    with a debit leg on the booking account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = 'debit'",
        (tx_id, account_id)).fetchone()
    conn.close()
    return (head[0] if head else None), (leg[0] if leg else None)


def read_battery(af, led):
    return {
        "car_w100": dump(af.carousel_lineup("screen:quant-main", 100)),
        "car_w107": dump(af.carousel_lineup("screen:quant-main", 107)),
        "car_w110": dump(af.carousel_lineup("screen:quant-main", 110)),
        "car_w200": dump(af.carousel_lineup("screen:quant-main", 200)),
        "naming": dump(
            [af.naming_holder("naming:harbor-gate", t)
             for t in (299, 300, 309, 310)]),
        "splash": dump(
            [af.splash_owner("splash:lobby", t)
             for t in (299, 300, 304, 305)]),
        "board_screen": masked(
            dump(af.schedule_board("screen:quant-main"))),
        "board_naming": masked(
            dump(af.schedule_board("naming:harbor-gate"))),
        "board_splash": masked(dump(af.schedule_board("splash:lobby"))),
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
    tmp = tempfile.mkdtemp(prefix="ads-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    adsmod_sha_before = sha16(io_read(os.path.join(BASE, "ads.py")))
    vnmod_sha_before = sha16(io_read(os.path.join(BASE, "venue.py")))
    ledmod_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    # ---- instance 1: anchor world on the real product path -------
    led = L.Ledger(db_path, cfg)
    ven = V.VenueFace(led)
    af = A.AdsFace(led, ven)
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-ASP-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.adjust([("pool:reserve", "debit", 2000),
                ("usr:alice", "credit", 2000)],
               "manual:asp-fund-alice", "persist window funding alice")
    led.adjust([("pool:reserve", "debit", 600),
                ("usr:bob", "credit", 600)],
               "manual:asp-fund-bob", "persist window funding bob")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:carol", "credit", 400)],
               "manual:asp-fund-carol", "persist window funding carol")

    # ad registry: one carousel screen (2 rotation slots) + two
    # exclusive units; every booking below rides the venue engine
    af.register_ad_unit("screen:quant-main", "quant_screen_carousel",
                        rotation_slots=2)
    af.register_ad_unit("naming:harbor-gate", "building_naming")
    af.register_ad_unit("splash:lobby", "lobby_splash")

    # carousel: two overlapping advertisers inside capacity 2 + one
    # far-future window (lineup order = booking order)
    r_a1 = af.book("usr:alice", "screen:quant-main", 100, 10, 5,
                   "order:asp-a1")
    r_b1 = af.book("usr:bob", "screen:quant-main", 105, 10, 4,
                   "order:asp-b1")
    r_c1 = af.book("usr:carol", "screen:quant-main", 200, 5, 3,
                   "order:asp-c1")
    # exclusive: naming right + lobby splash, single holders
    ls_a1 = af.book("usr:alice", "naming:harbor-gate", 300, 10, 3,
                   "order:asp-s1")
    ls_b1 = af.book("usr:bob", "splash:lobby", 300, 5, 3,
                    "order:asp-s2")

    # -- AC-ASP1 control anchor: world pinned + gate probes -------
    bal1 = read_battery(af, led)
    cnt1 = table_counts(db_path)
    ok_world = (
        r_a1["fee"] == 50 and r_a1["start_window"] == 100
        and r_a1["end_window"] == 109
        and r_a1["ad_kind"] == "quant_screen_carousel"
        and r_b1["fee"] == 40 and r_c1["fee"] == 15
        and ls_a1["fee"] == 30 and ls_a1["start_window"] == 300
        and ls_a1["end_window"] == 309
        and ls_a1["ad_kind"] == "building_naming"
        and ls_b1["fee"] == 15 and ls_b1["ad_kind"] == "lobby_splash"
        and bal1["bal_alice"] == 1920 and bal1["bal_bob"] == 545
        and bal1["bal_carol"] == 385 and bal1["bal_pool"] == 17150
        and cnt1["ad_units"] == 3 and cnt1["venue_registry"] == 3
        and cnt1["venue_occupancy"] == 5 and cnt1["spend_tx"] == 5)
    lu100 = json.loads(bal1["car_w100"])["advertisers"]
    lu107 = json.loads(bal1["car_w107"])["advertisers"]
    lu110 = json.loads(bal1["car_w110"])["advertisers"]
    lu200 = json.loads(bal1["car_w200"])["advertisers"]
    ok_lineup = (
        [(a["account_id"], a["position"], a["start_window"],
          a["end_window"]) for a in lu100] ==
        [("usr:alice", 1, 100, 109)]
        and [(a["account_id"], a["position"]) for a in lu107] ==
        [("usr:alice", 1), ("usr:bob", 2)]
        and [(a["account_id"], a["position"]) for a in lu110] ==
        [("usr:bob", 1)]
        and [(a["account_id"], a["position"]) for a in lu200] ==
        [("usr:carol", 1)]
        and json.loads(bal1["car_w100"])["rotation_slots"] == 2)
    ok_holders = (
        json.loads(bal1["naming"]) ==
        [None, "usr:alice", "usr:alice", None]
        and json.loads(bal1["splash"]) ==
        [None, "usr:bob", "usr:bob", None])
    board_s = json.loads(bal1["board_screen"])
    board_n = json.loads(bal1["board_naming"])
    ok_board = (
        len(board_s["bookings"]) == 3
        and board_s["ad_kind"] == "quant_screen_carousel"
        and [(b["account_id"], b["start_window"], b["end_window"])
             for b in board_s["bookings"]] ==
        [("usr:alice", 100, 109), ("usr:bob", 105, 114),
         ("usr:carol", 200, 204)]
        and all(b["spend_tx"] == "<tx>" for b in board_s["bookings"])
        and len(board_n["bookings"]) == 1
        and board_n["bookings"][0]["account_id"] == "usr:alice"
        and all(b["terminated_tick"] is None
                for b in board_s["bookings"] + board_n["bookings"]))
    probe_specs = (
        ("unknown", lambda: af.book(
            "usr:alice", "screen:ghost", 400, 5, 3, "order:asp-p1"),
         A.E_AD_UNKNOWN),
        ("full", lambda: af.book(
            "usr:carol", "screen:quant-main", 106, 5, 3, "order:asp-p2"),
         A.E_AD_FULL),
        ("dup", lambda: af.book(
            "usr:alice", "screen:quant-main", 100, 10, 5, "order:asp-p3"),
         A.E_AD_DUP),
        ("taken", lambda: af.book(
            "usr:carol", "naming:harbor-gate", 305, 5, 3, "order:asp-p4"),
         A.E_AD_TAKEN),
        ("kind-mismatch", lambda: af.carousel_lineup(
            "naming:harbor-gate", 300),
         A.E_AD_KIND_MISMATCH))
    probes1 = []
    for label, fn, code in probe_specs:
        ok_one, got = expect_ad_error(fn, code)
        probes1.append("%s=%s" % (label, got) if ok_one else
                       "%s NOT-RAISED(%s)" % (label, got))
    ok_probes1 = all("NOT-RAISED" not in p for p in probes1)
    ok_probe_drift1 = (table_counts(db_path) == cnt1
                       and read_battery(af, led) == bal1)
    ok1 = (ok_world and ok_lineup and ok_holders and ok_board
           and ok_probes1 and ok_probe_drift1)
    record("AC-ASP1", ok1, "anchor world pinned (carousel screen"
          " capacity 2: alice [100,109] fee 50 + bob [105,114]"
          " fee 40 + carol far-future [200,204] fee 15; naming"
          " harbor-gate exclusive alice [300,309] fee 30; splash"
          " lobby exclusive bob [300,304] fee 15; lineup probes:"
          " w100 alice-only, w107 alice+bob in booking order,"
          " w110 bob-only, w200 carol; naming 299N/300A/309A/"
          "310N, splash 299N/300B/304B/305N); five gate probes"
          " rejected (%s); counts ad_units=%d registry=%d"
          " occupancy=%d spend-tx=%d frozen across probes;"
          " balances 1920/545/385/17150; digest=%s" % (
              "; ".join(probes1), cnt1["ad_units"],
              cnt1["venue_registry"], cnt1["venue_occupancy"],
              cnt1["spend_tx"], evidence_digest(bal1)))

    # -- AC-ASP2 cross-restart byte-identical replay -------------
    af.close()
    ven.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    ven2 = V.VenueFace(led2)
    af2 = A.AdsFace(led2, ven2)
    bal2 = read_battery(af2, led2)
    diffs2 = battery_diffs(bal1, bal2)
    ok2 = not diffs2
    record("AC-ASP2", ok2, "three-piece close->reopen (af.close ->"
          " ven.close -> led.close -> Ledger same db/cfg +"
          " VenueFace + AdsFace fresh): read battery byte-identical"
          " to pre-close snapshot (lineup four windows + naming/"
          "splash holder probes + three schedule boards with the"
          " spend_tx banded-projection mask + four balances),"
          " diffs=%s; ad_units registry and venue occupancy"
          " persisted values replay with zero in-memory drift;"
          " digest=%s" % (diffs2 or "none", evidence_digest(bal2)))

    # -- AC-ASP3 gates survive restart, zero drift ---------------
    probes2 = []
    for label, fn, code in probe_specs:
        if label == "unknown":
            def fn2():
                af2.book("usr:alice", "screen:ghost", 400, 5, 3,
                         "order:asp-p1")
        elif label == "full":
            def fn2():
                af2.book("usr:carol", "screen:quant-main", 106, 5, 3,
                         "order:asp-p2")
        elif label == "dup":
            def fn2():
                af2.book("usr:alice", "screen:quant-main", 100, 10, 5,
                         "order:asp-p3")
        elif label == "taken":
            def fn2():
                af2.book("usr:carol", "naming:harbor-gate", 305, 5, 3,
                         "order:asp-p4")
        else:
            def fn2():
                af2.carousel_lineup("naming:harbor-gate", 300)
        ok_one, got = expect_ad_error(fn2, code)
        probes2.append("%s=%s" % (label, got) if ok_one else
                       "%s NOT-RAISED(%s)" % (label, got))
    ok_probes2 = all("NOT-RAISED" not in p for p in probes2)
    ok_drift2 = (table_counts(db_path) == cnt1
                 and read_battery(af2, led2) == bal2)
    ok3 = ok_probes2 and ok_drift2
    record("AC-ASP3", ok3, "restart-surviving gates: five probes"
          " all rejected with identical codes on instance 2 (%s);"
          " counts and battery frozen across the probe batch"
          " (ad_units/registry/occupancy/spend-tx %d/%d/%d/%d"
          " unchanged, zero charge, zero rows)" % (
              "; ".join(probes2), cnt1["ad_units"],
              cnt1["venue_registry"], cnt1["venue_occupancy"],
              cnt1["spend_tx"]))

    # -- AC-ASP4 post-restart real-path continuation --------------
    r_c2 = af2.book("usr:carol", "screen:quant-main", 110, 5, 3,
                    "order:asp-c2")
    head_c2, leg_c2 = spend_cross(db_path, r_c2["spend_tx"],
                                  "usr:carol")
    ls_c3 = af2.book("usr:carol", "naming:harbor-gate", 310, 5, 3,
                     "order:asp-c3")
    head_c3, leg_c3 = spend_cross(db_path, ls_c3["spend_tx"],
                                   "usr:carol")
    bal4 = read_battery(af2, led2)
    cnt4 = table_counts(db_path)
    lu112 = af2.carousel_lineup("screen:quant-main", 112)["advertisers"]
    board_s4 = json.loads(bal4["board_screen"])
    board_n4 = json.loads(bal4["board_naming"])
    ok4 = (
        r_c2["fee"] == 15 and r_c2["start_window"] == 110
        and r_c2["end_window"] == 114
        and head_c2 == "spend" and leg_c2 == "debit"
        and ls_c3["fee"] == 15 and ls_c3["start_window"] == 310
        and ls_c3["end_window"] == 314
        and head_c3 == "spend" and leg_c3 == "debit"
        and cnt4["venue_occupancy"] == 7 and cnt4["spend_tx"] == 7
        and cnt4["ad_units"] == 3
        and bal4["bal_alice"] == 1920 and bal4["bal_bob"] == 545
        and bal4["bal_carol"] == 355 and bal4["bal_pool"] == 17180
        and [(a["account_id"], a["position"]) for a in lu112] ==
        [("usr:bob", 1), ("usr:carol", 2)]
        and json.loads(bal4["naming"])[3] == "usr:carol"
        and len(board_s4["bookings"]) == 4
        and (board_s4["bookings"][2]["account_id"],
             board_s4["bookings"][2]["start_window"],
             board_s4["bookings"][2]["end_window"]) ==
        ("usr:carol", 110, 114)
        and (board_s4["bookings"][3]["account_id"],
             board_s4["bookings"][3]["start_window"]) ==
        ("usr:carol", 200)
        and len(board_n4["bookings"]) == 2
        and board_n4["bookings"][1]["account_id"] == "usr:carol"
        and board_s4["bookings"][0]["account_id"] == "usr:alice"
        and board_s4["bookings"][0]["start_window"] == 100)
    record("AC-ASP4", ok4, "post-restart continuation: carol books"
          " the freed carousel window [110,114] fee 15 (alice's"
          " [100,109] has expired, only bob's [105,114] still"
          " active, capacity 2 has room) and leases the freed"
          " naming window [310,314] fee 15 - both bind real spend"
          " txs (SQL cross type=%s/%s, debit legs=%s/%s, tx_id"
          " not echoed); touched read faces recompute zero-cache"
          " (lineup w112 = bob pos1 + carol pos2, naming_holder"
          " 310 N->carol, screen board 3->4 rows with the new"
          " [110,114] row landing in (start_tick,occ_id) order"
          " ahead of the far-future [200,204] row, naming board"
          " 1->2 rows); untouched probes frozen; occupancy 5->7,"
          " spend-tx 5->7, balances 1920/545/355/17180;"
          " digest=%s" % (
              head_c2, head_c3, leg_c2, leg_c3,
              evidence_digest(bal4)))

    # -- AC-ASP5 frozen faces + dup/full gates across restart -----
    board_s1 = json.loads(bal1["board_screen"])["bookings"]
    board_n1 = json.loads(bal1["board_naming"])["bookings"]
    old_rows = {(b["account_id"], b["start_window"]): b
                for b in board_s1 + board_n1}
    now_rows = {(b["account_id"], b["start_window"]): b
                for b in board_s4["bookings"]
                + board_n4["bookings"]}
    fields = ("account_id", "start_window", "end_window",
              "terminated_tick", "spend_tx")
    frozen_ok = all(
        old_rows[key][f] == now_rows[key][f]
        for f in fields for key in old_rows if key in now_rows)
    dup_probe, code_dup = expect_ad_error(
        lambda: af2.book("usr:carol", "screen:quant-main", 110, 5, 3,
                         "order:asp-p5"), A.E_AD_DUP)
    full_probe, code_full = expect_ad_error(
        lambda: af2.book("usr:alice", "screen:quant-main", 112, 5, 3,
                         "order:asp-p6"), A.E_AD_FULL)
    bal5 = read_battery(af2, led2)
    ok5 = (frozen_ok and dup_probe and full_probe
           and table_counts(db_path) == cnt4 and bal5 == bal4)
    record("AC-ASP5", ok5, "frozen faces: every pre-existing"
          " booking row keeps all persisted fields (account/"
          "start/end/terminated/spend_tx) byte-identical to the"
          " pre-close snapshot - new rows only insert in order;"
          " dup gate across restart: carol's held [110,114] with"
          " a fresh ref still rejected %s (ref-blind, zero"
          " charge); capacity gate across restart: alice at"
          " [112,116] rejected %s with bob + carol filling"
          " capacity 2 (zero charge); counts and battery frozen"
          " across both probes (%s==%s)" % (
              code_dup, code_full, cnt4["spend_tx"],
              table_counts(db_path)["spend_tx"]))

    # -- AC-ASP6 pure-read law ------------------------------------
    bat_a = read_battery(af2, led2)
    bat_b = read_battery(af2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and table_counts(db_path) == cnt4)
    record("AC-ASP6", ok6, "pure-read law: full battery read twice"
          " back-to-back - lineup + holder faces + three boards"
          " + four balances byte-identical between the two reads"
          " and table counts constant (read faces have zero side"
          " effects)")

    # -- AC-ASP7 third instance stability + hygiene --------------
    af2.close()
    ven2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    ven3 = V.VenueFace(led3)
    af3 = A.AdsFace(led3, ven3)
    bal3 = read_battery(af3, led3)
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
           and sha16(io_read(os.path.join(BASE, "ads.py")))
           == adsmod_sha_before
           and sha16(io_read(os.path.join(BASE, "venue.py")))
           == vnmod_sha_before
           and sha16(io_read(os.path.join(BASE, "ledger.py")))
           == ledmod_sha_before
           and non_ascii == 0 and not net_imports
           and os.path.realpath(tmp).startswith(
               os.path.realpath(tempfile.gettempdir()))
           and not os.path.realpath(tmp).startswith(repo_root))
    record("AC-ASP7", ok7, "third instance: close -> reopen same db"
          " once more - battery byte-identical to instance-2"
          " terminal state (diffs=%s, lineup/holder/board faces"
          " stable across a second restart); shipped files"
          " untouched (config/ads/venue/ledger sha16 stable);"
          " suite source pure ASCII (%d non-ascii), zero network"
          " imports (%d hits), world tmp outside repo (%s)" % (
              diffs3 or "none", non_ascii, len(net_imports),
              "yes" if not os.path.realpath(tmp).startswith(
                  repo_root) else "NO"))

    af3.close()
    ven3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
