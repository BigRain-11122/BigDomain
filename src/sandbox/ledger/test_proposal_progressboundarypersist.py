"""Acceptance suite: proposal progress_board zero-registration
boundary world cross-restart example window (BigDomain R2011; canon
= explore-queue progress_board boundary-persist line, the R1995
reseed). Boundary posture (the R2010 AC-SSZB law): the ledger
domain carries data (accounts ensured, a platform certificate
awarded) while the proposal registry axis holds ZERO rows - the
read faces must keep honest empty envelopes byte-identical across
a full-stack restart, the write-side gate family still fires
before any read, and the post-restart first registration + first
signatures continue the boards with zero phantom rows, ending on
the threshold crossing where the memorial linkage re-proves the
collectibles dock reconnection from the boundary world.

Asserts the pre-registered criteria AC-PBZB1..AC-PBZB7 from the
R2011 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim rulings
(three, registered at claim time):
1. restart carrier = the R1995 same-module full-stack law:
   ProposalFace close -> Ledger close, then a fresh Ledger (same
   db_path, same cfg bytes) + CollectiblesFace + stateless SecGate
   + ProposalFace (same pp_path) reopen.
2. world = the boundary state: four accounts + one platform
   certificate in the ledger domain, zero proposals and zero
   signature rows - registry empty, adjacent domains populated.
3. comparison face = dumps(sort_keys=True) byte equality on both
   zero-param read faces (progress_board + proposal_board).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_proposal_progressboundarypersist.py
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


def progress_rows(pf):
    return pf.progress_board()["progress_board"]


def progress_dumps(pf):
    return dumps(pf.progress_board())


def registry_dumps(pf):
    return dumps(pf.proposal_board())


def table_counts(ppconn):
    return {"proposals": int(ppconn.execute(
                "SELECT COUNT(*) FROM proposals").fetchone()[0]),
            "proposal_signs": int(ppconn.execute(
                "SELECT COUNT(*) FROM proposal_signs").fetchone()[0])}


def probe(func, expected_code):
    """Run one rejection probe; return (code, caught)."""
    try:
        func()
        return (None, False)
    except P.ProposalError as exc:
        return (exc.code, exc.code == expected_code)


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="proposal-progressboundary-")
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
        # boundary world: ledger domain populated, registry axis
        # empty (the R2010 boundary posture)
        for who in ("alice", "bob", "carol", "dave"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        cf.issue_certificate("usr:alice", "boundary-seed:2026",
                            "boundary-cert")
        ppconn = sqlite3.connect(pp_path)

        # -- AC-PBZB1 zero-registration control anchor -----------
        env = pf.progress_board()
        penv = pf.proposal_board()
        ok_env = (set(env.keys()) == {"progress_board", "disclaimer"}
                  and env["progress_board"] == []
                  and env["disclaimer"] == DISCLAIMER)
        ok_penv = (set(penv.keys()) == {"proposals", "disclaimer"}
                   and penv["proposals"] == []
                   and penv["disclaimer"] == DISCLAIMER)
        ok_double = (progress_dumps(pf) == progress_dumps(pf)
                     and registry_dumps(pf) == registry_dumps(pf))
        ok_counts = (table_counts(ppconn)
                     == {"proposals": 0, "proposal_signs": 0})
        record("AC-PBZB1", ok_env and ok_penv and ok_double
               and ok_counts,
               "zero-reg boundary world (ledger domain has"
               " accounts + a certificate, registry axis empty):"
               " progress_board honest empty envelope=%s"
               " proposal_board honest empty envelope=%s"
               " double-read byte-stable=%s counts=%s"
               % (ok_env, ok_penv, ok_double, table_counts(ppconn)))

        # -- AC-PBZB2 gate family before any read -----------------
        bad_word = lobby_cfg["gate"]["forbidden_words"][0]
        before = table_counts(ppconn)
        p1 = probe(lambda: pf.sign_proposal(
            "usr:bob", "ghost-pet", 5), P.E_PP_UNKNOWN_PROPOSAL)
        p2 = probe(lambda: pf.register_proposal(
            "", "t", "b", "usr:alice", 10, 20, 3, False),
            P.E_PP_BAD_ARGS)
        p3 = probe(lambda: pf.register_proposal(
            "x-pet", "", "b", "usr:alice", 10, 20, 3, False),
            P.E_PP_BAD_ARGS)
        p4 = probe(lambda: pf.register_proposal(
            "x-pet", "t", "", "usr:alice", 10, 20, 3, False),
            P.E_PP_BAD_ARGS)
        p5 = probe(lambda: pf.register_proposal(
            "x-pet", "t", "b", "notusr:alice", 10, 20, 3, False),
            P.E_PP_BAD_ARGS)
        p6 = probe(lambda: pf.register_proposal(
            "x-pet", "t", "b", "usr:alice", 10, 20, 1, False),
            P.E_PP_BAD_ARGS)
        p7 = probe(lambda: pf.register_proposal(
            "x-pet", "t", "b", "usr:alice", True, 20, 3, False),
            P.E_PP_BAD_ARGS)
        p8 = probe(lambda: pf.register_proposal(
            "badword-pet", "title says " + bad_word, "clean body",
            "usr:alice", 10, 20, 3, False), P.E_PP_CONTENT_REJECTED)
        codes = [p[0] for p in (p1, p2, p3, p4, p5, p6, p7, p8)]
        caught = all(p[1] for p in (p1, p2, p3, p4, p5, p6, p7, p8))
        after = table_counts(ppconn)
        record("AC-PBZB2", caught and before == after,
               "zero-reg world gate family fires before any read:"
               " codes=%s all-expected=%s counts flat %s==%s"
               % (codes, caught, before, after))

        # -- AC-PBZB3 cross-restart byte identity -----------------
        pre_pb = progress_dumps(pf)
        pre_ppb = registry_dumps(pf)
        pf.close()
        led.close()
        pf = led = None
        led2 = L.Ledger(db_path, cfg)
        cf2 = C.CollectiblesFace(led2)
        gate2 = SecGate.from_config(lobby_cfg)
        pf2 = P.ProposalFace(cf2, gate2, DISCLAIMER, pp_path)
        post_pb = progress_dumps(pf2)
        post_ppb = registry_dumps(pf2)
        ok3 = (post_pb == pre_pb and post_ppb == pre_ppb
               and progress_dumps(pf2) == post_pb
               and registry_dumps(pf2) == post_ppb)
        record("AC-PBZB3", ok3,
               "full-stack close (proposal -> ledger) then rebuild"
               " on same paths + same cfg bytes: progress_board"
               " byte-identical=%s proposal_board byte-identical=%s"
               " double-read self-stable=%s"
               % (post_pb == pre_pb, post_ppb == pre_ppb, ok3))

        # -- AC-PBZB4 post-restart first registration -------------
        reg = pf2.register_proposal(
            "alpha-pet", "Alpha petition",
            "name the alpha avenue after a poet", "usr:alice",
            10, 20, 3, False)
        rows4 = progress_rows(pf2)
        alpha = rows4[0] if rows4 else {}
        ok_keys = (len(rows4) == 1
                   and set(alpha.keys()) == ROW_KEYS)
        ok_zeros = (alpha.get("proposal_id") == "alpha-pet"
                    and alpha.get("signature_count") == 0
                    and alpha.get("threshold") == 3
                    and alpha.get("remaining") == 3
                    and alpha.get("progress_pct") == 0.0
                    and alpha.get("qualified") is False
                    and alpha.get("ai_label") == 0)
        ok_receipt = (reg["signature_count"] == 0
                      and reg["qualified"] is False
                      and reg["ai_label"] == 0)
        ok_phantom = ([r["proposal_id"] for r in rows4]
                      == ["alpha-pet"]
                      and table_counts(ppconn)["proposals"] == 1)
        ok_live = progress_dumps(pf2) != post_pb
        penv4 = pf2.proposal_board()["proposals"]
        ok_echo = (len(penv4) == 1
                   and penv4[0]["proposal_id"] == "alpha-pet")
        record("AC-PBZB4",
               ok_keys and ok_zeros and ok_receipt and ok_phantom
               and ok_live and ok_echo,
               "post-restart first registration: one dense honest"
               " zero row (0/3, 0.0, remaining 3, unqualified,"
               " ai 0)=%s receipt echo=%s row-set==registry-set"
               " (zero phantom)=%s empty-snapshot -> live=%s"
               " proposal_board single-row echo=%s"
               % (ok_zeros, ok_receipt, ok_phantom, ok_live,
                  ok_echo))

        # -- AC-PBZB5 first-sign chain + memorial continuation -----
        r1 = pf2.sign_proposal("usr:bob", "alpha-pet", 11)
        a1 = progress_rows(pf2)[0]
        r2 = pf2.sign_proposal("usr:carol", "alpha-pet", 12)
        a2 = progress_rows(pf2)[0]
        r3 = pf2.sign_proposal("usr:dave", "alpha-pet", 13)
        a3 = progress_rows(pf2)[0]
        ok_s1 = (r1["signature_count"] == 1
                 and r1["memorial"] is None
                 and r1["qualified"] is False
                 and a1["progress_pct"] == 33.33
                 and a1["remaining"] == 2)
        ok_s2 = (r2["signature_count"] == 2
                 and r2["memorial"] is None
                 and a2["progress_pct"] == 66.67
                 and a2["remaining"] == 1)
        ok_s3 = (r3["signature_count"] == 3
                 and r3["qualified"] is True
                 and r3["memorial"] == "issued"
                 and a3["progress_pct"] == 100.0
                 and a3["remaining"] == 0
                 and a3["qualified"] is True)
        certs = cf2.collection("usr:alice")["certificates"]
        memorial_certs = [c for c in certs
                          if c["event_ref"]
                          == "proposal-memorial:alpha-pet"]
        ok_memorial = (len(memorial_certs) == 1
                       and memorial_certs[0]["item_id"]
                       == "proposal-memorial")
        record("AC-PBZB5",
               ok_s1 and ok_s2 and ok_s3 and ok_memorial,
               "post-restart sign chain: sign1 33.33/rem2"
               " memorial-None=%s sign2 66.67/rem1=%s sign3"
               " crossing 100.0/rem0 qualified memorial"
               " issued=%s collectibles dock reconnected:"
               " proposer certificate event_ref"
               " proposal-memorial:alpha-pet exactly one=%s"
               % (ok_s1, ok_s2, ok_s3, ok_memorial))

        # -- AC-PBZB6 third instance + pure-read law ---------------
        final_pb = progress_dumps(pf2)
        final_ppb = registry_dumps(pf2)
        counts6a = table_counts(ppconn)
        pf2.close()
        led2.close()
        pf2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        cf3 = C.CollectiblesFace(led3)
        gate3 = SecGate.from_config(lobby_cfg)
        pf3 = P.ProposalFace(cf3, gate3, DISCLAIMER, pp_path)
        third_pb = progress_dumps(pf3)
        third_ppb = registry_dumps(pf3)
        seq3 = (progress_dumps(pf3) == third_pb
                and registry_dumps(pf3) == third_ppb
                and third_pb == final_pb and third_ppb == final_ppb)
        battery = [progress_dumps(pf3), progress_dumps(pf3),
                   registry_dumps(pf3), registry_dumps(pf3)]
        counts6b = table_counts(ppconn)
        method_src = inspect.getsource(
            P.ProposalFace.progress_board)
        write_hits = [w for w in ("INSERT", "DELETE", "UPDATE ",
                                  "CREATE ", "ALTER ")
                      if w in method_src]
        ok6 = (seq3 and counts6a == counts6b
               and battery[0] == battery[1]
               and battery[2] == battery[3]
               and not write_hits and "random" not in method_src)
        record("AC-PBZB6", ok6,
               "third instance == second-instance final state"
               " byte-identical (progress=%s registry=%s)"
               " sequential double-read self-stable=%s counts"
               " flat %s==%s progress_board source zero write"
               " statements (%s) zero RNG"
               % (third_pb == final_pb, third_ppb == final_ppb,
                  seq3, counts6a, counts6b, write_hits))
        pf3.close()
        led3.close()
        pf3 = led3 = None

        # -- AC-PBZB7 hygiene ---------------------------------------
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
        reg_ok = ("ledger-proposal-progressboundary-persist"
                  in reg_src
                  and "test_proposal_progressboundarypersist.py"
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
    record("AC-PBZB7",
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
