"""followup_retry_history suite (R2325; criteria AC-FRH1..AC-FRH6 were
pre-registered inside the R2303 seed row of state/queue/tech.md:380 BEFORE
this code existed).

What this proves: the house aggregate stops judging a round from its
canonical leg alone. A round recovered by a green retry lands in `recovered`
and never in `unfixed`, an unfixed round is never counted as recovered, the
two partition every round whose canonical leg is not PASS, a canonical-only
round keeps exactly the reading followup_history gives it, and a retry leg
with no canonical leg refuses instead of dropping out of the counts.

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
import followup_retry_history as FRH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "followup_retry_history.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-followup-retry-history"

GREEN = ("RUNNER PASS 4/4 suites green\n"
         "SECTION matrix PASS\nSECTION fingerprint PASS\n"
         "SECTION profile PASS\nSECTION census PASS\nVERDICT R1500 PASS\n")
RED = ("RUNNER FAIL 2/4 suites green\n"
       "SECTION matrix PASS\nSECTION fingerprint PASS\n"
       "SECTION profile FAIL\nSECTION census FAIL\nVERDICT R1500 FAIL\n")
RED_BODY_ONLY = "RUNNER FAIL 1/4 suites green\nVERDICT R1504 FAIL\n"

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
    """A temp root with one qa directory."""
    world = tempfile.mkdtemp(prefix="bigdomain-frh-")
    qa = os.path.join(world, "qa")
    os.makedirs(qa)
    for name, body in files:
        with io.open(os.path.join(qa, name), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(body)
    return world


def tree_digest(world):
    """Every file under the world with size and digest, plus directories."""
    out = []
    for root, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(dirs):
            out.append("D:%s" % os.path.relpath(os.path.join(root, name),
                                                world))
        for name in sorted(files):
            path = os.path.join(root, name)
            with io.open(path, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()[:16]
            out.append("%s:%d:%s" % (os.path.relpath(path, world),
                                     os.path.getsize(path), digest))
    return "|".join(sorted(out))


def run_cli(world, extra=()):
    argv = [sys.executable, MODULE, "--history", "--root", world]
    argv.extend(extra)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def synthetic(rounds):
    """A legs report shaped exactly as followup_retry_legs returns one."""
    return {"dir": "qa", "target": "all", "counts": {}, "verdict": "X",
            "rounds": rounds}


def synthetic_round(label, legs, last):
    """One round with the pinned FR round keys."""
    return {"round": label, "evidence": "qa/%s.log" % label,
            "encoding": "utf-8", "runner": last, "sections": [],
            "legs": legs, "leg_count": len(legs), "verdict": last}


def synthetic_leg(name, index, verdict):
    return {"name": name, "index": index,
            "kind": "canonical" if index == 0 else "retry",
            "runner": verdict, "verdict": verdict,
            "evidence": "qa/" + name}


def ac_frh1():
    """AC-FRH1: the per-round reading is asked of followup_retry_legs."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    # The retry FAMILY must not be restated here: no literal suffix and no
    # regex, while the naming law is asked (retry_naming) and the reading and
    # leg order are asked of followup_retry_legs.
    no_second_law = ("re.compile" not in source
                     and '-retry"' not in source
                     and "retry_naming" in source)
    saved = FR.history
    try:
        FR.history = lambda root, directory="qa": synthetic([
            synthetic_round("R1600",
                            [synthetic_leg("reconcile-all-R1600.log", 0,
                                           "FAIL"),
                             synthetic_leg("reconcile-all-R1600-retry.log", 1,
                                           "PASS")], "PASS"),
            synthetic_round("R1601",
                            [synthetic_leg("reconcile-all-R1601.log", 0,
                                           "PASS")], "PASS"),
        ])
        report = FRH.history(".", "qa")
        ok = (no_second_law
              and report["counts"] == {"rounds": 2, "green": 1, "retried": 1,
                                       "recovered": 1, "unfixed": 0,
                                       "regressed": 0}
              and report["verdict"] == "ALL-CLEAN"
              and report["rounds"][0]["klass"] == "recovered"
              and report["rounds"][0]["leg_count"] == 2)
        if not ok:
            print("  measured: law=%r counts=%r report=%r"
                  % (no_second_law, report["counts"], report["rounds"]),
                  flush=True)
        check(ok, "AC-FRH1 per-round reading and leg order asked of the joiner")
    finally:
        FR.history = saved


def ac_frh2():
    """AC-FRH2: recovered and unfixed partition the canonical-not-PASS set."""
    world = make_world([("reconcile-all-R1500.log", RED),
                        ("reconcile-all-R1500-retry.log", GREEN),
                        ("reconcile-all-R1501.log", RED),
                        ("reconcile-all-R1501-retry.log", RED),
                        ("reconcile-all-R1501-retry2.log", GREEN),
                        ("reconcile-all-R1502.log", GREEN),
                        ("reconcile-all-R1503.log", RED)])
    try:
        report = FRH.history(world, "qa")
        by_round = dict((item["round"], item) for item in report["rounds"])
        counts = report["counts"]
        canonical_bad = [item for item in report["rounds"]
                         if item["canonical_verdict"] != "PASS"]
        ok = (by_round["R1500"]["klass"] == "recovered"
              and by_round["R1501"]["klass"] == "recovered"
              and by_round["R1502"]["klass"] == "green"
              and by_round["R1503"]["klass"] == "unfixed"
              and counts["recovered"] == 2
              and counts["unfixed"] == 1
              and counts["green"] == 1
              and counts["retried"] == 2
              and counts["regressed"] == 0
              and counts["recovered"] + counts["unfixed"] == len(canonical_bad)
              and counts["rounds"] == 4
              and report["verdict"] == "HISTORY-DEBT")
        if not ok:
            print("  measured: counts=%r classes=%r bad=%d"
                  % (counts, [(item["round"], item["klass"])
                              for item in report["rounds"]],
                     len(canonical_bad)), flush=True)
        check(ok, "AC-FRH2 recovered and unfixed partition the red canonicals")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_frh3():
    """AC-FRH3: a canonical-only round keeps the history reading verbatim."""
    world = make_world([("reconcile-all-R1504.log", RED_BODY_ONLY),
                        ("reconcile-all-R1505.log", GREEN)])
    try:
        theirs = dict((item["round"], item) for item in
                      FH.history(world, "qa")["rounds"])
        ours = dict((item["round"], item) for item in
                    FRH.history(world, "qa")["rounds"])
        same = all(ours[label][key] == theirs[label][key]
                   for label in ("R1504", "R1505")
                   for key in ("round", "evidence", "verdict"))
        ok = (same
              and ours["R1504"]["canonical_verdict"] == "FAIL"
              and ours["R1504"]["klass"] == "unfixed"
              and ours["R1505"]["canonical_verdict"] == "PASS"
              and ours["R1505"]["leg_count"] == 1)
        if not ok:
            print("  measured: same=%r ours=%r theirs=%r"
                  % (same, ours, theirs), flush=True)
        check(ok, "AC-FRH3 canonical-only round keeps the history reading")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_frh4():
    """AC-FRH4: a retry leg with no canonical leg refuses, never dropped."""
    orphan = make_world([("reconcile-all-R1506-retry.log", GREEN),
                         ("reconcile-all-R1507.log", GREEN)])
    try:
        raised = None
        try:
            FRH.history(orphan, "qa")
        except FRH.FollowupRetryHistoryError as exc:
            raised = exc.code
        code = run_cli(orphan)[0]
        ok = raised == "E_FRTL_ORPHAN_RETRY" and code == 3
        if not ok:
            print("  measured: raised=%r code=%r" % (raised, code),
                  flush=True)
        check(ok, "AC-FRH4 orphan retry refuses instead of vanishing")
    finally:
        shutil.rmtree(orphan, ignore_errors=True)


def ac_frh5():
    """AC-FRH5: read-only, exit codes, byte-stable json over pinned keys."""
    clean = make_world([("reconcile-all-R1508.log", RED),
                        ("reconcile-all-R1508-retry.log", GREEN),
                        ("reconcile-all-R1509.log", GREEN)])
    debt = make_world([("reconcile-all-R1510.log", RED)])
    try:
        before = tree_digest(clean)
        FRH.history(clean, "qa")
        after = tree_digest(clean)
        code_clean = run_cli(clean)[0]
        code_debt = run_cli(debt)[0]
        code_flags = run_cli(clean, ["--nope"])[0]
        code_absent = run_cli(os.path.join(clean, "nowhere"))[0]
        first = run_cli(debt, ["--json"])[1]
        second = run_cli(debt, ["--json"])[1]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == FRH.REPORT_KEYS
        counts_pinned = tuple(parsed["counts"].keys()) == FRH.COUNT_KEYS
        row_pinned = tuple(parsed["rounds"][0].keys()) == FRH.ROUND_KEYS
        ok = (before == after
              and code_clean == 0 and code_debt == 2
              and code_flags == 5 and code_absent == 3
              and first == second
              and pinned and counts_pinned and row_pinned
              and parsed["verdict"] == "HISTORY-DEBT"
              and parsed["counts"]["unfixed"] == 1)
        if not ok:
            print("  measured: writes=%r codes=%r stable=%r pinned=%r/%r/%r "
                  "verdict=%r" % (before == after,
                                  (code_clean, code_debt, code_flags,
                                   code_absent), first == second, pinned,
                                  counts_pinned, row_pinned,
                                  parsed["verdict"]), flush=True)
        check(ok, "AC-FRH5 read-only, four exit codes, stable pinned json")
    finally:
        shutil.rmtree(clean, ignore_errors=True)
        shutil.rmtree(debt, ignore_errors=True)


def ac_frh6():
    """AC-FRH6: pure source, wired label, and a real reading of the pile."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    no_clock = ("import time" not in source and "datetime" not in source
                and "time.time" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    live = FRH.history(REPO, "qa")
    legs = FR.history(REPO, "qa")
    rendered = FRH.render(live)
    recovered = [item for item in live["rounds"]
                 if item["klass"] == "recovered"]
    ok = (ascii_only and no_net and no_clock and wired
          and live["dir"] == "qa"
          and live["counts"]["rounds"] == legs["counts"]["rounds"]
          and live["counts"]["retried"] == legs["counts"]["retried"]
          and len(recovered) >= 1
          and "FOLLOWUP RETRY HISTORY" in rendered
          and "verdict=%s" % live["verdict"] in rendered)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r wired=%r live=%r legs=%r "
              "recovered=%r" % (ascii_only, no_net, no_clock, wired,
                                live["counts"], legs["counts"],
                                len(recovered)), flush=True)
    check(ok, "AC-FRH6 pure, wired, live pile aggregate agrees with the joiner")


def main():
    print("followup_retry_history suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_frh1()
    ac_frh2()
    ac_frh3()
    ac_frh4()
    ac_frh5()
    ac_frh6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())