"""Acceptance suite for the resident AI companion subscription
face (BigDomain R1689; canon = explore-queue emotional-stickiness
line: AI companion dialogue / memory archive / subscription tier;
seed = C-20261009-02). Asserts the pre-registered criteria
AC-CP1..AC-CP7 from the R1689 explore-queue row (criteria were
registered before this code existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero on any
FAIL.

The content gate is the lobby SecGate product injected by
reference (no copy): its Chinese wordlists are data loaded from
the lobby config at runtime - this test source stays pure ASCII
per the encoding discipline.

Usage: python test_companion.py
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
import companion as C                # noqa: E402 (R1689 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, reference)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: companion chat is"
              " entertainment only, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_cp_error(fn, *codes):
    try:
        fn()
    except C.CompanionError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


class _FaultGate(object):
    """Runtime-fault gate stub: check_text always blows up (the
    face must map this to E_CP_GATE_ERROR and never silently
    pass - AC-CP3 fail-closed posture)."""

    def check_text(self, text):
        raise RuntimeError("stub gate offline")


def _msg_rows(conn, account_id):
    return conn.execute(
        "SELECT COUNT(*) FROM companion_msgs WHERE account_id = ?",
        (account_id,)).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="companion-ac-")
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
    cf = C.CompanionFace(led, gate, DISCLAIMER)

    led.mint_to_pool("pool:reserve", 1000, "SETTLE-CP-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    for who, amount, tag in (("alice", 300, "a"), ("bob", 500, "b"),
                             ("carol", 200, "c")):
        led.adjust([("pool:reserve", "debit", amount),
                    ("usr:" + who, "credit", amount)],
                   "manual:fund-" + tag, "suite funding " + who)
    bal = lambda who: led.balance(who)["balance"]  # noqa: E731
    conn = sqlite3.connect(db_path)

    # -- AC-CP1 subscription tier: one spend per (account, month) ------
    b_bob0 = bal("usr:bob")
    p1 = cf.buy_pass("usr:bob", "2099-01", 199, "order:cp1a")
    b_bob1 = bal("usr:bob")
    ok_pdup, code_pd = expect_cp_error(
        lambda: cf.buy_pass("usr:bob", "2099-01", 199, "order:cp1b"),
        C.E_CP_PASS_DUP)
    b_bob2 = bal("usr:bob")
    p2 = cf.buy_pass("usr:bob", "2099-02", 199, "order:cp1c")
    b_bob3 = bal("usr:bob")
    tx_head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                           (p1["spend_tx"],)).fetchone()
    tx_leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = 'usr:bob'", (p1["spend_tx"],)).fetchone()
    subs = cf.subs_view("usr:bob")["subs"]
    ok1 = (b_bob1 == b_bob0 - 199 and ok_pdup
           and code_pd == C.E_CP_PASS_DUP and b_bob2 == b_bob1
           and b_bob3 == b_bob2 - 199
           and p1["spend_tx"] != p2["spend_tx"] and len(subs) == 2
           and tx_head is not None and tx_head[0] == "spend"
           and tx_leg is not None and tx_leg[0] == "debit"
           and subs[0]["spend_tx"] == p1["spend_tx"])
    record("AC-CP1", ok1, "pass 2099-01 charged once (%d->%d); same-month"
          " repurchase rejected %s before the spend (%d==%d); another"
          " month 2099-02 is a separate spend (%d); distinct txs %s/%s;"
          " sub rows bind real spend txs (type=spend, debit leg)"
          % (b_bob0, b_bob1, code_pd, b_bob1, b_bob2, b_bob3,
             p1["spend_tx"][:8], p2["spend_tx"][:8]))

    # -- AC-CP2 no subscription: fail-closed dialogue gate --------------
    b_carol0 = bal("usr:carol")
    n_msgs0 = _msg_rows(conn, "usr:carol")
    ok_denied, code_dn = expect_cp_error(
        lambda: cf.converse("usr:carol", "2099-01", "hello companion"),
        C.E_CP_DENIED)
    ok2 = (ok_denied and code_dn == C.E_CP_DENIED
           and bal("usr:carol") == b_carol0
           and _msg_rows(conn, "usr:carol") == n_msgs0
           and cf.can_converse("usr:carol", "2099-01")
           == {"allowed": False, "tx": None})
    record("AC-CP2", ok2, "carol without a pass rejected %s with zero"
          " charge (%d==%d) and zero rows stored (%d==%d);"
          " can_converse reports allowed=False"
          % (code_dn, b_carol0, bal("usr:carol"), n_msgs0,
             _msg_rows(conn, "usr:carol")))

    # -- AC-CP3 msgSecCheck pre-gate: fail-closed end to end ------------
    cf.buy_pass("usr:alice", "2099-01", 199, "order:cp3a")
    b_al0 = bal("usr:alice")
    n_al0 = _msg_rows(conn, "usr:alice")
    ok_forb, code_fb = expect_cp_error(
        lambda: cf.converse("usr:alice", "2099-01",
                            "clean prefix " + bad_word + " suffix"),
        C.E_CP_CONTENT_REJECTED)
    ok_adv, code_ad = expect_cp_error(
        lambda: cf.converse("usr:alice", "2099-01",
                            "clean prefix " + advisory_word + " suffix"),
        C.E_CP_CONTENT_REJECTED)
    m1 = cf.converse("usr:alice", "2099-01", "tell me about the harbor")
    ok_reply_gate, code_rg = expect_cp_error(
        lambda: cf.record_reply(m1["msg_id"],
                                "reply with " + bad_word + " inside"),
        C.E_CP_CONTENT_REJECTED)
    ok_no_gate, code_ng = expect_cp_error(
        lambda: C.CompanionFace(led, None, DISCLAIMER), C.E_CP_NO_GATE)
    fault_cf = C.CompanionFace(led, _FaultGate(), DISCLAIMER)
    ok_fault, code_fl = expect_cp_error(
        lambda: fault_cf.converse("usr:alice", "2099-01", "clean text"),
        C.E_CP_GATE_ERROR)
    n_al1 = _msg_rows(conn, "usr:alice")
    ok3 = (ok_forb and code_fb == C.E_CP_CONTENT_REJECTED
           and ok_adv and code_ad == C.E_CP_CONTENT_REJECTED
           and ok_reply_gate and code_rg == C.E_CP_CONTENT_REJECTED
           and ok_no_gate and code_ng == C.E_CP_NO_GATE
           and ok_fault and code_fl == C.E_CP_GATE_ERROR
           and bal("usr:alice") == b_al0 and n_al1 == n_al0 + 1)
    record("AC-CP3", ok3, "resident text with a forbidden word rejected"
          " %s zero rows; advisory word rejected %s; AI reply with a"
          " forbidden word rejected %s zero rows; unwired gate refuses"
          " construction %s; gate runtime fault mapped %s (never a"
          " silent pass); exactly 1 of 4 submitted texts stored"
          % (code_fb, code_ad, code_rg, code_ng, code_fl))

    # -- AC-CP4 AIGC label is structural --------------------------------
    r1 = cf.record_reply(m1["msg_id"], "the harbor lights are calm")
    rows = conn.execute(
        "SELECT role, ai_label FROM companion_msgs"
        " WHERE account_id = 'usr:alice' ORDER BY msg_id").fetchall()
    all_lab = (all(r[1] == 1 for r in rows if r[0] == 'companion')
               and all(r[1] == 0 for r in rows if r[0] == 'resident'))
    check_rejected = False
    try:
        conn.execute(
            "INSERT INTO companion_msgs (account_id, pass_month, role,"
            " text_content, ai_label, created_utc) VALUES"
            " ('usr:alice','2099-01','companion','x',0,'t')")
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        check_rejected = True
    with open(os.path.join(BASE, "companion.py"), encoding="utf-8") as h:
        src = h.read()
    def_line = [ln for ln in src.splitlines()
                if ln.strip().startswith("def record_reply")][0]
    ok4 = (m1["ai_label"] == 0 and r1["ai_label"] == 1 and all_lab
           and check_rejected and "ai_label" not in def_line
           and r1["anchor_msg_id"] == m1["msg_id"])
    record("AC-CP4", ok4, "resident msg ai_label=0, companion reply"
          " ai_label=1 (return faces carry both); DB rows consistent"
          " by role (%d rows); direct SQL insert role=companion"
          " ai_label=0 refused by the CHECK constraint (%s); the"
          " record_reply write face has no label parameter (%s)"
          % (len(rows), check_rejected,
             def_line.strip()[:44]))

    # -- AC-CP5 memory archive: append-only, companion-anchored ---------
    mem1 = cf.archive_memory("usr:alice", "harbor_preference",
                             {"topic": "harbor", "tone": "calm"},
                             r1["msg_id"])
    mem2 = cf.archive_memory("usr:alice", "harbor_preference",
                             {"topic": "harbor", "tone": "calm"},
                             r1["msg_id"])
    ok_res_anchor, code_ra = expect_cp_error(
        lambda: cf.archive_memory("usr:alice", "bad", {"x": 1},
                                  m1["msg_id"]),
        C.E_CP_BAD_MEMORY)
    ok_cross, code_xa = expect_cp_error(
        lambda: cf.archive_memory("usr:bob", "bad", {"x": 1},
                                  r1["msg_id"]),
        C.E_CP_BAD_MEMORY)
    n_mem = conn.execute(
        "SELECT COUNT(*) FROM companion_memories").fetchone()[0]
    b_al2 = bal("usr:alice")
    view = cf.memory_view("usr:alice")["memories"]
    with open(os.path.join(BASE, "companion.py"), encoding="utf-8") as h:
        src = h.read()
    no_update = ("UPDATE companion_" not in src)
    ok5 = (mem1["ai_label"] == 1 and mem2["memory_id"] != mem1["memory_id"]
           and n_mem == 2 and ok_res_anchor
           and code_ra == C.E_CP_BAD_MEMORY and ok_cross
           and code_xa == C.E_CP_BAD_MEMORY and bal("usr:alice") == b_al2
           and len(view) == 2 and no_update
           and sorted(view[0].keys()) == ["ai_label", "content",
                                           "created_utc", "kind",
                                           "memory_id", "source_msg_id"]
           and view[0]["source_msg_id"] == r1["msg_id"])
    record("AC-CP5", ok5, "memory row stored ai_label=1 anchored to the"
          " companion reply; same-source re-archive allowed (append,"
          " ids %d/%d, rows=%d); resident-source anchor rejected %s;"
          " cross-account anchor rejected %s; zero UPDATE surface in"
          " module source (%s); memory_view is a pure read (balance"
          " %d==%d) with exact key set + provenance"
          % (mem1["memory_id"], mem2["memory_id"], n_mem, code_ra,
             code_xa, no_update, b_al2, bal("usr:alice")))

    # -- AC-CP6 resident non-advisory disclaimer ------------------------
    ok_no_dis, code_nd = expect_cp_error(
        lambda: C.CompanionFace(led, gate, "  "), C.E_CP_NO_DISCLAIMER)
    m2 = cf.converse("usr:alice", "2099-01", "one more line")
    r2 = cf.record_reply(m2["msg_id"], "a calm reply")
    tv = cf.transcript_view("usr:alice", "2099-01")
    mv = cf.memory_view("usr:alice")
    b_al3 = bal("usr:alice")
    cf.can_converse("usr:alice", "2099-01")
    cf.subs_view("usr:alice")
    ok6 = (ok_no_dis and code_nd == C.E_CP_NO_DISCLAIMER
           and m2["disclaimer"] == DISCLAIMER
           and r2["disclaimer"] == DISCLAIMER
           and tv["disclaimer"] == DISCLAIMER
           and mv["disclaimer"] == DISCLAIMER
           and bal("usr:alice") == b_al3
           and sorted(tv.keys()) == ["account_id", "disclaimer",
                                     "messages", "pass_month"]
           and len(tv["messages"]) == 4)
    record("AC-CP6", ok6, "empty disclaimer refuses construction %s;"
          " converse/record_reply returns and transcript/memory view"
          " envelopes all carry the resident disclaimer; pure reads"
          " move zero tokens (%d==%d); transcript envelope key set"
          " exact {account_id, pass_month, disclaimer, messages}"
          " with %d dialogue rows"
          % (code_nd, b_al3, bal("usr:alice"), len(tv["messages"])))

    # -- AC-CP7 hard law: bad args, hygiene, byte-stable config --------
    b7a, b7b, b7c = (bal("usr:alice"), bal("usr:bob"), bal("usr:carol"))
    counts0 = (conn.execute(
        "SELECT COUNT(*) FROM companion_subs").fetchone()[0],
        conn.execute(
            "SELECT COUNT(*) FROM companion_msgs").fetchone()[0],
        conn.execute(
            "SELECT COUNT(*) FROM companion_memories").fetchone()[0])
    bad = []
    raised_all = True
    for label, fn, code in (
            ("bad buyer", lambda: cf.buy_pass("svc:x", "2099-03", 99,
                                              "order:cp7a"),
             C.E_CP_BAD_ACCOUNT),
            ("zero price", lambda: cf.buy_pass("usr:carol", "2099-03", 0,
                                               "order:cp7b"),
             C.E_CP_BAD_PRICE),
            ("bool price", lambda: cf.buy_pass("usr:carol", "2099-03",
                                               True, "order:cp7c"),
             C.E_CP_BAD_PRICE),
            ("empty ref", lambda: cf.buy_pass("usr:carol", "2099-03", 99,
                                              "  "),
             C.E_CP_BAD_ARGS),
            ("bad month fmt", lambda: cf.buy_pass("usr:carol", "209903",
                                                 199, "order:cp7d"),
             C.E_CP_BAD_MONTH),
            ("month 13", lambda: cf.buy_pass("usr:carol", "2099-13", 199,
                                             "order:cp7e"),
             C.E_CP_BAD_MONTH),
            ("empty text", lambda: cf.converse("usr:alice", "2099-01",
                                               "  "),
             C.E_CP_BAD_ARGS),
            ("bad reply id", lambda: cf.record_reply(0, "x"),
             C.E_CP_BAD_MSG),
            ("non-int reply id", lambda: cf.record_reply("x", "y"),
             C.E_CP_BAD_MSG),
            ("empty memory kind", lambda: cf.archive_memory(
                "usr:alice", " ", {"x": 1}, r1["msg_id"]),
             C.E_CP_BAD_ARGS),
            ("empty memory content", lambda: cf.archive_memory(
                "usr:alice", "k", {}, r1["msg_id"]),
             C.E_CP_BAD_ARGS)):
        ok_one, got = expect_cp_error(fn, code)
        if ok_one:
            bad.append("%s=%s" % (label, got))
        else:
            bad.append("%s NOT-RAISED(%s)" % (label, got))
            raised_all = False
    counts1 = (conn.execute(
        "SELECT COUNT(*) FROM companion_subs").fetchone()[0],
        conn.execute(
        "SELECT COUNT(*) FROM companion_msgs").fetchone()[0],
        conn.execute(
        "SELECT COUNT(*) FROM companion_memories").fetchone()[0])
    with open(os.path.join(BASE, "companion.py"), encoding="utf-8") as h:
        src = h.read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    net_imports = [ln for ln in src.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    with open(os.path.join(BASE, "config.json"), "rb") as h:
        cfg_after = h.read()
    ok7 = (b7a == bal("usr:alice") and b7b == bal("usr:bob")
           and b7c == bal("usr:carol") and counts0 == counts1
           and raised_all and non_ascii == 0 and not net_imports
           and "UPDATE companion_" not in src and cfg_after == cfg_bytes)
    record("AC-CP7", ok7, "all %d bad args rejected (%s); zero side"
          " effects (balances %d/%d/%d unchanged, sub/msg/memory rows"
          " %s unchanged); module pure ASCII (%d non-ascii); zero"
          " network imports (%d); zero UPDATE surface; config.json"
          " byte-stable"
          % (len(bad), "; ".join(bad), b7a, b7b, b7c, counts0,
             non_ascii, len(net_imports)))

    conn.close()
    fault_cf.close()
    cf.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
