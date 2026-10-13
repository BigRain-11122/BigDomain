"""Cross-restart persistence window for the developer API
marketplace face (BigDomain R1946; the apimarket seat of the
R1886 persist family - the R1941-seeded row, criteria
AC-AMP1..AC-AMP7 pre-registered in the R1946 tech.md claim row
before this code existed; honesty law). Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Four-piece full-chain restart world on the real product path:
anchor world (two registered developers, three listings across
two price points and both AIGC labels, three purchases with the
integer split law, three purchaser-only ratings) -> close all
four pieces (am/dk/metered/led) -> reopen the same db/config ->
byte-identical read replay -> restart-surviving gate probes ->
post-restart real-path continuation (a new listing sells with
a fresh bound spend/share pair, a new rating lands = the
marketplace keeps trading across the restart) -> frozen
history rows + dup gates -> pure-read law -> third instance
stability. The read faces carry persisted clock strings
(listed/purchased/rated utc - stored values, not clock echoes)
and time-derived hex tx ids, so the evidence digests mask both
families (banded projection, R1902 law) while the in-run
battery keeps full dumps.

Usage: python test_apimarket_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import metered as M                   # noqa: E402 (R626 product)
import apidev as D                    # noqa: E402 (R1700 registry face)
import apimarket as A                 # noqa: E402 (R1763 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, ref)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API marketplace"
              " is a service listing face, not investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

_UTC_RE = re.compile(
    r'"([a-z_]*utc[a-z_]*)": "(?:\d{4}-\d{2}[^"]*)"')
_TX_RE = re.compile(
    r'"(?:spend_tx|dev_share_tx)": "[^"]*"')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except A.ApiMarketError as exc:
        return exc.code in codes, exc.code
    except Exception as exc:                     # noqa: BLE001
        return False, type(exc).__name__ + ":" + str(exc)
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    text = _TX_RE.sub('"spend_tx": "<tx>"', text)
    return _UTC_RE.sub(lambda m: '"%s": "<ts>"' % m.group(1), text)


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


class _FaultGate(object):
    """Runtime-fault gate stub: check_text always blows up (the
    face must map this to E_AM_GATE_ERROR, never a silent pass)."""

    def check_text(self, text):
        raise RuntimeError("stub gate offline")


def table_counts(am_db, led_db):
    amc = sqlite3.connect(am_db)
    ledc = sqlite3.connect(led_db)
    out = {
        "listings": int(amc.execute(
            "SELECT COUNT(*) FROM apimarket_listings").fetchone()[0]),
        "purchases": int(amc.execute(
            "SELECT COUNT(*) FROM apimarket_purchases").fetchone()[0]),
        "ratings": int(amc.execute(
            "SELECT COUNT(*) FROM apimarket_ratings").fetchone()[0]),
        "spend_tx": int(ledc.execute(
            "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
        ).fetchone()[0]),
        "share_tx": int(ledc.execute(
            "SELECT COUNT(*) FROM ledger_tx WHERE type = 'share'"
        ).fetchone()[0]),
        "ledger_tx": int(ledc.execute(
            "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]),
    }
    amc.close()
    ledc.close()
    return out


def read_battery(am, led):
    return {
        "board": dump(am.api_board()),
        "view1": dump(am.api_view(1)),
        "view2": dump(am.api_view(2)),
        "view3": dump(am.api_view(3)),
        "ratings1": dump(am.api_ratings(1)),
        "sales_ada": dump(am.api_sales("usr:ada")),
        "sales_dan": dump(am.api_sales("usr:dan")),
        "bal_ada": led.balance("usr:ada")["balance"],
        "bal_dan": led.balance("usr:dan")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_eve": led.balance("usr:eve")["balance"],
        "bal_share": led.balance("pool:share")["balance"],
        "bal_reserve": led.balance("pool:reserve")["balance"],
    }


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def full_rows(am_db, table, order_col):
    conn = sqlite3.connect(am_db)
    rows = conn.execute(
        "SELECT * FROM %s ORDER BY %s" % (table, order_col)).fetchall()
    conn.close()
    return [tuple(r) for r in rows]


def make_probes(am, dk, led, bad_word, l1, l3):
    fault = A.APIMarketFace(led, dk, _FaultGate(), DISCLAIMER)
    probes = (
        ("not-dev", lambda: am.publish_api(
            "usr:eve", "eve-svc", "Eve Service",
            "off-register listing", PAYLOAD, 5, False),
         A.E_AM_NOT_DEV),
        ("dup-listing", lambda: am.publish_api(
            "usr:ada", "risk-scan", "Risk Scan API",
            "portfolio risk scan endpoint", PAYLOAD, 10, False),
         A.E_AM_DUP_LISTING),
        ("content", lambda: am.publish_api(
            "usr:ada", "bad-title", "Scan " + bad_word + " API",
            "clean description", PAYLOAD, 5, False),
         A.E_AM_CONTENT_REJECTED),
        ("purchase-dup", lambda: am.purchase_api(
            "usr:bob", l1, "ref-dup-bob"),
         A.E_AM_PURCHASE_DUP),
        ("self-buy", lambda: am.purchase_api(
            "usr:ada", l1, "ref-self-ada"),
         A.E_AM_SELF_BUY),
        ("unknown", lambda: am.purchase_api(
            "usr:bob", 999, "ref-unknown"),
         A.E_AM_UNKNOWN_LISTING),
        ("not-buyer", lambda: am.rate_api(
            "usr:eve", l1, 4),
         A.E_AM_NOT_BUYER),
        ("rate-dup", lambda: am.rate_api(
            "usr:bob", l1, 5),
         A.E_AM_RATE_DUP),
        ("bad-stars", lambda: am.rate_api(
            "usr:carol", l1, 6),
         A.E_AM_BAD_STARS),
        ("gate-fault", lambda: fault.publish_api(
            "usr:ada", "fault-svc", "Fault Probe", "d",
            PAYLOAD, 5, False),
         A.E_AM_GATE_ERROR),
    )
    return probes, fault


def run_probes(probe_specs):
    lines = []
    for label, fn, code in probe_specs:
        ok_one, got = expect_error(fn, code)
        lines.append("%s=%s" % (label, got) if ok_one else
                     "%s NOT-RAISED(%s)" % (label, got))
    return lines, all("NOT-RAISED" not in p for p in lines)


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    lobby_cfg = json.loads(io_read(
        os.path.join(LOBBY, "config.json")))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]
    mod_sha_before = dict(
        (name, sha16(io_read(os.path.join(BASE, name + ".py"))))
        for name in ("apimarket", "apidev", "metered", "ledger"))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    # ---- instance 1: anchor world on the real product path -----
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    gate = SecGate.from_config(lobby_cfg)
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 5000, "SETTLE-AMP-RES",
                     "settlement")
    led.mint_to_pool("pool:share", 2000, "SETTLE-AMP-SHARE",
                     "settlement")
    for who in ("ada", "dan", "bob", "carol", "eve"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    for who, amount in (("ada", 600), ("dan", 600), ("bob", 500),
                        ("carol", 400), ("eve", 200)):
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:amp-fund-" + who,
                   "persist window funding " + who)

    dk.issue_key("usr:ada", "amp-alpha", 10, ["backtest"], False)
    dk.issue_key("usr:dan", "amp-beta", 10, ["visualize"], True)

    t1 = am.publish_api("usr:ada", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD,
                        10, False)
    t2 = am.publish_api("usr:ada", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)
    t3 = am.publish_api("usr:dan", "risk-scan", "Dan Risk Variant",
                        "same key other developer", PAYLOAD, 7, False)
    l1, l3 = t1["listing_id"], t3["listing_id"]

    p1 = am.purchase_api("usr:bob", l1, "ref-amp-bob-l1")
    p2 = am.purchase_api("usr:carol", l1, "ref-amp-carol-l1")
    p3 = am.purchase_api("usr:bob", l3, "ref-amp-bob-l3")
    am.rate_api("usr:bob", l1, 5)
    am.rate_api("usr:carol", l1, 4)
    am.rate_api("usr:bob", l3, 3)

    # -- AC-AMP1 control anchor: world pinned + gate probes -----
    bat1 = read_battery(am, led)
    cnt1 = table_counts(am.db_path, db_path)
    snap1 = {
        "listings": full_rows(am.db_path, "apimarket_listings",
                              "listing_id"),
        "purchases": full_rows(am.db_path, "apimarket_purchases",
                               "purchase_id"),
        "ratings": full_rows(am.db_path, "apimarket_ratings",
                             "rating_id"),
    }
    ok_world = (
        t1["ai_label"] == 0 and t2["ai_label"] == 1
        and p1["dev_share"] == 7 and p1["platform_share"] == 3
        and p2["dev_share"] == 7 and p2["platform_share"] == 3
        and p3["dev_share"] == 5 and p3["platform_share"] == 2
        and cnt1["listings"] == 3 and cnt1["purchases"] == 3
        and cnt1["ratings"] == 3 and cnt1["spend_tx"] == 3
        and cnt1["share_tx"] == 3
        and bat1["bal_ada"] == 614 and bat1["bal_dan"] == 605
        and bat1["bal_bob"] == 483 and bat1["bal_carol"] == 390
        and bat1["bal_eve"] == 200 and bat1["bal_share"] == 1981
        and bat1["bal_reserve"] == 2727
        and '"rating_count": 2' in bat1["view1"]
        and '"rating_avg": 4.5' in bat1["view1"])
    probe_specs1, fault1 = make_probes(
        am, dk, led, bad_word, l1, l3)
    probes1, ok_probes1 = run_probes(probe_specs1)
    fault1.close()
    ok_drift1 = (table_counts(am.db_path, db_path) == cnt1
                 and read_battery(am, led) == bat1)
    ok1 = ok_world and ok_probes1 and ok_drift1
    record("AC-AMP1", ok1, "anchor world pinned (registered devs"
          " ada+dan; listings risk-scan@10 ai0 / macro-feed@3 ai1"
          " / dan variant@7 ai0; purchases bob+carol L1 10->7/3"
          " and bob L3 7->5/2 = integer split law across price"
          " points; ratings bob 5* + carol 4* on L1 (count 2 avg"
          " 4.5) + bob 3* on L3; listings=3 purchases=3 ratings=3"
          " spend-tx=3 share-tx=3 (one share tx per purchase);"
          " balances 614/605/483/390/200,"
          " pool:share 1981, pool:reserve 2727); ten gate probes"
          " rejected (%s); counts and battery frozen across the"
          " probe batch; digest=%s" % (
              "; ".join(probes1), evidence_digest(bat1)))

    # -- AC-AMP2 cross-restart byte-identical replay ------------
    am.close()
    dk.close()
    metered.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    metered2 = M.MeteredFace(led2)
    dk2 = D.DevKeyFace(metered2, DISCLAIMER)
    gate2 = SecGate.from_config(lobby_cfg)
    am2 = A.APIMarketFace(led2, dk2, gate2, DISCLAIMER)
    bat2 = read_battery(am2, led2)
    diffs2 = battery_diffs(bat1, bat2)
    ok2 = not diffs2
    record("AC-AMP2", ok2, "four-piece close->reopen (am.close ->"
          " dk.close -> metered.close -> led.close -> Ledger same"
          " db/cfg + MeteredFace + DevKeyFace + SecGate +"
          " APIMarketFace fresh): read battery byte-identical to"
          " the pre-close snapshot (market board + three listing"
          " views + rating ledger + both developer sales views"
          " with persisted spend/share tx pairs + seven"
          " balances), diffs=%s; the market read faces rebuild"
          " over the same apimarket.db rows with zero in-memory"
          " drift; digest=%s" % (
              diffs2 or "none", evidence_digest(bat2)))

    # -- AC-AMP3 gates survive the restart, zero drift ----------
    probe_specs2, fault2 = make_probes(
        am2, dk2, led2, bad_word, l1, l3)
    probes2, ok_probes2 = run_probes(probe_specs2)
    fault2.close()
    ok_drift2 = (table_counts(am2.db_path, db_path) == cnt1
                 and read_battery(am2, led2) == bat2)
    ok3 = ok_probes2 and ok_drift2
    record("AC-AMP3", ok3, "restart-surviving gates: ten probes"
          " all rejected with identical codes on instance 2 (%s);"
          " the registry gate rides the persisted dev-key board,"
          " the dup gates ride the UNIQUE constraints, the"
          " purchaser-only rating gate rides the persisted"
          " purchase rows - every gate survives the restart;"
          " counts and battery frozen across the probe batch"
          " (listings=%d purchases=%d ratings=%d unchanged, zero"
          " movement)" % (
              "; ".join(probes2), cnt1["listings"],
              cnt1["purchases"], cnt1["ratings"]))

    # -- AC-AMP4 post-restart real-path continuation -------------
    t4 = am2.publish_api("usr:dan", "quant-vision",
                         "Quant Vision API",
                         "quant vision analytics endpoint", PAYLOAD,
                         21, False)
    l4 = t4["listing_id"]
    p4 = am2.purchase_api("usr:eve", l4, "ref-amp-eve-l4")
    am2.rate_api("usr:eve", l4, 5)
    bat4 = read_battery(am2, led2)
    cnt4 = table_counts(am2.db_path, db_path)
    ledc = sqlite3.connect(db_path)
    spend_leg = ledc.execute(
        "SELECT COUNT(*) FROM ledger_entries e JOIN ledger_tx t"
        " ON t.tx_id = e.tx_id WHERE t.type = 'spend' AND"
        " e.direction = 'debit' AND e.account_id = 'usr:eve'"
    ).fetchone()[0]
    share_leg = ledc.execute(
        "SELECT COUNT(*) FROM ledger_entries e JOIN ledger_tx t"
        " ON t.tx_id = e.tx_id WHERE t.type = 'share' AND"
        " e.direction = 'credit' AND e.account_id = 'usr:dan'"
    ).fetchone()[0]
    ledc.close()
    ok4 = (
        t4["ai_label"] == 0
        and p4["dev_share"] == 15 and p4["platform_share"] == 6
        and p4["price_paid"] == 21
        and cnt4["listings"] == 4 and cnt4["purchases"] == 4
        and cnt4["ratings"] == 4 and cnt4["spend_tx"] == 4
        and cnt4["share_tx"] == 4
        and int(spend_leg) == 1 and int(share_leg) == 2
        and bat4["bal_eve"] == 179 and bat4["bal_dan"] == 620
        and bat4["bal_share"] == 1966
        and bat4["bal_reserve"] == 2748
        and '"rating_count": 1' in bat4["view3"]
        and '"purchase_count": 1' in dump(am2.api_view(l4)))
    record("AC-AMP4", ok4, "post-restart continuation: dan lists"
          " quant-vision@21 on instance 2 (registry + content"
          " gates + listing row all keep working); eve buys it"
          " -> 21 -> dev 15 / platform 6 (integer split law on a"
          " fresh price point), bound to a fresh spend tx and a"
          " fresh share tx (SQL cross: usr:eve spend debit leg"
          " and usr:dan share credit legs both present, dan has"
          " two share credit legs = the pre-restart one plus the"
          " new one); eve rates it 5* (purchaser-only gate keeps"
          " working); board grows 3->4 listings, dan sales"
          " 1->2 rows, listings/purchases/ratings 3->4, spend-tx"
          " 3->4, share-tx 3->4; balances eve 179 / dan 620,"
          " pool:share 1966, pool:reserve 2748; digest=%s"
          % evidence_digest(bat4))

    # -- AC-AMP5 frozen rows + dup gates across the restart -----
    frozen_ok = True
    for table, order, key in (
            ("apimarket_listings", "listing_id", "listings"),
            ("apimarket_purchases", "purchase_id", "purchases"),
            ("apimarket_ratings", "rating_id", "ratings")):
        now = full_rows(am2.db_path, table, order)
        if (len(now) < len(snap1[key])
                or any(old != new
                       for old, new in zip(snap1[key], now))):
            frozen_ok = False
            break
    dup_l, code_dup_l = expect_error(
        lambda: am2.publish_api(
            "usr:ada", "risk-scan", "Risk Scan API",
            "portfolio risk scan endpoint", PAYLOAD, 10, False),
        A.E_AM_DUP_LISTING)
    dup_p, code_dup_p = expect_error(
        lambda: am2.purchase_api("usr:bob", l1, "ref-dup2"),
        A.E_AM_PURCHASE_DUP)
    dup_r, code_dup_r = expect_error(
        lambda: am2.rate_api("usr:bob", l1, 5),
        A.E_AM_RATE_DUP)
    bat5 = read_battery(am2, led2)
    ok5 = (frozen_ok and dup_l and dup_p and dup_r
           and table_counts(am2.db_path, db_path) == cnt4
           and bat5 == bat4)
    record("AC-AMP5", ok5, "frozen faces: every pre-existing"
          " listing row (all eight columns incl. payload and"
          " declared AIGC label), purchase row (all nine columns"
          " incl. the bound spend_tx/dev_share_tx provenance"
          " pair) and rating row keeps every field byte-identical"
          " to the pre-close snapshot - the new listing/"
          " purchase/ rating only append (zero UPDATE surface);"
          " dup gates across the restart: listing replay"
          " rejected %s, purchase replay rejected %s, rating"
          " replay rejected %s (zero movement); counts and"
          " battery frozen across all three probes" % (
              code_dup_l, code_dup_p, code_dup_r))

    # -- AC-AMP6 pure-read law -----------------------------------
    bat_a = read_battery(am2, led2)
    bat_b = read_battery(am2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and table_counts(am2.db_path, db_path) == cnt4)
    record("AC-AMP6", ok6, "pure-read law: full battery read twice"
          " back-to-back - market board + three listing views +"
          " rating ledger + both sales views + seven balances"
          " byte-identical between the two reads and table counts"
          " constant (read faces have zero side effects)")

    # -- AC-AMP7 third instance stability + hygiene --------------
    am2.close()
    dk2.close()
    metered2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    metered3 = M.MeteredFace(led3)
    dk3 = D.DevKeyFace(metered3, DISCLAIMER)
    gate3 = SecGate.from_config(lobby_cfg)
    am3 = A.APIMarketFace(led3, dk3, gate3, DISCLAIMER)
    bat3 = read_battery(am3, led3)
    diffs3 = battery_diffs(bat5, bat3)
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in
                         ("urllib", "requests", "socket", "http"))]
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
    record("AC-AMP7", ok7, "third instance: four-piece close ->"
          " reopen same db once more - battery byte-identical to"
          " the instance-2 terminal state (diffs=%s, board/views/"
          " ratings/sales/balances stable across a second"
          " restart); shipped files untouched (config + apimarket"
          "/apidev/metered/ledger sha16 stable); suite source"
          " pure ASCII (%d non-ascii), zero network imports (%d"
          " hits), world tmp outside repo (%s)" % (
              diffs3 or "none", non_ascii, len(net_imports),
              "yes" if tmp_outside else "NO"))

    am3.close()
    dk3.close()
    metered3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
