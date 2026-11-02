# queue_export_freshness_gate.py - the export's queue block gets a watchdog
# Criteria AC-QEF1..AC-QEF6 were pre-registered in state/queue/tech.md:421
# (the R2374 seed row) BEFORE this file existed.
#
# Why this exists: R2374 shipped queue_floor_export_face, so the export finally
# carried a queue section derived at write time - but NOTHING checked that the
# section was still the live reading. check_export_consistency validates the
# twelve self_drive fields and never opens the queue block, so the section can
# age silently after a queue edit and only a manual CLI run notices.
#
# This module is the watchdog. It recomputes the live section through
# queue_floor_export_face.face - the one owner of that reading (AC-QEF1) - and
# compares it field by field with the section the export actually carries,
# naming EVERY drifted queue plus any drifted section scalar (AC-QEF2). An
# export whose queue block is absent reads MISSING and is never CURRENT
# (AC-QEF3). It writes nothing and reads no clock (AC-QEF4).
#
# Pure derivation, no second row parser and no canned number: the live side is
# the face's own reading and the row semantics stay with queue_floor.
# Source is pure ASCII, stdlib only, no network.
#
# CLI: queue_export_freshness_gate.py --check [--root PATH] [--export PATH]
#                                     [--json]
#   exit 0 = CURRENT (the export carries the live section)
#   exit 2 = STALE with the drifted names, or MISSING (no queue block)
#   exit 3 = the export file is missing
#   exit 5 = the flags are bad

import io
import json
import os
import sys

import queue_floor_export_face as QFE

FACE_KEY = QFE.FACE_KEY
LABEL = "os-queue-export-freshness-gate"
DEFAULT_EXPORT = os.path.join("docs", "status-export.json")

ROW_FIELDS = ("queue", "path", "present", "open_rows", "done_rows",
              "gated_rows", "claimable", "discounted", "delivered", "floor",
              "shortfall", "status")
SECTION_FIELDS = ("floors", "verdict", "shortfall_total", "missing",
                  "delivered_total")

USAGE = (
    "usage: queue_export_freshness_gate.py --check [--root PATH] "
    "[--export PATH] [--json]\n"
    "  --check        compare the export's queue block with the live reading\n"
    "  --root PATH    repository root to read the queues from (default .)\n"
    "  --export PATH  export document to check "
    "(default docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = CURRENT, 2 = STALE or MISSING (drift named), "
    "3 = export file missing, 5 = bad flags\n"
)


class QueueExportFreshnessGateError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def live_section(root):
    """The live queue section: queue_floor_export_face.face, not a copy."""
    try:
        return QFE.face(root)
    except QFE.QueueFloorExportFaceError as exc:
        raise QueueExportFreshnessGateError(exc.code, exc.detail)


def drift(live, on_disk):
    """Name every drifted queue and every drifted section scalar, in order."""
    names = []
    if not isinstance(on_disk, dict):
        return ["section:" + FACE_KEY]
    for field in SECTION_FIELDS:
        if live.get(field) != on_disk.get(field):
            names.append("section:" + field)
    live_rows = {}
    for row in live.get("queues") or ():
        if isinstance(row, dict):
            live_rows[row.get("queue")] = row
    disk_rows = {}
    for row in on_disk.get("queues") or ():
        if isinstance(row, dict):
            disk_rows[row.get("queue")] = row
    for name in sorted(set(live_rows) | set(disk_rows)):
        left = live_rows.get(name)
        right = disk_rows.get(name)
        if left is None or right is None:
            names.append("queue:%s" % (name,))
            continue
        if any(left.get(field) != right.get(field) for field in ROW_FIELDS):
            names.append("queue:%s" % (name,))
    return names


def check(root, path):
    """Compare the export against the live reading; write nothing."""
    live = live_section(root)
    try:
        on_disk = QFE.current(path)
    except (IOError, OSError):
        raise QueueExportFreshnessGateError("E_QEF_EXPORT_MISSING", path)
    except ValueError:
        raise QueueExportFreshnessGateError("E_QEF_EXPORT_NOT_JSON", path)
    if on_disk is None:
        return {"label": LABEL, "verdict": "MISSING", "path": path,
                "drifted": [], "claimable": [row["claimable"]
                                             for row in live["queues"]],
                "delivered_total": live["delivered_total"]}, 2
    names = drift(live, on_disk)
    verdict = "STALE" if names else "CURRENT"
    return {"label": LABEL, "verdict": verdict, "path": path,
            "drifted": names, "claimable": [row["claimable"]
                                            for row in live["queues"]],
            "delivered_total": live["delivered_total"]}, (2 if names else 0)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    export = DEFAULT_EXPORT
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_QEF_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                export = argv[index]
        else:
            sys.stderr.write("E_QEF_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_QEF_BAD_FLAGS --check is required\n")
        return 5

    try:
        result, code = check(root, export)
    except QueueExportFreshnessGateError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "QUEUE EXPORT FRESHNESS %s verdict=%s path=%s drifted=%s\n" % (
                result["label"], result["verdict"], result["path"],
                ",".join(result["drifted"]) if result["drifted"] else "(none)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))