"""AC-RQR1..AC-RQR7 suite: sec_batch rows_by_status / queue_counts
monthly-roll preservation example.

Criteria pre-registered in state/queue/tech.md (R1865 claim row,
registered BEFORE this code - honesty law). Suite convention: one
PASS line per criterion, SUITE tail line, exit 0 only when all green.

Faces under test across a frozen-clock +23d month roll:
  rows_by_status(status, window) and queue_counts(window) - the
  R1860 window params - preserved across the roll (R1730/R1838/R1839
  /R1845/R1854/R1858 month-roll family, rows/queue seat).

An independent world (own temp db + own face instance) carries the
roll example (R1859 banner_queue-roll precedent: the existing
test_sec_batch.py world reads the real-clock global queue, whose
roll reads would be polluted by real-month rows).

Landing uses check_batch's explicit ts param - the real product
path (record-time substr(ts_utc,1,7) window jurisdiction). The
StepClock(1.0) + default budget_ms=200 shape degrades exactly the
second text of each two-text call (first text passes and exhausts
the budget, the rest land queued ungated) - which lets a
banned-word text land queued (never gated) and later re-gate to
drained_rejected on the cross-month drain: fail-closed law exercised
across the roll. drain() writes status + ts_drained only, never
ts_utc - so a row drained in November still belongs to its landing
month window (R1860 AC-SB21 law, here enforced as the roll example).
"""

import json
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
for _p in (_LOBBY, BASE):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import ContentRejectedError, GateOfflineError, SecGate  # noqa: E402,F401
import sec_batch  # noqa: E402,F401
from sec_batch import SecBatchFace  # noqa: E402


class StepClock(object):
    """Injected clock: every call steps +1.0s (deterministic breach)."""

    def __init__(self, step=1.0):
        self.t = 0.0
        self.step = step

    def __call__(self):
        v = self.t
        self.t += self.step
        return v


def check(bad, ac, ok, evidence):
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)
    if not ok:
        bad.append(ac)


def rows_json(rows):
    return json.dumps([list(r) for r in rows], sort_keys=True)


def qids(rows):
    return set(r[0] for r in rows)


def sql_one(face, query, args=()):
    row = face.conn.execute(query, args).fetchone()
    return row[0] if row else None


def ts_map(face):
    rows = face.conn.execute(
        "SELECT qid, ts_utc FROM sec_degraded_queue").fetchall()
    return {str(q): str(t) for q, t in rows}


def main():
    bad = []
    tmp = tempfile.mkdtemp(prefix="secbatch-rowsroll-")
    db = os.path.join(tmp, "sec_degraded.db")
    gate = SecGate(["banned_alpha"], ["profit_promise_beta"])
    face = SecBatchFace(gate, db, config={}, clock=StepClock(1.0))

    # October: 6 queued rows (5 clean + 1 banned-word, ungated landing)
    oct_queued = [
        "queued oct %02d" % i for i in range(5)] + [
        "queued oct secret banned_alpha %02d" % 5]
    oct_ts = ["2026-10-15T10:00:%02dZ" % i for i in range(6)]
    for i, ts in enumerate(oct_ts):
        out = face.check_batch(
            ["clean oct %02d" % i, oct_queued[i]],
            source="rowsroll-oct", actor="actor-a", ts=ts)
        assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1

    # ---- AC-RQR1 October anchor --------------------------------------
    oct_sql = sql_one(
        face, "SELECT COUNT(*) FROM sec_degraded_queue"
        " WHERE status='queued' AND substr(ts_utc,1,7)='2026-10'")
    r_def = face.rows_by_status("queued")
    r_win = face.rows_by_status("queued", window="2026-10")
    c_def = face.queue_counts()
    c_win = face.queue_counts(window="2026-10")
    s_oct = rows_json(r_win)
    check(bad, "AC-RQR1",
          (oct_sql == 6 and len(r_def) == 6 and len(r_win) == 6
           and rows_json(r_def) == s_oct
           and c_def == {"queued": 6} and c_win == {"queued": 6}
           and c_def == c_win),
          "oct anchor: SQL record-time 2026-10 queued count==%d;"
          " default rows_by_status read == explicit 2026-10 window"
          " read (6 rows, byte-identical); queue_counts default =="
          " windowed == %r; snapshot S_oct locked"
          % (oct_sql, c_def))

    # ---- November: 4 new rows via the real product path ---------------
    nov_queued = [
        "queued nov %02d" % i for i in range(3)] + [
        "queued nov secret banned_alpha %02d" % 3]
    nov_ts = ["2026-11-07T09:30:%02dZ" % i for i in range(4)]
    for i, ts in enumerate(nov_ts):
        out = face.check_batch(
            ["clean nov %02d" % i, nov_queued[i]],
            source="rowsroll-nov", actor="actor-b", ts=ts)
        assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1

    # ---- AC-RQR2 new-month landing ------------------------------------
    nov_sql = sql_one(
        face, "SELECT COUNT(*) FROM sec_degraded_queue"
        " WHERE status='queued' AND substr(ts_utc,1,7)='2026-11'")
    r_nov = face.rows_by_status("queued", window="2026-11")
    r_all = face.rows_by_status("queued")
    check(bad, "AC-RQR2",
          (nov_sql == 4 and len(r_nov) == 4
           and qids(r_nov).isdisjoint(qids(r_win))
           and len(r_all) == 10
           and face.queue_counts() == {"queued": 10}),
          "roll landing: SQL record-time 2026-11 count==%d; windowed"
          " 2026-11 read = exactly the 4 new rows (zero overlap with"
          " S_oct); default all-window read = 10 rows (cross-month"
          " rows included); queue_counts==%r"
          % (nov_sql, face.queue_counts()))

    # ---- AC-RQR3 old-month window preservation ------------------------
    r_oct_after = face.rows_by_status("queued", window="2026-10")
    r_nov_after = face.rows_by_status("queued", window="2026-11")
    check(bad, "AC-RQR3",
          (rows_json(r_oct_after) == s_oct
           and face.queue_counts(window="2026-10") == {"queued": 6}
           and qids(r_nov_after).isdisjoint(qids(r_oct_after))),
          "old-month preservation: post-roll 2026-10 window read =="
          " S_oct byte-identical; queue_counts(2026-10)=={'queued':6}"
          " unchanged (nov rows never leak in); 2026-11 window read"
          " has zero oct qids (two windows never leak either way)")

    # ---- AC-RQR4 immutable rows never lost ----------------------------
    total_all = sql_one(face, "SELECT COUNT(*) FROM sec_degraded_queue")
    all_qids = qids(r_all)
    check(bad, "AC-RQR4",
          (total_all == 10 and len(all_qids) == 10
           and all_qids == qids(r_oct_after) | qids(r_nov_after)),
          "no-loss accounting: full-table COUNT 6 -> %d (constant"
          " growth, zero rows lost); global queued read carries all"
          " 10 distinct qids == oct-window set | nov-window set;"
          " queue_counts delta == 4 == new rows"
          % total_all)

    # ---- AC-RQR5 drain across the month + landing-month windows ------
    # Capture point honesty note: M_pre brackets the DRAIN itself -
    # captured with all 10 rows on the books, right before drain()
    # (capturing at the October anchor would compare a 6-row map to a
    # 10-row map and fail without any drain mutation - R1712
    # capture-point precedent family).
    m_pre = ts_map(face)
    drain_ts = "2026-11-07T23:00:00Z"
    drained = face.drain(ts=drain_ts)
    dp_oct = face.rows_by_status("drained_pass", window="2026-10")
    dr_oct = face.rows_by_status("drained_rejected", window="2026-10")
    dp_nov = face.rows_by_status("drained_pass", window="2026-11")
    dr_nov = face.rows_by_status("drained_rejected", window="2026-11")
    ts_drained_nov_drain = all(
        str(r[7]).startswith("2026-11") for r in dp_oct + dr_oct)
    q_oct_after_drain = face.rows_by_status("queued", window="2026-10")
    q_nov_after_drain = face.rows_by_status("queued", window="2026-11")
    check(bad, "AC-RQR5",
          (drained == {"drained": 10, "passed": 8, "rejected": 2,
                       "still_queued": 0}
           and len(dp_oct) == 5 and len(dr_oct) == 1
           and ts_drained_nov_drain
           and len(dp_nov) == 3 and len(dr_nov) == 1
           and face.queue_counts(window="2026-10")
           == {"drained_pass": 5, "drained_rejected": 1}
           and face.queue_counts(window="2026-11")
           == {"drained_pass": 3, "drained_rejected": 1}
           and face.queue_counts()
           == {"drained_pass": 8, "drained_rejected": 2}
           and q_oct_after_drain == [] and q_nov_after_drain == []),
          "drain x month-roll: drain(ts=nov) -> %r; oct-window"
          " drained_pass==5 rows each carrying a NOVEMBER ts_drained"
          " (landing-month window attribution, AC-SB21 law enforced);"
          " oct-window drained_rejected==1 (banned word re-gated"
          " fail-closed across the roll); nov-window 3+1;"
          " queue_counts windows follow the status transition without"
          " switching the row sets: 2026-10==%r, 2026-11==%r, all==%r;"
          " queued key vanishes from every window (sparse caliber)"
          % (drained, face.queue_counts(window="2026-10"),
             face.queue_counts(window="2026-11"), face.queue_counts()))

    # ---- AC-RQR6 row preservation, dual proof --------------------------
    m_post = ts_map(face)
    total_post = sql_one(face, "SELECT COUNT(*) FROM sec_degraded_queue")
    term_qids = qids(face.rows_by_status("drained_pass")) | qids(
        face.rows_by_status("drained_rejected"))
    check(bad, "AC-RQR6",
          (m_post == m_pre and total_post == 10
           and term_qids == all_qids),
          "row preservation: post-drain qid->ts_utc map == pre-drain"
          " map (drain never touches record-time identity); full-table"
          " COUNT still %d; union of terminal global reads == all 10"
          " original qids (zero-loss ledger)" % total_post)

    # ---- AC-RQR7 hygiene + runner wiring -------------------------------
    self_src = open(os.path.abspath(__file__), "rb").read()
    ascii_ok = all(b < 128 for b in self_src)
    net_imports = []
    for line in self_src.decode("ascii", "replace").splitlines():
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            if re.search(r"\burllib\b|\brequests\b|\bsocket\b|\bhttp\b",
                         s.split(" as ")[0]):
                net_imports.append(s)
    runner_txt = open(os.path.join(BASE, "..", "reconcile_all.py"),
                      encoding="utf-8").read()
    reg_ok = ('"ugc-sec-batch-rowsroll"' in runner_txt
              and runner_txt.count('"ugc-sec-batch-rowsroll"') == 1)
    check(bad, "AC-RQR7",
          (ascii_ok and not net_imports and reg_ok),
          "hygiene: suite source pure ASCII; true import lines carry"
          " zero network libraries; reconcile_all ugc-sec-batch-"
          "rowsroll wired exactly once (criteria 7); world = temp"
          " dir only, sec_batch.py untouched (git status evidence"
          " face)")

    face.close()
    n = 7
    print("SUITE %s: %d/%d" % ("PASS" if not bad else "FAIL",
                               n - len(bad), n), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
