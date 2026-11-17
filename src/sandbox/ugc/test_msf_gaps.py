"""Acceptance suite: the two decision-chain gaps named at R2910.

AC-MSFG1..AC-MSFG5 were pinned in src/os/backlog.md at R2911 BEFORE the edit
(pre-registration law). The subject is the SHIPPED path: every arm drives
pipeline.submit / drain_recover and reads what the face saw off the pipeline
itself, never a request typed into the assertion.

The two answers being controlled:
  * degraded branch  -> DECLINED. With no gate response there is nothing to
    adjudicate; asking would relabel an outage as a content rejection.
  * recovery branch  -> WIRED. A drained row re-enters the documented face
    before the post-gate flow, so an outage cannot buy a weaker chain.

Usage: python test_msf_gaps.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import pipeline as P  # noqa: E402
import msgsec_face as MSF  # noqa: E402
from sec_gate import GateOfflineError  # noqa: E402 (lobby gate product)

RESULTS = []
CLEAN = "idea for the lobby: a co-op mode with friends and a daily board"
RECEIPT_KEYS = {"drained", "passed", "rejected", "still_queued",
                "recovered", "skipped_existing", "failed_publish",
                "disclaimer", "persistent"}


class OfflineGate(object):
    """Runtime-failure stub: every check raises the gate-offline family."""

    def check_text(self, text):
        raise GateOfflineError("offline probe")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def load_cfg():
    with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def make(tmp, tag):
    """One world per arm: the degraded queue rides NEXT TO ugc.db and every
    instance in one directory shares that namespace (AC-PW1), so an arm that
    reused a directory would drain its neighbours' rows as well."""
    world = os.path.join(tmp, tag)
    os.makedirs(world, exist_ok=True)
    cfg = load_cfg()
    cfg["noise"] = dict(cfg.get("noise") or {}, flood_max_submissions=50)
    cfg["export"] = dict(cfg.get("export") or {}, dir="export-msfg-test")
    return P.UGCPipeline(cfg, os.path.join(world, "ugc.db")), cfg


def spy_face():
    """Wrap the shipped adjudicator so the face's call count is measured."""
    calls = []
    orig = P.MSF.adjudicate

    def spy(request, response):
        calls.append((request, response))
        return orig(request, response)

    P.MSF.adjudicate = spy
    return calls, orig


def degrade(pipe, actor, text):
    """Drive the outage branch through the SHIPPED submit path."""
    real_gate = pipe.batch.gate
    pipe.batch.gate = OfflineGate()
    try:
        return pipe.submit("direct", actor, text)
    finally:
        pipe.batch.gate = real_gate


def msfg1(tmp):
    """Degraded branch: the face is NOT asked, and why is measured."""
    pipe, cfg = make(tmp, "g1")
    calls, orig = spy_face()
    try:
        pipe.grant_entrance_sandbox("alice")
        out = degrade(pipe, "alice", CLEAN)
    finally:
        P.MSF.adjudicate = orig
        pipe.store.close()
    request = P.build_sec_request(CLEAN, "alice")
    decision, problems = MSF.adjudicate(request, None)
    ok = (out.get("received") is False and out.get("queued") is True
          and out.get("gate") is None and calls == []
          and decision == MSF.BLOCK
          and problems == ["E_MSF_RES_NOT_OBJECT"])
    record("AC-MSFG1", ok,
           "receipt received=%s queued=%s gate=%s | face_calls=%d | "
           "adjudicate(request, None)=%s problems=%s"
           % (out.get("received"), out.get("queued"), out.get("gate"),
              len(calls), decision, problems))


def msfg2(tmp):
    """Recovery branch: one face call per recovered row, documented shape."""
    pipe, cfg = make(tmp, "g2")
    try:
        pipe.grant_entrance_sandbox("bob")
        out = degrade(pipe, "bob", CLEAN)
        queued = out.get("queued") is True
        calls, orig = spy_face()
        try:
            rec = pipe.drain_recover()
            problems = list(pipe.sec_last_problems)
        finally:
            P.MSF.adjudicate = orig
        want_req = P.build_sec_request(CLEAN, "bob")
        want_res = P.sec_response_from_verdict("pass", 0)
        got_req = calls[0][0] if len(calls) == 1 else None
        got_res = calls[0][1] if len(calls) == 1 else None
        evt = pipe.store.event_row(P.compute_evt_id("direct", "bob", CLEAN))
        ok = (queued and len(calls) == 1 and got_req == want_req
              and got_res == want_res and problems == []
              and rec["drained"] == 1 and rec["passed"] == 1
              and len(rec["recovered"]) == 1
              and rec["failed_publish"] == 0 and evt is not None)
        record("AC-MSFG2", ok,
               "queued=%s face_calls=%d request_match=%s response_match=%s "
               "problems=%s recovered=%d failed=%d event_row=%s"
               % (queued, len(calls), got_req == want_req,
                  got_res == want_res, problems, len(rec["recovered"]),
                  rec["failed_publish"], evt is not None))
    finally:
        pipe.store.close()


def msfg3(tmp):
    """Red control: a face that refuses publishes nothing, loses nothing."""
    pipe, cfg = make(tmp, "g3")
    orig = P.MSF.adjudicate
    try:
        pipe.grant_entrance_sandbox("carol")
        out = degrade(pipe, "carol", CLEAN)
        queued = out.get("queued") is True
        P.MSF.adjudicate = lambda request, response: (MSF.BLOCK,
                                                      ["E_MSF_DOCTORED"])
        try:
            rec = pipe.drain_recover()
            problems = list(pipe.sec_last_problems)
        finally:
            P.MSF.adjudicate = orig
        evt = pipe.store.event_row(P.compute_evt_id("direct", "carol", CLEAN))
        queued_rows = pipe.batch.rows_by_status("drained_pass")
        kept = any(row[3] == CLEAN and row[5] == "drained_pass"
                   for row in queued_rows)
        ok = (queued and rec["drained"] == 1 and rec["passed"] == 1
              and rec["recovered"] == [] and rec["failed_publish"] == 1
              and problems == ["E_MSF_DOCTORED"] and evt is None and kept)
        record("AC-MSFG3", ok,
               "queued=%s drained=%d passed=%d recovered=%d failed=%d "
               "problems=%s event_published=%s queue_row_kept=%s"
               % (queued, rec["drained"], rec["passed"],
                  len(rec["recovered"]), rec["failed_publish"], problems,
                  evt is not None, kept))
    finally:
        P.MSF.adjudicate = orig
        pipe.store.close()


def msfg4(tmp):
    """Non-regression: receipt shape unchanged, sibling owners still green."""
    pipe, cfg = make(tmp, "g4")
    try:
        rec = pipe.drain_recover()
        shape_ok = set(rec) == RECEIPT_KEYS
    finally:
        pipe.store.close()
    runs = {}
    for name in ("test_msgsec_wire.py", "test_drain_waterwire.py",
                 "test_drain_waterpersist.py"):
        proc = subprocess.run([sys.executable, name], cwd=BASE,
                              capture_output=True, text=True)
        tail = [ln for ln in proc.stdout.splitlines()
                if ln.startswith("SUITE PASS")]
        runs[name] = (proc.returncode == 0, tail[-1] if tail else "no-pass-line")
    ok = shape_ok and all(v[0] for v in runs.values())
    record("AC-MSFG4", ok,
           "receipt_keys=%d shape_ok=%s | siblings=%s"
           % (len(rec), shape_ok,
              ",".join("%s:%s" % (k, "green" if v[0] else "red")
                       for k, v in runs.items())))


def msfg5(tmp):
    """Wiring + hygiene: registry count, ASCII/LF, stdlib-only imports."""
    here = os.path.abspath(__file__)
    with open(here, "rb") as fh:
        raw = fh.read()
    ascii_ok = all(byte < 128 for byte in raw)
    lf_ok = b"\r" not in raw
    reg = os.path.join(BASE, "..", "reconcile_all.py")
    with open(reg, "r", encoding="utf-8") as fh:
        text = fh.read()
    declared = None
    for line in text.splitlines():
        if "test_msf_gaps.py" in line:
            declared = line.strip()
    want = len(RESULTS) + 1  # this criterion counts itself
    count_ok = declared is not None and (", %d)" % want) in declared
    source = raw.decode("ascii", "replace")
    # Structural scan, not a token scan: a literal token list would match
    # itself (the same false-positive class the ledger names), so the check
    # reads the import STATEMENTS this file actually carries.
    imports = [ln.strip() for ln in source.splitlines()
               if ln.strip().startswith(("import ", "from "))]
    banned = [ln for ln in imports
              if ln.replace(",", " ").split()[1].split(".")[0]
              in ("time", "socket", "urllib", "http", "requests")]
    ok = ascii_ok and lf_ok and count_ok and not banned
    record("AC-MSFG5", ok,
           "ascii=%s lf=%s declared_ok=%s want=%d banned_imports=%s"
           % (ascii_ok, lf_ok, count_ok, want, banned))


def main():
    tmp = tempfile.mkdtemp(prefix="msfg-")
    try:
        msfg1(tmp)
        msfg2(tmp)
        msfg3(tmp)
        msfg4(tmp)
        msfg5(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria pass)%s"
          % ("PASS" if not failed else "FAIL",
             len(RESULTS) - len(failed), len(RESULTS),
             "" if not failed else " failing=" + ",".join(failed)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
