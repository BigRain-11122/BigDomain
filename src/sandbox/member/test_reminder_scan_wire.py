"""Acceptance suite for the reminder due-scan read-face wiring
(tech.md claim line R1779).

Asserts the pre-registered criteria AC-RW1..AC-RW7 (registered in
state/queue/tech.md BEFORE this code; honesty law).

Subject: ReminderFace.scan rewiring - the renewal-due scan consumes
the member pre-expiry read face (MemberStore.expiring_soon, R1774)
through an injected callable instead of its own SQL + window
arithmetic. The face is the single window-derivation source; the
due set is the board's still-running subset (end_utc strictly past
as_of; the exactly-expired boundary row rides the board but is not
due - AC-ES5 honest superset note). The reminder module performs
ZERO direct member.db access: reads flow through the injected
face's holder-side connection, so the member single-writer
discipline is untouched.

Usage: python test_reminder_scan_wire.py
"""

import datetime
import inspect
import json
import os
import re
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
for _p in (BASE,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import test_member as TM                    # world builder (path dance)
import member as M                           # window math (test-side only)
import reminder as RM

RESULTS = []
EXPECTED = 7
SRC = inspect.getsource(RM)
NETLIB_RE = re.compile(
    r"^\s*(?:import|from)\s+(urllib|requests|socket|http)\b", re.M)


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def rows(db, sql, args=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def fmt(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def active_period(db, avatar):
    return rows(db, "SELECT period_id, end_utc FROM member_periods"
                " WHERE census_avatar_id=? AND status='active'",
                (avatar,))[0]


class CountingFace(object):
    """Proxy proving the scan reads member data through the injected
    callable ONLY (zero other member read paths)."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = []

    def __call__(self, days, now):
        self.calls.append((days, now))
        return self.inner(days, now)


def main():
    world = TM.build()
    faces = []
    try:
        store, mcfg = world["store"], world["mcfg"]
        mdb = world["member_db"]
        rdb = os.path.join(world["tmp"], "member_reminder.db")

        avatars = ["AV-W1", "AV-W2", "AV-W3"]
        for av in avatars:
            _oid, gid = TM.happy(world, "tier_experience", av, "n-" + av)
            store.activate(gid, av)
        face = RM.ReminderFace(mcfg, rdb,
                               expiring_face=store.expiring_soon)
        faces.append(face)
        R = face.days
        face.grant_authorization("AV-W1", "renewal_notice", "longterm")
        face.grant_authorization("AV-W3", "renewal_notice", "longterm")

        # ---- AC-RW1: wiring contract + second-derivation removal ------
        scan_src = inspect.getsource(RM.ReminderFace.scan)
        ok1 = ("member_db" not in SRC and "mode=ro" not in SRC
               and "SELECT" not in scan_src
               and "add_days" not in scan_src
               and "parse_iso" not in scan_src
               and "sqlite3.connect" not in scan_src
               and callable(face.expiring_face))
        bare = RM.ReminderFace(mcfg, os.path.join(world["tmp"], "bare.db"))
        faces.append(bare)
        refused = False
        try:
            bare.scan(now="2026-10-11T00:00:00Z")
        except ValueError:
            refused = True
        bare_rows = rows(bare.db_path, "SELECT COUNT(*) FROM"
                         " member_reminder_log")[0][0]
        ok1 = ok1 and refused and bare_rows == 0
        record("AC-RW1", ok1,
               "face-less scan refused=%s zero-rows=%d; scan source"
               " free of SQL/window tokens; old member dock gone"
               % (refused, bare_rows))

        # world facts for the equivalence + boundary faces
        periods = {av: active_period(mdb, av) for av in avatars}
        ends = {av: row[1] for av, row in periods.items()}
        ts_due = fmt(M.parse_iso(min(ends.values()))
                     - datetime.timedelta(days=1))

        # ---- AC-RW2: three-source equivalence on a frozen ts ---------
        fired = face.scan(now=ts_due)
        fired_ids = {r[0] for r in rows(
            rdb, "SELECT period_key FROM member_reminder_log")}
        board = store.expiring_soon(R, ts_due)
        board_due_ids = {row["period_id"]
                         for row in board["expiring_soon"]
                         if row["end_utc"] > board["as_of"]}
        horizon_manual = fmt(M.parse_iso(ts_due)
                             + datetime.timedelta(days=R))
        manual_ids = {r[0] for r in rows(
            mdb, "SELECT period_id FROM member_periods"
            " WHERE status='active' AND end_utc > ? AND end_utc <= ?",
            (ts_due, horizon_manual))}
        ok2 = (fired_ids == board_due_ids == manual_ids
               and len(fired) == len(avatars))
        record("AC-RW2", ok2,
               "three sources equal=%s; scan=%d board=%d manual=%d"
               % (fired_ids == board_due_ids == manual_ids,
                  len(fired_ids), len(board_due_ids), len(manual_ids)))

        # ---- AC-RW3: boundary row + not-due + due-window fire --------
        b_av = "AV-W2"
        b_pid, b_end = periods[b_av]
        board_b = store.expiring_soon(R, b_end)
        on_board = any(row["period_id"] == b_pid
                       for row in board_b["expiring_soon"])
        scan_b = face.scan(now=b_end)
        b_day_rows = rows(rdb, "SELECT COUNT(*) FROM member_reminder_log"
                          " WHERE period_key=? AND substr(ts_utc,1,10)=?",
                          (b_pid, str(b_end)[:10]))[0][0]
        early = face.scan(now=fmt(M.parse_iso(min(ends.values()))
                                  - datetime.timedelta(days=10)))
        ok3 = (on_board and b_day_rows == 0 and early == []
               and len(fired) == len(avatars))
        record("AC-RW3", ok3,
               "boundary row on board=%s zero-attempt=%d; not-due=%d;"
               " due-window fired=%d"
               % (on_board, b_day_rows, len(early), len(fired)))

        # ---- AC-RW4: idempotent same-day rescan + zero silent loss ----
        before = rows(rdb, "SELECT COUNT(*) FROM"
                      " member_reminder_log")[0][0]
        rescan = face.scan(now=ts_due)
        after = rows(rdb, "SELECT COUNT(*) FROM"
                     " member_reminder_log")[0][0]
        grouped = rows(rdb, "SELECT COUNT(*) FROM (SELECT"
                       " census_avatar_id, period_key,"
                       " substr(ts_utc,1,10) FROM member_reminder_log"
                       " GROUP BY 1,2,3 HAVING COUNT(*) > 1)")
        skip_row = rows(rdb, "SELECT status FROM member_reminder_log"
                        " WHERE census_avatar_id='AV-W2'"
                        " AND substr(ts_utc,1,10)=?", (str(ts_due)[:10],))
        banner_nob = any(r[1] == "AV-W2" for r in face.banner_queue())
        ok4 = (all(r["status"] == "already_logged" for r in rescan)
               and before == after and grouped[0][0] == 0
               and skip_row and skip_row[0][0] == "skipped_no_budget"
               and banner_nob)
        record("AC-RW4", ok4,
               "rescan=%d all already_logged rows %d==%d dup-groups=0;"
               " no-grant row=%s banner=%s"
               % (len(rescan), before, after,
                  skip_row[0][0] if skip_row else "none", banner_nob))

        # ---- AC-RW5: zero direct member dock + injected-face-only ----
        rdb3 = os.path.join(world["tmp"], "member_reminder3.db")
        proxy = CountingFace(store.expiring_soon)
        face3 = RM.ReminderFace(mcfg, rdb3, expiring_face=proxy)
        faces.append(face3)
        scan3 = face3.scan(now=ts_due)
        ok5 = ("mode=ro" not in SRC and "member_db" not in SRC
               and proxy.calls == [(R, ts_due)] and len(scan3) > 0)
        record("AC-RW5", ok5,
               "injected-face calls=%s results=%d; module free of"
               " direct member dock tokens=%s"
               % (proxy.calls, len(scan3),
                  ("mode=ro" not in SRC and "member_db" not in SRC)))

        # ---- AC-RW6: registry cross-check + criteria-count self-check -
        all_path = os.path.join(os.path.dirname(BASE), "reconcile_all.py")
        with open(all_path, encoding="utf-8") as fh:
            all_text = fh.read()
        wired = ('"member-reminder-scanwire"' in all_text
                 and "test_reminder_scan_wire.py" in all_text)
        prior = len(RESULTS)              # five criteria before, two remain
        ok6 = wired and prior == EXPECTED - 2
        record("AC-RW6", ok6,
               "suites-registry-line=%s prior-criteria=%d expected=%d"
               % (wired, prior, EXPECTED))

        # ---- AC-RW7: hygiene face --------------------------------------
        try:
            SRC.encode("ascii")
            ascii_ok = True
        except UnicodeEncodeError:
            ascii_ok = False
        net_hits = NETLIB_RE.findall(SRC)
        update_hits = re.findall(r"\bUPDATE\b", SRC)
        ok7 = ascii_ok and not net_hits and not update_hits
        record("AC-RW7", ok7,
               "ascii=%s network-imports=%d update-tokens=%d"
               % (ascii_ok, len(net_hits), len(update_hits)))
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
