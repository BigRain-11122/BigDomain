# queue_row.py - the pre-registration gate for claimable queue rows
# Criteria AC-QROW1..AC-QROW6 were pre-registered in state/queue/tech.md as
# the R2248-b seed BEFORE this file existed. Anchor check for the R2253
# claim: "os-queue-row" was git grep -F zero-occupancy rc=1 and "AC-QROW"
# appeared only in the seed row text and its generator. Disclosed name
# collision: queue_floor.py already ships a FUNCTION called queue_row, so
# this module deliberately imports that file's row law instead of writing a
# second one (AC-QROW1) - the file name stays as pre-registered, the state
# of a row is still decided in exactly one place.
#
# Why this exists: a seed row is supposed to register its criteria before
# any code is written, but nothing enforced it. A window could append a
# claimable row with no criteria at all and the floor gauge would happily
# count it as stock. This gate makes pre-registration a check instead of a
# habit: every claimable open row must name its criteria prefix.
#
# Two pre-registration forms are accepted, and only these two:
#   FORM-1  "Criteria prefix AC-<TOKEN>"      e.g. Criteria prefix AC-EXP
#   FORM-2  "Criteria AC-<TOKEN><n>"          e.g. Criteria AC-QROW1..6
# A row that names no criteria prefix at all is a violation. A row that
# carries a gate marker (a CEO physical item, a group handoff, a merchant
# number) is reported as gated and exempt, because an outside party owns
# its acceptance (AC-QROW3). Legacy rows dated before this law are still
# reported rather than silently exempted - an honest reading of real debt
# is the point of the check.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import io
import json
import os
import re
import sys

import queue_floor as QF

# The marker phrase and the criteria token, per the pre-registered law.
HARD_RE = re.compile(r"Criteria prefix\s+(AC-[A-Z0-9]{2,})", re.IGNORECASE)
SOFT_RE = re.compile(r"Criteria\s+(AC-[A-Z][A-Z0-9-]*[0-9])", re.IGNORECASE)

VERDICTS = ("GATE-PASS", "GATE-DEBT")

QUEUE_KEYS = (
    "queue",
    "path",
    "present",
    "open_rows",
    "done_rows",
    "gated_rows",
    "claimable_rows",
    "prefixed_rows",
    "violation_count",
    "violations",
    "status",
)

VIOLATION_KEYS = ("file", "line", "prefix", "excerpt")

REPORT_KEYS = (
    "queues",
    "open_rows",
    "done_rows",
    "gated_rows",
    "claimable_rows",
    "prefixed_rows",
    "violation_count",
    "violations",
    "verdict",
)

EXCERPT_MAX = 120


class QueueRowError(Exception):
    """Raised when the gate cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def scan_row(text):
    """Read the pre-registration state of one row.

    Returns a dict with prefixed (bool), form ("FORM-1" / "FORM-2" / None)
    and prefix (the criteria token or None). FORM-1 wins when both appear,
    because the explicit marker phrase is the stricter declaration.
    """
    hard = HARD_RE.search(text)
    if hard:
        return {"prefixed": True, "form": "FORM-1", "prefix": hard.group(1)}
    soft = SOFT_RE.search(text)
    if soft:
        return {"prefixed": True, "form": "FORM-2", "prefix": soft.group(1)}
    return {"prefixed": False, "form": None, "prefix": None}


def excerpt(text):
    """A deterministic ASCII excerpt of a row, for the refusal report."""
    body = text.strip()
    if len(body) > EXCERPT_MAX:
        body = body[:EXCERPT_MAX] + "..."
    return body.encode("ascii", "replace").decode("ascii")


def read_text(path):
    """Read a queue file as utf-8; fail closed on unreadable input."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise QueueRowError("E_QR_BAD_QUEUE", "%s (%s)" % (path, exc))


def audit_text(name, rel, text):
    """Audit one queue file; the row law comes from queue_floor, not here."""
    open_rows = 0
    done_rows = 0
    gated_rows = 0
    claimable = 0
    prefixed = 0
    violations = []
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if QF.is_open_row(line):
            open_rows += 1
            if QF.is_gated(line):
                gated_rows += 1
                continue
            claimable += 1
            row = scan_row(line)
            if row["prefixed"]:
                prefixed += 1
            else:
                violations.append({
                    "file": rel,
                    "line": index + 1,
                    "prefix": None,
                    "excerpt": excerpt(line),
                })
        elif QF.is_done_row(line):
            done_rows += 1
    if violations:
        status = "DEBT"
    elif open_rows == 0:
        status = "EMPTY"
    else:
        status = "PASS"
    return {
        "queue": name,
        "path": rel,
        "present": True,
        "open_rows": open_rows,
        "done_rows": done_rows,
        "gated_rows": gated_rows,
        "claimable_rows": claimable,
        "prefixed_rows": prefixed,
        "violation_count": len(violations),
        "violations": violations,
        "status": status,
    }


def empty_queue(name, rel):
    """A missing queue reads MISSING with an honest zero, never a pass."""
    return {
        "queue": name,
        "path": rel,
        "present": False,
        "open_rows": 0,
        "done_rows": 0,
        "gated_rows": 0,
        "claimable_rows": 0,
        "prefixed_rows": 0,
        "violation_count": 0,
        "violations": [],
        "status": "MISSING",
    }


def audit_root(root):
    """Audit every queue under root; return the closed report shape."""
    queues = []
    missing = []
    for name, rel in QF.QUEUE_PATHS:
        full = os.path.join(root, rel)
        shown = rel.replace(os.sep, "/")
        if not os.path.isfile(full):
            queues.append(empty_queue(name, shown))
            missing.append(name)
            continue
        queues.append(audit_text(name, shown, read_text(full)))
    totals = {
        "open_rows": 0,
        "done_rows": 0,
        "gated_rows": 0,
        "claimable_rows": 0,
        "prefixed_rows": 0,
        "violation_count": 0,
    }
    violations = []
    for row in queues:
        for key in totals:
            totals[key] += row[key]
        violations.extend(row["violations"])
    verdict = "GATE-PASS" if totals["violation_count"] == 0 else "GATE-DEBT"
    report = {
        "queues": queues,
        "verdict": verdict,
    }
    for key in ("open_rows", "done_rows", "gated_rows", "claimable_rows",
                "prefixed_rows", "violation_count"):
        report[key] = totals[key]
    report["violations"] = violations
    report["missing"] = missing
    return report


def one_line(report):
    """The single line an operator reads."""
    return ("QUEUE ROW GATE claimable=%d prefixed=%d gated=%d "
            "violations=%d verdict=%s"
            % (report["claimable_rows"], report["prefixed_rows"],
               report["gated_rows"], report["violation_count"],
               report["verdict"]))


def render(report):
    """Full text rendering: the one line, per queue, then each violation."""
    out = [one_line(report)]
    for row in report["queues"]:
        out.append("  %-8s open=%d done=%d gated=%d claimable=%d "
                   "prefixed=%d violations=%d status=%s"
                   % (row["queue"], row["open_rows"], row["done_rows"],
                      row["gated_rows"], row["claimable_rows"],
                      row["prefixed_rows"], row["violation_count"],
                      row["status"]))
    for item in report["violations"]:
        out.append("  VIOLATION %s:%d %s"
                   % (item["file"], item["line"], item["excerpt"]))
    if report["missing"]:
        out.append("  missing=%s" % ",".join(report["missing"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    ordered["queues"] = []
    for row in report["queues"]:
        item = {}
        for key in QUEUE_KEYS:
            item[key] = row[key]
        item["violations"] = []
        for bad in row["violations"]:
            pinned = {}
            for key in VIOLATION_KEYS:
                pinned[key] = bad[key]
            item["violations"].append(pinned)
        ordered["queues"].append(item)
    pinned_violations = []
    for bad in report["violations"]:
        pinned = {}
        for key in VIOLATION_KEYS:
            pinned[key] = bad[key]
        pinned_violations.append(pinned)
    ordered["violations"] = pinned_violations
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: queue_row.py --check [--root PATH] [--json]\n"
         "  exit 0 = every claimable open row names a criteria prefix\n"
         "  exit 2 = violations (GATE-DEBT) or bad flags\n"
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
                sys.stdout.write("E_QR_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_QR_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_QR_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = audit_root(root)
    except QueueRowError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["missing"]:
        return 3
    if report["verdict"] == "GATE-DEBT":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))