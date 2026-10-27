"""Acceptance suite for the apimarket claim response latency scorecard
(BigDomain R2159; canon = the explore-queue row claimed in R2159,
criteria AC-CLT1..AC-CLT8 registered in that claim note BEFORE this
suite existed; the AC-CLT prefix, api_claim_latency, this suite name,
the ledger-apimarket-claimlatency runner label, claim_latency and
response_coverage were all git grep -F zero-occupancy anchored against
HEAD on 2026-10-27, rc=1).

Face under proof: APIMarketFace.api_claim_latency. The claim chain grew
one door per round - open (R2129), respond (R2130), withdraw (R2131),
note (R2137) - and the question/answer pair already scored its waiting
time (api_seller_answers reports fastest/slowest/mean seconds), but the
claim chain never produced a latency figure at all: api_seller_todo
lists only the unanswered rows and api_claim_thread opens one thread at
a time, so "does this seller answer within a day or sit on claims" had
no answer. This slot pins:

  - the twelve-key envelope, the sixteen-key row, claim_count ==
    len(claims), and the honest empty world;
  - durations derived from two stored stamps only, the never-happened
    leg being None rather than zero, and never negative;
  - the usr: prefix account gate before any read (eight bad forms),
    the operator-wide default, honest empty for an unknown seller and
    strict seller isolation;
  - the aggregate family: answered/unanswered partition, coverage,
    average, median parity (odd middle, even midpoint), fastest and
    slowest, all None when nothing was answered;
  - the api_claims status seam (refunded beats withdrawn beats answered
    beats open) with both stamps kept when a later refund lands;
  - cross-face agreement of the four stamps and price_paid with
    api_claims for the same claim id;
  - pure read (frozen table digests and a constant ledger tx set),
    three identical reads and two full-stack restarts;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_claimlatency.py
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

ENVELOPE_KEYS = {"dev_account", "claim_count", "answered_count",
                 "unanswered_count", "response_coverage",
                 "avg_response_seconds", "median_response_seconds",
                 "fastest_seconds", "slowest_seconds",
                 "latest_response_utc", "disclaimer", "claims"}

ROW_KEYS = {"claim_id", "purchase_id", "listing_id", "buyer_id",
            "dev_account", "price_paid", "opened_utc", "status",
            "responded_utc", "response_seconds", "noted_utc",
            "note_seconds", "withdrawn_utc", "withdraw_seconds",
            "refunded_utc", "refund_seconds"}

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

BAD_ACCOUNTS = ["", "bob", "USR:bob", " usr:bob", 42, True, []]


class Clock(object):
    """Deterministic stamp holder; the module clock is patched in
    main() and restored in the finally block."""

    def __init__(self):
        self.value = "2026-10-06T00:00:00Z"

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


def code_of(exc):
    return getattr(exc, "code", None)


def latency_code(am, dev_account):
    try:
        am.api_claim_latency(dev_account)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3); frank owns f1 (price 5).
    bob, carol and erin buy, so four claims can be opened on dana's
    shelves and one on frank's."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMCLT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMCLT-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "gina"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    clock.value = "2026-10-06T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-06T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    clock.value = "2026-10-06T00:00:03Z"
    f1 = am.publish_api("usr:frank", "sync-kit", "Sync Kit API",
                        "collaborative sync kit", PAYLOAD, 5, False)[
                            "listing_id"]
    clock.value = "2026-10-06T00:00:10Z"
    p_bob1 = am.purchase_api("usr:bob", d1, "BUY-CLT-1")
    clock.value = "2026-10-06T00:00:11Z"
    p_carol1 = am.purchase_api("usr:carol", d1, "BUY-CLT-2")
    clock.value = "2026-10-06T00:00:12Z"
    p_bob2 = am.purchase_api("usr:bob", d2, "BUY-CLT-3")
    clock.value = "2026-10-06T00:00:13Z"
    p_dave2 = am.purchase_api("usr:dave", d2, "BUY-CLT-4")
    clock.value = "2026-10-06T00:00:14Z"
    p_erin2 = am.purchase_api("usr:erin", d2, "BUY-CLT-5")
    clock.value = "2026-10-06T00:00:15Z"
    p_gina1 = am.purchase_api("usr:gina", f1, "BUY-CLT-6")
    return {"d1": d1, "d2": d2, "f1": f1, "p_bob1": p_bob1,
            "p_carol1": p_carol1, "p_bob2": p_bob2, "p_dave2": p_dave2,
            "p_erin2": p_erin2, "p_gina1": p_gina1}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amclt-")
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

        # -- AC-CLT1 contract and the honest empty world ---------------
        empty = am.api_claim_latency()
        ok1a = (set(empty) == ENVELOPE_KEYS
                and empty["claim_count"] == 0
                and empty["answered_count"] == 0
                and empty["unanswered_count"] == 0
                and empty["response_coverage"] is None
                and empty["avg_response_seconds"] is None
                and empty["median_response_seconds"] is None
                and empty["fastest_seconds"] is None
                and empty["slowest_seconds"] is None
                and empty["latest_response_utc"] is None
                and empty["claims"] == []
                and empty["disclaimer"] == DISCLAIMER)
        clock.value = "2026-10-06T00:01:00Z"
        c1 = am.open_claim("usr:bob", ids["p_bob1"]["purchase_id"],
                           "endpoint returned 500 on every call")
        clock.value = "2026-10-06T00:01:01Z"
        c2 = am.open_claim("usr:bob", ids["p_bob2"]["purchase_id"],
                           "data stale by two days")
        c3 = am.open_claim("usr:dave", ids["p_dave2"]["purchase_id"],
                           "response does not match the sample")
        clock.value = "2026-10-06T00:01:02Z"
        c4 = am.open_claim("usr:erin", ids["p_erin2"]["purchase_id"],
                           "delivery window missed")
        clock.value = "2026-10-06T00:01:03Z"
        c5 = am.open_claim("usr:gina", ids["p_gina1"]["purchase_id"],
                           "kit does not sync")
        env = am.api_claim_latency()
        ok1b = (ENVELOPE_KEYS <= set(env)
                and all(ROW_KEYS <= set(r) for r in env["claims"])
                and env["claim_count"] == len(env["claims"]) == 5
                and env["answered_count"] == 0
                and env["unanswered_count"] == 5
                and env["claims"][0]["claim_id"] == c1["claim_id"]
                and [c["claim_id"] for c in env["claims"]]
                == [c1["claim_id"], c2["claim_id"], c3["claim_id"],
                    c4["claim_id"], c5["claim_id"]])
        record("AC-CLT1", ok1a and ok1b,
               "empty_keys=%r empty_none=%r rows=%d order=%r"
               % (set(empty) == ENVELOPE_KEYS,
                  empty["claims"] == [], env["claim_count"],
                  [c["claim_id"] for c in env["claims"]]))

        # -- AC-CLT2 one timing authority ------------------------------
        clock.value = "2026-10-06T01:01:00Z"
        am.respond_claim("usr:dana", c1["claim_id"], "fixed, retry now")
        clock.value = "2026-10-06T00:03:00Z"
        am.respond_claim("usr:dana", c3["claim_id"], "sample updated")
        clock.value = "2026-10-06T02:01:00Z"
        am.add_claim_note("usr:bob", c1["claim_id"],
                          "still failing after the fix")
        clock.value = "2026-10-06T00:31:01Z"
        am.withdraw_claim("usr:bob", c2["claim_id"])
        clock.value = "2026-10-06T00:06:03Z"
        am.respond_claim("usr:frank", c5["claim_id"], "patch incoming")
        env = am.api_claim_latency()
        by_id = {r["claim_id"]: r for r in env["claims"]}
        r1 = by_id[c1["claim_id"]]
        r2 = by_id[c2["claim_id"]]
        r3 = by_id[c3["claim_id"]]
        r4 = by_id[c4["claim_id"]]
        r5 = by_id[c5["claim_id"]]
        ok2 = (r1["response_seconds"] == 3600
               and r1["note_seconds"] == 7200
               and r1["withdraw_seconds"] is None
               and r1["refund_seconds"] is None
               and r2["response_seconds"] is None
               and r2["withdraw_seconds"] == 1800
               and r3["response_seconds"] == 119
               and r4["response_seconds"] is None
               and r5["response_seconds"] == 300
               and all(
                   (v is None or v >= 0)
                   for r in env["claims"]
                   for v in (r["response_seconds"], r["note_seconds"],
                             r["withdraw_seconds"], r["refund_seconds"]))
               and r1["responded_utc"] == "2026-10-06T01:01:00Z"
               and r1["opened_utc"] == "2026-10-06T00:01:00Z")
        record("AC-CLT2", ok2,
               "c1_response=%r c1_note=%r c2_withdraw=%r c3_response=%r"
               " unanswered=%r"
               % (r1["response_seconds"], r1["note_seconds"],
                  r2["withdraw_seconds"], r3["response_seconds"],
                  r4["response_seconds"]))

        # -- AC-CLT3 gate family, honest empty, seller isolation -------
        digests_before = frozen_digests(am)
        codes = [latency_code(am, bad) for bad in BAD_ACCOUNTS]
        digests_after = frozen_digests(am)
        unknown = am.api_claim_latency("usr:nobody")
        # The gate is prefix-only by the truthful R2077/R2078 finding, so
        # the bare prefix "usr:" is NOT a bad-account form - it passes the
        # gate and answers an honest empty envelope (nobody owns claims
        # under a bare prefix). Measured here rather than assumed.
        bare_prefix = am.api_claim_latency("usr:")
        dana = am.api_claim_latency("usr:dana")
        frank = am.api_claim_latency("usr:frank")
        ok3 = (codes == [A.E_AM_BAD_ACCOUNT] * len(BAD_ACCOUNTS)
               and digests_before == digests_after
               and unknown["claim_count"] == 0
               and unknown["claims"] == []
               and unknown["response_coverage"] is None
               and bare_prefix["claim_count"] == 0
               and bare_prefix["claims"] == []
               and bare_prefix["disclaimer"] == DISCLAIMER
               and dana["claim_count"] == 4
               and frank["claim_count"] == 1
               and all(c["dev_account"] == "usr:dana"
                       for c in dana["claims"])
               and all(c["dev_account"] == "usr:frank"
                       for c in frank["claims"]))
        record("AC-CLT3", ok3,
               "codes=%r digests_frozen=%r dana=%d frank=%d unknown=%d"
               " bare_prefix=%d"
               % (codes, digests_before == digests_after,
                  dana["claim_count"], frank["claim_count"],
                  unknown["claim_count"], bare_prefix["claim_count"]))

        # -- AC-CLT4 aggregate family ----------------------------------
        lat = sorted(c["response_seconds"] for c in env["claims"]
                     if c["response_seconds"] is not None)
        market_ok = (lat == [119, 300, 3600]
                     and env["answered_count"] == 3
                     and env["unanswered_count"] == 2
                     and env["claim_count"] == 5
                     and env["response_coverage"] == 0.6
                     and env["avg_response_seconds"] == (sum(lat) / 3.0)
                     and env["median_response_seconds"] == 300.0
                     and env["fastest_seconds"] == 119
                     and env["slowest_seconds"] == 3600
                     and env["latest_response_utc"]
                     == "2026-10-06T01:01:00Z")
        dana_lat = sorted([3600, 119])
        dana_ok = (dana["answered_count"] == 2
                   and dana["unanswered_count"] == 2
                   and dana["response_coverage"] == 0.5
                   and dana["avg_response_seconds"]
                   == (sum(dana_lat) / 2.0)
                   and dana["median_response_seconds"]
                   == (dana_lat[0] + dana_lat[1]) / 2.0
                   and dana["median_response_seconds"] == 1859.5
                   and dana["fastest_seconds"] == 119
                   and dana["slowest_seconds"] == 3600)
        frank_ok = (frank["answered_count"] == 1
                    and frank["unanswered_count"] == 0
                    and frank["response_coverage"] == 1.0
                    and frank["avg_response_seconds"] == 300.0
                    and frank["median_response_seconds"] == 300.0
                    and frank["fastest_seconds"] == 300
                    and frank["slowest_seconds"] == 300)
        record("AC-CLT4", market_ok and dana_ok and frank_ok,
               "lat=%r avg=%r median=%r coverage=%r dana_median=%r"
               % (lat, env["avg_response_seconds"],
                  env["median_response_seconds"],
                  env["response_coverage"],
                  dana["median_response_seconds"]))

        # -- AC-CLT5 status seam and the later refund ------------------
        clock.value = "2026-10-06T03:01:00Z"
        am.refund_api("usr:bob", ids["p_bob1"]["purchase_id"],
                      "claim accepted")
        env = am.api_claim_latency()
        claims_env = am.api_claim_latency("usr:dana")
        dana_rows = {r["claim_id"]: r for r in claims_env["claims"]}
        ref = {r["claim_id"]: r for r in
               am.api_claims(dev_account="usr:dana")["claims"]}
        r1 = dana_rows[c1["claim_id"]]
        ok5 = (r1["status"] == "refunded"
               and r1["response_seconds"] == 3600
               and r1["responded_utc"] == "2026-10-06T01:01:00Z"
               and r1["refund_seconds"] == 10800
               and dana_rows[c2["claim_id"]]["status"] == "withdrawn"
               and dana_rows[c3["claim_id"]]["status"] == "answered"
               and dana_rows[c4["claim_id"]]["status"] == "open"
               and all(dana_rows[cid]["status"] == ref[cid]["status"]
                       for cid in dana_rows))
        record("AC-CLT5", ok5,
               "refunded=%r response_kept=%r refund_seconds=%r"
               " statuses=%r"
               % (r1["status"] == "refunded",
                  r1["response_seconds"] == 3600,
                  r1["refund_seconds"],
                  [dana_rows[cid]["status"] for cid in sorted(dana_rows)]))

        # -- AC-CLT6 cross-face stamp agreement ------------------------
        market_rows = {r["claim_id"]: r for r in env["claims"]}
        ref_all = {r["claim_id"]: r for r in am.api_claims()["claims"]}
        agree = True
        for cid, row in market_rows.items():
            other = ref_all[cid]
            agree = agree and (
                row["opened_utc"] == other["opened_utc"]
                and row["responded_utc"] == other["responded_utc"]
                and row["withdrawn_utc"] == other["withdrawn_utc"]
                and row["refunded_utc"] == other["refunded_utc"]
                and row["price_paid"] == other["price_paid"]
                and row["buyer_id"] == other["buyer_id"]
                and row["purchase_id"] == other["purchase_id"]
                and row["status"] == other["status"])
        price_ok = (market_rows[c1["claim_id"]]["price_paid"] == 10
                    and market_rows[c2["claim_id"]]["price_paid"] == 3
                    and market_rows[c5["claim_id"]]["price_paid"] == 5)
        record("AC-CLT6", agree and price_ok,
               "claims=%d agree=%r prices=%r"
               % (len(market_rows), agree, price_ok))

        # -- AC-CLT7 pure read and cross-restart identity --------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        runs = [dumps(am.api_claim_latency()),
                dumps(am.api_claim_latency()),
                dumps(am.api_claim_latency())]
        digests_after = frozen_digests(am)
        pure_ok = (runs[0] == runs[1] == runs[2]
                   and digests_before == digests_after
                   and tx_before == ledger_tx_ids(led))
        baseline_market = dumps(am.api_claim_latency())
        baseline_dana = dumps(am.api_claim_latency("usr:dana"))
        baseline_frank = dumps(am.api_claim_latency("usr:frank"))
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_claim_latency()))
            replays.append(dumps(am2.api_claim_latency("usr:dana")))
            replays.append(dumps(am2.api_claim_latency("usr:frank")))
            close_stack(am2, dk2, metered2, led2)
        ok7 = (pure_ok
               and replays[0] == baseline_market == replays[3]
               and replays[1] == baseline_dana == replays[4]
               and replays[2] == baseline_frank == replays[5])
        record("AC-CLT7", ok7,
               "pure=%r restart_market=%r restart_dana=%r"
               " restart_frank=%r"
               % (pure_ok, replays[0] == replays[3],
                  replays[1] == replays[4], replays[2] == replays[5]))

        # -- AC-CLT8 delivery hygiene ----------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-claimlatency"' in handle.read())
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
        record("AC-CLT8", ok8,
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