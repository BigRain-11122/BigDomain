"""Acceptance suite for the apimarket seller-side buyer concentration
face (BigDomain R2170; canon = the R2170 explore claim row, criteria
AC-SBC1..AC-SBC8 registered in that row BEFORE this code existed -
honesty law; the AC-SBC prefix, api_seller_concentration,
pareto_buyer_count, herfindahl, test_apimarket_concentration and
ledger-apimarket-concentration were all git-grep zero-occupancy
anchored against HEAD 2026-10-28, rc=1).

Face under proof: APIMarketFace.api_seller_concentration. The seller
side counts repeat purchases, quality, balances and gross volume; the
buyer side has its mirror image. None of them answers how many
residents a seller's net revenue hangs on and how much rides on the
biggest one. This suite pins:

  - the sixteen-key envelope and ten-key rows, honest empty first;
  - the purchase-side row authority and the total order
    (-net_revenue, buyer_id ascending) with rank 1..n and a
    cumulative_share that lands on exactly 1.0;
  - conservation (rows sum to envelope, net + refunded == gross) and
    the refund law (a fully refunded buyer stays on the roll at zero
    weight);
  - the share law (sum to 1.0 inside 1e-9, None when the scoped net
    total is zero - never a fake zero);
  - the herfindahl law (monopoly 10000.0, n equal buyers 10000/n);
  - the pareto law on integers, including the buyer that lands
    exactly on 80%;
  - the scope law (market scope carries no self-benchmark, a seller
    scope carries the market-wide herfindahl, strict seller
    isolation), the seven-form account gate, the pure-read law and
    cross-restart byte identity.

Usage: python test_apimarket_concentration.py
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
    "dev_account", "purchase_count", "refund_count", "buyer_count",
    "refunded_buyers", "gross_revenue", "refunded_tokens",
    "net_revenue", "top1_share", "top3_share", "herfindahl",
    "pareto_buyer_count", "market_herfindahl", "scope", "disclaimer",
    "buyers"}

ROW_KEYS = {
    "buyer_id", "purchase_count", "refund_count",
    "net_purchase_count", "gross_revenue", "refunded_tokens",
    "net_revenue", "share", "cumulative_share", "rank"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_relistings", "apimarket_price_revisions",
          "apimarket_listing_revisions", "apimarket_watchlist",
          "apimarket_unwatchings", "apimarket_refunds",
          "apimarket_category_revisions")


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


def fund(led, who):
    led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 400),
                ("usr:" + who, "credit", 400)],
               "manual:fund-" + who, "suite funding " + who)


def buyer_row(env, buyer_id):
    for row in env["buyers"]:
        if row["buyer_id"] == buyer_id:
            return row
    raise AssertionError("buyer %r missing from rows" % (buyer_id,))


def seed_world(led, dk, am):
    """dana sells to four residents (one of them twice, one fully
    refunded); frank sells to hal and to bob, so bob sits in both
    seller scopes with different weights; gina sells two equal units
    to two residents (the 10000/n law); hana has one buyer only (the
    monopoly law); ivan's single sale is fully refunded (the zero-net
    law); jade's first buyer lands exactly on 80% (the pareto
    boundary)."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-SBC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-SBC-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin", "hal", "ivy", "jon",
                "kate", "liam", "mia", "nate"):
        fund(led, who)
    for dev in ("dana", "frank", "gina", "hana", "ivan", "jade"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    a1 = am.publish_api("usr:dana", "a1", "Alpha API",
                        "alpha payloads", PAYLOAD, 10,
                        False)["listing_id"]
    a2 = am.publish_api("usr:dana", "a2", "Beta API",
                        "beta payloads", PAYLOAD, 20,
                        False)["listing_id"]
    a3 = am.publish_api("usr:dana", "a3", "Gamma API",
                        "gamma payloads", PAYLOAD, 30,
                        False)["listing_id"]
    a4 = am.publish_api("usr:dana", "a4", "Delta API",
                        "delta payloads", PAYLOAD, 40,
                        False)["listing_id"]
    a5 = am.publish_api("usr:dana", "a5", "Epsilon API",
                        "epsilon payloads", PAYLOAD, 30,
                        False)["listing_id"]
    f1 = am.publish_api("usr:frank", "f1", "Frank One API",
                        "frank payloads", PAYLOAD, 50,
                        False)["listing_id"]
    f2 = am.publish_api("usr:frank", "f2", "Frank Two API",
                        "frank payloads two", PAYLOAD, 50,
                        False)["listing_id"]
    g1 = am.publish_api("usr:gina", "g1", "Gina One API",
                        "gina payloads", PAYLOAD, 5,
                        False)["listing_id"]
    g2 = am.publish_api("usr:gina", "g2", "Gina Two API",
                        "gina payloads two", PAYLOAD, 5,
                        False)["listing_id"]
    h1 = am.publish_api("usr:hana", "h1", "Hana One API",
                        "hana payloads", PAYLOAD, 7,
                        False)["listing_id"]
    i1 = am.publish_api("usr:ivan", "i1", "Ivan One API",
                        "ivan payloads", PAYLOAD, 9,
                        False)["listing_id"]
    j1 = am.publish_api("usr:jade", "j1", "Jade One API",
                        "jade payloads", PAYLOAD, 8,
                        False)["listing_id"]
    j2 = am.publish_api("usr:jade", "j2", "Jade Two API",
                        "jade payloads two", PAYLOAD, 2,
                        False)["listing_id"]

    am.purchase_api("usr:bob", a1, "ref-bob-a1")
    am.purchase_api("usr:bob", a2, "ref-bob-a2")
    am.purchase_api("usr:carol", a3, "ref-carol-a3")
    am.purchase_api("usr:dave", a4, "ref-dave-a4")
    p_erin = am.purchase_api("usr:erin", a5, "ref-erin-a5")
    am.purchase_api("usr:hal", f1, "ref-hal-f1")
    am.purchase_api("usr:bob", f2, "ref-bob-f2")
    am.purchase_api("usr:ivy", g1, "ref-ivy-g1")
    am.purchase_api("usr:jon", g2, "ref-jon-g2")
    am.purchase_api("usr:kate", h1, "ref-kate-h1")
    p_nate = am.purchase_api("usr:nate", i1, "ref-nate-i1")
    am.purchase_api("usr:liam", j1, "ref-liam-j1")
    am.purchase_api("usr:mia", j2, "ref-mia-j2")

    am.refund_api("usr:erin", p_erin["purchase_id"],
                  "listing did not match description")
    am.refund_api("usr:nate", p_nate["purchase_id"],
                  "listing did not match description")


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-concentration-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    seed_world(led, dk, am)

    # -- AC-SBC1 the contract, honest empty first ---------------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-sbc-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_seller_concentration()
    empty_seller = e_am.api_seller_concentration("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_seller_concentration()
    row_keys_ok = all(set(row.keys()) == ROW_KEYS
                      for row in market["buyers"])
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and set(empty_seller.keys()) == ENVELOPE_KEYS
           and row_keys_ok
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["dev_account"] is None
           and empty["scope"] == "market"
           and empty["purchase_count"] == 0
           and empty["refund_count"] == 0
           and empty["buyer_count"] == 0
           and empty["refunded_buyers"] == 0
           and empty["gross_revenue"] == 0
           and empty["refunded_tokens"] == 0
           and empty["net_revenue"] == 0
           and empty["top1_share"] is None
           and empty["top3_share"] is None
           and empty["herfindahl"] is None
           and empty["pareto_buyer_count"] is None
           and empty["market_herfindahl"] is None
           and empty["buyers"] == []
           and empty_seller["dev_account"] == "usr:nobody"
           and empty_seller["scope"] == "seller"
           and empty_seller["buyer_count"] == 0
           and empty_seller["net_revenue"] == 0
           and empty_seller["herfindahl"] is None
           and empty_seller["buyers"] == [])
    record("AC-SBC1", ok1,
           "env_keys=%d exact=%r row_keys=%r rows=%d empty_rows=%d"
           % (len(market), set(market.keys()) == ENVELOPE_KEYS,
              row_keys_ok, len(market["buyers"]),
              len(empty["buyers"])))

    # -- AC-SBC2 purchase-side authority, order, cumulative -----------
    dana = am.api_seller_concentration("usr:dana")
    order = [row["buyer_id"] for row in dana["buyers"]]
    ranks = [row["rank"] for row in dana["buyers"]]
    cum = [row["cumulative_share"] for row in dana["buyers"]]
    monotone = all(cum[i] <= cum[i + 1] for i in range(len(cum) - 1))
    ok2 = (order == ["usr:dave", "usr:bob", "usr:carol", "usr:erin"]
           and ranks == [1, 2, 3, 4]
           and monotone
           and cum[-1] == 1.0
           and all(row["buyer_id"] != "usr:hal"
                   for row in dana["buyers"]))
    record("AC-SBC2", ok2,
           "order=%r ranks=%r cum=%r monotone=%r"
           % (order, ranks, cum, monotone))

    # -- AC-SBC3 conservation and the refund law ----------------------
    bob = buyer_row(dana, "usr:bob")
    erin = buyer_row(dana, "usr:erin")
    row_net = sum(row["net_revenue"] for row in dana["buyers"])
    row_gross = sum(row["gross_revenue"] for row in dana["buyers"])
    ok3 = (row_net == dana["net_revenue"] == 100
           and row_gross == dana["gross_revenue"] == 130
           and dana["net_revenue"] + dana["refunded_tokens"]
           == dana["gross_revenue"]
           and dana["refunded_tokens"] == 30
           and dana["purchase_count"] == 5
           and dana["refund_count"] == 1
           and dana["buyer_count"] == 4
           and dana["refunded_buyers"] == 1
           and bob["purchase_count"] == 2
           and bob["refund_count"] == 0
           and bob["net_purchase_count"] == 2
           and bob["gross_revenue"] == 30
           and bob["net_revenue"] == 30
           and erin["purchase_count"] == 1
           and erin["refund_count"] == 1
           and erin["net_purchase_count"] == 0
           and erin["gross_revenue"] == 30
           and erin["refunded_tokens"] == 30
           and erin["net_revenue"] == 0)
    record("AC-SBC3", ok3,
           "net=%r gross=%r refunded=%r counts=%r bob=%r erin=%r"
           % (dana["net_revenue"], dana["gross_revenue"],
              dana["refunded_tokens"],
              (dana["purchase_count"], dana["refund_count"],
               dana["buyer_count"], dana["refunded_buyers"]),
              (bob["purchase_count"], bob["net_revenue"]),
              (erin["purchase_count"], erin["net_revenue"])))

    # -- AC-SBC4 share law and the zero-net scope ---------------------
    shares = [row["share"] for row in dana["buyers"]]
    ivan = am.api_seller_concentration("usr:ivan")
    ivan_row = ivan["buyers"][0]
    ok4 = (shares == [0.4, 0.3, 0.3, 0.0]
           and abs(sum(shares) - 1.0) <= 1e-9
           and dana["top1_share"] == 0.4
           and dana["top3_share"] == 1.0
           and ivan["net_revenue"] == 0
           and ivan["buyer_count"] == 1
           and ivan["refunded_buyers"] == 1
           and ivan_row["net_revenue"] == 0
           and ivan_row["share"] is None
           and ivan_row["cumulative_share"] is None
           and ivan["top1_share"] is None
           and ivan["top3_share"] is None
           and ivan["herfindahl"] is None
           and ivan["pareto_buyer_count"] is None)
    record("AC-SBC4", ok4,
           "shares=%r sum=%r top1=%r top3=%r ivan=%r"
           % (shares, round(sum(shares), 9), dana["top1_share"],
              dana["top3_share"],
              (ivan["buyer_count"], ivan["herfindahl"],
               ivan_row["share"])))

    # -- AC-SBC5 herfindahl law ---------------------------------------
    gina = am.api_seller_concentration("usr:gina")
    hana = am.api_seller_concentration("usr:hana")
    jade = am.api_seller_concentration("usr:jade")
    exact = sum(
        (float(row["net_revenue"]) / dana["net_revenue"]) ** 2
        for row in dana["buyers"])
    ok5 = (dana["herfindahl"] == 3400.0
           and dana["herfindahl"] == round(exact * 10000, 2)
           and gina["herfindahl"] == 5000.0
           and gina["top1_share"] == 0.5
           and hana["herfindahl"] == 10000.0
           and hana["top1_share"] == 1.0
           and hana["top3_share"] == 1.0
           and jade["herfindahl"] == round(
               (0.8 ** 2 + 0.2 ** 2) * 10000, 2))
    record("AC-SBC5", ok5,
           "dana=%r exact=%r gina=%r hana=%r jade=%r"
           % (dana["herfindahl"], round(exact * 10000, 2),
              gina["herfindahl"], hana["herfindahl"],
              jade["herfindahl"]))

    # -- AC-SBC6 pareto law and the exact-80% boundary ----------------
    market_pareto = market["pareto_buyer_count"]
    jade_pareto = jade["pareto_buyer_count"]
    ok6 = (dana["pareto_buyer_count"] == 3
           and hana["pareto_buyer_count"] == 1
           and gina["pareto_buyer_count"] == 2
           and jade_pareto == 1
           # The market roll needs four buyers, not three: after
           # bob/hal/dave the cumulative net sits at 200 of 227
           # (88.1% is only reached on the fourth), so a hand-waved
           # three would be a defect, not a rounding choice.
           and market_pareto == 4
           and isinstance(jade_pareto, int)
           and not isinstance(jade_pareto, bool))
    record("AC-SBC6", ok6,
           "dana=%r hana=%r gina=%r jade=%r market=%r"
           % (dana["pareto_buyer_count"], hana["pareto_buyer_count"],
              gina["pareto_buyer_count"], jade_pareto,
              market_pareto))

    # -- AC-SBC7 scope law, benchmark and the gate --------------------
    bob_market = buyer_row(market, "usr:bob")
    ok7a = (market["scope"] == "market"
            and market["dev_account"] is None
            and market["market_herfindahl"] is None
            and dana["scope"] == "seller"
            and dana["market_herfindahl"] == market["herfindahl"]
            and gina["market_herfindahl"] == market["herfindahl"]
            and bob_market["net_revenue"] == 80
            and bob_market["purchase_count"] == 3
            and buyer_row(am.api_seller_concentration("usr:frank"),
                          "usr:bob")["net_revenue"] == 50
            and all(row["buyer_id"] != "usr:hal"
                    for row in dana["buyers"]))
    acct_codes = []
    for bad in ("", "u", "usr", 123, [], {"usr:x": 1}, False):
        try:
            am.api_seller_concentration(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_seller_concentration("usr:")
    ok7 = (ok7a
           and acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["buyer_count"] == 0
           and prefix["net_revenue"] == 0
           and prefix["herfindahl"] is None
           and prefix["buyers"] == [])
    record("AC-SBC7", ok7,
           "scope=%r benchmark=%r bob=%r acct=%r prefix=%r"
           % (market["scope"], dana["market_herfindahl"]
              == market["herfindahl"], bob_market["net_revenue"],
              acct_codes, prefix["buyer_count"]))

    # -- AC-SBC8 pure read, cross-restart identity and the wiring -----
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    again = dumps(am.api_seller_concentration("usr:dana"))
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    final_market = dumps(am.api_seller_concentration())
    final_dana = dumps(am.api_seller_concentration("usr:dana"))
    final_jade = dumps(am.api_seller_concentration("usr:jade"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_seller_concentration())
    second_dana = dumps(am.api_seller_concentration("usr:dana"))
    second_jade = dumps(am.api_seller_concentration("usr:jade"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_seller_concentration())
    third_dana = dumps(am.api_seller_concentration("usr:dana"))
    third_jade = dumps(am.api_seller_concentration("usr:jade"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_seller_concentration()
        am.api_seller_concentration("usr:dana")
        am.api_seller_concentration("usr:jade")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    ok8 = (again == final_dana
           and final_market == second_market == third_market
           and final_dana == second_dana == third_dana
           and final_jade == second_jade == third_jade
           and digests_before == digests_after
           and tx_before == tx_after
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-concentration" in runner_text)
    record("AC-SBC8", ok8,
           "sha16=%s stable=%r identical=%r frozen=%r tx_equal=%r"
           " files_equal=%r registered=%r"
           % (hashlib.sha256(final_market.encode("utf-8"))
              .hexdigest()[:16], again == final_dana,
              final_market == second_market == third_market,
              digests_before == digests_after, tx_b == tx_a,
              shas_before == shas_after,
              "ledger-apimarket-concentration" in runner_text))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS %d/%d" % (passed, total)
    if passed != total:
        verdict = "SUITE FAIL %d/%d" % (passed, total)
    print(verdict, flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())