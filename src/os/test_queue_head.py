"""queue_head suite (R2270; criteria AC-QHD1..AC-QHD6 were pre-registered
inside the R2267 seed row of state/queue/tech.md BEFORE this code existed).

What this proves: which queue row comes first is a reading, not a memory.
queue_floor counts claimable rows and queue_row gates their prefix, but
neither answers WHICH one is the head. Both laws are imported here rather
than rewritten - the gate marker table is read at call time from
queue_floor (AC-QHD2) and the criteria-prefix decision is queue_row's own
function (AC-QHD3), so a patched law flows straight through and the suite
proves it by patching each one in turn.

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
import queue_head as QH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_head.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-head"

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


def make_world(body):
    """Build a temp root with one tech queue file."""
    world = tempfile.mkdtemp(prefix="bigdomain-qhd-")
    state = os.path.join(world, "state", "queue")
    os.makedirs(state)
    path = os.path.join(state, "tech.md")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
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


def ac_qhd1():
    """The head is the first claimable open row in file order."""
    body = (HEADER
            + "- [ ] blocked on CEO physical item (Criteria prefix AC-GG)\n"
            + "- [ ] bare row without criteria\n"
            + "- [ ] the real head (Criteria prefix AC-HH)\n"
            + "- [ ] a later row (Criteria AC-II1..6)\n"
            + "- [x] a done row (Criteria prefix AC-JJ)\n")
    report = QH.head_text("tech", "state/queue/tech.md", body)
    ok = (report["verdict"] == "HEAD"
          and report["head"] is not None
          and report["head"]["line"] == 7
          and report["head"]["prefix"] == "AC-HH"
          and report["head"]["text"].startswith("- [ ] the real head")
          and report["skipped_before"] == 2
          and report["open_rows"] == 4
          and report["claimable_rows"] == 3
          and report["prefixed_rows"] == 2
          and report["done_rows"] == 1)
    if not ok:
        print("  measured: %r" % (report,), flush=True)
    check(ok, "AC-QHD1 head is first claimable prefixed row, file order")


def ac_qhd2():
    """Gated rows are skipped BY MARKER, and the marker table is queue_floor's."""
    body = (HEADER
            + "- [ ] gated on a group handoff (Criteria prefix AC-KK)\n"
            + "- [ ] plain head (Criteria prefix AC-LL)\n")
    report = QH.head_text("tech", "state/queue/tech.md", body)
    first = report["skipped"][0] if report["skipped"] else {}
    imported = QH.QF is QF
    saved = QF.GATED_MARKERS
    try:
        QF.GATED_MARKERS = ("zebra-hold",)
        patched_body = (HEADER
                        + "- [ ] zebra-hold row (Criteria prefix AC-MM)\n"
                        + "- [ ] gated on a group handoff (Criteria prefix AC-NN)\n")
        patched = QH.head_text("tech", "state/queue/tech.md", patched_body)
    finally:
        QF.GATED_MARKERS = saved
    ok = (imported
          and report["verdict"] == "HEAD"
          and first.get("reason") == "GATED"
          and first.get("detail") == "gated on"
          and report["gated_rows"] == 1
          # with the patched table the zebra row gates and the old word does not
          and patched["gated_rows"] == 1
          and patched["head"]["prefix"] == "AC-NN"
          and patched["skipped"][0]["detail"] == "zebra-hold")
    if not ok:
        print("  measured: first=%r patched=%r" % (first, patched), flush=True)
    check(ok, "AC-QHD2 gate marker law imported from queue_floor")


def ac_qhd3():
    """A claimable row with no criteria prefix reads SKIPPED-NO-CRITERIA."""
    body = (HEADER
            + "- [ ] bare row one\n"
            + "- [ ] the head (Criteria prefix AC-OO)\n")
    report = QH.head_text("tech", "state/queue/tech.md", body)
    bare = report["skipped"][0] if report["skipped"] else {}
    imported = QH.QR is QR
    saved = QR.scan_row
    try:
        QR.scan_row = lambda text: {"prefixed": False, "form": None,
                                    "prefix": None}
        patched = QH.head_text("tech", "state/queue/tech.md", body)
    finally:
        QR.scan_row = saved
    ok = (imported
          and bare.get("reason") == "NO-CRITERIA"
          and bare.get("line") == 5
          and bare.get("detail") is None
          and report["head"]["prefix"] == "AC-OO"
          # with the patched decision every claimable row loses its prefix
          and patched["verdict"] == "NO-HEAD"
          and patched["prefixed_rows"] == 0
          and len(patched["skipped"]) == 2)
    if not ok:
        print("  measured: bare=%r patched=%r" % (bare, patched), flush=True)
    check(ok, "AC-QHD3 criteria law imported from queue_row, refusals named")


def ac_qhd4():
    """Done rows never offered, order never sorted, empty queue reads NO-HEAD."""
    body = (HEADER
            + "- [x] done one (Criteria prefix AC-PP)\n"
            + "- [x] done two (Criteria prefix AC-QQ)\n")
    report = QH.head_text("tech", "state/queue/tech.md", body)
    empty = QH.head_text("tech", "state/queue/tech.md", HEADER)
    two = QH.head_text("tech", "state/queue/tech.md",
                       HEADER
                       + "- [ ] second in file (Criteria prefix AC-RR)\n"
                       + "- [x] done between (Criteria prefix AC-SS)\n"
                       + "- [ ] third in file (Criteria prefix AC-TT)\n")
    ok = (report["verdict"] == "NO-HEAD" and report["head"] is None
          and report["done_rows"] == 2 and report["open_rows"] == 0
          and empty["verdict"] == "NO-HEAD" and empty["skipped"] == []
          and two["head"]["line"] == 5
          and two["head"]["prefix"] == "AC-RR"
          and two["skipped"][0]["reason"] == "BEHIND-HEAD"
          and two["skipped"][0]["detail"] == 5)
    check(ok, "AC-QHD4 done rows never offered, NO-HEAD honest, no sorting")


def ac_qhd5():
    """CLI codes 0/2/3/5, --json pinned and byte-stable, nothing written."""
    world = make_world(HEADER + "- [ ] the head (Criteria prefix AC-UU)\n")
    none = make_world(HEADER + "- [x] only done (Criteria prefix AC-VV)\n")
    gone = make_world(HEADER)
    os.remove(os.path.join(gone, "state", "queue", "tech.md"))
    before = digest_tree(world)
    try:
        found = run_cli(["--head", "tech", "--root", world])
        headless = run_cli(["--head", "tech", "--root", none])
        missing = run_cli(["--head", "tech", "--root", gone])
        first = run_cli(["--head", "tech", "--root", world, "--json"])
        second = run_cli(["--head", "tech", "--root", world, "--json"])
        no_op = run_cli(["--json"])
        unknown_flag = run_cli(["--head", "--nonsense"])
        unknown_queue = run_cli(["--head", "nope", "--root", world])
        after = digest_tree(world)
    finally:
        drop_world(world)
        drop_world(none)
        drop_world(gone)
    pinned = list(json.loads(first[1]).keys())
    ok = (found[0] == 0 and "line=" in found[1] and "AC-UU" in found[1]
          and headless[0] == 2 and "NO-HEAD" in headless[1]
          and missing[0] == 3 and "MISSING" in missing[1]
          and no_op[0] == 5 and unknown_flag[0] == 5
          and unknown_queue[0] == 5
          and first == second and first[0] == 0
          and pinned == list(QH.REPORT_KEYS)
          and before == after)
    if not ok:
        print("  measured: %r %r %r %r"
              % (found, headless, missing, pinned), flush=True)
    check(ok, "AC-QHD5 CLI codes 0/2/3/5, --json pinned, nothing written")


def ac_qhd6():
    """Purity, ASCII source, no network, wired, live head names a real row."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_only = True
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "import asyncio", "urlopen", "time.time")
    no_net = not any(token in text for token in blocked)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_queue_head.py" in wiring) \
        and ("os\", \"test_queue_head.py\"), 6)" in wiring)
    live = run_cli(["--head", "tech"])
    live_ok = False
    if live[0] == 0:
        line_no = None
        prefix = None
        for part in live[1].split():
            if part.startswith("line="):
                line_no = int(part.split("=", 1)[1])
            elif part.startswith("prefix="):
                prefix = part.split("=", 1)[1]
        if line_no is not None and prefix is not None:
            with io.open(os.path.join(REPO, "state", "queue", "tech.md"),
                         "r", encoding="utf-8") as handle:
                rows = handle.read().split("\n")
            if 0 < line_no <= len(rows):
                row = rows[line_no - 1]
                live_ok = (row.startswith("- [ ]") and prefix in row)
    ok = ascii_only and no_net and wired and live_ok
    if not ok:
        print("  measured: ascii=%r net=%r wired=%r live=%r %r"
              % (ascii_only, no_net, wired, live_ok, live), flush=True)
    check(ok, "AC-QHD6 pure ASCII, no network, wired, live head is real")


def main():
    print("queue_head suite (expected criteria %d)" % EXPECTED_CRITERIA
          , flush=True)
    ac_qhd1()
    ac_qhd2()
    ac_qhd3()
    ac_qhd4()
    ac_qhd5()
    ac_qhd6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())