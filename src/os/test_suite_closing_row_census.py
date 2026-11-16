"""suite_closing_row_census suite (R2854; criteria AC-CEN1..AC-CEN6 were
pinned in the R2854 row of src/os/backlog.md BEFORE this file existed).

What this proves: tools/suite_closing_row_census.py has been quoted by this
line for ten windows as the number that says how many suites cannot emit the
battery row, and for those ten windows it carried NO registered suite - the
tool that grades 705 suites was itself graded by nothing but the runs that
cited it.

  - the law it reads is the runner's own pattern, proven both ways in a
    private world (a wrong pattern is REFUSED, the right one is read);
  - the probe table classifies into the families it was measured to be, and it
    carries both halves of the R2855 quote-style asymmetry (single-quoted
    binding reads suspect_status, the same binding double-quoted reads
    law_status), so the declared limitation is pinned rather than described;
  - on the live tree the ten law families partition the registry: law equals
    the registry size and non_law reads zero;
  - two runs read byte-identical output (no clock, no randomness);
  - --quiet-list drops the per-family non_law listing and keeps the shapes;
  - the registry declares this suite at six criteria.

Each world is read through a SUBPROCESS, not an in-process import: the tool
imports battery_shard and reconcile_all by bare module name, so two roots in
one process share whichever world was imported first (measured this window:
the right pattern read rc=2 because the wrong world was still cached).

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)

EXPECTED_CRITERIA = 6
LABEL = "os-suite-closing-row-census"
TOOL = os.path.join(ROOT, "tools", "suite_closing_row_census.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
SHARD = os.path.join(ROOT, "tools", "battery_shard.py")

PASSES = 0
FAILS = 0

# measured with the live tool BEFORE this file was written (R2854 window):
# the eight shapes below classify exactly as the right-hand column says.
PROBES = [
    ('print("SUITE PASS %d/%d" % (n, t))\n', "law_direct"),
    ('print("SUITE PASS (7/7)")\n', "law_punct"),
    ('print("SUITE RESULT passes=6 fails=0 criteria=6")\n', "law_counters"),
    ('print("SUITE 6/6")\n', "law_numeric"),
    ('print("SUITE foo: 7/7 criteria pass")\n', "law_label_pt"),
    ('print("SUITE PASS")\n', "no_numbers"),
    ('print("done")\n', "no_row"),
    ('print("SUITE %s %d/%d" % (s, p, t))\n', "suspect_status"),
    # R2855: the declared quote-style limitation, both halves of the asymmetry.
    # The same binding is law only when it is DOUBLE quoted; single quotes are
    # read as suspect on purpose (conservative direction, never a fake green).
    ("verdict = 'PASS' if ok else 'FAIL'\n"
     "print('SUITE %s %d/%d' % (verdict, p, t))\n", "suspect_status"),
    ('verdict = "PASS" if ok else "FAIL"\n'
     'print("SUITE %s %d/%d" % (verdict, p, t))\n', "law_status"),
    # A single-quoted format literal alone (no verdict token at all) is also
    # suspect: the literal is read, the missing binding is what fails.
    ("print('SUITE %s %d/%d' % (s, p, t))\n", "suspect_status"),
]


def check(ok, name):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("  PASS %s" % name, flush=True)
    else:
        FAILS += 1
        print("  FAIL %s" % name, flush=True)


def run_census(root, tool=None, quiet=False):
    """Run the tool as a subprocess and return (rc, stdout)."""
    tool = tool or TOOL
    argv = [sys.executable, tool, "--root", root]
    if quiet:
        argv.append("--quiet-list")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(argv, capture_output=True, env=env)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def write_text(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def world(mode, suites=None):
    """A private world holding a copy of the census and a stub runner.

    mode 'right' writes the runner's real pattern; mode 'wrong' writes a
    pattern that matches nothing the census expects, so its own guard fires.
    """
    folder = tempfile.mkdtemp(prefix="bd-cen-")
    os.makedirs(os.path.join(folder, "tools"))
    os.makedirs(os.path.join(folder, "src", "sandbox"))
    copy_tool = os.path.join(folder, "tools", "suite_closing_row_census.py")
    shutil.copyfile(TOOL, copy_tool)
    shard = io.open(SHARD, encoding="utf-8").read()
    match = re.search(r"(?m)^SUITE_LINE\s*=\s*re\.compile\((.*)\)\s*$", shard)
    pattern = match.group(1) if match else 'r"NOTHING"'
    if mode == "wrong":
        pattern = 'r"SUITE PASS \\((\\d+)/(\\d+)\\)"'
    write_text(os.path.join(folder, "tools", "battery_shard.py"),
               "import re\n\nSUITE_LINE = re.compile(%s)\n" % pattern)
    rows = suites or []
    body = ["SUITES = ["]
    for label, rel, declared in rows:
        body.append("    (%s, %s, %d)," % (
            json.dumps(label), json.dumps(rel.replace(os.sep, "/")), declared))
    body.append("]")
    write_text(os.path.join(folder, "src", "sandbox", "reconcile_all.py"),
               "\n".join(body) + "\n")
    for label, rel, declared in rows:
        path = os.path.join(folder, "src", "sandbox", rel)
        if not os.path.exists(path):
            write_text(path, 'print("SUITE PASS")\n')
    return folder, copy_tool


def cleanup(folder):
    shutil.rmtree(folder, ignore_errors=True)


def ac_cen1():
    """The law is the runner's, and the guard refuses a pattern that is not."""
    wrong, wrong_tool = world("wrong")
    try:
        code, out = run_census(wrong, wrong_tool)
    finally:
        cleanup(wrong)
    right, right_tool = world("right")
    try:
        code2, out2 = run_census(right, right_tool)
    finally:
        cleanup(right)
    refused = code == 2 and "CENSUS FAIL law pattern disagrees" in out
    read = code2 == 0 and "CENSUS registry=0 law=0 non_law=0 missing=0" in out2
    if not (refused and read):
        print("  measured wrong=(rc=%d refused=%r) right=(rc=%d read=%r)"
              % (code, refused, code2, read), flush=True)
    check(refused and read,
          "AC-CEN1 law imported from the runner and a wrong pattern REFUSED")


def ac_cen2():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import suite_closing_row_census as census
    bad = [(src, want, census.classify(src))
           for src, want in PROBES if census.classify(src) != want]
    if bad:
        print("  measured mismatches=%r" % (bad,), flush=True)
    check(not bad, "AC-CEN2 %d probe shapes classify as measured" % len(PROBES))


def ac_cen3():
    """On the live tree the law families partition the registry."""
    code, out = run_census(ROOT, quiet=True)
    line = [l for l in out.splitlines() if l.startswith("CENSUS registry=")]
    measured = "no CENSUS line"
    ok = False
    if code == 0 and line:
        fields = dict(re.findall(r"(\w+)=(\d+)", line[0]))
        registry_n = int(fields.get("registry", -1))
        law = int(fields.get("law", -1))
        non_law = int(fields.get("non_law", -1))
        missing = int(fields.get("missing", -1))
        measured = "registry=%d law=%d non_law=%d missing=%d" % (
            registry_n, law, non_law, missing)
        ok = non_law == 0 and law == registry_n and missing == 0
    if not ok:
        print("  measured rc=%d %s" % (code, measured), flush=True)
    check(ok, "AC-CEN3 live tree: law families partition the registry")


def ac_cen4():
    """Two runs read the same bytes - no clock, no iteration-order leakage."""
    code_a, out_a = run_census(ROOT)
    code_b, out_b = run_census(ROOT)
    ok = (code_a == 0 and code_b == 0 and out_a == out_b
          and out_a.strip() != "")
    if not ok:
        print("  measured rc=%d/%d identical=%r lines=%d"
              % (code_a, code_b, out_a == out_b, len(out_a.splitlines())),
              flush=True)
    check(ok, "AC-CEN4 two runs read byte-identical output")


def ac_cen5():
    """--quiet-list drops the per-family listing and keeps the shapes."""
    folder, copy_tool = world("right", [("bad", "bad.py", 1),
                                        ("good", "good.py", 1)])
    try:
        write_text(os.path.join(folder, "src", "sandbox", "good.py"),
                   'print("SUITE PASS 1/1")\n')
        code_a, out_a = run_census(folder, copy_tool)
        code_b, out_b = run_census(folder, copy_tool, quiet=True)
    finally:
        cleanup(folder)
    loud = ("CENSUS non_law no_numbers: bad" in out_a
            and "CENSUS registry=2" in out_a)
    quiet = ("CENSUS non_law" not in out_b
             and "CENSUS registry=2" in out_b
             and "CENSUS shape no_numbers=1" in out_b)
    if not (loud and quiet):
        print("  measured rc=%d/%d loud=%r quiet=%r"
              % (code_a, code_b, loud, quiet), flush=True)
    check(code_a == 0 and code_b == 0 and loud and quiet,
          "AC-CEN5 quiet-list drops the naming and keeps the shapes")


def ac_cen6():
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + '"' + LABEL + '"' + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    declared = int(match.group(1)) if match else -1
    if declared != EXPECTED_CRITERIA:
        print("  measured declared=%r" % declared, flush=True)
    check(declared == EXPECTED_CRITERIA,
          "AC-CEN6 the registry declares %d criteria" % EXPECTED_CRITERIA)


def main():
    print("suite closing-row census suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_cen1()
    ac_cen2()
    ac_cen3()
    ac_cen4()
    ac_cen5()
    ac_cen6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
