"""followup_retry_legs suite (R2303; criteria AC-FRTL1..AC-FRTL6 were
pre-registered inside the R2289 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: a round whose canonical battery went RED and whose retry
went GREEN no longer reads INCOMPLETE forever. The retry family is asked of
retry_naming (suffix, predicate, base-stem), the legs are ordered canonical
then -retry..-retryN, the round verdict comes from the LAST leg while every
earlier leg keeps its own runner line, a canonical-only round reads exactly
what followup_history returns, and a retry leg with no canonical leg refuses
instead of inventing a round.

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
import followup_retry_legs as FR  # noqa: E402
import retry_naming as RN  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "followup_retry_legs.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-followup-retry-legs"

GREEN = ("RUNNER PASS 4/4 suites green\n"
         "SECTION matrix PASS\nSECTION fingerprint PASS\n"
         "SECTION profile PASS\nSECTION census PASS\nVERDICT R1500 PASS\n")
RED = ("RUNNER FAIL 2/4 suites green\n"
       "SECTION matrix PASS\nSECTION fingerprint PASS\n"
       "SECTION profile FAIL\nSECTION census FAIL\nVERDICT R1500 FAIL\n")
RED_BODY_ONLY = "RUNNER FAIL 1/4 suites green\nVERDICT R1504 FAIL\n"
GREEN_BODY_ONLY = "RUNNER PASS 4/4 suites green\nVERDICT R1504 PASS\n"

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
    world = tempfile.mkdtemp(prefix="bigdomain-frtl-")
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
            rel = os.path.relpath(os.path.join(root, name), world)
            out.append("D:%s" % rel)
        for name in sorted(files):
            path = os.path.join(root, name)
            with io.open(path, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()[:16]
            rel = os.path.relpath(path, world)
            out.append("%s:%d:%s" % (rel, os.path.getsize(path), digest))
    return "|".join(sorted(out))


def run_cli(world, extra=()):
    argv = [sys.executable, MODULE, "--legs", "--root", world]
    argv.extend(extra)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_frtl1():
    """AC-FRTL1: the retry family comes from retry_naming, never re-derived."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    statements = [line.strip() for line in source.splitlines()]
    no_regex = ("import re" not in statements and "re.compile" not in source
                and "\\d" not in source)
    world = make_world([("reconcile-all-R1500.log", GREEN),
                        ("reconcile-all-R1500-retry.log", GREEN)])
    moved = make_world([("reconcile-all-R1500.log", GREEN),
                        ("reconcile-all-R1500-rerun.log", GREEN),
                        ("reconcile-all-R1500-rerun2.log", GREEN)])
    saved_is, saved_suffix, saved_base = (RN.is_retry, RN.RETRY_SUFFIX,
                                          RN.base_stem)
    try:
        live = FR.history(world, "qa", "R1500")
        # Ask the law to say "no retries": the reader must follow, which is
        # only possible if it asks rather than re-deriving the suffix.
        RN.is_retry = lambda name: False
        blind = FR.history(world, "qa", "R1500")
        # Ask the law to speak a different suffix: order and count follow.
        RN.RETRY_SUFFIX = "-rerun"

        def rerun_retry(name):
            stem = name[:-4] if name.endswith(".log") else name
            return stem.endswith("-rerun") or stem.endswith("-rerun2")

        def rerun_base(name):
            stem = name[:-4]
            for suffix in ("-rerun2", "-rerun"):
                if stem.endswith(suffix):
                    return stem[:-len(suffix)]
            return stem

        RN.is_retry = rerun_retry
        RN.base_stem = rerun_base
        renamed = FR.history(moved, "qa", "R1500")
        ok = (no_regex
              and live["rounds"][0]["leg_count"] == 2
              and blind["rounds"][0]["leg_count"] == 1
              and renamed["rounds"][0]["leg_count"] == 3
              and [leg["name"] for leg in renamed["rounds"][0]["legs"]]
              == ["reconcile-all-R1500.log",
                  "reconcile-all-R1500-rerun.log",
                  "reconcile-all-R1500-rerun2.log"]
              and FR.canonical_stem("R1500") == "reconcile-all-R1500")
        if not ok:
            print("  measured: no_regex=%r live=%r blind=%r renamed=%r"
                  % (no_regex, live["rounds"][0]["leg_count"],
                     blind["rounds"][0]["leg_count"],
                     [leg["name"] for leg in renamed["rounds"][0]["legs"]]),
                  flush=True)
        check(ok, "AC-FRTL1 retry family asked of retry_naming")
    finally:
        RN.is_retry, RN.RETRY_SUFFIX, RN.base_stem = (saved_is, saved_suffix,
                                                      saved_base)
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(moved, ignore_errors=True)


def ac_frtl2():
    """AC-FRTL2: canonical plus every retry leg, in retry order."""
    world = make_world([("reconcile-all-R1501-retry2.log", GREEN),
                        ("reconcile-all-R1501.log", GREEN),
                        ("reconcile-all-R1501-retry.log", GREEN),
                        ("reconcile-all-R1501-retry3.log", GREEN)])
    try:
        report = FR.history(world, "qa", "R1501")
        item = report["rounds"][0]
        names = [leg["name"] for leg in item["legs"]]
        indexes = [leg["index"] for leg in item["legs"]]
        kinds = [leg["kind"] for leg in item["legs"]]
        ok = (names == ["reconcile-all-R1501.log",
                        "reconcile-all-R1501-retry.log",
                        "reconcile-all-R1501-retry2.log",
                        "reconcile-all-R1501-retry3.log"]
              and indexes == [0, 1, 2, 3]
              and kinds == ["canonical", "retry", "retry", "retry"]
              and item["leg_count"] == 4
              and report["counts"]["retried"] == 1
              and report["counts"]["canonical_only"] == 0)
        if not ok:
            print("  measured: names=%r indexes=%r kinds=%r counts=%r"
                  % (names, indexes, kinds, report["counts"]), flush=True)
        check(ok, "AC-FRTL2 canonical plus every retry leg in retry order")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_frtl3():
    """AC-FRTL3: verdict from the LAST leg, earlier legs keep their runner."""
    recovered = make_world([("reconcile-all-R1502.log", RED),
                            ("reconcile-all-R1502-retry.log", GREEN)])
    still_red = make_world([("reconcile-all-R1502.log", RED),
                            ("reconcile-all-R1502-retry.log", GREEN),
                            ("reconcile-all-R1502-retry2.log", RED)])
    try:
        green = FR.history(recovered, "qa", "R1502")["rounds"][0]
        red = FR.history(still_red, "qa", "R1502")["rounds"][0]
        green_runners = [leg["runner"] for leg in green["legs"]]
        red_runners = [leg["runner"] for leg in red["legs"]]
        ok = (green["verdict"] == "PASS"
              and green["runner"] == "PASS"
              and green["leg_count"] == 2
              and green_runners == ["FAIL", "PASS"]
              and green["legs"][0]["verdict"] == "FAIL"
              and green["legs"][1]["verdict"] == "PASS"
              and red["verdict"] == "FAIL"
              and red["runner"] == "FAIL"
              and red_runners == ["FAIL", "PASS", "FAIL"]
              and red["legs"][1]["verdict"] == "PASS")
        if not ok:
            print("  measured: green=%r red=%r"
                  % ((green["verdict"], green_runners),
                     (red["verdict"], red_runners)), flush=True)
        check(ok, "AC-FRTL3 last leg decides, earlier legs still reported")
    finally:
        shutil.rmtree(recovered, ignore_errors=True)
        shutil.rmtree(still_red, ignore_errors=True)


def ac_frtl4():
    """AC-FRTL4: a canonical-only round reads exactly followup_history's row."""
    world = make_world([("reconcile-all-R1503.log", GREEN),
                        ("reconcile-all-R1504.log", RED_BODY_ONLY)])
    try:
        ours = FR.history(world, "qa", "R1503")["rounds"][0]
        theirs = [item for item in FH.history(world, "qa")["rounds"]
                  if item["round"] == "R1503"][0]
        same = all(ours[key] == theirs[key]
                   for key in ("round", "evidence", "encoding", "runner",
                               "sections", "verdict"))
        incomplete = FR.history(world, "qa", "R1504")["rounds"][0]
        ok = (same and ours["leg_count"] == 1
              and ours["legs"][0]["kind"] == "canonical"
              and FR.history(world, "qa", "R1503")["counts"]
              == {"rounds": 1, "canonical_only": 1, "retried": 0, "red": 0}
              and incomplete["verdict"] == "INCOMPLETE")
        if not ok:
            print("  measured: same=%r ours=%r theirs=%r incomplete=%r"
                  % (same, ours, theirs, incomplete["verdict"]), flush=True)
        check(ok, "AC-FRTL4 canonical-only round equals the history reading")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_frtl5():
    """AC-FRTL5: a retry leg with no canonical leg refuses, inventing nothing."""
    orphan = make_world([("reconcile-all-R1505-retry.log", GREEN)])
    try:
        raised = None
        try:
            FR.history(orphan, "qa", "R1505")
        except FR.FollowupRetryError as exc:
            raised = exc.code
        code = run_cli(orphan, ["--json", "R1505"])[0]
        all_code = run_cli(orphan, ["--json"])[0]
        ok = (raised == "E_FRTL_ORPHAN_RETRY" and code == 3
              and all_code == 3)
        if not ok:
            print("  measured: raised=%r code=%r all=%r"
                  % (raised, code, all_code), flush=True)
        check(ok, "AC-FRTL5 retry without canonical refuses")
    finally:
        shutil.rmtree(orphan, ignore_errors=True)


def ac_frtl6():
    """AC-FRTL6: read-only, pure source, wired, pinned json, live callable."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    no_clock = ("import time" not in source and "datetime" not in source
                and "time.time" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    world = make_world([("reconcile-all-R1506.log", RED),
                        ("reconcile-all-R1506-retry.log", GREEN),
                        ("reconcile-all-R1507.log", GREEN)])
    red_world = make_world([("reconcile-all-R1508.log", RED)])
    try:
        before = tree_digest(world)
        FR.history(world, "qa")
        after = tree_digest(world)
        code_green = run_cli(world)[0]
        code_red = run_cli(red_world)[0]
        code_flags = run_cli(world, ["--nope"])[0]
        code_absent = run_cli(os.path.join(world, "nowhere"))[0]
        first = run_cli(red_world, ["--json"])[1]
        second = run_cli(red_world, ["--json"])[1]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == FR.REPORT_KEYS
        counts_pinned = tuple(parsed["counts"].keys()) == FR.COUNT_KEYS
        row_pinned = tuple(parsed["rounds"][0].keys()) == FR.ROUND_KEYS
        leg_pinned = tuple(parsed["rounds"][0]["legs"][0].keys()) == \
            FR.LEG_KEYS
        rendered = FR.render(FR.history(red_world, "qa"))
        live = FR.history(REPO, "qa")
        recovered = [item for item in live["rounds"]
                     if item["leg_count"] > 1
                     and item["verdict"] == "PASS"
                     and item["legs"][0]["verdict"] != "PASS"]
        ok = (ascii_only and no_net and no_clock and wired
              and before == after
              and code_green == 0 and code_red == 2
              and code_flags == 5 and code_absent == 3
              and first == second
              and pinned and counts_pinned and row_pinned and leg_pinned
              and parsed["verdict"] == "HISTORY-RED"
              and "FOLLOWUP RETRY LEGS" in rendered
              and live["dir"] == "qa"
              and live["counts"]["retried"] >= 1
              and len(recovered) >= 1)
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r wired=%r writes=%r "
                  "codes=%r stable=%r pinned=%r/%r/%r/%r verdict=%r live=%r "
                  "recovered=%r"
                  % (ascii_only, no_net, no_clock, wired, before == after,
                     (code_green, code_red, code_flags, code_absent),
                     first == second, pinned, counts_pinned, row_pinned,
                     leg_pinned, parsed["verdict"], live["counts"],
                     len(recovered)), flush=True)
        check(ok, "AC-FRTL6 read-only, pure, wired, live recovery visible")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(red_world, ignore_errors=True)


def main():
    print("followup_retry_legs suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_frtl1()
    ac_frtl2()
    ac_frtl3()
    ac_frtl4()
    ac_frtl5()
    ac_frtl6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())