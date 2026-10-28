"""Acceptance suite for the apimarket seller monthly returning-buyer face
(BigDomain R2228; canon = the R2213 explore-seed row claimed in R2228,
criteria AC-SRB1..AC-SRB8 registered in that row BEFORE this code).

Face under proof: APIMarketFace.api_seller_repeat_months. The lifetime
repeat face answers how many buyers ever came back and the market cohort
face answers new-versus-returning across the whole market on active
months only, so a single seller had no month axis at all. This suite
pins:

  - the eighteen-key envelope, the eleven-key month rows and an honest
    empty first;
  - the net authority: a refunded purchase is not a purchase, a refund
    removes the buyer from that month, moves their seller-first month
    forward when that month was the earliest, and erases a buyer whose
    every purchase was refunded;
  - the returning law: returning means the seller-first month is
    strictly earlier, so two purchases inside one month are new, not
    returning (the disclosed asymmetry against api_repeat_purchase's
    two-or-more-purchases lifetime law);
  - the contiguous grid across a year boundary with honest zero rows
    whose returning_share is None;
  - conservation of purchases, gross, the new/returning money split and
    the newcomer credits, plus cross-face identity of buyer_count and
    purchase_count with api_repeat_purchase on the same scope;
  - seller isolation (the two sellers' rows partition the market), the
    seven-form gate family failing closed before any read, frozen table
    digests and a constant ledger_tx set;
  - byte-identical repeats, three instances over two restarts, the
    reconcile wiring and the ASCII/LF source hygiene.

Usage: python test_apimarket_sellerrepeatmonths.py
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
    "dev_account", "scope", "buyer_count", "repeat_buyer_count",
    "repeat_rate", "purchase_count", "gross", "new_gross",
    "returning_gross", "month_count", "active_month_count",
    "first_month", "last_month", "peak_month",
    "peak_returning_buyer_count", "latest_month_returning_share",
    "disclaimer", "months"}

ROW_KEYS = {
    "month", "purchase_count", "gross", "buyer_count",
    "new_buyer_count", "returning_buyer_count", "returning_share",
    "new_purchase_count", "returning_purchase_count", "new_gross",
    "returning_gross"}

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
        self.value = "2025-11-01T00:00:00Z"

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


def purchase_on(am, buyer, listing_id, token):
    return am.purchase_api("usr:" + buyer, listing_id, token)


def purchase_id_of(am, buyer, listing_id):
    for row in am.api_library("usr:" + buyer)["purchases"]:
        if int(row["listing_id"]) == int(listing_id):
            return row["purchase_id"]
    raise AssertionError("no purchase of listing %r by %r"
                         % (listing_id, buyer))


def seed_world(led, dk, am, clock):
    """Two sellers. dana owns t1 and t2 at 10 each, lia owns d1.

    bob: NOV25 t1 (newcomer), DEC25 t2 (returning), JAN26 d1 at lia
         (isolation: dana's JAN stays a zero row).
    carol: FEB26 t1 (newcomer), OCT26 t2 (returning).
    erin: MAR26 t2 (newcomer).
    frank: APR26 t1, MAY26 t2, then refunds the APR purchase so his
         seller-first month moves to MAY and APR becomes a zero row.
    gina: JUL26 t1, refunded in SEP26 so she disappears entirely.
    ivan: AUG26 t1 and t2 on two days - one month, so never returning
         here while api_repeat_purchase still calls him a repeat buyer.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SRB-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SRB-S",
                     "settlement")
    for who in ("bob", "carol", "erin", "frank", "gina", "ivan"):
        fund(led, who)
    for dev in ("dana", "lia"):
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

    clock.value = "2025-11-05T00:00:00Z"
    purchase_on(am, "bob", t1, "SRB-BOB-T1")
    clock.value = "2025-12-05T00:00:00Z"
    purchase_on(am, "bob", t2, "SRB-BOB-T2")

    clock.value = "2026-01-10T00:00:00Z"
    purchase_on(am, "bob", d1, "SRB-BOB-D1")

    clock.value = "2026-02-10T00:00:00Z"
    purchase_on(am, "carol", t1, "SRB-CAROL-T1")

    clock.value = "2026-03-05T00:00:00Z"
    purchase_on(am, "erin", t2, "SRB-ERIN-T2")

    clock.value = "2026-04-05T00:00:00Z"
    purchase_on(am, "frank", t1, "SRB-FRANK-T1")

    clock.value = "2026-05-05T00:00:00Z"
    purchase_on(am, "frank", t2, "SRB-FRANK-T2")

    clock.value = "2026-06-05T00:00:00Z"
    am.refund_api("usr:frank",
                  purchase_id_of(am, "frank", t1),
                  "defective payloads")

    clock.value = "2026-07-05T00:00:00Z"
    purchase_on(am, "gina", t1, "SRB-GINA-T1")

    clock.value = "2026-08-05T00:00:00Z"
    purchase_on(am, "ivan", t1, "SRB-IVAN-T1")
    clock.value = "2026-08-06T00:00:00Z"
    purchase_on(am, "ivan", t2, "SRB-IVAN-T2")

    clock.value = "2026-09-05T00:00:00Z"
    am.refund_api("usr:gina",
                  purchase_id_of(am, "gina", t1),
                  "changed my mind")

    clock.value = "2026-10-05T00:00:00Z"
    purchase_on(am, "carol", t2, "SRB-CAROL-T2")

    return {"t1": t1, "t2": t2, "d1": d1}


def month_row(env, month):
    for row in env["months"]:
        if row["month"] == month:
            return row
    raise AssertionError("month %r missing" % (month,))


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerrepeatmonths-")
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

    dana = am.api_seller_repeat_months("usr:dana")
    lia = am.api_seller_repeat_months("usr:lia")

    # -- AC-SRB1 contract, row keys and honest empty -----------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-srb-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_repeat_months("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    no_arg_ok = False
    try:
        am.api_seller_repeat_months()
    except TypeError:
        no_arg_ok = True
    ok1 = (set(dana.keys()) == ENVELOPE_KEYS
           and len(dana) == 18
           and all(set(row.keys()) == ROW_KEYS
                   for row in dana["months"] + lia["months"])
           and len(ROW_KEYS) == 11
           and dana["scope"] == "seller"
           and dana["dev_account"] == "usr:dana"
           and dana["disclaimer"] == DISCLAIMER
           and empty["buyer_count"] == 0
           and empty["purchase_count"] == 0
           and empty["gross"] == 0
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["repeat_rate"] is None
           and empty["peak_month"] is None
           and empty["peak_returning_buyer_count"] is None
           and empty["latest_month_returning_share"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["disclaimer"] == DISCLAIMER
           and no_arg_ok)
    record("AC-SRB1", ok1,
           "keys=%r rows=%r empty=%r no_arg=%r"
           % (len(dana), len(ROW_KEYS),
              (empty["buyer_count"], empty["month_count"],
               empty["repeat_rate"]), no_arg_ok))

    # -- AC-SRB2 net authority, refund move and buyer erasure --------
    apr = month_row(dana, "2026-04")
    may = month_row(dana, "2026-05")
    jul = month_row(dana, "2026-07")
    sep = month_row(dana, "2026-09")
    conn = sqlite3.connect(am.db_path)
    net_rows = conn.execute(
        "SELECT COUNT(*) FROM apimarket_purchases p"
        " JOIN apimarket_listings l ON l.listing_id = p.listing_id"
        " WHERE l.dev_account = 'usr:dana' AND NOT EXISTS"
        " (SELECT 1 FROM apimarket_refunds f"
        "  WHERE f.purchase_id = p.purchase_id)").fetchone()[0]
    erin_apr = conn.execute(
        "SELECT COUNT(*) FROM apimarket_purchases"
        " WHERE buyer_id = 'usr:gina'").fetchone()[0]
    conn.close()
    ok2 = (apr["purchase_count"] == 0
           and apr["returning_share"] is None
           and apr["gross"] == 0
           and may["new_buyer_count"] == 1
           and may["returning_buyer_count"] == 0
           and jul["purchase_count"] == 0
           and jul["new_buyer_count"] == 0
           and sep["purchase_count"] == 0
           and dana["buyer_count"] == 5
           and erin_apr == 1
           and dana["purchase_count"] == int(net_rows) == 8)
    record("AC-SRB2", ok2,
           "apr=%r may=%r sep=%r buyers=%r net=%r"
           % ((apr["purchase_count"], apr["returning_share"]),
              (may["new_buyer_count"], may["returning_buyer_count"]),
              sep["purchase_count"], dana["buyer_count"],
              int(net_rows)))

    # -- AC-SRB3 returning composition and the money split -----------
    aug = month_row(dana, "2026-08")
    nov = month_row(dana, "2025-11")
    dec = month_row(dana, "2025-12")
    octo = month_row(dana, "2026-10")
    comp_ok = all(
        row["returning_buyer_count"]
        == row["buyer_count"] - row["new_buyer_count"]
        and row["returning_purchase_count"]
        == row["purchase_count"] - row["new_purchase_count"]
        and row["returning_gross"]
        == row["gross"] - row["new_gross"]
        for row in dana["months"])
    ok3 = (comp_ok
           and nov["new_buyer_count"] == 1
           and nov["returning_buyer_count"] == 0
           and nov["returning_share"] == 0.0
           and dec["returning_buyer_count"] == 1
           and dec["returning_share"] == 1.0
           and dec["returning_gross"] == 10
           and dec["new_gross"] == 0
           and aug["purchase_count"] == 2
           and aug["new_purchase_count"] == 2
           and aug["returning_purchase_count"] == 0
           and aug["new_buyer_count"] == 1
           and aug["returning_buyer_count"] == 0
           and octo["returning_buyer_count"] == 1
           and octo["returning_share"] == 1.0)
    record("AC-SRB3", ok3,
           "nov=%r dec=%r aug=%r oct=%r"
           % ((nov["new_buyer_count"], nov["returning_share"]),
              (dec["returning_buyer_count"], dec["returning_gross"]),
              (aug["purchase_count"], aug["new_purchase_count"]),
              (octo["returning_buyer_count"],
               octo["returning_share"])))

    # -- AC-SRB4 contiguous grid across the year and the credits -----
    names = [row["month"] for row in dana["months"]]
    zero_months = [row["month"] for row in dana["months"]
                   if row["purchase_count"] == 0]
    ok4 = (dana["month_count"] == 12
           and dana["first_month"] == "2025-11"
           and dana["last_month"] == "2026-10"
           and names[1] == "2025-12" and names[2] == "2026-01"
           and zero_months == ["2026-01", "2026-04", "2026-06",
                               "2026-07", "2026-09"]
           and all(row["returning_share"] is None
                   and row["buyer_count"] == 0
                   and row["gross"] == 0
                   for row in dana["months"]
                   if row["purchase_count"] == 0)
           and dana["active_month_count"] == 7
           and sum(row["new_buyer_count"] for row in dana["months"])
           == dana["buyer_count"]
           and dana["peak_month"] == "2025-12"
           and dana["peak_returning_buyer_count"] == 1
           and dana["latest_month_returning_share"] == 1.0)
    record("AC-SRB4", ok4,
           "months=%r zeros=%r active=%r peak=%r latest=%r"
           % (len(names), zero_months, dana["active_month_count"],
              dana["peak_month"], dana["latest_month_returning_share"]))

    # -- AC-SRB5 conservation and the disclosed cross-face gap ------
    lifetime = am.api_repeat_purchase("usr:dana")
    ok5 = (sum(row["purchase_count"] for row in dana["months"])
           == dana["purchase_count"]
           and sum(row["gross"] for row in dana["months"])
           == dana["gross"] == 80
           and sum(row["new_gross"] for row in dana["months"])
           == dana["new_gross"] == 60
           and sum(row["returning_gross"] for row in dana["months"])
           == dana["returning_gross"] == 20
           and dana["buyer_count"] == lifetime["buyer_count"] == 5
           and dana["purchase_count"]
           == lifetime["purchase_count"] == 8
           and dana["repeat_buyer_count"] == 2
           and lifetime["repeat_buyer_count"] == 3
           and lifetime["repeat_buyer_count"]
           - dana["repeat_buyer_count"] == 1
           and round(dana["repeat_rate"], 6) == round(2.0 / 5.0, 6))
    record("AC-SRB5", ok5,
           "sums=%r money=%r/%r/%r lifetime=%r/%r gap=%r"
           % (dana["purchase_count"], dana["gross"],
              dana["new_gross"], dana["returning_gross"],
              lifetime["buyer_count"], lifetime["repeat_buyer_count"],
              lifetime["repeat_buyer_count"]
              - dana["repeat_buyer_count"]))

    # -- AC-SRB6 isolation and the gate family -----------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_codes = []
    for bad in (None, "", "u", "usr", 123, [],
                {"usr:x": 1}):
        try:
            am.api_seller_repeat_months(bad)
        except A.ApiMarketError as exc:
            bad_codes.append(exc.code)
        else:
            bad_codes.append("ACCEPTED")
    digests_mid = market_digests(am)
    bare = am.api_seller_repeat_months("usr:")
    conn = sqlite3.connect(am.db_path)
    market_net = conn.execute(
        "SELECT COUNT(*) FROM apimarket_purchases p WHERE NOT"
        " EXISTS (SELECT 1 FROM apimarket_refunds f"
        " WHERE f.purchase_id = p.purchase_id)").fetchone()[0]
    conn.close()
    ok6 = (bad_codes == [A.E_AM_BAD_ACCOUNT] * 7
           and digests_before == digests_mid
           and bare["buyer_count"] == 0
           and bare["month_count"] == 0
           and lia["buyer_count"] == 1
           and lia["purchase_count"] == 1
           and lia["month_count"] == 1
           and month_row(lia, "2026-01")["new_buyer_count"] == 1
           and dana["purchase_count"] + lia["purchase_count"]
           == int(market_net) == 9
           and month_row(dana, "2026-01")["purchase_count"] == 0)
    record("AC-SRB6", ok6,
           "gates=%r bare=%r lia=%r partition=%r"
           % (bad_codes, (bare["buyer_count"], bare["month_count"]),
              (lia["buyer_count"], lia["month_count"]),
              (dana["purchase_count"], lia["purchase_count"],
               int(market_net))))

    # -- AC-SRB7 pure read and byte-identical repeats ----------------
    call_a = dumps(am.api_seller_repeat_months("usr:dana"))
    call_b = dumps(am.api_seller_repeat_months("usr:dana"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    led2, metered2, dk2, _gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_seller_repeat_months("usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_seller_repeat_months("usr:dana"))
    close_stack(am3, dk3, metered3, led3)
    ok7 = (call_a == call_b == call_c == call_d == dumps(dana)
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-SRB7", ok7,
           "bytes_same=%r digests_same=%r tx_same=%r"
           % (call_a == call_d == dumps(dana),
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-SRB8 hygiene and the wiring ------------------------------
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok8 = (b'"ledger-apimarket-sellerrepeatmonths"' in recon
           and b"test_apimarket_sellerrepeatmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src)
           and shas_before == shas_after)
    record("AC-SRB8", ok8,
           "wired=%r src_lf=%r test_ascii_lf=%r shas=%r"
           % (b'"ledger-apimarket-sellerrepeatmonths"' in recon,
              b"\r\n" not in src, b"\r\n" not in test_src,
              shas_before == shas_after))

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())