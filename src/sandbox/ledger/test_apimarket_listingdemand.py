"""Acceptance suite for the apimarket seller-side demand read face
(BigDomain R2112; canon = the explore-queue row seeded in R2111 and
claimed in R2112, criteria AC-AMDM1..AC-AMDM8 registered in that claim
note BEFORE this code existed - honesty law; the AC-AMDM prefix, the
api_listing_demand name, this suite name and the
ledger-apimarket-listingdemand runner label were all git-grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Face under proof: APIMarketFace.api_listing_demand. The watch surface
is buyer-side only (api_watchlist takes a buyer_id; api_view /
dev_profile / api_supply carry no watch count), so a seller could not
answer "how many residents watch this listing, and did watching turn
into a sale". This window pins that missing face:

  - a seven-key envelope and an eleven-key row, EVERY listing of the
    seller becoming a row (zero watchers and retired included), the
    rows a total order on (-watcher_count, listing_id);
  - the live-watch law: only watches without an append-only unwatch
    row count, so an unwatch lowers the count and a later re-watch
    adds exactly one;
  - the net conversion law: a watch converts only through a purchase
    that has not been refunded, and a refund returns the buyer to
    pending (converted + pending == watcher_count per row, envelope
    totals equal to the row sums);
  - seller isolation plus an honest empty envelope for a prefix-valid
    account with no listings, and the account shape gate before any
    read with frozen table digests;
  - retirement keeping the demand, current_price through the one
    current-price seam and title through the effective-metadata seam;
  - zero row mutations and zero token movement (pure read);
  - cross-restart byte identity;
  - the consumer proof: the settlement report's attention digest
    grows an unconverted_demand family from this face, so the face is
    not shipped in the no-consumer idle form.

Usage: python test_apimarket_listingdemand.py
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
import apimarket_report as RPT        # noqa: E402 (R2101 consumer)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

ENVELOPE_KEYS = {"dev_account", "listing_count", "total_watchers",
                 "converted_count", "pending_count", "disclaimer",
                 "rows"}
ROW_KEYS = {"listing_id", "listing_key", "title", "delisted",
            "delisted_utc", "current_price", "watcher_count",
            "converted_count", "pending_count", "oldest_watch_utc",
            "newest_watch_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")


class Clock(object):
    """Deterministic stamp holder; the module clock is patched in
    main() and restored in the finally block."""

    def __init__(self):
        self.value = "2026-10-06T00:00:00Z"

    def now_utc(self):
        return self.value


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


def frozen_digests(am):
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


def pool_balances(led):
    return {pool: led.balance(pool) for pool in POOLS}


def row_of(env, listing_id):
    found = [r for r in env["rows"] if r["listing_id"] == listing_id]
    return found[0] if found else None


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


def code_of(exc):
    return getattr(exc, "code", None)


def demand_code(am, dev_account):
    try:
        am.api_listing_demand(dev_account)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """Owner dana with three listings (d1 hot, d2 mid, d4 silent) and
    frank a SECOND registered developer (d3) - the isolation anchor.
    Watches: bob/carol/dave on d1, bob/erin on d2, bob on frank's d3.
    Purchases: bob on d1, erin on d2 - so each of those watches
    converts and the rest stay pending."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMDM-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMDM-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    clock.value = "2026-10-06T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-06T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    clock.value = "2026-10-06T00:00:03Z"
    d4 = am.publish_api("usr:dana", "quiet-api", "Quiet API",
                        "a listing nobody watches yet", PAYLOAD, 7,
                        False)["listing_id"]
    d3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 5,
                        False)["listing_id"]
    clock.value = "2026-10-06T00:00:10Z"
    am.watch_api("usr:bob", d1)
    clock.value = "2026-10-06T00:00:11Z"
    am.watch_api("usr:carol", d1)
    clock.value = "2026-10-06T00:00:12Z"
    am.watch_api("usr:dave", d1)
    clock.value = "2026-10-06T00:00:13Z"
    am.watch_api("usr:bob", d2)
    clock.value = "2026-10-06T00:00:14Z"
    am.watch_api("usr:erin", d2)
    clock.value = "2026-10-06T00:00:15Z"
    am.watch_api("usr:bob", d3)
    clock.value = "2026-10-06T00:00:20Z"
    p_bob_d1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")[
        "purchase_id"]
    am.purchase_api("usr:erin", d2, "ref-erin-d2")
    return d1, d2, d3, d4, p_bob_d1


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-listingdemand-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    clock = Clock()
    orig_now = A._now_utc
    A._now_utc = clock.now_utc
    try:
        return run(db_path, cfg, lobby_cfg, tmp, shas_before, clock)
    finally:
        A._now_utc = orig_now


def run(db_path, cfg, lobby_cfg, tmp, shas_before, clock):
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, d4, p_bob_d1 = seed_world(led, dk, am, clock)

    # -- AC-AMDM1 contract + dense shelf + total order -------------------
    env = am.api_listing_demand("usr:dana")
    rows = env["rows"]
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["dev_account"] == "usr:dana"
           and env["listing_count"] == 3
           and env["listing_count"] == len(rows)
           and env["total_watchers"] == 5
           and env["converted_count"] == 2
           and env["pending_count"] == 3
           and env["disclaimer"] == DISCLAIMER
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and [r["listing_id"] for r in rows] == [d1, d2, d4]
           and row_of(env, d1)["watcher_count"] == 3
           and row_of(env, d2)["watcher_count"] == 2
           and row_of(env, d4)["watcher_count"] == 0
           and row_of(env, d4)["oldest_watch_utc"] is None
           and row_of(env, d1)["oldest_watch_utc"]
           == "2026-10-06T00:00:10Z"
           and row_of(env, d1)["newest_watch_utc"]
           == "2026-10-06T00:00:12Z"
           and row_of(env, d1)["current_price"] == 10
           and row_of(env, d1)["title"] == "Risk Scan API")
    record("AC-AMDM1", ok1,
           "keys=%r rows=%r total=%d conv=%d pend=%d d4=%r"
           % (set(env.keys()) == ENVELOPE_KEYS,
              [(r["listing_id"], r["watcher_count"]) for r in rows],
              env["total_watchers"], env["converted_count"],
              env["pending_count"],
              (row_of(env, d4)["watcher_count"],
               row_of(env, d4)["oldest_watch_utc"])))

    # -- AC-AMDM2 live-watch law -----------------------------------------
    am.unwatch_api("usr:dave", d1)
    after_unwatch = am.api_listing_demand("usr:dana")
    am.watch_api("usr:dave", d1)
    after_rewatch = am.api_listing_demand("usr:dana")
    am.unwatch_api("usr:erin", d2)
    after_erin = am.api_listing_demand("usr:dana")
    hist = sqlite3.connect(am.db_path).execute(
        "SELECT COUNT(*) FROM apimarket_watchlist"
        " WHERE listing_id = ?", (d1,)).fetchone()[0]
    ok2 = (row_of(after_unwatch, d1)["watcher_count"] == 2
           and row_of(after_unwatch, d1)["newest_watch_utc"]
           == "2026-10-06T00:00:11Z"
           and row_of(after_rewatch, d1)["watcher_count"] == 3
           and int(hist) == 4
           and row_of(after_rewatch, d1)["converted_count"] == 1
           and row_of(after_erin, d2)["watcher_count"] == 1
           and row_of(after_erin, d2)["converted_count"] == 0
           and after_erin["total_watchers"] == 4)
    record("AC-AMDM2", ok2,
           "unwatch=%d rewatch=%d history_rows=%d d2_after=%d"
           % (row_of(after_unwatch, d1)["watcher_count"],
              row_of(after_rewatch, d1)["watcher_count"], int(hist),
              row_of(after_erin, d2)["watcher_count"]))

    # -- AC-AMDM3 net conversion law -------------------------------------
    am.refund_api("usr:bob", p_bob_d1, "suite refund")
    after_refund = am.api_listing_demand("usr:dana")
    row_d1 = row_of(after_refund, d1)
    am.purchase_api("usr:erin", d1, "ref-erin-d1-nonwatch")
    after_nonwatch = am.api_listing_demand("usr:dana")
    row_d1b = row_of(after_nonwatch, d1)
    sums_ok = all(r["converted_count"] + r["pending_count"]
                  == r["watcher_count"] for r in rows)
    env_sums_ok = (after_nonwatch["total_watchers"]
                   == sum(r["watcher_count"]
                          for r in after_nonwatch["rows"])
                   and after_nonwatch["converted_count"]
                   == sum(r["converted_count"]
                          for r in after_nonwatch["rows"])
                   and after_nonwatch["pending_count"]
                   == sum(r["pending_count"]
                          for r in after_nonwatch["rows"]))
    ok3 = (row_d1["converted_count"] == 0
           and row_d1["pending_count"] == 3
           and row_d1["watcher_count"] == 3
           and row_d1b["converted_count"] == 0
           and row_d1b["pending_count"] == 3
           and sums_ok and env_sums_ok
           and row_of(after_refund, d2)["converted_count"] == 0)
    record("AC-AMDM3", ok3,
           "d1 after refund conv=%d pend=%d; non-watcher purchase"
           " conv=%d; row sums=%r env sums=%r"
           % (row_d1["converted_count"], row_d1["pending_count"],
              row_d1b["converted_count"], sums_ok, env_sums_ok))

    # -- AC-AMDM8 consumer proof (evaluated before the retirement legs) --
    fake_report = {"sellers": {"usr:dana": {
                       "revenue_months": {"months": []}}},
                   "board": {"listings": []},
                   "buyers": {}}
    attention = RPT.collect_attention(am, fake_report)
    demand_findings = [f for f in attention["findings"]
                       if f["kind"] == "unconverted_demand"]
    with open(RECONCILE, "r", encoding="utf-8") as handle:
        reconcile_text = handle.read()
    with open(os.path.join(BASE, "apimarket_report.py"), "r",
              encoding="utf-8") as handle:
        report_text = handle.read()
    with open(os.path.abspath(__file__), "rb") as handle:
        suite_bytes = handle.read()
    ascii_ok = all(b < 128 for b in suite_bytes)
    source_ascii = all(b < 128 for b in
                       open(os.path.join(BASE, "apimarket.py"),
                            "rb").read())
    ok8 = (len(demand_findings) == 1
           and demand_findings[0]["subject"] == "usr:dana"
           and demand_findings[0]["severity"] == "warn"
           and demand_findings[0]["ref"] == "risk-scan"
           and "3 watcher(s) on Risk Scan API with no sale yet"
           in demand_findings[0]["detail"]
           and "unconverted_demand" in report_text
           and "api_listing_demand" in report_text
           and "ledger-apimarket-listingdemand"
           in reconcile_text
           and "test_apimarket_listingdemand.py" in reconcile_text
           and ascii_ok and source_ascii)
    record("AC-AMDM8", ok8,
           "consumer findings=%r reconcile-wire=%r ascii=%r/%r"
           % ([(f["kind"], f["subject"], f["ref"])
               for f in demand_findings],
              "ledger-apimarket-listingdemand" in reconcile_text,
              ascii_ok, source_ascii))

    # -- AC-AMDM4 isolation + gate order ---------------------------------
    frank = am.api_listing_demand("usr:frank")
    empty = am.api_listing_demand("usr:ghost")
    dana_keys = set(r["listing_key"] for r in after_nonwatch["rows"])
    before_d = frozen_digests(am)
    before_tx = ledger_tx_ids(led)
    before_pools = pool_balances(led)
    bad_codes = [demand_code(am, v) for v in
                 (None, "", "infra:x", "dana", "usr")]
    after_d = frozen_digests(am)
    ok4 = (frank["listing_count"] == 1
           and frank["rows"][0]["listing_id"] == d3
           and frank["rows"][0]["watcher_count"] == 1
           and frank["rows"][0]["converted_count"] == 0
           and d3 not in [r["listing_id"] for r in after_nonwatch["rows"]]
           and dana_keys == {"risk-scan", "macro-feed", "quiet-api"}
           and empty["listing_count"] == 0 and empty["rows"] == []
           and empty["total_watchers"] == 0
           and empty["disclaimer"] == DISCLAIMER
           and bad_codes == ["E_AM_BAD_ACCOUNT"] * 5
           and before_d == after_d
           and ledger_tx_ids(led) == before_tx
           and pool_balances(led) == before_pools)
    record("AC-AMDM4", ok4,
           "frank=%r dana_keys=%r empty=%r bad=%r digests=%r"
           % ([(r["listing_id"], r["watcher_count"])
               for r in frank["rows"]], sorted(dana_keys),
              (empty["listing_count"], empty["rows"]), bad_codes,
              before_d == after_d))

    # -- AC-AMDM5 retirement + derived seams -----------------------------
    am.delist_api("usr:dana", d2)
    after_delist = am.api_listing_demand("usr:dana")
    am.revise_price("usr:dana", d1, 20)
    am.edit_listing("usr:dana", d1, title="Risk Scan API v2")
    after_move = am.api_listing_demand("usr:dana")
    row_d2 = row_of(after_delist, d2)
    row_d1c = row_of(after_move, d1)
    view_d1 = am.api_view(d1)
    ok5 = (row_d2 is not None
           and row_d2["delisted"] is True
           and row_d2["delisted_utc"] == "2026-10-06T00:00:20Z"
           and row_d2["watcher_count"] == 1
           and after_delist["listing_count"] == 3
           and row_d1c["current_price"] == 20
           and row_d1c["title"] == "Risk Scan API v2"
           and view_d1["token_price"] == 20
           and view_d1["title"] == "Risk Scan API v2")
    record("AC-AMDM5", ok5,
           "retired=%r stamp=%r watchers=%d price=%r title=%r"
           % (row_d2["delisted"], row_d2["delisted_utc"],
              row_d2["watcher_count"], row_d1c["current_price"],
              row_d1c["title"]))

    # -- AC-AMDM6 pure read ----------------------------------------------
    before6 = frozen_digests(am)
    before_tx6 = ledger_tx_ids(led)
    before_pools6 = pool_balances(led)
    runs = [dumps(am.api_listing_demand("usr:dana")) for _ in range(3)]
    after6 = frozen_digests(am)
    ok6 = (len(set(runs)) == 1
           and before6 == after6
           and ledger_tx_ids(led) == before_tx6
           and pool_balances(led) == before_pools6)
    record("AC-AMDM6", ok6,
           "three identical=%r digests=%r tx=%r pools=%r"
           % (len(set(runs)) == 1, before6 == after6,
              ledger_tx_ids(led) == before_tx6,
              pool_balances(led) == before_pools6))

    baseline = runs[0]
    close_stack(am, dk, metered, led)

    # -- AC-AMDM7 cross-restart byte identity ----------------------------
    replays = []
    for _ in range(2):
        led2, metered2, dk2, gate2, am2 = build_stack(
            db_path, cfg, lobby_cfg)
        replays.append(dumps(am2.api_listing_demand("usr:dana")))
        replays.append(dumps(am2.api_listing_demand("usr:frank")))
        close_stack(am2, dk2, metered2, led2)
    ok7 = (replays[0] == baseline
           and replays[2] == baseline
           and replays[0] == replays[2]
           and replays[1] == replays[3]
           and json.loads(baseline)["disclaimer"] == DISCLAIMER)
    record("AC-AMDM7", ok7,
           "dana identical twice=%r frank identical=%r disclaimer=%r"
           % (replays[0] == replays[2], replays[1] == replays[3],
              json.loads(baseline)["disclaimer"] == DISCLAIMER))

    # -- shipped files unchanged (part of the AC-AMDM8 delivery law) -----
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    shipped_same = (shas_after[PRODUCT_FILES[4]]
                    == shas_before[PRODUCT_FILES[4]]
                    and shas_after[PRODUCT_FILES[5]]
                    == shas_before[PRODUCT_FILES[5]])
    if not shipped_same:
        record("AC-AMDM8-shipped", False,
               "shipped config.json changed on disk")

    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("\nSUITE %s %d/%d" % ("PASS" if passed == len(RESULTS)
                                else "FAIL", passed, len(RESULTS)),
          flush=True)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())