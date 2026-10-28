"""Acceptance suite for the apimarket buyer-side watch-intent category
mix face (BigDomain R2191; canon = the R2189 seed 2/10 explore claim
row, criteria AC-BWCM1..AC-BWCM8 registered in that row BEFORE this
code existed - honesty law; the AC-BWCM1 label,
test_apimarket_buyerwatchcategorymix and
ledger-apimarket-buyerwatchcategorymix were all git-grep
zero-occupancy anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_buyer_watch_category_mix. The
watch side answers how many rows a buyer watches (api_watchlist),
their live state (api_watch_budget) and where the money went
(api_buyer_category_spend), but nothing answered "is my attention
biased to categories or to sellers". This suite pins:

  - the seventeen-key envelope and eleven-key rows, honest empty
    first;
  - the live-watch row authority (an unwatch leaves the roll, a watch
    on a retired listing stays counted as delisted, a purchased watch
    stays on the roll with the purchased/open split explicit);
  - the total order (-watch_count, -open_count, category) with the
    unclassified bucket pinned LAST on a genuine tie, rank 1..n and a
    cumulative_share landing on exactly 1.0;
  - conservation across rows and envelope, and the share/top1/top3
    law with None instead of a fake zero;
  - the herfindahl law (monopoly 10000.0, two equal buckets 5000.0)
    and the pareto law on integers including a run landing exactly on
    80%;
  - the seller axis (per-row distinct seller count, per-row top
    seller with the dev_account ascending tie-break, envelope-wide top
    seller by the same law);
  - the single _category_state seam (a revision moves one bucket in
    one step and reverting restores the bytes), strict buyer isolation
    and the market-wide benchmark;
  - the gate (eight bad forms), the bare prefix, cross-face identity
    with api_watchlist, the pure-read law, cross-instance and
    cross-restart byte identity and the wiring.

Usage: python test_apimarket_buyerwatchcategorymix.py
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
    "buyer_id", "watch_count", "category_count", "purchased_count",
    "open_count", "delisted_count", "seller_count", "top_seller",
    "top_seller_share", "top1_share", "top3_share", "herfindahl",
    "pareto_category_count", "market_watch_count", "market_herfindahl",
    "disclaimer", "rows"}

ROW_KEYS = {
    "category", "rank", "watch_count", "purchased_count", "open_count",
    "delisted_count", "seller_count", "top_seller", "top_seller_share",
    "share", "cumulative_share"}

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


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:" + who, "credit", 400)],
               "manual:fund-" + who, "suite funding " + who)


def cat_row(env, category):
    for row in env["rows"]:
        if row["category"] == category:
            return row
    raise AssertionError("category %r missing from rows" % (category,))


def seed_world(led, dk, am):
    """Listings: tools t1(dana)/l1(lia), data d2(dana)/l2(lia)/g1(gina),
    unclassified u1(ivan), art j1(jade), music m1(nina).

    bob watches seven live rows: tools 2 (dana 1, lia 1), data 2
    (dana 1, gina 1), art 1, music 1, unclassified 1. One of them
    (d2) is purchased, so data shows purchased 1 / open 1. l2 is
    watched then unwatched, so data must not become 3. j1 is retired
    after the watch, so art carries delisted_count 1.

    kit watches four rows (tools 2, data 2, none purchased) - the four
    of four cumulative lands exactly on 80% and buys the integer
    pareto law its boundary. sol watches one row (a monopoly). erin
    watches two rows so the market benchmark is not the buyer's own
    mix.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-BWCM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-BWCM-S",
                     "settlement")
    for who in ("bob", "kit", "sol", "erin"):
        fund(led, who)
    for dev in ("dana", "lia", "gina", "ivan", "jade", "nina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 40, False,
                        category="tools")["listing_id"]
    d2 = am.publish_api("usr:dana", "d2", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    l1 = am.publish_api("usr:lia", "l1", "Lia Tools API",
                        "lia tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    l2 = am.publish_api("usr:lia", "l2", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    u1 = am.publish_api("usr:ivan", "u1", "Ivan Plain API",
                        "ivan plain payloads", PAYLOAD, 10, False
                        )["listing_id"]
    j1 = am.publish_api("usr:jade", "j1", "Jade Art API",
                        "jade art payloads", PAYLOAD, 30, False,
                        category="art")["listing_id"]
    m1 = am.publish_api("usr:nina", "m1", "Nina Music API",
                        "nina music payloads", PAYLOAD, 10, False,
                        category="music")["listing_id"]

    for lid in (t1, l1, d2, g1, u1, j1, m1, l2):
        am.watch_api("usr:bob", lid)
    am.unwatch_api("usr:bob", l2)
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    am.delist_api("usr:jade", j1)

    for lid in (t1, l1, d2, g1):
        am.watch_api("usr:kit", lid)
    am.watch_api("usr:sol", t1)
    am.watch_api("usr:erin", d2)
    am.watch_api("usr:erin", m1)

    return {"t1": t1, "d2": d2, "l1": l1, "l2": l2, "g1": g1,
            "u1": u1, "j1": j1, "m1": m1}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerwatchcategorymix-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    ids = seed_world(led, dk, am)

    # -- AC-BWCM1 the contract, honest empty first --------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-bwcm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_buyer_watch_category_mix("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    bob = am.api_buyer_watch_category_mix("usr:bob")
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in bob["rows"])
    ok1 = (set(bob.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and bob["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["buyer_id"] == "usr:nobody"
           and empty["watch_count"] == 0
           and empty["category_count"] == 0
           and empty["purchased_count"] == 0
           and empty["open_count"] == 0
           and empty["delisted_count"] == 0
           and empty["seller_count"] == 0
           and empty["top_seller"] is None
           and empty["top_seller_share"] is None
           and empty["top1_share"] is None
           and empty["top3_share"] is None
           and empty["herfindahl"] is None
           and empty["pareto_category_count"] is None
           and empty["market_watch_count"] == 0
           and empty["rows"] == [])
    record("AC-BWCM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(bob), set(bob.keys()) == ENVELOPE_KEYS,
              rows_ok, (empty["watch_count"], empty["market_watch_count"])))

    # -- AC-BWCM2 authority, order, pin and cumulative ----------------
    order = [row["category"] for row in bob["rows"]]
    ranks = [row["rank"] for row in bob["rows"]]
    cum = [row["cumulative_share"] for row in bob["rows"]]
    ok2 = (order == ["tools", "data", "art", "music", None]
           and ranks == [1, 2, 3, 4, 5]
           and cum == [0.285714, 0.571429, 0.714286, 0.857143, 1.0]
           and cat_row(bob, None)["rank"] == 5
           and cat_row(bob, "art")["rank"] == 3
           and cat_row(bob, "art")["delisted_count"] == 1
           and cat_row(bob, "art")["watch_count"] == 1
           and cat_row(bob, "data")["watch_count"] == 2
           and cat_row(bob, "data")["purchased_count"] == 1
           and cat_row(bob, "data")["open_count"] == 1
           and cat_row(bob, "tools")["open_count"] == 2
           and am.api_watchlist("usr:bob")["watch_count"] == 7)
    record("AC-BWCM2", ok2,
           "order=%r ranks=%r cum=%r" % (order, ranks, cum))

    # -- AC-BWCM3 conservation ---------------------------------------
    sum_w = sum(r["watch_count"] for r in bob["rows"])
    sum_p = sum(r["purchased_count"] for r in bob["rows"])
    sum_o = sum(r["open_count"] for r in bob["rows"])
    sum_d = sum(r["delisted_count"] for r in bob["rows"])
    per_row = all(r["watch_count"] == r["purchased_count"]
                  + r["open_count"] for r in bob["rows"])
    live = am.api_watchlist("usr:bob")["watch_count"]
    ok3 = (sum_w == bob["watch_count"] == live == 7
           and sum_p == bob["purchased_count"] == 1
           and sum_o == bob["open_count"] == 6
           and sum_d == bob["delisted_count"] == 1
           and per_row
           and bob["category_count"] == len(bob["rows"]))
    record("AC-BWCM3", ok3,
           "sum_w=%d sum_p=%d sum_o=%d sum_d=%d live=%d per_row=%r"
           % (sum_w, sum_p, sum_o, sum_d, live, per_row))

    # -- AC-BWCM4 distribution law -----------------------------------
    total = bob["watch_count"]
    shares = [r["share"] for r in bob["rows"]]
    ok4 = (shares == [round(2 / 7.0, 6), round(2 / 7.0, 6),
                      round(1 / 7.0, 6), round(1 / 7.0, 6),
                      round(1 / 7.0, 6)]
           and abs(sum(shares) - 1.0) < 1e-5
           and bob["top1_share"] == shares[0]
           and bob["top3_share"] == round(sum(shares[:3]), 6)
           and bob["herfindahl"] == round(
               sum((float(r["watch_count"]) / total) ** 2
                   for r in bob["rows"]) * 10000, 2)
           and bob["herfindahl"] == 2244.9
           and bob["pareto_category_count"] == 4
           and am.api_buyer_watch_category_mix(
               "usr:kit")["pareto_category_count"] == 2
           and am.api_buyer_watch_category_mix(
               "usr:kit")["herfindahl"] == 5000.0
           and am.api_buyer_watch_category_mix(
               "usr:sol")["herfindahl"] == 10000.0
           and am.api_buyer_watch_category_mix(
               "usr:sol")["top3_share"] == 1.0
           and empty["top3_share"] is None)
    record("AC-BWCM4", ok4,
           "shares=%r top1=%r top3=%r h=%.2f pareto=%r"
           % (shares, bob["top1_share"], bob["top3_share"],
              bob["herfindahl"], bob["pareto_category_count"]))

    # -- AC-BWCM5 the seller axis ------------------------------------
    row = cat_row(bob, "tools")
    ok5 = (row["seller_count"] == 2
           and row["top_seller"] == "usr:dana"
           and row["top_seller_share"] == 0.5
           and cat_row(bob, "data")["seller_count"] == 2
           and cat_row(bob, "data")["top_seller"] == "usr:dana"
           and cat_row(bob, "data")["top_seller_share"] == 0.5
           and cat_row(bob, None)["seller_count"] == 1
           and cat_row(bob, None)["top_seller"] == "usr:ivan"
           and cat_row(bob, None)["top_seller_share"] == 1.0
           and bob["seller_count"] == 6
           and bob["top_seller"] == "usr:dana"
           and bob["top_seller_share"] == round(2 / 7.0, 6))
    record("AC-BWCM5", ok5,
           "tools_row=%r env_top=%r share=%r"
           % ((row["seller_count"], row["top_seller"],
               row["top_seller_share"]),
              bob["top_seller"], bob["top_seller_share"]))

    # -- AC-BWCM6 the single seam, isolation and the benchmark -------
    before = dumps(bob)
    am.revise_category("usr:gina", ids["g1"], "tools")
    moved = am.api_buyer_watch_category_mix("usr:bob")
    flags6 = [
        cat_row(moved, "tools")["watch_count"] == 3,
        cat_row(moved, "tools")["open_count"] == 3,
        cat_row(moved, "data")["watch_count"] == 1,
        cat_row(moved, "data")["open_count"] == 0,
        [r["category"] for r in moved["rows"]]
        == ["tools", "art", "music", None, "data"],
        cat_row(moved, "tools")["seller_count"] == 3]
    am.revise_category("usr:gina", ids["g1"], "data")
    reverted = am.api_buyer_watch_category_mix("usr:bob")
    kit = am.api_buyer_watch_category_mix("usr:kit")
    erin = am.api_buyer_watch_category_mix("usr:erin")
    flags6 += [dumps(reverted) == before,
               kit["watch_count"] == 4,
               [r["category"] for r in kit["rows"]] == ["data", "tools"],
               erin["watch_count"] == 2,
               bob["market_watch_count"] == 14,
               bob["market_herfindahl"] == 2857.14,
               bob["market_herfindahl"] == erin["market_herfindahl"],
               bob["market_watch_count"] == erin["market_watch_count"]]
    ok6 = all(flags6)
    record("AC-BWCM6", ok6,
           "moved=%r reverted_same=%r kit=%r market=%.2f flags=%r"
           % ([r["category"] for r in moved["rows"]],
              dumps(reverted) == before, kit["watch_count"],
              bob["market_herfindahl"], flags6))

    # -- AC-BWCM7 pure read and deterministic bytes -----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_buyer_watch_category_mix("usr:bob"))
    call_b = dumps(am.api_buyer_watch_category_mix("usr:bob"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_buyer_watch_category_mix("usr:bob"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_buyer_watch_category_mix("usr:bob"))
    close_stack(am3, dk3, metered3, led3)

    ok7 = (digests_before == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == before)
    record("AC-BWCM7", ok7,
           "digests_same=%r tx_same=%d bytes_same=%r len=%d"
           % (digests_before == digests_after, len(tx_before),
              call_a == call_d, len(call_a)))

    # -- AC-BWCM8 the gate and the wiring ---------------------------
    bad = [None, "", "   ", "nobody", "usr", "user:x", 123, "USR:x"]
    passed = []
    for value in bad:
        try:
            am.api_buyer_watch_category_mix(value)
        except A.ApiMarketError as exc:
            passed.append(str(exc).find(A.E_AM_BAD_ACCOUNT) >= 0)
        else:
            passed.append(False)
    bare = am.api_buyer_watch_category_mix("usr:")
    recon = open(os.path.join(
        os.path.dirname(BASE), "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (all(passed)
           and bare["watch_count"] == 0
           and bare["rows"] == []
           and bare["market_watch_count"] == 14
           and b'"ledger-apimarket-buyerwatchcategorymix"' in recon
           and b"test_apimarket_buyerwatchcategorymix.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-BWCM8", ok8,
           "gate=%r bare=%r wired=%r ascii_lf=%r"
           % (passed, bare["watch_count"],
              b"ledger-apimarket-buyerwatchcategorymix" in recon,
              b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())