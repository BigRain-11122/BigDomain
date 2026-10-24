"""Acceptance suite for the apimarket discovery PAGING axis
(BigDomain R2084; canon = the explore-queue row seeded and claimed
in R2084, criteria AC-AMPG1..AC-AMPG8 registered in that claim
note BEFORE this code existed - honesty law; the AC-AMPG prefix,
this suite name, the ledger-apimarket-searchpaging runner label
and the limit/offset paging shape were all git-grep
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_search(..., limit=None,
offset=None). R2082 gave the market a discovery door that returned
the entire matching set - a growing market could not be read page
by page and the caller could not learn the total. This window pins
the paging axis:

  - the backward-compatibility law: with NEITHER paging parameter
    given the envelope and rows stay byte-identical to the R2082
    contract (four legacy keys, five legacy criteria keys);
  - page stitching conservation: consecutive pages concatenate to
    the unpaged row list exactly (same order, no duplicate, no
    drop), with every page carrying the honest pre-page total;
  - boundary tie-break: limit=1 walks reproduce the full order and
    adjacent pages never share a row, so equal prices never split
    ambiguously;
  - bounds: limit == total, limit > total, offset == total,
    offset > total and an offset near the tail all clamp honestly
    instead of raising;
  - gate family and order: bad limit/offset shapes are all
    E_AM_BAD_ARGS with zero side effects, the account gate and the
    price-band gate both precede the limit gate (distinguishable
    probes), and the honest note that flag/limit/offset share one
    code so their relative order is not claimed;
  - paging composes with the existing filters: total derives from
    the FILTERED set, not the whole market, and the criteria echo
    carries the normalized limit/offset;
  - the pure-read law (zero row mutations, zero token movement,
    repeat-call byte identity);
  - cross-restart byte identity across three instances plus the
    runner wiring.

Usage: python test_apimarket_searchpage.py
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

PAGED_ENVELOPE_KEYS = {"disclaimer", "criteria", "count", "returned",
                       "total", "limit", "offset", "truncated",
                       "listings"}

LEGACY_CRITERIA_KEYS = {"keyword", "dev_account", "min_price",
                        "max_price", "include_delisted"}

PAGED_CRITERIA_KEYS = LEGACY_CRITERIA_KEYS | {"limit", "offset"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions")

BAD_LIMITS = ["2", True, 0, -1, 1.5]
BAD_OFFSETS = ["0", True, -1, 0.5]


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


def page_family(am):
    return {"legacy": dumps(am.api_search()),
            "p0": dumps(am.api_search(limit=2)),
            "p1": dumps(am.api_search(limit=2, offset=2,
                                      include_delisted=True)),
            "edge": dumps(am.api_search(offset=4,
                                        include_delisted=True)),
            "filtered": dumps(am.api_search(keyword="scan", limit=1))}


def seed_world(led, dk, am):
    """Two sellers, five listings, one retired -- the same shape the
    R2082 discovery suite pins, so the paging axis is proved on an
    already-established world: dana publishes risk-scan at 30 (then
    revises to 10), macro-feed at 3 (AIGC) and alpha-tool at 12;
    erin publishes scan-probe at 6 and roll-ups at 3 (the same-price
    tie with macro-feed); risk-scan is bought and rated; scan-probe
    is then retired, so the default market is four rows and the
    include_delisted market is five."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMPG-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMPG-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
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
    am.revise_price("usr:dana", d1, 10)
    am.purchase_api("usr:bob", d1, "ref-bob-amgp")
    am.rate_api("usr:bob", d1, 5)
    am.delist_api("usr:erin", e1)
    return d1, d2, e1, e2, d3


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-searchpage-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, e1, e2, d3 = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)

    # -- AC-AMPG1 backward-compatibility law -----------------------------
    env = am.api_search()
    none_pair = am.api_search(limit=None, offset=None)
    ok1 = (set(env.keys()) == LEGACY_ENVELOPE_KEYS
           and set(env["criteria"].keys()) == LEGACY_CRITERIA_KEYS
           and env["count"] == len(env["listings"]) == 4
           and dumps(env) == dumps(none_pair)
           and ids(env) == [d2, e2, d1, d3])
    record("AC-AMPG1", ok1,
           "legacy keys=%r criteria keys=%r count=%d"
           " none-pair identical=%r ids=%r"
           % (set(env.keys()) == LEGACY_ENVELOPE_KEYS,
              set(env["criteria"].keys()) == LEGACY_CRITERIA_KEYS,
              env["count"], dumps(env) == dumps(none_pair),
              ids(env)))

    # -- AC-AMPG2 page stitching conservation ----------------------------
    full5 = am.api_search(include_delisted=True)
    p0 = am.api_search(limit=2, include_delisted=True)
    p1 = am.api_search(limit=2, offset=2, include_delisted=True)
    p2 = am.api_search(limit=2, offset=4, include_delisted=True)
    stitched = ids(p0) + ids(p1) + ids(p2)
    ok2 = (stitched == ids(full5)
           and [len(ids(x)) for x in (p0, p1, p2)] == [2, 2, 1]
           and [x["total"] for x in (p0, p1, p2)] == [5, 5, 5]
           and [x["truncated"] for x in (p0, p1, p2)]
           == [True, True, False]
           and [x["count"] for x in (p0, p1, p2)] == [2, 2, 1]
           and [x["returned"] for x in (p0, p1, p2)] == [2, 2, 1]
           and set(p0.keys()) == PAGED_ENVELOPE_KEYS
           and set(p0["criteria"].keys()) == PAGED_CRITERIA_KEYS)
    record("AC-AMPG2", ok2,
           "stitched=%r unpaged=%r sizes=%r totals=%r"
           " truncated=%r paged keys=%r"
           % (stitched, ids(full5),
              [len(ids(x)) for x in (p0, p1, p2)],
              [x["total"] for x in (p0, p1, p2)],
              [x["truncated"] for x in (p0, p1, p2)],
              set(p0.keys()) == PAGED_ENVELOPE_KEYS))

    # -- AC-AMPG3 boundary tie-break -------------------------------------
    walk = [am.api_search(limit=1, offset=i, include_delisted=True)
            for i in range(5)]
    walk_ids = [ids(x)[0] for x in walk]
    disjoint = True
    for left, right in zip(walk, walk[1:]):
        if set(ids(left)) & set(ids(right)):
            disjoint = False
    ties = am.api_search(include_delisted=True)["listings"]
    tie_pair = [(r["listing_id"], r["token_price"]) for r in ties[:2]]
    ok3 = (walk_ids == ids(full5) == [d2, e2, e1, d1, d3]
           and disjoint
           and tie_pair == [(d2, 3), (e2, 3)])
    record("AC-AMPG3", ok3,
           "walk=%r unpaged=%r adjacent disjoint=%r tie pair=%r"
           % (walk_ids, ids(full5), disjoint, tie_pair))

    # -- AC-AMPG4 bounds clamp -------------------------------------------
    exact = am.api_search(limit=4)
    over = am.api_search(limit=99)
    at_end = am.api_search(offset=4)
    past_end = am.api_search(offset=9)
    tail = am.api_search(offset=3, limit=5)
    cross = am.api_search(offset=2, limit=1)
    ok4 = (exact["count"] == 4 and exact["truncated"] is False
           and over["count"] == 4 and over["truncated"] is False
           and at_end["listings"] == [] and at_end["count"] == 0
           and at_end["total"] == 4 and at_end["truncated"] is False
           and past_end["listings"] == [] and past_end["count"] == 0
           and past_end["total"] == 4
           and past_end["truncated"] is False
           and tail["count"] == 1 and tail["truncated"] is False
           and cross["count"] == 1 and cross["truncated"] is True)
    record("AC-AMPG4", ok4,
           "limit==total=%r limit>total=%r offset==total=%r"
           " offset>total=%r tail=%r crossing truncated=%r"
           % ((exact["count"], exact["truncated"]),
              (over["count"], over["truncated"]),
              (at_end["count"], at_end["listings"],
               at_end["truncated"]),
              (past_end["count"], past_end["total"]),
              (tail["count"], tail["truncated"]),
              cross["truncated"]))

    # -- AC-AMPG5 gate family and order ----------------------------------
    bad_limit_hits = [raises_code(lambda f=f: am.api_search(limit=f),
                                  A.E_AM_BAD_ARGS)
                      for f in BAD_LIMITS]
    bad_offset_hits = [raises_code(
        lambda f=f: am.api_search(offset=f), A.E_AM_BAD_ARGS)
        for f in BAD_OFFSETS]
    account_first = raises_code(
        lambda: am.api_search(dev_account="bob", limit=0),
        A.E_AM_BAD_ACCOUNT)
    band_first = raises_code(
        lambda: am.api_search(min_price=20, max_price=10, limit=0),
        A.E_AM_BAD_PRICE)
    flag_shared = raises_code(
        lambda: am.api_search(include_delisted="yes", limit=0),
        A.E_AM_BAD_ARGS)
    digests_after_gates = market_digests(am)
    ok5 = (all(bad_limit_hits) and all(bad_offset_hits)
           and account_first and band_first and flag_shared
           and digests_after_gates == digests_before)
    record("AC-AMPG5", ok5,
           "bad limits=%r bad offsets=%r account gate first=%r"
           " price band first=%r shared-code flag/limit=%r"
           " digests frozen=%r"
           % (bad_limit_hits, bad_offset_hits, account_first,
              band_first, flag_shared,
              digests_after_gates == digests_before))

    # -- AC-AMPG6 filters compose ----------------------------------------
    default_first = am.api_search(limit=1)
    retired_first = am.api_search(limit=1, include_delisted=True)
    kw_default = am.api_search(keyword="scan", limit=2)
    kw_retired = am.api_search(keyword="scan", limit=2,
                               include_delisted=True)
    erin_default = am.api_search(dev_account="usr:erin", limit=5)
    band = am.api_search(min_price=5, max_price=11, limit=5)
    echo = am.api_search(limit=2, offset=1)["criteria"]
    ok6 = (default_first["total"] == 4
           and retired_first["total"] == 5
           and kw_default["total"] == 1 and ids(kw_default) == [d1]
           and kw_retired["total"] == 2
           and ids(kw_retired) == [e1, d1]
           and erin_default["total"] == 1 and ids(erin_default) == [e2]
           and band["total"] == 1 and ids(band) == [d1]
           and echo == {"keyword": None, "dev_account": None,
                        "min_price": None, "max_price": None,
                        "include_delisted": False,
                        "limit": 2, "offset": 1})
    record("AC-AMPG6", ok6,
           "default total=%d retired total=%d keyword totals=%r"
           " keyword ids=%r erin total=%d band ids=%r echo=%r"
           % (default_first["total"], retired_first["total"],
              (kw_default["total"], kw_retired["total"]),
              (ids(kw_default), ids(kw_retired)),
              erin_default["total"], ids(band), echo))

    # -- AC-AMPG7 pure read and zero token movement ----------------------
    fam_a = page_family(am)
    fam_b = page_family(am)
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (fam_a == fam_b and digests_after == digests_before
           and tx_after == tx_before)
    record("AC-AMPG7", ok7,
           "repeat identical=%r digests frozen=%r tx constant=%r"
           " tx count=%d"
           % (fam_a == fam_b, digests_after == digests_before,
              tx_after == tx_before, len(tx_after)))

    # -- AC-AMPG8 cross-restart identity + wiring ------------------------
    family_one = page_family(am)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = page_family(am2)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = page_family(am3)
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-searchpaging" in handle.read()
    ok8 = (family_one == family_two == family_three and wired)
    record("AC-AMPG8", ok8,
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