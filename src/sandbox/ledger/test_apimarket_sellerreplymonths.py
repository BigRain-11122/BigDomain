"""Acceptance suite for the seller monthly rating-reply cadence
(BigDomain R2217; canon = the R2213 explore-queue seed row claimed in
R2217, criteria AC-SRM1..AC-SRM8 registered in that row in the same
window as this code, disclosed - the R2137/R2141/R2144 precedent).

Face under proof: APIMarketFace.api_seller_reply_months.
api_rating_reply_latency answers a LIFETIME latency scorecard, so a
seller that answered every rating within an hour last quarter and then
went silent reads exactly like one that never answered. This suite
pins:

  - the twenty-five-key envelope, the ten-key month rows and the
    honest empty world;
  - the cadence law: a reply books in the month of its own
    replied_utc, never the rating month, so a March discharge of a
    January rating raises only the March row and a silent month stays
    an honest zero row;
  - the latency law: reply seconds always measured rated->replied
    across the month boundary, month stats over the replies booked in
    that month, the integer floor mean, and None latencies on a zero
    month rather than a fabricated zero;
  - the backlog split (backlog_count + same_month_count ==
    replied_count per row, envelope totals conserved);
  - the contiguous grid, the monotone running_replied accumulator and
    the peak law with the earlier-month tie-break;
  - the scope law (market scope without a self-benchmark, seller
    scope with the market pooled mean, strict isolation) and the
    cross-face identity against api_rating_reply_latency;
  - the account gate and the pure-read law (frozen table digests,
    constant ledger_tx set);
  - cross-instance byte identity over two full-stack restarts,
    wiring and ASCII/LF hygiene.

Usage: python test_apimarket_sellerreplymonths.py
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
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

ENVELOPE_KEYS = {
    "scope", "dev_account", "rating_count", "replied_count",
    "unreplied_count", "reply_coverage", "backlog_reply_count",
    "same_month_reply_count", "buyer_count", "listing_count",
    "owned_listing_count", "month_count", "active_month_count",
    "peak_month", "peak_replied_count", "first_month", "last_month",
    "latest_month_replied_count", "fastest_seconds",
    "slowest_seconds", "mean_seconds", "market_mean_seconds",
    "oldest_unreplied_utc", "disclaimer", "months"}

ROW_KEYS = {
    "month", "replied_count", "backlog_count", "same_month_count",
    "buyer_count", "listing_count", "fastest_seconds",
    "slowest_seconds", "mean_seconds", "running_replied"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_questions", "apimarket_answers",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_rating_replies", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")

BAD_ACCOUNTS = ("", "u", "usrX:dana", 123, False, [],
                {}, {"usr:x": 1})

JAN_BO = 21600
MAR_CY = 4406400
MAR_ED = 10800
MAR_GI = 5788800


class Clock(object):
    """Deterministic stamp holder: one explicit UTC string is set
    before each write so the month buckets are reproducible."""

    def __init__(self):
        self.value = "2026-01-01T00:00:00Z"

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


def error_code(fn, *args):
    try:
        fn(*args)
    except A.ApiMarketError as exc:
        return exc.code
    return None


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
    """Two sellers. dana owns t1, d1 and the never-answered d2; gina
    owns g1. Every rater buys first because the rating door is
    purchaser-only.

    JAN: bo rates t1 and dana replies the same day (the same-month
    leg); cy rates t1 and is left waiting; gi rates g1 and is left
    waiting until March.
    FEB: no reply at all (the honest zero row of the grid).
    MAR: dana clears cy's JANUARY rating (the backlog leg), ed buys d1,
    rates it and is answered three hours later (the fast same-month
    leg); ha and iv rate and stay owed; gina clears her January
    backlog.

    dana therefore books 1 reply in January (21600s) and 2 in March
    (4406400s backlog + 10800s same-month) with an honest zero
    February; gina is isolated to one March backlog reply.
    """
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-SRM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-SRM-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "di", "ed", "gi", "ha", "iv"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)

    clock.value = "2026-01-01T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:dana", "d1", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-02T00:00:00Z"
    am.purchase_api("usr:bo", t1, "BUY-SRM-1")
    am.purchase_api("usr:cy", t1, "BUY-SRM-2")
    am.purchase_api("usr:gi", g1, "BUY-SRM-3")

    clock.value = "2026-01-04T00:00:00Z"
    r_bo = am.rate_api("usr:bo", t1, 5)["rating_id"]
    clock.value = "2026-01-04T06:00:00Z"
    am.reply_to_rating("usr:dana", r_bo, "thanks, enjoy the feed")

    clock.value = "2026-01-10T00:00:00Z"
    r_cy = am.rate_api("usr:cy", t1, 4)["rating_id"]
    clock.value = "2026-01-12T00:00:00Z"
    r_gi = am.rate_api("usr:gi", g1, 5)["rating_id"]

    clock.value = "2026-03-01T00:00:00Z"
    d2 = am.publish_api("usr:dana", "d2", "Dana Quiet API",
                        "a shelf with an owed answer", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    am.purchase_api("usr:ha", d2, "BUY-SRM-4")
    clock.value = "2026-03-02T00:00:00Z"
    am.reply_to_rating("usr:dana", r_cy, "sorry for the wait")
    clock.value = "2026-03-05T00:00:00Z"
    am.purchase_api("usr:ed", d1, "BUY-SRM-5")
    r_ed = am.rate_api("usr:ed", d1, 3)["rating_id"]
    clock.value = "2026-03-05T03:00:00Z"
    am.reply_to_rating("usr:dana", r_ed, "noted, we ship a fix")
    clock.value = "2026-03-10T00:00:00Z"
    r_ha = am.rate_api("usr:ha", d2, 2)["rating_id"]
    clock.value = "2026-03-11T00:00:00Z"
    am.purchase_api("usr:iv", d1, "BUY-SRM-6")
    r_iv = am.rate_api("usr:iv", d1, 1)["rating_id"]
    clock.value = "2026-03-20T00:00:00Z"
    am.reply_to_rating("usr:gina", r_gi, "yes, ask for a sample")

    return {"t1": t1, "d1": d1, "d2": d2, "g1": g1,
            "r_bo": r_bo, "r_cy": r_cy, "r_gi": r_gi,
            "r_ed": r_ed, "r_ha": r_ha, "r_iv": r_iv}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerreplymonths-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    cfg, lobby_cfg = RPT.load_configs()

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

    # -- AC-SRM1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-srm-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_reply_months("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_seller_reply_months("usr:dana")
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and env["scope"] == "seller"
           and env["dev_account"] == "usr:dana"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["rating_count"] == 0
           and empty["replied_count"] == 0
           and empty["unreplied_count"] == 0
           and empty["reply_coverage"] is None
           and empty["backlog_reply_count"] == 0
           and empty["same_month_reply_count"] == 0
           and empty["buyer_count"] == 0
           and empty["listing_count"] == 0
           and empty["owned_listing_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_replied_count"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_replied_count"] == 0
           and empty["fastest_seconds"] is None
           and empty["slowest_seconds"] is None
           and empty["mean_seconds"] is None
           and empty["market_mean_seconds"] is None
           and empty["oldest_unreplied_utc"] is None)
    record("AC-SRM1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["months"],
               empty["fastest_seconds"])))

    # -- AC-SRM2 cadence law: the reply books on replied_utc --------
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03"]
           and jan["replied_count"] == 1
           and jan["backlog_count"] == 0
           and jan["same_month_count"] == 1
           and mar["replied_count"] == 2
           and mar["backlog_count"] == 1
           and mar["same_month_count"] == 1
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-03"
           and env["replied_count"] == 3
           and env["backlog_reply_count"] == 1
           and env["rating_count"] == 5
           and env["unreplied_count"] == 2)
    record("AC-SRM2", ok2,
           "grid=%r jan=%r mar=%r totals=%r"
           % (grid, (jan["replied_count"], jan["backlog_count"]),
              (mar["replied_count"], mar["backlog_count"]),
              (env["replied_count"], env["backlog_reply_count"],
               env["rating_count"], env["unreplied_count"])))

    # -- AC-SRM3 latency law across the month boundary --------------
    ok3 = (jan["fastest_seconds"] == jan["slowest_seconds"]
           == jan["mean_seconds"] == JAN_BO
           and mar["fastest_seconds"] == MAR_ED
           and mar["slowest_seconds"] == MAR_CY
           and mar["mean_seconds"] == (MAR_CY + MAR_ED) // 2
           and env["fastest_seconds"] == MAR_ED
           and env["slowest_seconds"] == MAR_CY
           and env["mean_seconds"] == (JAN_BO + MAR_CY + MAR_ED) // 3)
    record("AC-SRM3", ok3,
           "jan=%r mar=%r env=%r"
           % ((jan["fastest_seconds"], jan["slowest_seconds"],
               jan["mean_seconds"]),
              (mar["fastest_seconds"], mar["slowest_seconds"],
               mar["mean_seconds"]),
              (env["fastest_seconds"], env["slowest_seconds"],
               env["mean_seconds"])))

    # -- AC-SRM4 backlog split, conservation, participants ----------
    ok4 = (all(row["backlog_count"] + row["same_month_count"]
               == row["replied_count"] for row in env["months"])
           and sum(row["backlog_count"] for row in env["months"])
           == env["backlog_reply_count"] == 1
           and sum(row["same_month_count"] for row in env["months"])
           == env["same_month_reply_count"] == 2
           and sum(row["replied_count"] for row in env["months"])
           == env["replied_count"] == 3
           and env["buyer_count"] == 3
           and env["listing_count"] == 2
           and env["owned_listing_count"] == 3
           and jan["buyer_count"] == 1
           and jan["listing_count"] == 1
           and mar["buyer_count"] == 2
           and mar["listing_count"] == 2)
    record("AC-SRM4", ok4,
           "backs=%r envelope=%r jan=%r mar=%r"
           % ([row["backlog_count"] for row in env["months"]],
              (env["replied_count"], env["backlog_reply_count"],
               env["same_month_reply_count"], env["buyer_count"],
               env["listing_count"], env["owned_listing_count"]),
              (jan["buyer_count"], jan["listing_count"]),
              (mar["buyer_count"], mar["listing_count"])))

    # -- AC-SRM5 contiguous grid, accumulator and the peak law ------
    feb = month_row(env, "2026-02")
    ok5 = (env["month_count"] == len(env["months"]) == 3
           and env["active_month_count"] == 2
           and feb["replied_count"] == 0
           and feb["backlog_count"] == 0
           and feb["same_month_count"] == 0
           and feb["buyer_count"] == 0
           and feb["listing_count"] == 0
           and feb["fastest_seconds"] is None
           and feb["slowest_seconds"] is None
           and feb["mean_seconds"] is None
           and feb["running_replied"] == jan["running_replied"] == 1
           and [row["running_replied"] for row in env["months"]]
           == [1, 1, 3]
           and env["months"][-1]["running_replied"]
           == env["replied_count"] == 3
           and env["latest_month_replied_count"] == 2
           and env["peak_month"] == "2026-03"
           and env["peak_replied_count"] == 2)
    record("AC-SRM5", ok5,
           "months=%d active=%d feb=%r running=%r peak=%r"
           % (env["month_count"], env["active_month_count"],
              (feb["replied_count"], feb["mean_seconds"]),
              [row["running_replied"] for row in env["months"]],
              (env["peak_month"], env["peak_replied_count"])))

    # -- AC-SRM6 scope law, isolation and cross-face identity ------
    life = am.api_rating_reply_latency("usr:dana")
    market = am.api_seller_reply_months()
    life_market = am.api_rating_reply_latency()
    gina = am.api_seller_reply_months("usr:gina")
    gina_life = am.api_rating_reply_latency("usr:gina")
    ok6 = (env["market_mean_seconds"] == market["mean_seconds"]
           and market["scope"] == "market"
           and market["dev_account"] is None
           and market["market_mean_seconds"] is None
           and market["rating_count"] == 6
           and market["replied_count"] == 4
           and market["unreplied_count"] == 2
           and market["backlog_reply_count"] == 2
           and market["same_month_reply_count"] == 2
           and market["fastest_seconds"] == MAR_ED
           and market["slowest_seconds"] == MAR_GI
           and market["mean_seconds"]
           == (JAN_BO + MAR_CY + MAR_ED + MAR_GI) // 4
           and life["rating_count"] == env["rating_count"] == 5
           and life["replied_count"] == env["replied_count"] == 3
           and life["unreplied_count"] == env["unreplied_count"] == 2
           and life["reply_coverage"] == env["reply_coverage"] == 0.6
           and life["fastest_seconds"] == env["fastest_seconds"]
           and life["slowest_seconds"] == env["slowest_seconds"]
           and life["oldest_unreplied_utc"]
           == env["oldest_unreplied_utc"] == "2026-03-10T00:00:00Z"
           and life_market["replied_count"] == market["replied_count"]
           and life_market["slowest_seconds"]
           == market["slowest_seconds"]
           and gina["replied_count"] == 1
           and gina["backlog_reply_count"] == 1
           and gina["same_month_reply_count"] == 0
           and gina["buyer_count"] == 1
           and gina["owned_listing_count"] == 1
           and gina["month_count"] == 1
           and gina["months"][0]["month"] == "2026-03"
           and gina["months"][0]["backlog_count"] == 1
           and gina["fastest_seconds"] == MAR_GI
           and gina["slowest_seconds"] == MAR_GI
           and gina_life["slowest_seconds"] == MAR_GI
           and gina["mean_seconds"] == MAR_GI)
    record("AC-SRM6", ok6,
           "lifetime=%r face=%r market=%r gina=%r"
           % ((life["replied_count"], life["reply_coverage"],
               life["oldest_unreplied_utc"]),
              (env["replied_count"], env["reply_coverage"],
               env["market_mean_seconds"]),
              (market["month_count"], market["mean_seconds"]),
              (gina["replied_count"], gina["month_count"],
               gina["mean_seconds"])))

    # -- AC-SRM7 account gate and the pure read --------------------
    codes = [error_code(am.api_seller_reply_months, form)
             for form in BAD_ACCOUNTS]
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    call_a = dumps(am.api_seller_reply_months("usr:dana"))
    call_b = dumps(am.api_seller_reply_months("usr:dana"))
    market_a = dumps(am.api_seller_reply_months())
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (codes == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and call_a == call_b == dumps(env)
           and market_a == dumps(market)
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-SRM7", ok7,
           "gate=%r deterministic=%r digests_same=%r tx_same=%r"
           % (codes, call_a == call_b,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-SRM8 restarts, wiring and hygiene ----------------------
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_seller_reply_months("usr:dana"))
    market_c = dumps(am2.api_seller_reply_months())
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_seller_reply_months("usr:dana"))
    market_d = dumps(am3.api_seller_reply_months())
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (call_a == call_c == call_d == dumps(env)
           and market_a == market_c == market_d == dumps(market)
           and b'"ledger-apimarket-sellerreplymonths"' in recon
           and b"test_apimarket_sellerreplymonths.py" in recon
           and b"def api_seller_reply_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-SRM8", ok8,
           "bytes_same=%r wired=%r ascii=%r crlf_clean=%r"
           % (call_a == call_d,
              b'"ledger-apimarket-sellerreplymonths"' in recon,
              all(b < 128 for b in test_src),
              b"\r\n" not in test_src))

    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    print("PRODUCT_SHA_STABLE %r" % (shas_before == shas_after),
          flush=True)

    green = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d" % (green, len(RESULTS)), flush=True)
    return 0 if green == len(RESULTS) else 1


_CLOCK = Clock()


if __name__ == "__main__":
    sys.exit(main())