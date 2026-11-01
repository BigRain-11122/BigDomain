"""queue_occupancy suite (R2337; criteria AC-QOC1..AC-QOC6 were
pinned in the R2337 round record before this code, but not in a queue seed
row first - disclosed).

What this proves: the queue can no longer offer, as claimable work, a row
whose module and suite already shipped. The row law stays with queue_floor
and the criteria-prefix law stays with queue_row (both are patched in this
suite and the reading moves), a row is DELIVERED only when every module it
names has both its module file and its suite on disk, a head that is already
delivered is named HEAD-DELIVERED instead of HEAD-CLAIMABLE, the reading
writes nothing and reads no clock, and the CLI speaks 0/2/3/5 with a
byte-stable JSON over pinned keys.

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

import queue_floor as QF  # noqa: E402
import queue_row as QR  # noqa: E402
import queue_occupancy as QO  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_occupancy.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-occupancy"

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


def seed(name, prefix, crumb="", gated=""):
    """A claimable seed row naming one module and its criteria prefix."""
    return row("%s P2 seed: src/os/%s.py - fixture work. Criteria prefix "
               "%s1..%s6 pre-registered. %s%s"
               % (crumb or "R9001", name, prefix, prefix, gated, ""))


def make_world(rows, modules=(), tests=()):
    """A temp root with one tech queue plus the modules it may name."""
    world = tempfile.mkdtemp(prefix="bigdomain-qoc-")
    os.makedirs(os.path.join(world, "state", "queue"))
    os.makedirs(os.path.join(world, "src", "os"))
    body = "# tech queue\n" + "".join(rows)
    with io.open(os.path.join(world, "state", "queue", "tech.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    for name in modules:
        with io.open(os.path.join(world, "src", "os", name + ".py"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write("# fixture module\n")
    for name in tests:
        with io.open(os.path.join(world, "src", "os", "test_" + name + ".py"),
                     "w", encoding="utf-8", newline="\n") as handle:
            handle.write("# fixture suite\n")
    return world


def read(world):
    return QO.audit_root(world, "tech")


def ac1():
    """No second row parser: the laws are the other modules' own."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_prefix_literal = "- [ ]" not in source and "- [x]" not in source
    no_criteria_pattern = "Criteria prefix" not in source
    seed_row = row("R9002 seed: src/os/alpha.py - fixture. Criteria prefix "
                   "AC-QOCA1..AC-QOCA6 pre-registered.")
    world = make_world([seed_row])
    before = read(world)["rows"]
    # Patch queue_row's prefix law: its verdict must flow straight through.
    original_scan = QR.scan_row
    try:
        QR.scan_row = lambda text: {"prefixed": False, "form": None,
                                    "prefix": None}
        after = read(world)["rows"]
    finally:
        QR.scan_row = original_scan
    # Patch queue_floor's open-row law: the row must disappear entirely.
    original_open = QF.is_open_row
    try:
        QF.is_open_row = lambda line: False
        closed = read(world)["rows"]
    finally:
        QF.is_open_row = original_open
    check(no_prefix_literal and no_criteria_pattern
          and len(before) == 1 and after == [] and closed == [],
          "AC-QOC1 the row law and the prefix law are queue_floor's and "
          "queue_row's, not a second parser")


def ac2():
    """DELIVERED needs the module AND its suite; anything less is claimable."""
    both = row("R9003 seed: src/os/alpha.py - fixture. Criteria prefix "
               "AC-QOCB1..AC-QOCB6 pre-registered.")
    world = make_world([both])
    none_row = read(world)["rows"][0]
    module_only = make_world([both], modules=["alpha"])
    module_reading = read(module_only)["rows"][0]
    delivered = make_world([both], modules=["alpha"], tests=["alpha"])
    delivered_reading = read(delivered)["rows"][0]
    # A row naming two modules is delivered only when BOTH are complete.
    two = row("R9004 seed: src/os/alpha.py and src/os/beta.py - fixture. "
              "Criteria prefix AC-QOCC1..AC-QOCC6 pre-registered.")
    half = make_world([two], modules=["alpha", "beta"], tests=["alpha"])
    half_reading = read(half)["rows"][0]
    check(none_row["status"] == QO.STATUS_CLAIMABLE
          and none_row["missing"] == ["alpha"]
          and module_reading["status"] == QO.STATUS_CLAIMABLE
          and module_reading["missing"] == ["alpha"]
          and delivered_reading["status"] == QO.STATUS_DELIVERED
          and delivered_reading["missing"] == []
          and half_reading["status"] == QO.STATUS_CLAIMABLE
          and half_reading["missing"] == ["beta"],
          "AC-QOC2 delivered means every named module has its file and suite")


def ac3():
    """Pure read: nothing written, no clock, no network."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    forbidden = ("import time", "import datetime", "from time",
                 "urllib", "socket", "requests", "http.client")
    clean_source = [token for token in forbidden if token in source]
    world = make_world([seed("alpha", "AC-QOCD")], modules=["alpha"],
                       tests=["alpha"])
    queue_file = os.path.join(world, "state", "queue", "tech.md")
    before = io.open(queue_file, "rb").read()
    listing_before = sorted(os.listdir(os.path.join(world, "src", "os")))
    report = read(world)
    after = io.open(queue_file, "rb").read()
    listing_after = sorted(os.listdir(os.path.join(world, "src", "os")))
    check(clean_source == [] and before == after
          and listing_before == listing_after and report["present"] is True,
          "AC-QOC3 the reading writes nothing, runs no suite, reads no clock")


def ac4():
    """The verdict names a delivered head; stale_delivered counts what lags."""
    shipped = seed("alpha", "AC-QOCE")
    pending = seed("beta", "AC-QOCF", crumb="R9005")
    world_stale_head = make_world([shipped, pending], modules=["alpha"],
                                  tests=["alpha"])
    stale = read(world_stale_head)
    # A later delivered row is NOT the head: it is the existing stale count.
    world_behind = make_world([pending, shipped], modules=["alpha"],
                              tests=["alpha"])
    behind = read(world_behind)
    empty = read(make_world([row("R9006 a plain row with no criteria and no "
                                "module named at all.")]))
    gated = read(make_world([row("R9007 seed: src/os/gamma.py - fixture. "
                                "Criteria prefix AC-QOCH1..6. blocked-on-CEO.")]))
    check(stale["verdict"] == QO.VERDICT_HEAD_DELIVERED
          and stale["head"]["status"] == QO.STATUS_DELIVERED
          and stale["delivered_rows"] == 1
          and stale["stale_delivered"] == 0
          and behind["verdict"] == QO.VERDICT_HEAD_CLAIMABLE
          and behind["stale_delivered"] == 1
          and empty["verdict"] == QO.VERDICT_NO_HEAD
          and gated["verdict"] == QO.VERDICT_NO_HEAD
          and gated["claimable_rows"] == 0,
          "AC-QOC4 HEAD-DELIVERED is named, and a delivered row behind the "
          "head counts as stale")


def ac5():
    """CLI codes 0/2/3/5 and a byte-stable JSON over the pinned keys."""
    world = make_world([seed("alpha", "AC-QOCI")], modules=["alpha"],
                       tests=["alpha"])
    cli = os.path.join(BASE, "queue_occupancy.py")
    codes = {}
    for name, argv in (
            ("ok", ["--queue", "tech", "--root", world]),
            ("empty", ["--queue", "tech", "--root",
                       make_world([row("R9008 plain row, no criteria.")])]),
            ("missing", ["--queue", "tech", "--root",
                         os.path.join(world, "nope")]),
            ("badflags", ["--frobnicate"]),
    ):
        proc = subprocess.run([sys.executable, cli] + argv,
                              capture_output=True)
        codes[name] = proc.returncode
    first = subprocess.run([sys.executable, cli, "--queue", "tech", "--root",
                            world, "--json"], capture_output=True)
    second = subprocess.run([sys.executable, cli, "--queue", "tech", "--root",
                             world, "--json"], capture_output=True)
    payload = json.loads(first.stdout.decode("utf-8"))
    keys_ok = tuple(payload.keys()) == QO.REPORT_KEYS
    check(codes["ok"] == 0 and codes["empty"] == 2 and codes["missing"] == 3
          and codes["badflags"] == 5 and first.stdout == second.stdout
          and keys_ok,
          "AC-QOC5 CLI 0/2/3/5 and a byte-stable JSON over pinned keys")


def ac6():
    """ASCII source, stdlib only, and its own reconcile label."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = True
    try:
        source.encode("ascii")
    except (UnicodeEncodeError, UnicodeDecodeError):
        ascii_only = False
    third_party = [token for token in ("numpy", "pandas", "yaml")
                   if ("import " + token) in source]
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL) in runner and "queue_occupancy_test" not in runner
    check(ascii_only and third_party == [] and wired,
          "AC-QOC6 pure ASCII, stdlib only, and wired under its own label")


def main():
    print("queue_occupancy suite (expected criteria %d)"
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