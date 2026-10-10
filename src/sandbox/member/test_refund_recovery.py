"""Acceptance suite for the close_refund entitlement-recovery linkage
(R1718 successor, tech.md claim line R1721).

Asserts the pre-registered criteria AC-RR1..AC-RR7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Design ruling (registered in the claim line): recovery = deactivation
through the EXISTING one-way active->expired edge - the member_periods
CHECK/trigger state machine is the law and a distinct 'refunded'
status state is a real schema-change window (migration-chain step +
fingerprint re-freeze, registered as a follow-up seed), not this
window; the refund-recovery audit row carries the provenance. The
ledger conversion-share clawback is ruled OUT of this window (token
balance semantics belong to the ledger domain; follow-up seed).
Wiring law: the recovery face is caller-built and caller-owned
(orders.py holds a reference only, entitlement_recovery=None default
= shipped behavior byte-stable); post-commit attempts never break the
close (R1681->R1701 degraded precedent); the face is independently
re-callable for the crash-window heal.

Usage: python test_refund_recovery.py
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_member as TM               # noqa: E402 (build/tear/happy reuse)
import member as M                     # noqa: E402 (recovery face, _h)
import orders as O                      # noqa: E402 (wiring subject)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_code(fn, *codes):
    try:
        fn()
    except (M.MemberError, O.PayError) as exc:
        return exc.code in codes, "%s (detail=%s)" % (exc.code, exc.detail or "-")
    return False, "no-error-raised"


def build_wired(recovery=None):
    """Fresh TM.build world re-opened with the recovery face wired
    (R1718 build_wired law): the un-wired PayOrders closes FIRST, then
    the wired one opens on the same pay.db. The face is caller-built
    (here: the member store itself, or a broken stub) and caller-owned;
    the store's pay dock is re-pointed at the live connection (the
    dock is read-only faces - grant_row/grants_for)."""
    world = TM.build()
    pay_db = world["pay_db"]
    world["pay"].close()
    with open(world["pcfg_path"], encoding="utf-8") as fh:
        pcfg = json.load(fh)
    face = world["store"] if recovery is None else recovery
    world["pay"] = O.PayOrders(pcfg, pay_db, world["events"], world["led"],
                               entitlement_recovery=face)
    world["store"].pay = world["pay"]
    return world


class BrokenRecovery(object):
    """AC-RR6 scenario: an unexpected recovery error must never break
    the refund close; the envelope carries the honest off:<ExcName>."""

    def revoke_refunded(self, grant_id):
        raise RuntimeError("member domain down")


def main():
    # ---- AC-RR1: pay read faces carry the additive refunded flag ----
    w = TM.build()
    oid1, gid1 = TM.happy(w, "tier_experience", "RR-1", "rr-1")
    before = w["pay"].grant_row(gid1)
    items_before = w["pay"].grants_for("RR-1")["items"]
    orig_keys = {"grant_id", "order_id", "entitlement", "granted_utc"}
    env1 = w["pay"].close_refund(oid1)
    after = w["pay"].grant_row(gid1)
    items_after = w["pay"].grants_for("RR-1")["items"]
    ok1 = (before is not None and not before["refunded"]
           and orig_keys.issubset(set(before))
           and all(orig_keys.issubset(set(i)) for i in items_before)
           and all(not i["refunded"] for i in items_before)
           and env1["status"] == "closed" and after["refunded"]
           and len(items_after) == 1 and items_after[0]["refunded"]
           and "recovery" not in env1 and "notify" not in env1)
    TM.tear(w)
    record("AC-RR1", ok1,
           "grant refunded before=%s after=%s; items=%d refunded=%s;"
           " envelope keys additive (no recovery/notify key unwired)"
           % (before["refunded"], after["refunded"], len(items_after),
              items_after[0]["refunded"]))

    # ---- AC-RR2: refunded grant is a dead activation source ---------
    w = TM.build()
    oid2, gid2 = TM.happy(w, "tier_experience", "RR-2", "rr-2")
    act_ok = "period_id" in w["store"].activate(gid2, "RR-2")
    w["pay"].close_refund(oid2)
    refused, ev2 = expect_code(
        lambda: w["store"].activate(gid2, "RR-2"), M.E_BAD_GRANT_SOURCE)
    oid2b, gid2b = TM.happy(w, "tier_experience", "RR-2", "rr-2b")
    w["pay"].close_refund(oid2b)
    refused_b, ev2b = expect_code(
        lambda: w["store"].activate(gid2b, "RR-2"), M.E_BAD_GRANT_SOURCE)
    periods = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_periods"
        " WHERE census_avatar_id = 'RR-2'")[0][0]
    TM.tear(w)
    record("AC-RR2", act_ok and refused and refused_b and periods == 1,
           "pre-refund activate=%s; post-refund re-activate=%s (%s);"
           " never-activated refunded grant=%s (%s); period rows=%d"
           % (act_ok, refused, ev2, refused_b, ev2b, periods))

    # ---- AC-RR3: revoke_refunded face semantics + idempotence -------
    w = build_wired()
    oid3, gid3 = TM.happy(w, "tier_mayor", "RR-3", "rr-3")
    opened = w["store"].activate(gid3, "RR-3")
    period_id = opened["period_id"]
    vouchers_opened = opened.get("vouchers_opened") or []
    env3 = w["pay"].close_refund(oid3)
    rec3 = env3.get("recovery") or {}
    status_row = TM.db_query(
        w["member_db"], "SELECT status FROM member_periods"
        " WHERE period_id = ?", (period_id,))[0][0]
    voucher_rows = TM.db_query(
        w["member_db"], "SELECT voucher_id, status FROM member_vouchers"
        " WHERE period_id = ?", (period_id,))
    expire_events = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_credit_events"
        " WHERE period_id = ? AND reason = 'expire'", (period_id,))[0][0]
    balance_after = w["store"].balance_face("RR-3")
    audit_id = M._h("audit", "refund-recovery", gid3)
    audit_n = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?", (audit_id,))[0][0]
    # idempotent re-call: zero new writes, audit row stays exactly one
    r2 = w["store"].revoke_refunded(gid3)
    audit_n2 = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?", (audit_id,))[0][0]
    expire_events2 = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_credit_events"
        " WHERE period_id = ? AND reason = 'expire'", (period_id,))[0][0]
    # fail-closed gates
    gate_unknown, ev_unk = expect_code(
        lambda: w["store"].revoke_refunded("no-such-grant"),
        M.E_BAD_GRANT_SOURCE)
    oid3b, gid3b = TM.happy(w, "tier_experience", "RR-3", "rr-3b")
    gate_live, ev_live = expect_code(
        lambda: w["store"].revoke_refunded(gid3b), M.E_BAD_STATE)
    # birth-cert-only grant (no period row): revoked=0 + provenance row
    oid3c, gid3c = TM.happy(w, "pack_compute_19_9", "RR-3", "rr-3c")
    w["store"].activate(gid3c, "RR-3")
    env3c = w["pay"].close_refund(oid3c)
    rec3c = env3c.get("recovery") or {}
    audit_c = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?",
        (M._h("audit", "refund-recovery", gid3c),))[0][0]
    rc = w["store"].revoke_refunded(gid3c)
    audit_c2 = TM.db_query(
        w["member_db"], "SELECT COUNT(*) FROM member_audit"
        " WHERE audit_id = ?",
        (M._h("audit", "refund-recovery", gid3c),))[0][0]
    face_keys = set(rec3) >= {"grant_id", "census_avatar_id", "revoked",
                              "idempotent", "ai_generated", "disclaimer",
                              "persistent"}
    ok3 = (rec3.get("revoked") == 1 and status_row == "expired"
           and len(vouchers_opened) >= 1
           and all(v[1] == "expired" for v in voucher_rows)
           and expire_events == 1 and audit_n == 1
           and r2["revoked"] == 0 and audit_n2 == 1 and expire_events2 == 1
           and gate_unknown and gate_live
           and rec3c.get("revoked") == 0 and audit_c == 1
           and rc["revoked"] == 0 and audit_c2 == 1 and face_keys)
    ev3 = ("recovery=%s; period=%s; vouchers open=%s expired=%s;"
           " expire_events=%d audit=%d->%d; re-call revoked=%s;"
           " gates unknown=%s live=%s; birth-only revoked=%s audit=%d->%d"
           % (rec3.get("revoked"), status_row, len(vouchers_opened),
              len(voucher_rows), expire_events, audit_n, audit_n2,
              r2["revoked"], ev_unk, ev_live, rec3c.get("revoked"),
              audit_c, audit_c2))
    # ---- AC-RR4: consumption faces stop immediately ------------------
    privs = w["store"].privileges_for("RR-3")
    no_priv, ev_priv = expect_code(
        lambda: w["store"].has_privilege("RR-3", "chat_highlight"),
        M.E_NO_ACTIVE_PERIOD)
    no_credits, ev_cred = expect_code(
        lambda: w["store"].consume_credits("RR-3", 1), M.E_PERIOD_EXPIRED)
    period_face = [p for p in balance_after["periods"]
                   if p["period_id"] == period_id][0]
    ok4 = (privs["active"] is False and not privs["tiers"]
           and not privs["privileges"] and no_priv and no_credits
           and period_face["status"] == "expired"
           and period_face["balance"] == 0)
    TM.tear(w)
    record("AC-RR3", ok3, ev3)
    record("AC-RR4", ok4,
           "privileges active=%s tiers=%s; has_privilege=%s (%s);"
           " consume_credits=%s (%s); period face status=%s balance=%s"
           " (history readable, not destroyed)"
           % (privs["active"], privs["tiers"], no_priv, ev_priv,
              no_credits, ev_cred, period_face["status"],
              period_face["balance"]))

    # ---- AC-RR5: birth cert re-judges on non-refunded grants ---------
    w = TM.build()
    oid5, gid5 = TM.happy(w, "tier_experience", "RR-5a", "rr-5a")
    w["store"].activate(gid5, "RR-5a")
    cert_before = w["store"].birth_cert_face("RR-5a")
    w["pay"].close_refund(oid5)
    cert_after = w["store"].birth_cert_face("RR-5a")
    oid5b, gid5b = TM.happy(w, "tier_experience", "RR-5b", "rr-5b1")
    oid5c, gid5c = TM.happy(w, "pack_compute_19_9", "RR-5b", "rr-5b2")
    w["store"].activate(gid5b, "RR-5b")
    cert_two_before = w["store"].birth_cert_face("RR-5b")
    w["pay"].close_refund(oid5b)
    cert_two_after = w["store"].birth_cert_face("RR-5b")
    TM.tear(w)
    ok5 = (cert_before["birth_cert"] is True
           and cert_after["birth_cert"] is False
           and cert_after["member_domain_marker"] is True
           and cert_after["first_granted_utc"] is not None
           and cert_two_before["birth_cert"] is True
           and cert_two_after["birth_cert"] is True)
    record("AC-RR5", ok5,
           "only-grant: before=%s after=%s (marker=%s first=%s);"
           " two-grant: before=%s after-refund-one=%s"
           % (cert_before["birth_cert"], cert_after["birth_cert"],
              cert_after["member_domain_marker"],
              cert_after["first_granted_utc"] is not None,
              cert_two_before["birth_cert"], cert_two_after["birth_cert"]))

    # ---- AC-RR6: wiring envelope + never-break + heal paths ----------
    # crash-window heal on an unwired world: activation happens BEFORE
    # the close, the close succeeds without any recovery face, then the
    # independent re-call converges (and a second re-call is a no-op)
    w = TM.build()
    oid6, gid6 = TM.happy(w, "tier_experience", "RR-6a", "rr-6a")
    w["store"].activate(gid6, "RR-6a")
    env6 = w["pay"].close_refund(oid6)
    shipped_clean = ("recovery" not in env6 and "notify" not in env6
                     and env6["status"] == "closed")
    heal1 = w["store"].revoke_refunded(gid6)
    heal2 = w["store"].revoke_refunded(gid6)
    TM.tear(w)
    # broken face: the close must survive a face crash, then heal
    w = build_wired(recovery=BrokenRecovery())
    oid6b, gid6b = TM.happy(w, "tier_experience", "RR-6b", "rr-6b")
    w["store"].activate(gid6b, "RR-6b")
    env6b = w["pay"].close_refund(oid6b)
    rec6b = env6b.get("recovery") or {}
    closed_ok = env6b["status"] == "closed"
    heal3 = w["store"].revoke_refunded(gid6b)
    TM.tear(w)
    ok6 = (shipped_clean and heal1["revoked"] == 1 and heal2["revoked"] == 0
           and closed_ok and rec6b.get("status") == "off:RuntimeError"
           and heal3["revoked"] == 1)
    record("AC-RR6", ok6,
           "shipped default recovery-key=%s; crash-window heal revoked=%s"
           " re-call=%s; broken face closed=%s recovery=%s; heal=%s"
           % ("recovery" not in env6, heal1["revoked"], heal2["revoked"],
              closed_ok, rec6b, heal3["revoked"]))

    # ---- AC-RR7: hygiene (ASCII, no network imports) ----------------
    subjects = [os.path.join(BASE, "member.py"),
                os.path.join(BASE, "..", "pay", "orders.py"),
                os.path.abspath(__file__)]
    ascii_ok = True
    net_hits = []
    for path in subjects:
        with open(path, "rb") as fh:
            data = fh.read()
        if any(b > 127 for b in data):
            ascii_ok = False
        text = data.decode("ascii", "replace")
        for line in text.splitlines():
            stripped = line.strip()
            if (stripped.startswith("import ")
                    or stripped.startswith("from ")) and (
                    re.search(r"\b(urllib|requests|socket|http)\b",
                              stripped)):
                net_hits.append(stripped)
    ok7 = ascii_ok and not net_hits
    record("AC-RR7", ok7,
           "ascii=%s subjects=%d; network import lines=%d%s"
           % (ascii_ok, len(subjects), len(net_hits),
              "" if not net_hits else " hits=%s" % net_hits))

    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
