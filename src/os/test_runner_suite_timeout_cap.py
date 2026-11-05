"""runner_suite_timeout_cap suite (R2479; criteria AC-RSC1..AC-RSC6 were
pinned inside the R2478 seed row of state/queue/tech.md BEFORE this code).

What this proves: the battery's per-suite cap is ONE declared number that the
headroom instrument READS from the runner source, a declared per-suite
override is honoured while every undeclared suite keeps the global cap, the
deployed AC-RTH reading does not regress, the three measured slow suites read
COMFORTABLE at the repaired cap while a genuine outlier still reads BAND, a
timeout is still recorded as one failed suite and never aborts the run, and
the shipped module is pure, read-only and wired.

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

import runner_suite_timeout_cap as RSC  # noqa: E402
import runner_suite_timeout_headroom as RTH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "runner_suite_timeout_cap.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
RTH_SUITE = os.path.join(BASE, "test_runner_suite_timeout_headroom.py")
LABEL = "os-runner-suite-timeout-cap"
FIXTURE_EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2478-leg2.log")
SLOW_THREE = ("ledger-apimarket-buyerhistory",
              "ledger-apimarket-refundregister",
              "ledger-apimarket-reportclaims")

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


def make_runner_world(declaration):
    """A throwaway runner source carrying (or lacking) the cap declaration."""
    world = tempfile.mkdtemp(prefix="bigdomain-rsc-")
    path = os.path.join(world, "reconcile_all.py")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("SUITES = []\n%s" % declaration)
    return world, path


def run_cli(args, cwd=None):
    proc = subprocess.Popen(
        [sys.executable, MODULE] + args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd or REPO)
    out, err = proc.communicate()
    return (proc.returncode, out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"))


def ac_rsc1():
    """One declared constant, read from the source, never a second literal."""
    declared_world, declared = make_runner_world("SUITE_TIMEOUT_S = 742\n")
    plain_world, plain = make_runner_world("")
    try:
        read_declared = RSC.read_cap(declared)
        read_plain = RSC.read_cap(plain)
        real = RSC.read_cap(RUNNER)
        text = io.open(RUNNER, "r", encoding="utf-8").read()
        declarations = len(re.findall(
            r"(?m)^SUITE_TIMEOUT_S\s*=\s*[0-9.]+\s*$", text))
        hardcoded = len(re.findall(r"timeout=300\b", text))
        ok = (read_declared[0] == 742.0
              and read_declared[1] == RSC.DECLARED
              and read_declared[2] == 1
              and read_plain[0] == RSC.FALLBACK_CAP
              and read_plain[1] == RSC.FALLBACK
              and read_plain[2] == 0
              and real[1] == RSC.DECLARED and real[2] == 1
              and real[0] > 0
              and declarations == 1
              and hardcoded == 0)
        if not ok:
            print("  measured: declared=%r plain=%r real=%r decls=%d "
                  "hardcoded300=%d"
                  % (read_declared, read_plain, real, declarations,
                     hardcoded), flush=True)
        check(ok, "AC-RSC1 cap is one declared constant read from the source")
    finally:
        shutil.rmtree(declared_world, ignore_errors=True)
        shutil.rmtree(plain_world, ignore_errors=True)


def ac_rsc2():
    """A declared override is honoured; undeclared suites keep the cap."""
    sys.path.insert(0, os.path.join(SRC, "sandbox"))
    import reconcile_all as RA  # noqa: E402 - the runner under test

    saved_cap = RA.SUITE_TIMEOUT_S
    saved_over = dict(RA.SUITE_TIMEOUT_OVERRIDES)
    world = tempfile.mkdtemp(prefix="bigdomain-rsc-sleep-")
    slow = os.path.join(world, "slow.py")
    fast = os.path.join(world, "fast.py")
    try:
        with io.open(slow, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("import time\ntime.sleep(5)\nprint('done')\n")
        with io.open(fast, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("print('done')\n")
        RA.SUITE_TIMEOUT_S = 30
        RA.SUITE_TIMEOUT_OVERRIDES = {"slow-fixture": 1}
        code_slow, out_slow = RA.run_cmd(
            [sys.executable, slow], cwd=world,
            timeout=RA.suite_timeout("slow-fixture"))
        code_fast, _out_fast = RA.run_cmd(
            [sys.executable, fast], cwd=world,
            timeout=RA.suite_timeout("fast-fixture"))
        helper_ok = (RA.suite_timeout("slow-fixture") == 1
                     and RA.suite_timeout("undeclared") == 30)
        ok = (code_slow == 124
              and "TIMEOUT suite exceeded the 1s per-suite cap" in out_slow
              and code_fast == 0
              and helper_ok)
        if not ok:
            print("  measured: slow=(%r,%r) fast=%r helper=%r"
                  % (code_slow, out_slow, code_fast, helper_ok), flush=True)
        check(ok, "AC-RSC2 declared override honoured, others keep the cap")
    finally:
        RA.SUITE_TIMEOUT_S = saved_cap
        RA.SUITE_TIMEOUT_OVERRIDES = saved_over
        shutil.rmtree(world, ignore_errors=True)


def ac_rsc3():
    """The deployed AC-RTH reading does not regress, unchanged."""
    proc = subprocess.Popen([sys.executable, RTH_SUITE],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    body = (out or b"").decode("utf-8", "replace")
    tail = (err or b"").decode("utf-8", "replace")
    ok = (proc.returncode == 0 and "SUITE PASS 6/6" in body
          and "FAIL " not in body)
    if not ok:
        print("  measured: rc=%r tail=%r" % (proc.returncode,
                                             (body + tail)[-400:]),
              flush=True)
    check(ok, "AC-RSC3 AC-RTH1..AC-RTH6 stay green unchanged")


def ac_rsc4():
    """Slow three read COMFORTABLE at the repaired cap; an outlier still BAND."""
    cap = RSC.default_cap(RUNNER)
    durations, _lines = RTH.read_evidence([FIXTURE_EVIDENCE])
    labels = RTH.registry_labels(RUNNER)
    report = RTH.assess(cap, RTH.BAND_DEFAULT, labels, durations)
    rows = dict((row["suite"], row) for row in report["suites"])
    slow_ok = all(name in durations for name in SLOW_THREE)
    statuses = dict((name, rows[name]["status"]) for name in SLOW_THREE
                    if name in rows)
    slow_comfortable = (slow_ok
                        and all(status == RTH.COMFORTABLE
                                for status in statuses.values()))
    outlier = RTH.assess(100.0, RTH.BAND_DEFAULT, ["hot"], {"hot": [95.0]})
    band_still_names = (outlier["band"] == ["hot"]
                        and outlier["verdict"] == RTH.BAND_HIT)
    ok = slow_comfortable and band_still_names and cap > 300.0
    if not ok:
        print("  measured: cap=%r statuses=%r outlier=%r"
              % (cap, statuses, outlier["verdict"]), flush=True)
    check(ok, "AC-RSC4 slow three COMFORTABLE, a real outlier still BAND")


def ac_rsc5():
    """The cap that ran is readable, and a timeout never aborts the run."""
    sys.path.insert(0, os.path.join(SRC, "sandbox"))
    import reconcile_all as RA  # noqa: E402
    text = io.open(RUNNER, "r", encoding="utf-8").read()
    states = "suite cap=%ds" in text
    world = tempfile.mkdtemp(prefix="bigdomain-rsc-cap-")
    slow = os.path.join(world, "slow.py")
    saved_cap = RA.SUITE_TIMEOUT_S
    saved_suites = list(RA.SUITES)
    try:
        with io.open(slow, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("import time\ntime.sleep(5)\n")
        RA.SUITE_TIMEOUT_S = 1
        RA.SUITE_TIMEOUT_OVERRIDES = {}
        RA.SUITES = [("cap-fixture", os.path.relpath(slow, RA.BASE), 3)]
        # Swallow the fixture battery's own lines: they are proof, not this
        # suite's verdicts, and a bare FAIL line in a green suite's output
        # would show up as fail-lines in the battery evidence.
        saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            ran = RA.phase_suites()
            captured = sys.stdout.getvalue()
        finally:
            sys.stdout = saved_stdout
        one_fail_named = captured.count("FAIL suite cap-fixture") == 1
        cap_named = "suite cap=1s" in captured
        ok = (states is True and ran is False and one_fail_named
              and cap_named)
        if not ok:
            print("  measured: summary_states_cap=%r ran=%r one_fail=%r "
                  "cap_named=%r" % (states, ran, one_fail_named, cap_named),
                  flush=True)
        check(ok, "AC-RSC5 cap readable and a timeout never aborts the run")
    finally:
        RA.SUITE_TIMEOUT_S = saved_cap
        RA.SUITES = saved_suites
        shutil.rmtree(world, ignore_errors=True)


def ac_rsc6():
    """Pure ASCII stdlib, read-only, one new row, neighbours green."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(
        r"\b(?:import time|import datetime|time\.time)\b", source)
    imports = re.findall(r"^\s*import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["json", "os", "re", "sys"]
    no_write = not re.search(
        r"open\([^)]*[\"'](?:w|a|x|r\+|w\+|a\+)[\"']", source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_runner_suite_timeout_cap.py" in runner)
    rows = len(re.findall(re.escape(LABEL), runner))
    rc, body, _err = run_cli(["--check"])
    declared_cli = (rc == 0 and "VERDICT CAP-DECLARED" in body
                    and "CAP " in body)
    rc_json, json_body, _err = run_cli(["--check", "--json"])
    parsed = json.loads(json_body) if rc_json in (0, 2) else {}
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_write
          and wired and rows == 1 and declared_cli
          and parsed.get("source") == RSC.DECLARED
          and parsed.get("occurrences") == 1)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r write=%r "
              "wired=%r rows=%d cli=%r parsed=%r"
              % (ascii_only, no_net, no_clock, sorted(set(imports)),
                 no_write, wired, rows, (rc, body.strip()),
                 parsed.get("source")), flush=True)
    check(ok, "AC-RSC6 pure, read-only, one row, own CLI declares the cap")


def main():
    print("runner_suite_timeout_cap suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rsc1()
    ac_rsc2()
    ac_rsc3()
    ac_rsc4()
    ac_rsc5()
    ac_rsc6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())