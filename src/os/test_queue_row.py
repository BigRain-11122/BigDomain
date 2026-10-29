"""queue_row suite (R2253; criteria AC-QROW1..AC-QROW6 were pre-registered
in state/queue/tech.md as the R2248-b seed BEFORE this code existed).)

What this proves: a claimable open queue row must name its criteria prefix,
so pre-registration is a gate instead of a habit. The row law is NOT
rewritten here - the gate imports queue_floor's deciders (AC-QROW1), which
is also why the file name can collide with that module's function name
without a second wheel. Two declaration forms are accepted and only those
two (AC-QROW2), gated rows are exempt but still reported (AC-QROW3), every
refusal carries a file and a line (AC-QROW4), the CLI codes are pinned
(AC-QROW5) and the whole thing is a pure read (AC-QROW6).

Stdlib only, ASCII source, zero network. Exit 0 = all green.
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

import queue_floor as QF  # noqa: E402
import queue_row as QR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_row.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-row"

HEADER = ("# queue test world\n\n"
          "prose that mentions - [ ] a row law and never becomes a row\n\n")

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


def make_world(bodies):
    """Build a temp root with the three queue files; bodies map name->text."""
    world = tempfile.mkdtemp(prefix="bigdomain-qr-")
    state = os.path.join(world, "state", "queue")
    os.makedirs(state)
    for name, rel in QF.QUEUE_PATHS:
        leaf = os.path.basename(rel)
        body = bodies.get(name)
        if body is None:
            continue
        with io.open(os.path.join(state, leaf), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(body)
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


def three_good():
    return {
        "main": HEADER + "- [ ] row one (Criteria prefix AC-AAA)\n",
        "tech": HEADER + "- [ ] row two (Criteria AC-BBB1..6)\n",
        "explore": HEADER + "- [x] done row (Criteria prefix AC-CCC)\n",
    }


def ac_qrow1():
    """The row law is reused from queue_floor, not re-implemented."""
    same_open = QR.QF.is_open_row is QF.is_open_row
    same_gated = QR.QF.is_gated is QF.is_gated
    same_done = QR.QF.is_done_row is QF.is_done_row
    body = (HEADER
            + "   - [ ] indented is not a row\n"
            + "- [ ]  row with the box then two spaces (Criteria prefix AC-DD)\n"
            + "table | - [ ] | cell is not a row\n")
    row = QR.audit_text("main", "state/queue/main.md", body)
    ok = (same_open and same_gated and same_done
          and row["open_rows"] == 1 and row["claimable_rows"] == 1
          and row["done_rows"] == 0)
    check(ok, "AC-QROW1 row law reused from queue_floor, narrow row shape")


def ac_qrow2():
    """Both declaration forms pass; a bare claimable row is a violation."""
    body = (HEADER
            + "- [ ] form one (Criteria prefix AC-QQ)\n"
            + "- [ ] form two (Criteria AC-RR1..AC-RR6 pre-registered)\n"
            + "- [ ] bare row with no declaration at all\n"
            + "- [ ] marker with no token (Criteria prefix AC-)\n")
    row = QR.audit_text("tech", "state/queue/tech.md", body)
    prefixes = [b["prefix"] for b in row["violations"]]
    ok = (row["open_rows"] == 4 and row["claimable_rows"] == 4
          and row["prefixed_rows"] == 2 and row["violation_count"] == 2
          and prefixes == [None, None])
    one = QR.scan_row("- [ ] x (Criteria prefix AC-ZZ)")
    two = QR.scan_row("- [ ] x (Criteria AC-ZZ1..4)")
    bare = QR.scan_row("- [ ] x")
    ok = (ok and one["form"] == "FORM-1" and one["prefix"] == "AC-ZZ"
          and two["form"] == "FORM-2" and two["prefix"] == "AC-ZZ1"
          and bare["prefixed"] is False)
    check(ok, "AC-QROW2 two declaration forms pass, bare rows refused")


def ac_qrow3():
    """A gated row is exempt from the prefix law but still reported."""
    body = (HEADER
            + "- [ ] blocked on CEO physical item merchant number\n"
            + "- [ ] gated on the group handoff arriving\n"
            + "- [ ] claimable row without declaration\n")
    row = QR.audit_text("explore", "state/queue/explore.md", body)
    ok = (row["open_rows"] == 3 and row["gated_rows"] == 2
          and row["claimable_rows"] == 1 and row["violation_count"] == 1
          and row["violations"][0]["line"] == 7)
    check(ok, "AC-QROW3 gated rows exempt and reported, claimable refused")


def ac_qrow4():
    """Every refusal names its file and line; counts conserve."""
    world = make_world({
        "main": HEADER + "- [ ] a (Criteria prefix AC-MA)\n",
        "tech": HEADER + "- [ ] b (no criteria)\n- [ ] c (no criteria)\n",
        "explore": HEADER + "- [ ] d (Criteria prefix AC-EX)\n",
    })
    try:
        report = QR.audit_root(world)
    finally:
        drop_world(world)
    bad = report["violations"]
    ok = (report["verdict"] == "GATE-DEBT"
          and report["violation_count"] == 2
          and [b["file"] for b in bad] == ["state/queue/tech.md"] * 2
          and [b["line"] for b in bad] == [5, 6]
          and bad[0]["excerpt"].startswith("- [ ] b")
          and bad[0]["excerpt"].isascii()
          and report["open_rows"] == 4
          and report["open_rows"] == (report["claimable_rows"]
                                      + report["gated_rows"]))
    if not ok:
        print("  measured: %r" % (report,), flush=True)
    check(ok, "AC-QROW4 refusal names file and line, counts conserve")


def ac_qrow5():
    """CLI codes pinned and --json byte-stable across two runs."""
    good = make_world(three_good())
    debt = make_world({"main": HEADER + "- [ ] bare\n",
                       "tech": HEADER + "- [ ] bare\n",
                       "explore": HEADER})
    missing = make_world({"main": HEADER})
    try:
        ok_world = run_cli(["--check", "--root", good])
        bad_world = run_cli(["--check", "--root", debt])
        gone = run_cli(["--check", "--root", missing])
        first = run_cli(["--check", "--root", debt, "--json"])
        second = run_cli(["--check", "--root", debt, "--json"])
        flags = run_cli(["--json"])
        unknown = run_cli(["--check", "--nonsense"])
    finally:
        drop_world(good)
        drop_world(debt)
        drop_world(missing)
    pinned = list(json.loads(first[1]).keys())
    ok = (ok_world[0] == 0 and "GATE-PASS" in ok_world[1]
          and bad_world[0] == 2 and "GATE-DEBT" in bad_world[1]
          and gone[0] == 3
          and first == second and first[0] == 2
          and pinned == list(QR.REPORT_KEYS)
          and flags[0] == 2 and unknown[0] == 2)
    check(ok, "AC-QROW5 CLI codes 0/2/3, --json pinned and byte-stable")


def ac_qrow6():
    """Purity: no write, ASCII source, no network import, wired in."""
    world = make_world(three_good())
    before = digest_tree(world)
    try:
        run_cli(["--check", "--root", world])
        run_cli(["--check", "--root", world, "--json"])
        after = digest_tree(world)
    finally:
        drop_world(world)
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_only = True
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "import asyncio", "urlopen")
    no_net = not any(token in text for token in blocked)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_queue_row.py" in wiring) \
        and ("..\", \"os\", \"test_queue_row.py\"), 6)" in wiring)
    ok = (before == after and ascii_only and no_net and wired)
    if not ok:
        print("  measured: write=%r ascii=%r net=%r wired=%r"
              % (before == after, ascii_only, no_net, wired), flush=True)
    check(ok, "AC-QROW6 pure read, ASCII source, no network, wired")


def main():
    print("queue_row suite (expected criteria %d)" % EXPECTED_CRITERIA
          , flush=True)
    ac_qrow1()
    ac_qrow2()
    ac_qrow3()
    ac_qrow4()
    ac_qrow5()
    ac_qrow6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())