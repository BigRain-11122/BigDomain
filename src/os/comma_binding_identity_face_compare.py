# comma_binding_identity_face_compare.py - all three publisher faces, one tree
#
# Criteria AC-PICIC1..AC-PICIC6 were pre-registered in the R2430 tech seed row
# of state/queue/tech.md (line 510) BEFORE this file existed.
#
# Why this exists: comma_binding_sibling_faces (R2430) compared the from-import
# face with the relative face only. MEASURED at R2430, the identity face
# reaches the comma-aware receiver table through a DIFFERENT seam -
# comma_binding_consumer_wire.wire_audit_script - so a regression on that one
# path could move the identity verdict while both sibling faces kept agreeing,
# and the split would be invisible in every reading the tree ships.
#
# This module adds no law and restates no table. It asks the three shipped
# faces at CALL time:
#
#   from-import : export_publish_from_import_law.audit
#   relative    : publish_relative_package_identity.audit
#   identity    : export_publish_wire_identity.audit
#
# and for each face it MEASURES which seam supplied the receiver table rather
# than asserting it: both seam providers are wrapped for the duration of that
# face's own audit and every call is counted, so the seam a face used is the
# seam that actually fired (AC-PICIC5). Every disagreement is published with
# the face name, its verdict and the seam calls behind it, so a one-path
# regression cannot hide behind an agreeing pair.
#
# This module writes nothing and reads no clock (AC-PICIC6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: comma_binding_identity_face_compare.py --check [--root PATH]
#                                             [--export NAME] [--owner MODULE]
#                                             [--wire MODULE] [--package NAME]
#                                             [--json]
#   exit 0 = FACES-AGREE or NO-PUBLISHER
#   exit 2 = FACES-SPLIT, naming each face, its verdict and its seam
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import json
import os
import sys

LABEL = "os-comma-binding-identity-face-compare"
DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"
SELF_NAME = "comma_binding_identity_face_compare.py"
SELF_TEST_NAME = "test_comma_binding_identity_face_compare.py"

FACE_SOURCE = "comma_binding_sibling_faces"
FACE_CONSUMER = "comma_binding_consumer_wire"
SEAM_SIBLING = "comma_binding_sibling_faces.receivers_for"
SEAM_IDENTITY = "comma_binding_consumer_wire.wire_audit_script"
SEAMS = (SEAM_SIBLING, SEAM_IDENTITY)

FACES = ("from-import", "relative", "identity")

REPORT_KEYS = ("label", "verdict", "root", "package", "wire", "faces",
               "split", "differences")

FACE_KEYS = ("face", "label", "verdict", "code", "publishers", "wire",
             "foreign", "unresolved", "no_publish", "seams", "rows")

AGREE = "FACES-AGREE"
SPLIT = "FACES-SPLIT"
NO_PUBLISHER = "NO-PUBLISHER"

USAGE = (
    "usage: comma_binding_identity_face_compare.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--wire MODULE] [--package NAME] "
    "[--json]\n"
    "  --check        ask every publisher face over one tree and compare\n"
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


class CommaBindingIdentityFaceCompareError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def face_modules():
    """The three shipped faces, imported at CALL time so nothing is frozen."""
    return (
        importlib.import_module("export_publish_from_import_law"),
        importlib.import_module("publish_relative_package_identity"),
        importlib.import_module("export_publish_wire_identity"),
    )


def seam_modules():
    """The two modules that can supply a receiver table, asked at CALL time."""
    return (importlib.import_module(FACE_SOURCE),
            importlib.import_module(FACE_CONSUMER))


def measure(call):
    """Run one face's own audit and measure which seam supplied its table.

    Both seam providers are wrapped for the duration of the call and every
    call is counted, so the recorded seam is the seam that fired rather than
    a claim about the source. Both wrappers delegate to the shipped
    functions unchanged, so a face's verdict cannot move because of this.
    """
    sibling_mod, consumer_mod = seam_modules()
    counts = dict((name, 0) for name in SEAMS)
    original_sibling = sibling_mod.receivers_for
    original_consumer = consumer_mod.wire_audit_script

    def sibling_seam(lines):
        counts[SEAM_SIBLING] += 1
        return original_sibling(lines)

    def consumer_seam(lines, export_name=DEFAULT_EXPORT_NAME,
                      wire_module=DEFAULT_WIRE):
        counts[SEAM_IDENTITY] += 1
        return original_consumer(lines, export_name, wire_module)

    sibling_mod.receivers_for = sibling_seam
    consumer_mod.wire_audit_script = consumer_seam
    try:
        report, code = call()
    finally:
        sibling_mod.receivers_for = original_sibling
        consumer_mod.wire_audit_script = original_consumer
    return report, code, counts


def face_row(name, report, code, counts):
    """One published row per face, from that face's own report."""
    return {
        "face": name,
        "label": report.get("label", ""),
        "verdict": report.get("verdict", ""),
        "code": code,
        "publishers": sorted(report.get("publishers") or []),
        "wire": sorted(report.get("wire") or []),
        "foreign": sorted(report.get("foreign") or []),
        "unresolved": sorted(report.get("unresolved") or []),
        "no_publish": sorted(report.get("no_publish") or []),
        "seams": [{"seam": seam, "calls": counts[seam]}
                  for seam in SEAMS if counts[seam]],
        "rows": list(report.get("detail") or []),
    }


def ask(root, export_name, owner, wire_module, package):
    """Ask all three faces over one tree, each with its seam measured."""
    law, relative, identity = face_modules()
    calls = (
        ("from-import",
         lambda: law.audit(root, export_name, owner, wire_module)),
        ("relative",
         lambda: relative.audit(root, package, export_name, owner,
                                wire_module)),
        ("identity",
         lambda: identity.audit(root, export_name, owner, wire_module)),
    )
    rows = []
    for name, call in calls:
        report, code, counts = measure(call)
        rows.append(face_row(name, report, code, counts))
    return rows


def differences_of(faces):
    """Every disagreement between the faces, each naming the face it is on."""
    differences = []
    verdicts = [row["verdict"] for row in faces]
    tally = {}
    for verdict in verdicts:
        tally[verdict] = tally.get(verdict, 0) + 1
    majority = None
    for verdict, count in tally.items():
        if count >= 2 and (majority is None or count > tally[majority]):
            majority = verdict
    for row in faces:
        if majority is None or row["verdict"] != majority:
            differences.append({"kind": "verdict", "face": row["face"],
                                "verdict": row["verdict"],
                                "code": row["code"]})
    every = set()
    for row in faces:
        every.update(row["publishers"])
    for row in faces:
        for name in row["publishers"]:
            others = [other for other in faces if other is not row]
            if all(name not in other["publishers"] for other in others):
                differences.append({"kind": "publisher", "face": row["face"],
                                    "publisher": name})
    return differences, majority


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER,
          wire_module=DEFAULT_WIRE, package=None):
    """Ask all three publisher faces over one tree and compare what they say."""
    if not os.path.isdir(root):
        raise CommaBindingIdentityFaceCompareError("E_PICIC_NO_ROOT", root)
    faces = ask(root, export_name, owner, wire_module, package)
    differences, majority = differences_of(faces)
    if all(not row["publishers"] for row in faces):
        verdict = NO_PUBLISHER
    elif differences:
        verdict = SPLIT
    else:
        verdict = AGREE
    split = [row for row in faces
             if majority is None or row["verdict"] != majority]
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "package": package or "",
        "wire": wire_module,
        "faces": faces,
        "split": split,
        "differences": differences,
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
                    "E_PICIC_BAD_FLAGS missing value for %s\n" % arg)
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
            sys.stderr.write("E_PICIC_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_PICIC_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, export_name, owner, wire_module, package)
    except CommaBindingIdentityFaceCompareError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "COMMA BINDING IDENTITY FACE COMPARE %s verdict=%s root=%s "
            "package=%s wire_module=%s\n" % (
                report["label"], report["verdict"], report["root"],
                report["package"] or "(none)", report["wire"]))
        for face in report["faces"]:
            sys.stdout.write(
                "  FACE %s verdict=%s publishers=%d seams=%s wire=%s "
                "foreign=%s unresolved=%s no_publish=%s\n" % (
                    face["face"], face["verdict"], len(face["publishers"]),
                    ",".join("%s:%d" % (row["seam"], row["calls"])
                             for row in face["seams"]) or "(none)",
                    ",".join(face["wire"]) or "(none)",
                    ",".join(face["foreign"]) or "(none)",
                    ",".join(face["unresolved"]) or "(none)",
                    ",".join(face["no_publish"]) or "(none)"))
        for row in report["differences"]:
            if row["kind"] == "verdict":
                sys.stdout.write("  SPLIT %s verdict=%s\n" % (
                    row["face"], row["verdict"]))
            else:
                sys.stdout.write("  SPLIT %s only-publisher=%s\n" % (
                    row["face"], row["publisher"]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))