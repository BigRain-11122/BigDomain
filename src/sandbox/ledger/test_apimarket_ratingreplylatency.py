"""Acceptance suite for the apimarket rating reply latency scorecard
(BigDomain R2193; canon = the R2189 explore-queue seed 5/10 row claimed
in R2193, criteria AC-RRL1..AC-RRL8 registered in that row BEFORE this
suite existed; AC-RRL / api_rating_reply_latency / this suite name /
the ledger-apimarket-ratingreplylatency runner label / reply_coverage /
oldest_unreplied_utc were all git grep -F zero-occupancy anchored
against HEAD on 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_rating_reply_latency. The trust
face grew a reply door (R2093), a reply revision leg (R2143) and a
reply history face, the present debt has api_seller_inbox, and the two
neighbouring conversation chains already score their waiting time
(api_seller_answers for questions, api_claim_latency for claims), but
nothing measured how long a RATING sat before the seller answered it.
This slot pins:

  - the thirteen-key envelope and thirteen-key row, the partition
    rating_count == replied + unreplied, and the honest empty world;
  - latency derived from two stored stamps only, integer, non-negative,
    None (never a fabricated zero) for an unanswered rating, and the
    same-second reply reading exactly 0;
  - the usr: prefix gate before any read (seven bad forms), the
    operator-wide default, honest empty for an unknown seller, the bare
    prefix honest empty, and strict seller isolation;
  - the aggregate family: average, median parity, fastest, slowest,
    latest reply stamp, oldest outstanding stamp, coverage, all None
    when nothing was answered;
  - the total order (answered by descending latency then rating_id,
    pending after them by rated_utc then rating_id);
  - the revision seams: a reply revision moves reply_text but never the
    historical latency, a star revision moves stars but no timing
    reading, and revising back restores the bytes;
  - cross-face agreement with api_seller_inbox on the total, the
    outstanding count and the oldest stamp;
  - pure read (frozen table digests, constant ledger tx set), three
    identical reads and two full-stack restarts;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_ratingreplylatency.py
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

ENVELOPE_KEYS = {"dev_account", "rating_count", "replied_count",
                 "unreplied_count", "reply_coverage", "avg_seconds",
                 "median_seconds", "fastest_seconds", "slowest_seconds",
                 "latest_reply_utc", "oldest_unreplied_utc",
                 "disclaimer", "rows"}

ROW_KEYS = {"rating_id", "listing_id", "listing_key", "title",
            "dev_account", "buyer_id", "stars", "rated_utc", "replied",
            "reply_id", "replied_utc", "reply_text", "latency_seconds"}

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
        am.api_rating_reply_latency(dev_account)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3); frank owns f1 (price 5).
    Every rater buys first because the rating door is purchaser-only."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMRRL-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMRRL-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "gina"):
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
    am.purchase_api("usr:bob", d1, "BUY-RRL-1")
    clock.value = "2026-10-06T00:00:11Z"
    am.purchase_api("usr:carol", d1, "BUY-RRL-2")
    clock.value = "2026-10-06T00:00:12Z"
    am.purchase_api("usr:bob", d2, "BUY-RRL-3")
    clock.value = "2026-10-06T00:00:13Z"
    am.purchase_api("usr:dave", d2, "BUY-RRL-4")
    clock.value = "2026-10-06T00:00:14Z"
    am.purchase_api("usr:gina", f1, "BUY-RRL-5")
    return {"d1": d1, "d2": d2, "f1": f1}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amrrl-")
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

        # -- AC-RRL1 contract and the honest empty world ---------------
        empty = am.api_rating_reply_latency()
        ok1a = (set(empty) == ENVELOPE_KEYS
                and empty["rating_count"] == 0
                and empty["replied_count"] == 0
                and empty["unreplied_count"] == 0
                and empty["reply_coverage"] is None
                and empty["avg_seconds"] is None
                and empty["median_seconds"] is None
                and empty["fastest_seconds"] is None
                and empty["slowest_seconds"] is None
                and empty["latest_reply_utc"] is None
                and empty["oldest_unreplied_utc"] is None
                and empty["rows"] == []
                and empty["disclaimer"] == DISCLAIMER)
        clock.value = "2026-10-06T01:00:00Z"
        r1 = am.rate_api("usr:bob", ids["d1"], 5)
        clock.value = "2026-10-06T01:00:10Z"
        r2 = am.rate_api("usr:carol", ids["d1"], 4)
        clock.value = "2026-10-06T01:00:20Z"
        r3 = am.rate_api("usr:bob", ids["d2"], 2)
        clock.value = "2026-10-06T01:00:30Z"
        r4 = am.rate_api("usr:dave", ids["d2"], 3)
        clock.value = "2026-10-06T01:00:40Z"
        r5 = am.rate_api("usr:gina", ids["f1"], 5)
        env = am.api_rating_reply_latency()
        ok1b = (ENVELOPE_KEYS <= set(env)
                and all(ROW_KEYS <= set(r) for r in env["rows"])
                and env["rating_count"] == len(env["rows"]) == 5
                and env["replied_count"] == 0
                and env["unreplied_count"] == 5
                and env["reply_coverage"] == 0.0
                and [r["rating_id"] for r in env["rows"]]
                == [r1["rating_id"], r2["rating_id"], r3["rating_id"],
                    r4["rating_id"], r5["rating_id"]])
        record("AC-RRL1", ok1a and ok1b,
               "empty_keys=%r empty_rows=%r open_rows=%d order=%r"
               % (set(empty) == ENVELOPE_KEYS, empty["rows"] == [],
                  env["rating_count"],
                  [r["rating_id"] for r in env["rows"]]))

        # -- AC-RRL2 one timing authority ------------------------------
        clock.value = "2026-10-06T01:10:00Z"
        am.reply_to_rating("usr:dana", r1["rating_id"], "thanks bob")
        clock.value = "2026-10-06T01:00:20Z"
        am.reply_to_rating("usr:dana", r3["rating_id"], "noted")
        clock.value = "2026-10-06T01:01:40Z"
        am.reply_to_rating("usr:frank", r5["rating_id"], "patch shipped")
        env = am.api_rating_reply_latency()
        by_id = {r["rating_id"]: r for r in env["rows"]}
        a1 = by_id[r1["rating_id"]]
        a2 = by_id[r2["rating_id"]]
        a3 = by_id[r3["rating_id"]]
        a4 = by_id[r4["rating_id"]]
        a5 = by_id[r5["rating_id"]]
        ok2 = (a1["latency_seconds"] == 600
               and a3["latency_seconds"] == 0
               and a5["latency_seconds"] == 60
               and a2["latency_seconds"] is None
               and a4["latency_seconds"] is None
               and a2["replied"] is False
               and a2["reply_id"] is None
               and a2["replied_utc"] is None
               and a2["reply_text"] is None
               and a1["replied"] is True
               and a1["replied_utc"] == "2026-10-06T01:10:00Z"
               and a1["rated_utc"] == "2026-10-06T01:00:00Z"
               and all(
                   (v is None or (isinstance(v, int) and v >= 0))
                   for row in env["rows"]
                   for v in (row["latency_seconds"],)))
        record("AC-RRL2", ok2,
               "r1=%r r3=%r r5=%r pending=%r/%r"
               % (a1["latency_seconds"], a3["latency_seconds"],
                  a5["latency_seconds"], a2["latency_seconds"],
                  a4["latency_seconds"]))

        # -- AC-RRL3 gate family, honest empty, seller isolation -------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        codes = [latency_code(am, bad) for bad in BAD_ACCOUNTS]
        digests_after = frozen_digests(am)
        unknown = am.api_rating_reply_latency("usr:nobody")
        bare_prefix = am.api_rating_reply_latency("usr:")
        dana = am.api_rating_reply_latency("usr:dana")
        frank = am.api_rating_reply_latency("usr:frank")
        ok3 = (codes == [A.E_AM_BAD_ACCOUNT] * len(BAD_ACCOUNTS)
               and digests_before == digests_after
               and tx_before == ledger_tx_ids(led)
               and unknown["rating_count"] == 0
               and unknown["rows"] == []
               and unknown["reply_coverage"] is None
               and bare_prefix["rating_count"] == 0
               and bare_prefix["rows"] == []
               and bare_prefix["disclaimer"] == DISCLAIMER
               and dana["rating_count"] == 4
               and frank["rating_count"] == 1
               and all(r["dev_account"] == "usr:dana"
                       for r in dana["rows"])
               and all(r["dev_account"] == "usr:frank"
                       for r in frank["rows"]))
        record("AC-RRL3", ok3,
               "codes=%r digests_frozen=%r dana=%d frank=%d"
               " unknown=%d bare_prefix=%d"
               % (codes, digests_before == digests_after,
                  dana["rating_count"], frank["rating_count"],
                  unknown["rating_count"], bare_prefix["rating_count"]))

        # -- AC-RRL4 aggregate family ----------------------------------
        lat = sorted(row["latency_seconds"] for row in env["rows"]
                     if row["latency_seconds"] is not None)
        market_ok = (lat == [0, 60, 600]
                     and env["replied_count"] == 3
                     and env["unreplied_count"] == 2
                     and env["rating_count"] == 5
                     and env["reply_coverage"] == 0.6
                     and env["avg_seconds"] == (sum(lat) / 3.0)
                     and env["median_seconds"] == 60.0
                     and env["fastest_seconds"] == 0
                     and env["slowest_seconds"] == 600
                     and env["latest_reply_utc"]
                     == "2026-10-06T01:10:00Z"
                     and env["oldest_unreplied_utc"]
                     == "2026-10-06T01:00:10Z")
        dana_ok = (dana["replied_count"] == 2
                   and dana["unreplied_count"] == 2
                   and dana["reply_coverage"] == 0.5
                   and dana["avg_seconds"] == 300.0
                   and dana["median_seconds"] == 300.0
                   and dana["fastest_seconds"] == 0
                   and dana["slowest_seconds"] == 600
                   and dana["oldest_unreplied_utc"]
                   == "2026-10-06T01:00:10Z")
        frank_ok = (frank["replied_count"] == 1
                    and frank["unreplied_count"] == 0
                    and frank["reply_coverage"] == 1.0
                    and frank["avg_seconds"] == 60.0
                    and frank["median_seconds"] == 60.0
                    and frank["fastest_seconds"] == 60
                    and frank["slowest_seconds"] == 60
                    and frank["oldest_unreplied_utc"] is None)
        record("AC-RRL4", market_ok and dana_ok and frank_ok,
               "lat=%r avg=%r median=%r coverage=%r dana_avg=%r"
               " frank_avg=%r"
               % (lat, env["avg_seconds"], env["median_seconds"],
                  env["reply_coverage"], dana["avg_seconds"],
                  frank["avg_seconds"]))

        # -- AC-RRL5 total order ---------------------------------------
        order = [r["rating_id"] for r in env["rows"]]
        dana_order = [r["rating_id"] for r in dana["rows"]]
        frank_order = [r["rating_id"] for r in frank["rows"]]
        want = [r1["rating_id"], r5["rating_id"], r3["rating_id"],
                r2["rating_id"], r4["rating_id"]]
        ok5 = (order == want
               and dana_order == [r1["rating_id"], r3["rating_id"],
                                  r2["rating_id"], r4["rating_id"]]
               and frank_order == [r5["rating_id"]]
               and env["rows"][:3] == [r for r in env["rows"]
                                       if r["latency_seconds"] is not None]
               and [r["rated_utc"] for r in env["rows"][3:]]
               == ["2026-10-06T01:00:10Z", "2026-10-06T01:00:30Z"])
        record("AC-RRL5", ok5, "order=%r dana=%r frank=%r"
               % (order, dana_order, frank_order))

        # -- AC-RRL6 revision seams freeze history ---------------------
        before_dana = dumps(am.api_rating_reply_latency("usr:dana"))
        before_row = {r["rating_id"]: r for r in dana["rows"]}
        reply_id = before_row[r1["rating_id"]]["reply_id"]
        clock.value = "2026-10-06T05:00:00Z"
        am.revise_reply("usr:dana", reply_id, "thanks bob, refund offered")
        after_reply = am.api_rating_reply_latency("usr:dana")
        row_after = {r["rating_id"]: r for r in after_reply["rows"]}
        ok6a = (row_after[r1["rating_id"]]["reply_text"]
                == "thanks bob, refund offered"
                and row_after[r1["rating_id"]]["replied_utc"]
                == before_row[r1["rating_id"]]["replied_utc"]
                and row_after[r1["rating_id"]]["latency_seconds"] == 600
                and after_reply["avg_seconds"] == 300.0
                and after_reply["latest_reply_utc"]
                == "2026-10-06T01:10:00Z")
        clock.value = "2026-10-06T06:00:00Z"
        am.revise_rating("usr:carol", r2["rating_id"], 1)
        after_star = am.api_rating_reply_latency("usr:dana")
        star_row = {r["rating_id"]: r for r in after_star["rows"]}
        ok6b = (star_row[r2["rating_id"]]["stars"] == 1
                and star_row[r2["rating_id"]]["latency_seconds"] is None
                and after_star["unreplied_count"] == 2
                and after_star["oldest_unreplied_utc"]
                == "2026-10-06T01:00:10Z")
        am.revise_reply("usr:dana", reply_id, "thanks bob")
        am.revise_rating("usr:carol", r2["rating_id"], 4)
        restored = dumps(am.api_rating_reply_latency("usr:dana"))
        record("AC-RRL6", ok6a and ok6b and restored == before_dana,
               "text_moved=%r latency_frozen=%r star_moved=%r"
               " restored=%r"
               % (row_after[r1["rating_id"]]["reply_text"]
                  == "thanks bob, refund offered",
                  row_after[r1["rating_id"]]["latency_seconds"] == 600,
                  star_row[r2["rating_id"]]["stars"] == 1,
                  restored == before_dana))

        # -- AC-RRL7 cross-face agreement and pure read ----------------
        inbox = am.api_seller_inbox("usr:dana")
        market = am.api_rating_reply_latency()
        dana_now = am.api_rating_reply_latency("usr:dana")
        ok7a = (inbox["total_rating_count"]
                == dana_now["rating_count"]
                == 4
                and market["rating_count"] == 5
                and inbox["answered_count"] == 2
                and inbox["unanswered_count"] == 2
                and len(inbox["rows"]) == dana_now["unreplied_count"] == 2
                and inbox["oldest_unanswered_utc"]
                == dana_now["oldest_unreplied_utc"]
                == market["oldest_unreplied_utc"])
        ok7b = (dana_now["replied_count"] + dana_now["unreplied_count"]
                == inbox["total_rating_count"]
                and dana_now["unreplied_count"] == len(inbox["rows"])
                and dana_now["oldest_unreplied_utc"]
                == inbox["oldest_unanswered_utc"])
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        runs = [dumps(am.api_rating_reply_latency()),
                dumps(am.api_rating_reply_latency()),
                dumps(am.api_rating_reply_latency())]
        digests_after = frozen_digests(am)
        pure_ok = (runs[0] == runs[1] == runs[2]
                   and digests_before == digests_after
                   and tx_before == ledger_tx_ids(led))
        record("AC-RRL7", ok7a and ok7b and pure_ok,
               "inbox_total=%d inbox_open=%d market_open=%d"
               " oldest=%r pure=%r"
               % (inbox["total_rating_count"],
                  inbox["unanswered_count"], market["unreplied_count"],
                  inbox["oldest_unanswered_utc"] ==
                  market["oldest_unreplied_utc"], pure_ok))

        # -- AC-RRL8 cross-restart identity and delivery hygiene --------
        baseline_market = dumps(am.api_rating_reply_latency())
        baseline_dana = dumps(am.api_rating_reply_latency("usr:dana"))
        baseline_frank = dumps(am.api_rating_reply_latency("usr:frank"))
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_rating_reply_latency()))
            replays.append(dumps(am2.api_rating_reply_latency("usr:dana")))
            replays.append(dumps(am2.api_rating_reply_latency(
                "usr:frank")))
            close_stack(am2, dk2, metered2, led2)
        restart_ok = (replays[0] == baseline_market == replays[3]
                      and replays[1] == baseline_dana == replays[4]
                      and replays[2] == baseline_frank == replays[5])
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-ratingreplylatency"'
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
        record("AC-RRL8", ok8,
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