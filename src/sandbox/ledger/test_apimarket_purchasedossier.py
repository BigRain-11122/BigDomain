"""Acceptance suite for the single-purchase dossier (BigDomain R2135;
canon = the R2135 explore-queue row, criteria AC-AMPD1..AC-AMPD8
registered there BEFORE this code existed - honesty law; the AC-AMPD
prefix, api_purchase_dossier, E_AM_NOT_PARTY, ticket_state, this suite
name and the ledger-apimarket-purchasedossier runner label were all
git grep -F zero-occupancy anchored 2026-10-26, rc=1).

Product under proof: every existing apimarket face answers one corner
of a trade (api_library lists a buyer's purchases, api_refund returns
one refund row, api_claims returns the claim queue, the two ledger
statements return cash movements), so a support ticket or a settlement
dispute had to be assembled by hand from four faces. api_purchase_dossier
is that assembly behind one gate: the buyer of record and the seller of
record both see the whole story (and only they do).

Criteria:
  AC-AMPD1 Contract: the twenty-one key envelope, the integer split
    identity price_paid == dev_share + platform_share, the stored
    category echoed (and None for an uncategorized listing), the
    resident disclaimer verbatim.
  AC-AMPD2 Party authorization: the buyer answers viewer_role "buyer"
    and the seller "seller", the two dossiers byte-identical apart from
    that one key; a third party is refused with E_AM_NOT_PARTY and the
    digests stay frozen.
  AC-AMPD3 Honest nested absences: refund / rating / claim are None
    until their row exists, the refund block carries its seven keys
    with amount == price_paid, and the rating block carries the
    effective stars, the revision count and the newest revision stamp.
  AC-AMPD4 Claim status precedence: refunded beats withdrawn beats
    answered beats open, recomputed from the append-only tables.
  AC-AMPD5 ticket_state precedence: refunded > withdrawn > answered >
    open > rated > settled, one dossier per state on one world.
  AC-AMPD6 Gate family and order: five bad purchase-id forms answer
    E_AM_BAD_ARGS, four bad account forms answer E_AM_BAD_ACCOUNT, a
    bad account on an unknown purchase answers BAD_ACCOUNT (account
    before existence), a live account on an unknown purchase answers
    E_AM_UNKNOWN_PURCHASE, and all refusals leave twenty-one table
    digests frozen.
  AC-AMPD7 Pure read and history: repeat calls byte-identical, zero
    token movement, and a retired + repriced listing keeps its dossier
    with the retirement stamp, the live asking price and the
    historical price_paid unchanged.
  AC-AMPD8 Cross-restart identity + wiring: instance one, two and
    three byte-identical for the buyer view, the seller view and the
    refusal code set, and the runner label is registered.

Usage: python test_apimarket_purchasedossier.py
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

ENVELOPE_KEYS = {
    "purchase_id", "listing_id", "listing_key", "title", "category",
    "buyer_id", "dev_account", "viewer_role", "price_paid", "dev_share",
    "platform_share", "spend_tx", "purchased_utc", "current_price",
    "delisted", "delisted_utc", "refund", "rating", "claim",
    "ticket_state", "disclaimer"}

REFUND_KEYS = {"refund_id", "amount", "dev_share", "platform_share",
               "refund_tx", "refunded_utc", "reason"}

RATING_KEYS = {"rating_id", "stars", "revision_count", "revised_utc"}

CLAIM_KEYS = {"claim_id", "claim_text", "opened_utc", "status",
              "refund_id", "refunded_utc", "response_id",
              "response_text", "responded_utc", "withdrawn_utc"}

BAD_PURCHASE_IDS = ["1", True, 0, -3, None]

BAD_ACCOUNTS = ["", None, "   ", 123]

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers",
          "apimarket_reviews", "apimarket_review_resubmits",
          "apimarket_claims", "apimarket_claim_responses",
          "apimarket_claim_withdrawals")


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
    return len(rows), hashlib.sha256(
        repr(rows).encode("utf-8")).hexdigest()


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


def without_role(env):
    copy = dict(env)
    copy.pop("viewer_role", None)
    return dumps(copy)


def dossier_family(am, pairs, refusals):
    """Byte-stable snapshot of the dossier read family: every
    (purchase, account) pair plus the refusal code set."""
    out = {}
    for purchase_id, account in pairs:
        out["%d|%s" % (purchase_id, account)] = dumps(
            am.api_purchase_dossier(purchase_id, account))
    codes = []
    for purchase_id in refusals:
        try:
            am.api_purchase_dossier(purchase_id, "usr:nobody")
            codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            codes.append(getattr(exc, "code", None))
    out["refusals"] = codes
    return out


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


def seed_world(led, dk, am):
    """Owner dana with four listings; bob, carol and erin each buy;
    seven purchases exist so the six ticket states can each land on
    their own row (no shared mutable history)."""
    led.mint_to_pool("pool:reserve", 8000, "SETTLE-AMPD-A",
                     "settlement")
    led.mint_to_pool("pool:share", 8000, "SETTLE-AMPD-S",
                     "settlement")
    for who in ("bob", "carol", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="backtest")["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 4,
                        True, category="macro")["listing_id"]
    d3 = am.publish_api("usr:dana", "clean-scan", "Clean Scan API",
                        "clean data scan endpoint", PAYLOAD, 6,
                        False)["listing_id"]
    d4 = am.publish_api("usr:dana", "tool-kit", "Tool Kit API",
                        "toolbox endpoint", PAYLOAD, 8,
                        False, category="tools")["listing_id"]
    p = {}
    p[1] = am.purchase_api("usr:bob", d1, "ref-p1")["purchase_id"]
    p[2] = am.purchase_api("usr:carol", d1, "ref-p2")["purchase_id"]
    p[3] = am.purchase_api("usr:bob", d2, "ref-p3")["purchase_id"]
    p[4] = am.purchase_api("usr:erin", d2, "ref-p4")["purchase_id"]
    p[5] = am.purchase_api("usr:bob", d3, "ref-p5")["purchase_id"]
    p[6] = am.purchase_api("usr:erin", d3, "ref-p6")["purchase_id"]
    p[7] = am.purchase_api("usr:bob", d4, "ref-p7")["purchase_id"]
    return {"d1": d1, "d2": d2, "d3": d3, "d4": d4}, p


PAIRS = [(1, "usr:bob"), (1, "usr:dana"),
         (2, "usr:carol"), (3, "usr:bob"),
         (4, "usr:erin"), (5, "usr:bob"),
         (6, "usr:erin"), (7, "usr:bob")]


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-purchasedossier-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    lids, p = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)
    digests_before = market_digests(am)

    # -- AC-AMPD1 contract -----------------------------------------------
    d1 = am.api_purchase_dossier(p[1], "usr:bob")
    d3 = am.api_purchase_dossier(p[5], "usr:bob")
    d4 = am.api_purchase_dossier(p[7], "usr:bob")
    ok1 = (set(d1.keys()) == ENVELOPE_KEYS
           and d1["disclaimer"] == DISCLAIMER
           and d1["purchase_id"] == p[1]
           and d1["listing_id"] == lids["d1"]
           and d1["listing_key"] == "risk-scan"
           and d1["title"] == "Risk Scan API"
           and d1["category"] == "backtest"
           and d1["buyer_id"] == "usr:bob"
           and d1["dev_account"] == "usr:dana"
           and d1["price_paid"] == 10
           and d1["price_paid"] == (d1["dev_share"]
                                    + d1["platform_share"])
           and d1["spend_tx"] and d1["purchased_utc"]
           and d3["category"] is None
           and d4["category"] == "tools"
           and d4["price_paid"] == 8)
    record("AC-AMPD1", ok1,
           "keys=%r categories=%r split=%d+%d==%d"
           % (set(d1.keys()) == ENVELOPE_KEYS,
              [d1["category"], d3["category"], d4["category"]],
              d1["dev_share"], d1["platform_share"],
              d1["price_paid"]))

    # -- AC-AMPD2 party authorization ------------------------------------
    dig2 = market_digests(am)
    as_buyer = am.api_purchase_dossier(p[1], "usr:bob")
    as_seller = am.api_purchase_dossier(p[1], "usr:dana")
    third_codes = []
    for account in ("usr:carol", "usr:erin", "usr:dana-x"):
        try:
            am.api_purchase_dossier(p[1], account)
            third_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            third_codes.append(code_of(exc))
    dig2_after = market_digests(am)
    ok2 = (as_buyer["viewer_role"] == "buyer"
           and as_seller["viewer_role"] == "seller"
           and without_role(as_buyer) == without_role(as_seller)
           and third_codes == ["E_AM_NOT_PARTY"] * 3
           and dig2_after == dig2)
    record("AC-AMPD2", ok2,
           "roles=%r identical-apart-from-role=%r third parties=%r"
           " digests frozen=%r"
           % ((as_buyer["viewer_role"], as_seller["viewer_role"]),
              without_role(as_buyer) == without_role(as_seller),
              third_codes, dig2_after == dig2))

    # -- AC-AMPD3 honest nested absences --------------------------------
    fresh = am.api_purchase_dossier(p[1], "usr:bob")
    am.rate_api("usr:bob", lids["d1"], 5)
    rated = am.api_purchase_dossier(p[1], "usr:bob")
    rating_id = rated["rating"]["rating_id"]
    am.revise_rating("usr:bob", rating_id, 2)
    revised = am.api_purchase_dossier(p[1], "usr:bob")
    ok3 = (fresh["refund"] is None and fresh["rating"] is None
           and fresh["claim"] is None
           and set(rated["rating"].keys()) == RATING_KEYS
           and rated["rating"]["stars"] == 5
           and rated["rating"]["revision_count"] == 0
           and rated["rating"]["revised_utc"] is None
           and revised["rating"]["stars"] == 2
           and revised["rating"]["revision_count"] == 1
           and revised["rating"]["revised_utc"] is not None
           and revised["rating"]["rating_id"] == rating_id
           and revised["ticket_state"] == "rated")
    record("AC-AMPD3", ok3,
           "fresh trio=%r rated=%r revised stars=%r count=%r"
           " stamp=%r"
           % ((fresh["refund"], fresh["rating"], fresh["claim"]),
              rated["rating"]["stars"],
              revised["rating"]["stars"],
              revised["rating"]["revision_count"],
              revised["rating"]["revised_utc"] is not None))

    # -- AC-AMPD4 claim status precedence -------------------------------
    # p2: open -> answered -> refunded (refunded beats answered)
    c2 = am.open_claim("usr:carol", p[2],
                       "service never returned the promised scan")
    c2_open = am.api_purchase_dossier(p[2], "usr:carol")["claim"]
    am.respond_claim("usr:dana", c2["claim_id"],
                     "the scan endpoint is fixed, rerun please")
    c2_ans = am.api_purchase_dossier(p[2], "usr:carol")["claim"]
    am.refund_api("usr:carol", p[2], "claim settled in full")
    d2_dos = am.api_purchase_dossier(p[2], "usr:carol")
    # p5: withdrawn only
    c5 = am.open_claim("usr:bob", p[5], "key never activated")
    am.withdraw_claim("usr:bob", c5["claim_id"])
    c5_wd = am.api_purchase_dossier(p[5], "usr:bob")["claim"]
    # p6: withdrawn then refunded (refunded beats withdrawn)
    c6 = am.open_claim("usr:erin", p[6], "endpoint returns stale rows")
    am.withdraw_claim("usr:erin", c6["claim_id"])
    am.refund_api("usr:erin", p[6], "goodwill refund after withdrawal")
    d6_dos = am.api_purchase_dossier(p[6], "usr:erin")
    ok4 = (c2_open["status"] == "open"
           and c2_open["response_id"] is None
           and c2_ans["status"] == "answered"
           and c2_ans["response_id"] is not None
           and c2_ans["response_text"]
           and c2_ans["responded_utc"]
           and d2_dos["claim"]["status"] == "refunded"
           and d2_dos["claim"]["refund_id"] is not None
           and set(d2_dos["refund"].keys()) == REFUND_KEYS
           and d2_dos["refund"]["amount"] == d2_dos["price_paid"]
           and c5_wd["status"] == "withdrawn"
           and c5_wd["withdrawn_utc"]
           and d6_dos["claim"]["status"] == "refunded"
           and d6_dos["claim"]["withdrawn_utc"] is not None
           and d6_dos["ticket_state"] == "refunded")
    record("AC-AMPD4", ok4,
           "p2 open=%r answered=%r refunded=%r refund amount=%r"
           " p5 withdrawn=%r p6 withdrawn+refunded=%r"
           % (c2_open["status"], c2_ans["status"],
              d2_dos["claim"]["status"], d2_dos["refund"]["amount"],
              c5_wd["status"], d6_dos["claim"]["status"]))

    # -- AC-AMPD5 ticket_state precedence -------------------------------
    # p3: claim opened and left open; p4: claim answered and left
    c3 = am.open_claim("usr:bob", p[3], "feed stopped after one call")
    c4 = am.open_claim("usr:erin", p[4], "feed returned empty payloads")
    am.respond_claim("usr:dana", c4["claim_id"],
                     "payload fixed, please retry")
    states = {
        "p1_rated": am.api_purchase_dossier(p[1], "usr:bob")
        ["ticket_state"],
        "p2_refunded": am.api_purchase_dossier(p[2], "usr:carol")
        ["ticket_state"],
        "p3_open": am.api_purchase_dossier(p[3], "usr:bob")
        ["ticket_state"],
        "p4_answered": am.api_purchase_dossier(p[4], "usr:erin")
        ["ticket_state"],
        "p5_withdrawn": am.api_purchase_dossier(p[5], "usr:bob")
        ["ticket_state"],
        "p7_settled": am.api_purchase_dossier(p[7], "usr:bob")
        ["ticket_state"],
    }
    ok5 = (states == {"p1_rated": "rated", "p2_refunded": "refunded",
                      "p3_open": "open", "p4_answered": "answered",
                      "p5_withdrawn": "withdrawn",
                      "p7_settled": "settled"}
           and c3["claim_id"] and c4["claim_id"])
    record("AC-AMPD5", ok5, "states=%r" % (states,))

    # -- AC-AMPD6 gate family and order ---------------------------------
    dig6 = market_digests(am)
    bad_pid = []
    for form in BAD_PURCHASE_IDS:
        try:
            am.api_purchase_dossier(form, "usr:bob")
            bad_pid.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_pid.append(code_of(exc))
    bad_acct = []
    for form in BAD_ACCOUNTS:
        try:
            am.api_purchase_dossier(p[1], form)
            bad_acct.append("NO-RAISE")
        except A.ApiMarketError as exc:
            bad_acct.append(code_of(exc))
    ordered = []
    try:
        am.api_purchase_dossier(999999, "")
        ordered.append("NO-RAISE")
    except A.ApiMarketError as exc:
        ordered.append(code_of(exc))
    try:
        am.api_purchase_dossier(999999, "usr:bob")
        ordered.append("NO-RAISE")
    except A.ApiMarketError as exc:
        ordered.append(code_of(exc))
    try:
        am.api_purchase_dossier(0, "")
        ordered.append("NO-RAISE")
    except A.ApiMarketError as exc:
        ordered.append(code_of(exc))
    dig6_after = market_digests(am)
    ok6 = (bad_pid == ["E_AM_BAD_ARGS"] * len(BAD_PURCHASE_IDS)
           and bad_acct == ["E_AM_BAD_ACCOUNT"] * len(BAD_ACCOUNTS)
           and ordered == ["E_AM_BAD_ACCOUNT",
                           "E_AM_UNKNOWN_PURCHASE", "E_AM_BAD_ARGS"]
           and dig6_after == dig6)
    record("AC-AMPD6", ok6,
           "pid forms=%r account forms=%r order=%r digests frozen=%r"
           % (bad_pid, bad_acct, ordered, dig6_after == dig6))

    # -- AC-AMPD7 pure read and history ---------------------------------
    dig7 = market_digests(am)
    tx7 = ledger_tx_ids(led)
    fam_a = dossier_family(
        am, [(p[k], acct) for k, acct in PAIRS], [999999])
    fam_b = dossier_family(
        am, [(p[k], acct) for k, acct in PAIRS], [999999])
    dig7_read = market_digests(am)
    tx7_after = ledger_tx_ids(led)
    am.revise_price("usr:dana", lids["d2"], 11)
    delist = am.delist_api("usr:dana", lids["d2"])
    hist = am.api_purchase_dossier(p[3], "usr:bob")
    hist_seller = am.api_purchase_dossier(p[3], "usr:dana")
    ok7 = (fam_a == fam_b
           and dig7_read == dig7
           and tx7_after == tx7
           and hist["delisted"] is True
           and hist["delisted_utc"] == delist["delisted_utc"]
           and hist["current_price"] == 11
           and hist["price_paid"] == 4
           and hist["claim"]["status"] == "open"
           and hist_seller["viewer_role"] == "seller"
           and hist_seller["current_price"] == 11)
    record("AC-AMPD7", ok7,
           "repeat identical=%r digests frozen=%r tx frozen=%r"
           " retired delisted=%r price_paid=%d current=%d"
           % (fam_a == fam_b, dig7_read == dig7, tx7_after == tx7,
              hist["delisted"], hist["price_paid"],
              hist["current_price"]))

    # -- AC-AMPD8 cross-restart identity + wiring -----------------------
    family_one = dossier_family(
        am, [(p[k], acct) for k, acct in PAIRS],
        [999999, 0, 1])
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = dossier_family(
        am2, [(p[k], acct) for k, acct in PAIRS],
        [999999, 0, 1])
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = dossier_family(
        am3, [(p[k], acct) for k, acct in PAIRS],
        [999999, 0, 1])
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-purchasedossier" in handle.read()
    ok8 = (family_one == family_two == family_three and wired)
    record("AC-AMPD8", ok8,
           "instance1==2==3=%r runner wiring=%r"
           % (family_one == family_two == family_three, wired))

    # -- hygiene ---------------------------------------------------------
    shas_after = {q: sha_file(q) for q in PRODUCT_FILES}
    with open(os.path.abspath(__file__), "rb") as handle:
        blob = handle.read()
    try:
        blob.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    src = blob.decode("utf-8", "replace")
    net_imports = [line for line in src.splitlines()
                   if line.strip().startswith(("import requests",
                                               "import urllib",
                                               "import http"))]
    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("HYGIENE: consumer shas stable=%r suite ascii=%r"
          " network imports=%d"
          % (shas_before == shas_after, ascii_ok, len(net_imports)))
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8
                 and shas_before == shas_after and ascii_ok
                 and not net_imports) else 1


if __name__ == "__main__":
    sys.exit(main())