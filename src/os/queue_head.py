# queue_head.py - which queue row comes first, as a reading
# Criteria AC-QHD1..AC-QHD6 were pre-registered in state/queue/tech.md as
# the R2267 seed row BEFORE this file existed. Anchor check at HEAD
# 2026-10-31: "os-queue-head", "test_queue_head" and "AC-QHD" outside the
# seed row text were git grep -F zero-occupancy rc=1 (disclosed: the seed
# row itself names the module, its criteria and its label).
#
# Why this exists: queue_floor counts claimable rows and queue_row gates
# their criteria prefix, but neither answers WHICH row comes first. Every
# window re-derived the same judgement by hand - skip the docker-absent
# row, the standing maintenance line, the product-gated row and the
# already-delivered row - and that judgement lived only in prose. This
# reader names it: the head row (file order, first claimable open row that
# declares its criteria), every skipped row with its reason, and an honest
# NO-HEAD when the queue carries nothing claimable.
#
# Both laws are IMPORTED, never re-implemented:
#   - the row / gate law comes from queue_floor (a patched marker table
#     flows straight through, because the table is read at call time),
#   - the criteria-prefix law comes from queue_row.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.
#
# CLI: queue_head.py --head [QUEUE] [--root PATH] [--json]
#   exit 0 = a head was found
#   exit 2 = NO-HEAD (nothing claimable) - an honest reading, not an error
#   exit 3 = the queue file is missing / unreadable
#   exit 5 = bad flags

import io
import json
import os
import sys

import queue_floor as QF
import queue_row as QR

VERDICTS = ("HEAD", "NO-HEAD", "MISSING")

REPORT_KEYS = (
    "queue",
    "path",
    "present",
    "head",
    "skipped",
    "skipped_before",
    "open_rows",
    "done_rows",
    "gated_rows",
    "claimable_rows",
    "prefixed_rows",
    "verdict",
)

HEAD_KEYS = ("line", "prefix", "text")
SKIP_KEYS = ("line", "reason", "detail")

EXCERPT_MAX = 120

# Row-order reasons a row is not offered, in the order they are judged.
REASON_GATED = "GATED"
REASON_NO_CRITERIA = "NO-CRITERIA"
REASON_BEHIND_HEAD = "BEHIND-HEAD"


class QueueHeadError(Exception):
    """Raised when the reader cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def queue_names():
    """The queue names the floor law already owns (one list, not two)."""
    names = []
    for name, _rel in QF.QUEUE_PATHS:
        names.append(name)
    return names


def queue_path(name):
    """Resolve a queue name to its repository-relative path."""
    for known, rel in QF.QUEUE_PATHS:
        if known == name:
            return rel
    return None


def gate_marker(text):
    """Name the marker that gates a row, reading queue_floor's table.

    Returns the marker string or None. The table is read at call time so a
    caller that patches queue_floor.GATED_MARKERS changes this answer too -
    there is no second copy of the gate law (AC-QHD2).
    """
    low = text.lower()
    for marker in QF.GATED_MARKERS:
        if marker in low:
            return marker
    return None


def excerpt(text):
    """A deterministic ASCII excerpt of a row, for the reading."""
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
        raise QueueHeadError("E_QHD_BAD_QUEUE", "%s (%s)" % (path, exc))


def head_text(name, rel, text):
    """Read one queue file in FILE order; return the closed report shape."""
    open_rows = 0
    done_rows = 0
    gated_rows = 0
    claimable = 0
    prefixed = 0
    head = None
    skipped_before = 0
    skipped = []
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if QF.is_done_row(line):
            # A done row is never offered and never sorted around (AC-QHD4).
            done_rows += 1
            continue
        if not QF.is_open_row(line):
            continue
        open_rows += 1
        marker = gate_marker(line)
        if QF.is_gated(line):
            gated_rows += 1
            skipped.append({"line": index + 1, "reason": REASON_GATED,
                            "detail": marker})
            continue
        claimable += 1
        # The prefix law is queue_row's, called here rather than copied.
        row = QR.scan_row(line)
        if not row["prefixed"]:
            skipped.append({"line": index + 1,
                            "reason": REASON_NO_CRITERIA, "detail": None})
            continue
        prefixed += 1
        if head is None:
            head = {"line": index + 1, "prefix": row["prefix"],
                    "text": excerpt(line)}
            skipped_before = len(skipped)
        else:
            skipped.append({"line": index + 1,
                            "reason": REASON_BEHIND_HEAD,
                            "detail": head["line"]})
    verdict = "HEAD" if head is not None else "NO-HEAD"
    return {
        "queue": name,
        "path": rel,
        "present": True,
        "head": head,
        "skipped": skipped,
        "skipped_before": skipped_before,
        "open_rows": open_rows,
        "done_rows": done_rows,
        "gated_rows": gated_rows,
        "claimable_rows": claimable,
        "prefixed_rows": prefixed,
        "verdict": verdict,
    }


def missing_queue(name, rel):
    """A missing queue reads MISSING with no invented head."""
    return {
        "queue": name,
        "path": rel,
        "present": False,
        "head": None,
        "skipped": [],
        "skipped_before": 0,
        "open_rows": 0,
        "done_rows": 0,
        "gated_rows": 0,
        "claimable_rows": 0,
        "prefixed_rows": 0,
        "verdict": "MISSING",
    }


def head(root, name="tech"):
    """Read one queue under root; the closed report shape."""
    rel = queue_path(name)
    if rel is None:
        raise QueueHeadError("E_QHD_BAD_QUEUE", "unknown queue %s" % name)
    full = os.path.join(root, rel)
    shown = rel.replace(os.sep, "/")
    if not os.path.isfile(full):
        return missing_queue(name, shown)
    return head_text(name, shown, read_text(full))


def one_line(report):
    """The single line an operator reads."""
    if report["verdict"] == "MISSING":
        return "QUEUE HEAD %s MISSING" % report["queue"]
    if report["head"] is None:
        return ("QUEUE HEAD %s NO-HEAD open=%d claimable=%d gated=%d"
                % (report["queue"], report["open_rows"],
                   report["claimable_rows"], report["gated_rows"]))
    return ("QUEUE HEAD %s line=%d prefix=%s skipped_before=%d claimable=%d"
            % (report["queue"], report["head"]["line"],
               report["head"]["prefix"], report["skipped_before"],
               report["claimable_rows"]))


def render(report):
    """Full text rendering: the one line, the head, then each skipped row."""
    out = [one_line(report)]
    if report["head"] is not None:
        out.append("  HEAD %s:%d %s"
                   % (report["path"], report["head"]["line"],
                      report["head"]["text"]))
    for item in report["skipped"]:
        detail = item["detail"]
        out.append("  SKIP %s:%d %s%s"
                   % (report["path"], item["line"], item["reason"],
                      "" if detail is None else " (%s)" % detail))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    if report["head"] is not None:
        head_out = {}
        for key in HEAD_KEYS:
            head_out[key] = report["head"][key]
        ordered["head"] = head_out
    skipped_out = []
    for item in report["skipped"]:
        pinned = {}
        for key in SKIP_KEYS:
            pinned[key] = item[key]
        skipped_out.append(pinned)
    ordered["skipped"] = skipped_out
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: queue_head.py --head [QUEUE] [--root PATH] [--json]\n"
         "  QUEUE defaults to tech (state/queue/<QUEUE>.md)\n"
         "  exit 0 = a head was found\n"
         "  exit 2 = NO-HEAD (nothing claimable)\n"
         "  exit 3 = the queue file is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    operation = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    name = "tech"
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--head":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_QHD_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_QHD_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            name = arg
        index += 1
    if not operation:
        sys.stdout.write("E_QHD_BAD_ARGS: --head is required\n")
        sys.stdout.write(USAGE)
        return 5
    if queue_path(name) is None:
        sys.stdout.write("E_QHD_BAD_ARGS: unknown queue %s\n" % name)
        sys.stdout.write(USAGE)
        return 5
    try:
        report = head(root, name)
    except QueueHeadError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "MISSING":
        return 3
    if report["verdict"] == "NO-HEAD":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))