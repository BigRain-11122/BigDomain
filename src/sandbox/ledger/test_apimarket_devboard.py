"""Acceptance suite for the apimarket developer sales board
read face (BigDomain explore queue, claimed round R1978; canon =
the "API market developer sales board" row). Asserts the
pre-registered criteria AC-AMB1..AC-AMB7 from the R1978
explore-queue claim row (criteria were registered in
state/queue/explore.md before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

The content gate is the lobby SecGate product injected by
reference (no copy): its Chinese wordlists are data loaded from
the lobby config at runtime - this test source stays pure ASCII
per the encoding discipline.

Usage: python test_apimarket_devboard.py
"""

import hashlib
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import sqlite3  # noqa: E402 (stdlib, after path setup)

import ledger as L                    # noqa: E402 (P-47-2b core)
import metered as M                   # noqa: E402 (R626 product)
import apidev as D                    # noqa: E402 (R1700 registry face)
import apimarket as A                 # noqa: E402 (R1763 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, reference)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API marketplace"
              " is a service listing face, not investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def table_digest(conn, table):
    rows = conn.execute(
        "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    blob = repr(rows).encode("utf-8")
    return len(rows), hashlib.sha256(blob).hexdigest()


def build_world(tmp):
    """Shared world builder: ledger + registry + market face with
    the seven-developer / three-buyer board world."""
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    gate = SecGate.from_config(lobby_cfg)
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)
    return led, dk, am, cfg, lobby_cfg


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-devboard-ac-")
    cfg_sha_before = sha_file(os.path.join(BASE, "config.json"))
    lobby_sha_before = sha_file(os.path.join(LOBBY, "config.json"))
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    led, dk, am, cfg, lobby_cfg = build_world(tmp)
    conn = sqlite3.connect(led.db_path)
    am_conn = sqlite3.connect(am.db_path)

    led.mint_to_pool("pool:reserve", 4000, "SETTLE-AMB-A", "settlement")
    led.mint_to_pool("pool:share", 1000, "SETTLE-AMB-S", "settlement")
    accounts = ("ada", "dan", "bob", "carol", "eve", "frank",
                "gina", "b-alpha", "b-zeta")
    for who in accounts:
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 200),
                    ("usr:" + who, "credit", 200)],
                   "manual:fund-" + who, "suite funding " + who)
    # developer registry rows (the registry gate needs >=1 key)
    for who, scopes in (("ada", ["backtest"]), ("dan", ["visualize"]),
                        ("carol", ["backtest"]), ("gina", ["visualize"]),
                        ("b-alpha", ["backtest"]),
                        ("b-zeta", ["visualize"])):
        dk.issue_key("usr:" + who, who + "-key", 10, scopes, False)

    # listings: ada x2, dan x1 (zero sales), carol x2, gina x1,
    # b-alpha x1 + b-zeta x1 (zero-sales tie group)
    a1 = am.publish_api("usr:ada", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)
    a2 = am.publish_api("usr:ada", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)
    am.publish_api("usr:dan", "risk-scan", "Dan Risk Variant",
                   "same key other developer", PAYLOAD, 7, False)
    c1 = am.publish_api("usr:carol", "carol-alpha", "Carol Alpha API",
                        "carol first endpoint", PAYLOAD, 10, False)
    c2 = am.publish_api("usr:carol", "carol-beta", "Carol Beta API",
                        "carol second endpoint", PAYLOAD, 4, True)
    g1 = am.publish_api("usr:gina", "gina-gamma", "Gina Gamma API",
                        "gina single endpoint", PAYLOAD, 14, False)
    am.publish_api("usr:b-alpha", "alpha-echo", "Alpha Echo API",
                   "alpha dormant endpoint", PAYLOAD, 5, False)
    am.publish_api("usr:b-zeta", "zeta-echo", "Zeta Echo API",
                   "zeta dormant endpoint", PAYLOAD, 5, False)

    # purchases (unique per buyer+listing; zero self-buys)
    am.purchase_api("usr:bob", a1["listing_id"], "ref-bob-a1")
    am.purchase_api("usr:bob", a2["listing_id"], "ref-bob-a2")
    am.purchase_api("usr:carol", a1["listing_id"], "ref-carol-a1")
    am.purchase_api("usr:eve", a1["listing_id"], "ref-eve-a1")
    am.purchase_api("usr:frank", c1["listing_id"], "ref-frank-c1")
    am.purchase_api("usr:bob", c2["listing_id"], "ref-bob-c2")
    am.purchase_api("usr:bob", g1["listing_id"], "ref-bob-g1")

    # pre-read table digests (pure-read law baseline)
    pre = {t: table_digest(am_conn, t) for t in
           ("apimarket_listings", "apimarket_purchases",
            "apimarket_ratings")}
    pre_ledger_tx = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]

    board_env = am.dev_sales_board()
    board = board_env["board"]

    # -- AC-AMB1 row-set authority --------------------------------------
    listed_devs = {r[0] for r in am_conn.execute(
        "SELECT DISTINCT dev_account FROM apimarket_listings")}
    rows_devs = {row["dev_account"] for row in board}
    zero_rows = [row for row in board
                 if row["dev_account"] in ("usr:dan", "usr:b-alpha",
                                          "usr:b-zeta")]
    ok1 = (rows_devs == listed_devs and len(board) == len(listed_devs)
           and "usr:eve" not in rows_devs
           and "usr:bob" not in rows_devs
           and len(zero_rows) == 3
           and all(r["purchase_count"] == 0 and r["gross_revenue"] == 0
                   and r["dev_revenue"] == 0
                   and r["platform_revenue"] == 0
                   and r["listing_count"] == 1 for r in zero_rows))
    record("AC-AMB1",
           ok1 and len(listed_devs) == 6,
           "rows=%d==listed_devs=%d zero-sales-rows=%d pure-buyer"
           " eve absent=%s" % (len(board), len(listed_devs),
                               len(zero_rows),
                               "usr:eve" not in rows_devs))

    # -- AC-AMB2 aggregation + conservation ------------------------------
    indep = {r[0]: r for r in am_conn.execute(
        "SELECT l.dev_account, COUNT(DISTINCT l.listing_id),"
        " COALESCE(SUM(p.price_paid), 0), COALESCE(SUM(p.dev_share),"
        " 0), COALESCE(SUM(p.platform_share), 0),"
        " COUNT(p.purchase_id) FROM apimarket_listings l LEFT JOIN"
        " apimarket_purchases p ON p.listing_id = l.listing_id"
        " GROUP BY l.dev_account")}
    ok2 = True
    for row in board:
        r = indep[row["dev_account"]]
        ok2 = ok2 and row["listing_count"] == int(r[1])
        ok2 = ok2 and row["gross_revenue"] == int(r[2])
        ok2 = ok2 and row["dev_revenue"] == int(r[3])
        ok2 = ok2 and row["platform_revenue"] == int(r[4])
        ok2 = ok2 and row["purchase_count"] == int(r[5])
        ok2 = ok2 and (row["gross_revenue"] == row["dev_revenue"]
                       + row["platform_revenue"])
    ada_row = [row for row in board
               if row["dev_account"] == "usr:ada"][0]
    sales = am.api_sales("usr:ada")["sales"]
    cross_gross = sum(s["price_paid"] for s in sales)
    cross_dev = sum(s["dev_share"] for s in sales)
    cross_plat = sum(s["platform_share"] for s in sales)
    expected_ada = {"listing_count": 2, "purchase_count": 4,
                    "gross_revenue": 33, "dev_revenue": 24,
                    "platform_revenue": 9}
    ok2 = (ok2 and ada_row["gross_revenue"] == cross_gross
           and ada_row["dev_revenue"] == cross_dev
           and ada_row["platform_revenue"] == cross_plat
           and all(ada_row[k] == v for k, v in expected_ada.items()))
    record("AC-AMB2", ok2,
           "groupby-equal=%s conservation-all-rows=%s"
           " ada-cross api_sales gross %d==%d dev %d==%d"
           " expected-ada-match=%s"
           % (rows_devs and ok2, ok2, ada_row["gross_revenue"],
              cross_gross, ada_row["dev_revenue"], cross_dev,
              all(ada_row[k] == v for k, v in
                  expected_ada.items())))

    # -- AC-AMB3 deterministic order -------------------------------------
    order = [row["dev_account"] for row in board]
    expected_order = ["usr:ada", "usr:carol", "usr:gina",
                      "usr:b-alpha", "usr:b-zeta", "usr:dan"]
    carol_row = [row for row in board
                 if row["dev_account"] == "usr:carol"][0]
    gina_row = [row for row in board
                if row["dev_account"] == "usr:gina"][0]
    ok3 = (order == expected_order
           and carol_row["dev_revenue"] == gina_row["dev_revenue"] == 10
           and carol_row["purchase_count"] > gina_row["purchase_count"])
    record("AC-AMB3", ok3,
           "order=%s rev-tie carol 10==gina 10 broken by count"
           " 2>1=%s zero-group account-ASC=%s"
           % (order,
              carol_row["purchase_count"] > gina_row["purchase_count"],
              order[3:] == ["usr:b-alpha", "usr:b-zeta", "usr:dan"]))

    # -- AC-AMB4 envelope + row key-set ----------------------------------
    row_keys = {"dev_account", "listing_count", "purchase_count",
                "gross_revenue", "dev_revenue", "platform_revenue"}
    ok4 = (board_env.get("disclaimer") == am.disclaimer
           and all(set(row.keys()) == row_keys for row in board))
    record("AC-AMB4", ok4,
           "disclaimer-resident=%s six-key-exact=%s"
           % (board_env.get("disclaimer") == am.disclaimer,
              all(set(row.keys()) == row_keys for row in board)))

    # -- AC-AMB5 pure-read law -------------------------------------------
    second = am.dev_sales_board()
    post = {t: table_digest(am_conn, t) for t in
            ("apimarket_listings", "apimarket_purchases",
             "apimarket_ratings")}
    post_ledger_tx = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    ok5 = (pre == post and pre_ledger_tx == post_ledger_tx
           and second["board"] == board)
    record("AC-AMB5", ok5,
           "three-table digests stable=%s ledger_tx %d==%d"
           " double-read-identical=%s"
           % (pre == post, pre_ledger_tx, post_ledger_tx,
              second["board"] == board))

    # -- AC-AMB6 empty market honest empty board -------------------------
    tmp2 = tempfile.mkdtemp(prefix="apimarket-devboard-empty-")
    led2, dk2, am2, _cfg2, _lc2 = build_world(tmp2)
    empty_env = am2.dev_sales_board()
    ok6 = (empty_env["board"] == []
           and empty_env["disclaimer"] == am2.disclaimer)
    record("AC-AMB6", ok6,
           "empty-board=%s disclaimer-present=%s"
           % (empty_env["board"] == [],
              empty_env["disclaimer"] == am2.disclaimer))
    am2.close()
    led2.close()

    # -- AC-AMB7 hygiene ---------------------------------------------------
    src_path = os.path.abspath(__file__)
    with open(src_path, "rb") as handle:
        src_bytes = handle.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    net_hits = []
    with open(src_path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                if any(word in stripped for word in
                       ("urllib", "requests", "socket", "http")):
                    net_hits.append(stripped)
    cfg_sha_after = sha_file(os.path.join(BASE, "config.json"))
    lobby_sha_after = sha_file(os.path.join(LOBBY, "config.json"))
    tmp_outside = not os.path.abspath(tmp).startswith(repo_root)
    am_mod = os.path.join(BASE, "apimarket.py")
    with open(am_mod, "rb") as handle:
        mod_ascii = all(b < 128 for b in handle.read())
    ok7 = (ascii_ok and not net_hits
           and cfg_sha_before == cfg_sha_after
           and lobby_sha_before == lobby_sha_after and tmp_outside
           and mod_ascii)
    record("AC-AMB7", ok7,
           "src-ascii=%s net-imports=%d config-sha-stable=%s"
           " lobby-sha-stable=%s tmp-outside-repo=%s module-ascii=%s"
           % (ascii_ok, len(net_hits),
              cfg_sha_before == cfg_sha_after,
              lobby_sha_before == lobby_sha_after, tmp_outside,
              mod_ascii))

    am.close()
    led.close()
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              len(RESULTS) - len(failed),
                              len(RESULTS)), flush=True)
    if failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
