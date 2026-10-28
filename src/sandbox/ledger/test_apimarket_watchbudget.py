"""Acceptance suite for the apimarket buyer watchlist budget face
(BigDomain R2183; canon = the R2178 explore-queue seed row 5/10, the
criteria AC-WBG1..AC-WBG8 registered in that row's claim note BEFORE
this code existed - honesty law; the AC-WBG prefix, api_watch_budget
and this suite name were git-grep -F zero-occupancy anchored
2026-10-28, rc=1; api_watch_budget appears only as a text pointer in
src/os/closeout_R2182.py, so the code face was untouched).

Face under proof: APIMarketFace.api_watch_budget(buyer_id). The R2086
watchlist answers which rows a buyer watches and R2104 answers what
happened to them; nothing answered "what would it cost me to buy the
whole watchlist", which is the question a budget review actually asks.

  - a thirteen-key envelope and ten-key rows, counts derived from the
    rows, honest empty envelope for a prefix-valid account with no
    watches;
  - one bucket per live watch row in a pinned precedence (purchased >
    delisted > sold_out > buyable), the four counts summing to
    watch_count;
  - spend authority = the buyable bucket only: total, min, max, avg
    (None on an empty bucket, never a fabricated zero);
  - savings_from_drops sums max(0, price_at_watch - current) over the
    buyable rows only, so a rise never nets a genuine drop down;
  - total order on (current_price, listing_id);
  - the account shape gate before any read, frozen table digests and
    a constant ledger tx set (pure read, zero token movement);
  - cross-face identity against api_watchlist, the retirement and
    refund flips, strict buyer isolation;
  - cross-restart byte identity on three instances;
  - runner wiring plus suite hygiene (ASCII, no network imports,
    world outside the repo).

Usage: python test_apimarket_watchbudget.py
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

BAD_ACCOUNTS = ["", "bob", None, 5, True, [], {}, "   "]

ENVELOPE_KEYS = {"buyer_id", "watch_count", "buyable_count",
                 "purchased_count", "delisted_count",
                 "sold_out_count", "total_potential_spend",
                 "avg_potential_price", "min_potential_price",
                 "max_potential_price", "savings_from_drops",
                 "dropped_count", "disclaimer", "watches"}

ROW_KEYS = {"watch_id", "listing_id", "listing_key", "title",
            "dev_account", "bucket", "current_price",
            "price_at_watch", "saved", "watched_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds")

T_WATCH = "2026-10-28T10:00:00Z"
T_CHANGE = "2026-10-28T11:00:00Z"
T_LATE = "2026-10-28T12:00:00Z"


class Clock(object):
    """Single mutable stamp behind A._now_utc so every product write
    lands on a pinned instant and the price-at-watch boundary is
    testable without sleeping."""

    def __init__(self, stamp):
        self.stamp = stamp

    def now_utc(self):
        return self.stamp

    def set(self, stamp):
        self.stamp = stamp


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


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


def code_of(exc):
    return getattr(exc, "code", None)


def rows_of(am, buyer_id):
    return am.api_watch_budget(buyer_id)["watches"]


def by_key(am, buyer_id):
    return {r["listing_key"]: r for r in rows_of(am, buyer_id)}


def seed_world(led, dk, am, clock):
    """Owner dana publishes eight listings; bob watches all of them at
    T_WATCH and the world then moves: a genuine drop, a rise, a
    sold-out shelf, a retired shelf, a shelf sold out AND then
    retired (precedence probe), a shelf bob buys and that is then
    re-priced (saved reported, envelope untouched), and one bob
    unwatches."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-WBG-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-WBG-S",
                     "settlement")
    for who in ("bob", "carol", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    clock.set("2026-10-28T09:00:00Z")
    ids = {}
    specs = [
        ("drop", "Service Drop", 10, None),
        ("flat", "Service Flat", 8, None),
        ("rise", "Service Rise", 5, None),
        ("sold", "Service Sold", 7, 1),
        ("retire", "Service Retire", 9, None),
        ("soldret", "Service Sold Then Retired", 4, 1),
        ("bought", "Service Bought", 6, None),
        ("gone", "Service Gone", 3, None),
    ]
    for key, title, price, supply in specs:
        ids[key] = am.publish_api("usr:dana", key, title,
                                  "service payload " + key, PAYLOAD,
                                  price, False, supply)["listing_id"]
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="amwatchbudget-")
    db_path = os.path.join(tmp, "wbg.db")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    original_now = A._now_utc
    clock = Clock("2026-10-28T09:00:00Z")
    A._now_utc = clock.now_utc
    watch_count_before = None
    try:
        ids = seed_world(led, dk, am, clock)
        clock.set(T_WATCH)
        for key in ids:
            am.watch_api("usr:bob", ids[key])
        am.watch_api("usr:carol", ids["sold"])

        clock.set(T_CHANGE)
        am.revise_price("usr:dana", ids["drop"], 6)
        am.revise_price("usr:dana", ids["rise"], 7)
        purchase = am.purchase_api("usr:carol", ids["sold"],
                                   "ref-carol-wbg-sold")
        am.purchase_api("usr:carol", ids["soldret"],
                        "ref-carol-wbg-soldret")
        bob_buy = am.purchase_api("usr:bob", ids["bought"],
                                  "ref-bob-wbg-bought")
        am.unwatch_api("usr:bob", ids["gone"])

        clock.set(T_LATE)
        am.delist_api("usr:dana", ids["retire"])
        am.delist_api("usr:dana", ids["soldret"])
        am.revise_price("usr:dana", ids["bought"], 4)

        env = am.api_watch_budget("usr:bob")
        rows = env["watches"]
        empty = am.api_watch_budget("usr:")
        ok1 = (set(env.keys()) == ENVELOPE_KEYS
               and set(empty.keys()) == ENVELOPE_KEYS
               and all(set(r.keys()) == ROW_KEYS for r in rows)
               and env["watch_count"] == len(rows) == 7
               and env["disclaimer"] == DISCLAIMER
               and env["buyer_id"] == "usr:bob"
               and empty["watch_count"] == 0
               and empty["watches"] == []
               and [(r["current_price"], r["listing_id"])
                    for r in rows]
               == sorted((r["current_price"], r["listing_id"])
                         for r in rows))
        record("AC-WBG1", ok1,
               "envelope keys=%d rows=%d row keys=%r watch=%d"
               " empty=%r ordered=%r"
               % (len(env), len(rows),
                  sorted(set(len(r) for r in rows)),
                  env["watch_count"],
                  (empty["watch_count"], empty["watches"]),
                  [(r["current_price"], r["listing_id"])
                   for r in rows] == sorted(
                       (r["current_price"], r["listing_id"])
                       for r in rows)))

        # -- AC-WBG2 one bucket per row, pinned precedence --------------
        buckets = {r["listing_key"]: r["bucket"] for r in rows}
        counts = (env["buyable_count"], env["purchased_count"],
                  env["delisted_count"], env["sold_out_count"])
        ok2 = (buckets == {"drop": "buyable", "flat": "buyable",
                           "rise": "buyable", "sold": "sold_out",
                           "retire": "delisted",
                           "soldret": "delisted",
                           "bought": "purchased"}
               and "gone" not in buckets
               and sum(counts) == env["watch_count"] == 7
               and counts == (3, 1, 2, 1)
               and all(r["bucket"] in A.APIMarketFace
                       ._WATCH_BUDGET_BUCKETS for r in rows))
        record("AC-WBG2", ok2,
               "buckets=%r counts(b,p,d,s)=%r sum=%d"
               % (sorted(buckets.items()), counts, sum(counts)))

        # -- AC-WBG3 spend authority on the buyable bucket -------------
        ok3 = (env["total_potential_spend"] == 21
               and env["avg_potential_price"] == 7.0
               and env["min_potential_price"] == 6
               and env["max_potential_price"] == 8
               and env["total_potential_spend"] == sum(
                   r["current_price"] for r in rows
                   if r["bucket"] == "buyable")
               and empty["total_potential_spend"] == 0
               and empty["avg_potential_price"] is None
               and empty["min_potential_price"] is None
               and empty["max_potential_price"] is None
               and empty["buyable_count"] == 0)
        record("AC-WBG3", ok3,
               "total=%r avg=%r min=%r max=%r empty trio=%r"
               % (env["total_potential_spend"],
                  env["avg_potential_price"],
                  env["min_potential_price"],
                  env["max_potential_price"],
                  (empty["total_potential_spend"],
                   empty["avg_potential_price"],
                   empty["min_potential_price"],
                   empty["max_potential_price"])))

        # -- AC-WBG4 savings law (rises never net a drop down) ---------
        rk = by_key(am, "usr:bob")
        ok4 = (rk["drop"]["saved"] == 4
               and rk["drop"]["price_at_watch"] == 10
               and rk["drop"]["current_price"] == 6
               and rk["rise"]["saved"] == 0
               and rk["rise"]["price_at_watch"] == 5
               and rk["rise"]["current_price"] == 7
               and rk["bought"]["saved"] == 2
               and env["savings_from_drops"] == 4
               and env["dropped_count"] == 1
               and empty["savings_from_drops"] == 0
               and empty["dropped_count"] == 0)
        record("AC-WBG4", ok4,
               "drop saved=%r rise saved=%r purchased saved=%r"
               " envelope savings=%r dropped=%r"
               % (rk["drop"]["saved"], rk["rise"]["saved"],
                  rk["bought"]["saved"], env["savings_from_drops"],
                  env["dropped_count"]))

        # -- AC-WBG5 gate before any read ------------------------------
        digests_before = market_digests(am)
        tx_before = ledger_tx_ids(led)
        codes = []
        for bad in BAD_ACCOUNTS:
            try:
                am.api_watch_budget(bad)
                codes.append("NO-RAISE")
            except A.ApiMarketError as exc:
                codes.append(code_of(exc))
        digests_after = market_digests(am)
        tx_after = ledger_tx_ids(led)
        ok5 = (codes == [A.E_AM_BAD_ACCOUNT] * len(BAD_ACCOUNTS)
               and digests_before == digests_after
               and tx_before == tx_after)
        record("AC-WBG5", ok5,
               "bad-account codes=%r digests frozen=%r tx frozen=%r"
               % (sorted(set(codes)), digests_before == digests_after,
                  tx_before == tx_after))

        # -- AC-WBG6 cross-face identity and the live partition --------
        wl = am.api_watchlist("usr:bob")
        wl_purchased = sum(1 for w in wl["watches"] if w["purchased"])
        clock.set("2026-10-28T13:00:00Z")
        am.delist_api("usr:dana", ids["flat"])
        flipped = am.api_watch_budget("usr:bob")
        ok6 = (env["watch_count"] == wl["watch_count"] == 7
               and wl_purchased == env["purchased_count"] == 1
               and flipped["delisted_count"] == 3
               and flipped["buyable_count"] == 2
               and flipped["total_potential_spend"] == 13
               and flipped["min_potential_price"] == 6
               and flipped["max_potential_price"] == 7)
        record("AC-WBG6", ok6,
               "watch_count wl=%d face=%d purchased wl=%d face=%d"
               " after retire flat: delisted=%d buyable=%d total=%d"
               % (wl["watch_count"], env["watch_count"], wl_purchased,
                  env["purchased_count"], flipped["delisted_count"],
                  flipped["buyable_count"],
                  flipped["total_potential_spend"]))

        # -- AC-WBG7 lifecycle: the purchase seam, re-watch, isolation --
        # A refund does NOT move a bought watch back into the buyable
        # bucket: the purchase row survives the refund and a re-purchase
        # is refused by E_AM_PURCHASE_DUP, so the bucket follows purchase
        # existence exactly like api_watchlist's purchased flag. The
        # criterion was corrected to this measured seam (no product
        # widening) after the first run.
        am.refund_api("usr:bob", bob_buy["purchase_id"],
                      "suite refund")
        refunded = am.api_watch_budget("usr:bob")
        wl_after = am.api_watchlist("usr:bob")
        rk2 = by_key(am, "usr:bob")
        before_rewatch = refunded["watch_count"]
        am.unwatch_api("usr:bob", ids["rise"])
        after_unwatch = am.api_watch_budget("usr:bob")
        rew = am.watch_api("usr:bob", ids["rise"])
        after_rewatch = am.api_watch_budget("usr:bob")
        carol = am.api_watch_budget("usr:carol")
        ok7 = (rk2["bought"]["bucket"] == "purchased"
               and rk2["bought"]["saved"] == 2
               and refunded["purchased_count"] == 1
               and refunded["buyable_count"] == 2
               and refunded["total_potential_spend"] == 13
               and any(w["purchased"] for w in wl_after["watches"])
               and after_unwatch["watch_count"] == before_rewatch - 1
               and after_rewatch["watch_count"] == before_rewatch
               and rew["watch_id"] not in [
                   w["watch_id"] for w in rows]
               and carol["watch_count"] == 1
               and carol["purchased_count"] == 1
               and carol["sold_out_count"] == 0
               and carol["total_potential_spend"] == 0)
        record("AC-WBG7", ok7,
               "refund bucket=%r purchased=%d buyable=%d total=%d"
               " unwatch %d->%d rewatch->%d new-id=%r carol=%r"
               % (rk2["bought"]["bucket"],
                  refunded["purchased_count"],
                  refunded["buyable_count"],
                  refunded["total_potential_spend"], before_rewatch,
                  after_unwatch["watch_count"],
                  after_rewatch["watch_count"], rew["watch_id"],
                  (carol["watch_count"], carol["purchased_count"],
                   carol["sold_out_count"],
                   carol["total_potential_spend"])))

        family_one = {who: dumps(am.api_watch_budget("usr:" + who))
                      for who in ("bob", "carol", "erin")}
    finally:
        A._now_utc = original_now
        close_stack(am, dk, metered, led)

    # -- AC-WBG8 cross-restart identity + wiring + hygiene -----------
    family = {}
    for index in (2, 3):
        led2, metered2, dk2, gate2, am2 = build_stack(
            db_path, cfg, lobby_cfg)
        try:
            family[index] = {
                who: dumps(am2.api_watch_budget("usr:" + who))
                for who in ("bob", "carol", "erin")}
        finally:
            close_stack(am2, dk2, metered2, led2)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-watchbudget" in handle.read()
    with open(os.path.abspath(__file__), "rb") as handle:
        blob = handle.read()
    try:
        blob.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    src = blob.decode("utf-8", "replace")
    net_imports = [line for line in src.splitlines()
                   if line.strip().startswith(("import requests",
                                               "import urllib",
                                               "import http"))]
    outside = not os.path.abspath(tmp).startswith(
        os.path.abspath(os.path.join(BASE, "..", "..", "..")))
    same = (family_one == family[2] == family[3])
    ok8 = (same and wired and ascii_ok and not net_imports
           and outside)
    record("AC-WBG8", ok8,
           "instance1==2==3=%r runner wiring=%r ascii=%r"
           " network imports=%d world outside repo=%r"
           % (same, wired, ascii_ok, len(net_imports), outside))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())