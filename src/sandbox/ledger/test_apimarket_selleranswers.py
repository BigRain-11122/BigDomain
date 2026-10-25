"""Acceptance suite for the apimarket seller-side answered-question
ledger (BigDomain R2120; canon = the explore-queue row seeded and
claimed in R2120, criteria AC-AMSA1..AC-AMSA8 registered there BEFORE
this suite existed - honesty law; the anchors api_seller_answers,
AC-AMSA, ledger-apimarket-selleranswers and apimarket_report_selleranswers
were all git-grep -F zero-occupancy anchored 2026-10-25, rc=1).

Face under proof: api_seller_answers. R2118 gave the seller the OPEN
debt queue (api_seller_questions rows carry unanswered questions only,
the answered side is one number) and R2119 gave the buyer a merged
history, but the seller had no merged view of what was ANSWERED - the
proving side of the Q&A service. A seller who answered on N listings
had to open N threads and merge by hand, and could not answer any
service-level question (how long did the slowest buyer wait, what is
the mean). This suite pins:

  - the envelope and row shape plus the honest empty state;
  - strict seller isolation (a buyer account sees its own honest empty);
  - the counts arithmetic and the total order on (answered_utc,
    question_id);
  - the latency arithmetic (per-row whole seconds, fastest / slowest /
    mean);
  - the merge across listings, the CURRENT metadata title, the retired
    shelf history and the separation from the unanswered queue;
  - the pure-read law (frozen table digests, constant ledger tx set)
    and the fail-closed account gate;
  - cross-restart byte identity on three instances;
  - the report consumer (seller block answers key, answered-questions
    table, hostile-text escaping, legacy degrade, REPORT_SCHEMA 12 -> 13
    additive), runner wiring and suite hygiene.

Usage: python test_apimarket_selleranswers.py
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

ENVELOPE_KEYS = {"dev_account", "listing_count", "answered_count",
                 "buyer_count", "first_answered_utc",
                 "latest_answered_utc", "fastest_seconds",
                 "slowest_seconds", "mean_seconds", "disclaimer",
                 "rows"}

ROW_KEYS = {"question_id", "answer_id", "listing_id", "listing_key",
            "title", "buyer_id", "question_text", "asked_utc",
            "answer_text", "answered_utc", "response_seconds"}

TABLES = ("apimarket_listings", "apimarket_purchases",
          "apimarket_ratings", "apimarket_rating_revisions",
          "apimarket_delistings", "apimarket_relistings",
          "apimarket_price_revisions", "apimarket_listing_revisions",
          "apimarket_watchlist", "apimarket_unwatchings",
          "apimarket_rating_replies", "apimarket_refunds",
          "apimarket_supply_revisions", "apimarket_questions",
          "apimarket_answers")


class Clock(object):
    """Single mutable stamp behind A._now_utc, so question and answer
    order is testable without sleeping."""

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


def seconds_between(earlier, later):
    """Independent latency re-derivation, written the long way on
    purpose so it never shares a helper with the face under proof."""
    def split(stamp):
        date_part, time_part = stamp.rstrip("Z").split("T")
        y, mo, d = [int(x) for x in date_part.split("-")]
        h, mi, s = [int(x) for x in time_part.split(":")]
        return ((((y * 12 + mo) * 31 + d) * 24 + h) * 60 + mi) * 60 + s
    return split(later) - split(earlier)


def seed_world(led, dk, am, clock):
    """Two sellers, two buyers. dana publishes three listings and
    answers three questions with distinct latencies; erin answers one
    so seller isolation is provable; two dana questions stay open."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-SA-A", "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-SA-S", "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 600),
                    ("usr:" + who, "credit", 600)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:erin", "erin-key", 10, ["backtest"], False)

    clock.set("2026-10-25T08:00:00Z")
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
    clock.set("2026-10-25T08:10:00Z")
    am.purchase_api("usr:bob", ids["alpha"], "sellerans-sale-1")
    return ids


def main():
    tmp = tempfile.mkdtemp(prefix="amsa-")
    db_path = os.path.join(tmp, "sellerans.db")
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

        # Questions land interleaved across listings; the answer order
        # is deliberately neither the ask order nor the listing order.
        clock.set("2026-10-25T09:00:00Z")
        q_alpha_bob = am.ask_question("usr:bob", ids["alpha"],
                                      "  does this support batch calls?  ")
        clock.set("2026-10-25T09:10:00Z")
        am.ask_question("usr:carol", ids["alpha"],
                        "is there a sample response?")
        clock.set("2026-10-25T09:20:00Z")
        q_beta_bob = am.ask_question("usr:bob", ids["beta"],
                                     "what is the rate limit?")
        clock.set("2026-10-25T09:30:00Z")
        q_gamma_carol = am.ask_question("usr:carol", ids["gamma"],
                                        "does this include history?")
        clock.set("2026-10-25T09:40:00Z")
        q_zeta_bob = am.ask_question("usr:bob", ids["zeta"],
                                     "is there a trial?")
        clock.set("2026-10-25T09:50:00Z")
        am.ask_question("usr:carol", ids["beta"],
                        "can I upgrade the plan later?")

        clock.set("2026-10-25T10:00:00Z")
        a_alpha = am.answer_question("usr:dana", q_alpha_bob["question_id"],
                                     "yes, up to 500 calls per batch")
        clock.set("2026-10-25T10:10:00Z")
        a_gamma = am.answer_question("usr:dana",
                                     q_gamma_carol["question_id"],
                                     "yes, twelve months of history")
        clock.set("2026-10-25T10:30:00Z")
        am.answer_question("usr:erin", q_zeta_bob["question_id"],
                           "there is a seven day trial")
        clock.set("2026-10-25T11:10:00Z")
        a_beta = am.answer_question("usr:dana", q_beta_bob["question_id"],
                                    "twenty calls per minute")
        clock.set("2026-10-25T12:00:00Z")
        am.delist_api("usr:dana", ids["gamma"])

        dana = am.api_seller_answers("usr:dana")
        newbie = am.api_seller_answers("usr:newbie")

        # -- AC-AMSA1 shape + honest empty ----------------------------
        ok1 = (set(dana.keys()) == ENVELOPE_KEYS
               and len(dana) == 11
               and all(set(row.keys()) == ROW_KEYS and len(row) == 11
                       for row in dana["rows"])
               and set(newbie.keys()) == ENVELOPE_KEYS
               and newbie["listing_count"] == 0
               and newbie["answered_count"] == 0
               and newbie["buyer_count"] == 0
               and newbie["first_answered_utc"] is None
               and newbie["latest_answered_utc"] is None
               and newbie["fastest_seconds"] is None
               and newbie["slowest_seconds"] is None
               and newbie["mean_seconds"] is None
               and newbie["rows"] == []
               and dana["dev_account"] == "usr:dana"
               and dana["disclaimer"] == DISCLAIMER)
        record("AC-AMSA1", ok1,
               "envelope=%d rows=%d newbie=(%d,%d,%r) disclaimer=%r"
               % (len(dana), len(dana["rows"]),
                  newbie["answered_count"], newbie["listing_count"],
                  newbie["rows"], dana["disclaimer"] == DISCLAIMER))

        # -- AC-AMSA2 seller isolation --------------------------------
        erin = am.api_seller_answers("usr:erin")
        buyer_view = am.api_seller_answers("usr:bob")
        dana_ids = {row["answer_id"] for row in dana["rows"]}
        erin_ids = {row["answer_id"] for row in erin["rows"]}
        ok2 = (len(erin["rows"]) == 1
               and erin["rows"][0]["listing_id"] == ids["zeta"]
               and erin["answered_count"] == 1
               and not (dana_ids & erin_ids)
               and buyer_view["answered_count"] == 0
               and buyer_view["rows"] == []
               and all(row["listing_id"] != ids["zeta"]
                       for row in dana["rows"]))
        record("AC-AMSA2", ok2,
               "dana=%d erin=%d overlap=%r buyer_empty=%r"
               % (len(dana["rows"]), len(erin["rows"]),
                  sorted(dana_ids & erin_ids), buyer_view["rows"] == []))

        # -- AC-AMSA3 counts + total order ----------------------------
        order = [(row["answered_utc"], row["question_id"])
                 for row in dana["rows"]]
        buyers = {row["buyer_id"] for row in dana["rows"]}
        ok3 = (order == sorted(order)
               and dana["answered_count"] == len(dana["rows"]) == 3
               and dana["buyer_count"] == len(buyers) == 2
               and buyers == {"usr:bob", "usr:carol"}
               and dana["first_answered_utc"] == dana["rows"][0]["answered_utc"]
               and dana["latest_answered_utc"] == dana["rows"][-1]["answered_utc"]
               and dana["first_answered_utc"] == "2026-10-25T10:00:00Z"
               and dana["latest_answered_utc"] == "2026-10-25T11:10:00Z"
               and dana["listing_count"] == 3)
        record("AC-AMSA3", ok3,
               "order=%r counts=(%d,%d) span=(%r..%r) listings=%d"
               % (order, dana["answered_count"], dana["buyer_count"],
                  dana["first_answered_utc"], dana["latest_answered_utc"],
                  dana["listing_count"]))

        # -- AC-AMSA4 latency arithmetic ------------------------------
        per_row = [(row["response_seconds"],
                    seconds_between(row["asked_utc"], row["answered_utc"]))
                   for row in dana["rows"]]
        latencies = [row["response_seconds"] for row in dana["rows"]]
        ok4 = (all(got == want for got, want in per_row)
               and latencies == [3600, 2400, 6600]
               and dana["fastest_seconds"] == min(latencies) == 2400
               and dana["slowest_seconds"] == max(latencies) == 6600
               and dana["mean_seconds"] == sum(latencies) // len(latencies)
               == 4200
               and erin["fastest_seconds"] == erin["slowest_seconds"]
               == erin["mean_seconds"] == 3000)
        record("AC-AMSA4", ok4,
               "per_row=%r fastest=%r slowest=%r mean=%r erin=%r"
               % (per_row, dana["fastest_seconds"],
                  dana["slowest_seconds"], dana["mean_seconds"],
                  erin["mean_seconds"]))

        # -- AC-AMSA5 merge, metadata seam, unanswered separation -----
        merged = {row["listing_id"] for row in dana["rows"]}
        beta_before = [row for row in dana["rows"]
                       if row["listing_id"] == ids["beta"]][0]["title"]
        clock.set("2026-10-25T12:30:00Z")
        am.edit_listing("usr:dana", ids["beta"], title="Service Beta v2")
        dana_after_edit = am.api_seller_answers("usr:dana")
        beta_after = [row for row in dana_after_edit["rows"]
                      if row["listing_id"] == ids["beta"]][0]["title"]
        open_queue = am.api_seller_questions("usr:dana")
        open_ids = {row["question_id"] for row in open_queue["rows"]}
        answered_ids = {row["question_id"] for row in dana["rows"]}
        ok5 = (merged == {ids["alpha"], ids["beta"], ids["gamma"]}
               and beta_before == "Service Beta"
               and beta_after == "Service Beta v2"
               and all(row["listing_key"] == "beta"
                       for row in dana_after_edit["rows"]
                       if row["listing_id"] == ids["beta"])
               and open_queue["answered_count"] == dana["answered_count"] == 3
               and open_queue["unanswered_count"] == 2
               and not (open_ids & answered_ids)
               and q_alpha_bob["question_id"] not in open_ids
               and [row["question_text"] for row in dana["rows"]
                    if row["question_id"] == q_alpha_bob["question_id"]]
               == ["does this support batch calls?"])
        record("AC-AMSA5", ok5,
               "listings=%r title=%r->%r answered_q=%r open_q=%r"
               " overlap=%r"
               % (sorted(merged), beta_before, beta_after,
                  sorted(answered_ids), sorted(open_ids),
                  sorted(open_ids & answered_ids)))

        # -- AC-AMSA6 retired history + pure read + account gate -----
        gamma_rows = [row for row in dana["rows"]
                      if row["listing_id"] == ids["gamma"]]
        gamma_thread = am.api_listing_qna(ids["gamma"])
        dana_now = am.api_seller_answers("usr:dana")
        before = market_digests(am)
        before_tx = ledger_tx_ids(led)
        codes = []
        for bad in BAD_ACCOUNTS:
            try:
                am.api_seller_answers(bad)
                codes.append(None)
            except A.ApiMarketError as exc:
                codes.append(code_of(exc))
        after = market_digests(am)
        after_tx = ledger_tx_ids(led)
        stable = dana_now == am.api_seller_answers("usr:dana")
        ok6 = (len(gamma_rows) == 1
               and gamma_rows[0]["title"] == "Service Gamma"
               and gamma_rows[0]["answered_utc"]
               == a_gamma["answered_utc"]
               and gamma_rows[0]["answer_text"] == a_gamma["answer_text"]
               and gamma_thread["retired"] is True
               and codes == [A.E_AM_BAD_ACCOUNT] * len(BAD_ACCOUNTS)
               and before == after and before_tx == after_tx
               and stable and len(TABLES) == 15)
        record("AC-AMSA6", ok6,
               "gamma_rows=%d retired=%r codes=%r digests_same=%r"
               " tx_same=%r stable=%r tables=%d"
               % (len(gamma_rows), gamma_thread["retired"], codes,
                  before == after, before_tx == after_tx, stable,
                  len(TABLES)))

        # -- AC-AMSA7 cross-restart byte identity --------------------
        dana_dump = dumps(am.api_seller_answers("usr:dana"))
        erin_dump = dumps(am.api_seller_answers("usr:erin"))
        close_stack(am, dk, metered, led)
        dumps_seen = []
        for _index in range(3):
            led2, metered2, dk2, gate2, am2 = build_stack(
                db_path, cfg, lobby_cfg)
            try:
                dumps_seen.append(
                    (dumps(am2.api_seller_answers("usr:dana")),
                     dumps(am2.api_seller_answers("usr:erin"))))
            finally:
                close_stack(am2, dk2, metered2, led2)
        ok7 = (dumps_seen[0] == dumps_seen[1] == dumps_seen[2]
               and dumps_seen[0][0] == dana_dump
               and dumps_seen[0][1] == erin_dump)
        record("AC-AMSA7", ok7,
               "instances identical=%r preclose_equal=%r"
               % (dumps_seen[0] == dumps_seen[1] == dumps_seen[2],
                  dumps_seen[0][0] == dana_dump))

        # -- AC-AMSA8 report consumer, wiring, hygiene ---------------
        led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
        clock.set("2026-10-25T12:40:00Z")
        hostile = am.answer_question("usr:dana",
                                     am.api_seller_questions("usr:dana")
                                     ["rows"][0]["question_id"],
                                     "<script>alert(1)</script>")
        report = R.collect(am)
        page = R.render_html(report)
        block = report["sellers"]["usr:dana"]
        payload = R.api_report_payload(report)
        legacy = json.loads(json.dumps(report))
        for seller in legacy["sellers"]:
            legacy["sellers"][seller].pop("answers", None)
        legacy.pop("attention", None)
        legacy_page = R.render_html(legacy)
        with open(RECONCILE, "rb") as handle:
            wired = b"ledger-apimarket-selleranswers" in handle.read()
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
        # R2121 note: the schema literal is read from the module constant
        # instead of being pinned to 13, because the additive bump to 14
        # this round is a legal contract extension (R2108/R2109/R2116/
        # R2117/R2119 precedent); the answers key and its envelope stay
        # byte-identical.
        ok8 = (R.REPORT_SCHEMA >= 13
               and set(payload.keys()) == {"schema_version", "report",
                                           "attention"}
               and payload["schema_version"] == R.REPORT_SCHEMA
               and "answers" in block
               and block["answers"]["answered_count"] == 4
               and set(block["answers"].keys()) == ENVELOPE_KEYS
               and "answered questions" in page
               and "&lt;script&gt;alert(1)&lt;/script&gt;" in page
               and "<script>alert(1)</script>" not in page
               and hostile["answer_text"] == "<script>alert(1)</script>"
               and "answered questions" in legacy_page
               and "no answered questions for this seller" in legacy_page
               and wired and ascii_ok and not net_imports)
        record("AC-AMSA8", ok8,
               "schema=%d keys=%r answers=%r page=%r escaped=%r"
               " legacy=%r wired=%r ascii=%r net=%d"
               % (R.REPORT_SCHEMA,
                  set(payload.keys()) == {"schema_version", "report",
                                          "attention"},
                  block.get("answers", {}).get("answered_count"),
                  "answered questions" in page,
                  "&lt;script&gt;" in page,
                  "answered questions" in legacy_page, wired,
                  ascii_ok, len(net_imports)))
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