"""AC-SB30..AC-SB36 suite: sec_batch rows_by_status/queue_counts
windowed read cross-restart persistence example.

Criteria pre-registered in state/queue/tech.md (R1906 claim row,
registered BEFORE this code - honesty law). Suite convention: one
PASS line per criterion, SUITE tail line, exit 0 only when all green.

Seed row (R1901): the window filter (R1860 AC-SB18..SB22), the
monthly-roll preservation (R1865), row-level persistence (R1742) and
the banner_queue cap-window read persistence (R1901 AC-SB23..SB29)
are all on the books - the missing pin is the DERIVATION PURITY of
the two sibling read faces across an instance restart:

  * rows_by_status  - the 8-field row face (recovery-loop read)
  * queue_counts    - the sparse per-status count face

Carrier verdicts (pre-registered in the claim row):
  1. restart carrier = SecBatchFace close -> fresh instance on the
     same db with the same gate wordlist (config={} sandbox-default
     world, R1859/R1901 roll precedent).
  2. world = true product path, zero fixture injection: 6 October
     check_batch calls land 6 queued rows (3 plain + 3 dirty), then
     one drain stamped in NOVEMBER flips them to 3 drained_pass + 3
     drained_rejected - the record-time identity law made live (a
     row drained in a later month keeps its LANDING-month window;
     module docstring law). 4 November calls land 4 queued rows
     (2 plain + 2 dirty). Per-row distinct ts = total order, no
     ties. A dirty tail carries the banned word - it was never
     gated at landing (budget breach skips the remainder) and only
     the drain re-gate sees it.
  3. snapshot sextet = dp_oct row face + dr_oct row face + q_nov
     row face + q_default row face + qc_oct count face + qc_default
     count face; every cross-restart comparison walks dumps
     sort_keys byte equality.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_sec_batch_rowpersist.py
"""

import hashlib
import inspect
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

from sec_gate import SecGate  # noqa: E402,F401
from sec_batch import SecBatchFace  # noqa: E402

RESULTS = []
EXPECTED = 7

OCT_TS = ["2026-10-15T10:00:%02dZ" % i for i in range(6)]
NOV_TS = ["2026-11-07T09:30:%02dZ" % i for i in range(4)]
NOV_DRAIN_TS = "2026-11-05T08:00:00Z"   # drain stamp = November
NOV_TS2 = "2026-11-20T12:00:00Z"        # 2nd November day (injection)
OCT_W = OCT_TS[0][:7]                    # "2026-10"
NOV_W = NOV_TS[0][:7]                    # "2026-11"
EMPTY_W = "2026-09"
CFG_PATH = os.path.join(BASE, "config.json")


class StepClock(object):
    """Injected clock: every call steps +1.0s (deterministic breach)."""

    def __init__(self, step=1.0):
        self.t = 0.0
        self.step = step

    def __call__(self):
        v = self.t
        self.t += self.step
        return v


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def rows_json(rows):
    return json.dumps([list(r) for r in rows], sort_keys=True)


def sql_one(face, query, args=()):
    row = face.conn.execute(query, args).fetchone()
    return row[0] if row else None


def load_world(face):
    """October 6 + drain(November stamp) + November 4, all via the
    true product path. Dirty tails carry the banned word: ungated at
    landing (budget breach), re-gated only by the drain."""
    for i, ts in enumerate(OCT_TS):
        tail = ("queued oct dirty %02d banned_alpha" % i
                if i % 2 == 1 else "queued oct plain %02d" % i)
        out = face.check_batch(
            ["clean oct lead %02d" % i, tail],
            source="rowpersist-oct", actor="actor-a", ts=ts)
        assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1
    drained = face.drain(ts=NOV_DRAIN_TS)
    assert drained["drained"] == 6 and drained["passed"] == 3 \
        and drained["rejected"] == 3 and drained["still_queued"] == 0
    for i, ts in enumerate(NOV_TS):
        tail = ("queued nov dirty %02d banned_alpha" % i
                if i % 2 == 1 else "queued nov plain %02d" % i)
        out = face.check_batch(
            ["clean nov lead %02d" % i, tail],
            source="rowpersist-nov", actor="actor-b", ts=ts)
        assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1


def main():
    bad = []
    tmp = tempfile.mkdtemp(prefix="secbatch-rowpersist-")
    db = os.path.join(tmp, "sec_degraded.db")
    gate = SecGate(["banned_alpha"], ["profit_promise_beta"])
    prod_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "sec_batch.py"), "rb").read()
    ).hexdigest()
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    face1 = SecBatchFace(gate, db, config={}, clock=StepClock(1.0))
    load_world(face1)

    # ---- AC-SB30: world load + pre-close snapshot sextet -----------
    dp_oct_sql = sql_one(
        face1, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " status='drained_pass' AND substr(ts_utc,1,7)=?", (OCT_W,))
    dr_oct_sql = sql_one(
        face1, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " status='drained_rejected' AND substr(ts_utc,1,7)=?", (OCT_W,))
    q_nov_sql = sql_one(
        face1, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " status='queued' AND substr(ts_utc,1,7)=?", (NOV_W,))
    cross_dp = sql_one(
        face1, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " substr(ts_utc,1,7)=? AND substr(ts_drained,1,7)=?"
        " AND status='drained_pass'", (OCT_W, NOV_W))
    cross_dr = sql_one(
        face1, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " substr(ts_utc,1,7)=? AND substr(ts_drained,1,7)=?"
        " AND status='drained_rejected'", (OCT_W, NOV_W))
    dp_oct = face1.rows_by_status("drained_pass", window=OCT_W)
    dr_oct = face1.rows_by_status("drained_rejected", window=OCT_W)
    q_nov = face1.rows_by_status("queued", window=NOV_W)
    q_def = face1.rows_by_status("queued")
    qc_oct = face1.queue_counts(window=OCT_W)
    qc_def = face1.queue_counts()
    manual_dp = face1.conn.execute(
        "SELECT qid, source, actor, content, reason, status, ts_utc,"
        " ts_drained FROM sec_degraded_queue WHERE status = ? AND"
        " substr(ts_utc, 1, 7) = ? ORDER BY ts_utc",
        ("drained_pass", OCT_W)).fetchall()
    snap = (rows_json(dp_oct), rows_json(dr_oct), rows_json(q_nov),
            rows_json(q_def), dumps(qc_oct), dumps(qc_def))
    ok30 = (
        dp_oct_sql == 3 and dr_oct_sql == 3 and q_nov_sql == 4
        and cross_dp == 3 and cross_dr == 3
        and len(dp_oct) == 3 and len(dr_oct) == 3
        and len(q_nov) == 4 and len(q_def) == 4
        and all(len(r) == 8 for r in dp_oct + dr_oct + q_nov + q_def)
        and qc_oct == {"drained_pass": 3, "drained_rejected": 3}
        and qc_def == {"drained_pass": 3, "drained_rejected": 3,
                       "queued": 4}
        and rows_json(dp_oct) == rows_json(manual_dp)
        and rows_json(face1.rows_by_status("drained_pass",
                                           window=OCT_W)) == snap[0]
        and dumps(face1.queue_counts()) == snap[5]
    )
    record("AC-SB30", ok30,
           "true-path world: oct landed 6 (sql dp=%d dr=%d) drained at"
           " a November stamp (cross-month stamps dp=%d dr=%d ="
           " record-time identity: landing month owns the window);"
           " nov queued sql=%d; sextet pinned (dp_oct 3 rows / dr_oct"
           " 3 rows / q_nov 4 rows / q_default 4 rows, all 8-field"
           " tuples; qc_oct exactly 2 keys sparse, no queued key;"
           " qc_default 3 keys); dp_oct == manual SQL mirror"
           " (same WHERE/ORDER); same-param second reads self-identical"
           % (dp_oct_sql, dr_oct_sql, cross_dp, cross_dr, q_nov_sql))
    if not ok30:
        bad.append("AC-SB30")

    # ---- AC-SB31: restart #1 - oct window row faces restored ------
    face1.close()
    face2 = SecBatchFace(gate, db, config={}, clock=StepClock(1.0))
    dp_oct2 = face2.rows_by_status("drained_pass", window=OCT_W)
    dr_oct2 = face2.rows_by_status("drained_rejected", window=OCT_W)
    ok31 = (
        rows_json(dp_oct2) == snap[0]
        and rows_json(dr_oct2) == snap[1]
        and rows_json(face2.rows_by_status("drained_pass",
                                           window=OCT_W)) == snap[0]
        and rows_json(face2.rows_by_status("drained_rejected",
                                           window=OCT_W)) == snap[1]
    )
    record("AC-SB31", ok31,
           "post-restart oct window row faces (drained_pass +"
           " drained_rejected, 8-field tuples incl the November"
           " ts_drained stamp) restored byte-identical to the"
           " pre-close snapshots; same-param second reads"
           " self-identical - derived row faces carry zero in-memory"
           " state" if ok31 else "RESTORE FAILED")
    if not ok31:
        bad.append("AC-SB31")

    # ---- AC-SB32: default + nov window faces restored --------------
    q_def2 = face2.rows_by_status("queued")
    q_nov2 = face2.rows_by_status("queued", window=NOV_W)
    qc_def2 = face2.queue_counts()
    qc_oct2 = face2.queue_counts(window=OCT_W)
    ok32 = (
        rows_json(q_def2) == snap[3]
        and rows_json(q_nov2) == snap[2]
        and dumps(qc_def2) == snap[5]
        and dumps(qc_oct2) == snap[4]
    )
    record("AC-SB32", ok32,
           "default queued row face + nov window row face + default"
           " count face + oct window count face all restored"
           " byte-identical across the restart (four faces complete"
           " the zero-in-memory-state proof)"
           if ok32 else "RESTORE FAILED")
    if not ok32:
        bad.append("AC-SB32")

    # ---- AC-SB33: new degraded row -> recompute + old-window freeze
    out = face2.check_batch(
        ["clean nov x2", "queued nov x2"],
        source="rowpersist-nov", actor="actor-c", ts=NOV_TS2)
    assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1
    q_nov_sql2 = sql_one(
        face2, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " status='queued' AND substr(ts_utc,1,7)=?", (NOV_W,))
    qc_def_after = face2.queue_counts()
    q_nov_after = face2.rows_by_status("queued", window=NOV_W)
    qc_nov_after = face2.queue_counts(window=NOV_W)
    ok33 = (
        q_nov_sql2 == 5
        and dumps(qc_def_after) != snap[5]
        and qc_def_after == {"drained_pass": 3, "drained_rejected": 3,
                             "queued": 5}
        and len(q_nov_after) == 5
        and q_nov_after[-1][3] == "queued nov x2"
        and q_nov_after[-1][6] == NOV_TS2
        and qc_nov_after == {"queued": 5}
        and rows_json(face2.rows_by_status("drained_pass",
                                            window=OCT_W)) == snap[0]
        and rows_json(face2.rows_by_status("drained_rejected",
                                           window=OCT_W)) == snap[1]
        and dumps(face2.queue_counts(window=OCT_W)) == snap[4]
    )
    record("AC-SB33", ok33,
           "injected 2nd-November queued row via the true path (fresh"
           " (source,actor,content) triple = fresh qid; nov queued"
           " sql 4->%d); default count face recomputed queued 4->5 and"
           " byte-differs from the pre-close snapshot (zero cache);"
           " nov window row face carries the new row as its tail"
           " (content + record-time stamp pinned); nov window count"
           " face == {'queued': 5}; oct faces (dp/dr rows + counts)"
           " still byte-identical to the pre-close snapshots"
           " (ts_utc record-time immutable = old-window zero"
           " permeation)" % q_nov_sql2
           if ok33 else "RECOMPUTE/FREEZE FAILED")
    if not ok33:
        bad.append("AC-SB33")

    # ---- AC-SB34: window-total semantics + sparse caliber ---------
    qc_oct_now = face2.queue_counts(window=OCT_W)
    qc_empty = face2.queue_counts(window=EMPTY_W)
    rbs_empty = face2.rows_by_status("drained_pass", window=EMPTY_W)
    rbs_q_empty = face2.rows_by_status("queued", window=EMPTY_W)
    bogus_raised = False
    try:
        face2.rows_by_status("bogus")
    except ValueError:
        bogus_raised = True
    ok34 = (
        qc_oct_now == {"drained_pass": 3, "drained_rejected": 3}
        and qc_empty == {}
        and rbs_empty == [] and rbs_q_empty == []
        and bogus_raised
    )
    record("AC-SB34", ok34,
           "oct window count face stays exactly 2 keys while queued"
           " rows exist globally (window narrows the data domain, it"
           " never reshapes the dict); empty-month 2026-09 reads are"
           " honestly empty ({} count face, [] row faces); unknown"
           " status rejects with ValueError (param gate fail-closed"
           " still enforced after the restart)"
           if ok34 else "WINDOW SEMANTICS FAILED")
    if not ok34:
        bad.append("AC-SB34")

    # ---- AC-SB35: second restart - sequential read identity --------
    face3 = SecBatchFace(gate, db, config={}, clock=StepClock(1.0))
    reads2 = (
        rows_json(face2.rows_by_status("drained_pass", window=OCT_W)),
        rows_json(face2.rows_by_status("drained_rejected",
                                        window=OCT_W)),
        rows_json(face2.rows_by_status("queued")),
        dumps(face2.queue_counts()),
    )
    reads3 = (
        rows_json(face3.rows_by_status("drained_pass", window=OCT_W)),
        rows_json(face3.rows_by_status("drained_rejected",
                                        window=OCT_W)),
        rows_json(face3.rows_by_status("queued")),
        dumps(face3.queue_counts()),
    )
    reread2 = (
        rows_json(face2.rows_by_status("drained_pass", window=OCT_W)),
        rows_json(face2.rows_by_status("drained_rejected",
                                        window=OCT_W)),
        rows_json(face2.rows_by_status("queued")),
        dumps(face2.queue_counts()),
    )
    ok35 = (reads2 == reads3 and reads2 == reread2
            and reads3[0] == snap[0])
    record("AC-SB35", ok35,
           "face3 (second reopen, two live instances) four reads =="
           " face2 same-param reads pairwise byte-identical; face2"
           " re-read self-identical; face3 dp_oct still == the"
           " original pre-close snapshot (restart x new-data double"
           " hijack, zero drift)" if ok35 else
           "SEQUENTIAL IDENTITY FAILED")
    if not ok35:
        bad.append("AC-SB35")

    # ---- AC-SB36: pure-read law + hygiene -------------------------
    count_before = sql_one(
        face3, "SELECT COUNT(*) FROM sec_degraded_queue")
    battery = []
    for status in ("queued", "drained_pass", "drained_rejected"):
        battery.append(face3.rows_by_status(status))
        for w in (OCT_W, NOV_W, EMPTY_W):
            battery.append(face3.rows_by_status(status, window=w))
    for w in (None, OCT_W, NOV_W, EMPTY_W):
        battery.append(face3.queue_counts(window=w))
    count_after = sql_one(
        face3, "SELECT COUNT(*) FROM sec_degraded_queue")
    write_verbs = []
    for method in (SecBatchFace.rows_by_status,
                   SecBatchFace.queue_counts):
        src = inspect.getsource(method).upper()
        write_verbs += re.findall(
            r"\bINSERT\b|\bUPDATE\b|\bDELETE\b", src)
    prod_sha_out = hashlib.sha256(
        open(os.path.join(BASE, "sec_batch.py"), "rb").read()
    ).hexdigest()
    cfg_sha_out = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()
    self_src = open(os.path.abspath(__file__), "rb").read()
    ascii_ok = all(b < 128 for b in self_src)
    net_imports = []
    for line in self_src.decode("ascii", "replace").splitlines():
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            if re.search(r"\burllib\b|\brequests\b|\bsocket\b"
                         r"|\bhttp\b", s.split(" as ")[0]):
                net_imports.append(s)
    runner_txt = open(os.path.join(BASE, "..", "reconcile_all.py"),
                      encoding="utf-8").read()
    reg_ok = ('"ugc-sec-batch-rowpersist"' in runner_txt
              and runner_txt.count(
                  '"ugc-sec-batch-rowpersist"') == 1)
    battery_nonempty = sum(1 for b in battery if b)
    ok36 = (not write_verbs
            and count_before == count_after
            and count_before == 11
            and battery_nonempty >= 6
            and prod_sha_in == prod_sha_out
            and cfg_sha_in == cfg_sha_out
            and ascii_ok and not net_imports and reg_ok
            and "domain\\BigDomain" not in tmp.replace("/", "\\"))
    record("AC-SB36", ok36,
           "read battery (%d reads, %d non-empty) before/after"
           " full-table count %d==%d; rows_by_status + queue_counts"
           " method sources free of write statements (inspect);"
           " sec_batch.py + shipped config.json sha256 unchanged"
           " (suite-only round); suite source pure ASCII; true import"
           " lines zero network libs; runner row wired; world = temp"
           " dir outside repo"
           % (len(battery), battery_nonempty, count_before,
              count_after) if ok36 else "HYGIENE FAILED")
    if not ok36:
        bad.append("AC-SB36")

    face2.close()
    face3.close()
    n = EXPECTED
    print("SUITE %s: %d/%d criteria pass"
          % ("PASS" if not bad else "FAIL", n - len(bad), n),
          flush=True)
    if len(RESULTS) != EXPECTED:
        print("criteria drift: recorded %d expected %d"
              % (len(RESULTS), EXPECTED), flush=True)
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
