"""runner_abort_history suite (R2417; criteria AC-RAH1..AC-RAH6 were
pre-registered inside the R2403 seed row of state/queue/tech.md line 484
BEFORE this code existed).

What this proves: an aborted battery body is aged against its own round's
retry family - a green leg of the same round makes it SUPERSEDED and names
both files, no green leg makes it LIVE-ABORT at exit 2, and a name carrying
no canonical round token reads ORPHAN-ABORT instead of being folded into
another round's family. Both the abort verdict and the family are the shipped
laws asked at CALL time: patching either one moves this reading. The CLI keeps
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

import retry_naming as RN  # noqa: E402
import round_evidence as RQE  # noqa: E402
import runner_abort_face as RAF  # noqa: E402
import runner_abort_history as RAH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "runner_abort_history.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-runner-abort-history"

FAKE_RUNNER = (
    "SUITES = [\n"
    "    ('lobby', 'lobby/test_x.py', 79),\n"
    "    ('ledger', 'ledger/test_y.py', 11),\n"
    "]\n")

PASS_TAIL = "RUNNER PASS (2/2 suites green, reconcile controls 7/7, 900.0s)"

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


def green_body():
    return [suite_line("lobby", 79.0), suite_line("ledger", 11.0), PASS_TAIL]


def aborted_body():
    return [suite_line("lobby", 79.0)]


def make_world(bodies, runner=FAKE_RUNNER):
    """bodies: {file name: list of lines}. Returns the world root."""
    world = tempfile.mkdtemp(prefix="bigdomain-rah-")
    qa = os.path.join(world, "qa")
    sandbox = os.path.join(world, "src", "sandbox")
    os.makedirs(qa)
    os.makedirs(sandbox)
    for name in sorted(bodies):
        path = os.path.join(qa, name)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(bodies[name]) + "\n")
    with io.open(os.path.join(sandbox, "reconcile_all.py"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(runner)
    return world


def pair_world(family="reconcile-all-R2400"):
    """One aborted retry leg beside a green first leg of the same round."""
    return make_world({
        family + ".log": green_body(),
        family + "-retry.log": aborted_body(),
    })


def aborted_only_world(family="reconcile-all-R2401"):
    return make_world({family + ".log": aborted_body()})


def run_cli(world, args):
    proc = subprocess.Popen(
        [sys.executable, MODULE] + args,
        cwd=world, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace")


def evidence(world, name):
    return os.path.join(world, "qa", name)


def runner_of(world):
    return os.path.join(world, "src", "sandbox", "reconcile_all.py")


def ac_rah1():
    """Both laws are asked at CALL time: patching either one moves the row."""
    world = pair_world("reconcile-all-R2400")
    try:
        path = evidence(world, "reconcile-all-R2400-retry.log")
        runt = runner_of(world)
        plain = RAH.history(path, runt)
        moved_family = None
        moved_verdict = None
        original_stem = RN.base_stem
        original_analyse = RAF.analyse
        try:
            RN.base_stem = lambda name: name
            moved_family = RAH.history(path, runt)

            def blinded(text, labels):
                row = original_analyse(text, labels)
                row["verdict"] = RAF.ABORTED
                row["verdict_line"] = "-"
                return row
            RAF.analyse = blinded
            moved_verdict = RAH.history(path, runt)
        finally:
            RN.base_stem = original_stem
            RAF.analyse = original_analyse
        recovered = RAH.history(path, runt)
        ok = (plain["verdict"] == RAH.SUPERSEDED
              and plain["family"] == ["reconcile-all-R2400.log"]
              and moved_family["verdict"] == RAH.LIVE_ABORT
              and moved_family["family"] == []
              and moved_family["family_code"] == "OUT-OF-SCOPE"
              and moved_verdict["verdict"] == RAH.LIVE_ABORT
              and moved_verdict["green_leg"] == "-"
              and recovered["verdict"] == RAH.SUPERSEDED)
        if not ok:
            print("  measured: plain=%r family_moved=%r verdict_moved=%r "
                  "recovered=%r"
                  % (plain["verdict"], moved_family, moved_verdict["verdict"],
                     recovered["verdict"]), flush=True)
        check(ok, "AC-RAH1 abort verdict and retry family come from the "
                  "shipped laws at call time")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rah2():
    """A green leg of the same round makes the abort SUPERSEDED, both named."""
    world = pair_world("reconcile-all-R2402")
    try:
        name = "reconcile-all-R2402-retry.log"
        path = evidence(world, name)
        row = RAH.history(path, runner_of(world))
        code, out = run_cli(world, ["--check", path])
        text = RAH.render(row)
        ok = (row["verdict"] == RAH.SUPERSEDED
              and row["code"] == 0
              and row["green_leg"] == "reconcile-all-R2402.log"
              and name in text
              and "reconcile-all-R2402.log" in text
              and row["round"] == 2402
              and row["leg_index"] == 1
              and code == 0)
        if not ok:
            print("  measured: row=%r code=%r text=%r"
                  % (row, code, text), flush=True)
        check(ok, "AC-RAH2 an aborted leg with a green leg reads SUPERSEDED "
                  "naming both files")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rah3():
    """No green leg for the round: LIVE-ABORT at exit 2."""
    world = aborted_only_world("reconcile-all-R2403")
    try:
        path = evidence(world, "reconcile-all-R2403.log")
        row = RAH.history(path, runner_of(world))
        code, _out = run_cli(world, ["--check", path])
        ok = (row["verdict"] == RAH.LIVE_ABORT
              and row["code"] == 2
              and code == 2
              and row["green_leg"] == "-"
              and row["family"] == []
              and row["leg_index"] == 0
              and row["family_code"] == "-")
        if not ok:
            print("  measured: row=%r code=%r" % (row, code), flush=True)
        check(ok, "AC-RAH3 an aborted leg with no green leg reads LIVE-ABORT "
                  "at exit 2")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rah4():
    """A name with no canonical round token reads ORPHAN-ABORT."""
    world = make_world({"reconcile-daily-fix.log": aborted_body(),
                        "reconcile-all-R2404-firstfail.log": aborted_body()})
    try:
        path = evidence(world, "reconcile-daily-fix.log")
        row = RAH.history(path, runner_of(world))
        code, _out = run_cli(world, ["--check", path])
        out_of_scope = RAH.history(
            evidence(world, "reconcile-all-R2404-firstfail.log"),
            runner_of(world))
        ok = (row["verdict"] == RAH.ORPHAN_ABORT
              and row["code"] == 3
              and code == 3
              and row["round"] is None
              and out_of_scope["verdict"] == RAH.LIVE_ABORT
              and out_of_scope["family"] == []
              and out_of_scope["family_code"] == "OUT-OF-SCOPE")
        if not ok:
            print("  measured: row=%r code=%r out_of_scope=%r"
                  % (row, code, out_of_scope), flush=True)
        check(ok, "AC-RAH4 an aborted body with no round token reads "
                  "ORPHAN-ABORT and a name outside the family scope is not "
                  "folded into a round")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rah5():
    """CLI exits 0/2/3/5 and --json is byte-stable over the pinned keys."""
    world = make_world({
        "reconcile-all-R2405.log": green_body(),
        "reconcile-all-R2405-retry.log": aborted_body(),
        "reconcile-all-R2406.log": aborted_body(),
    })
    try:
        superseded = evidence(world, "reconcile-all-R2405-retry.log")
        live = evidence(world, "reconcile-all-R2406.log")
        orphan_world = make_world({"ctl-fix.log": aborted_body()})
        orphan = evidence(orphan_world, "ctl-fix.log")
        first = run_cli(world, ["--check", "--json", superseded])
        second = run_cli(world, ["--check", "--json", superseded])
        codes = (run_cli(world, ["--check", superseded])[0],
                 run_cli(world, ["--check", live])[0],
                 run_cli(orphan_world, ["--check", orphan])[0],
                 run_cli(world, [])[0],
                 run_cli(world, ["--check", "--nosuch", superseded])[0],
                 run_cli(world, ["--check", os.path.join(
                     world, "qa", "missing.log")])[0])
        try:
            payload = json.loads(first[1])
        except ValueError:
            payload = {}
        ok = (first[0] == 0 and second[0] == 0
              and first[1] == second[1]
              and list(payload.keys()) == list(RAH.REPORT_KEYS)
              and codes == (0, 2, 3, 5, 5, 3))
        if not ok:
            print("  measured: first=%r second=%r keys=%r codes=%r"
                  % (first, second, sorted(payload.keys()), codes), flush=True)
        check(ok, "AC-RAH5 CLI exits 0/2/3/5 with a byte-stable --json")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(orphan_world, ignore_errors=True)


def ac_rah6():
    """Pure ASCII, stdlib only, no clock, no network, read-only, wired."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(ch) < 128 for ch in source)
    imports = set(re.findall(r"^\s*import (\w+)", source, re.M))
    stdlib_only = imports <= {"json", "os", "sys"}
    no_net = not re.search(
        r"\b(?:urllib|http|socket|requests|ssl|ftplib|smtplib)\b", source)
    no_clock = not re.search(
        r"\b(?:datetime|time\.time|time\.monotonic|strftime)\b", source)
    no_write = not re.search(
        r"open\([^)]*[\"'](?:w|a|x|r\+|w\+|a\+)[\"']", source)
    no_mutate = not re.search(
        r"\b(?:os\.remove|os\.replace|os\.rename|os\.mkdir|makedirs)\b",
        source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner
             and "test_runner_abort_history.py" in runner)
    own_label = source.count('SUITE_LABEL = "%s"' % LABEL) == 1
    laws = (source.count('"runner_abort_face"') == 1
            and source.count('"retry_naming"') == 1
            and source.count('"round_evidence"') == 1
            and source.count('"followup_retry_legs"') == 1
            and source.count('"followup_history"') == 1)
    ok = (ascii_only and stdlib_only and no_net and no_clock and no_write
          and no_mutate and wired and own_label and laws)
    if not ok:
        print("  measured: ascii=%r imports=%r net=%r clock=%r write=%r "
              "mutate=%r wired=%r label=%r laws=%r"
              % (ascii_only, sorted(imports), no_net, no_clock, no_write,
                 no_mutate, wired, own_label, laws), flush=True)
    check(ok, "AC-RAH6 pure, read-only, and wired with its own label")


def main():
    print("runner_abort_history suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rah1()
    ac_rah2()
    ac_rah3()
    ac_rah4()
    ac_rah5()
    ac_rah6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())