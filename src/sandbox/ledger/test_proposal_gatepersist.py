"""Acceptance suite: proposal register/sign write-side gate
family cross-restart same-code example window (BigDomain R2039;
canon = the explore-queue proposal gate-family claim row, the
R2011 reseed). Family posture (the R2035 AC-SGB / R2036 AC-SVW
same-code law): the R2011 AC-PBZB2 battery pinned the write-side
gate family on the pre-close instance of a zero-registration
boundary world only - this successor pins the SAME-CODE law on a
POPULATED registry world: the identical ordered 17-probe battery
rejects with the identical ordered code vector on instances
one/two/three across two full-stack restarts, every probe batch
leaves both table counts flat (gates fire before any read), the
post-restart real write path keeps the boards live with zero
phantom, and the battery stays same-code across that world
growth (world-growth invariance: probes reference the stable
gate-pet / ghost objects, never the liveness objects).

Asserts the pre-registered criteria AC-PPG1..AC-PPG7 from the
R2039 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim rulings
(three, registered at claim time): (1) world = populated
registry world (four accounts + one platform certificate in the
ledger domain, gate-pet registered with window 10..20 / threshold
3 / usr:alice proposer, bob already signed at tick 11 - the
dup-sign / self-sign / window probe preconditions); (2) probe
vector = 17 pure rejections proving the register_proposal gate
order (args -> content gate -> dup) and the sign_proposal gate
order (account shape -> tick shape -> unknown -> window -> self
-> dup) as the product's own code order; (3) same-code verdict =
the ordered (probe, code) vector JSON serialization byte-equal
across instances one/two/three over two full-stack restarts.

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_proposal_gatepersist.py
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
    """The three read faces, each one call, as a dict."""
    return {"progress": dumps(pf.progress_board()),
            "board": dumps(pf.proposal_board()),
            "view": dumps(pf.proposal_view("gate-pet"))}


def table_counts(ppconn):
    return {"proposals": int(ppconn.execute(
                "SELECT COUNT(*) FROM proposals").fetchone()[0]),
            "proposal_signs": int(ppconn.execute(
                "SELECT COUNT(*) FROM proposal_signs").fetchone()[0])}


def cert_count(ledconn):
    return int(ledconn.execute(
        "SELECT COUNT(*) FROM collectibles"
        " WHERE kind = 'certificate'").fetchone()[0])


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
    """The 17-probe pure-rejection battery. Returns (codes,
    all_expected). Every probe is a pure rejection - zero rows
    land. World-growth invariant: probes reference gate-pet and
    ghost ids plus the bob/alice preconditions, never the
    liveness objects."""
    out = []

    def expect(func, code):
        c, caught = probe(func, code)
        out.append((len(out) + 1, c, caught))

    # register-side (11): args gate -> content gate -> dup gate
    expect(lambda: pf.register_proposal(                     # 1
        "gate-pet", "t", "b", "usr:alice", 10, 20, 3, False),
        P.E_PP_DUP_PROPOSAL)
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
        "x-pet", "t", "b", "notusr:z", 10, 20, 3, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 6
        "x-pet", "t", "b", "usr:alice", 10, 20, 1, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 7
        "x-pet", "t", "b", "usr:alice", True, 20, 3, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 8
        "x-pet", "t", "b", "usr:alice", 20, 20, 3, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 9
        "x-pet", "t", "b", "usr:alice", 10, 20, 3, 2),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 10
        "x-pet", "title says " + bad_word, "clean body",
        "usr:alice", 10, 20, 1, False),
        P.E_PP_BAD_ARGS)
    expect(lambda: pf.register_proposal(                     # 11
        "x-pet", "title says " + bad_word, "clean body",
        "usr:alice", 10, 20, 3, False),
        P.E_PP_CONTENT_REJECTED)
    # sign / read side (6): unknown -> window -> self -> dup
    expect(lambda: pf.sign_proposal(                         # 12
        "usr:carol", "ghost-pet", 5), P.E_PP_UNKNOWN_PROPOSAL)
    expect(lambda: pf.sign_proposal(                         # 13
        "usr:carol", "gate-pet", 9), P.E_PP_WINDOW)
    expect(lambda: pf.sign_proposal(                         # 14
        "usr:bob", "gate-pet", 9), P.E_PP_WINDOW)
    expect(lambda: pf.sign_proposal(                        # 15
        "usr:bob", "gate-pet", 12), P.E_PP_DUP_SIGN)
    expect(lambda: pf.sign_proposal(                         # 16
        "usr:alice", "gate-pet", 12), P.E_PP_SELF_SIGN)
    expect(lambda: pf.proposal_view("ghost-pet"),            # 17
           P.E_PP_UNKNOWN_PROPOSAL)
    codes = [c for _i, c, _caught in out]
    all_expected = all(caught for _i, _c, caught in out)
    return codes, all_expected


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    bad_word = lobby_cfg["gate"]["forbidden_words"][0]

    tmp = tempfile.mkdtemp(prefix="proposal-gatepersist-")
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
        # populated registry world: ledger domain populated AND
        # the registry axis carries data (the R2011 zero-reg
        # boundary is already pinned; this successor needs a
        # populated face for the gates-before-read law)
        for who in ("alice", "bob", "carol", "dave"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        cf.issue_certificate("usr:alice", "gatepersist-seed:2026",
                             "boundary-cert")
        pf.register_proposal("gate-pet", "Gate petition",
                             "keep the gate family honest",
                             "usr:alice", 10, 20, 3, False)
        pf.sign_proposal("usr:bob", "gate-pet", 11)
        ppconn = sqlite3.connect(pp_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-PPG1 populated-world control anchor --------------
        env = pf.progress_board()
        benv = pf.proposal_board()
        venv = pf.proposal_view("gate-pet")
        rows = env["progress_board"]
        ok_env = (set(env.keys()) == {"progress_board", "disclaimer"}
                  and len(rows) == 1
                  and rows[0]["proposal_id"] == "gate-pet"
                  and rows[0]["signature_count"] == 1
                  and rows[0]["threshold"] == 3
                  and rows[0]["progress_pct"] == 33.33
                  and rows[0]["remaining"] == 2
                  and rows[0]["qualified"] is False
                  and rows[0]["ai_label"] == 0)
        ok_benv = (set(benv.keys()) == {"proposals", "disclaimer"}
                   and len(benv["proposals"]) == 1
                   and benv["proposals"][0]["proposal_id"]
                   == "gate-pet"
                   and benv["proposals"][0]["window"] == [10, 20])
        ok_venv = bool(
            set(venv.keys()) == {
                "proposal_id", "title", "body", "proposer",
                "window", "threshold", "signature_count",
                "qualified", "signers", "ai_label",
                "disclaimer"}
            and venv["signature_count"] == 1
            and len(venv["signers"]) == 1
            and venv["signers"][0]["account_id"] == "usr:bob"
            and venv["signers"][0]["at_tick"] == 11
            and isinstance(
                venv["signers"][0]["signed_utc"], str)
            and venv["signers"][0]["signed_utc"])
        fam1 = read_family(pf)
        ok_double = (fam1 == read_family(pf))
        ok_counts = (table_counts(ppconn)
                     == {"proposals": 1, "proposal_signs": 1})
        record("AC-PPG1",
               ok_env and ok_benv and ok_venv and ok_double
               and ok_counts,
               "populated-world anchor: progress row 1/3 33.33"
               " rem2 unqualified=%s board single-row echo=%s"
               " view signer bob@11=%s family double-read"
               " byte-stable=%s counts=%s"
               % (ok_env, ok_benv, ok_venv, ok_double,
                  table_counts(ppconn)))

        # -- AC-PPG2 instance-one baseline battery ----------------
        before = table_counts(ppconn)
        codes, caught = battery(pf, bad_word)
        after = table_counts(ppconn)
        v1 = json.dumps(codes)
        record("AC-PPG2",
               caught and len(codes) == 17 and before == after,
               "instance-one baseline: 17 probes all reject the"
               " expected ordered codes=%s all-expected=%s"
               " counts flat %s==%s V1 serialized=%s"
               % (caught, len(codes), before, after, v1))

        # -- AC-PPG3 cross-restart same-code (instance two) -------
        pre_fam = read_family(pf)
        pf.close()
        led.close()
        pf = led = None
        led2 = L.Ledger(db_path, cfg)
        cf2 = C.CollectiblesFace(led2)
        gate2 = SecGate.from_config(lobby_cfg)
        pf2 = P.ProposalFace(cf2, gate2, DISCLAIMER, pp_path)
        before3 = table_counts(ppconn)
        codes2, caught2 = battery(pf2, bad_word)
        after3 = table_counts(ppconn)
        v2 = json.dumps(codes2)
        fam2 = read_family(pf2)
        ok3 = (caught2 and v2 == v1 and before3 == after3
               and fam2 == pre_fam)
        record("AC-PPG3", ok3,
               "full-stack close (proposal -> ledger) + rebuild"
               " on same paths/cfg bytes: battery V2==V1"
               " byte-identical=%s probes all-expected=%s"
               " counts flat %s==%s read family F2==F1=%s"
               % (v2 == v1, caught2, before3, after3,
                  fam2 == pre_fam))

        # -- AC-PPG4 post-restart liveness ------------------------
        r1 = pf2.register_proposal(
            "live-pet", "Live petition", "second registry row",
            "usr:carol", 30, 40, 2, False)
        s1 = pf2.sign_proposal("usr:dave", "live-pet", 31)
        s2 = pf2.sign_proposal("usr:bob", "live-pet", 32)
        rows4 = pf2.progress_board()["progress_board"]
        live = rows4[0] if rows4 else {}
        gate_row = rows4[1] if len(rows4) > 1 else {}
        ok_rows = (len(rows4) == 2
                   and live.get("proposal_id") == "live-pet"
                   and live.get("signature_count") == 2
                   and live.get("progress_pct") == 100.0
                   and live.get("remaining") == 0
                   and live.get("qualified") is True
                   and gate_row.get("proposal_id") == "gate-pet"
                   and gate_row.get("progress_pct") == 33.33)
        ok_receipts = (r1["ai_label"] == 0
                       and s1["memorial"] is None
                       and s2["memorial"] == "issued"
                       and s2["qualified"] is True)
        certs = cf2.collection("usr:carol")["certificates"]
        mem = [c for c in certs
               if c["event_ref"] == "proposal-memorial:live-pet"]
        ok_memorial = (len(mem) == 1
                       and mem[0]["item_id"] == "proposal-memorial")
        before4 = table_counts(ppconn)
        codes4, caught4 = battery(pf2, bad_word)
        after4 = table_counts(ppconn)
        v2b = json.dumps(codes4)
        fam2b = read_family(pf2)
        ok4 = (ok_rows and ok_receipts and ok_memorial
               and caught4 and v2b == v1 and before4 == after4
               and fam2b != fam2)
        record("AC-PPG4", ok4,
               "post-restart liveness: live-pet register+2 signs"
               " crossing memorial issued=%s boards follow"
               " (live 100.0 qualified first, gate 33.33)=%s"
               " receipts=%s battery V2b==V1 after growth=%s"
               " counts flat=%s family changed via real write=%s"
               % (ok_memorial, ok_rows, ok_receipts, v2b == v1,
                  before4 == after4, fam2b != fam2))

        # -- AC-PPG5 third instance + pure-read law ---------------
        final_fam = fam2b
        counts5a = table_counts(ppconn)
        fam_pre = read_family(pf2)
        pf2.close()
        led2.close()
        pf2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        cf3 = C.CollectiblesFace(led3)
        gate3 = SecGate.from_config(lobby_cfg)
        pf3 = P.ProposalFace(cf3, gate3, DISCLAIMER, pp_path)
        before5 = table_counts(ppconn)
        codes5, caught5 = battery(pf3, bad_word)
        after5 = table_counts(ppconn)
        v3 = json.dumps(codes5)
        fam3 = read_family(pf3)
        ok5 = (caught5 and v3 == v1 and fam3 == final_fam
               and fam_pre == final_fam
               and fam3 == read_family(pf3)
               and before5 == after5 and counts5a == after5)
        record("AC-PPG5", ok5,
               "third instance (second restart): battery V3==V1=%s"
               " reads == instance-two final byte-identical=%s"
               " read battery double-run stable=%s counts flat"
               " %s==%s"
               % (v3 == v1, fam3 == final_fam,
                  fam3 == read_family(pf3), before5, after5))

        # -- AC-PPG6 cross-instance vector summary + zero token ---
        vectors_same = (v1 == v2 == v2b == v3)
        keysets = (set(pf3.progress_board().keys())
                   == {"progress_board", "disclaimer"}
                   and set(pf3.proposal_board().keys())
                   == {"proposals", "disclaimer"}
                   and set(pf3.proposal_view("gate-pet").keys())
                   == {"proposal_id", "title", "body", "proposer",
                       "window", "threshold", "signature_count",
                       "qualified", "signers", "ai_label",
                       "disclaimer"})
        zero_token = (tx_count(ledconn) == 0
                      and cert_count(ledconn) == 2)
        record("AC-PPG6",
               vectors_same and keysets and zero_token,
               "cross-instance same-code law: V1==V2==V2b==V3"
               " byte-identical=%s envelope key sets constant=%s"
               " zero-token law ledger_tx==0 with %d platform"
               " certificates=%s"
               % (vectors_same, keysets, cert_count(ledconn),
                  zero_token))
        pf3.close()
        led3.close()
        pf3 = led3 = None

        # -- AC-PPG7 hygiene ---------------------------------------
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
        reg_ok = ("ledger-proposal-gatepersist" in reg_src
                  and "test_proposal_gatepersist.py" in reg_src)
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
    record("AC-PPG7",
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
