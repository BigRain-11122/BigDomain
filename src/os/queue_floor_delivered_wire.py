# queue_floor_delivered_wire.py - the floor gauge asks the occupancy reading
# Criteria AC-FDW1..AC-FDW6 were pre-registered in state/queue/tech.md
# (R2354 seed row, line 411) BEFORE this file existed.
#
# Why this exists: queue_floor counts every open non-gated row as standing
# supply, and queue_occupancy knows that some of those rows have already
# shipped. Measured at the R2354 seed: the gauge read tech claimable=10 while
# occupancy had already flagged a delivered row, so the queue could read
# FLOOR-MET over a supply of nothing. A floor over shipped rows is not a
# standing line. This module discounts DELIVERED rows from the claimable
# count and NAMES them, so a full-looking queue is never reported as met.
#
# Both laws are IMPORTED, never re-implemented:
#   - the row law and the published counts come from queue_floor,
#   - the occupancy reading comes from queue_occupancy.
# This module carries no second row parser, no second module-path scan and
# no second status vocabulary.
#
# Nothing queue_floor already publishes is redefined: open_rows, done_rows,
# gated_rows and claimable stay byte-identical for the same file, because
# AC-FDW2 asks the wire to ADD a discount rather than to move a number. The
# discounted figure is its own key, and shortfall/status follow it.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.
#
# CLI: queue_floor_delivered_wire.py --check [--root PATH] [--json]
#   exit 0 = every queue meets its floor after the discount
#   exit 2 = a queue is short, or the flags are bad
#   exit 3 = a required queue file is missing

import io
import json
import os
import sys

import queue_floor as QF
import queue_occupancy as QOC

QUEUE_KEYS = (
    "queue",
    "path",
    "present",
    "open_rows",
    "done_rows",
    "gated_rows",
    "claimable",
    "claimable_effective",
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

VERDICTS = ("FLOOR-MET", "FLOOR-DEBT")


class QueueFloorDeliveredWireError(Exception):
    """Raised when the wire cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def occupancy(root, name, rel, text):
    """The occupancy reading for one queue file, owned by queue_occupancy."""
    return QOC.audit_text(root, name, rel, text)


def delivered_rows(reading):
    """Every DELIVERED row in file order, as line + prefix only."""
    found = []
    for row in reading.get("rows", []):
        if row.get("status") == QOC.STATUS_DELIVERED:
            found.append({"line": row["line"], "prefix": row["prefix"]})
    return found


def queue_row(name, rel, present, counts, floor, reading):
    """One queue reading: queue_floor's row plus a named discount."""
    row = QF.queue_row(name, rel, present, counts, floor)
    shipped = delivered_rows(reading) if present else []
    discounted = len(shipped)
    effective = row["claimable"] - discounted
    if effective < 0:
        effective = 0
    shortfall = floor - effective
    if shortfall < 0:
        shortfall = 0
    if not present:
        status = "MISSING"
    elif shortfall == 0:
        status = "MET"
    else:
        status = "SHORT"
    ordered = {}
    for key in QUEUE_KEYS:
        if key == "claimable_effective":
            ordered[key] = effective
        elif key == "discounted":
            ordered[key] = discounted
        elif key == "delivered":
            ordered[key] = shipped
        else:
            ordered[key] = row[key]
    ordered["shortfall"] = shortfall
    ordered["status"] = status
    return ordered


def empty_reading():
    """The reading an absent queue would have had: nothing to discount."""
    return {"rows": [], "delivered_rows": 0, "claimable_rows": 0}


def gauge(root):
    """Measure every queue under root, with DELIVERED rows discounted."""
    floors = {}
    for name, floor in QF.FLOORS:
        floors[name] = floor
    path_of = {}
    for name, rel in QF.QUEUE_PATHS:
        path_of[name] = rel
    rows = []
    missing = []
    delivered_total = 0
    for name, floor in QF.FLOORS:
        rel = path_of[name]
        full = os.path.join(root, rel)
        present = os.path.isfile(full)
        if present:
            text = QF.read_text(full)
            counts = QF.count_rows(text)
            reading = occupancy(root, name, rel, text)
        else:
            counts = {"open_rows": 0, "done_rows": 0,
                      "gated_rows": 0, "claimable": 0}
            reading = empty_reading()
            missing.append(name)
        row = queue_row(name, rel.replace(os.sep, "/"), present, counts,
                        floor, reading)
        delivered_total += row["discounted"]
        rows.append(row)
    total = 0
    for row in rows:
        total += row["shortfall"]
    verdict = "FLOOR-MET" if total == 0 else "FLOOR-DEBT"
    return {
        "floors": floors,
        "queues": rows,
        "verdict": verdict,
        "shortfall_total": total,
        "missing": missing,
        "delivered_total": delivered_total,
    }


def one_line(report):
    """One operator line: effective/floor per queue plus the discount."""
    parts = []
    for row in report["queues"]:
        shown = "%d/%d" % (row["claimable_effective"], row["floor"])
        if row["discounted"]:
            shown += "-%d" % row["discounted"]
        parts.append("%s=%s" % (row["queue"], shown))
    return "QUEUE FLOOR %s verdict=%s shortfall=%d delivered=%d" % (
        " ".join(parts), report["verdict"], report["shortfall_total"],
        report["delivered_total"])


def render(report):
    """Full text rendering: the one line, then one line per queue."""
    out = [one_line(report)]
    for row in report["queues"]:
        out.append("  %-8s open=%d done=%d gated=%d claimable=%d "
                   "effective=%d discounted=%d floor=%d shortfall=%d "
                   "status=%s"
                   % (row["queue"], row["open_rows"], row["done_rows"],
                      row["gated_rows"], row["claimable"],
                      row["claimable_effective"], row["discounted"],
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


USAGE = ("usage: queue_floor_delivered_wire.py --check [--root PATH] [--json]\n"
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
                sys.stdout.write("E_FDW_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_FDW_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_FDW_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = gauge(root)
    except (QF.QueueFloorError, QOC.QueueOccupancyError) as exc:
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