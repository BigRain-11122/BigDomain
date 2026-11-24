"""Acceptance suite for the apimarket market-wide MONTHLY achieved
ticket size (BigDomain R3387; canon = the R3387 explore-queue claim
row, criteria AC-MTM1..AC-MTM8 registered in that row BEFORE this
code existed).

Face under proof: APIMarketFace.api_market_ticket_size_months.

api_market_ticket_size answers the LIFETIME distribution for one scope
(mean/min/max over the whole history) and api_market_months carries
monthly cash, so the month-by-month MIDDLE of what a sale costs had no
face: a market that only moves its extremes and a market where every
price rose read the same mean. This suite pins:

  - the 17-key envelope, the 8-key month rows, the honest empty world
    and the no-argument contract;
  - the booking law (a sale books only in the UTC month of its own
    purchased_utc, a later refund rewrites no month and removes no
    row, refunded_sale_count keeps it visible);
  - the distribution arithmetic (mean, odd AND even medians,
    nearest-rank p90, min/max);
  - the contiguous grid (an honest zero month with None statistics and
    the carried running cash) and the earlier-month peak tie-break;
  - conservation and cross-face identity against api_market_months
    (per-month gross) and api_market_ticket_size (lifetime mean and
    sale count);
  - the pure-read law, determinism across instances, the wiring, the
    registry-facing filename and the ASCII/LF hygiene.
"""

import datetime  # noqa: F401 (kept for stamp arithmetic parity)
import hashlib
import inspect
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
import apimarket as A                 # noqa: E402 (R3387 face)
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
    "scope", "sale_count", "refunded_sale_count", "gross_tokens",
    "mean_ticket", "median_ticket", "p90_ticket", "min_ticket",
    "max_ticket", "month_count", "first_month", "last_month",
    "peak_month", "peak_median_ticket", "latest_month_median_ticket",
    "disclaimer", "months"}

ROW_KEYS = {
    "month", "sale_count", "refunded_sale_count", "gross_tokens",
    "mean_ticket", "median_ticket", "p90_ticket",
    "running_ticket_tokens"}

FMT = "%Y-%m-%dT%H:%M:%SZ"


class Clock(object):
    def __init__(self):
        self.value = "2026-08-01T00:00:00Z"

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


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
        " ORDER BY name").fetchall()]
    out = {}
    for table in tables:
        rows = conn.execute(
            "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
        out[table] = (len(rows),
                      hashlib.sha256(repr(rows).encode("utf-8"))
                      .hexdigest())
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
    """One seller, seven listings, four month buckets, one cross-month
    refund:

      2026-09  tickets 4, 10, 12, 30   (gross 56, median 11)
      2026-10  no sale at all          (honest zero row)
      2026-11  tickets 8, 14           (gross 22, median 11 -> tie)
      2026-12  ticket 6                (gross 6)

    The refund lands in 2026-11 on the 30-token September sale, so the
    September row must keep its four sales and gain only
    refunded_sale_count=1.
    """
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-MTM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-MTM-S",
                     "settlement")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 500),
                ("usr:bob", "credit", 500)],
               "manual:fund-bob", "suite funding bob")
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    clock.value = "2026-08-01T00:00:00Z"
    listings = []
    for key, price in (("p4", 4), ("p10", 10), ("p12", 12),
                       ("p30", 30), ("p8", 8), ("p14", 14),
                       ("p6", 6)):
        listings.append(am.publish_api(
            "usr:dana", key, "API " + key,
            "service listing " + key, PAYLOAD, price,
            False)["listing_id"])

    clock.value = "2026-09-05T10:00:00Z"
    buys = []
    for idx in (0, 1, 2, 3):
        buys.append(am.purchase_api(
            "usr:bob", listings[idx],
            "ref-mtm-%d" % idx)["purchase_id"])
    clock.value = "2026-11-04T10:00:00Z"
    for idx in (4, 5):
        buys.append(am.purchase_api(
            "usr:bob", listings[idx],
            "ref-mtm-%d" % idx)["purchase_id"])
    clock.value = "2026-12-02T10:00:00Z"
    buys.append(am.purchase_api(
        "usr:bob", listings[6], "ref-mtm-6")["purchase_id"])
    return buys


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-marketticketsizemonths-")
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

    # -- AC-MTM1 the contract, honest empty first --------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-mtm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_ticket_size_months()
    e_am.close()
    e_dk.close()
    e_metered.close()
    e_led.close()

    bad_arg = False
    try:
        am.api_market_ticket_size_months(1)
    except TypeError:
        bad_arg = True

    ok1 = (set(empty) == ENVELOPE_KEYS
           and empty["scope"] == "market"
           and empty["sale_count"] == 0
           and empty["refunded_sale_count"] == 0
           and empty["gross_tokens"] == 0
           and empty["mean_ticket"] is None
           and empty["median_ticket"] is None
           and empty["p90_ticket"] is None
           and empty["min_ticket"] is None
           and empty["max_ticket"] is None
           and empty["month_count"] == 0
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["peak_month"] is None
           and empty["peak_median_ticket"] is None
           and empty["latest_month_median_ticket"] is None
           and empty["months"] == []
           and empty["disclaimer"] == DISCLAIMER
           and bad_arg)
    record("AC-MTM1", ok1,
           "keys=%r empty=%r bad_arg=%r"
           % (sorted(empty) == sorted(ENVELOPE_KEYS),
              (empty["sale_count"], empty["month_count"],
               empty["months"]), bad_arg))

    # -- seed the world, then the cross-month refund ----------------
    buys = seed_world(led, dk, am, clock)
    before = am.api_market_ticket_size_months()
    sep_before = dict(month_row(before, "2026-09"))

    clock.value = "2026-11-20T10:00:00Z"
    am.refund_api("usr:bob", buys[3], "late settlement")
    env = am.api_market_ticket_size_months()

    # -- AC-MTM2 booking law: refund rewrites nothing ----------------
    sep = month_row(env, "2026-09")
    nov = month_row(env, "2026-11")
    ok2 = (all(sep[key] == sep_before[key] for key in sep_before
               if key != "refunded_sale_count")
           and sep["refunded_sale_count"] == 1
           and nov["refunded_sale_count"] == 0
           and nov["sale_count"] == 2
           and env["refunded_sale_count"] == 1
           and env["sale_count"] == 7
           and month_row(before, "2026-09")["refunded_sale_count"] == 0
           and set(sep) == ROW_KEYS)
    record("AC-MTM2", ok2,
           "sep=%r nov_refunded=%r refunded_total=%r"
           % ((sep["sale_count"], sep["gross_tokens"],
               sep["refunded_sale_count"]),
              nov["refunded_sale_count"], env["refunded_sale_count"]))

    # -- AC-MTM3 distribution arithmetic ----------------------------
    dec = month_row(env, "2026-12")
    ok3 = (sep["sale_count"] == 4
           and sep["gross_tokens"] == 56
           and sep["mean_ticket"] == 14.0
           and sep["median_ticket"] == 11.0
           and sep["p90_ticket"] == 30
           and nov["sale_count"] == 2
           and nov["gross_tokens"] == 22
           and nov["mean_ticket"] == 11.0
           and nov["median_ticket"] == 11.0
           and nov["p90_ticket"] == 14
           and dec["sale_count"] == 1
           and dec["mean_ticket"] == 6.0
           and dec["median_ticket"] == 6.0
           and dec["p90_ticket"] == 6
           and env["sale_count"] == 7
           and env["gross_tokens"] == 84
           and env["mean_ticket"] == 12.0
           and env["median_ticket"] == 10
           and env["p90_ticket"] == 30
           and env["min_ticket"] == 4
           and env["max_ticket"] == 30)
    record("AC-MTM3", ok3,
           "sep=%r nov=%r dec=%r env=%r"
           % ((sep["mean_ticket"], sep["median_ticket"],
               sep["p90_ticket"]),
              (nov["mean_ticket"], nov["median_ticket"],
               nov["p90_ticket"]),
              (dec["mean_ticket"], dec["median_ticket"]),
              (env["mean_ticket"], env["median_ticket"],
               env["p90_ticket"], env["min_ticket"],
               env["max_ticket"])))

    # -- AC-MTM4 contiguous grid, honest zero month, carried cash ----
    oct_row = month_row(env, "2026-10")
    ok4 = ([row["month"] for row in env["months"]]
           == ["2026-09", "2026-10", "2026-11", "2026-12"]
           and env["month_count"] == 4
           and env["first_month"] == "2026-09"
           and env["last_month"] == "2026-12"
           and oct_row["sale_count"] == 0
           and oct_row["gross_tokens"] == 0
           and oct_row["mean_ticket"] is None
           and oct_row["median_ticket"] is None
           and oct_row["p90_ticket"] is None
           and [row["running_ticket_tokens"] for row in env["months"]]
           == [56, 56, 78, 84])
    record("AC-MTM4", ok4,
           "months=%r running=%r"
           % ([row["month"] for row in env["months"]],
              [row["running_ticket_tokens"] for row in env["months"]]))

    # -- AC-MTM5 conservation and cross-face identity ---------------
    cash = am.api_market_months()
    cash_gross = {row["month"]: row["gross"] for row in cash["months"]}
    life = am.api_market_ticket_size(include_refunded=True)
    health = all(month_row(env, month)["gross_tokens"] == gross
                 for month, gross in cash_gross.items()
                 if month in [r["month"] for r in env["months"]])
    ok5 = (sum(row["sale_count"] for row in env["months"])
           == env["sale_count"]
           and sum(row["gross_tokens"] for row in env["months"])
           == env["gross_tokens"]
           and env["months"][-1]["running_ticket_tokens"]
           == env["gross_tokens"]
           and health
           and life["sale_count"] == env["sale_count"]
           and round(life["mean_ticket"], 4) == env["mean_ticket"])
    record("AC-MTM5", ok5,
           "sum_sales=%r sum_gross=%r cash_keys=%r life=%r"
           % (sum(row["sale_count"] for row in env["months"]),
              sum(row["gross_tokens"] for row in env["months"]),
              sorted(cash_gross), (life["sale_count"],
                                   round(life["mean_ticket"], 4))))

    # -- AC-MTM6 peak tie-break and latest month --------------------
    tied = [row["month"] for row in env["months"]
            if row["median_ticket"] == env["peak_median_ticket"]]
    ok6 = (env["peak_median_ticket"] == 11.0
           and env["peak_month"] == "2026-09"
           and tied == ["2026-09", "2026-11"]
           and env["peak_month"] == tied[0]
           and env["latest_month_median_ticket"]
           == env["months"][-1]["median_ticket"]
           and oct_row["month"] not in tied)
    record("AC-MTM6", ok6,
           "peak=%r tied=%r latest=%r"
           % ((env["peak_month"], env["peak_median_ticket"]), tied,
              env["latest_month_median_ticket"]))

    # -- AC-MTM7 pure read, determinism across instances ------------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_market_ticket_size_months())
    call_b = dumps(am.api_market_ticket_size_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                 lobby_cfg)
    call_c = dumps(am2.api_market_ticket_size_months())
    close_stack(am2, dk2, metered2, led2)

    body = inspect.getsource(am.api_market_ticket_size_months)
    no_write = not any(word in body.upper()
                       for word in ("INSERT ", "UPDATE ", "DELETE ",
                                    "REPLACE "))
    ok7 = (call_a == call_b == dumps(env) == call_c
           and digests_before == digests_after
           and tx_before == tx_after
           and no_write)
    record("AC-MTM7", ok7,
           "same=%r digests=%r tx=%r no_write=%r"
           % (call_a == call_c, digests_before == digests_after,
              tx_before == tx_after, no_write))

    # -- AC-MTM8 wiring, registry filename, hygiene, product shas ---
    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    ok8 = (b"ledger-apimarket-marketticketsizemonths" in recon
           and b"test_apimarket_marketticketsizemonths.py" in recon
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src)
           and all(b < 128 for b in src)
           and shas_before == shas_after)
    record("AC-MTM8", ok8,
           "wired=%r ascii=%r shas=%r"
           % (b"ledger-apimarket-marketticketsizemonths" in recon,
              all(b < 128 for b in test_src),
              shas_before == shas_after))

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
