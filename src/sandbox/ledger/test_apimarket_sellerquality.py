"""Acceptance suite for the apimarket seller-side rating quality
scorecard read face (BigDomain R2117; canon = the explore-queue row
claimed in R2117, criteria AC-AMQL1..AC-AMQL8 registered in that claim
note BEFORE this suite existed; the AC-AMQL prefix, the
api_seller_quality name, this suite name, the QUALITY_EMPTY constant,
the quality_risk attention family, the star_distribution key and the
ledger-apimarket-sellerquality runner label were all git-grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Face under proof: APIMarketFace.api_seller_quality. The reputation
surface was scattered across three faces (dev_profile average with no
shape, api_seller_inbox unanswered rows only, api_ratings /
api_rating_replies one listing at a time), so neither a seller nor the
operator could answer "what shape is this reputation, which shelf
drags it, and what share of ratings has a reply". This slot pins the
merge:

  - a twelve-key envelope and a ten-key row, the row set authority the
    listing table (dense, retired shelves included), rows a total order
    on listing_id, market-wide and single-seller modes;
  - distribution conservation: five ordered buckets, bucket sum ==
    rating_count == row sum, replies + unanswered == rating_count and
    the coverage/average arithmetic;
  - the effective-star law: a rating revision moves exactly its own
    units between buckets and never re-derives from the base stamp;
  - the reply law: one reply removes exactly one unanswered row, and
    every per-listing unanswered count matches api_rating_replies;
  - the low-rating law: low_rated_count counts live shelves with at
    least two ratings and an average at or below 2.5, so a retired
    shelf and a single-rating shelf never count;
  - the account gate before any read, fail-closed with frozen table
    digests and unchanged ledger movement;
  - zero row mutations, zero token movement, repeated-call and
    cross-restart byte identity;
  - the consumer proof: every seller block gains a quality key, the
    attention digest grows a quality_risk family and REPORT_SCHEMA
    moves 9 -> 10 additively, so the face is not shipped in the
    no-consumer idle form.

Usage: python test_apimarket_sellerquality.py
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
import apimarket_report as RPT        # noqa: E402 (R2101 consumer)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

ENVELOPE_KEYS = {"dev_account", "seller_count", "listing_count",
                 "rating_count", "reply_count", "unanswered_count",
                 "reply_coverage", "rating_avg", "star_distribution",
                 "low_rated_count", "disclaimer", "rows"}

ROW_KEYS = {"listing_id", "listing_key", "title", "retired",
            "rating_count", "rating_avg", "unanswered_count",
            "reply_count", "lowest_stars", "star_distribution"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")


class Clock(object):
    """Deterministic stamp holder; the module clock is patched in
    main() and restored in the finally block."""

    def __init__(self):
        self.value = "2026-10-25T00:00:00Z"

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


def frozen_digests(am):
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


def pool_balances(led):
    out = {}
    for pool in POOLS:
        out[pool] = led.balance(pool)["balance"]
    return out


def row_of(env, listing_id):
    for row in env["rows"]:
        if row["listing_id"] == listing_id:
            return row
    return None


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


def quality_code(am, dev_account):
    try:
        am.api_seller_quality(dev_account)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """Three sellers, four buyers, eight purchases, eight ratings, one
    reply and one retirement: dana owns d1 (three ratings) and d2 (a
    single-rating shelf); frank owns d3 (two low ratings, live); gina
    owns d4 (two one-star ratings, retired)."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-QL-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-QL-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    dk.issue_key("usr:gina", "gina-key", 10, ["backtest"], False)
    clock.value = "2026-10-05T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-05T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    clock.value = "2026-10-05T00:00:03Z"
    d3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "render charts from data", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-05T00:00:04Z"
    d4 = am.publish_api("usr:gina", "quiet-api", "Quiet API",
                        "a listing that will be retired", PAYLOAD, 7,
                        False)["listing_id"]
    clock.value = "2026-10-05T00:00:10Z"
    am.purchase_api("usr:bob", d1, "BUY-QL-1")
    am.purchase_api("usr:carol", d1, "BUY-QL-2")
    am.purchase_api("usr:dave", d1, "BUY-QL-3")
    am.purchase_api("usr:erin", d2, "BUY-QL-4")
    clock.value = "2026-10-05T00:00:11Z"
    am.purchase_api("usr:bob", d3, "BUY-QL-5")
    am.purchase_api("usr:carol", d3, "BUY-QL-6")
    clock.value = "2026-10-05T00:00:12Z"
    am.purchase_api("usr:dave", d4, "BUY-QL-7")
    am.purchase_api("usr:erin", d4, "BUY-QL-8")
    clock.value = "2026-10-05T00:00:20Z"
    am.rate_api("usr:bob", d1, 5)
    am.rate_api("usr:carol", d1, 4)
    am.rate_api("usr:dave", d1, 2)
    am.rate_api("usr:erin", d2, 5)
    clock.value = "2026-10-05T00:00:21Z"
    am.rate_api("usr:bob", d3, 1)
    am.rate_api("usr:carol", d3, 2)
    am.rate_api("usr:dave", d4, 1)
    am.rate_api("usr:erin", d4, 1)
    return {"d1": d1, "d2": d2, "d3": d3, "d4": d4}


def rating_id_of(am, listing_id, buyer):
    for row in am.api_ratings(listing_id)["ratings"]:
        if row["buyer_id"] == buyer:
            return row["rating_id"]
    return None


def independent_unanswered(am, listing_id):
    """Second, independent derivation of the unanswered count: the
    conversation face read through a separate connection."""
    conn = sqlite3.connect(am.db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM apimarket_ratings r"
            " LEFT JOIN apimarket_rating_replies p"
            " ON p.rating_id = r.rating_id"
            " WHERE r.listing_id = ? AND p.reply_id IS NULL",
            (listing_id,)).fetchone()
    finally:
        conn.close()
    return int(row[0])


def weighted_avg(env):
    dist = env["star_distribution"]
    total = sum(int(k) * dist[k] for k in dist)
    count = sum(dist[k] for k in dist)
    return (float(total) / count if count else 0.0), total, count


def main():
    tmpdir = tempfile.mkdtemp(prefix="amql-")
    db_path = os.path.join(tmpdir, "am.db")
    cfg = RPT.load_configs()[0]
    lobby_cfg = RPT.load_configs()[1]
    led = None
    am = None
    clock = Clock()
    real_now = A._now_utc
    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    try:
        A._now_utc = clock.now_utc
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
        ids = seed_world(led, dk, am, clock)
        # one reply and one retirement land before the first read so
        # both laws are exercised by the shipped state
        dana_bob = rating_id_of(am, ids["d1"], "usr:bob")
        am.reply_to_rating("usr:dana", dana_bob, "thanks for the review")
        am.delist_api("usr:gina", ids["d4"])

        # -- AC-AMQL1 contract, dense row set, both modes -------------
        env = am.api_seller_quality()
        keys_ok = set(env) == ENVELOPE_KEYS
        rows_ok = all(set(r) == ROW_KEYS for r in env["rows"])
        order_ok = [r["listing_id"] for r in env["rows"]] == sorted(
            [r["listing_id"] for r in env["rows"]])
        dense_ok = (env["seller_count"] == 3
                    and env["listing_count"] == 4
                    and sorted(r["listing_id"] for r in env["rows"])
                    == sorted([ids["d1"], ids["d2"], ids["d3"],
                               ids["d4"]]))
        single = am.api_seller_quality("usr:dana")
        single_ok = (single["seller_count"] == 1
                     and single["dev_account"] == "usr:dana"
                     and single["listing_count"] == 2
                     and set(r["listing_id"] for r in single["rows"])
                     == {ids["d1"], ids["d2"]})
        ghost = am.api_seller_quality("usr:nobody")
        ghost_ok = (ghost["seller_count"] == 0
                    and ghost["listing_count"] == 0
                    and ghost["rating_count"] == 0
                    and ghost["rows"] == []
                    and ghost["reply_coverage"] is None
                    and ghost["rating_avg"] == 0.0
                    and ghost["star_distribution"]
                    == {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                    and ghost["low_rated_count"] == 0)
        d4_row = row_of(env, ids["d4"])
        d2_row = row_of(env, ids["d2"])
        retired_ok = (d4_row["retired"] is True
                      and d4_row["rating_count"] == 2
                      and d2_row["retired"] is False
                      and d2_row["rating_count"] == 1)
        ok1 = (keys_ok and rows_ok and order_ok and dense_ok
               and single_ok and ghost_ok and retired_ok
               and env["dev_account"] is None
               and env["disclaimer"] == DISCLAIMER
               and d2_row["lowest_stars"] == 5)
        record("AC-AMQL1", ok1,
               "keys=%r rows=%r order=%r dense=%r single=%r ghost=%r"
               " retired=%r" % (keys_ok, rows_ok, order_ok, dense_ok,
                                single_ok, ghost_ok, retired_ok))

        # -- AC-AMQL2 distribution conservation -----------------------
        ok2 = (list(env["star_distribution"].keys())
               == ["1", "2", "3", "4", "5"])
        buckets_sum = sum(env["star_distribution"].values())
        row_sum = sum(r["rating_count"] for r in env["rows"])
        avg_from_dist, star_total, count_from_dist = weighted_avg(env)
        ok2 = (ok2
               and buckets_sum == env["rating_count"] == row_sum == 8
               and count_from_dist == env["rating_count"]
               and env["star_distribution"]
               == {"1": 3, "2": 2, "3": 0, "4": 1, "5": 2}
               and round(avg_from_dist, 10) == round(env["rating_avg"], 10)
               and env["reply_count"] + env["unanswered_count"]
               == env["rating_count"]
               and env["reply_count"] == 1
               and env["reply_coverage"] == round(1.0 / 8.0, 4)
               and all(sum(r["star_distribution"].values())
                       == r["rating_count"] for r in env["rows"]))
        record("AC-AMQL2", ok2,
               "buckets=%r sum=%d rows=%d avg=%r coverage=%r"
               % (env["star_distribution"], buckets_sum, row_sum,
                  env["rating_avg"], env["reply_coverage"]))

        # -- AC-AMQL3 effective-star law ------------------------------
        before = am.api_seller_quality("usr:dana")
        bob_rating = rating_id_of(am, ids["d1"], "usr:bob")
        carol_rating = rating_id_of(am, ids["d1"], "usr:carol")
        base_stamp = sqlite3.connect(am.db_path).execute(
            "SELECT stars FROM apimarket_ratings WHERE rating_id = ?",
            (bob_rating,)).fetchone()[0]
        am.revise_rating("usr:bob", bob_rating, 1)
        am.revise_rating("usr:carol", carol_rating, 2)
        after = am.api_seller_quality("usr:dana")
        delta = dict((k, after["star_distribution"][k]
                      - before["star_distribution"][k])
                     for k in after["star_distribution"])
        d1_after = row_of(after, ids["d1"])
        stamp_same = sqlite3.connect(am.db_path).execute(
            "SELECT stars FROM apimarket_ratings WHERE rating_id = ?",
            (bob_rating,)).fetchone()[0] == base_stamp
        ok3 = (delta == {"1": 1, "2": 1, "3": 0, "4": -1, "5": -1}
               and after["rating_count"] == before["rating_count"]
               and d1_after["star_distribution"]
               == {"1": 1, "2": 2, "3": 0, "4": 0, "5": 0}
               and round(d1_after["rating_avg"], 10)
               == round(5.0 / 3.0, 10)
               and d1_after["lowest_stars"] == 1
               and stamp_same)
        record("AC-AMQL3", ok3,
               "delta=%r count=%d d1=%r avg=%r stamp_same=%r"
               % (delta, after["rating_count"],
                  d1_after["star_distribution"], d1_after["rating_avg"],
                  stamp_same))

        # -- AC-AMQL4 reply law --------------------------------------
        before_reply = am.api_seller_quality("usr:dana")
        d1_before = row_of(before_reply, ids["d1"])
        am.reply_to_rating("usr:dana", carol_rating, "fixed in the sync")
        after_reply = am.api_seller_quality("usr:dana")
        d1_after_reply = row_of(after_reply, ids["d1"])
        per_row_ok = True
        for row in after_reply["rows"]:
            per_row_ok = (per_row_ok
                          and row["unanswered_count"]
                          == independent_unanswered(am, row["listing_id"]))
        conversations = am.api_rating_replies(ids["d1"])
        face_unanswered = sum(1 for r in conversations["rows"]
                              if r["reply"] is None)
        ok4 = (d1_before["unanswered_count"] == 2
               and d1_after_reply["unanswered_count"] == 1
               and d1_after_reply["reply_count"] == 2
               and after_reply["unanswered_count"]
               == before_reply["unanswered_count"] - 1
               and after_reply["reply_count"]
               == before_reply["reply_count"] + 1
               and after_reply["reply_coverage"]
               == round(2.0 / 4.0, 4)
               and per_row_ok
               and face_unanswered == d1_after_reply["unanswered_count"]
               and conversations["reply_count"] == 2)
        record("AC-AMQL4", ok4,
               "d1_unanswered=%d->%d reply=%d coverage=%r per_row=%r"
               % (d1_before["unanswered_count"],
                  d1_after_reply["unanswered_count"],
                  d1_after_reply["reply_count"],
                  after_reply["reply_coverage"], per_row_ok))

        # -- AC-AMQL5 low-rating law ---------------------------------
        world = am.api_seller_quality()
        dana_world = am.api_seller_quality("usr:dana")
        gina_world = am.api_seller_quality("usr:gina")
        frank_world = am.api_seller_quality("usr:frank")
        live_low = [(r["listing_id"], r["rating_count"],
                     round(r["rating_avg"], 4))
                    for r in world["rows"]
                    if not r["retired"] and r["rating_count"] >= 2
                    and r["rating_avg"] <= 2.5]
        ok5 = (world["low_rated_count"] == 2
               and sorted(x[0] for x in live_low) == sorted(
                   [ids["d1"], ids["d3"]])
               and dana_world["low_rated_count"] == 1
               and frank_world["low_rated_count"] == 1
               and gina_world["low_rated_count"] == 0
               and row_of(gina_world, ids["d4"])["rating_count"] == 2
               and row_of(gina_world, ids["d4"])["retired"] is True
               and row_of(dana_world, ids["d2"])["rating_count"] == 1)
        record("AC-AMQL5", ok5,
               "market=%d live_low=%r dana=%d frank=%d gina=%d"
               % (world["low_rated_count"], live_low,
                  dana_world["low_rated_count"],
                  frank_world["low_rated_count"],
                  gina_world["low_rated_count"]))

        # -- AC-AMQL6 gate order before any read ---------------------
        digests_before = frozen_digests(am)
        codes = [quality_code(am, bad) for bad in
                 ("dana", "USR:dana", "", 42, True, ["usr:dana"])]
        digests_after = frozen_digests(am)
        empty_prefix = am.api_seller_quality("usr:")
        ok6 = (all(code == A.E_AM_BAD_ACCOUNT for code in codes)
               and digests_before == digests_after
               and empty_prefix["listing_count"] == 0
               and empty_prefix["rows"] == [])
        record("AC-AMQL6", ok6,
               "codes=%r digests_frozen=%r prefix_ok=%r"
               % (codes, digests_before == digests_after,
                  empty_prefix["listing_count"] == 0))

        # -- AC-AMQL7 pure read, repeat and cross-restart identity ----
        tx_before = ledger_tx_ids(led)
        pools_before = pool_balances(led)
        digests_before = frozen_digests(am)
        first = dumps(am.api_seller_quality())
        second = dumps(am.api_seller_quality())
        digests_after = frozen_digests(am)
        tx_after = ledger_tx_ids(led)
        pools_after = pool_balances(led)
        close_stack(am, dk, metered, led)
        led, metered, dk, gate, am = build_stack(db_path, cfg,
                                                 lobby_cfg)
        third = dumps(am.api_seller_quality())
        ok7 = (first == second == third
               and tx_before == tx_after
               and pools_before == pools_after
               and digests_before == digests_after)
        record("AC-AMQL7", ok7,
               "repeat=%r restart=%r tx_frozen=%r pools_frozen=%r"
               " digests_frozen=%r"
               % (first == second, first == third,
                  tx_before == tx_after, pools_before == pools_after,
                  digests_before == digests_after))

        # -- AC-AMQL8 consumer and delivery --------------------------
        report = RPT.collect(am)
        attention = RPT.collect_attention(am, report)
        block_ok = True
        for dev in report["sellers"]:
            block_ok = (block_ok
                        and dumps(report["sellers"][dev]["quality"])
                        == dumps(am.api_seller_quality(dev)))
        risk = [f for f in attention["findings"]
                if f["kind"] == "quality_risk"]
        expected = sorted(dev for dev in report["sellers"]
                          if any(not r["retired"]
                                 and r["rating_count"] >= 2
                                 and r["rating_avg"] <= 2.5
                                 for r in
                                 am.api_seller_quality(dev)["rows"]))
        risk_ok = (sorted(set(f["subject"] for f in risk)) == expected
                   and len(risk) == 2
                   and all(f["severity"] == "warn" and "rated" in f["detail"]
                           for f in risk))
        payload = RPT.api_report_payload(report)
        # R2117 moves the schema 9 -> 10 additively (the seller quality
        # key and the quality_risk family), so the assertion follows the
        # module constant rather than pinning a literal.
        contract_ok = (RPT.REPORT_SCHEMA >= 10
                       and payload["schema_version"] == RPT.REPORT_SCHEMA
                       and set(payload) == {"schema_version", "report",
                                            "attention"}
                       and set(payload["report"]) == set(report))
        html = RPT.render_html(report)
        html_ok = ("quality_risk" in html
                   and "seller quality" in html
                   and "<th>star_distribution</th>" not in html)
        wired = False
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = '"ledger-apimarket-sellerquality"' in handle.read()
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        shipped_ok = (shas_after[PRODUCT_FILES[2]]
                      == shas_before[PRODUCT_FILES[2]]
                      and shas_after[PRODUCT_FILES[3]]
                      == shas_before[PRODUCT_FILES[3]])
        ok8 = (block_ok and risk_ok and contract_ok and html_ok
               and wired and shipped_ok)
        record("AC-AMQL8", ok8,
               "blocks=%r risk=%r expected=%r contract=%r html=%r"
               " wired=%r shipped=%r"
               % (block_ok, [f["subject"] for f in risk], expected,
                  contract_ok, html_ok, wired, shipped_ok))

        passed = sum(1 for _ac, ok in RESULTS if ok)
        print("\nSUITE %s %d/%d"
              % ("PASS" if passed == len(RESULTS) else "FAIL", passed,
                 len(RESULTS)), flush=True)
        lines = "\n".join("%s %s" % (ac, "PASS" if ok else "FAIL")
                          for ac, ok in RESULTS)
        print("CRITERIA LINE sha16 %s"
              % hashlib.sha256(lines.encode("utf-8")).hexdigest()[:16],
              flush=True)
        return 0 if passed == len(RESULTS) else 1
    finally:
        A._now_utc = real_now
        if am is not None:
            try:
                am.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())