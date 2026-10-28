"""Acceptance suite for the apimarket buyer price-reaction face
(BigDomain R2226; canon = the R2213 explore-seed row claimed in R2226,
criteria AC-BPR1..AC-BPR8 registered in that row BEFORE this code).

Face under proof: APIMarketFace.api_buyer_price_reaction. The alert face
reports what moved after a watch and the budget face reports the current
structure, but nothing linked the movement to the purchase: of the
shelves that fell after I watched them, how many did I actually buy.
This suite pins:

  - the twenty-five-key envelope, the eleven-key direction rows, the
    pinned ["drop","flat","rise"] order and the honest empty first;
  - the anchor law: the watch-time price is the newest revision stamped
    at or before watched_utc, so a later revision never re-dates it;
  - the observed-price law: a converted watch is priced by the frozen
    purchase price_paid, a pending or pre_owned watch by the values on
    record at read time, never a wall clock;
  - the direction law (below zero drop, zero flat, above zero rise) and
    the pre_owned exemption from the funnel while still bucketed;
  - the conversion law shared with api_watch_conversion (a refund sends
    the watch back to pending) and the None-not-zero rate law;
  - conservation of the three buckets, the integer-floor average and
    both extremes;
  - strict buyer isolation, the eight-form gate family failing closed
    before any read, frozen table digests, a constant ledger_tx set and
    byte-identical repeats;
  - three instances over two restarts, the reconcile wiring, and the
    ASCII/LF source hygiene.

Usage: python test_apimarket_buyerpricereaction.py
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
import metered as M                   # noqa: E402 (R626 product)
import apidev as D                    # noqa: E402 (R1700 registry)
import apimarket as A                 # noqa: E402 (R1763 face)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

ENVELOPE_KEYS = {
    "scope", "buyer_id", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate", "drop_count",
    "drop_converted_count", "drop_rate", "flat_count",
    "flat_converted_count", "flat_rate", "rise_count",
    "rise_converted_count", "rise_rate", "delta_sum", "avg_delta",
    "largest_drop", "largest_rise", "listing_count", "seller_count",
    "directions", "disclaimer"}

ROW_KEYS = {
    "direction", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate", "delta_sum",
    "avg_delta", "largest_drop", "largest_rise"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so every bucket is reproducible."""

    def __init__(self):
        self.value = "2026-01-05T00:00:00Z"

    def now_utc(self):
        return self.value


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dumps(env):
    return json.dumps(env, sort_keys=True)


def table_digest(conn, table):
    rows = conn.execute(
        "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    blob = repr(rows).encode("utf-8")
    return len(rows), hashlib.sha256(blob).hexdigest()


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    out = {t: table_digest(conn, t) for t in TABLES}
    conn.close()
    return out


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def build_stack(db_path, cfg, lobby_cfg):
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    gate = SecGate.from_config(lobby_cfg)
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)
    return led, metered, dk, gate, am


def close_stack(am, dk, metered, led):
    am.close()
    dk.close()
    metered.close()
    led.close()


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:" + who, "credit", 400)],
               "manual:fund-" + who, "suite funding " + who)


def direction_row(env, name):
    for row in env["directions"]:
        if row["direction"] == name:
            return row
    raise AssertionError("direction %r missing" % (name,))


def seed_world(led, dk, am, clock):
    """Four listings at base price 10: t1 and t2 at dana, d1 at lia,
    g1 at gina.

    bob: JAN watch t1 at 10, t1 falls to 8 in FEB, bob buys at 8 in
         APR, t1 then rises to 11 in MAY (the anchor and the frozen
         purchase price must both ignore it); FEB watch d1 at 10, d1
         rises to 12, bob buys at 12; MAR watch t2 at 10, bob buys at
         10 (flat); SEP unwatch t2 (the watch stays in this face).
    kit: JUL watch t2, buy at 10, refund in JUL (back to pending);
         AUG watch d1 at 10 while the live price is 12 (pending rise).
    erin: MAY g1 rises to 12, JUN erin buys at 12 then watches (the
         pre_owned exemption, bucketed but no funnel entry); g1 then
         falls to 6 after the watch.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-BPR-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-BPR-S",
                     "settlement")
    for who in ("bob", "kit", "erin"):
        fund(led, who)
    for dev in ("dana", "lia", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    t2 = am.publish_api("usr:dana", "t2", "Dana Tools Pro",
                        "dana tools pro payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:lia", "d1", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-05T00:00:00Z"
    am.watch_api("usr:bob", t1)

    clock.value = "2026-02-03T00:00:00Z"
    am.revise_price("usr:dana", t1, 8)

    clock.value = "2026-02-10T00:00:00Z"
    am.watch_api("usr:bob", d1)

    clock.value = "2026-02-20T00:00:00Z"
    am.revise_price("usr:lia", d1, 12)

    clock.value = "2026-03-02T00:00:00Z"
    am.watch_api("usr:bob", t2)

    clock.value = "2026-04-05T00:00:00Z"
    am.purchase_api("usr:bob", t1, "BPR-BOB-T1")

    clock.value = "2026-04-06T00:00:00Z"
    am.purchase_api("usr:bob", d1, "BPR-BOB-D1")

    clock.value = "2026-04-07T00:00:00Z"
    am.purchase_api("usr:bob", t2, "BPR-BOB-T2")

    clock.value = "2026-05-01T00:00:00Z"
    am.revise_price("usr:dana", t1, 11)

    clock.value = "2026-05-20T00:00:00Z"
    am.revise_price("usr:gina", g1, 12)

    clock.value = "2026-06-01T00:00:00Z"
    am.purchase_api("usr:erin", g1, "BPR-ERIN-G1")

    clock.value = "2026-06-10T00:00:00Z"
    am.watch_api("usr:erin", g1)

    clock.value = "2026-06-15T00:00:00Z"
    am.revise_price("usr:gina", g1, 6)

    clock.value = "2026-07-01T00:00:00Z"
    am.watch_api("usr:kit", t2)

    clock.value = "2026-07-05T00:00:00Z"
    am.purchase_api("usr:kit", t2, "BPR-KIT-T2")

    clock.value = "2026-07-20T00:00:00Z"
    am.refund_api("usr:kit", am.api_library("usr:kit")
                  ["purchases"][0]["purchase_id"], "not as described")

    clock.value = "2026-08-01T00:00:00Z"
    am.watch_api("usr:kit", d1)

    clock.value = "2026-08-05T00:00:00Z"
    am.revise_price("usr:dana", t2, 14)

    clock.value = "2026-09-01T00:00:00Z"
    am.unwatch_api("usr:bob", t2)

    return {"t1": t1, "t2": t2, "d1": d1, "g1": g1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerpricereaction-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = Clock()
    _CLOCK = clock
    orig_now = A._now_utc
    A._now_utc = clock.now_utc
    try:
        return run(db_path, cfg, lobby_cfg, shas_before)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    ids = seed_world(led, dk, am, _CLOCK)

    bob = am.api_buyer_price_reaction("usr:bob")
    kit = am.api_buyer_price_reaction("usr:kit")
    erin = am.api_buyer_price_reaction("usr:erin")

    # -- AC-BPR1 contract, pinned order, honest empty first ----------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bpr-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_price_reaction("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    rows_ok = all(set(row.keys()) == ROW_KEYS
                  for env in (bob, kit, erin)
                  for row in env["directions"])
    order_ok = all([r["direction"] for r in env["directions"]]
                   == ["drop", "flat", "rise"]
                   for env in (bob, kit, erin, empty))
    ok1 = (set(bob.keys()) == ENVELOPE_KEYS
           and len(bob) == 25
           and rows_ok
           and order_ok
           and bob["scope"] == "buyer"
           and bob["buyer_id"] == "usr:bob"
           and bob["disclaimer"] == DISCLAIMER
           and empty["watch_count"] == 0
           and empty["funnel_count"] == 0
           and empty["pre_owned_count"] == 0
           and empty["converted_count"] == 0
           and empty["pending_count"] == 0
           and empty["conversion_rate"] is None
           and empty["delta_sum"] == 0
           and empty["avg_delta"] is None
           and empty["largest_drop"] is None
           and empty["largest_rise"] is None
           and empty["listing_count"] == 0
           and empty["seller_count"] == 0
           and all(row["watch_count"] == 0
                   and row["conversion_rate"] is None
                   and row["avg_delta"] is None
                   and row["largest_drop"] is None
                   and row["largest_rise"] is None
                   for row in empty["directions"]))
    record("AC-BPR1", ok1,
           "env_keys=%d exact=%r row_keys=%r order=%r empty=%r"
           % (len(bob), set(bob.keys()) == ENVELOPE_KEYS, rows_ok,
              order_ok, (empty["watch_count"], empty["conversion_rate"],
                         empty["avg_delta"])))

    # -- AC-BPR2 anchor law: a later revision never re-dates ---------
    hist = am.api_price_history(ids["t1"])
    revisions = hist.get("revisions", [])
    prices = [r.get("token_price") for r in revisions]
    b_drop = direction_row(bob, "drop")
    ok2 = (len(revisions) == 2
           and prices == [8, 11]
           and hist.get("current_price") == 11
           and b_drop["watch_count"] == 1
           and b_drop["largest_drop"] == -2
           and bob["largest_drop"] == -2)
    record("AC-BPR2", ok2,
           "revisions=%r current=%r drop_count=%r largest_drop=%r"
           % (prices, hist.get("current_price"), b_drop["watch_count"],
              b_drop["largest_drop"]))

    # -- AC-BPR3 observed-price law: frozen purchase vs live price ---
    k_rise = direction_row(kit, "rise")
    k_flat = direction_row(kit, "flat")
    ok3 = (b_drop["converted_count"] == 1
           and bob["drop_converted_count"] == 1
           and bob["delta_sum"] == 0
           and bob["rise_count"] == 1 and bob["rise_rate"] == 1.0
           and k_rise["watch_count"] == 1
           and k_rise["delta_sum"] == 4
           and k_rise["converted_count"] == 0
           and k_flat["watch_count"] == 1
           and k_flat["delta_sum"] == 0)
    record("AC-BPR3", ok3,
           "bob_delta_sum=%r bob_drop=%r kit_rise=%r kit_flat=%r"
           % (bob["delta_sum"],
              (b_drop["converted_count"], b_drop["largest_drop"]),
              (k_rise["watch_count"], k_rise["delta_sum"]),
              (k_flat["watch_count"], k_flat["delta_sum"])))

    # -- AC-BPR4 direction partition and the pre_owned exemption -----
    e_flat = direction_row(erin, "flat")
    ok4 = (sum(r["watch_count"] for r in bob["directions"])
           == bob["watch_count"] == 3
           and (bob["drop_count"], bob["flat_count"], bob["rise_count"])
           == (1, 1, 1)
           and (kit["drop_count"], kit["flat_count"], kit["rise_count"])
           == (0, 1, 1)
           and (erin["drop_count"], erin["flat_count"],
                erin["rise_count"]) == (0, 1, 0)
           and erin["pre_owned_count"] == 1
           and erin["funnel_count"] == 0
           and e_flat["pre_owned_count"] == 1
           and e_flat["watch_count"] == 1
           and e_flat["funnel_count"] == 0)
    record("AC-BPR4", ok4,
           "bob=%r kit=%r erin=%r erin_flat=%r"
           % ((bob["drop_count"], bob["flat_count"], bob["rise_count"]),
              (kit["drop_count"], kit["flat_count"], kit["rise_count"]),
              (erin["drop_count"], erin["flat_count"],
               erin["rise_count"]),
              (e_flat["watch_count"], e_flat["funnel_count"],
               e_flat["pre_owned_count"])))

    # -- AC-BPR5 conversion law, the refund and the None rate --------
    ok5 = (kit["converted_count"] == 0
           and kit["pending_count"] == 2
           and kit["conversion_rate"] == 0.0
           and k_flat["converted_count"] == 0
           and k_flat["pending_count"] == 1
           and bob["converted_count"] == 3
           and bob["pending_count"] == 0
           and bob["conversion_rate"] == 1.0
           and erin["conversion_rate"] is None
           and e_flat["conversion_rate"] is None
           and kit["flat_rate"] == 0.0
           and kit["rise_rate"] == 0.0)
    record("AC-BPR5", ok5,
           "kit=%r bob=%r erin_rate=%r kit_rates=%r"
           % ((kit["converted_count"], kit["pending_count"],
               kit["conversion_rate"]),
              (bob["converted_count"], bob["conversion_rate"]),
              erin["conversion_rate"],
              (kit["flat_rate"], kit["rise_rate"])))

    # -- AC-BPR6 conservation, the floor average and the extremes ----
    conn = sqlite3.connect(am.db_path)
    bob_watches = conn.execute(
        "SELECT COUNT(*) FROM apimarket_watchlist WHERE buyer_id = ?",
        ("usr:bob",)).fetchone()[0]
    conn.close()
    ok6 = (bob["funnel_count"] + bob["pre_owned_count"]
           == bob["watch_count"] == int(bob_watches)
           and bob["drop_converted_count"]
           + bob["flat_converted_count"]
           + bob["rise_converted_count"] == bob["converted_count"]
           and all(row["converted_count"] <= row["funnel_count"]
                   <= row["watch_count"]
                   for env in (bob, kit, erin)
                   for row in env["directions"])
           and kit["delta_sum"] == 4
           and kit["avg_delta"] == 2
           and kit["largest_rise"] == 4
           and kit["largest_drop"] is None
           and bob["avg_delta"] == 0
           and bob["largest_rise"] == 2
           and bob["listing_count"] == 3
           and bob["seller_count"] == 2
           and erin["avg_delta"] == 0
           and erin["largest_drop"] is None
           and erin["largest_rise"] is None)
    record("AC-BPR6", ok6,
           "table=%r sums=%r avg=%r extremes=%r/%r"
           % (int(bob_watches),
              (bob["funnel_count"], bob["pre_owned_count"],
               bob["converted_count"]),
              (bob["avg_delta"], kit["avg_delta"], erin["avg_delta"]),
              bob["largest_drop"], bob["largest_rise"]))

    # -- AC-BPR7 gates, isolation, purity and repeats ----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_codes = []
    for bad in (123, [], {}, "  ", "bob", True, "usr", None):
        try:
            am.api_buyer_price_reaction(bad)
        except A.ApiMarketError as exc:
            bad_codes.append(exc.code)
        else:
            bad_codes.append("ACCEPTED")
    digests_mid = market_digests(am)
    call_a = dumps(am.api_buyer_price_reaction("usr:bob"))
    call_b = dumps(am.api_buyer_price_reaction("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    live = am.api_watchlist("usr:bob")

    led2, metered2, dk2, _gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_buyer_price_reaction("usr:bob"))
    kit_b = dumps(am2.api_buyer_price_reaction("usr:kit"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_buyer_price_reaction("usr:bob"))
    close_stack(am3, dk3, metered3, led3)

    ok7 = (bad_codes == [A.E_AM_BAD_ACCOUNT] * 8
           and digests_before == digests_mid == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == dumps(bob)
           and kit_b == dumps(kit)
           and live["watch_count"] == 2
           and bob["watch_count"] == 3)
    record("AC-BPR7", ok7,
           "gates=%r digests_same=%r tx_same=%r bytes_same=%r "
           "unwatch_kept=%r"
           % (bad_codes, digests_before == digests_after,
              tx_before == tx_after, call_a == call_d == dumps(bob),
              (live["watch_count"], bob["watch_count"])))

    # -- AC-BPR8 hygiene and the wiring ------------------------------
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (b'"ledger-apimarket-buyerpricereaction"' in recon
           and b"test_apimarket_buyerpricereaction.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-BPR8", ok8,
           "wired=%r src_lf=%r test_ascii_lf=%r"
           % (b'"ledger-apimarket-buyerpricereaction"' in recon,
              b"\r\n" not in src, b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("%s PRODUCT_SHA_STABLE %r"
          % ("PASS" if shas_before == shas_after else "FAIL",
             shas_before == shas_after), flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())