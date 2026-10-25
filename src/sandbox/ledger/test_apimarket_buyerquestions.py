"""Acceptance suite for the apimarket buyer-side question history
(BigDomain R2119; canon = the explore-queue row seeded and claimed in
R2119, criteria AC-AMBQ1..AC-AMBQ8 registered there BEFORE this suite
existed - honesty law; the anchors api_buyer_questions, AC-AMBQ,
ledger-apimarket-buyerquestions and MY_QUESTIONS_EMPTY were all
git-grep -F zero-occupancy anchored 2026-10-25, rc=1).

Face under proof: api_buyer_questions. R2118 gave the seller a merged
open-question queue (api_seller_questions) while the asking side could
only read one thread at a time (api_listing_qna), so a resident who had
asked on N listings had to open N threads and merge by hand. This
suite pins:

  - the envelope and row shape plus the honest empty state;
  - strict buyer isolation (a seller account sees its own honest empty);
  - the counts arithmetic and the total order on (asked_utc, question_id);
  - the merged time line across listings with the CURRENT metadata title;
  - retired listings keep their question history readable;
  - the pure-read law (frozen table digests, constant ledger tx set)
    and the fail-closed account gate;
  - cross-restart byte identity on three instances;
  - the report consumer (buyer block questions key, my-questions table,
    hostile-text escaping, legacy degrade, REPORT_SCHEMA 11 -> 12
    additive), runner wiring and suite hygiene.

Usage: python test_apimarket_buyerquestions.py
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

RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")

BAD_ACCOUNTS = ["", "bob", None, 5, True, [], {}, "   "]

ENVELOPE_KEYS = {"buyer_id", "listing_count", "question_count",
                 "answered_count", "unanswered_count",
                 "oldest_open_utc", "disclaimer", "rows"}

ROW_KEYS = {"question_id", "listing_id", "listing_key", "title",
            "dev_account", "question_text", "asked_utc", "answered",
            "answer_text", "answered_utc"}

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


def seed_world(led, dk, am, clock):
    """Owner dana publishes three listings; bob and carol ask in a
    scrambled order, one question is answered, and the shelf holding
    carol's last question retires."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-BQ-A", "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-BQ-S", "settlement")
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
    # one sale so the report derives usr:bob as a buyer and the buyer
    # block carrying the questions key is actually rendered.
    clock.set("2026-10-25T08:10:00Z")
    am.purchase_api("usr:bob", ids["alpha"], "buyerq-sale-1")
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="ambq-")
    db_path = os.path.join(tmp, "buyerq.db")
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

        # Questions land in a scrambled order on purpose: bob's first
        # answered question is neither the oldest nor the newest row of
        # his merged time line.
        clock.set("2026-10-25T09:00:00Z")
        q1 = am.ask_question("usr:bob", ids["alpha"],
                             "  does this support batch calls?  ")
        clock.set("2026-10-25T09:10:00Z")
        am.ask_question("usr:carol", ids["alpha"],
                        "is there a sample response?")
        clock.set("2026-10-25T09:20:00Z")
        am.ask_question("usr:bob", ids["beta"],
                        "what is the rate limit?")
        clock.set("2026-10-25T09:30:00Z")
        a1 = am.answer_question("usr:dana", q1["question_id"],
                                "yes, up to 500 calls per batch")
        clock.set("2026-10-25T09:40:00Z")
        am.ask_question("usr:carol", ids["gamma"],
                        "does this include history?")
        clock.set("2026-10-25T10:00:00Z")
        am.delist_api("usr:dana", ids["gamma"])

        bob = am.api_buyer_questions("usr:bob")
        newbie = am.api_buyer_questions("usr:newbie")

        # -- AC-AMBQ1 shape + honest empty ----------------------------
        ok1 = (set(bob.keys()) == ENVELOPE_KEYS
               and all(set(row.keys()) == ROW_KEYS
                       for row in bob["rows"])
               and set(newbie.keys()) == ENVELOPE_KEYS
               and newbie["listing_count"] == 0
               and newbie["question_count"] == 0
               and newbie["answered_count"] == 0
               and newbie["unanswered_count"] == 0
               and newbie["oldest_open_utc"] is None
               and newbie["rows"] == []
               and bob["disclaimer"] == DISCLAIMER)
        record("AC-AMBQ1", ok1,
               "envelope=%r rows=%d newbie=(%d,%r) disclaimer=%r"
               % (set(bob.keys()) == ENVELOPE_KEYS, len(bob["rows"]),
                  newbie["question_count"], newbie["rows"],
                  bob["disclaimer"] == DISCLAIMER))

        # -- AC-AMBQ2 buyer isolation ---------------------------------
        carol = am.api_buyer_questions("usr:carol")
        seller_view = am.api_buyer_questions("usr:dana")
        bob_ids = {row["question_id"] for row in bob["rows"]}
        carol_ids = {row["question_id"] for row in carol["rows"]}
        ok2 = (len(bob["rows"]) == 2
               and len(carol["rows"]) == 2
               and not (bob_ids & carol_ids)
               and seller_view["question_count"] == 0
               and seller_view["rows"] == []
               and carol["question_count"] == 2)
        record("AC-AMBQ2", ok2,
               "bob=%d carol=%d overlap=%r seller_empty=%r"
               % (len(bob["rows"]), len(carol["rows"]),
                  sorted(bob_ids & carol_ids),
                  seller_view["rows"] == []))

        # -- AC-AMBQ3 counts + total order ----------------------------
        order = [(row["asked_utc"], row["question_id"])
                 for row in bob["rows"]]
        first_open = next(row["asked_utc"] for row in bob["rows"]
                          if not row["answered"])
        thread = am.api_listing_qna(ids["alpha"])
        thread_row = [q for q in thread["questions"]
                      if q["question_id"] == q1["question_id"]][0]
        answered_row = [row for row in bob["rows"]
                        if row["question_id"] == q1["question_id"]][0]
        ok3 = (order == sorted(order)
               and bob["question_count"] == len(bob["rows"])
               and bob["answered_count"] + bob["unanswered_count"]
               == bob["question_count"]
               and bob["answered_count"] == 1
               and bob["unanswered_count"] == 1
               and bob["oldest_open_utc"] == first_open
               and answered_row["answered"] is True
               and answered_row["answer_text"] == thread_row["answer_text"]
               == a1["answer_text"]
               and answered_row["answered_utc"]
               == thread_row["answered_utc"] == a1["answered_utc"]
               and answered_row["question_text"]
               == "does this support batch calls?")
        record("AC-AMBQ3", ok3,
               "order=%r counts=(%d,%d,%d) oldest=%r answer=%r"
               % (order, bob["question_count"], bob["answered_count"],
                  bob["unanswered_count"], bob["oldest_open_utc"],
                  answered_row["answer_text"]))

        # -- AC-AMBQ4 merged across listings + current metadata ------
        listings = {row["listing_id"] for row in bob["rows"]}
        beta_before = [row for row in bob["rows"]
                       if row["listing_id"] == ids["beta"]][0]["title"]
        clock.set("2026-10-25T10:30:00Z")
        am.edit_listing("usr:dana", ids["beta"],
                        title="Service Beta v2")
        bob_after_edit = am.api_buyer_questions("usr:bob")
        beta_after = [row for row in bob_after_edit["rows"]
                      if row["listing_id"] == ids["beta"]][0]["title"]
        keys_ok = all(row["listing_key"] == "beta"
                      for row in bob_after_edit["rows"]
                      if row["listing_id"] == ids["beta"])
        ok4 = (listings == {ids["alpha"], ids["beta"]}
               and bob["listing_count"] == 2
               and bob["question_count"] == 2
               and beta_before == "Service Beta"
               and beta_after == "Service Beta v2"
               and keys_ok
               and [row["asked_utc"] for row in bob["rows"]]
               == sorted(row["asked_utc"] for row in bob["rows"]))
        record("AC-AMBQ4", ok4,
               "listings=%d question_count=%d title=%r->%r keys=%r"
               % (bob["listing_count"], bob["question_count"],
                  beta_before, beta_after, keys_ok))

        # -- AC-AMBQ5 retired listing keeps its history --------------
        carol_gamma = [row for row in carol["rows"]
                       if row["listing_id"] == ids["gamma"]]
        gamma_thread = am.api_listing_qna(ids["gamma"])
        ok5 = (len(carol_gamma) == 1
               and carol_gamma[0]["title"] == "Service Gamma"
               and carol_gamma[0]["answered"] is False
               and carol_gamma[0]["question_text"]
               == "does this include history?"
               and gamma_thread["retired"] is True
               and gamma_thread["question_count"] == 1)
        record("AC-AMBQ5", ok5,
               "gamma_rows=%d title=%r retired=%r thread_q=%d"
               % (len(carol_gamma),
                  carol_gamma[0]["title"] if carol_gamma else None,
                  gamma_thread["retired"],
                  gamma_thread["question_count"]))

        # -- AC-AMBQ6 pure read + fail-closed account gate -----------
        bob_now = am.api_buyer_questions("usr:bob")
        before = market_digests(am)
        before_tx = ledger_tx_ids(led)
        codes = []
        for bad in BAD_ACCOUNTS:
            try:
                am.api_buyer_questions(bad)
                codes.append(None)
            except A.ApiMarketError as exc:
                codes.append(code_of(exc))
        after = market_digests(am)
        after_tx = ledger_tx_ids(led)
        stable = bob_now == am.api_buyer_questions("usr:bob")
        ok6 = (codes == [A.E_AM_BAD_ACCOUNT] * len(BAD_ACCOUNTS)
               and before == after and before_tx == after_tx
               and stable)
        record("AC-AMBQ6", ok6,
               "codes=%r digests_same=%r tx_same=%r read_stable=%r"
               % (codes, before == after, before_tx == after_tx, stable))

        # -- AC-AMBQ7 cross-restart byte identity --------------------
        bob_dump = dumps(am.api_buyer_questions("usr:bob"))
        carol_dump = dumps(am.api_buyer_questions("usr:carol"))
        close_stack(am, dk, metered, led)
        dumps_seen = []
        for _index in range(3):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            try:
                dumps_seen.append((dumps(am2.api_buyer_questions("usr:bob")),
                                   dumps(am2.api_buyer_questions("usr:carol"))))
            finally:
                close_stack(am2, dk2, metered2, led2)
        ok7 = (dumps_seen[0] == dumps_seen[1] == dumps_seen[2]
               and dumps_seen[0][0] == bob_dump
               and dumps_seen[0][1] == carol_dump)
        record("AC-AMBQ7", ok7,
               "instances identical=%r preclose_equal=%r"
               % (dumps_seen[0] == dumps_seen[1] == dumps_seen[2],
                  dumps_seen[0][0] == bob_dump))

        # -- AC-AMBQ8 report consumer, wiring, hygiene ---------------
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
        clock.set("2026-10-25T11:00:00Z")
        am.ask_question("usr:bob", ids["alpha"],
                        "<script>alert(1)</script>")
        report = R.collect(am)
        page = R.render_html(report)
        block = report["buyers"]["usr:bob"]
        payload = R.api_report_payload(report)
        legacy = json.loads(json.dumps(report))
        for buyer in legacy["buyers"]:
            legacy["buyers"][buyer].pop("questions", None)
        legacy.pop("attention", None)
        legacy_page = R.render_html(legacy)
        with open(RECONCILE, "rb") as handle:
            wired = b"ledger-apimarket-buyerquestions" in handle.read()
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
        ok8 = (R.REPORT_SCHEMA >= 12
               and set(payload.keys()) == {"schema_version", "report",
                                           "attention"}
               and payload["schema_version"] == R.REPORT_SCHEMA
               and "questions" in block
               and block["questions"]["question_count"] == 3
               and block["questions"]["unanswered_count"] == 2
               and set(block["questions"].keys()) == ENVELOPE_KEYS
               and "my questions" in page
               and "&lt;script&gt;alert(1)&lt;/script&gt;" in page
               and "<script>alert(1)</script>" not in page
               and "my questions" in legacy_page
               and "no questions asked by this buyer" in legacy_page
               and wired and ascii_ok and not net_imports)
        record("AC-AMBQ8", ok8,
               "schema=%d keys=%r questions=(%d,%d) page=%r escaped=%r"
               " legacy=%r wired=%r ascii=%r net=%d"
               % (R.REPORT_SCHEMA,
                  set(payload.keys()) == {"schema_version", "report",
                                          "attention"},
                  block.get("questions", {}).get("question_count"),
                  block.get("questions", {}).get("unanswered_count"),
                  "my questions" in page,
                  "&lt;script&gt;" in page,
                  "my questions" in legacy_page, wired, ascii_ok,
                  len(net_imports)))
    finally:
        A._now_utc = original_now
        try:
            close_stack(am, dk, metered, led)
        except Exception:
            pass

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    print("SUITE %d/%d" % (passed, total))
    return 0 if (passed == total and total == 8) else 1


if __name__ == "__main__":
    sys.exit(main())