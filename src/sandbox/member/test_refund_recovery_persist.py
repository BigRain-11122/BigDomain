"""Acceptance suite for the refund-recovery linkage cross-restart
persistence window (R1955 reseed claim, registered as R1960 in
state/queue/tech.md BEFORE this code; honesty law).

Pre-registered criteria AC-RRP1..AC-RRP7 (tech.md claim line). The
refund-recovery chain lives on the pay side (close_refund granted->
closed edge + status-derived refunded read faces) and the member side
(revoke_refunded active->expired edge + refund-recovery audit
provenance + expire voucher/credit events). This window pins:
(a) both read families byte-identical across a full three-piece
close/reopen restart; (b) the recovery code path re-entry
post-restart (idempotent re-call converges via the deterministic
audit_id key, never duplicates); (c) a fresh wired refund closing
instantly on the restarted instance while pre-restart snapshots stay
zero-drift; (d) pure-read law for the snapshot read batch; (e) second
restart stability; (f) hygiene.

Design rulings (registered in the claim line): wired instant-converged
world; the pending->restart->converge path is carried by the in-book
AC-RR6 crash-window heal, its cross-restart variant = this window's
instance-ii fresh wired refund face (same recovery code path
post-restart first-run) plus the idempotent re-call face; restart =
full three-piece close (store+pay+led) and same-cfg same-db reopen in
the build_wired two-stage construction order; the events instance
stays out of the refund-chain focus face (honest note); no-clawback
wiring world = zero ledger refund writes (all-table count control
face, derived from sqlite_master - zero table-name assumptions).

Usage: python test_refund_recovery_persist.py
"""

import hashlib
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_member as TM                 # noqa: E402 (world primitives)
import test_refund_recovery as TR        # noqa: E402 (build_wired reuse)
import member as M                       # noqa: E402 (recovery face)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def db_dump(db_path, sql, args=()):
    return dumps(TM.db_query(db_path, sql, args))


def ledger_table_counts(db_path):
    tables = TM.db_query(
        db_path, "SELECT name FROM sqlite_master WHERE type='table'"
        " ORDER BY name")
    return dumps([(t[0], TM.db_query(
        db_path, "SELECT COUNT(*) FROM %s" % t[0])[0][0]) for t in tables])


def snapshot(w, ids):
    """Five-face snapshot: member full-table dumps (audit/periods/
    vouchers/credit events), per-avatar balance faces, pay refunded
    read faces, live-grant contrast face, plus the all-table ledger
    zero-refund-write control face."""
    s = {}
    s["audit"] = db_dump(w["member_db"],
                         "SELECT * FROM member_audit ORDER BY rowid")
    s["periods"] = db_dump(w["member_db"],
                           "SELECT * FROM member_periods ORDER BY rowid")
    s["vouchers"] = db_dump(w["member_db"],
                            "SELECT * FROM member_vouchers ORDER BY rowid")
    s["credits"] = db_dump(
        w["member_db"],
        "SELECT * FROM member_credit_events ORDER BY rowid")
    s["balA"] = dumps(w["store"].balance_face(ids["A"]))
    s["balB"] = dumps(w["store"].balance_face(ids["B"]))
    s["balC"] = dumps(w["store"].balance_face(ids["C"]))
    s["grA"] = dumps(w["pay"].grant_row(ids["gidA"]))
    s["grB"] = dumps(w["pay"].grant_row(ids["gidB"]))
    s["gfC"] = dumps(w["pay"].grants_for(ids["C"]))
    if "gidD" in ids:
        s["grD"] = dumps(w["pay"].grant_row(ids["gidD"]))
        s["balD"] = dumps(w["store"].balance_face(ids["D"]))
    s["ledger_counts"] = ledger_table_counts(w["ledger_db"])
    return s


def row_counts(w):
    """Pure-read-law counters: pay side and member side row totals."""
    c = {}
    c["pay_orders"] = TM.db_query(
        w["pay_db"], "SELECT COUNT(*) FROM pay_orders")[0][0]
    c["pay_grants"] = TM.db_query(
        w["pay_db"], "SELECT COUNT(*) FROM pay_grants")[0][0]
    c["pay_receipts"] = TM.db_query(
        w["pay_db"], "SELECT COUNT(*) FROM pay_receipts")[0][0]
    for tab in ("member_periods", "member_audit",
                "member_credit_events", "member_vouchers"):
        c[tab] = TM.db_query(
            w["member_db"], "SELECT COUNT(*) FROM %s" % tab)[0][0]
    return json.dumps(c, sort_keys=True, ensure_ascii=False)


def reopen_wired(w):
    """Full three-piece restart (store+pay+led closed, then same cfg
    same db reopened) in the build_wired two-stage construction order:
    led -> un-wired temp pay -> store -> temp pay close -> wired pay
    (entitlement_recovery=store) -> store.pay re-point."""
    w["store"].close()
    w["pay"].close()
    w["led"].close()
    led_cfg = TM.load_json(os.path.join(TM._LEDGER, "config.json"))
    led = TM.Ledger(w["ledger_db"], led_cfg)
    pcfg = TM.load_json(w["pcfg_path"])
    pay_tmp = TM.pay_orders.PayOrders(
        pcfg, w["pay_db"], w["events"], led)
    store = TM.M.MemberStore(w["mcfg"], w["member_db"], pay_tmp)
    pay_tmp.close()
    pay = TM.pay_orders.PayOrders(
        pcfg, w["pay_db"], w["events"], led,
        entitlement_recovery=store)
    store.pay = pay
    w["led"] = led
    w["pay"] = pay
    w["store"] = store
    return w


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    shipped_cfgs = [
        os.path.join(BASE, "config.json"),
        os.path.normpath(os.path.join(BASE, "..", "pay", "config.json")),
        os.path.normpath(os.path.join(BASE, "..", "ledger",
                                     "config.json")),
    ]
    cfg_before = [sha256_file(p) for p in shipped_cfgs]

    # ---- AC-RRP1: anchor world + pre-restart five-face snapshot ----
    w = TR.build_wired()
    ids = {"A": "RRP-A", "B": "RRP-B", "C": "RRP-C"}
    ids["oidA"], ids["gidA"] = TM.happy(w, "tier_mayor", "RRP-A", "rrp-a")
    opened_a = w["store"].activate(ids["gidA"], "RRP-A")
    period_a = opened_a["period_id"]
    led_pre = ledger_table_counts(w["ledger_db"])  # pre-close control
    env_a = w["pay"].close_refund(ids["oidA"])
    rec_a = env_a.get("recovery") or {}
    ids["oidB"], ids["gidB"] = TM.happy(
        w, "tier_experience", "RRP-B", "rrp-b")
    opened_b = w["store"].activate(ids["gidB"], "RRP-B")
    period_b = opened_b["period_id"]
    env_b = w["pay"].close_refund(ids["oidB"])
    rec_b = env_b.get("recovery") or {}
    ids["oidC"], ids["gidC"] = TM.happy(
        w, "tier_experience", "RRP-C", "rrp-c")
    opened_c = w["store"].activate(ids["gidC"], "RRP-C")
    period_c = opened_c["period_id"]
    snap1 = snapshot(w, ids)
    status_a = TM.db_query(
        w["member_db"], "SELECT status FROM member_periods"
        " WHERE period_id = ?", (period_a,))[0][0]
    status_b = TM.db_query(
        w["member_db"], "SELECT status FROM member_periods"
        " WHERE period_id = ?", (period_b,))[0][0]
    status_c = TM.db_query(
        w["member_db"], "SELECT status FROM member_periods"
        " WHERE period_id = ?", (period_c,))[0][0]
    gr_a = w["pay"].grant_row(ids["gidA"])
    gr_b = w["pay"].grant_row(ids["gidB"])
    gf_c = w["pay"].grants_for("RRP-C")
    period_a_row = db_dump(
        w["member_db"], "SELECT * FROM member_periods"
        " WHERE period_id = ?", (period_a,))
    audit_a_n = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?", (M._h("audit", "refund-recovery",
                                     ids["gidA"]),))[0][0]
    ledger_zero = json.loads(snap1["ledger_counts"])
    led_before_refund_rows = sum(n for _, n in ledger_zero)
    ok1 = (rec_a.get("revoked") == 1 and rec_b.get("revoked") == 1
           and status_a == "expired" and status_b == "expired"
           and status_c == "active"
           and gr_a["refunded"] is True and gr_b["refunded"] is True
           and all(not i["refunded"] for i in gf_c["items"])
           and len(snap1) == 11
           and snap1["ledger_counts"] == led_pre)
    record("AC-RRP1", ok1,
           "world: A revoked=%s period=%s; B revoked=%s period=%s;"
           " C period=%s live=%d; faces=%d; ledger rows=%d (pre-close"
           " control identical=%s)"
           % (rec_a.get("revoked"), status_a, rec_b.get("revoked"),
              status_b, status_c, len(gf_c["items"]), len(snap1),
              led_before_refund_rows,
              snap1["ledger_counts"] == led_pre))

    # ---- AC-RRP2: cross-restart byte identity -----------------------
    counts_pre = row_counts(w)
    reopen_wired(w)
    snap2 = snapshot(w, ids)
    diff_faces = [k for k in snap1 if snap1[k] != snap2.get(k)]
    ok2 = not diff_faces and set(snap1) == set(snap2)
    record("AC-RRP2", ok2,
           "restart faces identical=%s; diff=%s; faces=%d"
           % (ok2, diff_faces, len(snap2)))

    # ---- AC-RRP3: recovery path re-entry post-restart ---------------
    r_a = w["store"].revoke_refunded(ids["gidA"])
    r_b = w["store"].revoke_refunded(ids["gidB"])
    audit_a = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?", (M._h("audit", "refund-recovery",
                                     ids["gidA"]),))[0][0]
    audit_b = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?", (M._h("audit", "refund-recovery",
                                     ids["gidB"]),))[0][0]
    ok3 = (r_a["revoked"] == 0 and r_b["revoked"] == 0
           and audit_a == 1 and audit_b == 1)
    record("AC-RRP3", ok3,
           "re-entry A revoked=%s B revoked=%s; audit A=%d B=%d"
           " (deterministic key converges, zero duplicates)"
           % (r_a["revoked"], r_b["revoked"], audit_a, audit_b))

    # ---- AC-RRP4: fresh wired refund on instance ii + old faces ------
    ids["oidD"], ids["gidD"] = TM.happy(
        w, "tier_experience", "RRP-D", "rrp-d")
    ids["D"] = "RRP-D"
    opened_d = w["store"].activate(ids["gidD"], "RRP-D")
    period_d = opened_d["period_id"]
    env_d = w["pay"].close_refund(ids["oidD"])
    rec_d = env_d.get("recovery") or {}
    status_d = TM.db_query(
        w["member_db"], "SELECT status FROM member_periods"
        " WHERE period_id = ?", (period_d,))[0][0]
    audit_d = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?", (M._h("audit", "refund-recovery",
                                    ids["gidD"]),))[0][0]
    # old faces zero-drift against the pre-restart snapshot (named
    # faces only - the full-table audit/periods faces legitimately
    # grow by the D rows; the A-scoped row + count must not move)
    snap_d = snapshot(w, ids)
    drift = [k for k in ("balA", "balB", "grA", "grB", "balC", "gfC")
             if snap1[k] != snap_d[k]]
    period_a_row_after = db_dump(
        w["member_db"], "SELECT * FROM member_periods"
        " WHERE period_id = ?", (period_a,))
    audit_a_after = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?", (M._h("audit", "refund-recovery",
                                      ids["gidA"]),))[0][0]
    ok4 = (rec_d.get("revoked") == 1 and status_d == "expired"
           and audit_d == 1 and not drift
           and period_a_row_after == period_a_row
           and audit_a_after == audit_a_n)
    record("AC-RRP4", ok4,
           "fresh wired refund D revoked=%s period=%s audit=%d;"
           " named-face drift=%s; A row stable=%s; A audit=%d"
           % (rec_d.get("revoked"), status_d, audit_d, drift,
              period_a_row_after == period_a_row, audit_a_after))

    # ---- AC-RRP5: pure-read law ------------------------------------
    c1 = row_counts(w)
    snapshot(w, ids)  # read batch
    snapshot(w, ids)  # read batch again
    c2 = row_counts(w)
    ok5 = c1 == c2
    record("AC-RRP5", ok5,
           "read-batch row counts stable=%s (%s)" % (ok5, c1))

    # ---- AC-RRP6: second restart stability -------------------------
    reopen_wired(w)
    snap3 = snapshot(w, ids)
    diff3 = [k for k in snap_d if snap_d[k] != snap3.get(k)]
    ok6 = not diff3 and set(snap_d) == set(snap3)
    record("AC-RRP6", ok6,
           "second restart identical=%s; diff=%s; faces=%d"
           % (ok6, diff3, len(snap3)))
    world_tmp = w["tmp"]
    TM.tear(w)

    # ---- AC-RRP7: hygiene -------------------------------------------
    cfg_after = [sha256_file(p) for p in shipped_cfgs]
    cfg_ok = cfg_before == cfg_after
    with open(os.path.abspath(__file__), "rb") as fh:
        src = fh.read()
    ascii_ok = all(b < 128 for b in src)
    net_hits = []
    for line in src.decode("ascii", "replace").splitlines():
        stripped = line.strip()
        if (stripped.startswith("import ")
                or stripped.startswith("from ")) and re.search(
                r"\b(urllib|requests|socket|http)\b", stripped):
            net_hits.append(stripped)
    repo_root = os.path.normpath(os.path.join(BASE, "..", "..", ".."))
    tmp_ok = (not os.path.realpath(world_tmp).startswith(
        os.path.realpath(repo_root)))
    ok7 = cfg_ok and ascii_ok and not net_hits and tmp_ok
    record("AC-RRP7", ok7,
           "configs sha stable=%s; ascii=%s; net imports=%d;"
           " worlds outside repo=%s"
           % (cfg_ok, ascii_ok, len(net_hits), tmp_ok))

    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
