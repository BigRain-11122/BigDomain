"""Queue-floor gauge suite (R2244; criteria AC-QF1..AC-QF8 were
pre-registered in state/queue/tech.md as the R2240-a seed BEFORE this
code existed - honesty law).

What this proves: the standing-line floors (main >= 5, tech >= 10,
explore >= 10) are measured instead of eyeballed, and the measurement
is narrow in the ways that matter. A row is a row only when it starts at
column 0 with "- [ ]" or "- [x]"; a row that waits on an outside party
is reported but is never claimable, so a queue of pure gates reads as
debt rather than as stock. An empty queue is an honest zero (shortfall
equals the whole floor), a missing queue file fails closed, and the
gauge never writes anything.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import io
import json
import os
import re
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import queue_floor as QF  # noqa: E402

EXPECTED_CRITERIA = 8
MODULE = os.path.join(BASE, "queue_floor.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-floor"

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


def make_world(main_text, tech_text, explore_text):
    world = tempfile.mkdtemp(prefix="bigdomain-qf-")
    os.makedirs(os.path.join(world, "state", "queue"))
    with io.open(os.path.join(world, "state", "queue", "main.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(main_text)
    with io.open(os.path.join(world, "state", "queue", "tech.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(tech_text)
    with io.open(os.path.join(world, "state", "queue", "explore.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(explore_text)
    return world


def drop_world(world):
    queue_dir = os.path.join(world, "state", "queue")
    for leaf in os.listdir(queue_dir):
        os.unlink(os.path.join(queue_dir, leaf))
    os.rmdir(queue_dir)
    os.rmdir(os.path.join(world, "state"))
    os.rmdir(world)


def digest_tree(world):
    parts = []
    queue_dir = os.path.join(world, "state", "queue")
    for leaf in sorted(os.listdir(queue_dir)):
        path = os.path.join(queue_dir, leaf)
        with open(path, "rb") as handle:
            parts.append(("state/queue/" + leaf, len(handle.read())))
    return tuple(parts)


def run_cli(args, cwd=REPO):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=cwd)
    return (proc.returncode, proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def rows(count):
    return "".join("- [ ] open row number %d\n" % index
                   for index in range(1, count + 1))


def run():
    # AC-QF1: closed report shape, pinned row keys, deterministic.
    world = make_world(rows(5), rows(10), rows(10))
    try:
        first = QF.gauge(world)
        second = QF.gauge(world)
        keys_ok = sorted(first.keys()) == sorted(QF.REPORT_KEYS)
        row_keys_ok = all(sorted(row.keys()) == sorted(QF.QUEUE_KEYS)
                          for row in first["queues"])
        check(keys_ok and row_keys_ok and first == second
              and first["verdict"] in QF.VERDICTS
              and first["verdict"] == "FLOOR-MET"
              and first["shortfall_total"] == 0,
              "AC-QF1 report and row keys pinned, deterministic, "
              "verdict in the closed set")
    finally:
        drop_world(world)

    # AC-QF2: the row law is column-0 and marker exact.
    sample = "\n".join([
        "- [ ] a real open row",
        "- [x] a done row",
        "- [X] another done row",
        "  - [ ] indented continuation is not a row",
        "prose that mentions - [ ] in the middle is not a row",
        "| - [ ] column | value |",
        "- [ ]a row with no space after the box is not a row",
        "- [~] an unknown box is not a row",
        "- [ ] a second real open row",
    ])
    counts = QF.count_rows(sample)
    check(counts["open_rows"] == 2 and counts["done_rows"] == 2
          and counts["gated_rows"] == 0 and counts["claimable"] == 2,
          "AC-QF2 only column-0 boxed rows count, exact box letters only")

    # AC-QF3: gated rows are reported but never claimable.
    gated_text = "\n".join([
        "- [ ] free row",
        "- [ ] row [needs-CEO] a pricing decision waits",
        "- [ ] row blocked on CEO physical item",
        "- [ ] row GATED ON a group handoff",
        "- [ ] row blocked-on-CEO merchant number",
        "- [ ] row blocked on merchant account",
        "- [ ] row gated: settlement",
        "- [ ] row blocked on physical hardware",
    ])
    gated_counts = QF.count_rows(gated_text)
    check(gated_counts["open_rows"] == 8 and gated_counts["gated_rows"] == 7
          and gated_counts["claimable"] == 1,
          "AC-QF3 seven gate marker forms excluded from claimable, "
          "still counted as open")

    # AC-QF4: the floor table is exactly the standing-line law.
    floors = dict(QF.FLOORS)
    world = make_world(rows(4), rows(7), rows(12))
    try:
        report = QF.gauge(world)
        by_name = {}
        for row in report["queues"]:
            by_name[row["queue"]] = row
        check(floors == {"main": 5, "tech": 10, "explore": 10}
              and by_name["main"]["shortfall"] == 1
              and by_name["tech"]["shortfall"] == 3
              and by_name["explore"]["shortfall"] == 0
              and by_name["explore"]["status"] == "MET"
              and by_name["main"]["status"] == "SHORT"
              and report["shortfall_total"] == 4
              and report["verdict"] == "FLOOR-DEBT",
              "AC-QF4 floors pinned to 5/10/10, shortfall clamps at zero, "
              "total sums the queues")
    finally:
        drop_world(world)

    # AC-QF5: an empty queue is an honest zero, a missing file is MISSING.
    world = make_world("", "\n# header only\n", "\n\n")
    try:
        zero = QF.gauge(world)
        zero_main = zero["queues"][0]
        zero_ok = (zero_main["open_rows"] == 0
                   and zero_main["claimable"] == 0
                   and zero_main["shortfall"] == 5
                   and zero_main["status"] == "SHORT"
                   and zero["verdict"] == "FLOOR-DEBT"
                   and zero["missing"] == [])
    finally:
        drop_world(world)
    world = make_world(rows(5), rows(10), rows(10))
    try:
        os.unlink(os.path.join(world, "state", "queue", "explore.md"))
        absent = QF.gauge(world)
        by_name = {}
        for row in absent["queues"]:
            by_name[row["queue"]] = row
        missing_ok = (absent["missing"] == ["explore"]
                      and by_name["explore"]["status"] == "MISSING"
                      and by_name["explore"]["present"] is False
                      and by_name["explore"]["shortfall"] == 10
                      and absent["verdict"] == "FLOOR-DEBT")
    finally:
        drop_world(world)
    check(zero_ok and missing_ok,
          "AC-QF5 empty queue reads an honest zero, absent queue reads "
          "MISSING with the whole floor as shortfall")

    # AC-QF6: CLI exit codes and a stable JSON face.
    world = make_world(rows(5), rows(10), rows(10))
    world_short = make_world(rows(1), rows(2), rows(3))
    world_gone = make_world(rows(5), rows(10), rows(10))
    os.unlink(os.path.join(world_gone, "state", "queue", "main.md"))
    try:
        met_code, met_out, _ = run_cli(["--check", "--root", world])
        short_code, _, _ = run_cli(["--check", "--root", world_short])
        gone_code, _, _ = run_cli(["--check", "--root", world_gone])
        bad_code, _, _ = run_cli(["--check", "--root", world, "--wat"])
        noarg_code, _, _ = run_cli(["--check", "--root"])
        help_code, help_out, _ = run_cli(["--help"])
        json_code, json_a, _ = run_cli(["--check", "--root", world,
                                        "--json"])
        _, json_b, _ = run_cli(["--check", "--root", world, "--json"])
        parsed = json.loads(json_a)
        check(met_code == 0 and short_code == 2 and gone_code == 3
              and bad_code == 2 and noarg_code == 2
              and help_code == 0 and usage_ok(help_out)
              and json_code == 0
              and sorted(parsed.keys()) == sorted(QF.REPORT_KEYS)
              and json_a == json_b and json_a.endswith("\n"),
              "AC-QF6 CLI exits 0/2/3 on met/short/missing, bad flags "
              "exit 2, JSON parses and is byte-stable")
    finally:
        drop_world(world)
        drop_world(world_short)
        drop_world(world_gone)

    # AC-QF7: one line, and the live tree agrees with an independent count.
    world = make_world(rows(3), rows(9), rows(11))
    try:
        line = QF.one_line(QF.gauge(world))
    finally:
        drop_world(world)
    live = QF.gauge(REPO)
    independent = independent_counts(REPO)
    live_ok = True
    for row in live["queues"]:
        expected = independent[row["queue"]]
        if (row["open_rows"], row["claimable"]) != expected:
            live_ok = False
    check(line == ("QUEUE FLOOR main=3/5 tech=9/10 explore=11/10 "
                   "verdict=FLOOR-DEBT shortfall=3") and live_ok,
          "AC-QF7 one line carries every queue, live tree matches an "
          "independent recount")

    # AC-QF8: purity, ASCII source, no network import, wired into the
    # battery with the pinned criteria count.
    world = make_world(rows(2), rows(4), rows(6))
    try:
        before = digest_tree(world)
        QF.gauge(world)
        QF.one_line(QF.gauge(world))
        QF.to_json(QF.gauge(world))
        after = digest_tree(world)
    finally:
        drop_world(world)
    with io.open(MODULE, "r", encoding="ascii") as handle:
        source = handle.read()
    net = re.findall(r"^\s*(?:import|from)\s+"
                     r"(socket|ssl|urllib|http|requests|ftplib)\b",
                     source, re.M)
    wired = wiring_ok()
    check(before == after and not net and wired,
          "AC-QF8 gauge is a pure read, source ASCII with zero network "
          "imports and wired as os-queue-floor(8)")


def usage_ok(text):
    return "usage: queue_floor.py" in text and "--check" in text


def independent_counts(root):
    """Recount the three live files with different code than the module."""
    out = {}
    for name, rel in (("main", os.path.join("state", "queue", "main.md")),
                      ("tech", os.path.join("state", "queue", "tech.md")),
                      ("explore", os.path.join("state", "queue",
                                               "explore.md"))):
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            out[name] = (0, 0)
            continue
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        opened = 0
        claimable = 0
        for line in text.splitlines():
            if not line.startswith("- [ ]"):
                continue
            opened += 1
            low = line.lower()
            blocked = False
            for marker in ("[needs-ceo]", "needs-ceo", "blocked on ceo",
                           "blocked-on-ceo", "blocked on physical",
                           "gated on", "gated:", "blocked on merchant"):
                if marker in low:
                    blocked = True
            if not blocked:
                claimable += 1
        out[name] = (opened, claimable)
    return out


def wiring_ok():
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        text = handle.read()
    needle = '"%s"' % LABEL
    if needle not in text:
        return False
    tail = text[text.find(needle):]
    window = tail[:400]
    return ("test_queue_floor.py" in window) and (", 8)" in window)


if __name__ == "__main__":
    run()
    print("SUITE %s %d/%d" % (
        "PASS" if FAILS == 0 else "FAIL", PASSES + FAILS, EXPECTED_CRITERIA),
        flush=True)
    sys.exit(0 if FAILS == 0 else 2)