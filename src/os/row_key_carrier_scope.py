# row_key_carrier_scope.py - compare every key across the faces that carry it
#
# Criteria AC-PFKC1..AC-PFKC6 were pre-registered in the R2446 tech seed row of
# state/queue/tech.md:522 BEFORE this file existed.
#
# Why this exists: comma_binding_face_row_drift (R2446) compares the keys EVERY
# publisher face carries - the intersection of the three row shapes, which
# MEASURED at R2446 is 6/7/8 keys wide and leaves module/receiver/state/text.
# Two published keys are therefore dropped in silence:
#
#   * `kind` is carried by the from-import face and the relative face (22 rows
#     over 11 files) - a from-import/relative disagreement on it is published
#     by nothing;
#   * `relative` is carried by the relative face only (11 rows) and is never
#     read at all.
#
# No live disagreement was measured at R2446, so this is a latent blind spot
# proved on fixtures rather than a live catch, and it is stated that way.
#
# This module adds no law and restates no table. It asks the SHIPPED row-drift
# reading at CALL time (which itself asks the shipped identity compare) and
# keeps that report unchanged inside its own. What it adds is one reading:
#
#   * the carrier set of a key is DERIVED from the rows that actually publish
#     that key, never a fixed list (AC-PFKC1);
#   * a disagreement between the faces that carry a key reads ROWS-SPLIT
#     naming the key and every carrying face, including a two-of-three key
#     the intersection never compared (AC-PFKC2);
#   * a key only one face publishes is reported SINGLE-FACE with its carrier
#     count and is never invented as a split (AC-PFKC3);
#   * every key's carrier count is published beside the reading, and a key
#     carried by ALL faces keeps the R2446 reading byte for byte (AC-PFKC4);
#   * each split row keeps the R2446 carrier shape - face, label, module,
#     value, seams (AC-PFKC5).
#
# This module writes nothing and reads no clock (AC-PFKC6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: row_key_carrier_scope.py --check [--root PATH] [--export NAME]
#                                 [--owner MODULE] [--wire MODULE]
#                                 [--package NAME] [--json]
#   exit 0 = AGREE, SINGLE-FACE only, or NO-PUBLISHER
#   exit 2 = ROWS-SPLIT or FACES-SPLIT
#   exit 3 = the root is missing or a face refused
#   exit 5 = the flags are bad

import importlib
import json
import os
import sys

LABEL = "os-row-key-carrier-scope"
PARENT = "comma_binding_face_row_drift"

DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"

# The row identity is the ONLY fixed part: it says which cells are one cell.
# Every compared KEY is derived from the published rows at CALL time.
JOIN_KEYS = ("path", "line")

ALL_FACES = "all-faces"
SUBSET = "subset"

AGREE = "AGREE"
SPLIT = "ROWS-SPLIT"
FACES_SPLIT = "FACES-SPLIT"
NO_PUBLISHER = "NO-PUBLISHER"

USAGE = (
    "usage: row_key_carrier_scope.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--wire MODULE] [--package NAME] "
    "[--json]\n"
    "  --check        compare every published key across its carriers\n"
    "  --root PATH    tree to read (default .)\n"
    "  --export NAME  export document basename (default status-export.json)\n"
    "  --owner MODULE module that owns the current export shape\n"
    "                 (default queue_floor_export_face)\n"
    "  --wire MODULE  module that proves the bytes before publishing\n"
    "                 (default closeout_export_parity_wire)\n"
    "  --package NAME package declared to the relative face (optional)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = AGREE / SINGLE-FACE only / NO-PUBLISHER, 2 = a split,\n"
    "  3 = the root is missing or a face refused, 5 = bad flags\n"
)


class RowKeyCarrierScopeError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parent_module():
    """The shipped row-drift reading, imported at CALL time."""
    return importlib.import_module(PARENT)


def ask_row_drift(root, export_name, owner, wire_module, package):
    """Ask the shipped row-drift reading; its report is kept as-is."""
    module = parent_module()
    try:
        return module.audit(root, export_name, owner, wire_module, package)
    except Exception as exc:  # the parent's own refusal codes are carried
        raise RowKeyCarrierScopeError(
            "E_PFKC_PARENT", "%s: %s" % (type(exc).__name__, exc))


def carriers_of(faces):
    """key -> sorted tuple of the faces that publish a row carrying it.

    Derived from the rows in the report, so a key one face adds or drops simply
    changes its own carrier set instead of being skipped (AC-PFKC1). No fixed
    key list exists.
    """
    carriers = {}
    for face in faces:
        for row in face["rows"]:
            for name in row.keys():
                if name in JOIN_KEYS:
                    continue
                carriers.setdefault(name, set()).add(face["face"])
    return dict((name, tuple(sorted(names)))
                for name, names in carriers.items())


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


def splits_of(grid, carriers, faces):
    """Every per-key disagreement, naming the faces that carry that key."""
    by_name = dict((face["face"], face) for face in faces)
    splits = []
    for key in sorted(grid, key=lambda k: (str(k[0]), k[1], str(k[0]))):
        cell = grid[key]
        present = cell["faces"]
        for name in sorted(carriers):
            carrying = [face_name for face_name in carriers[name]
                        if face_name in present]
            if len(carrying) < 2:
                continue
            values = {}
            for face_name in carrying:
                values[face_name] = [_value(row.get(name))
                                     for row in present[face_name]]
            seen = set(json.dumps(item, sort_keys=True, ensure_ascii=False)
                       for item in values.values())
            if len(seen) < 2:
                continue
            rows = []
            for face_name in carrying:
                face = by_name[face_name]
                rows.append({
                    "face": face_name,
                    "label": face.get("label", ""),
                    "module": ", ".join(sorted(set(
                        str(row.get("module", ""))
                        for row in present[face_name]))),
                    "value": values[face_name],
                    "seams": _seams(face),
                })
            splits.append({"path": cell["path"], "line": cell["line"],
                           "key": name, "faces": rows})
    return splits


def scope_of(faces, carriers):
    """Per-key scope rows: carrier count, carrier faces, and which shape."""
    scopes = []
    for name in sorted(carriers):
        names = carriers[name]
        scopes.append({
            "key": name,
            "carriers": len(names),
            "faces": list(names),
            "scope": ALL_FACES if len(names) == len(faces) else SUBSET,
        })
    return scopes


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER,
          wire_module=DEFAULT_WIRE, package=None):
    """Read every published key across the faces that actually carry it."""
    if not os.path.isdir(root):
        raise RowKeyCarrierScopeError("E_PFKC_NO_ROOT", root)
    row_drift, row_drift_code = ask_row_drift(root, export_name, owner,
                                              wire_module, package)
    faces = (row_drift.get("parent") or {}).get("faces") or []
    carriers = carriers_of(faces)
    grid = grid_of(faces)
    splits = splits_of(grid, carriers, faces)
    scopes = scope_of(faces, carriers)
    singles = [row for row in scopes if row["carriers"] == 1]
    keys_all = [row["key"] for row in scopes if row["scope"] == ALL_FACES]
    keys_subset = [row["key"] for row in scopes if row["scope"] == SUBSET]

    if row_drift.get("verdict") == NO_PUBLISHER:
        verdict = NO_PUBLISHER
        code = 0
    elif row_drift.get("verdict") == FACES_SPLIT or row_drift_code == 2 \
            and not splits:
        verdict = FACES_SPLIT
        code = 2
    elif splits:
        verdict = SPLIT
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
        "row_drift": row_drift,
        "carrier_counts": dict((row["key"], row["carriers"])
                               for row in scopes),
        "scopes": scopes,
        "keys_all": keys_all,
        "keys_subset": keys_subset,
        "single_face": singles,
        "cells": len(grid),
        "splits": splits,
    }
    return report, code


def parse_args(argv):
    """Return (options, error code or None)."""
    options = {"root": ".", "export": DEFAULT_EXPORT_NAME, "owner":
               DEFAULT_OWNER, "wire": DEFAULT_WIRE, "package": None,
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
                    "E_PFKC_BAD_FLAGS missing value for %s\n" % arg)
                return options, 5
            options[arg[2:]] = argv[index]
        else:
            sys.stderr.write("E_PFKC_BAD_FLAGS unknown argument %s\n" % arg)
            return options, 5
        index += 1
    if not options["check"]:
        sys.stderr.write("E_PFKC_BAD_FLAGS --check is required\n")
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
    except RowKeyCarrierScopeError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if options["json"]:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
        return code

    sys.stdout.write(
        "ROW KEY CARRIER SCOPE %s verdict=%s cells=%d keys=%d all=%d "
        "subset=%d singles=%d\n" % (
            report["label"], report["verdict"], report["cells"],
            len(report["scopes"]), len(report["keys_all"]),
            len(report["keys_subset"]), len(report["single_face"])))
    for row in report["scopes"]:
        sys.stdout.write(
            "  KEY %s carriers=%d scope=%s faces=%s\n" % (
                row["key"], row["carriers"], row["scope"],
                ",".join(row["faces"])))
    for row in report["splits"]:
        sys.stdout.write(
            "  SPLIT %s line=%s key=%s faces=%s\n" % (
                row["path"], row["line"], row["key"],
                " ".join("%s=%s" % (item["face"], item["module"])
                         for item in row["faces"])))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))