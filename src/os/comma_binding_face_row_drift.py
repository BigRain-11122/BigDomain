# comma_binding_face_row_drift.py - per-line drift under an agreeing verdict
#
# Criteria AC-PFRD1..AC-PFRD6 were pre-registered in the R2444 tech seed row of
# state/queue/tech.md (line 512) BEFORE this file existed.
#
# Why this exists: comma_binding_identity_face_compare (R2444) asks all three
# publisher faces and compares each face's VERDICT and publisher SET. MEASURED
# at R2444, a per-line disagreement under an agreeing verdict is invisible:
# one identity detail row rewritten from closeout_export_parity_wire to
# drifted_wire keeps verdict=FACES-AGREE rc=0 differences=0. The three faces
# do not even share a row shape (identity publishes 6 keys, the from-import
# face 7, the relative face 8), so rows cannot be compared key for key.
#
# This module adds no law and restates no table. It asks the SHIPPED compare
# at CALL time and keeps its report unchanged; what it adds is one reading over
# the rows that compare already collected:
#
#   * the compared keys are DERIVED from the rows the faces actually publish
#     (the intersection of the published key sets minus the row identity),
#     never a fixed list;
#   * for every (path, line) the values of those keys are compared across the
#     faces that publish a row there, and a disagreement is published as
#     ROWS-SPLIT naming the file, the line, the key and every face's own
#     module, label and seam;
#   * a face that publishes no row for a line the others publish is reported
#     SILENT naming that face instead of being counted as agreement.
#
# When every row agrees the printed report is the shipped compare's own text,
# byte for byte (AC-PFRD3).
#
# This module writes nothing and reads no clock (AC-PFRD6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: comma_binding_face_row_drift.py --check [--root PATH]
#                                       [--export NAME] [--owner MODULE]
#                                       [--wire MODULE] [--package NAME]
#                                       [--json]
#   exit 0 = FACES-AGREE or NO-PUBLISHER
#   exit 2 = ROWS-SPLIT, ROWS-SILENT or FACES-SPLIT
#   exit 3 = the root is missing or a face refused
#   exit 5 = the flags are bad

import importlib
import io
import json
import os
import sys

LABEL = "os-comma-binding-face-row-drift"
PARENT = "comma_binding_identity_face_compare"

DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"

# The row identity is the ONLY fixed part: it says which cells are one cell.
# Every compared KEY is derived from the published rows at CALL time.
JOIN_KEYS = ("path", "line")

REPORT_KEYS = ("label", "verdict", "root", "package", "wire", "parent",
               "compared_keys", "cells", "splits", "silent")

SPLIT_KEYS = ("path", "line", "key", "faces")
SILENT_KEYS = ("path", "line", "face", "label", "seams", "published_by")

AGREE = "FACES-AGREE"
SPLIT = "ROWS-SPLIT"
SILENT = "ROWS-SILENT"
FACES_SPLIT = "FACES-SPLIT"
NO_PUBLISHER = "NO-PUBLISHER"

USAGE = (
    "usage: comma_binding_face_row_drift.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--wire MODULE] [--package NAME] "
    "[--json]\n"
    "  --check        compare the per-line rows of every publisher face\n"
    "  --root PATH    tree to read (default .)\n"
    "  --export NAME  export document basename (default status-export.json)\n"
    "  --owner MODULE module that owns the current export shape\n"
    "                 (default queue_floor_export_face)\n"
    "  --wire MODULE  module that proves the bytes before publishing\n"
    "                 (default closeout_export_parity_wire)\n"
    "  --package NAME package declared to the relative face (optional)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = FACES-AGREE or NO-PUBLISHER, 2 = a row or face split,\n"
    "  3 = the root is missing or a face refused, 5 = bad flags\n"
)


class CommaBindingFaceRowDriftError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parent_module():
    """The shipped compare, imported at CALL time so nothing is frozen."""
    return importlib.import_module(PARENT)


def ask_parent(root, export_name, owner, wire_module, package):
    """Ask the shipped compare over the same tree; its report is kept as-is."""
    module = parent_module()
    try:
        return module.audit(root, export_name, owner, wire_module, package)
    except Exception as exc:  # the parent's own refusal codes are carried
        raise CommaBindingFaceRowDriftError(
            "E_PFRD_PARENT", "%s: %s" % (type(exc).__name__, exc))


def compared_keys(faces):
    """The keys every published row actually carries, minus the row identity.

    Derived from the rows in the report, so a face that publishes one more or
    one fewer key simply narrows the comparison instead of being skipped
    (AC-PFRD1). No fixed key list exists.
    """
    names = None
    for face in faces:
        for row in face["rows"]:
            keys = set(row.keys())
            names = keys if names is None else (names & keys)
    if not names:
        return ()
    return tuple(sorted(name for name in names if name not in JOIN_KEYS))


def _line_label(value):
    return value if isinstance(value, int) else -1


def grid_of(faces):
    """(path, line) -> {face name: [rows in publication order]}."""
    grid = {}
    for face in faces:
        for row in face["rows"]:
            key = (row.get("path"), _line_label(row.get("line")))
            cell = grid.setdefault(key, {"path": row.get("path"),
                                         "line": row.get("line"),
                                         "faces": {}})
            cell["faces"].setdefault(face["face"], []).append(row)
    return grid


def _value(value):
    """A comparable, printable form of one cell value (JSON-safe)."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _seams(face):
    return [{"seam": row["seam"], "calls": row["calls"]}
            for row in face.get("seams") or []]


def splits_of(grid, keys, faces):
    """Every per-line disagreement, naming the faces, labels and seams."""
    by_name = dict((face["face"], face) for face in faces)
    splits = []
    for key in sorted(grid, key=lambda k: (str(k[0]), k[1], str(k[0]))):
        cell = grid[key]
        present = cell["faces"]
        for name in sorted(keys):
            values = {}
            for face_name in sorted(present):
                values[face_name] = [_value(row.get(name))
                                     for row in present[face_name]]
            seen = set(json.dumps(item, sort_keys=True, ensure_ascii=False)
                       for item in values.values())
            if len(seen) < 2:
                continue
            carriers = []
            for face_name in sorted(present):
                face = by_name[face_name]
                carriers.append({
                    "face": face_name,
                    "label": face.get("label", ""),
                    "module": ", ".join(sorted(set(
                        str(row.get("module", ""))
                        for row in present[face_name]))),
                    "value": values[face_name],
                    "seams": _seams(face),
                })
            splits.append({"path": cell["path"], "line": cell["line"],
                           "key": name, "faces": carriers})
    return splits


def silent_of(grid, faces):
    """A line some faces publish and others do not, naming the silent face."""
    silent = []
    for key in sorted(grid, key=lambda k: (str(k[0]), k[1], str(k[0]))):
        cell = grid[key]
        present = cell["faces"]
        if len(present) == len(faces):
            continue
        for face in faces:
            if face["face"] in present:
                continue
            silent.append({
                "path": cell["path"],
                "line": cell["line"],
                "face": face["face"],
                "label": face.get("label", ""),
                "seams": _seams(face),
                "published_by": sorted(present),
            })
    return silent


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER,
          wire_module=DEFAULT_WIRE, package=None):
    """Compare the per-line rows of every publisher face over one tree."""
    if not os.path.isdir(root):
        raise CommaBindingFaceRowDriftError("E_PFRD_NO_ROOT", root)
    parent, parent_code = ask_parent(root, export_name, owner, wire_module,
                                     package)
    faces = parent.get("faces") or []
    keys = compared_keys(faces)
    grid = grid_of(faces)
    splits = splits_of(grid, keys, faces) if keys else []
    silent = silent_of(grid, faces)

    if parent.get("verdict") == NO_PUBLISHER:
        verdict = NO_PUBLISHER
        code = 0
    elif parent.get("verdict") == FACES_SPLIT or parent_code == 2:
        verdict = FACES_SPLIT
        code = 2
    elif splits:
        verdict = SPLIT
        code = 2
    elif silent:
        verdict = SILENT
        code = 2
    else:
        verdict = AGREE
        code = 0

    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "package": package or "",
        "wire": wire_module,
        "parent": parent,
        "compared_keys": list(keys),
        "cells": len(grid),
        "splits": splits,
        "silent": silent,
    }
    return report, code


def parent_text(argv):
    """The shipped compare's own stdout for the same flags, byte for byte."""
    module = parent_module()
    captured = io.StringIO()
    saved = sys.stdout
    sys.stdout = captured
    try:
        module.main(list(argv))
    finally:
        sys.stdout = saved
    return captured.getvalue()


def parse_args(argv):
    """Return (options, error code or None)."""
    root = "."
    export_name = DEFAULT_EXPORT_NAME
    owner = DEFAULT_OWNER
    wire_module = DEFAULT_WIRE
    package = None
    options = {"root": root, "export": export_name, "owner": owner,
               "wire": wire_module, "package": package,
               "json": False, "check": False}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            options["check"] = True
        elif arg == "--json":
            options["json"] = True
        elif arg in ("--root", "--export", "--owner", "--wire", "--package"):
            index += 1
            if index >= len(argv):
                sys.stderr.write(
                    "E_PFRD_BAD_FLAGS missing value for %s\n" % arg)
                return options, 5
            options[arg[2:]] = argv[index]
        else:
            sys.stderr.write("E_PFRD_BAD_FLAGS unknown argument %s\n" % arg)
            return options, 5
        index += 1
    if not options["check"]:
        sys.stderr.write("E_PFRD_BAD_FLAGS --check is required\n")
        return options, 5
    return options, None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    options, failure = parse_args(argv)
    if failure is not None:
        return failure

    try:
        report, code = audit(options["root"], options["export"],
                             options["owner"], options["wire"],
                             options["package"])
    except CommaBindingFaceRowDriftError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if options["json"]:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
        return code

    sys.stdout.write(parent_text(argv))
    if report["verdict"] in (AGREE, NO_PUBLISHER):
        return code
    sys.stdout.write(
        "ROW DRIFT %s verdict=%s cells=%d compared=%s\n" % (
            report["label"], report["verdict"], report["cells"],
            ",".join(report["compared_keys"]) or "(none)"))
    for row in report["splits"]:
        sys.stdout.write(
            "  SPLIT %s line=%s key=%s faces=%s\n" % (
                row["path"], row["line"], row["key"],
                " ".join("%s=%s" % (item["face"], item["module"])
                         for item in row["faces"])))
    for row in report["silent"]:
        sys.stdout.write(
            "  SILENT %s line=%s face=%s published_by=%s\n" % (
                row["path"], row["line"], row["face"],
                ",".join(row["published_by"]) or "(none)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))