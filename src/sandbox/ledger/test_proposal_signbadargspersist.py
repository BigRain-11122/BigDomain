"""Acceptance suite: proposal sign-side bad-args gate family
cross-restart same-code example window (BigDomain R2041; canon =
the explore-queue proposal sign-side bad-args claim row, the
R2040 reseed). Family posture (the R2039 AC-PPG / R2040 AC-PBZG
gate-family cross-restart law): both predecessor batteries probe
the REGISTER-side argument gates and the sign-side UNKNOWN /
window / self / dup branches, but neither carries the sign-side
three-shape argument gate family (account shape, proposal id
shape, tick shape) - this window closes that gap on a
zero-registration boundary world: an ordered 12-probe battery
(one well-formed control probe that reaches the unknown branch,
eleven bad-args probes: four account-shape, two proposal-id-shape,
five tick-shape) rejects with the identical ordered code vector
on instances one/two/three across two full-stack restarts, the
control probe versus the bad-args probes is the mechanical proof
of the bad-args-before-unknown ordering law (the same unknown
id, well-formed args reach E_PP_UNKNOWN_PROPOSAL while every
shape violation returns E_PP_BAD_ARGS first), every probe batch
leaves both registry table counts flat (the shape gates fire
before any read), the honest empty envelopes stay byte-identical
around every batch and across all three instances, and the window
is zero-token end to end with zero phantom memorial awards.

Asserts the pre-registered criteria AC-PSG1..AC-PSG7 from the
R2041 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim rulings
(three, registered at claim time): (1) world = zero-registration
boundary world held for the whole window - four accounts plus
one platform certificate in the ledger domain, zero proposals
and zero signs on the registry axis (the sign-side bad-args
family rejects before any read, so the boundary world reaches
every probe; no growth section - R2039 pinned the loaded-world
growth face, R2040 pinned the boundary register-side family);
(2) probe vector = 12 ordered probes per instance (1 control +
11 bad-args); (3) same-code verdict = the ordered (probe, code)
vector JSON serialization byte-equal across instances one/two/
three over two full-stack restarts.

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_proposal_signbadargspersist.py
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

GHOST = "ghost-pet"


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


def battery(pf):
    """The sign-side bad-args 12-probe ordered battery: probe 1
    is the well-formed control (good account shape, known id
    shape, good tick shape, unknown proposal id - it reaches the
    unknown branch and returns E_PP_UNKNOWN_PROPOSAL, proving
    the unknown branch is reachable and that the bad-args codes
    in probes 2..12 are attributable to the shape gates firing
    FIRST); probes 2..5 are account-shape violations (int, None,
    wrong prefix, bare), probes 6..7 are proposal-id shape
    violations (empty, None), probes 8..12 are tick-shape
    violations (bool, str, negative int, float, None). Every
    probe is a pure rejection - zero rows land."""
    out = []

    def expect(func, code):
        c, caught = probe(func, code)
        out.append((c, caught))

    expect(lambda: pf.sign_proposal(                # 1 control
        "usr:bob", GHOST, 5), P.E_PP_UNKNOWN_PROPOSAL)
    expect(lambda: pf.sign_proposal(                # 2 account int
        123, GHOST, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 3 account None
        None, GHOST, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 4 bad prefix
        "notusr:bob", GHOST, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 5 bare account
        "bob", GHOST, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 6 empty id
        "usr:bob", "", 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 7 None id
        "usr:bob", None, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 8 tick bool
        "usr:bob", GHOST, True), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 9 tick str
        "usr:bob", GHOST, "11"), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 10 tick < 0
        "usr:bob", GHOST, -1), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 11 tick float
        "usr:bob", GHOST, 1.5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 12 tick None
        "usr:bob", GHOST, None), P.E_PP_BAD_ARGS)
    codes = [c for c, _caught in out]
    all_expected = all(caught for _c, caught in out)
    return codes, all_expected


def expected_vector():
    """The pinned expected ordered code vector (1 control
    UNKNOWN + 11 BAD_ARGS) - asserted literally against every
    instance's battery output."""
    return ([P.E_PP_UNKNOWN_PROPOSAL]
            + [P.E_PP_BAD_ARGS] * 11)


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="proposal-signbadargs-")
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
        cf.issue_certificate("usr:alice", "signbadargs-seed:2026",
                             "boundary-cert")
        ppconn = sqlite3.connect(pp_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-PSG1 zero-registration boundary control anchor --
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
        record("AC-PSG1",
               ok_env and ok_benv and ok_double and ok_counts,
               "zero-registration boundary world (R2011 AC-PBZB1"
               " posture: ledger domain has four accounts + one"
               " platform certificate, registry axis empty):"
               " progress_board honest empty envelope=%s"
               " proposal_board honest empty envelope=%s"
               " family double-read byte-stable=%s counts=%s"
               % (ok_env, ok_benv, ok_double, table_counts(ppconn)))

        # -- AC-PSG2 instance-one baseline battery --------------
        pre_env1 = read_family(pf)
        before = table_counts(ppconn)
        codes, caught = battery(pf)
        after = table_counts(ppconn)
        post_env1 = read_family(pf)
        v1 = json.dumps(codes)
        pinned = expected_vector()
        ok2 = (caught and codes == pinned and before == after
               and pre_env1 == post_env1)
        record("AC-PSG2", ok2,
               "instance-one baseline: 12 ordered sign-side"
               " probes all-expected=%s codes==pinned vector"
               " (1 control UNKNOWN + 11 BAD_ARGS)=%s counts"
               " flat %s==%s envelope unchanged across the"
               " batch=%s V1 serialized=%s"
               % (caught, codes == pinned, before, after,
                  pre_env1 == post_env1, v1))

        # -- AC-PSG3 instance-2 same-code, first restart ---------
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
        codes2, caught2 = battery(pf2)
        after3 = table_counts(ppconn)
        post_env2 = read_family(pf2)
        v2 = json.dumps(codes2)
        ok3 = (caught2 and codes2 == pinned and v2 == v1
               and before3 == after3
               and pre_env2 == post_env2 and pre_env2 == pre_fam
               and pre_env2 == read_family(pf2))
        record("AC-PSG3", ok3,
               "full-stack close (proposal -> ledger) + rebuild"
               " on same paths + same cfg bytes (the R1995"
               " same-module full-stack law): battery V2==V1"
               " byte-identical=%s probes all-expected=%s"
               " codes==pinned=%s counts flat %s==%s boundary"
               " envelope == pre-close snapshot"
               " byte-identical=%s batch-stable=%s sequential"
               " double-read stable=%s"
               % (v2 == v1, caught2, codes2 == pinned,
                  before3, after3,
                  pre_env2 == pre_fam, pre_env2 == post_env2,
                  pre_env2 == read_family(pf2)))

        # -- AC-PSG4 instance-3 same-code, second restart --------
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
        codes3, caught3 = battery(pf3)
        after4 = table_counts(ppconn)
        post_env3 = read_family(pf3)
        v3 = json.dumps(codes3)
        ok4 = (caught3 and codes3 == pinned and v3 == v1
               and before4 == after4
               and pre_env3 == post_env3 and pre_env3 == final_fam2
               and pre_env3 == read_family(pf3))
        record("AC-PSG4", ok4,
               "second full-stack close + rebuild (instance"
               " three): battery V3==V1 byte-identical=%s"
               " probes all-expected=%s codes==pinned=%s counts"
               " flat %s==%s boundary envelope == instance-two"
               " final byte-identical=%s batch-stable=%s"
               " sequential double-read stable=%s - sign-side"
               " shape gate family zero drift across both"
               " restarts"
               % (v3 == v1, caught3, codes3 == pinned,
                  before4, after4,
                  pre_env3 == final_fam2, pre_env3 == post_env3,
                  pre_env3 == read_family(pf3)))

        # -- AC-PSG5 probes never perturb the boundary state ----
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
        record("AC-PSG5",
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

        # -- AC-PSG6 ordering law + zero token -------------------
        control_ok = (codes[0] == P.E_PP_UNKNOWN_PROPOSAL
                      and codes3[0] == P.E_PP_UNKNOWN_PROPOSAL)
        badargs_ok = all(c == P.E_PP_BAD_ARGS for c in codes[1:])
        ghost_badargs = 9  # probes 2..5 (account) + 8..12 (tick)
        vectors_same = (v1 == v2 == v3)
        keysets = (set(pf3.progress_board().keys())
                   == {"progress_board", "disclaimer"}
                   and set(pf3.proposal_board().keys())
                   == {"proposals", "disclaimer"})
        zero_token = (tx_count(ledconn) == 0
                      and cert_count(ledconn) == 1
                      and memorial_count(ledconn) == 0)
        ordering = (control_ok and badargs_ok
                   and sum(1 for c in codes[1:] if c
                           == P.E_PP_BAD_ARGS) == 11)
        record("AC-PSG6",
               ordering and vectors_same and keysets
               and zero_token,
               "bad-args-before-unknown ordering law: the control"
               " probe (well-formed args, same unknown id %s)"
               " reaches E_PP_UNKNOWN_PROPOSAL=%s while all 11"
               " shape probes return E_PP_BAD_ARGS first=%s (%d"
               " of them on the same unknown id - the three shape"
               " gates precede the unknown lookup); V1==V2==V3"
               " byte-identical=%s envelope key sets constant=%s"
               " zero-token law ledger_tx==%d with exactly one"
               " boundary platform certificate=%s and zero"
               " phantom memorial awards=%s (ghost sign probes"
               " never award)"
               % (GHOST, control_ok, badargs_ok, ghost_badargs,
                  vectors_same, keysets, tx_count(ledconn),
                  cert_count(ledconn) == 1,
                  memorial_count(ledconn) == 0))
        pf3.close()
        led3.close()
        pf3 = led3 = None

        # -- AC-PSG7 hygiene --------------------------------------
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
        reg_ok = ("ledger-proposal-signbadargs-persist"
                  in reg_src
                  and "test_proposal_signbadargspersist.py"
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
    record("AC-PSG7",
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
