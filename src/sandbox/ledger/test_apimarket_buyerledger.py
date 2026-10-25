"""Acceptance suite for the apimarket buyer settlement statement face
(BigDomain R2128; canon = the explore-queue row claimed in R2128,
criteria AC-AMLGB1..AC-AMLGB8 registered in that claim note BEFORE this
suite existed; the AC-AMLGB prefix, the api_buyer_ledger name, this
suite name, the ledger-apimarket-buyerledger runner label and the
"buyer ledger statement" page caption were all git grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Face under proof: APIMarketFace.api_buyer_ledger. R2126 gave the seller
a settlement statement; the buyer side still had row faces, cash months
and lifetime aggregates but no face answering "how much money do I have
right now, and which ledger entries produced it" - the ledger movements
a purchase debits and a refund credits had zero product consumers. This
slot pins the join:

  - a ten-key envelope and a ten/eleven-key row, entry_count equal to
    the row length, credit/debit totals derived from the rows and net
    equal to their difference;
  - the balance read through the single _seller_balance seam (any usr:
    account, no second bookkeeping copy), equal to the ledger face value
    and moving immediately with a purchase and a refund;
  - account isolation proven against an independent sqlite read of the
    ledger entries (count and both direction totals);
  - newest-first order with the limit truncating the OLDEST tail (a
    prefix law) and an over-cap limit clamping instead of rejecting;
  - the market-action semantics: publish/repricing/metadata/restock/
    delist/relist/rate/reply/watch/unwatch/ask/answer move zero buyer
    entries, a purchase adds exactly one debit of the charged price and
    a refund adds exactly one credit of the refunded amount;
  - the gate family and its order: eight bad account forms answer
    E_AM_BAD_ACCOUNT, six bad limit forms answer E_AM_BAD_ARGS, the
    account gate precedes the limit gate, and every refusal freezes the
    seventeen table digests and the ledger tx set;
  - honest absence: an account the ledger never saw reports balance 0
    with balance_known False and an empty statement;
  - pure read (zero row mutations, zero token movement, pools frozen),
    three in-process runs byte-identical, and two full-stack restarts
    replaying both the default and a limited statement byte-identically;
  - the consumer: the settlement report's buyer block carries the
    statement verbatim, the buyer section renders it (escaped, with an
    honest empty state for an older block), the schema bumps additively,
    and delivery hygiene holds (runner label wired, pure ASCII source,
    no network imports, shipped configs unchanged).

Usage: python test_apimarket_buyerledger.py
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

ENVELOPE_KEYS = {"buyer_id", "balance", "balance_known", "entry_count",
                 "credit_total", "debit_total", "net", "limit",
                 "disclaimer", "entries"}

ROW_KEYS = {"tx_id", "ts_utc", "type", "action", "ref", "ref_type",
            "direction", "amount", "memo", "source_ai"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers", "apimarket_reviews")
POOLS = ("pool:reserve", "pool:share")

BAD_ACCOUNTS = [None, "", "bob", "USR:dana", " usr:dana", 99, True, []]
BAD_LIMITS = [0, -3, "5", True, 2.5, []]


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


def pool_balances(led):
    return {pool: led.balance(pool) for pool in POOLS}


def entry_totals(led, account_id):
    """Independent derivation of a statement from the ledger tables:
    count, credit sum and debit sum read straight out of sqlite."""
    conn = sqlite3.connect(led.db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*),"
            " COALESCE(SUM(CASE WHEN direction = 'credit' THEN amount"
            "  ELSE 0 END), 0),"
            " COALESCE(SUM(CASE WHEN direction = 'debit' THEN amount"
            "  ELSE 0 END), 0)"
            " FROM ledger_entries WHERE account_id = ?",
            (account_id,)).fetchone()
    finally:
        conn.close()
    return int(row[0]), int(row[1]), int(row[2])


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


def ledger_code(am, buyer_id, limit=None):
    try:
        if limit is None:
            am.api_buyer_ledger(buyer_id)
        else:
            am.api_buyer_ledger(buyer_id, limit)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3). bob and carol buy d1,
    bob buys d2, then carol refunds d1, so carols statement carries the
    funding credit, the purchase debit and one refund credit. usr:idle
    is a ledger account created with zero entries."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMLGB-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMLGB-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    led.ensure_account("usr:idle", census_avatar_id="idle")
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    clock.value = "2026-10-06T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-06T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    clock.value = "2026-10-06T00:00:10Z"
    p_bob_d1 = am.purchase_api("usr:bob", d1, "BUY-AMLGB-1")
    clock.value = "2026-10-06T00:00:11Z"
    p_carol_d1 = am.purchase_api("usr:carol", d1, "BUY-AMLGB-2")
    clock.value = "2026-10-06T00:00:12Z"
    p_bob_d2 = am.purchase_api("usr:bob", d2, "BUY-AMLGB-3")
    clock.value = "2026-10-06T00:00:13Z"
    am.refund_api("usr:carol", p_carol_d1["purchase_id"], "not needed")
    return {"d1": d1, "d2": d2,
            "p_bob_d1": p_bob_d1, "p_carol_d1": p_carol_d1,
            "p_bob_d2": p_bob_d2}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amamlgbb-")
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

        # -- AC-AMLGB1 contract and derived totals ----------------------
        env = am.api_buyer_ledger("usr:carol")
        rows = env["entries"]
        credits = sum(r["amount"] for r in rows
                      if r["direction"] == "credit")
        debits = sum(r["amount"] for r in rows
                     if r["direction"] == "debit")
        keys_ok = (set(env) == ENVELOPE_KEYS
                   and all(ROW_KEYS <= set(r) for r in rows)
                   and all(set(r) - ROW_KEYS in (set(), {"ai_label"})
                           for r in rows))
        totals_ok = (env["entry_count"] == len(rows)
                     and env["credit_total"] == credits
                     and env["debit_total"] == debits
                     and env["net"] == credits - debits
                     and env["buyer_id"] == "usr:carol"
                     and env["disclaimer"] == DISCLAIMER
                     and env["limit"] == 50)
        purchase_rows = [r for r in rows
                         if r["direction"] == "debit"]
        funding_rows = [r for r in rows
                        if r["ref_type"] == "manual"]
        ok1 = (keys_ok and totals_ok
               and len(rows) == 3
               and len(purchase_rows) == 1
               and len(funding_rows) == 1
               and env["balance"] == 300
               and env["credit_total"] == 310
               and env["debit_total"] == 10
               and env["net"] == 300)
        record("AC-AMLGB1", ok1,
               "keys=%r count=%d credit=%d debit=%d net=%d balance=%d"
               % (keys_ok, env["entry_count"], env["credit_total"],
                  env["debit_total"], env["net"], env["balance"]))

        # -- AC-AMLGB2 balance seam, isolation, live movement -----------
        seam_ok = (env["balance"] == led.balance("usr:carol")["balance"]
                   and env["balance_known"] is True)
        counts = entry_totals(led, "usr:carol")
        independent_ok = (counts == (env["entry_count"],
                                     env["credit_total"],
                                     env["debit_total"]))
        bob_env = am.api_buyer_ledger("usr:bob")
        bob_counts = entry_totals(led, "usr:bob")
        bob_refs = set(r["ref"] for r in bob_env["entries"])
        carol_refs = set(r["ref"] for r in env["entries"])
        bob_ok = ((bob_env["entry_count"], bob_env["credit_total"],
                   bob_env["debit_total"]) == bob_counts
                  and bob_env["entry_count"] == 3
                  and "BUY-AMLGB-2" not in bob_refs
                  and "BUY-AMLGB-1" not in carol_refs
                  and "BUY-AMLGB-3" not in carol_refs)
        clock.value = "2026-10-06T00:00:40Z"
        d3 = am.publish_api("usr:dana", "cheap-scan", "Cheap Scan API",
                            "a five token listing", PAYLOAD, 5, False)[
                                "listing_id"]
        clock.value = "2026-10-06T00:00:41Z"
        bought3 = am.purchase_api("usr:carol", d3, "BUY-AMLGB-4")
        after_buy = am.api_buyer_ledger("usr:carol")
        buy_ok = (after_buy["balance"] == env["balance"] - 5
                  and after_buy["entry_count"] == env["entry_count"] + 1
                  and after_buy["entries"][0]["direction"] == "debit"
                  and after_buy["entries"][0]["amount"] == 5
                  and after_buy["entries"][0]["ref"] == "BUY-AMLGB-4")
        clock.value = "2026-10-06T00:00:42Z"
        am.refund_api("usr:carol", bought3["purchase_id"], "wrong plan")
        after_refund = am.api_buyer_ledger("usr:carol")
        refund_ok = (after_refund["balance"] == env["balance"]
                     and after_refund["entry_count"]
                     == env["entry_count"] + 2
                     and after_refund["entries"][0]["direction"]
                     == "credit"
                     and after_refund["entries"][0]["amount"] == 5)
        ok2 = (seam_ok and independent_ok and bob_ok and buy_ok
               and refund_ok)
        record("AC-AMLGB2", ok2,
               "seam=%r independent=%r bob=%r buy=%r refund=%r"
               % (seam_ok, independent_ok, bob_ok, buy_ok, refund_ok))

        # -- AC-AMLGB3 order and oldest-tail truncation -----------------
        full = am.api_buyer_ledger("usr:carol", 500)
        stamps = [r["ts_utc"] for r in full["entries"]]
        ordered = all(stamps[i] >= stamps[i + 1]
                      for i in range(len(stamps) - 1))
        one = am.api_buyer_ledger("usr:carol", 1)
        three = am.api_buyer_ledger("usr:carol", 3)
        big = am.api_buyer_ledger("usr:carol", 999)
        clamp_ok = (big["limit"] == 500
                    and big["entries"] == full["entries"])
        ok3 = (ordered
               and full["limit"] == 500
               and full["entry_count"] == 5
               and one["entries"] == full["entries"][:1]
               and one["entry_count"] == 1
               and three["entries"] == full["entries"][:3]
               and three["entry_count"] == 3
               and clamp_ok
               and one["debit_total"]
               == sum(r["amount"] for r in one["entries"]
                      if r["direction"] == "debit")
               and three["credit_total"]
               == sum(r["amount"] for r in three["entries"]
                      if r["direction"] == "credit"))
        record("AC-AMLGB3", ok3,
               "ordered=%r full=%d one=%r three_prefix=%r clamp=%r"
               % (ordered, full["entry_count"],
                  one["entries"] == full["entries"][:1],
                  three["entries"] == full["entries"][:3], clamp_ok))

        # -- AC-AMLGB4 market action semantics --------------------------
        base = am.api_buyer_ledger("usr:bob", 500)
        base_count = base["entry_count"]
        base_balance = base["balance"]
        clock.value = "2026-10-06T00:00:50Z"
        d4 = am.publish_api("usr:dana", "fresh-api", "Fresh API",
                            "a newly published listing", PAYLOAD, 6,
                            False, supply=2)["listing_id"]
        clock.value = "2026-10-06T00:00:51Z"
        am.revise_price("usr:dana", d4, 7)
        clock.value = "2026-10-06T00:00:52Z"
        am.edit_listing("usr:dana", d4, title="Fresh API v2")
        clock.value = "2026-10-06T00:00:53Z"
        am.restock_api("usr:dana", d4, 3)
        clock.value = "2026-10-06T00:00:54Z"
        am.delist_api("usr:dana", d4)
        clock.value = "2026-10-06T00:00:55Z"
        am.relist_api("usr:dana", d4)
        rated = am.rate_api("usr:bob", ids["d1"], 5)
        am.reply_to_rating("usr:dana", rated["rating_id"], "thanks")
        am.watch_api("usr:bob", ids["d2"])
        am.unwatch_api("usr:bob", ids["d2"])
        question = am.ask_question("usr:bob", ids["d2"],
                                   "does it support hourly calls?")
        am.answer_question("usr:dana", question["question_id"], "yes")
        after_maintenance = am.api_buyer_ledger("usr:bob", 500)
        zero_ok = (after_maintenance["entry_count"] == base_count
                   and after_maintenance["balance"] == base_balance)
        clock.value = "2026-10-06T00:01:00Z"
        bought = am.purchase_api("usr:bob", d4, "BUY-AMLGB-5")
        after_buy = am.api_buyer_ledger("usr:bob", 500)
        newest = after_buy["entries"][0]
        buy_ok = (after_buy["entry_count"] == base_count + 1
                  and newest["direction"] == "debit"
                  and newest["amount"] == bought["price_paid"]
                  and newest["ref"] == "BUY-AMLGB-5")
        clock.value = "2026-10-06T00:01:01Z"
        am.refund_api("usr:bob", bought["purchase_id"], "changed mind")
        after_refund = am.api_buyer_ledger("usr:bob", 500)
        newest_refund = after_refund["entries"][0]
        refund_ok = (after_refund["entry_count"] == base_count + 2
                     and newest_refund["direction"] == "credit"
                     and newest_refund["amount"] == bought["price_paid"]
                     and after_refund["balance"] == base_balance)
        ok4 = zero_ok and buy_ok and refund_ok
        record("AC-AMLGB4", ok4,
               "base=%d maintenance=%d buy=%d refund=%d"
               " debit=%r credit=%r balance=%d"
               % (base_count, after_maintenance["entry_count"],
                  after_buy["entry_count"], after_refund["entry_count"],
                  buy_ok, refund_ok, after_refund["balance"]))

        # -- AC-AMLGB5 gate family and gate order -----------------------
        before5 = frozen_digests(am)
        before_tx5 = ledger_tx_ids(led)
        acct_codes = [ledger_code(am, v) for v in BAD_ACCOUNTS]
        limit_codes = [ledger_code(am, "usr:carol", v)
                       for v in BAD_LIMITS]
        order_code = ledger_code(am, "bob", 0)
        after5 = frozen_digests(am)
        ok5 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
               and limit_codes == ["E_AM_BAD_ARGS"] * len(BAD_LIMITS)
               and order_code == "E_AM_BAD_ACCOUNT"
               and before5 == after5
               and ledger_tx_ids(led) == before_tx5)
        record("AC-AMLGB5", ok5,
               "acct=%r limit=%r order=%r digests_frozen=%r tx_frozen=%r"
               % (acct_codes, limit_codes, order_code,
                  before5 == after5, ledger_tx_ids(led) == before_tx5))

        # -- AC-AMLGB6 honest absence -----------------------------------
        ghost = am.api_buyer_ledger("usr:nobody")
        idle = am.api_buyer_ledger("usr:idle")
        ok6 = (ghost["balance"] == 0
               and ghost["balance_known"] is False
               and ghost["entry_count"] == 0
               and ghost["credit_total"] == 0
               and ghost["debit_total"] == 0
               and ghost["net"] == 0
               and ghost["entries"] == []
               and idle["balance"] == 0
               and idle["balance_known"] is True
               and idle["entries"] == []
               and idle["disclaimer"] == DISCLAIMER)
        record("AC-AMLGB6", ok6,
               "ghost=%r idle_known=%r idle_rows=%d"
               % (ghost["balance_known"], idle["balance_known"],
                  idle["entry_count"]))

        # -- AC-AMLGB7 pure read and cross-restart byte identity --------
        before7 = frozen_digests(am)
        before_tx7 = ledger_tx_ids(led)
        before_pools7 = pool_balances(led)
        runs = [dumps(am.api_buyer_ledger("usr:carol", 3))
                for _ in range(3)]
        after7 = frozen_digests(am)
        pure_ok = (len(set(runs)) == 1
                   and before7 == after7
                   and ledger_tx_ids(led) == before_tx7
                   and pool_balances(led) == before_pools7)
        baseline_all = dumps(am.api_buyer_ledger("usr:carol", 500))
        baseline_three = runs[0]
        idle_base = dumps(am.api_buyer_ledger("usr:idle"))
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_buyer_ledger("usr:carol", 500)))
            replays.append(dumps(am2.api_buyer_ledger("usr:carol", 3)))
            replays.append(dumps(am2.api_buyer_ledger("usr:idle")))
            close_stack(am2, dk2, metered2, led2)
        ok7 = (pure_ok
               and replays[0] == baseline_all
               and replays[3] == baseline_all
               and replays[0] == replays[3]
               and replays[1] == baseline_three
               and replays[4] == baseline_three
               and replays[1] == replays[4]
               and replays[2] == idle_base
               and replays[5] == idle_base)
        record("AC-AMLGB7", ok7,
               "pure=%r restart_all=%r restart_limited=%r idle=%r"
               % (pure_ok, replays[0] == replays[3],
                  replays[1] == replays[4], replays[2] == replays[5]))

        # -- AC-AMLGB8 consumer, additive schema and delivery hygiene --
        led3, metered3, dk3, gate3, am3 = build_stack(
            db_path, cfg, lobby_cfg)
        try:
            led3.spend("usr:carol", 1, "SPEND-AMLGB-1",
                       memo="<script>alert(1)</script>")
            report = RPT.collect(am3)
            block = report["buyers"]["usr:carol"]["ledger"]
            same = dumps(block) == dumps(am3.api_buyer_ledger("usr:carol"))
            page = RPT.render_html(report)
            page_ok = ("ledger statement (balance" in page
                       and "<script>alert(1)</script>" not in page
                       and "&lt;script&gt;" in page)
            payload = RPT.api_report_payload(report)
            schema_ok = (payload["schema_version"] == RPT.REPORT_SCHEMA
                         and RPT.REPORT_SCHEMA >= 16
                         and set(payload) == {"schema_version", "report",
                                              "attention"})
            legacy = json.loads(json.dumps(report))
            for name in legacy["buyers"]:
                legacy["buyers"][name].pop("ledger", None)
            legacy_page = RPT.render_html(legacy)
            legacy_ok = RPT.LEDGER_EMPTY in legacy_page
        finally:
            close_stack(am3, dk3, metered3, led3)
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-buyerledger"' in handle.read())
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
        ok8 = (same and page_ok and schema_ok and legacy_ok and wired
               and ascii_ok and net_ok and shipped_ok and outside_ok)
        record("AC-AMLGB8", ok8,
               "same=%r page=%r schema=%r legacy=%r wired=%r ascii=%r"
               " no_net=%r shipped=%r outside=%r"
               % (same, page_ok, schema_ok, legacy_ok, wired, ascii_ok,
                  net_ok, shipped_ok, outside_ok))

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