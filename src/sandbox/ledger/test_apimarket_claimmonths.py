"""Acceptance suite for the market-wide claim monthly timeline
(BigDomain R2194; canon = the seed 6/10 row in state/queue/explore.md,
criteria AC-MCM1..AC-MCM8 registered in that row BEFORE this suite
existed; test_apimarket_claimmonths and ledger-apimarket-claimmonths
were git grep -F zero-occupancy against HEAD on 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_market_claim_months. The market
could say what is disputed right now (api_claims, three present views)
and how long each leg of a claim took (api_claim_latency), but not how
much after-sales pressure landed in a given month, so "seasonal or
incident" had no answer. This slot pins:

  - the thirteen-key envelope, the nine-key row, month_count ==
    len(months) and the honest empty world;
  - claim-month bucketing on opened_utc with no later movement: the
    refund of an October claim landing in December neither shifts the
    claim nor fabricates a December row;
  - the api_claims status seam (refunded beats withdrawn beats
    answered beats open) partitioning claim_count in every row and in
    the envelope;
  - money on the claim side: claim_amount is price_paid frozen at
    open, refunded_amount is the refund register reached through the
    claim purchase, and a refund with NO claim never appears;
  - conservation, ascending month order, first/last extremes and the
    peak month with its earlier-month tie break;
  - cross-face agreement with api_claims per month and in total;
  - pure read (frozen table digests, constant ledger tx set), three
    identical reads and two full-stack restarts;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_claimmonths.py
"""

import ast
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
import apimarket_report as RPT        # noqa: E402 (config loader)
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

ENVELOPE_KEYS = {"month_count", "months", "claim_count", "open_count",
                 "answered_count", "withdrawn_count", "refunded_count",
                 "claim_amount", "refunded_amount", "first_month",
                 "last_month", "peak_month", "disclaimer"}

ROW_KEYS = {"month", "claim_count", "open_count", "answered_count",
            "withdrawn_count", "refunded_count", "claim_amount",
            "refunded_amount", "avg_claim_amount"}

TABLES = ("apimarket_answer_revisions", "apimarket_answers",
          "apimarket_category_revisions", "apimarket_claim_notes",
          "apimarket_claim_responses", "apimarket_claim_withdrawals",
          "apimarket_claims", "apimarket_delistings",
          "apimarket_listing_revisions", "apimarket_listings",
          "apimarket_price_revisions", "apimarket_provider_revisions",
          "apimarket_providers", "apimarket_purchases",
          "apimarket_questions", "apimarket_rating_replies",
          "apimarket_rating_revisions", "apimarket_ratings",
          "apimarket_refunds", "apimarket_relistings",
          "apimarket_reply_revisions", "apimarket_review_resubmits",
          "apimarket_reviews", "apimarket_supply_revisions",
          "apimarket_unwatchings", "apimarket_watchlist")


class Clock(object):
    """Deterministic stamp holder; the module clock is patched in
    main() and restored in the finally block."""

    def __init__(self):
        self.value = "2026-09-01T00:00:00Z"

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
    """Two claims open in September, two in October, one refund with no
    claim in October, and the refund of an October claim landing in
    December. purchase_api returns the purchase envelope, so the claims
    and refunds address the nested purchase_id."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMCMR-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMCMR-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "gina"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

    clock.value = "2026-09-01T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-09-01T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    clock.value = "2026-09-01T00:00:03Z"
    f1 = am.publish_api("usr:frank", "sync-kit", "Sync Kit API",
                        "collaborative sync kit", PAYLOAD, 5, False)[
                            "listing_id"]

    clock.value = "2026-09-10T00:00:00Z"
    p1 = am.purchase_api("usr:bob", d1, "BUY-CM-1")
    clock.value = "2026-09-11T00:00:00Z"
    p2 = am.purchase_api("usr:carol", d1, "BUY-CM-2")
    clock.value = "2026-09-12T00:00:00Z"
    p3 = am.purchase_api("usr:bob", d2, "BUY-CM-3")
    clock.value = "2026-10-05T00:00:00Z"
    p4 = am.purchase_api("usr:dave", d2, "BUY-CM-4")
    clock.value = "2026-10-08T00:00:00Z"
    p5 = am.purchase_api("usr:carol", f1, "BUY-CM-5")
    p1 = p1["purchase_id"]
    p2 = p2["purchase_id"]
    p3 = p3["purchase_id"]
    p4 = p4["purchase_id"]
    p5 = p5["purchase_id"]

    clock.value = "2026-09-20T00:00:00Z"
    c1 = am.open_claim("usr:bob", p1, "no usable output")["claim_id"]
    clock.value = "2026-09-25T00:00:00Z"
    c2 = am.open_claim("usr:carol", p2, "stale data")["claim_id"]
    clock.value = "2026-09-27T00:00:00Z"
    am.respond_claim("usr:dana", c2, "re-synced the feed")
    clock.value = "2026-10-03T00:00:00Z"
    am.withdraw_claim("usr:carol", c2)
    clock.value = "2026-10-02T00:00:00Z"
    c3 = am.open_claim("usr:bob", p3, "macro values wrong")["claim_id"]
    clock.value = "2026-10-03T00:00:00Z"
    am.respond_claim("usr:dana", c3, "corrected feed")
    clock.value = "2026-10-05T00:00:00Z"
    c4 = am.open_claim("usr:dave", p4, "partial dataset")["claim_id"]
    clock.value = "2026-10-06T00:00:00Z"
    am.respond_claim("usr:dana", c4, "full dataset attached")

    # A refund with NO claim: must not appear on the claim face.
    clock.value = "2026-10-09T00:00:00Z"
    am.refund_api("usr:carol", p5, "changed my mind")
    # The October claim's refund lands two months later: the claim must
    # stay in October and December must not become a row.
    clock.value = "2026-12-01T00:00:00Z"
    am.refund_api("usr:bob", p3, "claim settled by refund")

    return {"d1": d1, "d2": d2, "f1": f1, "p1": p1, "p2": p2, "p3": p3,
            "p4": p4, "p5": p5, "c1": c1, "c2": c2, "c3": c3, "c4": c4}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amcm-")
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

        # -- AC-MCM1 contract and the honest empty world ---------------
        empty = am.api_market_claim_months()
        ok1a = (set(empty) == ENVELOPE_KEYS
                and empty["month_count"] == 0
                and empty["months"] == []
                and empty["claim_count"] == 0
                and empty["open_count"] == 0
                and empty["answered_count"] == 0
                and empty["withdrawn_count"] == 0
                and empty["refunded_count"] == 0
                and empty["claim_amount"] == 0
                and empty["refunded_amount"] == 0
                and empty["first_month"] is None
                and empty["last_month"] is None
                and empty["peak_month"] is None
                and empty["disclaimer"] == DISCLAIMER)
        ids = seed_world(led, dk, am, clock)
        env = am.api_market_claim_months()
        ok1b = (set(env) == ENVELOPE_KEYS
                and env["month_count"] == len(env["months"]) == 2
                and all(set(row) == ROW_KEYS for row in env["months"]))
        record("AC-MCM1", ok1a and ok1b,
               "empty_ok=%r env_ok=%r months=%r"
               % (ok1a, ok1b, [r["month"] for r in env["months"]]))

        # -- AC-MCM2 opened-month bucketing, no later movement ---------
        months = {r["month"]: r for r in env["months"]}
        sept = months.get("2026-09")
        octo = months.get("2026-10")
        ok2 = (sept is not None and octo is not None
               and "2026-12" not in months
               and sept["claim_count"] == 2
               and octo["claim_count"] == 2
               and sorted(months) == ["2026-09", "2026-10"])
        record("AC-MCM2", ok2,
               "months=%r sept=%r octo=%r"
               % (sorted(months),
                  sept and sept["claim_count"],
                  octo and octo["claim_count"]))

        # -- AC-MCM3 status partition by the api_claims seam -----------
        part_ok = True
        for row in env["months"]:
            part_ok = part_ok and (row["open_count"]
                                   + row["answered_count"]
                                   + row["withdrawn_count"]
                                   + row["refunded_count"]
                                   == row["claim_count"])
        ok3 = (part_ok
               and sept["open_count"] == 1
               and sept["withdrawn_count"] == 1
               and sept["answered_count"] == 0
               and sept["refunded_count"] == 0
               and octo["answered_count"] == 1
               and octo["refunded_count"] == 1
               and octo["open_count"] == 0
               and octo["withdrawn_count"] == 0
               and env["claim_count"] == 4)
        record("AC-MCM3", ok3,
               "partition=%r sept=%r octo=%r"
               % (part_ok,
                  [sept["open_count"], sept["answered_count"],
                   sept["withdrawn_count"], sept["refunded_count"]],
                  [octo["open_count"], octo["answered_count"],
                   octo["withdrawn_count"], octo["refunded_count"]]))

        # -- AC-MCM4 money on the claim side ---------------------------
        ok4 = (sept["claim_amount"] == 20
               and sept["refunded_amount"] == 0
               and octo["claim_amount"] == 6
               and octo["refunded_amount"] == 3
               and env["claim_amount"] == 26
               and env["refunded_amount"] == 3
               and sept["avg_claim_amount"] == 10.0
               and octo["avg_claim_amount"] == 3.0)
        record("AC-MCM4", ok4,
               "claim_amount=%r refunded_amount=%r"
               " (the claim-less refund of 5 is excluded) avg=%r"
               % (env["claim_amount"], env["refunded_amount"],
                  [sept["avg_claim_amount"], octo["avg_claim_amount"]]))

        # -- AC-MCM5 conservation, order and the peak tie break --------
        totals_ok = (env["claim_count"] == sum(
            r["claim_count"] for r in env["months"])
            and env["open_count"] == sum(
                r["open_count"] for r in env["months"])
            and env["answered_count"] == sum(
                r["answered_count"] for r in env["months"])
            and env["withdrawn_count"] == sum(
                r["withdrawn_count"] for r in env["months"])
            and env["refunded_count"] == sum(
                r["refunded_count"] for r in env["months"])
            and env["claim_amount"] == sum(
                r["claim_amount"] for r in env["months"])
            and env["refunded_amount"] == sum(
                r["refunded_amount"] for r in env["months"]))
        ok5 = (totals_ok
               and env["first_month"] == "2026-09"
               and env["last_month"] == "2026-10"
               and env["peak_month"] == "2026-09")
        record("AC-MCM5", ok5,
               "totals=%r first=%r last=%r peak=%r (2 vs 2 tie ->"
               " earlier month)"
               % (totals_ok, env["first_month"], env["last_month"],
                  env["peak_month"]))

        # -- AC-MCM6 cross-face agreement with api_claims --------------
        claims = am.api_claims()
        agg = {}
        for row in claims["claims"]:
            month = str(row["opened_utc"])[:7]
            b = agg.setdefault(month, {"claim_count": 0, "open": 0,
                                       "answered": 0, "withdrawn": 0,
                                       "refunded": 0, "money": 0})
            b["claim_count"] += 1
            b[row["status"]] += 1
            b["money"] += int(row["price_paid"])
        agree = True
        for row in env["months"]:
            b = agg.get(row["month"], {})
            agree = agree and (
                b.get("claim_count") == row["claim_count"]
                and b.get("open") == row["open_count"]
                and b.get("answered") == row["answered_count"]
                and b.get("withdrawn") == row["withdrawn_count"]
                and b.get("refunded") == row["refunded_count"]
                and b.get("money") == row["claim_amount"])
        agree = agree and (sum(b["claim_count"] for b in agg.values())
                           == env["claim_count"])
        record("AC-MCM6", agree,
               "claims_rows=%d face_rows=%d agree=%r"
               % (len(claims["claims"]), env["claim_count"], agree))

        # -- AC-MCM7 pure read and cross-restart identity --------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        runs = [dumps(am.api_market_claim_months()),
                dumps(am.api_market_claim_months()),
                dumps(am.api_market_claim_months())]
        digests_after = frozen_digests(am)
        pure_ok = (runs[0] == runs[1] == runs[2]
                   and digests_before == digests_after
                   and tx_before == ledger_tx_ids(led))
        baseline = dumps(am.api_market_claim_months())
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_market_claim_months()))
            close_stack(am2, dk2, metered2, led2)
        ok7 = pure_ok and replays[0] == baseline == replays[1]
        record("AC-MCM7", ok7,
               "pure=%r restart_a=%r restart_b=%r"
               % (pure_ok, replays[0] == baseline,
                  replays[1] == baseline))

        # -- AC-MCM8 delivery hygiene ----------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-claimmonths"' in handle.read())
        with open(os.path.abspath(__file__), "rb") as handle:
            own = handle.read()
        ascii_ok = True
        try:
            own.decode("ascii")
        except UnicodeDecodeError:
            ascii_ok = False
        net_marks = {"requests", "urllib", "socket", "http", "ftplib",
                     "smtplib", "telnetlib"}
        mods = set()
        for node in ast.walk(ast.parse(own)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        net_ok = not (mods & net_marks)
        outside_ok = not os.path.abspath(db_path).startswith(
            os.path.join(os.path.dirname(BASE), ""))
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        shipped_ok = (shas_after[PRODUCT_FILES[2]]
                      == shas_before[PRODUCT_FILES[2]]
                      and shas_after[PRODUCT_FILES[3]]
                      == shas_before[PRODUCT_FILES[3]])
        ok8 = (wired and ascii_ok and net_ok and shipped_ok and outside_ok)
        record("AC-MCM8", ok8,
               "wired=%r ascii=%r no_net=%r shipped=%r outside=%r"
               % (wired, ascii_ok, net_ok, shipped_ok, outside_ok))

        passed = sum(1 for _ac, ok in RESULTS if ok)
        print("\nSUITE %s %d/%d"
              % ("PASS" if passed == len(RESULTS) else "FAIL", passed,
                 len(RESULTS)), flush=True)
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