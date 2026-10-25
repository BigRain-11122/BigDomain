"""Acceptance suite for the apimarket seller settlement statement face
(BigDomain R2126; canon = the explore-queue row claimed in R2126,
criteria AC-AMLG1..AC-AMLG8 registered in that claim note BEFORE this
suite existed; the AC-AMLG prefix, the api_seller_ledger name, this
suite name and the ledger-apimarket-sellerledger runner label were all
git grep -F zero-occupancy anchored 2026-10-25, rc=1).

Face under proof: APIMarketFace.api_seller_ledger. The market answered a
seller's gross rows, monthly cash, lifetime aggregates and refund
exposure, but no face answered "how much money do I have right now, and
which ledger entries produced it". ledger.bill was the only per-account
entry face and had zero product consumers. This slot pins the join:

  - a ten-key envelope and a ten/eleven-key row, entry_count equal to
    the row length, credit/debit totals derived from the rows and net
    equal to their difference;
  - the balance read through the single _seller_balance seam, equal to
    the ledger face value and moving immediately with a new entry;
  - account isolation proven against an independent sqlite read of the
    ledger entries (count and both direction totals);
  - newest-first order with the limit truncating the OLDEST tail (a
    prefix law) and an over-cap limit clamping instead of rejecting;
  - the market-action semantics: a purchase adds exactly one credit of
    the stored dev_share, a refund adds exactly one debit of the same
    amount, and publish/repricing/metadata/restock/delist/relist move
    zero entries;
  - the gate family and its order: eight bad account forms answer
    E_AM_BAD_ACCOUNT, six bad limit forms answer E_AM_BAD_ARGS, the
    account gate precedes the limit gate, and every refusal freezes the
    seventeen table digests and the ledger tx set;
  - honest absence: an account the ledger never saw reports balance 0
    with balance_known False and an empty statement;
  - pure read (zero row mutations, zero token movement, pools frozen),
    two in-process runs byte-identical, and two full-stack restarts
    replaying both the default and a limited statement byte-identically;
  - delivery hygiene: shipped configs unchanged, runner label wired,
    suite source pure ASCII, no network imports.

Usage: python test_apimarket_sellerledger.py
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

ENVELOPE_KEYS = {"dev_account", "balance", "balance_known", "entry_count",
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


def ledger_code(am, dev_account, limit=None):
    try:
        if limit is None:
            am.api_seller_ledger(dev_account)
        else:
            am.api_seller_ledger(dev_account, limit)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3). bob and carol buy d1,
    bob buys d2, then carol refunds d1 so the statement carries both a
    credit family and one debit. gina owns a listing with no sales, and
    usr:idle is a ledger account created with zero entries."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMLG-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMLG-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    led.ensure_account("usr:idle", census_avatar_id="idle")
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:gina", "gina-key", 10, ["backtest"], False)
    clock.value = "2026-10-06T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-06T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    clock.value = "2026-10-06T00:00:03Z"
    d3 = am.publish_api("usr:gina", "quiet-api", "Quiet API",
                        "a listing nobody bought yet", PAYLOAD, 7,
                        False)["listing_id"]
    clock.value = "2026-10-06T00:00:10Z"
    p_bob_d1 = am.purchase_api("usr:bob", d1, "BUY-AMLG-1")
    clock.value = "2026-10-06T00:00:11Z"
    p_carol_d1 = am.purchase_api("usr:carol", d1, "BUY-AMLG-2")
    clock.value = "2026-10-06T00:00:12Z"
    p_bob_d2 = am.purchase_api("usr:bob", d2, "BUY-AMLG-3")
    clock.value = "2026-10-06T00:00:13Z"
    am.refund_api("usr:carol", p_carol_d1["purchase_id"], "not needed")
    return {"d1": d1, "d2": d2, "d3": d3,
            "p_bob_d1": p_bob_d1, "p_carol_d1": p_carol_d1,
            "p_bob_d2": p_bob_d2}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amamlg-")
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

        # -- AC-AMLG1 contract and derived totals ------------------------
        env = am.api_seller_ledger("usr:dana")
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
                     and env["dev_account"] == "usr:dana"
                     and env["disclaimer"] == DISCLAIMER
                     and env["limit"] == 50)
        debit_rows = [r for r in rows if r["direction"] == "debit"]
        purchase_rows = [r for r in rows
                         if r["action"] == "apimarket_dev_share"]
        ok1 = (keys_ok and totals_ok
               and len(purchase_rows) == 3
               and len(debit_rows) == 1
               and all(r["source_ai"] is False for r in rows))
        record("AC-AMLG1", ok1,
               "keys=%r count=%d credit=%d debit=%d net=%d rows=%d"
               % (keys_ok, env["entry_count"], env["credit_total"],
                  env["debit_total"], env["net"], len(rows)))

        # -- AC-AMLG2 balance seam and account isolation ----------------
        seam_ok = (env["balance"] == led.balance("usr:dana")["balance"]
                   and env["balance_known"] is True)
        counts = entry_totals(led, "usr:dana")
        independent_ok = (counts == (env["entry_count"],
                                     env["credit_total"],
                                     env["debit_total"]))
        bob_env = am.api_seller_ledger("usr:bob")
        bob_counts = entry_totals(led, "usr:bob")
        bob_ok = ((bob_env["entry_count"], bob_env["credit_total"],
                   bob_env["debit_total"]) == bob_counts
                  and bob_env["entry_count"] > 0
                  and all(r["ref"] != "apimarket:share:BUY-AMLG-9"
                          for r in bob_env["entries"]))
        before_bal = env["balance"]
        led.spend("usr:dana", 4, "SPEND-AMLG-1")
        after = am.api_seller_ledger("usr:dana")
        live_ok = (after["balance"] == before_bal - 4
                   and after["entry_count"] == env["entry_count"] + 1
                   and after["entries"][0]["ref"] == "SPEND-AMLG-1"
                   and after["entries"][0]["direction"] == "debit"
                   and after["entries"][0]["amount"] == 4)
        ok2 = (seam_ok and independent_ok and bob_ok and live_ok)
        record("AC-AMLG2", ok2,
               "seam=%r independent=%r bob=%r live=%r"
               % (seam_ok, independent_ok, bob_ok, live_ok))

        # -- AC-AMLG3 order and oldest-tail truncation ------------------
        full = am.api_seller_ledger("usr:dana", 500)
        stamps = [r["ts_utc"] for r in full["entries"]]
        ordered = all(stamps[i] >= stamps[i + 1]
                      for i in range(len(stamps) - 1))
        one = am.api_seller_ledger("usr:dana", 1)
        three = am.api_seller_ledger("usr:dana", 3)
        big = am.api_seller_ledger("usr:dana", 999)
        clamp_ok = (big["limit"] == 500
                    and big["entries"] == full["entries"])
        ok3 = (ordered
               and full["limit"] == 500
               and one["entries"] == full["entries"][:1]
               and one["entry_count"] == 1
               and three["entries"] == full["entries"][:3]
               and three["entry_count"] == 3
               and clamp_ok
               and one["credit_total"]
               == sum(r["amount"] for r in one["entries"]
                      if r["direction"] == "credit"))
        record("AC-AMLG3", ok3,
               "ordered=%r full=%d one=%r three_prefix=%r clamp=%r"
               % (ordered, full["entry_count"],
                  one["entries"] == full["entries"][:1],
                  three["entries"] == full["entries"][:3], clamp_ok))

        # -- AC-AMLG4 market action semantics ---------------------------
        base = am.api_seller_ledger("usr:dana", 500)
        base_count = base["entry_count"]
        clock.value = "2026-10-06T00:00:20Z"
        d4 = am.publish_api("usr:dana", "fresh-api", "Fresh API",
                            "a newly published listing", PAYLOAD, 6,
                            False, supply=2)["listing_id"]
        after_publish = am.api_seller_ledger("usr:dana", 500)
        clock.value = "2026-10-06T00:00:21Z"
        am.revise_price("usr:dana", ids["d1"], 12)
        clock.value = "2026-10-06T00:00:22Z"
        am.edit_listing("usr:dana", ids["d1"], title="Risk Scan API v2")
        clock.value = "2026-10-06T00:00:23Z"
        am.restock_api("usr:dana", d4, 3)
        clock.value = "2026-10-06T00:00:24Z"
        am.delist_api("usr:dana", d4)
        clock.value = "2026-10-06T00:00:25Z"
        am.relist_api("usr:dana", d4)
        after_maintenance = am.api_seller_ledger("usr:dana", 500)
        clock.value = "2026-10-06T00:00:30Z"
        bought = am.purchase_api("usr:carol", d4, "BUY-AMLG-4")
        after_buy = am.api_seller_ledger("usr:dana", 500)
        newest = after_buy["entries"][0]
        clock.value = "2026-10-06T00:00:31Z"
        am.refund_api("usr:carol", bought["purchase_id"], "changed mind")
        after_refund = am.api_seller_ledger("usr:dana", 500)
        newest_refund = after_refund["entries"][0]
        ok4 = (after_publish["entry_count"] == base_count
               and after_maintenance["entry_count"] == base_count
               and after_buy["entry_count"] == base_count + 1
               and newest["direction"] == "credit"
               and newest["amount"] == bought["dev_share"]
               and newest["action"] == "apimarket_dev_share"
               and after_refund["entry_count"] == base_count + 2
               and newest_refund["direction"] == "debit"
               and newest_refund["amount"] == bought["dev_share"]
               and newest_refund["type"] == "adjust")
        record("AC-AMLG4", ok4,
               "base=%d publish=%d maintenance=%d buy=%d refund=%d"
               " credit=%r debit=%r"
               % (base_count, after_publish["entry_count"],
                  after_maintenance["entry_count"],
                  after_buy["entry_count"], after_refund["entry_count"],
                  newest["amount"] == bought["dev_share"],
                  newest_refund["amount"] == bought["dev_share"]))

        # -- AC-AMLG5 gate family and gate order ------------------------
        before5 = frozen_digests(am)
        before_tx5 = ledger_tx_ids(led)
        acct_codes = [ledger_code(am, v) for v in BAD_ACCOUNTS]
        limit_codes = [ledger_code(am, "usr:dana", v) for v in BAD_LIMITS]
        order_code = ledger_code(am, "bob", 0)
        after5 = frozen_digests(am)
        ok5 = (acct_codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
               and limit_codes == ["E_AM_BAD_ARGS"] * len(BAD_LIMITS)
               and order_code == "E_AM_BAD_ACCOUNT"
               and before5 == after5
               and ledger_tx_ids(led) == before_tx5)
        record("AC-AMLG5", ok5,
               "acct=%r limit=%r order=%r digests_frozen=%r tx_frozen=%r"
               % (acct_codes, limit_codes, order_code,
                  before5 == after5, ledger_tx_ids(led) == before_tx5))

        # -- AC-AMLG6 honest absence ------------------------------------
        ghost = am.api_seller_ledger("usr:nobody")
        idle = am.api_seller_ledger("usr:idle")
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
        record("AC-AMLG6", ok6,
               "ghost=%r idle_known=%r idle_rows=%d"
               % (ghost["balance_known"], idle["balance_known"],
                  idle["entry_count"]))

        # -- AC-AMLG7 pure read and cross-restart byte identity ----------
        before7 = frozen_digests(am)
        before_tx7 = ledger_tx_ids(led)
        before_pools7 = pool_balances(led)
        runs = [dumps(am.api_seller_ledger("usr:dana", 5))
                for _ in range(3)]
        after7 = frozen_digests(am)
        pure_ok = (len(set(runs)) == 1
                   and before7 == after7
                   and ledger_tx_ids(led) == before_tx7
                   and pool_balances(led) == before_pools7)
        baseline_all = dumps(am.api_seller_ledger("usr:dana", 500))
        baseline_five = runs[0]
        idle_base = dumps(am.api_seller_ledger("usr:idle"))
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_seller_ledger("usr:dana", 500)))
            replays.append(dumps(am2.api_seller_ledger("usr:dana", 5)))
            replays.append(dumps(am2.api_seller_ledger("usr:idle")))
            close_stack(am2, dk2, metered2, led2)
        ok7 = (pure_ok
               and replays[0] == baseline_all
               and replays[3] == baseline_all
               and replays[0] == replays[3]
               and replays[1] == baseline_five
               and replays[4] == baseline_five
               and replays[1] == replays[4]
               and replays[2] == idle_base
               and replays[5] == idle_base)
        record("AC-AMLG7", ok7,
               "pure=%r restart_all=%r restart_limited=%r idle=%r"
               % (pure_ok, replays[0] == replays[3],
                  replays[1] == replays[4], replays[2] == replays[5]))

        # -- AC-AMLG8 delivery hygiene ----------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-sellerledger"' in handle.read())
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
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        shipped_ok = (shas_after[PRODUCT_FILES[2]]
                      == shas_before[PRODUCT_FILES[2]]
                      and shas_after[PRODUCT_FILES[3]]
                      == shas_before[PRODUCT_FILES[3]])
        ok8 = wired and ascii_ok and net_ok and shipped_ok
        record("AC-AMLG8", ok8,
               "wired=%r ascii=%r no_net_import=%r shipped=%r"
               % (wired, ascii_ok, net_ok, shipped_ok))

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