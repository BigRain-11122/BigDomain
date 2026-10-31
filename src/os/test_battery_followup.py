"""battery_followup suite (R2272; criteria AC-BFU1..AC-BFU6 were pre-registered
inside the R2250 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: the four post-battery sections are one callable instead of
forty-two per-round copies. The stub world below is a complete stand-in for the
four real tools, so every leg is exercised without touching the shipped tree.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import battery_followup as BF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "battery_followup.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-battery-followup"
DOC_BYTES = b"MATRIX\n"

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


def stub(body):
    return "import sys\n" + body + "\n"


MATRIX_OK = stub(
    "a = sys.argv\n"
    "if '--out' in a:\n"
    "    open(a[a.index('--out') + 1], 'wb').write(b'MATRIX\\n')\n"
    "    print('PASS generated matrix')\n"
    "else:\n"
    "    print('PASS check: byte-identical (7 bytes, 1 suites)')\n")

MATRIX_WIDE = stub(
    "a = sys.argv\n"
    "if '--out' in a:\n"
    "    open(a[a.index('--out') + 1], 'wb').write(b'MATRIX-REGEN\\n')\n"
    "    print('PASS generated matrix')\n"
    "else:\n"
    "    print('PASS check')\n")

CENSUS_OK = stub("print('CENSUS DRIFT-CLEAN files=0 flags=0')")
CENSUS_RED = stub("print('CENSUS DRIFT files=1 flags=1')\nsys.exit(2)")
FP_OK = stub("print('FINGERPRINT chain CLEAN domains=5')")
PROF_OK = stub("print('PROFILE daily check PASS')")
PROF_RED = stub("print('PROFILE drift')\nsys.exit(2)")


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def make_world(matrix=MATRIX_OK, profile=PROF_OK, census=CENSUS_OK,
               fp=FP_OK, tools=True, doc=True, evidence=True):
    """A complete stand-in root: four stub tools, the doc, an evidence file."""
    world = tempfile.mkdtemp(prefix="bigdomain-bfu-w-")
    if tools:
        write(os.path.join(world, "src", "sandbox", "suite_matrix.py"), matrix)
        write(os.path.join(world, "src", "sandbox", "fingerprint_regen.py"), fp)
        write(os.path.join(world, "src", "sandbox", "runner_profile.py"),
              profile)
        write(os.path.join(world, "src", "os", "qa_writer_census.py"), census)
    if doc:
        path = os.path.join(world, "docs", "sandbox-suite-matrix.md")
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "wb") as handle:
            handle.write(DOC_BYTES)
    if evidence:
        write(os.path.join(world, "qa", "evidence.log"), "RUNNER PASS\n")
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(root):
    entries = []
    for base, _dirs, files in os.walk(root):
        for leaf in sorted(files):
            path = os.path.join(base, leaf)
            with open(path, "rb") as handle:
                entries.append((os.path.relpath(path, root).replace(os.sep,
                                                                    "/"),
                                handle.read()))
    return tuple(sorted(entries))


def digest_files(paths):
    out = []
    for path in paths:
        with open(path, "rb") as handle:
            out.append((path, handle.read()))
    return tuple(out)


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def ac_bfu1():
    """The four pinned sections, in order, each PASS/FAIL with one detail."""
    world = make_world()
    try:
        report, bodies = BF.sections(world, "qa/evidence.log", "R2272")
        green = [entry["verdict"] for entry in report["sections"]]
        names = [entry["section"] for entry in report["sections"]]
        details_ok = all(entry["detail"] and "\n" not in entry["detail"]
                         for entry in report["sections"])
        bodies_ok = (len(bodies) == 4
                     and all(body.startswith("--- ") for body in bodies))
    finally:
        drop_world(world)
    world = make_world(profile=PROF_RED)
    try:
        red, _bodies = BF.sections(world, "qa/evidence.log", "R2273")
    finally:
        drop_world(world)
    ok = (names == list(BF.SECTIONS)
          and green == ["PASS", "PASS", "PASS", "PASS"]
          and report["verdict"] == "PASS" and report["failing"] == []
          and details_ok and bodies_ok
          and red["verdict"] == "FAIL" and red["failing"] == ["profile"]
          and [entry["verdict"] for entry in red["sections"]]
          == ["PASS", "PASS", "FAIL", "PASS"])
    if not ok:
        print("  measured: names=%r green=%r red=%r"
              % (names, green, red["failing"]), flush=True)
    check(ok, "AC-BFU1 four pinned sections in order, PASS/FAIL one-line detail")


def ac_bfu2():
    """Matrix regenerated into a temp copy; mismatch FAILs with BOTH counts."""
    world = make_world(matrix=MATRIX_WIDE)
    doc = os.path.join(world, "docs", "sandbox-suite-matrix.md")
    try:
        before = digest_files([doc])
        report, _bodies = BF.sections(world, "qa/evidence.log", "R2272")
        after = digest_files([doc])
        wide = report["sections"][0]
    finally:
        drop_world(world)
    world = make_world()
    try:
        report, _bodies = BF.sections(world, "qa/evidence.log", "R2272")
        even = report["sections"][0]
    finally:
        drop_world(world)
    ok = (wide["verdict"] == "FAIL"
          and "on-disk=%dB" % len(DOC_BYTES) in wide["detail"]
          and "regenerated=%dB" % len(b"MATRIX-REGEN\n") in wide["detail"]
          and "no rewrite" in wide["detail"]
          and before == after
          and even["verdict"] == "PASS"
          and "byte-identical" in even["detail"]
          and "%dB" % len(DOC_BYTES) in even["detail"])
    if not ok:
        print("  measured: wide=%r even=%r doc_unchanged=%r"
              % (wide, even, before == after), flush=True)
    check(ok, "AC-BFU2 matrix read-back, mismatch FAIL names both byte counts")


def ac_bfu3():
    """It writes nothing outside the evidence file it is given."""
    world = make_world()
    shipped = [os.path.join(REPO, "docs", "sandbox-suite-matrix.md"),
               os.path.join(REPO, "state", "queue", "tech.md")]
    try:
        before = digest_tree(world)
        shipped_before = digest_files(shipped)
        report, bodies = BF.sections(world, "qa/evidence.log", "R2272")
        after = digest_tree(world)
        shipped_after = digest_files(shipped)
        evidence = os.path.join(world, "qa", "evidence.log")
        with open(evidence, "rb") as handle:
            original = handle.read()
        written, eol_ok = BF.write_sections(evidence, report, bodies)
        listing = sorted(name for name, _blob in digest_tree(world))
        with open(evidence, "rb") as handle:
            appended = handle.read()
    finally:
        drop_world(world)
    grew = len(appended) == len(original) + written
    ascii_lf = (b"\r" not in appended[len(original):]
                and appended[len(original):].isascii())
    ok = (before == after and shipped_before == shipped_after
          and report["verdict"] == "PASS"
          and grew and ascii_lf and eol_ok
          and listing == ["docs/sandbox-suite-matrix.md", "qa/evidence.log",
                          "src/os/qa_writer_census.py",
                          "src/sandbox/fingerprint_regen.py",
                          "src/sandbox/runner_profile.py",
                          "src/sandbox/suite_matrix.py"])
    if not ok:
        print("  measured: world=%r shipped=%r grew=%r ascii=%r"
              % (before == after, shipped_before == shipped_after, grew,
                 ascii_lf), flush=True)
    check(ok, "AC-BFU3 read-orchestrator writes nothing; one writer, one path")


def ac_bfu4():
    """A missing tool or unreadable matrix FAILs with its code, never open."""
    world = make_world(tools=False)
    try:
        bare, _bodies = BF.sections(world, "qa/evidence.log", "R2272")
    finally:
        drop_world(world)
    world = make_world(doc=False)
    try:
        nodoc, _bodies = BF.sections(world, "qa/evidence.log", "R2272")
    finally:
        drop_world(world)
    codes = [entry["detail"].startswith(BF.E_BFU_NO_TOOL)
             for entry in bare["sections"]]
    ok = (bare["verdict"] == "FAIL" and all(codes)
          and bare["failing"] == list(BF.SECTIONS)
          and nodoc["sections"][0]["verdict"] == "FAIL"
          and nodoc["sections"][0]["detail"].startswith(BF.E_BFU_NO_MATRIX)
          and [entry["verdict"] for entry in nodoc["sections"]][1:]
          == ["PASS", "PASS", "PASS"])
    if not ok:
        print("  measured: bare=%r nodoc=%r"
              % (bare["failing"], nodoc["sections"][0]), flush=True)
    check(ok, "AC-BFU4 missing tool / unreadable matrix FAIL with codes")


def ac_bfu5():
    """CLI 0 / 2 / 3 / 5, --json pinned and byte-stable, one append target."""
    world = make_world()
    red = make_world(profile=PROF_RED)
    gone = make_world(evidence=False)
    try:
        green = run_cli(["--root", world, "--evidence", "qa/evidence.log",
                         "--label", "R2272", "--dry-run", "--json"])
        again = run_cli(["--root", world, "--evidence", "qa/evidence.log",
                         "--label", "R2272", "--dry-run", "--json"])
        red_run = run_cli(["--root", red, "--evidence", "qa/evidence.log",
                           "--dry-run"])
        missing = run_cli(["--root", gone, "--evidence", "qa/evidence.log",
                           "--dry-run"])
        no_flag = run_cli(["--root", world, "--dry-run"])
        bad_flag = run_cli(["--root", world, "--evidence", "qa/evidence.log",
                           "--nonsense"])
        bad_round = run_cli(["--root", world, "--evidence", "qa/evidence.log",
                             "--round", "abc", "--dry-run"])
        no_root = run_cli(["--root", os.path.join(world, "nope"),
                           "--evidence", "qa/evidence.log", "--dry-run"])
        before = digest_tree(world)
        append = run_cli(["--root", world, "--evidence", "qa/evidence.log"])
        after = digest_tree(world)
    finally:
        drop_world(world)
        drop_world(red)
        drop_world(gone)
    payload = green[1].split("{", 1)
    pinned = list(json.loads("{" + payload[1]).keys()) if len(payload) > 1 else []
    changed = [name for (name, blob), (_n2, blob2) in
               zip(before, after) if blob != blob2]
    ok = (green[0] == 0 and "SECTION matrix PASS" in green[1]
          and "VERDICT R2272 PASS failing=none" in green[1]
          and "APPENDED" not in green[1]
          and green == again
          and red_run[0] == 2 and "failing=profile" in red_run[1]
          and missing[0] == 3 and "MISSING EVIDENCE" in missing[1]
          and no_flag[0] == 5 and bad_flag[0] == 5 and bad_round[0] == 5
          and no_root[0] == 5
          and pinned == list(BF.REPORT_KEYS)
          and append[0] == 0 and "APPENDED" in append[1]
          and changed == ["qa/evidence.log"])
    if not ok:
        print("  measured: %r %r %r %r pinned=%r changed=%r"
              % (green[0], red_run[0], missing[0], no_flag[0], pinned,
                 changed), flush=True)
    check(ok, "AC-BFU5 CLI 0/2/3/5, --json pinned, single append target")


def ac_bfu6():
    """Purity, wiring, and the legacy pile measured against the callable."""
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "urlopen", "time.time", "datetime")
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_battery_followup.py" in wiring)
    copies = []
    for name in sorted(os.listdir(BASE)):
        if name.startswith("battery_followup_R") and name.endswith(".py"):
            copies.append(os.path.getsize(os.path.join(BASE, name)))
    total = sum(copies)
    newest = max(copies) if copies else 0
    ok = (ascii_only and not any(token in text for token in blocked)
          and wired and len(copies) >= 4 and total > len(raw)
          and newest > 0)
    print("  legacy copies=%d total=%dB widest=%dB callable=%dB"
          % (len(copies), total, newest, len(raw)), flush=True)
    if not ok:
        print("  measured: ascii=%r wired=%r copies=%d total=%d callable=%d"
              % (ascii_only, wired, len(copies), total, len(raw)), flush=True)
    check(ok, "AC-BFU6 ASCII, no network, wired, legacy pile byte-wider")


def main():
    print("battery_followup suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_bfu1()
    ac_bfu2()
    ac_bfu3()
    ac_bfu4()
    ac_bfu5()
    ac_bfu6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())