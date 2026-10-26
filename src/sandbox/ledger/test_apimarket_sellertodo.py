"""Acceptance suite for the apimarket seller unified duty queue
(BigDomain R2138; canon = the explore-queue row seeded and claimed in
R2138, criteria AC-AMTD1..AC-AMTD8 registered in that claim row BEFORE
this code existed - honesty law; the AC-AMTD prefix, the
api_seller_todo name, this suite name and the
ledger-apimarket-sellertodo runner label were all git-grep -F
zero-occupancy anchored 2026-10-26, rc=1).

Face under proof: APIMarketFace.api_seller_todo. Every seller
obligation already had its own face - api_seller_inbox carries
unanswered ratings, api_seller_questions unanswered questions,
api_claims the queue the seller must filter by hand, and the R2137
disputed state lived only inside one claim thread - so a seller
holding N listings had to open four faces and merge them by hand.
This window pins the merged queue:

  - an eleven-key envelope and an eight-key row across four families
    (rating, question, claim_open, claim_disputed);
  - the four family definitions against their source tables;
  - claim status derived through the api_claims precedence, so a
    refund or a withdrawal drains the queue and an answered claim
    with no follow-up note stays out (the ball is with the buyer);
  - the pinned total order (since_utc, kind_rank, ref_id) with
    rating < question < claim_open < claim_disputed;
  - seller isolation, an honest empty envelope and retirement not
    erasing a debt;
  - the account shape gate before any read with frozen digests;
  - pure read plus six life-cycle actions that each drain or rewrite
    exactly one row without ever adding one;
  - cross-restart byte identity and runner wiring.

Usage: python test_apimarket_sellertodo.py
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

ENVELOPE_KEYS = {"dev_account", "total_count", "rating_count",
                 "question_count", "claim_open_count",
                 "claim_disputed_count", "listing_count",
                 "oldest_utc", "oldest_kind", "rows", "disclaimer"}
ROW_KEYS = {"kind", "ref_id", "listing_id", "listing_key",
            "listing_title", "counterparty", "since_utc", "detail"}

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
    return {acc: dumps(am.api_seller_todo(acc)) for acc in accounts}


def todo_code(am, account):
    try:
        am.api_seller_todo(account)
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
    """dana owns d1 (price 10) and d2 (price 3); frank a SECOND
    registered developer owning d3 (price 5) - the isolation anchor.

    Debts seeded for dana (all stamps pinned so the order is
    reproducible):
      claim_open      c1 opened 01Z
      question        q1 asked 03Z
      rating          r1 rated 05Z
      question        q3 asked 05Z   (same second as r1: rank tie-break)
      rating          r3 rated 07Z
      claim_open      c6 opened 08Z
      claim_disputed  c2 opened 06Z, answered 06:30Z, note 09Z
    Settled and therefore ABSENT from the queue:
      rating r2 (answered), question q2 (answered),
      claim c4 (answered, no note - the ball is with the buyer).
    """
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMTD-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMTD-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3,
                        False)["listing_id"]
    d3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 5,
                        False)["listing_id"]
    p_bob_d1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")[
        "purchase_id"]
    p_carol_d1 = am.purchase_api("usr:carol", d1, "ref-carol-d1")[
        "purchase_id"]
    p_erin_d2 = am.purchase_api("usr:erin", d2, "ref-erin-d2")[
        "purchase_id"]
    p_dave_d3 = am.purchase_api("usr:dave", d3, "ref-dave-d3")[
        "purchase_id"]
    p_erin_d1 = am.purchase_api("usr:erin", d1, "ref-erin-d1")[
        "purchase_id"]

    clock.value = "2026-10-05T00:00:05Z"
    r1 = am.rate_api("usr:bob", d1, 5)["rating_id"]
    clock.value = "2026-10-05T00:00:02Z"
    r2 = am.rate_api("usr:carol", d1, 3)["rating_id"]
    clock.value = "2026-10-05T00:00:07Z"
    r3 = am.rate_api("usr:erin", d2, 4)["rating_id"]
    clock.value = "2026-10-05T00:00:00Z"
    r4 = am.rate_api("usr:dave", d3, 4)["rating_id"]
    am.reply_to_rating("usr:dana", r2, "thanks carol")
    am.reply_to_rating("usr:frank", r4, "thanks dave")

    clock.value = "2026-10-05T00:00:03Z"
    q1 = am.ask_question("usr:bob", d1, "does this cover bonds?")[
        "question_id"]
    clock.value = "2026-10-05T00:00:04Z"
    q2 = am.ask_question("usr:erin", d2, "how fresh is the feed?")[
        "question_id"]
    clock.value = "2026-10-05T00:00:05Z"
    q3 = am.ask_question("usr:bob", d1, "is there a sandbox key?")[
        "question_id"]
    am.answer_question("usr:dana", q2, "refreshed every five minutes")

    clock.value = "2026-10-05T00:00:01Z"
    c1 = am.open_claim("usr:bob", p_bob_d1, "scan returns 500")[
        "claim_id"]
    clock.value = "2026-10-05T00:00:06Z"
    c2 = am.open_claim("usr:carol", p_carol_d1,
                       "results look stale")["claim_id"]
    clock.value = "2026-10-05T00:00:00Z"
    c3 = am.open_claim("usr:dave", p_dave_d3, "chart is blank")[
        "claim_id"]
    clock.value = "2026-10-05T00:00:04Z"
    c4 = am.open_claim("usr:erin", p_erin_d2, "feed stopped")[
        "claim_id"]
    clock.value = "2026-10-05T00:00:08Z"
    c6 = am.open_claim("usr:erin", p_erin_d1,
                       "wrong payload shape")["claim_id"]
    clock.value = "2026-10-05T00:00:06Z"
    am.respond_claim("usr:dana", c2, "the cache window is one hour")
    clock.value = "2026-10-05T00:00:09Z"
    am.add_claim_note("usr:carol", c2, "one hour is too stale for me")
    clock.value = "2026-10-05T00:00:04Z"
    am.respond_claim("usr:dana", c4, "restarted the feeder")
    clock.value = "2026-10-05T00:00:09Z"
    return {"d1": d1, "d2": d2, "d3": d3,
            "r1": r1, "r2": r2, "r3": r3, "r4": r4,
            "q1": q1, "q2": q2, "q3": q3,
            "c1": c1, "c2": c2, "c3": c3, "c4": c4, "c6": c6,
            "p_bob_d1": p_bob_d1, "p_carol_d1": p_carol_d1,
            "p_erin_d1": p_erin_d1, "p_erin_d2": p_erin_d2}


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-sellertodo-")
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
    d1, d2, d3 = ids["d1"], ids["d2"], ids["d3"]

    # -- AC-AMTD1 envelope + row contract -------------------------------
    env = am.api_seller_todo("usr:dana")
    rows = env["rows"]
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["dev_account"] == "usr:dana"
           and env["total_count"] == len(rows) == 7
           and env["rating_count"] == 2
           and env["question_count"] == 2
           and env["claim_open_count"] == 2
           and env["claim_disputed_count"] == 1
           and env["rating_count"] + env["question_count"]
           + env["claim_open_count"] + env["claim_disputed_count"]
           == env["total_count"]
           and env["listing_count"] == 2
           and env["listing_count"] == len({r["listing_id"]
                                            for r in rows})
           and env["oldest_utc"] == "2026-10-05T00:00:01Z"
           and env["oldest_kind"] == "claim_open"
           and env["disclaimer"] == DISCLAIMER
           and all(set(r.keys()) == ROW_KEYS for r in rows))
    record("AC-AMTD1", ok1,
           "envelope ok=%r total=%d r=%d q=%d co=%d cd=%d"
           " listings=%d oldest=%r/%r"
           % (set(env.keys()) == ENVELOPE_KEYS, env["total_count"],
              env["rating_count"], env["question_count"],
              env["claim_open_count"], env["claim_disputed_count"],
              env["listing_count"], env["oldest_utc"],
              env["oldest_kind"]))

    # -- AC-AMTD2 the four family definitions ---------------------------
    by = {(r["kind"], r["ref_id"]): r for r in rows}
    r1_row = by.get(("rating", ids["r1"]))
    q1_row = by.get(("question", ids["q1"]))
    c1_row = by.get(("claim_open", ids["c1"]))
    c2_row = by.get(("claim_disputed", ids["c2"]))
    ok2 = (r1_row is not None and q1_row is not None
           and c1_row is not None and c2_row is not None
           and r1_row["counterparty"] == "usr:bob"
           and r1_row["since_utc"] == "2026-10-05T00:00:05Z"
           and r1_row["detail"] is None
           and r1_row["listing_id"] == d1
           and r1_row["listing_key"] == "risk-scan"
           and r1_row["listing_title"] == "Risk Scan API"
           and q1_row["counterparty"] == "usr:bob"
           and q1_row["since_utc"] == "2026-10-05T00:00:03Z"
           and q1_row["detail"] == "does this cover bonds?"
           and c1_row["counterparty"] == "usr:bob"
           and c1_row["since_utc"] == "2026-10-05T00:00:01Z"
           and c1_row["detail"] == "scan returns 500"
           and c2_row["counterparty"] == "usr:carol"
           and c2_row["since_utc"] == "2026-10-05T00:00:09Z"
           and c2_row["detail"] == "one hour is too stale for me"
           and set(by.keys()) == {("rating", ids["r1"]),
                                  ("rating", ids["r3"]),
                                  ("question", ids["q1"]),
                                  ("question", ids["q3"]),
                                  ("claim_open", ids["c1"]),
                                  ("claim_open", ids["c6"]),
                                  ("claim_disputed", ids["c2"])})
    record("AC-AMTD2", ok2,
           "rating=%r question=%r claim_open=%r disputed=%r"
           " family-set=%d"
           % (bool(r1_row), bool(q1_row), bool(c1_row),
              bool(c2_row), len(by)))

    # -- AC-AMTD3 claim status derived through the api_claims seam ------
    claims = am.api_claims(dev_account="usr:dana")
    status = {c["claim_id"]: c["status"] for c in claims["claims"]}
    present = {r["ref_id"] for r in rows
               if r["kind"].startswith("claim")}
    withdrew = am.withdraw_claim("usr:erin", ids["c4"])
    claims2 = am.api_claims(dev_account="usr:dana")
    status2 = {c["claim_id"]: c["status"] for c in claims2["claims"]}
    env3 = am.api_seller_todo("usr:dana")
    present3 = {r["ref_id"] for r in env3["rows"]
                if r["kind"].startswith("claim")}
    ok3 = (status[ids["c1"]] == "open"
           and status[ids["c2"]] == "answered"
           and status[ids["c4"]] == "answered"
           and status[ids["c6"]] == "open"
           and present == {ids["c1"], ids["c2"], ids["c6"]}
           and ids["c4"] not in present
           and withdrew["claim_id"] == ids["c4"]
           and status2[ids["c4"]] == "withdrawn"
           and present3 == present
           and env3["total_count"] == 7)
    record("AC-AMTD3", ok3,
           "statuses=%r queue-claims=%r answered-no-note-excluded=%r"
           " withdrawn-still-excluded=%r"
           % (sorted(status.items()), sorted(present),
              ids["c4"] not in present, ids["c4"] not in present3))

    # -- AC-AMTD4 pinned total order ------------------------------------
    seq = [(r["since_utc"], r["kind"], r["ref_id"]) for r in rows]
    expect = [("2026-10-05T00:00:01Z", "claim_open", ids["c1"]),
              ("2026-10-05T00:00:03Z", "question", ids["q1"]),
              ("2026-10-05T00:00:05Z", "rating", ids["r1"]),
              ("2026-10-05T00:00:05Z", "question", ids["q3"]),
              ("2026-10-05T00:00:07Z", "rating", ids["r3"]),
              ("2026-10-05T00:00:08Z", "claim_open", ids["c6"]),
              ("2026-10-05T00:00:09Z", "claim_disputed", ids["c2"])]
    again = am.api_seller_todo("usr:dana")
    ok4 = (seq == expect
           and dumps(again) == dumps(env)
           and [r["kind"] for r in again["rows"]]
           == [k for _s, k, _r in expect])
    record("AC-AMTD4", ok4,
           "sequence=%r identical-repeat=%r"
           % ([(s, k) for s, k, _r in seq], dumps(again) == dumps(env)))

    # -- AC-AMTD5 isolation, honest empty, retirement keeps the debt ----
    am.delist_api("usr:dana", d2)
    retired = am.api_seller_todo("usr:dana")
    r3_row = [r for r in retired["rows"]
              if r["kind"] == "rating" and r["ref_id"] == ids["r3"]][0]
    frank_env = am.api_seller_todo("usr:frank")
    empty_env = am.api_seller_todo("usr:nobody")
    dana_refs = {(r["kind"], r["ref_id"]) for r in retired["rows"]}
    ok5 = (retired["total_count"] == 7
           and r3_row["listing_id"] == d2
           and r3_row["listing_key"] == "macro-feed"
           and r3_row["listing_title"] == "Macro Feed API"
           and set(frank_env.keys()) == ENVELOPE_KEYS
           and frank_env["total_count"] == 1
           and frank_env["claim_open_count"] == 1
           and [r["ref_id"] for r in frank_env["rows"]] == [ids["c3"]]
           and all(r["listing_id"] == d3 for r in frank_env["rows"])
           and not ({(r["kind"], r["ref_id"])
                     for r in frank_env["rows"]} & dana_refs)
           and empty_env["rows"] == []
           and empty_env["total_count"] == 0
           and empty_env["rating_count"] == 0
           and empty_env["question_count"] == 0
           and empty_env["claim_open_count"] == 0
           and empty_env["claim_disputed_count"] == 0
           and empty_env["listing_count"] == 0
           and empty_env["oldest_utc"] is None
           and empty_env["oldest_kind"] is None
           and empty_env["disclaimer"] == DISCLAIMER)
    record("AC-AMTD5", ok5,
           "retired-debt-kept=%r frank=%d empty=%r isolated=%r"
           % (r3_row["listing_key"] == "macro-feed",
              frank_env["total_count"], empty_env["rows"],
              not ({(r["kind"], r["ref_id"])
                    for r in frank_env["rows"]} & dana_refs)))

    # -- AC-AMTD6 account gate family, fail-closed ----------------------
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
    record("AC-AMTD6", ok6,
           "bad-codes=%r blank=%r tables-frozen=%r ledger-frozen=%r"
           % (sorted(set(bad_codes)), blank_code,
              frozen_before == frozen_after,
              tx_before == ledger_tx_ids(led)))

    # -- AC-AMTD7 pure read + six life-cycle actions --------------------
    tx0 = ledger_tx_ids(led)
    pools0 = pool_balances(led)
    digests0 = frozen_digests(am)
    first = dumps(am.api_seller_todo("usr:dana"))
    second = dumps(am.api_seller_todo("usr:dana"))
    pure_ok = (tx0 == ledger_tx_ids(led)
               and pools0 == pool_balances(led)
               and digests0 == frozen_digests(am)
               and first == second)
    am.reply_to_rating("usr:dana", ids["r1"], "thanks bob")
    step1 = am.api_seller_todo("usr:dana")
    am.answer_question("usr:dana", ids["q1"], "yes, bond sleeve too")
    step2 = am.api_seller_todo("usr:dana")
    am.respond_claim("usr:dana", ids["c1"], "rolled back the deploy")
    step3 = am.api_seller_todo("usr:dana")
    clock.value = "2026-10-05T00:00:10Z"
    am.add_claim_note("usr:bob", ids["c1"], "still failing today")
    step4 = am.api_seller_todo("usr:dana")
    am.refund_api("usr:erin", ids["p_erin_d1"], "payload mismatch")
    step5 = am.api_seller_todo("usr:dana")
    am.withdraw_claim("usr:carol", ids["c2"])
    step6 = am.api_seller_todo("usr:dana")
    ok7 = (pure_ok
           and step1["rating_count"] == 1
           and step1["total_count"] == 6
           and step2["question_count"] == 1
           and step2["total_count"] == 5
           and step3["claim_open_count"] == 1
           and step3["total_count"] == 4
           and step4["claim_disputed_count"] == 2
           and step4["total_count"] == 5
           and step4["claim_open_count"] == 1
           and step5["claim_open_count"] == 0
           and step5["total_count"] == 4
           and step6["claim_disputed_count"] == 1
           and step6["total_count"] == 3
           and [r["kind"] for r in step6["rows"]]
           == ["question", "rating", "claim_disputed"]
           and step6["oldest_utc"] == "2026-10-05T00:00:05Z"
           and step6["listing_count"] == 2
           and step4["rows"][-1]["ref_id"] == ids["c1"]
           and step4["rows"][-1]["since_utc"]
           == "2026-10-05T00:00:10Z")
    record("AC-AMTD7", ok7,
           "pure-read=%r drain-steps=%r final=%r kinds=%r"
           % (pure_ok,
              [step1["total_count"], step2["total_count"],
               step3["total_count"], step4["total_count"],
               step5["total_count"], step6["total_count"]],
              step6["total_count"],
              [r["kind"] for r in step6["rows"]]))

    # -- AC-AMTD8 cross-restart identity + wiring + hygiene -------------
    accounts = ("usr:dana", "usr:frank", "usr:nobody")
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
        wired = b"ledger-apimarket-sellertodo" in handle.read()
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
    record("AC-AMTD8", ok8,
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