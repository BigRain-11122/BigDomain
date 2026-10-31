"""stamp_residue suite (R2298; criteria AC-SRS1..AC-SRS6 were pre-registered
inside the R2284 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: the triage of the stamped-but-never-logged residue becomes
one table instead of N hand greps, and a stamp on an unfinished row is never
read as delivery evidence. Both laws are imported - the residue list from
state_seq, the hit scan from stamp_locator - and the suite proves each import
by patching it and watching the reading move.

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

import stamp_locator as SL  # noqa: E402
import stamp_residue as SR  # noqa: E402
import state_seq as SQ  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "stamp_residue.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-stamp-residue"

HEADER = "# queue test world\n\nprose that never becomes a row\n\n"

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


def make_world(log_items, tech, main=None, explore=None, drop=None,
               no_state=False):
    """Build a temp root: state.json plus the three queue files."""
    world = tempfile.mkdtemp(prefix="bigdomain-srs-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    if not no_state:
        payload = {"tick": 2300, "log": list(log_items)}
        path = os.path.join(world, "src", "os", "state.json")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload))
    bodies = {"tech": tech,
              "main": main if main is not None else HEADER,
              "explore": explore if explore is not None else HEADER}
    for name in bodies:
        if drop and name in drop:
            continue
        path = os.path.join(world, "state", "queue", name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    return world


def tree_digest(root):
    """Deterministic digest of the queue tree bytes."""
    parts = []
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            with open(path, "rb") as handle:
                parts.append((os.path.relpath(path, root).replace("\\", "/"),
                              handle.read()))
    return parts


def ac_srs1():
    """AC-SRS1: residue list and stamp law are imported, patches flow."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_second_law = ("import state_seq" in source
                     and "re.compile" not in source
                     and "\\[done" not in source)
    tech = "- [x] [done 2026-10-31 R2210] a closed row\n"
    world = make_world(["R2200 a logged item"], tech)
    try:
        plain = SR.read(world)
        saved_audit = SQ.audit
        saved_law = SQ.DONE_STAMP_RE
        try:
            SQ.audit = lambda root: {"queue_only": [2287]}
            patched_list = SR.read(world)
            SQ.audit = saved_audit
            SQ.DONE_STAMP_RE = SQ.re.compile(
                r"\[done\s+\d{4}-\d{2}-\d{2}\s+R(22\d{2})\]")
            patched_law = SR.read(world)
        finally:
            SQ.audit = saved_audit
            SQ.DONE_STAMP_RE = saved_law
        ok = (no_second_law
              and [row["round"] for row in plain["rounds"]] == [2210]
              and [row["round"] for row in patched_list["rounds"]] == [2287]
              and patched_list["rounds"][0]["status"] == "NO-HIT"
              and patched_law["rounds"][0]["hit_count"] == 1)
        if not ok:
            print("  measured: law=%r plain=%r list=%r narrow=%r"
                  % (no_second_law,
                     [row["round"] for row in plain["rounds"]],
                     [row["round"] for row in patched_list["rounds"]],
                     patched_law["rounds"][0]["hit_count"]), flush=True)
        check(ok, "AC-SRS1 residue list and stamp law imported")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_srs2():
    """AC-SRS2: every residue round once, with counts that reconcile."""
    tech = ("- [x] [done 2026-10-31 R2211] closed one\n"
            "- [ ] [done 2026-10-31 R2212] an open row with a stamp\n"
            "- [x] [done 2026-10-31 R2213] closed two\n")
    main = "- [x] [done 2026-10-31 R2214] a main-line closed row\n"
    world = make_world(["R2200 a logged item"], tech, main=main)
    try:
        report = SR.read(world)
        rounds = [row["round"] for row in report["rounds"]]
        keys_ok = all(sorted(row.keys()) == sorted(SR.ROW_KEYS)
                      for row in report["rounds"])
        hit_keys_ok = all(sorted(hit.keys()) == sorted(SR.HIT_KEYS)
                          for row in report["rounds"] for hit in row["hits"])
        sums_ok = all(row["closed_hits"] + row["open_hits"] == row["hit_count"]
                      for row in report["rounds"])
        by_round = dict((row["round"], row) for row in report["rounds"])
        ok = (keys_ok and hit_keys_ok and sums_ok
              and rounds == [2211, 2212, 2213, 2214]
              and len(set(rounds)) == len(rounds)
              and report["round_count"] == 4
              and report["delivered"] + report["stamp_only_open"]
              + report["no_hit"] == report["round_count"]
              and report["delivered"] == 3
              and report["stamp_only_open"] == 1
              and by_round[2212]["closed_hits"] == 0
              and by_round[2212]["open_hits"] == 1
              and by_round[2214]["closed_hits"] == 1
              and report["verdict"] == "RESIDUE")
        if not ok:
            print("  measured: rounds=%r keys=%r sums=%r d=%r s=%r n=%r"
                  % (rounds, keys_ok, sums_ok, report["delivered"],
                     report["stamp_only_open"], report["no_hit"]), flush=True)
        check(ok, "AC-SRS2 each round once, counts reconcile")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_srs3():
    """AC-SRS3: a stamp only on an OPEN row is not delivery evidence."""
    tech = ("- [ ] [done 2026-10-31 R2220] an open row carrying a stamp\n"
            "- [x] [done 2026-10-31 R2221] a closed row\n"
            "- [x] [done 2026-10-31 R2221] the same round again, closed\n"
            "- [ ] [done 2026-10-31 R2221] and once more, open\n")
    world = make_world(["R2200 a logged item"], tech)
    try:
        report = SR.read(world)
        by_round = dict((row["round"], row) for row in report["rounds"])
        open_only = by_round[2220]
        mixed = by_round[2221]
        ok = (open_only["status"] == "STAMP-ONLY-OPEN"
              and open_only["closed_hits"] == 0
              and open_only["open_hits"] == 1
              and mixed["status"] == "DELIVERED"
              and mixed["hit_count"] == 3
              and mixed["closed_hits"] == 2
              and mixed["open_hits"] == 1)
        if not ok:
            print("  measured: open=%r mixed=%r"
                  % (open_only, mixed), flush=True)
        check(ok, "AC-SRS3 open-only stamp reads STAMP-ONLY-OPEN")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_srs4():
    """AC-SRS4: no hit reads NO-HIT; empty residue reads CLEAN at exit 0."""
    tech = "- [x] [done 2026-10-31 R2230] a closed row\n"
    world = make_world(["R2200 a logged item"], tech)
    try:
        saved = SQ.audit
        try:
            SQ.audit = lambda root: {"queue_only": [2299]}
            absent = SR.read(world)
            SQ.audit = lambda root: {"queue_only": []}
            empty = SR.read(world)
        finally:
            SQ.audit = saved
        code = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--check"],
            cwd=BASE, capture_output=True, text=True)
        clean_world = make_world(["R2231 a logged item"],
                                 "- [x] [done 2026-10-31 R2231] closed\n")
        try:
            clean = subprocess.run(
                [sys.executable, MODULE, "--root", clean_world, "--check"],
                cwd=BASE, capture_output=True, text=True)
        finally:
            shutil.rmtree(clean_world, ignore_errors=True)
        ok = (absent["rounds"][0]["status"] == "NO-HIT"
              and absent["no_hit"] == 1
              and absent["verdict"] == "RESIDUE"
              and empty["round_count"] == 0
              and empty["verdict"] == "CLEAN"
              and clean.returncode == 0
              and clean.stdout.startswith("STAMP RESIDUE rounds=0")
              and code.returncode == 2)
        if not ok:
            print("  measured: absent=%r empty=%r codes=%r out=%r"
                  % (absent["rounds"][0]["status"], empty["verdict"],
                     (code.returncode, clean.returncode),
                     clean.stdout[:80]), flush=True)
        check(ok, "AC-SRS4 NO-HIT named, empty residue CLEAN at exit 0")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_srs5():
    """AC-SRS5: CLI codes, byte-stable --json, zero writes."""
    tech = "- [x] [done 2026-10-31 R2240] a closed row\n"
    world = make_world(["R2200 a logged item"], tech)
    try:
        before = tree_digest(world)
        residue = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--check"],
            cwd=BASE, capture_output=True, text=True)
        bad = subprocess.run(
            [sys.executable, MODULE, "--nope"], cwd=BASE,
            capture_output=True, text=True)
        missing = subprocess.run(
            [sys.executable, MODULE, "--root",
             os.path.join(world, "absent"), "--check"], cwd=BASE,
            capture_output=True, text=True)
        one = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--check", "--json"],
            cwd=BASE, capture_output=True, text=True)
        two = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--check", "--json"],
            cwd=BASE, capture_output=True, text=True)
        after = tree_digest(world)
        payload = json.loads(one.stdout)
        keys_ok = list(payload.keys()) == list(SR.REPORT_KEYS)
        row_keys_ok = all(list(row.keys()) == list(SR.ROW_KEYS)
                          for row in payload["rounds"])
        ok = (residue.returncode == 2 and bad.returncode == 5
              and missing.returncode == 3
              and residue.stdout.startswith("STAMP RESIDUE rounds=1")
              and one.stdout == two.stdout and keys_ok and row_keys_ok
              and before == after)
        if not ok:
            print("  measured: codes=%r stable=%r keys=%r rowkeys=%r "
                  "writes=%r" % (residue.returncode, one.stdout == two.stdout,
                                 keys_ok, row_keys_ok, before == after),
                  flush=True)
        check(ok, "AC-SRS5 CLI codes and byte-stable --json")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_srs6():
    """AC-SRS6: pure source, both imports live, wired, zero writes."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    no_clock = ("datetime" not in source and "time.time" not in source)
    imported = ("SQ.audit" in source and "SL.locate" in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = '"%s"' % LABEL in runner or "'%s'" % LABEL in runner
    tech = "- [x] [done 2026-10-31 R2250] a closed row\n"
    world = make_world(["R2200 a logged item"], tech)
    try:
        before = tree_digest(world)
        live = SR.read(world)
        after = tree_digest(world)
        saved = SL.locate
        try:
            SL.locate = lambda root, number: {
                "round": number, "hit_count": 0, "hits": [],
                "queues_scanned": 3, "missing_queues": [], "verdict": "NO-HITS"}
            patched = SR.read(world)
        finally:
            SL.locate = saved
        ok = (ascii_only and no_net and no_clock and imported and wired
              and live["rounds"][0]["status"] == "DELIVERED"
              and patched["rounds"][0]["status"] == "NO-HIT"
              and before == after)
        if not ok:
            print("  measured: ascii=%r net=%r clock=%r imported=%r wired=%r "
                  "live=%r patched=%r writes=%r"
                  % (ascii_only, no_net, no_clock, imported, wired,
                     live["rounds"][0]["status"],
                     patched["rounds"][0]["status"], before == after),
                  flush=True)
        check(ok, "AC-SRS6 pure, both imports live, wired, zero writes")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def main():
    print("stamp_residue suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_srs1()
    ac_srs2()
    ac_srs3()
    ac_srs4()
    ac_srs5()
    ac_srs6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())