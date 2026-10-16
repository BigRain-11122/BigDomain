"""Acceptance suite for the apimarket developer sales board
cross-restart persistence example window (BigDomain R2006;
canon = the R1978-reseeded explore-queue row claimed by R2006,
criteria AC-AMBP1..AC-AMBP7 registered in the claim note BEFORE
this code existed - honesty law; AC-AMBP prefix git-grep
zero-occupancy anchored 2026-10-17).

Face under proof: APIMarketFace.dev_sales_board() - the R1978
developer-level sales / revenue aggregation board (row-set
authority = the listing side, dormant zero-sale developers stay
visible, deterministic order dev_revenue DESC ->
purchase_count DESC -> dev_account ASC, per-row integer-split
conservation). Persistence substrate: the append-only
apimarket_listings / apimarket_purchases rows plus the ledger
spend / share legs; the board is a read-time derivation with
zero cached state, so the suite pins derived purity across
full-stack instance restarts (R1946 four-piece close/rebuild
canon: am -> dk -> metered -> led orderly close, same db_path
same cfg bytes rebuild):

  - pre-close pinning: exact board rows, envelope key laws,
    independent two-query manual recomputation cross, per-row
    conservation, double-call identity;
  - full-stack restart: board byte-identical over the same
    apimarket.db;
  - post-restart purchase: zero-cache recompute on the touched
    developer row, untouched rows byte-frozen;
  - post-restart new developer listing: honest zero row joins
    the board, gate family identical codes across the restart
    with zero side effects;
  - third instance: sequential reads byte-identical,
    repeat-read purity;
  - pure-read law + end-state manual cross + product-file
    sha256 double-proof (suite-only round), hygiene.

Usage: python test_apimarket_devsalespersist.py
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


def manual_board(am):
    """Independent second derivation: two separate queries (no
    JOIN shared with the product SQL), Python-side aggregation,
    then the registered order law. Zero shared code with the
    product face."""
    conn = sqlite3.connect(am.db_path)
    listings = conn.execute(
        "SELECT listing_id, dev_account FROM"
        " apimarket_listings").fetchall()
    purchases = conn.execute(
        "SELECT listing_id, price_paid, dev_share,"
        " platform_share FROM apimarket_purchases").fetchall()
    conn.close()
    dev_of = {int(lid): dev for lid, dev in listings}
    per_dev = {}
    for lid, dev in listings:
        per_dev.setdefault(dev, {"listing_count": 0,
                                  "purchase_count": 0,
                                  "gross_revenue": 0,
                                  "dev_revenue": 0,
                                  "platform_revenue": 0})
        per_dev[dev]["listing_count"] += 1
    for lid, price, dev_share, plat_share in purchases:
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


def row_tuple(row):
    return (row["dev_account"], row["listing_count"],
            row["purchase_count"], row["gross_revenue"],
            row["dev_revenue"], row["platform_revenue"])


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-dsb-persist-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg,
                                             lobby_cfg)

    # -- world: accounts, dev keys, listings, purchases ---------
    led.mint_to_pool("pool:reserve", 4000, "SETTLE-AMBP-A",
                     "settlement")
    led.mint_to_pool("pool:share", 1000, "SETTLE-AMBP-S",
                     "settlement")
    accounts = ("ada", "carol", "dan", "bob", "eve", "frank",
                "gina")
    for who in accounts:
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 200),
                    ("usr:" + who, "credit", 200)],
                   "manual:fund-" + who, "suite funding " + who)
    for who, scopes in (("ada", ["backtest"]),
                        ("carol", ["backtest"]),
                        ("dan", ["visualize"])):
        dk.issue_key("usr:" + who, who + "-key", 10, scopes, False)

    a1 = am.publish_api("usr:ada", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD,
                        10, False)
    a2 = am.publish_api("usr:ada", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)
    c1 = am.publish_api("usr:carol", "carol-alpha",
                        "Carol Alpha API", "carol first endpoint",
                        PAYLOAD, 10, False)
    am.publish_api("usr:dan", "dan-echo", "Dan Echo API",
                   "dan dormant endpoint", PAYLOAD, 7, False)
    am.purchase_api("usr:bob", a1["listing_id"], "pb1")
    am.purchase_api("usr:bob", a2["listing_id"], "pb2")
    am.purchase_api("usr:eve", a1["listing_id"], "pe1")
    am.purchase_api("usr:eve", c1["listing_id"], "pe2")

    # -- AC-AMBP1 control anchor: pre-close pinning --------------
    d0 = market_digests(am)
    tx0 = ledger_tx_count(led)
    env = am.dev_sales_board()
    ok1 = []
    ok1.append(sorted(env.keys()) == ["board", "disclaimer"])
    ok1.append(all(sorted(r.keys()) == [
        "dev_account", "dev_revenue", "gross_revenue",
        "listing_count", "platform_revenue", "purchase_count"]
        for r in env["board"]))
    ok1.append([row_tuple(r) for r in env["board"]] == [
        ("usr:ada", 2, 3, 23, 17, 6),
        ("usr:carol", 1, 1, 10, 7, 3),
        ("usr:dan", 1, 0, 0, 0, 0)])
    ok1.append(all(r["gross_revenue"] == r["dev_revenue"]
                   + r["platform_revenue"] for r in env["board"]))
    ok1.append([row_tuple(r) for r in env["board"]]
               == [row_tuple(r) for r in manual_board(am)])
    ok1.append(dumps(am.dev_sales_board())
               == dumps(am.dev_sales_board()))
    record("AC-AMBP1", all(ok1),
           "pre-close pinning: envelope keys %s; six-key rows;"
           " board [(ada,2,3,23,17,6),(carol,1,1,10,7,3),"
           "(dan,1,0,0,0,0) honest zero-sale row]; per-row"
           " gross == dev + platform; independent two-query"
           " manual recomputation cross equal; double-call"
           " dumps identical" % sorted(env.keys()))
    snap1 = dumps(env)

    # pure-read law part 1: the pinning read batch left the
    # digests and the ledger_tx count untouched
    d0b = market_digests(am)
    tx0b = ledger_tx_count(led)

    # -- AC-AMBP2 full-stack restart: byte-identical board -------
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    env2 = am2.dev_sales_board()
    ok2 = [dumps(env2) == snap1]
    record("AC-AMBP2", all(ok2),
           "full-stack close (am -> dk -> metered -> led) then"
           " same db_path same cfg rebuild (Ledger + MeteredFace"
           " + DevKeyFace + SecGate + APIMarketFace): the board"
           " re-read is byte-identical to the pre-close snapshot"
           " (sort_keys dumps; zero in-memory drift in the"
           " derived developer sales board)")

    # -- AC-AMBP3 post-restart purchase: zero-cache recompute -----
    am2.purchase_api("usr:frank", c1["listing_id"], "pf1")
    env3 = am2.dev_sales_board()
    ok3 = []
    ok3.append([row_tuple(r) for r in env3["board"]] == [
        ("usr:ada", 2, 3, 23, 17, 6),
        ("usr:carol", 1, 2, 20, 14, 6),
        ("usr:dan", 1, 0, 0, 0, 0)])
    ok3.append(all(r["gross_revenue"] == r["dev_revenue"]
                   + r["platform_revenue"] for r in env3["board"]))
    ok3.append([row_tuple(r) for r in env3["board"]]
               == [row_tuple(r) for r in manual_board(am2)])
    ok3.append(dumps(am2.dev_sales_board()) == dumps(env3))
    conn = sqlite3.connect(am2.db_path)
    carol_spend_tx = conn.execute(
        "SELECT spend_tx FROM apimarket_purchases WHERE"
        " buyer_id = 'usr:frank'").fetchall()
    conn.close()
    ok3.append(len(carol_spend_tx) == 1
               and str(carol_spend_tx[0][0]).strip() != "")
    record("AC-AMBP3", all(ok3),
           "post-restart purchase (frank -> carol c1, one spend"
           " bound to its tx): the carol row recomputes"
           " zero-cache (purchases 1 -> 2, gross 10 -> 20,"
           " dev 7 -> 14, platform 3 -> 6) while the ada / dan"
           " rows stay byte-frozen; conservation and the manual"
           " cross hold; repeat read identical")
    snap3 = dumps(env3)

    # -- AC-AMBP4 post-restart new listing + gate family ---------
    dk2.issue_key("usr:gina", "gina-key", 10, ["visualize"],
                  False)
    am2.publish_api("usr:gina", "gina-gamma", "Gina Gamma API",
                    "gina single endpoint", PAYLOAD, 14, False)
    env4 = am2.dev_sales_board()
    ok4 = []
    ok4.append([row_tuple(r) for r in env4["board"]] == [
        ("usr:ada", 2, 3, 23, 17, 6),
        ("usr:carol", 1, 2, 20, 14, 6),
        ("usr:dan", 1, 0, 0, 0, 0),
        ("usr:gina", 1, 0, 0, 0, 0)])
    ok4.append([row_tuple(r) for r in env4["board"]]
               == [row_tuple(r) for r in manual_board(am2)])
    # gate family: identical codes, zero side effects (the probe
    # baseline is captured AFTER the legitimate gina listing
    # write, so the zero-side-effect assertion covers exactly
    # the four rejection probes)
    d_probe = market_digests(am2)
    tx_probe = ledger_tx_count(led2)
    codes = []
    try:
        am2.publish_api("usr:frank", "frank-svc", "Frank Svc",
                        "off-register listing", PAYLOAD, 5, False)
        codes.append(None)
    except A.ApiMarketError as exc:
        codes.append(exc.code)
    try:
        am2.purchase_api("usr:bob", a1["listing_id"],
                         "ref-dup-bob")
        codes.append(None)
    except A.ApiMarketError as exc:
        codes.append(exc.code)
    try:
        am2.purchase_api("usr:ada", a1["listing_id"],
                         "ref-self-ada")
        codes.append(None)
    except A.ApiMarketError as exc:
        codes.append(exc.code)
    try:
        am2.purchase_api("usr:bob", 999, "ref-unknown")
        codes.append(None)
    except A.ApiMarketError as exc:
        codes.append(exc.code)
    ok4.append(codes == [A.E_AM_NOT_DEV, A.E_AM_PURCHASE_DUP,
                         A.E_AM_SELF_BUY, A.E_AM_UNKNOWN_LISTING])
    ok4.append(market_digests(am2) == d_probe)
    ok4.append(ledger_tx_count(led2) == tx_probe)
    record("AC-AMBP4", all(ok4),
           "post-restart new developer listing (gina key +"
           " gina-gamma publish): the board grows 3 -> 4 rows"
           " with the gina honest zero row at the tail"
           " (dan < gina account ASC inside the zero-revenue"
           " group), untouched rows byte-frozen; gate family"
           " identical across the restart: off-register publish"
           " E_AM_NOT_DEV, purchase replay E_AM_PURCHASE_DUP,"
           " self-buy E_AM_SELF_BUY, unknown listing"
           " E_AM_UNKNOWN_LISTING - all rejected with the"
           " market digests and ledger_tx constant")
    snap4 = dumps(env4)

    # -- AC-AMBP5 third instance: sequential reads identical ------
    d1 = market_digests(am2)
    tx1 = ledger_tx_count(led2)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    env5 = am3.dev_sales_board()
    env5b = am3.dev_sales_board()
    ok5 = [dumps(env5) == snap4, dumps(env5b) == snap4,
           dumps(env5) == dumps(env5b)]
    record("AC-AMBP5", all(ok5),
           "second full-stack restart (third instance, same"
           " dbs): the board read is byte-identical to the"
           " post-listing state and the repeated read batch"
           " identical to itself (repeat-read purity, zero"
           " in-memory drift across two restarts)")

    # -- AC-AMBP6 pure-read law + manual cross + product sha -------
    d1b = market_digests(am3)
    tx1b = ledger_tx_count(led3)
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    ok6 = [d0 == d0b, d1 == d1b, tx0 == tx0b, tx1 == tx1b,
           shas_after == shas_before]
    ok6.append([row_tuple(r) for r in am3.dev_sales_board()["board"]]
               == [row_tuple(r) for r in manual_board(am3)])
    record("AC-AMBP6", all(ok6),
           "pure-read law: the pinning / restart / third-instance"
           " read batches left the apimarket three-table digests"
           " and the ledger_tx count constant (digest equal,"
           " tx equal); end-state board == fresh two-query"
           " manual cross; apimarket.py + both shipped"
           " config.json sha256 unchanged (suite-only round)")

    # -- AC-AMBP7 hygiene: ASCII, zero-network, tmp world ---------
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
    ok7.append(len(RESULTS) + 1 == 7)
    record("AC-AMBP7", all(ok7),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, world db in system"
           " tmp outside the repo, criteria count == 7"
           % len(src_bytes))

    close_stack(am3, dk3, metered3, led3)

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
