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
    the registry size and non_law reads zero. AC-CEN3 reads the LIVE registry
    ON PURPOSE (decided R2856, not carried a third window): a frozen snapshot
    would let the tree that is actually shipped drift while this suite stayed
    green, and the census' one job is to measure that tree. The cost is stated
    rather than hidden - adding a non-law suite mid-window reddens this suite
    until the new suite grows a law row or the census is taught its shape, and
    that is the intended pressure, not a flake;
  - two runs read byte-identical output (no clock, no randomness);
  - --quiet-list drops the per-family non_law listing and keeps the shapes;
  - the registry declares this suite at eight criteria.

R2962 (AC-CEN7..AC-CEN8, pinned in the R2962 row of src/os/backlog.md BEFORE
this edit and before the row they grade): the live census read one non_law row,
and that row was RIGHT - src/os/test_logs_toolkit.py printed
'SUITE PASS %d checks', a shape the battery law refuses by design, so its 168
declared criteria were unreadable to every machine reader. The temptation is to
teach the census that shape; AC-CEN7 measures that both authorities refuse it
together, and AC-CEN8 runs the shipped suite and feeds its real row to the
runner's own parser.

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

EXPECTED_CRITERIA = 12
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


# R2963: the SOURCE reading is not an output proof, and this round measures
# how wide the gap is. DOC_ONLY is a suite whose only law literal sits in its
# module docstring while the code that actually runs prints the single-count
# shape the battery refuses - law by source, unreadable in fact.
DOC_ONLY_SRC = ('"""SUITE PASS %d/%d"""\n'
                'print("SUITE PASS %d checks" % 3)\n')
# the same law literal, now in a slot that reaches the print
MOVED_SRC = ('print("SUITE PASS %d/%d" % (3, 3))\n'
             'print("SUITE PASS %d checks" % 3)\n')
LIVE_PRINT_SRC = 'print("SUITE PASS %d/%d" % (3, 3))\n'
UNCALLED_SRC = 'def worker():\n    print("SUITE PASS %d/%d" % (3, 3))\n'
CALLED_SRC = UNCALLED_SRC + 'worker()\n'


def run_suite(path):
    """Run one private suite and return (rc, last SUITE row)."""
    proc = subprocess.run([sys.executable, path], capture_output=True,
                          timeout=120)
    text = proc.stdout.decode("utf-8", "replace")
    rows = [l.strip() for l in text.splitlines() if l.startswith("SUITE ")]
    return proc.returncode, (rows[-1] if rows else "<no SUITE row>")


def exec_line(out):
    """The position face line, or (None, None)."""
    for line in out.splitlines():
        if line.startswith("CENSUS exec law="):
            fields = dict(re.findall(r"(\w+)=(\d+)", line))
            return int(fields.get("law", -1)), int(fields.get("unexecuted", -1))
    return None, None


def ac_cen9():
    """The gap is real: law by source, unreadable when actually run."""
    folder, copy_tool = world("right", [("doc", "doc.py", 3),
                                        ("live", "live.py", 3)])
    try:
        write_text(os.path.join(folder, "src", "sandbox", "doc.py"),
                   DOC_ONLY_SRC)
        write_text(os.path.join(folder, "src", "sandbox", "live.py"),
                   LIVE_PRINT_SRC)
        code, out = run_census(folder, copy_tool)
        doc_rc, doc_row = run_suite(os.path.join(folder, "src", "sandbox",
                                                 "doc.py"))
        live_rc, live_row = run_suite(os.path.join(folder, "src", "sandbox",
                                                   "live.py"))
    finally:
        cleanup(folder)
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import battery_shard
    doc_read = battery_shard.parse_suite_row(doc_row)
    live_read = battery_shard.parse_suite_row(live_row)
    cited = "CENSUS registry=2 law=2 non_law=0 missing=0" in out
    escaped = doc_rc == 0 and doc_row == "SUITE PASS 3 checks" and doc_read is None
    control = (live_rc == 0 and live_read == ("PASS", 3, 3)
               and "CENSUS shape law_direct=2" in out)
    if not (code == 0 and cited and escaped and control):
        print("  measured rc=%d cited=%r doc=(rc=%d row=%r read=%r) "
              "live=(rc=%d read=%r)"
              % (code, cited, doc_rc, doc_row, doc_read, live_rc, live_read),
              flush=True)
    check(code == 0 and cited and escaped and control,
          "AC-CEN9 law-by-source prints an unreadable row (run, not asserted)")


def ac_cen10():
    """The position face tells a live law literal from a dead one, on a tree."""
    folder, copy_tool = world("right", [
        ("doc", "doc.py", 3), ("moved", "moved.py", 3),
        ("unc", "unc.py", 3), ("called", "called.py", 3)])
    try:
        sandbox = os.path.join(folder, "src", "sandbox")
        write_text(os.path.join(sandbox, "doc.py"), DOC_ONLY_SRC)
        write_text(os.path.join(sandbox, "moved.py"), MOVED_SRC)
        write_text(os.path.join(sandbox, "unc.py"), UNCALLED_SRC)
        write_text(os.path.join(sandbox, "called.py"), CALLED_SRC)
        code, out = run_census(folder, copy_tool)
        proc_l = subprocess.run(
            [sys.executable, copy_tool, "--root", folder,
             "--list-unexecuted"], capture_output=True)
        code_l = proc_l.returncode
        out_l = proc_l.stdout.decode("utf-8", "replace")
    finally:
        cleanup(folder)
    n, m = exec_line(out)
    town = (code == 0 and n == 2 and m == 2
            and "CENSUS exec why docstring=1 uncalled=1" in out)
    listed = []
    for line in out_l.splitlines():
        if line.startswith("CENSUS unexecuted "):
            listed += [x.strip() for x in line.split(":", 1)[1].split(",")]
    named = code_l == 0 and sorted(listed) == ["doc", "unc"]
    live_tree_ok, blind = live_exec_face()
    if not (town and named and live_tree_ok):
        print("  measured exec=(n=%r m=%r) town=%r named=%r live=%r %s"
              % (n, m, town, named, live_tree_ok, blind), flush=True)
    check(town and named and live_tree_ok,
          "AC-CEN10 position face partitions law (%s)" % blind)


def live_exec_face():
    """On the live tree n+u must equal law, and the listing must name u rows."""
    proc = subprocess.run(
        [sys.executable, TOOL, "--root", ROOT, "--quiet-list",
         "--list-unexecuted"], capture_output=True)
    out = proc.stdout.decode("utf-8", "replace")
    law = None
    for line in out.splitlines():
        if line.startswith("CENSUS registry="):
            law = int(re.findall(r"(\w+)=(\d+)", line)[0][1])
    n, m = exec_line(out)
    listed = []
    for line in out.splitlines():
        if line.startswith("CENSUS unexecuted "):
            listed += [x.strip() for x in line.split(":", 1)[1].split(",")]
    ok = (proc.returncode == 0 and law is not None and n is not None
          and n + m == law and len(listed) == m)
    return ok, "law=%r exec=%r unexecuted=%r named=%d" % (law, n, m, len(listed))


# R2962: the two shapes that round was about. The single-count row is the one
# src/os/test_logs_toolkit.py shipped until that round; the pair is what it
# ships now. Both the source (what the census reads) and the printed row (what
# the runner reads) are spelled out, so neither authority is fed a string the
# other one built.
ROW_SINGLE_SRC = 'print("SUITE PASS %d checks" % 3)\n'
ROW_SINGLE_OUT = "SUITE PASS 3 checks"
ROW_PAIR_SRC = 'print("SUITE PASS %d/%d" % (3, 3))\n'
ROW_PAIR_OUT = "SUITE PASS 3/3"
# The exact row the shipped suite printed before this round (168 assertions).
ROW_PRE_R2962 = "SUITE PASS 168 checks"


def ac_cen7():
    """The census refuses that shape AND the runner cannot read it either."""
    folder, copy_tool = world("right", [("checks", "checks.py", 3),
                                        ("pair", "pair.py", 3)])
    try:
        write_text(os.path.join(folder, "src", "sandbox", "checks.py"),
                   ROW_SINGLE_SRC)
        write_text(os.path.join(folder, "src", "sandbox", "pair.py"),
                   ROW_PAIR_SRC)
        code, out = run_census(folder, copy_tool)
    finally:
        cleanup(folder)
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import suite_closing_row_census as census
    import battery_shard
    old_shape = census.classify(ROW_SINGLE_SRC)
    new_shape = census.classify(ROW_PAIR_SRC)
    old_read = battery_shard.parse_suite_row(ROW_SINGLE_OUT)
    new_read = battery_shard.parse_suite_row(ROW_PAIR_OUT)
    town = ("CENSUS registry=2 law=1 non_law=1 missing=0" in out
            and "CENSUS shape law_direct=1" in out
            and "CENSUS shape other=1" in out
            and "CENSUS non_law other: checks" in out)
    agree = (old_shape not in census_law_families() and old_read is None
             and new_shape == "law_direct" and new_read == ("PASS", 3, 3))
    if not (town and agree):
        print("  measured rc=%d town=%r old=(shape=%r read=%r) "
              "new=(shape=%r read=%r)"
              % (code, town, old_shape, old_read, new_shape, new_read),
              flush=True)
    check(code == 0 and town and agree,
          "AC-CEN7 single-count row stays non-law in BOTH authorities")


def census_law_families():
    return ("law_direct", "law_status", "law_split", "law_numeric",
            "law_numeric_slot", "law_punct", "law_label_pt", "law_counters",
            "law_status_colon", "law_status_punct")


def ac_cen8():
    """Run the shipped suite and read its REAL closing row with the runner."""
    suite = os.path.join(BASE, "test_logs_toolkit.py")
    proc = subprocess.run([sys.executable, suite], capture_output=True,
                          timeout=300)
    text = proc.stdout.decode("utf-8", "replace")
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import battery_shard
    rows = [l.strip() for l in text.splitlines() if l.startswith("SUITE ")]
    row = rows[-1] if rows else "<no SUITE row>"
    read = battery_shard.parse_suite_row(text)
    red = battery_shard.parse_suite_row(ROW_PRE_R2962)
    code, out = run_census(ROOT, quiet=True)
    line = [l for l in out.splitlines() if l.startswith("CENSUS registry=")]
    live = False
    measured = "no CENSUS line"
    if code == 0 and line:
        fields = dict(re.findall(r"(\w+)=(\d+)", line[0]))
        live = (int(fields.get("non_law", -1)) == 0
                and int(fields.get("law", -1)) == int(fields.get("registry", -2)))
        measured = line[0]
    green = (proc.returncode == 0 and read is not None and read[0] == "PASS"
             and read[1] == read[2] and read[1] > 0)
    if not (green and red is None and live):
        print("  measured rc=%d row=%r read=%r red=%r live=%r %s"
              % (proc.returncode, row, read, red, live, measured), flush=True)
    check(green and red is None and live,
          "AC-CEN8 shipped closing row reads PASS through the runner (%s)" % row)


# R2964: a suite that WRITES a probe module into a string carries the split
# shape as bytes, not as structure. The text reading matched it; the structural
# reading must not. The same bytes as real code are the positive control, and
# an unconditional binding stays non-law in both readings (measured, not
# assumed) because it would print PASS over a red run.
FIXTURE_ONLY_SRC = (
    "FILES = {\n"
    "    'vi.py': 'V = \"SUITE PASS\" if OK else \"SUITE FAIL\"\\n"
    "print(\"%s %d/%d\" % (V, 2, 2))\\n',\n"
    "}\n"
    "print(\"done\")\n")
REAL_SPLIT_SRC = ('V = "SUITE PASS" if OK else "SUITE FAIL"\n'
                  'print("%s %d/%d" % (V, 2, 2))\n')
UNCONDITIONAL_SRC = ('V = "SUITE PASS"\n'
                     'print("%s %d/%d" % (V, 2, 2))\n')


def ac_cen11():
    """Fixture text cannot buy a split verdict; real code and the control split."""
    folder, copy_tool = world("right", [("fixture", "fixture.py", 1),
                                        ("real", "real.py", 1),
                                        ("uncond", "uncond.py", 1)])
    try:
        sandbox = os.path.join(folder, "src", "sandbox")
        write_text(os.path.join(sandbox, "fixture.py"), FIXTURE_ONLY_SRC)
        write_text(os.path.join(sandbox, "real.py"), REAL_SPLIT_SRC)
        write_text(os.path.join(sandbox, "uncond.py"), UNCONDITIONAL_SRC)
        code, out = run_census(folder, copy_tool)
        fixture = subprocess.run(
            [sys.executable, os.path.join(sandbox, "fixture.py")],
            capture_output=True, timeout=120)
        fixture_out = fixture.stdout.decode("utf-8", "replace")
        fixture_rows = [l for l in fixture_out.splitlines()
                        if l.startswith("SUITE ")]
    finally:
        cleanup(folder)
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import suite_closing_row_census as census
    shapes = {"fixture": census.classify(FIXTURE_ONLY_SRC),
              "real": census.classify(REAL_SPLIT_SRC),
              "uncond": census.classify(UNCONDITIONAL_SRC)}
    split = {"fixture": census.split_law(FIXTURE_ONLY_SRC),
             "real": census.split_law(REAL_SPLIT_SRC),
             "uncond": census.split_law(UNCONDITIONAL_SRC)}
    quiet = ("CENSUS registry=3 law=1 non_law=2 missing=0" in out
             and "CENSUS shape law_split=1" in out
             and "CENSUS non_law no_numbers: uncond" in out
             and "CENSUS non_law other: fixture" in out)
    ok = (code == 0 and quiet
          and split["fixture"] is False and shapes["fixture"] == "other"
          and split["real"] is True and shapes["real"] == "law_split"
          and split["uncond"] is False
          and shapes["uncond"] not in census_law_families()
          and fixture.returncode == 0 and "done" in fixture_out
          and fixture_rows == [])
    if not ok:
        print("  measured rc=%d quiet=%r split=%r shapes=%r fixture=(rc=%d "
              "out=%r rows=%r)" % (code, quiet, split, shapes,
                                   fixture.returncode, fixture_out,
                                   fixture_rows), flush=True)
    check(ok, "AC-CEN11 a fixture string buys no split verdict (%s)"
          % ",".join("%s=%s" % (k, shapes[k]) for k in sorted(shapes)))


def live_tree_closure():
    """The live split and exec lines: law == registry, unexecuted == 0."""
    proc = subprocess.run(
        [sys.executable, TOOL, "--root", ROOT, "--quiet-list",
         "--list-unexecuted"], capture_output=True)
    out = proc.stdout.decode("utf-8", "replace")
    fields = {}
    for line in out.splitlines():
        if line.startswith("CENSUS registry="):
            fields = dict(re.findall(r"(\w+)=(\d+)", line))
    n, m = exec_line(out)
    listed = []
    for line in out.splitlines():
        if line.startswith("CENSUS unexecuted "):
            listed += [x.strip() for x in line.split(":", 1)[1].split(",")]
    good = (proc.returncode == 0
            and fields.get("law") == fields.get("registry")
            and fields.get("non_law") == "0"
            and n is not None and m is not None and n + m == int(fields["law"])
            and m == 0 and listed == [])
    text = "registry=%r law=%r non_law=%r exec=%r unexecuted=%r named=%d" % (
        fields.get("registry"), fields.get("law"), fields.get("non_law"),
        n, m, len(listed))
    return good, text


def ac_cen12():
    """The row that sat inside the gap prints a row the runner can read."""
    suite = os.path.join(BASE, "test_registry_counter_census.py")
    proc = subprocess.run([sys.executable, suite], capture_output=True,
                          timeout=600)
    text = proc.stdout.decode("utf-8", "replace")
    rows = [l.strip() for l in text.splitlines() if l.startswith("SUITE ")]
    row = rows[-1] if rows else "<no SUITE row>"
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import battery_shard
    read = battery_shard.parse_suite_row(row + "\n")
    red = battery_shard.parse_suite_row("SUITE PASS 26 checks")
    green = (proc.returncode == 0 and read is not None and read[0] == "PASS"
             and read[1] == read[2] and read[1] > 0)
    closure, measured = live_tree_closure()
    if not (green and red is None and closure):
        print("  measured rc=%d row=%r read=%r red=%r %s"
              % (proc.returncode, row, read, red, measured), flush=True)
    check(green and red is None and closure,
          "AC-CEN12 live gap closed: row reads %r and %s" % (read, measured))


def main():
    print("suite closing-row census suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_cen1()
    ac_cen2()
    ac_cen3()
    ac_cen4()
    ac_cen5()
    ac_cen6()
    ac_cen7()
    ac_cen8()
    ac_cen9()
    ac_cen10()
    ac_cen11()
    ac_cen12()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
