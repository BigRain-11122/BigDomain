"""AC-M17 assertion suite (subscribe-message reminder face, W10/W15).

Pre-registered criteria live in membership-spec.md section 1 (AC-M17,
registered before implementation). This suite reuses the test_member
world builder (real pay grants -> real activations) and verifies the
reminder face against the member sandbox:

  AC-M17.1  timepoints      : not-due scan empty; due-window scan fires
  AC-M17.2  template gate   : unapproved/unknown template -> refused,
                              zero log rows
  AC-M17.3  banned copy     : banned template copy -> config refused
                              (fail-closed, AC-M15 same method)
  AC-M17.4  budget 2 types  : once grant = 1 send then exhausted;
                              longterm grant = unlimited sends
  AC-M17.5  daily cap       : small injected cap -> sent capped at N,
                              overflow rows skipped_daily_cap
  AC-M17.6  zero-silent-loss: every due attempt lands exactly one row;
                              banner queue == all skipped rows
  AC-M17.7  idempotent scan : same-day rescan -> already_logged, rows
                              unchanged
  AC-M17.8  fiat-free schema: reminder tables carry zero fiat/token
                              column vocabulary; raw fiat inject refused
  AC-M17.9  W10 dual timepoint: MVP manual renewal -> on_accept
                              not_required_mvp (zero rows, honest);
                              auto-renewal simulation flag -> both
                              timepoints covered
  AC-M17.10 regression      : reconcile six checks stay clean with the
                              reminder face wired (separate db file,
                              member single-writer untouched)

Run:
    python test_reminder.py
"""

import datetime
import json
import os
import shutil
import sqlite3
import sys

import test_member as TM                    # world builder (path dance)
import member as M                          # noqa: F401 (house imports)
import reconcile as RC
import reminder as RM

RESULTS = []
FIAT_TOKEN_SUBSTRINGS = ("price", "amount", "cent", "fee", "yuan", "rmb",
                         "cny", "token", "coin")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def rows(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def period_end(db, avatar):
    got = rows(db, "SELECT end_utc FROM member_periods"
                " WHERE census_avatar_id=? AND status='active'", (avatar,))
    return got[0][0]


def fmt(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    world = TM.build()
    face = None
    face2 = None
    try:
        store, mcfg = world["store"], world["mcfg"]
        mdb = world["member_db"]
        rdb = os.path.join(world["tmp"], "member_reminder.db")
        rdb2 = os.path.join(world["tmp"], "member_reminder2.db")

        avatars = ["AV-R1", "AV-R2", "AV-R3", "AV-R4",
                   "AV-C1", "AV-C2", "AV-C3"]
        for av in avatars:
            _oid, gid = TM.happy(world, "tier_experience", av, "n-" + av)
            store.activate(gid, av)
        ends = [M.parse_iso(period_end(mdb, av)) for av in avatars]
        now_before = fmt(min(ends) - datetime.timedelta(days=4))
        now_due = fmt(max(ends) - datetime.timedelta(days=3)
                      + datetime.timedelta(seconds=5))
        now_due2 = fmt(M.parse_iso(now_due) + datetime.timedelta(days=1))

        face = RM.ReminderFace(mcfg, rdb, member_db=mdb)
        face.grant_authorization("AV-R1", "renewal_notice", "once")
        face.grant_authorization("AV-R2", "renewal_notice", "longterm")
        face.grant_authorization("AV-R4", "renewal_notice", "longterm")

        # ---- AC-M17.1: timepoints (not due / due window) --------------
        early = face.scan(now=now_before)
        fired = face.scan(now=now_due)
        ok1 = (early == [] and len(fired) == len(avatars)
               and all(r["reason"] == "renewal_due" for r in fired))
        record("AC-M17.1", ok1,
               "not-due scan=%d; due-window scan=%d all renewal_due"
               % (len(early), len(fired)))

        # ---- AC-M17.6 (part): zero silent loss ------------------------
        log1 = rows(rdb, "SELECT status, census_avatar_id FROM"
                    " member_reminder_log")
        sent1 = [r for r in log1 if r[0] == "sent"]
        skip1 = [r for r in log1 if r[0].startswith("skipped")]
        r1row = [r for r in log1 if r[1] == "AV-R1"]
        ok6a = (len(log1) == len(avatars) and len(sent1) == 3
                and len(skip1) == 4 and len(r1row) == 1)
        record("AC-M17.6", ok6a,
               "%d due attempts -> %d rows (sent=%d skipped=%d);"
               " AV-R1 rows=%d" % (len(fired), len(log1), len(sent1),
                                   len(skip1), len(r1row)))

        # ---- AC-M17.4 (part): budget two types, day 1 ------------------
        ok4a = (any(r[1] == "AV-R1" and r[0] == "sent" for r in log1)
                and any(r[1] == "AV-R2" and r[0] == "sent" for r in log1)
                and any(r[1] == "AV-R3" and r[0] == "skipped_no_budget"
                        for r in log1))
        record("AC-M17.4", ok4a,
               "day1: once-grant AV-R1 sent, longterm AV-R2 sent,"
               " no-grant AV-R3 skipped_no_budget")

        # ---- AC-M17.7: idempotent same-day rescan ----------------------
        rescan = face.scan(now=now_due)
        log1b = rows(rdb, "SELECT COUNT(*) FROM member_reminder_log")
        ok7 = (all(r["status"] == "already_logged" for r in rescan)
               and log1b[0][0] == len(avatars))
        record("AC-M17.7", ok7,
               "rescan=%d already_logged; rows unchanged=%d"
               % (len(rescan), log1b[0][0]))

        # ---- AC-M17.4 (part): once budget exhausts, longterm unlimited --
        day2 = face.scan(now=now_due2)
        by = {}
        for r in day2:
            by[(r["reason"], r["status"])] = by.get(
                (r["reason"], r["status"]), 0) + 1
        r1d2 = rows(rdb, "SELECT status FROM member_reminder_log WHERE"
                    " census_avatar_id='AV-R1' AND status LIKE 'skipped%'")
        ok4b = (by.get(("renewal_due", "sent"), 0) == 2
                and by.get(("renewal_due", "skipped_no_budget"), 0) == 5
                and len(r1d2) == 1)
        record("AC-M17.4", ok4b,
               "day2: sent=%d (longterm only), skipped_no_budget=%d;"
               " once-grant AV-R1 exhausted -> skipped row=%s"
               % (by.get(("renewal_due", "sent"), 0),
                  by.get(("renewal_due", "skipped_no_budget"), 0),
                  r1d2[0][0] if r1d2 else "none"))

        # ---- AC-M17.6 (part): banner queue == all skipped rows ---------
        queue = face.banner_queue()
        skipped_rows = rows(rdb, "SELECT send_id FROM member_reminder_log"
                            " WHERE status LIKE 'skipped_%'")
        ok6b = len(queue) == len(skipped_rows) == 9
        record("AC-M17.6", ok6b,
               "banner_queue=%d == skipped rows=%d (zero silent loss)"
               % (len(queue), len(skipped_rows)))

        # ---- AC-M17.2: template review gate ----------------------------
        before = rows(rdb, "SELECT COUNT(*) FROM member_reminder_log")
        gate_ev = []
        try:
            face.attempt("AV-R1", "pending_review_example",
                         "renewal_due", now=now_due)
            gate_ev.append("unapproved accepted")
        except RM.TemplateNotApproved as exc:
            gate_ev.append("unapproved refused: %s" % exc)
        try:
            face.attempt("AV-R1", "no_such_template",
                         "renewal_due", now=now_due)
            gate_ev.append("unknown accepted")
        except ValueError as exc:
            gate_ev.append("unknown refused: %s" % exc)
        after = rows(rdb, "SELECT COUNT(*) FROM member_reminder_log")
        ok2 = (before[0][0] == after[0][0]
               and gate_ev[0].startswith("unapproved refused")
               and gate_ev[1].startswith("unknown refused")
               and RM.E_TEMPLATE_NOT_APPROVED in gate_ev[0])
        record("AC-M17.2", ok2, "; ".join(gate_ev)
               + "; log rows unchanged=%d" % after[0][0])

        # ---- AC-M17.3: banned template copy -> fail-closed config ------
        bad = json.loads(json.dumps(mcfg))
        bad["reminder"]["templates"]["renewal_notice"]["copy"] = \
            "会员保本提醒（违禁文案用例）"
        try:
            RM.ReminderFace(bad, os.path.join(world["tmp"], "bad.db"))
            ev3 = "banned copy accepted"
            ok3 = False
        except RM.ConfigRejected as exc:
            ev3 = "banned copy refused: %s" % exc
            ok3 = RM.E_BANNED_TEMPLATE_COPY in str(exc)
        record("AC-M17.3", ok3, ev3)

        # ---- AC-M17.5: daily send cap (scaled injection) ---------------
        capcfg = json.loads(json.dumps(mcfg))
        capcfg["reminder"]["daily_send_cap_default"] = 2
        face2 = RM.ReminderFace(capcfg, rdb2, member_db=mdb)
        for av in avatars:
            face2.grant_authorization(av, "renewal_notice", "once")
        capped = face2.scan(now=now_due)
        stats = {}
        for r in capped:
            stats[r["status"]] = stats.get(r["status"], 0) + 1
        rescan2 = face2.scan(now=now_due)
        ok5 = (stats.get("sent", 0) == 2
               and stats.get("skipped_daily_cap", 0) == len(avatars) - 2
               and all(r["status"] == "already_logged" for r in rescan2))
        record("AC-M17.5", ok5,
               "cap=2: sent=%d, skipped_daily_cap=%d; rescan already_logged"
               % (stats.get("sent", 0),
                  stats.get("skipped_daily_cap", 0)))

        # ---- AC-M17.9: W10 dual timepoint (honest MVP face) -------------
        mvp = face.on_accept("AV-R4", now=now_due, auto_renewal=False)
        fs_before = rows(rdb, "SELECT COUNT(*) FROM member_reminder_log"
                         " WHERE census_avatar_id='AV-R4'"
                         " AND reason='first_service'")
        auto = face.on_accept("AV-R4", now=now_due, auto_renewal=True)
        coverage = face.dual_timepoint_coverage("AV-R4")
        ok9 = (mvp["status"] == "not_required_mvp" and fs_before[0][0] == 0
               and auto["status"] == "sent"
               and coverage == {"first_service", "renewal_due"})
        record("AC-M17.9", ok9,
               "MVP on_accept=%s (rows=%d, no fake activity);"
               " auto-renewal sim on_accept=%s; coverage=%s"
               % (mvp["status"], fs_before[0][0], auto["status"],
                  sorted(coverage)))

        # ---- AC-M17.8: fiat/token-free schema ---------------------------
        hits = []
        for table in ("member_subscribe_grants", "member_reminder_log"):
            for row in rows(rdb, "PRAGMA table_info(%s)" % table):
                low = str(row[1]).lower()
                if any(s in low for s in FIAT_TOKEN_SUBSTRINGS):
                    hits.append("%s.%s" % (table, row[1]))
        conn = sqlite3.connect(rdb)
        try:
            try:
                conn.execute("INSERT INTO member_reminder_log"
                             " (price_cent) VALUES (1)")
                inject = "accepted"
            except sqlite3.OperationalError as exc:
                inject = str(exc)
        finally:
            conn.close()
        ok8 = (not hits and ("no such column" in inject
                             or "no column named" in inject))
        record("AC-M17.8", ok8,
               "fiat/token-named columns=%s; raw fiat inject refused=%s"
               % (hits or "none", inject))

        # ---- AC-M17.10: reconcile regression ----------------------------
        fails = RC.run_checks(mdb, world["pay_db"], world["ledger_db"],
                              mcfg)
        record("AC-M17.10", not fails,
               "reconcile six checks clean=%s%s"
               % (not fails, "" if not fails else " (%s)" % fails[:3]))
    finally:
        if face is not None:
            face.close()
        if face2 is not None:
            face2.close()
        TM.tear(world)

    failed = [ac for ac, ok in RESULTS if not ok]
    counts = {}
    for ac, _ in RESULTS:
        counts[ac] = counts.get(ac, 0) + 1
    print("suite: %d assertions over %d criteria; failed=%s"
          % (len(RESULTS), len(counts), failed or "none"), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
