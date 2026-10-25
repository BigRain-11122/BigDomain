#!/usr/bin/env python3
"""Claim follow-up note and claim thread suite.

(BigDomain R2137; canon = the explore-queue row claimed in R2137,
criteria AC-AMCN1..AC-AMCN8 registered in that claim note BEFORE this
suite existed; the AC-AMCN prefix, add_claim_note, api_claim_thread,
apimarket_claim_notes, E_AM_BAD_NOTE and E_AM_CLAIM_NOTE_DUP were all
git grep -F zero-occupancy anchored 2026-10-26, rc=1.)

Face under proof: APIMarketFace.add_claim_note + api_claim_thread.
After R2129 (open_claim), R2130 (respond_claim) and R2131
(withdraw_claim) the claim thread was still one-way: once the seller
answered, a buyer who did not accept that answer had only two exits -
withdraw (give up) or wait for a refund the seller may never issue -
and neither side could separate an accepted answer from a disputed one.
This slot pins:

  - the ten-key door envelope, the append-only one-note-per-claim
    table, the stripped text and the first stamp never rewritten;
  - the fifteen-key thread envelope, the enumerated event stream
    ordered by stamp then by a pinned same-second rank
    (opened < answered < note < withdrawn < refunded), the buyer and
    seller payloads byte-identical apart from viewer_role, and the
    disputed flag false once the claim is refunded or withdrawn;
  - the door gate family and its order (account, claim-id shape, note
    shape, existence, ownership, already-refunded, withdrawn,
    duplicate) and the thread gate order (account, shape, existence,
    party) with frozen table digests and a constant ledger tx set;
  - one note per claim enforced by the table UNIQUE, no UPDATE surface,
    and a refund landing later leaving the note byte-identical;
  - pure read on the thread, zero token movement on the door, three
    identical in-process runs and two full-stack restarts;
  - delivery hygiene (runner label wired, pure ASCII source, zero
    network imports, shipped configs unchanged, temp world outside the
    repo).

Usage: python test_apimarket_claimnote.py
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

DOOR_KEYS = {"note_id", "claim_id", "purchase_id", "listing_id",
             "buyer_id", "dev_account", "note_text", "noted_utc",
             "status", "disclaimer"}

THREAD_KEYS = {"claim_id", "purchase_id", "listing_id",
               "listing_title", "buyer_id", "dev_account",
               "viewer_role", "price_paid", "claim_text",
               "opened_utc", "status", "disputed", "event_count",
               "events", "disclaimer"}

EVENT_KEYS = {"kind", "utc", "actor", "text", "rank"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers", "apimarket_providers", "apimarket_reviews",
          "apimarket_claims", "apimarket_claim_responses",
          "apimarket_claim_withdrawals", "apimarket_claim_notes")

BAD_ACCOUNTS = [None, "", 42, True, [], {}, 0.5, ("usr:bob",)]
BAD_CLAIM_IDS = [0, -1, "1", True, 2.5, []]
BAD_TEXTS = [None, "", "   ", "x" * 501, 42, [], {}]


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


def note_code(am, buyer, claim_id, text):
    try:
        am.add_claim_note(buyer, claim_id, text)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def thread_code(am, claim_id, account):
    try:
        am.api_claim_thread(claim_id, account)
    except A.ApiMarketError as exc:
        return code_of(exc)
    return "NO-RAISE"


def seed_world(led, dk, am, clock):
    """dana owns d1 (price 10) and d2 (price 3). Four purchases exist:
    bob on d1, carol on d1, dave on d1, bob on d2. Every purchase gets
    a claim, so the world carries all four claim shapes: answered with
    a buyer follow-up, refunded after a claim, withdrawn after a
    follow-up, and still open with no answer."""
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-AMCN-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-AMCN-S",
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
    p_bob1 = am.purchase_api("usr:bob", d1, "BUY-AMCN-1")
    clock.value = "2026-10-06T00:00:11Z"
    p_carol1 = am.purchase_api("usr:carol", d1, "BUY-AMCN-2")
    clock.value = "2026-10-06T00:00:12Z"
    p_dave1 = am.purchase_api("usr:dave", d1, "BUY-AMCN-3")
    clock.value = "2026-10-06T00:00:13Z"
    p_bob2 = am.purchase_api("usr:bob", d2, "BUY-AMCN-4")
    return {"d1": d1, "d2": d2, "p_bob1": p_bob1, "p_carol1": p_carol1,
            "p_dave1": p_dave1, "p_bob2": p_bob2}


def main():
    tmpdir = tempfile.mkdtemp(prefix="amamcn-")
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

        # -- AC-AMCN1 door contract -------------------------------------
        clock.value = "2026-10-06T00:01:00Z"
        c_bob = am.open_claim("usr:bob", ids["p_bob1"]["purchase_id"],
                             "endpoint returned 500 on every call")
        clock.value = "2026-10-06T00:01:01Z"
        c_carol = am.open_claim("usr:carol",
                               ids["p_carol1"]["purchase_id"],
                               "the feed stopped updating after a day")
        clock.value = "2026-10-06T00:01:02Z"
        c_dave = am.open_claim("usr:dave", ids["p_dave1"]["purchase_id"],
                              "schema changed without notice")
        clock.value = "2026-10-06T00:01:03Z"
        c_bob2 = am.open_claim("usr:bob", ids["p_bob2"]["purchase_id"],
                              "daily file was empty twice")
        clock.value = "2026-10-06T00:01:10Z"
        am.respond_claim("usr:dana", c_bob["claim_id"],
                         "we are redeploying the endpoint today")
        clock.value = "2026-10-06T00:01:20Z"
        n_bob = am.add_claim_note("usr:bob", c_bob["claim_id"],
                                  "  still failing after the redeploy  ")
        digests_seed = frozen_digests(am)
        conn = sqlite3.connect(am.db_path)
        stored = conn.execute(
            "SELECT claim_id, buyer_id, note_text, noted_utc"
            " FROM apimarket_claim_notes ORDER BY note_id").fetchall()
        conn.close()
        ok1 = (set(n_bob.keys()) == DOOR_KEYS
               and n_bob["note_text"] == "still failing after the"
               " redeploy"
               and n_bob["noted_utc"] == "2026-10-06T00:01:20Z"
               and n_bob["status"] == "noted"
               and n_bob["buyer_id"] == "usr:bob"
               and n_bob["dev_account"] == "usr:dana"
               and n_bob["purchase_id"] == ids["p_bob1"]["purchase_id"]
               and n_bob["disclaimer"] == DISCLAIMER
               and stored == [(c_bob["claim_id"], "usr:bob",
                               "still failing after the redeploy",
                               "2026-10-06T00:01:20Z")])
        record("AC-AMCN1", ok1,
               "keys=%d text=%r rows=%d"
               % (len(n_bob), n_bob["note_text"], len(stored)))

        # -- AC-AMCN2 thread contract, ordering and dual party view -----
        buyer_thread = am.api_claim_thread(c_bob["claim_id"], "usr:bob")
        seller_thread = am.api_claim_thread(c_bob["claim_id"], "usr:dana")
        buyer_only = dict(buyer_thread)
        seller_only = dict(seller_thread)
        buyer_only["viewer_role"] = None
        seller_only["viewer_role"] = None
        kinds = [e["kind"] for e in buyer_thread["events"]]
        ok2 = (set(buyer_thread.keys()) == THREAD_KEYS
               and buyer_thread["viewer_role"] == "buyer"
               and seller_thread["viewer_role"] == "seller"
               and buyer_only == seller_only
               and buyer_thread["event_count"] == 3
               and buyer_thread["event_count"] == len(
                   buyer_thread["events"])
               and kinds == ["opened", "answered", "note"]
               and all(set(e.keys()) == EVENT_KEYS
                       for e in buyer_thread["events"])
               and [e["rank"] for e in buyer_thread["events"]]
               == [0, 1, 2]
               and [e["actor"] for e in buyer_thread["events"]]
               == ["usr:bob", "usr:dana", "usr:bob"]
               and buyer_thread["status"] == "answered"
               and buyer_thread["disputed"] is True
               and buyer_thread["claim_text"] == c_bob["claim_text"]
               and buyer_thread["price_paid"] == 10
               and buyer_thread["disclaimer"] == DISCLAIMER)
        record("AC-AMCN2", ok2,
               "keys=%d kinds=%r roles=%r same=%r"
               % (len(buyer_thread), kinds,
                  buyer_thread["viewer_role"],
                  buyer_only == seller_only))

        # -- AC-AMCN3 door gate family and its order --------------------
        clock.value = "2026-10-06T00:02:00Z"
        acct_codes = [note_code(am, bad, c_bob["claim_id"], "x")
                      for bad in BAD_ACCOUNTS]
        id_codes = [note_code(am, "usr:bob", bad, "x")
                    for bad in BAD_CLAIM_IDS]
        text_codes = [note_code(am, "usr:bob", c_bob["claim_id"], bad)
                      for bad in BAD_TEXTS]
        unknown = note_code(am, "usr:bob", 999999, "x")
        text_first = note_code(am, "usr:bob", 999999, "")
        acct_first = note_code(am, None, 999999, "x")
        not_owner = note_code(am, "usr:carol", c_bob["claim_id"], "x")
        owner_unknown = note_code(am, "usr:carol", 999999, "x")
        dup = note_code(am, "usr:bob", c_bob["claim_id"], "another")
        # refund landing after a claim: the note door is closed
        clock.value = "2026-10-06T00:02:10Z"
        am.refund_api("usr:carol", ids["p_carol1"]["purchase_id"],
                      "verified outage")
        refunded_note = note_code(am, "usr:carol", c_carol["claim_id"],
                                  "x")
        # follow-up then withdrawal: withdrawn beats the duplicate note
        clock.value = "2026-10-06T00:02:20Z"
        n_dave = am.add_claim_note("usr:dave", c_dave["claim_id"],
                                   "seller offered a credit, declined")
        clock.value = "2026-10-06T00:02:30Z"
        am.withdraw_claim("usr:dave", c_dave["claim_id"])
        withdrawn_note = note_code(am, "usr:dave", c_dave["claim_id"],
                                   "x")
        ok3 = (acct_codes == [A.E_AM_BAD_ACCOUNT] * len(BAD_ACCOUNTS)
               and id_codes == [A.E_AM_BAD_ARGS] * len(BAD_CLAIM_IDS)
               and text_codes == [A.E_AM_BAD_NOTE] * len(BAD_TEXTS)
               and unknown == A.E_AM_UNKNOWN_CLAIM
               and text_first == A.E_AM_BAD_NOTE
               and acct_first == A.E_AM_BAD_ACCOUNT
               and not_owner == A.E_AM_NOT_BUYER
               and owner_unknown == A.E_AM_UNKNOWN_CLAIM
               and dup == A.E_AM_CLAIM_NOTE_DUP
               and refunded_note == A.E_AM_ALREADY_REFUNDED
               and withdrawn_note == A.E_AM_CLAIM_WITHDRAWN
               and n_dave["status"] == "noted")
        record("AC-AMCN3", ok3,
               "acct=%r ids=%r text=%r order=%r/%r dup=%s "
               "refunded=%s withdrawn=%s"
               % (set(acct_codes), set(id_codes), set(text_codes),
                  text_first, acct_first, dup, refunded_note,
                  withdrawn_note))

        # -- AC-AMCN4 one note per claim, no rewrite, no UPDATE ---------
        probe = None
        conn = sqlite3.connect(am.db_path)
        try:
            conn.execute(
                "INSERT INTO apimarket_claim_notes (claim_id, buyer_id,"
                " note_text, noted_utc) VALUES (?,?,?,?)",
                (c_bob["claim_id"], "usr:bob", "second", "2026-10-06"))
            probe = "INSERTED"
        except sqlite3.IntegrityError:
            probe = "INTEGRITY"
        before = conn.execute(
            "SELECT note_text, noted_utc FROM apimarket_claim_notes"
            " WHERE claim_id = ?", (c_bob["claim_id"],)).fetchone()
        conn.rollback()
        conn.close()
        # a refund landing later never rewrites the note bytes
        clock.value = "2026-10-06T00:03:00Z"
        am.refund_api("usr:bob", ids["p_bob1"]["purchase_id"],
                      "outage confirmed")
        after_thread = am.api_claim_thread(c_bob["claim_id"], "usr:bob")
        note_event = [e for e in after_thread["events"]
                      if e["kind"] == "note"][0]
        with open(os.path.join(BASE, "apimarket.py"),
                  "r", encoding="utf-8") as handle:
            src = handle.read()
        no_update = ("UPDATE apimarket_claim_notes" not in src
                     and "DELETE FROM apimarket_claim_notes" not in src)
        ok4 = (probe == "INTEGRITY"
               and before == ("still failing after the redeploy",
                              "2026-10-06T00:01:20Z")
               and note_event["text"] == before[0]
               and note_event["utc"] == before[1]
               and no_update)
        record("AC-AMCN4", ok4,
               "probe=%s before=%r no_update=%r"
               % (probe, before[0], no_update))

        # -- AC-AMCN5 disputed flag across every closing act ------------
        t_bob = am.api_claim_thread(c_bob["claim_id"], "usr:dana")
        t_carol = am.api_claim_thread(c_carol["claim_id"], "usr:carol")
        t_dave = am.api_claim_thread(c_dave["claim_id"], "usr:dana")
        t_bob2 = am.api_claim_thread(c_bob2["claim_id"], "usr:bob")
        yields = {t["claim_id"]: (t["status"], t["disputed"],
                                  [e["kind"] for e in t["events"]])
                  for t in (t_bob, t_carol, t_dave, t_bob2)}
        ok5 = (yields[c_bob["claim_id"]]
               == ("refunded", False, ["opened", "answered", "note",
                                       "refunded"])
               and yields[c_carol["claim_id"]]
               == ("refunded", False, ["opened", "refunded"])
               and yields[c_dave["claim_id"]]
               == ("withdrawn", False, ["opened", "note", "withdrawn"])
               and yields[c_bob2["claim_id"]]
               == ("open", False, ["opened"]))
        record("AC-AMCN5", ok5, "yields=%r" % (yields,))

        # -- AC-AMCN6 thread party gating and purity --------------------
        digests_before = frozen_digests(am)
        tx_before = ledger_tx_ids(led)
        bal_before = pool_balances(led)
        party_codes = [thread_code(am, c_bob["claim_id"], who)
                       for who in ("usr:carol", "usr:dave", "usr:nobody")]
        t_acct = [thread_code(am, c_bob["claim_id"], bad)
                  for bad in BAD_ACCOUNTS]
        t_ids = [thread_code(am, bad, "usr:bob")
                 for bad in BAD_CLAIM_IDS]
        t_unknown = thread_code(am, 999999, "usr:bob")
        t_acct_first = thread_code(am, 999999, None)
        runs = [dumps(am.api_claim_thread(c_bob["claim_id"], "usr:bob")),
                dumps(am.api_claim_thread(c_bob["claim_id"], "usr:bob")),
                dumps(am.api_claim_thread(c_bob["claim_id"], "usr:bob"))]
        digests_after = frozen_digests(am)
        ok6 = (party_codes == [A.E_AM_NOT_PARTY] * 3
               and t_acct == [A.E_AM_BAD_ACCOUNT] * len(BAD_ACCOUNTS)
               and t_ids == [A.E_AM_BAD_ARGS] * len(BAD_CLAIM_IDS)
               and t_unknown == A.E_AM_UNKNOWN_CLAIM
               and t_acct_first == A.E_AM_BAD_ACCOUNT
               and runs[0] == runs[1] == runs[2]
               and digests_before == digests_after
               and tx_before == ledger_tx_ids(led)
               and bal_before == pool_balances(led))
        record("AC-AMCN6", ok6,
               "party=%r acct=%r ids=%r runs=%r frozen=%r tx=%r"
               % (set(party_codes), set(t_acct), set(t_ids),
                  runs[0] == runs[1] == runs[2],
                  digests_before == digests_after,
                  tx_before == ledger_tx_ids(led)))

        # -- AC-AMCN7 determinism and cross-restart identity ------------
        base_buyer = dumps(am.api_claim_thread(c_bob["claim_id"],
                                               "usr:bob"))
        base_seller = dumps(am.api_claim_thread(c_bob["claim_id"],
                                                "usr:dana"))
        base_queue = dumps(am.api_claims(dev_account="usr:dana"))
        close_stack(am, dk, metered, led)
        am = None
        replays = []
        for _ in range(2):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            replays.append(dumps(am2.api_claim_thread(
                c_bob["claim_id"], "usr:bob")))
            replays.append(dumps(am2.api_claim_thread(
                c_bob["claim_id"], "usr:dana")))
            replays.append(dumps(am2.api_claims(dev_account="usr:dana")))
            close_stack(am2, dk2, metered2, led2)
        ok7 = (replays[0] == base_buyer == replays[3]
               and replays[1] == base_seller == replays[4]
               and replays[2] == base_queue == replays[5])
        record("AC-AMCN7", ok7,
               "restart_buyer=%r restart_seller=%r restart_queue=%r"
               % (replays[0] == replays[3], replays[1] == replays[4],
                  replays[2] == replays[5]))

        # -- AC-AMCN8 delivery hygiene ----------------------------------
        with open(RECONCILE, "r", encoding="utf-8") as handle:
            wired = ('"ledger-apimarket-claimnote"' in handle.read())
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
        record("AC-AMCN8", ok8,
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