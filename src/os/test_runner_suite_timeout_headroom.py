"""runner_suite_timeout_headroom suite (R2395; criteria AC-RTH1..AC-RTH6
were pre-registered inside the R2393 seed row of state/queue/tech.md line 462
BEFORE this code existed).

What this proves: the battery's 300s per-suite cap is now a READING. Each
registered suite's slowest measured leg comes from the runner's own evidence
lines, its headroom is cap minus that measured leg, a suite inside the
warning band is named with verdict BAND-HIT, a suite with no measured leg is
NO-MEASURE rather than comfortable, the CLI keeps 0/2/3/5 with a byte-stable
--json, and the module is pure ASCII, stdlib only, read-only and wired.

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

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import runner_suite_timeout_headroom as RTH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "runner_suite_timeout_headroom.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-runner-suite-timeout-headroom"

FAKE_RUNNER = (
    "SUITES = [\n"
    "    ('lobby', 'lobby/test_x.py', 79),\n"
    "    ('ledger', 'ledger/test_y.py', 11),\n"
    "    ('heavy', 'ledger/test_z.py', 4),\n"
    "]\n")

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


def suite_line(label, seconds, ok=True):
    return ("%s suite %s exit=%d pass-lines=3 fail-lines=0 criteria=3 %.1fs"
            % ("PASS" if ok else "FAIL", label, 0 if ok else 1, seconds))


def make_world(evidence, runner=FAKE_RUNNER):
    world = tempfile.mkdtemp(prefix="bigdomain-rth-")
    qa = os.path.join(world, "qa")
    sandbox = os.path.join(world, "src", "sandbox")
    os.makedirs(qa)
    os.makedirs(sandbox)
    body = "\n".join(evidence) + "\n"
    with io.open(os.path.join(qa, "reconcile-all-fixture.log"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with io.open(os.path.join(sandbox, "reconcile_all.py"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(runner)
    return world


def run_cli(world, args):
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE,
                                      "runner_suite_timeout_headroom.py")]
        + args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


class Patched(object):
    def __init__(self, owner, name, value):
        self.owner = owner
        self.name = name
        self.value = value
        self.saved = None

    def __enter__(self):
        self.saved = getattr(self.owner, self.name)
        setattr(self.owner, self.name, self.value)
        return self

    def __exit__(self, *exc):
        setattr(self.owner, self.name, self.saved)
        return False


def ac_rth1():
    """Durations come from the runner's own suite lines; a patch moves them."""
    world = make_world([suite_line("lobby", 43.0),
                        suite_line("ledger", 0.4),
                        "PASS suites 2/2 green, expected criteria total=3",
                        "  | PASS AC-S1: an echoed child line is not a suite"])
    evidence = os.path.join(world, "qa", "reconcile-all-fixture.log")
    runner = os.path.join(world, "src", "sandbox", "reconcile_all.py")
    try:
        durations, lines = RTH.read_evidence([evidence])
        labels = RTH.registry_labels(runner)
        straight = RTH.assess(300.0, 0.6, labels, durations)
        with Patched(RTH, "parse_evidence_line",
                     lambda line: (line.split()[2], True, 250.0)
                     if RTH.SUITE_LINE_RE.match(line) else None):
            moved_durations, _lines = RTH.read_evidence([evidence])
            moved = RTH.assess(300.0, 0.6, labels, moved_durations)
        ok = (lines == 2
              and sorted(durations) == ["ledger", "lobby"]
              and durations["lobby"] == [43.0]
              and [row["slowest"] for row in straight["suites"]]
              == ["43.0", "0.4", "-"]
              and moved["band"] == ["lobby", "ledger"]
              and straight["band"] == [])
        if not ok:
            print("  measured: lines=%r durations=%r straight=%r moved=%r"
                  % (lines, durations, straight["band"], moved["band"]),
                  flush=True)
        check(ok, "AC-RTH1 durations read from suite lines, patch moves them")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rth2():
    """Headroom is cap minus the slowest measured leg, per suite."""
    durations = {"lobby": [183.3, 43.0], "ledger": [194.9, 0.4]}
    report = RTH.assess(300.0, 0.6, ["lobby", "ledger"], durations)
    rows = dict((row["suite"], row) for row in report["suites"])
    tighter = RTH.assess(240.0, 0.9, ["lobby", "ledger"], durations)
    tight_rows = dict((row["suite"], row) for row in tighter["suites"])
    ok = (rows["ledger"]["slowest"] == "194.9"
          and rows["ledger"]["headroom"] == "105.1"
          and rows["ledger"]["legs"] == 2
          and rows["lobby"]["headroom"] == "116.7"
          and tight_rows["ledger"]["headroom"] == "45.1"
          and report["cap"] == "300.0"
          and report["verdict"] == RTH.BAND_HIT)
    if not ok:
        print("  measured: rows=%r tight=%r" % (rows, tight_rows), flush=True)
    check(ok, "AC-RTH2 headroom is cap minus the slowest measured leg")


def ac_rth3():
    """A band suite is named (exit 2); a comfortable pile is CLEAN (exit 0)."""
    hot = make_world([suite_line("lobby", 194.9), suite_line("ledger", 0.4),
                      suite_line("heavy", 12.0)])
    cool = make_world([suite_line("lobby", 43.0), suite_line("ledger", 0.4),
                       suite_line("heavy", 12.0)])
    try:
        rc_hot, body_hot, _err = run_cli(
            hot, ["--check", "--root", hot,
                  os.path.join(hot, "qa", "reconcile-all-fixture.log")])
        rc_hot_json, json_hot, _err = run_cli(
            hot, ["--check", "--root", hot, "--json",
                  os.path.join(hot, "qa", "reconcile-all-fixture.log")])
        rc_cool, body_cool, _err = run_cli(
            cool, ["--check", "--root", cool,
                   os.path.join(cool, "qa", "reconcile-all-fixture.log")])
        parsed = json.loads(json_hot)
        ok = (rc_hot == 2
              and "VERDICT BAND-HIT" in body_hot
              and "BAND lobby slowest=194.9s headroom=105.1s" in body_hot
              and rc_hot_json == 2 and parsed["band"] == ["lobby"]
              and parsed["verdict"] == "BAND-HIT"
              and rc_cool == 0 and "VERDICT HEADROOM-CLEAN" in body_cool
              and "BAND-HIT" not in body_cool
              and body_cool.count("BAND ") == 1)
        if not ok:
            print("  measured: hot=%r/%r cool=%r"
                  % (rc_hot, body_hot, body_cool), flush=True)
        check(ok, "AC-RTH3 band named with BAND-HIT, comfortable reads CLEAN")
    finally:
        shutil.rmtree(hot, ignore_errors=True)
        shutil.rmtree(cool, ignore_errors=True)


def ac_rth4():
    """A registered suite with no measured leg is NO-MEASURE, never clean."""
    world = make_world([suite_line("lobby", 43.0)])
    try:
        rc, body, _err = run_cli(
            world, ["--check", "--root", world,
                    os.path.join(world, "qa", "reconcile-all-fixture.log")])
        rc_json, json_body, _err = run_cli(
            world, ["--check", "--root", world, "--json",
                    os.path.join(world, "qa", "reconcile-all-fixture.log")])
        parsed = json.loads(json_body)
        rows = dict((row["suite"], row) for row in parsed["suites"])
        ok = (rc == 2 and rc_json == 2
              and parsed["verdict"] == "NO-MEASURE"
              and parsed["no_measure"] == ["ledger", "heavy"]
              and rows["ledger"]["status"] == "NO-MEASURE"
              and rows["ledger"]["slowest"] == "-"
              and rows["ledger"]["legs"] == 0
              and "NO-MEASURE ledger" in body
              and parsed["measured"] == 1 and parsed["total"] == 3)
        if not ok:
            print("  measured: rc=%r parsed=%r body=%r"
                  % (rc, parsed, body), flush=True)
        check(ok, "AC-RTH4 an unmeasured suite reads NO-MEASURE")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rth5():
    """Exits 0/2/3/5 with a byte-stable --json over the pinned keys."""
    cool = make_world([suite_line("lobby", 43.0), suite_line("ledger", 0.4),
                       suite_line("heavy", 12.0)])
    hot = make_world([suite_line("lobby", 194.9), suite_line("ledger", 0.4),
                      suite_line("heavy", 12.0)])
    broken = make_world([suite_line("lobby", 43.0),
                         suite_line("ledger", 0.4),
                         suite_line("heavy", 12.0)],
                        runner="SUITES = [ not literal ]\n")
    try:
        rc_zero, _b, _e = run_cli(cool, ["--check", "--root", cool])
        rc_two, _b, _e = run_cli(hot, ["--check", "--root", hot])
        rc_three, _b, _e = run_cli(cool, ["--check", "--root", cool,
                                          "--runner", os.path.join(
                                              cool, "src", "sandbox",
                                              "missing.py")])
        rc_five_a, _b, _e = run_cli(cool, ["--check", "--nope"])
        rc_five_b, _b, _e = run_cli(cool, [])
        rc_five_c, _b, _e = run_cli(cool, ["--check", "--cap", "0"])
        rc_a, body_a, _e = run_cli(cool, ["--check", "--root", cool, "--json"])
        rc_b, body_b, _e = run_cli(cool, ["--check", "--root", cool, "--json"])
        rc_broken, _b, _e = run_cli(broken, ["--check", "--root", broken])
        parsed = json.loads(body_a)
        ok = (rc_zero == 0 and rc_two == 2 and rc_three == 3
              and rc_five_a == 5 and rc_five_b == 5 and rc_five_c == 5
              and rc_broken == 3
              and rc_a == 0 and body_a == body_b
              and tuple(parsed.keys()) == RTH.REPORT_KEYS)
        if not ok:
            print("  measured: rcs=%r stable=%r keys=%r broken=%r"
                  % ((rc_zero, rc_two, rc_three, rc_five_a, rc_five_b,
                      rc_five_c, rc_broken), body_a == body_b,
                     tuple(parsed.keys()), rc_broken), flush=True)
        check(ok, "AC-RTH5 exits 0/2/3/5 and --json is byte-stable")
    finally:
        shutil.rmtree(cool, ignore_errors=True)
        shutil.rmtree(hot, ignore_errors=True)
        shutil.rmtree(broken, ignore_errors=True)


def ac_rth6():
    """Pure ASCII, stdlib only, read-only, wired with its own label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(
        r"\b(?:import time|import datetime|time\.time)\b", source)
    imports = re.findall(r"^\s*import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["ast", "io", "json", "os", "re",
                                           "sys"]
    no_write = not re.search(
        r"open\([^)]*[\"'](?:w|a|x|r\+|w\+|a\+)[\"']", source)
    no_mutate = not re.search(
        r"\b(?:os\.remove|os\.replace|os\.rename|os\.mkdir|makedirs|"
        r"tempfile)\b", source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_runner_suite_timeout_headroom.py" in runner)
    own_label = source.count('SUITE_LABEL = "%s"' % LABEL) == 1
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_write
          and no_mutate and wired and own_label)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r write=%r "
              "mutate=%r wired=%r label=%r"
              % (ascii_only, no_net, no_clock, sorted(set(imports)),
                 no_write, no_mutate, wired, own_label), flush=True)
    check(ok, "AC-RTH6 pure, read-only, and wired with its own label")


def main():
    print("runner_suite_timeout_headroom suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rth1()
    ac_rth2()
    ac_rth3()
    ac_rth4()
    ac_rth5()
    ac_rth6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())