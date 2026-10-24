"""Acceptance suite for the apimarket seller inbox read face
(BigDomain R2096; canon = the explore-queue row seeded and claimed in
R2096, criteria AC-AMI1..AC-AMI8 registered in that claim note BEFORE
this code existed - honesty law; the AC-AMI prefix, the
api_seller_inbox name, this suite name and the
ledger-apimarket-sellerinbox runner label were all git-grep -F
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.api_seller_inbox. The reply door
(R2093) gave the seller a voice but no work queue: api_rating_replies
answers one listing at a time, so a seller with N listings has to
open N faces and count the gaps by hand. This window pins the
missing triage face:

  - an eight-key envelope and a seven-key row, the rows carrying ONLY
    unanswered ratings merged across every listing of the seller;
  - the debt ordering law (rated_utc ascending, then rating_id), so
    the oldest unanswered rating is always first, never grouped by
    listing;
  - conversation arithmetic (answered + unanswered == total) where a
    reply drains the queue without changing the historical count;
  - the star column reading through the one effective-value seam, so
    a buyer revision shows up in the queue;
  - retirement not erasing the seller's obligation;
  - seller isolation plus an honest empty inbox for a prefix-valid
    account with no ratings;
  - the account shape gate before any read, fail-closed with frozen
    table digests;
  - zero row mutations and zero token movement (pure read);
  - cross-restart byte identity and runner wiring.

Usage: python test_apimarket_sellerinbox.py
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

ENVELOPE_KEYS = {"dev_account", "rated_listing_count",
                 "total_rating_count", "answered_count",
                 "unanswered_count", "oldest_unanswered_utc",
                 "disclaimer", "rows"}
ROW_KEYS = {"rating_id", "listing_id", "listing_key", "title",
            "buyer_id", "stars", "rated_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions")
POOLS = ("pool:reserve", "pool:share")


class Clock(object):
    """Deterministic stamp holder: the suite sets one explicit UTC
    string before each rating so the ordering laws are reproducible
    (module clock patched, restored in main's finally block)."""

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


def inbox_family(am, accounts):
    return {acc: dumps(am.api_seller_inbox(acc)) for acc in accounts}


def reply_rows(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT reply_id, rating_id, listing_id, dev_account,"
        " reply_text, replied_utc FROM apimarket_rating_replies"
        " ORDER BY reply_id").fetchall()
    conn.close()
    return rows


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


def inbox_code(am, dev_account):
    try:
        am.api_seller_inbox(dev_account)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """Owner dana with two listings (d1, d2); frank a SECOND
    registered developer with its own listing (d3) - the isolation
    anchor. Four unanswered ratings for dana across both listings,
    two of them sharing one stamp so the rating_id tie-break is
    provable; one rating for frank so his inbox is non-empty."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMI-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMI-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    d3 = am.publish_api("usr:frank", "chart-render",
                        "Chart Render API",
                        "chart image render endpoint", PAYLOAD, 5,
                        False)["listing_id"]
    for buyer, listing, ref in (("bob", d1, "ref-bob-d1"),
                                ("carol", d1, "ref-carol-d1"),
                                ("bob", d2, "ref-bob-d2"),
                                ("erin", d2, "ref-erin-d2"),
                                ("dave", d3, "ref-dave-d3")):
        am.purchase_api("usr:" + buyer, listing, ref)
    clock.value = "2026-10-05T00:00:01Z"
    r1 = am.rate_api("usr:bob", d1, 5)["rating_id"]
    clock.value = "2026-10-05T00:00:02Z"
    r2 = am.rate_api("usr:carol", d1, 3)["rating_id"]
    clock.value = "2026-10-05T00:00:02Z"
    r3 = am.rate_api("usr:erin", d2, 4)["rating_id"]
    clock.value = "2026-10-05T00:00:03Z"
    r4 = am.rate_api("usr:bob", d2, 2)["rating_id"]
    clock.value = "2026-10-05T00:00:00Z"
    r5 = am.rate_api("usr:dave", d3, 4)["rating_id"]
    return d1, d2, d3, r1, r2, r3, r4, r5


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-sellerinbox-")
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
    d1, d2, d3, r1, r2, r3, r4, r5 = seed_world(
        led, dk, am, clock)

    # -- AC-AMI1 envelope + row contract, unanswered only ----------------
    env = am.api_seller_inbox("usr:dana")
    rows = env["rows"]
    ok1 = (set(env.keys()) == ENVELOPE_KEYS
           and env["dev_account"] == "usr:dana"
           and env["rated_listing_count"] == 2
           and env["total_rating_count"] == 4
           and env["answered_count"] == 0
           and env["unanswered_count"] == 4
           and env["unanswered_count"] == len(rows)
           and env["oldest_unanswered_utc"] == "2026-10-05T00:00:01Z"
           and env["disclaimer"] == DISCLAIMER
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and [r["rating_id"] for r in rows] == [r1, r2, r3, r4]
           and rows[0]["listing_id"] == d1
           and rows[0]["listing_key"] == "risk-scan"
           and rows[0]["title"] == "Risk Scan API"
           and rows[0]["buyer_id"] == "usr:bob"
           and rows[0]["stars"] == 5
           and rows[0]["rated_utc"] == "2026-10-05T00:00:01Z")
    record("AC-AMI1", ok1,
           "envelope keys ok=%r rows=%r count=%d answered=%d oldest=%r"
           % (set(env.keys()) == ENVELOPE_KEYS,
              [r["rating_id"] for r in rows], env["unanswered_count"],
              env["answered_count"], env["oldest_unanswered_utc"]))

    # -- AC-AMI2 debt ordering across listings ---------------------------
    stamps = [(r["rated_utc"], r["rating_id"]) for r in rows]
    ordered = stamps == sorted(stamps)
    merged = [r["listing_id"] for r in rows] == [d1, d1, d2, d2]
    tie_ok = (rows[1]["rated_utc"] == rows[2]["rated_utc"]
              == "2026-10-05T00:00:02Z"
              and rows[1]["rating_id"] < rows[2]["rating_id"]
              and rows[1]["listing_id"] == d1
              and rows[2]["listing_id"] == d2)
    ok2 = ordered and merged and tie_ok
    record("AC-AMI2", ok2,
           "stamps=%r ordered=%r merged-across-listings=%r"
           " tie-break-by-rating-id=%r"
           % (stamps, ordered, merged, tie_ok))

    # -- AC-AMI3 conversation conservation -------------------------------
    reply = am.reply_to_rating("usr:dana", r1, "thanks bob")
    after_reply = am.api_seller_inbox("usr:dana")
    ids_after = [r["rating_id"] for r in after_reply["rows"]]
    ok3 = (after_reply["total_rating_count"] == 4
           and after_reply["answered_count"] == 1
           and after_reply["unanswered_count"] == 3
           and after_reply["answered_count"]
           + after_reply["unanswered_count"]
           == after_reply["total_rating_count"]
           and r1 not in ids_after
           and ids_after == [r2, r3, r4]
           and after_reply["oldest_unanswered_utc"]
           == "2026-10-05T00:00:02Z")
    record("AC-AMI3", ok3,
           "total=%d answered=%d unanswered=%d ids=%r oldest=%r"
           % (after_reply["total_rating_count"],
              after_reply["answered_count"],
              after_reply["unanswered_count"], ids_after,
              after_reply["oldest_unanswered_utc"]))

    # -- AC-AMI4 effective star value in the queue -----------------------
    rev = am.revise_rating("usr:carol", r2, 2)
    after_rev = am.api_seller_inbox("usr:dana")
    row_r2 = [r for r in after_rev["rows"]
              if r["rating_id"] == r2][0]
    base_aggs = am.api_ratings(d1)
    ok4 = (row_r2["stars"] == 2
           and after_rev["unanswered_count"] == 3
           and base_aggs["rating_count"] == 2
           and base_aggs["rating_avg"] == 3.5
           and rev["stars"] == 2)
    record("AC-AMI4", ok4,
           "queue star=%r revision=%r listing avg=%r count=%r"
           % (row_r2["stars"], rev["stars"], base_aggs["rating_avg"],
              base_aggs["rating_count"]))

    # -- AC-AMI5 retirement does not erase the debt ----------------------
    am.delist_api("usr:dana", d2)
    after_delist = am.api_seller_inbox("usr:dana")
    ids_delist = [r["rating_id"] for r in after_delist["rows"]]
    ok5 = (ids_delist == [r2, r3, r4]
           and after_delist["unanswered_count"] == 3
           and after_delist["rated_listing_count"] == 2
           and all(r["listing_id"] == d2 for r in after_delist["rows"]
                   if r["rating_id"] in (r3, r4))
           and [r["listing_key"] for r in after_delist["rows"]
                if r["rating_id"] == r3] == ["macro-feed"])
    record("AC-AMI5", ok5,
           "ids after delist=%r count=%d rated_listings=%d"
           % (ids_delist, after_delist["unanswered_count"],
              after_delist["rated_listing_count"]))

    # -- AC-AMI6 isolation, honest empty, account gate -------------------
    frank_env = am.api_seller_inbox("usr:frank")
    empty_env = am.api_seller_inbox("usr:nobody")
    dana_ids = set(r["rating_id"] for r in
                   am.api_seller_inbox("usr:dana")["rows"])
    bad_codes = [inbox_code(am, bad) for bad in
                 (None, "", "bob", 7, 1.5, True, [], {})]
    blank_code = inbox_code(am, "   ")
    ok6 = (set(frank_env.keys()) == ENVELOPE_KEYS
           and [r["rating_id"] for r in frank_env["rows"]] == [r5]
           and frank_env["total_rating_count"] == 1
           and all(r["listing_id"] == d3 and
                   r["buyer_id"] == "usr:dave"
                   for r in frank_env["rows"])
           and r5 not in dana_ids
           and empty_env["rows"] == []
           and empty_env["total_rating_count"] == 0
           and empty_env["answered_count"] == 0
           and empty_env["unanswered_count"] == 0
           and empty_env["rated_listing_count"] == 0
           and empty_env["oldest_unanswered_utc"] is None
           and empty_env["disclaimer"] == DISCLAIMER
           and bad_codes == [A.E_AM_BAD_ACCOUNT] * 8
           and blank_code == A.E_AM_BAD_ACCOUNT)
    record("AC-AMI6", ok6,
           "frank rows=%r dana ids=%r empty=%r bad=%r blank=%r"
           % ([r["rating_id"] for r in frank_env["rows"]],
              sorted(dana_ids), empty_env["rows"],
              set(bad_codes), blank_code))

    # -- AC-AMI7 pure read: frozen digests, constant ledger --------------
    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)
    frozen_before = frozen_digests(am)
    replies_before = reply_rows(am)
    first = dumps(am.api_seller_inbox("usr:dana"))
    second = dumps(am.api_seller_inbox("usr:dana"))
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)
    frozen_after = frozen_digests(am)
    ok7 = (tx_before == tx_after
           and pools_before == pools_after
           and frozen_before == frozen_after
           and replies_before == reply_rows(am)
           and first == second)
    record("AC-AMI7", ok7,
           "ledger tx frozen=%r pools frozen=%r thirteen-table"
           " digests frozen=%r replies frozen=%r repeat identical=%r"
           % (tx_before == tx_after, pools_before == pools_after,
              frozen_before == frozen_after,
              replies_before == reply_rows(am), first == second))

    # -- AC-AMI8 cross-restart identity + wiring + hygiene ---------------
    accounts = ("usr:dana", "usr:frank", "usr:nobody")
    ids = (d1, d2, d3)
    family_before = inbox_family(am, accounts)
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = inbox_family(am2, accounts)
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = inbox_family(am3, accounts)
    close_stack(am3, dk3, metered3, led3)
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-sellerinbox" in handle.read()
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
           and not net_imports and outside and len(ids) == 3)
    record("AC-AMI8", ok8,
           "three instances byte-identical=%r runner wiring=%r"
           " consumer shas stable=%r ascii=%r network imports=%d"
           " world outside repo=%r"
           % (family_before == family_two == family_three, wired,
              shas_before == shas_after, ascii_ok,
              len(net_imports), outside))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())