"""followup_incomplete_cause suite (R2343; criteria AC-FIC1..AC-FIC6 were
pre-registered inside the R2325 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: INCOMPLETE stops being one word. A round whose log predates
the SECTION ritual reads LEGACY-DIALECT (no rerun can heal it), a round whose
sections ran but whose VERDICT line is missing reads NO-VERDICT, a round whose
VERDICT exists while a named section is ABSENT reads MISSING-SECTION with the
absent names listed, and a round with nothing absent reads COMPLETE. The
section vocabulary and the SECTION/VERDICT reading are asked of
followup_history rather than restated, so a patched parser moves this reader.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
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

import followup_history as FH  # noqa: E402
import followup_incomplete_cause as FIC  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "followup_incomplete_cause.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-followup-incomplete-cause"

COMPLETE_BODY = ("RUNNER PASS 4/4 suites green\n"
                 "SECTION matrix PASS\nSECTION fingerprint PASS\n"
                 "SECTION profile PASS\nSECTION census PASS\n"
                 "VERDICT R1500 PASS\n")
NO_VERDICT_BODY = ("RUNNER PASS 4/4 suites green\n"
                   "SECTION matrix PASS\nSECTION fingerprint PASS\n"
                   "SECTION profile PASS\nSECTION census PASS\n")
MISSING_BODY = ("RUNNER PASS 4/4 suites green\n"
                "SECTION matrix PASS\nSECTION fingerprint PASS\n"
                "VERDICT R1500 PASS\n")
LEGACY_BODY = "RUNNER PASS 4/4 suites green\nall four sections ran fine\n"

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


def make_world(files):
    """A temp root with one qa directory; body None makes a directory."""
    world = tempfile.mkdtemp(prefix="bigdomain-fic-")
    qa = os.path.join(world, "qa")
    os.makedirs(qa)
    for name, body in files:
        target = os.path.join(qa, name)
        if body is None:
            os.makedirs(target)
            continue
        with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return world


def tree_digest(world):
    """Every file under the world with size and digest, plus directories."""
    out = []
    for root, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(dirs):
            out.append(("d", os.path.relpath(os.path.join(root, name), world)))
        for name in sorted(files):
            path = os.path.join(root, name)
            blob = io.open(path, "rb").read()
            out.append(("f", os.path.relpath(path, world), len(blob),
                        hashlib.sha256(blob).hexdigest()))
    return out


def run_cli(args, cwd=None):
    proc = subprocess.Popen([sys.executable, MODULE] + args,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            cwd=cwd)
    out = proc.communicate()[0]
    return proc.returncode, out.decode("utf-8", "replace")


def one_round(world, name="reconcile-all-R1500.log"):
    report = FIC.audit(world, "qa")
    for item in report["rounds"]:
        if item["evidence"].endswith(name):
            return report, item
    raise AssertionError("round not found: " + name)


def case_fic1():
    """AC-FIC1: readings asked of followup_history; a patched parser flows."""
    source = io.open(MODULE, encoding="utf-8").read()
    asked = ("FH.parse(" in source and "FH.vocabulary(" in source
             and "FH.read_log(" in source and "FH.collect(" in source)
    no_second_scan = ("re.compile" not in source and '"SECTION"' not in source
                      and "'SECTION'" not in source)
    world = make_world([("reconcile-all-R1500.log", MISSING_BODY)])
    try:
        report, item = one_round(world)
        moved = item["cause"] == "MISSING-SECTION"
        real = FH.parse
        try:
            FH.parse = lambda text: ({"matrix": ["PASS"], "fingerprint": ["PASS"],
                                      "profile": ["PASS"], "census": ["PASS"]},
                                     "PASS", "RUNNER")
            patched = FIC.audit(world, "qa")["rounds"][0]["cause"]
        finally:
            FH.parse = real
        flow = moved and patched == "COMPLETE"
    finally:
        shutil.rmtree(world, ignore_errors=True)
    check(asked and no_second_scan and flow,
          "AC-FIC1 readings asked of followup_history, patched parser flows")


def case_fic2():
    """AC-FIC2: four causes disjoint, every round lands in exactly one."""
    world = make_world([("reconcile-all-R1500.log", COMPLETE_BODY),
                        ("reconcile-all-R1501.log", NO_VERDICT_BODY),
                        ("reconcile-all-R1502.log", MISSING_BODY),
                        ("reconcile-all-R1503.log", LEGACY_BODY)])
    names = list(FH.vocabulary())
    try:
        report = FIC.audit(world, "qa")
        seen = [item["cause"] for item in report["rounds"]]
        disjoint = len(set(seen)) == len(seen)
        covered = sorted(set(seen)) == sorted(FIC.CAUSES)
        counts_ok = sum(report["counts"].values()) == len(report["rounds"])
        direct = [FIC.classify({n: ["PASS"] for n in names}, "PASS", names)["cause"],
                  FIC.classify({n: ["PASS"] for n in names}, None, names)["cause"],
                  FIC.classify({"matrix": ["PASS"]}, "PASS", names)["cause"],
                  FIC.classify({}, None, names)["cause"]]
        four = (direct == ["COMPLETE", "NO-VERDICT", "MISSING-SECTION",
                           "LEGACY-DIALECT"])
        gone = report["rounds"][2]["absent"]
        listed = gone and gone == [n for n in names if n not in ("matrix",
                                                                "fingerprint")]
    finally:
        shutil.rmtree(world, ignore_errors=True)
    check(disjoint and covered and counts_ok and four and listed,
          "AC-FIC2 four causes disjoint, one per round, absent names listed")


def case_fic3():
    """AC-FIC3: derived from the log alone - no clock, no round threshold."""
    source = io.open(MODULE, encoding="utf-8").read()
    no_clock = ("import time" not in source and "import datetime" not in source
                and "time." not in source and "datetime." not in source)
    worlds = []
    try:
        same = []
        for label in ("R1500", "R2050", "R9999"):
            world = make_world([("reconcile-all-%s.log" % label, LEGACY_BODY)])
            worlds.append(world)
            same.append(one_round(
                world, "reconcile-all-%s.log" % label)[1]["cause"])
        stable = len(set(same)) == 1 and same[0] == "LEGACY-DIALECT"
        numeric = [line for line in source.splitlines()
                   if "round" in line.lower() and ">" in line
                   and "R1" in line]
        no_threshold = not numeric
    finally:
        for world in worlds:
            shutil.rmtree(world, ignore_errors=True)
    check(no_clock and stable and no_threshold,
          "AC-FIC3 cause from the log alone, no clock and no round threshold")


def case_fic4():
    """AC-FIC4: unreadable or absent evidence refuses at 3, never COMPLETE."""
    empty = tempfile.mkdtemp(prefix="bigdomain-fic4-")
    try:
        absent_root = os.path.join(empty, "nowhere")
        code_absent, out_absent = run_cli(["--audit", "--root", absent_root])
        never_complete = "COMPLETE" not in out_absent
        own_code = "E_FIC_NO_EVIDENCE" in out_absent and code_absent == 3
        world = make_world([("reconcile-all-R1500.log", None)])
        code_bad, out_bad = run_cli(["--audit", "--root", world])
        unreadable = (code_bad == 3 and "E_FIC_UNREADABLE" in out_bad
                      and "COMPLETE" not in out_bad)
        no_dir = os.path.join(empty, "nodir")
        os.makedirs(no_dir)
        code_nodir, out_nodir = run_cli(["--audit", "--root", no_dir])
        second = code_nodir == 3 and "E_FIC_NO_EVIDENCE" in out_nodir
    finally:
        shutil.rmtree(empty, ignore_errors=True)
    check(own_code and never_complete and unreadable and second,
          "AC-FIC4 absent/unreadable evidence refuses at 3 with its own code")


def case_fic5():
    """AC-FIC5: read-only, exit codes, byte-stable --json over pinned keys."""
    world = make_world([("reconcile-all-R1500.log", COMPLETE_BODY),
                        ("reconcile-all-R1501.log", NO_VERDICT_BODY)])
    clean = make_world([("reconcile-all-R1500.log", COMPLETE_BODY),
                        ("reconcile-all-R1501.log", COMPLETE_BODY)])
    try:
        before = tree_digest(world)
        FIC.audit(world, "qa")
        read_only = before == tree_digest(world)
        code_split, _out_split = run_cli(["--audit", "--root", world])
        code_clean, _out_clean = run_cli(["--audit", "--root", clean])
        codes = code_split == 2 and code_clean == 0
        code_bad, _out_bad = run_cli(["--audit", "--explode"])
        bad = code_bad == 5
        first = run_cli(["--audit", "--root", world, "--json"])[1]
        second = run_cli(["--audit", "--root", world, "--json"])[1]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == FIC.REPORT_KEYS
        rows_pinned = all(tuple(row.keys()) == FIC.ROW_KEYS
                          for row in parsed["rounds"])
        stable = first == second
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(clean, ignore_errors=True)
    check(read_only and codes and bad and pinned and rows_pinned and stable,
          "AC-FIC5 read-only, 0/2/5 codes, pinned byte-stable JSON")


def case_fic6():
    """AC-FIC6: pure-ASCII, stdlib only, zero network, own reconcile label."""
    raw = io.open(MODULE, "rb").read()
    ascii_ok = all(byte < 128 for byte in raw)
    source = raw.decode("ascii")
    imports = sorted(set(line.split()[1] for line in source.splitlines()
                         if line.startswith("import ")))
    stdlib_only = set(imports) == {"json", "os", "sys", "followup_history"}
    no_network = not any(token in source for token in
                         ("socket", "urllib", "http", "requests"))
    runner = io.open(RUNNER, encoding="utf-8").read()
    wired = ('"%s"' % LABEL) in runner and "test_followup_incomplete_cause.py" in runner
    check(ascii_ok and stdlib_only and no_network and wired,
          "AC-FIC6 ASCII, stdlib only, zero network, reconcile label wired")


def main():
    print("followup_incomplete_cause suite (criteria=%d)" % EXPECTED_CRITERIA,
          flush=True)
    case_fic1()
    case_fic2()
    case_fic3()
    case_fic4()
    case_fic5()
    case_fic6()
    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                              PASSES, EXPECTED_CRITERIA), flush=True)
    return 0 if FAILS == 0 and PASSES == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(main())