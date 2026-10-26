"""Acceptance suite for the apimarket seller-side answer revision leg
(BigDomain R2145; canon = the explore-queue row seeded and claimed in
R2145, criteria AC-AMAW1..AC-AMAW8 registered there BEFORE this suite
existed - honesty law; the anchors AC-AMAW, revise_answer,
api_answer_history, apimarket_answer_revisions, E_AM_ANSWER_UNCHANGED,
E_AM_UNKNOWN_ANSWER, test_apimarket_answerrev and
ledger-apimarket-answerrev were all git-grep -F zero-occupancy
anchored 2026-10-26, rc=1).

Face under proof: revise_answer + api_answer_history. R2118 gave the
Q&A face one write-once answer per question (UNIQUE(question_id),
E_AM_ALREADY_ANSWERED forever), while price (R2079), metadata (R2083),
supply (R2095), rating (R2094), reply (R2143) and provider identity
(R2136) each grew a remedy door. An answer that named a stock level or
a delivery window therefore stayed welded to the shelf after the shelf
moved. This suite pins:

  - one append-only apimarket_answer_revisions row per revision, the
    base answer row never rewritten, the nine-key envelope;
  - the pinned fail-closed gate order and the unchanged state judged
    against the EFFECTIVE text;
  - one effective-text seam shared by all three public Q&A read faces;
  - the retirement law (retirement freezes the shelf, not the duty to
    answer) and re-listing;
  - the history surface, its errors and its pure-read law;
  - counters and first-response latency that a revision must not move;
  - determinism, cross-restart identity, runner wiring and source
    hygiene.

Usage: python test_apimarket_answerrev.py
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

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

BAD_ACCOUNTS = ["", "bob", None, 5, True, [], {}, "   "]

ENVELOPE_KEYS = {"revision_id", "answer_id", "question_id",
                 "listing_id", "dev_account", "previous_text",
                 "answer_text", "revised_utc", "disclaimer"}

HISTORY_KEYS = {"answer_id", "question_id", "listing_id",
                "dev_account", "buyer_id", "question_text",
                "effective_text", "base_text", "revision_count",
                "latest_revised_utc", "disclaimer", "revisions"}

REVISION_KEYS = {"revision_id", "previous_text", "answer_text",
                 "revised_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_rating_replies", "apimarket_reply_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds", "apimarket_supply_revisions",
          "apimarket_questions", "apimarket_answers",
          "apimarket_answer_revisions")


class Clock(object):
    """Single mutable stamp behind A._now_utc, so asks, answers and
    revisions are orderable without sleeping."""

    def __init__(self, stamp):
        self.stamp = stamp

    def now_utc(self):
        return self.stamp

    def set(self, stamp):
        self.stamp = stamp


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(env):
    return json.dumps(env, sort_keys=True)


def table_digest(conn, table):
    rows = conn.execute(
        "SELECT * FROM " + table + " ORDER BY rowid").fetchall()
    blob = repr(rows).encode("utf-8")
    return len(rows), hashlib.sha256(blob).hexdigest()


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


def balances(led, accounts=("usr:bob", "usr:carol", "usr:dana",
                            "usr:erin")):
    conn = sqlite3.connect(led.db_path)
    out = {}
    for acct in accounts:
        row = conn.execute(
            "SELECT balance FROM ledger_accounts WHERE account_id = ?",
            (acct,)).fetchone()
        out[acct] = None if row is None else row[0]
    conn.close()
    return out


def code_of(exc):
    return getattr(exc, "code", None)


def expect_code(code, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except A.ApiMarketError as exc:
        return code_of(exc) == code
    except BaseException:
        return False
    return False


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


def base_row(market_db, answer_id):
    conn = sqlite3.connect(market_db)
    row = conn.execute(
        "SELECT answer_id, question_id, listing_id, dev_account,"
        " answer_text, answered_utc FROM apimarket_answers"
        " WHERE answer_id = ?", (answer_id,)).fetchone()
    conn.close()
    return row


def revision_rows(market_db):
    conn = sqlite3.connect(market_db)
    rows = conn.execute(
        "SELECT answer_id, question_id, listing_id, dev_account,"
        " previous_text, answer_text, revised_utc"
        " FROM apimarket_answer_revisions ORDER BY revision_id"
    ).fetchall()
    conn.close()
    return rows


def seed_world(led, dk, am, clock):
    """Two sellers, two buyers. dana publishes three listings (one is
    retired later), erin publishes one so owner isolation and the
    cross-seller equality of an identical wording are provable."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AW-A", "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AW-S", "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 600),
                    ("usr:" + who, "credit", 600)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)

    clock.set("2026-10-26T08:00:00Z")
    ids = {}
    for key, title, price in (("alpha", "Service Alpha", 10),
                              ("beta", "Service Beta", 8),
                              ("gamma", "Service Gamma", 6)):
        ids[key] = am.publish_api("usr:dana", key, title,
                                  "service payload " + key, PAYLOAD,
                                  price, False)["listing_id"]
    ids["zeta"] = am.publish_api("usr:erin", "zeta", "Service Zeta",
                                 "service payload zeta", PAYLOAD, 7,
                                 False)["listing_id"]
    clock.set("2026-10-26T08:10:00Z")
    am.purchase_api("usr:bob", ids["alpha"], "answerrev-sale-1")
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="amaw-")
    db_path = os.path.join(tmp, "answerrev.db")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    market_db = am.db_path

    original_now = A._now_utc
    clock = Clock("2026-10-26T08:30:00Z")
    A._now_utc = clock.now_utc
    try:
        ids = seed_world(led, dk, am, clock)

        clock.set("2026-10-26T09:00:00Z")
        q_alpha = am.ask_question("usr:bob", ids["alpha"],
                                  "  how many units are in stock?  ")
        clock.set("2026-10-26T09:05:00Z")
        q_beta = am.ask_question("usr:carol", ids["beta"],
                                 "what is the delivery window?")
        clock.set("2026-10-26T09:10:00Z")
        q_gamma = am.ask_question("usr:bob", ids["gamma"],
                                  "is there a volume discount?")
        clock.set("2026-10-26T09:15:00Z")
        q_zeta = am.ask_question("usr:bob", ids["zeta"],
                                 "is there a trial?")
        clock.set("2026-10-26T10:00:00Z")
        a_alpha = am.answer_question("usr:dana",
                                     q_alpha["question_id"],
                                     "  thirty units in stock  ")
        clock.set("2026-10-26T10:10:00Z")
        a_beta = am.answer_question("usr:dana", q_beta["question_id"],
                                    "ships in two business days")
        clock.set("2026-10-26T10:20:00Z")
        a_gamma = am.answer_question("usr:dana",
                                     q_gamma["question_id"],
                                     "no discount below fifty units")
        clock.set("2026-10-26T10:30:00Z")
        a_zeta = am.answer_question("usr:erin", q_zeta["question_id"],
                                    "seven day trial on request")

        # -- AC-AMAW1 append-only shape + contract --------------------
        base_alpha = base_row(market_db, a_alpha["answer_id"])
        clock.set("2026-10-26T11:00:00Z")
        rev1 = am.revise_answer("usr:dana", a_alpha["answer_id"],
                                "  four units left  ")
        base_alpha_after = base_row(market_db, a_alpha["answer_id"])
        rows1 = revision_rows(market_db)
        ok1 = (set(rev1.keys()) == ENVELOPE_KEYS
               and len(rev1) == 9
               and rev1["answer_id"] == a_alpha["answer_id"]
               and rev1["question_id"] == q_alpha["question_id"]
               and rev1["listing_id"] == ids["alpha"]
               and rev1["dev_account"] == "usr:dana"
               and rev1["previous_text"] == "thirty units in stock"
               and rev1["answer_text"] == "four units left"
               and rev1["revised_utc"] == "2026-10-26T11:00:00Z"
               and rev1["disclaimer"] == DISCLAIMER
               and len(rows1) == 1
               and rows1[0] == (a_alpha["answer_id"],
                                q_alpha["question_id"], ids["alpha"],
                                "usr:dana", "thirty units in stock",
                                "four units left",
                                "2026-10-26T11:00:00Z")
               and base_alpha == base_alpha_after
               and base_alpha[4] == "thirty units in stock")
        record("AC-AMAW1", ok1,
               "keys=%d rows=%d base_unchanged=%s rev=%.40s"
               % (len(rev1), len(rows1),
                  base_alpha == base_alpha_after, rev1["answer_text"]))

        # -- AC-AMAW2 pinned gate order, fail-closed ------------------
        digests_before = market_digests(am)
        txs_before = ledger_tx_ids(led)
        bal_before = balances(led)
        gate_ok = all(expect_code(A.E_AM_BAD_ACCOUNT,
                                  am.revise_answer, acct,
                                  a_alpha["answer_id"], "text")
                      for acct in BAD_ACCOUNTS)
        gate_ok = gate_ok and all(
            expect_code(A.E_AM_BAD_ARGS, am.revise_answer, "usr:dana",
                        bad, "text")
            for bad in (0, -3, "1", True, 1.5, None))
        gate_ok = gate_ok and all(
            expect_code(A.E_AM_BAD_REPLY, am.revise_answer,
                        "usr:dana", a_alpha["answer_id"], bad)
            for bad in ("", "   ", "x" * 501, 5, None,
                        "line\nbreak", "tab\there"))
        gate_ok = gate_ok and expect_code(
            A.E_AM_UNKNOWN_ANSWER, am.revise_answer, "usr:dana",
            999999, "anything")
        gate_ok = gate_ok and expect_code(
            A.E_AM_NOT_OWNER, am.revise_answer, "usr:erin",
            a_alpha["answer_id"], "anything")
        gate_ok = gate_ok and expect_code(
            A.E_AM_NOT_OWNER, am.revise_answer, "usr:bob",
            a_alpha["answer_id"], "anything")
        gate_ok = gate_ok and expect_code(
            A.E_AM_ANSWER_UNCHANGED, am.revise_answer, "usr:dana",
            a_alpha["answer_id"], "  four units left  ")
        # Double-bad probes answer the FIRST failing gate.
        gate_ok = gate_ok and expect_code(
            A.E_AM_BAD_ACCOUNT, am.revise_answer, "bob", 0, "")
        gate_ok = gate_ok and expect_code(
            A.E_AM_BAD_ARGS, am.revise_answer, "usr:dana", 0, 5)
        gate_ok = gate_ok and expect_code(
            A.E_AM_BAD_REPLY, am.revise_answer, "usr:dana", 999999,
            "")
        gate_ok = gate_ok and expect_code(
            A.E_AM_UNKNOWN_ANSWER, am.revise_answer, "usr:dana",
            999999, "ok")
        ok2 = (gate_ok and market_digests(am) == digests_before
               and ledger_tx_ids(led) == txs_before
               and balances(led) == bal_before
               and len(revision_rows(market_db)) == 1)
        record("AC-AMAW2", ok2,
               "gate=%s digests=%s tx=%s rows=%d"
               % (gate_ok, market_digests(am) == digests_before,
                  ledger_tx_ids(led) == txs_before,
                  len(revision_rows(market_db))))

        # -- AC-AMAW3 one effective seam on three read faces ----------
        qna = am.api_listing_qna(ids["alpha"])
        buyer_q = am.api_buyer_questions("usr:bob")
        seller_a = am.api_seller_answers("usr:dana")
        qna_row = [q for q in qna["questions"]
                   if q["question_id"] == q_alpha["question_id"]][0]
        bq_row = [q for q in buyer_q["rows"]
                  if q["question_id"] == q_alpha["question_id"]][0]
        sa_row = [r for r in seller_a["rows"]
                  if r["answer_id"] == a_alpha["answer_id"]][0]
        seam_ok = (qna_row["answer_text"] == "four units left"
                   and bq_row["answer_text"] == "four units left"
                   and sa_row["answer_text"] == "four units left")
        # Revising back to an earlier wording stays legal.
        clock.set("2026-10-26T11:30:00Z")
        rev2 = am.revise_answer("usr:dana", a_alpha["answer_id"],
                                "thirty units in stock")
        back_ok = (rev2["previous_text"] == "four units left"
                   and rev2["answer_text"] == "thirty units in stock"
                   and am.api_listing_qna(ids["alpha"])["questions"][0]
                   ["answer_text"] == "thirty units in stock")
        # A cross-seller identical wording is legal: ownership, not text.
        clock.set("2026-10-26T11:40:00Z")
        erin_rev = am.revise_answer("usr:erin", a_zeta["answer_id"],
                                    "thirty units in stock")
        cross_ok = (erin_rev["answer_text"] == "thirty units in stock"
                    and erin_rev["dev_account"] == "usr:erin")
        unchanged_ok = expect_code(A.E_AM_ANSWER_UNCHANGED,
                                   am.revise_answer, "usr:dana",
                                   a_alpha["answer_id"],
                                   "thirty units in stock")
        ok3 = (seam_ok and back_ok and cross_ok and unchanged_ok
               and len(revision_rows(market_db)) == 3)
        record("AC-AMAW3", ok3,
               "seam=%s back=%s cross=%s unchanged=%s rows=%d"
               % (seam_ok, back_ok, cross_ok, unchanged_ok,
                  len(revision_rows(market_db))))

        # -- AC-AMAW4 retirement law + re-listing ---------------------
        clock.set("2026-10-26T12:00:00Z")
        am.delist_api("usr:dana", ids["beta"])
        clock.set("2026-10-26T12:10:00Z")
        retired_rev = am.revise_answer("usr:dana", a_beta["answer_id"],
                                       "ships in five business days")
        retired_qna = am.api_listing_qna(ids["beta"])
        retired_row = [q for q in retired_qna["questions"]
                       if q["question_id"] == q_beta["question_id"]][0]
        history_beta = am.api_answer_history(a_beta["answer_id"])
        clock.set("2026-10-26T12:20:00Z")
        am.relist_api("usr:dana", ids["beta"])
        relisted_history = am.api_answer_history(a_beta["answer_id"])
        ok4 = (retired_rev["answer_text"] == "ships in five business days"
               and retired_qna["retired"] is True
               and retired_row["answer_text"]
               == "ships in five business days"
               and history_beta["revision_count"] == 1
               and relisted_history["revision_count"] == 1
               and relisted_history["effective_text"]
               == "ships in five business days")
        record("AC-AMAW4", ok4,
               "retired_revisable=%s retired_face=%s history=%d/%d"
               % (retired_rev["answer_text"] == "ships in five business days",
                  retired_row["answer_text"], history_beta["revision_count"],
                  relisted_history["revision_count"]))

        # -- AC-AMAW5 history surface, shape, order, errors -----------
        clock.set("2026-10-26T13:00:00Z")
        am.revise_answer("usr:dana", a_alpha["answer_id"],
                         "ten units left")
        hist = am.api_answer_history(a_alpha["answer_id"])
        shape_ok = (set(hist.keys()) == HISTORY_KEYS
                    and len(hist) == 12
                    and all(set(x.keys()) == REVISION_KEYS
                            and len(x) == 4 for x in hist["revisions"]))
        order_ok = ([x["answer_text"] for x in hist["revisions"]]
                    == ["four units left", "thirty units in stock",
                        "ten units left"])
        values_ok = (hist["base_text"] == "thirty units in stock"
                     and hist["effective_text"] == "ten units left"
                     and hist["revision_count"] == 3
                     and hist["question_text"]
                     == "how many units are in stock?"
                     and hist["buyer_id"] == "usr:bob"
                     and hist["dev_account"] == "usr:dana"
                     and hist["latest_revised_utc"]
                     == "2026-10-26T13:00:00Z")
        errors_ok = (expect_code(A.E_AM_UNKNOWN_ANSWER,
                                 am.api_answer_history, 999999)
                     and expect_code(A.E_AM_BAD_ARGS,
                                     am.api_answer_history, 0)
                     and expect_code(A.E_AM_BAD_ARGS,
                                     am.api_answer_history, "1")
                     and expect_code(A.E_AM_BAD_ARGS,
                                     am.api_answer_history, True))
        ok5 = shape_ok and order_ok and values_ok and errors_ok
        record("AC-AMAW5", ok5,
               "shape=%s order=%s values=%s errors=%s"
               % (shape_ok, order_ok, values_ok, errors_ok))

        # -- AC-AMAW6 counters and first-response latency frozen ------
        seller_before = am.api_seller_answers("usr:dana")
        questions_before = am.api_seller_questions("usr:dana")
        qna_before = am.api_listing_qna(ids["alpha"])
        clock.set("2026-10-26T14:00:00Z")
        am.revise_answer("usr:dana", a_beta["answer_id"],
                         "ships in three business days")
        seller_after = am.api_seller_answers("usr:dana")
        questions_after = am.api_seller_questions("usr:dana")
        qna_after = am.api_listing_qna(ids["alpha"])
        row_before = [r for r in seller_before["rows"]
                      if r["answer_id"] == a_beta["answer_id"]][0]
        row_after = [r for r in seller_after["rows"]
                     if r["answer_id"] == a_beta["answer_id"]][0]
        counts_ok = (seller_before["answered_count"]
                     == seller_after["answered_count"]
                     and seller_before["buyer_count"]
                     == seller_after["buyer_count"]
                     and seller_before["mean_seconds"]
                     == seller_after["mean_seconds"]
                     and row_before["response_seconds"]
                     == row_after["response_seconds"]
                     and row_before["answered_utc"]
                     == row_after["answered_utc"]
                     == "2026-10-26T10:10:00Z"
                     and qna_before["answered_count"]
                     == qna_after["answered_count"]
                     and qna_before["unanswered_count"]
                     == qna_after["unanswered_count"]
                     and questions_before["unanswered_count"]
                     == questions_after["unanswered_count"]
                     and dumps(questions_before)
                     == dumps(questions_after))
        ok6 = counts_ok
        record("AC-AMAW6", ok6,
               "answered=%d/%d mean=%r/%r latency=%d/%d queue_same=%s"
               % (seller_before["answered_count"],
                  seller_after["answered_count"],
                  seller_before["mean_seconds"],
                  seller_after["mean_seconds"],
                  row_before["response_seconds"],
                  row_after["response_seconds"],
                  dumps(questions_before) == dumps(questions_after)))

        # -- AC-AMAW7 pure read + determinism -------------------------
        digests7 = market_digests(am)
        txs7 = ledger_tx_ids(led)
        first = dumps(am.api_answer_history(a_alpha["answer_id"]))
        second = dumps(am.api_answer_history(a_alpha["answer_id"]))
        repeated = all(
            dumps(am.api_listing_qna(ids[key]))
            == dumps(am.api_listing_qna(ids[key]))
            for key in ("alpha", "beta", "gamma", "zeta"))
        ok7 = (first == second and repeated
               and market_digests(am) == digests7
               and ledger_tx_ids(led) == txs7)
        record("AC-AMAW7", ok7,
               "history_same=%s faces_same=%s digests=%s tx=%s"
               % (first == second, repeated,
                  market_digests(am) == digests7,
                  ledger_tx_ids(led) == txs7))

        # -- AC-AMAW8 cross-restart identity, wiring, hygiene ---------
        watched = (a_alpha["answer_id"], a_beta["answer_id"],
                   a_zeta["answer_id"])
        face_before = [dumps(am.api_answer_history(x)) for x in watched]
        snapshot = [dumps(am.api_listing_qna(ids["alpha"])),
                    dumps(am.api_buyer_questions("usr:bob")),
                    dumps(am.api_seller_answers("usr:dana"))]
        close_stack(am, dk, metered, led)
        restarts = 0
        for _ in range(2):
            led, metered, dk, gate, am = build_stack(db_path, cfg,
                                                     lobby_cfg)
            face_after = [dumps(am.api_answer_history(x))
                          for x in watched]
            faces_after = [dumps(am.api_listing_qna(ids["alpha"])),
                           dumps(am.api_buyer_questions("usr:bob")),
                           dumps(am.api_seller_answers("usr:dana"))]
            if face_after == face_before and faces_after == snapshot:
                restarts += 1
            close_stack(am, dk, metered, led)
        with open(RECONCILE, "rb") as handle:
            runner = handle.read().decode("utf-8")
        wired = ('("ledger-apimarket-answerrev"' in runner
                 and "test_apimarket_answerrev.py" in runner)
        with open(os.path.abspath(__file__), "rb") as handle:
            source = handle.read()
        ascii_ok = all(b < 128 for b in source)
        ok8 = (restarts == 2 and wired and ascii_ok)
        record("AC-AMAW8", ok8,
               "restarts=%d/2 wired=%s ascii=%s" % (restarts, wired,
                                                    ascii_ok))

    finally:
        A._now_utc = original_now
        try:
            close_stack(am, dk, metered, led)
        except BaseException:
            pass

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS" if passed == total else "SUITE FAIL"
    print("\n%s %d/%d" % (verdict, passed, total), flush=True)
    if passed != total:
        for ac, ok in RESULTS:
            if not ok:
                print("FAILED: " + ac, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())