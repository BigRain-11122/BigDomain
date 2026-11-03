# comma_binding_sibling_faces.py - one table, every face that resolves publishers
# Criteria AC-PICBS1..AC-PICBS6 were pre-registered in the R2428 tech seed row
# of state/queue/tech.md (line 492) BEFORE this file existed.
#
# Why this exists: comma_binding_consumer_wire (R2428) put the comma-aware
# table on the identity face only. MEASURED at R2428 on one comma-list
# fixture, export_publish_from_import_law --check still read
# verdict=UNRESOLVED rc=2 (comma_pub.py:6 receiver=CEPW module=(unbound)) and
# publish_relative_package_identity --check read the same UNRESOLVED, while
# export_publish_wire_identity read WIRE - so one spelling of one publisher
# read WIRE on one face and UNRESOLVED on another.
#
# This module adds no law. It owns ONE seam - which receiver table a face
# consults - and both sibling faces ask it at CALL time:
#
#   * the table itself is comma_binding_wire.bindings, asked at CALL time, so
#     the split of a comma list stays owned by the shipped splitter and no
#     import grammar is restated here (AC-PICBS1);
#   * for a file with no comma list that table is byte-identical to
#     export_publish_wire_identity.import_bindings (measured by that wire's
#     own parity count at R2426), so every non-comma row keeps every key
#     (AC-PICBS3, true by construction rather than by a second comparison);
#   * a receiver no import line binds still yields module "" and therefore
#     UNRESOLVED on both faces rather than being guessed (AC-PICBS4);
#   * the classification itself stays each face's own shipped call, and no
#     refusal code, exit code or printed line of either CLI is touched
#     (AC-PICBS5).
#
# The face reading this module publishes (`--check`) asks BOTH shipped faces
# over the same tree and prints each verdict with its own code path, so a
# split is visible as a set difference instead of being inferred from two
# separate logs (AC-PICBS2).
#
# This module writes nothing and reads no clock (AC-PICBS6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: comma_binding_sibling_faces.py --check [--root PATH] [--export NAME]
#                                     [--owner MODULE] [--wire MODULE]
#                                     [--package NAME] [--json]
#   exit 0 = FACES-AGREE or NO-PUBLISHER
#   exit 2 = FACES-SPLIT, naming each face and its verdict
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import json
import os
import sys

LABEL = "os-comma-binding-sibling-faces"
DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"
SELF_NAME = "comma_binding_sibling_faces.py"
SELF_TEST_NAME = "test_comma_binding_sibling_faces.py"

REPORT_KEYS = ("label", "verdict", "root", "package", "wire", "faces",
               "split", "detail")

FACE_KEYS = ("face", "verdict", "code", "publishers", "wire", "foreign",
             "unresolved", "no_publish")

AGREE = "FACES-AGREE"
SPLIT = "FACES-SPLIT"
NO_PUBLISHER = "NO-PUBLISHER"

WIRE = "WIRE"
FOREIGN = "FOREIGN"
UNRESOLVED = "UNRESOLVED"
NO_PUBLISH = "NO-PUBLISH"
EMPTY = "EMPTY"

USAGE = (
    "usage: comma_binding_sibling_faces.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--wire MODULE] [--package NAME] "
    "[--json]\n"
    "  --check        read every publisher on both sibling faces and compare\n"
    "  --root PATH    tree to read (default .)\n"
    "  --export NAME  export document basename (default status-export.json)\n"
    "  --owner MODULE module that owns the current export shape\n"
    "                 (default queue_floor_export_face)\n"
    "  --wire MODULE  module that proves the bytes before publishing\n"
    "                 (default closeout_export_parity_wire)\n"
    "  --package NAME package declared to the relative face (optional)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = FACES-AGREE or NO-PUBLISHER, 2 = FACES-SPLIT,\n"
    "  3 = root missing, 5 = bad flags\n"
)


class CommaBindingSiblingFacesError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def identity():
    """The module that owns the receiver table and the prose mask."""
    return importlib.import_module("export_publish_wire_identity")


def comma_wire():
    """The module that owns the comma-aware binding table and its splitter."""
    return importlib.import_module("comma_binding_wire")


def from_import_face():
    """The sibling face that reads a publish imported by name."""
    return importlib.import_module("export_publish_from_import_law")


def relative_face():
    """The sibling face that reads a package-relative publish."""
    return importlib.import_module("publish_relative_package_identity")


def receivers_for(lines):
    """The one receiver table every face consults, asked at CALL time.

    The comma-aware table is comma_binding_wire.bindings, asked here rather
    than restated; for a file with no comma list it equals the shipped
    import_bindings byte for byte, so a non-comma row cannot move.
    """
    code = identity().code_only(lines)
    return comma_wire().bindings(code)


def face_rows(report):
    """One published row per face, from that face's own report."""
    return {
        "face": report.get("label", ""),
        "verdict": report.get("verdict", ""),
        "code": 0 if report.get("verdict") in (WIRE, EMPTY) else 2,
        "publishers": len(report.get("publishers") or []),
        "wire": sorted(report.get("wire") or []),
        "foreign": sorted(report.get("foreign") or []),
        "unresolved": sorted(report.get("unresolved") or []),
        "no_publish": sorted(report.get("no_publish") or []),
    }


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER,
          wire_module=DEFAULT_WIRE, package=None):
    """Ask both sibling faces over one tree and compare what they answer."""
    if not os.path.isdir(root):
        raise CommaBindingSiblingFacesError("E_PICBS_NO_ROOT", root)
    law_report, law_code = from_import_face().audit(
        root, export_name, owner, wire_module)
    rel_report, rel_code = relative_face().audit(
        root, package, export_name, owner, wire_module)
    faces = [face_rows(law_report), face_rows(rel_report)]
    split = []
    for face, code in zip(faces, (law_code, rel_code)):
        if face["verdict"] != faces[0]["verdict"]:
            split.append({"face": face["face"], "verdict": face["verdict"],
                          "code": code})
    if all(face["publishers"] == 0 for face in faces):
        verdict = NO_PUBLISHER
    elif split:
        verdict = SPLIT
    else:
        verdict = AGREE
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "package": package or "",
        "wire": wire_module,
        "faces": faces,
        "split": split,
        "detail": [row for row in law_report.get("detail") or []] +
                  [row for row in rel_report.get("detail") or []] +
                  split,
    }
    return report, (2 if verdict == SPLIT else 0)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    export_name = DEFAULT_EXPORT_NAME
    owner = DEFAULT_OWNER
    wire_module = DEFAULT_WIRE
    package = None
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export", "--owner", "--wire", "--package"):
            index += 1
            if index >= len(argv):
                sys.stderr.write(
                    "E_PICBS_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            elif arg == "--export":
                export_name = argv[index]
            elif arg == "--owner":
                owner = argv[index]
            elif arg == "--wire":
                wire_module = argv[index]
            else:
                package = argv[index]
        else:
            sys.stderr.write("E_PICBS_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_PICBS_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, export_name, owner, wire_module, package)
    except CommaBindingSiblingFacesError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "COMMA BINDING SIBLING FACES %s verdict=%s root=%s package=%s "
            "wire_module=%s\n" % (
                report["label"], report["verdict"], report["root"],
                report["package"] or "(none)", report["wire"]))
        for face in report["faces"]:
            sys.stdout.write(
                "  FACE %s verdict=%s publishers=%d wire=%s foreign=%s "
                "unresolved=%s no_publish=%s\n" % (
                    face["face"], face["verdict"], face["publishers"],
                    ",".join(face["wire"]) or "(none)",
                    ",".join(face["foreign"]) or "(none)",
                    ",".join(face["unresolved"]) or "(none)",
                    ",".join(face["no_publish"]) or "(none)"))
        for row in report["split"]:
            sys.stdout.write("  SPLIT %s verdict=%s\n" % (
                row["face"], row["verdict"]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))