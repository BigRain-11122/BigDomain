"""Acceptance suite for the seller-side refund reason structure
(BigDomain R2190; canon = the R2189 explore-queue seed row 1/10,
claimed in R2190 with criteria AC-SRR1..AC-SRR8 registered in that
claim note BEFORE this code existed - honesty law; the
test_apimarket_sellerrefundreasons / ledger-apimarket-sellerrefundreasons
/ market_refund_share / reason_herfindahl names were git-grep -F
zero-occupancy anchored 2026-10-28 rc=1, while AC-SRR and
api_seller_refund_reasons were occupied only by the seed row text and
the market face's own by_reason / top_reason keys stay untouched).

Face under proof: APIMarketFace.api_seller_refund_reasons. The market
face already aggregates the reason text, but a seller could not read
"what are MY refunds caused by", so a description mismatch and a
service break were indistinguishable on the seller's own ledger. This
window pins the seller scope:

  - a seventeen-key envelope with eight-key reason rows;
  - the same narrow bucket law (strip()+lower(), no stemming, no
    synonym merging) and the same HONEST unlabeled bucket, pinned
    last and excluded from top_reason while still counting as one
    bucket of the concentration measure;
  - attribution by the stored dev_account, so another seller's
    refunds never enter the envelope;
  - conservation against the scoped raw tables (count, amount, split,
    and the seller's own purchase denominator);
  - share / average / top share derived from the rows, None instead
    of a fabricated zero, herfindahl from exact fractions;
  - market benchmarks on a seller scope and None on the market scope
    (the face never benchmarks itself against itself);
  - a pure read, cross-restart byte identity, one step of freshness
    on a new refund, and runner wiring.

Usage: python test_apimarket_sellerrefundreasons.py
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
import apimarket as A                 # noqa: E402 (R2190 face)
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

ENVELOPE_KEYS = {"scope", "dev_account", "purchase_count",
                 "refund_count", "refund_rate", "refunded_total",
                 "labeled_count", "unlabeled_count", "reason_count",
                 "top_reason", "top_reason_count", "top_reason_share",
                 "reason_herfindahl", "market_refund_rate",
                 "market_refund_share", "rows", "disclaimer"}
ROW_KEYS = {"reason", "refund_count", "refunded", "dev_share",
            "platform_share", "share", "avg_amount", "listing_count"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")


class Clock(object):
    """Deterministic stamp holder (module clock patched, restored in
    main's finally block)."""

    def __init__(self):
        self.value = "2026-08-01T10:00:00Z"

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
    return {pool: led.balance(pool) for pool in POOLS}


def raw_refunds(am, dev_account=None):
    """Ground truth straight from the scoped tables: (purchase_count,
    rows) where each row is (stored_reason, amount, dev_share,
    platform_share, listing_id)."""
    conn = sqlite3.connect(am.db_path)
    if dev_account is None:
        purchases = int(conn.execute(
            "SELECT COUNT(*) FROM apimarket_purchases").fetchone()[0])
        rows = conn.execute(
            "SELECT reason, amount, dev_share, platform_share,"
            " listing_id FROM apimarket_refunds"
            " ORDER BY refund_id").fetchall()
    else:
        purchases = int(conn.execute(
            "SELECT COUNT(*) FROM apimarket_purchases p"
            " JOIN apimarket_listings l"
            " ON l.listing_id = p.listing_id"
            " WHERE l.dev_account = ?", (dev_account,)).fetchone()[0])
        rows = conn.execute(
            "SELECT reason, amount, dev_share, platform_share,"
            " listing_id FROM apimarket_refunds"
            " WHERE dev_account = ? ORDER BY refund_id",
            (dev_account,)).fetchall()
    conn.close()
    return purchases, [(None if r[0] is None else str(r[0]),
                        int(r[1]), int(r[2]), int(r[3]), int(r[4]))
                       for r in rows]


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


def seed_world(led, dk, am, clock):
    """Owner dana (d1 price 10, d2 price 3) and frank (d3 price 5).
    Seven purchases, six refunds, one purchase left unrefunded.

    dana's own ledger (five purchases, five refunds, 36 refunded):
      1. bob   d1 10  "Late Service"          (case fold)
      2. carol d1 10  "late service "         (space fold -> same)
      3. dave  d2  3  "Description mismatch"
      4. grace d1 10  "   "                   (blank -> unlabeled)
      5. frank d2  3  "refunded by mistake"
    frank's own ledger (two purchases, one refund, 5 refunded):
      6. erin  d3  5  None                    (unlabeled only)
      7. henry d3  5  never refunded          (keeps his rate honest)

    Dana buckets: late service 2/20, description mismatch 1/3,
    refunded by mistake 1/3, unlabeled 1/10; herfindahl 3200.0.
    Frank: one unlabeled bucket 1/5 -> herfindahl 10000.0.
    Market: six refunds / 41 refunded, two unlabeled, herfindahl
    2777.78."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-SRR-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-SRR-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "grace", "frank",
                "henry"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    d3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 5,
                        False)["listing_id"]
    clock.value = "2026-08-01T10:00:00Z"
    p1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")["purchase_id"]
    clock.value = "2026-08-02T10:00:00Z"
    p2 = am.purchase_api("usr:carol", d1, "ref-carol-d1")["purchase_id"]
    clock.value = "2026-08-03T00:00:00Z"
    p3 = am.purchase_api("usr:dave", d2, "ref-dave-d2")["purchase_id"]
    clock.value = "2026-09-01T00:00:00Z"
    p4 = am.purchase_api("usr:erin", d3, "ref-erin-d3")["purchase_id"]
    clock.value = "2026-09-15T00:00:00Z"
    p5 = am.purchase_api("usr:grace", d1, "ref-grace-d1")["purchase_id"]
    clock.value = "2026-09-16T00:00:00Z"
    p6 = am.purchase_api("usr:frank", d2, "ref-frank-d2")["purchase_id"]
    clock.value = "2026-09-17T00:00:00Z"
    p7 = am.purchase_api("usr:henry", d3, "ref-henry-d3")["purchase_id"]
    clock.value = "2026-08-05T10:00:00Z"
    am.refund_api("usr:bob", p1, "Late Service")
    am.refund_api("usr:carol", p2, "late service ")
    am.refund_api("usr:dave", p3, "Description mismatch")
    am.refund_api("usr:erin", p4, None)
    am.refund_api("usr:grace", p5, "   ")
    am.refund_api("usr:frank", p6, "refunded by mistake")
    return d1, d2, d3, (p1, p2, p3, p4, p5, p6, p7)


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerrefundreasons-")
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
        return run(db_path, cfg, lobby_cfg, tmp, shas_before, clock)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, tmp, shas_before, clock):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    _d1, _d2, _d3, purchases = seed_world(led, dk, am, clock)

    env = am.api_seller_refund_reasons("usr:dana")
    rows = env["rows"]
    buckets = {}
    for row in rows:
        buckets[row["reason"]] = row
    unlabeled_rows = [r for r in rows if r["reason"] is None]
    labeled_rows = [r for r in rows if r["reason"] is not None]
    market = am.api_seller_refund_reasons()
    frank = am.api_seller_refund_reasons("usr:frank")
    bare = am.api_seller_refund_reasons("usr:")

    # -- AC-SRR1 envelope and row contract ----------------------------
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and env["disclaimer"] == DISCLAIMER
           and isinstance(env["rows"], list)
           and env["scope"] == "seller"
           and env["dev_account"] == "usr:dana"
           and market["scope"] == "market"
           and market["dev_account"] is None
           and set(market.keys()) == ENVELOPE_KEYS
           and bare["scope"] == "seller"
           and bare["refund_count"] == 0
           and bare["rows"] == []
           and bare["reason_herfindahl"] is None)
    record("AC-SRR1", ok1,
           "keys ok=%r row keys ok=%r rows=%d scope=%r/%r bare"
           " refunds=%d bare rows=%r"
           % (set(env.keys()) == ENVELOPE_KEYS,
              all(set(r.keys()) == ROW_KEYS for r in rows),
              len(rows), env["scope"], market["scope"],
              bare["refund_count"], bare["rows"]))

    # -- AC-SRR2 bucket law and seller attribution -------------------
    ok2 = ([r["reason"] for r in labeled_rows]
           == ["late service", "description mismatch",
               "refunded by mistake"]
           and len(unlabeled_rows) == 1
           and unlabeled_rows[0]["reason"] is None
           and rows[-1]["reason"] is None
           and buckets["late service"]["refund_count"] == 2
           and buckets["late service"]["refunded"] == 20
           and buckets["late service"]["listing_count"] == 1
           and unlabeled_rows[0]["refunded"] == 10
           and env["reason_count"] == 4
           and env["labeled_count"] == 4
           and env["unlabeled_count"] == 1
           and env["refund_count"] == 5
           and frank["refund_count"] == 1
           and [r["reason"] for r in frank["rows"]] == [None]
           and frank["labeled_count"] == 0
           and frank["unlabeled_count"] == 1)
    record("AC-SRR2", ok2,
           "labeled=%r unlabeled last=%r late bucket=%r frank"
           " refunds=%d buckets=%r"
           % ([r["reason"] for r in labeled_rows],
              rows[-1]["reason"] is None,
              (buckets["late service"]["refund_count"],
               buckets["late service"]["refunded"],
               buckets["late service"]["listing_count"]),
              frank["refund_count"],
              [r["reason"] for r in frank["rows"]]))

    # -- AC-SRR3 conservation against the scoped raw tables ----------
    raw_purchases, raw = raw_refunds(am, "usr:dana")
    raw_count = len(raw)
    raw_total = sum(r[1] for r in raw)
    raw_dev = sum(r[2] for r in raw)
    raw_plat = sum(r[3] for r in raw)
    ok3 = (env["purchase_count"] == raw_purchases == 5
           and env["refund_count"] == raw_count == 5
           and sum(r["refund_count"] for r in rows)
           == env["refund_count"]
           and sum(r["refunded"] for r in rows)
           == env["refunded_total"] == raw_total == 36
           and sum(r["dev_share"] for r in rows) == raw_dev
           and sum(r["platform_share"] for r in rows) == raw_plat
           and all(r["dev_share"] + r["platform_share"] == r["refunded"]
                   for r in rows)
           and raw_dev + raw_plat == raw_total
           and env["labeled_count"] + env["unlabeled_count"]
           == env["refund_count"]
           and env["refund_rate"] == 1.0
           and env["reason_count"] == len(rows))
    record("AC-SRR3", ok3,
           "purchases=%d refunds=%d/%d refunded sum=%d/%d splits"
           " ok=%r dev=%d plat=%d total=%d rate=%r"
           % (env["purchase_count"], env["refund_count"], raw_count,
              env["refunded_total"], raw_total,
              all(r["dev_share"] + r["platform_share"] == r["refunded"]
                  for r in rows), raw_dev, raw_plat, raw_total,
              env["refund_rate"]))

    # -- AC-SRR4 share, average and top share ------------------------
    shares = [r["share"] for r in rows]
    ok4 = (buckets["late service"]["share"] == 0.4
           and buckets["description mismatch"]["share"] == 0.2
           and buckets["refunded by mistake"]["share"] == 0.2
           and unlabeled_rows[0]["share"] == 0.2
           and round(sum(shares), 4) == 1.0
           and buckets["late service"]["avg_amount"] == 10.0
           and buckets["description mismatch"]["avg_amount"] == 3.0
           and unlabeled_rows[0]["avg_amount"] == 10.0
           and env["top_reason"] == "late service"
           and env["top_reason_count"] == 2
           and env["top_reason_share"] == 0.5
           and round(float(env["top_reason_count"])
                     / env["labeled_count"], 4)
           == env["top_reason_share"]
           and frank["top_reason"] is None
           and frank["top_reason_count"] is None
           and frank["top_reason_share"] is None
           and frank["rows"][0]["share"] == 1.0
           and frank["rows"][0]["avg_amount"] == 5.0)
    record("AC-SRR4", ok4,
           "shares=%r sum=%r avg late=%r unlabeled=%r top=%r/%r/%r"
           " frank top=%r"
           % (shares, round(sum(shares), 4),
              buckets["late service"]["avg_amount"],
              unlabeled_rows[0]["avg_amount"], env["top_reason"],
              env["top_reason_count"], env["top_reason_share"],
              frank["top_reason"]))

    # -- AC-SRR5 order and concentration -----------------------------
    def order_key(row):
        return (1 if row["reason"] is None else 0,
                -row["refund_count"], -row["refunded"],
                row["reason"] or "")

    ordered = sorted(rows, key=order_key)
    tie_a = buckets["description mismatch"]
    tie_b = buckets["refunded by mistake"]
    ok5 = ([r["reason"] for r in rows]
           == ["late service", "description mismatch",
               "refunded by mistake", None]
           and [r["reason"] for r in rows]
           == [r["reason"] for r in ordered]
           and rows.index(tie_a) < rows.index(tie_b)
           and env["reason_herfindahl"] == 2800.0
           and frank["reason_herfindahl"] == 10000.0
           and market["reason_herfindahl"] == 2777.78)
    record("AC-SRR5", ok5,
           "order=%r tie by name=%r herfindahl dana=%r frank=%r"
           " market=%r"
           % ([r["reason"] for r in rows],
              rows.index(tie_a) < rows.index(tie_b),
              env["reason_herfindahl"], frank["reason_herfindahl"],
              market["reason_herfindahl"]))

    # -- AC-SRR6 market benchmark and seller isolation ---------------
    dana_only = buckets["late service"]["refund_count"] == 2
    ok6 = (market["market_refund_rate"] is None
           and market["market_refund_share"] is None
           and market["refund_count"] == 6
           and market["refunded_total"] == 41
           and market["labeled_count"] == 4
           and market["unlabeled_count"] == 2
           and market["top_reason_share"] == 0.5
           and env["market_refund_rate"] == 0.8571
           and env["market_refund_share"] == 0.878
           and frank["market_refund_rate"] == 0.8571
           and frank["market_refund_share"] == 0.122
           and frank["refund_rate"] == 0.5
           and dana_only)
    record("AC-SRR6", ok6,
           "market benchmarks none=%r/%r market refunds=%d/%d"
           " seller rate=%r share=%r frank=%r/%r isolated=%r"
           % (market["market_refund_rate"] is None,
              market["market_refund_share"] is None,
              market["refund_count"], market["refunded_total"],
              env["market_refund_rate"], env["market_refund_share"],
              frank["market_refund_rate"],
              frank["market_refund_share"], dana_only))

    # -- AC-SRR7 pure read, determinism and freshness in one step ----
    before = dumps(env)
    frozen_before = frozen_digests(am)
    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)
    clock.value = "2027-12-31T23:59:59Z"
    after_clock = dumps(am.api_seller_refund_reasons("usr:dana"))
    clock.value = "2026-09-18T00:00:00Z"
    frozen_after = frozen_digests(am)
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)

    quality = am.api_refund_register(dev_account="usr:dana")
    market_face = am.api_refund_reasons()
    delist = am.delist_api("usr:dana", _d1)
    retired = am.api_seller_refund_reasons("usr:dana")
    clock.value = "2026-09-19T00:00:00Z"
    am.refund_api("usr:henry", purchases[6], "Late Service")
    fresh = am.api_seller_refund_reasons("usr:dana")
    fresh_frank = am.api_seller_refund_reasons("usr:frank")
    fresh_market = am.api_seller_refund_reasons()
    base = json.loads(before)
    ok7 = (before == after_clock
           and frozen_before == frozen_after
           and tx_before == tx_after and pools_before == pools_after
           and env["refund_count"] == quality["refund_count"]
           and env["refunded_total"]
           == market_face["refunded_total"] - frank["refunded_total"]
           and dumps(retired) == before
           and fresh["rows"] == base["rows"]
           and fresh["refund_count"] == base["refund_count"]
           and fresh["refunded_total"] == base["refunded_total"]
           and fresh["top_reason"] == base["top_reason"]
           and fresh["reason_herfindahl"]
           == base["reason_herfindahl"]
           and fresh["market_refund_rate"] == 1.0
           and fresh["market_refund_share"] == 0.7826
           and fresh_frank["refund_count"] == 2
           and fresh_frank["refunded_total"] == 10
           and fresh_frank["top_reason"] == "late service"
           and fresh_frank["top_reason_count"] == 1
           and fresh_market["refund_count"] == 7
           and fresh_market["refunded_total"] == 46)
    record("AC-SRR7", ok7,
           "clock-shift identical=%r digests frozen=%r tx frozen=%r"
           " pools frozen=%r dana quality refunds=%d/%d market"
           " identity ok=%r retirement no-op=%r dana rows stable=%r"
           " benchmark moved to %r/%r frank step=%d/%d/%r"
           " market=%d/%d"
           % (before == after_clock, frozen_before == frozen_after,
              tx_before == tx_after, pools_before == pools_after,
              env["refund_count"], quality["refund_count"],
              env["refunded_total"]
              == market_face["refunded_total"]
              - frank["refunded_total"],
              dumps(retired) == before, fresh["rows"] == base["rows"],
              fresh["market_refund_rate"],
              fresh["market_refund_share"],
              fresh_frank["refund_count"],
              fresh_frank["refunded_total"],
              fresh_frank["top_reason"],
              fresh_market["refund_count"],
              fresh_market["refunded_total"]))

    # -- AC-SRR8 gates, cross-restart, empty world and wiring --------
    bad_forms = ("", "dana", 123, "USR:dana", " usr:dana")
    gate_ok = True
    gate_seen = []
    for form in bad_forms:
        try:
            am.api_seller_refund_reasons(form)
            gate_ok = False
            gate_seen.append((form, "ACCEPTED"))
        except A.ApiMarketError as exc:
            gate_seen.append((form, exc.code))
            if exc.code != A.E_AM_BAD_ACCOUNT:
                gate_ok = False

    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    two = dumps(am2.api_seller_refund_reasons("usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    three = dumps(am3.api_seller_refund_reasons("usr:dana"))
    close_stack(am3, dk3, metered3, led3)

    empty_dir = os.path.join(tmp, "empty")
    os.makedirs(empty_dir)
    empty_db = os.path.join(empty_dir, "ledger.db")
    led4, metered4, dk4, gate4, am4 = build_stack(
        empty_db, cfg, lobby_cfg)
    empty = am4.api_seller_refund_reasons("usr:nobody")
    empty_market = am4.api_seller_refund_reasons()
    close_stack(am4, dk4, metered4, led4)

    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-sellerrefundreasons" in handle.read()
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
    ok8 = (gate_ok
           and dumps(fresh) != dumps(retired)
           and two == dumps(fresh) == three
           and set(empty.keys()) == ENVELOPE_KEYS
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["refund_rate"] is None
           and empty["reason_count"] == 0
           and empty["refunded_total"] == 0
           and empty["top_reason"] is None
           and empty["reason_herfindahl"] is None
           and empty["market_refund_rate"] is None
           and empty["market_refund_share"] is None
           and empty["rows"] == []
           and set(empty_market.keys()) == ENVELOPE_KEYS
           and empty_market["refund_count"] == 0
           and empty_market["rows"] == []
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside_repo)
    record("AC-SRR8", ok8,
           "gate forms=%r three instances identical=%r empty=%r"
           " wired=%r consumer shas stable=%r ascii=%r net"
           " imports=%d outside repo=%r"
           % (gate_seen, two == dumps(fresh) == three,
              (empty["refund_count"], empty["rows"],
               empty["reason_herfindahl"]), wired,
              shas_before == shas_after, ascii_ok, len(net_imports),
              outside_repo))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())