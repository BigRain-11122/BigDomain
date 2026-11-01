"""queue_floor_reading_wire suite (R2368; criteria AC-QFR1..AC-QFR6 were
pre-registered in state/queue/tech.md line 413 at R2365 BEFORE this code).

What this proves: there is now ONE published floor reading, and the number it
publishes is the DISCOUNTED number with the discounted rows travelling beside
it. The reading is queue_floor_delivered_wire's own gauge (patching it moves
this one), a queue with no discount publishes exactly queue_floor's numbers
byte for byte, and the CLI speaks 0/2/3 with a byte-stable JSON over the
pinned report keys. Pure: no clock, no writes, no network.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
sys.path.insert(0, BASE)

import queue_floor as QF  # noqa: E402
import queue_occupancy as QOC  # noqa: E402
import queue_floor_delivered_wire as FDW  # noqa: E402
import queue_floor_reading_wire as QFR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_floor_reading_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-floor-reading-wire"

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


def row(text, done=False):
    return ("- [x] %s\n" % text) if done else ("- [ ] %s\n" % text)


def plain_rows(count, tag):
    """Open rows with no prefix and no module: never discounted."""
    return [row("%s plain work item %d with no prefix and no module"
                % (tag, index))
            for index in range(count)]


def seed(name, prefix, crumb="R9001"):
    """A claimable seed row naming one module and its criteria prefix."""
    return row("%s P2 seed: src/os/%s.py - fixture work. Criteria prefix "
               "%s1..%s6 pre-registered." % (crumb, name, prefix, prefix))


def make_world(tech_rows, modules=(), tests=(), main_rows=None,
               explore_rows=None):
    """A temp root with the three queue files queue_floor requires."""
    world = tempfile.mkdtemp(prefix="bigdomain-qfr-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    bodies = {
        "tech": tech_rows,
        "main": main_rows if main_rows is not None else [],
        "explore": explore_rows if explore_rows is not None else [],
    }
    for name, rows in bodies.items():
        with io.open(os.path.join(world, "state", "queue", name + ".md"),
                     "w", encoding="utf-8", newline="\n") as handle:
            handle.write("# %s queue\n" % name + "".join(rows))
    for name in modules:
        with io.open(os.path.join(world, "src", "os", name + ".py"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write("# fixture module\n")
    for name in tests:
        with io.open(os.path.join(world, "src", "os", "test_" + name + ".py"),
                     "w", encoding="utf-8", newline="\n") as handle:
            handle.write("# fixture suite\n")
    return world


def all_met_world():
    """A world where every queue meets its floor with nothing delivered."""
    return make_world(plain_rows(10, "tech"), main_rows=plain_rows(5, "main"),
                      explore_rows=plain_rows(10, "explore"))


def source():
    return io.open(MODULE, "r", encoding="utf-8").read()


def ac1():
    """AC-QFR1 the discounted report is imported from the delivered wire."""
    text = source()
    imported = ("FDW.gauge" in text and "QF.gauge" not in text)
    world = all_met_world()
    base = QFR.published(world)
    doctored = FDW.gauge(world)
    for entry in doctored["queues"]:
        if entry["queue"] == "tech":
            entry["claimable_effective"] = entry["claimable"] - 3
            entry["discounted"] = 3
            entry["delivered"] = [{"line": 7, "prefix": "AC-DOC"},
                                  {"line": 8, "prefix": "AC-DOC"},
                                  {"line": 9, "prefix": "AC-DOC"}]
            entry["shortfall"] = entry["floor"] - entry["claimable_effective"]
            if entry["shortfall"] < 0:
                entry["shortfall"] = 0
            entry["status"] = "MET" if entry["shortfall"] == 0 else "SHORT"
    original = FDW.gauge
    try:
        FDW.gauge = lambda root: doctored
        patched = QFR.published(world)
    finally:
        FDW.gauge = original
    base_tech = [r for r in base["queues"] if r["queue"] == "tech"][0]
    patched_tech = [r for r in patched["queues"] if r["queue"] == "tech"][0]
    check(imported
          and base_tech["discounted"] == 0
          and patched_tech["discounted"] == 3
          and patched_tech["claimable"] == base_tech["claimable"] - 3,
          "AC-QFR1 the report comes from queue_floor_delivered_wire.gauge "
          "and patching it moves the published number")


def ac2():
    """AC-QFR2 the published reading names the discount and its rows."""
    world = make_world([seed("alpha", "AC-ALP")], modules=["alpha"],
                       tests=["alpha"])
    report = QFR.published(world)
    tech = [r for r in report["queues"] if r["queue"] == "tech"][0]
    # The prefix is whatever queue_occupancy reported for that row - this
    # reading never reformats it.
    audit = QOC.audit_text(world, "tech", "state/queue/tech.md",
                           QF.read_text(os.path.join(
                               world, "state", "queue", "tech.md")))
    expected = [{"line": entry["line"], "prefix": entry["prefix"]}
                for entry in audit["rows"]
                if entry["status"] == QOC.STATUS_DELIVERED]
    named = (tech["discounted"] == 1
             and tech["delivered"] == expected
             and len(tech["delivered"]) == 1
             and set(tech["delivered"][0].keys()) == {"line", "prefix"}
             and "-1" in QFR.one_line(report)
             and report["delivered_total"] == 1)
    gross_ok = tech["claimable"] + tech["discounted"] == QF.gauge(
        world)["queues"][1]["claimable"]
    check(named and gross_ok,
          "AC-QFR2 the discount count and the discounted rows (line+prefix) "
          "travel with the published number and gross reconciles")


def ac3():
    """AC-QFR3 no discount publishes exactly queue_floor's numbers."""
    world = all_met_world()
    ours = QFR.published(world)
    theirs = QF.gauge(world)
    identical = True
    for index in range(len(theirs["queues"])):
        mine = ours["queues"][index]
        ref = theirs["queues"][index]
        projected = {}
        for key in QFR.SHARED_KEYS:
            projected[key] = mine[key]
        if projected != ref:
            identical = False
        if mine["discounted"] != 0:
            identical = False
    check(identical
          and ours["verdict"] == theirs["verdict"]
          and ours["shortfall_total"] == theirs["shortfall_total"]
          and ours["missing"] == theirs["missing"],
          "AC-QFR3 a queue with nothing delivered publishes queue_floor's "
          "row byte for byte on every shared key")


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args, cwd=SRC,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac4():
    """AC-QFR4 CLI keeps 0/2/3 with a byte-stable --json over pinned keys."""
    met = all_met_world()
    debt = make_world(plain_rows(1, "tech"), main_rows=plain_rows(5, "main"),
                      explore_rows=plain_rows(10, "explore"))
    missing = make_world(plain_rows(10, "tech"))
    try:
        os.remove(os.path.join(missing, "state", "queue", "main.md"))
    except OSError:
        pass
    rc_met, out_met = run_cli(["--check", "--root", met])
    rc_json, out_json = run_cli(["--check", "--root", met, "--json"])
    rc_json2, out_json2 = run_cli(["--check", "--root", met, "--json"])
    rc_debt, _ = run_cli(["--check", "--root", debt])
    rc_bad, _ = run_cli(["--check", "--root", met, "--nope"])
    rc_missing, _ = run_cli(["--check", "--root", missing])
    order_ok = False
    if out_json.strip():
        try:
            parsed = json.loads(out_json)
            order_ok = tuple(parsed.keys()) == QFR.REPORT_KEYS
        except ValueError:
            order_ok = False
    check(rc_met == 0 and rc_json == 0 and rc_json2 == 0
          and out_json == out_json2 and order_ok
          and rc_debt == 2 and rc_bad == 2 and rc_missing == 3
          and "QUEUE FLOOR READING" in out_met,
          "AC-QFR4 CLI 0 met / 2 short or bad flags / 3 missing, JSON "
          "byte-stable in the pinned key order")


def ac5():
    """AC-QFR5 pure function of a root: two calls agree, no clock read."""
    text = source()
    no_clock = ("import time" not in text and "datetime" not in text
                and "time.time" not in text and "now()" not in text)
    world = make_world([seed("alpha", "AC-ALP")], modules=["alpha"],
                       tests=["alpha"])
    before = sorted(os.listdir(world))
    first = QFR.published(world)
    second = QFR.published(world)
    after = sorted(os.listdir(world))
    check(no_clock and first == second and before == after,
          "AC-QFR5 the reading is a pure function of the root and no clock "
          "is read")


def ac6():
    """AC-QFR6 pure ASCII, stdlib only, no network, own reconcile label."""
    text = source()
    ascii_ok = all(ord(char) < 128 for char in text)
    banned = ("socket", "urllib", "http.client", "requests", "ftplib")
    no_net = not any(token in text for token in banned)
    wired = False
    if os.path.isfile(RUNNER):
        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = ('"%s"' % LABEL) in runner and "test_queue_floor_reading_wire" \
            in runner
    check(ascii_ok and no_net and wired,
          "AC-QFR6 pure ASCII, stdlib only, zero network imports, wired as "
          "%s(6)" % LABEL)


def main():
    ac1()
    ac2()
    ac3()
    ac4()
    ac5()
    ac6()
    total = PASSES + FAILS
    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL", PASSES, total))
    if total != EXPECTED_CRITERIA:
        print("FAIL criteria count %d != %d" % (total, EXPECTED_CRITERIA))
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())