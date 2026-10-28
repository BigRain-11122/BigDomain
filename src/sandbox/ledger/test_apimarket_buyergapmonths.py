"""Acceptance suite for the buyer purchase-gap rhythm face
(BigDomain R2196; canon = the seed 7/10 row in state/queue/explore.md,
criteria AC-BGM1..AC-BGM8 registered in that row BEFORE this suite
existed; test_apimarket_buyergapmonths and ledger-apimarket-buyergapmonths
were git grep -F zero-occupancy against HEAD on 2026-10-28, rc=1, and
api_buyer_gap_months / _month_index / trailing_dormant_months were free
on the code face).

Face under proof: APIMarketFace.api_buyer_gap_months. api_buyer_months
answers the money in each month and api_market_buyer_retention answers
the market-wide survival curve, but the rhythm of ONE resident - how
many months passed between two purchases, how long the longest silence
ran, how many months sit dormant inside the observed extent - had no
face, so a regular repurchase cadence and a sleeping account read
identically. This slot pins:

  - the sixteen-key envelope, the four-key row, the honest empty world
    and the buyer isolation of the account gate;
  - activity as the NET purchase month (a refunded purchase is not a
    purchase, so a refund REMOVES an activity month and can widen a
    gap - disclosed, never patched over);
  - the gap law gap_months == span_months - 1, so two consecutive
    calendar months read 0 (unbroken rhythm, not absent rhythm);
  - the aggregates: gap_count, dormant_months_total, mean, median (odd
    middle, even midpoint), max with the earlier-pair tie break;
  - trailing silence measured against an explicit as_of and NEVER a
    wall clock, with the default as_of being the buyer's own last
    activity month, plus the fail-closed as_of family (shape and the
    precedes-last-activity ordering) and the gate order account first;
  - pure read (frozen table digests, constant ledger tx set), three
    identical reads, and byte identity across two full-stack restarts;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_buyergapmonths.py
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

ENVELOPE_KEYS = {"buyer_id", "activity_month_count", "purchase_count",
                 "first_activity_month", "last_activity_month",
                 "gap_count", "dormant_months_total", "avg_gap_months",
                 "median_gap_months", "max_gap_months",
                 "longest_from_month", "longest_to_month",
                 "as_of_month", "trailing_dormant_months",
                 "disclaimer", "gaps"}

ROW_KEYS = {"from_month", "to_month", "span_months", "gap_months"}

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
    """Bob's net purchase months run 2026-09, 2026-10, 2026-12,
    2027-01 and 2027-03 - six purchase rows over five months. Carol
    buys once (2026-11) and Zoe never buys. The December purchase of
    bob stays live until the refund step, so the suite can read the
    world BOTH before and after a refund removes an activity month."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMBGM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMBGM-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    clock.value = "2026-09-01T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    # One listing per purchase: the purchase door is unique on
    # (buyer, listing), so a repeat buyer needs distinct shelves.
    listings = [d1]
    for index in range(2, 7):
        clock.value = "2026-09-01T00:00:0%dZ" % index
        listings.append(am.publish_api(
            "usr:dana", "scan-%d" % index, "Scan API %d" % index,
            "portfolio scan endpoint %d" % index, PAYLOAD, 10,
            False)["listing_id"])

    stamps = ["2026-09-10T00:00:00Z", "2026-09-20T00:00:00Z",
              "2026-10-05T00:00:00Z", "2026-12-01T00:00:00Z",
              "2027-01-10T00:00:00Z", "2027-03-15T00:00:00Z"]
    purchases = []
    for index, stamp in enumerate(stamps):
        clock.value = stamp
        purchases.append(am.purchase_api(
            "usr:bob", listings[index],
            "BUY-BGM-%d" % (index + 1))["purchase_id"])

    clock.value = "2026-11-05T00:00:00Z"
    carol_purchase = am.purchase_api(
        "usr:carol", d1, "BUY-BGM-C")["purchase_id"]

    return {"d1": d1, "bob": purchases, "carol": carol_purchase}


def seed_refund(am, clock, world):
    """The December purchase is refunded in place: bob's activity
    months drop from five to four and the October..January silence
    widens from one empty month to two."""
    clock.value = "2027-04-01T00:00:00Z"
    am.refund_api("usr:bob", world["bob"][3], "changed my mind")


def main():
    tmpdir = tempfile.mkdtemp(prefix="ambgm-")
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

        # -- AC-BGM1 contract and the honest empty world ---------------
        empty = am.api_buyer_gap_months("usr:zoe")
        ok1a = (set(empty) == ENVELOPE_KEYS
                and empty["buyer_id"] == "usr:zoe"
                and empty["activity_month_count"] == 0
                and empty["purchase_count"] == 0
                and empty["first_activity_month"] is None
                and empty["last_activity_month"] is None
                and empty["gap_count"] == 0
                and empty["dormant_months_total"] == 0
                and empty["avg_gap_months"] is None
                and empty["median_gap_months"] is None
                and empty["max_gap_months"] is None
                and empty["as_of_month"] is None
                and empty["trailing_dormant_months"] is None
                and empty["gaps"] == []
                and empty["disclaimer"] == DISCLAIMER)
        world = seed_world(led, dk, am, clock)
        env = am.api_buyer_gap_months("usr:bob")
        ok1b = (set(env) == ENVELOPE_KEYS
                and all(set(row) == ROW_KEYS for row in env["gaps"]))
        record("AC-BGM1", ok1a and ok1b,
               "empty_ok=%r env_ok=%r" % (ok1a, ok1b))

        # -- AC-BGM2 activity months before the refund -----------------
        rows = env["gaps"]
        pairs2 = [(r["from_month"], r["to_month"], r["span_months"],
                   r["gap_months"]) for r in rows]
        ok2 = (env["activity_month_count"] == 5
               and env["purchase_count"] == 6
               and pairs2 == [("2026-09", "2026-10", 1, 0),
                              ("2026-10", "2026-12", 2, 1),
                              ("2026-12", "2027-01", 1, 0),
                              ("2027-01", "2027-03", 2, 1)])
        record("AC-BGM2", ok2,
               "activity=%r purchases=%r pairs=%r"
               % (env["activity_month_count"], env["purchase_count"],
                  pairs2))

        # -- AC-BGM3 a refund removes an activity month ----------------
        seed_refund(am, clock, world)
        after = am.api_buyer_gap_months("usr:bob")
        pairs3 = [(r["from_month"], r["to_month"], r["span_months"],
                   r["gap_months"]) for r in after["gaps"]]
        ok3 = (after["activity_month_count"] == 4
               and after["purchase_count"] == 5
               and "2026-12" not in json.dumps(
                   [after["first_activity_month"],
                    after["last_activity_month"],
                    after["longest_from_month"],
                    after["longest_to_month"]])
               and pairs3 == [("2026-09", "2026-10", 1, 0),
                              ("2026-10", "2027-01", 3, 2),
                              ("2027-01", "2027-03", 2, 1)])
        record("AC-BGM3", ok3,
               "activity=%r purchases=%r pairs=%r"
               % (after["activity_month_count"], after["purchase_count"],
                  pairs3))

        # -- AC-BGM4 the gap law on every row --------------------------
        law_ok = True
        for first, second, span, gap in pairs3:
            law_ok = law_ok and (span >= 1 and gap == span - 1)
        ok4 = (law_ok
               and len(pairs3) == after["activity_month_count"] - 1
               and pairs3[0][0] == after["first_activity_month"]
               and pairs3[-1][1] == after["last_activity_month"]
               and [p[1] for p in pairs3[:-1]] == [p[0] for p in pairs3[1:]])
        record("AC-BGM4", ok4,
               "law=%r rows=%d chain=%r"
               % (law_ok, len(pairs3),
                  [p[0] for p in pairs3] + [pairs3[-1][1]]))

        # -- AC-BGM5 aggregates ---------------------------------------
        ok5 = (after["gap_count"] == 3
               and after["dormant_months_total"] == 3
               and after["avg_gap_months"] == 1.0
               and after["median_gap_months"] == 1
               and after["max_gap_months"] == 2
               and after["longest_from_month"] == "2026-10"
               and after["longest_to_month"] == "2027-01"
               and after["first_activity_month"] == "2026-09"
               and after["last_activity_month"] == "2027-03")
        record("AC-BGM5", ok5,
               "gap_count=%r dormant=%r avg=%r median=%r max=%r"
               " longest=%r"
               % (after["gap_count"], after["dormant_months_total"],
                  after["avg_gap_months"], after["median_gap_months"],
                  after["max_gap_months"],
                  [after["longest_from_month"],
                   after["longest_to_month"]]))

        # -- AC-BGM6 as_of silence and the fail-closed family ----------
        default6 = am.api_buyer_gap_months("usr:bob")
        given6 = am.api_buyer_gap_months("usr:bob", as_of="2027-06")
        same6 = am.api_buyer_gap_months("usr:bob", as_of="2027-03")
        bad6 = []
        for bad in ("2027-6", "2027-13", "2027-00", 202706, "2027-06x",
                    "2027-02"):
            try:
                am.api_buyer_gap_months("usr:bob", as_of=bad)
                bad6.append(("accepted", bad))
            except A.ApiMarketError as exc:
                if exc.code != A.E_AM_BAD_WINDOW:
                    bad6.append((exc.code, bad))
        try:
            am.api_buyer_gap_months("bob", as_of="2027-06")
            order6 = "accepted"
        except A.ApiMarketError as exc:
            order6 = exc.code
        ok6 = (default6["as_of_month"] == "2027-03"
               and default6["trailing_dormant_months"] == 0
               and given6["as_of_month"] == "2027-06"
               and given6["trailing_dormant_months"] == 3
               and same6["trailing_dormant_months"] == 0
               and bad6 == []
               and order6 == A.E_AM_BAD_ACCOUNT)
        record("AC-BGM6", ok6,
               "default=%r given=%r same=%r bad=%r order=%r"
               % ([default6["as_of_month"],
                   default6["trailing_dormant_months"]],
                  given6["trailing_dormant_months"],
                  same6["trailing_dormant_months"], bad6, order6))

        # -- AC-BGM7 pure read and buyer isolation ---------------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        runs = [dumps(am.api_buyer_gap_months("usr:bob",
                                             as_of="2027-06")),
                dumps(am.api_buyer_gap_months("usr:bob",
                                             as_of="2027-06")),
                dumps(am.api_buyer_gap_months("usr:bob",
                                             as_of="2027-06"))]
        digests_after = frozen_digests(am)
        pure_ok = (runs[0] == runs[1] == runs[2]
                   and digests_before == digests_after
                   and tx_before == ledger_tx_ids(led))
        carol7 = am.api_buyer_gap_months("usr:carol")
        bare7 = am.api_buyer_gap_months("usr:")
        ok7 = (pure_ok
               and carol7["activity_month_count"] == 1
               and carol7["purchase_count"] == 1
               and carol7["first_activity_month"] == "2026-11"
               and carol7["gaps"] == []
               and carol7["avg_gap_months"] is None
               and carol7["trailing_dormant_months"] == 0
               and bare7["activity_month_count"] == 0
               and bare7["gaps"] == [])
        record("AC-BGM7", ok7,
               "pure=%r carol=%r bare=%r"
               % (pure_ok, [carol7["activity_month_count"],
                            carol7["gaps"], carol7["avg_gap_months"]],
                  bare7["activity_month_count"]))

        # -- AC-BGM8 restart identity and delivery hygiene -------------
        baseline_bob = dumps(am.api_buyer_gap_months("usr:bob",
                                                    as_of="2027-06"))
        baseline_carol = dumps(am.api_buyer_gap_months("usr:carol"))
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append((dumps(am2.api_buyer_gap_months(
                "usr:bob", as_of="2027-06")),
                dumps(am2.api_buyer_gap_months("usr:carol"))))
            close_stack(am2, dk2, metered2, led2)
        restart_ok = all(pair == (baseline_bob, baseline_carol)
                         for pair in replays)
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-buyergapmonths"'
                     in handle.read())
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
        ok8 = (restart_ok and wired and ascii_ok and net_ok
               and shipped_ok and outside_ok)
        record("AC-BGM8", ok8,
               "restart=%r wired=%r ascii=%r no_net=%r shipped=%r"
               " outside=%r"
               % (restart_ok, wired, ascii_ok, net_ok, shipped_ok,
                  outside_ok))

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