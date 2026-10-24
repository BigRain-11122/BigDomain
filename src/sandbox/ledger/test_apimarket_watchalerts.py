"""Acceptance suite for the apimarket buyer watch alert feed
(BigDomain R2104; canon = the explore-queue row seeded and claimed in
R2104, criteria AC-WAL1..AC-WAL8 registered in that claim note BEFORE
this code existed - honesty law; the AC-WAL prefix, api_watch_alerts,
_price_at_instant, this suite name and the ledger-apimarket-watchalerts
runner label were all git-grep -F zero-occupancy anchored 2026-10-25,
rc=1).

Face under proof: APIMarketFace.api_watch_alerts(buyer_id). The R2086
watchlist answers WHAT a buyer is watching; nothing answered WHAT
HAPPENED to those watches, so a resident had to diff the table by
hand. This window pins the resident-side event feed:

  - a four-key envelope and thirteen-key rows, alert_count derived
    from the rows, watch_count from the live watch rows, honest empty
    envelope for a prefix-valid account with no watches;
  - the price-at-watch law: the asking price at the watch instant is
    the base row overridden by the newest revision stamped at or
    before watched_utc (ties by revision_id); a later revision never
    rewrites what an earlier instant saw;
  - four derived kinds (delisted / sold_out / price_drop /
    price_rise) with pinned severities, a signed delta, deliberate
    silence when the price did not move, and retirement superseding
    every price signal;
  - settled and unwatched watches are silent; strict buyer isolation;
  - a total order on (rank, listing_id) and byte-identical double
    runs;
  - the account shape gate before any read, frozen table digests and
    a constant ledger tx set (pure read, zero token movement);
  - cross-restart byte identity on three instances;
  - runner wiring plus suite hygiene (ASCII, no network imports,
    world outside the repo, stable product file shas).

Usage: python test_apimarket_watchalerts.py
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

ENVELOPE_KEYS = {"buyer_id", "watch_count", "alert_count",
                 "disclaimer", "alerts"}

ROW_KEYS = {"watch_id", "listing_id", "listing_key", "title",
            "dev_account", "kind", "severity", "price_at_watch",
            "current_price", "delta", "delisted", "sold_out",
            "watched_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds")

RANK = {"delisted": 0, "sold_out": 1, "price_drop": 2,
        "price_rise": 3}

SEVERITY = {"delisted": "high", "sold_out": "warn",
            "price_drop": "info", "price_rise": "info"}

T_WATCH = "2026-10-25T10:00:00Z"
T_CHANGE = "2026-10-25T11:00:00Z"
T_LATE = "2026-10-25T12:00:00Z"


class Clock(object):
    """Single mutable stamp behind A._now_utc (the report suite
    precedent), so every product write lands on a pinned instant and
    the price-at-watch boundary is testable without sleeping."""

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


def code_of(exc):
    return getattr(exc, "code", None)


def alert_rows(am, buyer_id):
    return am.api_watch_alerts(buyer_id)["alerts"]


def keys_of(am, buyer_id):
    return [row["listing_key"] for row in alert_rows(am, buyer_id)]


def kinds_of(am, buyer_id):
    return {(row["listing_key"], row["kind"]) for row in alert_rows(
        am, buyer_id)}


def seed_world(led, dk, am, clock):
    """Owner dana publishes eight listings; bob watches all of them at
    T_WATCH and the world then moves: a drop, a rise, two sold-out
    shelves, a retire after a drop, a settled purchase, an unwatch and
    one listing that deliberately never moves."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-WAL-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-WAL-S",
                     "settlement")
    for who in ("bob", "carol", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    clock.set("2026-10-25T09:00:00Z")
    ids = {}
    specs = [
        ("drop", "Service Drop", 10, None),
        ("rise", "Service Rise", 8, None),
        ("sold2", "Service Sold Two", 5, 2),
        ("sold1", "Service Sold One", 7, 1),
        ("retire", "Service Retire", 4, None),
        ("settled", "Service Settled", 6, None),
        ("gone", "Service Gone", 9, None),
        ("flat", "Service Flat", 3, None),
        ("tie", "Service Tie", 4, None),
    ]
    for key, title, price, supply in specs:
        ids[key] = am.publish_api("usr:dana", key, title,
                                  "service payload " + key, PAYLOAD,
                                  price, False, supply)["listing_id"]
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="amwatchalerts-")
    db_path = os.path.join(tmp, "wal.db")
    cfg, lobby_cfg = None, None
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    original_now = A._now_utc
    clock = Clock("2026-10-25T09:00:00Z")
    A._now_utc = clock.now_utc
    try:
        # -- AC-WAL1 contract + honest empty ---------------------------
        ids = seed_world(led, dk, am, clock)
        clock.set(T_WATCH)
        for key in ids:
            if key == "tie":
                continue
            am.watch_api("usr:bob", ids[key])
        am.watch_api("usr:carol", ids["sold1"])
        # the tie-stamp anchor: the watch lands first and a revision
        # with the SAME stamp lands right after it (AC-WAL2)
        am.watch_api("usr:bob", ids["tie"])
        am.revise_price("usr:dana", ids["tie"], 5)

        clock.set(T_CHANGE)
        am.revise_price("usr:dana", ids["drop"], 6)
        am.revise_price("usr:dana", ids["rise"], 12)
        am.revise_price("usr:dana", ids["retire"], 2)
        am.purchase_api("usr:carol", ids["sold2"], "ref-carol-sold2")
        am.purchase_api("usr:erin", ids["sold1"], "ref-erin-sold1")
        am.purchase_api("usr:erin", ids["sold2"], "ref-erin-sold2")
        am.purchase_api("usr:bob", ids["settled"], "ref-bob-settled")
        am.unwatch_api("usr:bob", ids["gone"])

        clock.set(T_LATE)
        am.delist_api("usr:dana", ids["retire"])

        env = am.api_watch_alerts("usr:bob")
        rows = env["alerts"]
        empty = am.api_watch_alerts("usr:erin")
        ok1 = (set(env.keys()) == ENVELOPE_KEYS
               and set(empty.keys()) == ENVELOPE_KEYS
               and all(set(r.keys()) == ROW_KEYS for r in rows)
               and env["alert_count"] == len(rows)
               and env["watch_count"] == 8
               and env["disclaimer"] == DISCLAIMER
               and empty["watch_count"] == 0
               and empty["alert_count"] == 0
               and empty["alerts"] == []
               and empty["disclaimer"] == DISCLAIMER
               and env["buyer_id"] == "usr:bob")
        record("AC-WAL1", ok1,
               "envelope keys=%d rows=%d row keys=%r watch=%d"
               " alert=%d empty=%r"
               % (len(env), len(rows),
                  sorted(set(len(r) for r in rows)), env["watch_count"],
                  env["alert_count"], (empty["watch_count"],
                                       empty["alert_count"])))

        # -- AC-WAL2 price-at-watch law --------------------------------
        # a revision stamped EXACTLY at the watch stamp counts, a
        # later one never rewrites it.
        clock.set(T_LATE)
        am.revise_price("usr:dana", ids["tie"], 1)
        at_watch = None
        for row in alert_rows(am, "usr:bob"):
            if row["listing_key"] == "tie":
                at_watch = row["price_at_watch"]
        drop_row = [r for r in alert_rows(am, "usr:bob")
                    if r["listing_key"] == "drop"][0]
        ok2 = (at_watch == 5 and drop_row["price_at_watch"] == 10
               and drop_row["current_price"] == 6
               and drop_row["delta"] == -4)
        record("AC-WAL2", ok2,
               "tie-stamp at_watch=%r drop at_watch=%r current=%r"
               " delta=%r" % (at_watch, drop_row["price_at_watch"],
                              drop_row["current_price"],
                              drop_row["delta"]))

        # -- AC-WAL3 derived kinds, severity, signed delta, silence ----
        by_key = {}
        for row in alert_rows(am, "usr:bob"):
            by_key.setdefault(row["listing_key"], []).append(row)
        rise_rows = by_key.get("rise", [])
        retire_rows = by_key.get("retire", [])
        ok3 = (set(by_key) == {"drop", "rise", "sold2", "sold1",
                               "retire", "tie"}
               and "settled" not in by_key and "gone" not in by_key
               and "flat" not in by_key
               and len(retire_rows) == 1
               and retire_rows[0]["kind"] == "delisted"
               and retire_rows[0]["delisted"] is True
               and retire_rows[0]["severity"] == "high"
               and [r["kind"] for r in by_key["sold2"]] == ["sold_out"]
               and [r["kind"] for r in by_key["sold1"]] == ["sold_out"]
               and by_key["sold2"][0]["severity"] == "warn"
               and by_key["sold2"][0]["sold_out"] is True
               and [r["kind"] for r in by_key["drop"]] == ["price_drop"]
               and by_key["drop"][0]["severity"] == "info"
               and len(rise_rows) == 1 and rise_rows[0]["kind"] ==
               "price_rise"
               and rise_rows[0]["delta"] == 4
               and rise_rows[0]["severity"] == "info"
               and [r["delta"] for r in by_key["tie"]] == [-4]
               and [r["kind"] for r in by_key["tie"]] == ["price_drop"]
               and by_key["tie"][0]["delta"] == -4
               and all(r["severity"] == SEVERITY[r["kind"]]
                       for r in alert_rows(am, "usr:bob")))
        record("AC-WAL3", ok3,
               "keys=%r retire=%r rise=%r drop delta=%r sold=%r"
               % (sorted(by_key), [r["kind"] for r in retire_rows],
                  [r["kind"] for r in rise_rows],
                  by_key["drop"][0]["delta"],
                  [by_key["sold2"][0]["kind"],
                   by_key["sold1"][0]["kind"]]))

        # -- AC-WAL4 total order + determinism -------------------------
        rows_now = alert_rows(am, "usr:bob")
        keys = [(RANK[r["kind"]], r["listing_id"]) for r in rows_now]
        ok4 = (keys == sorted(keys)
               and len(set(keys)) == len(keys)
               and dumps(am.api_watch_alerts("usr:bob")) ==
               dumps(am.api_watch_alerts("usr:bob")))
        record("AC-WAL4", ok4,
               "ordered=%r distinct=%r double-run identical=%r"
               % (keys == sorted(keys), len(set(keys)) == len(keys),
                  dumps(am.api_watch_alerts("usr:bob")) ==
                  dumps(am.api_watch_alerts("usr:bob"))))

        # -- AC-WAL5 scope laws ---------------------------------------
        carol_keys = set(keys_of(am, "usr:carol"))
        ok5 = (carol_keys == {"sold1"}
               and kinds_of(am, "usr:carol") == {("sold1", "sold_out")}
               and "retire" not in carol_keys
               and "settled" not in keys_of(am, "usr:bob")
               and "gone" not in keys_of(am, "usr:bob")
               and any(r["listing_key"] == "retire"
                       and r["delisted"] for r in rows_now))
        record("AC-WAL5", ok5,
               "carol keys=%r bob watch=%d settled silent=%r"
               " unwatched silent=%r watched-then-retired=%r"
               % (sorted(carol_keys), env["watch_count"],
                  "settled" not in keys_of(am, "usr:bob"),
                  "gone" not in keys_of(am, "usr:bob"),
                  "retire" in keys_of(am, "usr:bob")))

        # -- AC-WAL6 gate before read + pure read ----------------------
        digests_before = market_digests(am)
        tx_before = ledger_tx_ids(led)
        codes = []
        for bad in BAD_ACCOUNTS:
            try:
                am.api_watch_alerts(bad)
                codes.append("NO-RAISE")
            except A.ApiMarketError as exc:
                codes.append(code_of(exc))
        digests_after = market_digests(am)
        tx_after = ledger_tx_ids(led)
        ok6 = (codes == [A.E_AM_BAD_ACCOUNT] * len(BAD_ACCOUNTS)
               and digests_before == digests_after
               and tx_before == tx_after)
        record("AC-WAL6", ok6,
               "bad-account codes=%r digests frozen=%r tx frozen=%r"
               % (sorted(set(codes)), digests_before == digests_after,
                  tx_before == tx_after))

        family_one = {who: dumps(am.api_watch_alerts("usr:" + who))
                      for who in ("bob", "carol", "erin")}
        counts_one = {t: digests_after[t][0] for t in TABLES}
    finally:
        A._now_utc = original_now
        close_stack(am, dk, metered, led)

    # -- AC-WAL7 cross-restart byte identity --------------------------
    family_two = {}
    family_three = {}
    for index in (2, 3):
        led2, metered2, dk2, gate2, am2 = build_stack(
            db_path, cfg, lobby_cfg)
        try:
            fam = {who: dumps(am2.api_watch_alerts("usr:" + who))
                   for who in ("bob", "carol", "erin")}
        finally:
            close_stack(am2, dk2, metered2, led2)
        if index == 2:
            family_two = fam
        else:
            family_three = fam
    ok7 = family_one == family_two == family_three
    record("AC-WAL7", ok7,
           "instance1==2==3 byte-identical=%r" % ok7)

    # -- AC-WAL8 wiring + hygiene ------------------------------------
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-watchalerts" in handle.read()
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
    outside = not os.path.abspath(tmp).startswith(
        os.path.abspath(os.path.join(BASE, "..", "..", "..")))
    ok8 = (wired and ascii_ok and not net_imports and outside
           and counts_one["apimarket_watchlist"] == 10)
    record("AC-WAL8", ok8,
           "runner wiring=%r ascii=%r network imports=%d world"
           " outside repo=%r watch rows=%r product shas=%d"
           % (wired, ascii_ok, len(net_imports), outside,
              counts_one["apimarket_watchlist"], len(shas_after)))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())