"""Acceptance suite for the apimarket developer sales board
three-month purchase straddle cross-restart persistence example
window (BigDomain R2073; canon = the explore-queue FIFO head
seeded by R2045 and claimed in R2073, criteria AC-AMSTR1..7
registered in the claim note BEFORE this code existed - honesty
law; the AC-AMSTR prefix, the suite name and the
ledger-apimarket-devboardmonthstraddle runner label were all
git-grep zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.dev_sales_board(window=None) -
the R2022 month-window read face (record-time dual-family
slicing: listing_count by the listed_utc prefix, purchase
aggregates by the purchased_utc prefix). The R2045 window
pinned OCT listing + NOV first purchase on the boundary world;
this window grows the loaded three-month world and pins:

  - the exact boundary second law: a record stamped
    2026-10-31T23:59:59Z belongs to OCT only and a record
    stamped 2026-11-01T00:00:00Z belongs to NOV only (same for
    NOV/DEC), with adjacent-second pairs landing on opposite
    sides and each side counted exactly once;
  - three-window zero-permeation: the OCT window snapshot taken
    between the OCT records and the later months stays
    byte-frozen while NOV and DEC records accumulate, and NOV
    stays frozen while DEC records land;
  - the third-month purchase face: a DEC purchase rides an OCT
    listing and a NOV listing, so the DEC window shows purchase
    aggregates on rows whose listing_count is zero for both
    developers (registration month never decides the sales
    month, in every direction);
  - three-month conservation: OCT + NOV + DEC gross equals the
    lifetime gross, per developer and in total, with the
    purchase ids partitioned (zero double counting) and every
    row holding gross == dev + platform;
  - the dense ever-listed row set across every month window
    (SEP / OCT / NOV / DEC / 2099-01) with honest zero rows;
  - full-stack restart persistence (three instances, byte-
    identical five-form family) and the fourteen-form bad-window
    gate family rejecting E_AM_BAD_WINDOW before any read on the
    loaded world with zero mutations;
  - hygiene: product sha256 double-proof, pure ASCII, zero
    network imports, registry wiring, criteria count.

Usage: python test_apimarket_devboardmonth_straddlepersist.py
"""

import hashlib
import io
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

OCT_LIST_TS = "2026-10-15T09:00:00Z"
NOV_LIST_TS = "2026-11-10T09:00:00Z"

OCT_FIRST_SEC = "2026-10-01T00:00:00Z"
OCT_LAST_SEC = "2026-10-31T23:59:59Z"
NOV_FIRST_SEC = "2026-11-01T00:00:00Z"
NOV_LAST_SEC = "2026-11-30T23:59:59Z"
DEC_FIRST_SEC = "2026-12-01T00:00:00Z"
DEC_LAST_SEC = "2026-12-31T23:59:59Z"

WINDOWS = ["2026-09", "2026-10", "2026-11", "2026-12", "2099-01"]

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

BAD_FORMS = [2026, True, 2.5, "", "26-10", "2026-100", "abcd",
             "2026-13", "2026-00", "2026/10", "2026-1",
             " 2026-10", "2026-10\n", "2026-10-05"]

KEYS = ("listing_count", "purchase_count", "gross_revenue",
        "dev_revenue", "platform_revenue")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def table_digest(conn, table):
    rows = conn.execute(
        "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    blob = repr(rows).encode("utf-8")
    return len(rows), hashlib.sha256(blob).hexdigest()


def market_digests(am):
    conn = sqlite3.connect(am.db_path)
    out = {t: table_digest(conn, t) for t in
           ("apimarket_listings", "apimarket_purchases",
            "apimarket_ratings")}
    conn.close()
    return out


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def row_tuple(row):
    return (row["dev_account"], row["listing_count"],
            row["purchase_count"], row["gross_revenue"],
            row["dev_revenue"], row["platform_revenue"])


def manual_board(am, window=None):
    """Independent second derivation over a checker's own
    connection: dense ever-listed developer set, record-time
    prefix slicing per family, Python-side aggregation,
    registered order law. Zero shared code with the face."""
    conn = sqlite3.connect(am.db_path)
    listings = conn.execute(
        "SELECT listing_id, dev_account, listed_utc FROM"
        " apimarket_listings").fetchall()
    purchases = conn.execute(
        "SELECT listing_id, price_paid, dev_share,"
        " platform_share, purchased_utc FROM"
        " apimarket_purchases").fetchall()
    conn.close()
    dev_of = {int(lid): dev for lid, dev, _ts in listings}
    per_dev = {}
    for lid, dev, _ts in listings:
        per_dev.setdefault(dev, {k: 0 for k in KEYS})
    for lid, dev, listed in listings:
        if window is None or listed[:7] == window:
            per_dev[dev]["listing_count"] += 1
    for lid, price, dev_share, plat_share, purchased in purchases:
        if window is None or purchased[:7] == window:
            row = per_dev[dev_of[int(lid)]]
            row["purchase_count"] += 1
            row["gross_revenue"] += int(price)
            row["dev_revenue"] += int(dev_share)
            row["platform_revenue"] += int(plat_share)
    board = [{"dev_account": dev, **vals} for dev, vals in
             per_dev.items()]
    board.sort(key=lambda r: (-r["dev_revenue"],
                              -r["purchase_count"],
                              r["dev_account"]))
    return board


def record_month(am, month):
    """Direct SQL record-time month count, an orthogonal reading
    of the boundary second (no shared code with the face)."""
    conn = sqlite3.connect(am.db_path)
    n = int(conn.execute(
        "SELECT COUNT(*) FROM apimarket_purchases WHERE"
        " substr(purchased_utc, 1, 7) = ?", (month,)).fetchone()[0])
    conn.close()
    return n


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


def read_family(am):
    out = [dumps(am.dev_sales_board())]
    for window in WINDOWS:
        out.append(dumps(am.dev_sales_board(window)))
    return out


def gate_battery(am):
    codes = []
    for form in BAD_FORMS:
        try:
            am.dev_sales_board(form)
            codes.append(None)
        except A.ApiMarketError as exc:
            codes.append(exc.code)
    return codes


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-dsb-straddle-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg,
                                             lobby_cfg)
    led.mint_to_pool("pool:reserve", 4000, "SETTLE-AMSTR-A",
                     "settlement")
    led.mint_to_pool("pool:share", 4000, "SETTLE-AMSTR-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)

    clock = {"now": OCT_LIST_TS}
    orig_now = A._now_utc

    def fake_now():
        return clock["now"]

    def at(ts, fn, *args):
        A._now_utc = fake_now
        try:
            clock["now"] = ts
            return fn(*args)
        finally:
            A._now_utc = orig_now

    def publish(dev, key, title, price, ts):
        return at(ts, am.publish_api, dev, key, title,
                  "straddle world listing", PAYLOAD, price, False)

    def buy(who, listing_id, ref, ts):
        return at(ts, am.purchase_api, "usr:" + who, listing_id,
                  ref)

    # -- world: two developers, three listings, six purchases ---
    dana_oct = publish("usr:dana", "dana-oct", "Dana OCT API", 10,
                       OCT_LIST_TS)
    dana_nov = publish("usr:dana", "dana-nov", "Dana NOV API", 20,
                       NOV_LIST_TS)
    erin_oct = publish("usr:erin", "erin-oct", "Erin OCT API", 7,
                       OCT_LIST_TS)

    # OCT-side records (month-start and month-end seconds)
    buy("dave", erin_oct["listing_id"], "str-oct-first",
        OCT_FIRST_SEC)
    buy("bob", dana_oct["listing_id"], "str-oct-last", OCT_LAST_SEC)
    oct_snap = [dumps(am.dev_sales_board(w)) for w in WINDOWS]
    oct_count = record_month(am, "2026-10")

    # NOV-side records (first second and month-end second)
    buy("carol", dana_oct["listing_id"], "str-nov-first",
        NOV_FIRST_SEC)
    buy("dave", dana_nov["listing_id"], "str-nov-last", NOV_LAST_SEC)
    nov_snap = [dumps(am.dev_sales_board(w)) for w in WINDOWS]
    nov_count = record_month(am, "2026-11")

    # DEC third month (first second and month-end second)
    buy("bob", dana_nov["listing_id"], "str-dec-first", DEC_FIRST_SEC)
    buy("carol", erin_oct["listing_id"], "str-dec-last", DEC_LAST_SEC)

    d1 = market_digests(am)
    tx1 = sorted(ledger_tx_ids(led))
    env_def = am.dev_sales_board()
    family1 = read_family(am)

    # -- AC-AMSTR1 three-window anchor on the loaded world ------
    expect_default = [("usr:dana", 2, 4, 60, 42, 18),
                      ("usr:erin", 1, 2, 14, 10, 4)]
    expect_oct = [("usr:dana", 1, 1, 10, 7, 3),
                  ("usr:erin", 1, 1, 7, 5, 2)]
    expect_nov = [("usr:dana", 1, 2, 30, 21, 9),
                  ("usr:erin", 0, 0, 0, 0, 0)]
    expect_dec = [("usr:dana", 0, 1, 20, 14, 6),
                  ("usr:erin", 0, 1, 7, 5, 2)]
    ok1 = []
    ok1.append(sorted(env_def.keys()) == ["board", "disclaimer"])
    ok1.append([row_tuple(r) for r in env_def["board"]]
               == expect_default)
    for window, expected in (("2026-10", expect_oct),
                             ("2026-11", expect_nov),
                             ("2026-12", expect_dec)):
        env = am.dev_sales_board(window)
        ok1.append(sorted(env.keys())
                   == ["board", "disclaimer", "window"])
        ok1.append(env["window"] == window)
        ok1.append([row_tuple(r) for r in env["board"]] == expected)
    ok1.append([row_tuple(r) for r in env_def["board"]]
               == [row_tuple(r) for r in manual_board(am)])
    ok1.append(all([row_tuple(r) for r in
                    am.dev_sales_board(w)["board"]]
                   == [row_tuple(r) for r in manual_board(am, w)]
                   for w in WINDOWS))
    ok1.append(read_family(am) == family1)
    ok1.append(all(r["gross_revenue"] == r["dev_revenue"]
                   + r["platform_revenue"]
                   for w in (None,) + tuple(WINDOWS)
                   for r in am.dev_sales_board(w)["board"]))
    record("AC-AMSTR1", all(ok1),
           "three-month loaded world anchor: default lifetime"
           " board == %s (dana 60/42/18 over four purchases,"
           " erin 14/10/4 over two); OCT window == %s; NOV"
           " window == %s; DEC window == %s; every window"
           " envelope carries the echo key, every row holds"
           " gross == dev + platform, the five-form family is"
           " self-stable and equals the independent manual"
           " derivation on every form"
           % (expect_default, expect_oct, expect_nov,
              expect_dec))

    # -- AC-AMSTR2 exact boundary-second law --------------------
    conn = sqlite3.connect(am.db_path)
    stamps = conn.execute(
        "SELECT buyer_id, purchased_utc FROM apimarket_purchases"
        " ORDER BY purchase_id").fetchall()
    conn.close()
    pairs = [(OCT_LAST_SEC, NOV_FIRST_SEC), (NOV_LAST_SEC,
                                             DEC_FIRST_SEC)]
    ok2 = []
    ok2.append(oct_count == 2 and nov_count == 2)
    ok2.append(record_month(am, "2026-12") == 2)
    ok2.append(record_month(am, "2026-09") == 0)
    ok2.append(record_month(am, "2099-01") == 0)
    for left, right in pairs:
        ok2.append(left[:7] != right[:7])
        ok2.append(left[:10] + " " < right[:10] + " ")
        ok2.append(len(left) == len(right) == 20)
    seen = [str(s[1]) for s in stamps]
    ok2.append(len(seen) == 6)
    ok2.append(sorted(seen) == [OCT_FIRST_SEC, OCT_LAST_SEC,
                                NOV_FIRST_SEC, NOV_LAST_SEC,
                                DEC_FIRST_SEC, DEC_LAST_SEC])
    # each boundary stamp is counted exactly once by its own
    # month, and the neighbour month count never absorbs it
    ok2.append(seen.count(OCT_LAST_SEC) == 1
               and seen.count(NOV_FIRST_SEC) == 1)
    ok2.append(seen.count(NOV_LAST_SEC) == 1
               and seen.count(DEC_FIRST_SEC) == 1)
    ok2.append(seen.count(DEC_LAST_SEC) == 1)
    record("AC-AMSTR2", all(ok2),
           "exact boundary-second law: the six purchase stamps"
           " are %s; the OCT window counts exactly the two OCT"
           " records (month-start %s and month-end %s) and the"
           " NOV window exactly its two, the DEC window exactly"
           " its two (first %s, month-end %s); the last second of"
           " a month never leaks into the next month and the"
           " first second never leaks back; the SEP and 2099-01"
           " months count zero rows"
           % (seen, OCT_FIRST_SEC, OCT_LAST_SEC, DEC_FIRST_SEC,
              DEC_LAST_SEC))

    # -- AC-AMSTR3 zero-permeation: earlier windows frozen ------
    i_oct = WINDOWS.index("2026-10")
    i_nov = WINDOWS.index("2026-11")
    i_dec = WINDOWS.index("2026-12")
    ok3 = []
    # the OCT window taken between the OCT records and the NOV
    # records is unchanged by both later months
    ok3.append(dumps(am.dev_sales_board("2026-10"))
               == oct_snap[i_oct])
    ok3.append(dumps(am.dev_sales_board("2026-09"))
               == oct_snap[WINDOWS.index("2026-09")])
    ok3.append(dumps(am.dev_sales_board("2099-01"))
               == oct_snap[WINDOWS.index("2099-01")])
    # the NOV window taken before the DEC records is unchanged
    # by the DEC month
    ok3.append(dumps(am.dev_sales_board("2026-11"))
               == nov_snap[i_nov])
    # liveness in the other direction: the DEC window is new
    ok3.append(dumps(am.dev_sales_board("2026-12"))
               != nov_snap[i_dec])
    ok3.append(dumps(am.dev_sales_board("2026-10"))
               != dumps(am.dev_sales_board("2026-12")))
    record("AC-AMSTR3", all(ok3),
           "zero-permeation: the OCT window snapshot taken"
           " between the OCT records and the NOV records stays"
           " byte-identical after both later months accumulate"
           " (SEP and the out month likewise frozen), while the"
           " NOV window equals its own snapshot taken before the"
           " DEC records landed - no later purchase reaches an"
           " earlier window, and no earlier listing blocks a"
           " later purchase")

    # -- AC-AMSTR4 three-month conservation ---------------------
    def sum_rows(board, key):
        return sum(r[key] for r in board)

    octb = am.dev_sales_board("2026-10")["board"]
    novb = am.dev_sales_board("2026-11")["board"]
    decb = am.dev_sales_board("2026-12")["board"]
    lifeb = am.dev_sales_board()["board"]
    ok4 = []
    for key in ("purchase_count", "gross_revenue", "dev_revenue",
                "platform_revenue"):
        ok4.append(sum_rows(octb, key) + sum_rows(novb, key)
                   + sum_rows(decb, key) == sum_rows(lifeb, key))
    ok4.append(sum_rows(octb, "purchase_count") == 2
               and sum_rows(novb, "purchase_count") == 2
               and sum_rows(decb, "purchase_count") == 2)
    ok4.append(sum_rows(lifeb, "gross_revenue") == 74)
    conn = sqlite3.connect(am.db_path)
    ids_by_month = {}
    for month in ("2026-10", "2026-11", "2026-12"):
        ids_by_month[month] = set(int(r[0]) for r in conn.execute(
            "SELECT purchase_id FROM apimarket_purchases WHERE"
            " substr(purchased_utc, 1, 7) = ?", (month,)).fetchall())
    all_ids = set(int(r[0]) for r in conn.execute(
        "SELECT purchase_id FROM apimarket_purchases").fetchall())
    conn.close()
    union = set()
    overlap = 0
    for ids in ids_by_month.values():
        overlap += len(union & ids)
        union |= ids
    ok4.append(overlap == 0 and union == all_ids
               and len(all_ids) == 6)
    ok4.append(ids_by_month["2026-10"] & ids_by_month["2026-11"]
               == set())
    ok4.append(ids_by_month["2026-11"] & ids_by_month["2026-12"]
               == set())
    record("AC-AMSTR4", all(ok4),
           "three-month conservation: OCT + NOV + DEC equals the"
           " lifetime board on purchase_count, gross, dev and"
           " platform (2 + 2 + 2 = 6 purchases, 17 + 30 + 27 ="
           " 74 gross); the per-month purchase_id sets are"
           " disjoint and their union is exactly the market's"
           " six rows (zero double counting), and every window"
           " row still holds gross == dev + platform")

    # -- AC-AMSTR5 dense ever-listed row set --------------------
    ok5 = []
    for window in WINDOWS:
        devs = [r["dev_account"]
                for r in am.dev_sales_board(window)["board"]]
        ok5.append(devs == ["usr:dana", "usr:erin"]
                   or devs == ["usr:erin", "usr:dana"])
    order = [r["dev_account"] for r in lifeb]
    ok5.append(order == ["usr:dana", "usr:erin"])
    ok5.append([row_tuple(r)
                for r in am.dev_sales_board("2099-01")["board"]]
               == [("usr:dana", 0, 0, 0, 0, 0),
                   ("usr:erin", 0, 0, 0, 0, 0)])
    ok5.append(am.dev_sales_board("2026-09")["board"] ==
               am.dev_sales_board("2099-01")["board"])
    record("AC-AMSTR5", all(ok5),
           "dense ever-listed row set: both developers appear in"
           " every month window (SEP / OCT / NOV / DEC /"
           " 2099-01) with honest zero rows where they have no"
           " activity, and the lifetime ordering law (dev"
           " revenue desc, purchases desc, account asc) puts"
           " dana first")

    # -- AC-AMSTR6 restart persistence + gate on loaded world ---
    snaps = family1
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                 lobby_cfg)
    family2 = read_family(am2)
    d2 = market_digests(am2)
    tx2 = sorted(ledger_tx_ids(led2))
    codes1 = gate_battery(am2)
    d2b = market_digests(am2)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                 lobby_cfg)
    family3 = read_family(am3)
    codes2 = gate_battery(am3)
    ok6 = []
    ok6.append(family2 == snaps)
    ok6.append(family3 == snaps)
    ok6.append(d1 == d2 and tx1 == tx2)
    ok6.append(codes1 == [A.E_AM_BAD_WINDOW] * len(BAD_FORMS))
    ok6.append(codes2 == codes1)
    ok6.append(market_digests(am3) == d2)
    ok6.append(sorted(ledger_tx_ids(led3)) == tx2)
    ok6.append(d2b == d2)
    record("AC-AMSTR6", all(ok6),
           "restart persistence: full-stack close (am -> dk ->"
           " metered -> led) and same-db/z same-cfg rebuild on"
           " instances two and three replay all five read forms"
           " byte-identically to the pre-close family (the"
           " straddle world and every window echo cross the"
           " restart with zero in-memory drift); the %d-form"
           " bad-window gate family answers E_AM_BAD_WINDOW on"
           " every form on both instances on the LOADED world,"
           " and the probe batch leaves the three market tables"
           " and the ledger_tx set constant (gate before any"
           " read, zero mutation)" % len(BAD_FORMS))

    # -- AC-AMSTR7 hygiene / wiring -----------------------------
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    with io.open(os.path.abspath(__file__), "rb") as handle:
        raw = handle.read()
    text = raw.decode("ascii")
    bad_imports = [line for line in text.splitlines()
                   if line.strip().startswith(("import socket",
                                               "import requests",
                                               "import urllib",
                                               "import http"))]
    recon = io.open(os.path.join(BASE, "..", "reconcile_all.py"),
                    encoding="utf-8").read()
    ok7 = []
    ok7.append(shas_before == shas_after)
    ok7.append("ledger-apimarket-devboardmonthstraddle" in recon)
    ok7.append(bad_imports == [])
    ok7.append("tempfile" in text and "prefix=" in text)
    ok7.append(len(RESULTS) == 6)   # this record lands after
    record("AC-AMSTR7", all(ok7),
           "hygiene and wiring: the five product files sha256"
           " are unchanged across the whole run, the suite"
           " source is pure ASCII with zero network imports,"
           " its temp world lives outside the repo, and the"
           " ledger-apimarket-devboardmonthstraddle label is"
           " wired into reconcile_all")

    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              len(RESULTS) - len(failed),
                              len(RESULTS)), flush=True)
    if failed:
        print("FAILED: " + ", ".join(failed), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())