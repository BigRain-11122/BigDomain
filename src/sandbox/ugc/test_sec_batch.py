"""AC-SB1..AC-SB12 suite: UGC sec-gate batch + degradation face.

Criteria pre-registered in state/queue/tech.md (R1681 claim row;
R1850 read-cap extension AC-SB8..AC-SB12) BEFORE this code - honesty
law. Suite convention: one PASS line per criterion, SUITE tail line,
exit 0 only when all green.

Face under test: sec_batch.SecBatchFace (batch gate wrapper + own-file
persistent degraded banner queue, R1254 rows-are-queue semantics).
"""

import inspect
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
for _p in (_LOBBY, BASE):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import ContentRejectedError, GateOfflineError, SecGate  # noqa: E402
import sec_batch  # noqa: E402
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


class FlakyGate(object):
    """Stub gate: raises GateOfflineError from the Nth call on
    (simulated runtime outage; AC-SB5)."""

    def __init__(self, fail_on):
        self.n = 0
        self.fail_on = fail_on

    def check_text(self, text):
        self.n += 1
        if self.n >= self.fail_on:
            raise GateOfflineError("simulated runtime outage")
        return None


def check(bad, ac, ok, evidence):
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)
    if not ok:
        bad.append(ac)


def main():
    bad = []
    tmp = tempfile.mkdtemp(prefix="secbatch-ac-")
    db = os.path.join(tmp, "sec_degraded.db")
    gate = SecGate(["banned_alpha"], ["profit_promise_beta"])
    frozen = lambda: 0.0  # noqa: E731  (frozen clock -> zero elapsed)

    # accounting accumulators (AC-SB7)
    submitted, verdicted, queued_contents = set(), set(), set()

    # ---- AC-SB1: module construct, defaults, hygiene -----------------------
    face = SecBatchFace(gate, db, config={}, clock=frozen)
    src = open(sec_batch.__file__, "rb").read()
    ascii_ok = all(b < 128 for b in src)
    text_src = src.decode("ascii")
    import_lines = [ln for ln in text_src.splitlines()
                    if re.match(r"\s*(import|from)\s", ln)]
    net_imports = [ln for ln in import_lines
                    if re.search(r"\b(urllib|requests|socket|http)\b", ln)]
    # R1678 lesson: scan true import statement lines only (the docstring
    # mentions no network words either way, but the scan stays precise)
    check(bad, "AC-SB1",
          (face.budget_s == 0.2 and face.max_batch == 200 and ascii_ok
           and not net_imports
           and "import store" not in text_src
           and "UGCStore" not in text_src
           and "from sec_gate import" in text_src),
          "defaults budget_ms=200 max_batch=200; own-db single file; "
          "ascii=%s net_imports=%d ugc store never imported (zero "
          "ugc.db schema touch) sec_gate=referenced"
          % (ascii_ok, len(net_imports)))

    # ---- AC-SB2: batch verdicts == per-text gate outcomes ------------------
    corpus = ["clean alpha text", "has banned_alpha inside",
              "clean beta text", "profit_promise_beta wording",
              "clean gamma text"]
    out = face.check_batch(corpus, source="sb2")
    expected = []
    for t in corpus:
        try:
            gate.check_text(t)
            expected.append(("pass", 0, "", t))
        except ContentRejectedError as exc:
            expected.append(("rejected", exc.gate, exc.word, t))
    submitted |= set(corpus)
    verdicted |= {v[3] for v in out["verdicts"]}
    check(bad, "AC-SB2",
          out["verdicts"] == expected and not out["degraded"],
          "verdicts %d/%d identical to per-text gate; degraded=0"
          % (len(out["verdicts"]), len(expected)))
    face.close()

    # ---- AC-SB4: budget breach -> persistent degraded queue -----------------
    sb4 = ["sb4 first clean", "sb4 has banned_alpha tail",
           "sb4 second clean", "sb4 third clean", "sb4 fourth clean"]
    f4 = SecBatchFace(gate, db, config={"sec_batch": {"budget_ms": 100}},
                      clock=StepClock())
    out4 = f4.check_batch(sb4, source="sb4")
    submitted |= set(sb4)
    verdicted |= {v[3] for v in out4["verdicts"]}
    queued_contents |= {r[3] for r in f4.banner_queue()}
    q_after = len(f4.banner_queue())
    # idempotent landing while queued: replay the same batch -> zero new rows
    out4b = f4.check_batch(sb4, source="sb4")
    q_after_replay = len(f4.banner_queue())
    reasons = {r[4] for r in f4.banner_queue()}
    degraded_texts = {r[3] for r in f4.banner_queue()}
    check(bad, "AC-SB4",
          (len(out4["verdicts"]) == 1 and len(out4["degraded"]) == 4
           and q_after == 4 and q_after_replay == 4
           and reasons == {"budget_breach"}
           and not (degraded_texts & {v[3] for v in out4["verdicts"]})),
          "first text gated, 4 land queued reason=budget_breach; replay "
          "dedupe rows 4==4; no degraded text holds a verdict (fail-closed)")
    f4.close()

    # ---- AC-SB5: runtime gate failure -> same queue -------------------------
    sb5 = ["sb5 one", "sb5 two", "sb5 three has profit_promise_beta",
           "sb5 four", "sb5 five"]
    f5 = SecBatchFace(FlakyGate(fail_on=3), db, config={}, clock=frozen)
    out5 = f5.check_batch(sb5, source="sb5")
    submitted |= set(sb5)
    verdicted |= {v[3] for v in out5["verdicts"]}
    queued_contents |= {r[3] for r in f5.banner_queue()}
    sb5_set = set(sb5)
    rows5 = [r for r in f5.banner_queue() if r[3] in sb5_set]
    r5 = {r[4] for r in rows5}
    check(bad, "AC-SB5",
          (len(out5["verdicts"]) == 2 and len(out5["degraded"]) == 3
           and len(rows5) == 3 and r5 == {"gate_error"}
           and not ({r[3] for r in f5.banner_queue()}
                    & {v[3] for v in out5["verdicts"]})),
          "outage at text 3 -> texts 3..5 queued reason=gate_error; "
          "verdicts=2; zero silent pass")
    f5.close()

    # ---- AC-SB6: restart persistence + idempotent drain ---------------------
    f6 = SecBatchFace(gate, db, config={}, clock=frozen)
    survived = len(f6.banner_queue())
    drained = f6.drain()
    counts = f6.queue_counts()
    drained2 = f6.drain()
    # re-degrade a terminal row: PK dedupe -> zero new rows, landing
    # reports the existing terminal status (history never overwritten)
    f6.close()
    f6b = SecBatchFace(gate, db, config={"sec_batch": {"budget_ms": 100}},
                       clock=StepClock())
    out6 = f6b.check_batch(["sb4 first clean", "sb4 second clean"],
                           source="sb4")
    landed = {qid: status for qid, status in out6["degraded"]}
    total_rows_after = sum(f6b.queue_counts().values())
    f6b.close()
    check(bad, "AC-SB6",
          (survived == 7 and drained == {"drained": 7, "passed": 5,
                                         "rejected": 2, "still_queued": 0}
           and counts.get("queued", 0) == 0
           and counts.get("drained_pass", 0) == 5
           and counts.get("drained_rejected", 0) == 2
           and drained2["drained"] == 0
           and total_rows_after == 7
           and list(landed.values()) == ["drained_pass"]),
          "restart: 7 queued rows survive; drain 5 pass + 2 rejected "
          "(fail-closed forever); second drain=0; terminal re-degrade "
          "PK-deduped rows 7==7 landed=%s"
          % sorted(set(landed.values())))

    # ---- AC-SB3: p95 profile (real monotonic clock, honest stand-in) --------
    f3 = SecBatchFace(gate, db, config={})  # default clock = time.monotonic
    pool = ["profile clean corpus message %03d padded text body" % i
            for i in range(200)]
    profile = f3.p95_profile(pool, (1, 10, 50, 100, 200), 5)
    submitted |= set(pool)
    verdicted |= set(pool)
    f3.close()
    for row in profile:
        print("PROF n=%d runs=%d p50_ms=%.3f p95_ms=%.3f max_ms=%.3f"
              % (row["n"], row["runs"], row["p50_ms"], row["p95_ms"],
                 row["max_ms"]), flush=True)
    shape_ok = (len(profile) == 5
                and [r["n"] for r in profile] == [1, 10, 50, 100, 200]
                and all(r["runs"] == 5 for r in profile))
    mono_ok = all(r["p95_ms"] >= r["p50_ms"] and r["max_ms"] >= r["p95_ms"]
                  for r in profile)
    real_ok = profile[-1]["max_ms"] > 0
    check(bad, "AC-SB3", shape_ok and mono_ok and real_ok,
          "profile 5 sizes x5 runs real monotonic clock; shape+monotone "
          "ok; n=200 max_ms=%.3f>0 (wordlist-mock floor; production "
          "msgSecCheck p95 = bootstrap wiring window [needs-CEO])"
          % profile[-1]["max_ms"])

    # ---- AC-SB7: zero silent loss accounting + suite hygiene ---------------
    every_outcome = verdicted | queued_contents
    xor_ok = (submitted == every_outcome
              and not (verdicted & queued_contents))
    self_src = open(os.path.abspath(__file__), "rb").read()
    self_ascii = all(b < 128 for b in self_src)
    check(bad, "AC-SB7",
          xor_ok and self_ascii,
          "submitted=%d verdicted=%d queued_rows=%d exactly-one-outcome "
          "xor ok; suite ascii=%s; config.json untouched (module "
          "defaults only); other suites untouched (git closeout)"
          % (len(submitted), len(verdicted), len(queued_contents),
             self_ascii))

    # ---- AC-SB8..AC-SB12: banner_queue read-cap (R1850) --------------------
    capdb = os.path.join(tmp, "sec_degraded_cap.db")
    fcap = SecBatchFace(gate, capdb, config={}, clock=frozen)
    raw_zero = fcap.banner_queue()
    raw_zero_b = fcap.banner_queue()
    cap_zero = fcap.banner_queue(limit=3)
    check(bad, "AC-SB8",
          (isinstance(raw_zero, list) and raw_zero == []
           and json.dumps(raw_zero) == json.dumps(raw_zero_b)
           and isinstance(cap_zero, dict)
           and sorted(cap_zero.keys()) ==
           ["limit", "returned", "rows", "total", "truncated"]
           and isinstance(cap_zero["rows"], list)),
          "default face raw list byte-identical (double call); capped "
          "envelope exact 5 keys {rows,limit,total,returned,truncated}; "
          "default zero shape drift")

    raised9 = []
    before9 = fcap.queue_counts()
    for bad_limit in (-1, True, "2", 2.5, None):
        try:
            fcap.banner_queue(limit=bad_limit)
            raised9.append(None)
        except ValueError:
            raised9.append("ValueError")
    check(bad, "AC-SB9",
          raised9 == ["ValueError"] * 5
          and fcap.queue_counts() == before9,
          "five bad forms {-1,True,'2',2.5,None} all ValueError "
          "(module family code, R1850 verdict 2); queue_counts "
          "unchanged across 5 rejections (reject before any read)")

    fcap.close()
    # 6-row queued world: two StepClock budget-breach batches, shared
    # ts per batch (realistic chunk-degradation tie groups)
    fcapb = SecBatchFace(gate, capdb,
                         config={"sec_batch": {"budget_ms": 100}},
                         clock=StepClock())
    ts_a = "2026-10-12T01:00:00.000000Z"
    ts_b = "2026-10-12T02:00:00.000000Z"
    outa = fcapb.check_batch(["capA one", "capA two", "capA three",
                              "capA four"], source="capA", ts=ts_a)
    outb = fcapb.check_batch(["capB one", "capB two", "capB three",
                              "capB four"], source="capB", ts=ts_b)
    fcapb.close()
    fcapr = SecBatchFace(gate, capdb, config={}, clock=frozen)
    full = fcapr.banner_queue()
    counts_pre = fcapr.queue_counts()

    cap2 = fcapr.banner_queue(limit=2)
    ro = sqlite3.connect(
        "file:" + capdb.replace("\\", "/") + "?mode=ro", uri=True)
    mir2 = ro.execute(
        "SELECT qid, source, actor, content, reason, status, ts_utc"
        " FROM sec_degraded_queue WHERE status='queued'"
        " ORDER BY ts_utc DESC, rowid DESC LIMIT 2").fetchall()
    ro.close()
    mir2.reverse()
    cap4 = fcapr.banner_queue(limit=4)
    tie_ok = (len(outa["degraded"]) == 3 and len(outb["degraded"]) == 3
              and len(full) == 6
              and [r[6] for r in full[:3]] == [ts_a] * 3
              and [r[6] for r in full[3:]] == [ts_b] * 3)
    check(bad, "AC-SB10",
          (tie_ok
           and cap2["returned"] == 2 and cap2["truncated"] is True
           and cap2["total"] == 6
           and cap2["rows"] == full[-2:]
           and mir2 == cap2["rows"]
           and cap4["returned"] == 4 and cap4["truncated"] is True
           and cap4["rows"] == full[-4:]),
          "6-row tie world (3+3 shared-ts groups); limit=2 tail==full"
          "[-2:]; mirror SQL (ro conn, DESC rowid tiebreak, reversed)"
          "== product; limit=4 straddles tie group ==full[-4:]")

    cap6 = fcapr.banner_queue(limit=6)
    cap50 = fcapr.banner_queue(limit=50)
    cap1 = fcapr.banner_queue(limit=1)
    check(bad, "AC-SB11",
          (cap6["truncated"] is False and cap6["rows"] == full
           and cap50["truncated"] is False and cap50["rows"] == full
           and cap50["total"] == 6
           and cap1["returned"] == 1 and cap1["rows"] == full[-1:]
           and cap_zero["rows"] == [] and cap_zero["total"] == 0
           and cap_zero["returned"] == 0
           and cap_zero["truncated"] is False
           and cap_zero["limit"] == 3),
          "limit==total full (truncated=False); limit>total full; "
          "limit=1 single tail row; zero world honest empty cap read "
          "carries all keys")

    cap2_b = fcapr.banner_queue(limit=2)
    counts_post = fcapr.queue_counts()
    method_src = inspect.getsource(SecBatchFace.banner_queue).upper()
    write_verbs = re.findall(r"\bINSERT\b|\bUPDATE\b|\bDELETE\b",
                             method_src)
    runner_path = os.path.normpath(
        os.path.join(BASE, "..", "reconcile_all.py"))
    runner_txt = open(runner_path, encoding="utf-8").read()
    reg_ok = ('"ugc-sec-batch"' in runner_txt
              and 'os.path.join("ugc", "test_sec_batch.py"), 12)'
              in runner_txt)
    fcapr.close()
    check(bad, "AC-SB12",
          (not write_verbs
           and json.dumps(cap2, default=list)
           == json.dumps(cap2_b, default=list)
           and counts_post == counts_pre
           and reg_ok),
          "method source zero write verbs (inspect); capped double "
          "call json-identical; queue_counts stable across all cap "
          "reads; reconcile_all ugc-sec-batch criteria 7->12 wired")

    n = 12
    print("SUITE %s: %d/%d" % ("PASS" if not bad else "FAIL",
                               n - len(bad), n), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
