"""followup_section_foreign suite (R2357; criteria AC-FSF1..AC-FSF6 were
pre-registered inside the R2343 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: a SECTION line under a name the ritual does not own is now
named instead of parsed and forgotten. The vocabulary and the parse are
followup_history's (proved by patching them and watching the report move),
every round lands in exactly one reading, the reading comes from the log alone
(no clock, no round threshold), an unreadable pile fails closed, the CLI is
stable and writes nothing, and the source is pure and wired.

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

import followup_history as FH  # noqa: E402
import followup_section_foreign as FSF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "followup_section_foreign.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-followup-section-foreign"

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
    cmd = [sys.executable, MODULE, "--check"] + list(args or [])
    cmd += ["--root", root]
    proc = subprocess.run(cmd, capture_output=True)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace")
            + proc.stderr.decode("utf-8", "replace"))


def body(sections, verdict="PASS", round_label="R100"):
    """One evidence log body from (name, status) legs."""
    lines = ["RUNNER %s (2/2 suites green, reconcile controls 7/7, 1.0s)"
             % verdict]
    for name, status in sections:
        lines.append("SECTION %s %s detail here" % (name, status))
    if verdict is not None:
        lines.append("VERDICT %s %s failing=none" % (round_label, verdict))
    return "\n".join(lines) + "\n"


def make_world(logs):
    """Temp root with a qa/ directory holding (name, text) logs."""
    world = tempfile.mkdtemp(prefix="bigdomain-fsf-")
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
            parts.append((os.path.relpath(os.path.join(base, name), world),
                          -1))
    return tuple(parts)


ALL = (("matrix", "PASS"), ("fingerprint", "PASS"),
       ("profile", "PASS"), ("census", "PASS"))


def ac_fsf1():
    """AC-FSF1: vocabulary and parse are followup_history's at call time."""
    world = make_world([("reconcile-all-R100.log", body(ALL))])
    original_vocab = FH.vocabulary
    original_parse = FH.parse
    try:
        reported = FSF.reading(world)["vocabulary"]
        owned = list(FH.vocabulary())

        FH.vocabulary = lambda: ("matrix", "census")
        patched = FSF.reading(world)
        patched_names = patched["vocabulary"]
        patched_reading = patched["rounds"][0]["reading"]

        def widening(text):
            runs, verdict, runner = original_parse(text)
            runs.setdefault("timing", []).append("PASS")
            return runs, verdict, runner

        FH.vocabulary = original_vocab
        FH.parse = widening
        seen = FSF.reading(world)
        consequence = (seen["rounds"][0]["foreign"] == ["timing"]
                       and seen["verdict"] == FSF.VERDICT_FOREIGN)
        # A narrowed vocabulary makes the two names it no longer owns foreign,
        # which is the flow-through itself rather than a defect.
        narrowed = (patched["rounds"][0]["foreign"] == ["fingerprint",
                                                        "profile"]
                    and patched_reading == FSF.READING_FOREIGN)
        ok = (reported == owned
              and patched_names == ["matrix", "census"]
              and narrowed
              and consequence)
        if not ok:
            print("  measured: reported=%r patched=%r/%r/%r parse=%r"
                  % (reported, patched_names, patched_reading,
                     patched["rounds"][0]["foreign"], consequence),
                  flush=True)
        check(ok, "AC-FSF1 vocabulary and parse asked of followup_history")
    finally:
        FH.vocabulary = original_vocab
        FH.parse = original_parse
        shutil.rmtree(world, ignore_errors=True)


def ac_fsf2():
    """AC-FSF2: disjoint readings, exactly one per round, census is a diff."""
    world = make_world([
        ("reconcile-all-R200.log", body(ALL, round_label="R200")),
        ("reconcile-all-R201.log",
         body([("matrix", "PASS"), ("timing", "FAIL")],
              round_label="R201")),
        ("reconcile-all-R202.log",
         body([("matrix", "PASS"), ("timing", "PASS"),
               ("audio", "PASS")], round_label="R202")),
    ])
    world_b = make_world([("reconcile-all-R300.log",
                           body([("matrix", "PASS"), ("seal", "PASS")],
                                round_label="R300"))])
    try:
        report = FSF.reading(world)
        names = report["vocabulary"]
        readings = [item["reading"] for item in report["rounds"]]
        disjoint = True
        for item in report["rounds"]:
            foreign = item["foreign"]
            if item["reading"] == FSF.READING_FOREIGN and not foreign:
                disjoint = False
            if item["reading"] == FSF.READING_CLEAN and foreign:
                disjoint = False
            if any(name in names for name in foreign):
                disjoint = False
        all_names = sorted(item["round"] for item in report["rounds"]
                           if item["reading"] == FSF.READING_FOREIGN)
        census = report["census"]
        missing = FSF.reading(world_b)
        ok = (readings == [FSF.READING_CLEAN, FSF.READING_FOREIGN,
                           FSF.READING_FOREIGN]
              and all_names == ["R201", "R202"]
              and disjoint
              and report["counts"] == {"rounds": 3, "clean": 1, "foreign": 2}
              and census["foreign"] == ["audio", "timing"]
              and census["missing"] == []
              and sorted(census["vocabulary"]) == sorted(names)
              and missing["census"]["missing"] ==
              ["census", "fingerprint", "profile"]
              and missing["rounds"][0]["foreign"] == ["seal"])
        if not ok:
            print("  measured: readings=%r foreign=%r census=%r missing=%r"
                  % (readings, all_names, census, missing["census"]),
                  flush=True)
        check(ok, "AC-FSF2 disjoint readings, exactly one per round")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(world_b, ignore_errors=True)


def ac_fsf3():
    """AC-FSF3: derived from the log alone - no clock, no round threshold."""
    text = body([("matrix", "PASS"), ("timing", "PASS")],
                round_label="R400")
    low = make_world([("reconcile-all-R001.log", text)])
    high = make_world([("reconcile-all-R9999.log", text)])
    source = io.open(MODULE, "r", encoding="utf-8").read()
    try:
        first = FSF.reading(low)["rounds"][0]
        second = FSF.reading(high)["rounds"][0]
        no_clock = ("import time" not in source and "datetime" not in source
                    and "time.time" not in source
                    and "stat(" not in source and "getmtime" not in source)
        low_dir = FSF.reading(low)["dir"]
        ok = (first["foreign"] == ["timing"] and second["foreign"] == ["timing"]
              and first["reading"] == second["reading"] ==
              FSF.READING_FOREIGN
              and low_dir == "qa"
              and no_clock)
        if not ok:
            print("  measured: first=%r second=%r clock=%r dir=%r"
                  % (first, second, no_clock, low_dir), flush=True)
        check(ok, "AC-FSF3 log-derived, clockless, no round threshold")
    finally:
        shutil.rmtree(low, ignore_errors=True)
        shutil.rmtree(high, ignore_errors=True)


def ac_fsf4():
    """AC-FSF4: unreadable/absent refuses at exit 3, never reads CLEAN."""
    world = make_world([("reconcile-all-R700.log",
                         body(ALL, round_label="R700")),
                        ("reconcile-all-R0710.log", None)])
    empty = make_world([("notes.txt", "not evidence\n")])
    bare = os.path.join(tempfile.mkdtemp(prefix="bigdomain-fsf-bare-"), "qa")
    try:
        codes = []
        for target in (world, empty, bare):
            try:
                FSF.reading(target)
                codes.append("no-raise")
            except FSF.FollowupSectionForeignError as exc:
                codes.append(exc.code)
        cli = [run_cli(target)[0] for target in (world, empty, bare)]
        clean_never = "VOCABULARY-CLEAN" not in (run_cli(empty)[1]
                                                 + run_cli(bare)[1])
        ok = (codes == [FSF.E_FSF_UNREADABLE, FSF.E_FSF_NO_EVIDENCE,
                        FSF.E_FSF_NO_EVIDENCE]
              and cli == [3, 3, 3] and clean_never)
        if not ok:
            print("  measured: codes=%r cli=%r clean-never=%r"
                  % (codes, cli, clean_never), flush=True)
        check(ok, "AC-FSF4 fails closed at exit 3, never reads CLEAN")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(empty, ignore_errors=True)
        shutil.rmtree(os.path.dirname(bare), ignore_errors=True)


def ac_fsf5():
    """AC-FSF5: read-only, CLI 0/2/3/5, byte-stable json over pinned keys."""
    clean = make_world([("reconcile-all-R800.log",
                         body(ALL, round_label="R800"))])
    foreign = make_world([("reconcile-all-R801.log",
                           body([("matrix", "PASS"), ("timing", "PASS")],
                                round_label="R801"))])
    try:
        before = tree_digest(clean)
        code_clean, text_clean = run_cli(clean)
        first = run_cli(clean, ["--json"])[1]
        second = run_cli(clean, ["--json"])[1]
        after = tree_digest(clean)
        code_foreign = run_cli(foreign)[0]
        code_bad = run_cli(clean, ["--nope"])[0]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == FSF.REPORT_KEYS
        round_pinned = tuple(parsed["rounds"][0].keys()) == FSF.ROUND_KEYS
        count_pinned = tuple(parsed["counts"].keys()) == FSF.COUNT_KEYS
        census_pinned = tuple(parsed["census"].keys()) == FSF.CENSUS_KEYS
        ok = (code_clean == 0 and code_foreign == 2 and code_bad == 5
              and first == second and before == after
              and pinned and round_pinned and count_pinned and census_pinned
              and parsed["verdict"] == FSF.VERDICT_CLEAN
              and "verdict=VOCABULARY-CLEAN" in text_clean)
        if not ok:
            print("  measured: clean=%r foreign=%r bad=%r stable=%r writes=%r"
                  " pinned=%r/%r/%r/%r"
                  % (code_clean, code_foreign, code_bad, first == second,
                     before == after, pinned, round_pinned, count_pinned,
                     census_pinned), flush=True)
        check(ok, "AC-FSF5 CLI 0/2/5, byte-stable json, zero writes")
    finally:
        shutil.rmtree(clean, ignore_errors=True)
        shutil.rmtree(foreign, ignore_errors=True)


def ac_fsf6():
    """AC-FSF6: pure source, stdlib only, wired, its own label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    runner_text = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner_text) or ("'%s'" % LABEL in runner_text)
    # One round that reports only one of the four ritual names, so the census
    # has a real set difference to name (a full round would leave it empty).
    world = make_world([("reconcile-all-R900.log",
                         body([("matrix", "PASS")], round_label="R900"))])
    try:
        report = FSF.reading(world)
        ok = (ascii_only and no_net and wired
              and report["verdict"] == FSF.VERDICT_CLEAN
              and [item["reading"] for item in report["rounds"]] ==
              [FSF.READING_CLEAN]
              and report["census"]["missing"] ==
              ["census", "fingerprint", "profile"])
        if not ok:
            print("  measured: ascii=%r net=%r wired=%r verdict=%r"
                  % (ascii_only, no_net, wired, report["verdict"]), flush=True)
        check(ok, "AC-FSF6 pure, wired, missing ritual names named")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("followup_section_foreign suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_fsf1()
    ac_fsf2()
    ac_fsf3()
    ac_fsf4()
    ac_fsf5()
    ac_fsf6()
    print("SUITE %s %d/%d"
          % ("PASS" if FAILS == 0 else "FAIL", PASSES,
             PASSES + FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())