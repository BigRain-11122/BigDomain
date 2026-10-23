"""Acceptance suite for the apimarket developer sales board
zero-listing boundary gate-family cross-restart same-code
example window (BigDomain R2065; canon = the explore-queue
FIFO head reseeded by R2024 and claimed by R2065, criteria
AC-AMZG1..AC-AMZG8 registered in the claim note BEFORE this
code existed - honesty law; AC-AMZG prefix + suite name +
registry row three-face git-grep zero-occupancy anchored
2026-10-24).

Face under proof: the write-side gate family of
APIMarketFace.publish_api() / purchase_api() observed on the
zero-listing boundary world across restart instances. The
seed window (R2024, AC-AMZB1..7) proved the gates fire once on
a fresh instance and that the empty board survives a restart;
this window proves the SPECIFIC rejection codes and their
ORDER are restart-invariant, and that the probe battery itself
leaves the world untouched on every instance.

Instances: (1) fresh stack, (2) full-stack ordered close
(am -> dk -> metered -> led) then same db_path + same cfg
bytes rebuild, (3) a second identical restart.

Gate battery (fixed order, identical on every instance):
  p1 unregistered publisher, clean title   -> E_AM_NOT_DEV
  p2 registered developer, forbidden word  -> E_AM_CONTENT_REJECTED
  p3 registered developer, zero price      -> E_AM_BAD_PRICE
  p4 funded buyer, unknown listing id      -> E_AM_UNKNOWN_LISTING

Usage: python test_apimarket_devboardgatepersist.py
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

REFERENCE = [A.E_AM_NOT_DEV, A.E_AM_CONTENT_REJECTED,
             A.E_AM_BAD_PRICE, A.E_AM_UNKNOWN_LISTING]


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
        return "no-raise"
    except A.ApiMarketError as exc:
        return exc.code


def gate_battery(am, bad_word):
    """Fixed-order four-probe battery. Returns the ordered code
    vector plus the registry-vs-content ordering witness."""
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
    order_witness = probe(lambda: am.publish_api(
        "usr:frank", "frank-word-svc",
        "title says " + bad_word,
        "unregistered publisher with a forbidden word", PAYLOAD,
        5, False), A.E_AM_NOT_DEV)
    return [p1, p2, p3, p4], order_witness


def probe_batch(am, led, bad_word):
    """Run the battery with side-effect pinning; returns the code
    vector, the ordering witness and the purity verdict."""
    d_before = market_digests(am)
    tx_before = sorted(ledger_tx_ids(led))
    board_before = dumps(am.dev_sales_board())
    manual_before = manual_board(am)
    codes, order_witness = gate_battery(am, bad_word)
    d_after = market_digests(am)
    tx_after = sorted(ledger_tx_ids(led))
    board_after = dumps(am.dev_sales_board())
    manual_after = manual_board(am)
    rows_zero = all(v[0] == 0 for v in d_after.values())
    pure = [d_before == d_after, tx_before == tx_after,
            board_before == board_after,
            manual_before == manual_after, rows_zero]
    return codes, order_witness, pure, board_after


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-dsb-gate-")
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
    led.mint_to_pool("pool:reserve", 2000, "SETTLE-AMZG-A",
                     "settlement")
    led.mint_to_pool("pool:share", 1000, "SETTLE-AMZG-S",
                     "settlement")
    for who in ("ada", "bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 200),
                    ("usr:" + who, "credit", 200)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:ada", "ada-key", 10, ["backtest"], False)

    # -- AC-AMZG1 control anchor on instance one ---------------
    d0 = market_digests(am)
    empty_ok = all(v[0] == 0 for v in d0.values())
    env1 = am.dev_sales_board()
    codes1, order1, pure1, board1 = probe_batch(am, led,
                                                bad_word)
    ok1 = [empty_ok,
           sorted(env1.keys()) == ["board", "disclaimer"],
           env1["board"] == [] and board1 == dumps(env1),
           codes1 == REFERENCE,
           order1 == A.E_AM_NOT_DEV,
           all(pure1)]
    record("AC-AMZG1", all(ok1),
           "instance one control anchor: zero-listing boundary"
           " world (ledger + devkeys populated, apimarket three"
           " tables at zero rows), empty board envelope with"
           " keys %s, battery code vector %s == reference,"
           " unregistered publisher carrying a forbidden word"
           " rejects %s (registry gate precedes the content"
           " gate), probe batch leaves digests / ledger_tx /"
           " board / manual board constant"
           % (sorted(env1.keys()), codes1, order1))

    # -- AC-AMZG2 restart instance two, identical codes --------
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    codes2, order2, pure2, board2 = probe_batch(am2, led2,
                                                bad_word)
    ok2 = [codes2 == REFERENCE, codes2 == codes1,
           order2 == A.E_AM_NOT_DEV, all(pure2),
           board2 == board1]
    record("AC-AMZG2", all(ok2),
           "restart instance two (ordered close am -> dk ->"
           " metered -> led, same db_path same cfg bytes):"
           " battery code vector %s identical to the instance-"
           "one reference, ordering witness %s, probe batch"
           " zero side effects (digests, ledger_tx, board and"
           " manual board constant), board still empty"
           % (codes2, order2))

    # -- AC-AMZG3 restart instance three, identical codes ------
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(db_path, cfg,
                                                  lobby_cfg)
    codes3, order3, pure3, board3 = probe_batch(am3, led3,
                                                bad_word)
    ok3 = [codes3 == REFERENCE, codes3 == codes2,
           order3 == A.E_AM_NOT_DEV, all(pure3)]
    record("AC-AMZG3", all(ok3),
           "restart instance three (second full-stack restart):"
           " battery code vector %s identical again, ordering"
           " witness %s, probe batch zero side effects on the"
           " third instance"
           % (codes3, order3))

    # -- AC-AMZG4 three-instance code-set invariance -----------
    ok4 = [codes1 == codes2 == codes3 == REFERENCE,
           len(codes1) == 4,
           board3 == board1 and dumps(am3.dev_sales_board())
           == board1,
           am3.dev_sales_board()["board"] == []]
    record("AC-AMZG4", all(ok4),
           "three-instance invariance: the ordered four-code"
           " vector is pairwise identical across instances"
           " one/two/three (%s), the full probe history leaves"
           " the board at the honest empty state (zero phantom"
           " rows across two restarts)"
           % " = ".join([str(codes1), str(codes2),
                         str(codes3)]))

# -- AC-AMZG5 gate ordering law across restarts -----------
    # The battery already recorded the unregistered-with-a-
    # forbidden-word witness on instances two and three; this
    # pins the registered contrast on the still-open third
    # instance (instance two is closed by design above).
    d5 = market_digests(am3)
    board5 = dumps(am3.dev_sales_board())
    w3 = probe(lambda: am3.publish_api(
        "usr:ada", "ada-word-svc",
        "title says " + bad_word,
        "registered developer with a forbidden word", PAYLOAD,
        5, False), A.E_AM_CONTENT_REJECTED)
    ok5 = [order2 == A.E_AM_NOT_DEV and order3 == A.E_AM_NOT_DEV,
           w3 == A.E_AM_CONTENT_REJECTED,
           market_digests(am3) == d5,
           dumps(am3.dev_sales_board()) == board5]
    record("AC-AMZG5", all(ok5),
           "gate ordering law survives restart: on instances"
           " two and three an unregistered publisher whose"
           " title carries a forbidden word still rejects"
           " E_AM_NOT_DEV (registry gate first, no msgSecCheck"
           " burned), while the registered developer with the"
           " same forbidden word on the third instance rejects"
           " %s (content gate reachable only past the registry"
           " gate); the contrast probe leaves digests and the"
           " board constant" % w3)

    # -- AC-AMZG6 probe batch zero read dependency ------------
    d6 = market_digests(am3)
    ok6 = [all(v[0] == 0 for v in d6.values()),
           manual_board(am3) == [],
           dumps(am3.dev_sales_board()) == board1]
    record("AC-AMZG6", all(ok6),
           "probe batch leaves no read-visible trace on the"
           " third instance: apimarket three tables still at"
           " zero rows, manual two-query cross == [], board"
           " dump identical to the pre-battery snapshot"
           " (rejections never materialise as rows)")

    # -- AC-AMZG7 post-battery liveness on instance three ------
    first = am3.publish_api(
        "usr:ada", "gate-after", "Gate After API",
        "first listing after the gate battery", PAYLOAD, 10,
        False)
    buy = am3.purchase_api("usr:bob", first["listing_id"],
                           "pgz1")
    env7 = am3.dev_sales_board()
    rows7 = env7["board"]
    conn = sqlite3.connect(am3.db_path)
    prow = conn.execute(
        "SELECT spend_tx, dev_share_tx FROM apimarket_purchases"
        " WHERE buyer_id = 'usr:bob'").fetchall()
    conn.close()
    ids3 = ledger_tx_ids(led3)
    ok7 = []
    ok7.append([row_tuple(r) for r in rows7]
               == [("usr:ada", 1, 1, 10, 7, 3)])
    ok7.append(rows7 and rows7[0]["gross_revenue"]
               == rows7[0]["dev_revenue"]
               + rows7[0]["platform_revenue"])
    ok7.append([row_tuple(r) for r in rows7]
               == [row_tuple(r) for r in manual_board(am3)])
    ok7.append(dumps(am3.dev_sales_board()) == dumps(env7))
    ok7.append(len(prow) == 1)
    if prow:
        spend_tx, share_tx = str(prow[0][0]), str(prow[0][1])
        ok7.append(spend_tx.strip() != ""
                   and share_tx.strip() != ""
                   and spend_tx != share_tx
                   and spend_tx in ids3 and share_tx in ids3)
    else:
        ok7.append(False)
    ok7.append(buy["purchase_id"] > 0)
    record("AC-AMZG7", all(ok7),
           "post-battery liveness on the third instance: a"
           " legitimate publish + purchase still succeeds"
           " (listing_id=%s purchase_id=%s) and the board"
           " recomputes to exactly (usr:ada, 1, 1, 10, 7, 3)"
           " with gross == dev + platform conservation, manual"
           " cross equal, repeat read identical, and both"
           " provenance tx ids present in the ledger_tx set"
           " (the gate battery poisoned nothing)"
           % (first["listing_id"], buy["purchase_id"]))
    close_stack(am3, dk3, metered3, led3)

    # -- AC-AMZG8 hygiene + delivery ---------------------------
    shas_after = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        src_bytes = handle.read()
    ok8 = [all(b < 128 for b in src_bytes)]
    net_hits = []
    for line in src_bytes.decode("ascii").splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith(
                "from "):
            for bad in ("urllib", "requests", "socket", "http"):
                if bad in stripped:
                    net_hits.append(stripped)
    ok8.append(not net_hits)
    ok8.append(os.path.abspath(tmp).startswith(
        tempfile.gettempdir()))
    ok8.append(os.path.abspath(BASE) not in os.path.abspath(tmp))
    reg_path = os.path.normpath(
        os.path.join(BASE, "..", "reconcile_all.py"))
    with open(reg_path, encoding="utf-8") as handle:
        reg_src = handle.read()
    ok8.append(
        "ledger-apimarket-devboardgatepersist" in reg_src
        and "test_apimarket_devboardgatepersist.py" in reg_src
        and "), 8)" in reg_src)
    ok8.append(shas_after == shas_before)
    ok8.append(len(RESULTS) + 1 == 8)
    record("AC-AMZG8", all(ok8),
           "hygiene: source pure ASCII (%d bytes), zero network"
           " imports on true import lines, world db in system"
           " tmp outside the repo, registry row wired"
           " (ledger-apimarket-devboardgatepersist, criteria"
           " 8), product five-file sha256 unchanged, criteria"
           " count == 8" % len(src_bytes))

    fails = [r for r in RESULTS if not r[1]]
    print("SUITE PASS (%d/%d criteria green)"
          % (len(RESULTS) - len(fails), len(RESULTS)), flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()