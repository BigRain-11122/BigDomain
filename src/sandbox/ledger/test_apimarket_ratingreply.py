"""Acceptance suite for the apimarket seller rating-reply faces
(BigDomain R2093; canon = the explore-queue row seeded and claimed in
R2093, criteria AC-AMRP1..AC-AMRP8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMRP prefix, the
reply_to_rating / api_rating_replies names, the
apimarket_rating_replies table, the E_AM_UNKNOWN_RATING /
E_AM_REPLY_DUP / E_AM_BAD_REPLY codes, this suite name and the
ledger-apimarket-ratreply runner label were all git-grep -F
zero-occupancy anchored 2026-10-24, rc=1).

Face under proof: APIMarketFace.reply_to_rating /
api_rating_replies. Thirteen read faces and two write doors existed,
but a seller could never answer a rating: the trust signal had one
arrow only. This window pins the response leg:

  - one seven-key reply row and one five-key envelope whose rows
    mirror api_ratings in rating_id order, unanswered ratings
    carrying reply=None;
  - ownership gate (only the seller of the rated listing answers,
    another registered developer owning its own listing is refused);
  - the pinned gate order (account shape, rating id shape, text
    shape, rating existence, ownership, duplicate) with fail-closed
    zero side effects;
  - one immutable reply per rating, the first text and stamp
    preserved byte-identical on a repeat;
  - zero token movement and frozen rating/purchase/refund digests;
  - a retired listing keeps its conversation readable and answerable;
  - cross-restart byte identity of the read family;
  - runner wiring plus suite hygiene (ASCII, no network imports,
    world outside the repo).

Usage: python test_apimarket_ratingreply.py
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

ENVELOPE_KEYS = {"listing_id", "rating_count", "reply_count",
                 "disclaimer", "rows"}
ROW_KEYS = {"rating_id", "buyer_id", "stars", "rated_utc", "reply"}
REPLY_KEYS = {"reply_id", "dev_account", "reply_text", "replied_utc"}
DOOR_KEYS = {"reply_id", "rating_id", "listing_id", "dev_account",
             "reply_text", "replied_utc", "disclaimer"}

FROZEN_TABLES = ("apimarket_listings", "apimarket_purchases",
                 "apimarket_ratings", "apimarket_refunds",
                 "apimarket_price_revisions",
                 "apimarket_listing_revisions")
POOLS = ("pool:reserve", "pool:share")


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
    out = {t: table_digest(conn, t) for t in FROZEN_TABLES}
    conn.close()
    return out


def reply_rows(am):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT reply_id, rating_id, listing_id, dev_account,"
        " reply_text, replied_utc FROM apimarket_rating_replies"
        " ORDER BY reply_id").fetchall()
    conn.close()
    return rows


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def pool_balances(led):
    return {pool: led.balance(pool) for pool in POOLS}


def reply_family(am, ids):
    return {str(lid): dumps(am.api_rating_replies(lid))
            for lid in ids}


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


def expect(am, dev_account, rating_id, text):
    try:
        am.reply_to_rating(dev_account, rating_id, text)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am):
    """Owner dana with two listings; bob buys and rates both, carol
    buys and rates d1, frank is a SECOND registered developer with
    its own live listing (the ownership-gate anchor)."""
    led.mint_to_pool("pool:reserve", 6000, "SETTLE-AMRP-A",
                     "settlement")
    led.mint_to_pool("pool:share", 6000, "SETTLE-AMRP-S",
                     "settlement")
    for who in ("bob", "carol", "erin"):
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
    am.purchase_api("usr:bob", d1, "ref-bob-d1")
    am.purchase_api("usr:carol", d1, "ref-carol-d1")
    am.purchase_api("usr:bob", d2, "ref-bob-d2")
    r_bob_d1 = am.rate_api("usr:bob", d1, 5)
    r_carol_d1 = am.rate_api("usr:carol", d1, 3)
    r_bob_d2 = am.rate_api("usr:bob", d2, 4)
    return d1, d2, d3, r_bob_d1, r_carol_d1, r_bob_d2


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-ratreply-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    d1, d2, d3, rb1, rc1, rb2 = seed_world(led, dk, am)

    tx_before = ledger_tx_ids(led)
    pools_before = pool_balances(led)
    frozen_before = frozen_digests(am)
    rating_digest_before = dumps(am.api_ratings(d1))

    # -- AC-AMRP1 contract + unanswered rows ------------------------------
    door = am.reply_to_rating("usr:dana", rb1["rating_id"],
                              "  thanks bob, glad it worked  ")
    env = am.api_rating_replies(d1)
    rows = env["rows"]
    answered = [r for r in rows if r["reply"] is not None]
    unanswered = [r for r in rows if r["reply"] is None]
    ok1 = (set(door.keys()) == DOOR_KEYS
           and door["rating_id"] == rb1["rating_id"]
           and door["listing_id"] == d1
           and door["dev_account"] == "usr:dana"
           and door["reply_text"] == "thanks bob, glad it worked"
           and set(env.keys()) == ENVELOPE_KEYS
           and env["listing_id"] == d1
           and env["rating_count"] == 2
           and env["reply_count"] == 1
           and env["disclaimer"] == DISCLAIMER
           and all(set(r.keys()) == ROW_KEYS for r in rows)
           and set(answered[0]["reply"].keys()) == REPLY_KEYS
           and answered[0]["rating_id"] == rb1["rating_id"]
           and answered[0]["rating_id"] < unanswered[0]["rating_id"]
           and answered[0]["buyer_id"] == "usr:bob"
           and answered[0]["stars"] == 5
           and answered[0]["reply"]["reply_id"] == door["reply_id"]
           and answered[0]["reply"]["reply_text"]
           == "thanks bob, glad it worked"
           and answered[0]["reply"]["replied_utc"]
           == door["replied_utc"]
           and unanswered[0]["rating_id"] == rc1["rating_id"]
           and unanswered[0]["buyer_id"] == "usr:carol"
           and unanswered[0]["stars"] == 3)
    record("AC-AMRP1", ok1,
           "door keys=%r envelope=%r rows=%d answered=%d reply_count=%d"
           % (set(door.keys()) == DOOR_KEYS,
              set(env.keys()) == ENVELOPE_KEYS, len(rows),
              len(answered), env["reply_count"]))

    # -- AC-AMRP2 ownership gate ------------------------------------------
    n_before = len(reply_rows(am))
    codes = {
        "buyer": expect(am, "usr:carol", rc1["rating_id"],
                        "not my listing"),
        "other_dev": expect(am, "usr:frank", rc1["rating_id"],
                            "not my listing either"),
        "empty_account": expect(am, "", rc1["rating_id"], "x"),
        "dev_prefix": expect(am, "dev:dana", rc1["rating_id"], "x"),
    }
    n_after = len(reply_rows(am))
    ok2 = (codes == {"buyer": A.E_AM_NOT_OWNER,
                     "other_dev": A.E_AM_NOT_OWNER,
                     "empty_account": A.E_AM_BAD_ACCOUNT,
                     "dev_prefix": A.E_AM_BAD_ACCOUNT}
           and n_before == n_after)
    record("AC-AMRP2", ok2,
           "codes=%r reply rows %d->%d" % (codes, n_before, n_after))

    # -- AC-AMRP3 gate order + argument shapes ----------------------------
    order = [
        ("account_first", expect(am, "", 0, ""), A.E_AM_BAD_ACCOUNT),
        ("id_before_text", expect(am, "usr:dana", 0, ""),
         A.E_AM_BAD_ARGS),
        ("text_before_exists", expect(am, "usr:dana", 9999, ""),
         A.E_AM_BAD_REPLY),
        ("unknown_rating", expect(am, "usr:dana", 9999, "hello"),
         A.E_AM_UNKNOWN_RATING),
        ("owner_after_exists", expect(am, "usr:frank",
                                      rc1["rating_id"], "hello"),
         A.E_AM_NOT_OWNER),
        ("dup_last", expect(am, "usr:dana", rb1["rating_id"],
                            "hello again"), A.E_AM_REPLY_DUP),
    ]
    id_shapes = [expect(am, "usr:dana", bad, "hello")
                 for bad in (0, -1, True, "1", None)]
    text_shapes = [expect(am, "usr:dana", rc1["rating_id"], bad)
                   for bad in ("", "   ", "x" * 501, "a\nb", 7, None)]
    n_after3 = len(reply_rows(am))
    ok3 = (all(got == want for _name, got, want in order)
           and id_shapes == [A.E_AM_BAD_ARGS] * 5
           and text_shapes == [A.E_AM_BAD_REPLY] * 6
           and n_after3 == n_before)
    record("AC-AMRP3", ok3,
           "order=%r id_shapes=%r text_shapes=%r rows=%d"
           % ([(n, g == w) for n, g, w in order],
              set(id_shapes), set(text_shapes), n_after3))

    # -- AC-AMRP4 honest absence + retired listing -----------------------
    try:
        am.api_rating_replies(9999)
        unknown_listing = "NO-RAISE"
    except A.ApiMarketError as exc:
        unknown_listing = code_of(exc)
    am.delist_api("usr:dana", d2)
    retired_before = am.api_rating_replies(d2)
    retired_reply = am.reply_to_rating("usr:dana", rb2["rating_id"],
                                       "fixed the latency in v2")
    retired_after = am.api_rating_replies(d2)
    aggs = am.api_ratings(d2)
    ok4 = (unknown_listing == A.E_AM_UNKNOWN_LISTING
           and retired_before["reply_count"] == 0
           and retired_before["rows"][0]["reply"] is None
           and retired_reply["reply_text"] == "fixed the latency in v2"
           and retired_after["reply_count"] == 1
           and retired_after["rows"][0]["rating_id"]
           == rb2["rating_id"]
           and retired_after["rows"][0]["reply"]["reply_id"]
           == retired_reply["reply_id"]
           and aggs["rating_count"] == 1
           and aggs["rating_avg"] == 4.0)
    record("AC-AMRP4", ok4,
           "unknown listing=%r retired reply readable=%r rating agg"
           " intact=%r"
           % (unknown_listing, retired_after["reply_count"] == 1,
              aggs["rating_avg"] == 4.0))

    # -- AC-AMRP5 one immutable reply ------------------------------------
    first = reply_rows(am)[0]
    dup_code = expect(am, "usr:dana", rb1["rating_id"],
                      "rewritten text")
    after_dup = [r for r in reply_rows(am) if r[1] == rb1["rating_id"]]
    env_after_dup = am.api_rating_replies(d1)
    still = [r for r in env_after_dup["rows"]
             if r["rating_id"] == rb1["rating_id"]][0]["reply"]
    ok5 = (dup_code == A.E_AM_REPLY_DUP
           and len(after_dup) == 1
           and after_dup[0] == first
           and still["reply_text"] == "thanks bob, glad it worked"
           and still["replied_utc"] == first[5])
    record("AC-AMRP5", ok5,
           "dup code=%r rows=%d text preserved=%r stamp preserved=%r"
           % (dup_code, len(after_dup),
              still["reply_text"] == "thanks bob, glad it worked",
              still["replied_utc"] == first[5]))

    # -- AC-AMRP6 zero side effects --------------------------------------
    tx_after = ledger_tx_ids(led)
    pools_after = pool_balances(led)
    frozen_after = frozen_digests(am)
    rat_digest_after = dumps(am.api_ratings(d1))
    ok6 = (tx_after == tx_before
           and pools_after == pools_before
           and {k: v for k, v in frozen_after.items() if k !=
                "apimarket_refunds"} ==
           {k: v for k, v in frozen_before.items() if k !=
            "apimarket_refunds"}
           and frozen_after["apimarket_refunds"]
           == frozen_before["apimarket_refunds"]
           and rat_digest_after == rating_digest_before
           and len(reply_rows(am)) == 2)
    record("AC-AMRP6", ok6,
           "ledger tx frozen=%r pools frozen=%r frozen tables=%r"
           " ratings byte-identical=%r reply rows=%d"
           % (tx_after == tx_before, pools_after == pools_before,
              frozen_after == frozen_before,
              rat_digest_after == rating_digest_before,
              len(reply_rows(am))))

    # -- AC-AMRP7 cross-restart identity ---------------------------------
    ids = (d1, d2, d3)
    family_before = reply_family(am, ids)
    counts_before = len(reply_rows(am))
    close_stack(am, dk, metered, led)
    led2, metered2, dk2, gate2, am2 = build_stack(
        db_path, cfg, lobby_cfg)
    family_two = reply_family(am2, ids)
    counts_two = len(reply_rows(am2))
    close_stack(am2, dk2, metered2, led2)
    led3, metered3, dk3, gate3, am3 = build_stack(
        db_path, cfg, lobby_cfg)
    family_three = reply_family(am3, ids)
    counts_three = len(reply_rows(am3))
    close_stack(am3, dk3, metered3, led3)
    ok7 = (family_before == family_two == family_three
           and counts_before == counts_two == counts_three == 2)
    record("AC-AMRP7", ok7,
           "instance1==2==3 byte-identical=%r reply rows=%r %r %r"
           % (family_before == family_two == family_three,
              counts_before, counts_two, counts_three))

    # -- AC-AMRP8 wiring + hygiene ---------------------------------------
    with open(RECONCILE, "rb") as handle:
        wired = b"ledger-apimarket-ratreply" in handle.read()
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
    ok8 = (wired and shas_before == shas_after and ascii_ok
           and not net_imports and outside)
    record("AC-AMRP8", ok8,
           "runner wiring=%r consumer shas stable=%r ascii=%r"
           " network imports=%d world outside repo=%r"
           % (wired, shas_before == shas_after, ascii_ok,
              len(net_imports), outside))

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())