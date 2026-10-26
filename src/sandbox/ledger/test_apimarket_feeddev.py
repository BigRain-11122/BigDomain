"""Seller dimension on the market activity feed (AC-AMSF1..AC-AMSF8).

Face under proof: APIMarketFace.api_market_feed(since_utc, until_utc,
kinds, limit, listing_id, dev_account) - the R2107 stream with the
R2113 per-listing filter grown by the one axis neither had. Before
this suite a seller holding N listings could slice the feed only by
time window, event family, tail limit or ONE shelf at a time: a
single timeline of "what happened across everything I sell" was
reachable only by calling the per-listing filter N times and merging
the answers by hand (which is what the offline report dossiers do,
and only there).

Criteria were pre-registered in the R2139 explore-queue row; the
zero-occupancy anchor check (AC-AMSF / test_apimarket_feeddev /
ledger-apimarket-feeddev) ran BEFORE the product edit (git grep -F
rc=1), while the row text itself was recorded after the edit in the
same window and that is disclosed there.

  AC-AMSF1 contract: with dev_account the envelope gains exactly one
    key (dev_account, echoing the normalized filter) and a default
    call stays byte-identical to the R2107/R2113 contract (ten
    envelope keys, thirteen row keys); total is the pre-truncation
    count.
  AC-AMSF2 gates: the seller shape gate sits AFTER window, inverted
    window, kinds, limit and listing gates; bad seller shapes are
    refused with E_AM_BAD_ACCOUNT and every refusal leaves the
    thirteen table digests and the ledger tx set untouched.
  AC-AMSF3 isolation: the per-seller streams partition the market
    stream exactly - disjoint, and their union is the market stream.
  AC-AMSF4 composition: seller x kinds, seller x window, seller x
    limit and seller x listing equal the set intersections, and limit
    keeps the tail of the FILTERED stream while total stays the
    pre-truncation count.
  AC-AMSF5 honest empty and retirement: a shape-valid account owning
    no listing answers an empty feed, and a seller's retired listing
    keeps its historical events.
  AC-AMSF6 pure read and restart: three identical calls move no row
    and no token, and a full-stack restart replays the same bytes.
  AC-AMSF7 consumers untouched: the report dossier feed still reads
    the per-listing filter, the JSON envelope still has exactly three
    keys and the schema does not rewind.
  AC-AMSF8 delivery: no shipped config byte changes, the module stays
    ASCII with LF endings, and the runner label is registered.
"""

import hashlib
import io
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
import apimarket_report as R          # noqa: E402 (R2101 consumer)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

LEGACY_ENVELOPE_KEYS = {"kinds", "since_utc", "until_utc", "listing_id",
                        "limit", "total", "returned", "truncated",
                        "disclaimer", "events"}
ENVELOPE_KEYS = LEGACY_ENVELOPE_KEYS | {"dev_account"}

ROW_KEYS = {"kind", "event_utc", "ref_id", "listing_id", "listing_key",
            "title", "dev_account", "token_price", "stars",
            "previous_stars", "amount", "units", "detail"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")

T1 = "2026-10-26T09:00:00Z"
T2 = "2026-10-26T09:10:00Z"
T3 = "2026-10-26T09:20:00Z"
T4 = "2026-10-26T09:30:00Z"
T5 = "2026-10-26T09:40:00Z"
T6 = "2026-10-26T09:50:00Z"
T7 = "2026-10-26T10:00:00Z"
T8 = "2026-10-26T10:10:00Z"
T9 = "2026-10-26T10:20:00Z"
T10 = "2026-10-26T10:30:00Z"

DANA = "usr:dana"
ERIN = "usr:erin"
BOB = "usr:bob"


class Clock(object):
    """Single mutable stamp behind A._now_utc so every write lands on a
    pinned instant and windows are testable without sleeping."""

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


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


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


def close_stack(stack):
    led, metered, dk, _gate, am = stack
    for handle in (am, dk, metered, led):
        try:
            handle.close()
        except Exception:
            pass


def code_of(exc):
    return getattr(exc, "code", None)


def expect_code(fn, code):
    try:
        fn()
    except A.ApiMarketError as exc:
        return code_of(exc) == code
    return False


def seed_world(led, dk):
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMSF-R",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMSF-S",
                     "settlement")
    led.ensure_account(BOB, census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 600),
                (BOB, "credit", 600)],
               "manual:fund-bob", "suite funding bob")
    dk.issue_key(DANA, "dana-key", 10, ["backtest"], False)
    dk.issue_key(ERIN, "erin-key", 10, ["backtest"], False)


def note_rows(env):
    return sorted((r["kind"], r["event_utc"], r["ref_id"], r["listing_id"])
                  for r in env["events"])


def main():
    tmp = tempfile.mkdtemp(prefix="amfeeddev-")
    db_path = os.path.join(tmp, "feeddev.db")
    cfg_path = os.path.join(BASE, "config.json")
    lobby_cfg_path = os.path.join(LOBBY, "config.json")
    cfg_sha = sha_file(cfg_path)
    lobby_sha = sha_file(lobby_cfg_path)
    with open(cfg_path, "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(lobby_cfg_path, "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    original_now = A._now_utc
    clock = Clock(T1)
    A._now_utc = clock.now_utc
    stack = build_stack(db_path, cfg, lobby_cfg)
    try:
        led, metered, dk, gate, am = stack
        seed_world(led, dk)
        clock.set(T1)
        a = am.publish_api(DANA, "flow-a", "Flow A", "first service",
                           PAYLOAD, 10, False, supply=5)["listing_id"]
        clock.set(T2)
        b = am.publish_api(DANA, "flow-b", "Flow B", "second service",
                           PAYLOAD, 11, False, supply=5)["listing_id"]
        clock.set(T3)
        am.restock_api(DANA, a, 3)
        clock.set(T4)
        am.revise_price(DANA, a, 8)
        clock.set(T5)
        am.revise_price(DANA, b, 9)
        clock.set(T6)
        c = am.publish_api(ERIN, "flow-c", "Flow C", "third service",
                           PAYLOAD, 12, False, supply=5)["listing_id"]
        clock.set(T7)
        am.revise_price(ERIN, c, 7)
        clock.set(T8)
        am.purchase_api(BOB, a, "ref-amsf-buy")
        clock.set(T9)
        am.rate_api(BOB, a, 5)
        clock.set(T10)
        am.delist_api(DANA, b)

        market = am.api_market_feed()
        fd = am.api_market_feed(dev_account=DANA)
        fe = am.api_market_feed(dev_account=ERIN)

        # -- AC-AMSF1 contract and echo ------------------------------
        default_same = (dumps(market) ==
                        dumps(am.api_market_feed(dev_account=None)))
        ok1 = (set(market.keys()) == LEGACY_ENVELOPE_KEYS
               and default_same
               and set(fd.keys()) == ENVELOPE_KEYS
               and fd["dev_account"] == DANA
               and fe["dev_account"] == ERIN
               and fd["total"] == len(fd["events"]) == 8
               and fe["total"] == len(fe["events"]) == 2
               and market["total"] == 10
               and all(set(r.keys()) == ROW_KEYS for r in fd["events"])
               and fd["returned"] == 8 and fd["truncated"] is False)
        record("AC-AMSF1", ok1,
               "keys=%d legacy=%s dana=%d erin=%d market=%d"
               % (len(fd), set(market.keys()) == LEGACY_ENVELOPE_KEYS,
                  fd["total"], fe["total"], market["total"]))

        # -- AC-AMSF2 gate family, order and zero side effects --------
        before = market_digests(am)
        tx_before = ledger_tx_ids(led)
        bad_sellers = ["", "   ", "dana", 3, 3.5, True,
                       [DANA], {"d": DANA}]
        shape_ok = all(expect_code(
            lambda v=v: am.api_market_feed(dev_account=v),
            A.E_AM_BAD_ACCOUNT) for v in bad_sellers)
        # The shape gate is prefix-only (the R2077/R2078 precedent), so a
        # bare "usr:" passes it and answers an honest empty stream.
        prefix_only = am.api_market_feed(dev_account="usr:")
        window_first = expect_code(
            lambda: am.api_market_feed(since_utc="bad", dev_account=""),
            A.E_AM_BAD_WINDOW)
        inverted_first = expect_code(
            lambda: am.api_market_feed(since_utc=T9, until_utc=T3,
                                       dev_account=""),
            A.E_AM_BAD_WINDOW)
        kinds_first = expect_code(
            lambda: am.api_market_feed(kinds=["nope"], dev_account=""),
            A.E_AM_BAD_ARGS)
        limit_first = expect_code(
            lambda: am.api_market_feed(limit=0, dev_account=""),
            A.E_AM_BAD_ARGS)
        listing_first = expect_code(
            lambda: am.api_market_feed(listing_id=0, dev_account=""),
            A.E_AM_BAD_ARGS)
        after = market_digests(am)
        ok2 = (shape_ok and prefix_only["total"] == 0
               and prefix_only["events"] == []
               and window_first and inverted_first
               and kinds_first and limit_first and listing_first
               and before == after
               and tx_before == ledger_tx_ids(led))
        record("AC-AMSF2", ok2,
               "shapes=%d win=%s inv=%s kinds=%s limit=%s listing=%s"
               " frozen=%s"
               % (len(bad_sellers), window_first, inverted_first,
                  kinds_first, limit_first, listing_first,
                  before == after))

        # -- AC-AMSF3 isolation and exact partition ------------------
        union = sorted(note_rows(fd) + note_rows(fe))
        ok3 = (union == note_rows(market)
               and fd["total"] + fe["total"] == market["total"]
               and not (set(note_rows(fd)) & set(note_rows(fe)))
               and all(r["dev_account"] == DANA for r in fd["events"])
               and all(r["dev_account"] == ERIN for r in fe["events"]))
        record("AC-AMSF3", ok3,
               "union=%d market=%d disjoint=%s"
               % (len(union), market["total"],
                  not (set(note_rows(fd)) & set(note_rows(fe)))))

        # -- AC-AMSF4 composition with kinds / window / limit / listing
        kinds_d = am.api_market_feed(dev_account=DANA,
                                     kinds=["price_revised", "purchased"])
        want_kinds = sorted(r for r in note_rows(fd)
                            if r[0] in ("price_revised", "purchased"))
        win_d = am.api_market_feed(dev_account=DANA, since_utc=T3,
                                   until_utc=T9)
        want_win = sorted(r for r in note_rows(fd)
                          if T3 <= r[1] < T9)
        tail_d = am.api_market_feed(dev_account=DANA, limit=3)
        both_d = am.api_market_feed(dev_account=DANA, listing_id=a)
        ok4 = (note_rows(kinds_d) == want_kinds
               and kinds_d["total"] == len(want_kinds) == 3
               and note_rows(win_d) == want_win
               and win_d["total"] == len(want_win) == 4
               and tail_d["events"] == fd["events"][-3:]
               and tail_d["returned"] == 3 and tail_d["total"] == 8
               and tail_d["truncated"] is True
               and both_d["total"] == 5
               and all(r["listing_id"] == a for r in both_d["events"])
               and note_rows(both_d) == sorted(
                   note_rows(am.api_market_feed(listing_id=a))))
        record("AC-AMSF4", ok4,
               "kinds=%d window=%d tail=%d/%d listing=%d"
               % (kinds_d["total"], win_d["total"], tail_d["returned"],
                  tail_d["total"], both_d["total"]))

        # -- AC-AMSF5 honest empty and retirement --------------------
        ghost = am.api_market_feed(dev_account="usr:ghost")
        dana_kinds = [r["kind"] for r in fd["events"]]
        ok5 = (ghost["total"] == 0 and ghost["returned"] == 0
               and ghost["events"] == [] and ghost["truncated"] is False
               and ghost["dev_account"] == "usr:ghost"
               and "delisted" in dana_kinds
               and any(r["listing_id"] == b and r["kind"] == "delisted"
                       for r in fd["events"]))
        record("AC-AMSF5", ok5,
               "ghost=%d retired_kept=%s"
               % (ghost["total"], "delisted" in dana_kinds))

        # -- AC-AMSF6 pure read --------------------------------------
        d0 = market_digests(am)
        t0 = ledger_tx_ids(led)
        r1 = dumps(am.api_market_feed(dev_account=DANA))
        r2 = dumps(am.api_market_feed(dev_account=DANA))
        r3 = dumps(am.api_market_feed(dev_account=DANA))
        frozen = (d0 == market_digests(am)
                  and t0 == ledger_tx_ids(led))

        # -- AC-AMSF7 consumers untouched ----------------------------
        report = R.collect(am)
        dossiers = report["dossiers"]
        same = all(
            dossiers[str(lid)]["feed"] ==
            am.api_market_feed(listing_id=lid, limit=R.FEED_LIMIT)
            for lid in (a, b, c))
        js_tmp = os.path.join(tmp, "s.json")
        out_tmp = os.path.join(tmp, "s.html")
        R.main(["--db", db_path, "--out", out_tmp, "--json-out", js_tmp])
        doc = json.loads(io.open(js_tmp, "r", encoding="utf-8").read())
        page = R.render_html(report)
        ok7 = (R.REPORT_SCHEMA >= 7
               and len(R.DOSSIER_KEYS) == 9
               and same
               and "recent activity (" in page
               and sorted(doc) == ["attention", "report",
                                   "schema_version"]
               and doc.get("schema_version") == R.REPORT_SCHEMA)
        record("AC-AMSF7", ok7,
               "schema=%d keys=%d dossier_feed_same=%s env=%s"
               % (R.REPORT_SCHEMA, len(R.DOSSIER_KEYS), same,
                  sorted(doc)))
    finally:
        close_stack(stack)

    # -- AC-AMSF6 restart leg (same db, fresh stack) -----------------
    stack2 = build_stack(db_path, cfg, lobby_cfg)
    try:
        am2 = stack2[4]
        restart_same = (dumps(am2.api_market_feed(dev_account=DANA)) == r1)
        erin_same = (dumps(am2.api_market_feed(dev_account=ERIN)) ==
                     dumps(fe))
        ok6 = (r1 == r2 == r3 and frozen and restart_same
               and erin_same)
        record("AC-AMSF6", ok6,
               "identical=%s frozen=%s restart=%s erin_restart=%s"
               % (r1 == r2 == r3, frozen, restart_same, erin_same))

        # -- AC-AMSF8 delivery hygiene -------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            runner = handle.read()
        with open(os.path.join(BASE, "apimarket.py"), "rb") as handle:
            src = handle.read()
        ok8 = ("ledger-apimarket-feeddev" in runner
               and sha_file(cfg_path) == cfg_sha
               and sha_file(lobby_cfg_path) == lobby_sha
               and b"\r" not in src
               and all(byte < 128 for byte in src))
        record("AC-AMSF8", ok8,
               "runner=%s cfgs=%s ascii=%s"
               % ("ledger-apimarket-feeddev" in runner,
                  sha_file(cfg_path) == cfg_sha,
                  all(byte < 128 for byte in src)))
    finally:
        A._now_utc = original_now
        close_stack(stack2)

    total = len(RESULTS)
    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d %s" % (passed, total,
                             "PASS" if passed == total else "FAIL"),
          flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())