"""queue_floor_delivered_wire suite (R2365; criteria AC-FDW1..AC-FDW6 were
pre-registered in state/queue/tech.md line 411 at R2354 BEFORE this code).

What this proves: the floor gauge finally asks the occupancy reading, so a
row whose module and suite already shipped is DISCOUNTED from standing
supply and NAMED with its line and prefix, while every count queue_floor
already publishes stays byte-identical for the same file. A queue whose
claimable rows are all delivered reads FLOOR-DEBT with a shortfall equal to
the whole floor instead of a met floor over shipped rows, a queue with no
prefixed row keeps exactly queue_floor's reading, and the CLI speaks 0/2/3
with a byte-stable JSON over pinned keys.

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

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_floor_delivered_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-floor-delivered-wire"

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


def seed(name, prefix, crumb="R9001"):
    """A claimable seed row naming one module and its criteria prefix."""
    return row("%s P2 seed: src/os/%s.py - fixture work. Criteria prefix "
               "%s1..%s6 pre-registered." % (crumb, name, prefix, prefix))


def make_world(tech_rows, modules=(), tests=(), main_rows=None,
               explore_rows=None):
    """A temp root with the three queue files queue_floor requires."""
    world = tempfile.mkdtemp(prefix="bigdomain-fdw-")
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


def reading(rows, prefixed=None, claimable=None, delivered=None):
    """A hand-built occupancy reading: the shape queue_occupancy returns."""
    if prefixed is None:
        prefixed = len(rows)
    if claimable is None:
        claimable = len(rows)
    if delivered is None:
        delivered = len([r for r in rows
                         if r["status"] == QOC.STATUS_DELIVERED])
    return {
        "queue": "tech",
        "path": "state/queue/tech.md",
        "present": True,
        "rows": rows,
        "head": None,
        "claimable_rows": claimable,
        "prefixed_rows": prefixed,
        "delivered_rows": delivered,
        "stale_delivered": 0,
        "gated_rows": 0,
        "verdict": QOC.VERDICT_NO_HEAD,
    }


def scan_row(line, prefix, status, modules=()):
    return {"line": line, "prefix": prefix, "modules": list(modules),
            "signals": [], "missing": [], "status": status,
            "excerpt": "fixture"}


def ac1():
    """The occupancy reading is queue_occupancy's, not a second scan."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_scan = ("MODULE_RE" not in source
               and "os.path.exists" not in source
               and "src/os/" not in source)
    delivered = scan_row(1, "AC-FDWA", QOC.STATUS_DELIVERED, ["alpha"])
    world = make_world([row("loose work with no prefix and no module")])
    base = FDW.gauge(world)
    original = QOC.audit_text
    try:
        QOC.audit_text = lambda root, name, rel, text: reading([delivered])
        patched = FDW.gauge(world)
    finally:
        QOC.audit_text = original
    base_tech = [r for r in base["queues"] if r["queue"] == "tech"][0]
    patched_tech = [r for r in patched["queues"] if r["queue"] == "tech"][0]
    check(no_scan
          and base_tech["discounted"] == 0
          and patched_tech["discounted"] == 1
          and patched_tech["delivered"] == [{"line": 1, "prefix": "AC-FDWA"}]
          and patched_tech["claimable_effective"] == base_tech["claimable"] - 1,
          "AC-FDW1 occupancy is imported from queue_occupancy and patching "
          "its reader moves the gauge")


def ac2():
    """A delivered row is discounted; the published counts stay identical."""
    text = (seed("alpha", "AC-FDWC") + seed("beta", "AC-FDWD")
            + seed("gamma", "AC-FDWE"))
    counts = QF.count_rows(text)
    shipped = scan_row(1, "AC-FDWC", QOC.STATUS_DELIVERED, ["alpha"])
    pending = scan_row(2, "AC-FDWD", QOC.STATUS_CLAIMABLE, ["beta"])
    wired = FDW.queue_row("tech", "state/queue/tech.md", True, counts, 2,
                          reading([shipped, pending]))
    base = QF.queue_row("tech", "state/queue/tech.md", True, counts, 2)
    same = all(wired[key] == base[key] for key in QF.QUEUE_KEYS
               if key not in ("shortfall", "status"))
    check(same
          and wired["claimable"] == 3
          and wired["claimable_effective"] == 2
          and wired["discounted"] == 1
          and wired["shortfall"] == 0
          and wired["status"] == "MET",
          "AC-FDW2 a DELIVERED row is discounted while open/done/gated/"
          "claimable stay byte-identical")


def ac3():
    """Every claimable row delivered: FLOOR-DEBT for the whole floor."""
    all_shipped = reading([
        scan_row(3, "AC-FDWF", QOC.STATUS_DELIVERED, ["alpha"]),
        scan_row(4, "AC-FDWG", QOC.STATUS_DELIVERED, ["beta"]),
    ], claimable=2)
    counts = {"open_rows": 2, "done_rows": 0, "gated_rows": 0,
              "claimable": 2}
    row_full = FDW.queue_row("tech", "state/queue/tech.md", True, counts, 10,
                             all_shipped)
    report = FDW.gauge(make_world([seed("alpha", "AC-FDWF"),
                                   seed("beta", "AC-FDWG")],
                                  modules=["alpha", "beta"],
                                  tests=["alpha", "beta"]))
    tech = [r for r in report["queues"] if r["queue"] == "tech"][0]
    check(row_full["claimable_effective"] == 0
          and row_full["shortfall"] == 10
          and row_full["status"] == "SHORT"
          and [i["prefix"] for i in row_full["delivered"]]
          == ["AC-FDWF", "AC-FDWG"]
          and tech["claimable_effective"] == 0
          and report["verdict"] == "FLOOR-DEBT"
          and report["delivered_total"] == 2,
          "AC-FDW3 an all-delivered queue reads FLOOR-DEBT with the whole "
          "floor as shortfall and the rows named")


def ac4():
    """No prefixed row at all: exactly queue_floor's reading, no discount."""
    text = (row("loose note without a prefix") +
            row("another loose note, still no module"))
    counts = QF.count_rows(text)
    base = QF.queue_row("main", "state/queue/main.md", True, counts, 2)
    wired = FDW.queue_row("main", "state/queue/main.md", True, counts, 2,
                          reading([], prefixed=0, claimable=2, delivered=0))
    same = all(wired[key] == base[key] for key in QF.QUEUE_KEYS)
    check(same
          and wired["discounted"] == 0
          and wired["claimable_effective"] == wired["claimable"] == 2
          and wired["status"] == "MET",
          "AC-FDW4 a queue with no prefixed row keeps queue_floor's reading "
          "exactly")


def ac5():
    """CLI codes 0/2/3 and a byte-stable JSON over the pinned keys."""
    cli = os.path.join(BASE, "queue_floor_delivered_wire.py")
    met = make_world([row("loose tech work %d" % i) for i in range(10)],
                     main_rows=[row("loose main work %d" % i)
                                for i in range(5)],
                     explore_rows=[row("loose explore work %d" % i)
                                   for i in range(10)])
    short = make_world([row("one loose tech row")])
    codes = {}
    for name, argv in (
            ("met", ["--check", "--root", met]),
            ("short", ["--check", "--root", short]),
            ("missing", ["--check", "--root",
                         os.path.join(met, "nope")]),
            ("badflags", ["--frobnicate"]),
    ):
        proc = subprocess.run([sys.executable, cli] + argv,
                              capture_output=True)
        codes[name] = proc.returncode
    first = subprocess.run([sys.executable, cli, "--check", "--root", met,
                            "--json"], capture_output=True)
    second = subprocess.run([sys.executable, cli, "--check", "--root", met,
                             "--json"], capture_output=True)
    payload = json.loads(first.stdout.decode("utf-8"))
    keys_ok = tuple(payload.keys()) == FDW.REPORT_KEYS
    check(codes["met"] == 0 and codes["short"] == 2
          and codes["missing"] == 3 and codes["badflags"] == 2
          and first.stdout == second.stdout and keys_ok
          and payload["verdict"] == "FLOOR-MET",
          "AC-FDW5 CLI 0/2/3 and a byte-stable JSON over pinned keys")


def ac6():
    """ASCII source, stdlib only, no clock, no network, wired label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = True
    try:
        source.encode("ascii")
    except (UnicodeEncodeError, UnicodeDecodeError):
        ascii_only = False
    forbidden = ("import time", "import datetime", "from time",
                 "urllib", "socket", "requests", "http.client")
    clean = [token for token in forbidden if token in source]
    third_party = [token for token in ("numpy", "pandas", "yaml")
                   if ("import " + token) in source]
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL) in runner
    check(ascii_only and clean == [] and third_party == [] and wired,
          "AC-FDW6 pure ASCII, stdlib only, no clock, no network, wired")


def main():
    print("queue_floor_delivered_wire suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    for test in (ac1, ac2, ac3, ac4, ac5, ac6):
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - a crash is a red criterion
            check(False, "%s raised %r" % (test.__name__, exc))
    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                              PASSES, PASSES + FAILS), flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())