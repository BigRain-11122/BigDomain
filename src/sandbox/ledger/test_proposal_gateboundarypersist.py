"""Acceptance suite: proposal gate family zero-registration
boundary world cross-restart same-code example window (BigDomain
R2040; canon = the explore-queue proposal gate-family boundary
claim row, the R2039 reseed). Family posture (the R2010 AC-SSZB /
R2028 AC-HYZG boundary gate-family cross-restart law): the R2011
AC-PBZB2 battery pinned the 8-probe write-side gate family on
the PRE-CLOSE instance of a zero-registration boundary world
only, and the R2039 AC-PPG successor pinned the same-code law on
a POPULATED registry world - this window closes the boundary
gap: the identical ordered 8-probe battery (R2011 AC-PBZB2 face,
zero added or removed probes) rejects with the identical ordered
code vector on the pre-close instance and on both full-stack
restart instances, every probe batch leaves both registry table
counts flat (gates fire before any read), the honest empty
envelopes stay byte-identical around every batch and across all
three instances (the boundary state survives the whole window,
zero phantom rows), and the window is zero-token end to end
with zero phantom memorial awards.

Asserts the pre-registered criteria AC-PBZG1..AC-PBZG7 from the
R2040 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim rulings
(two, registered at claim time): (1) world = the R2011 AC-PBZB1
boundary posture held for the whole window - four accounts plus
one platform certificate in the ledger domain, zero proposals
and zero signs on the registry axis, NO growth section (the
R2039 AC-PPG loaded-world growth face and the R2011 AC-PBZB4/5
post-restart first-registration chain are both already pinned;
this window keeps the R2028 AC-HYZG pure-boundary three-instance
form); (2) same-code verdict = the ordered 8-probe (probe, code)
vector JSON serialization byte-equal across instances one/two/
three over two full-stack restarts.

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_proposal_gateboundarypersist.py
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

import ledger as L                     # noqa: E402 (P-47-2b core)
import collectibles as C              # noqa: E402 (owner face)
import proposal as P                  # noqa: E402 (face under test)
from sec_gate import SecGate          # noqa: E402 (lobby product)

EXPECTED = 7
RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the co-signature"
              " registry is a civic feature, not investment"
              " advice")

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


def read_family(pf):
    """The two zero-param read faces, each one call, as a dict.
    The boundary world carries no proposal id, so the view face
    has no reachable object - the family is the two board
    faces."""
    return {"progress": dumps(pf.progress_board()),
            "board": dumps(pf.proposal_board())}


def table_counts(ppconn):
    return {"proposals": int(ppconn.execute(
                "SELECT COUNT(*) FROM proposals").fetchone()[0]),
            "proposal_signs": int(ppconn.execute(
                "SELECT COUNT(*) FROM proposal_signs").fetchone()[0])}


def cert_count(ledconn):
    return int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles"
        " WHERE kind = 'certificate'").fetchone()[0])


def memorial_count(ledconn):
    return int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles"
        " WHERE event_ref LIKE 'proposal-memorial:%'"
    ).fetchone()[0])


def tx_count(ledconn):
    return int(ledconn.execute(
        "SELECT COUNT(*) FROM ledger_tx").fetchone()[0])


def probe(func, expected_code):
    """Run one rejection probe; return (code, caught)."""
    try:
        func()
        return (None, False)
    except P.ProposalError as exc:
        return (exc.code, exc.code == expected_code)


def battery(pf, bad_word):
    """The R2011 AC-PBZB2 8-probe pure-rejection battery,
    identical order and args (zero probes added or removed).
    Returns (codes, all_expected). Every probe is a pure
    rejection - zero rows land; probes reference only ghost
    ids (ghost-pet / x-pet / badword-pet), never a live row."""
    out = []

    def expect(func, code):
        c, caught = probe(func, code)
        out.append((c, caught))

    expect(lambda: pf.sign_proposal(                        # 1
        "usr:bob", "ghost-pet", 5), P.E_PP_UNKNOWN_PROPOSAL)
    expect(lambda: pf.register_proposal(                     # 2
        "", "t", "b", "usr:alice", 10, 20, 3, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 3
        "x-pet", "", "b", "usr:alice", 10, 20, 3, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 4
        "x-pet", "t", "", "usr:alice", 10, 20, 3, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 5
        "x-pet", "t", "b", "notusr:alice", 10, 20, 3, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 6
        "x-pet", "t", "b", "usr:alice", 10, 20, 1, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 7
        "x-pet", "t", "b", "usr:alice", True, 20, 3, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 8
        "badword-pet", "title says " + bad_word, "clean body",
        "usr:alice", 10, 20, 3, False), P.E_PP_CONTENT_REJECTED)
    codes = [c for c, _caught in out]
    all_expected = all(caught for _c, caught in out)
    return codes, all_expected


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]

    tmp = tempfile.mkdtemp(prefix="proposal-gateboundary-")
    db_path = os.path.join(tmp, "ledger.db")
    pp_path = os.path.join(tmp, "proposal.db")
    hyg = {}
    led = pf = led2 = pf2 = led3 = pf3 = None
    ppconn = ledconn = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        pf = P.ProposalFace(cf, gate, DISCLAIMER, pp_path)
        # zero-registration boundary world (the R2011 AC-PBZB1
        # posture): ledger domain populated (four accounts + one
        # platform certificate), registry axis empty
        for who in ("alice", "bob", "carol", "dave"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        cf.issue_certificate("usr:alice", "gateboundary-seed:2026",
                             "boundary-cert")
        ppconn = sqlite3.connect(pp_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-PBZG1 zero-registration boundary control anchor --
        env = pf.progress_board()
        benv = pf.proposal_board()
        ok_env = (set(env.keys()) == {"progress_board", "disclaimer"}
                  and env["progress_board"] == []
                  and env["disclaimer"] == DISCLAIMER)
        ok_benv = (set(benv.keys()) == {"proposals", "disclaimer"}
                   and benv["proposals"] == []
                   and benv["disclaimer"] == DISCLAIMER)
        fam1 = read_family(pf)
        ok_double = fam1 == read_family(pf)
        ok_counts = (table_counts(ppconn)
                     == {"proposals": 0, "proposal_signs": 0})
        record("AC-PBZG1",
               ok_env and ok_benv and ok_double and ok_counts,
               "zero-registration boundary world (R2011 AC-PBZB1"
               " posture: ledger domain has four accounts + one"
               " platform certificate, registry axis empty):"
               " progress_board honest empty envelope=%s"
               " proposal_board honest empty envelope=%s"
               " family double-read byte-stable=%s counts=%s"
               % (ok_env, ok_benv, ok_double, table_counts(ppconn)))

        # -- AC-PBZG2 instance-one baseline battery --------------
        pre_env1 = read_family(pf)
        before = table_counts(ppconn)
        codes, caught = battery(pf, bad_word)
        after = table_counts(ppconn)
        post_env1 = read_family(pf)
        v1 = json.dumps(codes)
        ok2 = (caught and len(codes) == 8 and before == after
               and pre_env1 == post_env1)
        record("AC-PBZG2", ok2,
               "instance-one baseline (the R2011 AC-PBZB2"
               " 8-probe face, identical order and args): codes=%s"
               " all-expected=%s counts flat %s==%s envelope"
               " unchanged across the batch=%s V1 serialized=%s"
               % (codes, caught, before, after,
                  pre_env1 == post_env1, v1))

        # -- AC-PBZG3 instance-2 same-code, first restart ---------
        pre_fam = read_family(pf)
        pf.close()
        led.close()
        pf = led = None
        led2 = L.Ledger(db_path, cfg)
        cf2 = C.CollectiblesFace(led2)
        gate2 = SecGate.from_config(lobby_cfg)
        pf2 = P.ProposalFace(cf2, gate2, DISCLAIMER, pp_path)
        pre_env2 = read_family(pf2)
        before3 = table_counts(ppconn)
        codes2, caught2 = battery(pf2, bad_word)
        after3 = table_counts(ppconn)
        post_env2 = read_family(pf2)
        v2 = json.dumps(codes2)
        ok3 = (caught2 and v2 == v1 and before3 == after3
               and pre_env2 == post_env2 and pre_env2 == pre_fam
               and pre_env2 == read_family(pf2))
        record("AC-PBZG3", ok3,
               "full-stack close (proposal -> ledger) + rebuild"
               " on same paths + same cfg bytes (the R1995"
               " same-module full-stack law): battery V2==V1"
               " byte-identical=%s probes all-expected=%s"
               " counts flat %s==%s boundary envelope == pre-close"
               " snapshot byte-identical=%s batch-stable=%s"
               " sequential double-read stable=%s"
               % (v2 == v1, caught2, before3, after3,
                  pre_env2 == pre_fam, pre_env2 == post_env2,
                  pre_env2 == read_family(pf2)))

        # -- AC-PBZG4 instance-3 same-code, second restart --------
        final_fam2 = read_family(pf2)
        pf2.close()
        led2.close()
        pf2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        cf3 = C.CollectiblesFace(led3)
        gate3 = SecGate.from_config(lobby_cfg)
        pf3 = P.ProposalFace(cf3, gate3, DISCLAIMER, pp_path)
        pre_env3 = read_family(pf3)
        before4 = table_counts(ppconn)
        codes3, caught3 = battery(pf3, bad_word)
        after4 = table_counts(ppconn)
        post_env3 = read_family(pf3)
        v3 = json.dumps(codes3)
        ok4 = (caught3 and v3 == v1 and before4 == after4
               and pre_env3 == post_env3 and pre_env3 == final_fam2
               and pre_env3 == read_family(pf3))
        record("AC-PBZG4", ok4,
               "second full-stack close + rebuild (instance"
               " three): battery V3==V1 byte-identical=%s"
               " probes all-expected=%s counts flat %s==%s"
               " boundary envelope == instance-two final"
               " byte-identical=%s batch-stable=%s sequential"
               " double-read stable=%s - front-door gate family"
               " zero drift across both restarts"
               % (v3 == v1, caught3, before4, after4,
                  pre_env3 == final_fam2, pre_env3 == post_env3,
                  pre_env3 == read_family(pf3)))

        # -- AC-PBZG5 probes never perturb the boundary state ----
        ok_local = (pre_env1 == post_env1
                    and pre_env2 == post_env2
                    and pre_env3 == post_env3
                    and pre_env1 == read_family(pf3)
                    and pre_env2 == post_env1
                    and pre_env3 == post_env2)
        ok_cross = (pre_env1 == pre_env2 == pre_env3
                    == post_env1 == post_env2 == post_env3)
        ok_rows = (table_counts(ppconn)
                   == {"proposals": 0, "proposal_signs": 0})
        record("AC-PBZG5",
               ok_local and ok_cross and ok_rows,
               "probes never perturb the boundary state: on every"
               " instance the honest empty envelope replays"
               " byte-identical before the batch, after it, and"
               " across the double read (per-instance=%s); the"
               " envelope is byte-identical across all three"
               " instances (cross-instance=%s); registry axis row"
               " counts stay zero the whole window=%s (%s)"
               % (ok_local, ok_cross, ok_rows,
                  table_counts(ppconn)))

        # -- AC-PBZG6 cross-instance vector summary + zero token --
        vectors_same = (v1 == v2 == v3)
        keysets = (set(pf3.progress_board().keys())
                   == {"progress_board", "disclaimer"}
                   and set(pf3.proposal_board().keys())
                   == {"proposals", "disclaimer"})
        zero_token = (tx_count(ledconn) == 0
                      and cert_count(ledconn) == 1
                      and memorial_count(ledconn) == 0)
        record("AC-PBZG6",
               vectors_same and keysets and zero_token,
               "cross-instance same-code law: V1==V2==V3"
               " byte-identical=%s envelope key sets constant=%s"
               " zero-token law ledger_tx==%d with exactly one"
               " boundary platform certificate=%s and zero"
               " phantom memorial awards=%s (the ghost-sign"
               " probe never awards)"
               % (vectors_same, keysets, tx_count(ledconn),
                  cert_count(ledconn) == 1,
                  memorial_count(ledconn) == 0))
        pf3.close()
        led3.close()
        pf3 = led3 = None

        # -- AC-PBZG7 hygiene --------------------------------------
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
        reg_ok = ("ledger-proposal-gateboundary-persist"
                  in reg_src
                  and "test_proposal_gateboundarypersist.py"
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
        if ledconn is not None:
            ledconn.close()

    post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    sha_ok = pre_sha == post_sha
    record("AC-PBZG7",
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
