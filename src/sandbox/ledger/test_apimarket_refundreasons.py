"""Acceptance suite for the apimarket refund reason distribution
(BigDomain R2187; canon = the R2178 explore-queue seed row 9/10,
claimed in R2187 with criteria AC-RFR1..AC-RFR8 registered in that
claim note BEFORE this code existed - honesty law; the AC-RFR prefix,
the ledger-apimarket-refundreasons runner label and the top_reason key
were git-grep -F zero-occupancy anchored 2026-10-28 rc=1, while the
api_refund_reasons / test_apimarket_refundreasons / refund_reasons
names were occupied only by the seed row, state/r2178_payload.json and
the export text - disclosed in the claim note).

Face under proof: APIMarketFace.api_refund_reasons. The refund family
answers money, headcount and time, and apimarket_refunds has always
carried a free-text reason, yet nothing aggregated it. This window
pins the distribution:

  - a thirteen-key envelope with eight-key reason rows;
  - a bucket key derived from the stored text by strip()+lower() only
    (case and surrounding whitespace fold, different spellings never
    merge - no stemming, no synonym guessing);
  - an HONEST unlabeled bucket for an empty reason, ordered last no
    matter how large it is and excluded from top_reason;
  - row/envelope/envelope-money conservation and per-row split
    conservation;
  - share and average derived from the rows, None instead of a
    fabricated zero;
  - a total order (-refund_count, -refunded, reason ascending) so two
    equally sized buckets never swap between calls;
  - cross-face identity with api_market_stats and the raw tables, one
    step of freshness on a new refund, and no effect from retirement;
  - a pure read with no arguments, zero row mutations, zero token
    movement, cross-restart byte identity and runner wiring.

Usage: python test_apimarket_refundreasons.py
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
import apimarket as A                 # noqa: E402 (R2187 face)
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

ENVELOPE_KEYS = {"purchase_count", "refund_count", "refund_rate",
                 "labeled_count", "unlabeled_count", "reason_count",
                 "refunded_total", "avg_refunded", "top_reason",
                 "top_reason_count", "top_reason_share", "by_reason",
                 "disclaimer"}
ROW_KEYS = {"reason", "refund_count", "refunded", "dev_share",
            "platform_share", "share", "avg_amount"}

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


def raw_refunds(am):
    """Ground truth straight from the tables: (purchase_count, rows)
    where each row is (stored_reason, amount, dev_share,
    platform_share)."""
    conn = sqlite3.connect(am.db_path)
    purchases = int(conn.execute(
        "SELECT COUNT(*) FROM apimarket_purchases").fetchone()[0])
    rows = conn.execute(
        "SELECT reason, amount, dev_share, platform_share"
        " FROM apimarket_refunds ORDER BY refund_id").fetchall()
    conn.close()
    return purchases, [(None if r[0] is None else str(r[0]),
                        int(r[1]), int(r[2]), int(r[3]))
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
    Seven purchases, six refunds with the reason shapes this face has
    to fold, one purchase left unrefunded:

      1. bob   d1 10  "Late Service"        (case fold)
      2. carol d1 10  "late service "       (space fold -> same bucket)
      3. dave  d2  3  "Description mismatch"
      4. erin  d3  5  None                  (unlabeled)
      5. grace d1 10  "   "                 (blank -> unlabeled)
      6. frank d2  3  "refunded by mistake"
      7. henry d3  5  never refunded        (keeps refund_rate honest)

    Expected buckets: late service 2/20, description mismatch 1/3,
    refunded by mistake 1/3, unlabeled 2/15. Total refunded 41."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-RFR-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-RFR-S",
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
    tmp = tempfile.mkdtemp(prefix="apimarket-refundreasons-")
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

    env = am.api_refund_reasons()
    rows = env["by_reason"]
    buckets = {}
    for row in rows:
        buckets[row["reason"]] = row
    unlabeled_rows = [r for r in rows if r["reason"] is None]
    labeled_rows = [r for r in rows if r["reason"] is not None]

    # -- AC-RFR1 envelope and row contract ----------------------------
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and env["disclaimer"] == DISCLAIMER
           and isinstance(env["by_reason"], list))
    record("AC-RFR1", ok1,
           "keys ok=%r row keys ok=%r rows=%d disclaimer ok=%r"
           % (set(env.keys()) == ENVELOPE_KEYS,
              all(set(r.keys()) == ROW_KEYS for r in rows),
              len(rows), env["disclaimer"] == DISCLAIMER))

    # -- AC-RFR2 normalisation law (fold case/space, never merge) -----
    ok2 = ([r["reason"] for r in labeled_rows]
           == ["late service", "description mismatch",
               "refunded by mistake"]
           and len(unlabeled_rows) == 1
           and unlabeled_rows[0]["reason"] is None
           and rows[-1]["reason"] is None
           and buckets["late service"]["refund_count"] == 2
           and buckets["late service"]["refunded"] == 20
           and env["reason_count"] == 4
           and env["labeled_count"] == 4
           and env["unlabeled_count"] == 2
           and env["labeled_count"] + env["unlabeled_count"]
           == env["refund_count"] == 6)
    record("AC-RFR2", ok2,
           "labeled=%r unlabeled last=%r fold 2/20=%r counts"
           " labeled+unlabeled=%d+%d == %d"
           % ([r["reason"] for r in labeled_rows],
              rows[-1]["reason"] is None,
              (buckets["late service"]["refund_count"],
               buckets["late service"]["refunded"]),
              env["labeled_count"], env["unlabeled_count"],
              env["refund_count"]))

    # -- AC-RFR3 conservation against the raw tables ------------------
    raw_purchases, raw = raw_refunds(am)
    raw_count = len(raw)
    raw_total = sum(r[1] for r in raw)
    raw_dev = sum(r[2] for r in raw)
    raw_plat = sum(r[3] for r in raw)
    ok3 = (env["purchase_count"] == raw_purchases == 7
           and env["refund_count"] == raw_count == 6
           and sum(r["refund_count"] for r in rows) == env["refund_count"]
           and sum(r["refunded"] for r in rows)
           == env["refunded_total"] == raw_total == 41
           and sum(r["dev_share"] for r in rows) == raw_dev
           and sum(r["platform_share"] for r in rows) == raw_plat
           and all(r["dev_share"] + r["platform_share"] == r["refunded"]
                   for r in rows)
           and raw_dev + raw_plat == raw_total
           and env["reason_count"] == len(rows))
    record("AC-RFR3", ok3,
           "purchases=%d refunds=%d/%d refunded sum=%d/%d dev+plat"
           " per row ok=%r dev=%d plat=%d total=%d"
           % (env["purchase_count"], env["refund_count"], raw_count,
              env["refunded_total"], raw_total,
              all(r["dev_share"] + r["platform_share"] == r["refunded"]
                  for r in rows), raw_dev, raw_plat, raw_total))

    # -- AC-RFR4 share and average, None never a fake zero ------------
    shares = [r["share"] for r in rows]
    ok4 = (buckets["late service"]["share"] == 0.3333
           and buckets["description mismatch"]["share"] == 0.1667
           and unlabeled_rows[0]["share"] == 0.3333
           and round(sum(shares), 4) == 1.0
           and buckets["late service"]["avg_amount"] == 10.0
           and buckets["description mismatch"]["avg_amount"] == 3.0
           and unlabeled_rows[0]["avg_amount"] == 7.5
           and env["avg_refunded"] == 6.83)
    record("AC-RFR4", ok4,
           "shares=%r share sum=%r avg late=%r unlabeled=%r"
           " envelope avg=%r"
           % (shares, round(sum(shares), 4),
              buckets["late service"]["avg_amount"],
              unlabeled_rows[0]["avg_amount"], env["avg_refunded"]))

    # -- AC-RFR5 total order, unlabeled last whatever its size --------
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
           and tie_a["refund_count"] == tie_b["refund_count"] == 1
           and tie_a["refunded"] == tie_b["refunded"] == 3
           and rows.index(tie_a) < rows.index(tie_b)
           and rows[-1]["refund_count"] == 2
           > rows[1]["refund_count"])
    record("AC-RFR5", ok5,
           "order=%r ties broken by name=%r unlabeled last while"
           " holding %d refunds"
           % ([r["reason"] for r in rows],
              rows.index(tie_a) < rows.index(tie_b),
              rows[-1]["refund_count"]))

    # -- AC-RFR6 top reason over labeled rows only --------------------
    ok6 = (env["top_reason"] == "late service"
           and env["top_reason_count"] == 2
           and env["top_reason_share"] == 0.5
           and round(float(env["top_reason_count"])
                     / env["labeled_count"], 4) == env["top_reason_share"])
    record("AC-RFR6", ok6,
           "top=%r count=%r share=%r over labeled=%d (unlabeled %d"
           " excluded)"
           % (env["top_reason"], env["top_reason_count"],
              env["top_reason_share"], env["labeled_count"],
              env["unlabeled_count"]))

    # -- AC-RFR7 pure read, freshness in one step, cross-face --------
    before = dumps(env)
    frozen_before = frozen_digests(am)
    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)
    clock.value = "2027-12-31T23:59:59Z"
    after_clock = dumps(am.api_refund_reasons())
    clock.value = "2026-09-18T00:00:00Z"
    frozen_after = frozen_digests(am)
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)
    no_args_ok = True
    for call in (lambda: am.api_refund_reasons(1),
                 lambda: am.api_refund_reasons(since_utc="2026-08"),
                 lambda: am.api_refund_reasons(None)):
        try:
            call()
            no_args_ok = False
        except TypeError:
            pass

    stats = am.api_market_stats()
    register = am.api_refund_register()
    delist = am.delist_api("usr:dana", _d1)
    retired = am.api_refund_reasons()
    _buyer, purchase7 = "usr:henry", purchases[6]
    clock.value = "2026-09-19T00:00:00Z"
    am.refund_api("usr:henry", purchase7, "Late Service")
    fresh = am.api_refund_reasons()
    fresh_rows = {r["reason"]: r for r in fresh["by_reason"]}
    ok7 = (before == after_clock and no_args_ok
           and frozen_before == frozen_after
           and tx_before == tx_after and pools_before == pools_after
           and env["refunded_total"] == stats["refunded_tokens"]
           and env["refund_count"] == stats["refund_count"]
           and env["refunded_total"] == register["amount"]
           and env["refund_count"] == register["refund_count"]
           and dumps(retired) == before
           and fresh["refund_count"] == 7
           and fresh["refund_rate"] == 1.0
           and fresh["refunded_total"] == env["refunded_total"] + 5
           and fresh_rows["late service"]["refund_count"] == 3
           and fresh_rows["late service"]["refunded"] == 25
           and fresh["top_reason"] == "late service"
           and fresh["top_reason_count"] == 3)
    record("AC-RFR7", ok7,
           "clock-shift identical=%r args rejected=%r digests frozen"
           "=%r tx frozen=%r pools frozen=%r stats refunds=%d/%d"
           " register refunds=%d/%d retirement no-op=%r fresh"
           " step=%d/%d top=%r"
           % (before == after_clock, no_args_ok,
              frozen_before == frozen_after, tx_before == tx_after,
              pools_before == pools_after, env["refund_count"],
              stats["refund_count"], env["refund_count"],
              register["refund_count"], dumps(retired) == before,
              fresh["refund_count"], fresh["refunded_total"],
              fresh["top_reason"]))

    # -- AC-RFR8 cross-restart, empty world, wiring and hygiene ------
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    two = dumps(am2.api_refund_reasons())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    three = dumps(am3.api_refund_reasons())
    close_stack(am3, dk3, metered3, led3)

    empty_dir = os.path.join(tmp, "empty")
    os.makedirs(empty_dir)
    empty_db = os.path.join(empty_dir, "ledger.db")
    led4, metered4, dk4, gate4, am4 = build_stack(
        empty_db, cfg, lobby_cfg)
    empty = am4.api_refund_reasons()
    close_stack(am4, dk4, metered4, led4)

    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-refundreasons" in handle.read()
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
    ok8 = (dumps(fresh) == two == three
           and set(empty.keys()) == ENVELOPE_KEYS
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["refund_rate"] is None
           and empty["labeled_count"] == 0
           and empty["unlabeled_count"] == 0
           and empty["reason_count"] == 0
           and empty["refunded_total"] == 0
           and empty["avg_refunded"] is None
           and empty["top_reason"] is None
           and empty["top_reason_count"] is None
           and empty["top_reason_share"] is None
           and empty["by_reason"] == []
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside_repo)
    record("AC-RFR8", ok8,
           "three instances identical=%r empty world=%r wired=%r"
           " consumer shas stable=%r ascii=%r net imports=%d"
           " outside repo=%r"
           % (dumps(fresh) == two == three,
              (empty["refund_count"], empty["by_reason"],
               empty["top_reason"]), wired,
              shas_before == shas_after, ascii_ok, len(net_imports),
              outside_repo))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())