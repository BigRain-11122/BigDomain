"""Acceptance suite for the apimarket repricing step-size band face
(BigDomain R2198; canon = the R2198 explore claim row, criteria
AC-PSD1..AC-PSD8 registered in that row BEFORE this code existed -
honesty law; test_apimarket_pricesteps, ledger-apimarket-pricesteps,
step_band, band_share, most_common_band and _STEP_BANDS were all
git-grep zero-occupancy against HEAD 2026-10-28, rc=1, while the
AC-PSD prefix and the face name only ever appeared inside that seed
row text).

Face under proof: APIMarketFace.api_price_step_distribution.
api_price_history lists one listing's revisions and api_price_volatility
collapses every step into scalar aggregates, so a market of timid
micro-adjustments and one of half-price cuts read identically there.
This suite pins:

  - the thirteen-key envelope and ten-key band rows with the five
    bands ALWAYS present in fixed order, honest empty first;
  - the half-open band law with the upper bound included (a boundary
    value lands in the larger band) and step arithmetic identical to
    api_price_volatility;
  - count conservation per band and across faces;
  - the share law (step_share sums to 1.0, up_share None on an empty
    band rather than a fabricated 0.0);
  - within-band aggregates and the pooled envelope aggregates with
    None instead of 0.0 on zero steps;
  - the most_common_band law with the smaller-magnitude tie-break;
  - the scope law (market carries no self-benchmark, a seller carries
    the market-wide pooled benchmark, strict isolation, a
    never-repricing seller reads honestly empty);
  - the seven-form account gate, the pure-read law, cross-face
    identity against api_price_volatility, the invariances (purchase,
    delist, relist) and cross-restart byte identity.

Usage: python test_apimarket_pricesteps.py
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
    "dev_account", "scope", "revision_count", "band_count", "up_count",
    "down_count", "avg_abs_step_pct", "median_abs_step_pct",
    "max_abs_step_pct", "market_avg_abs_step_pct", "most_common_band",
    "disclaimer", "bands"}

BAND_KEYS = {
    "band", "lower_pct", "upper_pct", "step_count", "up_count",
    "down_count", "step_share", "up_share", "avg_abs_pct",
    "max_abs_pct"}

BAND_ORDER = ["micro", "small", "medium", "large", "sweep"]

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


def band_of(env, name):
    for row in env["bands"]:
        if row["band"] == name:
            return row
    raise AssertionError("band %r missing from bands" % (name,))


def seed_world(led, dk, am):
    """Eight steps landing exactly on every band boundary the law
    cares about: two 1.0% micro steps, a 2.0% (small boundary) and a
    5.0% small step, a +10.0% (medium boundary) and a -10.0% medium
    step, a 25.0% (large boundary) and a 100.0% sweep step, so micro,
    small and medium tie at two and the smallest-magnitude band must
    win. frank publishes but never reprices, so f1 must stay absent
    from every count."""
    led.mint_to_pool("pool:reserve", 40000, "SETTLE-PSD-A", "settlement")
    led.mint_to_pool("pool:share", 40000, "SETTLE-PSD-S", "settlement")
    for who in ("bob", "carol"):
        fund(led, who)
    for dev in ("dana", "erin", "frank", "gina"):
        dk.issue_key("usr:" + dev, dev + "-key", 10,
                     ["backtest"], False)

    a1 = am.publish_api("usr:dana", "a1", "Alpha API",
                        "alpha payloads", PAYLOAD, 100,
                        False)["listing_id"]
    a2 = am.publish_api("usr:dana", "a2", "Beta API",
                        "beta payloads", PAYLOAD, 100,
                        False)["listing_id"]
    a3 = am.publish_api("usr:dana", "a3", "Gamma API",
                        "gamma payloads", PAYLOAD, 100,
                        False)["listing_id"]
    b1 = am.publish_api("usr:erin", "b1", "Erin One API",
                        "erin payloads", PAYLOAD, 100,
                        False)["listing_id"]
    b2 = am.publish_api("usr:erin", "b2", "Erin Two API",
                        "erin payloads", PAYLOAD, 100,
                        False)["listing_id"]
    f1 = am.publish_api("usr:frank", "f1", "Frank One API",
                        "frank payloads", PAYLOAD, 50,
                        False)["listing_id"]
    c1 = am.publish_api("usr:gina", "c1", "Gina One API",
                        "gina payloads", PAYLOAD, 100,
                        False)["listing_id"]
    c2 = am.publish_api("usr:gina", "c2", "Gina Two API",
                        "gina payloads", PAYLOAD, 100,
                        False)["listing_id"]

    am.revise_price("usr:dana", a1, 101)      # +1.0  micro
    am.revise_price("usr:dana", a2, 101)      # +1.0  micro
    am.revise_price("usr:dana", a3, 102)      # +2.0  small boundary
    am.revise_price("usr:erin", b1, 105)      # +5.0  small
    am.revise_price("usr:erin", b2, 110)      # +10.0 medium boundary
    am.revise_price("usr:erin", b2, 99)       # -10.0 medium
    am.revise_price("usr:gina", c1, 125)      # +25.0 large boundary
    am.revise_price("usr:gina", c2, 200)      # +100.0 sweep
    return {"a1": a1, "a2": a2, "a3": a3, "b1": b1, "b2": b2,
            "f1": f1, "c1": c1, "c2": c2}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-pricesteps-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    ids = seed_world(led, dk, am)

    # -- AC-PSD1 the contract, five bands always present --------------
    empty_tmp = tempfile.mkdtemp(prefix="apimarket-psd-empty-")
    e_led, e_metered, e_dk, _e_gate, e_am = build_stack(
        os.path.join(empty_tmp, "ledger.db"), cfg, lobby_cfg)
    empty = e_am.api_price_step_distribution()
    empty_seller = e_am.api_price_step_distribution("usr:nobody")
    close_stack(e_am, e_dk, e_metered, e_led)
    market = am.api_price_step_distribution()
    band_keys_ok = all(set(row.keys()) == BAND_KEYS
                       for row in market["bands"])
    empty_bands_ok = all(set(row.keys()) == BAND_KEYS
                         for row in empty["bands"])
    ok1 = (set(market.keys()) == ENVELOPE_KEYS
           and set(empty.keys()) == ENVELOPE_KEYS
           and set(empty_seller.keys()) == ENVELOPE_KEYS
           and band_keys_ok and empty_bands_ok
           and [row["band"] for row in market["bands"]] == BAND_ORDER
           and [row["band"] for row in empty["bands"]] == BAND_ORDER
           and market["disclaimer"] == DISCLAIMER
           and empty["disclaimer"] == DISCLAIMER
           and empty["dev_account"] is None
           and empty["revision_count"] == 0
           and empty["band_count"] == 0
           and empty["up_count"] == 0
           and empty["down_count"] == 0
           and all(row["step_count"] == 0 for row in empty["bands"])
           and all(row["step_share"] is None for row in empty["bands"])
           and all(row["up_share"] is None for row in empty["bands"])
           and all(row["avg_abs_pct"] is None for row in empty["bands"])
           and all(row["max_abs_pct"] is None for row in empty["bands"])
           and empty["avg_abs_step_pct"] is None
           and empty["median_abs_step_pct"] is None
           and empty["max_abs_step_pct"] is None
           and empty["market_avg_abs_step_pct"] is None
           and empty["most_common_band"] is None
           and empty_seller["bands"] == empty["bands"]
           and empty_seller["avg_abs_step_pct"] is None)
    record("AC-PSD1", ok1,
           "keys=%d bandkeys=%r order=%r empty=%r"
           % (len(market), band_keys_ok,
              [row["band"] for row in market["bands"]],
              (empty["revision_count"], empty["most_common_band"],
               len(empty["bands"]))))

    # -- AC-PSD2 the half-open band law with the upper bound included --
    law_ok = (A.APIMarketFace._step_band(0.01) == "micro"
              and A.APIMarketFace._step_band(2.0) == "small"
              and A.APIMarketFace._step_band(2.01) == "small"
              and A.APIMarketFace._step_band(10.0) == "medium"
              and A.APIMarketFace._step_band(10.01) == "medium"
              and A.APIMarketFace._step_band(25.0) == "large"
              and A.APIMarketFace._step_band(25.01) == "large"
              and A.APIMarketFace._step_band(49.99) == "large"
              and A.APIMarketFace._step_band(50.0) == "sweep"
              and A.APIMarketFace._step_band(150.0) == "sweep"
              and A.APIMarketFace._step_band(0.0) is None)
    bounds_ok = (
        band_of(market, "micro")["lower_pct"] == 0.0
        and band_of(market, "micro")["upper_pct"] == 2.0
        and band_of(market, "small")["lower_pct"] == 2.0
        and band_of(market, "small")["upper_pct"] == 10.0
        and band_of(market, "medium")["lower_pct"] == 10.0
        and band_of(market, "medium")["upper_pct"] == 25.0
        and band_of(market, "large")["lower_pct"] == 25.0
        and band_of(market, "large")["upper_pct"] == 50.0
        and band_of(market, "sweep")["lower_pct"] == 50.0
        and band_of(market, "sweep")["upper_pct"] is None)
    # boundary members land in the larger band, proven on the world
    ok2 = (law_ok and bounds_ok
           and band_of(market, "small")["step_count"] == 2
           and band_of(market, "large")["step_count"] == 1
           and band_of(market, "sweep")["step_count"] == 1
           and ids["f1"] not in [ids["c1"], ids["c2"]])
    record("AC-PSD2", ok2,
           "law=%r bounds=%r counts=%r"
           % (law_ok, bounds_ok,
              {row["band"]: row["step_count"] for row in market["bands"]}))

    # -- AC-PSD3 count conservation and cross-face identity -----------
    vol = am.api_price_volatility()
    per_band_ok = all(
        row["step_count"] == row["up_count"] + row["down_count"]
        for row in market["bands"])
    ok3 = (per_band_ok
           and market["revision_count"] == 8
           and market["revision_count"] == sum(
               row["step_count"] for row in market["bands"])
           and market["revision_count"] == vol["revision_count"]
           and market["up_count"] == 7
           and market["down_count"] == 1
           and market["up_count"] == vol["up_count"] == sum(
               row["up_count"] for row in market["bands"])
           and market["down_count"] == vol["down_count"] == sum(
               row["down_count"] for row in market["bands"])
           and market["band_count"] == 5
           and market["band_count"] == sum(
               1 for row in market["bands"] if row["step_count"] > 0))
    record("AC-PSD3", ok3,
           "per_band=%r rev=%d/%d up=%d/%d down=%d/%d band_count=%d"
           % (per_band_ok, market["revision_count"],
              vol["revision_count"], market["up_count"], vol["up_count"],
              market["down_count"], vol["down_count"],
              market["band_count"]))

    # -- AC-PSD4 the share law ---------------------------------------
    shares = [row["step_share"] for row in market["bands"]]
    ok4 = (abs(sum(shares) - 1.0) < 1e-9
           and all(share == 0.25 for share in shares[:3])
           and shares[3] == 0.125 and shares[4] == 0.125
           and band_of(market, "micro")["up_share"] == 1.0
           and band_of(market, "small")["up_share"] == 1.0
           and band_of(market, "medium")["up_share"] == 0.5
           and band_of(market, "large")["up_share"] == 1.0
           and band_of(market, "sweep")["up_share"] == 1.0
           and empty["bands"][0]["step_share"] is None)
    record("AC-PSD4", ok4,
           "sum=%r shares=%r medium_up=%r"
           % (round(sum(shares), 12), shares,
              band_of(market, "medium")["up_share"]))

    # -- AC-PSD5 within-band and pooled aggregates -------------------
    ok5 = (band_of(market, "micro")["avg_abs_pct"] == 1.0
           and band_of(market, "small")["avg_abs_pct"] == 3.5
           and band_of(market, "medium")["avg_abs_pct"] == 10.0
           and band_of(market, "large")["avg_abs_pct"] == 25.0
           and band_of(market, "sweep")["avg_abs_pct"] == 100.0
           and band_of(market, "micro")["max_abs_pct"] == 1.0
           and band_of(market, "small")["max_abs_pct"] == 5.0
           and band_of(market, "medium")["max_abs_pct"] == 10.0
           and band_of(market, "large")["max_abs_pct"] == 25.0
           and band_of(market, "sweep")["max_abs_pct"] == 100.0
           and market["avg_abs_step_pct"] == 19.25
           and market["median_abs_step_pct"] == 7.5
           and market["max_abs_step_pct"] == 100.0)
    record("AC-PSD5", ok5,
           "band_avg=%r pooled=%r"
           % ({row["band"]: row["avg_abs_pct"]
               for row in market["bands"]},
              (market["avg_abs_step_pct"],
               market["median_abs_step_pct"],
               market["max_abs_step_pct"])))

    # -- AC-PSD6 the most_common_band tie-break ----------------------
    tie_counts = {row["band"]: row["step_count"]
                  for row in market["bands"] if row["step_count"] == 2}
    ok6 = (tuple(tie_counts.keys()) == ("micro", "small", "medium")
           and market["most_common_band"] == "micro"
           and empty["most_common_band"] is None)
    record("AC-PSD6", ok6,
           "tie=%r most=%r empty=%r"
           % (tie_counts, market["most_common_band"],
              empty["most_common_band"]))

    # -- AC-PSD7 the scope law, the gate family and the pure read -----
    dana = am.api_price_step_distribution("usr:dana")
    erin = am.api_price_step_distribution("usr:erin")
    frank = am.api_price_step_distribution("usr:frank")
    dana_counts = {row["band"]: row["step_count"] for row in dana["bands"]}
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    acct_codes = []
    for bad in ("", "u", "usr", 123, [], {"usr:x": 1}, False):
        try:
            am.api_price_step_distribution(bad)
            acct_codes.append("NO-ERROR:%r" % (bad,))
        except A.ApiMarketError as exc:
            acct_codes.append(getattr(exc, "code", "?"))
    prefix = am.api_price_step_distribution("usr:")
    twice = am.api_price_step_distribution()
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    ok7 = (market["scope"] == "market"
           and market["market_avg_abs_step_pct"] is None
           and dana["scope"] == "seller"
           and dana["market_avg_abs_step_pct"] == 19.25
           and dana["revision_count"] == 3
           and dana_counts == {"micro": 2, "small": 1, "medium": 0,
                              "large": 0, "sweep": 0}
           and dana["avg_abs_step_pct"] == 1.33
           and dana["median_abs_step_pct"] == 1.0
           and dana["most_common_band"] == "micro"
           and erin["revision_count"] == 3
           and erin["avg_abs_step_pct"] == 8.33
           and erin["most_common_band"] == "medium"
           and frank["revision_count"] == 0
           and frank["bands"] == empty["bands"]
           and frank["market_avg_abs_step_pct"] == 19.25
           and acct_codes == ["E_AM_BAD_ACCOUNT"] * 7
           and prefix["revision_count"] == 0
           and prefix["most_common_band"] is None
           and prefix["bands"] == empty["bands"]
           and twice == market
           and digests_before == digests_after
           and tx_before == tx_after)
    record("AC-PSD7", ok7,
           "market_bench=%r dana=%r erin=%r frank=%r acct=%r"
           " frozen=%r idem=%r"
           % (market["market_avg_abs_step_pct"],
              (dana["revision_count"], dana["avg_abs_step_pct"],
               dana["most_common_band"]),
              (erin["revision_count"], erin["avg_abs_step_pct"],
               erin["most_common_band"]), frank["revision_count"],
              acct_codes, digests_before == digests_after,
              twice == market))

    # -- AC-PSD8 invariances, cross-restart identity and the wiring ---
    snapshot = dumps(am.api_price_step_distribution())
    am.purchase_api("usr:bob", ids["c1"], "ref-psd-bob-c1")
    after_buy = dumps(am.api_price_step_distribution())
    am.delist_api("usr:frank", ids["f1"])
    after_delist = dumps(am.api_price_step_distribution())
    am.relist_api("usr:frank", ids["f1"])
    after_relist = dumps(am.api_price_step_distribution())
    before_move = am.api_price_step_distribution()
    am.revise_price("usr:dana", ids["a3"], 120)
    after_move = am.api_price_step_distribution()
    ok_move = (after_move["revision_count"] == 9
               and band_of(after_move, "small")["step_count"] == 2
               and band_of(after_move, "medium")["step_count"] == 3
               and after_move["most_common_band"] == "medium")
    final_market = dumps(am.api_price_step_distribution())
    final_dana = dumps(am.api_price_step_distribution("usr:dana"))
    final_frank = dumps(am.api_price_step_distribution("usr:frank"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second_market = dumps(am.api_price_step_distribution())
    second_dana = dumps(am.api_price_step_distribution("usr:dana"))
    second_frank = dumps(am.api_price_step_distribution("usr:frank"))
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third_market = dumps(am.api_price_step_distribution())
    third_dana = dumps(am.api_price_step_distribution("usr:dana"))
    third_frank = dumps(am.api_price_step_distribution("usr:frank"))
    tx_b = ledger_tx_ids(led)
    dig_b = market_digests(am)
    for _ in range(3):
        am.api_price_step_distribution()
        am.api_price_step_distribution("usr:dana")
        am.api_price_step_distribution("usr:frank")
    tx_a = ledger_tx_ids(led)
    dig_a = market_digests(am)
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    with open(os.path.abspath(__file__), "rb") as handle:
        suite_text = handle.read().decode("utf-8")
    # the needle is assembled so this very assertion line is not a
    # self-referential hit (R1678 lesson).
    net_needle = "import " + "socket"
    ok8 = (after_buy == snapshot
           and after_delist == snapshot
           and after_relist == snapshot
           and ok_move
           and final_market == second_market == third_market
           and final_dana == second_dana == third_dana
           and final_frank == second_frank == third_frank
           and tx_b == tx_a
           and dig_b == dig_a
           and shas_before == shas_after
           and "ledger-apimarket-pricesteps" in runner_text
           and all(ord(ch) < 128 for ch in suite_text)
           and net_needle not in suite_text)
    record("AC-PSD8", ok8,
           "sha16=%s buy=%r delist=%r relist=%r move=%r"
           " identical=%r files_equal=%r registered=%r"
           % (hashlib.sha256(final_market.encode("utf-8"))
              .hexdigest()[:16],
              after_buy == snapshot, after_delist == snapshot,
              after_relist == snapshot,
              (ok_move, after_move["revision_count"],
               band_of(after_move, "small")["step_count"],
               band_of(after_move, "medium")["step_count"],
               after_move["most_common_band"]),
              final_market == second_market == third_market,
              shas_before == shas_after,
              "ledger-apimarket-pricesteps" in runner_text))

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