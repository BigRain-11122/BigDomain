# queue_floor.py - read-only gauge: open queue rows against the standing floors
# Criteria AC-QF1..AC-QF8 were pre-registered in state/queue/tech.md (R2240 a)
# BEFORE this file existed.
#
# Why this exists: the standing-line floors (main >= 5, tech >= 10,
# explore >= 10) were enforced by eyeballing a grep count mid-window, so a
# shortfall was discovered only after the queue had already starved and the
# round had to spend its budget on seeding instead of product. This gauge
# makes the shortfall a reading, not a discovery.
#
# The row law is deliberately narrow: a queue row must start at column 0
# with "- [ ]" (open) or "- [x]"/"- [X]" (done). Indented continuation
# lines, prose that merely mentions "- [ ]" inside a sentence, and table
# rows are not rows. A row that carries a gate marker is still a row but
# it is NOT claimable: it waits on an outside party (a CEO physical item,
# a group handoff, a merchant number). Gated rows are reported, never
# silently dropped, and never counted toward the floor - a queue of pure
# gates is debt, which is exactly the debt this gauge exists to expose.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import io
import os
import re
import sys

# Standing floors, self-drive v2.0 section 1.
FLOORS = (("main", 5), ("tech", 10), ("explore", 10))

# Queue paths, relative to the repository root. The main line is the
# self-drive work queue the export checker also reads
# (state/queue/main.md, not the canonical tasks.md board - the R2244
# consistency check caught this gauge pointing at tasks.md, a file with
# two open rows, while the house reading was six).
QUEUE_PATHS = (
    ("main", os.path.join("state", "queue", "main.md")),
    ("tech", os.path.join("state", "queue", "tech.md")),
    ("explore", os.path.join("state", "queue", "explore.md")),
)

# A row carrying any of these markers waits on an outside party.
GATED_MARKERS = (
    "[needs-ceo]",
    "needs-ceo",
    "blocked on ceo",
    "blocked-on-ceo",
    "blocked on physical",
    "gated on",
    "gated:",
    "blocked on merchant",
)

VERDICTS = ("FLOOR-MET", "FLOOR-DEBT")

QUEUE_KEYS = (
    "queue",
    "path",
    "present",
    "open_rows",
    "done_rows",
    "gated_rows",
    "claimable",
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
)

OPEN_RE = re.compile(r"^- \[ \](?:\s|$)")
DONE_RE = re.compile(r"^- \[[xX]\](?:\s|$)")


class QueueFloorError(Exception):
    """Raised when the gauge cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def is_open_row(line):
    """True when the line is an OPEN queue row (column-0 anchored)."""
    return bool(OPEN_RE.match(line))


def is_done_row(line):
    """True when the line is a DONE queue row (column-0 anchored)."""
    return bool(DONE_RE.match(line))


def is_gated(text):
    """True when the row text carries a gate marker (case-insensitive)."""
    low = text.lower()
    for marker in GATED_MARKERS:
        if marker in low:
            return True
    return False


def read_text(path):
    """Read a queue file as utf-8; fail closed on unreadable input."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise QueueFloorError("E_QF_BAD_QUEUE", "%s (%s)" % (path, exc))


def count_rows(text):
    """Count open / done rows in one queue file.

    Returns a dict with open_rows (every open row), gated_rows (the open
    rows that wait on an outside party) and claimable (open minus gated).
    """
    open_rows = 0
    done_rows = 0
    gated_rows = 0
    for line in text.split("\n"):
        if is_open_row(line):
            open_rows += 1
            if is_gated(line):
                gated_rows += 1
        elif is_done_row(line):
            done_rows += 1
    return {
        "open_rows": open_rows,
        "done_rows": done_rows,
        "gated_rows": gated_rows,
        "claimable": open_rows - gated_rows,
    }


def queue_row(name, path, present, counts, floor):
    """One queue reading: counts plus the floor verdict for that queue."""
    claimable = counts["claimable"] if present else 0
    shortfall = floor - claimable
    if shortfall < 0:
        shortfall = 0
    if not present:
        status = "MISSING"
    elif shortfall == 0:
        status = "MET"
    else:
        status = "SHORT"
    return {
        "queue": name,
        "path": path,
        "present": present,
        "open_rows": counts["open_rows"],
        "done_rows": counts["done_rows"],
        "gated_rows": counts["gated_rows"],
        "claimable": claimable,
        "floor": floor,
        "shortfall": shortfall,
        "status": status,
    }


def gauge(root):
    """Measure every queue under root; return the closed report shape."""
    floors = {}
    for name, floor in FLOORS:
        floors[name] = floor
    rows = []
    missing = []
    path_of = {}
    for name, rel in QUEUE_PATHS:
        path_of[name] = rel
    for name, floor in FLOORS:
        rel = path_of[name]
        full = os.path.join(root, rel)
        present = os.path.isfile(full)
        if present:
            counts = count_rows(read_text(full))
        else:
            counts = {"open_rows": 0, "done_rows": 0,
                      "gated_rows": 0, "claimable": 0}
            missing.append(name)
        rows.append(queue_row(name, rel.replace(os.sep, "/"), present,
                              counts, floor))
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
    }


def one_line(report):
    """The single line an operator reads: claimable/floor per queue."""
    parts = []
    for row in report["queues"]:
        parts.append("%s=%d/%d" % (row["queue"], row["claimable"],
                                   row["floor"]))
    return "QUEUE FLOOR %s verdict=%s shortfall=%d" % (
        " ".join(parts), report["verdict"], report["shortfall_total"])


def render(report):
    """Full text rendering: the one line, then one line per queue."""
    out = [one_line(report)]
    for row in report["queues"]:
        out.append("  %-8s open=%d done=%d gated=%d claimable=%d floor=%d "
                   "shortfall=%d status=%s"
                   % (row["queue"], row["open_rows"], row["done_rows"],
                      row["gated_rows"], row["claimable"], row["floor"],
                      row["shortfall"], row["status"]))
    if report["missing"]:
        out.append("  missing=%s" % ",".join(report["missing"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    import json
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: queue_floor.py --check [--root PATH] [--json]\n"
         "  exit 0 = every queue meets its floor\n"
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
                sys.stdout.write("E_QF_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_QF_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_QF_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = gauge(root)
    except QueueFloorError as exc:
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