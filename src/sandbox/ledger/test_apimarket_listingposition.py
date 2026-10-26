"""Acceptance suite for the apimarket per-listing competitive
position face (BigDomain R2144; canon = the explore-queue row seeded
and claimed in R2144, criteria AC-AMPOS1..AC-AMPOS8 registered in
that claim note BEFORE this code existed - honesty law; the AC-AMPOS
prefix, api_listing_position, the suite name and the
ledger-apimarket-listingposition runner label were all git-grep
zero-occupancy anchored 2026-10-26, rc=1).

Face under proof: APIMarketFace.api_listing_position. The catalog
face answers what a category is made of (R2132/R2141 answer the
supply and demand sides) and the market faces answer the whole
market, but nothing answered the seller's own question: "where do I
stand against the listings I actually compete with". This window
pins that face:

  - the contract (25-key envelope, 10-key rival rows, bucket
    derivation from the stored category declaration, the honest
    uncategorized bucket, the singleton bucket, effective titles);
  - the price axis (total-order positions, listing_id tie-break,
    cheaper/pricier counts excluding ties, min/max band, a
    repricing moving ranks in one step while the base row is never
    rewritten);
  - the sales axis (net sales through the scarcity seam, tie-break
    law, a refund lowering a rank with no listing row touched);
  - the rating axis (effective stars through the aggregate seam, a
    revision moving a rank, revise-back legality, zero-rating
    listings last, ratings of a retired listing still counted);
  - the retirement law (a retired listing keeps its bucket, ranks
    and history while the partition counters move, and a re-listing
    returns it live);
  - the gate family and gate ORDER (six bad listing forms, the
    unknown listing, five bad limit forms, listing-before-limit),
    all fail-closed with frozen table digests and a constant ledger
    transaction set;
  - the pure-read law plus same-call byte identity;
  - cross-restart byte identity on three instances, the product
    files' sha being unchanged and the runner registration.

Usage: python test_apimarket_listingposition.py
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
    "listing_id", "listing_key", "title", "dev_account", "category",
    "live", "delisted_utc", "current_price", "net_sales",
    "rating_count", "rating_avg", "price_rank", "sales_rank",
    "rating_rank", "cheaper_count", "pricier_count",
    "category_size", "category_live_count",
    "category_retired_count", "category_min_price",
    "category_max_price", "rivals", "returned", "truncated",
    "disclaimer"}

ROW_KEYS = {
    "listing_id", "dev_account", "listing_key", "title",
    "current_price", "net_sales", "rating_count", "rating_avg",
    "live", "delisted_utc"}


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
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
        " AND name LIKE 'apimarket_%' ORDER BY name").fetchall()]
    out = {t: table_digest(conn, t) for t in names}
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


def rival_ids(env):
    return [row["listing_id"] for row in env["rivals"]]


def expect_code(fn, code):
    """Run fn and return the error code it raised ('' when it did
    not raise at all)."""
    try:
        fn()
    except A.ApiMarketError as exc:
        return str(exc.code)
    return ""


def seed_world(led, dk, am):
    """One deterministic world.

    Category 'data': L1 dana price 10 (unrated), L2 dana price 3,
    L3 frank price 5. Uncategorized: L4 dana price 5, L5 frank
    price 7. Category 'tools': L6 dana price 4 alone.

    Purchases: bob L2, carol L2, bob L3, dave L3, carol L1.
    Ratings: bob L2 five stars, carol L2 one star (avg 3.0), bob L3
    four, dave L3 five (avg 4.5).
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AMPOS-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AMPOS-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    l1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    l2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        category="data")["listing_id"]
    l3 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 5,
                        False, category="data")["listing_id"]
    l4 = am.publish_api("usr:dana", "chart-raw", "Raw Chart API",
                        "uncategorized chart payloads", PAYLOAD, 5,
                        False)["listing_id"]
    l5 = am.publish_api("usr:frank", "docs-kit", "Docs Kit API",
                        "document pipeline kit", PAYLOAD, 7, False)
    l5 = l5["listing_id"]
    l6 = am.publish_api("usr:dana", "tools-a", "Tools A API",
                        "tool listing alone in its category",
                        PAYLOAD, 4, False,
                        category="tools")["listing_id"]
    bob_l2 = am.purchase_api("usr:bob", l2, "ref-bob-l2")["purchase_id"]
    carol_l2 = am.purchase_api("usr:carol", l2,
                               "ref-carol-l2")["purchase_id"]
    am.purchase_api("usr:bob", l3, "ref-bob-l3")
    am.purchase_api("usr:dave", l3, "ref-dave-l3")
    am.purchase_api("usr:carol", l1, "ref-carol-l1")
    bob_l2_rate = am.rate_api("usr:bob", l2, 5)["rating_id"]
    am.rate_api("usr:carol", l2, 1)
    bob_l3_rate = am.rate_api("usr:bob", l3, 4)["rating_id"]
    am.rate_api("usr:dave", l3, 5)
    return {"data": (l1, l2, l3), "none": (l4, l5),
            "tools": l6, "bob_l2": bob_l2, "carol_l2": carol_l2,
            "bob_l2_rate": bob_l2_rate, "bob_l3_rate": bob_l3_rate}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-listingposition-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    world = seed_world(led, dk, am)
    l1, l2, l3 = world["data"]
    l4, l5 = world["none"]
    l6 = world["tools"]

    # -- AC-AMPOS1: contract, bucket derivation, effective titles ------
    env = am.api_listing_position(l3)
    ok = set(env) == ENVELOPE_KEYS
    ok = ok and all(set(row) == ROW_KEYS for row in env["rivals"])
    ok = ok and env["listing_id"] == l3 and env["category"] == "data"
    ok = ok and env["category_size"] == 3
    ok = ok and env["category_live_count"] == 3
    ok = ok and env["category_retired_count"] == 0
    ok = ok and env["returned"] == 3 and env["truncated"] is False
    ok = ok and rival_ids(env) == [l2, l3, l1]
    none_env = am.api_listing_position(l4)
    ok = ok and none_env["category"] is None
    ok = ok and none_env["category_size"] == 2
    ok = ok and rival_ids(none_env) == [l4, l5]
    tools_env = am.api_listing_position(l6)
    ok = ok and tools_env["category"] == "tools"
    ok = ok and tools_env["category_size"] == 1
    ok = ok and rival_ids(tools_env) == [l6]
    ok = ok and tools_env["price_rank"] == 1
    ok = ok and tools_env["cheaper_count"] == 0
    ok = ok and tools_env["pricier_count"] == 0
    am.edit_listing("usr:frank", l3, title="Chart Kit v2")
    titled = am.api_listing_position(l3)
    base_title = am.api_view(l3)["base_title"]
    ok = ok and titled["title"] == "Chart Kit v2"
    ok = ok and titled["rivals"][1]["title"] == "Chart Kit v2"
    ok = ok and base_title == "Chart Kit API"
    record("AC-AMPOS1", ok,
           "envelope=%d keys rows=%d keys; data bucket %s; "
           "uncategorized %s; tools singleton rank 1; effective "
           "title carried with base row preserved"
           % (len(env), len(env["rivals"][0]), rival_ids(env),
              rival_ids(none_env)))

    # -- AC-AMPOS2: price axis, total order, tie-break, band -----------
    env = am.api_listing_position(l3)
    ok = env["price_rank"] == 2 and env["cheaper_count"] == 1
    ok = ok and env["pricier_count"] == 1
    ok = ok and env["category_min_price"] == 3
    ok = ok and env["category_max_price"] == 10
    am.revise_price("usr:frank", l3, 2)
    cheap = am.api_listing_position(l3)
    ok = ok and cheap["price_rank"] == 1
    ok = ok and cheap["cheaper_count"] == 0
    ok = ok and cheap["pricier_count"] == 2
    ok = ok and cheap["category_min_price"] == 2
    ok = ok and rival_ids(cheap) == [l3, l2, l1]
    view = am.api_view(l3)
    ok = ok and view["base_token_price"] == 5
    ok = ok and view["token_price"] == 2
    am.revise_price("usr:frank", l3, 3)
    tie = am.api_listing_position(l3)
    tie_l2 = am.api_listing_position(l2)
    ok = ok and tie["current_price"] == 3
    ok = ok and tie_l2["price_rank"] == 1 and tie["price_rank"] == 2
    ok = ok and tie["cheaper_count"] == 0
    ok = ok and tie_l2["pricier_count"] == 1
    ranks = sorted([tie["price_rank"], tie_l2["price_rank"],
                    am.api_listing_position(l1)["price_rank"]])
    ok = ok and ranks == [1, 2, 3]
    am.revise_price("usr:frank", l3, 2)
    record("AC-AMPOS2", ok,
           "price rank 2->1 after 5->2; base row still 5 and current "
           "2; equal prices at 3 give distinct positions 1/2 by "
           "listing_id; band min/max tracked; ranks %s" % (ranks,))

    # -- AC-AMPOS3: sales axis, tie-break, refund seam -----------------
    env_l2 = am.api_listing_position(l2)
    env_l3 = am.api_listing_position(l3)
    ok = env_l2["net_sales"] == 2 and env_l2["sales_rank"] == 1
    ok = ok and env_l3["net_sales"] == 2 and env_l3["sales_rank"] == 2
    am.refund_api("usr:carol", world["carol_l2"], "suite refund")
    after = am.api_listing_position(l2)
    after_l3 = am.api_listing_position(l3)
    after_l1 = am.api_listing_position(l1)
    ok = ok and after["net_sales"] == 1
    ok = ok and after["sales_rank"] == 3
    ok = ok and after_l3["sales_rank"] == 1
    ok = ok and after_l1["sales_rank"] == 2
    ok = ok and after["rating_count"] == 2
    view = am.api_view(l2)
    ok = ok and view["purchase_count"] == 2
    ok = ok and view["net_purchase_count"] == 1
    record("AC-AMPOS3", ok,
           "tie at net 2 broken by id (l2 rank 1, l3 rank 2); after "
           "one refund l2 net 1 and rank 3 while l3 is rank 1 and l1 "
           "rank 2; the purchase rows are untouched (2 gross, 1 net)")

    # -- AC-AMPOS4: rating axis, revision movement, zero-rating last ---
    env = am.api_listing_position(l3)
    env_l2 = am.api_listing_position(l2)
    env_l1 = am.api_listing_position(l1)
    ok = env["rating_count"] == 2 and abs(env["rating_avg"] - 4.5) < 1e-9
    ok = ok and env["rating_rank"] == 1
    ok = ok and abs(env_l2["rating_avg"] - 3.0) < 1e-9
    ok = ok and env_l2["rating_rank"] == 2
    ok = ok and env_l1["rating_count"] == 0
    ok = ok and env_l1["rating_avg"] == 0.0
    ok = ok and env_l1["rating_rank"] == 3
    am.revise_rating("usr:bob", world["bob_l3_rate"], 1)
    moved = am.api_listing_position(l3)
    moved_l2 = am.api_listing_position(l2)
    ok = ok and abs(moved["rating_avg"] - 3.0) < 1e-9
    ok = ok and moved["rating_rank"] == 2
    ok = ok and moved_l2["rating_rank"] == 1
    ok = ok and moved["rating_count"] == 2
    am.revise_rating("usr:bob", world["bob_l3_rate"], 5)
    back = am.api_listing_position(l3)
    ok = ok and abs(back["rating_avg"] - 5.0) < 1e-9
    ok = ok and back["rating_rank"] == 1
    record("AC-AMPOS4", ok,
           "avg 4.5 rank 1; revising 4->1 drops to 3.0 and swaps with "
           "l2 (rank 2); revising back to 5 restores rank 1; the "
           "unrated listing is last and rating_count never moved")

    # -- AC-AMPOS5: retirement keeps bucket, ranks and history ---------
    am.delist_api("usr:dana", l2)
    retired = am.api_listing_position(l2)
    bucket = am.api_listing_position(l3)
    ok = retired["live"] is False and retired["delisted_utc"] is not None
    ok = ok and retired["category_size"] == 3
    ok = ok and retired["rating_count"] == 2
    ok = ok and abs(retired["rating_avg"] - 3.0) < 1e-9
    ok = ok and retired["net_sales"] == 1
    ok = ok and retired["price_rank"] == 2
    ok = ok and bucket["category_live_count"] == 2
    ok = ok and bucket["category_retired_count"] == 1
    ok = ok and l2 in rival_ids(bucket)
    ok = ok and [r for r in bucket["rivals"]
                 if r["listing_id"] == l2][0]["live"] is False
    am.relist_api("usr:dana", l2)
    live = am.api_listing_position(l2)
    ok = ok and live["live"] is True and live["delisted_utc"] is None
    ok = ok and live["category_live_count"] == 3
    ok = ok and live["category_retired_count"] == 0
    ok = ok and live["net_sales"] == 1 and live["rating_count"] == 2
    record("AC-AMPOS5", ok,
           "retired l2 keeps its bucket slot, ranks, 1 net sale and "
           "two ratings while the partition reads 2 live / 1 retired; "
           "a re-listing returns it live with history intact")

    # -- AC-AMPOS6: gate family, gate order, frozen side effects -------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_id_codes = [expect_code(
        lambda v=v: am.api_listing_position(v), "X")
        for v in (0, -3, "1", True, 1.5, None)]
    ok = all(code == "E_AM_BAD_ARGS" for code in bad_id_codes)
    ok = ok and expect_code(
        lambda: am.api_listing_position(999999), "X") == \
        "E_AM_UNKNOWN_LISTING"
    bad_limit_codes = [expect_code(
        lambda v=v: am.api_listing_position(l3, v), "X")
        for v in (0, -2, "2", True, 2.0)]
    ok = ok and all(code == "E_AM_BAD_ARGS" for code in bad_limit_codes)
    ok = ok and expect_code(
        lambda: am.api_listing_position(999999, 0), "X") == \
        "E_AM_UNKNOWN_LISTING"
    ok = ok and am.api_listing_position(l3, 1)["returned"] == 1
    ok = ok and am.api_listing_position(l3, 99)["truncated"] is False
    head = am.api_listing_position(l3, 2)
    ok = ok and head["returned"] == 2 and head["truncated"] is True
    ok = ok and head["category_size"] == 3
    ok = ok and rival_ids(head) == [l3, l2]
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok = ok and digests_before == digests_after
    ok = ok and tx_before == tx_after
    record("AC-AMPOS6", ok,
           "six bad ids %s; unknown listing; five bad limits %s; "
           "unknown-listing-plus-bad-limit answers UNKNOWN_LISTING "
           "(listing gate first); limit keeps the cheapest head with "
           "category_size intact; %d table digests and %d ledger "
           "transactions frozen"
           % (bad_id_codes, bad_limit_codes, len(digests_after),
              len(tx_after)))

    # -- AC-AMPOS7: pure read and same-call determinism ----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_listing_position(l1))
    second = dumps(am.api_listing_position(l1))
    ok = first == second
    for target in (l1, l2, l3, l4, l5, l6):
        am.api_listing_position(target)
        am.api_listing_position(target, 1)
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok = ok and digests_before == digests_after
    ok = ok and tx_before == tx_after
    with open(os.path.join(BASE, "apimarket.py"), "rb") as handle:
        src = handle.read().decode("utf-8")
    ok = ok and "INSERT INTO" not in src.split(
        "def api_listing_position")[1].split("\n    def ")[0]
    record("AC-AMPOS7", ok,
           "twelve calls across six buckets leave %d table digests and "
           "%d ledger transactions unchanged; the face body carries no "
           "INSERT; same call twice is byte-identical"
           % (len(digests_after), len(tx_after)))

    # -- AC-AMPOS8: cross-restart identity, file hygiene, wiring -------
    snap1 = [dumps(am.api_listing_position(t)) for t in (l1, l4, l6)]
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    snap2 = [dumps(am2.api_listing_position(t)) for t in (l1, l4, l6)]
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    snap3 = [dumps(am3.api_listing_position(t)) for t in (l1, l4, l6)]
    close_stack(am3, dk3, metered3, led3)
    ok = snap1 == snap2 and snap2 == snap3
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok = ok and shas_before == shas_after
    with open(os.path.join(os.path.dirname(BASE),
                           "reconcile_all.py"), "rb") as handle:
        runner = handle.read().decode("utf-8")
    ok = ok and "ledger-apimarket-listingposition" in runner
    with open(os.path.abspath(__file__), "rb") as handle:
        raw = handle.read()
    ok = ok and all(byte < 128 for byte in raw)
    record("AC-AMPOS8", ok,
           "three instances agree byte for byte on three buckets "
           "(sha256 %s); product files unchanged; runner label "
           "registered; suite source pure ASCII"
           % hashlib.sha256("".join(snap1).encode("utf-8")
                            ).hexdigest()[:16])

    passed = sum(1 for _ac, good in RESULTS if good)
    print("SUITE PASS %d/%d" % (passed, len(RESULTS)), flush=True)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())