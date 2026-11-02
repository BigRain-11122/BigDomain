# queue_export_gate_wire.py - the export write proves its block before publishing it
# Criteria AC-QEG1..AC-QEG6 were pre-registered in state/queue/tech.md:422
# (the R2375 seed row) BEFORE this file existed.
#
# Why this exists: R2375 shipped queue_export_freshness_gate, so a stale queue
# block on the CEO-visible export can finally be NAMED - but only when a human
# types the CLI. The writer itself never asks: queue_floor_export_face.write
# replaces the export with the section it just composed, without comparing that
# section against anything. check_export_consistency still validates only the
# twelve self_drive fields, so a block can be published unproven and then age
# in silence.
#
# This module is the write path with the proof baked in. It composes the export
# exactly as the face composes it (QFE.compose - the one owner of that byte
# shape), stages those bytes BESIDE the original, and only then asks
# queue_export_freshness_gate.check whether the staged document carries the
# live section. The original is replaced only when the gate answers CURRENT; a
# refusal leaves the original byte-identical and removes the staged file.
#
# Nothing is re-derived: the section is the face's own composition, the verdict
# is the gate's own check, the drift names are the gate's own names. This file
# carries no row parser, no second status vocabulary, no canned number, and it
# reads no clock. The gate is called as an attribute at call time, so patching
# queue_export_freshness_gate.check moves this wire's verdict (AC-QEG1).
#
# Source is pure ASCII, stdlib only, no network.
#
# CLI: queue_export_gate_wire.py --execute [--root PATH] [--export PATH] [--json]
#   exit 0 = the export was replaced and read back identically
#   exit 2 = the gate refused (stale or missing block); nothing was replaced
#   exit 3 = a required file is missing or unreadable
#   exit 5 = the flags are bad

import io
import json
import os
import sys

import queue_export_freshness_gate as GATE
import queue_floor_export_face as QFE

LABEL = "os-queue-export-gate-wire"
STAGE_SUFFIX = ".gate-stage"
DEFAULT_EXPORT = os.path.join("docs", "status-export.json")

USAGE = (
    "usage: queue_export_gate_wire.py --execute [--root PATH] "
    "[--export PATH] [--json]\n"
    "  --execute      compose the live queue section, prove it with the gate,\n"
    "                 then replace the export (refused otherwise)\n"
    "  --root PATH    repository root to read the queues from (default .)\n"
    "  --export PATH  export document to write "
    "(default docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = written and read back, 2 = refused (nothing replaced), "
    "3 = missing file, 5 = bad flags\n"
)


class QueueExportGateWireError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _stage(text, path):
    """Write the composed bytes beside the export; never over it."""
    staged = path + STAGE_SUFFIX
    with io.open(staged, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return staged


def _discard(staged):
    """Remove the staged file so a refusal leaves no residue."""
    try:
        os.remove(staged)
    except OSError:
        pass


def publish(root, path):
    """Compose, prove, then replace. Returns (result, exit code)."""
    try:
        text = QFE.compose(root, path)
    except QFE.QueueFloorExportFaceError as exc:
        raise QueueExportGateWireError(exc.code, exc.detail)
    except (IOError, OSError):
        raise QueueExportGateWireError("E_QEG_EXPORT_MISSING", path)

    staged = _stage(text, path)
    try:
        verdict, code = GATE.check(root, staged)
    except GATE.QueueExportFreshnessGateError as exc:
        _discard(staged)
        raise QueueExportGateWireError(exc.code, exc.detail)
    except (IOError, OSError):
        _discard(staged)
        raise QueueExportGateWireError("E_QEG_STAGE_MISSING", staged)
    except Exception:
        _discard(staged)
        raise

    if code != 0:
        _discard(staged)
        return {
            "label": LABEL,
            "verdict": "REFUSED",
            "path": path,
            "gate": verdict.get("verdict"),
            "drifted": list(verdict.get("drifted") or ()),
            "bytes": len(text.encode("utf-8")),
        }, 2

    os.replace(staged, path)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    if back != text:
        raise QueueExportGateWireError("E_QEG_READBACK", path)

    return {
        "label": LABEL,
        "verdict": "WRITTEN",
        "path": path,
        "gate": verdict.get("verdict"),
        "drifted": [],
        "bytes": len(text.encode("utf-8")),
    }, 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    export = DEFAULT_EXPORT
    as_json = False
    saw_execute = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--execute":
            saw_execute = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_QEG_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                export = argv[index]
        else:
            sys.stderr.write("E_QEG_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_execute:
        sys.stderr.write("E_QEG_BAD_FLAGS --execute is required\n")
        return 5

    try:
        result, code = publish(root, export)
    except QueueExportGateWireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "QUEUE EXPORT GATE %s verdict=%s path=%s gate=%s bytes=%d "
            "drifted=%s\n" % (
                result["label"], result["verdict"], result["path"],
                result["gate"], result["bytes"],
                ",".join(result["drifted"]) if result["drifted"] else "(none)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))