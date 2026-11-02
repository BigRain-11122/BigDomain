"""runner_abort_face suite (R2403; criteria AC-RAF1..AC-RAF6 were
pre-registered inside the R2395 seed row of state/queue/tech.md line 474
BEFORE this code existed).

What this proves: a battery body that carries suite lines but no verdict line
reads ABORTED and NAMES the suite that was running - the first suite the
runner registers that has no suite line in the body, derived from the registry
and the body only, never a hard-coded label - while a body that carries the
runner's own verdict line reads COMPLETE with no abort reading at all, a body
with neither reads UNREADABLE instead of inventing an abort, and the CLI keeps
0/2/3/5 with a byte-stable --json over pinned keys.

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

import runner_abort_face as RAF  # noqa: E402
import runner_suite_timeout_headroom as RTH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "runner_abort_face.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-runner-abort-face"

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


def suite_line(label, seconds):
    return ("PASS suite %s exit=0 pass-lines=3 fail-lines=0 criteria=3 %.1fs"
            % (label, seconds))


COMPLETE_TAIL = "RUNNER PASS (3/3 suites green, reconcile controls 7/7, 900.0s)"


def make_world(body, runner=FAKE_RUNNER):
    world = tempfile.mkdtemp(prefix="bigdomain-raf-")
    qa = os.path.join(world, "qa")
    sandbox = os.path.join(world, "src", "sandbox")
    os.makedirs(qa)
    os.makedirs(sandbox)
    with io.open(os.path.join(qa, "reconcile-all-fixture.log"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(body) + "\n")
    with io.open(os.path.join(sandbox, "reconcile_all.py"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(runner)
    return world


def run_cli(world, args):
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "runner_abort_face.py")] + args,
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


def ac_raf1():
    """The aborted suite is registry minus body suite lines; a patch moves it."""
    body = [suite_line("lobby", 43.0),
            "  | PASS AC-S1: an echoed child line is not a suite line"]
    labels = ["lobby", "ledger", "heavy"]
    straight = RAF.analyse("\n".join(body), labels)
    with Patched(RTH, "registry_labels", lambda path: ["alpha", "beta"]):
        moved = RAF.analyse("\n".join(body),
                            RAF.registry_labels("ignored"))
    with Patched(RTH, "parse_evidence_line", lambda line: None):
        blind = RAF.analyse("\n".join(body), labels)
    ok = (straight["verdict"] == RAF.ABORTED
          and straight["suite"] == "ledger"
          and straight["missing"] == ["ledger", "heavy"]
          and straight["seen"] == 1
          and straight["registered"] == 3
          and moved["suite"] == "alpha"
          and moved["missing"] == ["alpha", "beta"]
          and blind["verdict"] == RAF.UNREADABLE)
    if not ok:
        print("  measured: straight=%r moved=%r blind=%r"
              % (straight, moved, blind["verdict"]), flush=True)
    check(ok, "AC-RAF1 aborted suite = registry minus body suite lines")


def ac_raf2():
    """A body carrying the runner's own verdict writes no abort reading."""
    world = make_world([suite_line("lobby", 43.0), suite_line("ledger", 0.4),
                        suite_line("heavy", 12.0), COMPLETE_TAIL])
    try:
        rc, body, _err = run_cli(
            world, ["--check", "--root", world,
                    os.path.join(world, "qa", "reconcile-all-fixture.log")])
        rc_json, json_body, _err = run_cli(
            world, ["--check", "--root", world, "--json",
                    os.path.join(world, "qa", "reconcile-all-fixture.log")])
        parsed = json.loads(json_body)
        ok = (rc == 0 and rc_json == 0
              and parsed["verdict"] == "COMPLETE"
              and parsed["suite"] == "-" and parsed["missing"] == []
              and parsed["seen"] == 3 and parsed["registered"] == 3
              and "abort=none" in body
              and "SUITE " not in body)
        if not ok:
            print("  measured: rc=%r parsed=%r body=%r"
                  % (rc, parsed, body), flush=True)
        check(ok, "AC-RAF2 a complete body writes no abort reading")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_raf3():
    """ABORTED names the suite at exit 2; the same registry reads COMPLETE."""
    aborted = make_world([suite_line("lobby", 43.0),
                          suite_line("ledger", 0.4),
                          "  | FAIL AC-X1: still streaming when the cap hit",
                          "  | child output line inside ledger/test_y.py"])
    complete = make_world([suite_line("lobby", 43.0),
                           suite_line("ledger", 0.4),
                           suite_line("heavy", 12.0), COMPLETE_TAIL])
    try:
        rc_abort, body_abort, _err = run_cli(
            aborted, ["--check", "--root", aborted,
                      os.path.join(aborted, "qa", "reconcile-all-fixture.log")])
        rc_ok, body_ok, _err = run_cli(
            complete, ["--check", "--root", complete,
                       os.path.join(complete, "qa", "reconcile-all-fixture.log")])
        ok = (rc_abort == 2
              and "BATTERY ABORT VERDICT ABORTED" in body_abort
              and "SUITE heavy (first registered suite with no suite line)"
              in body_abort
              and "LAST | child output line inside ledger/test_y.py"
              in body_abort
              and "MISSING heavy" in body_abort
              and rc_ok == 0 and "VERDICT COMPLETE" in body_ok
              and "VERDICT-LINE RUNNER PASS" in body_ok)
        if not ok:
            print("  measured: abort=%r/%r ok=%r/%r"
                  % (rc_abort, body_abort, rc_ok, body_ok), flush=True)
        check(ok, "AC-RAF3 ABORTED names the suite, COMPLETE exits 0")
    finally:
        shutil.rmtree(aborted, ignore_errors=True)
        shutil.rmtree(complete, ignore_errors=True)


def ac_raf4():
    """A body with neither a verdict line nor a suite line is UNREADABLE."""
    world = make_world(["", "  | some child chatter with no suite line",
                        "Traceback (most recent call last):",
                        "KeyboardInterrupt"])
    try:
        rc, body, _err = run_cli(
            world, ["--check", "--root", world,
                    os.path.join(world, "qa", "reconcile-all-fixture.log")])
        rc_json, json_body, _err = run_cli(
            world, ["--check", "--root", world, "--json",
                    os.path.join(world, "qa", "reconcile-all-fixture.log")])
        parsed = json.loads(json_body)
        ok = (rc == 3 and rc_json == 3
              and parsed["verdict"] == "UNREADABLE"
              and parsed["suite"] == "-" and parsed["seen"] == 0
              and parsed["last_line"] == "KeyboardInterrupt"
              and "no suite line and no verdict line" in body)
        empty = make_world([""])
        try:
            rc_empty, _b, _err = run_cli(
                empty, ["--check", "--root", empty,
                        os.path.join(empty, "qa",
                                     "reconcile-all-fixture.log")])
            ok = ok and rc_empty == 3
        finally:
            shutil.rmtree(empty, ignore_errors=True)
        if not ok:
            print("  measured: rc=%r parsed=%r body=%r"
                  % (rc, parsed, body), flush=True)
        check(ok, "AC-RAF4 an unparseable body reads UNREADABLE")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_raf5():
    """Exits 0/2/3/5 with a byte-stable --json over the pinned keys."""
    ok_world = make_world([suite_line("lobby", 43.0),
                           suite_line("ledger", 0.4),
                           suite_line("heavy", 12.0), COMPLETE_TAIL])
    abort_world = make_world([suite_line("lobby", 43.0)])
    unreadable = make_world(["nothing here at all"])
    broken = make_world([suite_line("lobby", 43.0)],
                        runner="SUITES = [ not literal ]\n")
    try:
        rc_zero, _b, _e = run_cli(ok_world, ["--check", "--root", ok_world,
                                             os.path.join(
                                                 ok_world, "qa",
                                                 "reconcile-all-fixture.log")])
        rc_two, _b, _e = run_cli(abort_world, ["--check", "--root",
                                               abort_world,
                                               os.path.join(
                                                   abort_world, "qa",
                                                   "reconcile-all-fixture.log")])
        rc_three, _b, _e = run_cli(ok_world, ["--check", "--root", ok_world,
                                              "--runner", os.path.join(
                                                  ok_world, "src", "sandbox",
                                                  "missing.py"),
                                              os.path.join(
                                                  ok_world, "qa",
                                                  "reconcile-all-fixture.log")])
        rc_five_a, _b, _e = run_cli(ok_world, ["--check", "--nope",
                                               os.path.join(
                                                   ok_world, "qa",
                                                   "reconcile-all-fixture.log")])
        rc_five_b, _b, _e = run_cli(ok_world, [])
        rc_five_c, _b, _e = run_cli(abort_world, ["--check", "--root",
                                                  abort_world])
        rc_unreadable, _b, _e = run_cli(unreadable, [
            "--check", "--root", unreadable,
            os.path.join(unreadable, "qa", "reconcile-all-fixture.log")])
        rc_broken, _b, _e = run_cli(broken, ["--check", "--root", broken,
                                             os.path.join(
                                                 broken, "qa",
                                                 "reconcile-all-fixture.log")])
        rc_a, body_a, _e = run_cli(abort_world, ["--check", "--root",
                                                 abort_world, "--json",
                                                 os.path.join(
                                                     abort_world, "qa",
                                                     "reconcile-all-fixture.log")])
        rc_b, body_b, _e = run_cli(abort_world, ["--check", "--root",
                                                 abort_world, "--json",
                                                 os.path.join(
                                                     abort_world, "qa",
                                                     "reconcile-all-fixture.log")])
        parsed = json.loads(body_a)
        ok = (rc_zero == 0 and rc_two == 2 and rc_three == 3
              and rc_five_a == 5 and rc_five_b == 5 and rc_five_c == 5
              and rc_unreadable == 3 and rc_broken == 3
              and rc_a == 2 and body_a == body_b
              and tuple(parsed.keys()) == RAF.REPORT_KEYS)
        if not ok:
            print("  measured: rcs=%r stable=%r keys=%r"
                  % ((rc_zero, rc_two, rc_three, rc_five_a, rc_five_b,
                      rc_five_c, rc_unreadable, rc_broken), body_a == body_b,
                     tuple(parsed.keys())), flush=True)
        check(ok, "AC-RAF5 exits 0/2/3/5 and --json is byte-stable")
    finally:
        for world in (ok_world, abort_world, unreadable, broken):
            shutil.rmtree(world, ignore_errors=True)


def ac_raf6():
    """Pure ASCII, stdlib only, read-only, wired with its own label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not re.search(r"\b(?:socket|urllib|http)\b", source)
    no_clock = not re.search(
        r"\b(?:import time|import datetime|time\.time)\b", source)
    imports = re.findall(r"^\s*import (\w+)", source, re.MULTILINE)
    stdlib_only = sorted(set(imports)) == ["io", "json", "os", "re",
                                           "runner_suite_timeout_headroom",
                                           "sys"]
    no_write = not re.search(
        r"open\([^)]*[\"'](?:w|a|x|r\+|w\+|a\+)[\"']", source)
    no_mutate = not re.search(
        r"\b(?:os\.remove|os\.replace|os\.rename|os\.mkdir|makedirs|"
        r"tempfile)\b", source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_runner_abort_face.py" in runner)
    own_label = source.count('SUITE_LABEL = "%s"' % LABEL) == 1
    ok = (ascii_only and no_net and no_clock and stdlib_only and no_write
          and no_mutate and wired and own_label)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r imports=%r write=%r "
              "mutate=%r wired=%r label=%r"
              % (ascii_only, no_net, no_clock, sorted(set(imports)),
                 no_write, no_mutate, wired, own_label), flush=True)
    check(ok, "AC-RAF6 pure, read-only, and wired with its own label")


def main():
    print("runner_abort_face suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_raf1()
    ac_raf2()
    ac_raf3()
    ac_raf4()
    ac_raf5()
    ac_raf6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())