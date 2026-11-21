"""Acceptance suite for the apimarket market-wide monthly DISCOUNT-EVENT
face (BigDomain R3160; canon = the R2248 e explore-queue seed row and the
R3160 PIN row, which pinned every criterion BEFORE this code existed).

Face under proof: APIMarketFace.api_market_discount_months.

The shipped price family answers snapshots (api_category_price_months), the
lifetime step shape (api_price_step_distribution) and monthly repricing
cadence (api_seller_price_cadence_months: up/down counts and the average
absolute step), but none of them books a DISCOUNT as an event: how many
tokens were given away, how deep the cut went, which shelves were cut and
whether the cut was later taken back. A month of heavy discounting and a
month of flat asking prices can therefore read alike.

Private world (six months, three sellers, five listings, base prices set at
publish time):
  l1 alice tools 100  listed 01-05; cut to 80 on 01-10 (UNDONE by the
     02-05 raise to 120); cut again 120 -> 90 on 04-10 (STANDING)
  l2 bob   data  200  listed 01-08; raised 250 on 01-20; cut 250 -> 200 on
     02-20 (STANDING); cut 200 -> 150 on 06-15 (STANDING)
  l3 dana  tools  50  listed 03-01; cut to 40 on 03-05 (UNDONE by the
     03-20 raise back to 50); raised to 55 on 06-05
  l4 dana  data   80  listed 03-01; category revised to tools on 05-15;
     cut to 60 on 06-20 (booked to TOOLS, STANDING)
  l5 dana  none   40  listed 04-01; cut to 30 on 04-20 (STANDING) - the
     uncategorized bucket

2026-05 carries NO price revision at all and must still appear as an honest
zero row between April and June.

Given that world the face must read:
  JAN rev 2 disc 1 tokens 20 undone 1
  FEB rev 2 disc 1 tokens 50 standing 1
  MAR rev 2 disc 1 tokens 10 undone 1
  APR rev 2 disc 2 tokens 40 standing 2 (peak tie with JUN -> APR wins)
  MAY rev 0 honest zero row, share/avg/deepest None
  JUN rev 3 disc 2 tokens 70 standing 2
  envelope disc 7 / tokens 190 / avg -22.86 (pooled) / deepest -25.0 /
  largest 50 / undone 2 / standing 5 / standing_tokens 160 / share 0.6364

Usage: python test_apimarket_discountmonths.py
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
    "scope", "include_uncategorized", "month_count",
    "active_month_count", "revision_count", "discount_count",
    "raise_count", "discount_share", "discounted_listing_count",
    "discounted_seller_count", "tokens_cut", "avg_cut_pct",
    "deepest_cut_pct", "largest_cut_tokens", "undone_discount_count",
    "standing_discount_count", "standing_tokens_cut", "peak_month",
    "peak_discount_count", "first_month", "last_month",
    "latest_month_discount_count", "category_count", "disclaimer",
    "months"}

ROW_KEYS = {
    "month", "as_of", "revision_count", "discount_count",
    "raise_count", "discount_share", "discounted_listing_count",
    "discounted_seller_count", "tokens_cut", "avg_cut_pct",
    "deepest_cut_pct", "largest_cut_tokens", "undone_discount_count",
    "standing_discount_count", "running_discount_count",
    "running_tokens_cut", "categories"}

CELL_KEYS = {"category", "revision_count", "discount_count",
             "raise_count", "tokens_cut", "avg_cut_pct"}

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


def cell_of(row, category):
    for cell in row["categories"]:
        if cell["category"] == category:
            return cell
    raise AssertionError("category %r missing from %s cells"
                         % (category, row["month"]))


def fund(led, *names):
    for who in names:
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 500),
                    ("usr:" + who, "credit", 500)],
                   "manual:fund-" + who, "suite funding " + who)


def seed_world(led, dk, am, clock):
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-MDK-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-MDK-S", "settlement")
    for dev in ("alice", "bob", "dana"):
        dk.issue_key("usr:" + dev, dev + "-key", 10, ["backtest"],
                     False)
    fund(led, "buyer")

    clock.value = "2026-01-05T00:00:00Z"
    l1 = am.publish_api("usr:alice", "l1", "L One", "l one payload",
                        PAYLOAD, 100, False, supply=1,
                        category="tools")["listing_id"]
    clock.value = "2026-01-08T00:00:00Z"
    l2 = am.publish_api("usr:bob", "l2", "L Two", "l two payload",
                        PAYLOAD, 200, False, supply=1,
                        category="data")["listing_id"]
    clock.value = "2026-03-01T00:00:00Z"
    l3 = am.publish_api("usr:dana", "l3", "L Three",
                        "l three payload", PAYLOAD, 50, False,
                        supply=1, category="tools")["listing_id"]
    l4 = am.publish_api("usr:dana", "l4", "L Four",
                        "l four payload", PAYLOAD, 80, False,
                        supply=1, category="data")["listing_id"]
    clock.value = "2026-04-01T00:00:00Z"
    l5 = am.publish_api("usr:dana", "l5", "L Five",
                        "l five payload", PAYLOAD, 40, False,
                        supply=1)["listing_id"]

    owners = {l1: "alice", l2: "bob", l3: "dana", l4: "dana",
              l5: "dana"}

    def price(when, lid, value):
        clock.value = when
        am.revise_price("usr:" + owners[lid], lid, value)

    price("2026-01-10T00:00:00Z", l1, 80)
    price("2026-01-20T00:00:00Z", l2, 250)
    price("2026-02-05T00:00:00Z", l1, 120)
    price("2026-02-20T00:00:00Z", l2, 200)
    price("2026-03-05T00:00:00Z", l3, 40)
    price("2026-03-20T00:00:00Z", l3, 50)
    price("2026-04-10T00:00:00Z", l1, 90)
    price("2026-04-20T00:00:00Z", l5, 30)
    clock.value = "2026-05-15T00:00:00Z"
    am.revise_category("usr:dana", l4, "tools")
    price("2026-06-05T00:00:00Z", l3, 55)
    price("2026-06-15T00:00:00Z", l2, 150)
    price("2026-06-20T00:00:00Z", l4, 60)
    return {"l1": l1, "l2": l2, "l3": l3, "l4": l4, "l5": l5}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-discount-")
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
        return run(db_path, cfg, lobby_cfg, shas_before)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    clock = Clock()
    orig = A._now_utc
    A._now_utc = clock.now_utc
    try:
        seed_world(led, dk, am, clock)
    finally:
        A._now_utc = orig

    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mdk-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_discount_months()
    close_stack(e_am, e_dk, e_metered, e_led)

    env = am.api_market_discount_months()
    bare = am.api_market_discount_months(include_uncategorized=False)
    cadence = am.api_seller_price_cadence_months()

    # -- AC-MDK1 contract, honest empty, argument gate ---------------
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    cells_ok = all(set(cell.keys()) == CELL_KEYS
                   for row in env["months"]
                   for cell in row["categories"])
    gate_codes = []
    for bad in ("yes", 1, None):
        try:
            am.api_market_discount_months(bad)
        except A.ApiMarketError as exc:
            gate_codes.append(exc.code)
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and len(env) == 25
           and rows_ok
           and cells_ok
           and all(len(row) == 17 for row in env["months"])
           and all(len(cell) == 6 for row in env["months"]
                   for cell in row["categories"])
           and env["scope"] == "market"
           and env["include_uncategorized"] is True
           and env["disclaimer"] == DISCLAIMER
           and set(empty.keys()) == ENVELOPE_KEYS
           and empty["month_count"] == 0
           and empty["active_month_count"] == 0
           and empty["months"] == []
           and empty["revision_count"] == 0
           and empty["discount_count"] == 0
           and empty["raise_count"] == 0
           and empty["discount_share"] is None
           and empty["avg_cut_pct"] is None
           and empty["deepest_cut_pct"] is None
           and empty["largest_cut_tokens"] == 0
           and empty["undone_discount_count"] == 0
           and empty["standing_discount_count"] == 0
           and empty["standing_tokens_cut"] == 0
           and empty["peak_month"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_discount_count"] is None
           and empty["category_count"] == 0
           and gate_codes == [A.E_AM_BAD_ARGS] * 3)
    record("AC-MDK1", ok1,
           "env_keys=%d rows_ok=%r cells_ok=%r rows=%d empty=%r"
           " gate=%s"
           % (len(env), rows_ok, cells_ok, len(env["months"]),
              (empty["month_count"], empty["discount_count"],
               empty["discount_share"], empty["peak_month"]),
              gate_codes))

    # -- AC-MDK2 discount-event law, booked in its own month ---------
    jan = month_row(env, "2026-01")
    feb = month_row(env, "2026-02")
    mar = month_row(env, "2026-03")
    apr = month_row(env, "2026-04")
    jun = month_row(env, "2026-06")
    jan_tools = cell_of(jan, "tools")
    jan_data = cell_of(jan, "data")
    ok2 = (jan["revision_count"] == 2
           and jan["discount_count"] == 1
           and jan["raise_count"] == 1
           and jan["tokens_cut"] == 20
           and jan["avg_cut_pct"] == -20.0
           and jan["largest_cut_tokens"] == 20
           and jan_tools["discount_count"] == 1
           and jan_tools["tokens_cut"] == 20
           and jan_data["discount_count"] == 0
           and jan_data["raise_count"] == 1
           and feb["tokens_cut"] == 50
           and mar["tokens_cut"] == 10
           and apr["tokens_cut"] == 40
           and jun["tokens_cut"] == 70
           and env["revision_count"] == 11
           and env["discount_count"] == 7
           and env["raise_count"] == 4
           and env["discount_share"] == 0.6364
           and env["tokens_cut"] == 190)
    record("AC-MDK2", ok2,
           "jan=%r feb_tokens=%d mar_tokens=%d apr_tokens=%d"
           " jun_tokens=%d env=%r"
           % ((jan["revision_count"], jan["discount_count"],
               jan["raise_count"], jan["tokens_cut"]),
              feb["tokens_cut"], mar["tokens_cut"], apr["tokens_cut"],
              jun["tokens_cut"],
              (env["revision_count"], env["discount_count"],
               env["raise_count"], env["discount_share"],
               env["tokens_cut"])))

    # -- AC-MDK3 undone versus standing, and the standing tokens -----
    per_month_ok = all(row["undone_discount_count"]
                       + row["standing_discount_count"]
                       == row["discount_count"]
                       for row in env["months"])
    ok3 = (jan["undone_discount_count"] == 1
           and jan["standing_discount_count"] == 0
           and feb["undone_discount_count"] == 0
           and feb["standing_discount_count"] == 1
           and mar["undone_discount_count"] == 1
           and mar["standing_discount_count"] == 0
           and apr["standing_discount_count"] == 2
           and jun["standing_discount_count"] == 2
           and env["undone_discount_count"] == 2
           and env["standing_discount_count"] == 5
           and env["standing_tokens_cut"] == 160
           and env["undone_discount_count"]
           + env["standing_discount_count"] == env["discount_count"]
           and per_month_ok)
    record("AC-MDK3", ok3,
           "undone=%d standing=%d standing_tokens=%d per_month=%r"
           % (env["undone_discount_count"],
              env["standing_discount_count"],
              env["standing_tokens_cut"], per_month_ok))

    # -- AC-MDK4 contiguous grid, honest zero row, conservation ------
    may = month_row(env, "2026-05")
    discount_sum = sum(row["discount_count"] for row in env["months"])
    tokens_sum = sum(row["tokens_cut"] for row in env["months"])
    ok4 = ([row["month"] for row in env["months"]]
           == ["2026-01", "2026-02", "2026-03", "2026-04",
               "2026-05", "2026-06"]
           and env["month_count"] == 6
           and env["active_month_count"] == 5
           and may["as_of"] == "2026-05-31T23:59:59Z"
           and may["revision_count"] == 0
           and may["discount_count"] == 0
           and may["discount_share"] is None
           and may["avg_cut_pct"] is None
           and may["deepest_cut_pct"] is None
           and may["largest_cut_tokens"] == 0
           and may["categories"] == []
           and discount_sum == env["discount_count"]
           and tokens_sum == env["tokens_cut"]
           and env["months"][-1]["running_discount_count"]
           == env["discount_count"]
           and env["months"][-1]["running_tokens_cut"]
           == env["tokens_cut"])
    record("AC-MDK4", ok4,
           "grid=%d active=%d may=%r sums=%d/%d tokens=%d/%d"
           % (env["month_count"], env["active_month_count"],
              (may["revision_count"], may["discount_share"],
               may["largest_cut_tokens"]), discount_sum,
              env["discount_count"], tokens_sum, env["tokens_cut"]))

    # -- AC-MDK5 category seam at the event instant ------------------
    jun_tools = cell_of(jun, "tools")
    jun_data = cell_of(jun, "data")
    apr_none = cell_of(apr, None)
    apr_bare = month_row(bare, "2026-04")
    bare_categories = [cell["category"] for cell in apr_bare["categories"]]
    no_none_anywhere = all(
        cell["category"] is not None
        for row in bare["months"] for cell in row["categories"])
    totals_same = all(
        (row["revision_count"], row["discount_count"],
         row["tokens_cut"])
        == (other["revision_count"], other["discount_count"],
            other["tokens_cut"])
        for row, other in zip(bare["months"], env["months"]))
    order_ok = (apr["categories"][0]["category"] == "tools"
                and apr["categories"][-1]["category"] is None)
    ok5 = (jun_tools["discount_count"] == 1
           and jun_tools["tokens_cut"] == 20
           and jun_tools["raise_count"] == 1
           and jun_data["discount_count"] == 1
           and jun_data["tokens_cut"] == 50
           and apr_none["tokens_cut"] == 10
           and apr_none["avg_cut_pct"] == -25.0
           and order_ok
           and env["category_count"] == 3
           and bare["category_count"] == 2
           and bare_categories == ["tools"]
           and no_none_anywhere
           and totals_same
           and bare["include_uncategorized"] is False)
    record("AC-MDK5", ok5,
           "jun_tools=%r jun_data=%r apr_none=%r order=%r"
           " categories=%d/%d bare_cells=%s totals_same=%r"
           % ((jun_tools["discount_count"], jun_tools["tokens_cut"]),
              (jun_data["discount_count"], jun_data["tokens_cut"]),
              (apr_none["category"], apr_none["tokens_cut"]),
              order_ok, env["category_count"],
              bare["category_count"], bare_categories, totals_same))

    # -- AC-MDK6 peak, depth, and POOLED average --------------------
    monthly_means = [row["avg_cut_pct"] for row in env["months"]
                     if row["avg_cut_pct"] is not None]
    naive_mean = round(sum(monthly_means) / len(monthly_means), 2)
    ok6 = (env["peak_month"] == "2026-04"
           and env["peak_discount_count"] == 2
           and jun["discount_count"] == 2
           and env["deepest_cut_pct"] == -25.0
           and env["largest_cut_tokens"] == 50
           and env["avg_cut_pct"] == -22.86
           and naive_mean == -22.0
           and env["avg_cut_pct"] != naive_mean
           and jun["deepest_cut_pct"] == -25.0
           and apr["deepest_cut_pct"] == -25.0)
    record("AC-MDK6", ok6,
           "peak=%s/%d deepest=%r largest=%d pooled=%r naive=%r"
           % (env["peak_month"], env["peak_discount_count"],
              env["deepest_cut_pct"], env["largest_cut_tokens"],
              env["avg_cut_pct"], naive_mean))

    # -- AC-MDK7 cross-face identity and the NEGATIVE CONTROL -------
    cad_by_month = {row["month"]: row for row in cadence["months"]}
    identity = (env["revision_count"] == cadence["revision_count"]
                and env["discount_count"] == cadence["down_count"]
                and env["raise_count"] == cadence["up_count"])
    monthly_identity = all(
        (row["revision_count"], row["discount_count"],
         row["raise_count"])
        == (cad_by_month[row["month"]]["revision_count"],
            cad_by_month[row["month"]]["down_count"],
            cad_by_month[row["month"]]["up_count"])
        for row in env["months"])
    row_discount_sum = sum(row["discount_count"]
                           for row in env["months"])
    ok7 = (identity
           and monthly_identity
           and cad_by_month["2026-05"]["down_count"] == 0
           and month_row(env, "2026-05")["discount_count"] == 0
           and env["discounted_listing_count"] == 5
           and env["discounted_seller_count"] == 3
           and env["discounted_listing_count"] < row_discount_sum)
    record("AC-MDK7", ok7,
           "identity=%r monthly=%r counts=listings%d/sellers%d"
           " rows=%d control=%r"
           % (identity, monthly_identity,
              env["discounted_listing_count"],
              env["discounted_seller_count"], row_discount_sum,
              cad_by_month["2026-05"]["down_count"]))

    # -- AC-MDK8 pure read, byte identity, hygiene, wiring ----------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    for bad in ("yes", 1, None):
        try:
            am.api_market_discount_months(bad)
        except A.ApiMarketError:
            pass
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    first = dumps(am.api_market_discount_months())
    second = dumps(am.api_market_discount_months())
    third = dumps(am.api_market_discount_months())

    led2, metered2, dk2, _gate2, am2 = build_stack(db_path, cfg,
                                                   lobby_cfg)
    second_instance = dumps(am2.api_market_discount_months())
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
    wired = ('"ledger-apimarket-discountmonths"' in registry_text
             and "test_apimarket_discountmonths.py" in registry_text)

    ok8 = (digests_before == digests_after
           and tx_before == tx_after
           and first == second == third
           and first == second_instance
           and source_clean
           and wired
           and all(shas_before[p] == sha_file(p)
                   for p in PRODUCT_FILES))
    record("AC-MDK8", ok8,
           "digests_same=%r tx_same=%r repeat=%r cross=%r"
           " source_clean=%r wired=%r"
           % (digests_before == digests_after, tx_before == tx_after,
              first == second == third, first == second_instance,
              source_clean, wired))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if passed == total else "FAIL",
                              passed, total), flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
