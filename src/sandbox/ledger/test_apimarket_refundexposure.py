"""Acceptance suite for the apimarket seller-side refund exposure read
face (BigDomain R2115; canon = the explore-queue row claimed in R2115,
criteria AC-RPX1..AC-RPX8 registered in that claim note BEFORE this
suite existed - honesty note: the product implementation preceded the
criteria text inside the same window, disclosed in the row; the AC-RPX
prefix, the api_refund_exposure name, _seller_balance, this suite name,
the ledger-apimarket-refundexposure runner label and the refund_risk
attention family were all git-grep -F zero-occupancy anchored
2026-10-25, rc=1).

Face under proof: APIMarketFace.api_refund_exposure. refund_api fails
closed with E_AM_REFUND_UNFUNDABLE when the seller already spent the
proceeds, but no face warned anyone the money to fund the reversal was
gone. This slot pins the warning face:

  - a seven-key envelope and a nine-key row, the row set authority the
    listing table (every distinct seller appears, zero-sale sellers
    included), rows a total order on dev_account;
  - the liability law: unrefunded purchases' stored dev_share, never
    recomputed from a price, so a repricing moves it by nothing;
  - conservation: envelope totals equal the row sums and at_risk_count
    counts exactly the shortfall-bearing rows;
  - the refund dynamics: a reversal removes its own dev_share from the
    liability and lowers the seller balance by the same amount, so the
    shortfall itself does not move through a refund;
  - the funding law: an underfunded seller shows the exact shortfall
    and covered False, a topped-up seller clears, and a seller with no
    ledger account reports balance 0 with balance_known False instead
    of raising;
  - retirement keeps the obligation;
  - the account gate before any read, fail-closed with frozen digests;
  - zero row mutations and zero token movement (pure read);
  - cross-restart byte identity;
  - the consumer proof: the settlement report's attention digest grows
    a refund_risk family and REPORT_SCHEMA moves 7 -> 8 additively, so
    the face is not shipped in the no-consumer idle form.

Usage: python test_apimarket_refundexposure.py
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

ENVELOPE_KEYS = {"dev_account", "seller_count", "total_liability",
                 "total_shortfall", "at_risk_count", "disclaimer",
                 "rows"}

ROW_KEYS = {"dev_account", "listing_count", "open_purchases",
            "refunded_purchases", "refundable_liability", "balance",
            "balance_known", "shortfall", "covered"}

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


def row_of(env, dev_account):
    found = [r for r in env["rows"] if r["dev_account"] == dev_account]
    return found[0] if found else None


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


def exposure_code(am, dev_account):
    try:
        am.api_refund_exposure(dev_account)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def independent_liability(am, dev_account):
    """Second, independent derivation of the liability: the same stored
    dev_share column read through NOT EXISTS against the refunds table,
    executed on a separate read-only connection."""
    conn = sqlite3.connect(am.db_path)
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(p.dev_share), 0), COUNT(*)"
            " FROM apimarket_purchases p"
            " JOIN apimarket_listings l"
            " ON l.listing_id = p.listing_id"
            " WHERE l.dev_account = ? AND NOT EXISTS ("
            "  SELECT 1 FROM apimarket_refunds f"
            "  WHERE f.purchase_id = p.purchase_id)",
            (dev_account,)).fetchone()
    finally:
        conn.close()
    return int(row[0]), int(row[1])


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3); frank owns d3
    (price 10); gina owns d4 (price 7, no sales); hermes owns d5, a
    listing row inserted straight into the table so the account the
    ledger never saw is exercised honestly."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-RPX-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-RPX-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
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
    d3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "render charts from data", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-06T00:00:04Z"
    d4 = am.publish_api("usr:gina", "quiet-api", "Quiet API",
                        "a listing nobody bought yet", PAYLOAD, 7,
                        False)["listing_id"]
    conn = sqlite3.connect(am.db_path)
    try:
        conn.execute(
            "INSERT INTO apimarket_listings (dev_account, listing_key,"
            " title, description, payload_json, token_price, ai_label,"
            " listed_utc, supply) VALUES (?,?,?,?,?,?,?,?,?)",
            ("usr:hermes", "ghost-api", "Ghost API",
             "a listing owned by an account the ledger never saw",
             json.dumps(PAYLOAD, sort_keys=True), 5, 0,
             "2026-10-06T00:00:05Z", None))
        conn.commit()
        d5 = int(conn.execute(
            "SELECT listing_id FROM apimarket_listings"
            " WHERE dev_account = 'usr:hermes'").fetchone()[0])
    finally:
        conn.close()
    clock.value = "2026-10-06T00:00:10Z"
    p_bob_d1 = am.purchase_api("usr:bob", d1, "BUY-RPX-1")[
        "purchase_id"]
    clock.value = "2026-10-06T00:00:11Z"
    p_carol_d1 = am.purchase_api("usr:carol", d1, "BUY-RPX-2")[
        "purchase_id"]
    clock.value = "2026-10-06T00:00:12Z"
    p_erin_d2 = am.purchase_api("usr:erin", d2, "BUY-RPX-3")[
        "purchase_id"]
    clock.value = "2026-10-06T00:00:13Z"
    am.purchase_api("usr:dave", d3, "BUY-RPX-4")
    return {"d1": d1, "d2": d2, "d3": d3, "d4": d4, "d5": d5,
            "p_bob_d1": p_bob_d1, "p_carol_d1": p_carol_d1,
            "p_erin_d2": p_erin_d2}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amrpx-")
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

        # -- AC-RPX1 contract and the dense row set ----------------------
        env = am.api_refund_exposure()
        keys_ok = set(env) == ENVELOPE_KEYS
        rows_ok = all(set(r) == ROW_KEYS for r in env["rows"])
        owners = [r["dev_account"] for r in env["rows"]]
        dense_ok = owners == sorted(owners) and set(owners) == {
            "usr:dana", "usr:frank", "usr:gina", "usr:hermes"}
        single = am.api_refund_exposure("usr:dana")
        single_ok = (single["seller_count"] == 1
                     and single["dev_account"] == "usr:dana"
                     and len(single["rows"]) == 1)
        hermes = row_of(env, "usr:hermes")
        dana = row_of(env, "usr:dana")
        ok1 = (keys_ok and rows_ok and dense_ok and single_ok
               and env["dev_account"] is None
               and env["disclaimer"] == DISCLAIMER
               and dana["listing_count"] == 2
               and hermes["listing_count"] == 1
               and hermes["balance"] == 0
               and hermes["balance_known"] is False
               and gina_ok(env))
        record("AC-RPX1", ok1,
               "keys=%r rows=%r owners=%r single=%r hermes_known=%r"
               % (keys_ok, rows_ok, owners, single_ok,
                  hermes["balance_known"]))

        # -- AC-RPX2 liability derivation and conservation ---------------
        dana_liab = dana["refundable_liability"]
        frank_liab = row_of(env, "usr:frank")["refundable_liability"]
        ind_dana = independent_liability(am, "usr:dana")
        ind_frank = independent_liability(am, "usr:frank")
        # price 10 -> 7/3; price 3 -> 3/0 (floor 2.1 is 2 but the
        # integer remainder law gives the first leg the extra unit), so
        # dana carries 7 + 7 + 3 = 17 on three open purchases.
        pinned = (dana_liab == 17 and dana["open_purchases"] == 3
                  and frank_liab == 7
                  and row_of(env, "usr:gina")["refundable_liability"]
                  == 0)
        cross = (ind_dana == (dana_liab, dana["open_purchases"])
                 and ind_frank == (frank_liab,
                                   row_of(env, "usr:frank")[
                                       "open_purchases"]))
        conserv = (env["total_liability"]
                   == sum(r["refundable_liability"]
                          for r in env["rows"])
                   and env["total_shortfall"]
                   == sum(r["shortfall"] for r in env["rows"])
                   and env["at_risk_count"]
                   == sum(1 for r in env["rows"] if r["shortfall"] > 0))
        clock.value = "2026-10-06T00:00:20Z"
        am.revise_price("usr:dana", ids["d1"], 20)
        am.edit_listing("usr:dana", ids["d1"], title="Risk Scan API v2")
        after_edit = am.api_refund_exposure()
        stable = (row_of(after_edit, "usr:dana")
                  ["refundable_liability"] == dana_liab)
        ok2 = (pinned and cross and conserv and stable
               and after_edit["total_liability"] == env["total_liability"])
        record("AC-RPX2", ok2,
               "dana_liab=%d frank_liab=%d pinned=%r cross=%r"
               " conserv=%r repricing_stable=%r total %r -> %r"
               % (dana_liab, frank_liab, pinned, cross, conserv,
                  stable, env["total_liability"],
                  after_edit["total_liability"]))

        # -- AC-RPX3 refund dynamics -------------------------------------
        before_r3 = am.api_refund_exposure()
        bal_before = led.balance("usr:dana")["balance"]
        clock.value = "2026-10-06T00:00:30Z"
        am.refund_api("usr:erin", ids["p_erin_d2"], "service unusable")
        after_r3 = am.api_refund_exposure()
        dana_r3 = row_of(after_r3, "usr:dana")
        bal_after = led.balance("usr:dana")["balance"]
        frank_r3 = row_of(after_r3, "usr:frank")
        frank_frozen = frank_r3 == row_of(before_r3, "usr:frank")
        ok3 = (dana_r3["refundable_liability"] == dana_liab - 3
               and dana_r3["open_purchases"] == 2
               and dana_r3["refunded_purchases"] == 1
               and bal_after == bal_before - 3
               and dana_r3["shortfall"]
               == row_of(before_r3, "usr:dana")["shortfall"]
               and frank_frozen)
        record("AC-RPX3", ok3,
               "liab %d->%d open=%d refunded=%d balance %d->%d"
               " shortfall_moved=%r frank_frozen=%r"
               % (dana_liab, dana_r3["refundable_liability"],
                  dana_r3["open_purchases"],
                  dana_r3["refunded_purchases"], bal_before,
                  bal_after,
                  dana_r3["shortfall"]
                  != row_of(before_r3, "usr:dana")["shortfall"],
                  frank_frozen))

        # -- AC-RPX4 funding states --------------------------------------
        exposure_now = am.api_refund_exposure("usr:dana")["rows"][0]
        liability_now = exposure_now["refundable_liability"]
        spend = liability_now - 4
        led.spend("usr:dana", spend, "SPEND-RPX-1")
        thin = am.api_refund_exposure("usr:dana")["rows"][0]
        thin_ok = (thin["shortfall"] == liability_now - thin["balance"]
                   and thin["shortfall"] > 0 and thin["covered"] is False
                   and thin["balance_known"] is True)
        top_up = thin["shortfall"]
        led.adjust([("pool:reserve", "debit", top_up),
                    ("usr:dana", "credit", top_up)],
                   "manual:topup-dana", "suite top-up")
        full = am.api_refund_exposure("usr:dana")["rows"][0]
        full_ok = (full["shortfall"] == 0
                   and full["covered"] is True
                   and full["balance"] >= full["refundable_liability"])
        hermes_row = row_of(am.api_refund_exposure(), "usr:hermes")
        ghost_ok = (hermes_row["balance"] == 0
                    and hermes_row["balance_known"] is False
                    and hermes_row["covered"] is True)
        ok4 = thin_ok and full_ok and ghost_ok
        record("AC-RPX4", ok4,
               "thin shortfall=%d covered=%r full shortfall=%d"
               " covered=%r hermes known=%r"
               % (thin["shortfall"], thin["covered"],
                  full["shortfall"], full["covered"],
                  hermes_row["balance_known"]))

        # -- AC-RPX5 retirement keeps the obligation ---------------------
        before_r5 = am.api_refund_exposure("usr:dana")
        clock.value = "2026-10-06T00:00:40Z"
        am.delist_api("usr:dana", ids["d1"])
        after_r5 = am.api_refund_exposure("usr:dana")
        ok5 = (after_r5["rows"][0]["refundable_liability"]
               == before_r5["rows"][0]["refundable_liability"]
               and after_r5["rows"][0]["open_purchases"]
               == before_r5["rows"][0]["open_purchases"]
               and am.api_view(ids["d1"])["delisted"] is True)
        record("AC-RPX5", ok5,
               "liability %d -> %d after delist, delisted=%r"
               % (before_r5["rows"][0]["refundable_liability"],
                  after_r5["rows"][0]["refundable_liability"],
                  am.api_view(ids["d1"])["delisted"]))
        clock.value = "2026-10-06T00:00:41Z"
        am.relist_api("usr:dana", ids["d1"])

        # -- AC-RPX6 gate family before any read -------------------------
        before6 = frozen_digests(am)
        before_tx6 = ledger_tx_ids(led)
        bad = [99, True, 2.5, "", [], {}, "bob", "USR:dana"]
        codes = [exposure_code(am, v) for v in bad]
        after6 = frozen_digests(am)
        gate_ok = (codes == ["E_AM_BAD_ACCOUNT"] * len(bad)
                   and before6 == after6
                   and ledger_tx_ids(led) == before_tx6)
        empty = am.api_refund_exposure("usr:nobody")
        empty_ok = (empty["seller_count"] == 0 and empty["rows"] == []
                    and empty["total_liability"] == 0
                    and empty["total_shortfall"] == 0
                    and empty["at_risk_count"] == 0
                    and empty["disclaimer"] == DISCLAIMER)
        ok6 = gate_ok and empty_ok
        record("AC-RPX6", ok6,
               "codes=%r digests_frozen=%r tx_frozen=%r empty=%r"
               % (codes, before6 == after6,
                  ledger_tx_ids(led) == before_tx6, empty_ok))

        # -- AC-RPX7 pure read and cross-restart byte identity -----------
        before7 = frozen_digests(am)
        before_tx7 = ledger_tx_ids(led)
        before_pools7 = pool_balances(led)
        runs = [dumps(am.api_refund_exposure()) for _ in range(3)]
        after7 = frozen_digests(am)
        pure_ok = (len(set(runs)) == 1
                   and before7 == after7
                   and ledger_tx_ids(led) == before_tx7
                   and pool_balances(led) == before_pools7)
        baseline = runs[0]
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_refund_exposure()))
            replays.append(dumps(am2.api_refund_exposure("usr:dana")))
            close_stack(am2, dk2, metered2, led2)
        ok7 = (pure_ok and replays[0] == baseline
               and replays[2] == baseline
               and replays[0] == replays[2]
               and replays[1] == replays[3]
               and json.loads(baseline)["disclaimer"] == DISCLAIMER)
        record("AC-RPX7", ok7,
               "pure=%r restart_identical=%r dana_identical=%r"
               % (pure_ok, replays[0] == replays[2],
                  replays[1] == replays[3]))

        # -- AC-RPX8 consumer and delivery -------------------------------
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
        # drive one seller under water so the consumer sees a real
        # finding: dana spends part of the proceeds she may owe back.
        led.spend("usr:dana", 5, "SPEND-RPX-2")
        exposure = am.api_refund_exposure()
        at_risk = sorted(r["dev_account"] for r in exposure["rows"]
                         if r["shortfall"] > 0)
        report = RPT.collect(am)
        attention = RPT.collect_attention(am, report)
        risk = [f for f in attention["findings"]
                if f["kind"] == "refund_risk"]
        others = [f for f in attention["findings"]
                  if f["kind"] != "refund_risk"]
        risk_ok = (sorted(f["subject"] for f in risk) == at_risk
                   and all(f["severity"] == "high" for f in risk)
                   and (not risk
                        or all("liability" in f["detail"]
                               for f in risk)))
        # the zero-shortfall world must produce no refund_risk finding
        covered_world = [f for f in risk
                         if f["subject"] in ("usr:frank", "usr:gina",
                                             "usr:hermes")]
        payload = RPT.api_report_payload(report)
        # birth station: this criterion pinned schema 8 when the
        # refund_risk family was born (R2115). R2116 added the seller
        # demand block as an ADDITIVE bump (8 -> 9), so the assertion
        # follows the module constant instead of pinning a literal while
        # still proving the envelope shape the additive rule promises.
        contract_ok = (RPT.REPORT_SCHEMA >= 8
                       and payload["schema_version"] == RPT.REPORT_SCHEMA
                       and set(payload) == {"schema_version", "report",
                                            "attention"}
                       and set(payload["report"]) == set(report))
        html = RPT.render_html(report)
        html_ok = ("refund_risk" in html) if risk else True
        heading_ok = "<th>kind</th>" in html
        wired = False
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = '"ledger-apimarket-refundexposure"' in handle.read()
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        shipped_ok = (shas_after[PRODUCT_FILES[2]]
                      == shas_before[PRODUCT_FILES[2]]
                      and shas_after[PRODUCT_FILES[3]]
                      == shas_before[PRODUCT_FILES[3]])
        ok8 = (risk_ok and not covered_world and contract_ok
               and heading_ok and (html_ok or not risk) and wired
               and shipped_ok and len(others) >= 0)
        record("AC-RPX8", ok8,
               "at_risk=%r risk_findings=%d severity_ok=%r"
               " contract=%r wired=%r shipped=%r"
               % (at_risk, len(risk), risk_ok, contract_ok, wired,
                  shipped_ok))

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


def gina_ok(env):
    gina = row_of(env, "usr:gina")
    return (gina is not None
            and gina["listing_count"] == 1
            and gina["open_purchases"] == 0
            and gina["refundable_liability"] == 0
            and gina["shortfall"] == 0
            and gina["covered"] is True)


if __name__ == "__main__":
    sys.exit(main())