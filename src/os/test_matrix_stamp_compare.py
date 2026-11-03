"""matrix_stamp_compare suite (R2418; criteria AC-MSC1..AC-MSC6 were pinned
at R2414 inside the seed row of state/queue/tech.md line 493 BEFORE this code).

What this proves: the matrix section's compare is content-only because the
render is stamp-ALIGNED to the document it is compared with, so a doc
regenerated in another minute no longer reads a mismatch of EQUAL byte length
on the one volatile line - and a genuine content difference at that same byte
length still fails with both counts.

The compare is driven through a stand-in generator in a fake root so the proof
does not depend on this window's registry count; the stamp-following of the
REAL generator is proved separately against the shipped document, so the one
thing that changed in suite_matrix is measured on the real tool too.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import io
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
sys.path.insert(0, BASE)

import matrix_stamp_compare as MSC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "matrix_stamp_compare.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-matrix-stamp-compare"
SANDBOX = os.path.join(SRC, "sandbox")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2418.log")
MATRIX_TOOL = os.path.join(SANDBOX, "suite_matrix.py")
OTHER_MINUTE = "1999-01-01 00:00 +08:00"
BODY = "SUITE body line one\nSUITE body line two\n"

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


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def recorded_evidence():
    """The evidence path the SHIPPED doc records, asked of suite_matrix's own
    doc_evidence_face at CALL time.

    R2421 birth-site repair, measured not guessed: the live leg of AC-MSC4
    pinned ONE round's evidence file, so the window after the doc was
    regenerated from the next round's evidence read live=FAIL while
    suite_matrix --check read PASS - a split that was the test's fault, not
    the law's. The doc already names the file it was rendered from, so this
    leg asks the same law --check asks instead of naming a round.
    """
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix  # noqa: E402  (one evidence-face law in the tree)
    recorded = suite_matrix.doc_evidence_face(read_text(DOC),
                                              suite_matrix.load_patterns())
    if recorded is None:
        return EVIDENCE
    return os.path.join(REPO, recorded.replace("/", os.sep))


def stamp_parts():
    """(prefix, stamp value) taken from the shipped doc through the law."""
    verdict, _code, stamp, _detail = MSC.stamp_of(DOC)
    if verdict != MSC.PASS or not stamp:
        return None, None
    for line in read_text(DOC).split("\n"):
        if stamp in line:
            return line[:line.index(stamp)], stamp
    return None, None


PREFIX, STAMP = stamp_parts()

FAKE_TEMPLATE = (
    "import os\n"
    "import sys\n"
    "a = sys.argv\n"
    "if '--out' not in a:\n"
    "    print('PASS check')\n"
    "    sys.exit(0)\n"
    "if '--stamp-from' not in a:\n"
    "    print('E_STUB_NO_STAMP_FROM')\n"
    "    sys.exit(9)\n"
    "ev = a[a.index('--evidence') + 1] if '--evidence' in a else ''\n"
    "if not os.path.isfile(ev):\n"
    "    print('FAIL no evidence ' + ev)\n"
    "    sys.exit(2)\n"
    "src = a[a.index('--stamp-from') + 1]\n"
    "text = open(src, encoding='utf-8').read()\n"
    "prefix = @PREFIX@\n"
    "lines = [l for l in text.split('\\n') if l.startswith(prefix)]\n"
    "if not lines:\n"
    "    print('E_STUB_NO_STAMP')\n"
    "    sys.exit(9)\n"
    "out = a[a.index('--out') + 1]\n"
    "open(out, 'w', encoding='utf-8', newline='\\n').write("
    "lines[0] + '\\n' + @BODY@)\n"
    "print('PASS generated')\n")

FAKE_TOOL = (FAKE_TEMPLATE.replace("@PREFIX@", repr(PREFIX or ""))
             .replace("@BODY@", repr(BODY)))


def make_world(tool=True, evidence=True):
    world = tempfile.mkdtemp(prefix="bigdomain-msc-w-")
    if tool:
        path = os.path.join(world, "src", "sandbox", "suite_matrix.py")
        os.makedirs(os.path.dirname(path))
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(FAKE_TOOL)
    if evidence:
        path = os.path.join(world, "qa", "evidence.log")
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("RUNNER PASS\n")
    return world


def make_doc(world, stamp, body=BODY):
    path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("%s%s\n%s" % (PREFIX, stamp, body))
    return path


def cli(args, root=REPO):
    proc = subprocess.Popen([sys.executable, MODULE] + args, cwd=root,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace") + err.decode(
        "utf-8", "replace")


def real_stamp_following(target):
    """What the REAL generator stamps when told to follow a document."""
    work = tempfile.mkdtemp(prefix="bigdomain-msc-r-")
    try:
        out_path = os.path.join(work, "matrix.md")
        proc = subprocess.run(
            [sys.executable, MATRIX_TOOL, "--out", out_path,
             "--evidence", EVIDENCE, "--stamp-from", target],
            cwd=REPO, capture_output=True)
        if proc.returncode != 0 or not os.path.isfile(out_path):
            return proc.returncode, None
        verdict, _code, stamp, _detail = MSC.stamp_of(out_path)
        return 0, stamp if verdict == MSC.PASS else None
    finally:
        shutil.rmtree(work, ignore_errors=True)


def ac_msc1():
    """Content-only: a doc from another minute still reads PASS."""
    if PREFIX is None:
        print("  measured: the shipped doc carries no readable stamp line",
              flush=True)
        check(False, "AC-MSC1 a doc from another minute reads PASS")
        return
    world = make_world()
    moved_world = make_world()
    other = make_doc(moved_world, OTHER_MINUTE)
    same = make_doc(world, STAMP)
    evidence = os.path.join(world, "qa", "evidence.log")
    try:
        live = MSC.compare(world, same, evidence)
        moved = MSC.compare(moved_world, other,
                            os.path.join(moved_world, "qa", "evidence.log"))
        code, out = cli(["--check", "--root", moved_world, "--doc", other,
                         "--evidence",
                         os.path.join(moved_world, "qa", "evidence.log")])
        real_rc, real_stamp = real_stamp_following(DOC)
        plain_work = tempfile.mkdtemp(prefix="bigdomain-msc-n-")
        try:
            plain = os.path.join(plain_work, "matrix.md")
            subprocess.run([sys.executable, MATRIX_TOOL, "--out", plain,
                            "--evidence", EVIDENCE], cwd=REPO,
                           capture_output=True)
            _v, _c, plain_stamp, _d = MSC.stamp_of(plain)
        finally:
            shutil.rmtree(plain_work, ignore_errors=True)
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(moved_world, ignore_errors=True)
    ok = (live["verdict"] == MSC.PASS
          and moved["verdict"] == MSC.PASS
          and moved["stamp"] == OTHER_MINUTE
          and code == 0
          and OTHER_MINUTE in out
          and real_rc == 0
          and real_stamp == STAMP
          and plain_stamp != OTHER_MINUTE)
    if not ok:
        print("  measured: live=%r moved=%r code=%r real=%r/%r plain=%r"
              % (live, moved, code, real_rc, real_stamp, plain_stamp),
              flush=True)
    check(ok, "AC-MSC1 a doc from another minute reads PASS and the real "
              "generator follows its stamp")


def ac_msc2():
    """A genuine content change of EQUAL length still FAILs with both counts."""
    world = make_world()
    changed = make_doc(world, STAMP,
                       BODY.replace("one", "eno", 1))
    evidence = os.path.join(world, "qa", "evidence.log")
    try:
        before = digest(changed)
        row = MSC.compare(world, changed, evidence)
        code, out = cli(["--check", "--root", world, "--doc", changed,
                         "--evidence", evidence])
        after = digest(changed)
    finally:
        shutil.rmtree(world, ignore_errors=True)
    ok = (row["verdict"] == MSC.FAIL
          and row["code"] == 2
          and row["on_disk_bytes"] == row["fresh_bytes"]
          and "on-disk=%dB" % row["on_disk_bytes"] in row["detail"]
          and "regenerated=%dB" % row["fresh_bytes"] in row["detail"]
          and code == 2
          and before == after)
    if not ok:
        print("  measured: row=%r code=%r unchanged=%r"
              % (row, code, before == after), flush=True)
    check(ok, "AC-MSC2 a genuine equal-length content difference FAILs naming "
              "both byte counts")


def ac_msc3():
    """Missing doc, missing tool, unreadable evidence: own codes, never open."""
    world = make_world()
    bare = make_world(tool=False)
    doc = make_doc(world, STAMP)
    evidence = os.path.join(world, "qa", "evidence.log")
    absent_doc = os.path.join(world, "docs", "absent.md")
    absent_ev = os.path.join(world, "qa", "absent.log")
    try:
        no_doc = MSC.compare(world, absent_doc, evidence)
        no_doc_code = cli(["--check", "--root", world, "--doc", absent_doc,
                           "--evidence", evidence])[0]
        no_tool = MSC.compare(bare, doc, evidence)
        no_tool_code = cli(["--check", "--root", bare, "--doc", doc,
                            "--evidence", evidence])[0]
        bad_ev = MSC.compare(world, doc, absent_ev)
        bad_ev_code = cli(["--check", "--root", world, "--doc", doc,
                           "--evidence", absent_ev])[0]
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(bare, ignore_errors=True)
    ok = (no_doc["verdict"] == MSC.MISSING_DOC
          and no_doc["code"] == MSC.E_MSC_NO_DOC
          and no_doc_code == 3
          and no_tool["verdict"] == MSC.NO_TOOL
          and no_tool["code"] == MSC.E_MSC_NO_TOOL
          and no_tool_code == 3
          and bad_ev["verdict"] == MSC.REGEN_FAILED
          and bad_ev["code"] == MSC.E_MSC_REGEN
          and bad_ev_code == 3)
    if not ok:
        print("  measured: no_doc=%r/%r no_tool=%r/%r bad_ev=%r/%r"
              % (no_doc, no_doc_code, no_tool, no_tool_code, bad_ev,
                 bad_ev_code), flush=True)
    check(ok, "AC-MSC3 missing doc / missing tool / unreadable evidence keep "
              "their own codes and never fail open")


def ac_msc4():
    """--check stays the authority and no path rewrites the shipped doc."""
    world = make_world()
    red_world = make_world()
    green = make_doc(world, STAMP)
    red = make_doc(red_world, STAMP, BODY.replace("two", "owt", 1))
    evidence = os.path.join(world, "qa", "evidence.log")
    try:
        before = digest(green)
        green_row = MSC.compare(world, green, evidence)
        mid = digest(green)
        red_row = MSC.compare(red_world, red,
                              os.path.join(red_world, "qa", "evidence.log"))
        after = digest(green)
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(red_world, ignore_errors=True)
    source = read_text(MODULE)
    never_writes_doc = not re.search(r'doc_path[^\n]*,\s*"w', source)
    live_row = MSC.compare(REPO, DOC, recorded_evidence())
    authority_live = subprocess.run([sys.executable, MATRIX_TOOL, "--check"],
                                    cwd=REPO, capture_output=True)
    agrees = ((authority_live.returncode == 0)
              == (live_row["verdict"] == MSC.PASS))
    ok = (green_row["verdict"] == MSC.PASS
          and red_row["verdict"] == MSC.FAIL
          and before == mid == after
          and never_writes_doc
          and agrees)
    if not ok:
        print("  measured: green=%r red=%r unchanged=%r no_write=%r"
              " check=%r live=%r agrees=%r"
              % (green_row, red_row, before == mid == after, never_writes_doc,
                 authority_live.returncode, live_row["verdict"], agrees),
              flush=True)
    check(ok, "AC-MSC4 --check remains the authority and no path rewrites the "
              "shipped doc")


def ac_msc5():
    """A doc with no stamp line refuses with its own code, never a pass."""
    world = make_world()
    path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
    os.makedirs(os.path.dirname(path))
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(BODY)
    evidence = os.path.join(world, "qa", "evidence.log")
    try:
        row = MSC.compare(world, path, evidence)
        code, out = cli(["--check", "--root", world, "--doc", path,
                         "--evidence", evidence])
        code_json, out_json = cli(["--check", "--json", "--root", world,
                                   "--doc", path, "--evidence", evidence])
        try:
            payload = json.loads(out_json)
        except ValueError:
            payload = None
    finally:
        shutil.rmtree(world, ignore_errors=True)
    ok = (row["verdict"] == MSC.NO_STAMP
          and row["code"] == MSC.E_MSC_NO_STAMP
          and row["on_disk_bytes"] is None
          and code == 3
          and MSC.E_MSC_NO_STAMP in out
          and code_json == 3
          and payload is not None
          and sorted(payload.keys()) == sorted(MSC.REPORT_KEYS)
          and payload["verdict"] == MSC.NO_STAMP)
    if not ok:
        print("  measured: row=%r code=%r out=%r json=%r"
              % (row, code, out.strip(), payload), flush=True)
    check(ok, "AC-MSC5 stamp-line absence is a refusal with its own code "
              "rather than an assumed pass")


def ac_msc6():
    """Pure ASCII, stdlib only, zero network, no clock, wired, one law."""
    source = read_text(MODULE)
    ascii_only = all(ord(ch) < 128 for ch in source)
    imports = set(re.findall(r"(?m)^import (\w+)", source))
    stdlib_only = imports <= {"io", "json", "os", "shutil", "subprocess",
                              "sys", "tempfile"}
    call_time_tree_import = source.count("import suite_matrix") == 1
    no_net = not re.search(
        r"\b(?:urllib|http|socket|requests|ssl|ftplib|smtplib)\b", source)
    no_clock = not re.search(
        r"\b(?:time\.time|time\.monotonic|strftime|datetime)\b", source)
    runner = read_text(RUNNER)
    wired = ('"%s"' % LABEL in runner
             and "test_matrix_stamp_compare.py" in runner)
    own_label = source.count('SUITE_LABEL = "%s"' % LABEL) == 1
    one_law = (source.count(".doc_stamp(") == 1
               and source.count('"--stamp-from"') == 1
               and "E_MSC_NO_STAMP" in source)
    ok = (ascii_only and stdlib_only and call_time_tree_import and no_net
          and no_clock and wired and own_label and one_law)
    if not ok:
        print("  measured: ascii=%r imports=%r tree_import=%r net=%r clock=%r"
              " wired=%r label=%r law=%r"
              % (ascii_only, sorted(imports), call_time_tree_import, no_net,
                 no_clock, wired, own_label, one_law), flush=True)
    check(ok, "AC-MSC6 pure ASCII, stdlib only, no clock, no network, one "
              "stamp law, wired with its own label")


def main():
    print("matrix_stamp_compare suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    if not os.path.isfile(EVIDENCE):
        print("MISSING evidence %s" % EVIDENCE, flush=True)
        return 3
    ac_msc1()
    ac_msc2()
    ac_msc3()
    ac_msc4()
    ac_msc5()
    ac_msc6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())