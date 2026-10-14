"""Acceptance suite for the resident proposal co-signature face
(BigDomain R1766; canon = explore-queue proposal line: proposal ->
co-signature -> threshold crossing triggers the collectibles
memorial linkage; seed = R-20260928-bigdomain-belonging-economy.md
+ collectibles.py R619). Asserts the pre-registered criteria
AC-PP1..AC-PP7 from the R1766 explore-queue row plus the R1968
progress-board successor criteria AC-PP8..AC-PP12 (all registered
before the code they govern existed; honesty law). Each criterion
prints PASS/FAIL with evidence; the process exits non-zero on any
FAIL.

The content gate is the lobby SecGate product injected by
reference (no copy): its Chinese wordlists are data loaded from
the lobby config at runtime - this test source stays pure ASCII
per the encoding discipline.

Usage: python test_proposal.py
"""

import inspect
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
import collectibles as C              # noqa: E402 (R619 face)
import proposal as P                  # noqa: E402 (R1766 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, reference)

RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the proposal board is a"
              " civic participation tool, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_pp_error(fn, *codes):
    try:
        fn()
    except P.ProposalError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


class _FaultGate(object):
    """Runtime-fault gate stub: check_text always blows up (the
    face must map this to E_PP_GATE_ERROR and never silently pass
    - AC-PP2 fail-closed posture)."""

    def check_text(self, text):
        raise RuntimeError("stub gate offline")


class _CountCerts(object):
    """Counting wrapper around the real CollectiblesFace: delegates
    every call, counts issue_certificate invocations (AC-PP4
    non-crossing-sign zero-award-call evidence)."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    def issue_certificate(self, *args, **kwargs):
        self.calls += 1
        return self.inner.issue_certificate(*args, **kwargs)

    def collection(self, *args, **kwargs):
        return self.inner.collection(*args, **kwargs)


def _count(conn, table):
    return conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]


def _cert_count(ledconn, event_ref):
    return ledconn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE kind = 'certificate'"
        " AND event_ref = ?", (event_ref,)).fetchone()[0]


def main():
    tmp = tempfile.mkdtemp(prefix="proposal-ac-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]
    advisory_word = lobby_cfg["gate"]["advisory_ban_words"][0]
    db_path = os.path.join(tmp, "ledger.db")
    pp_path = os.path.join(tmp, "proposal.db")

    led = L.Ledger(db_path, cfg)
    gate = SecGate.from_config(lobby_cfg)
    clt = C.CollectiblesFace(led)
    pf = P.ProposalFace(clt, gate, DISCLAIMER, pp_path)
    for who in ("alice", "bob", "carol", "dave", "erin", "frank",
                "gina"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    ledconn = sqlite3.connect(db_path)
    ppconn = sqlite3.connect(pp_path)
    led_tx0 = _count(ledconn, "ledger_tx")

    # -- AC-PP1 proposal registry --------------------------------------------
    r1 = pf.register_proposal(
        "night-lights", "Night lights for the harbor promenade",
        "Add warm lamp rows along the pier walk", "usr:alice",
        100, 200, 3, False)
    n_p0 = _count(ppconn, "proposals")
    ok_dup, code_dup = expect_pp_error(
        lambda: pf.register_proposal(
            "night-lights", "Night lights for the harbor promenade",
            "Add warm lamp rows along the pier walk", "usr:alice",
            100, 200, 3, False),
        P.E_PP_DUP_PROPOSAL)
    n_p1 = _count(ppconn, "proposals")
    r2 = pf.register_proposal(
        "quiet-hours", "Quiet hours for the plaza fountain",
        "Dim the fountain loop after midnight", "usr:bob",
        0, 50, 2, True)
    n_p2 = _count(ppconn, "proposals")
    bad1 = []
    raised1 = True
    for label, fn in (
            ("empty id", lambda: pf.register_proposal(
                "", "t", "b", "usr:alice", 0, 10, 2, False)),
            ("empty title", lambda: pf.register_proposal(
                "x1", "  ", "b", "usr:alice", 0, 10, 2, False)),
            ("empty body", lambda: pf.register_proposal(
                "x2", "t", "", "usr:alice", 0, 10, 2, False)),
            ("non-usr proposer", lambda: pf.register_proposal(
                "x3", "t", "b", "res:alice", 0, 10, 2, False)),
            ("negative start", lambda: pf.register_proposal(
                "x4", "t", "b", "usr:alice", -1, 10, 2, False)),
            ("end <= start", lambda: pf.register_proposal(
                "x5", "t", "b", "usr:alice", 10, 10, 2, False)),
            ("threshold 1", lambda: pf.register_proposal(
                "x6", "t", "b", "usr:alice", 0, 10, 1, False)),
            ("threshold bool", lambda: pf.register_proposal(
                "x7", "t", "b", "usr:alice", 0, 10, True, False)),
            ("ai flag non-bool", lambda: pf.register_proposal(
                "x8", "t", "b", "usr:alice", 0, 10, 2, "yes"))):
        ok_one, got = expect_pp_error(fn, P.E_PP_BAD_ARGS)
        if not ok_one:
            bad1.append(label + "->" + str(got))
            raised1 = False
    n_p3 = _count(ppconn, "proposals")
    ok_unk, code_unk = expect_pp_error(
        lambda: pf.proposal_view("no-such-proposal"),
        P.E_PP_UNKNOWN_PROPOSAL)
    ok1 = (n_p0 == 1 and ok_dup and n_p1 == 1 and r2["ai_label"] == 1
           and n_p2 == 2 and n_p3 == 2 and not bad1 and raised1
           and ok_unk and r1["signature_count"] == 0
           and r1["qualified"] is False
           and r1["window"] == [100, 200] and r1["threshold"] == 3)
    record("AC-PP1", ok1, "registry UNIQUE (1 row; dup %s rows %d);"
          " ai_label persistent (quiet-hours=1); bad args all"
          " rejected zero rows (%s -> rows %d); unknown read %s"
          % (code_dup, n_p1, bad1 or "none", n_p3, code_unk))

    # -- AC-PP2 msgSecCheck pre-gate ------------------------------------------
    n_gate0 = _count(ppconn, "proposals")
    ok_badw, code_badw = expect_pp_error(
        lambda: pf.register_proposal(
            "bad-title", "harbor plan " + bad_word,
            "clean body text", "usr:alice", 0, 10, 2, False),
        P.E_PP_CONTENT_REJECTED)
    ok_advw, code_advw = expect_pp_error(
        lambda: pf.register_proposal(
            "bad-body", "clean title text",
            "plaza note " + advisory_word, "usr:alice", 0, 10, 2,
            False),
        P.E_PP_CONTENT_REJECTED)
    n_gate1 = _count(ppconn, "proposals")
    fault_db = os.path.join(tmp, "proposal_fault.db")
    raised_fault = False
    code_fault = ""
    try:
        pff = P.ProposalFace(clt, _FaultGate(), DISCLAIMER, fault_db)
        pff.register_proposal("faulted", "t", "b", "usr:alice",
                              0, 10, 2, False)
    except P.ProposalError as exc:
        raised_fault = exc.code == P.E_PP_GATE_ERROR
        code_fault = exc.code
    fault_rows = 0
    fconn = sqlite3.connect(fault_db)
    fault_rows = _count(fconn, "proposals")
    fconn.close()
    ok_nogate, code_nogate = expect_pp_error(
        lambda: P.ProposalFace(clt, None, DISCLAIMER,
                               os.path.join(tmp, "p_ng.db")),
        P.E_PP_NO_GATE)
    ok_notext, code_notext = expect_pp_error(
        lambda: P.ProposalFace(clt, object(), DISCLAIMER,
                               os.path.join(tmp, "p_nt.db")),
        P.E_PP_NO_GATE)
    ok2 = (ok_badw and ok_advw and n_gate1 == n_gate0
           and raised_fault and fault_rows == 0 and ok_nogate
           and ok_notext)
    record("AC-PP2", ok2, "forbidden word in title -> %s; advisory"
          " word in body -> %s; zero rows stored (%d -> %d); fault"
          " gate -> %s with %d rows; unwired gate -> %s / %s"
          % (code_badw, code_advw, n_gate0, n_gate1, code_fault,
             fault_rows, code_nogate, code_notext))

    # -- AC-PP3 co-signature idempotency + window ------------------------------
    s_edge_a = pf.sign_proposal("usr:bob", "night-lights", 100)
    s_edge_b = pf.sign_proposal("usr:carol", "night-lights", 200)
    n_s0 = _count(ppconn, "proposal_signs")
    ok_win_lo, code_lo = expect_pp_error(
        lambda: pf.sign_proposal("usr:dave", "night-lights", 99),
        P.E_PP_WINDOW)
    ok_win_hi, code_hi = expect_pp_error(
        lambda: pf.sign_proposal("usr:dave", "night-lights", 201),
        P.E_PP_WINDOW)
    ok_self, code_self = expect_pp_error(
        lambda: pf.sign_proposal("usr:alice", "night-lights", 150),
        P.E_PP_SELF_SIGN)
    ok_resign, code_resign = expect_pp_error(
        lambda: pf.sign_proposal("usr:bob", "night-lights", 150),
        P.E_PP_DUP_SIGN)
    ok_acct, code_acct = expect_pp_error(
        lambda: pf.sign_proposal("res:x", "night-lights", 150),
        P.E_PP_BAD_ARGS)
    ok_tick, code_tick = expect_pp_error(
        lambda: pf.sign_proposal("usr:dave", "night-lights", True),
        P.E_PP_BAD_ARGS)
    n_s1 = _count(ppconn, "proposal_signs")
    led_tx3 = _count(ledconn, "ledger_tx")
    ok3 = (s_edge_a["signature_count"] == 1
           and s_edge_b["signature_count"] == 2 and n_s0 == 2
           and ok_win_lo and ok_win_hi and ok_self and ok_resign
           and ok_acct and ok_tick and n_s1 == 2
           and led_tx3 == led_tx0)
    record("AC-PP3", ok3, "window edges inclusive (tick 100 -> 1,"
          " tick 200 -> 2); outside rejected zero rows (%s / %s);"
          " self-sign %s; re-sign %s; bad account %s; bad tick %s;"
          " signs %d rows; ledger_tx constant (%d == %d)"
          % (code_lo, code_hi, code_self, code_resign, code_acct,
             code_tick, n_s1, led_tx3, led_tx0))

    # -- AC-PP4 derived qualification + memorial linkage ------------------------
    wrap = _CountCerts(clt)
    pf2_path = os.path.join(tmp, "proposal2.db")
    pf2 = P.ProposalFace(wrap, gate, DISCLAIMER, pf2_path)
    pp2conn = sqlite3.connect(pf2_path)
    pf2.register_proposal("ferry-line", "Weekend ferry line to the island",
                          "One extra crossing each weekend morning",
                          "usr:dave", 10, 30, 2, False)
    s_a = pf2.sign_proposal("usr:erin", "ferry-line", 10)
    calls_after_first = wrap.calls
    s_b = pf2.sign_proposal("usr:frank", "ferry-line", 12)
    calls_after_cross = wrap.calls
    cert_ferry = _cert_count(ledconn, "proposal-memorial:ferry-line")
    s_c = pf2.sign_proposal("usr:gina", "ferry-line", 20)
    calls_after_third = wrap.calls
    pf2.register_proposal("pre-award", "Pre-awarded plaza bench plan",
                          "Platform pre-granted the memorial before"
                          " the crossing", "usr:alice", 10, 30, 2, False)
    clt.issue_certificate("usr:alice", "proposal-memorial:pre-award",
                          "proposal-memorial")
    cert_pre0 = _cert_count(ledconn, "proposal-memorial:pre-award")
    pf2.sign_proposal("usr:erin", "pre-award", 10)
    s_pre = pf2.sign_proposal("usr:frank", "pre-award", 11)
    cert_pre1 = _cert_count(ledconn, "proposal-memorial:pre-award")
    pre_signs = _count(pp2conn, "proposal_signs") - 3
    ok_nocl, code_nocl = expect_pp_error(
        lambda: P.ProposalFace(None, gate, DISCLAIMER,
                               os.path.join(tmp, "p_nc.db")),
        P.E_PP_BAD_ARGS)
    ok_noic, code_noic = expect_pp_error(
        lambda: P.ProposalFace(object(), gate, DISCLAIMER,
                               os.path.join(tmp, "p_ni.db")),
        P.E_PP_BAD_ARGS)
    ok4 = (s_a["memorial"] is None and calls_after_first == 0
           and s_b["signature_count"] == 2 and s_b["qualified"] is True
           and s_b["memorial"] == "issued" and calls_after_cross == 1
           and cert_ferry == 1 and s_c["memorial"] is None
           and calls_after_third == 1 and cert_pre0 == 1
           and s_pre["memorial"] == "already" and cert_pre1 == 1
           and pre_signs == 2 and ok_nocl and ok_noic)
    record("AC-PP4", ok4, "non-crossing sign zero award calls"
          " (%d); crossing sign awards (memorial=%s, calls %d,"
          " cert rows %d); over-threshold sign no award (%d calls);"
          " platform pre-award internalized (memorial=%s, certs"
          " %d -> %d, signs %d); unwired collectibles %s / %s"
          % (calls_after_first, s_b["memorial"], calls_after_cross,
             cert_ferry, calls_after_third, s_pre["memorial"],
             cert_pre0, cert_pre1, pre_signs, code_nocl, code_noic))

    # -- AC-PP5 pure-read derivation --------------------------------------------
    view_a = pf2.proposal_view("ferry-line")
    live_count_sql = pp2conn.execute(
        "SELECT COUNT(*) FROM proposal_signs WHERE proposal_id ="
        " 'ferry-line'").fetchone()[0]
    pf2.sign_proposal("usr:bob", "ferry-line", 15)
    view_b = pf2.proposal_view("ferry-line")
    live_count_sql_b = pp2conn.execute(
        "SELECT COUNT(*) FROM proposal_signs WHERE proposal_id ="
        " 'ferry-line'").fetchone()[0]
    board = pf2.proposal_board()
    board_rows = {row["proposal_id"]: row for row in board["proposals"]}
    src_view = inspect.getsource(P.ProposalFace.proposal_view)
    src_board = inspect.getsource(P.ProposalFace.proposal_board)
    src_count = inspect.getsource(P.ProposalFace._sign_count)
    write_words = [w for w in ("INSERT", "UPDATE", "DELETE")
                   if w in src_view or w in src_board or w in src_count]
    led_tx5 = _count(ledconn, "ledger_tx")
    ok5 = (view_a["signature_count"] == 3
           and view_a["signature_count"] == live_count_sql
           and view_a["qualified"] is True
           and len(view_a["signers"]) == 3
           and view_a["signers"][0]["account_id"] == "usr:erin"
           and view_b["signature_count"] == 4
           and view_b["signature_count"] == live_count_sql_b
           and board_rows["ferry-line"]["signature_count"] == 4
           and board_rows["pre-award"]["qualified"] is True
           and not write_words and led_tx5 == led_tx0)
    record("AC-PP5", ok5, "view count == SQL COUNT (%d == %d),"
          " qualified derived; live derivation (new sign 3 -> %d);"
          " board counts (%d); read methods zero write statements"
          " (%s); ledger_tx constant (%d == %d)"
          % (view_a["signature_count"], live_count_sql,
             view_b["signature_count"],
             board_rows["ferry-line"]["signature_count"],
             write_words or "none", led_tx5, led_tx0))

    # -- AC-PP6 AIGC label + resident disclaimer law -----------------------------
    ok_nod1, _c1 = expect_pp_error(
        lambda: P.ProposalFace(clt, gate, "",
                               os.path.join(tmp, "p_nd1.db")),
        P.E_PP_NO_DISCLAIMER)
    ok_nod2, _c2 = expect_pp_error(
        lambda: P.ProposalFace(clt, gate, "   ",
                               os.path.join(tmp, "p_nd2.db")),
        P.E_PP_NO_DISCLAIMER)
    quiet_view = pf.proposal_view("quiet-hours")
    envelopes_ok = (r1["disclaimer"] == DISCLAIMER
                    and s_edge_a["disclaimer"] == DISCLAIMER
                    and quiet_view["disclaimer"] == DISCLAIMER
                    and board["disclaimer"] == DISCLAIMER
                    and quiet_view["ai_label"] == 1
                    and r1["ai_label"] == 0)
    integ_caught = False
    try:
        ppconn.execute(
            "INSERT INTO proposals (proposal_id, title, body,"
            " proposer, start_tick, end_tick, threshold, ai_label,"
            " registered_utc) VALUES ('bad-ai','t','b','usr:alice',"
            "0,10,2,2,'now')")
        ppconn.commit()
    except sqlite3.IntegrityError:
        ppconn.rollback()
        integ_caught = True
    ok6 = (ok_nod1 and ok_nod2 and envelopes_ok and integ_caught)
    record("AC-PP6", ok6, "empty disclaimer refused construction"
          " (%s/%s); disclaimer rides every envelope (register/sign/"
          "view/board); ai_label persistent on views (quiet-hours=1,"
          " night-lights=0); direct ai_label=2 INSERT rejected by DB"
          " CHECK (%s)" % (_c1, _c2, integ_caught))

    # -- AC-PP7 hard laws --------------------------------------------------------
    with open(os.path.join(BASE, "proposal.py"), "rb") as handle:
        pp_src = handle.read().decode("utf-8")
    non_ascii = sum(1 for ch in pp_src if ord(ch) > 127)
    net_imports = [ln for ln in pp_src.splitlines()
                   if (ln.startswith("import ") or ln.startswith("from "))
                   and any(w in ln for w in
                           ("urllib", "requests", "socket", "http"))]
    update_hits = [w for w in ("UPDATE proposals", "UPDATE proposal_signs")
                   if w in pp_src]
    second_engine = [w for w in ("FROM collectibles", "INTO collectibles",
                                 "FROM ledger_tx", "INTO ledger_tx")
                     if w in pp_src]
    ledger_ref = ("import ledger" in pp_src
                  or "from ledger import" in pp_src)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    ok7 = (non_ascii == 0 and not net_imports and not update_hits
           and not second_engine and not ledger_ref
           and "random" not in pp_src and cfg_after == cfg_bytes)
    record("AC-PP7", ok7, "module pure ASCII (%d non-ascii); zero"
          " network imports (%d); zero UPDATE surface (%s); zero"
          " collectibles/ledger direct SQL (%s); zero ledger import"
          " (%s); zero RNG; shipped config.json byte-stable"
          % (non_ascii, len(net_imports), update_hits or "none",
             second_engine or "none", ledger_ref))

    # -- AC-PP8..AC-PP12 progress board (R1968 read-face successor) ----------
    pf3_path = os.path.join(tmp, "proposal3.db")
    pf3 = P.ProposalFace(clt, gate, DISCLAIMER, pf3_path)
    pp3conn = sqlite3.connect(pf3_path)
    empty_pb = pf3.progress_board()
    empty_keys = set(empty_pb.keys())
    # register in reverse board order (zero insertion-order key probe)
    pf3.register_proposal("fresh-air", "Fresh air intakes for the arcade",
                          "Add two green-air intakes at the arcade ends",
                          "usr:carol", 10, 30, 4, True)
    pf3.register_proposal("midway", "Midweek market stalls",
                          "Open the plaza for midweek stall holders",
                          "usr:dave", 10, 30, 3, False)
    pf3.register_proposal("at-bar", "At-bar rooftop apiary",
                          "A rooftop apiary at the required bar",
                          "usr:frank", 10, 30, 3, True)
    pf3.register_proposal("over-pass", "Over-pass harbor lanterns",
                          "Lantern rows past the required bar",
                          "usr:gina", 10, 30, 3, False)
    for who in ("bob", "carol", "dave", "erin", "frank"):
        pf3.sign_proposal("usr:" + who, "over-pass", 12)
    for who in ("bob", "carol", "dave"):
        pf3.sign_proposal("usr:" + who, "at-bar", 14)
    pf3.sign_proposal("usr:bob", "midway", 16)
    pb1 = pf3.progress_board()
    rows1 = {r["proposal_id"]: r for r in pb1["progress_board"]}
    row_keys = {frozenset(r.keys()) for r in pb1["progress_board"]}
    row_shape = frozenset(("proposal_id", "title", "signature_count",
                           "threshold", "remaining", "progress_pct",
                           "qualified", "ai_label"))
    want_vals = {"over-pass": (5, 3, 0, 100.0, True),
                 "at-bar": (3, 3, 0, 100.0, True),
                 "midway": (1, 3, 2, 33.33, False),
                 "fresh-air": (0, 4, 4, 0.0, False)}
    vals_ok = all(
        (rows1[k]["signature_count"], rows1[k]["threshold"],
         rows1[k]["remaining"], rows1[k]["progress_pct"],
         rows1[k]["qualified"]) == v for k, v in want_vals.items())
    ok8 = (empty_pb["progress_board"] == []
           and empty_keys == {"progress_board", "disclaimer"}
           and set(pb1.keys()) == {"progress_board", "disclaimer"}
           and row_keys == {row_shape}
           and len(pb1["progress_board"]) == 4 and vals_ok)
    record("AC-PP8", ok8, "empty world honest []; envelope keys"
          " %s; row keys exact (8); dense 4 rows; four-state values"
          " pinned (5/3->100.0 rem0 Q; 3/3->100.0 rem0 Q; 1/3->"
          "33.33 rem2; 0/4->0.0 rem4): %s"
          % (sorted(empty_keys), vals_ok))

    manual = {}
    for pid in want_vals:
        cnt = pp3conn.execute(
            "SELECT COUNT(*) FROM proposal_signs WHERE proposal_id ="
            " ?", (pid,)).fetchone()[0]
        thr = pp3conn.execute(
            "SELECT threshold FROM proposals WHERE proposal_id = ?",
            (pid,)).fetchone()[0]
        manual[pid] = (cnt, int(thr))
    cross_ok = all(
        rows1[pid]["signature_count"] == manual[pid][0]
        and rows1[pid]["threshold"] == manual[pid][1]
        and rows1[pid]["progress_pct"] == round(
            min(manual[pid][0], manual[pid][1]) * 100.0
            / manual[pid][1], 2)
        and rows1[pid]["remaining"] == max(
            manual[pid][1] - manual[pid][0], 0)
        and rows1[pid]["qualified"] == (
            manual[pid][0] >= manual[pid][1])
        for pid in want_vals)
    sat_law = (rows1["over-pass"]["progress_pct"] == 100.0
               and rows1["over-pass"]["progress_pct"] != 166.67)
    ok9 = cross_ok and sat_law
    record("AC-PP9", ok9, "per-row count/threshold == manual SQL;"
          " progress_pct == manual arithmetic (overshoot saturated"
          " 100.0, not 166.67); remaining == max(t-c,0); qualified"
          " == count>=threshold arithmetic")

    order1 = [r["proposal_id"] for r in pb1["progress_board"]]
    pb2 = pf3.progress_board()
    dumps_same = (json.dumps(pb1, sort_keys=True)
                  == json.dumps(pb2, sort_keys=True))
    ok10 = (order1 == ["at-bar", "over-pass", "midway", "fresh-air"]
            and dumps_same)
    record("AC-PP10", ok10, "reverse-registration world still key-"
          "ordered (100.0 tie band id-ascending: at-bar <"
          " over-pass; then 33.33; then 0.0); double-call"
          " json.dumps(sort_keys=True) byte-identical: %s"
          % dumps_same)

    n_prop_a = _count(pp3conn, "proposals")
    n_sign_a = _count(pp3conn, "proposal_signs")
    pb_x = pf3.progress_board()
    pb_y = pf3.progress_board()
    n_prop_b = _count(pp3conn, "proposals")
    n_sign_b = _count(pp3conn, "proposal_signs")
    src_prog = inspect.getsource(P.ProposalFace.progress_board)
    write_words = [w for w in ("INSERT", "UPDATE", "DELETE")
                   if w in src_prog]
    led_tx11 = _count(ledconn, "ledger_tx")
    pf3.sign_proposal("usr:carol", "midway", 18)
    pb_live = pf3.progress_board()
    live_mid = {r["proposal_id"]: r for r in pb_live["progress_board"]}
    pf3.sign_proposal("usr:erin", "midway", 20)
    pb_cross = pf3.progress_board()
    order_cross = [r["proposal_id"] for r in pb_cross["progress_board"]]
    ok11 = (n_prop_a == n_prop_b and n_sign_a == n_sign_b
            and pb_x == pb1 and pb_y == pb1 and not write_words
            and led_tx11 == led_tx0
            and live_mid["midway"]["progress_pct"] == 66.67
            and live_mid["midway"]["remaining"] == 1
            and live_mid["midway"]["qualified"] is False
            and order_cross == ["at-bar", "midway", "over-pass",
                                "fresh-air"])
    record("AC-PP11", ok11, "pure-read (rows %d/%d signs %d/%d"
          " constant; double extra calls == first; method source"
          " zero write words %s; ledger_tx constant %d==%d); live"
          " derivation (sign 2/3 -> pct 66.67 rem 1; crossing sign"
          " -> midway joins the saturated band, order %s)"
          % (n_prop_a, n_prop_b, n_sign_a, n_sign_b,
             write_words or "none", led_tx11, led_tx0, order_cross))

    rows_final = {r["proposal_id"]: r for r in
                  pb_cross["progress_board"]}
    ai_ok = (rows_final["over-pass"]["ai_label"] == 0
             and rows_final["at-bar"]["ai_label"] == 1
             and rows_final["midway"]["ai_label"] == 0
             and rows_final["fresh-air"]["ai_label"] == 1)
    src_ascii = all(ord(ch) <= 127 for ch in src_prog)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after12 = handle.read()
    ok12 = (pb_cross["disclaimer"] == DISCLAIMER and ai_ok
            and src_ascii and "random" not in src_prog
            and cfg_after12 == cfg_bytes)
    record("AC-PP12", ok12, "disclaimer rides the envelope; ai_label"
          " persistent per registration declaration (over-pass 0,"
          " at-bar 1, midway 0, fresh-air 1); method source pure"
          " ASCII, zero RNG; shipped config.json byte-stable")

    ppconn.close()
    pp2conn.close()
    pp3conn.close()
    ledconn.close()
    pf.close()
    pf2.close()
    led.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                              len(RESULTS) - fail, len(RESULTS)),
          flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
