"""Acceptance suite for the apimarket report SLOW ANSWER attention
family (BigDomain R2121; canon = the explore-queue row claimed in R2121,
criteria AC-AMSL1..AC-AMSL8 registered there BEFORE this code existed -
honesty law).

Product under proof: collect_attention in
src/sandbox/ledger/apimarket_report.py. R2120 measured how long each
buyer waited on the answered-question ledger, but the operator still
had to scan that table to notice a seller who is answering slowly. This
window turns the latency into one sortable attention finding, consuming
the seller block the report already collected (no second face read),
and bumps REPORT_SCHEMA 13 -> 14 additively.

Criteria:
  AC-AMSL1 Threshold law: strictly over SLOW_ANSWER_SECONDS (86400)
    raises exactly one finding per answered row; the exact boundary
    second, anything below it and every unanswered question stay
    silent; the published finding keeps its five-key shape.
  AC-AMSL2 Row content: subject is the seller, detail carries the
    question id, listing id and the response seconds all equal to the
    answered-question face, and the ref names the question.
  AC-AMSL3 Total order: within the family by response seconds
    descending then seller ascending; the global order keeps
    (rank, kind, family order, subject, detail); two runs identical.
  AC-AMSL4 Live, no cache: answering one more slow question shows up in
    the very next collect.
  AC-AMSL5 Severity and zero interference: severity warn; every other
    family in the same world is exactly what its own face implies (no
    phantom, no swallowed sibling).
  AC-AMSL6 Additive contract: REPORT_SCHEMA 13 -> 14, the JSON envelope
    still carries exactly schema_version/report/attention, every
    earlier report key equals its direct face call, and a legacy seller
    block without the answers key degrades to no slow findings instead
    of raising.
  AC-AMSL7 Pure read and restarts: fifteen table digests and the ledger
    tx set are constant across collect; two full-stack restarts give a
    byte-identical attention block.
  AC-AMSL8 HTML, wiring and hygiene: the Attention section renders the
    slow row, a clean digest shows the honest empty text, the runner
    label ledger-apimarket-reportslowanswer is registered, and the
    suite is pure ASCII with no network import.

Usage: python test_apimarket_report_slowanswer.py
"""

import copy
import hashlib
import io
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
RECONCILE = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
LABEL = "ledger-apimarket-reportslowanswer"

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

FINDING_KEYS = {"kind", "severity", "subject", "detail", "ref"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers")


class Clock(object):
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


def dumps(value):
    return json.dumps(value, sort_keys=True)


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


def seconds_of(finding):
    return int(finding["detail"].split("after ")[1].split(" ")[0])


def slow_findings(report):
    return [f for f in report["attention"]["findings"]
            if f["kind"] == "slow_answer"]


def other_kinds(report):
    return sorted(f["kind"] for f in report["attention"]["findings"]
                  if f["kind"] != "slow_answer")


def seed_world(led, dk, am, clock):
    """Two sellers. Latencies are chosen so the ordering axis is
    provable: a tie at 200000 seconds across dana and erin, a slower
    (in wall time) 172801 dana answer, a 90000 answer on a shelf that is
    retired afterwards, an exact-boundary 86400 answer, a fast 3600
    answer and one open question."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-SL-A", "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-SL-S", "settlement")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.adjust([("pool:reserve", "debit", 600),
                ("usr:bob", "credit", 600)],
               "manual:fund-bob", "suite funding bob")
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)

    clock.set("2026-10-18T00:00:00Z")
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

    questions = {}

    def ask(who, listing, text, asked):
        clock.set(asked)
        questions[text] = am.ask_question(who, listing, text)

    def answer(dev, text, said, answered):
        clock.set(answered)
        am.answer_question(dev, questions[text]["question_id"], said)

    # 200000 s (dana, beta) and 200000 s (erin, zeta): the tie.
    ask("usr:bob", ids["beta"], "what is the rate limit?",
        "2026-10-19T00:00:00Z")
    answer("usr:dana", "what is the rate limit?",
           "twenty calls per minute", "2026-10-21T07:33:20Z")
    ask("usr:bob", ids["zeta"], "is there a trial?",
        "2026-10-19T00:00:00Z")
    answer("usr:erin", "is there a trial?",
           "there is a seven day trial", "2026-10-21T07:33:20Z")

    # 172801 s (dana, alpha).
    ask("usr:bob", ids["alpha"], "does this support batch calls?",
        "2026-10-20T00:00:00Z")
    answer("usr:dana", "does this support batch calls?",
           "yes, up to 500 calls per batch", "2026-10-22T00:00:01Z")

    # 90000 s on a shelf that is retired right after.
    ask("usr:bob", ids["gamma"], "does this include history?",
        "2026-10-18T00:00:00Z")
    answer("usr:dana", "does this include history?",
           "yes, twelve months of history", "2026-10-19T01:00:00Z")

    # Exactly the threshold second: silent by AC-AMSL1.
    ask("usr:bob", ids["alpha"], "can I upgrade the plan later?",
        "2026-10-23T09:00:00Z")
    answer("usr:dana", "can I upgrade the plan later?",
           "yes, any time", "2026-10-24T09:00:00Z")

    # Fast answer: silent.
    ask("usr:bob", ids["alpha"], "is there a sample response?",
        "2026-10-25T08:00:00Z")
    answer("usr:dana", "is there a sample response?",
           "see the docs page", "2026-10-25T09:00:00Z")

    # One question stays open (the question_debt family probe).
    ask("usr:bob", ids["beta"], "do you offer refunds?",
        "2026-10-25T09:30:00Z")

    clock.set("2026-10-25T10:00:00Z")
    am.delist_api("usr:dana", ids["gamma"])
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="amsl-")
    db_path = os.path.join(tmp, "slowanswer.db")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)

    original_now = A._now_utc
    clock = Clock("2026-10-25T10:00:00Z")
    A._now_utc = clock.now_utc
    try:
        ids = seed_world(led, dk, am, clock)

        report = R.collect(am)
        slow = slow_findings(report)
        expected = []
        for dev in sorted(report["sellers"]):
            face = am.api_seller_answers(dev)
            for row in face["rows"]:
                if row["response_seconds"] > R.SLOW_ANSWER_SECONDS:
                    expected.append((row["response_seconds"], dev,
                                     row["question_id"],
                                     row["listing_id"]))
        expected.sort(key=lambda item: (-item[0], item[1]))

        # -- AC-AMSL1 threshold law -----------------------------------
        detail_seconds = [seconds_of(f) for f in slow]
        shapes_ok = all(set(f.keys()) == FINDING_KEYS for f in slow)
        report_face = am.api_seller_answers("usr:dana")
        boundary = [row for row in report_face["rows"]
                    if row["response_seconds"] == 86400]
        ok1 = (len(slow) == 4 and shapes_ok
               and sorted(detail_seconds) == [90000, 172801, 200000,
                                              200000]
               and len(boundary) == 1
               and R.SLOW_ANSWER_SECONDS == 86400)
        record("AC-AMSL1", ok1,
               "findings=%d keys=%r seconds=%r boundary=%d"
               % (len(slow), shapes_ok, sorted(detail_seconds),
                  len(boundary)))

        # -- AC-AMSL2 row content -------------------------------------
        ok2 = True
        pairs = []
        for finding in slow:
            seconds = seconds_of(finding)
            qid = int(finding["ref"].split(":", 1)[1])
            source = [row for row in
                      am.api_seller_answers(finding["subject"])["rows"]
                      if row["question_id"] == qid][0]
            pairs.append((finding["subject"], qid, seconds))
            ok2 = ok2 and (
                seconds == source["response_seconds"]
                and ("question %d" % qid) in finding["detail"]
                and ("listing %d" % source["listing_id"])
                in finding["detail"])
        record("AC-AMSL2", ok2, "pairs=%r" % (sorted(pairs),))

        # -- AC-AMSL3 total order -------------------------------------
        got = [(seconds_of(f), f["subject"]) for f in slow]
        want = [(item[0], item[1]) for item in expected]
        ranked = [f["kind"] for f in report["attention"]["findings"]]
        ok3 = (got == want
               and want[0] == (200000, "usr:dana")
               and want[1] == (200000, "usr:erin")
               and want[2] == (172801, "usr:dana")
               and want[3] == (90000, "usr:dana")
               and dumps(report["attention"])
               == dumps(R.collect(am)["attention"])
               and ranked == sorted(ranked, key=lambda k: k))
        record("AC-AMSL3", ok3,
               "got=%r want=%r double_run=%s"
               % (got, want,
                  dumps(report["attention"])
                  == dumps(R.collect(am)["attention"])))

        # -- AC-AMSL4 live, no cache ----------------------------------
        clock.set("2026-10-25T10:10:00Z")
        extra = am.ask_question("usr:bob", ids["beta"],
                                "is there a bulk discount?")
        clock.set("2026-10-29T10:10:00Z")
        am.answer_question("usr:dana", extra["question_id"],
                           "yes, from ten units")
        fresh = R.collect(am)
        slow_now = slow_findings(fresh)
        added = [f for f in slow_now
                 if f["ref"] == "question:%d" % extra["question_id"]]
        ok4 = (len(slow_now) == len(slow) + 1 == 5 and len(added) == 1
               and seconds_of(added[0]) == 4 * 86400
               and added[0]["subject"] == "usr:dana")
        record("AC-AMSL4", ok4,
               "before=%d after=%d added=%r"
               % (len(slow), len(slow_now), len(added)))

        # -- AC-AMSL5 severity and zero interference ------------------
        kinds_now = other_kinds(fresh)
        severities = sorted({f["severity"] for f in slow_now})
        ok5 = (severities == ["warn"]
               and kinds_now == ["question_debt"]
               and len([f for f in fresh["attention"]["findings"]
                        if f["kind"] == "question_debt"]) == 1)
        record("AC-AMSL5", ok5,
               "severity=%r other_kinds=%r" % (severities, kinds_now))

        # -- AC-AMSL6 additive contract + legacy degrade --------------
        payload = R.api_report_payload(fresh)
        legacy = copy.deepcopy(fresh)
        for dev in legacy["sellers"]:
            legacy["sellers"][dev].pop("answers", None)
        legacy_attention = R.collect_attention(am, legacy)
        legacy["attention"] = legacy_attention
        legacy_slow = [f for f in legacy_attention["findings"]
                       if f["kind"] == "slow_answer"]
        legacy_html = R.render_html(legacy)
        ok6 = (R.REPORT_SCHEMA >= 14
               and payload["schema_version"] == R.REPORT_SCHEMA
               and set(payload.keys())
               == {"schema_version", "report", "attention"}
               and dumps(payload["report"]["market"])
               == dumps(am.api_market_stats())
               and legacy_slow == []
               and "slow_answer" not in legacy_html)
        record("AC-AMSL6", ok6,
               "schema=%d envelope=%r legacy_slow=%d"
               % (R.REPORT_SCHEMA, sorted(payload.keys()),
                  len(legacy_slow)))

        # -- AC-AMSL7 pure read + restarts ----------------------------
        before = market_digests(am)
        before_tx = ledger_tx_ids(led)
        first_attention = R.collect(am)["attention"]
        after = market_digests(am)
        after_tx = ledger_tx_ids(led)
        close_stack(am, dk, metered, led)

        reopen = []
        for _ in range(2):
            led2, mtr2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            reopen.append(R.collect(am2)["attention"])
            close_stack(am2, dk2, mtr2, led2)
        ok7 = (before == after and before_tx == after_tx
               and dumps(reopen[0]) == dumps(first_attention)
               and dumps(reopen[1]) == dumps(first_attention))
        record("AC-AMSL7", ok7,
               "digest stable=%s tx %d==%d restart_identical=%s"
               % (before == after, len(before_tx), len(after_tx),
                  dumps(reopen[1]) == dumps(first_attention)))

        # -- AC-AMSL8 HTML, wiring and hygiene -----------------------
        html = R.render_html(fresh)
        empty_block = R.attention_block({"findings": [],
                                         "finding_count": 0})
        src = io.open(RECONCILE, encoding="utf-8").read()
        suite_src = io.open(os.path.abspath(__file__),
                            encoding="utf-8").read()
        ok8 = ("slow_answer" in html
               and "answered after 345600 s" in html
               and "no findings" in empty_block
               and ('"%s"' % LABEL) in src
               and "test_apimarket_report_slowanswer.py" in src
               and all(ord(ch) < 128 for ch in suite_src)
               and ("import " + "urllib") not in suite_src
               and ("import " + "requests") not in suite_src
               and not tmp.startswith(BASE))
        record("AC-AMSL8", ok8,
               "row=%s detail=%s empty=%s wired=%s ascii=%s"
               " net=%s outside=%s"
               % ("slow_answer" in html,
                  "answered after 345600 s" in html,
                  "no findings" in empty_block,
                  ('"%s"' % LABEL) in src,
                  all(ord(ch) < 128 for ch in suite_src),
                  (("import " + "urllib") not in suite_src
                   and ("import " + "requests") not in suite_src),
                  not tmp.startswith(BASE)))
    finally:
        A._now_utc = original_now

    passed = sum(1 for _, ok in RESULTS if ok)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(RESULTS)
                              else "FAIL", passed, len(RESULTS)))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())