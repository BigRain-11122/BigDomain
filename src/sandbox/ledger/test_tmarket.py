"""Acceptance suite for the UGC template marketplace face
(BigDomain R1691; canon = explore-queue UGC template marketplace
line: template listing / revenue split / rating three domains;
seed = creator-incentive gradient successor). Asserts the
pre-registered criteria AC-TM1..AC-TM7 from the R1691
explore-queue row (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

The content gate is the lobby SecGate product injected by
reference (no copy): its Chinese wordlists are data loaded from
the lobby config at runtime - this test source stays pure ASCII
per the encoding discipline.

Usage: python test_tmarket.py
"""

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
import tmarket as T                   # noqa: E402 (R1691 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, reference)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: template marketplace is"
              " a creation tool, not investment advice")

PAYLOAD = {"scene": "harbor", "layout": ["pier", "lamprow"],
           "revision": 1}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_tm_error(fn, *codes):
    try:
        fn()
    except T.TMarketError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


class _FaultGate(object):
    """Runtime-fault gate stub: check_text always blows up (the
    face must map this to E_TM_GATE_ERROR and never silently pass
    - AC-TM2 fail-closed posture)."""

    def check_text(self, text):
        raise RuntimeError("stub gate offline")


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="tmarket-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]
    advisory_word = lobby_cfg["gate"]["advisory_ban_words"][0]
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    gate = SecGate.from_config(lobby_cfg)
    tf = T.TMarketFace(led, gate, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 2000, "SETTLE-TM-A", "settlement")
    led.mint_to_pool("pool:share", 1000, "SETTLE-TM-S", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.ensure_account("usr:dave", census_avatar_id="dave")
    for who, amount, tag in (("alice", 400, "a"), ("bob", 500, "b"),
                             ("carol", 300, "c"), ("dave", 100, "d")):
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    bal = lambda who: led.balance("usr:" + who)["balance"]  # noqa: E731
    conn = sqlite3.connect(db_path)

    # -- AC-TM1 listing idempotency + structure ---------------------------
    t1 = tf.publish_template("usr:alice", "harbor-tpl",
                             "Harbor Walk Template",
                             "a calm pier layout", PAYLOAD, 10, False)
    n_tpl0 = _count(conn, "tmarket_templates")
    ok_dup, code_dup = expect_tm_error(
        lambda: tf.publish_template("usr:alice", "harbor-tpl",
                                    "Harbor Walk Template",
                                    "a calm pier layout", PAYLOAD, 10,
                                    False),
        T.E_TM_DUP_TEMPLATE)
    n_tpl1 = _count(conn, "tmarket_templates")
    t2 = tf.publish_template("usr:alice", "night-market",
                             "Night Market Template",
                             "lantern row layout", PAYLOAD, 3, True)
    t3 = tf.publish_template("usr:bob", "harbor-tpl",
                             "Bob Harbor Variant",
                             "same key other creator", PAYLOAD, 7, False)
    n_tpl2 = _count(conn, "tmarket_templates")
    bad1 = []
    raised1 = True
    for label, fn, code in (
            ("svc creator", lambda: tf.publish_template(
                "svc:x", "k", "t", "d", PAYLOAD, 9, False),
             T.E_TM_BAD_ACCOUNT),
            ("zero price", lambda: tf.publish_template(
                "usr:alice", "k0", "t", "d", PAYLOAD, 0, False),
             T.E_TM_BAD_PRICE),
            ("bool price", lambda: tf.publish_template(
                "usr:alice", "k1", "t", "d", PAYLOAD, True, False),
             T.E_TM_BAD_PRICE),
            ("empty title", lambda: tf.publish_template(
                "usr:alice", "k2", "  ", "d", PAYLOAD, 9, False),
             T.E_TM_BAD_ARGS),
            ("empty key", lambda: tf.publish_template(
                "usr:alice", " ", "t", "d", PAYLOAD, 9, False),
             T.E_TM_BAD_ARGS),
            ("empty payload", lambda: tf.publish_template(
                "usr:alice", "k3", "t", "d", {}, 9, False),
             T.E_TM_BAD_ARGS),
            ("non-bool ai flag", lambda: tf.publish_template(
                "usr:alice", "k4", "t", "d", PAYLOAD, 9, "yes"),
             T.E_TM_BAD_ARGS)):
        ok_one, got = expect_tm_error(fn, code)
        if ok_one:
            bad1.append("%s=%s" % (label, got))
        else:
            bad1.append("%s NOT-RAISED(%s)" % (label, got))
            raised1 = False
    n_tpl3 = _count(conn, "tmarket_templates")
    row_labels = [r[0] for r in conn.execute(
        "SELECT ai_label FROM tmarket_templates"
        " ORDER BY template_id").fetchall()]
    ok1 = (t1["ai_label"] == 0 and t2["ai_label"] == 1
           and ok_dup and code_dup == T.E_TM_DUP_TEMPLATE
           and n_tpl0 == 1 and n_tpl1 == 1 and n_tpl2 == 3
           and n_tpl3 == 3 and raised1
           and row_labels == [0, 1, 0]
           and t3["template_id"] != t1["template_id"])
    record("AC-TM1", ok1, "one row per (creator, key): %d rows after"
          " 3 legal publishes; same-(creator,key) republish rejected"
          " %s with zero rows (%d==%d); same key other creator legal"
          " (distinct ids %d/%d); declared labels persist"
          " %s; all %d bad args rejected (%s)"
          % (n_tpl2, code_dup, n_tpl0, n_tpl1,
             t1["template_id"], t3["template_id"], row_labels,
             len(bad1), "; ".join(bad1)))

    # -- AC-TM2 msgSecCheck pre-gate: fail-closed end to end ---------------
    n_g0 = _count(conn, "tmarket_templates")
    ok_t, code_t = expect_tm_error(
        lambda: tf.publish_template(
            "usr:alice", "bad-t", "clean prefix " + bad_word + " suffix",
            "clean desc", PAYLOAD, 9, False),
        T.E_TM_CONTENT_REJECTED)
    ok_d, code_d = expect_tm_error(
        lambda: tf.publish_template(
            "usr:alice", "bad-d", "clean title",
            "clean prefix " + advisory_word + " suffix", PAYLOAD, 9, False),
        T.E_TM_CONTENT_REJECTED)
    ok_clean = tf.publish_template(
        "usr:alice", "clean-t", "Clean Listing", "clean words",
        PAYLOAD, 5, False)
    n_g1 = _count(conn, "tmarket_templates")
    ok_no_gate, code_ng = expect_tm_error(
        lambda: T.TMarketFace(led, None, DISCLAIMER), T.E_TM_NO_GATE)
    fault_tf = T.TMarketFace(led, _FaultGate(), DISCLAIMER)
    ok_fault, code_fl = expect_tm_error(
        lambda: fault_tf.publish_template(
            "usr:alice", "fault-t", "t", "d", PAYLOAD, 9, False),
        T.E_TM_GATE_ERROR)
    ok2 = (ok_t and code_t == T.E_TM_CONTENT_REJECTED
           and ok_d and code_d == T.E_TM_CONTENT_REJECTED
           and n_g1 == n_g0 + 1 and ok_no_gate
           and code_ng == T.E_TM_NO_GATE and ok_fault
           and code_fl == T.E_TM_GATE_ERROR)
    record("AC-TM2", ok2, "title with a forbidden word rejected %s zero"
          " rows; description with an advisory word rejected %s zero"
          " rows; exactly 1 of 3 submits stored (%d->%d); unwired"
          " gate refuses construction %s; gate runtime fault mapped %s"
          " (never a silent pass)"
          % (code_t, code_d, n_g0, n_g1, code_ng, code_fl))

    # -- AC-TM3 purchase idempotency + self-buy gate ------------------------
    b_bob0, b_alice0 = bal("bob"), bal("alice")
    p1 = tf.purchase("usr:bob", t1["template_id"], "order:tm3a")
    b_bob1 = bal("bob")
    ok_pdup, code_pd = expect_tm_error(
        lambda: tf.purchase("usr:bob", t1["template_id"], "order:tm3b"),
        T.E_TM_PURCHASE_DUP)
    b_bob2 = bal("bob")
    b_alice_pre = bal("alice")
    ok_self, code_sb = expect_tm_error(
        lambda: tf.purchase("usr:alice", t1["template_id"],
                            "order:tm3c"),
        T.E_TM_SELF_BUY)
    b_alice_post = bal("alice")
    ok_unknown, code_uk = expect_tm_error(
        lambda: tf.purchase("usr:bob", 999, "order:tm3d"),
        T.E_TM_UNKNOWN_TEMPLATE)
    p2 = tf.purchase("usr:carol", t1["template_id"], "order:tm3e")
    tx_head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                           (p1["spend_tx"],)).fetchone()
    tx_leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:bob'", (p1["spend_tx"],)).fetchone()
    n_pur = _count(conn, "tmarket_purchases")
    ok3 = (b_bob1 == b_bob0 - 10 and ok_pdup
           and code_pd == T.E_TM_PURCHASE_DUP and b_bob2 == b_bob1
           and ok_self and code_sb == T.E_TM_SELF_BUY
           and b_alice_post == b_alice_pre
           and ok_unknown and code_uk == T.E_TM_UNKNOWN_TEMPLATE
           and p1["spend_tx"] != p2["spend_tx"] and n_pur == 2
           and tx_head is not None and tx_head[0] == "spend"
           and tx_leg is not None and tx_leg[0] == "debit")
    record("AC-TM3", ok3, "bob's first buy charged once (%d->%d);"
          " repurchase rejected %s BEFORE the spend (%d==%d);"
          " self-purchase rejected %s zero movement (%d==%d); unknown"
          " template rejected %s; carol's buy = distinct legal tx;"
          " 2 purchase rows, each bound to a real spend tx"
          " (type=spend, debit leg)"
          % (b_bob0, b_bob1, code_pd, b_bob1, b_bob2, code_sb,
             b_alice_pre, b_alice_post, code_uk))

    # -- AC-TM4 split integer law -------------------------------------------
    s10 = T.split_amount(10)
    s3 = T.split_amount(3)
    s7 = T.split_amount(7)
    zero_loss = all(sum(T.split_amount(p)) == p for p in range(1, 51))
    det = all(T.split_amount(p) == T.split_amount(p) for p in range(1, 21))
    p3 = tf.purchase("usr:bob", t2["template_id"], "order:tm4a")  # price 3
    p4 = tf.purchase("usr:carol", t3["template_id"], "order:tm4b")  # price 7
    share_credit = conn.execute(
        "SELECT e.amount FROM ledger_entries e JOIN ledger_tx t ON"
        " t.tx_id = e.tx_id WHERE e.tx_id = ? AND e.direction ="
        " 'credit' AND e.account_id = 'usr:alice'",
        (p1["creator_share_tx"],)).fetchone()
    share_type = conn.execute(
        "SELECT type FROM ledger_tx WHERE tx_id = ?",
        (p1["creator_share_tx"],)).fetchone()
    check_rejected = False
    try:
        conn.execute(
            "INSERT INTO tmarket_purchases (template_id, buyer_id,"
            " price_paid, creator_share, platform_share, spend_tx,"
            " creator_share_tx, purchased_utc) VALUES"
            " (1,'usr:dave',10,6,3,'x','x','t')")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        check_rejected = True
    ok_split_params, code_sp = expect_tm_error(
        lambda: T.TMarketFace(led, gate, DISCLAIMER,
                              {"creator_weight": 0,
                               "platform_weight": 30}),
        T.E_TM_BAD_SPLIT)
    b_alice4 = bal("alice")
    ok4 = (s10 == (7, 3) and s3 == (3, 0) and s7 == (5, 2)
           and zero_loss and det
           and p1["creator_share"] == 7 and p1["platform_share"] == 3
           and p3["creator_share"] == 3 and p3["platform_share"] == 0
           and p4["creator_share"] == 5 and p4["platform_share"] == 2
           and share_credit is not None and int(share_credit[0]) == 7
           and share_type is not None and share_type[0] == "share"
           and b_alice4 == b_alice0 + 7 + 7 + 3
           and check_rejected and ok_split_params
           and code_sp == T.E_TM_BAD_SPLIT)
    record("AC-TM4", ok4, "integer law 70/30: price 10->%s, 3->%s,"
          " 7->%s; zero-loss holds for prices 1..50 (%s);"
          " deterministic double-run (%s); each purchase carries"
          " exactly one creator share tx (type=share, credit 7 to"
          " alice); creator balance %d->%d (+7+7+3); CHECK"
          " creator_share+platform_share=price_paid refuses a"
          " 6+3!=10 row (%s); bad split weights refused %s"
          % (s10, s3, s7, zero_loss, det, b_alice0, b_alice4,
             check_rejected, code_sp))

    # -- AC-TM5 rating gate ---------------------------------------------------
    b_c0, b_d0 = bal("carol"), bal("dave")
    n_r0 = _count(conn, "tmarket_ratings")
    r1 = tf.rate("usr:bob", t1["template_id"], 5)
    ok_rdup, code_rd = expect_tm_error(
        lambda: tf.rate("usr:bob", t1["template_id"], 4),
        T.E_TM_RATE_DUP)
    ok_notb, code_nb = expect_tm_error(
        lambda: tf.rate("usr:dave", t1["template_id"], 5),
        T.E_TM_NOT_BUYER)
    ok_unk, code_ru = expect_tm_error(
        lambda: tf.rate("usr:bob", 999, 5), T.E_TM_UNKNOWN_TEMPLATE)
    star_bad = []
    raised_stars = True
    for label, val in (("stars 0", 0), ("stars 6", 6), ("bool stars",
                                                        True)):
        ok_st, got = expect_tm_error(
            lambda v=val: tf.rate("usr:carol", t1["template_id"], v),
            T.E_TM_BAD_STARS)
        if ok_st:
            star_bad.append("%s=%s" % (label, got))
        else:
            star_bad.append("%s NOT-RAISED(%s)" % (label, got))
            raised_stars = False
    r2 = tf.rate("usr:carol", t1["template_id"], 1)
    n_r1 = _count(conn, "tmarket_ratings")
    rv = tf.rating_view(t1["template_id"])
    tv = tf.template_view(t1["template_id"])
    ok5 = (r1["stars"] == 5 and ok_rdup and code_rd == T.E_TM_RATE_DUP
           and ok_notb and code_nb == T.E_TM_NOT_BUYER
           and ok_unk and code_ru == T.E_TM_UNKNOWN_TEMPLATE
           and raised_stars and n_r1 == n_r0 + 2 and r2["stars"] == 1
           and rv["rating_count"] == 2 and rv["rating_avg"] == 3.0
           and [r["stars"] for r in rv["ratings"]] == [5, 1]
           and tv["rating_count"] == 2 and tv["rating_avg"] == 3.0
           and bal("carol") == b_c0 and bal("dave") == b_d0
           and sorted(rv.keys()) == ["disclaimer", "rating_avg",
                                     "rating_count", "ratings",
                                     "template_id"])
    record("AC-TM5", ok5, "purchaser bob rated 5 stars; repeat rating"
          " rejected %s (append-only, rows %d); non-buyer dave"
          " rejected %s; unknown template rejected %s; bad stars all"
          " rejected (%s); carol rated 1 star; deterministic"
          " aggregate avg=3.0 count=2 in both rating_view and"
          " template_view; pure reads move zero tokens (%d==%d,"
          " %d==%d)"
          % (code_rd, n_r1 - n_r0, code_nb, code_ru,
             "; ".join(star_bad), b_c0, bal("carol"), b_d0,
             bal("dave")))

    # -- AC-TM6 AIGC label + resident disclaimer ----------------------------
    ok_no_dis, code_nd = expect_tm_error(
        lambda: T.TMarketFace(led, gate, "  "), T.E_TM_NO_DISCLAIMER)
    mv = tf.market_view()
    sv = tf.sales_view("usr:alice")
    tv6 = tf.template_view(t2["template_id"])
    pub6 = tf.publish_template("usr:dave", "dave-tpl", "Dave Layout",
                               "clean", PAYLOAD, 4, True)
    label_rejected = False
    try:
        conn.execute(
            "INSERT INTO tmarket_templates (creator_id, template_key,"
            " title, description, payload_json, token_price, ai_label,"
            " listed_utc) VALUES ('usr:dave','x','t','d','{}',9,2,'t')")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        label_rejected = True
    all_labeled = all("ai_label" in row for row in mv["templates"])
    ok6 = (ok_no_dis and code_nd == T.E_TM_NO_DISCLAIMER
           and tv6["ai_label"] == 1 and tv6["disclaimer"] == DISCLAIMER
           and mv["disclaimer"] == DISCLAIMER and all_labeled
           and sv["disclaimer"] == DISCLAIMER
           and rv["disclaimer"] == DISCLAIMER
           and pub6["ai_label"] == 1 and label_rejected
           and all(row["ai_label"] in (0, 1)
                   for row in mv["templates"]))
    record("AC-TM6", ok6, "empty disclaimer refuses construction %s;"
          " every listing surface carries ai_label (template_view"
          " ai_label=%d, market_view rows %s, publish return %d);"
          " direct SQL ai_label=2 refused by the CHECK (%s); all four"
          " view envelopes (template/market/rating/sales) carry the"
          " resident disclaimer" % (code_nd, tv6["ai_label"],
                                     all_labeled, pub6["ai_label"],
                                     label_rejected))

    # -- AC-TM7 hard law: bad args, hygiene, byte-stable config -------------
    b7 = {who: bal(who) for who in
          ("alice", "bob", "carol", "dave")}
    counts0 = (_count(conn, "tmarket_templates"),
               _count(conn, "tmarket_purchases"),
               _count(conn, "tmarket_ratings"))
    bad7 = []
    raised7 = True
    for label, fn, code in (
            ("bad buyer", lambda: tf.purchase(
                "pool:reserve", t1["template_id"], "order:tm7a"),
             T.E_TM_BAD_ACCOUNT),
            ("empty ref", lambda: tf.purchase(
                "usr:dave", t1["template_id"], "  "),
             T.E_TM_BAD_ARGS),
            ("bool template id", lambda: tf.purchase(
                "usr:dave", True, "order:tm7b"),
             T.E_TM_BAD_ARGS),
            ("str template id", lambda: tf.purchase(
                "usr:dave", "x", "order:tm7c"),
             T.E_TM_BAD_ARGS),
            ("bad rater", lambda: tf.rate(
                "svc:x", t1["template_id"], 5),
             T.E_TM_BAD_ACCOUNT),
            ("rate unknown bool id", lambda: tf.rate(
                "usr:dave", False, 5),
             T.E_TM_BAD_ARGS)):
        ok_one, got = expect_tm_error(fn, code)
        if ok_one:
            bad7.append("%s=%s" % (label, got))
        else:
            bad7.append("%s NOT-RAISED(%s)" % (label, got))
            raised7 = False
    counts1 = (_count(conn, "tmarket_templates"),
               _count(conn, "tmarket_purchases"),
               _count(conn, "tmarket_ratings"))
    with open(os.path.join(BASE, "tmarket.py"), encoding="utf-8") as h:
        src = h.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    net_imports = [ln for ln in src.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    bal7 = {who: bal(who) for who in
            ("alice", "bob", "carol", "dave")}
    ok7 = (raised7 and counts0 == counts1 and b7 == bal7
           and non_ascii == 0 and not net_imports
           and "UPDATE tmarket_" not in src
           and "random" not in src and cfg_after == cfg_bytes)
    record("AC-TM7", ok7, "all %d bad args rejected (%s); zero side"
          " effects (rows %s unchanged, balances %s unchanged);"
          " module pure ASCII (%d non-ascii); zero network imports"
          " (%d); zero UPDATE surface; zero RNG (no random in"
          " source); config.json byte-stable"
          % (len(bad7), "; ".join(bad7), counts0,
             [b7[k] for k in ("alice", "bob", "carol", "dave")],
             non_ascii, len(net_imports)))

    conn.close()
    fault_tf.close()
    tf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
