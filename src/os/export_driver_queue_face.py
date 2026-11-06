# export_driver_queue_face.py - the export driver finally asks the queue face
# Criteria AC-EDQF1..AC-EDQF6 were pre-registered in state/queue/tech.md:531
# (the R2453 seed row) BEFORE this file existed.
#
# Why this exists: the round export driver (export_R2431.main) re-derived the
# CEO-visible queue block itself out of `queue_floor --check --json`, while the
# published queue section the rest of the house reads (AC-QFE1) is
# queue_floor_export_face.face = queue_floor_reading_wire.published - the
# DISCOUNTED reading, with delivered_total. Two derivations, one document:
# MEASURED TWICE at R2452 and R2453, both windows refreshed the export and then
# read queue_floor_export_face --check STALE (claimable=5,10,10) and had to land
# the block by hand through queue_export_gate_wire --execute. A freshly
# re-derived CEO document could therefore carry a stale queue block, and only a
# human typing a second command could fix it.
#
# This module closes it by construction, not by a second number:
#   - AC-EDQF1 the section the driver writes IS queue_floor_export_face.face,
#     asked as an attribute at CALL time (patching that reading moves the
#     section the driver publishes), so no gross re-derivation survives here.
#   - AC-EDQF3 the write is staged BESIDE the export and proved through
#     queue_export_freshness_gate.check before any byte is replaced; a queue
#     that moved between the reading and the write refuses with the gate's own
#     verdict word and leaves the document byte-identical with no residue.
#   - AC-EDQF4 the section is refreshed IN PLACE: every already-published key
#     of the document keeps its value and its position.
#   - AC-EDQF5 the gate verdict and the byte count travel back to the driver so
#     a refused or drifted run is visible rather than silent.
#
# Nothing is re-derived: the reading, the row laws, the drift names and the
# transport law all stay with their owners, asked at call time.
# Source is pure ASCII, stdlib only, no clock, zero network.
#
# CLI: export_driver_queue_face.py --check [--root PATH] [--export PATH]
#                                  [--json]
#   exit 0 = the export carries the live section
#   exit 2 = the export carries a stale or missing section
#   exit 3 = a required file is missing
#   exit 5 = the flags are bad

import io
import json
import os
import sys

import general_writer_dialect_audit as GWDA
import queue_export_freshness_gate as GATE
import queue_floor_export_face as QFE

FACE_KEY = QFE.FACE_KEY
LABEL = "os-export-driver-queue-face"
STAGE_SUFFIX = ".edqf-stage"
DEFAULT_EXPORT = os.path.join("docs", "status-export.json")

USAGE = (
    "usage: export_driver_queue_face.py --check [--root PATH] "
    "[--export PATH] [--json]\n"
    "  --check        report whether the export carries the live section\n"
    "  --root PATH    repository root to read the queues from (default .)\n"
    "  --export PATH  export document to check "
    "(default docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = current, 2 = stale or missing, 3 = missing file, "
    "5 = bad flags\n"
)


class ExportDriverQueueFaceError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def section(root):
    """The queue section: the shipped face's own reading, at CALL time."""
    try:
        return QFE.face(root)
    except QFE.QueueFloorExportFaceError as exc:
        raise ExportDriverQueueFaceError(exc.code, exc.detail)


def _refresh_rows(existing, live):
    """Move a row's values into the row already published, keeping its order."""
    if not isinstance(existing, list) or not isinstance(live, list):
        return live
    by_name = {}
    for row in existing:
        if isinstance(row, dict):
            by_name[row.get("queue")] = row
    out = []
    for row in live:
        if not isinstance(row, dict):
            out.append(row)
            continue
        target = by_name.get(row.get("queue"))
        if isinstance(target, dict):
            for key in list(target.keys()):
                if key not in row:
                    del target[key]
            for key in row:
                target[key] = row[key]
            out.append(target)
        else:
            out.append(row)
    return out


def refresh(document, root):
    """Refresh the queue section IN PLACE, keeping published key order."""
    if not isinstance(document, dict):
        raise ExportDriverQueueFaceError("E_EDQF_NOT_AN_OBJECT")
    live = section(root)
    existing = document.get(FACE_KEY)
    if isinstance(existing, dict) and isinstance(live, dict):
        for key in list(existing.keys()):
            if key not in live:
                del existing[key]
        for key in live:
            if key == "queues":
                existing[key] = _refresh_rows(existing.get(key), live[key])
            else:
                existing[key] = live[key]
        return document
    document[FACE_KEY] = live
    return document


def _payload(path, text):
    """The bytes to land, in the target's OWN transport (AC-SEWD2/3)."""
    try:
        return GWDA.payload_for(path, text)
    except GWDA.AuditError as exc:
        raise ExportDriverQueueFaceError(exc.code, exc.detail)


def _discard(staged):
    try:
        os.remove(staged)
    except OSError:
        pass


def publish(root, path, text):
    """Stage, prove with the gate, then replace. Returns the gate verdict.

    A queue that moved between the caller's reading and this proof refuses with
    the gate's own verdict word before any byte is replaced (AC-EDQF3).
    """
    if not isinstance(text, str):
        raise ExportDriverQueueFaceError("E_EDQF_BAD_TEXT")
    payload = _payload(path, text)
    staged = path + STAGE_SUFFIX
    with io.open(staged, "wb") as handle:
        handle.write(payload)
    try:
        verdict, code = GATE.check(root, staged)
    except GATE.QueueExportFreshnessGateError as exc:
        _discard(staged)
        raise ExportDriverQueueFaceError(exc.code, exc.detail)
    except (IOError, OSError):
        _discard(staged)
        raise ExportDriverQueueFaceError("E_EDQF_STAGE_MISSING", staged)
    except Exception:
        _discard(staged)
        raise

    result = {
        "label": LABEL,
        "path": path,
        "gate": verdict.get("verdict"),
        "drifted": list(verdict.get("drifted") or ()),
        "bytes": len(payload),
        "claimable": list(verdict.get("claimable") or ()),
    }
    if code != 0:
        _discard(staged)
        raise ExportDriverQueueFaceError(
            str(verdict.get("verdict")),
            ",".join(result["drifted"]) or path)

    os.replace(staged, path)
    with io.open(path, "rb") as handle:
        back = handle.read()
    if back != payload:
        raise ExportDriverQueueFaceError("E_EDQF_READBACK", path)
    return result


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
                sys.stderr.write("E_EDQF_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                export = argv[index]
        else:
            sys.stderr.write("E_EDQF_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_EDQF_BAD_FLAGS --check is required\n")
        return 5

    try:
        verdict, code = GATE.check(root, export)
    except GATE.QueueExportFreshnessGateError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3
    except (IOError, OSError):
        sys.stderr.write("E_EDQF_EXPORT_MISSING %s\n" % export)
        return 3

    result = {
        "label": LABEL,
        "path": export,
        "gate": verdict.get("verdict"),
        "drifted": list(verdict.get("drifted") or ()),
        "bytes": os.path.getsize(export),
        "claimable": list(verdict.get("claimable") or ()),
    }
    if as_json:
        sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "QUEUE DRIVER FACE %s verdict=%s path=%s gate=%s bytes=%d "
            "drifted=%s\n" % (
                result["label"],
                "CURRENT" if code == 0 else "STALE",
                result["path"], result["gate"], result["bytes"],
                ",".join(result["drifted"]) if result["drifted"] else "(none)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))