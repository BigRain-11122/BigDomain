# queue_floor_export_face.py - the CEO-visible export finally publishes a queue line
# Criteria AC-QFE1..AC-QFE6 were pre-registered in state/queue/tech.md line 420
# (the R2368 seed row) BEFORE this file existed.
#
# Why this exists: R2368 shipped queue_floor_reading_wire, so the DISCOUNTED
# floor reading had exactly one owner - but docs/status-export.json published
# no queue line at all. Measured at the R2368 seed: git grep -F for claimable /
# floor / FLOOR over docs/status-export.json and check_export_consistency.py
# returned ZERO hits, so the corrected number had no consumer on the face the
# reader actually opens. A reading nobody publishes is a number with no reader.
#
# This module is that consumer. The section it writes IS
# queue_floor_reading_wire.published(root) - the whole report, byte for byte
# in the order that module fixes - so the discounted `claimable` and every
# discounted row (line + prefix) travel to the export unchanged. Nothing is
# re-derived here:
#   - the floor reading is queue_floor_reading_wire's own published report
#     (AC-QFE1: patching that reading moves the exported section),
#   - the row law, counts, floor, discount and status stay with queue_floor
#     and queue_floor_delivered_wire.
# This module carries no second row parser, no queue-file scan, no second
# status vocabulary and no canned number. Every byte it publishes is read at
# write time from the live tree.
#
# Pure derivation: the only write is the caller's export document, and the
# write path is one atomic replace with a read-back proof. No clock, no
# network. Source is pure ASCII, stdlib only.
#
# CLI: queue_floor_export_face.py --check [--root PATH] [--export PATH]
#                                  [--json] [--execute]
#   exit 0 = the export already carries the live section (dry run), or the
#            section was written and read back identically (--execute)
#   exit 2 = the export carries a stale section, or the flags are bad
#   exit 3 = a required file is missing

import io
import json
import os
import sys

import general_writer_dialect_audit as GWDA
import queue_floor_reading_wire as QFRW

FACE_KEY = "queue"
LABEL = "os-queue-floor-export-face"

USAGE = (
    "usage: queue_floor_export_face.py --check [--root PATH] "
    "[--export PATH] [--json] [--execute]\n"
    "  --check        report whether the export carries the live section\n"
    "  --root PATH    repository root to read the queues from (default .)\n"
    "  --export PATH  export document to read or write "
    "(default docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  --execute      write the derived section back to the export\n"
    "  exit 0 = current (or written and read back), 2 = stale or bad flags, "
    "3 = missing file\n"
)


class QueueFloorExportFaceError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def face(root):
    """The queue section the export publishes: the one floor reading."""
    try:
        return QFRW.published(root)
    except QFRW.QueueFloorReadingWireError as exc:
        raise QueueFloorExportFaceError(exc.code, exc.detail)


def apply(data, root):
    """Insert or refresh the queue section in one export document."""
    if not isinstance(data, dict):
        raise QueueFloorExportFaceError("E_QFE_NOT_AN_OBJECT")
    data[FACE_KEY] = face(root)
    return data


def compose(root, path):
    """The exact bytes to write: the existing document plus the live section."""
    try:
        with io.open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except (IOError, OSError) as exc:
        raise QueueFloorExportFaceError("E_QFE_EXPORT_MISSING", path)
    except ValueError:
        raise QueueFloorExportFaceError("E_QFE_EXPORT_NOT_JSON", path)
    apply(data, root)
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _payload(path, text):
    """The bytes to land, in the target's OWN transport (AC-SEWD2/AC-SEWD3).

    The dialect is not decided here: general_writer_dialect_audit.payload_for
    asks the shared law at CALL time, so an LF export keeps exactly today's
    bytes and a CRLF export keeps CRLF.
    """
    try:
        return GWDA.payload_for(path, text)
    except GWDA.AuditError as exc:
        raise QueueFloorExportFaceError(exc.code, exc.detail)


def write(root, path):
    """Write the derived section atomically and prove it by reading back."""
    text = compose(root, path)
    payload = _payload(path, text)
    temporary = path + ".tmp"
    with io.open(temporary, "wb") as handle:
        handle.write(payload)
    os.replace(temporary, path)
    with io.open(path, "rb") as handle:
        back = handle.read()
    if back != payload:
        raise QueueFloorExportFaceError("E_QFE_READBACK")
    return text


def current(path):
    """The section already on disk, or None when the export has none."""
    with io.open(path, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise QueueFloorExportFaceError("E_QFE_NOT_AN_OBJECT")
    return data.get(FACE_KEY)


def main(argv):
    root = "."
    export = os.path.join("docs", "status-export.json")
    as_json = False
    execute = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--help":
            sys.stdout.write(USAGE)
            return 0
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--execute":
            execute = True
        elif arg in ("--root", "--export"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_QFE_BAD_FLAGS missing value for %s\n" % arg)
                return 2
            if arg == "--root":
                root = argv[index]
            else:
                export = argv[index]
        else:
            sys.stderr.write("E_QFE_BAD_FLAGS unknown argument %s\n" % arg)
            return 2
        index += 1

    if not saw_check and not execute:
        sys.stderr.write("E_QFE_BAD_FLAGS --check is required\n")
        return 2

    try:
        live = face(root)
        if execute:
            text = write(root, export)
            on_disk = current(export)
            result = {
                "label": LABEL,
                "verdict": "WRITTEN",
                "path": export,
                "bytes": len(text.encode("utf-8")),
                "claimable": [row["claimable"] for row in on_disk["queues"]],
                "matches_live": on_disk == live,
            }
            code = 0 if result["matches_live"] else 2
        else:
            on_disk = current(export)
            fresh = on_disk == live
            result = {
                "label": LABEL,
                "verdict": "CURRENT" if fresh else "STALE",
                "path": export,
                "claimable": [row["claimable"] for row in live["queues"]],
                "delivered_total": live["delivered_total"],
                "matches_live": fresh,
            }
            code = 0 if fresh else 2
    except QueueFloorExportFaceError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3
    except (IOError, OSError) as exc:
        sys.stderr.write("E_QFE_EXPORT_MISSING %s\n" % export)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "QUEUE EXPORT %s verdict=%s path=%s claimable=%s\n" % (
                result["label"], result["verdict"], result["path"],
                ",".join(str(value) for value in result["claimable"])))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))