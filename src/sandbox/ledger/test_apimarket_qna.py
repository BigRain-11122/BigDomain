"""Acceptance suite for the apimarket pre-purchase Q&A face
(BigDomain R2118; canon = the explore-queue row seeded and claimed in
R2118, criteria AC-AMQA1..AC-AMQA8 registered there BEFORE this suite
existed - honesty law; the AC-AMQA prefix, ask_question,
answer_question, api_listing_qna, api_seller_questions,
apimarket_questions, apimarket_answers, E_AM_BAD_QUESTION and
E_AM_ALREADY_ANSWERED anchors were all git-grep -F zero-occupancy
anchored 2026-10-25, rc=1).

Face under proof: ask_question / answer_question / api_listing_qna /
api_seller_questions. Every trust face on this market is
post-purchase (ratings, rating revisions, seller replies, refunds and
the seller inbox all need a sale first), so a resident deciding
whether to buy had no way to ask the seller anything and the answer
could never be seen by the next buyer. This suite pins:

  - the ask door (one append-only row, verbatim stripped text, the
    pinned gate order account -> listing shape -> existence ->
    retired -> text shape) and its fail-closed family;
  - the answer door (one append-only answer per question, owner only,
    first stamp never rewritten, gate order account -> question shape
    -> text shape -> existence -> ownership -> already answered);
  - the public thread read face (total order, answered arithmetic,
    retired threads still readable, per-listing isolation);
  - the seller open-question queue (unanswered only, merged across
    listings, oldest first, seller isolation, honest empty);
  - the pure-read law (frozen table digests, constant ledger tx set);
  - cross-restart byte identity on three instances;
  - the report consumer (seller block questions key, question_debt
    attention family, REPORT_SCHEMA 10 -> 11 additive, legacy report
    degrade, hostile-text escaping), runner wiring and suite hygiene.

Usage: python test_apimarket_qna.py
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
import apimarket_report as R          # noqa: E402 (R2101 consumer)
from sec_gate import SecGate          # noqa: E402 (lobby ref, no copy)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apimarket_report.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

BAD_ACCOUNTS = ["", "bob", None, 5, True, [], {}, "   "]

BAD_LISTING_IDS = [0, -1, "1", None, True, 1.5, [], {}]

BAD_TEXTS = ["", "   ", "x" * 501, "bad\nline", "tab\there", 5, None,
             [], {}]

THREAD_KEYS = {"listing_id", "listing_key", "title", "retired",
               "question_count", "answered_count", "unanswered_count",
               "oldest_unanswered_utc", "disclaimer", "questions"}

THREAD_ROW_KEYS = {"question_id", "buyer_id", "question_text",
                   "asked_utc", "answered", "answer_text",
                   "answered_utc", "dev_account"}

QUEUE_KEYS = {"dev_account", "listing_count", "total_question_count",
              "answered_count", "unanswered_count",
              "oldest_unanswered_utc", "disclaimer", "rows"}

QUEUE_ROW_KEYS = {"question_id", "listing_id", "listing_key", "title",
                  "buyer_id", "question_text", "asked_utc"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_delistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_refunds", "apimarket_supply_revisions",
          "apimarket_questions", "apimarket_answers")


class Clock(object):
    """Single mutable stamp behind A._now_utc, so question order is
    testable without sleeping."""

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


def error_codes(call, args_list):
    codes = []
    for args in args_list:
        try:
            call(*args)
            codes.append(None)
        except A.ApiMarketError as exc:
            codes.append(code_of(exc))
    return codes


def seed_world(led, dk, am, clock):
    """Owner dana publishes three listings; buyers bob and carol ask
    four questions, one of which is answered before the shelf that
    holds the last question retires."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-QA-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-QA-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 600),
                    ("usr:" + who, "credit", 600)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)

    clock.set("2026-10-25T08:00:00Z")
    ids = {}
    for key, title, price in (("alpha", "Service Alpha", 10),
                              ("beta", "Service Beta", 8),
                              ("gamma", "Service Gamma", 6)):
        ids[key] = am.publish_api("usr:dana", key, title,
                                  "service payload " + key, PAYLOAD,
                                  price, False)["listing_id"]
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="amqa-")
    db_path = os.path.join(tmp, "qa.db")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    original_now = A._now_utc
    clock = Clock("2026-10-25T08:30:00Z")
    A._now_utc = clock.now_utc
    try:
        ids = seed_world(led, dk, am, clock)

        # questions land in a scrambled order on purpose: the oldest
        # open question (alpha/carol) is neither the first nor the last
        # question id.
        clock.set("2026-10-25T09:00:00Z")
        q1 = am.ask_question("usr:bob", ids["alpha"],
                             "  does this support batch calls?  ")
        clock.set("2026-10-25T09:10:00Z")
        q2 = am.ask_question("usr:carol", ids["alpha"],
                             "is there a sample response?")
        clock.set("2026-10-25T09:20:00Z")
        q3 = am.ask_question("usr:bob", ids["beta"],
                             "what is the rate limit?")
        clock.set("2026-10-25T09:30:00Z")
        a1 = am.answer_question("usr:dana", q1["question_id"],
                                "yes, up to 500 calls per batch")
        clock.set("2026-10-25T09:40:00Z")
        q4 = am.ask_question("usr:carol", ids["gamma"],
                             "does this include history?")
        clock.set("2026-10-25T10:00:00Z")
        am.delist_api("usr:dana", ids["gamma"])

        # -- AC-AMQA1 door shape + honest empty -----------------------
        ask_keys = {"question_id", "listing_id", "dev_account",
                    "buyer_id", "question_text", "asked_utc",
                    "answered", "disclaimer"}
        thread = am.api_listing_qna(ids["alpha"])
        newbie = am.api_seller_questions("usr:newbie")
        ok1 = (set(q1.keys()) == ask_keys
               and set(a1.keys()) == {"answer_id", "question_id",
                                      "listing_id", "dev_account",
                                      "answer_text", "answered_utc",
                                      "disclaimer"}
               and q1["question_text"]
               == "does this support batch calls?"
               and q1["answered"] is False
               and q1["dev_account"] == "usr:dana"
               and set(thread.keys()) == THREAD_KEYS
               and all(set(r.keys()) == THREAD_ROW_KEYS
                       for r in thread["questions"])
               and set(newbie.keys()) == QUEUE_KEYS
               and newbie["listing_count"] == 0
               and newbie["rows"] == []
               and newbie["total_question_count"] == 0
               and newbie["oldest_unanswered_utc"] is None)
        record("AC-AMQA1", ok1,
               "ask keys=%d answer keys ok=%r stripped=%r envelope=%d"
               " row keys=%r empty queue=%r"
               % (len(q1), sorted(a1.keys()), q1["question_text"]
                  == "does this support batch calls?",
                  len(thread), sorted(set(len(r) for r in
                                          thread["questions"])),
                  newbie["rows"] == []))

        # -- AC-AMQA2 ask gate order + fail-closed --------------------
        pre = market_digests(am)
        pre_tx = ledger_tx_ids(led)
        bad_acct = error_codes(
            lambda who: am.ask_question(who, ids["alpha"], "hi"),
            [(w,) for w in BAD_ACCOUNTS])
        bad_listing = error_codes(
            lambda lid: am.ask_question("usr:bob", lid, "hi"),
            [(lid,) for lid in BAD_LISTING_IDS])
        unknown = None
        try:
            am.ask_question("usr:bob", 999999, "hi")
        except A.ApiMarketError as exc:
            unknown = code_of(exc)
        retired = None
        try:
            am.ask_question("usr:bob", ids["gamma"], "hi")
        except A.ApiMarketError as exc:
            retired = code_of(exc)
        bad_text = error_codes(
            lambda text: am.ask_question("usr:bob", ids["alpha"], text),
            [(t,) for t in BAD_TEXTS])
        post = market_digests(am)
        post_tx = ledger_tx_ids(led)
        ok2 = (all(c == A.E_AM_BAD_ACCOUNT for c in bad_acct)
               and all(c == A.E_AM_BAD_ARGS for c in bad_listing)
               and unknown == A.E_AM_UNKNOWN_LISTING
               and retired == A.E_AM_DELISTED
               and all(c == A.E_AM_BAD_QUESTION for c in bad_text)
               and pre == post and pre_tx == post_tx)
        record("AC-AMQA2", ok2,
               "account=%r listing=%r unknown=%r retired=%r text=%r"
               " digests frozen=%r"
               % (bad_acct, bad_listing, unknown, retired, bad_text,
                  pre == post))

        # -- AC-AMQA3 answer gate order, dup, first stamp ------------
        pre = market_digests(am)
        bad_acct = error_codes(
            lambda who: am.answer_question(who, q2["question_id"], "ok"),
            [(w,) for w in BAD_ACCOUNTS])
        bad_qid = error_codes(
            lambda qid: am.answer_question("usr:dana", qid, "ok"),
            [(qid,) for qid in BAD_LISTING_IDS])
        bad_text = error_codes(
            lambda text: am.answer_question("usr:dana",
                                            q2["question_id"], text),
            [(t,) for t in BAD_TEXTS])
        unknown = None
        try:
            am.answer_question("usr:dana", 999999, "ok")
        except A.ApiMarketError as exc:
            unknown = code_of(exc)
        not_owner = None
        try:
            am.answer_question("usr:carol", q2["question_id"], "ok")
        except A.ApiMarketError as exc:
            not_owner = code_of(exc)
        dup = None
        try:
            am.answer_question("usr:dana", q1["question_id"], "again")
        except A.ApiMarketError as exc:
            dup = code_of(exc)
        alpha_after_dup = am.api_listing_qna(ids["alpha"])
        first_row = [r for r in alpha_after_dup["questions"]
                     if r["question_id"] == q1["question_id"]][0]
        post = market_digests(am)
        ok3 = (all(c == A.E_AM_BAD_ACCOUNT for c in bad_acct)
               and all(c == A.E_AM_BAD_ARGS for c in bad_qid)
               and all(c == A.E_AM_BAD_REPLY for c in bad_text)
               and unknown == A.E_AM_UNKNOWN_QUESTION
               and not_owner == A.E_AM_NOT_OWNER
               and dup == A.E_AM_ALREADY_ANSWERED
               and first_row["answer_text"]
               == "yes, up to 500 calls per batch"
               and first_row["answered_utc"] == a1["answered_utc"]
               and pre == post)
        record("AC-AMQA3", ok3,
               "account=%r qid=%r text=%r unknown=%r owner=%r dup=%r"
               " first stamp kept=%r rows frozen=%r"
               % (bad_acct, bad_qid, bad_text, unknown, not_owner, dup,
                  first_row["answered_utc"] == a1["answered_utc"],
                  pre == post))

        # -- AC-AMQA4 thread laws ------------------------------------
        alpha = am.api_listing_qna(ids["alpha"])
        beta = am.api_listing_qna(ids["beta"])
        gamma = am.api_listing_qna(ids["gamma"])
        bad_thread = error_codes(
            lambda lid: am.api_listing_qna(lid),
            [(lid,) for lid in BAD_LISTING_IDS])
        unknown = None
        try:
            am.api_listing_qna(999999)
        except A.ApiMarketError as exc:
            unknown = code_of(exc)
        alpha_ids = [r["question_id"] for r in alpha["questions"]]
        ok4 = (alpha["question_count"] == 2
               and alpha["answered_count"] == 1
               and alpha["unanswered_count"] == 1
               and alpha["oldest_unanswered_utc"] == q2["asked_utc"]
               and alpha_ids == [q1["question_id"], q2["question_id"]]
               and [r["asked_utc"] for r in alpha["questions"]]
               == sorted(r["asked_utc"] for r in alpha["questions"])
               and beta["question_count"] == 1
               and beta["answered_count"] == 0
               and beta["oldest_unanswered_utc"] == q3["asked_utc"]
               and gamma["question_count"] == 1
               and gamma["retired"] is True
               and gamma["unanswered_count"] == 1
               and all(c == A.E_AM_BAD_ARGS for c in bad_thread)
               and unknown == A.E_AM_UNKNOWN_LISTING
               and alpha["disclaimer"] == DISCLAIMER)
        record("AC-AMQA4", ok4,
               "alpha=%d/%d/%d order=%r beta=%d gamma retired=%r"
               " gamma thread=%d bad=%r unknown=%r"
               % (alpha["question_count"], alpha["answered_count"],
                  alpha["unanswered_count"], alpha_ids,
                  beta["question_count"], gamma["retired"],
                  gamma["question_count"], bad_thread, unknown))

        # -- AC-AMQA5 seller queue laws ------------------------------
        queue = am.api_seller_questions("usr:dana")
        carol_queue = am.api_seller_questions("usr:carol")
        bad_queue = error_codes(
            lambda who: am.api_seller_questions(who),
            [(w,) for w in BAD_ACCOUNTS])
        row_ids = [r["question_id"] for r in queue["rows"]]
        ok5 = (queue["total_question_count"] == 4
               and queue["answered_count"] == 1
               and queue["unanswered_count"] == 3
               and queue["oldest_unanswered_utc"] == q2["asked_utc"]
               and row_ids == [q2["question_id"], q3["question_id"],
                               q4["question_id"]]
               and all(set(r.keys()) == QUEUE_ROW_KEYS
                       for r in queue["rows"])
               and carol_queue["total_question_count"] == 0
               and carol_queue["rows"] == []
               and all(c == A.E_AM_BAD_ACCOUNT for c in bad_queue))
        # answering drains the queue without touching any other row
        clock.set("2026-10-25T10:10:00Z")
        am.answer_question("usr:dana", q3["question_id"],
                           "500 calls per hour")
        drained = am.api_seller_questions("usr:dana")
        beta_after = am.api_listing_qna(ids["beta"])
        ok5 = (ok5
               and drained["unanswered_count"] == 2
               and drained["answered_count"] == 2
               and drained["total_question_count"] == 4
               and [r["question_id"] for r in drained["rows"]]
               == [q2["question_id"], q4["question_id"]]
               and beta_after["answered_count"] == 1
               and beta_after["question_count"] == 1)
        record("AC-AMQA5", ok5,
               "total=%d answered=%d unanswered=%d order=%r"
               " carol queue=%d bad=%r drain->%d/%d rows=%r"
               % (queue["total_question_count"],
                  queue["answered_count"], queue["unanswered_count"],
                  row_ids, carol_queue["total_question_count"],
                  bad_queue, drained["answered_count"],
                  drained["unanswered_count"],
                  [r["question_id"] for r in drained["rows"]]))

        # -- AC-AMQA6 pure read -------------------------------------
        mid_digests = market_digests(am)
        mid_tx = ledger_tx_ids(led)
        family_one = {who: dumps(am.api_seller_questions("usr:" + who))
                      for who in ("dana", "carol", "newbie")}
        threads_one = {key: dumps(am.api_listing_qna(ids[key]))
                       for key in ("alpha", "beta", "gamma")}
        repeat = {who: dumps(am.api_seller_questions("usr:" + who))
                  for who in ("dana", "carol", "newbie")}
        after_digests = market_digests(am)
        after_tx = ledger_tx_ids(led)
        ok6 = (mid_digests == after_digests and mid_tx == after_tx
               and family_one == repeat)
        record("AC-AMQA6", ok6,
               "digests stable=%r tx stable=%r repeat identical=%r"
               % (mid_digests == after_digests, mid_tx == after_tx,
                  family_one == repeat))

        # -- AC-AMQA7 cross-restart byte identity -------------------
        family_two = {}
        family_three = {}
        for index in (2, 3):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            try:
                fam = {who: dumps(am2.api_seller_questions("usr:" + who))
                       for who in ("dana", "carol", "newbie")}
                th = {key: dumps(am2.api_listing_qna(ids[key]))
                      for key in ("alpha", "beta", "gamma")}
            finally:
                close_stack(am2, dk2, metered2, led2)
            if index == 2:
                family_two = fam
                threads_two = th
            else:
                family_three = fam
                threads_three = th
        ok7 = (family_one == family_two == family_three
               and threads_one == threads_two == threads_three)
        record("AC-AMQA7", ok7,
               "instances 1==2==3=%r threads identical=%r"
               % (family_one == family_two == family_three,
                  threads_one == threads_two == threads_three))

        # -- AC-AMQA8 report consumer, wiring, hygiene ---------------
        am.ask_question("usr:bob", ids["alpha"],
                        "<script>alert(1)</script>")
        report = R.collect(am)
        page = R.render_html(report)
        block = report["sellers"]["usr:dana"]
        kinds = [f["kind"] for f in report["attention"]["findings"]]
        debt = [f for f in report["attention"]["findings"]
                if f["kind"] == "question_debt"]
        legacy = json.loads(json.dumps(report))
        for dev in legacy["sellers"]:
            legacy["sellers"][dev].pop("questions", None)
        legacy.pop("attention", None)
        legacy_page = R.render_html(legacy)
        with open(RECONCILE, "rb") as handle:
            wired = b"ledger-apimarket-qna" in handle.read()
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
        ok8 = (R.REPORT_SCHEMA == 11
               and "questions" in block
               and block["questions"]["unanswered_count"] == 3
               and "question_debt" in kinds
               and len(debt) == 1 and debt[0]["subject"] == "usr:dana"
               and "3 unanswered question(s)" in debt[0]["detail"]
               and "open questions" in page
               and "&lt;script&gt;alert(1)&lt;/script&gt;" in page
               and "<script>alert(1)</script>" not in page
               and "open questions" in legacy_page
               and wired and ascii_ok and not net_imports and outside)
        record("AC-AMQA8", ok8,
               "schema=%d questions key=%r unanswered=%r debt=%r"
               " page section=%r escaped=%r legacy render=%r"
               " wired=%r ascii=%r net=%d"
               % (R.REPORT_SCHEMA, "questions" in block,
                  block.get("questions", {}).get("unanswered_count"),
                  debt[0]["detail"] if debt else None,
                  "open questions" in page,
                  "&lt;script&gt;" in page,
                  "open questions" in legacy_page, wired, ascii_ok,
                  len(net_imports)))
    finally:
        A._now_utc = original_now
        close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())