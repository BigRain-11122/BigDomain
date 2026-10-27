"""Acceptance suite for the apimarket retirement to re-listing gap
face (BigDomain R2180; canon = the R2178 explore seed claimed in R2180,
criteria AC-ARG1..AC-ARG8 pre-registered in that claim row BEFORE this
code existed - honesty law; the AC-ARG prefix, api_relist_gap,
test_apimarket_relistgap and ledger-apimarket-relistgap were all
git-grep zero-occupancy anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_relist_gap. The market answers the
raw lifecycle event stream, the shelf-to-sale duration and the live
set - none of them answers how long a shelf stayed off the market
before it came back. This suite pins:

  - the thirteen-key envelope and nine-key rows, honest empty first;
  - the pairing law (a delisting in cycle c pairs only with the
    re-listing opening cycle c+1) and the elapsed derivation from the
    two stored stamps alone;
  - the pending law (a running gap has no duration, never a zero, and
    never enters an aggregate) and the orphan skip;
  - the pooled average, the median (odd middle / even midpoint) and
    the fastest / slowest extremes with the listing_id then from_cycle
    tie-break;
  - the disclosed ordering (slowest responsiveness first, pending
    last) and the MARKET-scoped benchmark under a seller scope;
  - the one effective-category seam, the seven-form account gate, the
    bare usr: prefix reading honestly empty, the pure-read law and
    cross-restart byte identity.

Usage: python test_apimarket_relistgap.py
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
    "dev_account", "listing_count", "gap_count", "pending_count",
    "avg_seconds", "median_seconds", "fastest_seconds",
    "slowest_seconds", "fastest_listing_id", "slowest_listing_id",
    "market_avg_seconds", "rows", "disclaimer"}

ROW_KEYS = {
    "listing_id", "listing_key", "category", "from_cycle", "to_cycle",
    "delisted_utc", "relisted_utc", "gap_seconds", "pending"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")

D1_DELIST = "2026-05-10T00:00:00Z"
D1_RELIST = "2026-05-12T00:00:00Z"
D2_DELIST = "2026-06-01T00:00:00Z"
D2_RELIST = "2026-06-11T00:00:00Z"
F1_DELIST_1 = "2026-05-01T00:00:00Z"
F1_RELIST_1 = "2026-05-02T00:00:00Z"
F1_DELIST_2 = "2026-07-01T00:00:00Z"
F1_RELIST_2 = "2026-07-09T00:00:00Z"
F2_DELIST = "2026-08-01T00:00:00Z"
G2_DELIST = "2026-05-03T00:00:00Z"
G2_RELIST = "2026-05-04T00:00:00Z"

# Pooled over the five completed gaps: 172800, 864000, 86400,
# 691200, 86400 -> sum 1900800.
MARKET_AVG = 380160.0


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


def set_stamp(am, table, column, key_column, key, stamp):
    """Fixture setup only: every write door stamps the wall clock, and
    this face reads what the append-only tables store, so a
    deterministic duration grid needs fixed instants."""
    conn = sqlite3.connect(am.db_path)
    conn.execute("UPDATE " + table + " SET " + column + " = ?"
                 " WHERE " + key_column + " = ?", (stamp, key))
    conn.commit()
    conn.close()


def set_cycle_stamp(am, table, column, listing_id, cycle, stamp):
    """Fixture setup only, addressed by cycle: a listing with more
    than one row in the same table must not have every row stamped
    by the latest call."""
    conn = sqlite3.connect(am.db_path)
    conn.execute("UPDATE " + table + " SET " + column + " = ?"
                 " WHERE listing_id = ? AND cycle = ?",
                 (stamp, listing_id, cycle))
    conn.commit()
    conn.close()


def retire(am, owner, listing_id, delist_utc):
    am.delist_api(owner, listing_id)
    cycle = am.api_listing_lifecycle(listing_id)["cycle"]
    set_cycle_stamp(am, "apimarket_delistings", "delisted_utc",
                    listing_id, cycle, delist_utc)


def revoke(am, owner, listing_id, relist_utc):
    am.relist_api(owner, listing_id)
    cycle = am.api_listing_lifecycle(listing_id)["cycle"]
    set_cycle_stamp(am, "apimarket_relistings", "relisted_utc",
                    listing_id, cycle, relist_utc)


def row_of(env, listing_id, from_cycle=None):
    for row in env["rows"]:
        if row["listing_id"] == listing_id:
            if from_cycle is None or row["from_cycle"] == from_cycle:
                return row
    raise AssertionError("listing %r cycle %r missing from rows"
                         % (listing_id, from_cycle))


def seed_world(led, dk, am):
    """dana owns d1 (data, 2-day gap) and d2 (data, 10-day gap, the
    slowest). frank owns f1 (tools, two closed cycles: 1 day then 8
    days) and f2 (tools, retired and never returned -> one pending
    row). gina owns g1 (media, never retired -> no row at all) and g2
    (media, one 1-day gap tying the fastest band)."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-ARG-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-ARG-S",
                     "settlement")
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    dk.issue_key("usr:gina", "gina-key", 10, ["backtest"], False)

    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True,
                        category="data")["listing_id"]
    f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                        "deterministic chart payloads", PAYLOAD, 7,
                        False, category="tools")["listing_id"]
    f2 = am.publish_api("usr:frank", "grid-kit", "Grid Kit API",
                        "deterministic grid payloads", PAYLOAD, 4,
                        False, category="tools")["listing_id"]
    g1 = am.publish_api("usr:gina", "media-pack", "Media Pack API",
                        "media pipeline pack", PAYLOAD, 6, False,
                        category="media")["listing_id"]
    g2 = am.publish_api("usr:gina", "media-grid", "Media Grid API",
                        "media grid payloads", PAYLOAD, 8, False,
                        category="media")["listing_id"]

    retire(am, "usr:dana", d1, D1_DELIST)
    revoke(am, "usr:dana", d1, D1_RELIST)
    retire(am, "usr:dana", d2, D2_DELIST)
    revoke(am, "usr:dana", d2, D2_RELIST)

    retire(am, "usr:frank", f1, F1_DELIST_1)
    revoke(am, "usr:frank", f1, F1_RELIST_1)
    retire(am, "usr:frank", f1, F1_DELIST_2)
    revoke(am, "usr:frank", f1, F1_RELIST_2)
    retire(am, "usr:frank", f2, F2_DELIST)

    retire(am, "usr:gina", g2, G2_DELIST)
    revoke(am, "usr:gina", g2, G2_RELIST)
    return d1, d2, f1, f2, g1, g2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-relistgap-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, f1, f2, g1, g2 = seed_world(led, dk, am)

    # -- AC-ARG1 the contract, honest empty first ----------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-arg-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_relist_gap()
    empty_seller = e_am.api_relist_gap("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_relist_gap()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["rows"])
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["listing_count"] == 0 and empty["gap_count"] == 0
           and empty["pending_count"] == 0 and empty["rows"] == []
           and empty["avg_seconds"] is None
           and empty["median_seconds"] is None
           and empty["market_avg_seconds"] is None
           and empty_seller["rows"] == []
           and empty_seller["gap_count"] == 0)
    record("AC-ARG1", ok1,
           "keys=%r rows=%r empty=%d seller=%d"
           % (set(market.keys()) == ENVELOPE_KEYS, row_keys_ok,
              empty["listing_count"], empty_seller["listing_count"]))

    # -- AC-ARG2 the pairing law and the elapsed derivation ------------
    d1_row = row_of(market, d1)
    d2_row = row_of(market, d2)
    f1_first = row_of(market, f1, 1)
    f1_second = row_of(market, f1, 2)
    g2_row = row_of(market, g2)
    pairing_ok = (d1_row["gap_seconds"] == 172800
                  and d2_row["gap_seconds"] == 864000
                  and f1_first["gap_seconds"] == 86400
                  and f1_second["gap_seconds"] == 691200
                  and g2_row["gap_seconds"] == 86400
                  and d1_row["from_cycle"] == 1
                  and d1_row["to_cycle"] == 2
                  and d1_row["delisted_utc"] == D1_DELIST
                  and d1_row["relisted_utc"] == D1_RELIST
                  and d1_row["pending"] is False
                  and f1_second["from_cycle"] == 2
                  and f1_second["to_cycle"] == 3)
    # The pairing law is cycle-addressed, not stamp-addressed: shifting
    # every stored stamp of one closed pair by the same offset must
    # move the gap with it and nothing else.
    set_stamp(am, "apimarket_delistings", "delisted_utc",
              "listing_id", d1, "2026-05-09T00:00:00Z")
    shifted = row_of(am.api_relist_gap(), d1)
    other_shift_ok = (shifted["gap_seconds"] == 259200
                      and row_of(am.api_relist_gap(), d2)["gap_seconds"]
                      == 864000)
    set_stamp(am, "apimarket_delistings", "delisted_utc",
              "listing_id", d1, D1_DELIST)
    ok2 = pairing_ok and other_shift_ok
    record("AC-ARG2", ok2,
           "gaps=%r shift=%r"
           % ([d1_row["gap_seconds"], d2_row["gap_seconds"],
               f1_first["gap_seconds"], f1_second["gap_seconds"],
               g2_row["gap_seconds"]], other_shift_ok))

    # -- AC-ARG3 the running gap never becomes a duration --------------
    f2_row = row_of(market, f2)
    frank = am.api_relist_gap("usr:frank")
    gina = am.api_relist_gap("usr:gina")
    pending_ok = (f2_row["pending"] is True
                  and f2_row["gap_seconds"] is None
                  and f2_row["relisted_utc"] is None
                  and f2_row["to_cycle"] is None
                  and f2_row["from_cycle"] == 1
                  and market["pending_count"] == 1
                  and market["gap_count"] == 5
                  and frank["gap_count"] == 2
                  and frank["pending_count"] == 1
                  and frank["avg_seconds"] == 388800.0
                  and gina["listing_count"] == 1
                  and gina["gap_count"] == 1)
    # A never-retired shelf contributes no row at all.
    untouched = [row for row in market["rows"]
                 if row["listing_id"] == g1]
    # A second retirement turns the pending row into one more gap and
    # the ledger of the running one is not lost.
    revoke(am, "usr:frank", f2, "2026-08-05T00:00:00Z")
    resolved = am.api_relist_gap("usr:frank")
    f2_resolved = row_of(resolved, f2)
    resolve_ok = (untouched == []
                  and f2_resolved["pending"] is False
                  and f2_resolved["gap_seconds"] == 345600
                  and resolved["gap_count"] == 3
                  and resolved["pending_count"] == 0)
    ok3 = pending_ok and resolve_ok
    record("AC-ARG3", ok3,
           "pending=%r frank=%r gina=%r resolved=%r"
           % (pending_ok, frank["gap_count"], gina["gap_count"],
              resolve_ok))
    # Return the fixture to its pinned shape for the aggregate laws:
    # dropping the return row puts cycle 1 back in flight, so the
    # original pending row is what the market reads again.
    conn = sqlite3.connect(am.db_path)
    conn.execute("DELETE FROM apimarket_relistings WHERE listing_id = ?"
                 " AND cycle = 2", (f2,))
    conn.commit()
    conn.close()

    # -- AC-ARG4 the aggregates ----------------------------------------
    market = am.api_relist_gap()
    frank = am.api_relist_gap("usr:frank")
    ok4 = (market["avg_seconds"] == MARKET_AVG
           and market["median_seconds"] == 172800.0
           and market["fastest_seconds"] == 86400
           and market["slowest_seconds"] == 864000
           and market["slowest_listing_id"] == d2
           and market["fastest_listing_id"] == f1
           and frank["avg_seconds"] == 388800.0
           and frank["median_seconds"] == 388800.0
           and frank["fastest_seconds"] == 86400
           and frank["slowest_seconds"] == 691200
           and frank["slowest_listing_id"] == f1)
    # Even-count median is the midpoint: dana holds two gaps only.
    dana = am.api_relist_gap("usr:dana")
    ok4 = ok4 and (dana["gap_count"] == 2
                   and dana["median_seconds"] == 518400.0
                   and dana["avg_seconds"] == 518400.0)
    record("AC-ARG4", ok4,
           "avg=%r median=%r fastest=%r/%r slowest=%r/%r"
           % (market["avg_seconds"], market["median_seconds"],
              market["fastest_seconds"], market["fastest_listing_id"],
              market["slowest_seconds"], market["slowest_listing_id"]))

    # -- AC-ARG5 the disclosed ordering --------------------------------
    gaps = [row["gap_seconds"] for row in market["rows"]
            if not row["pending"]]
    tail = [row for row in market["rows"] if row["pending"]]
    order_ok = (gaps == sorted(gaps, reverse=True)
                and market["rows"][0]["gap_seconds"] == 864000
                and market["rows"][-1]["pending"] is True
                and tail == [market["rows"][-1]]
                and [row["listing_id"] for row in market["rows"]
                     if row["gap_seconds"] == 86400]
                == [f1, g2])
    record("AC-ARG5", order_ok,
           "gaps=%r pending_tail=%r" % (gaps, len(tail)))

    # -- AC-ARG6 scope, benchmark and the category seam ----------------
    pre = dumps(dana)
    ok6a = (dana["market_avg_seconds"] == market["avg_seconds"]
            == MARKET_AVG
            and dana["dev_account"] == "usr:dana"
            and all(row["listing_id"] in (d1, d2)
                    for row in dana["rows"])
            and all(row["listing_id"] not in (d1, d2)
                    for row in frank["rows"])
            and dana["listing_count"] == 2)
    am.revise_category("usr:dana", d1, category="media")
    moved = row_of(am.api_relist_gap("usr:dana"), d1)
    moved_ok = moved["category"] == "media"
    am.revise_category("usr:dana", d1, category="data")
    back = dumps(am.api_relist_gap("usr:dana"))
    ok6 = ok6a and moved_ok and back == pre
    record("AC-ARG6", ok6,
           "bench=%r moved=%r roundtrip=%r"
           % (ok6a, moved_ok, back == pre))

    # -- AC-ARG7 gates and the pure read -------------------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in ("", " ", "dana", 123, [], {"usr:x": 1}, 1.0):
        try:
            am.api_relist_gap(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_relist_gap("usr:")
    first = dumps(am.api_relist_gap("usr:frank"))
    second = dumps(am.api_relist_gap("usr:frank"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["listing_count"] == 0
           and prefix["gap_count"] == 0
           and prefix["pending_count"] == 0
           and prefix["rows"] == []
           and prefix["avg_seconds"] is None
           and first == second
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-ARG7", ok7,
           "acct=%r prefix=%r frozen=%r tx=%r"
           % (acct_codes, prefix["listing_count"],
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-ARG8 lifecycle history, restart identity and wiring --------
    before = row_of(am.api_relist_gap(), d1, 1)
    retire(am, "usr:dana", d1, "2026-09-01T00:00:00Z")
    revoke(am, "usr:dana", d1, "2026-09-02T00:00:00Z")
    after_env = am.api_relist_gap()
    after_first = row_of(after_env, d1, 1)
    after_second = row_of(after_env, d1, 2)
    life_ok = (dumps(before) == dumps(after_first)
               and after_second["gap_seconds"] == 86400
               and after_env["gap_count"] == 6)
    retire(am, "usr:dana", d1, "2026-10-01T00:00:00Z")
    retired_env = am.api_relist_gap("usr:dana")
    retired_ok = (dumps(row_of(retired_env, d1, 1)) == dumps(before)
                  and retired_env["pending_count"] == 1
                  and retired_env["gap_count"] == 3)

    final = dumps(am.api_relist_gap())
    final_dana = dumps(am.api_relist_gap("usr:dana"))
    final_gina = dumps(am.api_relist_gap("usr:gina"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_relist_gap())
    second_dana = dumps(am.api_relist_gap("usr:dana"))
    second_gina = dumps(am.api_relist_gap("usr:gina"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_relist_gap())
    third_dana = dumps(am.api_relist_gap("usr:dana"))
    third_gina = dumps(am.api_relist_gap("usr:gina"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_relist_gap()
        am.api_relist_gap("usr:dana")
        am.api_relist_gap("usr:gina")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (life_ok and retired_ok
           and final == second_market == third_market
           and final_dana == second_dana == third_dana
           and final_gina == second_gina == third_gina
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-relistgap" in runner_text)
    record("AC-ARG8", ok8,
           "life=%r retired=%r sha16=%s identical=%r tx_equal=%r"
           " digests_equal=%r files_equal=%r registered=%r"
           % (life_ok, retired_ok,
              hashlib.sha256(final.encode("utf-8")).hexdigest()[:16],
              final == second_market == third_market, tx_b == tx_a,
              dig_b == dig_a, shas_before == shas_after,
              "ledger-apimarket-relistgap" in runner_text))

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