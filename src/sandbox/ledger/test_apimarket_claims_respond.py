#!/usr/bin/env python3
"""Claim answer door suite - the seller side of the post-sale claim.

(BigDomain R2130; canon = the explore-queue row claimed in R2130,
criteria AC-AMCR1..AC-AMCR8 registered in that claim note BEFORE this
suite existed; the AC-AMCR prefix, respond_claim,
apimarket_claim_responses, E_AM_BAD_RESPONSE, E_AM_UNKNOWN_CLAIM,
E_AM_CLAIM_ANSWERED, this suite name and the
ledger-apimarket-claims-respond runner label were all git grep -F
zero-occupancy anchored 2026-10-25, rc=1; answered_count is a reused
envelope field name, not an anchor).

Face under proof: APIMarketFace.respond_claim + the api_claims answer
extension. R2129 gave the buyer an open_claim door and both sides a
queue, but the seller had no way to say anything: the only reply in the
product was a refund, which fails closed when the proceeds are spent.
This slot pins:

  - the nine-key door envelope, the eight-key queue envelope and the
    fifteen-key row (R2129 twelve plus response_id / response_text /
    responded_utc), with claim_count == open + answered + refunded;
  - status derived in ONE place with the precedence refunded > answered
    > open, and both the claim row and the response row never rewritten;
  - the gate family and its order: account, claim-id shape, response
    text shape, claim existence, ownership, already-refunded, duplicate,
    with frozen table digests and a constant ledger tx set;
  - one answer per claim (table UNIQUE), first stamp never rewritten,
    the same seller answering a second claim, no UPDATE surface;
  - buyer / seller / market views carrying the answer keys with the
    answered counts derived from the filtered set and strict isolation;
  - pure read on api_claims, zero token movement on the door, three
    identical in-process runs and two full-stack restarts;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_claims_respond.py
"""

import ast
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
import apimarket_report as RPT        # noqa: E402 (config loader)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

DOOR_KEYS = {"response_id", "claim_id", "purchase_id", "listing_id",
             "dev_account", "response_text", "replied_utc", "status",
             "disclaimer"}

ENVELOPE_KEYS = {"buyer_id", "dev_account", "claim_count", "open_count",
                 "answered_count", "refunded_count", "disclaimer",
                 "claims"}

ROW_KEYS = {"claim_id", "purchase_id", "listing_id", "listing_title",
            "dev_account", "buyer_id", "price_paid", "claim_text",
            "opened_utc", "status", "refund_id", "refunded_utc",
            "response_id", "response_text", "responded_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers", "apimarket_reviews",
          "apimarket_claims", "apimarket_claim_responses")

BAD_ACCOUNTS = [None, "", 42, True, [], {}, 0.5, ("usr:dana",)]
BAD_CLAIM_IDS = [0, -1, "1", True, 2.5, []]
BAD_TEXTS = [None, "", "   ", 99, "x" * 501]


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


def resp_code(am, dev, claim_id, text):
    try:
        am.respond_claim(dev, claim_id, text)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3). Four purchases exist:
    bob and carol buy d1, bob and dave buy d2, dave buys d1, and carol's
    d1 purchase is refunded before any claim exists - so the refunded
    purchase face is in the world from the start."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMCR-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMCR-S",
                     "settlement")
    for who in ("bob", "carol", "dave"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    clock.value = "2026-10-06T00:00:01Z"
    d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False)["listing_id"]
    clock.value = "2026-10-06T00:00:02Z"
    d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 3, True)[
                            "listing_id"]
    clock.value = "2026-10-06T00:00:10Z"
    p_bob1 = am.purchase_api("usr:bob", d1, "BUY-AMCR-1")
    clock.value = "2026-10-06T00:00:11Z"
    p_carol1 = am.purchase_api("usr:carol", d1, "BUY-AMCR-2")
    clock.value = "2026-10-06T00:00:12Z"
    p_bob2 = am.purchase_api("usr:bob", d2, "BUY-AMCR-3")
    clock.value = "2026-10-06T00:00:13Z"
    p_dave2 = am.purchase_api("usr:dave", d2, "BUY-AMCR-4")
    clock.value = "2026-10-06T00:00:14Z"
    p_dave1 = am.purchase_api("usr:dave", d1, "BUY-AMCR-5")
    clock.value = "2026-10-06T00:00:15Z"
    am.refund_api("usr:carol", p_carol1["purchase_id"], "not needed")
    return {"d1": d1, "d2": d2, "p_bob1": p_bob1, "p_carol1": p_carol1,
            "p_bob2": p_bob2, "p_dave2": p_dave2, "p_dave1": p_dave1}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amamcr-")
    db_path = os.path.join(tmpdir, "am.db")
    cfg = RPT.load_configs()[0]
    lobby_cfg = RPT.load_configs()[1]
    led = None
    am = None
    clock = Clock()
    real_now = A._now_utc
    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}
    try:
        A._now_utc = clock.now_utc
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
        ids = seed_world(led, dk, am, clock)

        # -- AC-AMCR1 contract and derived counts -----------------------
        clock.value = "2026-10-06T00:01:00Z"
        c1 = am.open_claim("usr:bob", ids["p_bob1"]["purchase_id"],
                           "endpoint returned 500 on every call")
        clock.value = "2026-10-06T00:01:01Z"
        c2 = am.open_claim("usr:bob", ids["p_bob2"]["purchase_id"],
                           "data stale by two days")
        c3 = am.open_claim("usr:dave", ids["p_dave2"]["purchase_id"],
                           "response does not match the sample")
        clock.value = "2026-10-06T00:01:02Z"
        c4 = am.open_claim("usr:dave", ids["p_dave1"]["purchase_id"],
                           "licence header missing from the payload")
        env = am.api_claims()
        rows = env["claims"]
        ok1 = (set(env) == ENVELOPE_KEYS
               and all(set(r) == ROW_KEYS for r in rows)
               and env["claim_count"] == len(rows) == 4
               and env["open_count"] == 4
               and env["answered_count"] == 0
               and env["refunded_count"] == 0
               and all(r["status"] == "open" for r in rows)
               and all(r["response_id"] is None for r in rows)
               and all(r["response_text"] is None for r in rows)
               and all(r["responded_utc"] is None for r in rows)
               and env["disclaimer"] == DISCLAIMER)
        record("AC-AMCR1", ok1,
               "env=%r rows=%r rows=%d open=%d answered=%d refunded=%d"
               % (set(env) == ENVELOPE_KEYS,
                  all(set(r) == ROW_KEYS for r in rows),
                  env["claim_count"], env["open_count"],
                  env["answered_count"], env["refunded_count"]))

        # -- AC-AMCR2 one status seam, refunded beats answered ----------
        conn = sqlite3.connect(am.db_path)
        claim_digest_before = table_digest(conn, "apimarket_claims")
        conn.close()
        clock.value = "2026-10-06T00:02:00Z"
        a1 = am.respond_claim("usr:dana", c1["claim_id"],
                              "the upstream vendor is patching it today")
        ok_a1 = (set(a1) == DOOR_KEYS
                 and a1["status"] == "answered"
                 and a1["claim_id"] == c1["claim_id"]
                 and a1["dev_account"] == "usr:dana"
                 and a1["response_text"] ==
                 "the upstream vendor is patching it today"
                 and a1["disclaimer"] == DISCLAIMER)
        conn = sqlite3.connect(am.db_path)
        resp_digest_before = table_digest(
            conn, "apimarket_claim_responses")
        conn.close()
        env_a = am.api_claims()
        by_id = {r["claim_id"]: r for r in env_a["claims"]}
        answered_row = by_id[c1["claim_id"]]
        clock.value = "2026-10-06T00:02:10Z"
        am.refund_api("usr:bob", ids["p_bob1"]["purchase_id"], "claim")
        conn = sqlite3.connect(am.db_path)
        claim_digest_after = table_digest(conn, "apimarket_claims")
        resp_digest_after = table_digest(
            conn, "apimarket_claim_responses")
        conn.close()
        env_b = am.api_claims()
        by_id_b = {r["claim_id"]: r for r in env_b["claims"]}
        flipped = by_id_b[c1["claim_id"]]
        ok2 = (ok_a1
               and answered_row["status"] == "answered"
               and answered_row["response_id"] == a1["response_id"]
               and answered_row["responded_utc"] ==
               "2026-10-06T00:02:00Z"
               and answered_row["refund_id"] is None
               and claim_digest_before == claim_digest_after
               and resp_digest_before == resp_digest_after
               and flipped["status"] == "refunded"
               and flipped["refund_id"] is not None
               and flipped["response_id"] == a1["response_id"]
               and flipped["response_text"] == a1["response_text"]
               and by_id_b[c2["claim_id"]]["status"] == "open"
               and by_id_b[c2["claim_id"]]["response_id"] is None
               and env_b["answered_count"] == 0
               and env_b["refunded_count"] == 1
               and env_b["open_count"] == 3)
        record("AC-AMCR2", ok2,
               "door_keys=%r answered=%s refunded_wins=%s"
               " row_frozen=%r resp_frozen=%r open=%d answered=%d"
               " refunded=%d"
               % (set(a1) == DOOR_KEYS,
                  answered_row["status"] == "answered",
                  flipped["status"] == "refunded",
                  claim_digest_before == claim_digest_after,
                  resp_digest_before == resp_digest_after,
                  env_b["open_count"], env_b["answered_count"],
                  env_b["refunded_count"]))

        # -- AC-AMCR3 gate family and order -----------------------------
        clock.value = "2026-10-06T00:03:00Z"
        am.refund_api("usr:dave", ids["p_dave1"]["purchase_id"], "claim")
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        acc_codes = [resp_code(am, who, c2["claim_id"], "x")
                     for who in BAD_ACCOUNTS]
        cid_codes = [resp_code(am, "usr:dana", cid, "x")
                     for cid in BAD_CLAIM_IDS]
        text_codes = [resp_code(am, "usr:dana", c2["claim_id"], text)
                      for text in BAD_TEXTS]
        biz_codes = [resp_code(am, "usr:dana", 999999, "unknown"),
                     resp_code(am, "usr:bob", c2["claim_id"], "not mine"),
                     resp_code(am, "usr:dana", c4["claim_id"], "refunded"),
                     resp_code(am, "usr:dana", c1["claim_id"], "refunded")]
        order_codes = [resp_code(am, "bob", 0, "x"),
                       resp_code(am, "usr:dana", 0, "x"),
                       resp_code(am, "usr:dana", 999999, ""),
                       resp_code(am, "usr:dana", 999999, "unknown"),
                       resp_code(am, "usr:bob", c2["claim_id"], "ok")]
        digests_after = frozen_digests(am)
        ok3 = (acc_codes == [A.E_AM_BAD_ACCOUNT] * 8
               and cid_codes == [A.E_AM_BAD_ARGS] * 6
               and text_codes == [A.E_AM_BAD_RESPONSE] * 5
               and biz_codes == [A.E_AM_UNKNOWN_CLAIM, A.E_AM_NOT_OWNER,
                                 A.E_AM_ALREADY_REFUNDED,
                                 A.E_AM_ALREADY_REFUNDED]
               and order_codes == [A.E_AM_BAD_ACCOUNT, A.E_AM_BAD_ARGS,
                                   A.E_AM_BAD_RESPONSE,
                                   A.E_AM_UNKNOWN_CLAIM,
                                   A.E_AM_NOT_OWNER]
               and digests_before == digests_after
               and tx_before == ledger_tx_ids(led))
        record("AC-AMCR3", ok3,
               "acc=%d cid=%d text=%d biz=%r order=%r frozen=%r"
               % (len(acc_codes), len(cid_codes), len(text_codes),
                  biz_codes, order_codes,
                  digests_before == digests_after))

        # -- AC-AMCR4 one answer per claim, stamps never rewritten ------
        clock.value = "2026-10-06T00:04:00Z"
        a3 = am.respond_claim("usr:dana", c3["claim_id"],
                              "the sample file was regenerated")
        dup_code = resp_code(am, "usr:dana", c3["claim_id"], "again")
        conn = sqlite3.connect(am.db_path)
        try:
            conn.execute(
                "INSERT INTO apimarket_claim_responses (claim_id,"
                " dev_account, response_text, replied_utc)"
                " VALUES (?,?,?,?)",
                (c3["claim_id"], "usr:dana", "direct",
                 "2026-10-06T00:09:00Z"))
            unique_ok = False
        except sqlite3.IntegrityError:
            unique_ok = True
        stored = conn.execute(
            "SELECT claim_id, dev_account, replied_utc FROM"
            " apimarket_claim_responses ORDER BY response_id").fetchall()
        conn.close()
        with open(os.path.join(BASE, "apimarket.py"), "r",
                  encoding="utf-8") as handle:
            source = handle.read()
        no_update = ("UPDATE apimarket_claim_responses" not in source
                     and "DELETE FROM apimarket_claim_responses"
                     not in source)
        ok4 = (a3["status"] == "answered"
               and dup_code == A.E_AM_CLAIM_ANSWERED
               and unique_ok
               and stored == [(c1["claim_id"], "usr:dana",
                               "2026-10-06T00:02:00Z"),
                              (c3["claim_id"], "usr:dana",
                               "2026-10-06T00:04:00Z")]
               and no_update)
        record("AC-AMCR4", ok4,
               "dup=%s unique=%r stamps=%r no_update=%r"
               % (dup_code, unique_ok,
                  [r[2] for r in stored], no_update))

        # -- AC-AMCR5 views, isolation and derived answer counts --------
        bob_view = am.api_claims(buyer_id="usr:bob")
        dave_view = am.api_claims(buyer_id="usr:dave")
        dana_view = am.api_claims(dev_account="usr:dana")
        carol_view = am.api_claims(buyer_id="usr:carol")
        both_view = am.api_claims(buyer_id="usr:dave",
                                  dev_account="usr:dana")
        gate_codes = []
        for bad in BAD_ACCOUNTS[1:]:
            try:
                am.api_claims(buyer_id=bad)
                gate_codes.append("NO-RAISE")
            except A.ApiMarketError as exc:
                gate_codes.append(code_of(exc))
        try:
            am.api_claims(dev_account="")
            gate_codes.append("NO-RAISE")
        except A.ApiMarketError as exc:
            gate_codes.append(code_of(exc))
        ok5 = (bob_view["claim_count"] == 2
               and bob_view["open_count"] == 1
               and bob_view["answered_count"] == 0
               and bob_view["refunded_count"] == 1
               and all(r["buyer_id"] == "usr:bob"
                       for r in bob_view["claims"])
               and dave_view["claim_count"] == 2
               and dave_view["answered_count"] == 1
               and dave_view["refunded_count"] == 1
               and dana_view["claim_count"] == 4
               and dana_view["answered_count"] == 1
               and dana_view["open_count"] == 1
               and dana_view["refunded_count"] == 2
               and carol_view["claim_count"] == 0
               and carol_view["claims"] == []
               and both_view["claim_count"] == 2
               and am.api_claims()["claim_count"] == 4
               and gate_codes == [A.E_AM_BAD_ACCOUNT] * 8)
        record("AC-AMCR5", ok5,
               "bob=%d dave=%d dana=%d carol=%d both=%d"
               " answered=%d gates=%r"
               % (bob_view["claim_count"], dave_view["claim_count"],
                  dana_view["claim_count"], carol_view["claim_count"],
                  both_view["claim_count"], dana_view["answered_count"],
                  gate_codes))

        # -- AC-AMCR6 pure read and zero token movement -----------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        runs = [dumps(am.api_claims()), dumps(am.api_claims()),
                dumps(am.api_claims())]
        digests_after = frozen_digests(am)
        ok6 = (runs[0] == runs[1] == runs[2]
               and digests_before == digests_after
               and tx_before == ledger_tx_ids(led))
        record("AC-AMCR6", ok6,
               "three_runs=%r frozen=%r tx_constant=%r"
               % (runs[0] == runs[1] == runs[2],
                  digests_before == digests_after,
                  tx_before == ledger_tx_ids(led)))

        # -- AC-AMCR7 determinism and cross-restart identity ------------
        baseline_market = dumps(am.api_claims())
        baseline_boby = dumps(am.api_claims(buyer_id="usr:bob"))
        baseline_dana = dumps(am.api_claims(dev_account="usr:dana"))
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_claims()))
            replays.append(dumps(am2.api_claims(buyer_id="usr:bob")))
            replays.append(dumps(am2.api_claims(dev_account="usr:dana")))
            close_stack(am2, dk2, metered2, led2)
        ok7 = (replays[0] == baseline_market == replays[3]
               and replays[1] == baseline_boby == replays[4]
               and replays[2] == baseline_dana == replays[5])
        record("AC-AMCR7", ok7,
               "restart_market=%r restart_buyer=%r restart_seller=%r"
               % (replays[0] == replays[3], replays[1] == replays[4],
                  replays[2] == replays[5]))

        # -- AC-AMCR8 delivery hygiene ----------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-claims-respond"' in handle.read())
        with open(os.path.abspath(__file__), "rb") as handle:
            own = handle.read()
        ascii_ok = True
        try:
            own.decode("ascii")
        except UnicodeDecodeError:
            ascii_ok = False
        net_marks = {"requests", "urllib", "socket", "http", "ftplib",
                     "smtplib", "telnetlib"}
        mods = set()
        for node in ast.walk(ast.parse(own)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        net_ok = not (mods & net_marks)
        outside_ok = not os.path.abspath(db_path).startswith(
            os.path.join(os.path.dirname(BASE), ""))
        shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
        shipped_ok = (shas_after[PRODUCT_FILES[2]]
                      == shas_before[PRODUCT_FILES[2]]
                      and shas_after[PRODUCT_FILES[3]]
                      == shas_before[PRODUCT_FILES[3]])
        ok8 = (wired and ascii_ok and net_ok and shipped_ok and outside_ok)
        record("AC-AMCR8", ok8,
               "wired=%r ascii=%r no_net=%r shipped=%r outside=%r"
               % (wired, ascii_ok, net_ok, shipped_ok, outside_ok))

        passed = sum(1 for _ac, ok in RESULTS if ok)
        print("\nSUITE %s %d/%d"
              % ("PASS" if passed == len(RESULTS) else "FAIL", passed,
                 len(RESULTS)), flush=True)
        return 0 if passed == len(RESULTS) else 1
    finally:
        A._now_utc = real_now
        if am is not None:
            try:
                am.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())