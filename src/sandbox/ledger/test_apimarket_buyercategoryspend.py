"""Acceptance suite for the apimarket buyer-side category spend face
(BigDomain R2149; canon = the explore-queue row seeded and claimed in
R2149, criteria AC-BCS1..AC-BCS8 registered in that claim note BEFORE
this code existed - honesty law; the AC-BCS prefix, the
api_buyer_category_spend name, this suite name, the
ledger-apimarket-buyercategoryspend runner label, avg_net_price as a
row key on this face and the include_uncategorized switch on this face
were all git-grep zero-occupancy anchored against HEAD 2026-10-27,
rc=1).

Face under proof: APIMarketFace.api_buyer_category_spend. The buyer
side had a time axis (api_buyer_months), a lifetime aggregate
(api_buyer_profile), a row face (api_library) and two statements, and
the market had a per-category demand face; nobody answered "where did
my money go". This window pins the new face:

  - the fourteen-key envelope and the fourteen-key rows on an honest
    empty world and on the loaded world;
  - row authority on the PURCHASE side (a category the buyer never
    bought in stays absent, a listed-but-unsold category never shows);
  - trade conservation per row and cash-basis totals that equal
    api_buyer_months' lifetime figures on the default call;
  - listing_count purchase-derived, seller_count distinct within the
    row and over the envelope (not a sum of rows);
  - a refund lowering only the net side of its own category;
  - the effective-category seam: a revise_category moves the buyer's
    spend bucket in one step, a round trip restores it byte for byte,
    and summing buyers reproduces api_category_demand;
  - strict buyer isolation, the uncategorized switch and the gate
    family with its pinned order;
  - cross-restart byte identity and the pure-read law.

Usage: python test_apimarket_buyercategoryspend.py
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
    "buyer_id", "category_count", "purchase_count", "refund_count",
    "net_purchase_count", "gross_spent", "refunded_tokens",
    "net_spent", "dev_paid_net", "platform_paid_net",
    "listing_count", "seller_count", "categories", "disclaimer"}

ROW_KEYS = {
    "category", "purchase_count", "refund_count",
    "net_purchase_count", "gross_spent", "refunded_tokens",
    "net_spent", "dev_paid", "platform_paid", "dev_paid_net",
    "platform_paid_net", "listing_count", "seller_count",
    "avg_net_price"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


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


def by_category(env):
    return {row["category"]: row for row in env["categories"]}


def seed_world(led, dk, am):
    """dana owns two 'data' listings and one uncategorized listing,
    frank one 'tools' listing, gina one 'media' listing that never
    sells. bob buys d1/d2/f1/d3 (data 13, tools 7, uncategorized 5 =
    25). carol buys d1 and f1 then refunds d1 (data gross 10 refunded
    10, tools 7). dave buys only g1 (media 6)."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BCS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BCS-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    dk.issue_key("usr:gina", "gina-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        category="data")["listing_id"]
    d3 = am.publish_api("usr:dana", "chart-raw", "Raw Chart API",
                        "uncategorized chart payloads", PAYLOAD, 5,
                        False)["listing_id"]
    f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 7,
                        False, category="tools")["listing_id"]
    g1 = am.publish_api("usr:gina", "media-pack", "Media Pack API",
                        "media pipeline pack", PAYLOAD, 6, False,
                        category="media")["listing_id"]
    for lid, ref in ((d1, "ref-bob-d1"), (d2, "ref-bob-d2"),
                     (f1, "ref-bob-f1"), (d3, "ref-bob-d3")):
        am.purchase_api("usr:bob", lid, ref)
    carol_d1 = am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:carol", f1, "ref-carol-f1")
    am.purchase_api("usr:dave", g1, "ref-dave-g1")
    am.refund_api("usr:carol", carol_d1["purchase_id"],
                  "listing did not match description")
    return d1, d2, d3, f1, g1, carol_d1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyercategoryspend-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, f1, g1, carol_d1 = seed_world(led, dk, am)

    # -- AC-BCS1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bcs-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_category_spend("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    bob = am.api_buyer_category_spend("usr:bob")
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in bob["categories"])
    ok1 = (set(bob.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and bob["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["buyer_id"] == "usr:nobody"
           and empty["category_count"] == 0
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["net_purchase_count"] == 0
           and empty["gross_spent"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_spent"] == 0
           and empty["listing_count"] == 0
           and empty["seller_count"] == 0
           and empty["categories"] == [])
    record("AC-BCS1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty_rows=%d"
           % (len(bob), set(bob.keys()) == ENVELOPE_KEYS,
              row_keys_ok, len(bob["categories"]),
              len(empty["categories"])))

    # -- AC-BCS2 purchase-side row authority and buyer isolation -------
    carol = am.api_buyer_category_spend("usr:carol")
    dave = am.api_buyer_category_spend("usr:dave")
    ok2 = ([row["category"] for row in bob["categories"]]
           == ["data", "tools", None]
           and [row["category"] for row in carol["categories"]]
           == ["data", "tools"]
           and [row["category"] for row in dave["categories"]]
           == ["media"]
           and bob["category_count"] == 3
           and carol["category_count"] == 2
           and dave["category_count"] == 1
           and bob["purchase_count"] == 4
           and carol["purchase_count"] == 2
           and dave["purchase_count"] == 1
           and bob["gross_spent"] == 25
           and carol["gross_spent"] == 17
           and dave["gross_spent"] == 6
           and "media" not in by_category(bob)
           and "media" not in by_category(carol)
           and None not in by_category(carol)
           and "data" not in by_category(dave))
    record("AC-BCS2", ok2,
           "bob=%r carol=%r dave=%r"
           % ([row["category"] for row in bob["categories"]],
              [row["category"] for row in carol["categories"]],
              [row["category"] for row in dave["categories"]]))

    # -- AC-BCS3 trade conservation and cross-face cash totals ---------
    view = by_category(bob)
    b_data = view["data"]
    b_tools = view["tools"]
    b_none = view[None]
    months = am.api_buyer_months("usr:bob")
    c_months = am.api_buyer_months("usr:carol")
    ok3 = (b_data["purchase_count"] == 2
           and b_data["gross_spent"] == 13
           and b_tools["gross_spent"] == 7
           and b_none["gross_spent"] == 5
           and all(row["gross_spent"]
                   == row["net_spent"] + row["refunded_tokens"]
                   for row in bob["categories"])
           and all(row["net_purchase_count"]
                   == row["purchase_count"] - row["refund_count"]
                   for row in bob["categories"])
           and all(row["dev_paid"] + row["platform_paid"]
                   == row["gross_spent"]
                   for row in bob["categories"])
           and all(row["dev_paid_net"] + row["platform_paid_net"]
                   == row["net_spent"]
                   for row in bob["categories"])
           and all(row["dev_paid_net"] <= row["dev_paid"]
                   and row["platform_paid_net"]
                   <= row["platform_paid"]
                   for row in bob["categories"])
           and bob["gross_spent"] == months["lifetime_gross_spent"]
           and bob["refunded_tokens"] == months["lifetime_refunded"]
           and bob["net_spent"] == months["lifetime_net_spent"]
           and bob["purchase_count"]
           == months["lifetime_purchase_count"]
           and bob["refund_count"] == months["lifetime_refund_count"]
           and bob["dev_paid_net"]
           == months["lifetime_dev_paid"]
           and bob["platform_paid_net"]
           == months["lifetime_platform_paid"]
           and carol["gross_spent"] == c_months["lifetime_gross_spent"]
           and carol["refunded_tokens"] == c_months["lifetime_refunded"]
           and carol["net_spent"] == c_months["lifetime_net_spent"])
    record("AC-BCS3", ok3,
           "data=%d tools=%d none=%d total=%d months=%d"
           % (b_data["gross_spent"], b_tools["gross_spent"],
              b_none["gross_spent"], bob["gross_spent"],
              months["lifetime_gross_spent"]))

    # -- AC-BCS4 listing_count purchase-derived, seller_count distinct -
    ok4 = (bob["listing_count"] == 4
           and b_data["listing_count"] == 2
           and b_tools["listing_count"] == 1
           and b_none["listing_count"] == 1
           and bob["listing_count"]
           == sum(row["listing_count"] for row in bob["categories"])
           and bob["seller_count"] == 2
           and b_data["seller_count"] == 1
           and b_tools["seller_count"] == 1
           and b_none["seller_count"] == 1
           and sum(row["seller_count"] for row in bob["categories"])
           == 3
           and bob["seller_count"] != sum(
               row["seller_count"] for row in bob["categories"])
           and carol["listing_count"] == 2
           and carol["seller_count"] == 2
           and dave["seller_count"] == 1)
    record("AC-BCS4", ok4,
           "listings=%d row_sum=%d sellers=%d row_seller_sum=%d"
           % (bob["listing_count"],
              sum(row["listing_count"] for row in bob["categories"]),
              bob["seller_count"],
              sum(row["seller_count"] for row in bob["categories"])))

    # -- AC-BCS5 refund lowers only its own category's net side --------
    c_view = by_category(carol)
    c_data = c_view["data"]
    c_tools = c_view["tools"]
    c_once = am.api_buyer_months("usr:carol")
    ok5 = (c_data["purchase_count"] == 1
           and c_data["refund_count"] == 1
           and c_data["net_purchase_count"] == 0
           and c_data["gross_spent"] == 10
           and c_data["refunded_tokens"] == 10
           and c_data["net_spent"] == 0
           and c_data["listing_count"] == 1
           and c_data["seller_count"] == 1
           and c_data["avg_net_price"] is None
           and c_data["dev_paid_net"] == 0
           and c_data["platform_paid_net"] == 0
           and c_tools["refund_count"] == 0
           and c_tools["net_spent"] == 7
           and c_tools["avg_net_price"] == 7.0
           and carol["net_purchase_count"] == 1
           and carol["net_spent"] == 7
           and carol["refunded_tokens"] == 10
           and c_once["lifetime_refund_count"] == 1
           and b_data["refund_count"] == 0
           and b_data["net_spent"] == 13
           and b_data["avg_net_price"] == 6.5)
    record("AC-BCS5", ok5,
           "carol_data net=%d refunded=%d avg=%r tools_avg=%r"
           % (c_data["net_spent"], c_data["refunded_tokens"],
              c_data["avg_net_price"], c_tools["avg_net_price"]))

    # -- AC-BCS6 the effective-category seam, round trip and demand ----
    before = dumps(bob)
    am.revise_category("usr:dana", d2, "tools")
    moved = by_category(am.api_buyer_category_spend("usr:bob"))
    demand = am.api_category_demand()
    demand_view = by_category(demand)
    ok6 = (moved["data"]["purchase_count"] == 1
           and moved["data"]["gross_spent"] == 10
           and moved["tools"]["purchase_count"] == 2
           and moved["tools"]["gross_spent"] == 10
           and moved["tools"]["listing_count"] == 2
           and moved[None]["gross_spent"] == 5
           and [row["category"]
                for row in am.api_buyer_category_spend(
                    "usr:bob")["categories"]]
           == ["data", "tools", None]
           and demand_view["data"]["purchase_count"] == 2
           and demand_view["tools"]["purchase_count"] == 3
           and demand_view["media"]["purchase_count"] == 1
           and demand_view[None]["purchase_count"] == 1
           and demand_view["data"]["purchase_count"]
           == (moved["data"]["purchase_count"]
               + by_category(carol)["data"]["purchase_count"])
           and demand_view["tools"]["purchase_count"]
           == (moved["tools"]["purchase_count"]
               + by_category(carol)["tools"]["purchase_count"])
           and demand_view[None]["purchase_count"]
           == moved[None]["purchase_count"])
    am.revise_category("usr:dana", d2, "data")
    restored = dumps(am.api_buyer_category_spend("usr:bob"))
    ok6 = ok6 and restored == before
    record("AC-BCS6", ok6,
           "moved_tools=%d demand_data=%d demand_tools=%d"
           " roundtrip=%r"
           % (moved["tools"]["gross_spent"],
              demand_view["data"]["purchase_count"],
              demand_view["tools"]["purchase_count"],
              restored == before))

    # -- AC-BCS7 the gate family, its order and the switch -------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in (None, "", "bob", "usr", 1, True, 1.5, [], {}):
        try:
            am.api_buyer_category_spend(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    flag_codes = []
    for bad in (None, 1, 0, "yes", [], {}):
        try:
            am.api_buyer_category_spend("usr:bob",
                                        include_uncategorized=bad)
            flag_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            flag_codes.append(getattr(exc, "code", "?"))
    order_codes = []
    for _ in range(2):
        try:
            am.api_buyer_category_spend("bob",
                                        include_uncategorized="yes")
            order_codes.append("NO-ERROR")
        except A.ApiMarketError as exc:
            order_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_buyer_category_spend("usr:")
    switched = am.api_buyer_category_spend(
        "usr:bob", include_uncategorized=False)
    s_view = by_category(switched)
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * 9
           and flag_codes == ["E_AM_BAD_ARGS"] * 6
           and order_codes == ["E_AM_BAD_ACCOUNT"] * 2
           and prefix["category_count"] == 0
           and prefix["purchase_count"] == 0
           and switched["category_count"] == 2
           and [row["category"] for row in switched["categories"]]
           == ["data", "tools"]
           and None not in s_view
           and switched["purchase_count"]
           == bob["purchase_count"] - 1
           and switched["gross_spent"]
           == bob["gross_spent"] - view[None]["gross_spent"]
           and switched["seller_count"] == 2
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-BCS7", ok7,
           "acct=%r flag=%r order=%r prefix_rows=%d switch_rows=%d"
           " frozen=%r"
           % (acct_codes, flag_codes, order_codes,
              prefix["category_count"], switched["category_count"],
              digests_before == digests_after))

    # -- AC-BCS8 cross-restart identity and the pure-read law ----------
    final = am.api_buyer_category_spend("usr:bob")
    first = dumps(final)
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second = dumps(am.api_buyer_category_spend("usr:bob"))
    second_carol = dumps(am.api_buyer_category_spend("usr:carol"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third = dumps(am.api_buyer_category_spend("usr:bob"))
    third_carol = dumps(am.api_buyer_category_spend("usr:carol"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_buyer_category_spend("usr:bob")
        am.api_buyer_category_spend("usr:carol")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (first == second == third
           and second_carol == third_carol
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-buyercategoryspend" in runner_text)
    record("AC-BCS8", ok8,
           "sha16=%s identical=%r tx_equal=%r digests_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(first.encode("utf-8")).hexdigest()[:16],
              first == second == third, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-buyercategoryspend" in runner_text))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS %d/%d" % (passed, total)
    if passed != total:
        verdict = "SUITE FAIL %d/%d" % (passed, total)
    print(verdict, flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())