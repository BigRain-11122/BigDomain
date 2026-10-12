"""Acceptance suite for the authorize budget_face/authorization_state
read cross-restart persistence example (BigDomain R1885 tech-queue
claim; seed = the R1884 reseed line - the revocation suites
AC-VR1..VR7 and the authorize suite AC-AZ1..AZ7 proved their faces
inside ONE process lifetime; this closes the family gap: close ->
brand-new instance -> same-db reopen must reproduce the live-budget
read faces byte-identically (zero in-memory drift), the R1740
revocation cutoff must keep excluding pre-cutoff grants/sends after
the restart, and the post-restart cycle (nothing_to_revoke no-op,
post-cutoff re-arm, exhausted-once honest state) must behave on the
reopened instance exactly as the in-lifetime suites showed.

Asserts the pre-registered criteria AC-PN37..AC-PN43 from the R1885
tech.md claim line (criteria were registered before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Carrier verdict (R1884 same family): a fresh isolated face instance
in its own temp world drives the TRUE product write paths end to
end - grants land via notify.grant_authorization (explicit ts, the
authorize face's own write dock), sends land via
notify_payment_success() on granted orders (budget actually
consumed), the revoke lands via revoke_authorization (explicit ts);
zero fixture injection into pay_notify_* tables.

World (all template tpl_ok; explicit timestamps, zero real clock):
  AV-LT    longterm x1 @T1, send @T2            -> {0,1,1}
           (remaining_once=-1 honest negative: consumed counts all
            sent rows for a longterm holder, no clamping)
  AV-ONCE  once x2 @T1, send#1 @T2              -> {2,0,1}
           post-restart send#2 @NOV2            -> {2,0,2}
  AV-RVK   longterm+once x2 @T1, send @T2,
           revoke @T3 (cutoff)                   -> {0,0,0} revoked
           post-restart re-arm once @NOV         -> {1,0,0}
  AV-EMPTY nothing                              -> {0,0,0}

Instance #1 builds October + snapshots the 8 read faces
(4 avatars x az.budget/az.state); instance #2 reopens the same db,
proves byte-identity, then drives the November cycle (no-op
re-revoke, re-arm, second send, longterm suppression); instance #3
reopens once more and reproduces the whole post-cycle state.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_authorize_persist.py
"""

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (fixture reuse)
import test_pay_notify as TN             # noqa: E402 (scaffold reuse)
import notify as N                       # noqa: E402 (face under test)
import authorize as AZ                   # noqa: E402 (subject)

RESULTS = []
EXPECTED = 7

T1 = "2026-10-05T10:00:00Z"             # October grants
T2 = "2026-10-05T10:00:01Z"             # October sends
T3 = "2026-10-05T10:00:02Z"             # October revoke cutoff
NOV = "2026-11-03T09:00:00Z"            # post-restart re-arm
NOV2 = "2026-11-03T09:00:01Z"           # post-restart send #2

TPL = "tpl_ok"
AVATARS = ("AV-LT", "AV-ONCE", "AV-RVK", "AV-EMPTY")

CFG_PATH = os.path.join(BASE, "config.json")
NOTIFY_PATH = os.path.join(BASE, "notify.py")
AZ_PATH = os.path.join(BASE, "authorize.py")

BUDGET_KEYS = {"once", "longterm", "consumed"}
STATE_KEYS = {"avatar", "template_id", "once", "longterm", "consumed",
              "remaining_once", "revoked", "revoke_ts"}


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True, default=str)


def q(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def anchor(db):
    """Row-set anchor across the three tables (pure-read law)."""
    return (q(db, "SELECT send_id, census_avatar_id, order_id, reason,"
                  " status, ts_utc FROM pay_notify_log"
                  " ORDER BY send_id"),
            q(db, "SELECT grant_id, census_avatar_id, template_id,"
                  " grant_type, ts_utc FROM pay_notify_grants"
                  " ORDER BY grant_id"),
            q(db, "SELECT revoke_id, census_avatar_id, template_id,"
                  " ts_utc FROM pay_notify_revokes ORDER BY revoke_id"))


def eight_faces(az):
    """The eight derived read faces of the persistence example
    (4 avatars x the two authorize docks)."""
    out = {}
    for av in AVATARS:
        out["budget:" + av] = az.budget(av, TPL)
        out["state:" + av] = az.state(av, TPL)
    return out


def snap(faces):
    return {k: dumps(v) for k, v in faces.items()}


def main():
    tmp = tempfile.mkdtemp(prefix="az-persist-")
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    notify_sha_in = hashlib.sha256(
        open(NOTIFY_PATH, "rb").read()).hexdigest()
    az_sha_in = hashlib.sha256(
        open(AZ_PATH, "rb").read()).hexdigest()

    world = TP.build(mint=True)
    pay_db = os.path.join(world["tmp"], "pay.db")
    oid_lt, _ = TP.happy(world, "pack_compute_19_9", "AV-LT",
                         nonce="azp-lt")
    oid_once1, _ = TP.happy(world, "pack_compute_19_9", "AV-ONCE",
                            nonce="azp-o1")
    oid_once2, _ = TP.happy(world, "birthright_entry", "AV-ONCE",
                            nonce="azp-o2")
    oid_rvk, _ = TP.happy(world, "pack_compute_19_9", "AV-RVK",
                          nonce="azp-rv")

    db = os.path.join(tmp, "azpersist.db")
    cfg = TN.notify_cfg(TP.load_pay_config())

    # ---- instance #1: October anchor + pre-restart snapshot -------
    f1 = N.PayNotifyFace(cfg, db, pay_db=pay_db)
    az1 = AZ.AuthorizeFace(f1)
    f1.grant_authorization("AV-LT", TPL, "longterm", now=T1)
    f1.grant_authorization("AV-ONCE", TPL, "once", now=T1)
    f1.grant_authorization("AV-ONCE", TPL, "once", now=T1)  # tie
    f1.grant_authorization("AV-RVK", TPL, "longterm", now=T1)
    f1.grant_authorization("AV-RVK", TPL, "once", now=T1)
    f1.grant_authorization("AV-RVK", TPL, "once", now=T1)    # tie
    s_lt = f1.notify_payment_success(oid_lt, now=T2)
    s_o1 = f1.notify_payment_success(oid_once1, now=T2)
    s_rv = f1.notify_payment_success(oid_rvk, now=T2)
    rev1 = f1.revoke_authorization("AV-RVK", TPL, now=T3)

    pre_a = anchor(db)
    faces1 = eight_faces(az1)
    s1 = snap(faces1)
    post_a = anchor(db)

    b = faces1
    ok37 = (s_lt["status"] == "sent" and s_o1["status"] == "sent"
            and s_rv["status"] == "sent"
            and rev1["status"] == "revoked"
            and b["budget:AV-LT"] == {"once": 0, "longterm": 1,
                                      "consumed": 1}
            and b["state:AV-LT"]["remaining_once"] == -1
            and b["state:AV-LT"]["revoked"] is False
            and b["budget:AV-ONCE"] == {"once": 2, "longterm": 0,
                                        "consumed": 1}
            and b["state:AV-ONCE"]["remaining_once"] == 1
            and b["state:AV-ONCE"]["revoked"] is False
            and b["state:AV-ONCE"]["revoke_ts"] is None
            and b["budget:AV-RVK"] == {"once": 0, "longterm": 0,
                                       "consumed": 0}
            and b["state:AV-RVK"]["revoked"] is True
            and b["state:AV-RVK"]["revoke_ts"] == T3
            and b["state:AV-RVK"]["remaining_once"] == 0
            and b["budget:AV-EMPTY"] == {"once": 0, "longterm": 0,
                                         "consumed": 0}
            and b["state:AV-EMPTY"]["revoked"] is False
            and b["state:AV-EMPTY"]["revoke_ts"] is None
            and all(set(b["budget:" + a].keys()) == BUDGET_KEYS
                    for a in AVATARS)
            and all(set(b["state:" + a].keys()) == STATE_KEYS
                    for a in AVATARS))
    record("AC-PN37", ok37,
           "sends=%s revoke=%s lt=%s once=%s rvk=%s empty=%s "
           "key_sets=%s"
           % ([s_lt["status"], s_o1["status"], s_rv["status"]],
              rev1["status"],
              [b["budget:AV-LT"], b["state:AV-LT"]["remaining_once"]],
              [b["budget:AV-ONCE"],
               b["state:AV-ONCE"]["remaining_once"]],
              [b["state:AV-RVK"]["revoked"],
               b["state:AV-RVK"]["revoke_ts"]],
              b["state:AV-EMPTY"],
              all(set(b["budget:" + a].keys()) == BUDGET_KEYS
                  for a in AVATARS)
              and all(set(b["state:" + a].keys()) == STATE_KEYS
                      for a in AVATARS)))

    # ---- instance #2: same-db reopen, byte-identity ----------------
    f1.close()
    f2 = N.PayNotifyFace(cfg, db, pay_db=pay_db)
    az2 = AZ.AuthorizeFace(f2)
    faces2 = eight_faces(az2)
    s2 = snap(faces2)
    ok38 = (s2 == s1
            and faces2["state:AV-RVK"]["revoked"] is True
            and faces2["state:AV-LT"]["remaining_once"] == -1)
    record("AC-PN38", ok38,
           "all_eight_byte_identical=%s rvk_revoked=%s lt_neg=%s"
           % (s2 == s1,
              faces2["state:AV-RVK"]["revoked"],
              faces2["state:AV-LT"]["remaining_once"]))

    # ---- cutoff continuation across restart (revoke window) -------
    rr = f2.revoke_authorization("AV-RVK", TPL, now=NOV)
    rvk_rows = q(db, "SELECT COUNT(*) FROM pay_notify_revokes")[0][0]
    f2.grant_authorization("AV-RVK", TPL, "once", now=NOV)
    b_rvk = az2.budget("AV-RVK", TPL)
    st_rvk = az2.state("AV-RVK", TPL)
    ok39 = (rr["status"] == "nothing_to_revoke"
            and rr["revoke_id"] is None
            and rvk_rows == 1
            and b_rvk == {"once": 1, "longterm": 0, "consumed": 0}
            and st_rvk["revoked"] is False
            and st_rvk["revoke_ts"] == T3
            and st_rvk["remaining_once"] == 1
            and int(q(db, "SELECT COUNT(*) FROM pay_notify_grants"
                         " WHERE census_avatar_id='AV-RVK'"
                         " AND ts_utc>?", (T3,))[0][0]) == 1)
    record("AC-PN39", ok39,
           "rerevoke=%s rvk_rows=%d rearm_budget=%s revoked=%s "
           "cutoff_kept=%s postcutoff_grants=%d"
           % (rr["status"], rvk_rows, b_rvk, st_rvk["revoked"],
              st_rvk["revoke_ts"],
              int(q(db, "SELECT COUNT(*) FROM pay_notify_grants"
                        " WHERE census_avatar_id='AV-RVK'"
                        " AND ts_utc>?", (T3,))[0][0])))

    # ---- post-restart drift: second send + suppression + empty ----
    grants_before = int(q(db, "SELECT COUNT(*) FROM"
                              " pay_notify_grants")[0][0])
    s_o2 = f2.notify_payment_success(oid_once2, now=NOV2)
    st_o = az2.state("AV-ONCE", TPL)
    sup = az2.authorize("AV-LT", TPL, "longterm")
    grants_after = int(q(db, "SELECT COUNT(*) FROM"
                             " pay_notify_grants")[0][0])
    b_empty = az2.budget("AV-EMPTY", TPL)
    ok40 = (s_o2["status"] == "sent"
            and st_o["once"] == 2 and st_o["consumed"] == 2
            and st_o["remaining_once"] == 0
            and st_o["revoked"] is False
            and sup["status"] == "already_longterm"
            and sup["grant_id"] is None
            and grants_after == grants_before
            and b_empty == {"once": 0, "longterm": 0, "consumed": 0})
    record("AC-PN40", ok40,
           "send2=%s once_state=%s suppressed=%s grant_rows=%d->%d "
           "empty=%s"
           % (s_o2["status"],
              [st_o["once"], st_o["consumed"],
               st_o["remaining_once"], st_o["revoked"]],
              sup["status"], grants_before, grants_after, b_empty))

    # ---- post-cycle snapshot + pure-read law (instance #2) --------
    pre_b = anchor(db)
    faces2n = eight_faces(az2)
    s2n = snap(faces2n)
    post_b = anchor(db)
    ok41 = (pre_a == post_a            # instance #1 read batch
            and pre_b == post_b        # instance #2 read batch
            and int(q(db, "SELECT COUNT(*) FROM"
                         " pay_notify_log")[0][0]) == 4
            and int(q(db, "SELECT COUNT(*) FROM"
                         " pay_notify_grants")[0][0]) == 7
            and int(q(db, "SELECT COUNT(*) FROM"
                         " pay_notify_revokes")[0][0]) == 1)
    record("AC-PN41", ok41,
           "i1_batch_clean=%s i2_batch_clean=%s log=%d grants=%d "
           "revokes=%d"
           % (pre_a == post_a, pre_b == post_b, 4, 7, 1))

    # ---- instance #3: double-restart stability ---------------------
    f2.close()
    f3 = N.PayNotifyFace(cfg, db, pay_db=pay_db)
    az3 = AZ.AuthorizeFace(f3)
    faces3 = eight_faces(az3)
    s3 = snap(faces3)
    ok42 = (s3 == s2n
            and faces3["state:AV-RVK"]["revoked"] is False
            and faces3["state:AV-RVK"]["revoke_ts"] == T3
            and faces3["state:AV-ONCE"]["remaining_once"] == 0
            and faces3["state:AV-ONCE"]["revoked"] is False
            and faces3["budget:AV-RVK"] == {"once": 1, "longterm": 0,
                                            "consumed": 0}
            and faces3["state:AV-LT"]["remaining_once"] == -1)
    record("AC-PN42", ok42,
           "i3_eq_postcycle=%s rvk_rearmed=%s once_exhausted=%s "
           "lt_neg=%s"
           % (s3 == s2n,
              [faces3["state:AV-RVK"]["revoked"],
               faces3["state:AV-RVK"]["revoke_ts"]],
              [faces3["state:AV-ONCE"]["remaining_once"],
               faces3["state:AV-ONCE"]["revoked"]],
              faces3["state:AV-LT"]["remaining_once"]))

    # ---- hygiene ----------------------------------------------------
    cfg_sha_out = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    notify_sha_out = hashlib.sha256(
        open(NOTIFY_PATH, "rb").read()).hexdigest()
    az_sha_out = hashlib.sha256(
        open(AZ_PATH, "rb").read()).hexdigest()
    ascii_ok = all(ord(c) < 128 for c in
                   open(os.path.abspath(__file__),
                        encoding="utf-8").read())
    ok43 = (cfg_sha_out == cfg_sha_in
            and notify_sha_out == notify_sha_in
            and az_sha_out == az_sha_in
            and not os.path.abspath(db).startswith(
                os.path.abspath(BASE))
            and ascii_ok)
    record("AC-PN43", ok43,
           "cfg_stable=%s notify_stable=%s az_stable=%s "
           "world_outside=%s ascii=%s"
           % (cfg_sha_out == cfg_sha_in,
              notify_sha_out == notify_sha_in,
              az_sha_out == az_sha_in,
              not os.path.abspath(db).startswith(
                  os.path.abspath(BASE)),
              ascii_ok))

    f3.close()
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(world["tmp"], ignore_errors=True)

    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s: %d/%d pass-lines"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), EXPECTED))
    if len(RESULTS) != EXPECTED or fails:
        print("SUITE FAIL: %s" % fails)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
