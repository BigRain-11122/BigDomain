"""Acceptance suite for the apimarket nearest-neighbour discovery
face (BigDomain R2148; canon = the explore-queue row seeded and
claimed in R2148, criteria AC-AMSI1..AC-AMSI8 registered in that
claim note BEFORE this code existed - honesty law; the AC-AMSI
prefix, api_similar_listings, apimarket_similar, the suite name, the
ledger-apimarket-similar runner label and abs_price_delta were all
git-grep zero-occupancy anchored against HEAD 2026-10-27, rc=1).

Face under proof: APIMarketFace.api_similar_listings. Every other
discovery door makes the caller state the criteria first
(api_search wants a keyword/seller/price band/category,
api_categories describes a bucket, api_category_demand asks whether
it sells, api_listing_position ranks one listing inside its own
bucket). Nothing answered the buyer's follow-up after opening one
listing: "what else is like this one". This window pins it:

  - the contract (12-key envelope, 13-key rows, the total order by
    price distance then price then listing_id, the head never in
    its own rows, an honest empty neighbour set);
  - the bucket law (the EFFECTIVE category through one seam, the
    uncategorized bucket recruiting only uncategorized listings,
    zero cross-bucket permeation, the api_categories conservation
    identity);
  - the distance seam (a repricing on a candidate or on the head
    moving every delta in one step while the base listing row is
    never rewritten, net sales through the scarcity seam, ratings
    through the effective-star seam);
  - the visibility switch (retired candidates excluded by default,
    kept with their stamp on request, a retired head still
    readable);
  - the limit law (the closest head kept while total reports the
    whole candidate set, clamping at/beyond total, five bad forms);
  - the gate family and gate ORDER (six bad listing forms, the
    unknown listing, five bad limit forms, four bad include_delisted
    forms, listing-before-limit and listing-before-flag), all
    fail-closed with frozen table digests and a constant ledger
    transaction set;
  - the pure-read law plus same-call byte identity;
  - cross-restart byte identity on three instances, the product
    files' sha unchanged and the runner registration.

Usage: python test_apimarket_similar.py
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
    "listing_id", "category", "live", "delisted_utc", "current_price",
    "include_delisted", "limit", "total", "returned", "truncated",
    "rows", "disclaimer"}

ROW_KEYS = {
    "listing_id", "dev_account", "listing_key", "title",
    "current_price", "price_delta", "abs_price_delta",
    "rating_count", "rating_avg", "net_sales", "live",
    "delisted_utc"}


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


def row_ids(env):
    return [row["listing_id"] for row in env["rows"]]


def expect_code(fn):
    """Run fn and return the error code it raised ('' when it did
    not raise at all)."""
    try:
        fn()
    except A.ApiMarketError as exc:
        return str(exc.code)
    return ""


def bucket_count(am, name):
    for row in am.api_categories()["categories"]:
        if row["category"] == name:
            return row["listing_count"]
    return 0


def seed_world(led, dk, am):
    """One deterministic world.

    Category 'data': l1 dana price 10, l2 dana price 3, l3 frank
    price 5. Category 'tools': l4 dana price 4 alone. Uncategorized:
    l5 frank price 5, l6 dana price 7.

    Purchases: bob l2, carol l2, bob l3, dave l3.
    Ratings: bob l2 five, carol l2 one (avg 3.0), bob l3 four,
    dave l3 five (avg 4.5).
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AMSI-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AMSI-S",
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
    l4 = am.publish_api("usr:dana", "tools-a", "Tools A API",
                        "tool listing alone in its category",
                        PAYLOAD, 4, False,
                        category="tools")["listing_id"]
    l5 = am.publish_api("usr:frank", "docs-kit", "Docs Kit API",
                        "document pipeline kit", PAYLOAD, 5,
                        False)["listing_id"]
    l6 = am.publish_api("usr:dana", "chart-raw", "Raw Chart API",
                        "uncategorized chart payloads", PAYLOAD, 7,
                        False)["listing_id"]
    bob_l2 = am.purchase_api("usr:bob", l2, "ref-bob-l2")["purchase_id"]
    am.purchase_api("usr:carol", l2, "ref-carol-l2")
    am.purchase_api("usr:bob", l3, "ref-bob-l3")
    am.purchase_api("usr:dave", l3, "ref-dave-l3")
    bob_l2_rate = am.rate_api("usr:bob", l2, 5)["rating_id"]
    am.rate_api("usr:carol", l2, 1)
    am.rate_api("usr:bob", l3, 4)
    am.rate_api("usr:dave", l3, 5)
    return {"data": (l1, l2, l3), "tools": l4, "none": (l5, l6),
            "bob_l2": bob_l2, "bob_l2_rate": bob_l2_rate}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-similar-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    world = seed_world(led, dk, am)
    l1, l2, l3 = world["data"]
    l4 = world["tools"]
    l5, l6 = world["none"]

    # -- AC-AMSI1: contract, total order, derived deltas, empty set ----
    env = am.api_similar_listings(l3)
    ok = set(env) == ENVELOPE_KEYS
    ok = ok and all(set(row) == ROW_KEYS for row in env["rows"])
    ok = ok and env["listing_id"] == l3 and env["category"] == "data"
    ok = ok and env["live"] is True and env["delisted_utc"] is None
    ok = ok and env["current_price"] == 5
    ok = ok and env["include_delisted"] is False
    ok = ok and env["limit"] is None
    ok = ok and env["total"] == 2 and env["returned"] == 2
    ok = ok and env["truncated"] is False
    ok = ok and row_ids(env) == [l2, l1]
    ok = ok and l3 not in row_ids(env)
    near, far = env["rows"][0], env["rows"][1]
    ok = ok and near["listing_id"] == l2
    ok = ok and near["price_delta"] == -2 and near["abs_price_delta"] == 2
    ok = ok and near["net_sales"] == 2 and near["rating_count"] == 2
    ok = ok and near["rating_avg"] == 3.0 and near["live"] is True
    ok = ok and far["listing_id"] == l1
    ok = ok and far["price_delta"] == 5 and far["abs_price_delta"] == 5
    ok = ok and far["net_sales"] == 0 and far["rating_count"] == 0
    ok = ok and far["rating_avg"] == 0.0
    ok = ok and all(row["abs_price_delta"] == abs(row["price_delta"])
                    for row in env["rows"])
    none_env = am.api_similar_listings(l5)
    ok = ok and none_env["category"] is None
    ok = ok and row_ids(none_env) == [l6]
    ok = ok and none_env["rows"][0]["price_delta"] == 2
    tools_env = am.api_similar_listings(l4)
    ok = ok and tools_env["category"] == "tools"
    ok = ok and tools_env["total"] == 0 and tools_env["rows"] == []
    ok = ok and tools_env["returned"] == 0
    ok = ok and tools_env["truncated"] is False
    am.edit_listing("usr:dana", l1, title="Risk Scan v2")
    retitled = am.api_similar_listings(l3)
    base_title = am.api_view(l1)["base_title"]
    ok = ok and retitled["rows"][1]["title"] == "Risk Scan v2"
    ok = ok and base_title == "Risk Scan API"
    record("AC-AMSI1", ok,
           "envelope=%d keys rows=%d keys; head l3 neighbours %s with "
           "deltas %s; uncategorized head recruits %s only; tools "
           "singleton honest empty; effective title carried while the "
           "base row keeps its own"
           % (len(env), len(ROW_KEYS), row_ids(env),
              [r["price_delta"] for r in env["rows"]],
              row_ids(none_env)))

    # -- AC-AMSI2: effective bucket law, no cross-bucket permeation ----
    wide = am.api_similar_listings(l3, include_delisted=True)
    ok = len(wide["rows"]) + 1 == bucket_count(am, "data")
    ok = ok and bucket_count(am, "data") == 3
    am.revise_category("usr:dana", l1, "tools")
    moved = am.api_similar_listings(l3)
    ok = ok and row_ids(moved) == [l2] and moved["total"] == 1
    ok = ok and bucket_count(am, "data") == 2
    ok = ok and bucket_count(am, "tools") == 2
    into_tools = am.api_similar_listings(l4)
    ok = ok and row_ids(into_tools) == [l1]
    ok = ok and into_tools["rows"][0]["price_delta"] == 6
    back = am.api_similar_listings(l1)
    ok = ok and l4 in row_ids(back)
    am.revise_category("usr:dana", l1, "data")
    restored = am.api_similar_listings(l3)
    ok = ok and row_ids(restored) == [l2, l1] and restored["total"] == 2
    ok = ok and bucket_count(am, "data") == 3
    uncat_wide = am.api_similar_listings(l5, include_delisted=True)
    ok = ok and row_ids(uncat_wide) == [l6]
    ok = ok and uncat_wide["category"] is None
    record("AC-AMSI2", ok,
           "include_delisted=True gives %d neighbours + 1 head == the "
           "data bucket's %d listings; a category revision moves l1 out "
           "of l3's neighbours and into l4's in one step and back; the "
           "uncategorized head never recruits a bucketed listing"
           % (len(wide["rows"]), bucket_count(am, "data")))

    # -- AC-AMSI3: distance seam, base rows untouched, sales/ratings ----
    am.revise_price("usr:dana", l2, 4)
    repriced = am.api_similar_listings(l3)
    ok = repriced["rows"][0]["listing_id"] == l2
    ok = ok and repriced["rows"][0]["abs_price_delta"] == 1
    ok = ok and repriced["rows"][0]["price_delta"] == -1
    am.revise_price("usr:frank", l3, 6)
    head_moved = am.api_similar_listings(l3)
    ok = ok and head_moved["current_price"] == 6
    ok = ok and [r["abs_price_delta"] for r in head_moved["rows"]] \
        == [2, 4]
    ok = ok and [r["price_delta"] for r in head_moved["rows"]] \
        == [-2, 4]
    ok = ok and am.api_view(l2)["base_token_price"] == 3
    ok = ok and am.api_view(l3)["base_token_price"] == 5
    am.refund_api("usr:bob", world["bob_l2"], "service never delivered")
    refunded = am.api_similar_listings(l3)
    ok = ok and refunded["rows"][0]["net_sales"] == 1
    am.revise_rating("usr:bob", world["bob_l2_rate"], 1)
    revised = am.api_similar_listings(l3)
    ok = ok and revised["rows"][0]["rating_avg"] == 1.0
    ok = ok and revised["rows"][0]["rating_count"] == 2
    am.revise_price("usr:frank", l3, 5)
    am.revise_price("usr:dana", l2, 3)
    reset = am.api_similar_listings(l3)
    ok = ok and reset["current_price"] == 5
    ok = ok and [r["abs_price_delta"] for r in reset["rows"]] == [2, 5]
    record("AC-AMSI3", ok,
           "a candidate repricing halves its distance to 1 and a "
           "repricing of the head moves every delta (deltas %s, "
           "absolutes %s); both base prices still 3 and 5; a refund "
           "lowers net sales to 1 and a rating revision moves the "
           "effective average to 1.0 with the rating count intact"
           % ([r["price_delta"] for r in head_moved["rows"]],
              [r["abs_price_delta"] for r in head_moved["rows"]]))

    # -- AC-AMSI4: retirement switch and a retired head ----------------
    am.delist_api("usr:dana", l2)
    narrow = am.api_similar_listings(l3)
    ok = narrow["total"] == 1 and row_ids(narrow) == [l1]
    kept = am.api_similar_listings(l3, include_delisted=True)
    ok = ok and kept["total"] == 2 and row_ids(kept) == [l2, l1]
    ok = ok and kept["rows"][0]["live"] is False
    ok = ok and kept["rows"][0]["delisted_utc"] is not None
    am.delist_api("usr:dana", l1)
    retired_head = am.api_similar_listings(l1)
    ok = ok and retired_head["live"] is False
    ok = ok and retired_head["delisted_utc"] is not None
    ok = ok and retired_head["total"] == 1
    ok = ok and row_ids(retired_head) == [l3]
    history = am.api_similar_listings(l1, include_delisted=True)
    ok = ok and history["total"] == 2
    ok = ok and l2 in row_ids(history) and l3 in row_ids(history)
    am.relist_api("usr:dana", l2)
    am.relist_api("usr:dana", l1)
    live_again = am.api_similar_listings(l3)
    ok = ok and live_again["total"] == 2
    ok = ok and row_ids(live_again) == [l2, l1]
    ok = ok and all(row["live"] is True for row in live_again["rows"])
    record("AC-AMSI4", ok,
           "a retired candidate leaves the default set and returns with "
           "its stamp on request; a retired head still reads (live "
           "False, the live neighbour alone by default, both with the "
           "flag); two re-listings restore the default pair %s"
           % row_ids(live_again))

    # -- AC-AMSI5: limit law and clamping ------------------------------
    ok = am.api_similar_listings(l3, limit=1)["returned"] == 1
    one = am.api_similar_listings(l3, limit=1)
    ok = ok and row_ids(one) == [l2]
    ok = ok and one["total"] == 2 and one["truncated"] is True
    ok = ok and one["limit"] == 1
    even = am.api_similar_listings(l3, limit=2)
    ok = ok and even["returned"] == 2 and even["truncated"] is False
    over = am.api_similar_listings(l3, limit=99)
    ok = ok and over["returned"] == 2 and over["total"] == 2
    ok = ok and over["truncated"] is False
    bad_limits = [expect_code(
        lambda v=v: am.api_similar_listings(l3, limit=v))
        for v in (0, -2, "2", True, 2.0)]
    ok = ok and all(code == "E_AM_BAD_ARGS" for code in bad_limits)
    record("AC-AMSI5", ok,
           "limit=1 keeps the closest neighbour %s while total stays 2; "
           "limit at total and beyond total both report not-truncated; "
           "five bad limits %s"
           % (row_ids(one), bad_limits))

    # -- AC-AMSI6: gate family, gate order, frozen side effects --------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_ids = [expect_code(lambda v=v: am.api_similar_listings(v))
               for v in (0, -3, "1", True, 1.5, None)]
    ok = all(code == "E_AM_BAD_ARGS" for code in bad_ids)
    ok = ok and expect_code(
        lambda: am.api_similar_listings(999999)) == \
        "E_AM_UNKNOWN_LISTING"
    ok = ok and expect_code(
        lambda: am.api_similar_listings(999999, limit=0)) == \
        "E_AM_UNKNOWN_LISTING"
    ok = ok and expect_code(
        lambda: am.api_similar_listings(999999,
                                        include_delisted="yes")) == \
        "E_AM_UNKNOWN_LISTING"
    ok = ok and expect_code(
        lambda: am.api_similar_listings(l3, limit=0)) == \
        "E_AM_BAD_ARGS"
    bad_flags = [expect_code(
        lambda v=v: am.api_similar_listings(l3, include_delisted=v))
        for v in ("yes", 1, 0, None)]
    ok = ok and all(code == "E_AM_BAD_ARGS" for code in bad_flags)
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok = ok and digests_before == digests_after
    ok = ok and tx_before == tx_after
    record("AC-AMSI6", ok,
           "six bad ids %s; unknown listing; unknown-plus-bad-limit and "
           "unknown-plus-bad-flag both answer UNKNOWN_LISTING (the "
           "listing gate runs first); four bad include_delisted forms "
           "%s; %d table digests and %d ledger transactions frozen"
           % (bad_ids, bad_flags, len(digests_after), len(tx_after)))

    # -- AC-AMSI7: pure read and same-call determinism -----------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_similar_listings(l2))
    second = dumps(am.api_similar_listings(l2))
    ok = first == second
    for target in (l1, l2, l3, l4, l5, l6):
        am.api_similar_listings(target)
        am.api_similar_listings(target, 1, True)
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok = ok and digests_before == digests_after
    ok = ok and tx_before == tx_after
    with open(os.path.join(BASE, "apimarket.py"), "rb") as handle:
        src = handle.read().decode("utf-8")
    body = src.split("def api_similar_listings")[1]
    body = body.split("\n    def ")[0]
    ok = ok and "INSERT INTO" not in body
    ok = ok and "UPDATE " not in body and "DELETE FROM" not in body
    record("AC-AMSI7", ok,
           "twelve calls across six heads leave %d table digests and %d "
           "ledger transactions unchanged; the face body carries no "
           "INSERT/UPDATE/DELETE; the same call twice is byte-identical"
           % (len(digests_after), len(tx_after)))

    # -- AC-AMSI8: cross-restart identity, hygiene, wiring -------------
    snap1 = [dumps(am.api_similar_listings(t)) for t in (l1, l5, l6)]
    ok = ok and am.api_similar_listings(l3)["disclaimer"] == DISCLAIMER
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    snap2 = [dumps(am2.api_similar_listings(t)) for t in (l1, l5, l6)]
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    snap3 = [dumps(am3.api_similar_listings(t)) for t in (l1, l5, l6)]
    close_stack(am3, dk3, metered3, led3)
    ok = snap1 == snap2 and snap2 == snap3
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok = ok and shas_before == shas_after
    with open(os.path.join(os.path.dirname(BASE),
                           "reconcile_all.py"), "rb") as handle:
        runner = handle.read().decode("utf-8")
    ok = ok and "ledger-apimarket-similar" in runner
    with open(os.path.abspath(__file__), "rb") as handle:
        raw = handle.read()
    ok = ok and all(byte < 128 for byte in raw)
    record("AC-AMSI8", ok,
           "three instances agree byte for byte on three heads (sha256 "
           "%s); the resident disclaimer is carried; product files "
           "unchanged; runner label registered; suite source pure ASCII"
           % hashlib.sha256("".join(snap1).encode("utf-8")
                            ).hexdigest()[:16])

    passed = sum(1 for _ac, good in RESULTS if good)
    print("SUITE PASS %d/%d" % (passed, len(RESULTS)), flush=True)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())