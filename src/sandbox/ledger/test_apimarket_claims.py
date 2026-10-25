"""Acceptance suite for the apimarket post-sale claim registry
(BigDomain R2129; canon = the explore-queue row claimed in R2129,
criteria AC-AMCL1..AC-AMCL8 registered in that claim note BEFORE this
suite existed; the AC-AMCL prefix, open_claim, api_claims,
apimarket_claims, E_AM_CLAIM_DUP, E_AM_BAD_CLAIM, this suite name and
the ledger-apimarket-claims runner label were all git grep -F
zero-occupancy anchored 2026-10-25, rc=1).

Face under proof: APIMarketFace.open_claim + api_claims. The refund
door fails closed when the seller already spent the proceeds
(E_AM_REFUND_UNFUNDABLE, refuse-never-chase); after that refusal the
product had no surface at all - the buyer could not lodge the complaint
and the seller had no queue of disputed purchases. This slot pins:

  - the ten-key door envelope, the seven-key queue envelope and the
    twelve-key row, with claim_count == len(claims) == open + refunded;
  - status derived from the refunds table only (a claim row carries no
    status column and is never rewritten when a refund lands later);
  - the gate family and its order: account, purchase-id shape, claim
    text shape, purchase existence, ownership, already-refunded,
    duplicate, with frozen table digests and a constant ledger tx set
    around every refusal;
  - one claim per purchase (table UNIQUE), first stamp never rewritten,
    another purchase of the same buyer stays claimable;
  - buyer / seller / market views through one filter param pair, with
    strict isolation, an honest empty envelope and combined AND filters;
  - ordering by (opened_utc, claim_id) ascending with ties broken by
    id, and immediacy in both views after opening;
  - pure read, three identical in-process runs and two full-stack
    restarts replaying all three views byte-identically;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_claims.py
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
             "status", "disclaimer"}

ENVELOPE_KEYS = {"buyer_id", "dev_account", "claim_count", "open_count",
                 "refunded_count", "disclaimer", "claims"}

ROW_KEYS = {"claim_id", "purchase_id", "listing_id", "listing_title",
            "dev_account", "buyer_id", "price_paid", "claim_text",
            "opened_utc", "status", "refund_id", "refunded_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers", "apimarket_reviews",
          "apimarket_claims")

BAD_ACCOUNTS = [None, "", "bob", "USR:bob", " usr:bob", 42, True, []]
BAD_PURCHASES = [0, -1, "1", True, 2.5, []]
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


def claim_code(am, buyer, purchase_id, text):
    try:
        am.open_claim(buyer, purchase_id, text)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3). bob and carol buy d1,
    bob and dave buy d2, then carol refunds her d1 purchase (funded), so
    one purchase is already refunded before any claim exists."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMCL-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMCL-S",
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
    p_bob1 = am.purchase_api("usr:bob", d1, "BUY-AMCL-1")
    clock.value = "2026-10-06T00:00:11Z"
    p_carol1 = am.purchase_api("usr:carol", d1, "BUY-AMCL-2")
    clock.value = "2026-10-06T00:00:12Z"
    p_bob2 = am.purchase_api("usr:bob", d2, "BUY-AMCL-3")
    clock.value = "2026-10-06T00:00:13Z"
    p_dave2 = am.purchase_api("usr:dave", d2, "BUY-AMCL-4")
    clock.value = "2026-10-06T00:00:14Z"
    am.refund_api("usr:carol", p_carol1["purchase_id"], "not needed")
    return {"d1": d1, "d2": d2, "p_bob1": p_bob1, "p_carol1": p_carol1,
            "p_bob2": p_bob2, "p_dave2": p_dave2}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amamcl-")
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

        # -- AC-AMCL1 contract and derived counts -----------------------
        clock.value = "2026-10-06T00:01:00Z"
        c1 = am.open_claim("usr:bob", ids["p_bob1"]["purchase_id"],
                           "endpoint returned 500 on every call")
        clock.value = "2026-10-06T00:01:01Z"
        c2 = am.open_claim("usr:bob", ids["p_bob2"]["purchase_id"],
                           "data stale by two days")
        c3 = am.open_claim("usr:dave", ids["p_dave2"]["purchase_id"],
                           "response does not match the sample")
        env = am.api_claims()
        rows = env["claims"]
        ok1 = (set(c1) == DOOR_KEYS
               and set(env) == ENVELOPE_KEYS
               and all(set(r) == ROW_KEYS for r in rows)
               and env["claim_count"] == len(rows) == 3
               and env["open_count"] == 3
               and env["refunded_count"] == 0
               and c1["status"] == "open"
               and c1["price_paid"] == 10
               and c1["dev_account"] == "usr:dana"
               and c1["listing_id"] == ids["d1"]
               and env["disclaimer"] == DISCLAIMER)
        record("AC-AMCL1", ok1,
               "door=%r env=%r rows=%d open=%d refunded=%d"
               % (set(c1) == DOOR_KEYS, set(env) == ENVELOPE_KEYS,
                  env["claim_count"], env["open_count"],
                  env["refunded_count"]))

        # -- AC-AMCL2 status derives from the refunds table only --------
        conn = sqlite3.connect(am.db_path)
        claim_digest_before = table_digest(conn, "apimarket_claims")
        conn.close()
        clock.value = "2026-10-06T00:02:00Z"
        am.refund_api("usr:bob", ids["p_bob2"]["purchase_id"], "claim")
        conn = sqlite3.connect(am.db_path)
        claim_digest_after = table_digest(conn, "apimarket_claims")
        conn.close()
        env2 = am.api_claims()
        by_id = {r["claim_id"]: r for r in env2["claims"]}
        flipped = by_id[c2["claim_id"]]
        ok2 = (claim_digest_before == claim_digest_after
               and flipped["status"] == "refunded"
               and flipped["refund_id"] is not None
               and flipped["refunded_utc"] is not None
               and flipped["claim_text"] == c2["claim_text"]
               and flipped["opened_utc"] == c2["opened_utc"]
               and by_id[c1["claim_id"]]["status"] == "open"
               and by_id[c1["claim_id"]]["refund_id"] is None
               and env2["open_count"] == 2
               and env2["refunded_count"] == 1)
        record("AC-AMCL2", ok2,
               "row_frozen=%r status=%s open=%d refunded=%d"
               % (claim_digest_before == claim_digest_after,
                  flipped["status"], env2["open_count"],
                  env2["refunded_count"]))

        # -- AC-AMCL3 gate family and order -----------------------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        carol_purchase = ids["p_carol1"]["purchase_id"]
        bob_purchase = ids["p_bob1"]["purchase_id"]
        acc_codes = [claim_code(am, who, bob_purchase, "x")
                     for who in BAD_ACCOUNTS]
        pid_codes = [claim_code(am, "usr:bob", pid, "x")
                     for pid in BAD_PURCHASES]
        text_codes = [claim_code(am, "usr:bob", bob_purchase, text)
                      for text in BAD_TEXTS]
        biz_codes = [claim_code(am, "usr:bob", 999999, "unknown"),
                     claim_code(am, "usr:dave", bob_purchase, "not mine"),
                     claim_code(am, "usr:carol", carol_purchase, "refunded"),
                     claim_code(am, "usr:bob", bob_purchase, "again")]
        order_codes = [claim_code(am, "bob", 0, "x"),
                       claim_code(am, "usr:bob", 0, "x"),
                       claim_code(am, "usr:bob", 999999, ""),
                       claim_code(am, "usr:bob", 999999, "unknown"),
                       claim_code(am, "usr:carol", carol_purchase, "ok")]
        digests_after = frozen_digests(am)
        ok3 = (acc_codes == [A.E_AM_BAD_ACCOUNT] * 8
               and pid_codes == [A.E_AM_BAD_ARGS] * 6
               and text_codes == [A.E_AM_BAD_CLAIM] * 5
               and biz_codes == [A.E_AM_UNKNOWN_PURCHASE, A.E_AM_NOT_BUYER,
                                 A.E_AM_ALREADY_REFUNDED,
                                 A.E_AM_CLAIM_DUP]
               and order_codes == [A.E_AM_BAD_ACCOUNT, A.E_AM_BAD_ARGS,
                                   A.E_AM_BAD_CLAIM,
                                   A.E_AM_UNKNOWN_PURCHASE,
                                   A.E_AM_ALREADY_REFUNDED]
               and digests_before == digests_after
               and tx_before == ledger_tx_ids(led))
        record("AC-AMCL3", ok3,
               "acc=%d pid=%d text=%d biz=%r order=%r frozen=%r"
               % (len(acc_codes), len(pid_codes), len(text_codes),
                  biz_codes, order_codes, digests_before == digests_after))

        # -- AC-AMCL4 one claim per purchase, stamps never rewritten ----
        conn = sqlite3.connect(am.db_path)
        stored = conn.execute(
            "SELECT claim_id, purchase_id, opened_utc FROM"
            " apimarket_claims ORDER BY claim_id").fetchall()
        conn.close()
        conn = sqlite3.connect(am.db_path)
        try:
            conn.execute(
                "INSERT INTO apimarket_claims (purchase_id, listing_id,"
                " buyer_id, dev_account, price_paid, claim_text,"
                " opened_utc) VALUES (?,?,?,?,?,?,?)",
                (bob_purchase, ids["d1"], "usr:bob", "usr:dana", 10,
                 "direct", "2026-10-06T00:09:00Z"))
            unique_ok = False
        except sqlite3.IntegrityError:
            unique_ok = True
        finally:
            conn.close()
        ok4 = (unique_ok
               and [r[0] for r in stored] == [c1["claim_id"],
                                              c2["claim_id"],
                                              c3["claim_id"]]
               and stored[0][2] == "2026-10-06T00:01:00Z"
               and stored[1][2] == "2026-10-06T00:01:01Z")
        record("AC-AMCL4", ok4,
               "unique=%r rows=%r" % (unique_ok, [r[0] for r in stored]))

        # -- AC-AMCL5 isolation, empty state and combined filters -------
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
        # None is the absence of a filter, not a bad form: the
        # unfiltered call is the market view proven above (3 rows).
        ok5 = (bob_view["claim_count"] == 2
               and all(r["buyer_id"] == "usr:bob" for r in bob_view["claims"])
               and dave_view["claim_count"] == 1
               and dana_view["claim_count"] == 3
               and carol_view["claim_count"] == 0
               and carol_view["claims"] == []
               and both_view["claim_count"] == 1
               and both_view["claims"][0]["buyer_id"] == "usr:dave"
               and am.api_claims(buyer_id=None)["claim_count"] == 3
               and gate_codes == [A.E_AM_BAD_ACCOUNT] * 8)
        record("AC-AMCL5", ok5,
               "bob=%d dave=%d dana=%d carol=%d both=%d gates=%r"
               % (bob_view["claim_count"], dave_view["claim_count"],
                  dana_view["claim_count"], carol_view["claim_count"],
                  both_view["claim_count"], gate_codes))

        # -- AC-AMCL6 ordering (oldest first, ties by id) ---------------
        order = [(r["opened_utc"], r["claim_id"]) for r in env2["claims"]]
        tie_group = [cid for stamp, cid in order
                     if stamp == "2026-10-06T00:01:01Z"]
        ok6 = (order == sorted(order)
               and tie_group == sorted(tie_group)
               and tie_group == [c2["claim_id"], c3["claim_id"]]
               and order[0][1] == c1["claim_id"]
               and order[-1][0] == "2026-10-06T00:01:01Z")
        record("AC-AMCL6", ok6, "order=%r ties=%r" % (order, tie_group))

        # -- AC-AMCL7 pure read and cross-restart identity --------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        runs = [dumps(am.api_claims()), dumps(am.api_claims()),
                dumps(am.api_claims())]
        digests_after = frozen_digests(am)
        pure_ok = (runs[0] == runs[1] == runs[2]
                   and digests_before == digests_after
                   and tx_before == ledger_tx_ids(led))
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
        ok7 = (pure_ok
               and replays[0] == baseline_market == replays[3]
               and replays[1] == baseline_boby == replays[4]
               and replays[2] == baseline_dana == replays[5])
        record("AC-AMCL7", ok7,
               "pure=%r restart_market=%r restart_buyer=%r"
               " restart_seller=%r"
               % (pure_ok, replays[0] == replays[3],
                  replays[1] == replays[4], replays[2] == replays[5]))

        # -- AC-AMCL8 delivery hygiene ----------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-claims"' in handle.read())
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
        record("AC-AMCL8", ok8,
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