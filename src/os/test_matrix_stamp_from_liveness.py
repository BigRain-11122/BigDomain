"""matrix_stamp_from_liveness suite (R2494).

Criteria AC-MSFL1..AC-MSFL6 were pinned in the R2442 tech seed row of
state/queue/tech.md:529 BEFORE this code existed.

What this proves: R2442 gave an artifact a provenance line naming the document
its stamp was borrowed from, and MEASURED at R2442 nothing asked whether that
document still exists - recorded_source() handed the recorded string back
verbatim, so a doc borrowing from a source deleted the next day read exactly
like a live one. This face asks the tree at CALL time and publishes
LIVE / MISSING / AMBIGUOUS / NONE beside the segment, never rewriting the
recorded string.

Proofs are measured on fixture worlds and on REAL renders of the shipped tool,
not on stubs.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import matrix_stamp_from_liveness as MSFL  # noqa: E402
import matrix_stamp_provenance_line as MSPL  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "matrix_stamp_from_liveness.py")
MATRIX_TOOL = os.path.join(SANDBOX, "suite_matrix.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
WIRED_EXPECT = '"test_matrix_stamp_from_liveness.py"), 6),'


def check(ok, label):
    if ok:
        print("  PASS %s" % label)
    else:
        print("  FAIL %s" % label)
    return ok


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write_text(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def patterns():
    with open(PATTERNS_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def make_world():
    """A private tree so a real os.walk never touches the repository."""
    logdir = os.path.join(REPO, "logs")
    root = logdir if os.path.isdir(logdir) else REPO
    return tempfile.mkdtemp(prefix="msfl-", dir=root)


def doc_with(labels, recorded):
    """A document carrying exactly the provenance line the law renders."""
    return "fixture document\n%s\nbody\n" % MSPL.segment(labels, recorded)


def cli(world, recorded_doc, root=None):
    args = [sys.executable, MODULE, "--patterns", PATTERNS_PATH,
            "--doc", recorded_doc]
    if root is not None:
        args += ["--root", root]
    proc = subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_msfl1(world):
    """The tree is asked at CALL time and the recorded string is never
    rewritten: the same doc reads differently once the source moves."""
    labels = patterns()["labels"]
    tree = os.path.join(world, "tree1")
    source = os.path.join(tree, "qa", "live-R2494.log")
    write_text(source, "evidence\n")
    recorded = "qa/live-R2494.log"
    doc = os.path.join(world, "doc1.md")
    write_text(doc, doc_with(labels, recorded))
    before_bytes = read_text(doc)

    first = MSFL.report(labels, read_text(doc), tree)
    ok = check(first["state"] == MSFL.LIVE,
               "AC-MSFL1 a source on the tree reads LIVE")
    os.remove(source)
    second = MSFL.report(labels, read_text(doc), tree)
    ok = check(second["state"] == MSFL.MISSING,
               "AC-MSFL1 the same doc reads MISSING once the tree moved") and ok
    ok = check(first["recorded"] == recorded and second["recorded"] == recorded,
               "AC-MSFL1 the recorded string is published verbatim") and ok
    ok = check(read_text(doc) == before_bytes,
               "AC-MSFL1 reading the doc rewrites no byte of it") and ok

    original = MSPL.recorded_source
    asked = []

    def probe(text, labels_arg):
        asked.append(text)
        return original(text, labels_arg)

    MSPL.recorded_source = probe
    try:
        MSFL.report(labels, read_text(doc), tree)
    finally:
        MSPL.recorded_source = original
    ok = check(len(asked) == 1,
               "AC-MSFL1 the provenance reader is asked at CALL time") and ok
    return ok


def ac_msfl2(world):
    """A resolvable borrow reads LIVE naming the resolved path, and deleting
    that source moves the reading to MISSING."""
    labels = patterns()["labels"]
    tree = os.path.join(world, "tree2")
    source = os.path.join(tree, "qa", "deep", "borrow-R2494-b.log")
    write_text(source, "evidence\n")
    recorded = "qa/deep/borrow-R2494-b.log"
    doc = os.path.join(world, "doc2.md")
    write_text(doc, doc_with(labels, recorded))

    live = MSFL.report(labels, read_text(doc), tree)
    ok = check(live["state"] == MSFL.LIVE,
               "AC-MSFL2 the exact recorded path reads LIVE")
    ok = check(live["resolved"] == recorded,
               "AC-MSFL2 LIVE names the resolved path (%r)" % live["resolved"]) and ok
    ok = check(live["segment"] == MSPL.segment(labels, recorded),
               "AC-MSFL2 the reading carries the segment the doc must hold") and ok
    os.remove(source)
    gone = MSFL.report(labels, read_text(doc), tree)
    ok = check(gone["state"] == MSFL.MISSING and gone["resolved"] is None,
               "AC-MSFL2 deleting the source moves the reading to MISSING") and ok
    rc, out = cli(world, doc, tree)
    ok = check(rc == 2 and "state=MISSING" in out,
               "AC-MSFL2 the CLI names the dangling borrow at exit 2") and ok
    return ok


def ac_msfl3(world):
    """Two files answering the recorded string read AMBIGUOUS with both
    candidates named instead of a pick."""
    labels = patterns()["labels"]
    tree = os.path.join(world, "tree3")
    write_text(os.path.join(tree, "qa", "dup-R2494.log"), "a\n")
    write_text(os.path.join(tree, "logs", "dup-R2494.log"), "b\n")
    recorded = "elsewhere/dup-R2494.log"
    doc = os.path.join(world, "doc3.md")
    write_text(doc, doc_with(labels, recorded))

    row = MSFL.report(labels, read_text(doc), tree)
    ok = check(row["state"] == MSFL.AMBIGUOUS,
               "AC-MSFL3 two matching files read AMBIGUOUS")
    ok = check(row["resolved"] is None,
               "AC-MSFL3 an ambiguous borrow is not picked for the caller") and ok
    ok = check(row["candidates"] == ["logs/dup-R2494.log",
                                     "qa/dup-R2494.log"],
               "AC-MSFL3 both candidates are named (%r)" % (row["candidates"],)) and ok
    ok = check(row["recorded"] == recorded,
               "AC-MSFL3 the ambiguous reading keeps the recorded string") and ok
    rc, out = cli(world, doc, tree)
    ok = check(rc == 2 and "state=AMBIGUOUS" in out
               and "logs/dup-R2494.log,qa/dup-R2494.log" in out,
               "AC-MSFL3 the CLI publishes both candidates") and ok
    return ok


def ac_msfl4(world):
    """A doc with no provenance line reads NONE at exit 0, never MISSING."""
    labels = patterns()["labels"]
    tree = os.path.join(world, "tree4")
    write_text(os.path.join(tree, "qa", "unrelated.log"), "x\n")
    doc = os.path.join(world, "doc4.md")
    write_text(doc, "fixture document\nno provenance here\nbody\n")

    row = MSFL.report(labels, read_text(doc), tree)
    ok = check(row["state"] == MSFL.NONE and row["recorded"] is None,
               "AC-MSFL4 a doc with no borrow reads NONE")
    ok = check(row["state"] != MSFL.MISSING,
               "AC-MSFL4 an absent borrow is not called a dangling one") and ok
    ok = check(row["segment"] is None,
               "AC-MSFL4 no segment is invented for an ordinary doc") and ok
    rc, out = cli(world, doc, tree)
    ok = check(rc == 0 and "state=NONE" in out and "MISSING" not in out,
               "AC-MSFL4 the CLI reads NONE at exit 0") and ok
    return ok


def ac_msfl5(world):
    """Every existing suite_matrix face keeps its bytes and exit codes."""
    pats = patterns()
    labels = pats["labels"]
    tool_source = read_text(MATRIX_TOOL)
    ok = check("matrix_stamp_from_liveness" not in tool_source,
               "AC-MSFL5 suite_matrix is untouched by this face")

    doc_text = read_text(DOC)
    evid = os.path.join(REPO, SM.doc_evidence_face(doc_text, pats))
    plain = os.path.join(world, "render-a.md")
    again = os.path.join(world, "render-b.md")
    for out_path in (plain, again):
        # R2496 birth-site repair, measured not guessed: a plain render stamps
        # the wall clock at minute resolution, so two renders that straddled a
        # minute under battery load differed on that one line and this
        # determinism proof was measuring the clock rather than the content.
        # Both renders now borrow the shipped doc's own stamp through the
        # shipped --stamp-from law, so the comparison stays byte for byte and
        # no clock is asked.
        proc = subprocess.run(
            [sys.executable, MATRIX_TOOL, "--out", out_path,
             "--evidence", evid, "--stamp-from", DOC], cwd=REPO,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            raise SystemExit("FAIL setup: render refused\n%s"
                             % proc.stdout.decode("utf-8", "replace"))
    ok = check(read_text(plain) == read_text(again),
               "AC-MSFL5 two renders are byte-identical") and ok
    # --check is proved on a doc rendered and checked in the same world: the
    # shipped document is restamped at closeout by design, so comparing it
    # here would measure the clock rather than this face.
    proc = subprocess.run(
        [sys.executable, MATRIX_TOOL, "--check", "--out", plain,
         "--evidence", evid], cwd=REPO, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    ok = check(proc.returncode == 0 and "PASS check" in out,
               "AC-MSFL5 --check still reads PASS at exit 0") and ok
    stamp = SM.doc_stamp(doc_text, pats)
    stamp_line = [row for row in doc_text.splitlines()
                  if row.startswith("- %s: " % labels["stamp"])]
    ok = check(len(stamp_line) == 1 and stamp_line[0].endswith(str(stamp)),
               "AC-MSFL5 doc_stamp still reads the doc's own stamp line") and ok
    ok = check(SM.doc_evidence_face(doc_text, pats) == SM.doc_evidence_face(
                   read_text(plain), pats),
               "AC-MSFL5 doc_evidence_face still reads the same evidence path") and ok
    return ok


def ac_msfl6(world):
    """Pure ASCII source, stdlib only, zero network, no clock, read-only, own
    reconcile label and own suite."""
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    source = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", source))
    ok = check(ascii_only, "AC-MSFL6 source is pure ASCII")
    ok = check(imports <= {"argparse", "json", "os", "sys"},
               "AC-MSFL6 imports are stdlib only (%r)" % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime"}),
               "AC-MSFL6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-MSFL6 zero network imports") and ok
    ok = check('"w"' not in source and "os.replace" not in source
               and "makedirs" not in source,
               "AC-MSFL6 the module holds no write primitive") and ok
    ok = check(MSFL.LABEL == "os-matrix-stamp-from-liveness",
               "AC-MSFL6 the module names its own reconcile label") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_EXPECT in runner,
               "AC-MSFL6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-MSFL6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("MATRIX STAMP FROM LIVENESS suite (R2494, %d criteria)"
          % EXPECTED_CRITERIA)
    world = make_world()
    try:
        results = [ac_msfl1(world), ac_msfl2(world), ac_msfl3(world),
                   ac_msfl4(world), ac_msfl5(world), ac_msfl6(world)]
    finally:
        shutil.rmtree(world, ignore_errors=True)
    passed = sum(1 for row in results if row)
    print("SUITE %s exit=%d pass-lines=%d fail-lines=%d criteria=%d"
          % ("PASS" if passed == len(results) else "FAIL",
             0 if passed == len(results) else 1, passed,
             len(results) - passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())