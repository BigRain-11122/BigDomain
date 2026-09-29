"""Acceptance suite for the slow-live room conversion-piece supply
face (BigDomain explore queue item, round R608). Asserts the
pre-registered criteria AC-LR1..AC-LR7 from the R608 backlog row
(criteria were registered before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Test data discipline: the banned words, the disclaimer text and
the ai label all arrive from the ledger sandbox config (data not
code literals); clean bodies stay plain ASCII.

Usage: python test_liveroom.py
"""

import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER_DIR = os.path.abspath(os.path.join(BASE, "..", "ledger"))
LOBBY_DIR = os.path.abspath(os.path.join(BASE, "..", "lobby"))
for _d in (BASE, LEDGER_DIR, LOBBY_DIR):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L          # noqa: E402  (P-47-2b core)
import sec_gate as SG       # noqa: E402  (lobby gate, reuse family law)
import liveroom as LR       # noqa: E402  (R608 conversion-piece face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_live_error(fn, *codes):
    try:
        fn()
    except LR.LiveRoomError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def spend_count(db_path):
    conn = sqlite3.connect(db_path)
    n = conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'").fetchone()[0]
    conn.close()
    return n


def main():
    tmp = tempfile.mkdtemp(prefix="liveroom-ac-")
    with open(os.path.join(LEDGER_DIR, "config.json"),
              encoding="utf-8") as handle:
        cfg = json.load(handle)
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    gate = SG.SecGate(cfg["gate"]["forbidden_words"],
                      cfg["gate"]["advisory_ban_words"])
    disc = cfg["token"]["disclaimer"]
    ai_label = cfg["token"]["ai_label_text"]
    lf = LR.LiveRoomFace(led, gate, disc, ai_label)

    led.mint_to_pool("pool:reserve", 100000, "SETTLE-LR", "settlement")
    led.ensure_account("usr:amy", census_avatar_id="amy")
    led.ensure_account("usr:ben", census_avatar_id="ben")
    led.ensure_account("usr:cyd", census_avatar_id="cyd")
    led.adjust([("pool:reserve", "debit", 3000), ("usr:amy", "credit", 3000)],
               "manual:fund-amy", "suite funding amy")
    led.adjust([("pool:reserve", "debit", 2000), ("usr:ben", "credit", 2000)],
               "manual:fund-ben", "suite funding ben")
    led.adjust([("pool:reserve", "debit", 1000), ("usr:cyd", "credit", 1000)],
               "manual:fund-cyd", "suite funding cyd")

    bad_word = cfg["gate"]["forbidden_words"][0]
    advisory_word = cfg["gate"]["advisory_ban_words"][0]

    # -- AC-LR1 unattended form is platform-banned, fail-closed ---------
    ok_unatt, code_unatt = expect_live_error(
        lambda: lf.open_session("s-ghost", "room-x", False,
                                "bigcompute-risk-control"),
        LR.E_LIVE_UNATTENDED)
    ok_ref, code_ref = expect_live_error(
        lambda: lf.open_session("s-noref", "room-x", True, "  "),
        LR.E_LIVE_BAD_ARGS)
    conn = sqlite3.connect(db_path)
    sess_rows = conn.execute(
        "SELECT COUNT(*) FROM live_sessions").fetchone()[0]
    conn.close()
    ok1 = ok_unatt and ok_ref and sess_rows == 0
    record("AC-LR1", ok1, "unattended open rejected %s; attended"
          " with empty risk-control ref rejected %s; sessions table"
          " rows=%d after both rejects" % (code_unatt, code_ref, sess_rows))

    s = lf.open_session("s-main", "room-bund", True,
                         "bigcompute-risk-control-ref")
    ok_open = (s["attended"] is True
               and s["risk_control_ref"] == "bigcompute-risk-control-ref")
    record("AC-LR1", ok_open, "attended session opens only with a"
          " non-empty risk-control citation (%s)"
          % s["risk_control_ref"])

    # -- AC-LR2 anonymous cohort is free, zero token touch --------------
    tx0 = spend_count(db_path)
    for i in range(5):
        lf.viewer_enter("s-main", "anon-%d" % i)
    f2 = lf.funnel("s-main")
    tx1 = spend_count(db_path)
    ok2 = (f2["entered"] == 5 and f2["registered"] == 0
           and f2["converted"] == 0 and tx1 == tx0)
    record("AC-LR2", ok2, "5 anonymous enters: funnel entered=%d"
          " registered=%d converted=%d; spend-tx count %d==%d"
          % (f2["entered"], f2["registered"], f2["converted"], tx0, tx1))

    # -- AC-LR3 danmaku front gate rejects BEFORE any row lands ----------
    lf.viewer_register("s-main", "anon-0", "amy")
    dm0 = sqlite3.connect(db_path).execute(
        "SELECT COUNT(*) FROM live_danmaku").fetchone()[0]
    ok_g1, _ = (False, "")
    try:
        lf.post_danmaku("s-main", "anon-0", "clean hello " + bad_word)
    except SG.ContentRejectedError as exc:
        ok_g1 = (exc.gate == 1 and exc.word == bad_word)
    ok_g2 = False
    try:
        lf.post_danmaku("s-main", "anon-0",
                        "clean hello " + advisory_word)
    except SG.ContentRejectedError as exc:
        ok_g2 = (exc.gate == 2 and exc.word == advisory_word)
    dm1 = sqlite3.connect(db_path).execute(
        "SELECT COUNT(*) FROM live_danmaku").fetchone()[0]
    ok_res, code_res = expect_live_error(
        lambda: lf.post_danmaku("s-main", "anon-1", "clean hello"),
        LR.E_LIVE_NOT_RESIDENT)
    dm2 = sqlite3.connect(db_path).execute(
        "SELECT COUNT(*) FROM live_danmaku").fetchone()[0]
    clean = lf.post_danmaku("s-main", "anon-0", "clean hello city",
                            ai_generated=True)
    dm3 = sqlite3.connect(db_path).execute(
        "SELECT COUNT(*) FROM live_danmaku").fetchone()[0]
    ok3 = (ok_g1 and ok_g2 and dm1 == dm0 and ok_res and dm2 == dm0
           and dm3 == dm0 + 1 and clean["ai_generated"] is True)
    record("AC-LR3", ok3, "banned word (%s) rejected at gate 1 and"
          " advisory word (%s) rejected at gate 2 before any row"
          " (rows %d==%d); anonymous danmaku rejected %s (rows %d);"
          " clean AI-flagged danmaku lands (rows %d)"
          % (bad_word, advisory_word, dm1, dm0, code_res, dm2, dm3))

    # -- AC-LR4 conversion is exactly one spend ---------------------------
    bal_a0 = led.balance("usr:amy")["balance"]
    tx2 = spend_count(db_path)
    c1 = lf.cart_convert("s-main", "anon-0", 1990, "order:cart-amy")
    bal_a1 = led.balance("usr:amy")["balance"]
    tx3 = spend_count(db_path)
    conn = sqlite3.connect(db_path)
    head = conn.execute(
        "SELECT type FROM ledger_tx WHERE tx_id = ?",
        (c1["spend_tx_id"],)).fetchone()
    leg = conn.execute(
        "SELECT direction, amount FROM ledger_entries"
        " WHERE tx_id = ? AND account_id = ?",
        (c1["spend_tx_id"], "usr:amy")).fetchone()
    conn.close()
    ok_conv = (c1["account_id"] == "usr:amy" and c1["price"] == 1990
               and bal_a1 == bal_a0 - 1990 and tx3 == tx2 + 1
               and head is not None and head[0] == "spend"
               and leg is not None and leg[0] == "debit"
               and leg[1] == 1990)
    record("AC-LR4", ok_conv, "registered viewer converts price 1990:"
          " balance %d->%d (exact -1990), spend-tx %d->%d (+1), bound"
          " tx is a real spend with a 1990 debit for usr:amy"
          % (bal_a0, bal_a1, tx2, tx3))

    lf.viewer_enter("s-main", "anon-2")
    lf.viewer_register("s-main", "anon-2", "ben")
    bal_b0 = led.balance("usr:ben")["balance"]
    ok_res2, code_res2 = expect_live_error(
        lambda: lf.cart_convert("s-main", "anon-1", 1990, "order:cart-anon"),
        LR.E_LIVE_NOT_RESIDENT)
    bal_b1 = led.balance("usr:ben")["balance"]
    ok4 = ok_res2 and bal_b1 == bal_b0
    record("AC-LR4", ok4 and True, "unregistered (anonymous) viewer"
          " convert rejected %s with zero charge (%d==%d)"
          % (code_res2, bal_b0, bal_b1))

    # -- AC-LR5 idempotence and closed-session refuses -------------------
    lf.viewer_enter("s-main", "anon-3")
    lf.viewer_register("s-main", "anon-3", "cyd")
    bal_c0 = led.balance("usr:cyd")["balance"]
    c2 = lf.cart_convert("s-main", "anon-3", 990, "order:cart-cyd")
    ok_dup, code_dup = expect_live_error(
        lambda: lf.cart_convert("s-main", "anon-3", 990, "order:cart-cyd2"),
        LR.E_LIVE_CONV_DUP)
    bal_c1 = led.balance("usr:cyd")["balance"]
    lf.close_session("s-main")
    ok_closed1, code_closed1 = expect_live_error(
        lambda: lf.cart_convert("s-main", "anon-3", 990, "order:late"),
        LR.E_LIVE_CLOSED)
    ok_closed2, code_closed2 = expect_live_error(
        lambda: lf.post_danmaku("s-main", "anon-0", "after close"),
        LR.E_LIVE_CLOSED)
    ok5 = (c2["price"] == 990 and ok_dup and bal_c1 == bal_c0 - 990
           and ok_closed1 and ok_closed2)
    record("AC-LR5", ok5, "second conversion same viewer same session"
          " rejected %s zero charge (%d==%d-990); after close_session:"
          " convert rejected %s, danmaku rejected %s"
          % (code_dup, bal_c1, bal_c0, code_closed1, code_closed2))

    # -- AC-LR6 funnel transcript compliance spine ------------------------
    s2 = lf.open_session("s-stat", "room-stat", True, "bigcompute-risk-2")
    for vid in ("v1", "v2", "v3", "v4"):
        lf.viewer_enter("s-stat", vid)
    lf.viewer_register("s-stat", "v1", "amy")
    lf.viewer_register("s-stat", "v2", "ben")
    lf.post_danmaku("s-stat", "v1", "hello from amy", ai_generated=True)
    lf.post_danmaku("s-stat", "v2", "hello from ben")
    lf.cart_convert("s-stat", "v1", 500, "order:stat-amy")
    lf.cart_convert("s-stat", "v2", 300, "order:stat-ben")
    f6 = lf.funnel("s-stat")
    conn = sqlite3.connect(db_path)
    ent = conn.execute(
        "SELECT COUNT(*) FROM live_cohort WHERE session_id = 's-stat'"
    ).fetchone()[0]
    reg = conn.execute(
        "SELECT COUNT(*) FROM live_cohort WHERE session_id = 's-stat'"
        " AND census_avatar_id IS NOT NULL").fetchone()[0]
    conv = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(price),0) FROM live_conversions"
        " WHERE session_id = 's-stat'").fetchone()
    conn.close()
    lines = lf.transcript("s-stat")
    ai_line = [ln for ln in lines if "hello from amy" in ln]
    ok6 = (f6["entered"] == 4 and f6["registered"] == 2
           and f6["converted"] == 2 and f6["conversion_total"] == 800
           and ent == 4 and reg == 2 and conv[0] == 2
           and int(conv[1]) == 800
           and lines[0] == disc and lines[-1] == disc
           and len(ai_line) == 1
           and ("[" + ai_label + "]") in ai_line[0])
    record("AC-LR6", ok6, "funnel counts match an independent SQL"
          " recount (entered=%d/%d registered=%d/%d converted=%d/%d"
          " total=%d/%d); transcript first+last lines are the config"
          " disclaimer verbatim; the AI danmaku row carries [%s]"
          % (f6["entered"], ent, f6["registered"], reg,
             f6["converted"], conv[0], f6["conversion_total"],
             int(conv[1]), ai_label))

    # bound spend debit sum equals the conversion total
    rows = lf.conversion_ledger("s-stat")
    conn = sqlite3.connect(db_path)
    debit_sum = 0
    ok_bind = len(rows) == 2
    for r in rows:
        leg = conn.execute(
            "SELECT direction, amount FROM ledger_entries"
            " WHERE tx_id = ? AND account_id = ?",
            (r["bound_spend_tx"], r["account_id"])).fetchone()
        ok_bind = ok_bind and leg is not None and leg[0] == "debit"
        debit_sum += leg[1] if leg else 0
    conn.close()
    record("AC-LR6", ok_bind and debit_sum == 800, "conversion audit"
          " rows %d each bind a real debit entry; bound debit sum %d"
          "== conversion_total 800" % (len(rows), debit_sum))

    # -- AC-LR7 isolation and source law ----------------------------------
    tx_all = spend_count(db_path)
    conv_all = sqlite3.connect(db_path).execute(
        "SELECT COUNT(*) FROM live_conversions").fetchone()[0]
    ok_tokens = tx_all == conv_all + 0  # suite spent nothing else
    with open(os.path.join(BASE, "liveroom.py"), encoding="utf-8") as handle:
        src = handle.read()
    banned = ("sell", "refund", "exchange", "withdraw",
              "transfer", "mint")
    hits = [b for b in banned if b in src]
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    ok7 = ok_tokens and not hits and non_ascii == 0
    record("AC-LR7", ok7, "whole-suite token touches: spend-tx %d =="
          " conversion rows %d (enter/register/danmaku/close moved zero"
          " tokens); source banned-verb hits=%s non-ascii=%d; prices"
          " arrive as caller arguments only ([needs-CEO] P1 face)"
          % (tx_all, conv_all, hits, non_ascii))

    lf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
