"""Acceptance suite for the apimarket buyer post-sale decision queue
(BigDomain R2140; canon = the explore-queue row seeded and claimed in
R2140, criteria AC-AMBC1..AC-AMBC8 registered in that claim row BEFORE
this code existed - honesty law; the AC-AMBC prefix, the
api_buyer_claim_todo name, this suite name and the
ledger-apimarket-buyerclaimtodo runner label were all git-grep -F
zero-occupancy anchored 2026-10-26, rc=1).

Face under proof: APIMarketFace.api_buyer_claim_todo. The claim thread
became two-way across R2129 (open), R2130 (one seller answer), R2131
(withdraw) and R2137 (buyer follow-up note), but the ball only changed
hands silently: R2138 had to say out loud that an answered claim with
no note stays out of the SELLER queue "because the ball is with the
buyer", and nothing told the buyer the ball had arrived. This suite
pins the buyer-side counterpart:

  - an eleven-key envelope and a ten-key row;
  - the five disjoint states with pinned precedence
    refunded > withdrawn > disputed > needs_decision > waiting, and
    the partition identity over the five counters;
  - only needs_decision rows enter the queue (the buyer's real debt);
  - the total order (opened_utc, claim_id) with oldest first and a
    same-second tie broken by id;
  - buyer isolation, an honest empty envelope, retirement keeping the
    debt and price_paid staying the stored purchase amount;
  - the prefix-only account gate before any read with frozen digests;
  - pure read plus four life-cycle acts that each push into or drain
    out of the queue without rewriting a single stored row;
  - cross-restart byte identity and runner wiring.

Usage: python test_apimarket_buyerclaimtodo.py
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

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

ENVELOPE_KEYS = {"buyer_id", "claim_count", "needs_decision_count",
                 "waiting_count", "disputed_count", "refunded_count",
                 "withdrawn_count", "oldest_needs_decision_utc",
                 "oldest_waiting_utc", "disclaimer", "claims"}
ROW_KEYS = {"claim_id", "purchase_id", "listing_id", "listing_title",
            "dev_account", "price_paid", "claim_text", "opened_utc",
            "response_text", "responded_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_claims",
          "apimarket_claim_responses", "apimarket_claim_withdrawals",
          "apimarket_claim_notes", "apimarket_provider_identities")
POOLS = ("pool:reserve", "pool:share")


class Clock(object):
    """Deterministic stamp holder (module clock patched, restored in
    main's finally block)."""

    def __init__(self):
        self.value = "2026-10-05T00:00:00Z"

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
    try:
        rows = conn.execute(
            "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    except sqlite3.OperationalError:
        return (-1, "ABSENT")
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


def todo_family(am, accounts):
    return {acc: dumps(am.api_buyer_claim_todo(acc)) for acc in accounts}


def todo_code(am, account):
    try:
        am.api_buyer_claim_todo(account)
    except A.ApiMarketError as exc:
        return getattr(exc, "code", None)
    return "NO-RAISE"


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


def seed_world(led, dk, am, clock):
    """dana owns seven listings; bob buys one of each so he holds six
    claims in every state plus one same-second tie. carol owns a claim
    of her own (the isolation anchor).

    bob's claims (all stamps pinned so the order is reproducible):
      b1 on d1  opened 01Z, answered 02Z   -> needs_decision
      b2 on d2  opened 03Z, answered 03Z   -> needs_decision (tie, low id)
      b7 on d7  opened 03Z, answered 03Z   -> needs_decision (tie, high id)
      b3 on d3  opened 04Z, answered 05Z, refunded 06Z -> refunded
      b4 on d4  opened 07Z, withdrawn 08Z  -> withdrawn
      b5 on d5  opened 09Z, answered 10Z, noted 11Z -> disputed
      b6 on d6  opened 12Z                 -> waiting
    """
    led.mint_to_pool("pool:reserve", 90000, "SETTLE-AMBC-A",
                     "settlement")
    led.mint_to_pool("pool:share", 90000, "SETTLE-AMBC-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 4000),
                    ("usr:" + who, "credit", 4000)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    listings = []
    spec = [("risk-scan", "Risk Scan API", 10),
            ("macro-feed", "Macro Feed API", 3),
            ("chart-render", "Chart Render API", 5),
            ("news-digest", "News Digest API", 7),
            ("greek-engine", "Greek Engine API", 2),
            ("bond-sleeve", "Bond Sleeve API", 4),
            ("factor-lab", "Factor Lab API", 6)]
    for key, title, price in spec:
        listings.append(am.publish_api(
            "usr:dana", key, title, "endpoint for " + key, PAYLOAD,
            price, False)["listing_id"])
    d1, d2, d3, d4, d5, d6, d7 = listings
    buys = {}
    for idx, lid in enumerate(listings):
        buys[lid] = am.purchase_api(
            "usr:bob", lid, "ref-bob-%d" % idx)["purchase_id"]
    p_carol = am.purchase_api("usr:carol", d1, "ref-carol-d1")[
        "purchase_id"]

    claims = {}
    clock.value = "2026-10-05T00:00:01Z"
    claims["b1"] = am.open_claim("usr:bob", buys[d1],
                                 "scan returns 500")["claim_id"]
    clock.value = "2026-10-05T00:00:03Z"
    claims["b2"] = am.open_claim("usr:bob", buys[d2],
                                 "feed looks stale")["claim_id"]
    claims["b7"] = am.open_claim("usr:bob", buys[d7],
                                 "factors disagree")["claim_id"]
    clock.value = "2026-10-05T00:00:04Z"
    claims["b3"] = am.open_claim("usr:bob", buys[d3],
                                 "chart is blank")["claim_id"]
    clock.value = "2026-10-05T00:00:07Z"
    claims["b4"] = am.open_claim("usr:bob", buys[d4],
                                 "digest truncated")["claim_id"]
    clock.value = "2026-10-05T00:00:09Z"
    claims["b5"] = am.open_claim("usr:bob", buys[d5],
                                 "unpriced greeks")["claim_id"]
    clock.value = "2026-10-05T00:00:12Z"
    claims["b6"] = am.open_claim("usr:bob", buys[d6],
                                 "bond list missing")["claim_id"]
    clock.value = "2026-10-05T00:00:00Z"
    claims["c_carol"] = am.open_claim("usr:carol", p_carol,
                                      "carol says stale")["claim_id"]

    # seller answers (b1, b2, b7 answered with no note -> the ball is
    # with the buyer; b3 answered then refunded; b5 answered then the
    # buyer pushed back).
    clock.value = "2026-10-05T00:00:02Z"
    am.respond_claim("usr:dana", claims["b1"], "rolled back the deploy")
    clock.value = "2026-10-05T00:00:03Z"
    am.respond_claim("usr:dana", claims["b2"],
                     "cache window is five minutes")
    am.respond_claim("usr:dana", claims["b7"], "rerun the factor job")
    clock.value = "2026-10-05T00:00:05Z"
    am.respond_claim("usr:dana", claims["b3"], "render worker restarted")
    clock.value = "2026-10-05T00:00:10Z"
    am.respond_claim("usr:dana", claims["b5"], "greeks are on request")
    clock.value = "2026-10-05T00:00:06Z"
    am.refund_api("usr:bob", buys[d3], "blank chart")
    clock.value = "2026-10-05T00:00:08Z"
    am.withdraw_claim("usr:bob", claims["b4"])
    clock.value = "2026-10-05T00:00:11Z"
    am.add_claim_note("usr:bob", claims["b5"],
                      "on request is not what the listing says")
    clock.value = "2026-10-05T00:00:12Z"
    return {"listings": listings, "buys": buys,
            "carol_purchase": p_carol, "claims": claims}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-buyerclaimtodo-")
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
    ids = seed_world(led, dk, am, clock)
    claims = ids["claims"]
    d1, d2, d3, d4, d5, d6, d7 = ids["listings"]
    buys = ids["buys"]

    # -- AC-AMBC1 envelope + row contract -------------------------------
    env = am.api_buyer_claim_todo("usr:bob")
    rows = env["claims"]
    sum_counts = (env["needs_decision_count"] + env["waiting_count"]
                  + env["disputed_count"] + env["refunded_count"]
                  + env["withdrawn_count"])
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["buyer_id"] == "usr:bob"
           and env["claim_count"] == 7
           and len(rows) == 3
           and env["needs_decision_count"] == 3
           and env["waiting_count"] == 1
           and env["disputed_count"] == 1
           and env["refunded_count"] == 1
           and env["withdrawn_count"] == 1
           and env["claim_count"] == sum_counts == 7
           and env["oldest_needs_decision_utc"] == "2026-10-05T00:00:01Z"
           and env["oldest_needs_decision_utc"] == rows[0]["opened_utc"]
           and env["oldest_waiting_utc"] == "2026-10-05T00:00:12Z"
           and env["disclaimer"] == DISCLAIMER
           and all(set(r.keys()) == ROW_KEYS for r in rows))
    record("AC-AMBC1", ok1,
           "envelope-keys=%r rows=%d need=%d wait=%d disp=%d"
           " ref=%d wd=%d oldest=%r"
           % (set(env.keys()) == ENVELOPE_KEYS, len(rows),
              env["needs_decision_count"], env["waiting_count"],
              env["disputed_count"], env["refunded_count"],
              env["withdrawn_count"], env["oldest_needs_decision_utc"]))

    # -- AC-AMBC2 five disjoint states, pinned precedence ----------------
    api = am.api_claims(buyer_id="usr:bob")
    status = {c["claim_id"]: c["status"] for c in api["claims"]}
    queued = {r["claim_id"] for r in rows}
    expect_status = {claims["b1"]: "answered",
                     claims["b2"]: "answered",
                     claims["b7"]: "answered",
                     claims["b3"]: "refunded",
                     claims["b4"]: "withdrawn",
                     claims["b5"]: "answered",
                     claims["b6"]: "open"}
    expect_queue = {claims["b1"], claims["b2"], claims["b7"]}
    ok2 = (status == expect_status
           and queued == expect_queue
           and api["claim_count"] == 7
           and api["refunded_count"] == 1
           and api["withdrawn_count"] == 1
           and api["answered_count"] == 4
           and api["open_count"] == 1
           and claims["b5"] not in queued
           and claims["b6"] not in queued
           and claims["b3"] not in queued
           and claims["b4"] not in queued
           and all(r["response_text"] is not None for r in rows)
           and all(r["responded_utc"] is not None for r in rows))
    record("AC-AMBC2", ok2,
           "api-status=%r queue=%r refunded-excluded=%r"
           " withdrawn-excluded=%r disputed-excluded=%r"
           % (sorted(status.items()), sorted(queued),
              claims["b3"] not in queued, claims["b4"] not in queued,
              claims["b5"] not in queued))

    # -- AC-AMBC3 pushed, never stored: rows are the live derivation ----
    b1_row = [r for r in rows if r["claim_id"] == claims["b1"]][0]
    ok3 = (b1_row["purchase_id"] == buys[d1]
           and b1_row["listing_id"] == d1
           and b1_row["listing_title"] == "Risk Scan API"
           and b1_row["dev_account"] == "usr:dana"
           and b1_row["price_paid"] == 10
           and b1_row["claim_text"] == "scan returns 500"
           and b1_row["response_text"] == "rolled back the deploy"
           and b1_row["responded_utc"] == "2026-10-05T00:00:02Z"
           and [r["claim_id"] for r in rows]
           == [claims["b1"], claims["b2"], claims["b7"]])
    record("AC-AMBC3", ok3,
           "row=%r order=%r"
           % ({k: b1_row[k] for k in ("listing_title", "price_paid",
                                      "claim_text", "response_text")},
              [r["claim_id"] for r in rows]))

    # -- AC-AMBC4 total order incl. same-second tie, determinism --------
    seq = [(r["opened_utc"], r["claim_id"]) for r in rows]
    expect = [("2026-10-05T00:00:01Z", claims["b1"]),
              ("2026-10-05T00:00:03Z", claims["b2"]),
              ("2026-10-05T00:00:03Z", claims["b7"])]
    again = am.api_buyer_claim_todo("usr:bob")
    tie_ordered = claims["b2"] < claims["b7"]
    ok4 = (seq == expect and tie_ordered and dumps(again) == dumps(env)
           and [r["claim_id"] for r in again["claims"]]
           == [c for _s, c in expect])
    record("AC-AMBC4", ok4,
           "sequence=%r identical-repeat=%r tie-by-id=%r"
           % (seq, dumps(again) == dumps(env), tie_ordered))

    # -- AC-AMBC5 isolation, honest empty, retirement, stored price -----
    clock.value = "2026-10-05T00:00:20Z"
    am.revise_price("usr:dana", d7, 60)
    am.delist_api("usr:dana", d7)
    retired = am.api_buyer_claim_todo("usr:bob")
    b7_row = [r for r in retired["claims"]
              if r["claim_id"] == claims["b7"]][0]
    carol_env = am.api_buyer_claim_todo("usr:carol")
    empty_env = am.api_buyer_claim_todo("usr:nobody")
    bob_ids = {r["claim_id"] for r in retired["claims"]}
    ok5 = (retired["needs_decision_count"] == 3
           and b7_row["listing_id"] == d7
           and b7_row["listing_title"] == "Factor Lab API"
           and b7_row["price_paid"] == 6
           and carol_env["claim_count"] == 1
           and carol_env["waiting_count"] == 1
           and carol_env["needs_decision_count"] == 0
           and carol_env["claims"] == []
           and carol_env["oldest_waiting_utc"] == "2026-10-05T00:00:00Z"
           and {c["claim_id"] for c in am.api_claims(
               buyer_id="usr:carol")["claims"]} == {claims["c_carol"]}
           and claims["c_carol"] not in bob_ids
           and empty_env["claims"] == []
           and empty_env["claim_count"] == 0
           and empty_env["needs_decision_count"] == 0
           and empty_env["waiting_count"] == 0
           and empty_env["disputed_count"] == 0
           and empty_env["refunded_count"] == 0
           and empty_env["withdrawn_count"] == 0
           and empty_env["oldest_needs_decision_utc"] is None
           and empty_env["oldest_waiting_utc"] is None
           and empty_env["disclaimer"] == DISCLAIMER)
    record("AC-AMBC5", ok5,
           "retired-kept=%r stored-price=%d carol=%d isolated=%r"
           " empty=%r"
           % (b7_row["listing_title"] == "Factor Lab API",
              b7_row["price_paid"], carol_env["claim_count"],
              claims["c_carol"] not in bob_ids, empty_env["claims"]))

    # -- AC-AMBC6 prefix-only account gate, fail-closed -----------------
    frozen_before = frozen_digests(am)
    tx_before = ledger_tx_ids(led)
    bad_codes = [todo_code(am, bad) for bad in
                 (None, "", "bob", 7, 1.5, True, [], {})]
    blank_code = todo_code(am, "   ")
    frozen_after = frozen_digests(am)
    ok6 = (bad_codes == [A.E_AM_BAD_ACCOUNT] * 8
           and blank_code == A.E_AM_BAD_ACCOUNT
           and frozen_before == frozen_after
           and tx_before == ledger_tx_ids(led))
    record("AC-AMBC6", ok6,
           "bad-codes=%r blank=%r tables-frozen=%r ledger-frozen=%r"
           % (sorted(set(bad_codes)), blank_code,
              frozen_before == frozen_after,
              tx_before == ledger_tx_ids(led)))

    # -- AC-AMBC7 pure read + four life-cycle pushes and drains ---------
    tx0 = ledger_tx_ids(led)
    pools0 = pool_balances(led)
    digests0 = frozen_digests(am)
    first = dumps(am.api_buyer_claim_todo("usr:bob"))
    second = dumps(am.api_buyer_claim_todo("usr:bob"))
    pure_ok = (tx0 == ledger_tx_ids(led)
               and pools0 == pool_balances(led)
               and digests0 == frozen_digests(am)
               and first == second)
    # answer lands -> waiting drains into needs_decision
    clock.value = "2026-10-05T00:00:30Z"
    am.respond_claim("usr:dana", claims["b6"], "listing fixed upstream")
    step1 = am.api_buyer_claim_todo("usr:bob")
    # buyer pushes back -> needs_decision drains into disputed
    am.add_claim_note("usr:bob", claims["b6"], "still missing entries")
    step2 = am.api_buyer_claim_todo("usr:bob")
    # refund lands after the answer -> needs_decision drains into refunded
    am.refund_api("usr:bob", buys[d2], "stale feed")
    step3 = am.api_buyer_claim_todo("usr:bob")
    # buyer withdraws -> needs_decision drains into withdrawn
    am.withdraw_claim("usr:bob", claims["b1"])
    step4 = am.api_buyer_claim_todo("usr:bob")
    ok7 = (pure_ok
           and step1["needs_decision_count"] == 4
           and step1["waiting_count"] == 0
           and step1["claim_count"] == 7
           and [r["claim_id"] for r in step1["claims"]][-1]
           == claims["b6"]
           and step2["needs_decision_count"] == 3
           and step2["disputed_count"] == 2
           and claims["b6"] not in {r["claim_id"]
                                    for r in step2["claims"]}
           and step3["needs_decision_count"] == 2
           and step3["refunded_count"] == 2
           and claims["b2"] not in {r["claim_id"]
                                    for r in step3["claims"]}
           and step4["needs_decision_count"] == 1
           and step4["withdrawn_count"] == 2
           and [r["claim_id"] for r in step4["claims"]] \
           == [claims["b7"]]
           and step4["oldest_needs_decision_utc"] \
           == "2026-10-05T00:00:03Z"
           and step4["claim_count"] \
           == (step4["needs_decision_count"] + step4["waiting_count"]
               + step4["disputed_count"] + step4["refunded_count"]
               + step4["withdrawn_count"]) == 7)
    record("AC-AMBC7", ok7,
           "pure-read=%r drains=%r final-queue=%r"
           % (pure_ok,
              [step1["needs_decision_count"],
               step2["needs_decision_count"],
               step3["needs_decision_count"],
               step4["needs_decision_count"]],
              [r["claim_id"] for r in step4["claims"]]))

    # -- AC-AMBC8 cross-restart identity + wiring + hygiene -------------
    accounts = ("usr:bob", "usr:carol", "usr:nobody")
    family_before = todo_family(am, accounts)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = todo_family(am2, accounts)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = todo_family(am3, accounts)
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-buyerclaimtodo" in handle.read()
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        blob = handle.read()
    ascii_ok = True
    try:
        blob.decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
    src = blob.decode("utf-8", "replace")
    net_imports = [line for line in src.splitlines()
                   if line.strip().startswith(("import requests",
                                               "import urllib",
                                               "import http"))]
    outside = not os.path.abspath(tmp).startswith(
        os.path.abspath(os.path.join(BASE, "..", "..", "..")))
    ok8 = (family_before == family_two == family_three
           and wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside)
    record("AC-AMBC8", ok8,
           "three-instances-identical=%r runner-wiring=%r"
           " consumer-shas-stable=%r ascii=%r network-imports=%d"
           " world-outside-repo=%r"
           % (family_before == family_two == family_three, wired,
              shas_before == shas_after, ascii_ok,
              len(net_imports), outside))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())