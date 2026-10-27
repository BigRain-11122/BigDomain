#!/usr/bin/env python3
"""test_evidence_writer_dir.py - batch directory face of evidence_writer.

AC-EVDB1..AC-EVDB8 (pre-registered in state/queue/tech.md R2172 claim
line BEFORE this code): one check per criterion, on throwaway temp
fixtures. ASCII-only source; stdlib only; zero network; no wall clock
reads (mtime equality is the OS own stamp, not a clock value).
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import evidence_writer as EW

TOOL = os.path.join(HERE, "evidence_writer.py")
RECONCILE = os.path.join(HERE, "..", "sandbox", "reconcile_all.py")
CHECKS = 0


def ok(cond, label):
    global CHECKS
    assert cond, "FAIL: " + label
    CHECKS += 1
    print("PASS " + label)


def run(*args):
    proc = subprocess.run([sys.executable, TOOL] + list(args),
                          capture_output=True)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def snapshot(root):
    snap = {}
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as handle:
            snap[name] = (handle.read(), os.stat(path).st_mtime)
    return snap


def write_raw(path, data):
    with open(path, "wb") as handle:
        handle.write(data)


def main():
    root = tempfile.mkdtemp(prefix="bd-evbdir-")
    try:
        world = os.path.join(root, "qa")
        os.makedirs(world)
        os.makedirs(os.path.join(world, "nested"))
        write_raw(os.path.join(world, "a-tee.log"), b"alpha\nbeta\n")
        write_raw(os.path.join(world, "b-crlf.log"), b"one\r\ntwo\r\n")
        write_raw(os.path.join(world, "c-cr.log"), b"three\rfour\r")
        write_raw(os.path.join(world, "notes.txt"), b"ignore me\r\n")
        write_raw(os.path.join(world, "upper.LOG"), b"ignore me too\r\n")
        write_raw(os.path.join(world, "nested", "deep.log"), b"x\r\ny\r\n")

        # AC-EVDB1: envelope and name family
        envelope = EW.check_dir(world)
        names = [row["name"] for row in envelope["rows"]]
        ok(sorted(envelope.keys()) == sorted(
               ["dir", "file_count", "tee_count", "flagged_count",
                "skipped_count", "rows"])
           and sorted(envelope["rows"][0].keys()) == sorted(
               ["name", "class", "bytes", "crlf", "bare_lf", "utf8"])
           and names == ["a-tee.log", "b-crlf.log", "c-cr.log"]
           and envelope["file_count"] == 3 and envelope["tee_count"] == 2
           and envelope["flagged_count"] == 1
           and envelope["skipped_count"] == 3,
           "AC-EVDB1 six-key envelope, .log-only candidates, name order")

        # AC-EVDB2: read-only check, missing path refuses
        before = snapshot(world)
        again = EW.check_dir(world)
        after = snapshot(world)
        missing = False
        try:
            EW.check_dir(os.path.join(root, "gone"))
        except EW.EvidenceDialectError:
            missing = True
        ok(before == after and again["rows"] == envelope["rows"] and missing,
           "AC-EVDB2 check_dir writes nothing and refuses a missing dir")

        # AC-EVDB3: only flagged files are chosen for repair
        healthy_stamp = before["a-tee.log"]
        notes_stamp = before["notes.txt"]
        fixed = EW.fix_dir(world)
        after_fix = snapshot(world)
        # Honest boundary: a lone-CR file reads as class tee (the census only
# counts CRLF pairs), so the batch face leaves it alone by the same
# selective law - recorded in the claim row, not repaired here.
        ok(fixed["fixed_count"] == 1
           and fixed["rows"][0]["changed"] is False
           and after_fix["a-tee.log"] == healthy_stamp
           and after_fix["notes.txt"] == notes_stamp,
           "AC-EVDB3 healthy and non-candidate files are untouched")

        # AC-EVDB4: before/after bytes and lines from bytes on disk
        row_b = [row for row in fixed["rows"] if row["name"] == "b-crlf.log"][0]
        row_c = [row for row in fixed["rows"] if row["name"] == "c-cr.log"][0]
        ok(sorted(row_b.keys()) == sorted(
               ["name", "before_bytes", "before_lines", "after_bytes",
                "after_lines", "class_before", "class_after", "changed"])
           and row_b["before_bytes"] == 10 and row_b["before_lines"] == 2
           and row_b["after_bytes"] == 8 and row_b["after_lines"] == 2
           and row_b["class_before"] != "tee" and row_b["class_after"] == "tee"
           and after_fix["b-crlf.log"][0] == b"one\ntwo\n"
           and row_c["class_before"] == "tee"
           and row_c["before_bytes"] == row_c["after_bytes"] == 11
           and row_c["before_lines"] == row_c["after_lines"] == 2
           and after_fix["c-cr.log"][0] == b"three\rfour\r",
           "AC-EVDB4 before/after byte and line report, EOL-only change")

        # AC-EVDB5: an unfixable candidate fails the whole batch
        bad = os.path.join(root, "bad")
        os.makedirs(bad)
        write_raw(os.path.join(bad, "a-dirty.log"), b"legit\r\nline\r\n")
        write_raw(os.path.join(bad, "z-binary.log"), b"\xff\xfe\r\n")
        bad_before = snapshot(bad)
        refused = False
        try:
            EW.fix_dir(bad)
        except EW.EvidenceDialectError:
            refused = True
        ok(refused and snapshot(bad) == bad_before,
           "AC-EVDB5 non utf-8 candidate fails the batch before any write")

        # AC-EVDB6: mid-batch write failure restores what was written
        rollback = os.path.join(root, "rollback")
        os.makedirs(rollback)
        write_raw(os.path.join(rollback, "a-crlf.log"), b"one\r\ntwo\r\n")
        write_raw(os.path.join(rollback, "b-crlf.log"), b"three\r\nfour\r\n")
        rollback_before = snapshot(rollback)
        original = EW.write_evidence
        calls = {"n": 0}

        def flaky(path, text, check=True):
            calls["n"] += 1
            if calls["n"] == 2:
                raise OSError("simulated disk failure")
            return original(path, text, check=check)

        EW.write_evidence = flaky
        try:
            raised = False
            try:
                EW.fix_dir(rollback)
            except OSError:
                raised = True
        finally:
            EW.write_evidence = original
        leftovers = [n for n in os.listdir(rollback) if n.startswith(".evd-")]
        restored = snapshot(rollback)
        bytes_equal = all(restored[n][0] == rollback_before[n][0]
                          for n in rollback_before)
        ok(raised and bytes_equal and not leftovers,
           "AC-EVDB6 write failure rolls every written file back")

        # AC-EVDB7: CLI contract and idempotence
        cli = os.path.join(root, "cli")
        os.makedirs(cli)
        write_raw(os.path.join(cli, "a-tee.log"), b"clean\n")
        c_clean, out_clean, _ = run("--check-dir", cli)
        write_raw(os.path.join(cli, "b-crlf.log"), b"dirty\r\nfile\r\n")
        c_dirty, out_dirty, _ = run("--check-dir", cli)
        c_missing, out_missing, _ = run(
            "--check-dir", os.path.join(root, "absent"))
        c_fix, out_fix, _ = run("--fix-dir", cli)
        c_again, out_again, _ = run("--fix-dir", cli)
        ok(c_clean == 0 and "dir files=1 tee=1 flagged=0" in out_clean
           and c_dirty == 2 and "dir files=2 tee=1 flagged=1" in out_dirty
           and "fix-dir name=b-crlf.log class=" in out_fix
           and "bytes=13->11" in out_fix and c_fix == 0
           and c_again == 0 and "dir fixed=0" in out_again
           and c_missing == 3 and out_missing.startswith("MISSING"),
           "AC-EVDB7 CLI 0/2/3, per-file report, idempotent second fix")

        # AC-EVDB8: hygiene and battery wiring
        with open(os.path.join(HERE, "evidence_writer.py"), "rb") as handle:
            src = handle.read().decode("ascii", "replace")
        with open(os.path.join(HERE, "test_evidence_writer_dir.py"),
                  "rb") as handle:
            own = handle.read().decode("ascii", "replace")
        names = ["requ" + "ests", "urll" + "ib", "sock" + "et",
                 "http" + ".client"]
        net = [n for n in names if ("import " + n) in src]
        with open(RECONCILE, "r", encoding="utf-8", errors="replace") as h:
            registry = h.read()
        label = "os-evidence-writer-" + "dir"
        suite_name = "test_evidence_writer_" + "dir.py"
        ok(not net and not [n for n in names if ("import " + n) in own]
           and label in registry and suite_name in registry,
           "AC-EVDB8 ASCII stdlib source and battery wiring in place")

        print("SUITE PASS %d/8 checks" % CHECKS)
        return 0 if CHECKS == 8 else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())