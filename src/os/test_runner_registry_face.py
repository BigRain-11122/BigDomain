"""runner_registry_face suite (R3314; criteria AC-RCA6 were pinned inside the
R3314 PIN row of src/os/backlog.md BEFORE this code existed; AC-RCA7/AC-RCA8
were pinned in the R3315 PIN row the same way).

What this proves: the battery runner grades the third cell of every SUITES row
against the count the suite itself declares, so a hand edit that updates one
side and forgets the other stops the leg by name instead of printing an old
number. The gate reads a suite's own `EXPECTED_CRITERIA` assignment without
executing it, refuses a disagreement with E_RCA_CRIT_DRIFT naming the label and
BOTH counts, refuses a duplicate label and a non-positive cell by their own
words, lets an undeclared suite inherit the table cell untouched, refuses a row
whose suite file is absent (E_RCA_MISSING_PATH), and stops the real CLI before
the first suite starts. R3315 adds a whole-table entry: `--registry-only` grades
every row and starts no suite, and the two flag questions are refused together
instead of one silently winning.

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

EXPECTED_CRITERIA = 25
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
    """A suite with no declaration inherits the table cell and still runs.

    R3315 re-worded this arm: the row must exist on disk, because an ABSENT
    suite is now refused by name (AC-RCA7(a)) instead of being counted as
    inherited."""
    root = plant("# planted, no declaration at all\n")
    second = os.path.join(root, "test_legacy.py")
    with io.open(second, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("# legacy, no declaration either\n")
    rows = [("legacy", "test_planted.py", 12),
            ("legacy-two", "test_legacy.py", 4)]
    try:
        with PatchedBase(root):
            declared, inherited, drift, dups, zeros = \
                RA.registry_declarations(rows)
            ok, out = capture_registry(rows)
        check(declared == 0 and inherited == 2 and not drift and ok
              and " inherited=2 " in out and " missing=0 " in out
              and "E_RCA_" not in out,
              "AC-RCA6(e) undeclared suites inherit the table cell, no "
              "refusal")
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


def ac_rca7():
    """AC-RCA7: an absent suite is refused by name, a real undeclared suite
    still inherits, and the three published buckets sum to the row count."""
    root = plant("# planted\nEXPECTED_CRITERIA = 3\n")
    rows = [("present", "test_planted.py", 3),
            ("abs", "test_absent.py", 4)]
    try:
        with PatchedBase(root):
            ok, out = capture_registry(rows)
        named = "E_RCA_MISSING_PATH label=abs path=test_absent.py" in out
        check(not ok and named
              and " rows=2 declared=1 inherited=0 missing=1 " in out,
              "AC-RCA7(a) absent suite refused by name, buckets sum to rows")
        root2 = plant("# undeclared, but really on disk\n")
        rows2 = [("legacy", "test_planted.py", 12)]
        try:
            with PatchedBase(root2):
                ok2, out2 = capture_registry(rows2)
            check(ok2 and " inherited=1 " in out2 and "E_RCA_" not in out2,
                  "AC-RCA7(b) a real undeclared suite still inherits, no "
                  "refusal")
        finally:
            shutil.rmtree(root2, ignore_errors=True)
        ok_live, out_live = capture_registry(RA.SUITES)
        line = [l for l in out_live.splitlines() if l.startswith("REGISTRY ")]
        fields = {}
        if line:
            for part in line[0].split()[1:]:
                key, _, value = part.partition("=")
                fields[key] = value
        sums = (fields.get("rows") is not None
                and int(fields["declared"]) + int(fields["inherited"])
                + int(fields["missing"]) == int(fields["rows"]))
        check(ok_live and fields.get("missing") == "0"
              and "E_RCA_" not in out_live,
              "AC-RCA7(c) live registry answers missing=0 and stays green")
        check(sums, "AC-RCA7(d) live buckets are self-consistent "
                    "(declared+inherited+missing==rows)")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def run_cli(args):
    proc = subprocess.Popen([sys.executable, RUNNER] + args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace")


def ac_rca8():
    """AC-RCA8: --registry-only answers the whole-table question with zero
    suites started, never says RUNNER PASS, and the two flag questions are
    refused together rather than one winning silently."""
    code, text = run_cli(["--registry-only"])
    reg = [l for l in text.splitlines() if l.startswith("REGISTRY ")]
    started = [l for l in text.splitlines() if l.startswith("SUITE ")]
    only = [l for l in text.splitlines() if l.startswith("REGISTRY-ONLY ")]
    check(code == 0 and len(reg) == 1 and len(only) == 1 and not started
          and "RUNNER PASS" not in text and "E_RCA_" not in text
          and (" rows=%d " % len(RA.SUITES)) in reg[0],
          "AC-RCA8(a) --registry-only grades the whole table, starts zero "
          "suites, publishes REGISTRY-ONLY, no PARTIAL/PASS sentence")
    code2, text2 = run_cli(["--registry-only", "--only", "os-ledger-lines"])
    started2 = [l for l in text2.splitlines() if l.startswith("SUITE ")]
    check(code2 == 2 and "E_RCA_FLAG_CLASH" in text2 and not started2,
          "AC-RCA8(b) --registry-only with --only refused by name, zero "
          "suites started")
    rt = [l for l in text.splitlines() if l.startswith("RUNTIME-CRIT ")]
    check(len(rt) == 1 and "skipped=registry-only" in rt[0]
          and "graded=" not in rt[0],
          "AC-RCA8(c) --registry-only says the runtime count was skipped "
          "instead of quoting an older one")


def ac_rca9():
    """R3316 AC-RCA9: only a self-consistent GREEN fraction is graded, and a
    disagreement with the table cell is named."""
    obs = [
        ("alpha", 8, 0, "SUITE PASS 7/7\n"),
        ("alpha", 8, 0, "SUITE 8/8 green\n"),
        ("alpha", 8, 1, "SUITE FAIL 7/7\n"),
        ("alpha", 8, 0, "SUITE PASS no fraction here\n"),
        ("alpha", 8, 0, "SUITE FAIL 3/8 failed=[x]\n"),
    ]
    graded, ungraded, drift = RA.runtime_crit_drift(obs)
    check(graded == 2 and ungraded == 3 and drift == [("alpha", 8, 7)],
          "AC-RCA9(a) one graded green reads 7 against table 8 while its "
          "agreeing neighbour is silent, and three shapes stay ungraded "
          "(red suite, no fraction, self-inconsistent)")

    graded2, ungraded2, drift2 = RA.runtime_crit_drift(
        [("beta", 6, 0, "    SUITE PASS 6/6\n")])
    check(graded2 == 1 and ungraded2 == 0 and not drift2,
          "AC-RCA9(b) a space-indented green fraction that agrees with the "
          "table is graded and silent instead of missed")

    graded2b, ungraded2b, drift2b = RA.runtime_crit_drift(
        [("beta", 6, 0, "  | SUITE PASS 9/9\n")])
    check(graded2b == 0 and ungraded2b == 1 and not drift2b,
          "AC-RCA9(b2) the runner's own echo prefix is not read as a verdict, "
          "so only raw suite output can move the gate")

    graded3, _u3, drift3 = RA.runtime_crit_drift(
        [("gamma", 20, 0, "SUITE FAIL 2/20 failed=[a, b]\n")])
    check(graded3 == 0 and not drift3,
          "AC-RCA9(c) the launcher numerator shape is not read as a count")

    check(RA.parse_runtime_verdict("no suite line\n") is None
          and RA.parse_runtime_verdict("SUITE 9/9") == (9, 9),
          "AC-RCA9(d) the parser answers None or (numerator, denominator)")

    graded5, ungraded5, drift5 = RA.runtime_crit_drift([])
    check((graded5, ungraded5, drift5) == (0, 0, []),
          "AC-RCA9(e) an empty observation set answers three zeros")


def _run_planted(body, crit):
    """Run the shipped phase_suites over one planted suite row."""
    root = plant(body)
    saved_base, saved_suites = RA.BASE, RA.SUITES
    saved_drift = list(RA.RUNTIME_CRIT_DRIFT)
    RA.BASE = root
    RA.SUITES = [("drift-fixture", "test_planted.py", crit)]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            ran = RA.phase_suites()
        drift = list(RA.RUNTIME_CRIT_DRIFT)
    finally:
        RA.BASE, RA.SUITES = saved_base, saved_suites
        del RA.RUNTIME_CRIT_DRIFT[:]
        RA.RUNTIME_CRIT_DRIFT.extend(saved_drift)
        shutil.rmtree(root, ignore_errors=True)
    return ran, drift, buf.getvalue()


def ac_rca10():
    """R3316 AC-RCA10: the reading is wired into the leg itself. A green
    fixture whose own fraction disagrees with the table stops the run by name,
    a matching one does not, and main()'s green flag reads the drift list."""
    ran, drift, out = _run_planted(
        "print('SUITE PASS 9/9')\n", 8)
    lines = out.splitlines()
    named = ("E_RCA_RUN_CRIT_DRIFT label=drift-fixture table=8 suite=9"
             in out)
    reading = "RUNTIME-CRIT graded=1 ungraded=0 drift=1" in lines
    check(ran == (1, 1, 8) and drift == [("drift-fixture", 8, 9)]
          and named and reading
          and any(l.startswith("FAIL runtime-crit drift=1") for l in lines),
          "AC-RCA10(a) a green 9/9 fixture against table 8 stops the leg by "
          "name and the reading line counts it")

    ran2, drift2, out2 = _run_planted(
        "print('SUITE PASS 8/8')\n", 8)
    check(ran2 == (1, 1, 8) and not drift2
          and "RUNTIME-CRIT graded=1 ungraded=0 drift=0" in out2
          and "E_RCA_" not in out2,
          "AC-RCA10(b) a green 8/8 fixture against table 8 is graded silent")

    ran3, drift3, out3 = _run_planted(
        "import sys\nprint('SUITE PASS 9/9')\nsys.exit(2)\n", 8)
    check(ran3 == (0, 1, 8) and not drift3
          and "RUNTIME-CRIT graded=0 ungraded=1 drift=0" in out3,
          "AC-RCA10(c) a red fixture that prints 9/9 is left to its own exit "
          "code instead of being graded here")

    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        source = handle.read()
    wired = ("suites_ok = green_n == rows_n and not RUNTIME_CRIT_DRIFT"
             in source)
    check(wired,
          "AC-RCA10(d) main() counts the drift list in the green flag")


def ac_rca11():
    """R3318 AC-RCA11: the return shape is named where it is born, so a
    swapped order reddens here instead of reading green at length three."""
    ran, _drift, _out = _run_planted("print('SUITE PASS 3/3')\n", 3)
    check(isinstance(ran, tuple) and type(ran) is RA.PhaseSuites
          and ran._fields == ("green", "rows", "criteria")
          and (ran.green, ran.rows, ran.criteria) == tuple(ran),
          "AC-RCA11(a) the exit names its three fields in a fixed order")
    green, rows, total = ran
    check((green, rows, total) == (1, 1, 3)
          and ran.green == green and ran.rows == rows
          and ran.criteria == total,
          "AC-RCA11(b) positional unpacking still answers the same three "
          "values, so existing readers keep working")


def main():
    print("runner_registry_face suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rca6_a()
    ac_rca6_b()
    ac_rca6_c()
    ac_rca6_d()
    ac_rca6_e()
    ac_rca6_f()
    ac_rca7()
    ac_rca8()
    ac_rca9()
    ac_rca10()
    ac_rca11()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
