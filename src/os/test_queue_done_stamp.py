"""queue_done_stamp suite (R2278; criteria AC-QDS1..AC-QDS6 were
pre-registered inside the R2255 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the trace from a delivered row back to the window that
closed it is a reading, not prose. Every accepted stamp form resolves to a
window, a date alone does not (several rounds share a day), an unstamped
closed row is debt, and a stamp that predates the round the row was opened
in is refused with BOTH rounds named.

The row law is imported from queue_floor, so a row is still decided in
exactly one place, and the suite proves it by patching is_done_row and
watching the reading move.

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
import queue_done_stamp as QD  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_done_stamp.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-done-stamp"

HEADER = ("# queue test world\n\n"
          "prose that mentions - [x] a done row and never becomes a row\n\n")

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
    world = tempfile.mkdtemp(prefix="bigdomain-qds-")
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


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(world):
    parts = []
    for base, _dirs, files in os.walk(world):
        for leaf in sorted(files):
            path = os.path.join(base, leaf)
            with open(path, "rb") as handle:
                parts.append((os.path.relpath(path, world).replace(os.sep,
                                                                   "/"),
                              len(handle.read())))
    return tuple(sorted(parts))


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def statuses(report):
    return [item["status"] for item in report["violations"]]


def ac_qds1():
    """Every accepted stamp form resolves; a date alone does not."""
    tech = ("- [x] [done 2026-10-31 R2276] a delivered row\n"
            "- [x] [done R2270] a window-only row\n"
            "- [x] [claimed+done 2026-10-29 R2231] a claimed row\n"
            "- [x] [negative 2026-10-29 R2231] a refused row\n"
            "- [x] [closed R2200] a closed row\n"
            "- [x] [done 2026-10-31] a date-only row\n"
            "- [x] [done] an empty bracket row\n"
            "- [x] [done nothing useful here] a shape-less row\n")
    world = make_world(tech)
    try:
        report = QD.audit_root(world)
        cli = run_cli(["--check", "--root", world])
    finally:
        drop_world(world)
    forms = [QD.parse_stamp(line)["form"] for line in tech.split("\n")
             if line.startswith("- [x]")]
    got = statuses(report)
    ok = (forms == ["DATE+ROUND", "ROUND", "DATE+ROUND", "DATE+ROUND",
                    "ROUND", "DATE", "BAD", "BAD"]
          and got == ["DATE-ONLY", "BAD-STAMP", "BAD-STAMP"]
          and report["stamped_rows"] == 8
          and report["ok_rows"] == 5
          and report["date_only_rows"] == 1
          and report["bad_stamp_rows"] == 2
          and report["verdict"] == "DONE-STAMP-DEBT"
          and cli[0] == 2)
    if not ok:
        print("  measured: forms=%r got=%r %r" % (forms, got, report),
              flush=True)
    check(ok, "AC-QDS1 stamp forms resolve, a date alone is debt")


def ac_qds2():
    """An unstamped closed row is debt, and the counts reconcile."""
    tech = (HEADER
            + "- [x] a delivered row with no stamp at all\n"
            + "- [x] [done 2026-10-31 R2276] a stamped row\n"
            + "- [ ] an open row is not this gate business\n")
    world = make_world(tech)
    try:
        report = QD.audit_root(world)
        cli = run_cli(["--check", "--root", world])
    finally:
        drop_world(world)
    ok = (report["done_rows"] == 2
          and report["stamped_rows"] == 1
          and report["unstamped_rows"] == 1
          and report["ok_rows"] == 1
          and report["violation_count"] == 1
          and report["violation_count"] == (report["unstamped_rows"]
                                            + report["bad_stamp_rows"]
                                            + report["date_only_rows"]
                                            + report["before_seed_rows"])
          and report["violations"][0]["status"] == "UNSTAMPED"
          and report["violations"][0]["line"] == 5
          and report["verdict"] == "DONE-STAMP-DEBT"
          and cli[0] == 2 and "UNSTAMPED" in cli[1])
    if not ok:
        print("  measured: %r %r" % (report, cli), flush=True)
    check(ok, "AC-QDS2 unstamped done row is debt, counts reconcile")


def ac_qds3():
    """A stamp older than the row own seed round is refused, both named."""
    tech = (HEADER
            + "- [x] [done 2026-10-31 R2250] R2260 first item: too early\n"
            + "- [x] [done 2026-10-31 R2260] R2260 first item: on time\n"
            + "- [x] [done 2026-10-31 R2280] R2260 first item: later is fine\n"
            + "- [x] [done 2026-10-31 R2276] a row that names no round\n")
    world = make_world(tech)
    try:
        report = QD.audit_root(world)
        cli = run_cli(["--check", "--root", world])
        text = QD.render(report)
    finally:
        drop_world(world)
    bad = report["violations"]
    ok = (report["before_seed_rows"] == 1
          and len(bad) == 1
          and bad[0]["status"] == "STAMP-BEFORE-SEED"
          and bad[0]["round"] == 2250
          and bad[0]["seed_round"] == 2260
          and bad[0]["line"] == 5
          and report["ok_rows"] == 3
          and cli[0] == 2
          and "round=R2250" in text and "seed=R2260" in text)
    if not ok:
        print("  measured: %r %r" % (report, text), flush=True)
    check(ok, "AC-QDS3 stamp before its own seed round refused")


def ac_qds4():
    """The report carries file and a 1-based line that really is the row."""
    tech = HEADER + "- [x] first unstamped row\n- [x] second unstamped row\n"
    world = make_world(tech)
    try:
        report = QD.audit_root(world)
        path = os.path.join(world, "state", "queue", "tech.md")
        with io.open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().split("\n")
        located = []
        for item in report["violations"]:
            number = item["line"]
            located.append((item["file"], 0 < number <= len(lines),
                            lines[number - 1].startswith("- [x]")))
        text = QD.render(report)
    finally:
        drop_world(world)
    ok = (len(report["violations"]) == 2
          and all(entry[0] == "state/queue/tech.md" for entry in located)
          and all(entry[1] and entry[2] for entry in located)
          and [entry[0] for entry in located] == ["state/queue/tech.md"] * 2
          and [item["line"] for item in report["violations"]] == [5, 6]
          and "state/queue/tech.md:5" in text
          and report["violations"][0]["excerpt"].startswith("- [x] first"))
    if not ok:
        print("  measured: %r %r" % (report, located), flush=True)
    check(ok, "AC-QDS4 file and line point at the real row")


def ac_qds5():
    """An empty queue is an honest zero and an absent one is honest too."""
    world = make_world(HEADER)
    absent = make_world(HEADER, drop=("explore",))
    try:
        empty = QD.audit_root(world)
        gone = QD.audit_root(absent)
        cli = run_cli(["--check", "--root", absent])
    finally:
        drop_world(world)
        drop_world(absent)
    ok = (empty["done_rows"] == 0 and empty["violation_count"] == 0
          and empty["verdict"] == "DONE-STAMP-CLEAN"
          and [row["status"] for row in empty["queues"]] == ["EMPTY"] * 3
          and gone["missing"] == ["explore"]
          and gone["violation_count"] == 0
          and [row["status"] for row in gone["queues"]]
          == ["EMPTY", "EMPTY", "MISSING"]
          and gone["queues"][2]["done_rows"] == 0
          and cli[0] == 3
          # a missing queue never invents debt and never reads clean
          and gone["verdict"] == "DONE-STAMP-CLEAN"
          and "missing=explore" in cli[1])
    if not ok:
        print("  measured: %r %r %r" % (empty, gone, cli), flush=True)
    check(ok, "AC-QDS5 honest empty and honest absent")


def ac_qds6():
    """Purity, ASCII, no clock, no network, wiring, and the row law imported."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_only = True
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "import asyncio", "urlopen", "time.time",
               "datetime")
    no_net = not any(token in text for token in blocked)
    no_second_row_law = (not any(token in text for token in
                                 ("is_open_row", "OPEN_RE", "DONE_RE")))
    imported = QD.QF is QF
    world = make_world("- [x] a row the law will be told is not done\n")
    saved = QF.is_done_row
    try:
        QF.is_done_row = lambda line: False
        patched = QD.audit_root(world)
    finally:
        QF.is_done_row = saved
    digest_before = digest_tree(world)
    try:
        live_report = QD.audit_root(world)
    finally:
        digest_after = digest_tree(world)
        drop_world(world)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_queue_done_stamp.py" in wiring) \
        and ('"test_queue_done_stamp.py"), %d)' % EXPECTED_CRITERIA in wiring)
    ok = (ascii_only and no_net and no_second_row_law and imported
          # a patched row law flows straight through: nothing is a done row
          and patched["done_rows"] == 0
          and patched["verdict"] == "DONE-STAMP-CLEAN"
          # and the reader writes nothing at all
          and live_report["violation_count"] == 1
          and digest_before == digest_after
          and wired)
    if not ok:
        print("  measured: ascii=%r net=%r law=%r imported=%r patched=%r "
              "writes=%r wired=%r"
              % (ascii_only, no_net, no_second_row_law, imported, patched,
                 digest_before == digest_after, wired), flush=True)
    check(ok, "AC-QDS6 pure, imported row law, wired, zero writes")


def main():
    print("queue_done_stamp suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_qds1()
    ac_qds2()
    ac_qds3()
    ac_qds4()
    ac_qds5()
    ac_qds6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())