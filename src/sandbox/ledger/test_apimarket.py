"""Acceptance suite for the developer API marketplace face
(BigDomain explore queue, claimed round R1763; canon = the
"API market listing" line: developer service listing / purchase
with revenue split / purchaser-only rating). Asserts the
pre-registered criteria AC-AM1..AC-AM7 from the R1763
explore-queue row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

The content gate is the lobby SecGate product injected by
reference (no copy): its Chinese wordlists are data loaded from
the lobby config at runtime - this test source stays pure ASCII
per the encoding discipline.

Usage: python test_apimarket.py
"""

import hashlib
import json
import os
import re
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
import apidev as D                    # noqa: E402 (R1700 registry face)
import apimarket as A                 # noqa: E402 (R1763 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, reference)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API marketplace"
              " is a service listing face, not investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except A.ApiMarketError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


class _CountingGate(object):
    """Calls-counting wrapper around the lobby SecGate: proves the
    registry gate runs BEFORE the content gate (an off-register
    publisher burns zero msgSecCheck calls - AC-AM2)."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    def check_text(self, text):
        self.calls += 1
        return self.inner.check_text(text)


class _FaultGate(object):
    """Runtime-fault gate stub: check_text always blows up (the
    face must map this to E_AM_GATE_ERROR and never silently pass
    - AC-AM3 fail-closed posture)."""

    def check_text(self, text):
        raise RuntimeError("stub gate offline")


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-ac-")
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as handle:
        cfg_sha_before = hashlib.sha256(handle.read()).hexdigest()
    with open(cfg_path, "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]
    advisory_word = lobby_cfg["gate"]["advisory_ban_words"][0]

    db_path = os.path.join(tmp, "ledger.db")
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    ledger_tables_base = set(
        r[0] for r in sqlite3.connect(db_path).execute(
            "SELECT name FROM sqlite_master WHERE type='table'"))
    gate = _CountingGate(SecGate.from_config(lobby_cfg))
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)
    conn = sqlite3.connect(db_path)
    am_conn = sqlite3.connect(am.db_path)

    led.mint_to_pool("pool:reserve", 2000, "SETTLE-AM-A", "settlement")
    led.mint_to_pool("pool:share", 1000, "SETTLE-AM-S", "settlement")
    led.ensure_account("usr:ada", census_avatar_id="ada")   # developer 1
    led.ensure_account("usr:dan", census_avatar_id="dan")   # developer 2
    led.ensure_account("usr:bob", census_avatar_id="bob")   # buyer
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.ensure_account("usr:eve", census_avatar_id="eve")   # non-dev buyer
    for who, amount, tag in (("ada", 200, "ada"), ("dan", 200, "dan"),
                              ("bob", 500, "bob"),
                              ("carol", 300, "carol"),
                              ("eve", 100, "eve")):
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)

    def bal(who):
        return led.balance("usr:" + who)["balance"]

    def tx_count(kind):
        return conn.execute(
            "SELECT COUNT(*) FROM ledger_tx WHERE type = ?",
            (kind,)).fetchone()[0]

    # register the two developers in the DevKeyFace registry
    dk.issue_key("usr:ada", "ada-key", 10, ["backtest"], False)
    dk.issue_key("usr:dan", "dan-key", 10, ["visualize"], True)

    # -- AC-AM1 listing idempotency + structure ---------------------------
    t1 = am.publish_api("usr:ada", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10, False)
    n0 = _count(am_conn, "apimarket_listings")
    ok_dup, code_dup = expect_error(
        lambda: am.publish_api("usr:ada", "risk-scan", "Risk Scan API",
                               "portfolio risk scan endpoint", PAYLOAD,
                               10, False),
        A.E_AM_DUP_LISTING)
    n1 = _count(am_conn, "apimarket_listings")
    t2 = am.publish_api("usr:ada", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)
    t3 = am.publish_api("usr:dan", "risk-scan", "Dan Risk Variant",
                        "same key other developer", PAYLOAD, 7, False)
    n2 = _count(am_conn, "apimarket_listings")
    bad1 = []
    for fn in (
            lambda: am.publish_api("ent:corp", "k", "t", "d",
                                   PAYLOAD, 5, False),
            lambda: am.publish_api("usr:ada", "", "t", "d",
                                   PAYLOAD, 5, False),
            lambda: am.publish_api("usr:ada", "k2", " ", "d",
                                   PAYLOAD, 5, False),
            lambda: am.publish_api("usr:ada", "k3", "t", "d",
                                   PAYLOAD, 0, False),
            lambda: am.publish_api("usr:ada", "k4", "t", "d",
                                   PAYLOAD, True, False),
            lambda: am.publish_api("usr:ada", "k5", "t", "d",
                                   PAYLOAD, "5", False),
            lambda: am.publish_api("usr:ada", "k6", "t", "d",
                                   {}, 5, False),
            lambda: am.publish_api("usr:ada", "k7", "t", "d",
                                   PAYLOAD, 5, "yes")):
        ok_x, _code_x = expect_error(fn, A.E_AM_BAD_ACCOUNT,
                                      A.E_AM_BAD_ARGS, A.E_AM_BAD_PRICE)
        bad1.append(ok_x)
    n3 = _count(am_conn, "apimarket_listings")
    ok_unk, _ = expect_error(lambda: am.api_view(999),
                             A.E_AM_UNKNOWN_LISTING)
    ok_badid, _ = expect_error(lambda: am.api_view("abc"),
                               A.E_AM_UNKNOWN_LISTING)
    record("AC-AM1",
           t1["listing_id"] > 0 and t1["ai_label"] == 0
           and t2["ai_label"] == 1 and ok_dup
           and n1 == n0 and n2 == n0 + 2 and n3 == n0 + 2
           and all(bad1) and ok_unk and ok_badid,
           "listing t1=%d ai t1/t2=%d/%d dup=%s rows %d->%d->%d"
           " badargs=%d/8 unknown=%s badid=%s"
           % (t1["listing_id"], t1["ai_label"], t2["ai_label"], ok_dup,
              n0, n2, n3, sum(bad1), ok_unk, ok_badid))

    # -- AC-AM2 developer registry gate ------------------------------------
    c0 = gate.calls
    ok_eve, code_eve = expect_error(
        lambda: am.publish_api("usr:eve", "eve-svc", "Eve Service",
                               "off-register listing", PAYLOAD, 5, False),
        A.E_AM_NOT_DEV)
    c1 = gate.calls
    ok_order, code_order = expect_error(
        lambda: am.publish_api("usr:eve", "eve-svc2",
                               "Eve " + bad_word + " probe",
                               "off-register listing", PAYLOAD, 5, False),
        A.E_AM_NOT_DEV)
    c2 = gate.calls
    n4 = _count(am_conn, "apimarket_listings")
    with open(os.path.join(BASE, "apimarket.py"), "rb") as handle:
        mod_src = handle.read().decode("ascii")
    # statement-level scan (R1678 self-referential false-positive
    # lesson): the docstring may MENTION api_dev_keys; what is
    # banned is any execute() line reading that table.
    no_direct = not any(".execute(" in ln and "api_dev_keys" in ln
                        for ln in mod_src.splitlines())
    spend_b4 = tx_count("spend")
    p_eve = am.purchase_api("usr:eve", t3["listing_id"], "ref-eve-t3")
    spend_a4 = tx_count("spend")
    record("AC-AM2",
           ok_eve and code_eve == A.E_AM_NOT_DEV and c1 == c0
           and ok_order and code_order == A.E_AM_NOT_DEV and c2 == c1
           and n4 == n3 and no_direct
           and p_eve["price_paid"] == 7 and spend_a4 - spend_b4 == 1,
           "non-dev E_AM_NOT_DEV (gate calls %d->%d->%d zero burn,"
           " worded probe still registry-rejected) rows %d==%d"
           " no-direct-read=%s non-dev purchase ok (%d spend tx)"
           % (c0, c1, c2, n4, n3, no_direct, spend_a4 - spend_b4))

    # -- AC-AM3 msgSecCheck pre-gate ---------------------------------------
    ok_gt, code_gt = expect_error(
        lambda: am.publish_api("usr:ada", "bad-title",
                               "Scan " + bad_word + " API",
                               "clean description", PAYLOAD, 5, False),
        A.E_AM_CONTENT_REJECTED)
    ok_gd, code_gd = expect_error(
        lambda: am.publish_api("usr:ada", "bad-desc", "Clean Title",
                               "contains " + advisory_word + " tip",
                               PAYLOAD, 5, False),
        A.E_AM_CONTENT_REJECTED)
    n5 = _count(am_conn, "apimarket_listings")
    ok_nogate, _ = expect_error(
        lambda: A.APIMarketFace(led, dk, None, DISCLAIMER),
        A.E_AM_NO_GATE)
    am_fault = A.APIMarketFace(led, dk, _FaultGate(), DISCLAIMER)
    ok_fault, _ = expect_error(
        lambda: am_fault.publish_api("usr:ada", "fault-svc",
                                     "Fault Probe", "d", PAYLOAD, 5,
                                     False),
        A.E_AM_GATE_ERROR)
    am_fault.close()
    n6 = _count(am_conn, "apimarket_listings")
    record("AC-AM3",
           ok_gt and code_gt == A.E_AM_CONTENT_REJECTED
           and ok_gd and code_gd == A.E_AM_CONTENT_REJECTED
           and n5 == n4 and ok_nogate and ok_fault and n6 == n4,
           "title hit=%s desc hit=%s rows %d==%d==%d no-gate=%s"
           " fault=%s (fail-closed, zero rows on every path)"
           % (ok_gt, ok_gd, n4, n5, n6, ok_nogate, ok_fault))

    # -- AC-AM4 purchase idempotency + integer split -----------------------
    b0 = bal("bob")
    spend0, share0 = tx_count("spend"), tx_count("share")
    p1 = am.purchase_api("usr:bob", t1["listing_id"], "ref-bob-t1")
    b1 = bal("bob")
    spend1, share1 = tx_count("spend"), tx_count("share")
    prow = am_conn.execute(
        "SELECT price_paid, dev_share, platform_share, spend_tx,"
        " dev_share_tx FROM apimarket_purchases WHERE purchase_id = ?",
        (p1["purchase_id"],)).fetchone()
    ok_dupbuy, _ = expect_error(
        lambda: am.purchase_api("usr:bob", t1["listing_id"],
                                "ref-bob-t1b"),
        A.E_AM_PURCHASE_DUP)
    b2 = bal("bob")
    ok_self, _ = expect_error(
        lambda: am.purchase_api("usr:ada", t1["listing_id"], "ref-ada"),
        A.E_AM_SELF_BUY)
    ok_unkbuy, _ = expect_error(
        lambda: am.purchase_api("usr:bob", 999, "ref-bob-999"),
        A.E_AM_UNKNOWN_LISTING)
    ok_badref, _ = expect_error(
        lambda: am.purchase_api("usr:bob", t1["listing_id"], " "),
        A.E_AM_BAD_ARGS)
    ok_badacct, _ = expect_error(
        lambda: am.purchase_api("corp:bob", t1["listing_id"], "r"),
        A.E_AM_BAD_ACCOUNT)
    s10 = A.split_amount(10)
    s3 = A.split_amount(3)
    s7 = A.split_amount(7)
    am2 = A.APIMarketFace(
        led, dk, gate, DISCLAIMER,
        params={"dev_weight": 60, "platform_weight": 40})
    cb0 = bal("carol")
    p2 = am2.purchase_api("usr:carol", t1["listing_id"], "ref-carol-t1")
    cb1 = bal("carol")
    ok_split0, _ = expect_error(
        lambda: A.APIMarketFace(
            led, dk, gate, DISCLAIMER,
            params={"dev_weight": 0, "platform_weight": 40}),
        A.E_AM_BAD_SPLIT)
    ok_splitb, _ = expect_error(
        lambda: A.APIMarketFace(
            led, dk, gate, DISCLAIMER,
            params={"dev_weight": True, "platform_weight": 40}),
        A.E_AM_BAD_SPLIT)
    ok_check = False
    try:
        am_conn.execute(
            "INSERT INTO apimarket_purchases (listing_id, buyer_id,"
            " price_paid, dev_share, platform_share, spend_tx,"
            " dev_share_tx, purchased_utc) VALUES (?,?,?,?,?,?,?,?)",
            (t1["listing_id"], "usr:hack", 10, 7, 2, "x", "y", "z"))
    except sqlite3.IntegrityError:
        ok_check = True
    finally:
        am_conn.rollback()   # release the implicit write txn
    record("AC-AM4",
           b0 - b1 == 10 and spend1 - spend0 == 1 and share1 - share0 == 1
           and prow == (10, 7, 3, p1["spend_tx"], p1["dev_share_tx"])
           and bool(p1["spend_tx"]) and bool(p1["dev_share_tx"])
           and ok_dupbuy and b2 == b1 and ok_self and ok_unkbuy
           and ok_badref and ok_badacct
           and s10 == (7, 3) and s3 == (3, 0) and s7 == (5, 2)
           and cb0 - cb1 == 10 and p2["dev_share"] == 6
           and p2["platform_share"] == 4
           and ok_split0 and ok_splitb and ok_check,
           "bob -10 (spend %d->%d share %d->%d) row=(10,7,3)"
           " dup-before-spend=%s self=%s unknown=%s badref=%s"
           " badacct=%s splits 10->(7,3) 3->(3,0) 7->(5,2)"
           " custom60/40=(%d,%d) badsplit=%s/%s db-check=%s"
           % (spend0, spend1, share0, share1, ok_dupbuy, ok_self,
              ok_unkbuy, ok_badref, ok_badacct, p2["dev_share"],
              p2["platform_share"], ok_split0, ok_splitb, ok_check))

    # -- AC-AM5 purchaser-only rating gate ---------------------------------
    tx_b = conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    ok_nb, _ = expect_error(
        lambda: am.rate_api("usr:dan", t1["listing_id"], 4),
        A.E_AM_NOT_BUYER)
    r1 = am.rate_api("usr:bob", t1["listing_id"], 5)
    ok_duprate, _ = expect_error(
        lambda: am.rate_api("usr:bob", t1["listing_id"], 4),
        A.E_AM_RATE_DUP)
    bad_stars = []
    for stars in (0, 6, True):
        ok_s, _ = expect_error(
            lambda s=stars: am.rate_api("usr:carol", t1["listing_id"], s),
            A.E_AM_BAD_STARS)
        bad_stars.append(ok_s)
    r2 = am.rate_api("usr:carol", t1["listing_id"], 4)
    rview = am.api_ratings(t1["listing_id"])
    tx_a = conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    nrate = _count(am_conn, "apimarket_ratings")
    record("AC-AM5",
           ok_nb and r1["stars"] == 5 and ok_duprate
           and all(bad_stars) and r2["stars"] == 4
           and nrate == 2 and rview["rating_count"] == 2
           and abs(rview["rating_avg"] - 4.5) < 1e-9
           and tx_a == tx_b,
           "non-buyer=%s dup=%s stars-bad=%d/3 rows=%d agg=(%d,%.1f)"
           " ledger_tx %d==%d (zero token movement)"
           % (ok_nb, ok_duprate, sum(bad_stars), nrate,
              rview["rating_count"], rview["rating_avg"], tx_b, tx_a))

    # -- AC-AM6 AIGC label + resident disclaimer ---------------------------
    ok_nodisc, _ = expect_error(
        lambda: A.APIMarketFace(led, dk, gate, "  "),
        A.E_AM_NO_DISCLAIMER)
    v1 = am.api_view(t1["listing_id"])
    board = am.api_board()
    sales = am.api_sales("usr:ada")
    rat = am.api_ratings(t1["listing_id"])
    env_ok = all(x.get("disclaimer") == DISCLAIMER
                 for x in (v1, board, sales, rat, p1))
    ai_ok = (v1["ai_label"] == 0
             and any(row["ai_label"] == 1 for row in board["listings"])
             and t1["ai_label"] == 0)
    ok_ai2 = False
    try:
        am_conn.execute(
            "INSERT INTO apimarket_listings (dev_account, listing_key,"
            " title, description, payload_json, token_price, ai_label,"
            " listed_utc) VALUES (?,?,?,?,?,?,?,?)",
            ("usr:ada", "hack-row", "t", "d", "{}", 5, 2, "z"))
    except sqlite3.IntegrityError:
        ok_ai2 = True
    finally:
        am_conn.rollback()   # release the implicit write txn
    record("AC-AM6",
           ok_nodisc and env_ok and ai_ok and ok_ai2,
           "empty-disclaimer=%s envelopes=%s ai_view=%d ai_board"
           " dual-label=%s ai_label=2 db-check=%s"
           % (ok_nodisc, env_ok, v1["ai_label"], ai_ok, ok_ai2))

    # -- AC-AM7 hygiene + hard laws ----------------------------------------
    with open(os.path.join(BASE, "apimarket.py"), "rb") as handle:
        src_bytes = handle.read()
    ascii_ok = all(b < 128 for b in src_bytes)
    src_text = src_bytes.decode("ascii")
    upd_lines = [ln for ln in src_text.splitlines()
                 if ".execute(" in ln
                 and ("UPDATE" in ln.upper() or "DELETE" in ln.upper())]
    import_lines = [ln for ln in src_text.splitlines()
                    if ln.startswith("import ")
                    or ln.startswith("from ")]
    net_ok = not any(re.search(r"\b(urllib|requests|socket|http)\b", ln)
                     for ln in import_lines)
    rng_ok = ("import random" not in src_text
              and "random." not in src_text)
    with open(cfg_path, "rb") as handle:
        cfg_sha_after = hashlib.sha256(handle.read()).hexdigest()
    ledger_tables_after = set(
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"))
    indep_ok = (os.path.exists(am.db_path)
                and not any(name.startswith("apimarket_")
                           for name in ledger_tables_after)
                and ledger_tables_after == ledger_tables_base)
    record("AC-AM7",
           ascii_ok and not upd_lines and net_ok and rng_ok
           and cfg_sha_after == cfg_sha_before and indep_ok,
           "ascii=%s upd/del-execute-lines=%d net-import=%s rng=%s"
           " config-sha-stable=%s independent-db=%s"
           " (ledger tables untouched)"
           % (ascii_ok, len(upd_lines), net_ok, rng_ok,
              cfg_sha_after == cfg_sha_before, indep_ok))

    am2.close()
    am.close()
    am_conn.close()
    conn.close()
    print("", flush=True)
    fails = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fails == 0 else "FAIL",
                              len(RESULTS) - fails, len(RESULTS)),
          flush=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
