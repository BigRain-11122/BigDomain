# queue_floor_reading_wire.py - the ONE floor reading the status face publishes
# Criteria AC-QFR1..AC-QFR6 were pre-registered in state/queue/tech.md line 413
# (the R2365 seed row) BEFORE this file existed.
#
# Why this exists: R2365 shipped queue_floor_delivered_wire, so the DELIVERED
# discount existed - but the reader every other tool calls was still
# queue_floor.gauge. Measured at the same instant at R2365: queue_floor
# --check read tech=9/10 (FLOOR-DEBT 1) while the wire read tech=8/10-1
# (FLOOR-DEBT 2). Two readers, two answers, and the published number was the
# undiscounted one. A published supply figure that counts rows already shipped
# is a wrong number shown to the reader who pays for it.
#
# This module is that ONE reading. The number it publishes is the DISCOUNTED
# number, and the rows that were discounted travel with it - so a consumer can
# reconcile gross = claimable + discounted and name every discounted row.
#
# Nothing is re-derived here:
#   - the discounted report is queue_floor_delivered_wire's own gauge
#     (AC-QFR1: patching that gauge moves this reading),
#   - the row law, the counts, the floor and the status law stay with
#     queue_floor, and the discount stays with the delivered wire.
# This module carries no second row parser, no module-path scan, no second
# status vocabulary and no second discount rule.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.
#
# CLI: queue_floor_reading_wire.py --check [--root PATH] [--json]
#   exit 0 = every queue meets its floor after the discount
#   exit 2 = a queue is short, or the flags are bad
#   exit 3 = a required queue file is missing

import json
import os
import sys

import queue_floor as QF
import queue_floor_delivered_wire as FDW

QUEUE_KEYS = (
    "queue",
    "path",
    "present",
    "open_rows",
    "done_rows",
    "gated_rows",
    "claimable",
    "discounted",
    "delivered",
    "floor",
    "shortfall",
    "status",
)

REPORT_KEYS = (
    "floors",
    "queues",
    "verdict",
    "shortfall_total",
    "missing",
    "delivered_total",
)

# The keys queue_floor itself publishes for a row. A published row must agree
# with them byte for byte whenever nothing was discounted (AC-QFR3).
SHARED_KEYS = tuple(QF.QUEUE_KEYS)


class QueueFloorReadingWireError(Exception):
    """Raised when the published reading cannot be produced honestly."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def reading(root):
    """The discounted floor reading, owned by queue_floor_delivered_wire."""
    try:
        return FDW.gauge(root)
    except (QF.QueueFloorError, FDW.QueueFloorDeliveredWireError) as exc:
        raise QueueFloorReadingWireError(exc.code, exc.detail)


def published_row(row):
    """One published row: queue_floor's row with the DISCOUNTED claimable.

    `claimable` is the effective (discounted) number because that is the
    figure a reader must be shown. The gross figure is recoverable as
    claimable + discounted, and `delivered` names the rows taken out.
    """
    ordered = {}
    for key in QUEUE_KEYS:
        if key == "claimable":
            ordered[key] = row["claimable_effective"]
        else:
            ordered[key] = row[key]
    return ordered


def publish(report):
    """Turn a discounted report into the published report shape."""
    rows = []
    for row in report["queues"]:
        rows.append(published_row(row))
    ordered = {}
    ordered["floors"] = report["floors"]
    ordered["queues"] = rows
    ordered["verdict"] = report["verdict"]
    ordered["shortfall_total"] = report["shortfall_total"]
    ordered["missing"] = report["missing"]
    ordered["delivered_total"] = report["delivered_total"]
    return ordered


def published(root):
    """The published reading for a root: read, then publish. Pure."""
    return publish(reading(root))


def one_line(report):
    """One operator line: discounted claimable/floor per queue."""
    parts = []
    for row in report["queues"]:
        shown = "%d/%d" % (row["claimable"], row["floor"])
        if row["discounted"]:
            shown += "-%d" % row["discounted"]
        parts.append("%s=%s" % (row["queue"], shown))
    return "QUEUE FLOOR READING %s verdict=%s shortfall=%d delivered=%d" % (
        " ".join(parts), report["verdict"], report["shortfall_total"],
        report["delivered_total"])


def render(report):
    """Full text rendering: the one line, then one line per queue."""
    out = [one_line(report)]
    for row in report["queues"]:
        out.append("  %-8s open=%d done=%d gated=%d claimable=%d "
                   "discounted=%d floor=%d shortfall=%d status=%s"
                   % (row["queue"], row["open_rows"], row["done_rows"],
                      row["gated_rows"], row["claimable"], row["discounted"],
                      row["floor"], row["shortfall"], row["status"]))
        for item in row["delivered"]:
            out.append("    discounted line=%d prefix=%s"
                       % (item["line"], item["prefix"]))
    if report["missing"]:
        out.append("  missing=%s" % ",".join(report["missing"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: queue_floor_reading_wire.py --check [--root PATH] [--json]\n"
         "  exit 0 = every queue meets its floor after the discount\n"
         "  exit 2 = a queue is short (FLOOR-DEBT) or the flags are bad\n"
         "  exit 3 = a required queue file is missing\n")


def main(argv):
    check = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_QFR_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_QFR_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_QFR_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = published(root)
    except QueueFloorReadingWireError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["missing"]:
        return 3
    if report["verdict"] == "FLOOR-DEBT":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))