"""evidence_capture suite (R2261; criteria AC-EVC1..AC-EVC6 were pinned in
state/queue/tech.md as the R2259 seed row BEFORE this code existed).

What this proves: the per-round evidence ritual (double run, criterion digest,
single-writer utf-8 LF body, adjacent batch, live line) lived in eighty-eight
hand-typed near-copies. This suite pins the callable that replaces the ritual -
the two legs agree on their criterion lines while their wall-clock bodies
differ, the file lands once as utf-8 LF and a second write is refused, the
adjacent batch keeps its declared order and a red leg refuses the whole capture
with nothing left on disk, and every refusal has its own code.

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

import evidence_capture as EC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "evidence_capture.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-evidence-capture"
WIRED_EXPECT = '"test_evidence_capture.py"), 6),'

GREEN = ("import sys\n"
         "print('PASS alpha')\n"
         "print('SUITE PASS 1/1')\n"
         "sys.exit(0)\n")

GREEN_CLOCK = ("import sys, time\n"
               "print('PASS alpha')\n"
               "print('clock %d' % time.time_ns())\n"
               "print('PASS beta')\n"
               "print('SUITE PASS 2/2')\n"
               "sys.exit(0)\n")

RED = ("import sys\n"
       "print('PASS alpha')\n"
       "print('FAIL beta')\n"
       "print('SUITE FAIL 1/2')\n"
       "sys.exit(1)\n")

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


def write_text(path, body):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)


def world(suites):
    """A throwaway root holding the named suites plus an empty qa/ dir."""
    root = tempfile.mkdtemp(prefix="bigdomain-evc-")
    os.makedirs(os.path.join(root, "qa"))
    for name, body in suites.items():
        write_text(os.path.join(root, name), body)
    return root


def drop(root):
    shutil.rmtree(root, ignore_errors=True)


def refusal(fn, *args, **kwargs):
    """Return the refusal code, or None-free tuple when it did not refuse."""
    try:
        fn(*args, **kwargs)
    except EC.EvidenceError as exc:
        return exc.code, exc.detail
    return None, None


def read_bytes(path):
    with io.open(path, "rb") as handle:
        return handle.read()


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + list(args),
                          cwd=BASE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_evc1():
    """Two legs, one digest of the criterion lines, differing wall clock."""
    root = world({"green_clock.py": GREEN_CLOCK})
    try:
        report = EC.capture(root, "R9999", "green_clock.py",
                            evidence="qa/ev.log")
        body = read_bytes(os.path.join(root, "qa", "ev.log"))
    finally:
        drop(root)
    text = body.decode("utf-8")
    digests = [line.split("digest=")[1].strip()
               for line in text.splitlines()
               if line.startswith("== LEG")]
    clocks = [line.split("clock ")[1].strip()
              for line in text.splitlines()
              if line.startswith("clock ")]
    manual = EC.criteria_digest("PASS alpha\nPASS beta\n")
    ok = (report["legs"] == 2
          and report["identical"] is True
          and report["digest"] == manual
          and len(digests) == 2 and digests[0] == digests[1] == manual
          and len(clocks) == 2 and clocks[0] != clocks[1]
          and text.count("SUITE PASS 2/2") == 2)
    if not ok:
        print("  measured legs=%r identical=%r digest=%r manual=%r "
              "digests=%r clocks=%r"
              % (report["legs"], report["identical"], report["digest"],
                 manual, digests, clocks), flush=True)
    check(ok, "AC-EVC1 two legs same criterion digest, wall clock differs")


def ac_evc2():
    """One writer, utf-8 LF, exactly one trailing newline, second write refused."""
    root = world({"green.py": GREEN})
    try:
        report = EC.capture(root, "R9999", "green.py", evidence="qa/ev.log")
        path = os.path.join(root, "qa", "ev.log")
        first = read_bytes(path)
        code, _detail = refusal(EC.capture, root, "R9999", "green.py",
                                evidence="qa/ev.log")
        second = read_bytes(path)
    finally:
        drop(root)
    ok = (b"\r" not in first
          and first.endswith(b"\n") and not first.endswith(b"\n\n")
          and first.decode("utf-8")
          and report["bytes"] == len(first)
          and code == "E_EVC_EXISTS"
          and second == first)
    if not ok:
        print("  measured cr=%r tail=%r bytes=%r code=%r untouched=%r"
              % (b"\r" in first, first[-3:], report["bytes"], code,
                 second == first), flush=True)
    check(ok, "AC-EVC2 utf-8 LF single trailing newline, reuse refused")


def ac_evc3():
    """Declared adjacent order with its own SUITE lines; a red leg refuses."""
    root = world({"green.py": GREEN,
                  "green2.py": GREEN,
                  "red.py": RED})
    try:
        good = EC.capture(root, "R9999", "green.py",
                          adjacent=["green.py", "green2.py"],
                          evidence="qa/ok.log")
        code, detail = refusal(EC.capture, root, "R9999", "green.py",
                               adjacent=["green.py", "red.py"],
                               evidence="qa/red.log")
        left = os.path.exists(os.path.join(root, "qa", "red.log"))
    finally:
        drop(root)
    rows = good["adjacent"]
    ok = ([row["name"] for row in rows] == ["green.py", "green2.py"]
          and [row["rc"] for row in rows] == [0, 0]
          and all(row["suite_line"].startswith("SUITE PASS")
                  for row in rows)
          and good["fails"] == 0 and good["offending"] is None
          and code == "E_EVC_RED" and detail == "red.py"
          and left is False)
    if not ok:
        print("  measured rows=%r code=%r detail=%r left=%r"
              % (rows, code, detail, left), flush=True)
    check(ok, "AC-EVC3 adjacent order recorded, red leg refuses with no file")


def ac_evc4():
    """Missing suite, unreadable directory and a red suite fail closed."""
    root = world({"green.py": GREEN, "red.py": RED})
    try:
        missing = refusal(EC.capture, root, "R9999", "absent.py",
                          evidence="qa/ev.log")
        bad_dir = refusal(EC.capture, root, "R9999", "green.py",
                          evidence="nowhere/deep/ev.log")
        red = refusal(EC.capture, root, "R9999", "red.py",
                      evidence="qa/ev.log")
        absent_adjacent = refusal(EC.capture, root, "R9999", "green.py",
                                  adjacent=["green.py", "absent.py"],
                                  evidence="qa/ev.log")
        bad_round = refusal(EC.capture, root, "2261", "green.py",
                            evidence="qa/ev.log")
        left = [name for name in ("ev.log",)
                if os.path.exists(os.path.join(root, "qa", name))]
        stray = os.path.exists(os.path.join(root, "nowhere"))
    finally:
        drop(root)
    ok = (missing[0] == "E_EVC_NO_SUITE"
          and bad_dir[0] == "E_EVC_BADDIR"
          and red[0] == "E_EVC_RED" and red[1] == "red.py"
          and absent_adjacent[0] == "E_EVC_NO_SUITE"
          and bad_round[0] == "E_EVC_BAD_ROUND"
          and left == [] and stray is False)
    if not ok:
        print("  measured missing=%r bad_dir=%r red=%r adjacent=%r round=%r "
              "left=%r stray=%r"
              % (missing, bad_dir, red, absent_adjacent, bad_round, left,
                 stray), flush=True)
    check(ok, "AC-EVC4 three refusals each with its own code, zero residue")


def ac_evc5():
    """CLI codes 0/2/3/4/5 and a byte-stable pinned json."""
    root = world({"green.py": GREEN, "red.py": RED})
    try:
        ev = os.path.join(root, "qa", "cli.log")
        rc_green, body_green = run_cli(["--round", "R9999", "--suite",
                                        "green.py", "--root", root,
                                        "--evidence", "qa/cli.log"])
        made = os.path.exists(ev)
        rc_again, body_again = run_cli(["--round", "R9999", "--suite",
                                        "green.py", "--root", root,
                                        "--evidence", "qa/cli.log"])
        rc_red, body_red = run_cli(["--round", "R9999", "--suite", "red.py",
                                    "--root", root,
                                    "--evidence", "qa/red.log"])
        rc_flag, _body_flag = run_cli(["--round", "R9999", "--suite",
                                       "green.py", "--root", root,
                                       "--bogus"])
        rc_missing, _body_missing = run_cli(["--round", "R9999", "--suite",
                                             "absent.py", "--root", root])
        if made:
            os.unlink(ev)
        rc_first, body_first = run_cli(["--round", "R9999", "--suite",
                                        "green.py", "--root", root,
                                        "--evidence", "qa/cli.log",
                                        "--json"])
        os.unlink(ev)
        rc_second, body_second = run_cli(["--round", "R9999", "--suite",
                                          "green.py", "--root", root,
                                          "--evidence", "qa/cli.log",
                                          "--json"])
    finally:
        drop(root)
    keys = list(json.loads(body_first).keys())
    ok = (rc_green == 0 and made
          and "verdict=CAPTURED" in body_green
          and rc_again == 4 and "E_EVC_EXISTS" in body_again
          and rc_red == 2 and "E_EVC_RED" in body_red
          and rc_flag == 5 and "E_EVC_BAD_ARGS" in _body_flag
          and rc_missing == 3 and "E_EVC_NO_SUITE" in _body_missing
          and rc_first == 0 and rc_second == 0
          and body_first == body_second
          and keys == list(EC.REPORT_KEYS))
    if not ok:
        print("  measured green=%r made=%r again=%r red=%r flag=%r "
              "missing=%r stable=%r keys=%r"
              % (rc_green, made, rc_again, rc_red, rc_flag, rc_missing,
                 body_first == body_second, keys), flush=True)
    check(ok, "AC-EVC5 CLI 0/2/3/4/5 with byte-stable pinned json")


def ac_evc6():
    """Purity, wiring, and the legacy ritual pile measured byte-wider."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_only = True
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "import asyncio", "urlopen")
    no_net = not any(token in text for token in blocked)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_evidence_capture.py" in wiring) \
        and (WIRED_EXPECT in wiring)
    legacy = [name for name in sorted(os.listdir(BASE))
              if name.startswith("evidence_R") and name.endswith(".py")]
    legacy_bytes = 0
    for name in legacy:
        with io.open(os.path.join(BASE, name), "rb") as handle:
            legacy_bytes += len(handle.read())
    callable_bytes = len(raw)
    wider = len(legacy) >= 50 and legacy_bytes > callable_bytes
    print("  measured legacy_files=%d legacy_bytes=%d callable_bytes=%d"
          % (len(legacy), legacy_bytes, callable_bytes), flush=True)
    ok = ascii_only and no_net and wired and wider
    if not ok:
        print("  measured ascii=%r net=%r wired=%r wider=%r"
              % (ascii_only, no_net, wired, wider), flush=True)
    check(ok, "AC-EVC6 pure ASCII, no network, wired, legacy pile byte-wider")


def main():
    print("evidence_capture suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_evc1()
    ac_evc2()
    ac_evc3()
    ac_evc4()
    ac_evc5()
    ac_evc6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())