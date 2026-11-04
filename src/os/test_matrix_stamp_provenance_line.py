"""matrix_stamp_provenance_line suite (R2442).

Criteria AC-MSPL1..AC-MSPL6 were pinned in the R2418 tech seed row of
state/queue/tech.md:508 BEFORE this code existed.

What this proves: suite_matrix gained --stamp-from at R2418 so a render can
follow another document's stamp, but MEASURED at R2418 the artifact could not
say so - the generation command line is a fixed format string naming only
--evidence, so a doc rendered with a BORROWED stamp was byte-for-byte
indistinguishable from an ordinary render. The borrow lived in the operator's
memory and nowhere on disk.

One law with two directions ships in src/os: segment() renders the line an
artifact must carry for a given source, recorded_source() reads that same
line back, so --check on a stamp-aligned doc recovers the borrow instead of
reporting drift. The label comes from suite_matrix_patterns.json, an ordinary
render gets nothing extra and keeps its bytes byte for byte.

Proofs are measured on REAL renders of the shipped tool, not on stubs.

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

import matrix_stamp_provenance_line as MSPL  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "matrix_stamp_provenance_line.py")
MATRIX_TOOL = os.path.join(SANDBOX, "suite_matrix.py")
PATTERNS_PATH = os.path.join(SANDBOX, "suite_matrix_patterns.json")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
LABEL = "os-matrix-stamp-provenance-line"
WIRED_EXPECT = '"test_matrix_stamp_provenance_line.py"), 6),'


def check(ok, label):
    if ok:
        print("  PASS %s" % label)
    else:
        print("  FAIL %s" % label)
    return ok


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def patterns():
    with open(PATTERNS_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def evidence_path():
    """The evidence the SHIPPED doc was built from, asked of the shipped law
    rather than spelled here (one evidence-face reading in the tree)."""
    recorded = SM.doc_evidence_face(read_text(DOC), patterns())
    if recorded is None:
        raise SystemExit("FAIL setup: shipped doc records no evidence path")
    return os.path.abspath(os.path.join(REPO, recorded))


def make_world():
    logdir = os.path.join(REPO, "logs")
    root = logdir if os.path.isdir(logdir) else REPO
    return tempfile.mkdtemp(prefix="mspl-", dir=root)


def cli(args):
    proc = subprocess.run([sys.executable, MATRIX_TOOL] + args,
                          cwd=REPO, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def render_pair(world):
    evid = evidence_path()
    plain = os.path.join(world, "plain.md")
    borrow = os.path.join(world, "borrow.md")
    rc_a, out_a = cli(["--out", plain, "--evidence", evid])
    rc_b, out_b = cli(["--out", borrow, "--evidence", evid,
                       "--stamp-from", plain])
    if rc_a != 0 or rc_b != 0:
        raise SystemExit("FAIL setup: real renders refused\n%s\n%s"
                         % (out_a, out_b))
    return evid, plain, borrow


def ac_mspl1(world):
    """The command line records --stamp-from and its source when given, and
    records NOTHING extra when it was not - two real renders."""
    labels = patterns()["labels"]
    evid, plain, borrow = render_pair(world)
    plain_lines = read_text(plain).splitlines()
    borrow_lines = read_text(borrow).splitlines()
    doc_lines = read_text(DOC).splitlines()

    expected = "- %s: %s %s" % (labels["stamp_from"], MSPL.FLAG,
                                SM.rel(plain))
    recorded = check(expected in borrow_lines,
                     "AC-MSPL1 stamp-from render records the flag and source")
    command = "- %s: python src/sandbox/suite_matrix.py --evidence %s" % (
        labels["command"], SM.rel(evid))
    recorded = check(command in plain_lines,
                     "AC-MSPL1 command line keeps today's wording") and recorded
    owned = [line for line in plain_lines
             if line.startswith("- %s: " % labels["stamp_from"])]
    recorded = check(owned == [],
                     "AC-MSPL1 ordinary render records nothing extra") and recorded
    # Byte-level: the header/label block of an ordinary render is identical
    # to the shipped (HEAD-law) doc's block apart from the volatile stamp
    # line and the provenance segment. The stamp line is volatile by law; the
    # provenance line belongs only to a STAMP-ALIGNED doc, so a shipped doc
    # regenerated with --stamp-from legitimately carries it and the ordinary
    # render does not - that absence is proved on its own above, so excluding
    # it on both sides keeps every other header/label line byte-compared. The
    # matrix body is NOT compared here: the registry legitimately grew by
    # this window's own suite, which no label law may hide.
    def block(lines):
        for index, row in enumerate(lines):
            if row.startswith("- %s: " % labels["response"]):
                return [row for row in lines[:index + 1]
                        if not row.startswith("- %s: " % labels["stamp"])
                        and not row.startswith("- %s: " % labels["stamp_from"])]
        return []

    recorded = check(block(plain_lines) == block(doc_lines)
                     and len(block(plain_lines)) >= 5,
                     "AC-MSPL1 ordinary render keeps the header/label block"
                     " byte for byte") and recorded
    return recorded


def ac_mspl2(world):
    """The stamp value is still read of doc_stamp and never re-derived, so the
    recorded line and the stamp line cannot disagree."""
    labels = patterns()["labels"]
    stamp = "MARKER-STAMP-2099-01-01 00:00 +08:00"
    original = SM.doc_stamp
    SM.doc_stamp = lambda text, pats: stamp
    try:
        status, run = SM.parse_evidence(evidence_path())
        text = SM.render(patterns(), evidence_path(), status, run, stamp,
                         stamp_from="docs/elsewhere.md")
    finally:
        SM.doc_stamp = original
    lines = text.splitlines()
    stamp_line = [row for row in lines
                  if row.startswith("- %s: " % labels["stamp"])]
    segment = [row for row in lines
               if row.startswith("- %s: " % labels["stamp_from"])]
    ok = check(len(stamp_line) == 1 and stamp_line[0].endswith(stamp),
               "AC-MSPL2 the stamp line carries the value doc_stamp answered")
    ok = check(segment == [MSPL.segment(labels, "docs/elsewhere.md")],
               "AC-MSPL2 the provenance line is the seam's own segment") and ok
    ok = check("2099" not in (segment[0] if segment else ""),
               "AC-MSPL2 the recorded line restates no stamp value") and ok
    return ok


def ac_mspl3(world):
    """doc_evidence_face keeps answering the evidence path byte for byte on
    both kinds of doc (the R1749 stale-face reading is unchanged)."""
    evid, plain, borrow = render_pair(world)
    pats = patterns()
    want = SM.rel(evid)
    on_plain = SM.doc_evidence_face(read_text(plain), pats)
    on_borrow = SM.doc_evidence_face(read_text(borrow), pats)
    ok = check(on_plain == want,
               "AC-MSPL3 ordinary doc answers the evidence path")
    ok = check(on_borrow == want,
               "AC-MSPL3 stamp-aligned doc answers the evidence path") and ok
    on_shipped = SM.doc_evidence_face(read_text(DOC), pats)
    ok = check(on_shipped == want,
               "AC-MSPL3 shipped doc answers the same path") and ok
    return ok


def ac_mspl4(world):
    """--check still reads PASS on an ordinary doc regenerated in another
    minute and on a stamp-aligned doc - the borrow is recovered, not drift."""
    evid, plain, borrow = render_pair(world)
    rc_a, out_a = cli(["--check", "--out", plain, "--evidence", evid])
    rc_b, out_b = cli(["--check", "--out", borrow, "--evidence", evid])
    ok = check(rc_a == 0 and "PASS check" in out_a,
               "AC-MSPL4 --check PASS on the ordinary render")
    ok = check(rc_b == 0 and "PASS check" in out_b,
               "AC-MSPL4 --check PASS on the stamp-aligned render") and ok
    rc_m = subprocess.run(
        [sys.executable, MODULE, "--patterns", PATTERNS_PATH,
         "--doc", borrow], cwd=REPO,
        stdout=subprocess.PIPE).returncode
    ok = check(rc_m == 0, "AC-MSPL4 the recorded source reads back at exit 0") and ok
    recorded = MSPL.recorded_source(read_text(borrow), patterns()["labels"])
    ok = check(recorded == SM.rel(plain),
               "AC-MSPL4 the read-back equals the render's own source") and ok
    return ok


def ac_mspl5(world):
    """The label lives in suite_matrix_patterns.json, not in the source, and
    every existing label line keeps its position and wording."""
    pats = patterns()
    labels = pats["labels"]
    ok = check("stamp_from" in labels,
               "AC-MSPL5 the patterns file carries the new label")
    source = read_text(MODULE)
    ok = check(labels["stamp_from"] not in source,
               "AC-MSPL5 the label text is not in the source") and ok
    moved = dict(labels)
    moved["stamp_from"] = "ZZTESTLABEL"
    ok = check(MSPL.segment(moved, "x").startswith("- ZZTESTLABEL: "),
               "AC-MSPL5 the label is asked of the patterns at CALL time") and ok
    try:
        MSPL.segment({}, "x")
        missing = False
    except KeyError as exc:
        missing = "E_MSPL_NO_LABEL" in str(exc)
    ok = check(missing,
               "AC-MSPL5 a patterns file without the label fails closed") and ok

    evid, plain, borrow = render_pair(world)
    keys = ["command", "evidence_line", "response"]
    def order(lines):
        found = []
        for row in lines:
            for key in keys:
                if row.startswith("- %s: " % labels[key]):
                    found.append(key)
        return found
    plain_lines = read_text(plain).splitlines()
    doc_lines = read_text(DOC).splitlines()
    ok = check(order(plain_lines) == keys,
               "AC-MSPL5 existing label lines keep their order") and ok
    ok = check(order(doc_lines) == keys,
               "AC-MSPL5 the shipped doc carries that same order") and ok
    borrow_lines = read_text(borrow).splitlines()
    cmd_at = [i for i, row in enumerate(borrow_lines)
              if row.startswith("- %s: " % labels["command"])]
    seg_at = [i for i, row in enumerate(borrow_lines)
              if row.startswith("- %s: " % labels["stamp_from"])]
    ok = check(bool(cmd_at) and seg_at == [cmd_at[0] + 1],
               "AC-MSPL5 the new segment sits directly under the command"
               " line") and ok
    return ok


def ac_mspl6(world):
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
    ok = check(ascii_only, "AC-MSPL6 source is pure ASCII")
    ok = check(imports <= {"argparse", "json", "sys"},
               "AC-MSPL6 imports are stdlib only (%r)" % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime"}),
               "AC-MSPL6 the module reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-MSPL6 zero network imports") and ok
    ok = check('"w"' not in source and "os.replace" not in source,
               "AC-MSPL6 the module holds no write primitive") and ok
    runner = read_text(RUNNER)
    ok = check(WIRED_EXPECT in runner,
               "AC-MSPL6 the runner wires this suite") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-MSPL6 the suite declares its own six criteria") and ok
    return ok


def main():
    print("MATRIX STAMP PROVENANCE LINE suite (R2442, %d criteria)"
          % EXPECTED_CRITERIA)
    world = make_world()
    try:
        results = [ac_mspl1(world), ac_mspl2(world), ac_mspl3(world),
                   ac_mspl4(world), ac_mspl5(world), ac_mspl6(world)]
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