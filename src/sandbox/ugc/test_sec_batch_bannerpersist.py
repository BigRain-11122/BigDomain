"""AC-SB23..AC-SB29 suite: sec_batch banner_queue cap-window read
cross-restart persistence example.

Criteria pre-registered in state/queue/tech.md (R1901 claim row,
registered BEFORE this code - honesty law). Suite convention: one
PASS line per criterion, SUITE tail line, exit 0 only when all green.

Seed row (R1895): the capped+windowed read faces (R1850 limit /
R1855 window / R1859 monthly roll) are all on the books, and R1742
pinned ROW-level persistence (banner rows survive a restart) - the
missing pin is the read face's DERIVATION PURITY across an instance
restart. This suite closes that gap, member banner_queue R1889 /
banner_board R1894 / freetrial R1895 / apidev lineage R1896 /
chain_usage R1897 / eventtickets R1898 persist family law.

Carrier verdict: a fresh isolated SecBatchFace in its own temp db
world drives the TRUE product write path end to end - every degraded
row lands via check_batch under a StepClock budget breach with an
explicit ts (record-time landing, R1859 roll-suite precedent),
zero fixture injection, shipped config.json untouched
(config={} sandbox-default world).

World = the R1859 roll twin: October 6 check_batch calls (1 verdict
+ 1 queued row each) + November 4 calls = 10 queued rows, per-row
distinct ts so ORDER BY ts_utc is a total order.

Restart genealogy: face1 loads the world + takes the pre-close
snapshot quartet -> close -> face2 reopens (same db, same gate
wordlist) + injects ONE new November degraded row (fresh
(source, actor, content) triple = fresh qid, true check_batch
path, second November day) -> face3 reopens again (two live
instances) for the sequential read identity law.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_sec_batch_bannerpersist.py
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
NOV_TS2 = "2026-11-20T12:00:00Z"          # 2nd November day (injection)
OCT_W = OCT_TS[0][:7]                      # "2026-10"
NOV_W = NOV_TS[0][:7]                      # "2026-11"
EMPTY_W = "2026-09"
CFG_PATH = os.path.join(BASE, "config.json")

CAP_SIX = {"rows", "limit", "total", "returned", "truncated",
           "window"}
CAP_FIVE = {"rows", "limit", "total", "returned", "truncated"}


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
    """R1859 roll twin: 6 October + 4 November degraded rows, all
    via check_batch under a deterministic budget breach."""
    for i, ts in enumerate(OCT_TS):
        out = face.check_batch(
            ["clean oct %02d" % i, "queued oct %02d" % i],
            source="persist-oct", actor="actor-a", ts=ts)
        assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1
    for i, ts in enumerate(NOV_TS):
        out = face.check_batch(
            ["clean nov %02d" % i, "queued nov %02d" % i],
            source="persist-nov", actor="actor-b", ts=ts)
        assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1


def main():
    bad = []
    tmp = tempfile.mkdtemp(prefix="secbatch-bannerpersist-")
    db = os.path.join(tmp, "sec_degraded.db")
    gate = SecGate(["banned_alpha"], ["profit_promise_beta"])
    prod_sha_in = hashlib.sha256(
        open(os.path.join(BASE, "sec_batch.py"), "rb").read()
    ).hexdigest()
    cfg_sha_in = hashlib.sha256(
        open(CFG_PATH, "rb").read()).hexdigest()

    face1 = SecBatchFace(gate, db, config={}, clock=StepClock(1.0))
    load_world(face1)

    # ---- AC-SB23: world load + pre-close snapshot quartet ----------
    oct_sql = sql_one(
        face1, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " status='queued' AND substr(ts_utc,1,7)=?", (OCT_W,))
    nov_sql = sql_one(
        face1, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " status='queued' AND substr(ts_utc,1,7)=?", (NOV_W,))
    oct_bare = face1.banner_queue(window=OCT_W)
    def_bare = face1.banner_queue()
    oct_capwin = face1.banner_queue(limit=2, window=OCT_W)
    def_cap = face1.banner_queue(limit=2)
    snap = (dumps(oct_capwin), dumps(def_cap),
            rows_json(def_bare), rows_json(oct_bare))
    ok23 = (
        oct_sql == 6 and nov_sql == 4
        and set(oct_capwin.keys()) == CAP_SIX
        and oct_capwin["total"] == 6
        and oct_capwin["returned"] == 2
        and oct_capwin["truncated"] is True
        and oct_capwin["window"] == OCT_W
        and rows_json(oct_capwin["rows"]) ==
        rows_json(oct_bare[-2:])
        and set(def_cap.keys()) == CAP_FIVE
        and def_cap["total"] == 10
        and rows_json(def_cap["rows"]) == rows_json(def_bare[-2:])
        and len(def_bare) == 10 and len(oct_bare) == 6
    )
    record("AC-SB23", ok23,
           "oct sql=%d nov sql=%d; oct capwin 6 keys total=6 tail=="
           "oct_bare[-2:]; default cap 5 keys total=10 tail=="
           "def_bare[-2:]; bare 10 rows / oct window 6 rows"
           % (oct_sql, nov_sql))
    if not ok23:
        bad.append("AC-SB23")

    # ---- AC-SB24: restart #1 - oct capwin envelope restored --------
    face1.close()
    face2 = SecBatchFace(gate, db, config={}, clock=StepClock(1.0))
    oct_capwin2 = face2.banner_queue(limit=2, window=OCT_W)
    oct_capwin2b = face2.banner_queue(limit=2, window=OCT_W)
    oct_bare2 = face2.banner_queue(window=OCT_W)
    ok24 = (dumps(oct_capwin2) == snap[0]
            and dumps(oct_capwin2b) == dumps(oct_capwin2)
            and rows_json(oct_bare2) == snap[3])
    record("AC-SB24", ok24,
           "post-restart oct capwin envelope == pre-close snapshot"
           " byte-identical (6 keys incl window echo + overflow block;"
           " rowid tiebreak deterministic across restart); same-param"
           " second read self-identical; oct bare window read =="
           " snapshot"
           if ok24 else "RESTORE FAILED")
    if not ok24:
        bad.append("AC-SB24")

    # ---- AC-SB25: default cap + bare faces restored ---------------
    def_cap2 = face2.banner_queue(limit=2)
    def_bare2 = face2.banner_queue()
    ok25 = (dumps(def_cap2) == snap[1]
            and rows_json(def_bare2) == snap[2])
    record("AC-SB25", ok25,
           "default capped read (5 keys) and default bare read"
           " (7-field row list) restored byte-identical across the"
           " restart - derived face carries zero in-memory state"
           if ok25 else "RESTORE FAILED")
    if not ok25:
        bad.append("AC-SB25")

    # ---- AC-SB26: new degraded row -> recompute + old-window freeze
    out = face2.check_batch(
        ["clean nov x2", "queued nov x2"],
        source="persist-nov", actor="actor-c", ts=NOV_TS2)
    assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1
    nov_sql2 = sql_one(
        face2, "SELECT COUNT(*) FROM sec_degraded_queue WHERE"
        " status='queued' AND substr(ts_utc,1,7)=?", (NOV_W,))
    def_cap_after = face2.banner_queue(limit=2)
    nov_bare_after = face2.banner_queue(window=NOV_W)
    nov_capwin_after = face2.banner_queue(limit=2, window=NOV_W)
    oct_capwin_after = face2.banner_queue(limit=2, window=OCT_W)
    oct_bare_after = face2.banner_queue(window=OCT_W)
    ok26 = (
        nov_sql2 == 5
        and def_cap_after["total"] == 11
        and dumps(def_cap_after) != snap[1]
        and nov_capwin_after["total"] == 5
        and rows_json(nov_capwin_after["rows"]) ==
        rows_json(nov_bare_after[-2:])
        and dumps(oct_capwin_after) == snap[0]
        and rows_json(oct_bare_after) == snap[3]
    )
    record("AC-SB26", ok26,
           "injected 2nd-November row via true path (nov sql 4->%d);"
           " default capped read recomputed total 10->11 (differs"
           " from pre-close snapshot = zero cache); nov window cap"
           " carries the new row (total==5); oct capwin envelope"
           " still == pre-close snapshot byte-identical + oct bare"
           " window frozen (ts_utc record-time immutable = old"
           " window zero permeation)"
           % nov_sql2 if ok26 else "RECOMPUTE/FREEZE FAILED")
    if not ok26:
        bad.append("AC-SB26")

    # ---- AC-SB27: window-total semantics across restart ------------
    oct_cap1 = face2.banner_queue(limit=1, window=OCT_W)
    nov_cap1 = face2.banner_queue(limit=1, window=NOV_W)
    empty_cap = face2.banner_queue(limit=2, window=EMPTY_W)
    ok27 = (
        oct_cap1["total"] == 6
        and nov_cap1["total"] == 5
        and set(empty_cap.keys()) == CAP_SIX
        and empty_cap["rows"] == []
        and empty_cap["total"] == 0
        and empty_cap["returned"] == 0
        and empty_cap["truncated"] is False
        and empty_cap["window"] == EMPTY_W
    )
    record("AC-SB27", ok27,
           "oct capped total stays 6 (new data zero permeation);"
           " nov capped total==5; empty-month 2026-09 capped read"
           " honest-empty six keys (rows=[] total=0 returned=0"
           " truncated=False + window echo)"
           if ok27 else "WINDOW-TOTAL SEMANTICS FAILED")
    if not ok27:
        bad.append("AC-SB27")

    # ---- AC-SB28: second restart - sequential read identity --------
    face3 = SecBatchFace(gate, db, config={}, clock=StepClock(1.0))
    reads2 = (
        dumps(face2.banner_queue(limit=2, window=OCT_W)),
        dumps(face2.banner_queue(limit=2)),
        dumps(face2.banner_queue(limit=2, window=NOV_W)),
        rows_json(face2.banner_queue()),
    )
    reads3 = (
        dumps(face3.banner_queue(limit=2, window=OCT_W)),
        dumps(face3.banner_queue(limit=2)),
        dumps(face3.banner_queue(limit=2, window=NOV_W)),
        rows_json(face3.banner_queue()),
    )
    reread2 = (
        dumps(face2.banner_queue(limit=2, window=OCT_W)),
        dumps(face2.banner_queue(limit=2)),
        dumps(face2.banner_queue(limit=2, window=NOV_W)),
        rows_json(face2.banner_queue()),
    )
    ok28 = (reads2 == reads3 and reads2 == reread2)
    record("AC-SB28", ok28,
           "face3 (second reopen, two live instances) four reads =="
           " face2 same-param reads pairwise byte-identical; face2"
           " re-read self-identical - zero cross-instance drift"
           if ok28 else "SEQUENTIAL IDENTITY FAILED")
    if not ok28:
        bad.append("AC-SB28")

    # ---- AC-SB29: pure-read law + hygiene --------------------------
    count_before = sql_one(
        face3, "SELECT COUNT(*) FROM sec_degraded_queue")
    battery = [face3.banner_queue(),
               face3.banner_queue(limit=2),
               face3.banner_queue(window=OCT_W),
               face3.banner_queue(limit=2, window=NOV_W),
               face3.queue_counts(),
               face3.queue_counts(window=OCT_W),
               face3.rows_by_status("queued"),
               face3.rows_by_status("drained_pass"),
               face3.rows_by_status("queued", window=NOV_W)]
    count_after = sql_one(
        face3, "SELECT COUNT(*) FROM sec_degraded_queue")
    write_verbs = []
    for method in (SecBatchFace.banner_queue, SecBatchFace.queue_counts,
                   SecBatchFace.rows_by_status):
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
    reg_ok = ('"ugc-sec-batch-bannerpersist"' in runner_txt
              and runner_txt.count(
                  '"ugc-sec-batch-bannerpersist"') == 1)
    ok29 = (not write_verbs
            and count_before == count_after
            and prod_sha_in == prod_sha_out
            and cfg_sha_in == cfg_sha_out
            and ascii_ok and not net_imports and reg_ok
            and "domain\\BigDomain" not in tmp.replace("/", "\\"))
    record("AC-SB29", ok29,
           "read faces zero write statements (inspect); read battery"
           " before/after full-table count %d==%d; sec_batch.py +"
           " shipped config.json sha256 unchanged (suite-only round);"
           " suite source pure ASCII; true import lines zero"
           " network libs; runner row wired; world = temp dir"
           " outside repo" % (count_before, count_after)
           if ok29 else "HYGIENE FAILED")
    if not ok29:
        bad.append("AC-SB29")

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
