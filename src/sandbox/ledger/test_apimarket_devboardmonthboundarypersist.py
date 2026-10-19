"""Acceptance suite for the apimarket developer sales board
month-window zero-listing boundary cross-restart persistence
example window (BigDomain R2045; canon = the R2023-reseeded
explore-queue FIFO head claimed by R2045, criteria
AC-AMWZB1..AC-AMWZB7 registered in the claim note BEFORE this
code existed - honesty law; the AC-AMWZB prefix, the suite
name and the ledger-apimarket-devboardmonthboundary runner
label were all git-grep zero-occupancy anchored 2026-10-19).

Face under proof: APIMarketFace.dev_sales_board(window=None) -
the R2022 month-window read face (record-time dual-family
slicing: listing_count by the listed_utc prefix, purchase
aggregates by the purchased_utc prefix; strict YYYY-MM gate
E_AM_BAD_WINDOW before any read) pinned in its zero-listing
boundary world (R2024 AC-AMZB judgment family, R1976 AC-CBW
precedent): the boundary isolates the listing axis only, not
the whole stack - the ledger domain (accounts, funding) and
the devkeys register stay populated while the apimarket
listing / purchase / rating tables stay at zero rows. The
suite pins:

  - pre-close pinning: all five read forms (default + SEP /
    OCT / NOV real months + 2099-01 out month) return honest
    empty envelopes with the window echo key, double-call
    identity, pure-read anchor, manual two-query cross == [];
  - the fourteen bad-window gate family (R2023 BAD_FORMS
    order) rejecting identically before any read on the
    empty data face with zero side effects;
  - full-stack restart (R1946 canon: am -> dk -> metered ->
    led orderly close, same db_path same cfg bytes rebuild):
    all five forms byte-identical, window echo survives;
  - post-restart first listing at a frozen OCT clock: dense
    window-face join (the listing record month carries the
    listing_count, every other month keeps the honest dense
    zero row - ever-listed axis holds across windows), zero
    phantoms, liveness against the empty snapshot;
  - post-restart first purchase at a frozen NOV clock: the
    NOV window recomputes zero-cache with the 70/30 split,
    the OCT window keeps the listing family (record-time
    dual-family law), per-row conservation, per-purchase
    spend_tx / dev_share_tx provenance into the ledger_tx id
    set;
  - second restart (third instance) byte-identical, pure-read
    law, gate family identical codes on instances two and
    three;
  - hygiene: product five-file sha256 double-proof, pure
    ASCII, zero network imports, tmp world outside the repo,
    registry wiring, criteria count.

Usage: python test_apimarket_devboardmonthboundarypersist.py
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

OCT_TS = "2026-10-20T11:00:00Z"
NOV_TS = "2026-11-25T12:00:00Z"

WINDOWS = ["2026-09", "2026-10", "2026-11", "2099-01"]

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


def read_family(am):
    """The five read forms: default + SEP / OCT / NOV real
    month windows + the 2099-01 out month, as a dumps list."""
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
    tmp = tempfile.mkdtemp(prefix="apimarket-dsb-mboundary-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    # -- zero-listing boundary world: ledger + devkeys domain
    #    populated, listing axis empty (R2024 posture) --------
    led, metered, dk, gate, am = build_stack(db_path, cfg,
                                             lobby_cfg)
    led.mint_to_pool("pool:reserve", 2000, "SETTLE-AMWZB-A",
                     "settlement")
    led.mint_to_pool("pool:share", 1000, "SETTLE-AMWZB-S",
                     "settlement")
    for who in ("ada", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 200),
                    ("usr:" + who, "credit", 200)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:ada", "ada-key", 10, ["backtest"], False)

    # -- AC-AMWZB1 zero-listing control anchor ------------------
    d0 = market_digests(am)
    tx0 = sorted(ledger_tx_ids(led))
    env_def = am.dev_sales_board()
    ok1 = []
    ok1.append(sorted(env_def.keys()) == ["board", "disclaimer"])
    ok1.append(env_def["board"] == [])
    window_envs = {}
    for window in WINDOWS:
        env = am.dev_sales_board(window)
        window_envs[window] = env
        ok1.append(sorted(env.keys())
                   == ["board", "disclaimer", "window"])
        ok1.append(env["window"] == window)
        ok1.append(env["board"] == [])
    ok1.append(read_family(am) == read_family(am))
    d0b = market_digests(am)
    tx0b = sorted(ledger_tx_ids(led))
    ok1.append(d0 == d0b and tx0 == tx0b)
    ok1.append(manual_board(am) == [])
    ok1.append(all(manual_board(am, w) == []
                   for w in WINDOWS))
    record("AC-AMWZB1", all(ok1),
           "zero-listing boundary world (ledger + devkeys"
           " populated, apimarket three tables at zero rows):"
           " default envelope keys %s with board == [] honest"
           " empty; all four window reads (SEP / OCT / NOV /"
           " 2099-01) carry the echo key with board == []"
           " honest empty (zero fabricated rows, out month"
           " included); five-form family double-call dumps"
           " identical; the pinning batch leaves the market"
           " digests and the ledger_tx id set constant"
           " (pure-read anchor); manual two-query cross == []"
           " on all five forms" % sorted(env_def.keys()))
    snaps = [dumps(env_def)] + [dumps(window_envs[w])
                                for w in WINDOWS]

    # -- AC-AMWZB2 bad-window gate family before any read --------
    d_probe = market_digests(am)
    tx_probe = ledger_tx_count(led)
    codes1 = gate_battery(am)
    ok2 = [codes1 == [A.E_AM_BAD_WINDOW] * len(BAD_FORMS),
           market_digests(am) == d_probe,
           ledger_tx_count(led) == tx_probe]
    record("AC-AMWZB2", all(ok2),
           "the %d bad-window forms (R2023 BAD_FORMS order)"
           " all reject E_AM_BAD_WINDOW on the empty data face"
           " (code-face assertion) before any read, with the"
           " market digests and ledger_tx constant across the"
           " probe batch - the window gate is independent of"
           " the empty data face" % len(BAD_FORMS))

    # -- AC-AMWZB3 full-stack restart: byte-identical family -----
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                 lobby_cfg)
    family2 = read_family(am2)
    ok3 = [family2 == snaps,
           read_family(am2) == family2,
           am2.dev_sales_board("2026-09")["window"] == "2026-09"]
    record("AC-AMWZB3", all(ok3),
           "full-stack close (am -> dk -> metered -> led) then"
           " same db_path same cfg bytes rebuild (Ledger +"
           " MeteredFace + DevKeyFace + SecGate +"
           " APIMarketFace): all five read forms byte-identical"
           " to the pre-close snapshots (zero-listing state"
           " crosses the restart with zero in-memory drift; the"
           " window echo key survives) and the sequential"
           " second read is self-stable")

    # -- AC-AMWZB4 post-restart first listing: dense window join --
    clock = {"now": OCT_TS}
    orig_now = A._now_utc

    def fake_now():
        return clock["now"]

    A._now_utc = fake_now
    try:
        first = am2.publish_api(
            "usr:ada", "boundary-first", "Boundary First API",
            "first listing after restart", PAYLOAD, 10, False)
    finally:
        A._now_utc = orig_now
    env_def4 = am2.dev_sales_board()
    rows_def4 = env_def4["board"]
    env_oct4 = am2.dev_sales_board("2026-10")
    ok4 = []
    ok4.append([row_tuple(r) for r in rows_def4]
               == [("usr:ada", 1, 0, 0, 0, 0)])
    ok4.append([row_tuple(r) for r in env_oct4["board"]]
               == [("usr:ada", 1, 0, 0, 0, 0)])
    for window, expected in (("2026-09", ("usr:ada", 0, 0, 0, 0, 0)),
                             ("2026-11", ("usr:ada", 0, 0, 0, 0, 0)),
                             ("2099-01", ("usr:ada", 0, 0, 0, 0, 0))):
        env = am2.dev_sales_board(window)
        ok4.append([row_tuple(r) for r in env["board"]]
                   == [expected])
    ok4.append(len(rows_def4) == 1)
    ok4.append(dumps(env_def4) != snaps[0])
    ok4.append([row_tuple(r) for r in rows_def4]
               == [row_tuple(r) for r in manual_board(am2)])
    ok4.append([row_tuple(r) for r in env_oct4["board"]]
               == [row_tuple(r) for r in manual_board(am2,
                                                     "2026-10")])
    ok4.append(all([row_tuple(r) for r in
                    am2.dev_sales_board(w)["board"]]
                   == [row_tuple(r) for r in manual_board(am2, w)]
                   for w in ("2026-09", "2026-11", "2099-01")))
    ok4.append(read_family(am2) == read_family(am2))
    record("AC-AMWZB4", all(ok4),
           "post-restart first listing (ada boundary-first,"
           " price 10, frozen OCT clock): the default board"
           " grows 0 -> 1 honest zero row (usr:ada, 1, 0, 0, 0,"
           " 0) and the OCT record-month window carries the"
           " same row (listing family by listed_utc); the SEP /"
           " NOV / out-month window reads each keep the honest"
           " dense zero row (usr:ada, 0, 0, 0, 0, 0) - the"
           " ever-listed axis holds across windows, board rows"
           " == listing rows == 1 (zero phantom); the read"
           " differs from the pre-restart empty snapshot"
           " (liveness, zero cache); the record-time manual"
           " cross equals on every form; repeat family reads"
           " identical")
    family4 = read_family(am2)
    snap_oct4 = dumps(am2.dev_sales_board("2026-10"))
    snap_sep4 = dumps(am2.dev_sales_board("2026-09"))

    # -- AC-AMWZB5 post-restart first purchase + tx provenance ----
    A._now_utc = fake_now
    try:
        clock["now"] = NOV_TS
        buy = am2.purchase_api("usr:bob", first["listing_id"],
                               "pmbz1")
    finally:
        A._now_utc = orig_now
    env_nov5 = am2.dev_sales_board("2026-11")
    env_oct5 = am2.dev_sales_board("2026-10")
    conn = sqlite3.connect(am2.db_path)
    prow = conn.execute(
        "SELECT spend_tx, dev_share_tx FROM apimarket_purchases"
        " WHERE buyer_id = 'usr:bob'").fetchall()
    conn.close()
    ids2 = ledger_tx_ids(led2)
    ok5 = []
    ok5.append([row_tuple(r) for r in env_nov5["board"]]
               == [("usr:ada", 0, 1, 10, 7, 3)])
    ok5.append([row_tuple(r) for r in env_oct5["board"]]
               == [("usr:ada", 1, 0, 0, 0, 0)])
    ok5.append(dumps(env_oct5) == snap_oct4)
    ok5.append(dumps(am2.dev_sales_board("2026-09")) == snap_sep4)
    ok5.append(all(r["gross_revenue"] == r["dev_revenue"]
                   + r["platform_revenue"]
                   for r in env_nov5["board"]
                   + am2.dev_sales_board()["board"]))
    ok5.append(len(prow) == 1)
    if prow:
        spend_tx, share_tx = str(prow[0][0]), str(prow[0][1])
        ok5.append(spend_tx.strip() != ""
                   and share_tx.strip() != ""
                   and spend_tx != share_tx
                   and spend_tx in ids2 and share_tx in ids2)
    else:
        ok5.append(False)
    ok5.append([row_tuple(r) for r in env_nov5["board"]]
               == [row_tuple(r) for r in manual_board(am2,
                                                     "2026-11")])
    ok5.append(read_family(am2) == read_family(am2))
    ok5.append(buy["purchase_id"] > 0)
    record("AC-AMWZB5", all(ok5),
           "post-restart first purchase (bob -> ada"
           " boundary-first, purchase_id=%s, frozen NOV clock):"
           " the NOV window recomputes zero-cache to (usr:ada,"
           " 0, 1, 10, 7, 3) - the 70/30 default integer split"
           " with the purchase family by purchased_utc while the"
           " OCT window keeps the listing family row (usr:ada,"
           " 1, 0, 0, 0, 0) byte-frozen and the SEP window stays"
           " byte-frozen to the pre-purchase state (record-time"
           " dual-family law, zero cross-window leakage);"
           " per-row conservation gross == dev + platform holds"
           " on every read form; the purchase row carries a"
           " non-empty distinct spend_tx / dev_share_tx pair"
           " with both ids present in the ledger_tx id set"
           " (cross-db provenance); manual cross equal; repeat"
           " family reads identical" % buy["purchase_id"])
    family5 = read_family(am2)

    # -- AC-AMWZB6 pure-read law + third instance + gate ---------
    d_read = market_digests(am2)
    tx_read = ledger_tx_count(led2)
    for _ in range(2):
        am2.dev_sales_board()
        for window in WINDOWS:
            am2.dev_sales_board(window)
    ok6a = [market_digests(am2) == d_read,
            ledger_tx_count(led2) == tx_read,
            read_family(am2) == family5]
    d_probe2 = market_digests(am2)
    tx_probe2 = ledger_tx_count(led2)
    codes2 = gate_battery(am2)
    ok6b = [codes2 == [A.E_AM_BAD_WINDOW] * len(BAD_FORMS),
            market_digests(am2) == d_probe2,
            ledger_tx_count(led2) == tx_probe2]
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                 lobby_cfg)
    family3 = read_family(am3)
    d_probe3 = market_digests(am3)
    tx_probe3 = ledger_tx_count(led3)
    codes3 = gate_battery(am3)
    ok6 = ok6a + ok6b + [family3 == family5,
                         read_family(am3) == family3,
                         codes3 == codes2,
                         codes3 == [A.E_AM_BAD_WINDOW]
                         * len(BAD_FORMS),
                         market_digests(am3) == d_probe3,
                         ledger_tx_count(led3) == tx_probe3]
    close_stack(am3, dk3, metered3, led3)
    record("AC-AMWZB6", all(ok6),
           "pure-read law: the read battery (default + four"
           " windows, twice) left the digests and ledger_tx"
           " constant with the family byte-identical to the"
           " post-purchase state; the bad-window gate family"
           " rejects identically on instances two and three"
           " (code vector byte-identical across both restarts,"
           " probe batches zero side effects); second full-stack"
           " restart (third instance, same dbs): all five read"
           " forms byte-identical to the instance-two end state"
           " (liveness-written world survives the second"
           " restart, repeat-read purity)")

    # -- AC-AMWZB7 hygiene + product sha double-proof -------------
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        src_bytes = handle.read()
    ok7 = [all(b < 128 for b in src_bytes)]
    net_hits = []
    for line in src_bytes.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith(
                "from "):
            for bad in ("urllib", "requests", "socket", "http"):
                if bad in stripped:
                    net_hits.append(stripped)
    ok7.append(not net_hits)
    ok7.append(os.path.abspath(tmp).startswith(
        tempfile.gettempdir()))
    ok7.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    reg_path = os.path.normpath(
        os.path.join(BASE, "..", "reconcile_all.py"))
    with open(reg_path, encoding="utf-8") as handle:
        reg_src = handle.read()
    ok7.append("ledger-apimarket-devboardmonthboundary" in reg_src
               and "test_apimarket_devboardmonthboundarypersist.py"
               in reg_src)
    ok7.append(shas_after == shas_before)
    ok7.append(len(RESULTS) + 1 == 7)
    record("AC-AMWZB7", all(ok7),
           "hygiene: suite source pure ASCII (%d bytes), zero"
           " network imports on true import lines, world db in"
           " system tmp outside the repo, registry row wired"
           " (ledger-apimarket-devboardmonthboundary), product"
           " five-file sha256 unchanged (apimarket.py,"
           " apidev.py, ledger.py, both shipped config.json -"
           " suite-only round), criteria count == 7"
           % len(src_bytes))

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
