"""queue_head_delivered suite (R2354; criteria AC-QHO1..AC-QHO6 were
pre-registered in state/queue/tech.md as the R2337 seed row BEFORE this code).

What this proves: the offer finally asks the occupancy reading, so a row
whose module and suite already shipped is walked over and NAMED with the
module that shipped it instead of being handed to a fresh window. The
occupancy reading stays with queue_occupancy (patched here, and the offer
moves), a queue whose every prefixed row is DELIVERED reads ALL-DELIVERED
rather than the NO-HEAD that would mistake a full queue for an empty one,
the walked-over rows are reported in file order and only rows BEFORE the
chosen head are walked over, and the CLI speaks 0/2/3/5 with a byte-stable
JSON over pinned keys.

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

import queue_occupancy as QO  # noqa: E402
import queue_head_delivered as QHD  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_head_delivered.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-head-delivered"

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


def make_world(rows, modules=(), tests=()):
    """A temp root with one tech queue plus the modules it may name."""
    world = tempfile.mkdtemp(prefix="bigdomain-qho-")
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


def reading(rows, prefixed=None, claimable=None, delivered=None):
    """A hand-built occupancy reading: the shape queue_occupancy returns."""
    if prefixed is None:
        prefixed = len(rows)
    if claimable is None:
        claimable = len(rows)
    if delivered is None:
        delivered = len([r for r in rows if r["status"] == QO.STATUS_DELIVERED])
    return {
        "queue": "tech",
        "path": "state/queue/tech.md",
        "present": True,
        "rows": rows,
        "head": ({"line": rows[0]["line"], "prefix": rows[0]["prefix"],
                  "status": rows[0]["status"]} if rows else None),
        "claimable_rows": claimable,
        "prefixed_rows": prefixed,
        "delivered_rows": delivered,
        "stale_delivered": 0,
        "gated_rows": 0,
        "verdict": QO.VERDICT_NO_HEAD,
    }


def scan_row(line, prefix, status, modules=()):
    return {"line": line, "prefix": prefix, "modules": list(modules),
            "signals": [], "missing": [], "status": status,
            "excerpt": "fixture"}


def ac1():
    """The occupancy reading is queue_occupancy's, not a second scan."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_path_scan = ("MODULE_RE" not in source
                    and "os.path.exists" not in source
                    and "src/os/" not in source)
    delivered = scan_row(1, "AC-QHOA", QO.STATUS_DELIVERED, ["alpha"])
    pending = scan_row(2, "AC-QHOB", QO.STATUS_CLAIMABLE, ["beta"])
    base = QHD.offer(reading([delivered, pending]))
    original = QO.audit_root
    try:
        QO.audit_root = lambda root, name="tech": reading([pending])
        patched = QHD.read("/nowhere", "tech")
    finally:
        QO.audit_root = original
    check(no_path_scan
          and base["head"]["prefix"] == "AC-QHOB"
          and base["walked_over"][0]["prefix"] == "AC-QHOA"
          and patched["head"]["prefix"] == "AC-QHOB"
          and patched["walked_over"] == [],
          "AC-QHO1 occupancy is imported from queue_occupancy and no second "
          "module-path scan exists")


def ac2():
    """A delivered head is walked over, named, and the offer continues."""
    shipped = scan_row(5, "AC-QHOC", QO.STATUS_DELIVERED, ["alpha"])
    pending = scan_row(9, "AC-QHOD", QO.STATUS_CLAIMABLE, ["beta"])
    report = QHD.offer(reading([shipped, pending]))
    walked = report["walked_over"][0]
    check(report["verdict"] == QHD.VERDICT_OFFERED
          and report["head"]["prefix"] == "AC-QHOD"
          and report["head"]["line"] == 9
          and walked["prefix"] == "AC-QHOC"
          and walked["line"] == 5
          and walked["modules"] == ["alpha"]
          and walked["status"] == QO.STATUS_DELIVERED,
          "AC-QHO2 a delivered head is walked over with its module named and "
          "the offer continues")


def ac3():
    """All prefixed rows delivered is ALL-DELIVERED, never NO-HEAD."""
    all_delivered = reading([
        scan_row(3, "AC-QHOE", QO.STATUS_DELIVERED, ["alpha"]),
        scan_row(4, "AC-QHOF", QO.STATUS_DELIVERED, ["beta"]),
    ])
    full = QHD.offer(all_delivered)
    empty = QHD.offer(reading([], prefixed=0, claimable=0, delivered=0))
    nothing_prefixed = QHD.offer(reading([], prefixed=0, claimable=2,
                                         delivered=0))
    check(full["verdict"] == QHD.VERDICT_ALL_DELIVERED
          and full["head"] is None
          and len(full["walked_over"]) == 2
          and empty["verdict"] == QHD.VERDICT_NO_HEAD
          and nothing_prefixed["verdict"] == QHD.VERDICT_NO_HEAD
          and QHD.VERDICT_ALL_DELIVERED != QHD.VERDICT_NO_HEAD,
          "AC-QHO3 a queue of shipped rows reads ALL-DELIVERED, not NO-HEAD")


def ac4():
    """File order is kept, and only rows BEFORE the head are walked over."""
    rows = [
        scan_row(1, "AC-QHOG", QO.STATUS_DELIVERED, ["alpha"]),
        scan_row(2, "AC-QHOH", QO.STATUS_DELIVERED, ["beta"]),
        scan_row(3, "AC-QHOI", QO.STATUS_CLAIMABLE, ["gamma"]),
        scan_row(4, "AC-QHOJ", QO.STATUS_DELIVERED, ["delta"]),
        scan_row(5, "AC-QHOK", QO.STATUS_CLAIMABLE, ["epsilon"]),
    ]
    report = QHD.offer(reading(rows))
    walked = [(item["line"], item["prefix"], item["status"])
              for item in report["walked_over"]]
    check(report["head"]["line"] == 3
          and report["head"]["prefix"] == "AC-QHOI"
          and walked == [(1, "AC-QHOG", QO.STATUS_DELIVERED),
                         (2, "AC-QHOH", QO.STATUS_DELIVERED)]
          and report["claimable_rows"] == 5
          and report["prefixed_rows"] == 5,
          "AC-QHO4 walked-over rows are in file order and only rows before "
          "the head are walked over")


def ac5():
    """CLI codes 0/2/3/5 and a byte-stable JSON over the pinned keys."""
    cli = os.path.join(BASE, "queue_head_delivered.py")
    shipped = seed("alpha", "AC-QHOL")
    pending = seed("beta", "AC-QHOM", crumb="R9002")
    offered_world = make_world([shipped, pending], modules=["alpha", "beta"],
                              tests=["alpha"])
    all_delivered_world = make_world([shipped], modules=["alpha"],
                                     tests=["alpha"])
    codes = {}
    for name, argv in (
            ("offered", ["--head", "--root", offered_world]),
            ("alldelivered", ["--head", "--root", all_delivered_world]),
            ("missing", ["--head", "--root",
                         os.path.join(offered_world, "nope")]),
            ("badflags", ["--frobnicate"]),
    ):
        proc = subprocess.run([sys.executable, cli] + argv,
                              capture_output=True)
        codes[name] = proc.returncode
    first = subprocess.run([sys.executable, cli, "--head", "--root",
                            offered_world, "--json"], capture_output=True)
    second = subprocess.run([sys.executable, cli, "--head", "--root",
                             offered_world, "--json"], capture_output=True)
    payload = json.loads(first.stdout.decode("utf-8"))
    keys_ok = tuple(payload.keys()) == QHD.REPORT_KEYS
    check(codes["offered"] == 0 and codes["alldelivered"] == 2
          and codes["missing"] == 3 and codes["badflags"] == 5
          and first.stdout == second.stdout and keys_ok
          and payload["verdict"] == QHD.VERDICT_OFFERED,
          "AC-QHO5 CLI 0/2/3/5 and a byte-stable JSON over pinned keys")


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
          "AC-QHO6 pure ASCII, stdlib only, no clock, no network, wired")


def main():
    print("queue_head_delivered suite (expected criteria %d)"
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