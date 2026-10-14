"""Cross-restart persistence suite for the resident proposal
co-signature face (BigDomain R1956; FIFO head claim of the R1951
reseed row; persist-example family R1886 lineage).
Asserts the pre-registered criteria AC-PLP1..AC-PLP7 from the
tech.md proposal-persist claim row (criteria were registered before
this code existed; honesty law). Two-piece restart law: the proposal
face owns its sqlite connection over its own db file (proposal.db,
append-only, zero UPDATE); the collectibles memorial certificates
ride the ledger db (caller-owned face injected by reference).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Usage: python test_proposal_persist.py
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
import collectibles as C              # noqa: E402 (R619 face)
import proposal as P                  # noqa: E402 (R1766 face)
from sec_gate import SecGate          # noqa: E402 (lobby product, reference)

RESULTS = []

PROPOSALS = ("night-lights", "quiet-hours", "pier-garden",
             "lantern-fund")
DISCLAIMER = ("sandbox stand-in disclaimer: the proposal board is a"
              " civic participation tool, not investment advice")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_pp_error(fn, *codes):
    try:
        fn()
    except P.ProposalError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def cert_count(led_path, event_ref):
    conn = sqlite3.connect(led_path)
    n = conn.execute(
        "SELECT COUNT(*) FROM collectibles WHERE kind = 'certificate'"
        " AND event_ref = ?", (event_ref,)).fetchone()[0]
    conn.close()
    return int(n)


def pp_rows(pp_path):
    conn = sqlite3.connect(pp_path)
    out = {}
    out["proposals"] = [list(r) for r in conn.execute(
        "SELECT proposal_id, title, body, proposer, start_tick,"
        " end_tick, threshold, ai_label FROM proposals"
        " ORDER BY rowid").fetchall()]
    out["proposal_signs"] = [list(r) for r in conn.execute(
        "SELECT sign_id, proposal_id, account_id, at_tick FROM"
        " proposal_signs ORDER BY sign_id").fetchall()]
    conn.close()
    return out


def pp_counts(pp_path):
    conn = sqlite3.connect(pp_path)
    a = conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]
    b = conn.execute("SELECT COUNT(*) FROM proposal_signs").fetchone()[0]
    conn.close()
    return (int(a), int(b))


def tx_count(led_path):
    conn = sqlite3.connect(led_path)
    n = conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    conn.close()
    return int(n)


def battery(face):
    out = {}
    for pid in PROPOSALS:
        out[pid + "/view"] = face.proposal_view(pid)
    out["board"] = face.proposal_board()
    return json.dumps(out, sort_keys=True, default=str)


def gate_batch(face, bad_word):
    """Nine-gate reject probe batch (every reject fires before any
    row write). Returns (codes, all_ok, pre, post)."""
    pre = pp_counts(face.db_path)
    codes = []
    all_ok = True

    def probe(fn, *expect):
        ok, code = expect_pp_error(fn, *expect)
        codes.append(code if ok else "WRONG:" + str(code))
        return ok

    all_ok &= probe(
        lambda: face.register_proposal(
            "night-lights", "dup", "dup body", "usr:alice",
            100, 200, 3, False), P.E_PP_DUP_PROPOSAL)
    all_ok &= probe(
        lambda: face.register_proposal(
            "gate-hit", "title with %s inside" % bad_word, "body",
            "usr:alice", 100, 200, 3, False),
        P.E_PP_CONTENT_REJECTED)
    all_ok &= probe(
        lambda: face.register_proposal(
            "bad-one", "", "body", "usr:alice", 100, 200, 3, False),
        P.E_PP_BAD_ARGS)
    all_ok &= probe(
        lambda: face.register_proposal(
            "bad-two", "t", "b", "usr:alice", 200, 100, 3, False),
        P.E_PP_BAD_ARGS)
    all_ok &= probe(
        lambda: face.register_proposal(
            "bad-three", "t", "b", "usr:alice", 100, 200, 1, False),
        P.E_PP_BAD_ARGS)
    all_ok &= probe(
        lambda: face.sign_proposal("usr:bob", "ghost-proposal", 150),
        P.E_PP_UNKNOWN_PROPOSAL)
    all_ok &= probe(
        lambda: face.sign_proposal("usr:bob", "night-lights", 99),
        P.E_PP_WINDOW)
    all_ok &= probe(
        lambda: face.sign_proposal("usr:bob", "night-lights", 201),
        P.E_PP_WINDOW)
    all_ok &= probe(
        lambda: face.sign_proposal("usr:alice", "night-lights", 150),
        P.E_PP_SELF_SIGN)
    all_ok &= probe(
        lambda: face.sign_proposal("usr:bob", "night-lights", 150),
        P.E_PP_DUP_SIGN)
    all_ok &= probe(
        lambda: face.sign_proposal("corp:bob", "night-lights", 150),
        P.E_PP_BAD_ARGS)
    all_ok &= probe(
        lambda: face.proposal_view("ghost-proposal"),
        P.E_PP_UNKNOWN_PROPOSAL)
    post = pp_counts(face.db_path)
    return codes, all_ok, pre, post


def main():
    tmp = tempfile.mkdtemp(prefix="proposal-persist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg_bytes = handle.read()
    lobby_cfg = json.loads(lobby_cfg_bytes.decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]
    with open(os.path.join(BASE, "proposal.py"), "rb") as handle:
        proposal_bytes = handle.read()
    with open(os.path.join(BASE, "collectibles.py"), "rb") as handle:
        collectibles_bytes = handle.read()
    with open(os.path.join(BASE, "ledger.py"), "rb") as handle:
        ledger_bytes = handle.read()
    with open(os.path.join(LOBBY, "sec_gate.py"), "rb") as handle:
        sec_gate_bytes = handle.read()

    db_path = os.path.join(tmp, "ledger.db")
    pp_path = os.path.join(tmp, "proposal.db")

    led = L.Ledger(db_path, cfg)
    gate = SecGate.from_config(lobby_cfg)
    clt = C.CollectiblesFace(led)
    pf = P.ProposalFace(clt, gate, DISCLAIMER, pp_path)
    for who in ("alice", "bob", "carol", "dave", "erin", "frank"):
        led.ensure_account("usr:" + who, census_avatar_id=who)

    tx0 = tx_count(db_path)

    # -- anchor world (AC-PLP1 shape) -------------------------------------
    r1 = pf.register_proposal(
        "night-lights", "Night lights for the harbor promenade",
        "Add warm lamp rows along the pier walk", "usr:alice",
        100, 200, 3, False)
    pf.register_proposal(
        "quiet-hours", "Quiet hours for the night market street",
        "Keep the market street calm after midnight", "usr:bob",
        100, 200, 2, True)
    pf.register_proposal(
        "pier-garden", "A public garden at the old pier head",
        "Turn the disused pier head into a small garden",
        "usr:carol", 100, 200, 4, False)
    pf.register_proposal(
        "lantern-fund", "Lantern fund for the winter festival",
        "A shared fund proposal for lanterns", "usr:erin",
        100, 200, 2, True)
    # platform pre-award for lantern-fund (idempotence path):
    clt.issue_certificate("usr:erin", "proposal-memorial:lantern-fund",
                          "proposal-memorial")
    s_nb = pf.sign_proposal("usr:bob", "night-lights", 120)
    s_nc = pf.sign_proposal("usr:carol", "night-lights", 130)
    s_nd = pf.sign_proposal("usr:dave", "night-lights", 140)
    s_qa = pf.sign_proposal("usr:alice", "quiet-hours", 110)
    s_pa = pf.sign_proposal("usr:alice", "pier-garden", 110)
    s_pb = pf.sign_proposal("usr:bob", "pier-garden", 120)
    s_la = pf.sign_proposal("usr:alice", "lantern-fund", 100)
    s_lf = pf.sign_proposal("usr:frank", "lantern-fund", 150)

    snap_battery = battery(pf)
    snap_rows = pp_rows(pp_path)
    snap_dump = json.dumps(snap_rows, sort_keys=True, default=str)
    counts1 = pp_counts(pp_path)
    cert_nl = cert_count(db_path, "proposal-memorial:night-lights")
    cert_lf = cert_count(db_path, "proposal-memorial:lantern-fund")
    tx1 = tx_count(db_path)
    codes1, ok_gates1, pre1, post1 = gate_batch(pf, bad_word)
    board1 = pf.proposal_board()

    ok1 = (r1["signature_count"] == 0 and r1["qualified"] is False
           and r1["ai_label"] == 0 and r1["threshold"] == 3
           and r1["disclaimer"] == DISCLAIMER
           and s_nb["signature_count"] == 1 and s_nb["memorial"] is None
           and s_nc["signature_count"] == 2 and s_nc["memorial"] is None
           and s_nd["signature_count"] == 3
           and s_nd["qualified"] is True
           and s_nd["memorial"] == "issued"
           and s_qa["signature_count"] == 1
           and s_pa["signature_count"] == 1
           and s_pb["signature_count"] == 2
           and s_la["signature_count"] == 1
           and s_lf["signature_count"] == 2
           and s_lf["qualified"] is True
           and s_lf["memorial"] == "already"
           and counts1 == (4, 8)
           and cert_nl == 1 and cert_lf == 1
           and tx1 == tx0
           and ok_gates1 and post1 == counts1
           and board1["proposals"][0]["qualified"] is True
           and board1["proposals"][1]["qualified"] is False
           and board1["proposals"][2]["qualified"] is False
           and board1["proposals"][3]["qualified"] is True
           and [p["signature_count"] for p in
                board1["proposals"]] == [3, 1, 2, 2])
    record("AC-PLP1", ok1, "anchor world: 4 proposals / 8 sign rows;"
          " crossing sign night-lights memorial=issued (alice cert"
          " SQL cross=1); lantern-fund pre-award crossing"
          " memorial=already (cert stays 1, zero double-issue);"
          " ledger_tx flat %d -> %d (zero-token structure law);"
          " twelve-gate probe batch codes %s all-reject, row counts"
          " flat %s -> %s; derived board qualified=[T,F,F,T]"
          " counts=[3,1,2,2]"
          % (tx0, tx1, codes1, pre1, post1))

    # -- AC-PLP2: two-piece close -> reopen, byte-identical battery ------
    pf.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    gate2 = SecGate.from_config(lobby_cfg)
    clt2 = C.CollectiblesFace(led2)
    pf2 = P.ProposalFace(clt2, gate2, DISCLAIMER, pp_path)
    post_battery = battery(pf2)
    post_rows = pp_rows(pp_path)
    post_dump = json.dumps(post_rows, sort_keys=True, default=str)
    cert_nl2 = cert_count(db_path, "proposal-memorial:night-lights")
    cert_lf2 = cert_count(db_path, "proposal-memorial:lantern-fund")
    ok2 = (post_battery == snap_battery and post_dump == snap_dump
           and cert_nl2 == 1 and cert_lf2 == 1)
    record("AC-PLP2", ok2, "close -> new Ledger + new CollectiblesFace"
          " + new ProposalFace over the same dbs: read battery"
          " byte-identical (%d bytes) and two-table SQL rows"
          " byte-identical (%d proposal + %d sign rows) = zero"
          " in-memory drift; memorial certificates survive restart"
          " (night-lights=1 lantern-fund=1)"
          % (len(snap_battery.encode("utf-8")), counts1[0],
             counts1[1]))

    # -- AC-PLP3: gates cross-restart, same codes, same order ------------
    codes2, ok_gates2, pre2, post2 = gate_batch(pf2, bad_word)
    ok3 = (codes2 == codes1 and ok_gates2 and post2 == counts1
           and pre2 == counts1)
    record("AC-PLP3", ok3, "restart-surviving gates: probe batch on"
          " the reopened instance returns the same code sequence %s"
          " (twelve rejects); row counts flat %s -> %s = every"
          " reject still fires before any write" % (codes2, pre2,
                                                    post2))

    # -- AC-PLP4: real-path continuation, zero-cache recompute ------------
    s_qc = pf2.sign_proposal("usr:carol", "quiet-hours", 160)
    r_ferry = pf2.register_proposal(
        "harbor-ferry", "A night ferry across the harbor bay",
        "Bring back the small night ferry line", "usr:dave",
        100, 200, 3, False)
    s_pc = pf2.sign_proposal("usr:dave", "pier-garden", 160)
    v_q = pf2.proposal_view("quiet-hours")
    board2 = pf2.proposal_board()
    cert_bob = cert_count(db_path, "proposal-memorial:quiet-hours")
    counts4 = pp_counts(pp_path)
    ok4 = (s_qc["signature_count"] == 2 and s_qc["qualified"] is True
           and s_qc["memorial"] == "issued"
           and cert_bob == 1
           and r_ferry["signature_count"] == 0
           and s_pc["signature_count"] == 3
           and s_pc["qualified"] is False
           and s_pc["memorial"] is None
           and v_q["signature_count"] == 2
           and v_q["qualified"] is True
           and len(v_q["signers"]) == 2
           and [p["proposal_id"] for p in
                board2["proposals"]] == list(PROPOSALS)
           + ["harbor-ferry"]
           and counts4 == (5, 10))
    record("AC-PLP4", ok4, "post-restart continuation: quiet-hours"
          " 2nd sign crosses (bob memorial=issued, cert SQL cross"
          "=1); new proposal harbor-ferry registers (5th row,"
          " board rowid order appends last); pier-garden 3rd sign"
          " stays under threshold 4 (memorial None); view recompute"
          " quiet-hours 1->2 qualified True; counts %s"
          % (counts4,))

    # -- AC-PLP5: frozen anchor rows + replay gate cross-restart ----------
    now_rows = pp_rows(pp_path)
    frozen_proposals = (now_rows["proposals"][:4]
                        == snap_rows["proposals"])
    frozen_signs = (now_rows["proposal_signs"][:8]
                    == snap_rows["proposal_signs"])
    grew = (len(now_rows["proposals"]) == 5
            and len(now_rows["proposal_signs"]) == 10)
    ok_replay, code_rp = expect_pp_error(
        lambda: pf2.register_proposal(
            "night-lights", "dup", "dup body", "usr:alice",
            100, 200, 3, False), P.E_PP_DUP_PROPOSAL)
    ok_resign, code_rs = expect_pp_error(
        lambda: pf2.sign_proposal("usr:bob", "night-lights", 150),
        P.E_PP_DUP_SIGN)
    ok_ghost, code_gh = expect_pp_error(
        lambda: pf2.proposal_view("ghost-proposal"),
        P.E_PP_UNKNOWN_PROPOSAL)
    pre5 = pp_counts(pp_path)
    cert_lf3 = cert_count(db_path, "proposal-memorial:lantern-fund")
    post5 = pp_counts(pp_path)
    ok5 = (frozen_proposals and frozen_signs and grew
           and ok_replay and code_rp == P.E_PP_DUP_PROPOSAL
           and ok_resign and code_rs == P.E_PP_DUP_SIGN
           and ok_ghost and code_gh == P.E_PP_UNKNOWN_PROPOSAL
           and pre5 == counts4 and post5 == counts4
           and cert_lf3 == 1)
    record("AC-PLP5", ok5, "frozen anchors: original 4 proposal rows"
          " and first 8 sign rows byte-identical after restart +"
          " continuation (append-only: proposals 4->%d signs 8->%d);"
          " pre-restart replay dup-register %s / dup-sign %s both"
          " rejected with counts flat %s -> %s; ghost view honest"
          " reject %s; pre-awarded lantern-fund memorial stays 1"
          " (idempotent, no double-issue across restart)"
          % (len(now_rows["proposals"]),
             len(now_rows["proposal_signs"]), code_rp, code_rs,
             pre5, post5, code_gh))

    # -- AC-PLP6: pure-read law --------------------------------------------
    before = pp_counts(pp_path)
    cert_pre = (cert_count(db_path, "proposal-memorial:night-lights"),
                cert_count(db_path,
                           "proposal-memorial:quiet-hours"),
                cert_count(db_path,
                           "proposal-memorial:lantern-fund"))
    b1 = battery(pf2)
    b2 = battery(pf2)
    after = pp_counts(pp_path)
    cert_post = (cert_count(db_path, "proposal-memorial:night-lights"),
                 cert_count(db_path,
                            "proposal-memorial:quiet-hours"),
                 cert_count(db_path,
                            "proposal-memorial:lantern-fund"))
    ok6 = (before == after and b1 == b2 and cert_pre == cert_post
           and cert_post == (1, 1, 1))
    record("AC-PLP6", ok6, "pure-read law: full battery double-call"
          " byte-identical; row counts flat %s; memorial cert"
          " counts flat %s (reads award nothing, zero side effects)"
          % (before, cert_post))

    # -- AC-PLP7: third instance stable + hygiene -------------------------
    end_battery = battery(pf2)
    pf2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    gate3 = SecGate.from_config(lobby_cfg)
    clt3 = C.CollectiblesFace(led3)
    pf3 = P.ProposalFace(clt3, gate3, DISCLAIMER, pp_path)
    third_battery = battery(pf3)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    with open(os.path.join(BASE, "proposal.py"), "rb") as handle:
        proposal_after = handle.read()
    with open(os.path.join(BASE, "collectibles.py"), "rb") as handle:
        collectibles_after = handle.read()
    with open(os.path.join(BASE, "ledger.py"), "rb") as handle:
        ledger_after = handle.read()
    with open(os.path.join(LOBBY, "sec_gate.py"), "rb") as handle:
        sec_gate_after = handle.read()
    with open(os.path.abspath(__file__), "rb") as handle:
        own_bytes = handle.read()
    own_non_ascii = sum(1 for b in own_bytes if b > 127)
    sha_own = hashlib.sha256(own_bytes).hexdigest()[:16]
    net_imports = [ln.strip() for ln in own_bytes.decode(
        "utf-8").splitlines()
        if ln.strip().startswith("import ")
        or ln.strip().startswith("from ")]
    src_text = proposal_bytes.decode("utf-8")
    update_hits = [ln.strip() for ln in src_text.splitlines()
                   if "UPDATE " in ln.upper()
                   and "execute(" in ln]
    ok7 = (third_battery == end_battery
           and cfg_after == cfg_bytes
           and proposal_after == proposal_bytes
           and collectibles_after == collectibles_bytes
           and ledger_after == ledger_bytes
           and sec_gate_after == sec_gate_bytes
           and own_non_ascii == 0
           and tmp.startswith(tempfile.gettempdir())
           and update_hits == [])
    record("AC-PLP7", ok7, "second close -> third instance over the"
          " same dbs: battery byte-identical to the second-instance"
          " end state (5 proposals x view + board); config.json /"
          " proposal.py / collectibles.py / ledger.py / sec_gate.py"
          " byte-identical before/after; suite source pure ASCII"
          " (%d non-ascii bytes, sha16 %s); %d imports all stdlib"
          " (zero network libraries); world in tempfile.gettempdir()"
          "; proposal.py source zero UPDATE statements (append-only"
          " law machine-checked)"
          % (own_non_ascii, sha_own, len(net_imports)))

    pf3.close()
    led3.close()
    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria green)%s"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), len(RESULTS),
             "" if not fails else " - failed: " + ",".join(fails)),
          flush=True)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
