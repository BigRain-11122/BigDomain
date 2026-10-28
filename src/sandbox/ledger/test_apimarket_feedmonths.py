"""Acceptance suite for the apimarket monthly activity-volume timeline
(BigDomain R2212; canon = the R2212 explore-queue claim row, criteria
AC-FMD1..AC-FMD8 registered in that row BEFORE this code existed).

Face under proof: APIMarketFace.api_market_feed_months. api_market_feed
answers "what just happened" as one flat ordered stream behind a
half-open window, so the shape of activity over months (a burst month
against a quiet one) can only be counted by hand, and every month face
already shipped reads a single family. This suite pins:

  - the seventeen-key envelope, the six-key month rows and the honest
    empty world;
  - the booking law (each event books in the month of its own immutable
    stamp, a revision being its own event);
  - the contiguous grid with an honest zero month and the running
    accumulator;
  - conservation of the per-month family counts, the monthly totals and
    the envelope totals;
  - the peak laws with the earlier-month tie-break and the pinned feed
    rank on a kind tie;
  - the filter laws (window, kinds normalization, seller scope) and the
    filter echo;
  - the fail-closed gate chain in the pinned feed order;
  - cross-face identity with api_market_feed and the rating month face,
    the pure-read law (frozen table digests, constant ledger_tx set),
    cross-instance byte identity, wiring and ASCII/LF hygiene.

Usage: python test_apimarket_feedmonths.py
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
    "scope", "dev_account", "since_utc", "until_utc", "kinds",
    "month_count", "active_month_count", "event_total", "by_kind",
    "busiest_kind", "peak_month", "peak_event_count", "first_month",
    "last_month", "latest_month_event_count", "disclaimer", "months"}

ROW_KEYS = {
    "month", "event_count", "by_kind", "busiest_kind",
    "active_kind_count", "running_total"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds", "apimarket_category_revisions")


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
    """Two sellers. dana owns t1 and d1, gina owns g1.

    2026-01: three publishes (t1, d1, g1), two purchases (bo, cy on
    t1), two ratings and one price revision = 8 events.
    2026-02: nothing at all (the honest zero row of the grid).
    2026-03: two purchases (di on d1, bo on g1), two ratings and one
    delisting = 5 events.
    2026-04: one rating revision and one rating reply = 2 events.

    Market: 15 events over four months, peak January with 8, busiest
    family purchased-and-rated tied at 4 and resolved to purchased by
    the pinned rank.
    """
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-FMD-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-FMD-S",
                     "settlement")
    for dev in ("dana", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)
    for who in ("bo", "cy", "di"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)

    clock.value = "2026-01-05T00:00:00Z"
    t1 = am.publish_api("usr:dana", "t1", "Dana Tools API",
                        "dana tools payloads", PAYLOAD, 10, False,
                        category="tools")["listing_id"]
    d1 = am.publish_api("usr:dana", "d1", "Dana Data API",
                        "dana data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina Data API",
                        "gina data payloads", PAYLOAD, 10, False,
                        category="data")["listing_id"]

    clock.value = "2026-01-09T00:00:00Z"
    am.purchase_api("usr:bo", t1, "buy-bo-t1")
    am.purchase_api("usr:cy", t1, "buy-cy-t1")

    clock.value = "2026-01-12T00:00:00Z"
    bo_t1 = am.rate_api("usr:bo", t1, 5)["rating_id"]
    clock.value = "2026-01-13T00:00:00Z"
    cy_t1 = am.rate_api("usr:cy", t1, 3)["rating_id"]

    clock.value = "2026-01-20T00:00:00Z"
    am.revise_price("usr:dana", t1, 15)

    clock.value = "2026-03-02T00:00:00Z"
    am.purchase_api("usr:di", d1, "buy-di-d1")
    clock.value = "2026-03-04T00:00:00Z"
    am.purchase_api("usr:bo", g1, "buy-bo-g1")

    clock.value = "2026-03-09T00:00:00Z"
    am.rate_api("usr:di", d1, 1)
    clock.value = "2026-03-10T00:00:00Z"
    am.rate_api("usr:bo", g1, 4)

    clock.value = "2026-03-15T00:00:00Z"
    am.delist_api("usr:gina", g1)

    clock.value = "2026-04-02T00:00:00Z"
    am.revise_rating("usr:cy", cy_t1, 2)
    clock.value = "2026-04-06T00:00:00Z"
    am.reply_to_rating("usr:dana", bo_t1, "thanks for the review")

    return {"t1": t1, "d1": d1, "g1": g1,
            "bo_t1": bo_t1, "cy_t1": cy_t1}


def main():
    global _CLOCK
    tmp = tempfile.mkdtemp(prefix="apimarket-feedmonths-")
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

    # -- AC-FMD1 the contract and the honest empty world ------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-fmd-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_market_feed_months()
    close_stack(e_am, e_dk, e_metered, e_led)
    env = am.api_market_feed_months()
    rows_ok = all(set(row.keys()) == ROW_KEYS for row in env["months"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and rows_ok
           and env["disclaimer"] == DISCLAIMER
           and env["scope"] == "market"
           and env["dev_account"] is None
           and env["since_utc"] is None
           and env["until_utc"] is None
           and env["kinds"] == list(A._FEED_KINDS)
           and empty["scope"] == "market"
           and empty["month_count"] == 0
           and empty["months"] == []
           and empty["event_total"] == 0
           and empty["by_kind"] == {}
           and empty["busiest_kind"] is None
           and empty["first_month"] is None
           and empty["last_month"] is None
           and empty["latest_month_event_count"] == 0
           and empty["peak_month"] is None
           and empty["peak_event_count"] is None
           and empty["active_month_count"] == 0)
    record("AC-FMD1", ok1,
           "env_keys=%d exact=%r row_keys=%r empty=%r"
           % (len(env), set(env.keys()) == ENVELOPE_KEYS, rows_ok,
              (empty["month_count"], empty["event_total"],
               empty["months"], empty["peak_month"])))

    # -- AC-FMD2 booking law: every family books in its own month ---
    jan = month_row(env, "2026-01")
    mar = month_row(env, "2026-03")
    apr = month_row(env, "2026-04")
    grid = [row["month"] for row in env["months"]]
    ok2 = (grid == ["2026-01", "2026-02", "2026-03", "2026-04"]
           and jan["event_count"] == 8
           and jan["by_kind"] == {"published": 3, "price_revised": 1,
                                  "purchased": 2, "rated": 2}
           and mar["event_count"] == 5
           and mar["by_kind"] == {"purchased": 2, "rated": 2,
                                  "delisted": 1}
           and apr["event_count"] == 2
           and apr["by_kind"] == {"rating_revised": 1,
                                  "rating_replied": 1}
           and env["first_month"] == "2026-01"
           and env["last_month"] == "2026-04"
           and env["event_total"] == 15)
    record("AC-FMD2", ok2,
           "grid=%r jan=%r mar=%r apr=%r total=%r"
           % (grid, jan["by_kind"], mar["by_kind"], apr["by_kind"],
              env["event_total"]))

    # -- AC-FMD3 contiguous grid, honest zero month, accumulator ----
    feb = month_row(env, "2026-02")
    ok3 = (env["month_count"] == len(env["months"]) == 4
           and env["active_month_count"] == 3
           and feb["event_count"] == 0
           and feb["by_kind"] == {}
           and feb["busiest_kind"] is None
           and feb["active_kind_count"] == 0
           and feb["running_total"] == jan["running_total"] == 8
           and [row["running_total"] for row in env["months"]]
           == [8, 8, 13, 15]
           and env["months"][-1]["running_total"]
           == env["event_total"] == 15
           and env["latest_month_event_count"] == 2
           and jan["active_kind_count"] == 4
           and mar["active_kind_count"] == 3)
    record("AC-FMD3", ok3,
           "months=%d active=%d feb=%r running=%r"
           % (env["month_count"], env["active_month_count"],
              (feb["event_count"], feb["by_kind"], feb["busiest_kind"]),
              [row["running_total"] for row in env["months"]]))

    # -- AC-FMD4 conservation, three ways --------------------------
    sum_count = sum(row["event_count"] for row in env["months"])
    sum_kind = sum(env["by_kind"].values())
    row_sums_ok = all(sum(row["by_kind"].values()) == row["event_count"]
                      for row in env["months"])
    rating_months = am.api_market_rating_months()
    rated_total = sum(row["by_kind"].get("rated", 0)
                      for row in env["months"])
    ok4 = (sum_count == env["event_total"] == 15
           and sum_kind == env["event_total"]
           and row_sums_ok
           and env["by_kind"] == {"published": 3, "price_revised": 1,
                                  "purchased": 4, "rated": 4,
                                  "rating_revised": 1,
                                  "rating_replied": 1, "delisted": 1}
           and all(row["active_kind_count"] == len(row["by_kind"])
                   for row in env["months"])
           and rated_total == rating_months["rating_count"] == 4)
    record("AC-FMD4", ok4,
           "counts=%r kinds_sum=%r rows_ok=%r by_kind=%r rated=%r"
           % (sum_count, sum_kind, row_sums_ok, env["by_kind"],
              (rated_total, rating_months["rating_count"])))

    # -- AC-FMD5 peak laws: earlier month, pinned rank on a tie ----
    ok5 = (env["peak_month"] == "2026-01"
           and env["peak_event_count"] == 8
           and env["busiest_kind"] == "purchased"
           and jan["busiest_kind"] == "published"
           and mar["busiest_kind"] == "purchased"
           and apr["busiest_kind"] == "rating_revised"
           and env["by_kind"]["purchased"] == env["by_kind"]["rated"] == 4
           and A._FEED_KIND_RANK["purchased"]
           < A._FEED_KIND_RANK["rated"]
           and A._FEED_KIND_RANK["rating_revised"]
           < A._FEED_KIND_RANK["rating_replied"])
    record("AC-FMD5", ok5,
           "peak=%r busiest=%r jan=%r mar=%r apr=%r"
           % ((env["peak_month"], env["peak_event_count"]),
              env["busiest_kind"], jan["busiest_kind"],
              mar["busiest_kind"], apr["busiest_kind"]))

    # -- AC-FMD6 filters compose and are echoed --------------------
    dana = am.api_market_feed_months(dev_account="usr:dana")
    gina = am.api_market_feed_months(dev_account="usr:gina")
    picked = am.api_market_feed_months(
        kinds=["rated", "purchased"])
    windowed = am.api_market_feed_months(
        since_utc="2026-03-01T00:00:00Z",
        until_utc="2026-04-01T00:00:00Z")
    bare = am.api_market_feed_months(dev_account="usr:")
    dana_grid = [row["month"] for row in dana["months"]]
    ok6 = (dana["scope"] == "seller"
           and dana["dev_account"] == "usr:dana"
           and dana["event_total"] == 11
           and dana_grid == ["2026-01", "2026-02", "2026-03",
                             "2026-04"]
           and month_row(dana, "2026-01")["event_count"] == 7
           and month_row(dana, "2026-03")["event_count"] == 2
           and month_row(dana, "2026-04")["event_count"] == 2
           and dana["by_kind"].get("delisted") is None
           and gina["scope"] == "seller"
           and gina["event_total"] == 4
           and [row["month"] for row in gina["months"]]
           == ["2026-01", "2026-02", "2026-03"]
           and gina["by_kind"]["delisted"] == 1
           and picked["kinds"] == ["purchased", "rated"]
           and picked["event_total"] == 8
           and picked["by_kind"] == {"purchased": 4, "rated": 4}
           and picked["busiest_kind"] == "purchased"
           and set(picked["months"][0]["by_kind"]) <= {"purchased",
                                                       "rated"}
           and windowed["since_utc"] == "2026-03-01T00:00:00Z"
           and windowed["until_utc"] == "2026-04-01T00:00:00Z"
           and windowed["event_total"] == 5
           and [row["month"] for row in windowed["months"]]
           == ["2026-03"]
           and bare["scope"] == "seller"
           and bare["event_total"] == 0
           and bare["months"] == []
           and bare["peak_month"] is None)
    record("AC-FMD6", ok6,
           "dana=%r gina=%r picked=%r windowed=%r bare=%r"
           % (dana["event_total"], gina["event_total"],
              (picked["kinds"], picked["event_total"]),
              (windowed["event_total"],
               [row["month"] for row in windowed["months"]]),
              (bare["event_total"], bare["months"])))

    # -- AC-FMD7 the gate chain, fail-closed before any read -------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_window = ["2026-03", "2026-3-01T00:00:00Z",
                  "2026-03-01T00:00:00", 123, [], {}]
    refused_window = 0
    for form in bad_window:
        try:
            am.api_market_feed_months(since_utc=form)
        except A.ApiMarketError as exc:
            if str(exc).split(":")[0].strip() == A.E_AM_BAD_WINDOW:
                refused_window += 1
    refused_inverted = 0
    try:
        am.api_market_feed_months(
            since_utc="2026-04-01T00:00:00Z",
            until_utc="2026-03-01T00:00:00Z")
    except A.ApiMarketError as exc:
        if str(exc).split(":")[0].strip() == A.E_AM_BAD_WINDOW:
            refused_inverted = 1
    bad_kinds = ["purchased", [], [""], ["bought"], [1], [None],
                 ("rated", "nope")]
    refused_kinds = 0
    for form in bad_kinds:
        try:
            am.api_market_feed_months(kinds=form)
        except A.ApiMarketError as exc:
            if str(exc).split(":")[0].strip() == A.E_AM_BAD_ARGS:
                refused_kinds += 1
    bad_acct = ["", "u", "usr", "user:bo", 123, [], {"usr:bo": 1},
                False]
    refused_acct = 0
    for form in bad_acct:
        try:
            am.api_market_feed_months(dev_account=form)
        except A.ApiMarketError as exc:
            if str(exc).split(":")[0].strip() == A.E_AM_BAD_ACCOUNT:
                refused_acct += 1
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (refused_window == len(bad_window)
           and refused_inverted == 1
           and refused_kinds == len(bad_kinds)
           and refused_acct == len(bad_acct)
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-FMD7", ok7,
           "window=%d/%d inverted=%d kinds=%d/%d acct=%d/%d"
           " digests_same=%r tx_same=%r"
           % (refused_window, len(bad_window), refused_inverted,
              refused_kinds, len(bad_kinds), refused_acct,
              len(bad_acct), digests_before == digests_after,
              tx_before == tx_after))

    # -- AC-FMD8 cross-face identity, purity, determinism, wiring --
    feed_market = am.api_market_feed()
    feed_dana = am.api_market_feed(dev_account="usr:dana")
    feed_picked = am.api_market_feed(kinds=["rated", "purchased"])
    feed_window = am.api_market_feed(
        since_utc="2026-03-01T00:00:00Z",
        until_utc="2026-04-01T00:00:00Z")
    call_a = dumps(am.api_market_feed_months())
    call_b = dumps(am.api_market_feed_months())
    digests_end = market_digests(am)
    tx_end = ledger_tx_ids(led)

    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_c = dumps(am2.api_market_feed_months())
    dana2 = dumps(am2.api_market_feed_months(dev_account="usr:dana"))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    call_d = dumps(am3.api_market_feed_months())
    dana3 = dumps(am3.api_market_feed_months(dev_account="usr:dana"))
    close_stack(am3, dk3, metered3, led3)

    recon = open(os.path.join(os.path.dirname(BASE),
                              "reconcile_all.py"), "rb").read()
    src = open(os.path.join(BASE, "apimarket.py"), "rb").read()
    test_src = open(os.path.abspath(__file__), "rb").read()
    ok8 = (env["event_total"] == feed_market["total"]
           and dana["event_total"] == feed_dana["total"]
           and picked["event_total"] == feed_picked["total"]
           and windowed["event_total"] == feed_window["total"]
           and digests_before == digests_end
           and tx_before == tx_end
           and call_a == call_b == call_c == call_d == dumps(env)
           and dana2 == dana3 == dumps(dana)
           and b'"ledger-apimarket-feedmonths"' in recon
           and b"test_apimarket_feedmonths.py" in recon
           and b"def api_market_feed_months" in src
           and b"\r\n" not in src
           and b"\r\n" not in test_src
           and all(b < 128 for b in test_src))
    record("AC-FMD8", ok8,
           "feed_identity=%r digests_same=%r tx_same=%r"
           " bytes=%r wired=%r ascii=%r"
           % ((env["event_total"], feed_market["total"],
               picked["event_total"], feed_picked["total"]),
              digests_before == digests_end, tx_before == tx_end,
              call_a == call_d,
              b'"ledger-apimarket-feedmonths"' in recon,
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