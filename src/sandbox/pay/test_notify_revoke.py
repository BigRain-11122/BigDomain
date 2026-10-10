"""Acceptance suite for the W15 revocation face (R1719 successor).

Asserts the pre-registered criteria AC-VR1..AC-VR7 (state/queue/
tech.md R1740 claim line, registered 2026-10-10 BEFORE this code;
honesty law). Rulings pre-registered in the claim line:
  1. The kill is the WHOLE (avatar, template) subscription - the
     longterm grant AND remaining once units both die (the WeChat
     user-side action is an unsubscribe, fail-closed toward not
     sending); pre-revoke sent rows stay immutable history.
  2. Live-only budget: the latest revoke ts is a cutoff, strict
     greater-than comparison - same-second grant-after-revoke lands
     on the dead side (conservative fail-closed, honest note).
  3. budget_face key set stays exactly {once, longterm, consumed};
     the revoked read face is the additive authorization_state.

Real-clock races are ruled out where they matter: re-arm assertions
sleep past the ts_utc second boundary, the same-second edge itself
is driven with deterministic explicit timestamps (ruling 2).

Usage: python test_notify_revoke.py
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse)
import test_pay_notify as TN             # noqa: E402 (notify_cfg helper)
import test_pay_notify_wiring as TW      # noqa: E402 (build_wired pattern)
import notify as N                       # noqa: E402 (face, never re-built)
import authorize as AZ                   # noqa: E402 (subject)

RESULTS = []

T1 = "2026-01-01T00:00:01Z"
T2 = "2026-01-01T00:00:02Z"
T3 = "2026-01-01T00:00:03Z"
T4 = "2026-01-01T00:00:04Z"
T5 = "2026-01-01T00:00:05Z"
T6 = "2026-01-01T00:00:06Z"
T7 = "2026-01-01T00:00:07Z"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_value_error(fn, code):
    try:
        fn()
    except ValueError as exc:
        return code in str(exc), str(exc).split(":", 1)[0]
    except Exception as exc:  # wrong family = FAIL
        return False, "wrong-family:%s" % type(exc).__name__
    return False, "no-error-raised"


def revoke_rows(db_path, avatar=None):
    """Test-side read-only count of the revoke event rows."""
    ro = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        if avatar is None:
            return int(ro.execute(
                "SELECT COUNT(*) FROM pay_notify_revokes"
            ).fetchone()[0])
        return int(ro.execute(
            "SELECT COUNT(*) FROM pay_notify_revokes"
            " WHERE census_avatar_id=?", (avatar,)).fetchone()[0])
    finally:
        ro.close()


def revoke_row(db_path, avatar):
    ro = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        return ro.execute(
            "SELECT revoke_id, census_avatar_id, template_id, ts_utc"
            " FROM pay_notify_revokes WHERE census_avatar_id=?",
            (avatar,)).fetchone()
    finally:
        ro.close()


def sent_rows_for(face, avatar):
    return [r for r in face.log_rows() if r[1] == avatar
            and r[4] == "sent"]


def main():
    tmp = tempfile.mkdtemp(prefix="vr-")
    cfg = TN.notify_cfg(TP.load_pay_config())
    ndb = os.path.join(tmp, "notify.db")
    nsrc = open(os.path.join(BASE, "notify.py"), encoding="ascii").read()
    asrc = open(os.path.join(BASE, "authorize.py"), encoding="ascii").read()

    # ---- AC-VR1: storage face (append-only, additive, single writer)
    schema_has = "pay_notify_revokes" in nsrc
    no_update = "UPDATE " not in nsrc and "UPDATE\n" not in nsrc
    az_no_db = "sqlite3" not in asrc
    face = N.PayNotifyFace(cfg, ndb)
    face.grant_authorization("AV-A", "tpl_ok", "longterm", now=T1)
    face.close()
    # additive reopen: the same db file (pre-revoke era or not) gains
    # the revokes table at next construction (CREATE IF NOT EXISTS)
    face = N.PayNotifyFace(cfg, ndb)
    az = AZ.AuthorizeFace(face)
    r1 = face.revoke_authorization("AV-A", "tpl_ok", now=T2)
    row = revoke_row(ndb, "AV-A")
    receipt_ok = (r1["status"] == "revoked"
                  and len(r1["revoke_id"]) == 16
                  and r1["template_id"] == "tpl_ok"
                  and r1["ts_utc"] == T2
                  and r1["ai_service"] == 1
                  and isinstance(r1["disclaimer"], str)
                  and r1["disclaimer"])
    row_ok = (row is not None and row[0] == r1["revoke_id"]
              and row[1] == "AV-A" and row[2] == "tpl_ok"
              and row[3] == T2)
    record("AC-VR1",
           schema_has and no_update and az_no_db and receipt_ok
           and row_ok,
           "schema=%s no-UPDATE=%s az-no-db=%s receipt=%s row=%s"
           % (schema_has, no_update, az_no_db, receipt_ok, row_ok))

    # ---- AC-VR2: revoke semantics + live-only budget ---------------
    face.grant_authorization("AV-B", "tpl_ok", "once", now=T3)
    face.grant_authorization("AV-B", "tpl_ok", "once", now=T4)
    b_pre = face.budget_face("AV-B", "tpl_ok")
    r2 = face.revoke_authorization("AV-B", "tpl_ok", now=T5)
    b_post = face.budget_face("AV-B", "tpl_ok")
    # post-cutoff grant is live; pre-cutoff grants stay dead
    face.grant_authorization("AV-B", "tpl_ok", "once", now=T6)
    b_rearm = face.budget_face("AV-B", "tpl_ok")
    # nothing_to_revoke: zero-grant avatar + idempotent re-revoke
    r3a = face.revoke_authorization("AV-NONE", "tpl_ok", now=T6)
    r3b = face.revoke_authorization("AV-NONE", "tpl_ok", now=T7)
    none_rows = revoke_rows(ndb, "AV-NONE")
    ok2 = (b_pre == {"once": 2, "longterm": 0, "consumed": 0}
           and r2["status"] == "revoked"
           and b_post == {"once": 0, "longterm": 0, "consumed": 0}
           and b_rearm == {"once": 1, "longterm": 0, "consumed": 0}
           and r3a["status"] == "nothing_to_revoke"
           and r3b["status"] == "nothing_to_revoke"
           and r3a["revoke_id"] is None
           and none_rows == 0)
    record("AC-VR2", ok2,
           "pre=%s revoke=%s post=%s rearm=%s none=%s rows=%d"
           % (b_pre, r2["status"], b_post, b_rearm, r3a["status"],
              none_rows))

    # ---- AC-VR4: re-subscribe cycle (authorize face) -----------------
    az.authorize("AV-C", "tpl_ok", "longterm")
    rev1 = az.revoke("AV-C", "tpl_ok")
    time.sleep(1.2)                       # past the ts_utc second edge
    reg1 = az.authorize("AV-C", "tpl_ok", "longterm")
    reg1_ok = (reg1["status"] == "granted"
               and reg1["budget"]["longterm"] == 1)
    rev2 = az.revoke("AV-C", "tpl_ok")
    time.sleep(1.2)
    reg2 = az.authorize("AV-C", "tpl_ok", "longterm")
    cycle_ok = (rev1["status"] == "revoked"
                and rev2["status"] == "revoked"
                and reg2["status"] == "granted"
                and reg2["budget"]["longterm"] == 1)
    # once re-arm: old units never resurrect; the revoke also kills the
    # LIVE longterm from reg2 (ruling 1: whole-subscription kill)
    az.authorize("AV-C", "tpl_ok", "once")
    az.authorize("AV-C", "tpl_ok", "once")
    b_before = az.budget("AV-C", "tpl_ok")
    az.revoke("AV-C", "tpl_ok")
    time.sleep(1.2)
    rearm = az.authorize("AV-C", "tpl_ok", "once")
    rearm_ok = (rearm["status"] == "granted"
                and rearm["budget"]["once"] == 1
                and rearm["budget"]["longterm"] == 0)
    # ruling-2 same-second edge, deterministic explicit timestamps
    face.grant_authorization("AV-S", "tpl_ok", "longterm", now=T1)
    face.revoke_authorization("AV-S", "tpl_ok", now=T2)
    face.grant_authorization("AV-S", "tpl_ok", "longterm", now=T2)
    edge = face.authorization_state("AV-S", "tpl_ok")
    edge_ok = (edge["revoked"] is True and edge["longterm"] == 0)
    record("AC-VR4", reg1_ok and cycle_ok and rearm_ok and edge_ok,
           "reg1=%s cycle=%s once-rearm=%s (pre=%s whole-kill longterm"
           " %d->0) same-second-edge=%s"
           % (reg1_ok, cycle_ok, rearm_ok, b_before,
              b_before.get("longterm", -1), edge_ok))

    # ---- AC-VR5: authorization_state read face ----------------------
    st_none = face.authorization_state("AV-NONE", "tpl_ok")
    keys = {"avatar", "template_id", "once", "longterm", "consumed",
            "remaining_once", "revoked", "revoke_ts"}
    none_ok = (set(st_none.keys()) == keys
               and st_none["revoked"] is False
               and st_none["revoke_ts"] is None
               and st_none["once"] == 0 and st_none["longterm"] == 0
               and st_none["remaining_once"] == 0)
    st_rev = face.authorization_state("AV-B", "tpl_ok")
    rev_ok = (st_rev["revoked"] is False   # post-cutoff once unit live
              and st_rev["once"] == 1
              and st_rev["remaining_once"] == 1
              and st_rev["revoke_ts"] == T5)
    face.revoke_authorization("AV-B", "tpl_ok", now=T7)
    st_dead = face.authorization_state("AV-B", "tpl_ok")
    dead_ok = (st_dead["revoked"] is True
               and st_dead["once"] == 0 and st_dead["longterm"] == 0
               and st_dead["revoke_ts"] == T7)
    # exhausted once WITHOUT a revoke is NOT revoked (honest distinction)
    w5 = TW.build_wired()
    az5 = AZ.AuthorizeFace(w5["face"])
    az5.authorize("AV-R5", "tpl_ok", "once")
    TW.flow(w5, "pack_compute_19_9", "AV-R5", "vr5-1")
    st_ex = w5["face"].authorization_state("AV-R5", "tpl_ok")
    ex_ok = (st_ex["once"] == 1 and st_ex["consumed"] == 1
             and st_ex["remaining_once"] == 0
             and st_ex["revoked"] is False)
    TW.drop(w5)
    record("AC-VR5", none_ok and rev_ok and dead_ok and ex_ok,
           "fresh=%s live=%s dead=%s exhausted-not-revoked=%s"
           % (none_ok, rev_ok, dead_ok, ex_ok))

    # ---- AC-VR3: send-side consumption (wired world) -----------------
    w3 = TW.build_wired()
    az3 = AZ.AuthorizeFace(w3["face"])
    az3.authorize("AV-R3", "tpl_ok", "longterm")
    az3.authorize("AV-R3", "tpl_ok", "once")
    az3.authorize("AV-R3", "tpl_ok", "once")
    o1, _, e1 = TW.flow(w3, "pack_compute_19_9", "AV-R3", "vr3-1")
    sent_pre = len(sent_rows_for(w3["face"], "AV-R3"))
    az3.revoke("AV-R3", "tpl_ok")
    b_dead = w3["face"].budget_face("AV-R3", "tpl_ok")
    o2, _, e2 = TW.flow(w3, "birthright_entry", "AV-R3", "vr3-2")
    n2 = (e2.get("notify") or {})
    banner = w3["face"].banner_queue()
    granted_both = all(w3["pay"].order_detail(o)["status"] == "granted"
                        for o in (o1, o2))
    # re-arm with a fresh once unit; consumed is cutoff-filtered so the
    # PRE-revoke sent row must not eat the new unit (sleep past the
    # ts_utc second boundary: ruling-2 same-second conservative edge)
    time.sleep(1.2)
    az3.authorize("AV-R3", "tpl_ok", "once")
    b_rearmed = w3["face"].budget_face("AV-R3", "tpl_ok")
    o3, _, e3 = TW.flow(w3, "share_observation", "AV-R3", "vr3-3")
    n3 = (e3.get("notify") or {})
    sent_immutable = len(sent_rows_for(w3["face"], "AV-R3"))
    ok3 = (e1["notify"]["status"] == "sent"
           and sent_pre == 1
           and b_dead == {"once": 0, "longterm": 0, "consumed": 0}
           and n2["status"] == "skipped_no_budget"
           and granted_both
           and len([r for r in banner if r[1] == "AV-R3"]) == 1
           and b_rearmed == {"once": 1, "longterm": 0, "consumed": 0}
           and n3["status"] == "sent"
           and sent_immutable == 2)
    TW.drop(w3)
    record("AC-VR3", ok3,
           "pre-sent=%d dead-budget=%s skipped=%s granted=%s banner=%d"
           " rearm=%s resend=%s immutable-sent=%d"
           % (sent_pre, b_dead, n2.get("status"), granted_both,
              len([r for r in banner if r[1] == "AV-R3"]),
              b_rearmed, n3.get("status"), sent_immutable))

    # ---- AC-VR6: authorize revoke gates ------------------------------
    pre6 = revoke_rows(ndb)
    e6a, m6a = expect_value_error(
        lambda: az.revoke("", "tpl_ok"), AZ.E_AZ_BAD_ARGS)
    e6b, m6b = expect_value_error(
        lambda: az.revoke(None, "tpl_ok"), AZ.E_AZ_BAD_ARGS)
    e6c, m6c = expect_value_error(
        lambda: az.revoke("   ", "tpl_ok"), AZ.E_AZ_BAD_ARGS)
    e6d, m6d = expect_value_error(
        lambda: az.revoke("AV-G", "tpl_missing"), N.E_PN_UNKNOWN_TEMPLATE)
    mid6 = revoke_rows(ndb)
    # approved deliberately NOT gated on revocation (stop action)
    cfg_un = TN.notify_cfg(TP.load_pay_config(), approved=False)
    db_un = os.path.join(tmp, "unapproved.db")
    face_un = N.PayNotifyFace(cfg_un, db_un)
    face_un.grant_authorization("AV-U", "tpl_ok", "longterm", now=T1)
    az_un = AZ.AuthorizeFace(face_un)
    grant_refused, _ = expect_value_error(
        lambda: az_un.authorize("AV-U", "tpl_ok", "once"),
        N.E_TEMPLATE_NOT_APPROVED)
    r_un = az_un.revoke("AV-U", "tpl_ok")
    un_rows = revoke_rows(db_un, "AV-U")
    face_un.close()
    ok6 = (e6a and e6b and e6c and e6d and mid6 == pre6
           and grant_refused and r_un["status"] == "revoked"
           and un_rows == 1)
    record("AC-VR6", ok6,
           "empty=%s(%s) none=%s(%s) blank=%s(%s) unknown-tpl=%s(%s)"
           " rows=%d->%d; grant-refused=%s revoke-on-unapproved=%s"
           " rows=%d"
           % (e6a, m6a, e6b, m6b, e6c, m6c, e6d, m6d, pre6, mid6,
              grant_refused, r_un["status"], un_rows))

    # ---- AC-VR7: hygiene + registration ------------------------------
    raw_n = open(os.path.join(BASE, "notify.py"), "rb").read()
    raw_a = open(os.path.join(BASE, "authorize.py"), "rb").read()
    ok_ascii = all(b < 128 for b in raw_n + raw_a)
    import_lines = [ln.strip() for ln in
                    (nsrc + asrc).splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    net_hits = [ln for ln in import_lines
                if any(w in ln for w in
                       ("urllib", "requests", "socket", "http"))]
    bf_keys = set(face.budget_face("AV-NONE", "tpl_ok").keys())
    keys_ok = bf_keys == {"once", "longterm", "consumed"}
    reg_src = open(os.path.join(
        os.path.dirname(BASE), "reconcile_all.py"),
        encoding="ascii").read()
    reg_ok = ('("pay-notify-revoke",'
              ' os.path.join("pay", "test_notify_revoke.py"), 7),'
              in reg_src)
    record("AC-VR7", ok_ascii and not net_hits and keys_ok and reg_ok
           and no_update,
           "ascii=%s net-imports=%s budget-keys=%s registered=%s"
           " no-UPDATE=%s"
           % (ok_ascii, net_hits or "none", sorted(bf_keys), reg_ok,
              no_update))

    face.close()
    shutil.rmtree(tmp, ignore_errors=True)
    fails = [ac for ac, ok in RESULTS if not ok]
    print("---- pay-notify-revoke acceptance: %d/%d passed"
          % (len(RESULTS) - len(fails), len(RESULTS)))
    if fails:
        print("FAILED: %s" % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
