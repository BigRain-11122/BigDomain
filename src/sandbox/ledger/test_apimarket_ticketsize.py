"""Acceptance suite for the apimarket achieved ticket-size face
(BigDomain R2184; canon = the explore-queue row seeded in R2178 and
claimed in R2184, criteria AC-MTS1..AC-MTS8 registered in that claim
note BEFORE this code existed - honesty law; the AC-MTS prefix,
ledger-apimarket-ticketsize, p90_ticket and _ticket_sample were
git-grep zero-occupancy against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_market_ticket_size. The asking
price percentiles answer what is still on the shelf, the position face
ranks one listing inside its bucket and the cash faces total money;
what a sale actually COSTS had no face, so the asking p50 and the
achieved p50 could drift apart invisibly. This suite pins:

  - the nineteen-key envelope and the ten-key rows, honest empty
    world first;
  - the net authority (a refunded purchase leaves the default sample)
    and the exact cross-face identity against api_market_stats on
    BOTH axes, plus partition conservation over rows;
  - the AC-MPP3 percentile law reused through one seam, on the exact
    sample [1..10] and on the one-sample and two-sample edges;
  - one row per effective category bucket, the uncategorized bucket
    last, and revise_category moving a ticket between buckets in one
    step that restores byte-identically on the way back;
  - the immutability of a historical ticket (revise_price and
    delist_api never rewrite price_paid) and the refund leg as the
    only way out of the default sample;
  - the seller scope law: strict isolation, per-seller sums equal to
    the market, and a single-seller world identical apart from the
    scope/dev_account pair;
  - the pinned gate order, the bool-only gate family, the pure-read
    law, cross-restart byte identity and the runner wiring.

Usage: python test_apimarket_ticketsize.py
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
    "scope", "dev_account", "include_refunded", "sale_count",
    "refunded_sale_count", "gross_tokens", "refunded_tokens",
    "net_gross_tokens", "min_ticket", "p25_ticket", "p50_ticket",
    "p75_ticket", "p90_ticket", "max_ticket", "mean_ticket", "spread",
    "category_count", "categories", "disclaimer"}

ROW_KEYS = {
    "category", "sale_count", "refunded_sale_count", "gross_tokens",
    "refunded_tokens", "net_gross_tokens", "min_ticket", "max_ticket",
    "mean_ticket", "p50_ticket"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def dumps(env):
    return json.dumps(env, sort_keys=True)


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
        " AND name LIKE 'apimarket_%' ORDER BY name").fetchall()]
    out = {}
    for name in names:
        rows = conn.execute(
            "SELECT * FROM " + name + " ORDER BY rowid").fetchall()
        out[name] = (len(rows),
                     hashlib.sha256(
                         repr(rows).encode("utf-8")).hexdigest())
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


def seed_devs(led, dk, devs, buyers):
    led.mint_to_pool("pool:reserve", 50000, "SETTLE-MTS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 50000, "SETTLE-MTS-S",
                     "settlement")
    for who in buyers:
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 2000),
                    ("usr:" + who, "credit", 2000)],
                   "manual:fund-" + who, "suite funding " + who)
    for who in devs:
        dk.issue_key("usr:" + who, who + "-key", 10, ["backtest"],
                     False)


def load_cfgs():
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    return cfg, lobby_cfg


def segment_map(env):
    """Envelope minus the two scope keys, so a seller scope and the
    market scope can be compared byte-for-byte on a single-seller
    world (AC-MTS6)."""
    out = dict(env)
    out.pop("scope", None)
    out.pop("dev_account", None)
    return out


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-ticketsize-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    cfg, lobby_cfg = load_cfgs()

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    buyers = ["b1", "b2", "b3", "b4", "b5", "b6"]
    seed_devs(led, dk, ("dana", "frank"), buyers)

    # dana: prices 2/4/6 in 'data', 8 in 'tools', 10 uncategorized.
    t1 = am.publish_api("usr:dana", "t-01", "Ticket 01",
                        "deterministic ticket sample", PAYLOAD, 2,
                        False, category="data")["listing_id"]
    t2 = am.publish_api("usr:dana", "t-02", "Ticket 02",
                        "deterministic ticket sample", PAYLOAD, 4,
                        False, category="data")["listing_id"]
    t3 = am.publish_api("usr:dana", "t-03", "Ticket 03",
                        "deterministic ticket sample", PAYLOAD, 6,
                        False, category="data")["listing_id"]
    t4 = am.publish_api("usr:dana", "t-04", "Ticket 04",
                        "deterministic ticket sample", PAYLOAD, 8,
                        False, category="tools")["listing_id"]
    t5 = am.publish_api("usr:dana", "t-05", "Ticket 05",
                        "deterministic ticket sample", PAYLOAD, 10,
                        False)["listing_id"]
    f1 = am.publish_api("usr:frank", "f-01", "Frank Ticket",
                        "deterministic ticket sample", PAYLOAD, 20,
                        False, category="tools")["listing_id"]

    buys = {}
    for buyer, listing in (("b1", t1), ("b2", t2), ("b3", t3),
                           ("b4", t4), ("b5", t5), ("b6", f1)):
        buys[buyer] = am.purchase_api("usr:" + buyer, listing,
                                      "ref-%s" % buyer)

    # -- AC-MTS1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mts-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_ticket_size()
    close_stack(e_am, e_dk, e_metered, e_led)
    base = am.api_market_ticket_size()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in base["categories"])
    ok1 = (set(base.keys()) == ENVELOPE_KEYS
           and len(base) == 19
           and set(empty.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and base["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["scope"] == "market"
           and empty["dev_account"] is None
           and empty["include_refunded"] is False
           and empty["sale_count"] == 0
           and empty["refunded_sale_count"] == 0
           and empty["gross_tokens"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_gross_tokens"] == 0
           and empty["min_ticket"] is None
           and empty["p25_ticket"] is None
           and empty["p50_ticket"] is None
           and empty["p75_ticket"] is None
           and empty["p90_ticket"] is None
           and empty["max_ticket"] is None
           and empty["mean_ticket"] is None
           and empty["spread"] is None
           and empty["category_count"] == 0
           and empty["categories"] == [])
    record("AC-MTS1", ok1,
           "env_keys=%d exact=%r rows=%d row_keys=%r empty_rows=%d"
           % (len(base), set(base.keys()) == ENVELOPE_KEYS,
              len(base["categories"]), row_keys_ok,
              len(empty["categories"])))

    # -- AC-MTS2 net authority and the cross-face identity ------------
    stats = am.api_market_stats()
    full = am.api_market_ticket_size(include_refunded=True)
    refund = am.refund_api("usr:b2", buys["b2"]["purchase_id"],
                           "changed my mind")
    stats_after = am.api_market_stats()
    net = am.api_market_ticket_size()
    back = am.api_market_ticket_size(include_refunded=True)
    row_sum_ok = (net["sale_count"]
                  == sum(r["sale_count"] for r in net["categories"])
                  and net["gross_tokens"]
                  == sum(r["gross_tokens"] for r in net["categories"])
                  and net["refunded_tokens"]
                  == sum(r["refunded_tokens"]
                         for r in net["categories"])
                  and back["sale_count"]
                  == sum(r["sale_count"] for r in back["categories"])
                  and back["gross_tokens"]
                  == sum(r["gross_tokens"]
                         for r in back["categories"])
                  and back["refunded_tokens"]
                  == sum(r["refunded_tokens"]
                         for r in back["categories"]))
    ok2 = (full["sale_count"] == stats["purchase_count"] == 6
           and full["gross_tokens"] == stats["gross_tokens"] == 50
           and full["refunded_tokens"] == stats["refunded_tokens"] == 0
           and full["net_gross_tokens"]
           == stats["net_gross_tokens"] == 50
           and net["sale_count"]
           == stats_after["net_purchase_count"] == 5
           and net["gross_tokens"]
           == stats_after["net_gross_tokens"] == 46
           and net["net_gross_tokens"] == 46
           and net["refunded_sale_count"] == 0
           and net["refunded_tokens"] == 0
           and back["sale_count"] == stats_after["purchase_count"] == 6
           and back["gross_tokens"]
           == stats_after["gross_tokens"] == 50
           and back["refunded_tokens"]
           == stats_after["refunded_tokens"] == 4
           and back["refunded_sale_count"] == 1
           and back["net_gross_tokens"]
           == stats_after["net_gross_tokens"] == 46
           and refund["purchase_id"] == buys["b2"]["purchase_id"]
           and row_sum_ok)
    record("AC-MTS2", ok2,
           "full=%r net=%r back=%r stats=%r row_sum=%r"
           % ((full["sale_count"], full["gross_tokens"]),
              (net["sale_count"], net["gross_tokens"]),
              (back["sale_count"], back["gross_tokens"],
               back["refunded_tokens"]),
              (stats_after["purchase_count"],
               stats_after["net_purchase_count"],
               stats_after["refunded_tokens"]), row_sum_ok))

    # -- AC-MTS3 the percentile law on the exact sample [1..10] -------
    sample_tmp = tempfile.mkdtemp(prefix="apimarket-mts-sample-")
    s_led, s_metered, s_dk, _s_gate, s_am = build_stack(
        os.path.join(sample_tmp, "ledger.db"), cfg, lobby_cfg)
    seed_devs(s_led, s_dk, ("dana",), ["c%02d" % i for i in range(1, 12)])
    for price in range(1, 11):
        lid = s_am.publish_api(
            "usr:dana", "s-%02d" % price, "Sample %02d" % price,
            "deterministic price sample", PAYLOAD, price, False,
            category="data")["listing_id"]
        s_am.purchase_api("usr:c%02d" % price, lid,
                          "ref-c%02d" % price)
    exact = s_am.api_market_ticket_size()
    exact_unfiltered = s_am.api_market_ticket_size(include_refunded=True)
    close_stack(s_am, s_dk, s_metered, s_led)

    one_tmp = tempfile.mkdtemp(prefix="apimarket-mts-one-")
    o_led, o_metered, o_dk, _o_gate, o_am = build_stack(
        os.path.join(one_tmp, "ledger.db"), cfg, lobby_cfg)
    seed_devs(o_led, o_dk, ("dana",), ["c01"])
    one_lid = o_am.publish_api(
        "usr:dana", "one", "One", "single sample", PAYLOAD, 7,
        False, category="data")["listing_id"]
    o_am.purchase_api("usr:c01", one_lid, "ref-one")
    single = o_am.api_market_ticket_size()
    close_stack(o_am, o_dk, o_metered, o_led)

    two_tmp = tempfile.mkdtemp(prefix="apimarket-mts-two-")
    w_led, w_metered, w_dk, _w_gate, w_am = build_stack(
        os.path.join(two_tmp, "ledger.db"), cfg, lobby_cfg)
    seed_devs(w_led, w_dk, ("dana",), ["c01", "c02"])
    for price in (4, 10):
        lid = w_am.publish_api(
            "usr:dana", "w-%d" % price, "W %d" % price,
            "two-sample", PAYLOAD, price, False,
            category="data")["listing_id"]
        w_am.purchase_api("usr:c0%d" % (1 if price == 4 else 2), lid,
                          "ref-w%d" % price)
    two = w_am.api_market_ticket_size()
    close_stack(w_am, w_dk, w_metered, w_led)

    with open(os.path.join(BASE, "apimarket.py"), "rb") as handle:
        prod_text = handle.read().decode("utf-8")
    _i0 = prod_text.find("def api_market_ticket_size")
    _i1 = prod_text.find("def api_buyer_rating_pattern")
    face_body = prod_text[_i0:_i1]

    _exact_a = dict(exact)
    _exact_b = dict(exact_unfiltered)
    _exact_a.pop("include_refunded", None)
    _exact_b.pop("include_refunded", None)
    ok3 = (exact["min_ticket"] == 1
           and exact["max_ticket"] == 10
           and exact["p25_ticket"] == 3.25
           and exact["p50_ticket"] == 5.5
           and exact["p75_ticket"] == 7.75
           and exact["p90_ticket"] == 9.1
           and exact["mean_ticket"] == 5.5
           and exact["spread"] == 9
           and exact["sale_count"] == 10
           and dumps(_exact_a) == dumps(_exact_b)
           and single["sale_count"] == 1
           and single["p25_ticket"] == 7.0
           and single["p50_ticket"] == 7.0
           and single["p75_ticket"] == 7.0
           and single["p90_ticket"] == 7.0
           and single["min_ticket"] == 7
           and single["max_ticket"] == 7
           and single["spread"] == 0
           and two["p50_ticket"] == 7.0
           and two["p25_ticket"] == 5.5
           and two["p75_ticket"] == 8.5
           and "def percentile(sorted_values, q):" in prod_text
           and face_body.count("percentile(vals,") == 5
           and "percentile(" in
           prod_text[prod_text.find("def api_market_price_percentiles"):
                     prod_text.find("def api_market_ticket_size")])
    record("AC-MTS3", ok3,
           "exact=%r single=%r two=%r"
           % ((exact["min_ticket"], exact["p25_ticket"],
               exact["p50_ticket"], exact["p75_ticket"],
               exact["p90_ticket"], exact["mean_ticket"],
               exact["spread"]),
              (single["p25_ticket"], single["p50_ticket"],
               single["spread"]),
              (two["p25_ticket"], two["p50_ticket"],
               two["p75_ticket"])))

    # -- AC-MTS4 category buckets and the revision seam ---------------
    pre_move = am.api_market_ticket_size()
    cats = [row["category"] for row in pre_move["categories"]]
    before_tools = {row["category"]: row
                    for row in pre_move["categories"]}
    am.revise_category("usr:dana", t3, "tools")
    moved = am.api_market_ticket_size()
    moved_cats = {row["category"]: row for row in moved["categories"]}
    am.revise_category("usr:dana", t3, "data")
    restored = am.api_market_ticket_size()
    ok4 = (cats == ["data", "tools", None]
           and before_tools["data"]["sale_count"] == 2
           and before_tools["data"]["min_ticket"] == 2
           and before_tools["data"]["max_ticket"] == 6
           and before_tools["tools"]["sale_count"] == 2
           and before_tools["tools"]["gross_tokens"] == 28
           and moved_cats["data"]["sale_count"] == 1
           and moved_cats["data"]["max_ticket"] == 2
           and moved_cats["tools"]["sale_count"] == 3
           and moved_cats["tools"]["gross_tokens"] == 34
           and moved_cats["tools"]["p50_ticket"] == 8.0
           and moved["sale_count"] == pre_move["sale_count"]
           and moved["gross_tokens"] == pre_move["gross_tokens"]
           and dumps(restored) == dumps(pre_move)
           and [r["category"] for r in moved["categories"]]
           == ["data", "tools", None])
    record("AC-MTS4", ok4,
           "cats=%r before=%r moved=%r restored=%r"
           % (cats,
              (before_tools["data"]["sale_count"],
               before_tools["tools"]["sale_count"]),
              (moved_cats["data"]["sale_count"],
               moved_cats["tools"]["sale_count"],
               moved_cats["tools"]["p50_ticket"]),
              dumps(restored) == dumps(pre_move)))

    # -- AC-MTS5 the historical ticket is immutable -------------------
    stable = dumps(am.api_market_ticket_size())
    am.revise_price("usr:dana", t1, 99)
    after_price = dumps(am.api_market_ticket_size())
    am.delist_api("usr:dana", t2)
    after_delist = dumps(am.api_market_ticket_size())
    # A delisted listing is terminal for NEW purchases, so the fresh
    # ticket is taken at the revised price on the still-live t1.
    am.purchase_api("usr:b2", t1, "ref-b2-t1")
    after_new_sale = am.api_market_ticket_size()
    stock_tmp = tempfile.mkdtemp(prefix="apimarket-mts-stock-")
    k_led, k_metered, k_dk, _k_gate, k_am = build_stack(
        os.path.join(stock_tmp, "ledger.db"), cfg, lobby_cfg)
    seed_devs(k_led, k_dk, ("dana",), ["c01", "c02"])
    capped = k_am.publish_api(
        "usr:dana", "capped", "Capped", "one unit", PAYLOAD, 5,
        False, category="data", supply=1)["listing_id"]
    k_am.purchase_api("usr:c01", capped, "ref-capped")
    sold_out = k_am.api_market_ticket_size()
    ok5 = (after_price == stable
           and after_delist == stable
           and after_new_sale["sale_count"] == 6
           and after_new_sale["gross_tokens"] == 145
           and after_new_sale["max_ticket"] == 99
           and sold_out["sale_count"] == 1
           and sold_out["gross_tokens"] == 5)
    close_stack(k_am, k_dk, k_metered, k_led)
    record("AC-MTS5", ok5,
           "price_frozen=%r delist_frozen=%r new_sale=%r capped=%r"
           % (after_price == stable, after_delist == stable,
              (after_new_sale["sale_count"],
               after_new_sale["gross_tokens"]),
              (sold_out["sale_count"], sold_out["gross_tokens"])))

    # -- AC-MTS6 the seller scope law ---------------------------------
    market_env = am.api_market_ticket_size()
    dana_env = am.api_market_ticket_size("usr:dana")
    frank_env = am.api_market_ticket_size("usr:frank")
    gina_env = am.api_market_ticket_size("usr:gina")
    sum_ok = (dana_env["sale_count"] + frank_env["sale_count"]
              + gina_env["sale_count"] == market_env["sale_count"]
              and dana_env["gross_tokens"] + frank_env["gross_tokens"]
              + gina_env["gross_tokens"] == market_env["gross_tokens"])
    bot_tmp = tempfile.mkdtemp(prefix="apimarket-mts-solo-")
    x_led, x_metered, x_dk, _x_gate, x_am = build_stack(
        os.path.join(bot_tmp, "ledger.db"), cfg, lobby_cfg)
    seed_devs(x_led, x_dk, ("dana",), ["c01", "c02"])
    for price in (3, 6):
        lid = x_am.publish_api(
            "usr:dana", "x-%d" % price, "X %d" % price,
            "solo world", PAYLOAD, price, False,
            category="data")["listing_id"]
        x_am.purchase_api("usr:c0%d" % (1 if price == 3 else 2), lid,
                          "ref-x%d" % price)
    solo_market = x_am.api_market_ticket_size()
    solo_seller = x_am.api_market_ticket_size("usr:dana")
    close_stack(x_am, x_dk, x_metered, x_led)
    ok6 = (market_env["scope"] == "market"
           and market_env["dev_account"] is None
           and dana_env["scope"] == "seller"
           and dana_env["dev_account"] == "usr:dana"
           and dana_env["sale_count"] == 5
           and dana_env["gross_tokens"] == 125
           and frank_env["sale_count"] == 1
           and frank_env["gross_tokens"] == 20
           and frank_env["max_ticket"] == 20
           and dana_env["max_ticket"] == 99
           and gina_env["sale_count"] == 0
           and gina_env["categories"] == []
           and sum_ok
           and dumps(segment_map(solo_market))
           == dumps(segment_map(solo_seller)))
    record("AC-MTS6", ok6,
           "dana=%r frank=%r gina=%r sum=%r solo_equal=%r"
           % ((dana_env["sale_count"], dana_env["gross_tokens"]),
              (frank_env["sale_count"], frank_env["gross_tokens"]),
              (gina_env["sale_count"],), sum_ok,
              dumps(segment_map(solo_market))
              == dumps(segment_map(solo_seller))))

    # -- AC-MTS7 the gate family and the pure read --------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    account_codes = []
    for bad in ("", "   ", 123, [], {}, "bob"):
        try:
            am.api_market_ticket_size(bad)
            account_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            account_codes.append(getattr(exc, "code", "?"))
    bool_codes = []
    for bad in (0, 1, "", "yes", None, [True]):
        try:
            am.api_market_ticket_size(None, bad)
            bool_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            bool_codes.append(getattr(exc, "code", "?"))
    order_code = "?"
    try:
        am.api_market_ticket_size("bob", 1)
    except A.ApiMarketError as exc:
        order_code = getattr(exc, "code", "?")
    bare = am.api_market_ticket_size("usr:")
    first = dumps(am.api_market_ticket_size())
    second = dumps(am.api_market_ticket_size())
    for _ in range(3):
        am.api_market_ticket_size()
        am.api_market_ticket_size(None, True)
        am.api_market_ticket_size("usr:dana")
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (account_codes == ["E_AM_BAD_ACCOUNT"] * 6
           and bool_codes == ["E_AM_BAD_ARGS"] * 6
           and order_code == "E_AM_BAD_ACCOUNT"
           and bare["sale_count"] == 0
           and bare["categories"] == []
           and bare["gross_tokens"] == 0
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-MTS7", ok7,
           "account=%r bool=%r order=%r bare=%r repeat=%r"
           " frozen=%r tx=%r"
           % (account_codes, bool_codes, order_code,
              bare["sale_count"], first == second,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-MTS8 cross-restart identity and the wiring ----------------
    final = dumps(am.api_market_ticket_size())
    final_full = dumps(am.api_market_ticket_size(None, True))
    final_seller = dumps(am.api_market_ticket_size("usr:dana"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_run = dumps(am.api_market_ticket_size())
    second_full = dumps(am.api_market_ticket_size(None, True))
    second_seller = dumps(am.api_market_ticket_size("usr:dana"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_run = dumps(am.api_market_ticket_size())
    third_full = dumps(am.api_market_ticket_size(None, True))
    third_seller = dumps(am.api_market_ticket_size("usr:dana"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_market_ticket_size()
        am.api_market_ticket_size(None, True)
        am.api_market_ticket_size("usr:dana")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    with open(os.path.abspath(__file__), "rb") as handle:
        own = handle.read()
    own_ascii = all(byte < 128 for byte in own)
    ok8 = (final == second_run == third_run
           and final_full == second_full == third_full
           and final_seller == second_seller == third_seller
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-ticketsize" in runner_text
           and own_ascii
           and b"\r" not in own)
    record("AC-MTS8", ok8,
           "sha16=%s identical=%r full_identical=%r seller_identical=%r"
           " tx_equal=%r digests_equal=%r files_equal=%r"
           " registered=%r ascii=%r"
           % (hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_run == third_run,
              final_full == second_full == third_full,
              final_seller == second_seller == third_seller,
              tx_b == tx_a, dig_b == dig_a,
              shas_before == shas_after,
              "ledger-apimarket-ticketsize" in runner_text,
              own_ascii))

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