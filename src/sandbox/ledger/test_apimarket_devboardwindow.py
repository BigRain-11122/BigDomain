"""Acceptance suite for the apimarket developer sales board
month-window read face (BigDomain R2022; canon = the R2005
reseeded explore-queue row claimed by R2022, criteria
AC-AMW1..AC-AMW7 registered in the claim note BEFORE this code
existed - honesty law; AC-AMW prefix, the E_AM_BAD_WINDOW code,
the dev_sales_board(window=None) signature, this suite name and
the ledger-apimarket-devboardwindow runner label were all
git-grep zero-occupancy anchored 2026-10-18).

Face under proof: APIMarketFace.dev_sales_board(window=None) -
the R1978 developer-level sales / revenue board extended with
the windowed-read family law (R1996/R1997/R1999/R2015
precedents, record-time law R1712):

  - default zero drift: no-arg and window=None calls are
    byte-identical, the envelope keeps exactly the two keys;
  - strict YYYY-MM gate before any read, dedicated
    E_AM_BAD_WINDOW code, fourteen bad forms all fail-closed
    with zero side effects;
  - record-time dual-family slicing: listing_count by the
    listed_utc prefix, purchase aggregates by the
    purchased_utc prefix - a listing's registration month
    never decides which month its sales land in;
  - dense ever-listed developer rows (honest zero rows in
    out-of-window months), honest [] on a zero-listing market;
  - additivity: the full board equals the month boards summed
    per developer per key (all five keys pure-additive);
  - pure-read law + hygiene.

World (frozen-clock fixture injection, product path real):
listings a1(ada,10) and c1(carol,10) recorded 2026-09,
a2(ada,3) and d1(dan,7) recorded 2026-10; purchases
bob->a1 and eve->c1 recorded 2026-09, bob->a2 and
eve->a1 recorded 2026-10 (the eve->a1 sale is the
registration-month separation probe: listed 09, sold 10).

Usage: python test_apimarket_devboardwindow.py
"""

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
import apimarket as A                 # noqa: E402 (R1763 face)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

SEP_TS = "2026-09-15T10:00:00Z"
OCT_TS = "2026-10-20T11:00:00Z"

CONFIG_FILES = [
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]


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


def ledger_tx_count(led):
    conn = sqlite3.connect(led.db_path)
    n = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])
    conn.close()
    return n


def row_tuple(row):
    return (row["dev_account"], row["listing_count"],
            row["purchase_count"], row["gross_revenue"],
            row["dev_revenue"], row["platform_revenue"])


KEYS = ("listing_count", "purchase_count", "gross_revenue",
        "dev_revenue", "platform_revenue")


def manual_board(am, window=None):
    """Independent second derivation over a checker's own
    connection: dense ever-listed developer set, record-time
    prefix slicing per family (listed_utc for listings,
    purchased_utc for purchases), Python-side aggregation,
    registered order law. Zero shared code with the product
    face."""
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


def utc_prefix(am, table, where, col):
    conn = sqlite3.connect(am.db_path)
    val = conn.execute(
        "SELECT substr(" + col + ", 1, 7) FROM " + table +
        " WHERE " + where).fetchone()[0]
    conn.close()
    return val


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-dsb-window-")
    db_path = os.path.join(tmp, "ledger.db")

    cfg_shas_before = {p: sha256_file(p) for p in CONFIG_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = {"now": SEP_TS}
    orig_now = A._now_utc

    def fake_now():
        return clock["now"]

    A._now_utc = fake_now
    try:
        led, metered, dk, gate, am = build_stack(db_path, cfg,
                                                 lobby_cfg)

        # -- world: accounts, dev keys, listings, purchases -----
        led.mint_to_pool("pool:reserve", 4000, "SETTLE-AMW-A",
                         "settlement")
        led.mint_to_pool("pool:share", 1000, "SETTLE-AMW-S",
                         "settlement")
        for who in ("ada", "carol", "dan", "bob", "eve"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
            led.adjust([("pool:reserve", "debit", 200),
                        ("usr:" + who, "credit", 200)],
                       "manual:fund-" + who, "suite funding " + who)
        for who, scopes in (("ada", ["backtest"]),
                            ("carol", ["backtest"]),
                            ("dan", ["visualize"])):
            dk.issue_key("usr:" + who, who + "-key", 10, scopes,
                         False)

        clock["now"] = SEP_TS
        a1 = am.publish_api("usr:ada", "risk-scan", "Risk Scan API",
                            "portfolio risk scan endpoint", PAYLOAD,
                            10, False)
        c1 = am.publish_api("usr:carol", "carol-alpha",
                            "Carol Alpha API", "carol first endpoint",
                            PAYLOAD, 10, False)
        clock["now"] = OCT_TS
        a2 = am.publish_api("usr:ada", "macro-feed",
                            "Macro Feed API",
                            "daily macro data feed", PAYLOAD, 3,
                            True)
        am.publish_api("usr:dan", "dan-echo", "Dan Echo API",
                       "dan dormant endpoint", PAYLOAD, 7, False)

        clock["now"] = SEP_TS
        am.purchase_api("usr:bob", a1["listing_id"], "pb1")
        am.purchase_api("usr:eve", c1["listing_id"], "pe2")
        clock["now"] = OCT_TS
        am.purchase_api("usr:bob", a2["listing_id"], "pb2")
        am.purchase_api("usr:eve", a1["listing_id"], "pe1")
    finally:
        A._now_utc = orig_now

    # -- AC-AMW1 default full-window zero drift ------------------
    env_none = am.dev_sales_board()
    env_arg = am.dev_sales_board(None)
    ok1 = []
    ok1.append(sorted(env_none.keys()) == ["board", "disclaimer"])
    ok1.append(dumps(env_none) == dumps(env_arg))
    ok1.append([row_tuple(r) for r in env_none["board"]] == [
        ("usr:ada", 2, 3, 23, 17, 6),
        ("usr:carol", 1, 1, 10, 7, 3),
        ("usr:dan", 1, 0, 0, 0, 0)])
    ok1.append(all(r["gross_revenue"] == r["dev_revenue"]
                   + r["platform_revenue"]
                   for r in env_none["board"]))
    ok1.append([row_tuple(r) for r in env_none["board"]]
               == [row_tuple(r) for r in manual_board(am)])
    ok1.append(dumps(am.dev_sales_board()) == dumps(env_none))
    record("AC-AMW1", all(ok1),
           "default zero drift: envelope keys %s; no-arg and"
           " window=None calls byte-identical; canonical world"
           " [(ada,2,3,23,17,6),(carol,1,1,10,7,3),"
           "(dan,1,0,0,0,0)]; per-row gross == dev + platform;"
           " independent manual cross equal; double-call"
           " identical" % sorted(env_none.keys()))

    # -- AC-AMW2 strict window gate, fail-closed -----------------
    d_gate = market_digests(am)
    tx_gate = ledger_tx_count(led)
    bad_forms = [2026, True, 2.5, "", "26-10", "2026-100",
                 "abcd", "2026-13", "2026-00", "2026/10",
                 "2026-1", " 2026-10", "2026-10\n",
                 "2026-10-05"]
    codes = []
    for form in bad_forms:
        try:
            am.dev_sales_board(form)
            codes.append(None)
        except A.ApiMarketError as exc:
            codes.append(exc.code)
    ok2 = [codes == [A.E_AM_BAD_WINDOW] * len(bad_forms),
           market_digests(am) == d_gate,
           ledger_tx_count(led) == tx_gate]
    record("AC-AMW2", all(ok2),
           "window gate fail-closed: %d bad forms (int/bool/"
           "float/empty/short/long/letters/month-13/month-00/"
           "slash/one-digit-month/leading-space/trailing-newline/"
           "day-segment) all reject E_AM_BAD_WINDOW before any"
           " read; empty string is not the default sentinel"
           " (None only); digests and ledger_tx constant across"
           " the probe batch" % len(bad_forms))

    # -- AC-AMW3 month-window slicing + cross-window fence -------
    sep = am.dev_sales_board("2026-09")
    octb = am.dev_sales_board("2026-10")
    ok3 = []
    ok3.append(sorted(sep.keys()) == ["board", "disclaimer",
                                      "window"])
    ok3.append(sep["window"] == "2026-09"
               and octb["window"] == "2026-10")
    ok3.append([row_tuple(r) for r in sep["board"]] == [
        ("usr:ada", 1, 1, 10, 7, 3),
        ("usr:carol", 1, 1, 10, 7, 3),
        ("usr:dan", 0, 0, 0, 0, 0)])
    ok3.append([row_tuple(r) for r in octb["board"]] == [
        ("usr:ada", 1, 2, 13, 10, 3),
        ("usr:carol", 0, 0, 0, 0, 0),
        ("usr:dan", 1, 0, 0, 0, 0)])
    ok3.append([row_tuple(r) for r in sep["board"]]
               == [row_tuple(r) for r in manual_board(am,
                                                      "2026-09")])
    ok3.append([row_tuple(r) for r in octb["board"]]
               == [row_tuple(r) for r in manual_board(am,
                                                      "2026-10")])
    ok3.append(all(r["gross_revenue"] == r["dev_revenue"]
                   + r["platform_revenue"]
                   for r in sep["board"] + octb["board"]))
    ok3.append(dumps(am.dev_sales_board("2026-09"))
               == dumps(sep))
    ok3.append(dumps(am.dev_sales_board("2026-10"))
               == dumps(octb))
    record("AC-AMW3", all(ok3),
           "month-window slicing: envelope %s with window echo;"
           " SEP board [(ada,1,1,10,7,3),(carol,1,1,10,7,3),"
           "(dan,0,0,0,0,0)] and OCT board [(ada,1,2,13,10,3),"
           "(carol,0,0,0,0,0),(dan,1,0,0,0,0)]; both equal the"
           " checker's record-time prefix recomputation"
           " (cross-window zero leakage both ways); conservation"
           " holds per row; double-call identical"
           % sorted(sep.keys()))

    # -- AC-AMW4 registration-month separation probe --------------
    a1_listed = utc_prefix(am, "apimarket_listings",
                           "listing_key = 'risk-scan'",
                           "listed_utc")
    pe1_purchased = utc_prefix(am, "apimarket_purchases",
                               "buyer_id = 'usr:eve' AND"
                               " listing_id = %d"
                               % a1["listing_id"],
                               "purchased_utc")
    ada_sep = [r for r in sep["board"]
               if r["dev_account"] == "usr:ada"][0]
    ada_oct = [r for r in octb["board"]
               if r["dev_account"] == "usr:ada"][0]
    dan_sep = [r for r in sep["board"]
               if r["dev_account"] == "usr:dan"][0]
    dan_oct = [r for r in octb["board"]
               if r["dev_account"] == "usr:dan"][0]
    ok4 = [a1_listed == "2026-09", pe1_purchased == "2026-10",
           ada_oct["purchase_count"] == 2,
           ada_sep["purchase_count"] == 1,
           dan_sep["listing_count"] == 0,
           dan_oct["listing_count"] == 1]
    record("AC-AMW4", all(ok4),
           "registration-month separation (record-time law):"
           " a1 listed %s but its eve sale recorded %s - the"
           " OCT window carries it (ada OCT purchases == 2"
           " including the Sep-listed sale), the SEP window"
           " does not (== 1); the listing's registration month"
           " never decides which month its sales land in; dan"
           " listed only in OCT so the SEP window keeps a dense"
           " zero row (listing_count 0) while OCT shows 1"
           % (a1_listed, pe1_purchased))

    # -- AC-AMW5 out-month dense zeros + empty market honest [] --
    ok5 = []
    for w in ("2026-08", "2026-11", "2099-01"):
        env = am.dev_sales_board(w)
        ok5.append(sorted(env.keys()) == ["board", "disclaimer",
                                         "window"])
        ok5.append(env["window"] == w)
        ok5.append([row_tuple(r) for r in env["board"]] == [
            ("usr:ada", 0, 0, 0, 0, 0),
            ("usr:carol", 0, 0, 0, 0, 0),
            ("usr:dan", 0, 0, 0, 0, 0)])
        ok5.append(dumps(am.dev_sales_board(w)) == dumps(env))
    empty_dir = os.path.join(tmp, "empty")
    os.makedirs(empty_dir, exist_ok=True)
    db2 = os.path.join(empty_dir, "ledger2.db")
    led2, metered2, dk2, gate2, am2 = build_stack(db2, cfg,
                                                  lobby_cfg)
    empty_env = am2.dev_sales_board("2026-10")
    try:
        am2.dev_sales_board("2026-13")
        empty_gate = None
    except A.ApiMarketError as exc:
        empty_gate = exc.code
    ok5b = [empty_env["board"] == [],
            sorted(empty_env.keys()) == ["board", "disclaimer",
                                         "window"],
            empty_env["window"] == "2026-10",
            am2.dev_sales_board()["board"] == [],
            empty_gate == A.E_AM_BAD_WINDOW]
    close_stack(am2, dk2, metered2, led2)
    record("AC-AMW5", all(ok5) and all(ok5b),
           "out-of-range months (2026-08 / 2026-11 / 2099-01):"
           " dense ever-listed developer rows with honest zero"
           " aggregates, account-ASC order inside the flat"
           " zero group, window echo kept, double-call"
           " identical; zero-listing market: window read"
           " returns honest [] (no phantom rows), default read"
           " [] as well, and the window gate still enforces"
           " E_AM_BAD_WINDOW on a data-empty face (gate"
           " independent of the data face)")

    # -- AC-AMW6 additivity cross + determinism -------------------
    full_rows = {r["dev_account"]: r for r in env_none["board"]}
    sep_rows = {r["dev_account"]: r for r in sep["board"]}
    oct_rows = {r["dev_account"]: r for r in octb["board"]}
    ok6 = []
    for dev in full_rows:
        for key in KEYS:
            ok6.append(full_rows[dev][key]
                       == sep_rows[dev][key]
                       + oct_rows[dev][key])
    ok6.append([r["dev_account"] for r in octb["board"]]
               == ["usr:ada", "usr:carol", "usr:dan"])
    ok6.append(dumps(sep) == dumps(am.dev_sales_board("2026-09")))
    ok6.append(dumps(octb) == dumps(am.dev_sales_board("2026-10")))
    record("AC-AMW6", all(ok6),
           "additivity cross: for every developer every one of"
           " the five keys (all pure-additive) satisfies"
           " full == SEP + OCT; OCT order law holds with the"
           " flat zero group resolved by account ASC (carol"
           " before dan - not listing recency, zero"
           " insertion-order keys); window reads deterministic"
           " double-call")

    # -- AC-AMW7 pure-read law + hygiene --------------------------
    d_read = market_digests(am)
    tx_read = ledger_tx_count(led)
    for _ in range(2):
        am.dev_sales_board()
        am.dev_sales_board("2026-09")
        am.dev_sales_board("2026-10")
        am.dev_sales_board("2026-08")
        am.dev_sales_board("2099-01")
    ok7 = [market_digests(am) == d_read,
           ledger_tx_count(led) == tx_read]
    method_src = inspect.getsource(
        A.APIMarketFace.dev_sales_board)
    ok7.append(not any(w in method_src for w in
                       ("INSERT", "UPDATE", "DELETE",
                        "CREATE", "ALTER")))
    with open(os.path.abspath(__file__), "rb") as handle:
        src_bytes = handle.read()
    ok7.append(all(b < 128 for b in src_bytes))
    net_hits = []
    for line in src_bytes.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith(
                "from "):
            for bad in ("urllib", "requests", "socket", "http"):
                if bad in stripped:
                    net_hits.append(stripped)
    ok7.append(not net_hits)
    ok7.append({p: sha256_file(p) for p in CONFIG_FILES}
               == cfg_shas_before)
    ok7.append(os.path.abspath(tmp).startswith(
        tempfile.gettempdir()))
    ok7.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    ok7.append(len(RESULTS) + 1 == 7)
    record("AC-AMW7", all(ok7),
           "pure-read law: the full read batch (default + four"
           " windows, twice) left the three-table digests and"
           " ledger_tx constant; dev_sales_board method source"
           " carries zero mutation statements; suite source"
           " pure ASCII (%d bytes), zero network imports on"
           " true import lines, both shipped config.json sha256"
           " unchanged, world db in system tmp outside the"
           " repo; criteria count == 7" % len(src_bytes))

    close_stack(am, dk, metered, led)

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
