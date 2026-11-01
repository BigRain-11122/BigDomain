# queue_occupancy.py - is the row the queue offers already shipped?
# Criteria AC-QOC1..AC-QOC6 were written into this round record at R2337
# before the module body, but NOT into a queue seed row first - disclosed.
#
# Why this exists: queue_head answers WHICH row comes first, but nothing
# asks whether that row still needs doing. Measured this window: the head
# row (state/queue/tech.md:386, prefix AC-GDIW1) named
# src/os/gate_decl_identity_wire.py, and that module, its suite, its two
# evidence captures, its live refusal capture, its runner entry and its
# matrix row had all shipped at R2315 - so the queue offered work that was
# already done, and the exported next_milestone pointed a fresh window at
# re-doing it. A reading is cheaper than trusting prose: a row that names a
# module and whose module AND suite are both on disk is reported DELIVERED,
# a row naming anything not yet on disk stays CLAIMABLE, and a row naming
# no module at all is NO-MODULE rather than a silent pass.
#
# Both laws are IMPORTED, never re-implemented:
#   - the open / gated row law comes from queue_floor,
#   - the criteria-prefix law comes from queue_row.
# This module carries no second row parser: it never tests a row prefix
# itself and never compiles a criteria pattern.
#
# Pure read: nothing is written, no suite is run, no clock is read, no
# network import. Source is pure ASCII, stdlib only.
#
# CLI: queue_occupancy.py [--queue tech] [--root PATH] [--json]
#   exit 0 = a reading was produced (HEAD-CLAIMABLE included)
#   exit 2 = NO-HEAD (the queue offers nothing claimable)
#   exit 3 = the queue file is missing / unreadable
#   exit 5 = bad flags

import io
import json
import os
import re
import sys

import queue_floor as QF
import queue_row as QR

# A row names work by naming the module it will ship. This is a path
# reader, not a row parser: the row's state stays with queue_floor.
MODULE_RE = re.compile(r"src/os/([a-z0-9_]+)\.py")

STATUS_DELIVERED = "DELIVERED"
STATUS_CLAIMABLE = "CLAIMABLE"
STATUS_NO_MODULE = "NO-MODULE"

VERDICT_HEAD_DELIVERED = "HEAD-DELIVERED"
VERDICT_HEAD_CLAIMABLE = "HEAD-CLAIMABLE"
VERDICT_NO_HEAD = "NO-HEAD"

VERDICTS = (VERDICT_HEAD_DELIVERED, VERDICT_HEAD_CLAIMABLE, VERDICT_NO_HEAD)

ROW_KEYS = ("line", "prefix", "modules", "missing", "status", "excerpt")
SIGNAL_KEYS = ("name", "module", "test")

REPORT_KEYS = (
    "queue",
    "path",
    "present",
    "rows",
    "head",
    "claimable_rows",
    "prefixed_rows",
    "delivered_rows",
    "stale_delivered",
    "verdict",
)

EXCERPT_MAX = 120


class QueueOccupancyError(Exception):
    """Raised when the reading cannot be produced honestly."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def queue_names():
    """The queue names queue_floor already owns (one list, not two)."""
    return [name for name, _rel in QF.QUEUE_PATHS]


def queue_path(name):
    """Resolve a queue name to its repository-relative path."""
    for known, rel in QF.QUEUE_PATHS:
        if known == name:
            return rel
    return None


def module_names(text):
    """Every module this row says it will ship, sorted and de-duplicated."""
    return sorted(set(MODULE_RE.findall(text)))


def occupancy(root, name):
    """The two files that make a named module a delivered face."""
    base = os.path.join(root, "src", "os")
    return {
        "name": name,
        "module": os.path.exists(os.path.join(base, name + ".py")),
        "test": os.path.exists(os.path.join(base, "test_" + name + ".py")),
    }


def excerpt(text):
    """A deterministic ASCII excerpt of a row."""
    body = text.strip()
    if len(body) > EXCERPT_MAX:
        body = body[:EXCERPT_MAX] + "..."
    return body.encode("ascii", "replace").decode("ascii")


def scan_reading(root, line, text, prefix):
    """One claimable row: what it names and whether that has shipped."""
    names = module_names(text)
    signals = [occupancy(root, name) for name in names]
    missing = [item["name"] for item in signals
               if not (item["module"] and item["test"])]
    if not names:
        status = STATUS_NO_MODULE
    elif missing:
        status = STATUS_CLAIMABLE
    else:
        status = STATUS_DELIVERED
    return {
        "line": line,
        "prefix": prefix,
        "modules": names,
        "signals": signals,
        "missing": missing,
        "status": status,
        "excerpt": excerpt(text),
    }


def empty_queue(name, rel, present):
    """The reading for an absent queue: present False, no rows, NO-HEAD."""
    return {
        "queue": name,
        "path": rel,
        "present": present,
        "rows": [],
        "head": None,
        "claimable_rows": 0,
        "prefixed_rows": 0,
        "delivered_rows": 0,
        "stale_delivered": 0,
        "verdict": VERDICT_NO_HEAD,
    }


def audit_text(root, name, rel, text, present=True):
    """Judge every claimable prefixed open row of one queue file."""
    rows = []
    claimable = 0
    prefixed = 0
    gated = 0
    for line_no, line in enumerate(text.split("\n"), 1):
        if not QF.is_open_row(line):
            continue
        if QF.is_gated(line):
            gated += 1
            continue
        claimable += 1
        scan = QR.scan_row(line)
        if not scan["prefixed"]:
            continue
        prefixed += 1
        rows.append(scan_reading(root, line_no, line, scan["prefix"]))
    head = rows[0] if rows else None
    if head is None:
        verdict = VERDICT_NO_HEAD
    elif head["status"] == STATUS_DELIVERED:
        verdict = VERDICT_HEAD_DELIVERED
    else:
        verdict = VERDICT_HEAD_CLAIMABLE
    delivered = [row["line"] for row in rows
                 if row["status"] == STATUS_DELIVERED]
    stale = [row["line"] for row in rows[1:]
             if row["status"] == STATUS_DELIVERED]
    report = empty_queue(name, rel, present)
    report["rows"] = rows
    report["head"] = {"line": head["line"], "prefix": head["prefix"],
                      "status": head["status"]} if head else None
    report["claimable_rows"] = claimable
    report["prefixed_rows"] = prefixed
    report["delivered_rows"] = len(delivered)
    report["stale_delivered"] = len(stale)
    report["gated_rows"] = gated
    report["verdict"] = verdict
    return report


def read_text(path):
    """Read a queue file as utf-8; fail closed on unreadable input."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise QueueOccupancyError("E_QOC_BAD_QUEUE", "%s (%s)" % (path, exc))


def audit_root(root, name="tech"):
    """One queue reading from a repository root."""
    rel = queue_path(name)
    if rel is None:
        raise QueueOccupancyError("E_QOC_BAD_QUEUE",
                                  "unknown queue %r (known: %s)"
                                  % (name, ", ".join(queue_names())))
    path = os.path.join(root, rel)
    if not os.path.exists(path):
        # An absent queue is not an empty queue: there is nothing to read,
        # so the reading fails closed instead of claiming NO-HEAD.
        raise QueueOccupancyError("E_QOC_BAD_QUEUE", "%s (absent)" % path)
    return audit_text(root, name, rel, read_text(path))


def one_line(report):
    """A single ASCII line: the head, how many rows are already shipped."""
    if report["head"] is None:
        head = "none"
    else:
        head = "line=%s prefix=%s status=%s" % (
            report["head"]["line"], report["head"]["prefix"],
            report["head"]["status"])
    return ("QUEUE OCCUPANCY queue=%s claimable=%d prefixed=%d delivered=%d "
            "stale=%d head=%s verdict=%s" % (
                report["queue"], report["claimable_rows"],
                report["prefixed_rows"], report["delivered_rows"],
                report["stale_delivered"], head, report["verdict"]))


def render(report):
    """A short multi-line rendering that never hides a stale delivery."""
    lines = [one_line(report)]
    if not report["present"]:
        lines.append("  MISSING %s" % report["path"])
    for row in report["rows"]:
        lines.append("  line=%d prefix=%s status=%s modules=%s%s" % (
            row["line"], row["prefix"], row["status"],
            ",".join(row["modules"]) or "-",
            "" if not row["missing"] else " missing=" + ",".join(row["missing"])))
    return "\n".join(lines)


def to_json(report):
    """A byte-stable JSON body over the pinned keys."""
    body = {}
    for key in REPORT_KEYS:
        value = report.get(key)
        if key == "rows":
            value = []
            for row in report["rows"]:
                item = {}
                for row_key in ROW_KEYS:
                    item[row_key] = row.get(row_key)
                item["signals"] = []
                for signal in row.get("signals", []):
                    item["signals"].append(
                        {k: signal[k] for k in SIGNAL_KEYS})
                value.append(item)
        body[key] = value
    return json.dumps(body, indent=2, sort_keys=False)


def parse_args(argv):
    """Read the flags by hand so exit 5 stays ours and no clock is touched."""
    opts = {"queue": "tech", "root": ".", "json": False}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            opts["json"] = True
            index += 1
        elif arg in ("--queue", "--root"):
            if index + 1 >= len(argv):
                raise QueueOccupancyError("E_QOC_BAD_FLAGS",
                                          "%s needs a value" % arg)
            opts[arg[2:]] = argv[index + 1]
            index += 2
        else:
            raise QueueOccupancyError("E_QOC_BAD_FLAGS", "unknown flag %r" % arg)
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
        report = audit_root(opts["root"], opts["queue"])
    except QueueOccupancyError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5 if exc.code == "E_QOC_BAD_FLAGS" else 3
    if opts["json"]:
        sys.stdout.write(to_json(report) + "\n")
    elif report["present"]:
        sys.stdout.write(render(report) + "\n")
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == VERDICT_NO_HEAD:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))