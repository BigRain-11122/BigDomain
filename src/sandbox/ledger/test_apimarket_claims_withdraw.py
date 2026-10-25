#!/usr/bin/env python3
"""Claim withdrawal door suite - the closing act of the post-sale claim.

(BigDomain R2131; canon = the explore-queue row claimed in R2131,
criteria AC-AMCW1..AC-AMCW8 registered in that claim note BEFORE this
suite existed; the AC-AMCW prefix, withdraw_claim,
apimarket_claim_withdrawals, E_AM_CLAIM_WITHDRAWN and withdrawn_utc
were all git grep -F zero-occupancy anchored 2026-10-25, rc=1.)

Face under proof: APIMarketFace.withdraw_claim + the api_claims
withdrawal extension. After R2129 (open_claim) and R2130
(respond_claim) the chain still had no closing act: a claim opened by
mistake, settled off-platform or fixed privately stayed open (or
answered) forever and kept polluting the seller queue and the
market-wide queue, because a refund was the only exit and that door
fails closed once the seller spent the proceeds. This slot pins:

  - the eleven-key door envelope, the nine-key queue envelope and the
    sixteen-key row (R2130 fifteen plus withdrawn_utc), with
    claim_count == open + answered + refunded + withdrawn;
  - status derived in ONE place with the precedence
    refunded > withdrawn > answered > open, and the claim row, the
    response row and the withdrawal row never rewritten;
  - the gate family and its order: account, claim-id shape, claim
    existence, ownership, already-refunded, duplicate, with frozen
    table digests and a constant ledger tx set;
  - one withdrawal per claim (table UNIQUE), first stamp never
    rewritten, no UPDATE surface;
  - buyer / seller / market views carrying withdrawn_utc with the four
    counts derived from the filtered set and strict isolation;
  - pure read on api_claims, zero token movement on the door, three
    identical in-process runs and two full-stack restarts;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_claims_withdraw.py
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

DOOR_KEYS = {"claim_id", "purchase_id", "listing_id", "buyer_id",
             "dev_account", "price_paid", "claim_text", "opened_utc",
             "withdrawn_utc", "status", "disclaimer"}

ENVELOPE_KEYS = {"buyer_id", "dev_account", "claim_count", "open_count",
                 "answered_count", "refunded_count", "withdrawn_count",
                 "disclaimer", "claims"}

ROW_KEYS = {"claim_id", "purchase_id", "listing_id", "listing_title",
            "dev_account", "buyer_id", "price_paid", "claim_text",
            "opened_utc", "status", "refund_id", "refunded_utc",
            "response_id", "response_text", "responded_utc",
            "withdrawn_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers", "apimarket_reviews",
          "apimarket_claims", "apimarket_claim_responses",
          "apimarket_claim_withdrawals")

BAD_ACCOUNTS = [None, "", 42, True, [], {}, 0.5, ("usr:dana",)]
BAD_CLAIM_IDS = [0, -1, "1", True, 2.5, []]


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
    return {acct: led.balance(acct)
            for acct in ("usr:bob", "usr:carol", "usr:dave", "usr:dana")}


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


def wd_code(am, buyer, claim_id):
    try:
        am.withdraw_claim(buyer, claim_id)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3). Five purchases exist:
    bob and carol buy d1, bob and dave buy d2, dave buys d1 again, and
    carol's d1 purchase is refunded before any claim exists - so the
    refunded purchase face is in the world from the start."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMCW-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMCW-S",
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
    p_bob1 = am.purchase_api("usr:bob", d1, "BUY-AMCW-1")
    clock.value = "2026-10-06T00:00:11Z"
    p_carol1 = am.purchase_api("usr:carol", d1, "BUY-AMCW-2")
    clock.value = "2026-10-06T00:00:12Z"
    p_bob2 = am.purchase_api("usr:bob", d2, "BUY-AMCW-3")
    clock.value = "2026-10-06T00:00:13Z"
    p_dave2 = am.purchase_api("usr:dave", d2, "BUY-AMCW-4")
    clock.value = "2026-10-06T00:00:14Z"
    p_dave1 = am.purchase_api("usr:dave", d1, "BUY-AMCW-5")
    clock.value = "2026-10-06T00:00:15Z"
    am.refund_api("usr:carol", p_carol1["purchase_id"], "not needed")
    return {"d1": d1, "d2": d2, "p_bob1": p_bob1, "p_carol1": p_carol1,
            "p_bob2": p_bob2, "p_dave2": p_dave2, "p_dave1": p_dave1}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amamcw-")
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

        # -- AC-AMCW1 contract and derived counts -----------------------
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
        clock.value = "2026-10-06T00:02:00Z"
        w1 = am.withdraw_claim("usr:bob", c1["claim_id"])
        ok1 = (set(w1) == DOOR_KEYS
               and w1["claim_id"] == c1["claim_id"]
               and w1["status"] == "withdrawn"
               and w1["buyer_id"] == "usr:bob"
               and w1["dev_account"] == "usr:dana"
               and w1["price_paid"] == 10
               and w1["opened_utc"] == "2026-10-06T00:01:00Z"
               and w1["withdrawn_utc"] == "2026-10-06T00:02:00Z"
               and w1["disclaimer"] == DISCLAIMER)
        env = am.api_claims()
        rows = env["claims"]
        ok1 = (ok1 and ENVELOPE_KEYS <= set(env)
               and all(ROW_KEYS <= set(r) for r in rows)
               and env["claim_count"] == len(rows) == 4
               and env["open_count"] == 3
               and env["answered_count"] == 0
               and env["refunded_count"] == 0
               and env["withdrawn_count"] == 1
               and env["disclaimer"] == DISCLAIMER)
        record("AC-AMCW1", ok1,
               "door=%r env=%r row=%r rows=%d open=%d answered=%d"
               " refunded=%d withdrawn=%d"
               % (set(w1) == DOOR_KEYS, ENVELOPE_KEYS <= set(env),
                  all(ROW_KEYS <= set(r) for r in rows),
                  env["claim_count"], env["open_count"],
                  env["answered_count"], env["refunded_count"],
                  env["withdrawn_count"]))

        # -- AC-AMCW2 one status seam, refunded still wins --------------
        conn = sqlite3.connect(am.db_path)
        claim_digest_before = table_digest(conn, "apimarket_claims")
        conn.close()
        clock.value = "2026-10-06T00:03:00Z"
        am.respond_claim("usr:dana", c2["claim_id"],
                         "the feed vendor is backfilling the gap")
        conn = sqlite3.connect(am.db_path)
        resp_digest_before = table_digest(
            conn, "apimarket_claim_responses")
        conn.close()
        env_answ = am.api_claims()
        by_id = {r["claim_id"]: r for r in env_answ["claims"]}
        answered_row = by_id[c2["claim_id"]]
        clock.value = "2026-10-06T00:03:10Z"
        w2 = am.withdraw_claim("usr:bob", c2["claim_id"])
        conn = sqlite3.connect(am.db_path)
        claim_digest_after = table_digest(conn, "apimarket_claims")
        resp_digest_after = table_digest(
            conn, "apimarket_claim_responses")
        conn.close()
        env_after = am.api_claims()
        by_id2 = {r["claim_id"]: r for r in env_after["claims"]}
        withdrawn_row = by_id2[c2["claim_id"]]
        clock.value = "2026-10-06T00:03:20Z"
        am.refund_api("usr:dave", ids["p_dave1"]["purchase_id"], "claim")
        env_refund = am.api_claims()
        by_id3 = {r["claim_id"]: r for r in env_refund["claims"]}
        refunded_row = by_id3[c4["claim_id"]]
        ok2 = (w2["status"] == "withdrawn"
               and answered_row["status"] == "answered"
               and answered_row["response_id"] is not None
               and withdrawn_row["status"] == "withdrawn"
               and withdrawn_row["response_id"] ==
               answered_row["response_id"]
               and withdrawn_row["response_text"] ==
               answered_row["response_text"]
               and claim_digest_before == claim_digest_after
               and resp_digest_before == resp_digest_after
               and refunded_row["status"] == "refunded"
               and refunded_row["withdrawn_utc"] is None
               and by_id3[c3["claim_id"]]["status"] == "open"
               and env_refund["withdrawn_count"] == 2
               and env_refund["refunded_count"] == 1
               and env_refund["answered_count"] == 0
               and env_refund["open_count"] == 1)
        record("AC-AMCW2", ok2,
               "answered_before=%r withdrawn_after=%r rows_frozen=%r"
               " refunded_after=%r counts=%r"
               % (answered_row["status"], withdrawn_row["status"],
                  claim_digest_before == claim_digest_after
                  and resp_digest_before == resp_digest_after,
                  refunded_row["status"],
                  (env_refund["open_count"],
                   env_refund["answered_count"],
                   env_refund["refunded_count"],
                   env_refund["withdrawn_count"])))

        # -- AC-AMCW3 gate family, order and zero side effects ----------
        digests_pre = frozen_digests(am)
        tx_pre = ledger_tx_ids(led)
        bal_pre = pool_balances(led)
        gate_codes = [wd_code(am, bad, c3["claim_id"])
                      for bad in BAD_ACCOUNTS]
        id_codes = [wd_code(am, "usr:dave", bad) for bad in BAD_CLAIM_IDS]
        unknown_code = wd_code(am, "usr:dave", 9999)
        owner_codes = [wd_code(am, "usr:dana", c3["claim_id"]),
                       wd_code(am, "usr:bob", c3["claim_id"])]
        refunded_code = wd_code(am, "usr:dave", c4["claim_id"])
        dup_code = wd_code(am, "usr:bob", c1["claim_id"])
        # double-bad probes resolve the earlier gate first
        order_codes = [wd_code(am, "", 0), wd_code(am, "usr:dave", 0),
                       wd_code(am, "usr:dave", 9999),
                       wd_code(am, "usr:dana", 9999)]
        digests_post = frozen_digests(am)
        ok3 = (gate_codes == [A.E_AM_BAD_ACCOUNT] * 8
               and id_codes == [A.E_AM_BAD_ARGS] * 6
               and unknown_code == A.E_AM_UNKNOWN_CLAIM
               and owner_codes == [A.E_AM_NOT_BUYER] * 2
               and refunded_code == A.E_AM_ALREADY_REFUNDED
               and dup_code == A.E_AM_CLAIM_WITHDRAWN
               and order_codes == [A.E_AM_BAD_ACCOUNT,
                                   A.E_AM_BAD_ARGS,
                                   A.E_AM_UNKNOWN_CLAIM,
                                   A.E_AM_UNKNOWN_CLAIM]
               and digests_pre == digests_post
               and tx_pre == ledger_tx_ids(led)
               and bal_pre == pool_balances(led))
        record("AC-AMCW3", ok3,
               "account=%r id=%r unknown=%r owner=%r refunded=%r"
               " dup=%r order=%r frozen=%r"
               % (set(gate_codes), set(id_codes), unknown_code,
                  owner_codes, refunded_code, dup_code, order_codes,
                  digests_pre == digests_post))

        # -- AC-AMCW4 one withdrawal per claim, no UPDATE surface -------
        conn = sqlite3.connect(am.db_path)
        wd_rows = conn.execute(
            "SELECT claim_id, buyer_id, withdrawn_utc"
            " FROM apimarket_claim_withdrawals"
            " ORDER BY claim_id").fetchall()
        conn.close()
        stamps = [r[2] for r in wd_rows]
        ok4 = (len(wd_rows) == 2
               and [r[0] for r in wd_rows] ==
               [c1["claim_id"], c2["claim_id"]]
               and [r[1] for r in wd_rows] == ["usr:bob", "usr:bob"]
               and stamps == ["2026-10-06T00:02:00Z",
                              "2026-10-06T00:03:10Z"]
               and wd_code(am, "usr:bob", c1["claim_id"]) ==
               A.E_AM_CLAIM_WITHDRAWN)
        record("AC-AMCW4", ok4,
               "rows=%r stamps=%r rows=%d" % (wd_rows, stamps,
                                              len(wd_rows)))

        # -- AC-AMCW5 three views, counts and isolation -----------------
        bob_view = am.api_claims(buyer_id="usr:bob")
        dave_view = am.api_claims(buyer_id="usr:dave")
        dana_view = am.api_claims(dev_account="usr:dana")
        carol_view = am.api_claims(buyer_id="usr:carol")
        both_view = am.api_claims(buyer_id="usr:dave",
                                  dev_account="usr:dana")
        gate_codes2 = []
        for bad in ("", 42, True, [], {}, 0.5, ("usr:bob",)):
            try:
                am.api_claims(buyer_id=bad)
                gate_codes2.append("NO-RAISE")
            except A.ApiMarketError as exc:
                gate_codes2.append(code_of(exc))
        ok5 = (bob_view["claim_count"] == 2
               and bob_view["withdrawn_count"] == 2
               and dave_view["claim_count"] == 2
               and dave_view["open_count"] == 1
               and dave_view["refunded_count"] == 1
               and dana_view["claim_count"] == 4
               and dana_view["withdrawn_count"] == 2
               and carol_view["claim_count"] == 0
               and carol_view["claims"] == []
               and both_view["claim_count"] == 2
               and all(r["withdrawn_utc"] is not None
                       for r in bob_view["claims"])
               and all(r["buyer_id"] == "usr:bob"
                       for r in bob_view["claims"])
               and all(r["dev_account"] == "usr:dana"
                       for r in dana_view["claims"])
               and gate_codes2 == [A.E_AM_BAD_ACCOUNT] * 7)
        record("AC-AMCW5", ok5,
               "bob=%d/%d dave=%d/%d dana=%d/%d carol=%d both=%d"
               " gates=%r"
               % (bob_view["claim_count"], bob_view["withdrawn_count"],
                  dave_view["claim_count"], dave_view["open_count"],
                  dana_view["claim_count"], dana_view["withdrawn_count"],
                  carol_view["claim_count"], both_view["claim_count"],
                  gate_codes2))

        # -- AC-AMCW6 pure read and zero token movement -----------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        bal_before = pool_balances(led)
        runs = [dumps(am.api_claims()), dumps(am.api_claims()),
                dumps(am.api_claims())]
        digests_after = frozen_digests(am)
        ok6 = (runs[0] == runs[1] == runs[2]
               and digests_before == digests_after
               and tx_before == ledger_tx_ids(led)
               and bal_before == pool_balances(led))
        record("AC-AMCW6", ok6,
               "three_runs=%r frozen=%r tx_constant=%r balance=%r"
               % (runs[0] == runs[1] == runs[2],
                  digests_before == digests_after,
                  tx_before == ledger_tx_ids(led),
                  bal_before == pool_balances(led)))

        # -- AC-AMCW7 determinism and cross-restart identity ------------
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
        record("AC-AMCW7", ok7,
               "restart_market=%r restart_buyer=%r restart_seller=%r"
               % (replays[0] == replays[3], replays[1] == replays[4],
                  replays[2] == replays[5]))

        # -- AC-AMCW8 delivery hygiene ----------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-claims-withdraw"' in handle.read())
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
        record("AC-AMCW8", ok8,
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