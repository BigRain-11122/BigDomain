"""Acceptance suite for the authorize idempotency-cache restart
semantics example (BigDomain R1886 tech-queue claim; seed = the
R1885 reseed line). The authorize.py file header carries an honest
boundary note - "restart survival is out of sandbox scope - a
post-restart replay re-grants one fresh once unit at most, longterm
stays gate-idempotent" - and this suite pins that note live:

  - in-TTL replay of the same request_id is absorbed (status
    already_granted, original grant_id preserved, zero new rows);
  - the cache keys on request_id only (a different rid, or no rid
    at all, grants fresh - re-accept is the legitimate W15
    default path);
  - the FIFO cap eviction is honest (an evicted key re-grants on
    replay while a survivor still absorbs);
  - a TTL-expired replay re-grants one fresh once unit (re-accept
    is legitimate semantics, not a double-grant bug);
  - across a close -> new-instance restart, a once replay grants
    exactly one fresh unit (the documented boundary), while a
    longterm replay stays gate-idempotent (already_longterm, zero
    new rows - gate E popup suppression is immune to cache loss);
  - a second restart reproduces the same boundary and the new
    instance's in-TTL absorption works again;
  - grant-row arithmetic closes (per-avatar counts equal the
    grant calls - no doubling, no swallowing) and the log table
    stays at zero rows (this suite never sends).

Asserts the pre-registered criteria AC-PN44..AC-PN50 from the
R1886 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Determinism caliber (claim ruling 4): evidence carries statuses,
counts and budget dicts only - zero ts / grant-id value echo -
so two runs print byte-identical stdout.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_authorize_idem.py
"""

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import test_pay as TP                    # noqa: E402 (config loader)
import test_pay_notify as TN             # noqa: E402 (config scaffold)
import notify as N                       # noqa: E402 (face under test)
import authorize as AZ                   # noqa: E402 (subject)

RESULTS = []
EXPECTED = 7

TPL = "tpl_ok"

CFG_PATH = os.path.join(BASE, "config.json")
NOTIFY_PATH = os.path.join(BASE, "notify.py")
AZ_PATH = os.path.join(BASE, "authorize.py")

RECEIPT_KEYS = {"status", "grant_id", "template_id", "grant_type",
                "budget"}
BUDGET_KEYS = {"once", "longterm", "consumed"}

# Expected per-avatar grant-row closure (AC-PN49): every authorize
# call that passed all gates wrote exactly one row; absorbed,
# suppressed and cap-evicted replays wrote none.
EXP_AV_ONCE = 6     # R1 + R2 + None + None + restart replay x2
EXP_AV_LT = 1       # original longterm only (replays suppressed)
EXP_AV_CAP = 4      # c1 + c2 + c3 + evicted-c1 replay
EXP_AV_EXP = 2      # original + TTL-expired replay
EXP_TOTAL = EXP_AV_ONCE + EXP_AV_LT + EXP_AV_CAP + EXP_AV_EXP


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def q(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def gcount(db, avatar=None):
    if avatar is None:
        return int(q(db, "SELECT COUNT(*) FROM"
                        " pay_notify_grants")[0][0])
    return int(q(db, "SELECT COUNT(*) FROM pay_notify_grants"
                 " WHERE census_avatar_id=?", (avatar,))[0][0])


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    tmp = tempfile.mkdtemp(prefix="az-idem-")
    sha_cfg_in = sha_of(CFG_PATH)
    sha_notify_in = sha_of(NOTIFY_PATH)
    sha_az_in = sha_of(AZ_PATH)

    db = os.path.join(tmp, "azidem.db")
    cfg = TN.notify_cfg(TP.load_pay_config())

    # ---- instance #1: absorption window (ttl 30s) ---------------
    f1 = N.PayNotifyFace(cfg, db)
    az1 = AZ.AuthorizeFace(f1, ttl_seconds=30.0)

    r1 = az1.authorize("AV-ONCE", TPL, "once", request_id="rid-A")
    gid1 = r1["grant_id"]
    c0 = gcount(db)

    # AC-PN44: in-TTL replay of the same request_id is absorbed
    rp = az1.authorize("AV-ONCE", TPL, "once", request_id="rid-A")
    ok44 = (r1["status"] == "granted" and gid1
            and rp["status"] == "already_granted"
            and rp["grant_id"] == gid1
            and rp["template_id"] == TPL
            and rp["grant_type"] == "once"
            and set(rp.keys()) == RECEIPT_KEYS
            and rp["budget"] == {"once": 1, "longterm": 0,
                                 "consumed": 0}
            and az1.budget("AV-ONCE", TPL) == {"once": 1,
                                               "longterm": 0,
                                               "consumed": 0}
            and gcount(db) == c0 == 1)
    record("AC-PN44", ok44,
           "r1=%s replay=%s gid_preserved=%s keys_ok=%s "
           "budget=%s live_budget=%s rows=%d->%d"
           % (r1["status"], rp["status"],
              rp["grant_id"] == gid1,
              set(rp.keys()) == RECEIPT_KEYS,
              rp["budget"], az1.budget("AV-ONCE", TPL),
              c0, gcount(db)))

    # AC-PN45: keying on request_id only + honest FIFO cap
    r2 = az1.authorize("AV-ONCE", TPL, "once", request_id="rid-B")
    n1 = az1.authorize("AV-ONCE", TPL, "once")
    n2 = az1.authorize("AV-ONCE", TPL, "once")
    b_once = az1.budget("AV-ONCE", TPL)
    keying_ok = (r2["status"] == "granted"
                 and n1["status"] == "granted"
                 and n2["status"] == "granted"
                 and b_once == {"once": 4, "longterm": 0,
                                "consumed": 0}
                 and gcount(db, "AV-ONCE") == 4)
    # cap probe: a second authorize face over the same notify face,
    # max_keys=2 -> insertion-order FIFO eviction
    azc = AZ.AuthorizeFace(f1, max_keys=2)
    c1 = azc.authorize("AV-CAP", TPL, "once", request_id="rid-c1")
    c2 = azc.authorize("AV-CAP", TPL, "once", request_id="rid-c2")
    c3 = azc.authorize("AV-CAP", TPL, "once", request_id="rid-c3")
    e1 = azc.authorize("AV-CAP", TPL, "once", request_id="rid-c1")
    s3 = azc.authorize("AV-CAP", TPL, "once", request_id="rid-c3")
    cap_ok = (c1["status"] == "granted" and c2["status"] == "granted"
              and c3["status"] == "granted"
              and e1["status"] == "granted"
              and e1["grant_id"] != c1["grant_id"]
              and s3["status"] == "already_granted"
              and s3["grant_id"] == c3["grant_id"]
              and azc.budget("AV-CAP", TPL) == {"once": 4,
                                               "longterm": 0,
                                               "consumed": 0}
              and gcount(db, "AV-CAP") == 4)
    record("AC-PN45", keying_ok and cap_ok,
           "keying: r2=%s none=%s,%s budget=%s rows=%d | cap: "
           "c1=%s c2=%s c3=%s evicted_replay=%s(new_gid=%s) "
           "survivor=%s(same_gid=%s) budget=%s rows=%d"
           % (r2["status"], n1["status"], n2["status"], b_once,
              gcount(db, "AV-ONCE"),
              c1["status"], c2["status"], c3["status"],
              e1["status"], e1["grant_id"] != c1["grant_id"],
              s3["status"], s3["grant_id"] == c3["grant_id"],
              azc.budget("AV-CAP", TPL), gcount(db, "AV-CAP")))

    # longterm anchor on instance #1 (grant + in-TTL absorption)
    rl1 = az1.authorize("AV-LT", TPL, "longterm",
                        request_id="rid-LT")
    rl1p = az1.authorize("AV-LT", TPL, "longterm",
                          request_id="rid-LT")
    lt_anchor_ok = (rl1["status"] == "granted"
                    and rl1p["status"] == "already_granted"
                    and rl1p["grant_id"] == rl1["grant_id"]
                    and gcount(db, "AV-LT") == 1)

    # AC-PN46: TTL-expired replay re-grants one fresh unit
    az1b = AZ.AuthorizeFace(f1, ttl_seconds=1.0)
    x1 = az1b.authorize("AV-EXP", TPL, "once", request_id="rid-X")
    xp = az1b.authorize("AV-EXP", TPL, "once", request_id="rid-X")
    time.sleep(1.3)                     # past the 1.0s TTL window
    xe = az1b.authorize("AV-EXP", TPL, "once", request_id="rid-X")
    ok46 = (x1["status"] == "granted"
            and xp["status"] == "already_granted"
            and xe["status"] == "granted"
            and xe["grant_id"] != x1["grant_id"]
            and az1b.budget("AV-EXP", TPL) == {"once": 2,
                                              "longterm": 0,
                                              "consumed": 0}
            and gcount(db, "AV-EXP") == 2)
    record("AC-PN46", ok46,
           "lt_anchor=%s,%s(rows=%d) | ttl: first=%s pre_expiry=%s "
           "post_expiry=%s(new_gid=%s) budget=%s rows=%d"
           % (rl1["status"], rl1p["status"], gcount(db, "AV-LT"),
              x1["status"], xp["status"], xe["status"],
              xe["grant_id"] != x1["grant_id"],
              az1b.budget("AV-EXP", TPL), gcount(db, "AV-EXP")))

    # ---- restart #1: new instances, in-memory cache is lost -----
    pre_total = gcount(db)
    pre_once = gcount(db, "AV-ONCE")
    f1.close()
    f2 = N.PayNotifyFace(cfg, db)
    az2 = AZ.AuthorizeFace(f2, ttl_seconds=30.0)

    # AC-PN47: cross-restart once replay grants exactly one fresh
    # unit (the documented header boundary, pinned live)
    rp2 = az2.authorize("AV-ONCE", TPL, "once", request_id="rid-A")
    ok47 = (rp2["status"] == "granted"
            and rp2["grant_id"] != gid1
            and gcount(db) == pre_total + 1
            and gcount(db, "AV-ONCE") == pre_once + 1
            and az2.budget("AV-ONCE", TPL) == {"once": 5,
                                               "longterm": 0,
                                               "consumed": 0})
    record("AC-PN47", ok47,
           "replay=%s new_gid=%s rows=%d->%d av_once=%d->%d "
           "budget=%s"
           % (rp2["status"], rp2["grant_id"] != gid1,
              pre_total, gcount(db),
              pre_once, gcount(db, "AV-ONCE"),
              az2.budget("AV-ONCE", TPL)))

    # AC-PN48: cross-restart longterm replay stays gate-idempotent
    pre_lt = gcount(db, "AV-LT")
    pre_total2 = gcount(db)
    rl2 = az2.authorize("AV-LT", TPL, "longterm",
                        request_id="rid-LT")
    ok48 = (lt_anchor_ok
            and rl2["status"] == "already_longterm"
            and rl2["grant_id"] is None
            and rl2["template_id"] == TPL
            and rl2["grant_type"] == "longterm"
            and set(rl2.keys()) == RECEIPT_KEYS
            and az2.budget("AV-LT", TPL) == {"once": 0,
                                            "longterm": 1,
                                            "consumed": 0}
            and gcount(db, "AV-LT") == pre_lt == 1
            and gcount(db) == pre_total2)
    record("AC-PN48", ok48,
           "replay=%s gid_none=%s keys_ok=%s budget=%s rows=%d "
           "total=%d->%d"
           % (rl2["status"], rl2["grant_id"] is None,
              set(rl2.keys()) == RECEIPT_KEYS,
              az2.budget("AV-LT", TPL), gcount(db, "AV-LT"),
              pre_total2, gcount(db)))

    # ---- restart #2: boundary stability + absorption return ----
    pre_total3 = gcount(db)
    f2.close()
    f3 = N.PayNotifyFace(cfg, db)
    az3 = AZ.AuthorizeFace(f3, ttl_seconds=30.0)

    rp3 = az3.authorize("AV-ONCE", TPL, "once", request_id="rid-A")
    rp3b = az3.authorize("AV-ONCE", TPL, "once",
                          request_id="rid-A")
    rl3 = az3.authorize("AV-LT", TPL, "longterm",
                        request_id="rid-LT")
    st_once = az3.state("AV-ONCE", TPL)
    av_once = gcount(db, "AV-ONCE")
    av_lt = gcount(db, "AV-LT")
    av_cap = gcount(db, "AV-CAP")
    av_exp = gcount(db, "AV-EXP")
    log_rows = int(q(db, "SELECT COUNT(*) FROM"
                     " pay_notify_log")[0][0])
    ok49 = (rp3["status"] == "granted"
            and gcount(db) == pre_total3 + 1
            and rp3b["status"] == "already_granted"
            and rp3b["grant_id"] == rp3["grant_id"]
            and rl3["status"] == "already_longterm"
            and rl3["grant_id"] is None
            and av_once == EXP_AV_ONCE
            and av_lt == EXP_AV_LT
            and av_cap == EXP_AV_CAP
            and av_exp == EXP_AV_EXP
            and gcount(db) == EXP_TOTAL
            and st_once["remaining_once"] == EXP_AV_ONCE
            and st_once["revoked"] is False
            and st_once["revoke_ts"] is None
            and log_rows == 0)
    record("AC-PN49", ok49,
           "replay2=%s rows=%d->%d absorb_back=%s(same_gid=%s) "
           "lt_still=%s closure: once=%d/%d lt=%d/%d cap=%d/%d "
           "exp=%d/%d total=%d/%d remaining=%d revoked=%s "
           "log_rows=%d"
           % (rp3["status"], pre_total3, gcount(db),
              rp3b["status"], rp3b["grant_id"] == rp3["grant_id"],
              rl3["status"],
              av_once, EXP_AV_ONCE, av_lt, EXP_AV_LT,
              av_cap, EXP_AV_CAP, av_exp, EXP_AV_EXP,
              gcount(db), EXP_TOTAL, st_once["remaining_once"],
              st_once["revoked"], log_rows))

    # ---- hygiene -------------------------------------------------
    sha_cfg_out = sha_of(CFG_PATH)
    sha_notify_out = sha_of(NOTIFY_PATH)
    sha_az_out = sha_of(AZ_PATH)
    ascii_ok = all(ord(c) < 128 for c in
                   open(os.path.abspath(__file__),
                        encoding="utf-8").read())
    ok50 = (sha_cfg_out == sha_cfg_in
            and sha_notify_out == sha_notify_in
            and sha_az_out == sha_az_in
            and not os.path.abspath(db).startswith(
                os.path.abspath(BASE))
            and ascii_ok)
    record("AC-PN50", ok50,
           "cfg_stable=%s notify_stable=%s az_stable=%s "
           "world_outside=%s ascii=%s"
           % (sha_cfg_out == sha_cfg_in,
              sha_notify_out == sha_notify_in,
              sha_az_out == sha_az_in,
              not os.path.abspath(db).startswith(
                  os.path.abspath(BASE)),
              ascii_ok))

    f3.close()
    shutil.rmtree(tmp, ignore_errors=True)

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
