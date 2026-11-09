"""runner_suite_timeout_headroom override face suite (R2599).

Criteria AC-EDWU1..AC-EDWU6 were pre-registered inside the R2598 seed row of
state/queue/tech.md line 632 BEFORE this code existed.

What this proves: the reader now consumes the runner's AC-RSC2 override table
by AST, so a suite with a declared 900s ceiling is judged against 900s and its
headroom is reported against that ceiling; an undeclared suite still reads the
flat global cap byte for byte; a malformed or non-literal table REFUSES with
its own code instead of silently reporting the global cap; every row names the
cap it was judged against; every R2395 answer survives; and the module stays
pure ASCII, stdlib only, read-only, clock-free and wired with its own label.

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
sys.path.insert(0, BASE)

import runner_suite_timeout_headroom as RTH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "runner_suite_timeout_headroom.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-runner-suite-timeout-headroom-overrides"

RUNNER_HEAD = (
    "SUITE_TIMEOUT_S = 600\n"
    "SUITES = [\n"
    "    ('lobby', 'lobby/test_x.py', 79),\n"
    "    ('heavy', 'ledger/test_z.py', 4),\n"
    "    ('ghost', 'ledger/test_q.py', 2),\n"
    "]\n")

RUNNER_OVERRIDES = (
    "SUITE_TIMEOUT_S = 600\n"
    "SUITE_TIMEOUT_OVERRIDES = {\n"
    "    \"heavy\": 900,\n"
    "}\n"
    "SUITES = [\n"
    "    ('lobby', 'lobby/test_x.py', 79),\n"
    "    ('heavy', 'ledger/test_z.py', 4),\n"
    "    ('ghost', 'ledger/test_q.py', 2),\n"
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


def make_world(evidence, runner=RUNNER_OVERRIDES):
    world = tempfile.mkdtemp(prefix="bigdomain-edwu-")
    qa = os.path.join(world, "qa")
    sandbox = os.path.join(world, "src", "sandbox")
    os.makedirs(qa)
    os.makedirs(sandbox)
    with io.open(os.path.join(qa, "reconcile-all-fixture.log"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(evidence) + "\n")
    with io.open(os.path.join(sandbox, "reconcile_all.py"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(runner)
    return world


def run_cli(world, args):
    proc = subprocess.Popen(
        [sys.executable, MODULE] + args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


def evidence_path(world):
    return os.path.join(world, "qa", "reconcile-all-fixture.log")


def ac_edwu1():
    """A declared override is the cap that suite is judged against."""
    world = make_world([suite_line("lobby", 43.0),
                        suite_line("heavy", 600.0),
                        suite_line("ghost", 12.0)])
    try:
        rc, body, _err = run_cli(world, ["--check", "--root", world,
                                         "--json", evidence_path(world)])
        parsed = json.loads(body)
        rows = dict((row["suite"], row) for row in parsed["suites"])
        ok = (rc == 2
              and rows["heavy"]["cap"] == "900.0"
              and rows["heavy"]["slowest"] == "600.0"
              and rows["heavy"]["headroom"] == "300.0"
              and rows["heavy"]["status"] == RTH.BAND_HIT
              and rows["lobby"]["cap"] == "600.0"
              and rows["lobby"]["headroom"] == "557.0")
        if not ok:
            print("  measured: rc=%r heavy=%r lobby=%r"
                  % (rc, rows.get("heavy"), rows.get("lobby")), flush=True)
        check(ok, "AC-EDWU1 declared override is the cap judged against")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_edwu2():
    """An undeclared suite still reads the flat global cap byte for byte."""
    durations = {"lobby": [43.0, 12.0], "ghost": [0.4]}
    labels = ["lobby", "ghost", "absent"]
    base = RTH.assess(600.0, 0.6, labels, durations)
    with_empty = RTH.assess(600.0, 0.6, labels, durations, {})
    with_other = RTH.assess(600.0, 0.6, labels, durations, {"elsewhere": 900})
    rendered = RTH.render(base)
    ok = (base == with_empty == with_other
          and base["cap"] == "600.0"
          and all(row["cap"] == "600.0" for row in base["suites"])
          and "SUITE lobby cap=600.0s legs=2 slowest=43.0s headroom=557.0s "
              "COMFORTABLE" in rendered
          and "VERDICT" in rendered)
    if not ok:
        print("  measured: equal=%r rows=%r"
              % (base == with_empty == with_other, base["suites"]), flush=True)
    check(ok, "AC-EDWU2 undeclared suite reads the flat global cap")


def ac_edwu3():
    """A malformed or non-literal override table refuses with its own code."""
    bad_runners = [
        RUNNER_OVERRIDES.replace("SUITE_TIMEOUT_OVERRIDES = {\n"
                                 "    \"heavy\": 900,\n"
                                 "}\n", "SUITE_TIMEOUT_OVERRIDES = 900\n"),
        RUNNER_OVERRIDES.replace('"heavy": 900', '"heavy": "900"'),
        RUNNER_OVERRIDES.replace('"heavy": 900', '"heavy": 0'),
        RUNNER_OVERRIDES.replace('"heavy": 900', '"heavy": NINE_HUNDRED'),
    ]
    codes = []
    refused = 0
    for body in bad_runners:
        world = make_world([suite_line("lobby", 43.0)], runner=body)
        try:
            rc, out, _err = run_cli(world, ["--check", "--root", world])
            codes.append(rc)
            if rc == 3 and "E_RTH_BAD_OVERRIDES" in out:
                refused += 1
        finally:
            shutil.rmtree(world, ignore_errors=True)
    ok = refused == len(bad_runners) and set(codes) == set([3])
    if not ok:
        print("  measured: codes=%r refused=%d/%d"
              % (codes, refused, len(bad_runners)), flush=True)
    check(ok, "AC-EDWU3 malformed override table refuses with its own code")


def ac_edwu4():
    """Every row names the cap it was judged against, measured and not."""
    world = make_world([suite_line("lobby", 43.0),
                        suite_line("heavy", 600.0)])
    try:
        rc, body, _err = run_cli(world, ["--check", "--root", world,
                                         evidence_path(world)])
        rc_json, json_body, _err = run_cli(
            world, ["--check", "--root", world, "--json",
                    evidence_path(world)])
        parsed = json.loads(json_body)
        rows = dict((row["suite"], row) for row in parsed["suites"])
        ok = ("SUITE lobby cap=600.0s" in body
              and "SUITE heavy cap=900.0s" in body
              and "NO-MEASURE ghost cap=600.0s" in body
              and rows["ghost"]["status"] == RTH.NO_MEASURE
              and rows["ghost"]["cap"] == "600.0"
              and all("cap" in row for row in parsed["suites"]))
        if not ok:
            print("  measured: rc=%r body=%r ghost=%r"
                  % (rc, body, rows.get("ghost")), flush=True)
        check(ok, "AC-EDWU4 every row names the cap it was judged against")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_edwu5():
    """Every R2395 answer survives beside the new ones."""
    durations = {"lobby": [400.0], "heavy": [43.0], "ghost": [12.0]}
    labels = ["lobby", "heavy", "ghost", "absent"]
    report = RTH.assess(600.0, 0.6, labels, durations, {})
    parsed_keys = tuple(report.keys())
    ok = (parsed_keys == RTH.REPORT_KEYS
          and RTH.REPORT_KEYS == ("cap", "band_fraction", "verdict", "code",
                                  "suites", "band", "no_measure", "measured",
                                  "total")
          and report["verdict"] == RTH.BAND_HIT
          and report["band"] == ["lobby"]
          and report["no_measure"] == ["absent"]
          and report["measured"] == 3 and report["total"] == 4
          and RTH.CLEAN == "HEADROOM-CLEAN"
          and RTH.BAND_HIT == "BAND-HIT"
          and RTH.NO_MEASURE == "NO-MEASURE"
          and RTH.COMFORTABLE == "COMFORTABLE")
    if not ok:
        print("  measured: keys=%r report=%r"
              % (parsed_keys, report["verdict"]), flush=True)
    check(ok, "AC-EDWU5 every R2395 answer survives beside the new ones")


def ac_edwu6():
    """Pure ASCII, stdlib only, read-only, clock-free, wired with its label."""
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
    own = io.open(os.path.join(BASE, "test_runner_suite_timeout_headroom_"
                                     "overrides.py"), "r",
                  encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_runner_suite_timeout_headroom_overrides.py" in runner)
    pinned_label = (source.count('SUITE_LABEL = "os-runner-suite-timeout-'
                                 'headroom"') == 1
                    and own.count('LABEL = "%s"' % LABEL) == 1)
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_write
          and no_mutate and wired and pinned_label)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r write=%r "
              "mutate=%r wired=%r label=%r"
              % (ascii_only, no_net, no_clock, sorted(set(imports)),
                 no_write, no_mutate, wired, pinned_label), flush=True)
    check(ok, "AC-EDWU6 pure, read-only, and wired with its own label")


def main():
    print("runner_suite_timeout_headroom_overrides suite "
          "(expected criteria %d)" % EXPECTED_CRITERIA, flush=True)
    ac_edwu1()
    ac_edwu2()
    ac_edwu3()
    ac_edwu4()
    ac_edwu5()
    ac_edwu6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())