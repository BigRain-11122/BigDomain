"""stamp_locator suite (R2284; criteria AC-SLC1..AC-SLC6 were pre-registered
inside the R2269 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: a NEVER-LOGGED stamp residue becomes a named evidence
trail of file, line, row head and closed marker instead of a hand grep.
The stamp law is imported from state_seq and the row-closed law from
queue_floor, so neither is re-implemented; the suite proves the import by
patching each one and watching the reading move.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import queue_floor as QF  # noqa: E402
import state_seq as SQ  # noqa: E402
import stamp_locator as SL  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "stamp_locator.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-stamp-locator"

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


def make_world(tech, main=None, explore=None, drop=None):
    """Build a temp root with the three queue files, minus any dropped."""
    world = tempfile.mkdtemp(prefix="bigdomain-slc-")
    state = os.path.join(world, "state", "queue")
    os.makedirs(state)
    bodies = {"tech": tech,
              "main": main if main is not None else HEADER,
              "explore": explore if explore is not None else HEADER}
    for name in bodies:
        if drop and name in drop:
            continue
        path = os.path.join(state, name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    return world


def count_rows(law_text):
    """Rows whose own line carries the imported law, counted independently."""
    total = 0
    for line in law_text.split("\n"):
        if list(SQ.DONE_STAMP_RE.finditer(line)):
            total += 1
    return total


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


def ac_slc1():
    """AC-SLC1: the stamp law is imported, and a patched law flows through."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_second_law = ("import state_seq" in source
                     and "re.compile" not in source
                     and "\\[done" not in source)
    tech = ("- [x] [done 2026-10-31 R2200] a closed row\n"
            "- [ ] open row\n")
    world = make_world(tech)
    try:
        plain = SL.locate(world, 2200)
        saved = SQ.DONE_STAMP_RE
        try:
            SQ.DONE_STAMP_RE = SQ.re.compile(
                r"\[done\s+\d{4}-\d{2}-\d{2}\s+R(22\d{2})\]")
            patched_same = SL.locate(world, 2200)
            patched_narrow = SL.locate(world, 2201)
        finally:
            SQ.DONE_STAMP_RE = saved
        ok = (no_second_law
              and plain["hit_count"] == 1
              # the patched law is really the one being read
              and patched_same["hit_count"] == 1
              and patched_narrow["hit_count"] == 0
              and patched_narrow["verdict"] == "NO-HITS")
        if not ok:
            print("  measured: law=%r plain=%r same=%r narrow=%r"
                  % (no_second_law, plain["hit_count"],
                     patched_same["hit_count"],
                     patched_narrow["hit_count"]), flush=True)
        check(ok, "AC-SLC1 stamp law imported from state_seq")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_slc2():
    """AC-SLC2: every hit carries file, line, row head and closed marker."""
    tech = ("- [x] [done 2026-10-31 R2210] the first closed row\n"
            "- [ ] [done 2026-10-31 R2210] an open row carrying a stamp\n")
    main = ("- [x] [done 2026-10-30 R2210] a main-line closed row\n")
    world = make_world(tech, main=main)
    try:
        report = SL.locate(world, 2210)
        keys_ok = all(sorted(hit.keys()) == sorted(SL.HIT_KEYS)
                      for hit in report["hits"])
        closed = [hit["closed"] for hit in report["hits"]]
        lines_ok = all(isinstance(hit["line"], int) and hit["line"] >= 1
                       for hit in report["hits"])
        heads_ok = all(hit["row_head"].startswith("- [")
                       for hit in report["hits"])
        expected = (count_rows(tech) + count_rows(main))
        files = sorted(set(hit["file"] for hit in report["hits"]))
        ok = (keys_ok and lines_ok and heads_ok
              and report["hit_count"] == expected == 3
              and files == ["state/queue/main.md", "state/queue/tech.md"]
              and sorted(closed) == [False, True, True])
        if not ok:
            print("  measured: keys=%r lines=%r heads=%r count=%d exp=%d "
                  "files=%r" % (keys_ok, lines_ok, heads_ok,
                                report["hit_count"], expected, files),
                  flush=True)
        check(ok, "AC-SLC2 hits carry file/line/head/closed, count matches")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_slc3():
    """AC-SLC3: a round with no stamp reads NO-HITS honestly at exit 2."""
    tech = "- [x] [done 2026-10-31 R2220] a closed row\n"
    world = make_world(tech)
    try:
        missing = SL.locate(world, 2999)
        present = SL.locate(world, 2220)
        code = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--round", "R2999"],
            cwd=BASE, capture_output=True, text=True)
        ok = (missing["hit_count"] == 0
              and missing["verdict"] == "NO-HITS"
              and present["verdict"] == "HITS"
              and code.returncode == 2
              and "STAMP LOCATOR round=R2999 hits=0" in code.stdout
              and "Traceback" not in code.stdout)
        if not ok:
            print("  measured: verdict=%r code=%r out=%r"
                  % (missing["verdict"], code.returncode,
                     code.stdout[:120]), flush=True)
        check(ok, "AC-SLC3 no stamp reads NO-HITS at exit 2")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_slc4():
    """AC-SLC4: the reader writes nothing and reads no clock."""
    tech = ("- [x] [done 2026-10-31 R2230] a closed row\n"
            "- [ ] open row\n")
    world = make_world(tech)
    try:
        before = tree_digest(world)
        first = SL.locate(world, 2230)
        second = SL.locate(world, 2230)
        after = tree_digest(world)
        source = io.open(MODULE, "r", encoding="utf-8").read()
        no_clock = ("datetime" not in source and "time.time" not in source
                    and "now(" not in source)
        ok = (before == after
              and SL.to_json(first) == SL.to_json(second)
              and no_clock)
        if not ok:
            print("  measured: writes=%r repeat=%r clock=%r"
                  % (before == after, SL.to_json(first) == SL.to_json(second),
                     no_clock), flush=True)
        check(ok, "AC-SLC4 zero writes, reproducible, no clock")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_slc5():
    """AC-SLC5: CLI codes and a byte-stable --json over pinned keys."""
    tech = "- [x] [done 2026-10-31 R2240] a closed row\n"
    world = make_world(tech, drop=("explore",))
    try:
        hits = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--round", "R2240"],
            cwd=BASE, capture_output=True, text=True)
        none = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--round", "R2999"],
            cwd=BASE, capture_output=True, text=True)
        bad = subprocess.run(
            [sys.executable, MODULE, "--nope"], cwd=BASE,
            capture_output=True, text=True)
        gone = subprocess.run(
            [sys.executable, MODULE, "--root",
             os.path.join(world, "absent"), "--round", "R2240"],
            cwd=BASE, capture_output=True, text=True)
        one = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--round", "R2240",
             "--json"], cwd=BASE, capture_output=True, text=True)
        two = subprocess.run(
            [sys.executable, MODULE, "--root", world, "--round", "R2240",
             "--json"], cwd=BASE, capture_output=True, text=True)
        import json
        payload = json.loads(one.stdout)
        keys_ok = list(payload.keys()) == list(SL.REPORT_KEYS)
        ok = (hits.returncode == 0 and none.returncode == 2
              and bad.returncode == 5 and gone.returncode == 3
              and hits.stdout.startswith("STAMP LOCATOR round=R2240 hits=1")
              and one.stdout == two.stdout and keys_ok
              and payload["missing_queues"] == ["explore"])
        if not ok:
            print("  measured: codes=%r stable=%r keys=%r out=%r"
                  % ((hits.returncode, none.returncode, bad.returncode,
                      gone.returncode), one.stdout == two.stdout, keys_ok,
                     hits.stdout[:80]), flush=True)
        check(ok, "AC-SLC5 CLI codes and byte-stable --json")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_slc6():
    """AC-SLC6: pure source, imported row law, wired, zero writes."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    imported = "QF.is_done_row" in source and "SQ.DONE_STAMP_RE" in source
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = '"%s"' % LABEL in runner or "'%s'" % LABEL in runner
    tech = ("- [x] [done 2026-10-31 R2250] a closed row\n"
            "- [ ] open row\n")
    world = make_world(tech)
    try:
        before = tree_digest(world)
        live = SL.locate(world, 2250)
        after = tree_digest(world)
        saved = QF.is_done_row
        try:
            QF.is_done_row = lambda line: False
            patched = SL.locate(world, 2250)
        finally:
            QF.is_done_row = saved
        ok = (ascii_only and no_net and imported
              and patched["hit_count"] == 1
              and all(hit["closed"] is False for hit in patched["hits"])
              and live["hits"][0]["closed"] is True
              and before == after and wired)
        if not ok:
            print("  measured: ascii=%r net=%r law=%r imported=%r "
                  "patched=%r writes=%r wired=%r"
                  % (ascii_only, no_net, no_second_row_law(source), imported,
                     patched, before == after, wired), flush=True)
        check(ok, "AC-SLC6 pure, imported row law, wired, zero writes")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def no_second_row_law(source):
    """True when the module carries no row predicate of its own."""
    return "startswith(\"- [x]\")" not in source


def main():
    print("stamp_locator suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_slc1()
    ac_slc2()
    ac_slc3()
    ac_slc4()
    ac_slc5()
    ac_slc6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())