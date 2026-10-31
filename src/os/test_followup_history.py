"""followup_history suite (R2288; criteria AC-FHY1..AC-FHY6 were pre-registered
inside the R2272 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: the four post-battery sections have a readable history
instead of prose. Round order is the R number (never file mtime), a section a
round never reported reads ABSENT instead of vanishing, a log with no VERDICT
reads INCOMPLETE instead of green, and an unreadable pile fails closed with
zero fabricated rounds. The section vocabulary is imported from battery_followup
and the suite proves that by patching the source list and watching the report
change.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
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
import followup_history as FH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "followup_history.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-followup-history"

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


def run_cli(root, args=None):
    cmd = [sys.executable, MODULE, "--history"] + list(args or [])
    cmd += ["--root", root]
    proc = subprocess.run(cmd, capture_output=True)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace")
            + proc.stderr.decode("utf-8", "replace"))


def body(sections, verdict="PASS", round_label="R100", runner="PASS"):
    """One evidence log body from (name, status) legs."""
    lines = ["RUNNER %s (2/2 suites green, reconcile controls 7/7, 1.0s)"
             % runner]
    for name, status in sections:
        lines.append("SECTION %s %s detail here" % (name, status))
    if verdict is not None:
        lines.append("VERDICT %s %s failing=none" % (round_label, verdict))
    return "\n".join(lines) + "\n"


def make_world(logs):
    """Temp root with a qa/ directory holding (r number, text) logs."""
    world = tempfile.mkdtemp(prefix="bigdomain-fhy-")
    qa = os.path.join(world, "qa")
    os.makedirs(qa)
    for name, text in logs:
        path = os.path.join(qa, name)
        if text is None:
            os.makedirs(path)
            continue
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return world


def tree_digest(world):
    parts = []
    for base, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            digest = os.path.getsize(path)
            with open(path, "rb") as handle:
                digest += sum(bytearray(handle.read()))
            parts.append((os.path.relpath(path, world), digest))
        for name in sorted(dirs):
            parts.append((os.path.relpath(os.path.join(base, name), world), -1))
    return tuple(parts)


ALL = (("matrix", "PASS"), ("fingerprint", "PASS"),
       ("profile", "PASS"), ("census", "PASS"))


def ac_fhy1():
    """AC-FHY1: vocabulary from battery_followup; missing reads ABSENT."""
    partial = make_world([("reconcile-all-R100.log",
                           body([("matrix", "PASS"), ("census", "PASS")]))])
    original = BF.SECTIONS
    try:
        report = FH.history(partial)
        names = [item["name"] for item in report["rounds"][0]["sections"]]
        absent = [item["name"] for item in report["rounds"][0]["sections"]
                  if item["status"] == "ABSENT"]
        reading = report["rounds"][0]["verdict"]

        BF.SECTIONS = ("matrix", "census")
        patched = FH.history(partial)
        patched_names = [item["name"]
                         for item in patched["rounds"][0]["sections"]]
        patched_verdict = patched["rounds"][0]["verdict"]
        ok = (names == list(original)
              and absent == ["fingerprint", "profile"]
              and reading == "INCOMPLETE"
              and patched_names == ["matrix", "census"]
              and patched_verdict == "PASS")
        if not ok:
            print("  measured: names=%r absent=%r reading=%r patched=%r/%r"
                  % (names, absent, reading, patched_names, patched_verdict),
                  flush=True)
        check(ok, "AC-FHY1 vocabulary imported, absent sections named")
    finally:
        BF.SECTIONS = original
        shutil.rmtree(partial, ignore_errors=True)


def ac_fhy2():
    """AC-FHY2: R-number order, never mtime; duplicate round refused."""
    world = make_world([
        ("reconcile-all-R2000.log", body(ALL, round_label="R2000")),
        ("reconcile-all-R1999.log", body(ALL, round_label="R1999")),
        ("reconcile-all-R2001.log", body(ALL, round_label="R2001")),
    ])
    dup = make_world([
        ("reconcile-all-R1500.log", body(ALL, round_label="R1500")),
        ("reconcile-all-R01500.log", body(ALL, round_label="R1500")),
    ])
    try:
        report = FH.history(world)
        order = [item["round"] for item in report["rounds"]]
        code = None
        try:
            FH.history(dup)
            code = "no-raise"
        except FH.FollowupHistoryError as exc:
            code = exc.code
        cli = run_cli(dup)[0]
        ok = (order == ["R1999", "R2000", "R2001"]
              and code == "E_FHY_DUP_ROUND" and cli == 3)
        if not ok:
            print("  measured: order=%r code=%r cli=%r"
                  % (order, code, cli), flush=True)
        check(ok, "AC-FHY2 ordered by round number, duplicate refused")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(dup, ignore_errors=True)


def ac_fhy3():
    """AC-FHY3: no VERDICT line reads INCOMPLETE, never green."""
    world = make_world([
        ("reconcile-all-R900.log", body(ALL, verdict=None)),
        ("reconcile-all-R901.log", body(ALL, round_label="R901")),
    ])
    try:
        report = FH.history(world)
        readings = [item["verdict"] for item in report["rounds"]]
        counts = report["counts"]
        code, text = run_cli(world)
        ok = (readings == ["INCOMPLETE", "PASS"]
              and counts["incomplete"] == 1 and counts["green"] == 1
              and report["verdict"] == "HISTORY-RED"
              and code == 2 and "INCOMPLETE" in text)
        if not ok:
            print("  measured: readings=%r counts=%r verdict=%r code=%r"
                  % (readings, counts, report["verdict"], code), flush=True)
        check(ok, "AC-FHY3 a verdict-less log reads INCOMPLETE, not green")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_fhy4():
    """AC-FHY4: writes nothing, no clock, unreadable/absent fails closed."""
    world = make_world([
        ("reconcile-all-R700.log", body(ALL, round_label="R700")),
        ("reconcile-all-R0710.log", None),
    ])
    absent = os.path.join(tempfile.mkdtemp(prefix="bigdomain-fhy-bare-"), "qa")
    empty = make_world([("notes.txt", "not evidence\n")])
    source = io.open(MODULE, "r", encoding="utf-8").read()
    try:
        before = tree_digest(world)
        codes = []
        for target in (world, empty, absent):
            try:
                FH.history(target)
                codes.append("no-raise")
            except FH.FollowupHistoryError as exc:
                codes.append(exc.code)
        after = tree_digest(world)
        cli = [run_cli(target)[0] for target in (world, empty, absent)]
        no_clock = ("import time" not in source and "datetime" not in source
                    and "time.time" not in source
                    and "stat(" not in source and "getmtime" not in source)
        ok = (codes == ["E_FHY_UNREADABLE", "E_FHY_NO_EVIDENCE",
                        "E_FHY_NO_EVIDENCE"]
              and cli == [3, 3, 3]
              and before == after and no_clock)
        if not ok:
            print("  measured: codes=%r cli=%r writes=%r clock=%r"
                  % (codes, cli, before == after, no_clock), flush=True)
        check(ok, "AC-FHY4 read-only, clockless, fails closed with no rounds")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(empty, ignore_errors=True)
        shutil.rmtree(os.path.dirname(absent), ignore_errors=True)


def ac_fhy5():
    """AC-FHY5: CLI 0/2/3/5 and a byte-stable --json over pinned keys."""
    green = make_world([("reconcile-all-R800.log", body(ALL, round_label="R800"))])
    red = make_world([("reconcile-all-R801.log",
                       body([("matrix", "PASS"), ("fingerprint", "FAIL"),
                             ("profile", "FAIL"), ("census", "PASS")],
                            verdict="FAIL", round_label="R801"))])
    try:
        before = tree_digest(green)
        code_green, _text = run_cli(green)
        first = run_cli(green, ["--json"])[1]
        second = run_cli(green, ["--json"])[1]
        after = tree_digest(green)
        code_red = run_cli(red)[0]
        code_bad = run_cli(green, ["--nope"])[0]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == FH.REPORT_KEYS
        round_pinned = tuple(parsed["rounds"][0].keys()) == FH.ROUND_KEYS
        section_pinned = (tuple(parsed["rounds"][0]["sections"][0].keys())
                          == FH.SECTION_KEYS)
        count_pinned = tuple(parsed["counts"].keys()) == FH.COUNT_KEYS
        ok = (code_green == 0 and code_red == 2 and code_bad == 5
              and first == second and before == after
              and pinned and round_pinned and section_pinned and count_pinned
              and parsed["verdict"] == "ALL-GREEN"
              and parsed["rounds"][0]["runner"] == "PASS")
        if not ok:
            print("  measured: green=%r red=%r bad=%r stable=%r writes=%r "
                  "pinned=%r/%r/%r/%r verdict=%r"
                  % (code_green, code_red, code_bad, first == second,
                     before == after, pinned, round_pinned, section_pinned,
                     count_pinned, parsed["verdict"]), flush=True)
        check(ok, "AC-FHY5 CLI 0/2/5, byte-stable json, zero writes")
    finally:
        shutil.rmtree(green, ignore_errors=True)
        shutil.rmtree(red, ignore_errors=True)


def ac_fhy6():
    """AC-FHY6: pure source, stdlib only, wired, FAIL then PASS visible."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    runner_text = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner_text) or ("'%s'" % LABEL in runner_text)
    world = make_world([("reconcile-all-R2287.log",
                         body(ALL, verdict="FAIL", round_label="R2287",
                              runner="PASS") + body(ALL,
                                                    round_label="R2287"))])
    try:
        report = FH.history(world)
        matrix = report["rounds"][0]["sections"][0]
        ok = (ascii_only and no_net and wired
              and matrix["name"] == "matrix"
              and matrix["runs"] == ["PASS", "PASS"]
              and matrix["status"] == "PASS"
              and report["rounds"][0]["verdict"] == "PASS"
              and report["verdict"] == "ALL-GREEN")
        red_world = make_world([("reconcile-all-R1600.log",
                                 body([("matrix", "FAIL"),
                                       ("fingerprint", "PASS"),
                                       ("profile", "PASS"),
                                       ("census", "PASS")],
                                      verdict="FAIL", round_label="R1600")
                                 + body(ALL, round_label="R1600"))])
        try:
            seen = FH.history(red_world)
            legs = seen["rounds"][0]["sections"][0]["runs"]
            ok = ok and legs == ["FAIL", "PASS"]
            if not ok:
                print("  measured: ascii=%r net=%r wired=%r matrix=%r legs=%r"
                      % (ascii_only, no_net, wired, matrix, legs), flush=True)
        finally:
            shutil.rmtree(red_world, ignore_errors=True)
        check(ok, "AC-FHY6 pure, wired, a FAIL then PASS is a visible run")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("followup_history suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_fhy1()
    ac_fhy2()
    ac_fhy3()
    ac_fhy4()
    ac_fhy5()
    ac_fhy6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())