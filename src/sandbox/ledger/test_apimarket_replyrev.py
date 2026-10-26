"""Acceptance suite for the apimarket seller reply-revision leg
(BigDomain R2143; canon = the explore-queue row seeded and claimed in
R2143, criteria AC-AMRY1..AC-AMRY8 registered in that claim note
BEFORE this code existed - honesty law; the AC-AMRY prefix,
revise_reply, api_reply_history, apimarket_reply_revisions,
E_AM_REPLY_UNCHANGED, E_AM_UNKNOWN_REPLY, this suite name and the
ledger-apimarket-replyrev runner label were all git-grep
zero-occupancy anchored 2026-10-26, rc=1).

Face under proof: APIMarketFace.revise_reply + api_reply_history.
reply_to_rating (R2093) is write-once behind UNIQUE(rating_id), while
revise_rating (R2094) lets the buyer change the star value at any
time, so a seller who answered under five stars stays welded to that
sentence when the same rating becomes one star. This window pins the
last write-once axis on the trust face:

  - the append-only contract and the frozen base reply row;
  - the pinned gate order with zero side effects on every refusal;
  - the unchanged gate judged against the EFFECTIVE text (so revising
    back to an earlier wording stays legal);
  - the single seam into api_rating_replies, plus the rule that a
    retired listing keeps its reply leg revisable;
  - the history read face and its shapes;
  - the pure-read law and transfer-free revisions;
  - orthogonality with the buyer-side rating revision;
  - cross-restart byte identity, product-file stability, the ASCII
    source law and the runner registration.

Usage: python test_apimarket_replyrev.py
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

PRODUCT_FILES = [
    os.path.join(BASE, "apimarket.py"),
    os.path.join(BASE, "apidev.py"),
    os.path.join(BASE, "ledger.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]

REVISION_KEYS = {"revision_id", "reply_id", "rating_id", "listing_id",
                 "dev_account", "previous_text", "reply_text",
                 "revised_utc", "disclaimer"}

HISTORY_KEYS = {"reply_id", "rating_id", "listing_id", "dev_account",
                "buyer_id", "stars", "effective_text", "base_text",
                "revision_count", "latest_revised_utc", "disclaimer",
                "revisions"}

HISTORY_ROW_KEYS = {"revision_id", "previous_text", "reply_text",
                    "revised_utc"}


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
    names = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
        " AND name LIKE 'apimarket_%' ORDER BY name").fetchall()]
    out = {t: table_digest(conn, t) for t in names}
    conn.close()
    return out


def ledger_tx_ids(led):
    conn = sqlite3.connect(led.db_path)
    ids = set(str(r[0]) for r in conn.execute(
        "SELECT tx_id FROM ledger_tx").fetchall())
    conn.close()
    return ids


def balances(led):
    return {who: led.balance(who)
            for who in ("usr:bob", "usr:carol", "usr:dana",
                        "pool:reserve", "pool:share")}


def base_reply_row(am, reply_id):
    conn = sqlite3.connect(am.db_path)
    row = conn.execute(
        "SELECT reply_id, rating_id, listing_id, dev_account,"
        " reply_text, replied_utc FROM apimarket_rating_replies"
        " WHERE reply_id = ?", (reply_id,)).fetchone()
    conn.close()
    return row


def revision_rows(am, reply_id):
    conn = sqlite3.connect(am.db_path)
    rows = conn.execute(
        "SELECT revision_id, rating_id, listing_id, dev_account,"
        " previous_text, reply_text, revised_utc"
        " FROM apimarket_reply_revisions WHERE reply_id = ?"
        " ORDER BY revision_id", (reply_id,)).fetchall()
    conn.close()
    return rows


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


def seed_world(led, dk, am):
    """dana sells L1 (10) and L2 (5). bob rates L1 five stars and
    dana answers; carol rates L1 four stars with no answer (the
    honest unanswered row). carol rates L2 two stars and dana
    answers, then L2 is retired to prove the reply leg stays alive
    after retirement."""
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-AMRY-A",
                     "settlement")
    led.mint_to_pool("pool:share", 20000, "SETTLE-AMRY-S",
                     "settlement")
    for who in ("bob", "carol"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 400),
                    ("usr:" + who, "credit", 400)],
                   "manual:fund-" + who, "suite funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    l1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                        "portfolio risk scan endpoint", PAYLOAD, 10,
                        False, category="data")["listing_id"]
    l2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                        "daily macro data feed", PAYLOAD, 5, False,
                        category="data")["listing_id"]
    am.purchase_api("usr:bob", l1, "ref-bob-l1")
    am.purchase_api("usr:carol", l1, "ref-carol-l1")
    am.purchase_api("usr:carol", l2, "ref-carol-l2")
    bob_rating = am.rate_api("usr:bob", l1, 5)["rating_id"]
    carol_rating = am.rate_api("usr:carol", l1, 4)["rating_id"]
    carol_l2_rating = am.rate_api("usr:carol", l2, 2)["rating_id"]
    reply1 = am.reply_to_rating("usr:dana", bob_rating,
                                "  glad it worked  ")["reply_id"]
    reply2 = am.reply_to_rating("usr:dana", carol_l2_rating,
                                "sorry about that")["reply_id"]
    return (l1, l2, bob_rating, carol_rating, carol_l2_rating,
            reply1, reply2)


def main():
    tmp = tempfile.mkdtemp(prefix="apimarket-replyrev-")
    db_path = os.path.join(tmp, "ledger.db")

    shas_before = {p: sha_file(p) for p in PRODUCT_FILES}

    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    (l1, l2, bob_rating, carol_rating, carol_l2_rating,
     reply1, reply2) = seed_world(led, dk, am)

    # -- AC-AMRY1 append-only contract and the frozen base row ---------
    base_before = base_reply_row(am, reply1)
    out = am.revise_reply("usr:dana", reply1,
                          "thanks for the feedback")
    base_after = base_reply_row(am, reply1)
    revs = revision_rows(am, reply1)
    ok1 = (set(out.keys()) == REVISION_KEYS
           and out["reply_id"] == reply1
           and out["rating_id"] == bob_rating
           and out["listing_id"] == l1
           and out["dev_account"] == "usr:dana"
           and out["previous_text"] == "glad it worked"
           and out["reply_text"] == "thanks for the feedback"
           and out["disclaimer"] == DISCLAIMER
           and base_before == base_after
           and len(revs) == 1
           and revs[0][4] == "glad it worked"
           and revs[0][5] == "thanks for the feedback"
           and revs[0][1] == bob_rating and revs[0][2] == l1
           and revs[0][3] == "usr:dana")
    record("AC-AMRY1", ok1,
           "keys=%r base_frozen=%r revs=%d prev=%r new=%r"
           % (sorted(out.keys()), base_before == base_after,
              len(revs), revs[0][4] if revs else None,
              revs[0][5] if revs else None))

    # -- AC-AMRY2 gate family, pinned order, zero side effects ---------
    digests_before = market_digests(am)
    tx_before = ledger_tx_ids(led)
    bal_before = balances(led)
    account_codes = []
    for bad in (None, "", "   ", "dana", 5, True, 1.5,
                ["usr:dana"], {"a": 1}):
        try:
            am.revise_reply(bad, reply1, "text")
            account_codes.append("NO-ERROR")
        except A.ApiMarketError as exc:
            account_codes.append(getattr(exc, "code", "?"))
    # the bare "usr:" prefix passes the shape gate (R2077/R2078
    # precedent) and is then stopped by the ownership gate
    prefix_code = "?"
    try:
        am.revise_reply("usr:", reply1, "text")
    except A.ApiMarketError as exc:
        prefix_code = getattr(exc, "code", "?")
    id_codes = []
    for bad in (0, -1, True, "1", None, 1.5):
        try:
            am.revise_reply("usr:dana", bad, "text")
            id_codes.append("NO-ERROR")
        except A.ApiMarketError as exc:
            id_codes.append(getattr(exc, "code", "?"))
    text_codes = []
    for bad in (None, "", "   ", "x" * 501, 5, True, "bad\x01text"):
        try:
            am.revise_reply("usr:dana", reply1, bad)
            text_codes.append("NO-ERROR")
        except A.ApiMarketError as exc:
            text_codes.append(getattr(exc, "code", "?"))
    order_codes = []
    for call in (lambda: am.revise_reply("dana", 0, None),
                 lambda: am.revise_reply("usr:dana", "1", None),
                 lambda: am.revise_reply("usr:dana", 999999, ""),
                 lambda: am.revise_reply("usr:bob", 999999, " text "),
                 lambda: am.revise_reply("usr:bob", reply1, " text ")):
        try:
            call()
            order_codes.append("NO-ERROR")
        except A.ApiMarketError as exc:
            order_codes.append(getattr(exc, "code", "?"))
    unknown_code = "?"
    try:
        am.revise_reply("usr:dana", 999999, "text")
    except A.ApiMarketError as exc:
        unknown_code = getattr(exc, "code", "?")
    digests_after = market_digests(am)
    tx_after = ledger_tx_ids(led)
    bal_after = balances(led)
    ok2 = (account_codes == ["E_AM_BAD_ACCOUNT"] * 9
           and prefix_code == "E_AM_NOT_OWNER"
           and id_codes == ["E_AM_BAD_ARGS"] * 6
           and text_codes == ["E_AM_BAD_REPLY"] * 7
           and order_codes == ["E_AM_BAD_ACCOUNT", "E_AM_BAD_ARGS",
                               "E_AM_BAD_REPLY", "E_AM_UNKNOWN_REPLY",
                               "E_AM_NOT_OWNER"]
           and unknown_code == "E_AM_UNKNOWN_REPLY"
           and digests_before == digests_after
           and tx_before == tx_after
           and bal_before == bal_after
           and len(revision_rows(am, reply1)) == 1)
    record("AC-AMRY2", ok2,
           "account=%r prefix=%r id=%r text=%r order=%r unknown=%r"
           " digests=%r tx=%r"
           % (set(account_codes), prefix_code, set(id_codes),
              set(text_codes), order_codes, unknown_code,
              digests_before == digests_after, tx_before == tx_after))

    # -- AC-AMRY3 unchanged gate judged against the EFFECTIVE text -----
    first_stamp = revision_rows(am, reply1)[0][6]
    same_code = "?"
    try:
        am.revise_reply("usr:dana", reply1, "thanks for the feedback")
    except A.ApiMarketError as exc:
        same_code = getattr(exc, "code", "?")
    rows_after_same = revision_rows(am, reply1)
    back = am.revise_reply("usr:dana", reply1, "glad it worked")
    forward = am.revise_reply("usr:dana", reply1,
                              "thanks for the feedback")
    rows_now = revision_rows(am, reply1)
    ok3 = (same_code == "E_AM_REPLY_UNCHANGED"
           and len(rows_after_same) == 1
           and rows_after_same[0][6] == first_stamp
           and back["previous_text"] == "thanks for the feedback"
           and back["reply_text"] == "glad it worked"
           and forward["reply_text"] == "thanks for the feedback"
           and len(rows_now) == 3
           and rows_now[0][6] == first_stamp
           and [r[5] for r in rows_now]
           == ["thanks for the feedback", "glad it worked",
               "thanks for the feedback"])
    record("AC-AMRY3", ok3,
           "same=%s count_after_same=%d first_stamp_frozen=%r"
           " series=%r"
           % (same_code, len(rows_after_same),
              rows_now[0][6] == first_stamp if rows_now else None,
              [r[5] for r in rows_now]))

    # -- AC-AMRY4 single seam, frozen neighbours, retired listing ------
    seam = am.api_rating_replies(l1)
    rows_by_rating = {row["rating_id"]: row for row in seam["rows"]}
    base_now = base_reply_row(am, reply1)
    am.delist_api("usr:dana", l2)
    retired_rev = am.revise_reply("usr:dana", reply2,
                                  "sorry - full refund was issued")
    seam_l2 = am.api_rating_replies(l2)
    l2_reply = seam_l2["rows"][0]["reply"]
    ok4 = (rows_by_rating[bob_rating]["reply"]["reply_text"]
           == "thanks for the feedback"
           and rows_by_rating[bob_rating]["reply"]["reply_id"] == reply1
           and rows_by_rating[bob_rating]["reply"]["replied_utc"]
           == base_now[5]
           and rows_by_rating[bob_rating]["stars"] == 5
           and rows_by_rating[carol_rating]["reply"] is None
           and seam["reply_count"] == 1
           and retired_rev["reply_text"]
           == "sorry - full refund was issued"
           and l2_reply["reply_text"] == "sorry - full refund was issued"
           and l2_reply["reply_id"] == reply2
           and seam_l2["rows"][0]["stars"] == 2
           and base_reply_row(am, reply2)[4] == "sorry about that")
    record("AC-AMRY4", ok4,
           "seam=%r unanswered=%r retired_effective=%r base_frozen=%r"
           % (rows_by_rating[bob_rating]["reply"]["reply_text"],
              rows_by_rating[carol_rating]["reply"] is None,
              l2_reply["reply_text"],
              base_reply_row(am, reply2)[4] == "sorry about that"))

    # -- AC-AMRY5 the history read face --------------------------------
    hist = am.api_reply_history(reply1)
    hist_keys_ok = set(hist.keys()) == HISTORY_KEYS
    row_keys_ok = all(set(r.keys()) == HISTORY_ROW_KEYS
                      for r in hist["revisions"])
    unknown_code = "?"
    try:
        am.api_reply_history(999999)
    except A.ApiMarketError as exc:
        unknown_code = getattr(exc, "code", "?")
    bad_code = "?"
    try:
        am.api_reply_history("1")
    except A.ApiMarketError as exc:
        bad_code = getattr(exc, "code", "?")
    bad_zero = "?"
    try:
        am.api_reply_history(0)
    except A.ApiMarketError as exc:
        bad_zero = getattr(exc, "code", "?")
    ok5 = (hist_keys_ok and row_keys_ok
           and hist["reply_id"] == reply1
           and hist["rating_id"] == bob_rating
           and hist["listing_id"] == l1
           and hist["dev_account"] == "usr:dana"
           and hist["buyer_id"] == "usr:bob"
           and hist["stars"] == 5
           and hist["base_text"] == "glad it worked"
           and hist["effective_text"] == "thanks for the feedback"
           and hist["revision_count"] == len(hist["revisions"]) == 3
           and hist["latest_revised_utc"]
           == hist["revisions"][-1]["revised_utc"]
           and [r["revision_id"] for r in hist["revisions"]]
           == sorted(r["revision_id"] for r in hist["revisions"])
           and hist["revisions"][0]["previous_text"]
           == "glad it worked"
           and hist["disclaimer"] == DISCLAIMER
           and unknown_code == "E_AM_UNKNOWN_REPLY"
           and bad_code == "E_AM_BAD_ARGS" and bad_zero == "E_AM_BAD_ARGS")
    record("AC-AMRY5", ok5,
           "env_keys=%r row_keys=%r base=%r effective=%r count=%d"
           " unknown=%s bad=%s"
           % (hist_keys_ok, row_keys_ok, hist["base_text"],
              hist["effective_text"], hist["revision_count"],
              unknown_code, bad_code))

    # -- AC-AMRY6 pure read and zero token movement --------------------
    tx_before = ledger_tx_ids(led)
    bal_before = balances(led)
    digests_before = market_digests(am)
    reads = [dumps(am.api_rating_replies(l1)),
             dumps(am.api_reply_history(reply1)),
             dumps(am.api_rating_replies(l2)),
             dumps(am.api_reply_history(reply2))]
    repeat = [dumps(am.api_rating_replies(l1)),
              dumps(am.api_reply_history(reply1)),
              dumps(am.api_rating_replies(l2)),
              dumps(am.api_reply_history(reply2))]
    tx_after = ledger_tx_ids(led)
    bal_after = balances(led)
    digests_after = market_digests(am)
    ok6 = (reads == repeat
           and tx_before == tx_after
           and bal_before == bal_after
           and digests_before == digests_after)
    record("AC-AMRY6", ok6,
           "repeat=%r tx_equal=%r balances_equal=%r digests_equal=%r"
           " sha16=%s"
           % (reads == repeat, tx_before == tx_after,
              bal_before == bal_after,
              digests_before == digests_after,
              hashlib.sha256(reads[1].encode("utf-8"))
              .hexdigest()[:16]))

    # -- AC-AMRY7 orthogonality with the rating revision ---------------
    before_reply = am.api_rating_replies(l1)["rows"][0]["reply"]
    before_hist = am.api_reply_history(reply1)
    am.revise_rating("usr:bob", bob_rating, 2)
    after_reply = am.api_rating_replies(l1)["rows"][0]["reply"]
    after_hist = am.api_reply_history(reply1)
    view = am.api_view(l1)
    rating_hist = am.api_rating_history(bob_rating)
    # a rating revision moves the stars only: the reply row itself
    # (id, author, wording, stamp) and the revision count stay frozen
    text_frozen = (before_reply == after_reply
                   and before_hist["effective_text"]
                   == after_hist["effective_text"]
                   and before_hist["revision_count"]
                   == after_hist["revision_count"]
                   and before_hist["base_text"] == after_hist["base_text"])
    stars_moved = (rating_hist["effective_stars"] == 2
                   and after_hist["stars"] == 2)
    stars_before = am.api_view(l1)["rating_count"]
    avg_before = am.api_view(l1)["rating_avg"]
    final_rev = am.revise_reply("usr:dana", reply1, "final wording")
    view_after = am.api_view(l1)
    after2_hist = am.api_reply_history(reply1)
    stars_frozen = (view_after["rating_count"] == stars_before == 2
                    and view_after["rating_avg"] == avg_before == 3.0
                    and after2_hist["stars"] == 2
                    and am.api_rating_history(bob_rating)
                    ["effective_stars"] == 2)
    text_moved = (after2_hist["effective_text"] == "final wording"
                  and after2_hist["revision_count"] == 4
                  and final_rev["previous_text"]
                  == "thanks for the feedback"
                  and am.api_rating_replies(l1)["rows"][0]["reply"]
                  ["reply_text"] == "final wording")
    ok7 = text_frozen and stars_moved and stars_frozen and text_moved
    record("AC-AMRY7", ok7,
           "text_frozen_on_rating_rev=%r stars_moved=%r"
           " stars_frozen_on_reply_rev=%r text_moved=%r count=%d"
           " avg=%.4f"
           % (text_frozen, stars_moved, stars_frozen, text_moved,
              view_after["rating_count"], view_after["rating_avg"]))

    # -- AC-AMRY8 cross-restart identity, files, ASCII, wiring ---------
    first = dumps({"l1": am.api_rating_replies(l1),
                   "l2": am.api_rating_replies(l2),
                   "h1": am.api_reply_history(reply1),
                   "h2": am.api_reply_history(reply2)})
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    second = dumps({"l1": am.api_rating_replies(l1),
                    "l2": am.api_rating_replies(l2),
                    "h1": am.api_reply_history(reply1),
                    "h2": am.api_reply_history(reply2)})
    close_stack(am, dk, metered, led)
    led, metered, dk, gate, am = build_stack(db_path, cfg, lobby_cfg)
    third = dumps({"l1": am.api_rating_replies(l1),
                   "l2": am.api_rating_replies(l2),
                   "h1": am.api_reply_history(reply1),
                   "h2": am.api_reply_history(reply2)})
    shas_after = {p: sha_file(p) for p in PRODUCT_FILES}
    runner = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
    with open(runner, "rb") as handle:
        runner_text = handle.read().decode("utf-8")
    with open(os.path.abspath(__file__), "rb") as handle:
        own = handle.read()
    ok8 = (first == second == third
           and shas_before == shas_after
           and "ledger-apimarket-replyrev" in runner_text
           and all(b < 128 for b in bytearray(own)))
    record("AC-AMRY8", ok8,
           "sha16=%s identical=%r files_equal=%r registered=%r"
           " ascii=%r"
           % (hashlib.sha256(first.encode("utf-8")).hexdigest()[:16],
              first == second == third, shas_before == shas_after,
              "ledger-apimarket-replyrev" in runner_text,
              all(b < 128 for b in bytearray(own))))

    close_stack(am, dk, metered, led)

    passed = sum(1 for _ac, ok in RESULTS if ok)
    total = len(RESULTS)
    verdict = "SUITE PASS %d/%d" % (passed, total)
    if passed != total:
        verdict = "SUITE FAIL %d/%d" % (passed, total)
    print(verdict, flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())