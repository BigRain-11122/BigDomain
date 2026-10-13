"""Cross-restart persistence window for the resident AI companion
face (BigDomain R1941; the companion seat of the R1886 persist
family - the R1934-seeded row, criteria pre-registered in the
R1941 tech.md claim row before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close both pieces -> reopen the same db/config -> byte-identical
read replay -> restart-surviving gate probes (zero drift) ->
post-restart real-path continuation (the missing month pass +
two new dialogue rounds + two memory appends) -> frozen faces +
dup/denied/content gates across restart -> pure-read law ->
third instance stability. The read faces replay stored values
only (created_utc is a stored column, never a clock echo), so
full-dump byte-identity holds without clock freezing; evidence
digests mask the timestamp and tx fields so the suite stdout
stays deterministic across double runs.

The content gate is the lobby SecGate product injected by
reference (no copy); its wordlist is runtime data, so this test
source stays pure ASCII per the encoding discipline.

Usage: python test_companion_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402 (P-47-2b core)
import companion as C                 # noqa: E402 (R1689 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, reference)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: companion chat is"
              " entertainment only, not investment advice")

_MASKS = (
    (re.compile(r'"created_utc": "[^"]*"'), '"created_utc": "<ts>"'),
    (re.compile(r'"spend_tx": "[^"]*"'), '"spend_tx": "<tx>"'),
    (re.compile(r'"tx": "[^"]*"'), '"tx": "<tx>"'),
)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_cp_error(fn, *codes):
    try:
        fn()
    except C.CompanionError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    for pat, rep in _MASKS:
        text = pat.sub(rep, text)
    return text


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    for tbl in ("companion_subs", "companion_msgs",
                "companion_memories", "ledger_tx", "ledger_entries"):
        out[tbl] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def sql_rows(db_path, query):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(query).fetchall()
    conn.close()
    return rows


def preexisting_row_snapshot(db_path):
    return (
        sql_rows(db_path, "SELECT sub_id, account_id, pass_month,"
         " token_price, bound_spend_tx, granted_utc FROM"
         " companion_subs ORDER BY sub_id"),
        sql_rows(db_path, "SELECT msg_id, account_id, pass_month,"
         " role, text_content, ai_label, created_utc FROM"
         " companion_msgs ORDER BY msg_id"),
        sql_rows(db_path, "SELECT memory_id, account_id, kind,"
         " content_json, source_msg_id, ai_label, created_utc FROM"
         " companion_memories ORDER BY memory_id"),
    )


def spend_cross(db_path, tx_id, account_id):
    """SQL cross: the bound spend tx is a real ledger spend row
    with a debit leg on the purchasing account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT direction FROM ledger_entries WHERE tx_id = ?"
        " AND account_id = ? AND direction = 'debit'",
        (tx_id, account_id)).fetchone()
    conn.close()
    return (head[0] if head else None), (leg[0] if leg else None)


def read_battery(cf, led):
    return {
        "can_a_jan": dump(cf.can_converse("usr:alice", "2099-01")),
        "can_b_jan": dump(cf.can_converse("usr:bob", "2099-01")),
        "can_c_jan": dump(cf.can_converse("usr:carol", "2099-01")),
        "can_c_feb": dump(cf.can_converse("usr:carol", "2099-02")),
        "can_a_feb": dump(cf.can_converse("usr:alice", "2099-02")),
        "tr_a_jan": dump(cf.transcript_view("usr:alice", "2099-01")),
        "tr_b_jan": dump(cf.transcript_view("usr:bob", "2099-01")),
        "tr_c_jan": dump(cf.transcript_view("usr:carol", "2099-01")),
        "tr_c_feb": dump(cf.transcript_view("usr:carol", "2099-02")),
        "mem_a": dump(cf.memory_view("usr:alice")),
        "mem_b": dump(cf.memory_view("usr:bob")),
        "mem_c": dump(cf.memory_view("usr:carol")),
        "subs_a": dump(cf.subs_view("usr:alice")),
        "subs_b": dump(cf.subs_view("usr:bob")),
        "subs_c": dump(cf.subs_view("usr:carol")),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def battery_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


class _FaultGate(object):
    """Runtime-fault gate stub: check_text always blows up (the
    face must map this to E_CP_GATE_ERROR and never silently
    pass - fail-closed posture across restarts)."""

    def check_text(self, text):
        raise RuntimeError("stub gate offline")


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="companion-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    cmpmod_sha_before = sha16(io_read(os.path.join(BASE, "companion.py")))
    ledmod_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    gatemod_sha_before = sha16(io_read(os.path.join(LOBBY, "sec_gate.py")))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")
    lobby_cfg = json.loads(io_read(os.path.join(LOBBY, "config.json")))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]

    # ---- instance 1: anchor world on the real product path ----
    led = L.Ledger(db_path, cfg)
    gate = SecGate.from_config(lobby_cfg)
    cf = C.CompanionFace(led, gate, DISCLAIMER)
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-CMP-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.adjust([("pool:reserve", "debit", 300),
                ("usr:alice", "credit", 300)],
               "manual:cmp-fund-alice", "persist window funding alice")
    led.adjust([("pool:reserve", "debit", 500),
                ("usr:bob", "credit", 500)],
               "manual:cmp-fund-bob", "persist window funding bob")
    led.adjust([("pool:reserve", "debit", 200),
                ("usr:carol", "credit", 200)],
               "manual:cmp-fund-carol", "persist window funding carol")

    # pass spectrum: two jan holders + one feb holder, each
    # purchase bound to one real spend tx
    p_a1 = cf.buy_pass("usr:alice", "2099-01", 120, "order:cmp-a1")
    p_b1 = cf.buy_pass("usr:bob", "2099-01", 120, "order:cmp-b1")
    p_c1 = cf.buy_pass("usr:carol", "2099-02", 90, "order:cmp-c1")

    # dialogue spectrum: alice two archived rounds + bob one round
    # + carol one feb round = eight structural-label rows
    m_a1 = cf.converse("usr:alice", "2099-01",
                       "tell me about the harbor tonight")
    r_a1 = cf.record_reply(m_a1["msg_id"],
                           "the harbor lights are quiet tonight")
    e_a1 = cf.archive_memory("usr:alice", "preference",
                             {"topic": "harbor", "tone": "calm"},
                             r_a1["msg_id"])
    m_a2 = cf.converse("usr:alice", "2099-01",
                        "remember I like short replies")
    r_a2 = cf.record_reply(m_a2["msg_id"], "noted: short replies")
    e_a2 = cf.archive_memory("usr:alice", "preference",
                             {"topic": "reply-length", "tone": "short"},
                             r_a2["msg_id"])
    m_b1 = cf.converse("usr:bob", "2099-01",
                        "what is on the city calendar")
    r_b1 = cf.record_reply(m_b1["msg_id"],
                           "the lantern parade opens the weekend")
    m_c1 = cf.converse("usr:carol", "2099-02", "play the rain sound")
    r_c1 = cf.record_reply(m_c1["msg_id"], "soft rain over the plaza")

    # -- AC-CMP1 control anchor: world pinned + gate probes ------
    bal1 = read_battery(cf, led)
    cnt1 = table_counts(db_path)
    subs_pre, msgs_pre, mems_pre = preexisting_row_snapshot(db_path)
    ok_world = (
        p_a1["token_price"] == 120 and p_a1["pass_month"] == "2099-01"
        and p_b1["token_price"] == 120 and p_b1["pass_month"] == "2099-01"
        and p_c1["token_price"] == 90 and p_c1["pass_month"] == "2099-02"
        and bal1["bal_alice"] == 180 and bal1["bal_bob"] == 380
        and bal1["bal_carol"] == 110 and bal1["bal_pool"] == 19330
        and cnt1["companion_subs"] == 3 and cnt1["companion_msgs"] == 8
        and cnt1["companion_memories"] == 2
        and cnt1["spend_tx"] == 3 and len(subs_pre) == 3
        and len(msgs_pre) == 8 and len(mems_pre) == 2)
    ok_label = (
        [int(r[5]) for r in msgs_pre] == [0, 1, 0, 1, 0, 1, 0, 1]
        and [r[3] for r in msgs_pre] ==
        ["resident", "companion", "resident", "companion",
         "resident", "companion", "resident", "companion"])
    ok_pass_faces = (
        json.loads(bal1["can_a_jan"])["allowed"] is True
        and json.loads(bal1["can_b_jan"])["allowed"] is True
        and json.loads(bal1["can_c_jan"])["allowed"] is False
        and json.loads(bal1["can_c_feb"])["allowed"] is True
        and json.loads(bal1["can_a_feb"])["allowed"] is False)
    tr_a = json.loads(bal1["tr_a_jan"])["messages"]
    ok_tr = (
        len(tr_a) == 4
        and [m["role"] for m in tr_a] ==
        ["resident", "companion", "resident", "companion"]
        and tr_a[1]["text"] == "the harbor lights are quiet tonight"
        and [m["ai_label"] for m in tr_a] == [0, 1, 0, 1]
        and json.loads(bal1["tr_a_jan"])["disclaimer"] == DISCLAIMER
        and len(json.loads(bal1["tr_b_jan"])["messages"]) == 2
        and json.loads(bal1["tr_c_jan"])["messages"] == []
        and len(json.loads(bal1["tr_c_feb"])["messages"]) == 2)
    mem_a = json.loads(bal1["mem_a"])["memories"]
    ok_mem = (
        len(mem_a) == 2
        and [m["kind"] for m in mem_a] == ["preference", "preference"]
        and [m["source_msg_id"] for m in mem_a] ==
        [r_a1["msg_id"], r_a2["msg_id"]]
        and all(m["ai_label"] == 1 for m in mem_a)
        and json.loads(bal1["mem_b"])["memories"] == []
        and json.loads(bal1["mem_c"])["memories"] == [])
    ok_subs = (
        json.loads(bal1["subs_a"])["subs"][0]["pass_month"] == "2099-01"
        and json.loads(bal1["subs_a"])["subs"][0]["token_price"] == 120
        and len(json.loads(bal1["subs_b"])["subs"]) == 1
        and json.loads(bal1["subs_c"])["subs"][0]["pass_month"] == "2099-02"
        and json.loads(bal1["subs_c"])["subs"][0]["token_price"] == 90)

    probe_specs = (
        ("dup-pass", lambda: cf.buy_pass(
            "usr:bob", "2099-01", 120, "order:cmp-p1"), C.E_CP_PASS_DUP),
        ("denied", lambda: cf.converse(
            "usr:carol", "2099-01", "hello there"), C.E_CP_DENIED),
        ("content", lambda: cf.converse(
            "usr:alice", "2099-01", bad_word), C.E_CP_CONTENT_REJECTED),
        ("bad-month", lambda: cf.can_converse(
            "usr:alice", "2099-13"), C.E_CP_BAD_MONTH),
    )
    probes1 = []
    for label, fn, code in probe_specs:
        ok_one, got = expect_cp_error(fn, code)
        probes1.append("%s=%s" % (label, got) if ok_one else
                       "%s NOT-RAISED(%s)" % (label, got))
    # gate-fault probe: a second face over the same db wired to a
    # fault gate must fail closed with zero rows stored
    fault_face = C.CompanionFace(led, _FaultGate(), DISCLAIMER)
    ok_fault, code_fault = expect_cp_error(
        lambda: fault_face.converse("usr:alice", "2099-01", "hi"),
        C.E_CP_GATE_ERROR)
    fault_face.close()
    probes1.append("gate-fault=%s" % code_fault if ok_fault else
                   "gate-fault NOT-RAISED(%s)" % code_fault)
    ok_probes1 = all("NOT-RAISED" not in p for p in probes1)
    ok_probe_drift1 = (table_counts(db_path) == cnt1
                       and read_battery(cf, led) == bal1)
    ok1 = (ok_world and ok_label and ok_pass_faces and ok_tr and ok_mem
           and ok_subs and ok_probes1 and ok_probe_drift1)
    record("AC-CMP1", ok1, "anchor world pinned (jan passes"
          " alice/bob fee 120 each + feb pass carol fee 90;"
          " balances 180/380/110 pool 19330 (spend counter-leg"
          " flows back to the pool); dialogue spectrum"
          " alice two archived rounds + bob one round + carol"
          " feb one round = 8 msg rows with structural ai_label"
          " 0/1 alternating, 2 memory rows both anchored to"
          " companion replies, same kind twice = append-not-"
          "unique; can_ probes a/b-jan True, c-jan False, c-feb"
          " True, a-feb False; transcript windows a-jan 4 /"
          " b-jan 2 / c-jan 0 / c-feb 2; memory views 2/0/0;"
          " subs views 1/1/1 with month+price+bound tx); five"
          " gate probes rejected (%s); counts subs=%d msgs=%d"
          " memories=%d spend-tx=%d frozen across probes;"
          " digest=%s" % (
              "; ".join(probes1), cnt1["companion_subs"],
              cnt1["companion_msgs"], cnt1["companion_memories"],
              cnt1["spend_tx"], evidence_digest(bal1)))

    # -- AC-CMP2 cross-restart byte-identical replay ------------
    cf.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    gate2 = SecGate.from_config(lobby_cfg)
    cf2 = C.CompanionFace(led2, gate2, DISCLAIMER)
    bal2 = read_battery(cf2, led2)
    diffs2 = battery_diffs(bal1, bal2)
    ok2 = not diffs2
    record("AC-CMP2", ok2, "two-piece close->reopen (cf.close ->"
          " led.close -> Ledger same db/cfg + SecGate +"
          " CompanionFace fresh): read battery byte-identical to"
          " the pre-close snapshot (can_ five probes + transcript"
          " four windows + memory three views + subs three views"
          " + four balances), diffs=%s; created_utc and bound tx"
          " replay as stored values with zero in-memory drift;"
          " digest=%s" % (diffs2 or "none", evidence_digest(bal2)))

    # -- AC-CMP3 gates survive restart, zero drift --------------
    probes2 = []
    for label, fn, code in probe_specs:
        if label == "dup-pass":
            def fn2():
                cf2.buy_pass("usr:bob", "2099-01", 120, "order:cmp-p1")
        elif label == "denied":
            def fn2():
                cf2.converse("usr:carol", "2099-01", "hello there")
        elif label == "content":
            def fn2():
                cf2.converse("usr:alice", "2099-01", bad_word)
        else:
            def fn2():
                cf2.can_converse("usr:alice", "2099-13")
        ok_one, got = expect_cp_error(fn2, code)
        probes2.append("%s=%s" % (label, got) if ok_one else
                       "%s NOT-RAISED(%s)" % (label, got))
    fault_face2 = C.CompanionFace(led2, _FaultGate(), DISCLAIMER)
    ok_fault2, code_fault2 = expect_cp_error(
        lambda: fault_face2.converse("usr:alice", "2099-01", "hi"),
        C.E_CP_GATE_ERROR)
    fault_face2.close()
    probes2.append("gate-fault=%s" % code_fault2 if ok_fault2 else
                   "gate-fault NOT-RAISED(%s)" % code_fault2)
    ok_probes2 = all("NOT-RAISED" not in p for p in probes2)
    ok_drift2 = (table_counts(db_path) == cnt1
                 and read_battery(cf2, led2) == bal2)
    ok3 = ok_probes2 and ok_drift2
    record("AC-CMP3", ok3, "restart-surviving gates: five probes"
          " all rejected with identical codes on instance 2 (%s);"
          " counts and battery frozen across the probe batch"
          " (subs/msgs/memories/spend-tx %d/%d/%d/%d unchanged,"
          " zero charge, zero rows, zero memory appends)" % (
              "; ".join(probes2), cnt1["companion_subs"],
              cnt1["companion_msgs"], cnt1["companion_memories"],
              cnt1["spend_tx"]))

    # -- AC-CMP4 post-restart real-path continuation -------------
    p_c2 = cf2.buy_pass("usr:carol", "2099-01", 90, "order:cmp-c2")
    head_c2, leg_c2 = spend_cross(db_path, p_c2["spend_tx"],
                                  "usr:carol")
    m_c2 = cf2.converse("usr:carol", "2099-01",
                        "good evening friend")
    r_c2 = cf2.record_reply(m_c2["msg_id"],
                            "evening, the city is calm")
    e_c2 = cf2.archive_memory("usr:carol", "preference",
                              {"topic": "evening-greeting"},
                              r_c2["msg_id"])
    m_b2 = cf2.converse("usr:bob", "2099-01", "and the harbor gates?")
    r_b2 = cf2.record_reply(m_b2["msg_id"],
                            "the gates close at the ninth bell")
    e_b2 = cf2.archive_memory("usr:bob", "preference",
                              {"topic": "calendar"}, r_b2["msg_id"])
    bal4 = read_battery(cf2, led2)
    cnt4 = table_counts(db_path)
    can_c_jan4 = json.loads(bal4["can_c_jan"])
    tr_c_jan4 = json.loads(bal4["tr_c_jan"])["messages"]
    mem_b4 = json.loads(bal4["mem_b"])["memories"]
    mem_c4 = json.loads(bal4["mem_c"])["memories"]
    tr_a4 = json.loads(bal4["tr_a_jan"])["messages"]
    ok4 = (
        p_c2["token_price"] == 90 and p_c2["pass_month"] == "2099-01"
        and head_c2 == "spend" and leg_c2 == "debit"
        and can_c_jan4["allowed"] is True
        and len(tr_c_jan4) == 2
        and [m["role"] for m in tr_c_jan4] == ["resident", "companion"]
        and tr_c_jan4[0]["text"] == "good evening friend"
        and len(mem_c4) == 1
        and mem_c4[0]["source_msg_id"] == r_c2["msg_id"]
        and len(mem_b4) == 1
        and mem_b4[0]["source_msg_id"] == r_b2["msg_id"]
        and cnt4["companion_subs"] == 4 and cnt4["companion_msgs"] == 12
        and cnt4["companion_memories"] == 4 and cnt4["spend_tx"] == 4
        and bal4["bal_alice"] == 180 and bal4["bal_bob"] == 380
        and bal4["bal_carol"] == 20 and bal4["bal_pool"] == 19420
        and [s["pass_month"] for s in
             json.loads(bal4["subs_c"])["subs"]] ==
        ["2099-02", "2099-01"]
        and tr_a4 == json.loads(bal1["tr_a_jan"])["messages"])
    record("AC-CMP4", ok4, "post-restart continuation: carol buys"
          " the jan pass she lacked (fee 90, real spend tx: SQL"
          " cross type=%s debit leg=%s, tx_id not echoed) and the"
          " denied->allowed flip proves the subscription gate now"
          " admits her (can_c_jan False->True, tr_c_jan 0->2"
          " rows); carol's new round archives one memory"
          " (mem_c 0->1) and bob's new round archives one memory"
          " (mem_b 0->1); touched faces recompute zero-cache"
          " (new rows land at the msg_id/memory_id tail in"
          " order, subs_c now 2 rows in sub_id order); untouched"
          " faces frozen (tr_a_jan byte-same as anchor); counts"
          " subs 3->4, msgs 8->12, memories 2->4, spend-tx 3->4;"
          " balances 180/380/20/19420; digest=%s" % (
              head_c2, leg_c2, evidence_digest(bal4)))

    # -- AC-CMP5 frozen faces + gates across restart -------------
    subs_now, msgs_now, mems_now = preexisting_row_snapshot(db_path)
    frozen_ok = (subs_now[:3] == subs_pre and msgs_now[:8] == msgs_pre
                 and mems_now[:2] == mems_pre
                 and len(subs_now) == 4 and len(msgs_now) == 12
                 and len(mems_now) == 4)
    dup_probe, code_dup = expect_cp_error(
        lambda: cf2.buy_pass("usr:carol", "2099-01", 90,
                             "order:cmp-p5"), C.E_CP_PASS_DUP)
    denied_probe, code_denied = expect_cp_error(
        lambda: cf2.converse("usr:alice", "2099-02", "hello"),
        C.E_CP_DENIED)
    content_probe, code_content = expect_cp_error(
        lambda: cf2.converse("usr:bob", "2099-01", bad_word),
        C.E_CP_CONTENT_REJECTED)
    bal5 = read_battery(cf2, led2)
    ok5 = (frozen_ok and dup_probe and denied_probe and content_probe
           and table_counts(db_path) == cnt4 and bal5 == bal4)
    record("AC-CMP5", ok5, "frozen faces: all pre-existing rows keep"
          " every persisted field byte-identical (3 sub rows incl"
          " bound_spend_tx + granted_utc, 8 msg rows incl"
          " created_utc, 2 memory rows incl content_json) - the"
          " restart + continuation only appended at the rowid tail;"
          " gates across restart: carol's held jan pass re-bought"
          " with a fresh ref rejected %s (ref-blind, zero charge),"
          " alice converse on her passless feb rejected %s (zero"
          " rows), bob's gate-word converse rejected %s (zero"
          " rows); counts and battery frozen across the probe"
          " batch (%d==%d spend-tx)" % (
              code_dup, code_denied, code_content,
              cnt4["spend_tx"], table_counts(db_path)["spend_tx"]))

    # -- AC-CMP6 pure-read law -----------------------------------
    bat_a = read_battery(cf2, led2)
    bat_b = read_battery(cf2, led2)
    ok6 = (bat_a == bat_b and battery_diffs(bat_a, bat_b) == []
           and table_counts(db_path) == cnt4)
    record("AC-CMP6", ok6, "pure-read law: full battery read twice"
          " back-to-back - can_ probes + transcript windows +"
          " memory views + subs views + four balances"
          " byte-identical between the two reads and table counts"
          " constant (read faces have zero side effects)")

    # -- AC-CMP7 third instance stability + hygiene -------------
    cf2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    gate3 = SecGate.from_config(lobby_cfg)
    cf3 = C.CompanionFace(led3, gate3, DISCLAIMER)
    bal3 = read_battery(cf3, led3)
    diffs3 = battery_diffs(bal5, bal3)
    src = io_read(os.path.abspath(__file__))
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [l.strip() for l in src.splitlines()
                    if l.strip().startswith("import ")
                    or l.strip().startswith("from ")]
    net_imports = [l for l in import_lines
                   if any(k in l for k in
                         ("urllib", "requests", "socket", "http"))]
    ok7 = (not diffs3
           and sha16(io_read(cfg_path)) == cfg_sha_before
           and sha16(io_read(os.path.join(BASE, "companion.py")))
           == cmpmod_sha_before
           and sha16(io_read(os.path.join(BASE, "ledger.py")))
           == ledmod_sha_before
           and sha16(io_read(os.path.join(LOBBY, "sec_gate.py")))
           == gatemod_sha_before
           and non_ascii == 0 and not net_imports
           and os.path.realpath(tmp).startswith(
               os.path.realpath(tempfile.gettempdir()))
           and not os.path.realpath(tmp).startswith(repo_root))
    record("AC-CMP7", ok7, "third instance: close -> reopen same db"
          " once more - battery byte-identical to the instance-2"
          " terminal state (diffs=%s, all read faces stable across"
          " a second restart); shipped files untouched"
          " (config/ledger/companion/sec_gate sha16 stable); suite"
          " source pure ASCII (%d non-ascii), zero network imports"
          " (%d hits), world tmp outside repo (%s)" % (
              diffs3 or "none", non_ascii, len(net_imports),
              "yes" if not os.path.realpath(tmp).startswith(
                  repo_root) else "NO"))

    cf3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
