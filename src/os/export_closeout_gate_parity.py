# export_closeout_gate_parity.py - the two export writers finally get compared
# Criteria AC-ECGP1..AC-ECGP6 were pre-registered in state/queue/tech.md:423
# (the R2376 seed row) BEFORE this file existed.
#
# Why this exists: R2375 shipped queue_export_gate_wire, a write path that
# proves its block with queue_export_freshness_gate before publishing it - but
# the closeout that publishes the export every round never calls that wire. It
# imports queue_floor_export_face directly, calls QFE.apply, then dumps and
# writes the document itself (src/os/closeout_R2375.py, closeout_R2376.py).
# So the gate wire has no caller in the real path: git grep -l
# queue_export_gate_wire at HEAD lists only the R2375 files and the registry.
# Two writers publish one CEO-visible face and nothing measures that they agree.
#
# This module is that measurement. It runs BOTH real recipes over the SAME
# document and compares the bytes they publish:
#   - the closeout recipe: read the document, QFE.apply(data, root), then
#     json.dumps(ensure_ascii=False, indent=2) + "\n" (the exact shape the
#     closeout writes),
#   - the wire recipe: queue_export_gate_wire.publish over a private copy of
#     that same document, which composes through QFE.compose, stages, asks the
#     gate, and only then replaces the staged copy.
# Neither side is re-implemented: the section comes from queue_floor_export_face
# (so patching QFE.apply moves the closeout bytes, AC-ECGP1) and the proven
# write comes from queue_export_gate_wire (so patching QEG.publish moves this
# verdict, AC-ECGP1). When the wire refuses, the closeout-style bytes ARE a
# block the gate would not have published, so the reading is BYPASS and names
# every queue the gate names (AC-ECGP3).
#
# The check writes nothing in the repository: the wire runs over a private
# temporary copy which is removed before returning, the original document is
# only ever read, and no clock is read (AC-ECGP4). Source is pure ASCII,
# stdlib only, no network.
#
# CLI: export_closeout_gate_parity.py --check [--root PATH] [--export PATH]
#                                     [--json]
#   exit 0 = AGREES (both recipes publish identical bytes)
#   exit 2 = BYPASS (the wire refused the closeout block) or DISAGREES
#   exit 3 = the export file is missing or unreadable
#   exit 5 = the flags are bad

import io
import json
import os
import shutil
import sys
import tempfile

import queue_export_gate_wire as QEG
import queue_floor_export_face as QFE

LABEL = "os-export-closeout-gate-parity"
DEFAULT_EXPORT = os.path.join("docs", "status-export.json")

USAGE = (
    "usage: export_closeout_gate_parity.py --check [--root PATH] "
    "[--export PATH] [--json]\n"
    "  --check        run both export recipes over one document and compare\n"
    "  --root PATH    repository root to read the queues from (default .)\n"
    "  --export PATH  export document to compare "
    "(default docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = AGREES, 2 = BYPASS or DISAGREES, 3 = missing file, "
    "5 = bad flags\n"
)


class ExportCloseoutGateParityError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def closeout_style(root, path):
    """The bytes the closeout recipe publishes for this document.

    This is the closeout's own shape: read, QFE.apply, json.dumps(indent=2)
    plus one trailing LF. QFE.apply is asked as an attribute at call time so a
    patched apply moves these bytes (AC-ECGP1).
    """
    try:
        with io.open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except (IOError, OSError):
        raise ExportCloseoutGateParityError("E_ECGP_EXPORT_MISSING", path)
    except ValueError:
        raise ExportCloseoutGateParityError("E_ECGP_EXPORT_NOT_JSON", path)
    if not isinstance(data, dict):
        raise ExportCloseoutGateParityError("E_ECGP_NOT_AN_OBJECT", path)
    try:
        QFE.apply(data, root)
    except QFE.QueueFloorExportFaceError as exc:
        raise ExportCloseoutGateParityError(exc.code, exc.detail)
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _wire_reading(root, path):
    """Run the real wire over a private copy; return (bytes, verdict, code)."""
    directory = tempfile.mkdtemp(prefix="ecgp-")
    try:
        staged = os.path.join(directory, os.path.basename(path))
        try:
            shutil.copyfile(path, staged)
        except (IOError, OSError):
            raise ExportCloseoutGateParityError("E_ECGP_EXPORT_MISSING", path)
        try:
            result, code = QEG.publish(root, staged)
        except QEG.QueueExportGateWireError as exc:
            raise ExportCloseoutGateParityError(exc.code, exc.detail)
        if code != 0:
            return None, result, code
        with io.open(staged, "r", encoding="utf-8", newline="") as handle:
            return handle.read(), result, 0
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def _first_difference(left, right, prefix=""):
    """Name the first differing field between two parsed documents."""
    if type(left) is not type(right):
        return prefix or "bytes"
    if isinstance(left, dict):
        for key in list(left.keys()):
            name = ("%s.%s" % (prefix, key)) if prefix else str(key)
            if key not in right:
                return name
            found = _first_difference(left[key], right[key], name)
            if found:
                return found
        for key in right:
            if key not in left:
                return ("%s.%s" % (prefix, key)) if prefix else str(key)
        return ""
    if isinstance(left, list):
        name = prefix or "list"
        if len(left) != len(right):
            return name
        for index in range(len(left)):
            found = _first_difference(left[index], right[index],
                                      "%s[%d]" % (name, index))
            if found:
                return found
        return ""
    return "" if left == right else (prefix or "value")


def first_difference(left_text, right_text):
    """The first differing field, or "bytes" when the shapes cannot be parsed."""
    try:
        left = json.loads(left_text)
        right = json.loads(right_text)
    except ValueError:
        return "bytes" if left_text != right_text else ""
    if left_text == right_text:
        return ""
    return _first_difference(left, right) or "bytes"


def check(root, path):
    """Compare both recipes over one document; write nothing in the repo."""
    closeout_text = closeout_style(root, path)
    wire_text, wire_result, wire_code = _wire_reading(root, path)

    if wire_code != 0:
        return {
            "label": LABEL,
            "verdict": "BYPASS",
            "path": path,
            "gate": wire_result.get("verdict"),
            "drifted": list(wire_result.get("drifted") or ()),
            "closeout_bytes": len(closeout_text.encode("utf-8")),
            "wire_bytes": 0,
            "differs": "wire-refused",
        }, 2

    difference = first_difference(closeout_text, wire_text)
    verdict = "DISAGREES" if difference else "AGREES"
    return {
        "label": LABEL,
        "verdict": verdict,
        "path": path,
        "gate": wire_result.get("verdict"),
        "drifted": [],
        "closeout_bytes": len(closeout_text.encode("utf-8")),
        "wire_bytes": len(wire_text.encode("utf-8")),
        "differs": difference,
    }, (0 if verdict == "AGREES" else 2)


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
                sys.stderr.write("E_ECGP_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                export = argv[index]
        else:
            sys.stderr.write("E_ECGP_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_ECGP_BAD_FLAGS --check is required\n")
        return 5

    try:
        result, code = check(root, export)
    except ExportCloseoutGateParityError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "EXPORT WRITER PARITY %s verdict=%s path=%s gate=%s differs=%s\n"
            % (result["label"], result["verdict"], result["path"],
               result["gate"], result["differs"] or "(none)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))