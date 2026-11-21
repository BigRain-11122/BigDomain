"""Acceptance suite for the apimarket market-wide seller REGISTER churn
face (BigDomain R3159; canon = the R2248 d explore-queue seed row and the
R3159 PIN row, which pinned every criterion BEFORE this code existed).

Face under proof: APIMarketFace.api_market_seller_churn_months.

The shipped family already answers breadth (api_market_supply_months
reports a month-end seller_count) and first-listing cohorts
(api_market_seller_cohort), but the cohort grid only carries months with a
listing EVENT, so the month in which two sellers left and nobody listed has
no row at all, and neither face answers who joined or left the register,
whether a seller left entirely or only pulled one shelf, or how long a
departing seller had been in the register.

Private world (six months, four sellers):
  alice  a1 (supply 2) listed 01-05, a2 (supply 1) listed 01-10;
         a1 retired 02-15 (she stays via a2 = RETREATING), a2 retired
         03-10 (she leaves the register = DEPARTED, tenure 2)
  dana   d1 (supply 1) listed 01-20 and SOLD OUT by a buyer on 01-25, yet
         she stays in the register every month (a shelf is alive, empty)
  bob    b1 listed 02-03 (NEW), retired 03-20 (DEPARTED, tenure 1),
         re-listed 04-05 (RETURNING, not new, and EXPANDING)
  carol  c1 listed 06-01 (NEW); 2026-05 has NO membership event at all and
         must still carry an honest zero-change row.

Given that world the face must read:
  JAN active 2 joined 2 new 2 departed 0 rates None (bootstrap month)
  FEB active 3 joined 1 new 1 departed 0 retreating 1 expanding 1
  MAR active 1 joined 0 departed 2 tenure mean 1.5 retreating 0
  APR active 2 joined 1 new 0 returning 1 expanding 1
  MAY active 2 joined 0 departed 0 retention 1.0 churn 0.0
  JUN active 3 joined 1 new 1 expanding 1 (peak tie with FEB -> FEB wins)

Usage: python test_apimarket_sellerchurnmonths.py
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

ENVELOPE_KEYS = {
    "scope", "month_count", "active_month_count", "seller_count",
    "joined_count", "new_seller_count", "returning_seller_count",
    "departed_count", "retreating_count", "expanding_count",
    "mean_tenure_of_departed_months",
    "longest_departed_tenure_months", "peak_month",
    "peak_active_seller_count", "first_month", "last_month",
    "latest_month_active_seller_count", "latest_month_joined_count",
    "latest_month_departed_count", "net_seller_change", "disclaimer",
    "months"}

ROW_KEYS = {
    "month", "as_of", "active_seller_count", "joined_seller_count",
    "new_seller_count", "returning_seller_count",
    "departed_seller_count", "departed_tenure_months_mean",
    "retention_rate", "churn_rate", "retreating_seller_count",
    "expanding_seller_count", "net_change", "running_joined_count",
    "running_departed_count"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_supply_revisions")


class Clock(object):
    def __init__(self):
        self.value = "2026-01-05T00:00:00Z"

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


def market_digests(am):
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


def month_row(env, month):
    for row in env["months"]:
        if row["month"] == month:
            return row
    raise AssertionError("month %r missing from months" % (month,))


def fund(led, *names):
    for who in names:
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:" + who, "credit", 500)],
                   "manual:fund-" + who, "suite funding " + who)


def seed_world(led, dk, am, clock):
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SSC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SSC-S",
                     "settlement")
    for dev in ("alice", "bob", "dana", "carol"):
        dk.issue_key("usr:" + dev, dev + "-key", 10, ["backtest"],
                     False)
    fund(led, "buyer")

    clock.value = "2026-01-05T00:00:00Z"
    a1 = am.publish_api("usr:alice", "a1", "Alice One",
                        "alice one payload", PAYLOAD, 10, False,
                        supply=2, category="tools")["listing_id"]
    clock.value = "2026-01-10T00:00:00Z"
    a2 = am.publish_api("usr:alice", "a2", "Alice Two",
                        "alice two payload", PAYLOAD, 10, False,
                        supply=1, category="data")["listing_id"]
    clock.value = "2026-01-20T00:00:00Z"
    d1 = am.publish_api("usr:dana", "d1", "Dana One",
                        "dana one payload", PAYLOAD, 10, False,
                        supply=1, category="tools")["listing_id"]
    clock.value = "2026-01-25T00:00:00Z"
    am.purchase_api("usr:buyer", d1, "ref-buyer-d1")

    clock.value = "2026-02-03T00:00:00Z"
    b1 = am.publish_api("usr:bob", "b1", "Bob One",
                        "bob one payload", PAYLOAD, 10, False,
                        supply=1, category="data")["listing_id"]
    clock.value = "2026-02-15T00:00:00Z"
    am.delist_api("usr:alice", a1)
    clock.value = "2026-03-10T00:00:00Z"
    am.delist_api("usr:alice", a2)
    clock.value = "2026-03-20T00:00:00Z"
    am.delist_api("usr:bob", b1)
    clock.value = "2026-04-05T00:00:00Z"
    am.relist_api("usr:bob", b1)
    clock.value = "2026-06-01T00:00:00Z"
    am.publish_api("usr:carol", "c1", "Carol One",
                   "carol one payload", PAYLOAD, 10, False,
                   supply=1, category="tools")
    return {"a1": a1, "a2": a2, "b1": b1, "d1": d1}


def seed_gap_world(led, dk, am, clock):
    """One seller who leaves for a whole month and comes back, so the grid
    holds a ZERO-active month that must never be a peak and whose churn
    reads 1.0 rather than None."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SSC-GA",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SSC-GS",
                     "settlement")
    dk.issue_key("usr:hana", "hana-key", 10, ["backtest"], False)
    clock.value = "2026-01-05T00:00:00Z"
    h1 = am.publish_api("usr:hana", "h1", "Hana One",
                        "hana one payload", PAYLOAD, 10, False,
                        supply=1, category="tools")["listing_id"]
    clock.value = "2026-02-10T00:00:00Z"
    am.delist_api("usr:hana", h1)
    clock.value = "2026-03-10T00:00:00Z"
    am.relist_api("usr:hana", h1)


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerchurn-")
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
        return run(db_path, cfg, lobby_cfg, shas_before, clock)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before, clock):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    ids = seed_world(led, dk, am, clock)

    empty_tmp = tempfile.mkdtemp(prefix="apimarket-ssc-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_seller_churn_months()
    close_stack(e_am, e_dk, e_metered, e_led)

    gap_tmp = tempfile.mkdtemp(prefix="apimarket-ssc-gap-")
    g_clock = Clock()
    A._now_utc = g_clock.now_utc
    g_led, g_metered, g_dk, _g_gate, g_am = build_stack(
        os.path.join(gap_tmp, "ledger.db"), cfg, lobby_cfg)
    seed_gap_world(g_led, g_dk, g_am, g_clock)
    A._now_utc = clock.now_utc
    gap = g_am.api_market_seller_churn_months()

    env = am.api_market_seller_churn_months()

    # -- AC-SSC1 contract, honest empty, no-argument market face ------
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    arg_rejected = False
    try:
        am.api_market_seller_churn_months("2026-01")
    except TypeError:
        arg_rejected = True
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and len(env) == 22
           and rows_ok
           and all(len(row) == 15 for row in env["months"])
           and env["scope"] == "market"
           and env["disclaimer"] == DISCLAIMER
           and set(empty.keys()) == ENVELOPE_KEYS
           and empty["month_count"] == 0
           and empty["active_month_count"] == 0
           and empty["months"] == []
           and empty["seller_count"] == 0
           and empty["joined_count"] == 0
           and empty["departed_count"] == 0
           and empty["retreating_count"] == 0
           and empty["expanding_count"] == 0
           and empty["mean_tenure_of_departed_months"] is None
           and empty["longest_departed_tenure_months"] is None
           and empty["peak_month"] is None
           and empty["peak_active_seller_count"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["net_seller_change"] is None
           and empty["latest_month_active_seller_count"] == 0
           and arg_rejected)
    record("AC-SSC1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              len(env["months"]),
              (empty["month_count"], empty["seller_count"],
               empty["months"])))

    # -- AC-SSC2 month-end register sampling law ---------------------
    grid = [row["month"] for row in env["months"]]
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    apr = month_row(env, "2026-04")
    conn = sqlite3.connect(am.db_path)
    d1_alive_jan = am._alive_at_instant(
        int(ids["d1"]), "2026-01-20T00:00:00Z",
        "2026-01-31T23:59:59Z")
    dana_months = [row["month"] for row in env["months"]
                   if am._alive_at_instant(
                       int(ids["d1"]), "2026-01-20T00:00:00Z",
                       row["as_of"])]
    conn.close()
    ok2 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04",
                    "2026-05", "2026-06"]
           and jan["as_of"] == "2026-01-31T23:59:59Z"
           and jan["active_seller_count"] == 2
           and d1_alive_jan
           and dana_months == grid
           and mar["active_seller_count"] == 1
           and apr["active_seller_count"] == 2)
    record("AC-SSC2", ok2,
           "grid=%s jan_as_of=%s jan_active=%d dana_months=%d"
           " mar_active=%d"
           % (grid, jan["as_of"], jan["active_seller_count"],
              len(dana_months), mar["active_seller_count"]))

    # -- AC-SSC3 contiguous grid, honest zero row, conservation ------
    may = month_row(env, "2026-05")
    previous_active = 0
    conservation = True
    for row in env["months"]:
        if row["net_change"] != (row["active_seller_count"]
                                 - previous_active):
            conservation = False
        previous_active = row["active_seller_count"]
    joined_sum = sum(row["joined_seller_count"]
                     for row in env["months"])
    departed_sum = sum(row["departed_seller_count"]
                       for row in env["months"])
    ok3 = (env["month_count"] == 6
           and env["active_month_count"] == 6
           and may["active_seller_count"] == 2
           and may["joined_seller_count"] == 0
           and may["departed_seller_count"] == 0
           and may["retention_rate"] == 1.0
           and may["churn_rate"] == 0.0
           and may["retreating_seller_count"] == 0
           and may["expanding_seller_count"] == 0
           and conservation
           and joined_sum == env["joined_count"]
           and departed_sum == env["departed_count"]
           and env["months"][-1]["running_joined_count"] == joined_sum
           and env["months"][-1]["running_departed_count"]
           == departed_sum)
    record("AC-SSC3", ok3,
           "may=%r conservation=%r joined=%d/%d departed=%d/%d"
           % ((may["active_seller_count"], may["joined_seller_count"],
               may["departed_seller_count"], may["retention_rate"]),
              conservation, joined_sum, env["joined_count"],
              departed_sum, env["departed_count"]))

    # -- AC-SSC4 join/leave law with NEW versus RETURNING -----------
    feb = month_row(env, "2026-02")
    ok4 = (jan["joined_seller_count"] == 2
           and jan["new_seller_count"] == 2
           and jan["returning_seller_count"] == 0
           and jan["retention_rate"] is None
           and jan["churn_rate"] is None
           and feb["joined_seller_count"] == 1
           and feb["new_seller_count"] == 1
           and feb["returning_seller_count"] == 0
           and feb["departed_seller_count"] == 0
           and feb["retention_rate"] == 1.0
           and apr["joined_seller_count"] == 1
           and apr["new_seller_count"] == 0
           and apr["returning_seller_count"] == 1
           and env["new_seller_count"] == 4
           and env["returning_seller_count"] == 1
           and env["joined_count"] == 5)
    record("AC-SSC4", ok4,
           "jan=%r feb=%r apr=%r totals=new%d/ret%d/joined%d"
           % ((jan["joined_seller_count"], jan["new_seller_count"],
               jan["retention_rate"]),
              (feb["joined_seller_count"], feb["new_seller_count"],
               feb["retention_rate"]),
              (apr["joined_seller_count"], apr["new_seller_count"],
               apr["returning_seller_count"]),
              env["new_seller_count"], env["returning_seller_count"],
              env["joined_count"]))

    # -- AC-SSC5 whole-seller exit versus partial retreat -----------
    ok5 = (feb["retreating_seller_count"] == 1
           and feb["expanding_seller_count"] == 1
           and jan["expanding_seller_count"] == 2
           and mar["departed_seller_count"] == 2
           and mar["retreating_seller_count"] == 0
           and apr["expanding_seller_count"] == 1
           and month_row(env, "2026-06")["expanding_seller_count"] == 1
           and env["retreating_count"] == 1
           and env["expanding_count"] == 5
           and env["departed_count"] == 2)
    record("AC-SSC5", ok5,
           "feb(ret%d/exp%d) mar(dep%d/ret%d) totals(ret%d/exp%d/dep%d)"
           % (feb["retreating_seller_count"],
              feb["expanding_seller_count"],
              mar["departed_seller_count"],
              mar["retreating_seller_count"], env["retreating_count"],
              env["expanding_count"], env["departed_count"]))

    # -- AC-SSC6 tenure and peak laws -------------------------------
    gap_feb = month_row(gap, "2026-02")
    ok6 = (mar["departed_tenure_months_mean"] == 1.5
           and env["mean_tenure_of_departed_months"] == 1.5
           and env["longest_departed_tenure_months"] == 2
           and env["peak_month"] == "2026-02"
           and env["peak_active_seller_count"] == 3
           and month_row(env, "2026-06")["active_seller_count"] == 3
           and gap_feb["active_seller_count"] == 0
           and gap_feb["churn_rate"] == 1.0
           and gap_feb["retention_rate"] == 0.0
           and gap["peak_month"] == "2026-01"
           and gap["peak_active_seller_count"] == 1
           and gap["departed_count"] == 1
           and gap["joined_count"] == 2)
    record("AC-SSC6", ok6,
           "mar_tenure=%r env_mean=%r longest=%r peak=%s/%r"
           " gap_feb=%r gap_peak=%s"
           % (mar["departed_tenure_months_mean"],
              env["mean_tenure_of_departed_months"],
              env["longest_departed_tenure_months"],
              env["peak_month"], env["peak_active_seller_count"],
              (gap_feb["active_seller_count"],
               gap_feb["churn_rate"]),
              gap["peak_month"]))

    # -- AC-SSC7 cross-face identity and the cohort NEGATIVE CONTROL -
    supply = am.api_market_supply_months()
    supply_by_month = {row["month"]: row["seller_count"]
                       for row in supply["months"]}
    identity = all(supply_by_month.get(row["month"])
                   == row["active_seller_count"]
                   for row in env["months"])
    cohort = am.api_market_seller_cohort()
    cohort_months = [row["month"] for row in cohort["months"]]
    ok7 = (identity
           and env["seller_count"] == 4
           and supply["seller_count"] == 4
           and "2026-03" not in cohort_months
           and mar["active_seller_count"] == 1
           and mar["departed_seller_count"] == 2
           and len(cohort_months) == 4)
    record("AC-SSC7", ok7,
           "identity=%r lifetime=%d supply_lifetime=%d"
           " cohort_months=%s mar=%r"
           % (identity, env["seller_count"], supply["seller_count"],
              cohort_months,
              (mar["active_seller_count"],
               mar["departed_seller_count"])))

    # -- AC-SSC8 pure read, byte identity, hygiene, wiring ----------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    first = dumps(am.api_market_seller_churn_months())
    second = dumps(am.api_market_seller_churn_months())
    third = dumps(am.api_market_seller_churn_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, _gate2, am2 = build_stack(db_path, cfg,
                                                   lobby_cfg)
    second_instance = dumps(am2.api_market_seller_churn_months())
    close_stack(am2, dk2, metered2, led2)

    source_clean = True
    for path in (os.path.join(BASE, "apimarket.py"),
                 os.path.abspath(__file__)):
        with open(path, "rb") as handle:
            raw = handle.read()
        if b"\r" in raw or any(byte > 127 for byte in raw):
            source_clean = False

    registry_path = os.path.join(os.path.dirname(BASE),
                                 "reconcile_all.py")
    with open(registry_path, "rb") as handle:
        registry_text = handle.read().decode("utf-8")
    wired = ('"ledger-apimarket-sellerchurnmonths"' in registry_text
             and "test_apimarket_sellerchurnmonths.py" in registry_text)

    ok8 = (digests_before == digests_after
           and tx_before == tx_after
           and first == second == third
           and first == second_instance
           and source_clean
           and wired
           and all(shas_before[p] == sha_file(p)
                   for p in PRODUCT_FILES))
    record("AC-SSC8", ok8,
           "digests_same=%r tx_same=%r repeat=%r cross=%r"
           " source_clean=%r wired=%r"
           % (digests_before == digests_after, tx_before == tx_after,
              first == second == third, first == second_instance,
              source_clean, wired))

    close_stack(am, dk, metered, led)
    close_stack(g_am, g_dk, g_metered, g_led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if passed == total else "FAIL",
                              passed, total), flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
