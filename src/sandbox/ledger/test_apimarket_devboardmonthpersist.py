"""Acceptance suite for the apimarket developer sales board
month-window read face cross-restart persistence example
window (BigDomain R2023; canon = the R2022-reseeded
explore-queue row claimed by R2023, criteria
AC-AMWP1..AC-AMWP7 registered in the claim note BEFORE this
code existed - honesty law; the AC-AMWP prefix, the suite name
and the ledger-apimarket-devboardmonthpersist runner label
were all git-grep zero-occupancy anchored 2026-10-18).

Face under proof: APIMarketFace.dev_sales_board(window=None) -
the R2022 month-window read face (record-time dual-family
slicing: listing_count by the listed_utc prefix, purchase
aggregates by the purchased_utc prefix; strict YYYY-MM gate
before any read, E_AM_BAD_WINDOW; dense ever-listed developer
rows with honest zero aggregates in out months). Persistence
substrate: the append-only apimarket_listings /
apimarket_purchases rows plus the ledger spend / share legs;
the window boards are read-time derivations with zero cached
state, so the suite pins derived purity across full-stack
instance restarts (R1946 four-piece close/rebuild canon:
am -> dk -> metered -> led orderly close, same db_path same
cfg bytes rebuild):

  - pre-close pinning: default + SEP + OCT window reads,
    envelope key laws, independent record-time prefix manual
    recomputation cross, registration-month separation probe,
    fourteen bad-window gate probes with zero side effects;
  - full-stack restart: all three reads byte-identical,
    window echo key survives;
  - post-restart continuation at a NOV frozen clock: SEP and
    OCT window boards stay byte-frozen (zero cross-window
    leakage), the NOV board recomputes zero-cache, the
    default board grows exactly as the manual recompute;
  - gate family identical codes on instances two and three;
  - append-only frozen row prefixes + per-purchase ledger
    tx provenance cross (spend + share legs both present);
  - third instance: sequential reads byte-identical,
    repeat-read purity, pure-read law, hygiene.

Usage: python test_apimarket_devboardmonthpersist.py
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
import apimarket as A                # noqa: E402 (R1763 face)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

SEP_TS = "2026-09-15T10:00:00Z"
OCT_TS = "2026-10-20T11:00:00Z"
NOV_TS = "2026-11-25T12:00:00Z"

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


def frozen_rows(am, table, count):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT * FROM " + table + " ORDER BY"
        " rowid").fetchall()[:count]
    conn.close()
    return repr(rows)


def purchase_tx_pairs(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT spend_tx, dev_share_tx FROM"
        " apimarket_purchases ORDER BY rowid").fetchall()
    conn.close()
    return rows


def utc_prefix(am, table, where, col):
    conn = sqlite3.connect(am.db_path)
    val = conn.execute(
        "SELECT substr(" + col + ", 1, 7) FROM " + table +
        " WHERE " + where).fetchone()[0]
    conn.close()
    return val


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-dsb-monthpersist-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

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

        # -- world: accounts, dev keys, listings, purchases ----
        led.mint_to_pool("pool:reserve", 4000, "SETTLE-AMWP-A",
                         "settlement")
        led.mint_to_pool("pool:share", 1000, "SETTLE-AMWP-S",
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

    # -- AC-AMWP1 control anchor: pre-close pinning -------------
    d_gate = market_digests(am)
    tx_gate = ledger_tx_count(led)
    env_def = am.dev_sales_board()
    env_sep = am.dev_sales_board("2026-09")
    env_oct = am.dev_sales_board("2026-10")
    ok1 = []
    ok1.append(sorted(env_def.keys()) == ["board", "disclaimer"])
    ok1.append(sorted(env_sep.keys()) == ["board", "disclaimer",
                                          "window"]
               and env_sep["window"] == "2026-09"
               and env_oct["window"] == "2026-10")
    ok1.append([row_tuple(r) for r in env_def["board"]] == [
        ("usr:ada", 2, 3, 23, 17, 6),
        ("usr:carol", 1, 1, 10, 7, 3),
        ("usr:dan", 1, 0, 0, 0, 0)])
    ok1.append([row_tuple(r) for r in env_sep["board"]] == [
        ("usr:ada", 1, 1, 10, 7, 3),
        ("usr:carol", 1, 1, 10, 7, 3),
        ("usr:dan", 0, 0, 0, 0, 0)])
    ok1.append([row_tuple(r) for r in env_oct["board"]] == [
        ("usr:ada", 1, 2, 13, 10, 3),
        ("usr:carol", 0, 0, 0, 0, 0),
        ("usr:dan", 1, 0, 0, 0, 0)])
    ok1.append(all(r["gross_revenue"] == r["dev_revenue"]
                   + r["platform_revenue"]
                   for r in env_def["board"] + env_sep["board"]
                   + env_oct["board"]))
    ok1.append([row_tuple(r) for r in env_def["board"]]
               == [row_tuple(r) for r in manual_board(am)])
    ok1.append([row_tuple(r) for r in env_sep["board"]]
               == [row_tuple(r) for r in manual_board(am,
                                                     "2026-09")])
    ok1.append([row_tuple(r) for r in env_oct["board"]]
               == [row_tuple(r) for r in manual_board(am,
                                                     "2026-10")])
    ok1.append(dumps(am.dev_sales_board()) == dumps(env_def))
    ok1.append(dumps(am.dev_sales_board("2026-09")) == dumps(env_sep))
    ok1.append(dumps(am.dev_sales_board("2026-10")) == dumps(env_oct))
    a1_listed = utc_prefix(am, "apimarket_listings",
                           "listing_key = 'risk-scan'",
                           "listed_utc")
    pe1_purchased = utc_prefix(am, "apimarket_purchases",
                               "buyer_id = 'usr:eve' AND"
                               " listing_id = %d"
                               % a1["listing_id"],
                               "purchased_utc")
    ok1.append(a1_listed == "2026-09"
               and pe1_purchased == "2026-10")
    codes = []
    for form in BAD_FORMS:
        try:
            am.dev_sales_board(form)
            codes.append(None)
        except A.ApiMarketError as exc:
            codes.append(exc.code)
    ok1.append(codes == [A.E_AM_BAD_WINDOW] * len(BAD_FORMS))
    ok1.append(market_digests(am) == d_gate)
    ok1.append(ledger_tx_count(led) == tx_gate)
    record("AC-AMWP1", all(ok1),
           "pre-close pinning: default envelope %s, window"
           " envelope adds the echo key; default / SEP / OCT"
           " boards pinned [(ada,2,3,23,17,6),(carol,1,1,10,7,3),"
           "(dan,1,0,0,0,0)] / [(ada,1,1,10,7,3),(carol,1,1,10,"
           "7,3),(dan,0,0,0,0,0)] / [(ada,1,2,13,10,3),(carol,0,"
           "0,0,0,0),(dan,1,0,0,0,0)]; per-row conservation;"
           " record-time prefix manual cross equal on all three"
           " reads; double-call identical; separation probe a1"
           " listed %s but its eve sale recorded %s; %d bad"
           " window forms all reject E_AM_BAD_WINDOW before any"
           " read with digests and ledger_tx constant"
           % (sorted(env_def.keys()), a1_listed, pe1_purchased,
              len(BAD_FORMS)))
    snap_def = dumps(env_def)
    snap_sep = dumps(env_sep)
    snap_oct = dumps(env_oct)

    # append-only anchors for AC-AMWP5
    list_prefix0 = frozen_rows(am, "apimarket_listings", 4)
    purch_prefix0 = frozen_rows(am, "apimarket_purchases", 4)

    # -- AC-AMWP2 full-stack restart: byte-identical reads -------
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    r_def = am2.dev_sales_board()
    r_sep = am2.dev_sales_board("2026-09")
    r_oct = am2.dev_sales_board("2026-10")
    ok2 = [dumps(r_def) == snap_def,
           dumps(r_sep) == snap_sep,
           dumps(r_oct) == snap_oct,
           dumps(am2.dev_sales_board()) == dumps(r_def),
           dumps(am2.dev_sales_board("2026-09")) == dumps(r_sep),
           dumps(am2.dev_sales_board("2026-10")) == dumps(r_oct),
           r_sep["window"] == "2026-09"]
    record("AC-AMWP2", all(ok2),
           "full-stack close (am -> dk -> metered -> led) then"
           " same db_path same cfg bytes rebuild: default / SEP"
           " / OCT window reads all byte-identical to the"
           " pre-close snapshots (sort_keys dumps; window echo"
           " key survives the restart; zero in-memory drift in"
           " the derived month-window boards)")

    # -- AC-AMWP3 post-restart continuation at a NOV clock -------
    tx_base = ledger_tx_count(led2)
    A._now_utc = fake_now
    try:
        clock["now"] = NOV_TS
        c2 = am2.publish_api("usr:carol", "carol-nova",
                             "Carol Nova API",
                             "carol nova month endpoint", PAYLOAD,
                             5, False)
        conn = sqlite3.connect(am2.db_path)
        row = conn.execute(
            "SELECT listing_id FROM apimarket_listings WHERE"
            " listing_key = 'dan-echo'").fetchone()
        d1_id = int(row[0])
        conn.close()
        am2.purchase_api("usr:bob", d1_id, "pn1")
        am2.purchase_api("usr:eve", c2["listing_id"], "pn2")
    finally:
        A._now_utc = orig_now

    n_def = am2.dev_sales_board()
    n_sep = am2.dev_sales_board("2026-09")
    n_oct = am2.dev_sales_board("2026-10")
    n_nov = am2.dev_sales_board("2026-11")
    ok3 = []
    ok3.append(dumps(n_sep) == snap_sep)
    ok3.append(dumps(n_oct) == snap_oct)
    ok3.append([row_tuple(r) for r in n_nov["board"]] == [
        ("usr:dan", 0, 1, 7, 5, 2),
        ("usr:carol", 1, 1, 5, 4, 1),
        ("usr:ada", 0, 0, 0, 0, 0)])
    ok3.append([row_tuple(r) for r in n_nov["board"]]
               == [row_tuple(r) for r in manual_board(am2,
                                                     "2026-11")])
    ok3.append([row_tuple(r) for r in n_def["board"]] == [
        ("usr:ada", 2, 3, 23, 17, 6),
        ("usr:carol", 2, 2, 15, 11, 4),
        ("usr:dan", 1, 1, 7, 5, 2)])
    ok3.append([row_tuple(r) for r in n_def["board"]]
               == [row_tuple(r) for r in manual_board(am2)])
    ok3.append(dumps(n_def) != snap_def)
    ok3.append(dumps(am2.dev_sales_board("2026-11")) == dumps(n_nov))
    ok3.append(all(r["gross_revenue"] == r["dev_revenue"]
                   + r["platform_revenue"]
                   for r in n_nov["board"] + n_def["board"]))
    record("AC-AMWP3", all(ok3),
           "post-restart continuation at the NOV frozen clock"
           " (carol publishes c2 price 5; bob buys dan's"
           " OCT-listed d1; eve buys c2, both purchases recorded"
           " NOV): SEP and OCT window boards stay byte-frozen to"
           " the pre-close snapshots (cross-window zero"
           " leakage); the NOV board recomputes zero-cache and"
           " equals the manual cross [(dan,0,1,7,5,2),(carol,1,"
           "1,5,4,1),(ada,0,0,0,0,0)]; the default board grows"
           " to [(ada,2,3,23,17,6),(carol,2,2,15,11,4),(dan,1,"
           "1,7,5,2)] == manual recompute and differs from the"
           " pre-close default; conservation holds per row")

    # -- AC-AMWP4 gate family identical codes across restarts ---
    d_probe2 = market_digests(am2)
    tx_probe2 = ledger_tx_count(led2)
    codes2 = []
    for form in BAD_FORMS:
        try:
            am2.dev_sales_board(form)
            codes2.append(None)
        except A.ApiMarketError as exc:
            codes2.append(exc.code)
    ok4a = [codes2 == [A.E_AM_BAD_WINDOW] * len(BAD_FORMS),
            market_digests(am2) == d_probe2,
            ledger_tx_count(led2) == tx_probe2]

    # -- AC-AMWP5 append-only frozen prefixes + tx provenance ----
    list_now = frozen_rows(am2, "apimarket_listings", 4)
    purch_now = frozen_rows(am2, "apimarket_purchases", 4)
    tx_pairs = purchase_tx_pairs(am2)
    ids = ledger_tx_ids(led2)
    spends = [str(p[0]) for p in tx_pairs]
    shares = [str(p[1]) for p in tx_pairs]
    ok5 = [list_now == list_prefix0,
           purch_now == purch_prefix0,
           len(tx_pairs) == 6,
           all(s and s in ids for s in spends),
           all(s and s in ids for s in shares),
           len(set(spends)) == 6,
           len(set(shares)) == 6,
           len(set(spends) & set(shares)) == 0,
           ledger_tx_count(led2) - tx_base == 4]
    record("AC-AMWP4", all(ok4a),
           "gate family identical codes across the restart: the"
           " %d bad window forms all reject E_AM_BAD_WINDOW on"
           " the restarted instance (code-face assertion) with"
           " the market digests and ledger_tx constant across"
           " the probe batch" % len(BAD_FORMS))
    record("AC-AMWP5", all(ok5),
           "append-only frozen prefixes + ledger provenance: the"
           " original four listing rows and four purchase rows"
           " are byte-frozen as rowid prefixes across the"
           " restart and the continuation (new rows pure tail"
           " appends); all six purchases carry non-empty pairwise"
           " distinct spend_tx and dev_share_tx strings, every"
           " one present in the ledger_tx id set (cross-db"
           " provenance, spend and share legs disjoint); the two"
           " NOV purchases grew ledger_tx by exactly 4 (spend +"
           " share per purchase)")

    # -- AC-AMWP6 pure-read law + product sha double-proof ------
    d_read2 = market_digests(am2)
    tx_read2 = ledger_tx_count(led2)
    for _ in range(2):
        am2.dev_sales_board()
        am2.dev_sales_board("2026-09")
        am2.dev_sales_board("2026-10")
        am2.dev_sales_board("2026-11")
        am2.dev_sales_board("2026-08")
    method_src = inspect.getsource(
        A.APIMarketFace.dev_sales_board)
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok6 = [market_digests(am2) == d_read2,
           ledger_tx_count(led2) == tx_read2,
           not any(w in method_src for w in
                   ("INSERT", "UPDATE", "DELETE", "CREATE",
                    "ALTER")),
           shas_after == shas_before]
    record("AC-AMWP6", all(ok6),
           "pure-read law: the restart + continuation read"
           " batches (default + four windows, twice) left the"
           " apimarket three-table digests and ledger_tx"
           " constant; dev_sales_board method source carries"
           " zero mutation statements; the five product files"
           " (apimarket.py, apidev.py, ledger.py, both shipped"
           " config.json) sha256 unchanged - suite-only round")

    # -- AC-AMWP7 third instance + hygiene ----------------------
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    t_def = am3.dev_sales_board()
    t_sep = am3.dev_sales_board("2026-09")
    t_oct = am3.dev_sales_board("2026-10")
    t_nov = am3.dev_sales_board("2026-11")
    d_probe3 = market_digests(am3)
    tx_probe3 = ledger_tx_count(led3)
    codes3 = []
    for form in BAD_FORMS:
        try:
            am3.dev_sales_board(form)
            codes3.append(None)
        except A.ApiMarketError as exc:
            codes3.append(exc.code)
    ok7 = [dumps(t_def) == dumps(n_def),
           dumps(t_sep) == snap_sep,
           dumps(t_oct) == snap_oct,
           dumps(t_nov) == dumps(n_nov),
           dumps(am3.dev_sales_board()) == dumps(t_def),
           dumps(am3.dev_sales_board("2026-11")) == dumps(t_nov),
           codes3 == [A.E_AM_BAD_WINDOW] * len(BAD_FORMS),
           market_digests(am3) == d_probe3,
           ledger_tx_count(led3) == tx_probe3]
    close_stack(am3, dk3, metered3, led3)
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
    ok7.append(os.path.abspath(tmp).startswith(
        tempfile.gettempdir()))
    ok7.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    ok7.append(len(RESULTS) + 1 == 7)
    record("AC-AMWP7", all(ok7),
           "third instance (second full-stack restart, same dbs):"
           " default / SEP / OCT / NOV reads byte-identical to"
           " the instance-two end state (SEP / OCT still equal"
           " the original pre-close snapshots) and repeat reads"
           " identical to themselves; the bad-window gate"
           " family rejects identically on the third instance"
           " with zero side effects; hygiene: suite source pure"
           " ASCII (%d bytes), zero network imports on true"
           " import lines, world db in system tmp outside the"
           " repo, criteria count == 7" % len(src_bytes))

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
