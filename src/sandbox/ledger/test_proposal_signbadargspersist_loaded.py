"""Acceptance suite: proposal sign-side bad-args gate family
loaded-world cross-restart same-code example window (BigDomain
R2068; canon = the explore-queue proposal sign-side loaded-world
claim row, the R2041 reseed successor).

Family posture: R2041 pinned the sign-side three-shape argument
gate family (account shape, proposal id shape, tick shape) on a
ZERO-REGISTRATION boundary world, where every probe necessarily
lands before any registry read. This window pins the complement:
the same family on a LOADED world (proposals registered and
already signed), where the shape gates have live business gates
behind them - window, self-sign and duplicate-sign. The battery
therefore grows two mechanical proofs:

  - the bad-args-before-{window,self,dup} ordering law: on a
    known proposal id every shape violation still answers
    E_PP_BAD_ARGS, never E_PP_WINDOW / E_PP_SELF_SIGN /
    E_PP_DUP_SIGN;
  - the three business gates stay REACHABLE (not masked by the
    shape gates): exactly one probe each answers DUP_SIGN,
    WINDOW and SELF_SIGN.

An ordered 15-probe battery (1 well-formed control on a ghost id
reaching the unknown branch, 11 shape probes on the KNOWN ids,
3 orthogonal business-gate probes) rejects with the identical
ordered code vector on instances one/two/three across two
full-stack restarts, every batch leaves the registry row counts
and all four read faces byte-identical, the loaded qualified
state never flips, and the window stays zero-token with zero
phantom memorial awards.

Asserts the pre-registered criteria AC-PSL1..AC-PSL7 from the
R2068 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_proposal_signbadargspersist_loaded.py
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
PP_A = "pp-alpha"
PP_B = "pp-beta"


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
    """Four read faces on the loaded world, each one call, as a
    dict of serialized envelopes."""
    return {"view_a": dumps(pf.proposal_view(PP_A)),
            "view_b": dumps(pf.proposal_view(PP_B)),
            "board": dumps(pf.proposal_board()),
            "progress": dumps(pf.progress_board())}


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
    """The loaded-world sign-side battery: 15 ordered probes.

    1 control: well-formed args on a ghost id -> unknown branch.
    2..5: account shape (int, None, wrong prefix, bare) on the
          KNOWN id pp-alpha.
    6..7: proposal id shape (empty, None).
    8..12: tick shape (bool, str, negative, float, None) on the
          KNOWN id with a NON-signer account, so a valid tick
          would have succeeded - the BAD_ARGS answer is
          attributable to the shape gate alone.
    13..15: the three business gates behind the shape gates -
          duplicate signer, out-of-window tick, self sign.

    Every probe is a pure rejection - zero rows land."""
    out = []

    def expect(func, code):
        c, caught = probe(func, code)
        out.append((c, caught))

    expect(lambda: pf.sign_proposal(                # 1 control
        "usr:bob", GHOST, 5), P.E_PP_UNKNOWN_PROPOSAL)
    expect(lambda: pf.sign_proposal(                # 2 account int
        123, PP_A, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 3 account None
        None, PP_A, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 4 bad prefix
        "notusr:bob", PP_A, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 5 bare account
        "bob", PP_A, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 6 empty id
        "usr:dave", "", 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 7 None id
        "usr:dave", None, 5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 8 tick bool
        "usr:dave", PP_A, True), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 9 tick str
        "usr:dave", PP_A, "11"), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 10 tick < 0
        "usr:dave", PP_A, -1), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 11 tick float
        "usr:dave", PP_A, 1.5), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 12 tick None
        "usr:dave", PP_A, None), P.E_PP_BAD_ARGS)
    expect(lambda: pf.sign_proposal(                # 13 dup signer
        "usr:bob", PP_A, 7), P.E_PP_DUP_SIGN)
    expect(lambda: pf.sign_proposal(                # 14 outside
        "usr:dave", PP_A, 150), P.E_PP_WINDOW)
    expect(lambda: pf.sign_proposal(                # 15 self sign
        "usr:alice", PP_A, 5), P.E_PP_SELF_SIGN)
    codes = [c for c, _caught in out]
    all_expected = all(caught for _c, caught in out)
    return codes, all_expected


def expected_vector():
    """The pinned expected ordered code vector: 1 control UNKNOWN,
    11 shape BAD_ARGS, then the three orthogonal business gates."""
    return ([P.E_PP_UNKNOWN_PROPOSAL]
            + [P.E_PP_BAD_ARGS] * 11
            + [P.E_PP_DUP_SIGN, P.E_PP_WINDOW, P.E_PP_SELF_SIGN])


def build_world():
    """Register two proposals and land three signs through the real
    product path (no raw inserts): pp-alpha (alice, window 0..100,
    threshold 3) signed by bob@5 and carol@6; pp-beta (bob, window
    10..50, threshold 2) signed by alice@20."""
    return [
        dict(proposal_id=PP_A, title="extend the night bus",
             body="more routes after midnight", proposer="usr:alice",
             start_tick=0, end_tick=100, threshold=3,
             ai_generated=False),
        dict(proposal_id=PP_B, title="open a rooftop garden",
             body="green the upper decks", proposer="usr:bob",
             start_tick=10, end_tick=50, threshold=2,
             ai_generated=False),
    ], [
        ("usr:bob", PP_A, 5),
        ("usr:carol", PP_A, 6),
        ("usr:alice", PP_B, 20),
    ]


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="proposal-signbadargs-loaded-")
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
        for who in ("alice", "bob", "carol", "dave"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        cf.issue_certificate("usr:alice", "signbadargs-loaded-seed:2026",
                             "loaded-cert")
        regs, signs = build_world()
        for row in regs:
            pf.register_proposal(**row)
        sign_echoes = [pf.sign_proposal(a, p, t) for a, p, t in signs]
        ppconn = sqlite3.connect(pp_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-PSL1 loaded-world control anchor ------------------
        counts0 = table_counts(ppconn)
        view_a = pf.proposal_view(PP_A)
        view_b = pf.proposal_view(PP_B)
        benv = pf.proposal_board()
        penv = pf.progress_board()
        ok_counts = counts0 == {"proposals": 2, "proposal_signs": 3}
        ok_views = (view_a["signature_count"] == 2
                    and view_a["threshold"] == 3
                    and view_a["qualified"] is False
                    and view_b["signature_count"] == 1
                    and view_b["threshold"] == 2
                    and view_b["qualified"] is False)
        ok_keys = (set(view_a.keys())
                   == {"proposal_id", "title", "body", "proposer",
                       "window", "threshold", "signature_count",
                       "qualified", "signers", "ai_label",
                       "disclaimer"}
                   and set(benv.keys()) == {"proposals", "disclaimer"}
                   and set(penv.keys())
                   == {"progress_board", "disclaimer"})
        fam1 = read_family(pf)
        ok_double = fam1 == read_family(pf)
        ok_sign_echo = (sign_echoes[0]["signature_count"] == 1
                        and sign_echoes[1]["signature_count"] == 2
                        and sign_echoes[2]["signature_count"] == 1
                        and sign_echoes[2]["qualified"] is False)
        record("AC-PSL1",
               ok_counts and ok_views and ok_keys and ok_double
               and ok_sign_echo,
               "loaded world built through the real product path:"
               " two proposals, three signs, counts=%s"
               " pp-alpha 2/3 unqualified + pp-beta 1/2"
               " unqualified=%s envelope key sets pinned=%s"
               " four-face double-read stable=%s sign echoes=%s"
               % (counts0, ok_views, ok_keys, ok_double,
                  [e["signature_count"] for e in sign_echoes]))

        # -- AC-PSL2 instance-one baseline battery ----------------
        pre_env1 = read_family(pf)
        before = table_counts(ppconn)
        codes, caught = battery(pf)
        after = table_counts(ppconn)
        post_env1 = read_family(pf)
        v1 = json.dumps(codes)
        pinned = expected_vector()
        ok2 = (caught and codes == pinned and before == after
               and pre_env1 == post_env1)
        record("AC-PSL2", ok2,
               "instance-one loaded baseline: 15 ordered probes"
               " all-expected=%s codes==pinned vector (1 control"
               " UNKNOWN + 11 BAD_ARGS + DUP/WINDOW/SELF)=%s"
               " counts flat %s==%s four faces unchanged across"
               " the batch=%s V1=%s"
               % (caught, codes == pinned, before, after,
                  pre_env1 == post_env1, v1))

        # -- AC-PSL3 instance-2 same-code, first restart ----------
        pre_fam = read_family(pf)
        pf.close()
        led.close()
        pf = led = None
        led2 = L.Ledger(db_path, cfg)
        cf2 = C.CollectiblesFace(led2)
        gate2 = SecGate.from_config(lobby_cfg)
        pf2 = P.ProposalFace(cf2, gate2, DISCLAIMER, pp_path)
        pre_env2 = read_family(pf2)
        before2 = table_counts(ppconn)
        codes2, caught2 = battery(pf2)
        after2 = table_counts(ppconn)
        post_env2 = read_family(pf2)
        v2 = json.dumps(codes2)
        ok3 = (caught2 and codes2 == pinned and v2 == v1
               and before2 == after2
               and pre_env2 == post_env2 and pre_env2 == pre_fam
               and pre_env2 == read_family(pf2))
        record("AC-PSL3", ok3,
               "full-stack close (proposal -> ledger) + rebuild on"
               " same paths + same cfg bytes: battery V2==V1"
               " byte-identical=%s all-expected=%s"
               " codes==pinned=%s counts flat %s==%s loaded"
               " four faces == pre-close snapshot=%s"
               " batch-stable=%s double-read stable=%s"
               % (v2 == v1, caught2, codes2 == pinned, before2,
                  after2, pre_env2 == pre_fam,
                  pre_env2 == post_env2,
                  pre_env2 == read_family(pf2)))

        # -- AC-PSL4 instance-3 same-code, second restart ---------
        final_fam2 = read_family(pf2)
        pf2.close()
        led2.close()
        pf2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        cf3 = C.CollectiblesFace(led3)
        gate3 = SecGate.from_config(lobby_cfg)
        pf3 = P.ProposalFace(cf3, gate3, DISCLAIMER, pp_path)
        pre_env3 = read_family(pf3)
        before3 = table_counts(ppconn)
        codes3, caught3 = battery(pf3)
        after3 = table_counts(ppconn)
        post_env3 = read_family(pf3)
        v3 = json.dumps(codes3)
        ok4 = (caught3 and codes3 == pinned and v3 == v1
               and before3 == after3
               and pre_env3 == post_env3
               and pre_env3 == final_fam2
               and pre_env3 == read_family(pf3))
        record("AC-PSL4", ok4,
               "second full-stack close + rebuild (instance"
               " three): battery V3==V1 byte-identical=%s"
               " all-expected=%s codes==pinned=%s counts flat"
               " %s==%s loaded four faces == instance-two final"
               " byte-identical=%s batch-stable=%s double-read"
               " stable=%s"
               % (v3 == v1, caught3, codes3 == pinned, before3,
                  after3, pre_env3 == final_fam2,
                  pre_env3 == post_env3,
                  pre_env3 == read_family(pf3)))

        # -- AC-PSL5 loaded-world gate ordering law ---------------
        shape_on_known = codes[1:12]
        ok_shape = all(c == P.E_PP_BAD_ARGS for c in shape_on_known)
        ok_business = (codes[12] == P.E_PP_DUP_SIGN
                       and codes[13] == P.E_PP_WINDOW
                       and codes[14] == P.E_PP_SELF_SIGN)
        ok_codes_same = (codes == codes2 == codes3)
        ok_control = (codes[0] == P.E_PP_UNKNOWN_PROPOSAL
                      and codes3[0] == P.E_PP_UNKNOWN_PROPOSAL)
        record("AC-PSL5",
               ok_shape and ok_business and ok_codes_same
               and ok_control,
               "loaded-world ordering law: all 11 shape probes on"
               " the KNOWN id pp-alpha answer E_PP_BAD_ARGS and"
               " never WINDOW/SELF/DUP=%s (shape gates precede"
               " the three business gates); the three business"
               " gates stay reachable, each exactly once"
               " (DUP/WINDOW/SELF)=%s; the well-formed control"
               " still reaches the unknown branch=%s; the ordered"
               " vector is identical on instances one/two/three=%s"
               % (ok_shape, ok_business, ok_control, ok_codes_same))

        # -- AC-PSL6 zero token + zero phantom memorial -----------
        zero_token = (tx_count(ledconn) == 0
                      and cert_count(ledconn) == 1
                      and memorial_count(ledconn) == 0)
        final_a = pf3.proposal_view(PP_A)
        final_b = pf3.proposal_view(PP_B)
        ok_state = (final_a["signature_count"] == 2
                    and final_a["qualified"] is False
                    and final_b["signature_count"] == 1
                    and final_b["qualified"] is False
                    and table_counts(ppconn)
                    == {"proposals": 2, "proposal_signs": 3})
        record("AC-PSL6", zero_token and ok_state,
               "zero-token law: ledger_tx==%d across the whole"
               " window with exactly one boundary platform"
               " certificate=%s and zero phantom memorial"
               " awards=%s; the loaded qualified state never"
               " flips (pp-alpha 2/3 unqualified, pp-beta 1/2"
               " unqualified)=%s registry counts steady=%s"
               % (tx_count(ledconn), cert_count(ledconn) == 1,
                  memorial_count(ledconn) == 0, ok_state,
                  table_counts(ppconn)))
        pf3.close()
        led3.close()
        pf3 = led3 = None

        # -- AC-PSL7 hygiene --------------------------------------
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
        reg_ok = ("ledger-proposal-signbadargs-loadedpersist"
                  in reg_src
                  and "test_proposal_signbadargspersist_loaded.py"
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
    record("AC-PSL7",
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