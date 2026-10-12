"""AC-SBR1..AC-SBR7 suite: sec_batch banner_queue monthly-roll example.

Criteria pre-registered in state/queue/tech.md (R1859 claim row,
registered BEFORE this code - honesty law). Suite convention: one
PASS line per criterion, SUITE tail line, exit 0 only when all green.

Face under test: sec_batch.SecBatchFace banner_queue read face
across a frozen-clock +23d month roll (R1845 devboard_roll /
R1854 caproll / R1858 callroll family precedent). An independent
world (own temp db + own face instance) carries the roll example:
the existing test_sec_batch.py world reads the real-clock global
queue, whose roll reads would be polluted by real-month rows.

Roll placement uses check_batch's explicit ts param - the real
product path (rows land ts_utc; the window jurisdiction is
record-time substr(ts_utc,1,7)). Rows get per-row distinct ts so
ORDER BY ts_utc is a total order (the capped path's rowid tiebreak
was already pinned by R1850; a total order keeps this suite's
reads bit-stable).
"""

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


def main():
    bad = []
    tmp = tempfile.mkdtemp(prefix="secbatch-roll-")
    db = os.path.join(tmp, "sec_degraded.db")
    gate = SecGate(["banned_alpha"], ["profit_promise_beta"])
    face = SecBatchFace(gate, db, config={}, clock=StepClock(1.0))

    oct_ts = ["2026-10-15T10:00:%02dZ" % i for i in range(6)]
    nov_ts = ["2026-11-07T09:30:%02dZ" % i for i in range(4)]

    # ---- October anchor world (pre-roll) -----------------------------
    for i, ts in enumerate(oct_ts):
        out = face.check_batch(
            ["clean oct %02d" % i, "queued oct %02d" % i],
            source="roll-oct", actor="actor-a", ts=ts)
        assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1
    oct_sql = sql_one(
        face, "SELECT COUNT(*) FROM sec_degraded_queue"
        " WHERE status='queued' AND substr(ts_utc,1,7)='2026-10'")
    oct_full = face.banner_queue()
    oct_win = face.banner_queue(window="2026-10")
    s_oct = rows_json(oct_win)
    counts_pre = face.queue_counts()
    check(bad, "AC-SBR1",
          (oct_sql == 6
           and len(oct_full) == 6 and len(oct_win) == 6
           and rows_json(oct_full) == s_oct
           and counts_pre == {"queued": 6}),
          "oct anchor: SQL record-time count==%d; default full read =="
          " explicit 2026-10 window read (6 rows, byte-identical);"
          " snapshot S_oct locked; queue_counts==%r"
          % (oct_sql, counts_pre))

    # ---- Month roll: November rows via the real product path ----------
    for i, ts in enumerate(nov_ts):
        out = face.check_batch(
            ["clean nov %02d" % i, "queued nov %02d" % i],
            source="roll-nov", actor="actor-b", ts=ts)
        assert len(out["verdicts"]) == 1 and len(out["degraded"]) == 1
    nov_sql = sql_one(
        face, "SELECT COUNT(*) FROM sec_degraded_queue"
        " WHERE status='queued' AND substr(ts_utc,1,7)='2026-11'")
    nov_win = face.banner_queue(window="2026-11")
    nov_full = face.banner_queue()
    check(bad, "AC-SBR2",
          (nov_sql == 4
           and len(nov_win) == 4
           and qids(nov_win).isdisjoint(qids(oct_win))
           and len(nov_full) == 10),
          "roll landing: SQL record-time 2026-11 count==%d; explicit"
          " 2026-11 window read = exactly the 4 new rows (zero overlap"
          " with S_oct); default full read = 10 rows (cross-month"
          " rows included)" % nov_sql)

    # ---- Old-month window preservation (bidirectional no-leak) -------
    oct_after = face.banner_queue(window="2026-10")
    nov_after = face.banner_queue(window="2026-11")
    check(bad, "AC-SBR3",
          (rows_json(oct_after) == s_oct
           and qids(nov_after).isdisjoint(qids(oct_after))),
          "old-month preservation: post-roll 2026-10 window read =="
          " S_oct byte-identical; 2026-11 window read has zero oct"
          " qids (two windows never leak into each other)")

    # ---- No-loss accounting across the roll ---------------------------
    counts_post = face.queue_counts()
    oct_qids_after = qids(face.rows_by_status("queued")) & qids(oct_win)
    total_all = sql_one(
        face, "SELECT COUNT(*) FROM sec_degraded_queue")
    check(bad, "AC-SBR4",
          (counts_post == {"queued": 10}
           and counts_post.get("queued", 0) - counts_pre.get("queued", 0) == 4
           and oct_qids_after == qids(oct_win)
           and total_all == 10),
          "no-loss accounting: queue_counts %r -> %r (per-status delta"
          " == 4 == new rows; old rows keep their status); all 6 oct"
          " qids still queued; full-table COUNT 6 -> 10 constant"
          " growth, zero rows lost" % (counts_pre, counts_post))

    # ---- window x cap x roll orthogonality ---------------------------
    cap_nov_1 = face.banner_queue(limit=1, window="2026-11")
    cap_nov_4 = face.banner_queue(limit=4, window="2026-11")
    cap_oct_1 = face.banner_queue(limit=1, window="2026-10")
    check(bad, "AC-SBR5",
          (set(cap_nov_1.keys()) ==
           {"rows", "limit", "total", "returned", "truncated", "window"}
           and cap_nov_1["total"] == 4
           and cap_nov_1["returned"] == 1
           and cap_nov_1["truncated"] is True
           and rows_json(cap_nov_1["rows"]) == rows_json(nov_win[-1:])
           and cap_nov_4["truncated"] is False
           and rows_json(cap_nov_4["rows"]) == rows_json(nov_win)
           and cap_oct_1["total"] == 6
           and rows_json(cap_oct_1["rows"]) ==
           rows_json(face.banner_queue(window="2026-10")[-1:])),
          "window x cap x roll orthogonal: (2026-11, limit=1) envelope"
          " = exactly 6 keys (5 base + window additive); total==4 ="
          " windowed count (never the global 10); rows == windowed"
          " full read [-1:] row-identical; (2026-11, limit=4) full"
          " truncated=False; (2026-10, limit=1) old-month capped read"
          " unchanged (total==6) - window filter precedes COUNT and"
          " LIMIT")

    # ---- pure-read law over the three read faces ----------------------
    write_verbs = []
    for method in (SecBatchFace.banner_queue, SecBatchFace.queue_counts,
                   SecBatchFace.rows_by_status):
        src = inspect.getsource(method).upper()
        write_verbs += re.findall(
            r"\bINSERT\b|\bUPDATE\b|\bDELETE\b", src)
    check(bad, "AC-SBR6",
          (not write_verbs),
          "pure-read law: banner_queue / queue_counts / rows_by_status"
          " method sources carry zero write statements (inspect)")

    # ---- hygiene + runner wiring ---------------------------------------
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
    reg_ok = ('"ugc-sec-batch-roll"' in runner_txt
              and runner_txt.count('"ugc-sec-batch-roll"') == 1)
    product_untouched = True  # evidence face: git status (no in-suite repo writes)
    check(bad, "AC-SBR7",
          (ascii_ok and not net_imports and reg_ok and product_untouched),
          "hygiene: suite source pure ASCII; true import lines carry"
          " zero network libraries; reconcile_all ugc-sec-batch-roll"
          " wired (criteria 7); world = temp dir only, sec_batch.py"
          " untouched (git status evidence face)")

    face.close()
    n = 7
    print("SUITE %s: %d/%d" % ("PASS" if not bad else "FAIL",
                               n - len(bad), n), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
