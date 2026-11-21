"""Acceptance suite for the apimarket seller-scoped monthly retirement
flow (BigDomain R3158; canon = the R2248 c explore-queue seed row, whose
AC-SDL1..AC-SDL8 prefix was pre-registered there BEFORE this code, and
the R3158 PIN row that pinned each criterion before any line was
written).

Face under proof: APIMarketFace.api_seller_delist_months. The supply
family answers adds (api_seller_restock_months), the market family
answers the market axis on cash basis (api_market_relist_months) and
api_relist_gap pairs one named listing's retirement with its return, so
"of the shelves I pulled THIS month, how many came back, how many units
left the shelf and how long were they dark" had no face at all.

This suite pins:

  - the twenty-six-key envelope and thirteen-key month rows, the honest
    empty world and the no-argument market default (AC-SDL1);
  - the retirement-month booking law: the return leg is judged at the
    month the shelf LEFT, so the January row counts two returns that the
    relistings actually stamped in March and April, and the June
    re-listing creates no month at all (AC-SDL2);
  - the cycle pairing law (a retirement of cycle N is answered only by a
    re-listing of cycle N + 1), with the equal-cycle reading measured as
    a NEGATIVE CONTROL that would answer the same rows differently
    (AC-SDL3);
  - the withdrawn-units law: purchases, refunds and restocks stamped at
    or before the retirement are netted, an unlimited shelf contributes
    an UNKNOWN that is counted and never summed as zero, and every
    average divides by the known units only (AC-SDL4);
  - the contiguous grid with honest zero rows, conservation of counts
    and units, and both running accumulators landing on the envelope
    totals (AC-SDL5);
  - the peak law with the earlier-month tie-break on its own world, the
    None (never 0.0) return rate on an eventless month, and the dark
    time triple measured over answered pairs only (AC-SDL6);
  - the scope law: the market scope agrees with api_market_relist_months
    value for value, a seller scope leaks no other seller, carries the
    pooled market mean and reads a prefix-valid stranger as an honest
    empty, while eight bad account shapes fail closed before any read
    (AC-SDL7);
  - the pure-read law (frozen table digests and ledger_tx set,
    byte-identical repeats, cross-instance byte identity), the
    ASCII/LF source hygiene and the registry wiring (AC-SDL8).

Usage: python test_apimarket_sellerdelistmonths.py
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
    "scope", "dev_account", "owned_listing_count",
    "market_mean_delist_count", "month_count", "active_month_count",
    "delist_count", "units_withdrawn", "units_unknown_count",
    "avg_units_per_delist", "largest_withdrawal_units",
    "listing_count", "seller_count", "returned_count",
    "open_retirement_count", "return_rate", "mean_dark_seconds",
    "min_dark_seconds", "max_dark_seconds", "peak_month",
    "peak_delist_count", "first_month", "last_month",
    "latest_month_delist_count", "months", "disclaimer"}

ROW_KEYS = {
    "month", "delist_count", "units_withdrawn", "units_unknown_count",
    "listing_count", "returned_count", "open_retirement_count",
    "return_rate", "mean_dark_seconds", "avg_units_per_delist",
    "largest_withdrawal_units", "running_delist_count",
    "running_units_withdrawn"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions",
          "apimarket_supply_revisions")

BAD_ACCOUNTS = ("", "   ", 123, [], {"a": 1}, "usr", b"usr:x", "usr")

DAY = 86400
# 2026-01-20 -> 2026-03-04, 2026-05-06 -> 2026-06-10, 2026-01-25 ->
# 2026-04-11, all UTC midnight to UTC midnight.
DARK_T1_C1 = 43 * DAY
DARK_T1_C2 = 35 * DAY
DARK_D1_C1 = 76 * DAY


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

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
    """Three sellers, four retirements over five months.

    JAN 20  dana retires t1 (supply 5, one unit already sold) -> 4 units
    JAN 25  lia retires d1 (no declared supply = unlimited)  -> unknown
    MAR 04  dana brings t1 back (opens cycle 2) and gina retires g1
                                                             -> 2 units
    APR 01  dana restocks t1 by three units                  -> 8 effective
    APR 11  lia brings d1 back
    MAY 06  dana retires t1 a second time (cycle 2)          -> 7 units
    JUN 10  dana brings t1 back a third time (opens cycle 3)

    Retirements by month: JAN 2, MAR 1, MAY 1 (FEB and APR are honest
    zero rows). Returned by RETIREMENT month: JAN 2, MAY 1; gina's g1 is
    the one open retirement. The JUN re-listing creates no month because
    this face's grid ends at the last RETIREMENT month.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SDL-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SDL-S",
                     "settlement")
    for dev in ("dana", "lia", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10, ["backtest"],
                     False)
    fund(led, "bob")

    clock.value = "2026-01-05T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        supply=5, category="tools")["listing_id"]
    d1 = am.publish_api("usr:lia", "d1", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        supply=2, category="data")["listing_id"]

    clock.value = "2026-01-10T00:00:00Z"
    am.purchase_api("usr:bob", t1, "ref-bob-t1")

    clock.value = "2026-01-20T00:00:00Z"
    am.delist_api("usr:dana", t1)
    clock.value = "2026-01-25T00:00:00Z"
    am.delist_api("usr:lia", d1)

    clock.value = "2026-03-04T00:00:00Z"
    am.relist_api("usr:dana", t1)
    am.delist_api("usr:gina", g1)

    clock.value = "2026-04-01T00:00:00Z"
    am.restock_api("usr:dana", t1, 3)
    clock.value = "2026-04-11T00:00:00Z"
    am.relist_api("usr:lia", d1)

    clock.value = "2026-05-06T00:00:00Z"
    am.delist_api("usr:dana", t1)
    clock.value = "2026-06-10T00:00:00Z"
    am.relist_api("usr:dana", t1)
    return {"t1": t1, "d1": d1, "g1": g1}


def seed_tie_world(led, dk, am, clock):
    """Two retirements in MAR and two in APR, so the peak is a tie the
    earlier month must win (AC-SDL6)."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SDL-TA",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SDL-TS",
                     "settlement")
    dk.issue_key("usr:hana", "hana-key", 10, ["backtest"], False)

    clock.value = "2026-01-05T00:00:00Z"
    a1 = am.publish_api("usr:hana", "h1", "Hana One",
                        "hana one payload", PAYLOAD, 10, False,
                        supply=1, category="tools")["listing_id"]
    a2 = am.publish_api("usr:hana", "h2", "Hana Two",
                        "hana two payload", PAYLOAD, 10, False,
                        supply=1, category="data")["listing_id"]

    clock.value = "2026-03-10T00:00:00Z"
    am.delist_api("usr:hana", a1)
    am.delist_api("usr:hana", a2)
    clock.value = "2026-03-20T00:00:00Z"
    am.relist_api("usr:hana", a1)
    am.relist_api("usr:hana", a2)
    clock.value = "2026-04-10T00:00:00Z"
    am.delist_api("usr:hana", a1)
    am.delist_api("usr:hana", a2)


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerdelist-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = Clock()
    _CLOCK = clock
    orig_now = A._now_utc
    A._now_utc = clock.now_utc
    try:
        return run(db_path, cfg, lobby_cfg, shas_before)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, shas_before):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    seed_world(led, dk, am, _CLOCK)

    empty_tmp = tempfile.mkdtemp(prefix="apimarket-sdl-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_delist_months()
    close_stack(e_am, e_dk, e_metered, e_led)

    env = am.api_seller_delist_months()

    # -- AC-SDL1 contract, honest empty, no-argument market default -
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    arg_rejected = False
    try:
        am.api_seller_delist_months("2026-01", "extra")
    except TypeError:
        arg_rejected = True
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and len(env) == 26
           and rows_ok
           and all(len(row) == 13 for row in env["months"])
           and env["scope"] == "market"
           and env["dev_account"] is None
           and env["market_mean_delist_count"] is None
           and env["owned_listing_count"] == 3
           and env["disclaimer"] == DISCLAIMER
           and set(empty.keys()) == ENVELOPE_KEYS
           and empty["scope"] == "market"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["delist_count"] == 0
           and empty["units_withdrawn"] == 0
           and empty["units_unknown_count"] == 0
           and empty["avg_units_per_delist"] is None
           and empty["largest_withdrawal_units"] is None
           and empty["returned_count"] == 0
           and empty["open_retirement_count"] == 0
           and empty["return_rate"] is None
           and empty["mean_dark_seconds"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["peak_month"] is None
           and empty["peak_delist_count"] is None
           and empty["latest_month_delist_count"] == 0
           and arg_rejected)
    record("AC-SDL1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              len(env["months"]),
              (empty["month_count"], empty["return_rate"],
               empty["months"])))

    # -- AC-SDL2 the return leg is judged at the RETIREMENT month ----
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    apr = month_row(env, "2026-04")
    may = month_row(env, "2026-05")
    market_face = am.api_market_relist_months()
    market_jan = month_row(market_face, "2026-01")
    market_apr = month_row(market_face, "2026-04")
    market_jun = month_row(market_face, "2026-06")
    grid = [row["month"] for row in env["months"]]
    ok2 = (jan["returned_count"] == 2
           and jan["open_retirement_count"] == 0
           and market_jan["relist_count"] == 0
           and apr["delist_count"] == 0 and apr["returned_count"] == 0
           and market_apr["relist_count"] == 1
           and market_jun["relist_count"] == 1
           and grid[-1] == "2026-05"
           and "2026-06" not in grid
           and may["returned_count"] == 1)
    record("AC-SDL2", ok2,
           "jan=returned%d/relist%d apr=delist%d/relist%d grid_end=%s"
           % (jan["returned_count"], market_jan["relist_count"],
              apr["delist_count"], market_apr["relist_count"],
              grid[-1]))

    # -- AC-SDL3 cycle pairing, equal-cycle as a NEGATIVE CONTROL ----
    pairs = am._conn.execute(
        "SELECT d.delist_id, d.listing_id, d.cycle, d.delisted_utc,"
        " (SELECT r.cycle FROM apimarket_relistings r"
        "  WHERE r.listing_id = d.listing_id AND r.cycle = d.cycle"
        "  ORDER BY r.relist_id LIMIT 1),"
        " (SELECT r.relisted_utc FROM apimarket_relistings r"
        "  WHERE r.listing_id = d.listing_id AND r.cycle = d.cycle + 1"
        "  ORDER BY r.relist_id LIMIT 1)"
        " FROM apimarket_delistings d ORDER BY d.delist_id"
    ).fetchall()

    def _same_cycle_reading():
        """The naive law: pair a retirement with the re-listing of the
        SAME cycle. Kept as a named NEGATIVE CONTROL so the suite proves
        the shipped law is not the obvious one."""
        answered = 0
        for _row in pairs:
            if _row[4] is not None:
                answered += 1
        return answered

    same_cycle_rows = [(p[2], p[4]) for p in pairs]
    next_cycle_rows = [(p[2], p[5]) for p in pairs]
    # The re-listing that OPENED cycle 2 is stamped BEFORE the cycle-2
    # retirement, so a same-cycle join would answer that retirement with
    # its own opening - the naive law is measurably wrong, not merely
    # unfashionable.
    opening_c2 = am._conn.execute(
        "SELECT relisted_utc FROM apimarket_relistings"
        " WHERE listing_id = ? AND cycle = 2",
        (pairs[3][1],)).fetchone()[0]
    naive_answered = _same_cycle_reading()
    law_answered = len([p for p in pairs if p[5] is not None])
    ok3 = (naive_answered == 1
           and law_answered == 3
           and env["returned_count"] == 3
           and env["open_retirement_count"] == 1
           and mar["returned_count"] == 0
           and mar["open_retirement_count"] == 1
           and may["returned_count"] == 1
           and may["open_retirement_count"] == 0
           and same_cycle_rows == [(1, None), (1, None), (1, None),
                                  (2, 2)]
           and pairs[3][5] == "2026-06-10T00:00:00Z"
           and pairs[3][4] == pairs[3][2] == 2
           and opening_c2 < pairs[3][3]
           and next_cycle_rows == [
               (1, "2026-03-04T00:00:00Z"),
               (1, "2026-04-11T00:00:00Z"),
               (1, None),
               (2, "2026-06-10T00:00:00Z")]
           and all(p[5] is None or p[5] > p[3] for p in pairs))
    record("AC-SDL3", ok3,
           "naive_same_cycle_answered=%d law_n+1_answered=%d face=%d open=%d"
           % (naive_answered, law_answered, env["returned_count"],
              env["open_retirement_count"]))

    # -- AC-SDL4 withdrawn units, unlimited counted never zeroed -----
    d1_unknown = [row for row in env["months"]
                  if row["month"] == "2026-01"]
    dana = am.api_seller_delist_months("usr:dana")
    lia = am.api_seller_delist_months("usr:lia")
    gina = am.api_seller_delist_months("usr:gina")
    ok4 = (jan["units_withdrawn"] == 4
           and jan["units_unknown_count"] == 1
           and jan["avg_units_per_delist"] == 4
           and jan["largest_withdrawal_units"] == 4
           and mar["units_withdrawn"] == 2
           and mar["units_unknown_count"] == 0
           and may["units_withdrawn"] == 7
           and may["largest_withdrawal_units"] == 7
           and env["units_withdrawn"] == 13
           and env["units_unknown_count"] == 1
           and env["avg_units_per_delist"] == 4
           and env["largest_withdrawal_units"] == 7
           and lia["units_unknown_count"] == 1
           and lia["units_withdrawn"] == 0
           and lia["avg_units_per_delist"] is None
           and lia["largest_withdrawal_units"] is None
           and dana["units_withdrawn"] == 11
           and gina["units_withdrawn"] == 2
           and len(d1_unknown) == 1)
    record("AC-SDL4", ok4,
           "jan=%r mar=%r may=%r env=%r lia=%r"
           % ((jan["units_withdrawn"], jan["units_unknown_count"]),
              mar["units_withdrawn"], may["units_withdrawn"],
              (env["units_withdrawn"], env["units_unknown_count"],
               env["avg_units_per_delist"]),
              (lia["units_withdrawn"], lia["units_unknown_count"],
               lia["avg_units_per_delist"])))

    # -- AC-SDL5 contiguous grid, honest zeros, conservation ---------
    feb = month_row(env, "2026-02")
    sum_d = sum(row["delist_count"] for row in env["months"])
    sum_u = sum(row["units_withdrawn"] for row in env["months"])
    ok5 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04",
                    "2026-05"]
           and feb["delist_count"] == 0
           and feb["units_withdrawn"] == 0
           and feb["units_unknown_count"] == 0
           and feb["return_rate"] is None
           and feb["avg_units_per_delist"] is None
           and feb["running_delist_count"] == jan["running_delist_count"]
           and sum_d == env["delist_count"] == 4
           and sum_u == env["units_withdrawn"] == 13
           and env["month_count"] == len(env["months"]) == 5
           and env["active_month_count"] == 3
           and env["months"][-1]["running_delist_count"] == 4
           and env["months"][-1]["running_units_withdrawn"] == 13
           and [row["running_delist_count"] for row in env["months"]]
           == [2, 2, 3, 3, 4]
           and [row["running_units_withdrawn"] for row in env["months"]]
           == [4, 4, 6, 6, 13]
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-05"
           and env["latest_month_delist_count"] == 1)
    record("AC-SDL5", ok5,
           "grid=%r sums=%r/%r running=%r/%r"
           % (grid, sum_d, sum_u,
              [row["running_delist_count"] for row in env["months"]],
              [row["running_units_withdrawn"]
               for row in env["months"]]))

    # -- AC-SDL6 peak, ties, honest None rate, dark triple ----------
    tie_tmp = tempfile.mkdtemp(prefix="apimarket-sdl-tie-")
    t_led, t_metered, t_dk, _t_gate, t_am = build_stack(
        os.path.join(tie_tmp, "ledger.db"), cfg, lobby_cfg)
    seed_tie_world(t_led, t_dk, t_am, _CLOCK)
    tie = t_am.api_seller_delist_months()
    close_stack(t_am, t_dk, t_metered, t_led)
    dark_pairs = [DARK_T1_C1, DARK_T1_C2, DARK_D1_C1]
    ok6 = (env["peak_month"] == "2026-01"
           and env["peak_delist_count"] == 2
           and tie["peak_month"] == "2026-03"
           and tie["peak_delist_count"] == 2
           and [row["delist_count"] for row in tie["months"]]
           == [2, 2]
           and feb["return_rate"] is None
           and apr["return_rate"] is None
           and mar["return_rate"] == 0.0
           and jan["return_rate"] == 1.0
           and may["return_rate"] == 1.0
           and env["return_rate"] == 0.75
           and env["mean_dark_seconds"] == sum(dark_pairs) // 3
           and env["min_dark_seconds"] == DARK_T1_C2
           and env["max_dark_seconds"] == DARK_D1_C1
           and feb["mean_dark_seconds"] is None
           and mar["mean_dark_seconds"] is None
           and dana["mean_dark_seconds"] == (
               (DARK_T1_C1 + DARK_T1_C2) // 2)
           and gina["mean_dark_seconds"] is None
           and lia["mean_dark_seconds"] == DARK_D1_C1)
    record("AC-SDL6", ok6,
           "peak=%r/%r tie=%r/%r dark=%r/%r/%r"
           % (env["peak_month"], env["peak_delist_count"],
              tie["peak_month"], tie["peak_delist_count"],
              env["min_dark_seconds"], env["mean_dark_seconds"],
              env["max_dark_seconds"]))

    # -- AC-SDL7 scope law, cross-face identity, fail-closed gate ---
    digests_gate = market_digests(am)
    tx_gate = ledger_tx_ids(led)
    refused = 0
    for bad in BAD_ACCOUNTS:
        try:
            am.api_seller_delist_months(bad)
        except A.ApiMarketError:
            refused += 1
    refused_digests = market_digests(am)
    refused_tx = ledger_tx_ids(led)
    stranger = am.api_seller_delist_months("usr:stranger")
    market_by_month = {row["month"]: row["delist_count"]
                       for row in market_face["months"]}
    face_by_month = {row["month"]: row["delist_count"]
                     for row in env["months"]}
    shared_equal = all(market_by_month.get(m) == face_by_month[m]
                       for m in face_by_month)
    market_only_months = sorted(set(market_by_month) - set(face_by_month))
    market_only_flat = all(market_by_month[m] == 0
                           for m in market_only_months)
    ok7 = (refused == len(BAD_ACCOUNTS)
           and digests_gate == refused_digests
           and tx_gate == refused_tx
           and shared_equal
           and market_only_flat
           and dana["scope"] == "seller"
           and dana["dev_account"] == "usr:dana"
           and dana["owned_listing_count"] == 1
           and dana["delist_count"] == 2
           and dana["returned_count"] == 2
           and dana["open_retirement_count"] == 0
           and dana["return_rate"] == 1.0
           and dana["seller_count"] == 1
           and dana["listing_count"] == 1
           and dana["market_mean_delist_count"] == 1.3333
           and gina["delist_count"] == 1
           and gina["open_retirement_count"] == 1
           and gina["return_rate"] == 0.0
           and gina["market_mean_delist_count"] == 1.3333
           and lia["delist_count"] == 1
           and lia["units_unknown_count"] == 1
           and stranger["month_count"] == 0
           and stranger["months"] == []
           and stranger["delist_count"] == 0
           and stranger["scope"] == "seller"
           and stranger["market_mean_delist_count"] == 1.3333)
    record("AC-SDL7", ok7,
           "refused=%d/%d digests_same=%r shared_equal=%r"
           " market_only=%r dana=%r gina=%r stranger=%r"
           % (refused, len(BAD_ACCOUNTS),
              digests_gate == refused_digests, shared_equal,
              market_only_months,
              (dana["delist_count"], dana["returned_count"],
               dana["market_mean_delist_count"]),
              (gina["delist_count"], gina["open_retirement_count"]),
              (stranger["month_count"], stranger["delist_count"])))

    # -- AC-SDL8 pure read, determinism, hygiene, wiring ------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_seller_delist_months())
    call_b = dumps(am.api_seller_delist_months())
    seller_a = dumps(am.api_seller_delist_months("usr:dana"))
    seller_b = dumps(am.api_seller_delist_months("usr:dana"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, _gate2, am2 = build_stack(db_path, cfg,
                                                   lobby_cfg)
    call_c = dumps(am2.api_seller_delist_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, _gate3, am3 = build_stack(db_path, cfg,
                                                   lobby_cfg)
    call_d = dumps(am3.api_seller_delist_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (digests_before == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == dumps(env)
           and seller_a == seller_b
           and b'"ledger-apimarket-sellerdelistmonths"' in recon
           and b"test_apimarket_sellerdelistmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src)
           and b"def api_seller_delist_months" in src)
    record("AC-SDL8", ok8,
           "digests_same=%r tx_same=%r bytes=%r wired=%r ascii=%r"
           % (digests_before == digests_after, tx_before == tx_after,
              call_a == call_d,
              b'"ledger-apimarket-sellerdelistmonths"' in recon,
              all(b < 128 for b in test_src)))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())
