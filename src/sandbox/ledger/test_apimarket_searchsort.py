"""Acceptance suite for the apimarket discovery SORT axis
(BigDomain R2098; canon = the explore-queue row seeded and claimed
in R2098, criteria AC-AMSR1..AC-AMSR8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMSR prefix, the
sort_by surface, this suite name, the ledger-apimarket-searchsort
runner label and the _SEARCH_SORT_MODES constant were all
git-grep zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_search(..., sort=None). R2082
gave the market a discovery door and R2084 gave it paging, but the
row order was frozen at current-price ascending: a resident who
wanted the flagship, the best rated, the best selling or the newest
had to take the whole set and re-sort locally, and a paged read
could not express "page N of THAT order". This window pins the
order axis:

  - the backward-compatibility law: with sort omitted the envelope,
    the criteria echo (no sort key) and the rows stay byte-
    identical to the pre-sort contract, and the price_asc alias
    reproduces the same row list;
  - five total orders with a listing_id ascending tie-break:
    price_desc, rating (avg desc, then count desc, then id), sales
    (NET sold - purchases minus refunds, floored at zero - then
    id), newest (listed_utc desc, then id), and the alias;
  - the order-only axis law: all six forms return the SAME matched
    id set (rows are never gained or lost by sorting) and total is
    sort-invariant;
  - the gate family and its position: bad sort shapes are all
    E_AM_BAD_ARGS with frozen digests, the account gate and the
    price-band gate both precede the sort gate (distinguishable
    probes), and a counting-connection proxy proves the sort gate
    runs with ZERO reads;
  - filters compose with every order (seller, price band,
    include_delisted) without changing the matched set;
  - paging composes with every order (limit=1 walks reproduce each
    mode, adjacent pages never overlap, bounds clamp honestly);
  - the pure-read law and the refund/rank correspondence: a refund
    lowers the net-sold rank in exactly the step it lowers
    api_supply.sold, while the rating rank and the row key set stay
    untouched;
  - cross-restart byte identity across three instances plus the
    runner wiring.

Fixture note (honest boundary): listed_utc is stamped at publish
time with one-second resolution, so six listings published inside
the same second would all tie and the newest axis could not be
observed. The suite therefore sets distinct listed_utc stamps -
including one deliberate tie - by direct UPDATE on its own temp
world. That is fixture seeding, not a product surface: no product
file is touched (the hygiene check proves their shas are stable).

Usage: python test_apimarket_searchsort.py
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

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

LEGACY_ENVELOPE_KEYS = {"disclaimer", "criteria", "count", "listings"}

LEGACY_CRITERIA_KEYS = {"keyword", "dev_account", "min_price",
                        "max_price", "include_delisted"}

ROW_KEYS = {"listing_id", "dev_account", "listing_key", "title",
            "token_price", "ai_label", "rating_count", "rating_avg",
            "delisted", "delisted_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_refunds",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_supply_revisions", "apimarket_relistings",
          "apimarket_listing_revisions",
          "apimarket_rating_replies",
          "apimarket_rating_revisions")

MODES = ("price_asc", "price_desc", "rating", "sales", "newest")

BAD_SORTS = [1, True, 1.5, [], {}, "", "   ", "PRICE_ASC", "price",
             "rarity"]


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


def ids(env):
    return [r["listing_id"] for r in env["listings"]]


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


def code_of(exc):
    return getattr(exc, "code", None)


def raises_code(fn, code):
    try:
        fn()
    except A.ApiMarketError as exc:
        return code_of(exc) == code
    return False


class CountingConn(object):
    """Read proxy for the gate-before-read proof: counts every
    execute() call while delegating to the real connection."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    def execute(self, *args, **kwargs):
        self.calls += 1
        return self.inner.execute(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.inner, name)


def order_family(am, include_delisted=False):
    """The six order forms (default plus five tokens), row ids only."""
    out = {"default": ids(am.api_search(
        include_delisted=include_delisted))}
    for mode in MODES:
        out[mode] = ids(am.api_search(sort=mode,
                                      include_delisted=include_delisted))
    return out


def stamp_world(am, stamps):
    conn = sqlite3.connect(am.db_path)
    for listing_id, stamp in stamps.items():
        conn.execute("UPDATE apimarket_listings SET listed_utc = ?"
                     " WHERE listing_id = ?", (stamp, listing_id))
    conn.commit()
    conn.close()


def seed_world(led, dk, am):
    """Two sellers, six listings (one retired), four buyers.

    dana: risk-scan 30 -> 10 (bob+carol bought, bob 5 / carol 3),
          macro-feed 3 (AIGC, unsold), alpha-tool 12 (dave bought,
          rated 5, THEN refunded), flagship 99 (bob bought, bob 4).
    erin: scan-probe 6 (retired), roll-ups 3 (three buyers bought).

    Net sold after the refund: roll-ups 3, risk-scan 2, flagship 1,
    macro-feed 0, alpha-tool 0. Ratings: alpha-tool 5.0/1,
    risk-scan 4.0/2, flagship 4.0/1, the rest 0.0/0.
    """
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMSR-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMSR-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 900),
                    ("usr:" + who, "credit", 900)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 30,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3,
                        True)["listing_id"]
    e1 = am.publish_api("usr:erin", "scan-probe", "Scan Probe API",
                        "probe endpoint for the scan pipeline",
                        PAYLOAD, 6, False)["listing_id"]
    e2 = am.publish_api("usr:erin", "roll-ups", "Roll Up Service",
                        "rolling aggregation service", PAYLOAD, 3,
                        False)["listing_id"]
    d3 = am.publish_api("usr:dana", "alpha-tool", "Service One",
                        "first service in the series", PAYLOAD, 12,
                        False)["listing_id"]
    d4 = am.publish_api("usr:dana", "flagship", "Flagship Suite",
                        "full portfolio suite", PAYLOAD, 99,
                        False)["listing_id"]
    am.revise_price("usr:dana", d1, 10)
    am.purchase_api("usr:bob", d1, "ref-bob-am1")
    am.purchase_api("usr:carol", d1, "ref-carol-am1")
    am.rate_api("usr:bob", d1, 5)
    am.rate_api("usr:carol", d1, 3)
    am.purchase_api("usr:bob", e2, "ref-bob-am2")
    am.purchase_api("usr:carol", e2, "ref-carol-am2")
    am.purchase_api("usr:dave", e2, "ref-dave-am2")
    p_d3 = am.purchase_api("usr:dave", d3, "ref-dave-am3")["purchase_id"]
    am.rate_api("usr:dave", d3, 5)
    am.purchase_api("usr:bob", d4, "ref-bob-am4")
    am.rate_api("usr:bob", d4, 4)
    am.delist_api("usr:erin", e1)
    return {"d1": d1, "d2": d2, "e1": e1, "e2": e2, "d3": d3,
            "d4": d4, "p_d3": p_d3}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-searchsort-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    w = seed_world(led, dk, am)
    d1, d2, d3, d4 = w["d1"], w["d2"], w["d3"], w["d4"]
    e1, e2 = w["e1"], w["e2"]

    # The newest axis needs distinct publication stamps (see the
    # fixture note in the module docstring). d2 and d4 deliberately
    # share a stamp to prove the listing_id tie-break.
    stamp_world(am, {d1: "2026-01-01T00:00:01Z",
                     d2: "2026-01-01T00:00:04Z",
                     e1: "2026-01-01T00:00:03Z",
                     e2: "2026-01-01T00:00:05Z",
                     d3: "2026-01-01T00:00:02Z",
                     d4: "2026-01-01T00:00:04Z"})

    # The refund leg: pre-refund sales rank, then the refund, so the
    # rank correspondence is measured inside one window.
    sales_pre = ids(am.api_search(sort="sales"))
    am.refund_api("usr:dave", w["p_d3"], "service unavailable")
    sales_post = ids(am.api_search(sort="sales"))

    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)

    # -- AC-AMSR1 backward-compatibility law -----------------------------
    env = am.api_search()
    alias = am.api_search(sort="price_asc")
    paged_none = am.api_search(limit=2)
    ok1 = (set(env.keys()) == LEGACY_ENVELOPE_KEYS
           and set(env["criteria"].keys()) == LEGACY_CRITERIA_KEYS
           and env["count"] == len(env["listings"]) == 5
           and dumps(env) == dumps(am.api_search(limit=None,
                                                 offset=None))
           and dumps(env) == dumps(am.api_search(sort=None))
           and env["listings"] == alias["listings"]
           and alias["criteria"]["sort"] == "price_asc"
           and set(paged_none["criteria"].keys())
           == LEGACY_CRITERIA_KEYS | {"limit", "offset"}
           and "sort" not in paged_none["criteria"])
    record("AC-AMSR1", ok1,
           "legacy keys=%r criteria keys=%r count=%d"
           " alias rows identical=%r alias criteria sort=%r"
           " paged-no-sort has sort key=%r"
           % (set(env.keys()) == LEGACY_ENVELOPE_KEYS,
              set(env["criteria"].keys()) == LEGACY_CRITERIA_KEYS,
              env["count"], env["listings"] == alias["listings"],
              alias["criteria"]["sort"],
              "sort" in paged_none["criteria"]))

    # -- AC-AMSR2 five total orders ---------------------------------------
    fam = order_family(am)
    ok2 = (fam["default"] == [d2, e2, d1, d3, d4]
           and fam["price_asc"] == fam["default"]
           and fam["price_desc"] == [d4, d3, d1, d2, e2]
           and fam["rating"] == [d3, d1, d4, d2, e2]
           and fam["sales"] == [e2, d1, d4, d2, d3]
           and fam["newest"] == [e2, d2, d4, d3, d1]
           and sales_pre == [e2, d1, d3, d4, d2])
    record("AC-AMSR2", ok2,
           "default=%r price_asc=%r price_desc=%r rating=%r"
           " sales=%r newest=%r sales pre-refund=%r"
           % (fam["default"], fam["price_asc"], fam["price_desc"],
              fam["rating"], fam["sales"], fam["newest"], sales_pre))

    # -- AC-AMSR3 total order and matched-set conservation -----------------
    walks = {}
    for mode in MODES:
        seq = [ids(am.api_search(limit=1, offset=i, sort=mode))[0]
               for i in range(5)]
        walks[mode] = seq
    overlap = []
    for mode in MODES:
        for i in range(4):
            left = set(ids(am.api_search(limit=1, offset=i, sort=mode)))
            right = set(ids(am.api_search(limit=1, offset=i + 1,
                                          sort=mode)))
            if left & right:
                overlap.append((mode, i))
    same_set = all(sorted(fam[m]) == sorted(fam["default"])
                   for m in MODES)
    totals = set(am.api_search(sort=m)["count"] for m in MODES)
    ok3 = (all(walks[m] == fam[m] for m in MODES)
           and not overlap
           and same_set
           and totals == {5}
           and dumps(am.api_search(sort="rating"))
           == dumps(am.api_search(sort="rating")))
    record("AC-AMSR3", ok3,
           "walks match orders=%r adjacent overlap=%r same id set=%r"
           " totals=%r repeat identical=True"
           % (all(walks[m] == fam[m] for m in MODES), overlap,
              same_set, sorted(totals)))

    # -- AC-AMSR4 gate family and position ---------------------------------
    bad_hits = [raises_code(lambda f=f: am.api_search(sort=f),
                            A.E_AM_BAD_ARGS)
                for f in BAD_SORTS]
    account_first = raises_code(
        lambda: am.api_search(dev_account="bob", sort=1),
        A.E_AM_BAD_ACCOUNT)
    band_first = raises_code(
        lambda: am.api_search(min_price=20, max_price=10, sort=1),
        A.E_AM_BAD_PRICE)
    whitespace_ok = am.api_search(sort=" newest ")["criteria"]["sort"]
    counting = CountingConn(am._conn)
    real_conn = am._conn
    am._conn = counting
    zero_read = raises_code(lambda: am.api_search(sort="rarity"),
                            A.E_AM_BAD_ARGS)
    reads = counting.calls
    am._conn = real_conn
    digests_after_gates = market_digests(am)
    ok4 = (all(bad_hits) and account_first and band_first
           and whitespace_ok == "newest"
           and zero_read and reads == 0
           and digests_after_gates == digests_before)
    record("AC-AMSR4", ok4,
           "bad sorts all rejected=%r account gate first=%r"
           " price band first=%r stripped token echo=%r"
           " zero-read gate=%r reads=%d digests frozen=%r"
           % (all(bad_hits), account_first, band_first,
              whitespace_ok, zero_read, reads,
              digests_after_gates == digests_before))

    # -- AC-AMSR5 filters compose with every order ------------------------
    dana = {m: ids(am.api_search(dev_account="usr:dana", sort=m))
            for m in (None,) + MODES}
    band = {m: ids(am.api_search(min_price=5, max_price=50, sort=m))
            for m in (None,) + MODES}
    retired = {m: ids(am.api_search(include_delisted=True, sort=m))
               for m in (None,) + MODES}
    ok5 = (all(sorted(v) == sorted(dana[None]) for v in dana.values())
           and dana[None] == [d2, d1, d3, d4]
           and all(sorted(v) == sorted(band[None]) for v in band.values())
           and sorted(band[None]) == sorted([d1, d3])
           and all(sorted(v) == sorted(retired[None])
                   for v in retired.values())
           and len(retired[None]) == 6 and e1 in retired[None]
           and am.api_search(dev_account="usr:dana",
                             sort="newest")["count"] == 4
           and am.api_search(include_delisted=True,
                             sort="sales")["count"] == 6)
    record("AC-AMSR5", ok5,
           "seller sets invariant=%r dana price order=%r"
           " band set=%r retired set=%r"
           % (all(sorted(v) == sorted(dana[None]) for v in dana.values()),
              dana[None], sorted(band[None]),
              sorted(retired[None])))

    # -- AC-AMSR6 paging composes with every order ------------------------
    stitched = {}
    for mode in MODES:
        pages = [ids(am.api_search(limit=2, offset=i, sort=mode))
                 for i in range(0, 5, 2)]
        stitched[mode] = pages[0] + pages[1] + pages[2]
    truncated = [am.api_search(limit=2, offset=i,
                               sort="price_desc")["truncated"]
                 for i in range(0, 5, 2)]
    exact = am.api_search(limit=5, sort="rating")
    over = am.api_search(limit=99, sort="rating")
    past = am.api_search(offset=9, sort="rating")
    echo = am.api_search(limit=2, offset=1, sort="sales")["criteria"]
    ok6 = (all(stitched[m] == fam[m] for m in MODES)
           and truncated == [True, True, False]
           and exact["count"] == 5 and exact["truncated"] is False
           and over["count"] == 5 and over["truncated"] is False
           and past["listings"] == [] and past["count"] == 0
           and past["total"] == 5 and past["truncated"] is False
           and echo["sort"] == "sales" and echo["limit"] == 2
           and echo["offset"] == 1)
    record("AC-AMSR6", ok6,
           "stitched matches every order=%r truncated flags=%r"
           " clamps=(%d,%r)/(%d,%r)/(%d,%d) echo=%r"
           % (all(stitched[m] == fam[m] for m in MODES), truncated,
              exact["count"], exact["truncated"], over["count"],
              over["truncated"], past["count"], past["total"], echo))

    # -- AC-AMSR7 pure read and refund/rank correspondence ----------------
    fam_a = {m: dumps(am.api_search(sort=m)) for m in MODES}
    fam_b = {m: dumps(am.api_search(sort=m)) for m in MODES}
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    row_keys = set(am.api_search(sort="sales")["listings"][0].keys())
    supply_row = am.api_supply(d3)
    ok7 = (fam_a == fam_b and digests_after == digests_before
           and tx_after == tx_before
           and row_keys == ROW_KEYS
           and supply_row["sold"] == 0
           and sales_pre != sales_post
           and sales_post == fam["sales"]
           and am.api_search(sort="rating")["listings"][0]["listing_id"]
           == d3)
    record("AC-AMSR7", ok7,
           "repeat identical=%r digests frozen=%r tx constant=%r"
           " row keys=%r supply sold after refund=%d"
           " sales rank moved by refund=%r rating rank kept=%r"
           % (fam_a == fam_b, digests_after == digests_before,
              tx_after == tx_before, row_keys == ROW_KEYS,
              supply_row["sold"], sales_pre != sales_post,
              am.api_search(sort="rating")["listings"][0]["listing_id"]
              == d3))

    # -- AC-AMSR8 cross-restart identity + wiring -------------------------
    family_one = {m: dumps(am.api_search(sort=m)) for m in MODES}
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = {m: dumps(am2.api_search(sort=m)) for m in MODES}
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = {m: dumps(am3.api_search(sort=m)) for m in MODES}
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-searchsort" in handle.read()
    ok8 = (family_one == family_two == family_three and wired)
    record("AC-AMSR8", ok8,
           "instance1==2==3 byte-identical=%r runner wiring=%r"
           % (family_one == family_two == family_three, wired))

    # -- hygiene ----------------------------------------------------------
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        blob = handle.read()
    ascii_ok = True
    try:
        blob.decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
    src = blob.decode("utf-8", "replace")
    net_imports = [line for line in src.splitlines()
                   if line.strip().startswith(("import requests",
                                               "import urllib",
                                               "import http"))]
    outside_repo = not os.path.abspath(tmp).startswith(
        os.path.abspath(os.path.join(BASE, "..", "..", "..")))
    hygiene = (shas_before == shas_after
               and ascii_ok
               and not net_imports
               and outside_repo)
    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("HYGIENE: consumer shas stable=%r suite ascii=%r"
          " network imports=%d world outside repo=%r"
          % (shas_before == shas_after, ascii_ok, len(net_imports),
             outside_repo))
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8 and hygiene) else 1


if __name__ == "__main__":
    sys.exit(main())