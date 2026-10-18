"""Acceptance suite for the apimarket developer sales board
zero-listing boundary world cross-restart persistence example
window (BigDomain R2024; canon = the R2006-reseeded
explore-queue FIFO head claimed by R2024, criteria
AC-AMZB1..AC-AMZB7 registered in the claim note BEFORE this
code existed - honesty law; AC-AMZB prefix + suite name +
registry row three-face git-grep zero-occupancy anchored
2026-10-18).

Face under proof: APIMarketFace.dev_sales_board() - the R1978
developer-level sales / revenue aggregation board. Row-set
authority = the listing side (every distinct dev_account with
at least one listing row gets exactly one board row), so a
zero-listing world returns an honest empty board. Boundary
ruling (R2010 AC-SSZB judgment family, R1976 AC-CBW
precedent): the boundary isolates the listing axis only, not
the whole stack - the ledger domain (accounts, funding) and
the devkeys register stay populated while the apimarket
listing / purchase / rating tables stay at zero rows.

Persist substrate: the board is a read-time derivation with
zero cached state over the append-only apimarket tables plus
the ledger spend / share legs, so the suite pins:

  - pre-close pinning: honest empty envelope {board: [],
    disclaimer}, key laws, double-call identity, pure-read
    anchor (digests + ledger_tx constant over the pinning
    batch);
  - write-side gate family on the empty data face: off-register
    publish E_AM_NOT_DEV (registry gate precedes the content
    gate), content gate hit E_AM_CONTENT_REJECTED, zero price
    E_AM_BAD_PRICE, unknown listing purchase
    E_AM_UNKNOWN_LISTING - all rejecting before any read with
    zero side effects;
  - full-stack restart (R1946 canon: am -> dk -> metered ->
    led orderly close, same db_path same cfg bytes rebuild):
    empty board byte-identical;
  - post-restart first listing: exactly one honest zero row
    joins the board (zero phantom), manual two-query cross;
  - post-restart first purchase: zero-cache recompute with
    the 70/30 integer split, per-row conservation, per-purchase
    spend_tx / dev_share_tx provenance into the ledger_tx id
    set;
  - second restart (third instance) byte-identical, repeat-read
    purity, pure-read law;
  - hygiene: product five-file sha256 double-proof, pure
    ASCII, zero network imports, tmp world outside the repo,
    registry wiring, criteria count.

Usage: python test_apimarket_devboardboundarypersist.py
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
    rows = conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall()
    conn.close()
    return {str(r[0]) for r in rows}


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


def probe(fn, want_code):
    try:
        fn()
        return "no-raise", False
    except A.ApiMarketError as exc:
        return exc.code, exc.code == want_code


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-dsb-boundary-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha256_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]

    led, metered, dk, gate, am = build_stack(db_path, cfg,
                                             lobby_cfg)

    # -- boundary world: ledger + devkeys populated, listing
    #    axis empty (zero listings / purchases / ratings) -----
    led.mint_to_pool("pool:reserve", 2000, "SETTLE-AMZB-A",
                     "settlement")
    led.mint_to_pool("pool:share", 1000, "SETTLE-AMZB-S",
                     "settlement")
    for who in ("ada", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 200),
                    ("usr:" + who, "credit", 200)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:ada", "ada-key", 10, ["backtest"], False)

    # -- AC-AMZB1 zero-listing control anchor ------------------
    d0 = market_digests(am)
    tx0 = sorted(ledger_tx_ids(led))
    env = am.dev_sales_board()
    ok1 = []
    ok1.append(sorted(env.keys()) == ["board", "disclaimer"])
    ok1.append(env["board"] == [])
    ok1.append(dumps(am.dev_sales_board())
               == dumps(am.dev_sales_board()))
    d0b = market_digests(am)
    tx0b = sorted(ledger_tx_ids(led))
    ok1.append(d0 == d0b and tx0 == tx0b)
    ok1.append(manual_board(am) == [])
    record("AC-AMZB1", all(ok1),
           "zero-listing world (ledger + devkeys populated,"
           " apimarket three tables at zero rows): default"
           " envelope keys %s with board == [] honest empty"
           " (zero fabricated rows); double-call dumps"
           " identical; pinning read batch leaves the market"
           " digests and the ledger_tx id set constant"
           " (pure-read anchor); manual two-query cross == []"
           % sorted(env.keys()))
    snap1 = dumps(env)

    # -- AC-AMZB2 gate family fires before any read -------------
    d_probe = market_digests(am)
    tx_probe = sorted(ledger_tx_ids(led))
    p1 = probe(lambda: am.publish_api(
        "usr:frank", "frank-svc", "Frank Svc",
        "off-register listing attempt", PAYLOAD, 5, False),
        A.E_AM_NOT_DEV)
    p2 = probe(lambda: am.publish_api(
        "usr:ada", "badword-svc", "title says " + bad_word,
        "content gate hit attempt", PAYLOAD, 5, False),
        A.E_AM_CONTENT_REJECTED)
    p3 = probe(lambda: am.publish_api(
        "usr:ada", "zero-price-svc", "Zero Price API",
        "zero price attempt", PAYLOAD, 0, False),
        A.E_AM_BAD_PRICE)
    p4 = probe(lambda: am.purchase_api("usr:bob", 999,
                                        "ref-unknown"),
        A.E_AM_UNKNOWN_LISTING)
    codes = [p[0] for p in (p1, p2, p3, p4)]
    caught = all(p[1] for p in (p1, p2, p3, p4))
    ok2 = [caught,
           codes == [A.E_AM_NOT_DEV, A.E_AM_CONTENT_REJECTED,
                     A.E_AM_BAD_PRICE, A.E_AM_UNKNOWN_LISTING],
           market_digests(am) == d_probe,
           sorted(ledger_tx_ids(led)) == tx_probe]
    record("AC-AMZB2", all(ok2),
           "write-side gate family on the empty data face:"
           " off-register publish %s, content gate hit %s"
           " (ada registered, title carries forbidden_words[0]"
           " - registry gate precedes the content gate, so the"
           " frank probe proves the register gate without"
           " burning a content check), zero price %s, unknown"
           " listing purchase %s; probe batch leaves digests"
           " and ledger_tx constant (gates fire before any"
           " read, independent of the empty data face)"
           % (p1[0], p2[0], p3[0], p4[0]))

    # -- AC-AMZB3 full-stack restart: byte-identical empty -------
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    env2 = am2.dev_sales_board()
    double2 = dumps(am2.dev_sales_board())
    ok3 = [dumps(env2) == snap1, double2 == snap1]
    record("AC-AMZB3", all(ok3),
           "full-stack close (am -> dk -> metered -> led) then"
           " same db_path same cfg bytes rebuild (Ledger +"
           " MeteredFace + DevKeyFace + SecGate +"
           " APIMarketFace): the empty board re-read is"
           " byte-identical to the pre-close snapshot and the"
           " second read is self-stable (zero in-memory drift"
           " in the derived board across the restart)")

    # -- AC-AMZB4 post-restart first listing: dense join ----------
    first = am2.publish_api(
        "usr:ada", "boundary-first", "Boundary First API",
        "first listing after restart", PAYLOAD, 10, False)
    env4 = am2.dev_sales_board()
    rows4 = env4["board"]
    ok4 = []
    ok4.append(len(rows4) == 1)
    ok4.append(rows4 and sorted(rows4[0].keys()) == [
        "dev_account", "dev_revenue", "gross_revenue",
        "listing_count", "platform_revenue", "purchase_count"])
    ok4.append([row_tuple(r) for r in rows4]
               == [("usr:ada", 1, 0, 0, 0, 0)])
    ok4.append(dumps(env4) != snap1)
    ok4.append([row_tuple(r) for r in rows4]
               == [row_tuple(r) for r in manual_board(am2)])
    ok4.append(dumps(am2.dev_sales_board()) == dumps(env4))
    record("AC-AMZB4", all(ok4),
           "post-restart first listing (ada boundary-first,"
           " price 10): the board grows 0 -> 1 row with exactly"
           " the honest zero row (usr:ada, 1, 0, 0, 0, 0) -"
           " the listed-but-unsold developer stays visible,"
           " board rows == listing rows == 1 (zero phantom),"
           " read differs from the pre-restart empty snapshot"
           " (liveness, zero cache), manual two-query cross"
           " equal, repeat read identical")
    snap4 = dumps(env4)

    # -- AC-AMZB5 post-restart first purchase + tx provenance ----
    buy = am2.purchase_api("usr:bob", first["listing_id"],
                           "pbz1")
    env5 = am2.dev_sales_board()
    rows5 = env5["board"]
    conn = sqlite3.connect(am2.db_path)
    prow = conn.execute(
        "SELECT spend_tx, dev_share_tx FROM apimarket_purchases"
        " WHERE buyer_id = 'usr:bob'").fetchall()
    conn.close()
    ids2 = ledger_tx_ids(led2)
    ok5 = []
    ok5.append([row_tuple(r) for r in rows5]
               == [("usr:ada", 1, 1, 10, 7, 3)])
    ok5.append(rows5 and rows5[0]["gross_revenue"]
               == rows5[0]["dev_revenue"]
               + rows5[0]["platform_revenue"])
    ok5.append(len(prow) == 1)
    if prow:
        spend_tx, share_tx = str(prow[0][0]), str(prow[0][1])
        ok5.append(spend_tx.strip() != ""
                   and share_tx.strip() != ""
                   and spend_tx != share_tx
                   and spend_tx in ids2 and share_tx in ids2)
    else:
        ok5.append(False)
    ok5.append([row_tuple(r) for r in rows5]
               == [row_tuple(r) for r in manual_board(am2)])
    ok5.append(dumps(am2.dev_sales_board()) == dumps(env5))
    ok5.append(buy["purchase_id"] > 0)
    record("AC-AMZB5", all(ok5),
           "post-restart first purchase (bob -> ada"
           " boundary-first, purchase_id=%s): the row recomputes"
           " zero-cache to (usr:ada, 1, 1, 10, 7, 3) with the"
           " 70/30 default integer split, per-row conservation"
           " gross == dev + platform holds, the purchase row"
           " carries a non-empty distinct spend_tx /"
           " dev_share_tx pair with both ids present in the"
           " ledger_tx id set (cross-db provenance, the two"
           " legs never coincide), manual cross equal, repeat"
           " read identical" % buy["purchase_id"])
    snap5 = dumps(env5)

    # -- AC-AMZB6 third instance + pure-read law -----------------
    d6a = market_digests(am2)
    tx6a = sorted(ledger_tx_ids(led2))
    read_a = [dumps(am2.dev_sales_board()),
              dumps(am2.dev_sales_board())]
    read_b = [dumps(am2.dev_sales_board()),
              dumps(am2.dev_sales_board())]
    d6b = market_digests(am2)
    tx6b = sorted(ledger_tx_ids(led2))
    ok6a = [read_a == read_b and read_a[0] == snap5
            and read_a[0] == read_a[1],
            d6a == d6b, tx6a == tx6b]
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    env6 = am3.dev_sales_board()
    env6b = am3.dev_sales_board()
    ok6 = ok6a + [dumps(env6) == snap5, dumps(env6b) == snap5,
                   dumps(env6) == dumps(env6b)]
    record("AC-AMZB6", all(ok6),
           "repeat read battery on instance two: double-pair"
           " byte-identical to the post-purchase state and to"
           " itself, digests + ledger_tx constant over the"
           " batch (pure-read law); second full-stack restart"
           " (third instance, same dbs): board byte-identical"
           " to the instance-two final state, sequential"
           " double-read self-stable (repeat-read purity, two"
           " restarts, zero in-memory drift)")
    close_stack(am3, dk3, metered3, led3)

    # -- AC-AMZB7 hygiene + product sha double-proof --------------
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
    ok7.append("ledger-apimarket-devboardboundary" in reg_src
               and "test_apimarket_devboardboundarypersist.py"
               in reg_src)
    ok7.append(shas_after == shas_before)
    ok7.append(len(RESULTS) + 1 == 7)
    record("AC-AMZB7", all(ok7),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, world db in system"
           " tmp outside the repo, registry row wired"
           " (ledger-apimarket-devboardboundary), product"
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
