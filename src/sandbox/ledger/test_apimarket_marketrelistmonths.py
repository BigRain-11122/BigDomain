"""Acceptance suite for the apimarket market-wide monthly retirement /
re-listing timeline (BigDomain R2200; canon = the R2189 seed 9/10
explore claim row, criteria AC-MRM1..AC-MRM8 registered in that row
BEFORE this code existed).

Face under proof: APIMarketFace.api_market_relist_months. api_relist_gap
answers one listing's retirement-to-return interval, api_listing_lifecycle
answers the raw event rows and api_market_months answers cash, so the
market carried no monthly view of how many shelves left and how many
came back. This suite pins:

  - the fifteen-key envelope and seven-key month rows, honest empty
    first, and the no-argument signature;
  - the cash-basis double stamp (a delisting books in its own
    delisted_utc month, a re-listing in its own relisted_utc month, and
    a later return never rewrites the month the shelf left in);
  - the contiguous month grid with an honest zero month in the middle,
    plus a pure-return month whose relist_rate is None instead of a
    fabricated zero;
  - conservation of delistings, relistings, nets and the two running
    accumulators landing on the envelope totals;
  - the same-month flow-ratio law on both the row and the envelope;
  - event-derived participants per month and lifetime in the envelope;
  - the peak laws with the earlier-month tie-break and None on an empty
    world;
  - cross-face identity with api_relist_gap (closed gaps plus pending
    equals the delisting count);
  - the pure-read law (frozen table digests and ledger_tx set,
    byte-identical repeats) and cross-instance byte identity;
  - the wiring and the ASCII/LF source hygiene.

Usage: python test_apimarket_marketrelistmonths.py
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
    "month_count", "delist_count", "relist_count", "net_count",
    "relist_rate", "seller_count", "listing_count",
    "peak_delist_month", "peak_delist_count", "peak_relist_month",
    "peak_relist_count", "first_month", "last_month", "months",
    "disclaimer"}

ROW_KEYS = {
    "month", "delist_count", "relist_count", "net_count",
    "relist_rate", "seller_count", "listing_count",
    "running_delist", "running_relist"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


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


def seed_world(led, dk, am, clock):
    """Three listings: t1 at dana, d1 at lia, g1 at gina.

    JAN: dana retires t1, lia retires d1 (2 delistings, 0 returns).
    FEB: no event at all (the honest zero row of the grid).
    MAR: dana brings t1 back, gina retires g1 (1 return, 1 delisting,
    so the flow ratio is exactly 1.0).
    APR: lia brings d1 back (1 return, 0 delisting, so the row rate is
    None rather than a fabricated zero).
    MAY: dana retires t1 again and brings it straight back (1 and 1).

    Totals: 4 delistings, 3 returns, net 1, envelope rate 0.75, and the
    JAN delisting month is never rewritten by the MAR/APR returns.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-MRM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-MRM-S",
                     "settlement")
    for dev in ("dana", "lia", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    clock.value = "2026-01-05T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:lia", "d1", "Lia Data API",
                        "lia data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-20T00:00:00Z"
    am.delist_api("usr:dana", t1)
    am.delist_api("usr:lia", d1)

    clock.value = "2026-03-04T00:00:00Z"
    am.relist_api("usr:dana", t1)
    am.delist_api("usr:gina", g1)

    clock.value = "2026-04-11T00:00:00Z"
    am.relist_api("usr:lia", d1)

    clock.value = "2026-05-06T00:00:00Z"
    am.delist_api("usr:dana", t1)
    am.relist_api("usr:dana", t1)

    return {"t1": t1, "d1": d1, "g1": g1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-marketrelistmonths-")
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
    ids = seed_world(led, dk, am, _CLOCK)

    # -- AC-MRM1 the contract, honest empty first, no argument ------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mrm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_relist_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_market_relist_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    row_count = len(rows_ok and env["months"] or [])
    arg_rejected = False
    try:
        am.api_market_relist_months("2026-01")
    except TypeError:
        arg_rejected = True
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["delist_count"] == 0
           and empty["relist_count"] == 0
           and empty["net_count"] == 0
           and empty["relist_rate"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["peak_delist_month"] is None
           and empty["peak_relist_month"] is None
           and arg_rejected)
    record("AC-MRM1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              row_count,
              (empty["month_count"], empty["relist_rate"],
               empty["months"])))

    # -- AC-MRM2 cash-basis double stamp, never rewritten ------------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    apr = month_row(env, "2026-04")
    may = month_row(env, "2026-05")
    earlier = dumps(am.api_market_relist_months())
    ok2 = (jan["delist_count"] == 2 and jan["relist_count"] == 0
           and jan["net_count"] == 2 and jan["relist_rate"] == 0.0
           and mar["delist_count"] == 1 and mar["relist_count"] == 1
           and mar["net_count"] == 0 and mar["relist_rate"] == 1.0
           and apr["delist_count"] == 0 and apr["relist_count"] == 1
           and apr["net_count"] == -1 and apr["relist_rate"] is None
           and may["delist_count"] == 1 and may["relist_count"] == 1)
    record("AC-MRM2", ok2,
           "jan=%r mar=%r apr=%r may=%r"
           % ((jan["delist_count"], jan["relist_count"],
               jan["relist_rate"]),
              (mar["delist_count"], mar["relist_count"],
               mar["relist_rate"]),
              (apr["delist_count"], apr["relist_count"],
               apr["relist_rate"]),
              (may["delist_count"], may["relist_count"])))

    # -- AC-MRM3 grid, honest zero month, conservation --------------
    grid = [row["month"] for row in env["months"]]
    feb = month_row(env, "2026-02")
    sum_d = sum(row["delist_count"] for row in env["months"])
    sum_r = sum(row["relist_count"] for row in env["months"])
    flat_feb = (feb["delist_count"] == 0 and feb["relist_count"] == 0
                and feb["net_count"] == 0 and feb["relist_rate"] is None
                and feb["seller_count"] == 0
                and feb["listing_count"] == 0
                and feb["running_delist"] == jan["running_delist"])
    ok3 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04",
                    "2026-05"]
           and flat_feb
           and sum_d == env["delist_count"] == 4
           and sum_r == env["relist_count"] == 3
           and env["net_count"] == 1
           and env["month_count"] == len(env["months"]) == 5
           and all(row["net_count"] == row["delist_count"]
                   - row["relist_count"] for row in env["months"])
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-05"
           and env["months"][-1]["running_delist"]
           == env["delist_count"] == 4
           and env["months"][-1]["running_relist"]
           == env["relist_count"] == 3
           and [row["running_delist"] for row in env["months"]]
           == [2, 2, 3, 3, 4]
           and [row["running_relist"] for row in env["months"]]
           == [0, 0, 1, 2, 3]
           and dumps(am.api_market_relist_months()) == earlier)
    record("AC-MRM3", ok3,
           "grid=%r feb=%r sums=%r/%r running=%r/%r"
           % (grid, (feb["delist_count"], feb["relist_rate"]),
              sum_d, sum_r,
              [row["running_delist"] for row in env["months"]],
              [row["running_relist"] for row in env["months"]]))

    # -- AC-MRM4 flow-ratio law on rows and envelope ----------------
    rate_ok = (env["relist_rate"] == 0.75
               and round(float(env["relist_count"])
                         / env["delist_count"], 4) == env["relist_rate"])
    ok4 = (rate_ok
           and jan["relist_rate"] == 0.0
           and mar["relist_rate"] == 1.0
           and apr["relist_rate"] is None
           and may["relist_rate"] == 1.0
           and feb["relist_rate"] is None)
    record("AC-MRM4", ok4,
           "envelope=%r rows=%r"
           % (env["relist_rate"],
              [row["relist_rate"] for row in env["months"]]))

    # -- AC-MRM5 event-derived participants -------------------------
    ok5 = (jan["seller_count"] == 2 and jan["listing_count"] == 2
           and mar["seller_count"] == 2 and mar["listing_count"] == 2
           and apr["seller_count"] == 1 and apr["listing_count"] == 1
           and may["seller_count"] == 1 and may["listing_count"] == 1
           and env["seller_count"] == 3
           and env["listing_count"] == 3
           and env["seller_count"] <= sum(row["seller_count"]
                                          for row in env["months"]))
    record("AC-MRM5", ok5,
           "jan=%r mar=%r apr=%r lifetime=%r"
           % ((jan["seller_count"], jan["listing_count"]),
              (mar["seller_count"], mar["listing_count"]),
              (apr["seller_count"], apr["listing_count"]),
              (env["seller_count"], env["listing_count"])))

    # -- AC-MRM6 peak laws with the earlier-month tie-break ---------
    empty_peaks = empty_peak_pair(cfg, lobby_cfg)
    ok6 = (env["peak_delist_month"] == "2026-01"
           and env["peak_delist_count"] == 2
           and env["peak_relist_month"] == "2026-03"
           and env["peak_relist_count"] == 1
           and empty_peaks == (None, None, None, None))
    record("AC-MRM6", ok6,
           "peaks=%r/%r empty=%r"
           % ((env["peak_delist_month"], env["peak_delist_count"]),
              (env["peak_relist_month"], env["peak_relist_count"]),
              empty_peaks))

    # -- AC-MRM7 cross-face with api_relist_gap ---------------------
    gap = am.api_relist_gap()
    ok7 = (gap["gap_count"] == 3 and gap["pending_count"] == 1
           and gap["gap_count"] + gap["pending_count"]
           == env["delist_count"] == 4
           and gap["gap_count"] == env["relist_count"] == 3
           and all(row["gap_seconds"] is not None
                   for row in gap["rows"] if not row["pending"]))
    record("AC-MRM7", ok7,
           "gap=%r pending=%r delist=%d relist=%d"
           % (gap["gap_count"], gap["pending_count"],
              env["delist_count"], env["relist_count"]))

    # -- AC-MRM8 pure read, determinism, hygiene and wiring ---------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_market_relist_months())
    call_b = dumps(am.api_market_relist_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg, lobby_cfg)
    call_c = dumps(am2.api_market_relist_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg, lobby_cfg)
    call_d = dumps(am3.api_market_relist_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (digests_before == digests_after
           and tx_before == tx_after
           and call_a == call_b == call_c == call_d == dumps(env)
           and b'"ledger-apimarket-marketrelistmonths"' in recon
           and b"test_apimarket_marketrelistmonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-MRM8", ok8,
           "digests_same=%r tx_same=%r bytes=%r wired=%r ascii=%r"
           % (digests_before == digests_after, tx_before == tx_after,
              call_a == call_d,
              b'"ledger-apimarket-marketrelistmonths"' in recon,
              all(b < 128 for b in test_src)))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


def empty_peak_pair(cfg, lobby_cfg):
    tmp = tempfile.mkdtemp(prefix="apimarket-mrm-empty2-")
    led, metered, dk, gate, am = build_stack(
        os.path.join(tmp, "ledger.db"), cfg, lobby_cfg)
    env = am.api_market_relist_months()
    close_stack(am, dk, metered, led)
    return (env["peak_delist_month"], env["peak_delist_count"],
            env["peak_relist_month"], env["peak_relist_count"])


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())