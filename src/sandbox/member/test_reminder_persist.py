"""Acceptance suite for the reminder authorization + read-face
family cross-restart persistence window (R1959 reseed claim,
registered as R1962 in state/queue/tech.md BEFORE this code;
honesty law).

Pre-registered criteria AC-RMP1..AC-RMP7 (tech.md claim line).
Seat boundary (registered ruling): the banner queue/board window+cap
persistence semantics are covered by the member-banner-queue-persist
and banner-board-persist seats (AC-MB family) - this seat does not
re-prove them. This seat pins: the authorization budget faces
(grant rows, budget arithmetic, idempotency keys), the W10
dual-timepoint faces (on_accept both states), the due-scan
idempotent re-entry, and the read-face family snapshot (banner_board
default envelope, dual_timepoint_coverage, daily_sent_count) across
full close/reopen restarts of the reminder face's own sqlite file
(the member store itself is NOT this seat's restart focus - its
persistence is carried by sibling seats like expiring_soon_persist;
honest note).

Design rulings (registered in the claim line): restart = both faces
closed then same-cfg same-db reopen with the expiring_face callable
re-injected (caller-held wiring, R1779 law); determinism = every
timestamp is injected (attempt/scan/grant_authorization/on_accept/
daily_sent_count all take now), evidence echoes zero wall-clock
values and zero raw ids (double-run stdout determinism face).

Usage: python test_reminder_persist.py
"""

import datetime
import hashlib
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
for _p in (BASE,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import test_member as TM                 # world primitives
import member as M                       # parse_iso (test-side math)
import reminder as RM

RESULTS = []
EXPECTED = 7
NETLIB_RE = re.compile(
    r"^\s*(?:import|from)\s+(urllib|requests|socket|http)\b", re.M)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      default=str)


def rows(db, sql, args=()):
    return TM.db_query(db, sql, args)


def fmt(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def face_snapshot(face, rdb, avatars, day_ts):
    """Six-face snapshot (native values; compared via sort_keys dumps
    at judgment time): authorization journal dump, send/skip log dump,
    per-avatar log slices, banner_board default envelope,
    dual_timepoint coverage for every avatar, daily sent count at the
    anchor day."""
    s = {}
    s["grants"] = rows(
        rdb, "SELECT * FROM member_subscribe_grants ORDER BY rowid")
    s["log"] = rows(
        rdb, "SELECT * FROM member_reminder_log ORDER BY rowid")
    s["log_by_av"] = {
        av: rows(rdb, "SELECT * FROM member_reminder_log WHERE"
                 " census_avatar_id=? ORDER BY rowid", (av,))
        for av in avatars}
    s["board"] = face.banner_board()
    s["cov"] = {av: sorted(face.dual_timepoint_coverage(av))
                for av in avatars}
    s["dsc"] = face.daily_sent_count(now=day_ts)
    return s


def snap_diff(a, b):
    if set(a) != set(b):
        return sorted(set(a) ^ set(b))
    return [k for k in a if dumps(a[k]) != dumps(b[k])]


def log_count(rdb):
    return rows(rdb, "SELECT COUNT(*) FROM member_reminder_log")[0][0]


def grant_count(rdb):
    return rows(
        rdb, "SELECT COUNT(*) FROM member_subscribe_grants")[0][0]


def member_counts(mdb):
    c = {}
    for tab in ("member_periods", "member_audit",
                "member_credit_events", "member_vouchers"):
        c[tab] = rows(mdb, "SELECT COUNT(*) FROM %s" % tab)[0][0]
    return dumps(c)


def active_period(mdb, avatar):
    return rows(mdb, "SELECT period_id, end_utc FROM member_periods"
               " WHERE census_avatar_id=? AND status='active'",
               (avatar,))[0]


def attempt_status(rdb, avatar, reason, period_key, day):
    hit = rows(rdb, "SELECT status FROM member_reminder_log"
               " WHERE census_avatar_id=? AND reason=?"
               " AND COALESCE(period_key,'')=? AND substr(ts_utc,1,10)=?",
               (avatar, reason, period_key or "", day))
    return hit[0][0] if hit else None


def main():
    shipped_cfg = os.path.join(BASE, "config.json")
    product_srcs = [os.path.join(BASE, "reminder.py"),
                    os.path.join(BASE, "member.py")]
    cfg_sha_before = sha256_file(shipped_cfg)
    prod_sha_before = [sha256_file(p) for p in product_srcs]

    world = TM.build()
    faces = []
    face = None
    capface = None
    try:
        store, mcfg, mdb = world["store"], world["mcfg"], world["member_db"]
        rdb = os.path.join(world["tmp"], "member_reminder.db")
        rcap = os.path.join(world["tmp"], "member_reminder_cap.db")

        P1, P2, P3, P4, P5 = ("RMP-P1", "RMP-P2", "RMP-P3",
                              "RMP-P4", "RMP-P5")
        Q1, Q2 = "RMP-Q1", "RMP-Q2"
        main_avs = [P1, P2, P3, P4, P5]
        cap_avs = [Q1, Q2]

        # three real member periods so the due-scan faces carry real
        # period keys (same tier, activated back-to-back)
        for av in (P1, P2, P3):
            _oid, gid = TM.happy(world, "tier_experience", av, "rmp-" + av)
            store.activate(gid, av)

        # frozen anchor timestamps derived from the real world
        ends = [active_period(mdb, av)[1] for av in (P1, P2, P3)]
        ts_due = fmt(M.parse_iso(min(ends))
                     - datetime.timedelta(days=1))
        D1 = str(ts_due)[:10]
        D1_A = D1 + "T08:00:00Z"
        D1_B = D1 + "T09:00:00Z"
        D2_A = fmt(M.parse_iso(ts_due) + datetime.timedelta(days=1))
        R = int(mcfg["reminder"]["remind_days_before"])
        periods = {av: active_period(mdb, av)[0] for av in (P1, P2, P3)}

        # ---- world construction (main + cap faces) -------------------
        face = RM.ReminderFace(mcfg, rdb, expiring_face=store.expiring_soon)
        capcfg = json.loads(json.dumps(mcfg))
        capcfg["reminder"]["daily_send_cap_default"] = 2
        capface = RM.ReminderFace(capcfg, rcap,
                                  expiring_face=store.expiring_soon)
        faces.append(face)
        faces.append(capface)

        # ---- AC-RMP1: anchor world + pre-restart multi-face snapshot --
        face.grant_authorization(P1, "renewal_notice", "longterm", now=D1_A)
        face.grant_authorization(P2, "renewal_notice", "once", now=D1_A)
        # second once unit: distinct injected ts (grant_id derives from
        # the accept moment - two accepts never share one ts in
        # production; same-ts injection would collide the deterministic
        # PK, harness calibration noted honestly)
        face.grant_authorization(P2, "renewal_notice", "once", now=D1_B)
        face.grant_authorization(P4, "renewal_notice", "longterm", now=D1_A)
        mvp = face.on_accept(P4, now=D1_A, auto_renewal=False)
        auto_p4 = face.on_accept(P4, now=D1_A, auto_renewal=True)
        auto_p5 = face.on_accept(P5, now=D1_A, auto_renewal=True)
        scan_res = face.scan(now=ts_due)
        board = store.expiring_soon(R, ts_due)
        due_avs = {row["census_avatar_id"] for row in board["expiring_soon"]
                   if row["end_utc"] > board["as_of"]}
        scan_by_av = {av: attempt_status(rdb, av, "renewal_due",
                                         periods[av], D1)
                      for av in due_avs}
        expected_scan = {av: ("sent" if av in (P1, P2)
                              else "skipped_no_budget")
                        for av in due_avs}
        re_p1 = face.attempt(P1, "renewal_notice", "renewal_due",
                             now=D1_B, period_key=periods[P1])
        gate_pre = log_count(rdb)
        gates = []
        try:
            face.attempt(P1, "pending_review_example", "renewal_due",
                         now=D1_B)
            gates.append("unapproved accepted")
        except RM.TemplateNotApproved as exc:
            gates.append("unapproved refused: %s" % exc)
        try:
            face.attempt(P1, "no_such_template", "renewal_due", now=D1_B)
            gates.append("unknown accepted")
        except ValueError as exc:
            gates.append("unknown refused: %s" % exc)
        gate_post = log_count(rdb)
        capface.grant_authorization(Q1, "renewal_notice", "longterm",
                                    now=D1_A)
        capface.grant_authorization(Q2, "renewal_notice", "longterm",
                                    now=D1_A)
        cq1 = capface.attempt(Q1, "renewal_notice", "renewal_due",
                              now=D1_A, period_key="rmp-q1-a")
        cq2 = capface.attempt(Q2, "renewal_notice", "renewal_due",
                              now=D1_A, period_key="rmp-q2-a")
        cq1b = capface.attempt(Q1, "renewal_notice", "renewal_due",
                              now=D1_B, period_key="rmp-q1-b")
        snap1 = face_snapshot(face, rdb, main_avs, D1_A)
        csnap1 = face_snapshot(capface, rcap, cap_avs, D1_A)
        ok1 = (mvp["status"] == "not_required_mvp"
               and auto_p4["status"] == "sent"
               and auto_p5["status"] == "skipped_no_budget"
               and due_avs == {P1, P2, P3}
               and scan_by_av == expected_scan
               and re_p1["status"] == "already_logged"
               and gate_pre == gate_post
               and gates[0].startswith("unapproved refused")
               and gates[1].startswith("unknown refused")
               and RM.E_TEMPLATE_NOT_APPROVED in gates[0]
               and RM.E_UNKNOWN_TEMPLATE in gates[1]
               and cq1["status"] == "sent" and cq2["status"] == "sent"
               and cq1b["status"] == "skipped_daily_cap"
               and len(snap1) == 6 and len(csnap1) == 6
               and log_count(rdb) == 5 and grant_count(rdb) == 4
               and log_count(rcap) == 3 and grant_count(rcap) == 2
               and all(s is not None for s in scan_by_av.values()))
        record("AC-RMP1", ok1,
               "world: mvp=%s p4=%s p5=%s; scan due=%d match=%s;"
               " dup=%s; gates=%s/%s rows %d==%d; cap=%s,%s,%s;"
               " main log=%d grants=%d cap log=%d grants=%d"
               % (mvp["status"] == "not_required_mvp",
                  auto_p4["status"], auto_p5["status"], len(due_avs),
                  scan_by_av == expected_scan, re_p1["status"],
                  gates[0].split(":")[0], gates[1].split(":")[0],
                  gate_pre, gate_post, cq1["status"], cq2["status"],
                  cq1b["status"], log_count(rdb), grant_count(rdb),
                  log_count(rcap), grant_count(rcap)))

        # ---- AC-RMP2: cross-restart byte identity ---------------------
        face.close()
        capface.close()
        face = RM.ReminderFace(mcfg, rdb, expiring_face=store.expiring_soon)
        capface = RM.ReminderFace(capcfg, rcap,
                                  expiring_face=store.expiring_soon)
        faces.append(face)
        faces.append(capface)
        snap2 = face_snapshot(face, rdb, main_avs, D1_A)
        csnap2 = face_snapshot(capface, rcap, cap_avs, D1_A)
        diff = snap_diff(snap1, snap2)
        cdiff = snap_diff(csnap1, csnap2)
        ok2 = not diff and not cdiff
        record("AC-RMP2", ok2,
               "restart identical=%s; main diff=%s cap diff=%s;"
               " faces=%d/%d"
               % (ok2, diff, cdiff, len(snap2), len(csnap2)))

        # ---- AC-RMP3: idempotency keys + gates post-restart -----------
        pre3 = log_count(rdb)
        rescan = face.scan(now=ts_due)
        rescan_ok = all(r["status"] == "already_logged" for r in rescan)
        mid3 = log_count(rdb)
        re_p1b = face.attempt(P1, "renewal_notice", "renewal_due",
                              now=D1_B, period_key=periods[P1])
        auto_p4b = face.on_accept(P4, now=D1_B, auto_renewal=True)
        mvp_p5b = face.on_accept(P5, now=D1_B, auto_renewal=False)
        gates2 = []
        try:
            face.attempt(P2, "pending_review_example", "renewal_due",
                         now=D1_B)
            gates2.append("unapproved accepted")
        except RM.TemplateNotApproved as exc:
            gates2.append("unapproved refused: %s" % exc)
        try:
            face.attempt(P2, "no_such_template", "renewal_due", now=D1_B)
            gates2.append("unknown accepted")
        except ValueError as exc:
            gates2.append("unknown refused: %s" % exc)
        post3 = log_count(rdb)
        ok3 = (rescan_ok and len(rescan) == 3
               and pre3 == mid3 == post3
               and re_p1b["status"] == "already_logged"
               and auto_p4b["status"] == "already_logged"
               and mvp_p5b["status"] == "not_required_mvp"
               and gates2[0].startswith("unapproved refused")
               and gates2[1].startswith("unknown refused"))
        record("AC-RMP3", ok3,
               "rescan=%d all already_logged=%s; attempt=%s on_accept=%s;"
               " mvp=%s; gates refused=%s/%s; rows %d==%d==%d"
               % (len(rescan), rescan_ok, re_p1b["status"],
                  auto_p4b["status"], mvp_p5b["status"],
                  gates2[0].split(":")[0], gates2[1].split(":")[0],
                  pre3, mid3, post3))

        # ---- AC-RMP4: budget arithmetic + fresh faces + zero-drift ---
        p2a = face.attempt(P2, "renewal_notice", "renewal_due",
                          now=D1_B, period_key="rmp-p2-b")
        p2b = face.attempt(P2, "renewal_notice", "renewal_due",
                          now=D1_B, period_key="rmp-p2-c")
        face.grant_authorization(P3, "renewal_notice", "once", now=D1_B)
        p3a = face.attempt(P3, "renewal_notice", "renewal_due",
                          now=D1_B, period_key="rmp-p3-b")
        cq1c = capface.attempt(Q1, "renewal_notice", "renewal_due",
                              now=D1_B, period_key="rmp-q1-c")
        cq1d = capface.attempt(Q1, "renewal_notice", "renewal_due",
                              now=D2_A, period_key="rmp-q1-d")
        snap4 = face_snapshot(face, rdb, main_avs, D1_A)
        csnap4 = face_snapshot(capface, rcap, cap_avs, D1_A)
        drift = [av for av in (P1, P4, P5)
                 if dumps(snap1["log_by_av"][av])
                 != dumps(snap4["log_by_av"][av])]
        cov_drift = [av for av in (P1, P4, P5)
                     if snap1["cov"][av] != snap4["cov"][av]]
        ok4 = (p2a["status"] == "sent"
               and p2b["status"] == "skipped_no_budget"
               and p3a["status"] == "sent"
               and cq1c["status"] == "skipped_daily_cap"
               and cq1d["status"] == "sent"
               and not drift and not cov_drift)
        record("AC-RMP4", ok4,
               "budget: p2 sent->exhausted=%s,%s; p3 fresh grant->sent=%s;"
               " cap same-day=%s next-day=%s; untouched drift=%s"
               " cov drift=%s"
               % (p2a["status"], p2b["status"], p3a["status"],
                  cq1c["status"], cq1d["status"], drift, cov_drift))

        # ---- AC-RMP5: pure-read law -----------------------------------
        def all_counts():
            return dumps({"mg": grant_count(rdb), "ml": log_count(rdb),
                          "cg": grant_count(rcap), "cl": log_count(rcap),
                          "member": member_counts(mdb)})
        c1 = all_counts()
        face_snapshot(face, rdb, main_avs, D1_A)
        face_snapshot(capface, rcap, cap_avs, D1_A)
        face.banner_board()
        face.daily_sent_count(now=D1_A)
        c2 = all_counts()
        ok5 = c1 == c2
        record("AC-RMP5", ok5,
               "read-batch counts stable=%s" % ok5)

        # ---- AC-RMP6: second restart stability ------------------------
        face.close()
        capface.close()
        face = RM.ReminderFace(mcfg, rdb, expiring_face=store.expiring_soon)
        capface = RM.ReminderFace(capcfg, rcap,
                                  expiring_face=store.expiring_soon)
        faces.append(face)
        faces.append(capface)
        snap6 = face_snapshot(face, rdb, main_avs, D1_A)
        csnap6 = face_snapshot(capface, rcap, cap_avs, D1_A)
        diff6 = snap_diff(snap4, snap6)
        cdiff6 = snap_diff(csnap4, csnap6)
        cap_new_rows = rows(
            rcap, "SELECT COUNT(*) FROM member_reminder_log"
            " WHERE period_key IN ('rmp-q1-c','rmp-q1-d')")[0][0]
        main_new_rows = rows(
            rdb, "SELECT COUNT(*) FROM member_reminder_log"
            " WHERE period_key IN ('rmp-p2-b','rmp-p2-c','rmp-p3-b')")[0][0]
        ok6 = (not diff6 and not cdiff6
               and cap_new_rows == 2 and main_new_rows == 3)
        record("AC-RMP6", ok6,
               "second restart identical=%s; main diff=%s cap diff=%s;"
               " post-restart rows carried: main=%d cap=%d"
               % (ok6, diff6, cdiff6, main_new_rows, cap_new_rows))

        # ---- AC-RMP7: hygiene -----------------------------------------
        cfg_sha_after = sha256_file(shipped_cfg)
        prod_sha_after = [sha256_file(p) for p in product_srcs]
        with open(os.path.abspath(__file__), "rb") as fh:
            src = fh.read()
        ascii_ok = all(b < 128 for b in src)
        net_hits = NETLIB_RE.findall(src.decode("ascii", "replace"))
        repo_root = os.path.normpath(os.path.join(BASE, "..", "..", ".."))
        tmp_ok = (not os.path.realpath(world["tmp"]).startswith(
            os.path.realpath(repo_root)))
        all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
        with open(all_path, encoding="utf-8") as fh:
            all_text = fh.read()
        registry_ok = ('"member-reminder-persist"' in all_text
                       and "test_reminder_persist.py" in all_text)
        ok7 = (cfg_sha_after == cfg_sha_before
               and prod_sha_after == prod_sha_before
               and ascii_ok and not net_hits and tmp_ok and registry_ok)
        record("AC-RMP7", ok7,
               "config sha stable=%s; product srcs stable=%s;"
               " ascii=%s; net imports=%d; worlds outside repo=%s;"
               " registry line=%s"
               % (cfg_sha_after == cfg_sha_before,
                  prod_sha_after == prod_sha_before, ascii_ok,
                  len(net_hits), tmp_ok, registry_ok))
    finally:
        for f in faces:
            try:
                f.close()
            except Exception:
                pass
        TM.tear(world)

    if len(RESULTS) != EXPECTED:
        print("SUITE FAIL: criteria drift %d != %d"
              % (len(RESULTS), EXPECTED))
        return 2
    failed = [ac for ac, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL: %s" % ",".join(failed))
        return 2
    print("SUITE PASS: %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
