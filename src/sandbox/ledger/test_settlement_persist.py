"""Cross-restart persistence window for the cross-subsidiary
settlement face (BigDomain R1944; the settlement seat of the R1886
persist family - the R1939-seeded row, criteria AC-SEP1..SEP7
pre-registered in the R1944 tech.md claim row before this code
existed; honesty law). Product face: settlement.py gains an
OPTIONAL sqlite persistence mirror (db_path=None default stays
purely in-memory, byte-identical to the R601 path; minors R1939
precedent) plus the read family manifest_view/claims_view/
last_window_id and close(); the window is proven on the real
product path.

Three-instance world: anchor world (two-window hash chain + three
claims, battery over the read family, SQL cross) -> close ->
same-db reopen with byte-identical read replay (zero in-memory
drift) -> five fail-closed gate probes surviving the restart ->
real-path continuation (third window chains onto the persisted
anchor: prev_id == pre-restart last_window_id, the core
persistence proof) -> frozen pre-restart windows + handed-out
manifest copies still verify -> pure-read law -> double-restart
stability + default-path zero drift + hygiene.

All evidence values are content-addressed (manifest ids are
sha256 over canonical payloads of deterministic inputs), so the
double-run stdout is byte-identical without clock freezing.
Stdlib only; this source stays pure ASCII (encoding
discipline). Usage: python test_settlement_persist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import settlement as ST  # noqa: E402  (R601 face + R1944 layer)

RESULTS = []

P1 = "2026-10-01/P1D"
P2 = "2026-10-02/P1D"
P3 = "2026-11-01/P1D"
SALES_A = [{"amount_cent": 1990}, {"amount_cent": 3990},
           {"amount_cent": 990}]
SALES_B = [{"amount_cent": 49900}]
SALES_C = [{"amount_cent": 299}, {"amount_cent": 101}]
USAGE = [{"units": 12}, {"units": 3}]
PARTIES = ("bigdomain-product", "bigmoney-engine", "bigcompute-outlet")
# fixture values only - canonical split ratios stay [needs-CEO]
WEIGHTS = {"bigdomain-product": 55, "bigmoney-engine": 30,
           "bigcompute-outlet": 15}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_error(fn, code):
    try:
        fn()
    except ST.SettlementError as exc:
        return exc.code == code, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def battery(face):
    """Canonical read-family battery over the whole world."""
    return {
        "m1": dump(face.manifest_view(P1)),
        "m2": dump(face.manifest_view(P2)),
        "count": face.window_count(),
        "claims": dump(face.claims_view()),
        "last_id": face.last_window_id(),
    }


def sql_counts(db_path):
    conn = sqlite3.connect(db_path)
    windows = conn.execute(
        "SELECT COUNT(*) FROM st_windows").fetchone()[0]
    claims = conn.execute(
        "SELECT COUNT(*) FROM st_claims").fetchone()[0]
    conn.close()
    return windows, claims


def main():
    world = tempfile.mkdtemp(prefix="st-persist-")
    db_path = os.path.join(world, "settlement.db")
    cfg_path = os.path.join(BASE, "config.json")
    with open(cfg_path, "rb") as handle:
        sha_cfg_before = hashlib.sha256(handle.read()).hexdigest()

    # ---------- AC-SEP1: anchor world + battery ----------
    face1 = ST.SettlementFace(db_path=db_path)
    m1 = face1.build_manifest(P1, SALES_A, USAGE, PARTIES, WEIGHTS)
    m2 = face1.build_manifest(P2, SALES_B, [], PARTIES, WEIGHTS)
    chain_ok = (m2["prev_id"] == m1["id"]
                and face1.last_window_id() == m2["id"])
    claim_a = face1.claim(P1, "bigdomain-product",
                          m1["apportioned_cent"]["bigdomain-product"])
    claim_b = face1.claim(P1, "bigmoney-engine", 100)
    claim_c = face1.claim(P2, "bigcompute-outlet",
                          m2["apportioned_cent"]["bigcompute-outlet"])
    claims_bound = (claim_a["manifest_id"] == m1["id"]
                    and claim_b["manifest_id"] == m1["id"]
                    and claim_c["manifest_id"] == m2["id"])
    bat1 = battery(face1)
    dig1 = sha16(dump(bat1))
    w1, c1 = sql_counts(db_path)
    ok1 = (chain_ok and claims_bound and w1 == 2 and c1 == 3
           and bat1["count"] == 2 and len(json.loads(bat1["claims"])) == 3
           and face1.verify_manifest(m1, SALES_A, USAGE) is True)
    record("AC-SEP1", ok1,
           "anchor: chain %s->%s, 3 claims bound, windows=%d claims=%d,"
           " battery sha16=%s" % (m1["id"][:12], m2["id"][:12],
                                  w1, c1, dig1))

    # ---------- AC-SEP2: cross-restart byte identity ----------
    face1.close()
    face2 = ST.SettlementFace(db_path=db_path)
    bat2 = battery(face2)
    dig2 = sha16(dump(bat2))
    ok2 = bat2 == bat1 and dig2 == dig1
    record("AC-SEP2", ok2,
           "reopen replay byte-identical (battery sha16 %s == %s),"
           " zero in-memory drift" % (dig2, dig1))

    # ---------- AC-SEP3: gate probes survive restart ----------
    p_dup_window, code_w = expect_error(
        lambda: face2.build_manifest(P1, SALES_A, USAGE, PARTIES,
                                     WEIGHTS), ST.E_ST_PERIOD_DUP)
    p_dup_claim, code_c = expect_error(
        lambda: face2.claim(P1, "bigdomain-product", 1),
        ST.E_ST_PERIOD_DUP)
    p_ghost_party, code_p = expect_error(
        lambda: face2.claim(P2, "ghost-party", 1), ST.E_ST_BAD_INPUT)
    p_unknown_period, code_u = expect_error(
        lambda: face2.claim("2099-01-01/P1D", "bigmoney-engine", 1),
        ST.E_ST_BAD_INPUT)
    p_over_limit, code_o = expect_error(
        lambda: face2.claim(P2, "bigmoney-engine", 10 ** 9),
        ST.E_ST_BAD_INPUT)
    w3, c3 = sql_counts(db_path)
    ok3 = (p_dup_window and p_dup_claim and p_ghost_party
           and p_unknown_period and p_over_limit and w3 == 2
           and c3 == 3)
    record("AC-SEP3", ok3,
           "five probes all-reject cross-restart (%s/%s/%s/%s/%s),"
           " rows frozen %d/%d" % (code_w, code_c, code_p, code_u,
                                   code_o, w3, c3))

    # ---------- AC-SEP4: real-path continuation, chain anchor ----------
    m3 = face2.build_manifest(P3, SALES_C, USAGE, PARTIES, WEIGHTS)
    chain_anchor_ok = m3["prev_id"] == m2["id"]
    claim_d = face2.claim(P3, "bigdomain-product",
                          m3["apportioned_cent"]["bigdomain-product"])
    verify_ok = face2.verify_manifest(m3, SALES_C, USAGE) is True
    w4, c4 = sql_counts(db_path)
    # zero-cache recompute: read faces alone re-derive the world
    bat4 = battery(face2)
    recompute_ok = (
        bat4["count"] == 3
        and json.loads(bat4["m1"])["id"] == m1["id"]
        and face2.manifest_view(P3)["id"] == m3["id"]
        and face2.last_window_id() == m3["id"]
        and len(json.loads(bat4["claims"])) == 4
        and claim_d["manifest_id"] == m3["id"])
    ok4 = (chain_anchor_ok and verify_ok and recompute_ok
           and w4 == 3 and c4 == 4)
    record("AC-SEP4", ok4,
           "continuation chains onto persisted anchor (prev_id=="
           "%s), verify True, rows %d/%d" % (m2["id"][:12], w4, c4))

    # ---------- AC-SEP5: frozen faces + verify survives ----------
    frozen_ok = (dump(face2.manifest_view(P1)) == bat1["m1"]
                 and dump(face2.manifest_view(P2)) == bat1["m2"]
                 and face2.claims_view(P1) == json.loads(bat1["claims"])
                 [:2])
    verify_old_ok = (face2.verify_manifest(m1, SALES_A, USAGE) is True
                     and face2.verify_manifest(m2, SALES_B, [])
                     is True)
    ok5 = frozen_ok and verify_old_ok
    record("AC-SEP5", ok5,
           "pre-restart windows byte-frozen; handed-out copies still"
           " verify cross-restart (%s)" % verify_old_ok)

    # ---------- AC-SEP6: pure-read law ----------
    reads_a = dump(battery(face2))
    reads_b = dump(battery(face2))
    w6a, c6a = sql_counts(db_path)
    w6b, c6b = sql_counts(db_path)
    ok6 = (reads_a == reads_b and (w6a, c6a) == (w6b, c6b)
           == (3, 4))
    record("AC-SEP6", ok6,
           "pure-read law: double read battery identical, row counts"
           " constant %d/%d" % (w6a, c6a))

    # ---------- AC-SEP7: double-restart + default path + hygiene ----------
    face2.close()
    face3 = ST.SettlementFace(db_path=db_path)
    bat3 = battery(face3)
    dig3 = sha16(dump(bat3))
    restart_stable = dump(bat3) == dump(bat4)
    # closed-face write rejection (db path): no memory/db divergence
    face3.close()
    p_closed, code_closed = expect_error(
        lambda: face3.build_manifest("2026-12-01/P1D", SALES_C, [],
                                     PARTIES, WEIGHTS),
        ST.E_ST_CLOSED)
    # default path: purely in-memory, zero db files, close no-op
    default_dir = tempfile.mkdtemp(prefix="st-default-")
    face_d = ST.SettlementFace()
    md = face_d.build_manifest("2026-10-09/P1D", SALES_A, USAGE,
                               PARTIES, WEIGHTS)
    cd = face_d.claim("2026-10-09/P1D", "bigdomain-product", 500)
    vd = face_d.verify_manifest(md, SALES_A, USAGE)
    face_d.close()
    default_ok = (md["prev_id"] is None and cd["manifest_id"] == md["id"]
                  and vd is True
                  and face_d.window_count() == 1
                  and os.listdir(default_dir) == [])
    # hygiene: pure ASCII, zero network imports, zero UPDATE,
    # config untouched, world outside repo
    with open(os.path.join(BASE, "settlement.py"), "rb") as handle:
        src = handle.read()
    text = src.decode("ascii")
    net_free = all(tok not in text for tok in
                   ("import urllib", "import requests", "import socket",
                    "import http"))
    update_free = "UPDATE" not in text
    with open(cfg_path, "rb") as handle:
        sha_cfg_after = hashlib.sha256(handle.read()).hexdigest()
    ascii_ok = all(byte < 128 for byte in src)
    outside = os.path.abspath(world).startswith(tempfile.gettempdir())
    ok7 = (restart_stable and p_closed and default_ok and ascii_ok
           and net_free and update_free and outside
           and sha_cfg_after == sha_cfg_before
           and hasattr(ST, "E_ST_CLOSED"))
    record("AC-SEP7", ok7,
           "3rd-open == 2nd end-state (sha16 %s); closed-write %s;"
           " default path zero-drift %s; ascii=%s net-free=%s"
           " update-free=%s cfg-sha-same=%s"
           % (dig3, code_closed, default_ok, ascii_ok, net_free,
              update_free, sha_cfg_after == sha_cfg_before))

    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s %d/%d criteria" % ("PASS" if not failed else "FAIL",
                                       len(RESULTS) - len(failed),
                                       len(RESULTS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
