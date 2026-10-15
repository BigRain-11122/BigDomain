"""Acceptance suite: proposal progress_board cross-restart
persistence example window (BigDomain R1995; canon = explore-queue
progress_board persist line, the R1994-reseed consume-1/reseed-1
head). The progress face (R1968) is a dense-registry pure-read
derivation: one row per registered proposal, progress saturates
at 100.0 once the bar is crossed while the raw signature_count
and the qualified flag ride every row (an overshoot stays
visible), remaining counts the signatures still needed. Sort
keys are the rounded progress descending with proposal id
ascending as the tie-break.

Asserts the pre-registered criteria AC-PBP1..AC-PBP7 from the
R1995 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim rulings
(three, registered at claim time):
1. restart carrier = the full stack: ProposalFace close ->
   Ledger close, then a fresh Ledger (same db_path, same cfg
   bytes) + CollectiblesFace + stateless SecGate + ProposalFace
   (same pp_path) reopen.
2. world = six proposals in mixed ai labels: gamma overshoot
   5/3 (saturated), alpha 2/3, epsilon/eta a rounded-progress
   tie pair at 50.0, beta 1/4, delta a zero-signature dense row;
   no frozen clock is needed because the board rows carry no
   timestamps.
3. comparison face = dumps(sort_keys=True) byte equality on the
   progress board; the mirror-SQL third path re-derives the
   order from the two tables alone (R1729/R1992 mirror law).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_proposal_progresspersist.py
"""

import hashlib
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

import ledger as L                     # noqa: E402 (P-47-2b core)
import collectibles as C              # noqa: E402 (owner face)
import proposal as P                  # noqa: E402 (face under test)
from sec_gate import SecGate          # noqa: E402 (lobby product)

EXPECTED = 7
RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the co-signature"
              " progress board is a civic display feature, not"
              " investment advice")

ROW_KEYS = {"proposal_id", "title", "signature_count", "threshold",
            "remaining", "progress_pct", "qualified", "ai_label"}
ENV_KEYS = {"progress_board", "disclaimer"}

ORDER_PRE = ["gamma-pet", "alpha-pet", "epsilon-pet", "eta-pet",
             "beta-pet", "delta-pet"]
ORDER_AFTER_BETA = ["gamma-pet", "alpha-pet", "beta-pet",
                    "epsilon-pet", "eta-pet", "delta-pet"]
ORDER_AFTER_ALPHA = ["alpha-pet", "gamma-pet", "beta-pet",
                     "epsilon-pet", "eta-pet", "delta-pet"]
ORDER_FINAL = ["alpha-pet", "gamma-pet", "beta-pet", "epsilon-pet",
               "eta-pet", "delta-pet", "zeta-pet"]

PRODUCT_FILES = [
    os.path.join(BASE, "proposal.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def rows_of(pf):
    return pf.progress_board()["progress_board"]


def board_dumps(pf):
    return dumps(pf.progress_board())


def row_map(pf):
    return {r["proposal_id"]: dumps(r) for r in rows_of(pf)}


def mirror_order(pp_path):
    """Mirror-SQL third path (R1729/R1992 mirror law): re-derive
    the board order from the two tables alone using the same
    rounded-progress descending / id ascending key."""
    uri = "file:" + pp_path.replace("\\", "/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    rows = conn.execute(
        "SELECT p.proposal_id FROM proposals p LEFT JOIN"
        " (SELECT proposal_id, COUNT(*) AS cnt FROM"
        "  proposal_signs GROUP BY proposal_id) c"
        " ON c.proposal_id = p.proposal_id"
        " ORDER BY ROUND(MIN(COALESCE(c.cnt, 0), p.threshold)"
        " * 100.0 / p.threshold, 2) DESC, p.proposal_id ASC"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def table_counts(ppconn):
    return {"proposals": int(ppconn.execute(
                "SELECT COUNT(*) FROM proposals").fetchone()[0]),
            "proposal_signs": int(ppconn.execute(
                "SELECT COUNT(*) FROM proposal_signs").fetchone()[0])}


def build_world(led, cf, pf):
    for who in ("alice", "bob", "carol", "dave", "eve", "frank"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    pf.register_proposal("gamma-pet", "Gamma petition",
                         "grant the gamma garden a fountain",
                         "usr:carol", 10, 20, 3, False)
    pf.register_proposal("alpha-pet", "Alpha petition",
                         "name the alpha avenue after a poet",
                         "usr:alice", 10, 20, 3, False)
    pf.register_proposal("epsilon-pet", "Epsilon petition",
                         "light the epsilon entry hall",
                         "usr:dave", 10, 20, 2, False)
    pf.register_proposal("eta-pet", "Eta petition",
                         "plant trees along the eta embankment",
                         "usr:frank", 10, 20, 2, True)
    pf.register_proposal("beta-pet", "Beta petition",
                         "open the beta bridge at night",
                         "usr:bob", 10, 20, 4, True)
    pf.register_proposal("delta-pet", "Delta petition",
                         "dig the delta drainage canal",
                         "usr:eve", 10, 20, 5, True)
    for who, tick in (("alice", 11), ("bob", 12), ("dave", 13),
                      ("eve", 14), ("frank", 15)):
        pf.sign_proposal("usr:" + who, "gamma-pet", tick)
    pf.sign_proposal("usr:bob", "alpha-pet", 11)
    pf.sign_proposal("usr:carol", "alpha-pet", 12)
    pf.sign_proposal("usr:eve", "epsilon-pet", 11)
    pf.sign_proposal("usr:alice", "eta-pet", 11)
    pf.sign_proposal("usr:carol", "beta-pet", 11)


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="proposal-progresspersist-")
    db_path = os.path.join(tmp, "ledger.db")
    pp_path = os.path.join(tmp, "proposal.db")
    hyg = {}
    led = pf = led2 = pf2 = led3 = pf3 = None
    ppconn = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        pf = P.ProposalFace(cf, gate, DISCLAIMER, pp_path)
        build_world(led, cf, pf)
        ppconn = sqlite3.connect(pp_path)

        # -- AC-PBP1 world + pre-close board ----------------------
        env = pf.progress_board()
        direct = rows_of(pf)
        ok_env = (set(env.keys()) == ENV_KEYS
                  and env["disclaimer"] == DISCLAIMER
                  and all(set(r.keys()) == ROW_KEYS for r in direct))
        gamma = next(r for r in direct
                     if r["proposal_id"] == "gamma-pet")
        alpha = next(r for r in direct
                     if r["proposal_id"] == "alpha-pet")
        beta = next(r for r in direct
                    if r["proposal_id"] == "beta-pet")
        delta = next(r for r in direct
                    if r["proposal_id"] == "delta-pet")
        ok_sat = (gamma["signature_count"] == 5
                  and gamma["progress_pct"] == 100.0
                  and gamma["remaining"] == 0
                  and gamma["qualified"] is True
                  and gamma["ai_label"] == 0)
        ok_math = (alpha["progress_pct"] == 66.67
                   and alpha["remaining"] == 1
                   and alpha["qualified"] is False
                   and beta["progress_pct"] == 25.0
                   and beta["remaining"] == 3
                   and beta["ai_label"] == 1)
        ok_zero = (delta["signature_count"] == 0
                   and delta["progress_pct"] == 0.0
                   and delta["remaining"] == 5
                   and delta["qualified"] is False)
        ok_order = ([r["proposal_id"] for r in direct]
                    == ORDER_PRE)
        ok_mirror = mirror_order(pp_path) == ORDER_PRE
        ok_double = (board_dumps(pf) == board_dumps(pf)
                     and dumps(env) == dumps(pf.progress_board()))
        record("AC-PBP1",
               ok_env and ok_sat and ok_math and ok_zero
               and ok_order and ok_mirror and ok_double,
               "envelope keys=%s row keys=%s gamma overshoot"
               " saturated (count 5 honest, 100.0, remaining 0)"
               "=%s alpha 66.67/rem1 + beta 25.0/rem3=%s delta"
               " dense zero row=%s order pre=%s"
               " mirror-SQL==order=%s double-read"
               " byte-stable=%s"
               % (set(env.keys()) == ENV_KEYS,
                  all(set(r.keys()) == ROW_KEYS for r in direct),
                  ok_sat, ok_math, ok_zero, ok_order, ok_mirror,
                  ok_double))

        # -- AC-PBP2 cross-restart byte identity --------------------
        pre = board_dumps(pf)
        pf.close()
        led.close()
        pf = led = None
        led2 = L.Ledger(db_path, cfg)
        cf2 = C.CollectiblesFace(led2)
        gate2 = SecGate.from_config(lobby_cfg)
        pf2 = P.ProposalFace(cf2, gate2, DISCLAIMER, pp_path)
        post = board_dumps(pf2)
        double2 = (board_dumps(pf2) == post
                   and board_dumps(pf2) == pre)
        record("AC-PBP2", post == pre and double2,
               "full-stack close (proposal -> ledger) then"
               " rebuild on same paths + same cfg bytes:"
               " progress_board byte-identical=%s double-read"
               " self-stable=%s"
               % (post == pre, double2))

        # -- AC-PBP3 post-restart new-signature liveness ------------
        frozen3 = row_map(pf2)
        r3 = pf2.sign_proposal("usr:eve", "beta-pet", 15)
        rows3 = rows_of(pf2)
        beta3 = next(x for x in rows3
                     if x["proposal_id"] == "beta-pet")
        frozen_now = row_map(pf2)
        ok_frozen3 = all(frozen_now[sid] == frozen3[sid]
                         for sid in frozen3
                         if sid != "beta-pet")
        record("AC-PBP3",
               r3["signature_count"] == 2
               and r3["qualified"] is False
               and beta3["progress_pct"] == 50.0
               and beta3["remaining"] == 2
               and beta3["signature_count"] == 2
               and [x["proposal_id"] for x in rows3]
               == ORDER_AFTER_BETA
               and ok_frozen3,
               "post-restart signature: beta 1/4 -> 2/4"
               " zero-cache recompute 25.0->50.0=%s remaining"
               " 3->2=%s receipt count 2=%s order %s=%s"
               " untouched rows byte-frozen=%s"
               % (beta3["progress_pct"] == 50.0,
                  beta3["remaining"] == 2,
                  r3["signature_count"] == 2,
                  [x["proposal_id"] for x in rows3],
                  ORDER_AFTER_BETA, ok_frozen3))

        # -- AC-PBP4 post-restart threshold crossing + overshoot ---
        r4 = pf2.sign_proposal("usr:dave", "alpha-pet", 13)
        rows4 = rows_of(pf2)
        alpha4 = next(x for x in rows4
                      if x["proposal_id"] == "alpha-pet")
        ok_cross = (r4["signature_count"] == 3
                    and r4["qualified"] is True
                    and r4["memorial"] == "issued"
                    and alpha4["progress_pct"] == 100.0
                    and alpha4["remaining"] == 0
                    and alpha4["qualified"] is True)
        r4b = pf2.sign_proposal("usr:frank", "alpha-pet", 14)
        rows4b = rows_of(pf2)
        alpha4b = next(x for x in rows4b
                      if x["proposal_id"] == "alpha-pet")
        ok_over = (r4b["signature_count"] == 4
                   and r4b["qualified"] is True
                   and r4b["memorial"] is None
                   and alpha4b["progress_pct"] == 100.0
                   and alpha4b["remaining"] == 0
                   and alpha4b["signature_count"] == 4)
        ok_tie = ([x["proposal_id"] for x in rows4b]
                  == ORDER_AFTER_ALPHA)
        record("AC-PBP4", ok_cross and ok_over and ok_tie,
               "crossing sign: receipt qualified/memorial"
               " issued/100.0/remaining 0=%s overshoot sign:"
               " saturated 100.0, remaining 0, count 4 honest,"
               " memorial None=%s 100.0 tie id-asc alpha first"
               "=%s"
               % (ok_cross, ok_over, ok_tie))

        # -- AC-PBP5 post-restart new registration ------------------
        pre5 = row_map(pf2)
        reg5 = pf2.register_proposal(
            "zeta-pet", "Zeta petition",
            "install zeta zone night lamps", "usr:eve",
            10, 20, 5, False)
        rows5 = rows_of(pf2)
        zeta = next(x for x in rows5
                    if x["proposal_id"] == "zeta-pet")
        frozen5 = row_map(pf2)
        ok_frozen5 = all(frozen5[sid] == pre5[sid]
                         for sid in pre5)
        record("AC-PBP5",
               reg5["signature_count"] == 0
               and reg5["qualified"] is False
               and zeta["signature_count"] == 0
               and zeta["progress_pct"] == 0.0
               and zeta["remaining"] == 5
               and zeta["qualified"] is False
               and zeta["ai_label"] == 0
               and [x["proposal_id"] for x in rows5]
               == ORDER_FINAL
               and ok_frozen5,
               "post-restart registration: zeta dense row honest"
               " zeros (0/5, 0.0, remaining 5, unqualified)=%s"
               " old rows byte-frozen=%s 0.0 tie id-asc delta"
               " before zeta=%s"
               % (zeta["progress_pct"] == 0.0, ok_frozen5,
                  [x["proposal_id"] for x in rows5]
                  == ORDER_FINAL))

        # -- AC-PBP6 third instance + pure-read law -----------------
        final6 = board_dumps(pf2)
        counts6a = table_counts(ppconn)
        pf2.close()
        led2.close()
        pf2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        cf3 = C.CollectiblesFace(led3)
        gate3 = SecGate.from_config(lobby_cfg)
        pf3 = P.ProposalFace(cf3, gate3, DISCLAIMER, pp_path)
        third = board_dumps(pf3)
        seq3 = (board_dumps(pf3) == third
                and third == final6)
        counts6b = table_counts(ppconn)
        battery_a = [board_dumps(pf3), board_dumps(pf3),
                     board_dumps(pf3)]
        battery_b = [board_dumps(pf3), board_dumps(pf3),
                     board_dumps(pf3)]
        counts6c = table_counts(ppconn)
        method_src = inspect.getsource(
            P.ProposalFace.progress_board)
        write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                                  "CREATE ", "ALTER ")
                      if w in method_src]
        ok6 = (counts6a == counts6b == counts6c
               and battery_a == battery_b
               and not write_hits
               and "random" not in method_src)
        record("AC-PBP6", ok6,
               "third instance == second-instance final state"
               " byte-identical=%s sequential double-read=%s"
               " counts flat across read battery %s==%s==%s"
               " progress_board source zero write statements"
               " (%s) zero RNG"
               % (third == final6, seq3, counts6a, counts6b,
                  counts6c, write_hits))
        pf3.close()
        led3.close()
        pf3 = led3 = None

        # -- AC-PBP7 hygiene ----------------------------------------
        with open(os.path.abspath(__file__), "rb") as handle:
            own_bytes = handle.read()
        ascii_ok = all(b < 128 for b in own_bytes)
        net_ok = True
        for line in own_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith(
                    "from "):
                if any(w in stripped for w in
                       ("urllib", "requests", "socket", "http")):
                    net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ("ledger-proposal-progresspersist" in reg_src
                  and "test_proposal_progresspersist.py"
                  in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1
        outside = tmp not in os.path.abspath(BASE)
        hyg = {"ascii_ok": ascii_ok, "net_ok": net_ok,
               "reg_ok": reg_ok, "expected_ok": expected_ok,
               "outside": outside}
    finally:
        for obj in (pf, led, pf2, led2, pf3, led3):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
        if ppconn is not None:
            ppconn.close()

    post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    sha_ok = pre_sha == post_sha
    record("AC-PBP7",
           hyg.get("ascii_ok") and hyg.get("net_ok")
           and hyg.get("reg_ok") and hyg.get("expected_ok")
           and hyg.get("outside") and sha_ok,
           "suite pure ASCII=%s net-clean=%s registry-wired=%s"
           " world outside repo=%s product-sha stable=%s"
           % (hyg.get("ascii_ok"), hyg.get("net_ok"),
              hyg.get("reg_ok"), hyg.get("outside"), sha_ok))

    ok_all = len(RESULTS) == EXPECTED and all(
        ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
