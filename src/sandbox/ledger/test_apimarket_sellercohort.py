"""Acceptance suite for the apimarket monthly seller cohort face
(BigDomain R2181; criteria AC-MSC1..AC-MSC8 were registered in the
R2178 seed row of the explore queue BEFORE this code existed - honesty
law; the AC-MSC prefix, api_market_seller_cohort, this suite name and
the ledger-apimarket-sellercohort runner label were all git-grep
zero-occupancy anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_market_seller_cohort. The buyer
side already carries a cohort face and a retention matrix, but the
seller side only had a lifetime view and a running total, so "are the
sellers who first listed in January still listing in March" was
unreadable. This suite pins the new face:

  - the twelve-key envelope, the nine-key rows, honest empty first,
    and the no-argument contract (an argument is a TypeError, never a
    silent ignore);
  - the two-source event law (one event per listing row, one per
    re-listing row) and the re-listing subset invariant;
  - the cohort law (a seller is new exactly once, in the earliest
    month across the whole event history, including a re-listing whose
    stamp is EARLIER than the listing stamp - disclosed, never clamped)
    and the repeat-seller law;
  - conservation (per-row partitions, row sums against the envelope);
  - month keys, ascending order, no zero rows, first/last stability,
    retirement and sold-out not being events;
  - orthogonality against four adjacent faces;
  - the pure-read law with frozen table digests and a constant
    ledger_tx set;
  - cross-restart byte identity over three instances plus product-file
    and runner wiring.

Usage: python test_apimarket_sellercohort.py
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
    "month_count", "seller_count", "listing_event_count",
    "relisting_event_count", "relisting_seller_count",
    "repeat_seller_count", "repeat_rate", "returning_event_count",
    "first_month", "last_month", "disclaimer", "months"}

ROW_KEYS = {
    "month", "seller_count", "new_seller_count",
    "returning_seller_count", "listing_event_count",
    "relisting_event_count", "new_event_count",
    "returning_event_count", "avg_events_per_seller"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


class Clock(object):
    """Deterministic stamp holder: the suite sets one explicit UTC
    string before each write so the month buckets are reproducible
    (module clock patched, restored in main's finally block)."""

    def __init__(self):
        self.value = "2026-01-10T00:00:00Z"

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


def by_month(env):
    return {row["month"]: row for row in env["months"]}


def seed_world(led, dk, am, clock):
    """alice lists in JAN and again in FEB; bob arrives in FEB and lists
    again in MAR; carol arrives in MAR. alice then retires a1 and brings
    it back in APR, which is a re-listing event but not a new seller.
    Expected cohort origins: alice JAN, bob FEB, carol MAR."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-MSC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-MSC-S",
                     "settlement")
    for who in ("alice", "bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    dk.issue_key("usr:alice", "alice-key", 10, ["backtest"], False)
    dk.issue_key("usr:bob", "bob-key", 10, ["backtest"], False)
    dk.issue_key("usr:carol", "carol-key", 10, ["backtest"], False)

    clock.value = "2026-01-10T00:00:00Z"
    a1 = am.publish_api("usr:alice", "alpha-one", "Alpha One API",
                        "first alice listing", PAYLOAD, 7, False,
                        category="data")["listing_id"]
    clock.value = "2026-02-10T00:00:00Z"
    am.publish_api("usr:alice", "alpha-two", "Alpha Two API",
                   "second alice listing", PAYLOAD, 8, False,
                   category="data")
    b1 = am.publish_api("usr:bob", "beta-one", "Beta One API",
                        "first bob listing", PAYLOAD, 5, False,
                        category="data")["listing_id"]
    clock.value = "2026-03-10T00:00:00Z"
    am.publish_api("usr:bob", "beta-two", "Beta Two API",
                   "second bob listing", PAYLOAD, 6, True,
                   category="tooling")
    am.publish_api("usr:carol", "gamma-one", "Gamma One API",
                   "first carol listing", PAYLOAD, 9, False,
                   category="tooling")
    clock.value = "2026-04-10T00:00:00Z"
    am.delist_api("usr:alice", a1)
    am.relist_api("usr:alice", a1)
    return a1, b1


def run(db_path, cfg, lobby_cfg, shas_before, clock, orig_now):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    a1, _b1 = seed_world(led, dk, am, clock)

    # -- AC-MSC1 the contract, honest empty first, no arguments -------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-msc-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_seller_cohort()
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_market_seller_cohort()
    arg_forms = []
    for bad in ("", 1, None, [], {"x": 1}, False):
        try:
            am.api_market_seller_cohort(bad)
            arg_forms.append("NO-ERROR:%r" % (bad,))
        except TypeError:
            continue
        except Exception as exc:                      # noqa: BLE001
            arg_forms.append("WRONG:%r:%s" % (bad, type(exc).__name__))
    contract_ok = (
        set(market.keys()) == ENVELOPE_KEYS
        and set(empty.keys()) == ENVELOPE_KEYS
        and all(set(row.keys()) == ROW_KEYS
                for row in market["months"])
        and empty["month_count"] == 0 and empty["months"] == []
        and empty["seller_count"] == 0
        and empty["first_month"] is None
        and empty["last_month"] is None
        and empty["repeat_rate"] is None
        and empty["relisting_seller_count"] == 0
        and not arg_forms)
    record("AC-MSC1", contract_ok,
           "envelope=%d keys, rows=%d keys, empty=(0,'%s',None,None),"
           " arg_forms=%s"
           % (len(market), len(ROW_KEYS), empty["repeat_rate"],
              arg_forms or "all TypeError"))

    # -- AC-MSC2 the two-source event law -----------------------------
    listed_rows = am._conn.execute(
        "SELECT COUNT(*) FROM apimarket_listings").fetchone()[0]
    relist_rows = am._conn.execute(
        "SELECT COUNT(*) FROM apimarket_relistings").fetchone()[0]
    subset_ok = all(row["relisting_event_count"]
                    <= row["listing_event_count"]
                    for row in market["months"])
    ac2 = (market["listing_event_count"] == listed_rows + relist_rows
           and market["relisting_event_count"] == relist_rows
           and subset_ok
           and relist_rows == 1 and listed_rows == 5)
    record("AC-MSC2", ac2,
           "listed=%d relisted=%d envelope=(%d,%d) subset=%s"
           % (listed_rows, relist_rows,
              market["listing_event_count"],
              market["relisting_event_count"], subset_ok))

    # -- AC-MSC3 the cohort law, including the backdated re-listing ---
    months = by_month(market)
    expect = {
        "2026-01": (1, 1, 0, 1, 0),
        "2026-02": (2, 1, 1, 2, 0),
        "2026-03": (2, 1, 1, 2, 0),
        "2026-04": (1, 0, 1, 1, 1),
    }
    shape_ok = True
    for month, want in expect.items():
        row = months.get(month)
        got = (row["seller_count"], row["new_seller_count"],
               row["returning_seller_count"],
               row["listing_event_count"],
               row["relisting_event_count"]) if row else None
        if got != want:
            shape_ok = False
            break
    back_tmp = tempfile.mkdtemp(prefix="apimarket-msc-backdated-")
    b_led, b_metered, b_dk, _b_gate, b_am = build_stack(
        os.path.join(back_tmp, "ledger.db"), cfg, lobby_cfg)
    b_dk.issue_key("usr:zoe", "zoe-key", 10, ["backtest"], False)
    clock.value = "2026-03-05T00:00:00Z"
    z1 = b_am.publish_api("usr:zoe", "zeta-one", "Zeta One API",
                          "backdated relist probe", PAYLOAD, 4, False,
                          category="data")["listing_id"]
    clock.value = "2026-05-05T00:00:00Z"
    b_am.delist_api("usr:zoe", z1)
    clock.value = "2026-02-05T00:00:00Z"
    b_am.relist_api("usr:zoe", z1)
    back = b_am.api_market_seller_cohort()
    close_stack(b_am, b_dk, b_metered, b_led)
    back_feb = by_month(back).get("2026-02")
    back_mar = by_month(back).get("2026-03")
    backdated_ok = (back["first_month"] == "2026-02"
                    and back_feb is not None
                    and back_feb["new_seller_count"] == 1
                    and back_feb["relisting_event_count"] == 1
                    and back_mar["new_seller_count"] == 0
                    and back_mar["returning_seller_count"] == 1)
    ac3 = (shape_ok
           and market["seller_count"] == 3
           and market["repeat_seller_count"] == 2
           and abs(market["repeat_rate"] - (2.0 / 3.0)) < 1e-12
           and market["relisting_seller_count"] == 1
           and market["returning_event_count"] == 3
           and backdated_ok)
    record("AC-MSC3", ac3,
           "rows=%s seller_count=%d repeat=%d rate=%.6f relist_sellers=%d"
           " backdated=%s"
           % ([(m, months[m]["seller_count"],
               months[m]["new_seller_count"],
               months[m]["returning_seller_count"]) for m in sorted(months)],
              market["seller_count"], market["repeat_seller_count"],
              market["repeat_rate"], market["relisting_seller_count"],
              backdated_ok))

    # -- AC-MSC4 conservation ----------------------------------------
    conn = sqlite3.connect(am.db_path)
    per_seller = {}
    for dev, stamp in conn.execute(
            "SELECT dev_account, listed_utc FROM apimarket_listings"):
        per_seller[stamp[:7]] = per_seller.get(stamp[:7], 0) + 1
    for dev, stamp in conn.execute(
            "SELECT dev_account, relisted_utc FROM apimarket_relistings"):
        per_seller[stamp[:7]] = per_seller.get(stamp[:7], 0) + 1
    conn.close()
    parts_ok = all(
        row["listing_event_count"]
        == row["new_event_count"] + row["returning_event_count"]
        for row in market["months"])
    sums_ok = all(row["listing_event_count"] == per_seller.get(
        row["month"], 0) for row in market["months"])
    totals_ok = (
        market["listing_event_count"] == sum(
            row["listing_event_count"] for row in market["months"])
        and market["relisting_event_count"] == sum(
            row["relisting_event_count"] for row in market["months"])
        and market["returning_event_count"] == sum(
            row["returning_event_count"] for row in market["months"])
        and market["relisting_event_count"]
        <= market["listing_event_count"])
    record("AC-MSC4", parts_ok and sums_ok and totals_ok,
           "partitions=%s row_sums=%s envelope_totals=%s"
           % (parts_ok, sums_ok, totals_ok))

    # -- AC-MSC5 month keys, order, no zero rows, retirement ----------
    keys = [row["month"] for row in market["months"]]
    order_ok = keys == sorted(keys) and len(set(keys)) == len(keys)
    shape_keys_ok = all(len(k) == 7 and k[4] == "-" for k in keys)
    first_last_ok = (market["first_month"] == keys[0]
                     and market["last_month"] == keys[-1]
                     and market["month_count"] == len(keys))
    no_zero_rows = all(row["listing_event_count"] > 0
                       for row in market["months"])
    clock.value = "2026-06-01T00:00:00Z"
    am.delist_api("usr:bob", _b1)
    after_retire = am.api_market_seller_cohort()
    retire_ok = dumps(after_retire) == dumps(market)
    record("AC-MSC5", order_ok and shape_keys_ok and first_last_ok
           and no_zero_rows and retire_ok,
           "keys=%s order=%s first_last=%s no_zero=%s retirement_noop=%s"
           % (keys, order_ok, first_last_ok, no_zero_rows, retire_ok))

    # -- AC-MSC6 orthogonality against four adjacent faces ------------
    before_faces = {
        "buyer_cohort": dumps(am.api_market_buyer_cohort()),
        "buyer_retention": dumps(am.api_market_buyer_retention()),
        "relist_gap": dumps(am.api_relist_gap()),
        "lifecycle": dumps(am.api_listing_lifecycle(_b1)),
    }
    am.api_market_seller_cohort()
    after_faces = {
        "buyer_cohort": dumps(am.api_market_buyer_cohort()),
        "buyer_retention": dumps(am.api_market_buyer_retention()),
        "relist_gap": dumps(am.api_relist_gap()),
        "lifecycle": dumps(am.api_listing_lifecycle(_b1)),
    }
    record("AC-MSC6", before_faces == after_faces,
           "four adjacent faces byte-identical=%s"
           % (before_faces == after_faces,))

    # -- AC-MSC7 pure read and determinism ---------------------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_market_seller_cohort())
    second = dumps(am.api_market_seller_cohort())
    third = dumps(am.api_market_seller_cohort())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    source = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    body_start = source.index(b"def api_market_seller_cohort")
    body_end = source.index(b"def api_market_buyer_retention", body_start)
    body = source[body_start:body_end]
    write_free = b"INSERT" not in body and b"UPDATE" not in body \
        and b"DELETE" not in body
    ac7 = (first == second == third
           and digests_before == digests_after
           and tx_before == tx_after
           and write_free)
    record("AC-MSC7", ac7,
           "three calls identical=%s tables frozen=%s ledger_tx=%d"
           " write_free=%s"
           % (first == second == third,
              digests_before == digests_after, len(tx_before),
              write_free))

    # -- AC-MSC8 cross-restart identity and wiring --------------------
    baseline = dumps(am.api_market_seller_cohort())
    close_stack(am, dk, metered, led)
    seen = []
    for _round in range(2):
        r_led, r_metered, r_dk, _r_gate, r_am = build_stack(
            db_path, cfg, lobby_cfg)
        seen.append(dumps(r_am.api_market_seller_cohort()))
        empty_again = dumps(r_am.api_market_seller_cohort())
        seen.append(empty_again)
        close_stack(r_am, r_dk, r_metered, r_led)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = open(os.path.join(os.path.dirname(BASE),
                               "reconcile_all.py"), "rb").read()
    wired = (b'"ledger-apimarket-sellercohort"' in runner)
    suite_src = open(os.path.abspath(__file__), "rb").read()
    ascii_ok = all(b < 128 for b in suite_src)
    lf_ok = b"\r\n" not in suite_src
    ac8 = (len(seen) == 4 and all(item == baseline for item in seen)
           and shas_before == shas_after
           and wired and ascii_ok and lf_ok)
    record("AC-MSC8", ac8,
           "four post-restart instances identical=%s files_frozen=%s"
           " wired=%s ascii=%s lf=%s"
           % (all(item == baseline for item in seen),
              shas_before == shas_after, wired, ascii_ok, lf_ok))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(RESULTS) else "FAIL",
                              passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-sellercohort-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = Clock()
    orig_now = A._now_utc
    A._now_utc = clock.now_utc
    try:
        return run(db_path, cfg, lobby_cfg, shas_before, clock, orig_now)
    finally:
        A._now_utc = orig_now


if __name__ == "__main__":
    sys.exit(main())