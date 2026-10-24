"""Per-listing filter on the market activity feed (AC-AMFL1..AC-AMFL8).

Face under proof: APIMarketFace.api_market_feed(since_utc, until_utc,
kinds, limit, listing_id) - the R2107 stream grown by the one axis it
never had. Before this suite the feed could only be sliced by time
window, kind family and tail limit: a buyer or seller sitting on one
listing page could not ask "what happened to THIS shelf", because the
per-listing history lives in seven separate faces that the caller had
to merge by hand (which is exactly what the offline report dossiers
did, and only there).

Criteria were pre-registered in the R2113 explore-queue row BEFORE
this code existed.

  AC-AMFL1 contract: the envelope gains exactly one key (listing_id,
    echoing the normalized filter or None) and a default call stays
    byte-identical to the R2107 contract; every returned row belongs
    to the filtered listing and total is the pre-truncation count.
  AC-AMFL2 gates: listing_id shape (bool/str/float/0/negative) is
    refused with E_AM_BAD_ARGS, the window gate still fires first, and
    every refusal leaves the thirteen table digests and the ledger tx
    set untouched.
  AC-AMFL3 honest empty: a shape-valid id the market does not hold
    answers an empty feed rather than raising (the feed is a stream
    filter; api_view is the entity face).
  AC-AMFL4 zero permeation: the per-listing streams partition the
    market stream exactly - concatenated they reproduce it, no row of
    another listing leaks in.
  AC-AMFL5 composition: listing x kinds and listing x window equal the
    set intersections, and limit keeps the tail of the filtered stream
    while total stays the pre-truncation count.
  AC-AMFL6 pure read: three identical calls move no row and no token.
  AC-AMFL7 consumer: every report dossier block carries the per-listing
    feed (DOSSIER_KEYS 8 -> 9, REPORT_SCHEMA 6 -> 7 additive), the page
    renders the recent-activity sub-table with the pinned six columns,
    and the JSON envelope still has exactly three keys.
  AC-AMFL8 delivery: no shipped config byte changes, the module stays
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

ENVELOPE_KEYS = {"kinds", "since_utc", "until_utc", "listing_id",
                 "limit", "total", "returned", "truncated",
                 "disclaimer", "events"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")

T_PUB_A = "2026-10-25T09:00:00Z"
T_PUB_B = "2026-10-25T09:10:00Z"
T_RESTOCK = "2026-10-25T09:20:00Z"
T_PRICE_A = "2026-10-25T09:30:00Z"
T_PRICE_B = "2026-10-25T09:40:00Z"
T_BUY = "2026-10-25T09:50:00Z"
T_RATE = "2026-10-25T10:00:00Z"
T_DELIST_B = "2026-10-25T10:10:00Z"


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


def code_of(exc):
    return getattr(exc, "code", None)


def expect_code(fn, code):
    try:
        fn()
    except A.ApiMarketError as exc:
        return code_of(exc) == code
    return False


def seed_world(led, dk):
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMFL-R",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMFL-S",
                     "settlement")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:bob", "credit", 400)],
               "manual:fund-bob", "suite funding bob")
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)


def note_rows(env):
    return [(r["kind"], r["event_utc"], r["ref_id"], r["listing_id"])
            for r in env["events"]]


def main():
    tmp = tempfile.mkdtemp(prefix="amfeedlisting-")
    db_path = os.path.join(tmp, "feedlisting.db")
    cfg_path = os.path.join(BASE, "config.json")
    lobby_cfg_path = os.path.join(LOBBY, "config.json")
    cfg_sha = sha_file(cfg_path)
    lobby_sha = sha_file(lobby_cfg_path)
    with open(cfg_path, "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(lobby_cfg_path, "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    original_now = A._now_utc
    clock = Clock(T_PUB_A)
    A._now_utc = clock.now_utc
    try:
        seed_world(led, dk)
        clock.set(T_PUB_A)
        a = am.publish_api("usr:dana", "flow-a", "Flow A",
                           "first service", PAYLOAD, 10, False,
                           supply=5)["listing_id"]
        clock.set(T_PUB_B)
        b = am.publish_api("usr:dana", "flow-b", "Flow B",
                           "second service", PAYLOAD, 11, False,
                           supply=5)["listing_id"]
        clock.set(T_RESTOCK)
        am.restock_api("usr:dana", a, 3)
        clock.set(T_PRICE_A)
        am.revise_price("usr:dana", a, 8)
        clock.set(T_PRICE_B)
        am.revise_price("usr:dana", b, 9)
        clock.set(T_BUY)
        am.purchase_api("usr:bob", a, "ref-amfl-buy")
        clock.set(T_RATE)
        am.rate_api("usr:bob", a, 5)
        clock.set(T_DELIST_B)
        am.delist_api("usr:dana", b)

        market = am.api_market_feed()
        fa = am.api_market_feed(listing_id=a)
        fb = am.api_market_feed(listing_id=b)

        # -- AC-AMFL1 contract and echo ------------------------------
        default_same = (dumps(market) ==
                        dumps(am.api_market_feed(listing_id=None)))
        ok1 = (set(market.keys()) == ENVELOPE_KEYS
               and market["listing_id"] is None
               and default_same
               and fa["listing_id"] == a and fb["listing_id"] == b
               and fa["total"] == len(fa["events"]) == 5
               and fb["total"] == len(fb["events"]) == 3
               and fa["returned"] == 5 and fa["truncated"] is False
               and all(r["listing_id"] == a for r in fa["events"])
               and all(r["listing_id"] == b for r in fb["events"])
               and market["total"] == 8)
        record("AC-AMFL1", ok1,
               "keys=%d default_same=%s a=%d b=%d market=%d"
               % (len(market), default_same, fa["total"], fb["total"],
                  market["total"]))

        # -- AC-AMFL2 gate family, order and zero side effects --------
        before = market_digests(am)
        tx_before = ledger_tx_ids(led)
        bad_shapes = [True, False, 0, -1, "3", 3.5, [3], {"id": 3}]
        shape_ok = all(expect_code(
            lambda v=v: am.api_market_feed(listing_id=v),
            A.E_AM_BAD_ARGS) for v in bad_shapes)
        window_first = expect_code(
            lambda: am.api_market_feed(since_utc="bad", listing_id=0),
            A.E_AM_BAD_WINDOW)
        inverted_first = expect_code(
            lambda: am.api_market_feed(since_utc=T_RATE,
                                       until_utc=T_RESTOCK,
                                       listing_id=0),
            A.E_AM_BAD_WINDOW)
        kinds_ok = expect_code(
            lambda: am.api_market_feed(kinds=["nope"]),
            A.E_AM_BAD_ARGS)
        limit_ok = expect_code(
            lambda: am.api_market_feed(limit=0),
            A.E_AM_BAD_ARGS)
        after = market_digests(am)
        ok2 = (shape_ok and window_first and inverted_first
               and kinds_ok and limit_ok and before == after
               and tx_before == ledger_tx_ids(led))
        record("AC-AMFL2", ok2,
               "shapes=%d window_first=%s inverted_first=%s"
               " kinds=%s limit=%s frozen=%s"
               % (len(bad_shapes), window_first, inverted_first,
                  kinds_ok, limit_ok, before == after))

        # -- AC-AMFL3 honest empty on an unknown listing --------------
        ghost = am.api_market_feed(listing_id=999999)
        ok3 = (ghost["total"] == 0 and ghost["returned"] == 0
               and ghost["events"] == [] and ghost["truncated"] is False
               and ghost["listing_id"] == 999999
               and ghost["kinds"] == market["kinds"])
        record("AC-AMFL3", ok3,
               "total=%s returned=%s listing=%s kinds_kept=%s"
               % (ghost["total"], ghost["returned"],
                  ghost["listing_id"], ghost["kinds"] == market["kinds"]))

        # -- AC-AMFL4 zero permeation, exact partition ----------------
        merged = sorted(note_rows(fa) + note_rows(fb))
        ok4 = (merged == sorted(note_rows(market))
               and fa["total"] + fb["total"] == market["total"]
               and not (set(note_rows(fa)) & set(note_rows(fb)))
               and all(r["listing_id"] in (a, b)
                       for r in market["events"]))
        record("AC-AMFL4", ok4,
               "merged=%d market=%d disjoint=%s"
               % (len(merged), len(market["events"]),
                  not (set(note_rows(fa)) & set(note_rows(fb)))))

        # -- AC-AMFL5 composition with kinds / window / limit ---------
        kinds_a = am.api_market_feed(listing_id=a,
                                     kinds=["price_revised",
                                            "purchased"])
        want_kinds = sorted(
            r for r in note_rows(fa)
            if r[0] in ("price_revised", "purchased"))
        win_a = am.api_market_feed(listing_id=a,
                                   since_utc=T_RESTOCK,
                                   until_utc=T_RATE)
        want_win = sorted(r for r in note_rows(fa)
                          if T_RESTOCK <= r[1] < T_RATE)
        tail_a = am.api_market_feed(listing_id=a, limit=2)
        ok5 = (sorted(note_rows(kinds_a)) == want_kinds
               and kinds_a["total"] == len(want_kinds) == 2
               and sorted(note_rows(win_a)) == want_win
               and win_a["total"] == len(want_win) == 3
               and tail_a["events"] == fa["events"][-2:]
               and tail_a["returned"] == 2 and tail_a["total"] == 5
               and tail_a["truncated"] is True)
        record("AC-AMFL5", ok5,
               "kinds=%d window=%d tail=%d/%d truncated=%s"
               % (kinds_a["total"], win_a["total"],
                  tail_a["returned"], tail_a["total"],
                  tail_a["truncated"]))

        # -- AC-AMFL6 pure read --------------------------------------
        d0 = market_digests(am)
        t0 = ledger_tx_ids(led)
        r1 = dumps(am.api_market_feed(listing_id=a))
        r2 = dumps(am.api_market_feed(listing_id=a))
        r3 = dumps(am.api_market_feed(listing_id=a))
        ok6 = (r1 == r2 == r3 and d0 == market_digests(am)
               and t0 == ledger_tx_ids(led))
        record("AC-AMFL6", ok6,
               "identical=%s frozen=%s tx_frozen=%s"
               % (r1 == r2 == r3, d0 == market_digests(am),
                  t0 == ledger_tx_ids(led)))

        # -- AC-AMFL7 consumer: dossier feed + schema + HTML ----------
        report = R.collect(am)
        dossiers = report["dossiers"]
        same = all(
            dossiers[str(lid)]["feed"] ==
            am.api_market_feed(listing_id=lid, limit=R.FEED_LIMIT)
            for lid in (a, b))
        page = R.render_html(report)
        heads = ("recent activity (" in page
                 and "<th>kind</th>" in page
                 and "<th>event_utc</th>" in page)
        js_tmp = os.path.join(tmp, "s.json")
        out_tmp = os.path.join(tmp, "s.html")
        R.main(["--db", db_path, "--out", out_tmp, "--json-out", js_tmp])
        doc = json.loads(io.open(js_tmp, "r", encoding="utf-8").read())
        ok7 = (R.REPORT_SCHEMA >= 7
               and len(R.DOSSIER_KEYS) == 9
               and "feed" in R.DOSSIER_KEYS
               and same and heads
               and sorted(doc) == ["attention", "report",
                                   "schema_version"]
               and doc.get("schema_version") == R.REPORT_SCHEMA
               and doc["report"]["dossiers"] == dossiers)
        record("AC-AMFL7", ok7,
               "schema=%d keys=%d same=%s heads=%s env=%s"
               % (R.REPORT_SCHEMA, len(R.DOSSIER_KEYS), same, heads,
                  sorted(doc)))

        # -- AC-AMFL8 delivery hygiene --------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            runner = handle.read()
        with open(os.path.join(BASE, "apimarket.py"), "rb") as handle:
            src = handle.read()
        ok8 = ("ledger-apimarket-feedlisting" in runner
               and sha_file(cfg_path) == cfg_sha
               and sha_file(lobby_cfg_path) == lobby_sha
               and b"\r" not in src
               and all(byte < 128 for byte in src))
        record("AC-AMFL8", ok8,
               "runner=%s cfgs=%s ascii=%s"
               % ("ledger-apimarket-feedlisting" in runner,
                  sha_file(cfg_path) == cfg_sha,
                  all(byte < 128 for byte in src)))
    finally:
        A._now_utc = original_now
        try:
            am.close()
            dk.close()
            metered.close()
            led.close()
        except Exception:
            pass

    total = len(RESULTS)
    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d %s" % (passed, total,
                             "PASS" if passed == total else "FAIL"),
          flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())