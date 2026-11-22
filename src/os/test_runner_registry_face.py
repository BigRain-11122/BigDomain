"""runner_registry_face suite (R3314; criteria AC-RCA6 were pinned inside the
R3314 PIN row of src/os/backlog.md BEFORE this code existed).

What this proves: the battery runner grades the third cell of every SUITES row
against the count the suite itself declares, so a hand edit that updates one
side and forgets the other stops the leg by name instead of printing an old
number. The gate reads a suite's own `EXPECTED_CRITERIA` assignment without
executing it, refuses a disagreement with E_RCA_CRIT_DRIFT naming the label and
BOTH counts, refuses a duplicate label and a non-positive cell by their own
words, lets an undeclared suite inherit the table cell untouched, and stops the
real CLI before the first suite starts.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, SANDBOX)
sys.path.insert(0, BASE)

import reconcile_all as RA  # noqa: E402

EXPECTED_CRITERIA = 6
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-runner-registry-face"

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


class PatchedBase(object):
    """Point the shipped reader at a planted registry root."""

    def __init__(self, root):
        self.root = root
        self.saved = None

    def __enter__(self):
        self.saved = RA.BASE
        RA.BASE = self.root
        return self

    def __exit__(self, *exc):
        RA.BASE = self.saved
        return False


def plant(body, name="test_planted.py"):
    root = tempfile.mkdtemp(prefix="bigdomain-rrf-")
    if body is not None:
        with io.open(os.path.join(root, name), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(body)
    return root


def capture_registry(rows):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = RA.phase_registry(rows)
    return ok, buf.getvalue()


def ac_rca6_a():
    """The live registry is graded, and the gate says so in one line."""
    declared, inherited, drift, dups, zeros = RA.registry_declarations(RA.SUITES)
    ok, out = capture_registry(RA.SUITES)
    line = [l for l in out.splitlines() if l.startswith("REGISTRY ")]
    shaped = (len(line) == 1
              and (" rows=%d " % len(RA.SUITES)) in line[0]
              and (" declared=%d " % declared) in line[0]
              and (" inherited=%d " % inherited) in line[0])
    check(ok and not drift and not dups and not zeros and declared > 0
          and declared + inherited == len(RA.SUITES) and shaped
          and "E_RCA_" not in out,
          "AC-RCA6(a) live registry graded: declared=%d inherited=%d "
          "drift=0 dup=0 zero=0, one REGISTRY line published"
          % (declared, inherited))


def ac_rca6_b():
    """A table cell that disagrees with the suite's own constant is refused."""
    root = plant("# planted\nEXPECTED_CRITERIA = 9\n")
    rows = [("planted", "test_planted.py", 7)]
    try:
        with PatchedBase(root):
            ok, out = capture_registry(rows)
        named = ("E_RCA_CRIT_DRIFT label=planted table=7 suite=9" in out)
        clean = plant("# planted\nEXPECTED_CRITERIA = 7\n")
        try:
            with PatchedBase(clean):
                ok2, out2 = capture_registry(rows)
        finally:
            shutil.rmtree(clean, ignore_errors=True)
        check(not ok and named and ok2 and "E_RCA_" not in out2,
              "AC-RCA6(b) drift refused naming label and both counts, the "
              "matched copy green")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_rca6_c():
    """Two rows may not carry the same label."""
    root = plant("# planted\nEXPECTED_CRITERIA = 3\n")
    rows = [("twin", "test_planted.py", 3), ("twin", "test_planted.py", 3)]
    try:
        with PatchedBase(root):
            ok, out = capture_registry(rows)
        check(not ok and "E_RCA_DUP_LABEL label=twin" in out,
              "AC-RCA6(c) duplicate label refused by name")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_rca6_d():
    """A non-positive cell is refused rather than counted as a green suite."""
    root = plant("# planted\nEXPECTED_CRITERIA = 3\n")
    rows = [("empty", "test_planted.py", 0)]
    try:
        with PatchedBase(root):
            ok, out = capture_registry(rows)
        check(not ok and "E_RCA_ZERO_CRIT label=empty" in out,
              "AC-RCA6(d) non-positive cell refused by name")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_rca6_e():
    """A suite with no declaration inherits the table cell and still runs."""
    root = plant("# planted, no declaration at all\n")
    rows = [("legacy", "test_planted.py", 12),
            ("missing", "test_absent.py", 4)]
    try:
        with PatchedBase(root):
            declared, inherited, drift, dups, zeros = \
                RA.registry_declarations(rows)
            ok, out = capture_registry(rows)
        check(declared == 0 and inherited == 2 and not drift and ok
              and " inherited=2 " in out and "E_RCA_" not in out,
              "AC-RCA6(e) undeclared and absent suites inherit the table "
              "cell, no refusal")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_rca6_f():
    """The refusal is wired before the first suite and the CLI agrees."""
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        source = handle.read()
    wired = (source.index("if not phase_registry(registry_rows):")
             < source.index("green_n, rows_n, total_n = phase_suites(selected)"))
    before_suite = ("aborted before the first suite" in source
                    and source.count("return 2") >= 2)
    proc = subprocess.Popen(
        [sys.executable, RUNNER, "--only", "os-ledger-lines"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = proc.communicate()
    text = out.decode("utf-8", "replace")
    live = [l for l in text.splitlines() if l.startswith("REGISTRY ")]
    started = [l for l in text.splitlines() if l.startswith("SUITE 1/1 ")]
    check(wired and before_suite and proc.returncode == 0 and live
          and started and "RUNNER PARTIAL" in text
          and "E_RCA_" not in text,
          "AC-RCA6(f) wired before the first suite: --only os-ledger-lines "
          "prints REGISTRY then SUITE 1/1 and ends PARTIAL rc=0")


def main():
    print("runner_registry_face suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rca6_a()
    ac_rca6_b()
    ac_rca6_c()
    ac_rca6_d()
    ac_rca6_e()
    ac_rca6_f()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
