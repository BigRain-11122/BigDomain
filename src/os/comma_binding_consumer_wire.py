# comma_binding_consumer_wire.py - the identity path asks the comma-aware table
# Criteria AC-PICBC1..AC-PICBC6 were pre-registered in the R2426 tech seed row
# of state/queue/tech.md (line 491) BEFORE this file existed.
#
# Why this exists: comma_binding_wire (R2426) RESOLVES a comma-list publisher,
# but no shipped reading asked it. Measured at R2426 on one fixture, the wire
# read RESOLVED receiver=wiremod wire_module=some_wire while
# export_publish_wire_identity on the very same tree still answered
# EMPTY publishers=0 - the fix existed but sat on no face an operator reads.
#
# This module puts the comma-aware table on that face and adds no law:
#
#   * the receiver table for a file WITH a comma list is
#     comma_binding_wire.bindings, asked at CALL time (AC-PICBC1), so the
#     split stays owned by the shipped splitter and is never restated here;
#   * every line classification is export_publish_from_import_law.classify_line,
#     asked at CALL time with that table - there is still exactly one publish
#     spelling law in the tree;
#   * a file with NO comma list is answered by
#     export_publish_from_import_law.classify_script unchanged, so its rows are
#     byte for byte what they are today (AC-PICBC3, true by construction
#     rather than by a second comparison);
#   * the prose mask and the verdict vocabulary stay
#     export_publish_wire_identity's own, asked at CALL time.
#
# The refusal codes, exit codes and printed lines of the identity CLI never
# change (AC-PICBC5): this module only changes which table one seam consults,
# and the identity module keeps its own row keys and its own report shape.
#
# This module writes nothing and reads no clock (AC-PICBC6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: comma_binding_consumer_wire.py --check [--root PATH] [--export NAME]
#                                    [--owner MODULE] [--wire MODULE] [--json]
#   exit 0 = WIRE (every publisher resolves to the wire) or EMPTY
#   exit 2 = FOREIGN or UNRESOLVED, naming every script and line
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import json
import os
import sys

LABEL = "os-comma-binding-consumer-wire"
DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"
SELF_NAME = "comma_binding_consumer_wire.py"
SELF_TEST_NAME = "test_comma_binding_consumer_wire.py"

REPORT_KEYS = ("label", "verdict", "root", "scanned", "publishers",
               "wire", "foreign", "unresolved", "no_publish",
               "comma_files", "comma_lines", "detail")

CALL_KEYS = ("kind", "receiver", "module", "state", "line", "text")

WIRE = "WIRE"
FOREIGN = "FOREIGN"
UNRESOLVED = "UNRESOLVED"
NO_PUBLISH = "NO-PUBLISH"
EMPTY = "EMPTY"

USAGE = (
    "usage: comma_binding_consumer_wire.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--wire MODULE] [--json]\n"
    "  --check         resolve every current publisher through the\n"
    "                  comma-aware binding table\n"
    "  --root PATH     tree to read (default .)\n"
    "  --export NAME   export document basename (default status-export.json)\n"
    "  --owner MODULE  module that owns the current export shape\n"
    "                  (default queue_floor_export_face)\n"
    "  --wire MODULE   module that proves the bytes before publishing\n"
    "                  (default closeout_export_parity_wire)\n"
    "  --json          emit one machine-readable object\n"
    "  exit 0 = WIRE or EMPTY, 2 = FOREIGN or UNRESOLVED, "
    "3 = root missing, 5 = bad flags\n"
)


class CommaBindingConsumerWireError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def identity():
    """The module that owns the mask, the row keys and the verdict words."""
    return importlib.import_module("export_publish_wire_identity")


def comma_wire():
    """The module that owns the comma-aware binding table."""
    return importlib.import_module("comma_binding_wire")


def from_import_law():
    """The module that owns the publish spelling law and its import names."""
    return importlib.import_module("export_publish_from_import_law")


def guard():
    """The module that owns script discovery and line reading."""
    return importlib.import_module("export_publish_path_guard")


def has_comma(lines):
    """True when any line of this file is a comma-separated plain import.

    The test is comma_binding_wire.comma_parts asked at CALL time, so the
    statement grammar stays where it already lives.
    """
    for line in lines:
        if comma_wire().comma_parts(line):
            return True
    return False


def classify_script(lines, export_name=DEFAULT_EXPORT_NAME,
                    wire_module=DEFAULT_WIRE):
    """Every publish call in one file, resolved through the right table.

    A file with no comma list is handed to the shipped from-import law
    unchanged, so its rows are identical to today's by construction
    (AC-PICBC3). Only a file that carries a comma list is read here, and even
    then the classification is the shipped classify_line - this function owns
    the TABLE CHOICE and nothing else.
    """
    lead = identity()
    code = lead.code_only(lines)
    law = from_import_law()
    if not has_comma(code):
        return law.classify_script(lines, export_name, wire_module)
    receivers = comma_wire().bindings(code)
    publish_names = law.imported_publish_names(code)
    calls = []
    for number, line in enumerate(code, 1):
        call = law.classify_line(line, receivers, publish_names,
                                 export_name, wire_module)
        if call is None:
            continue
        call["line"] = number
        call["text"] = line.strip()[:120]
        calls.append(call)
    return calls


def wire_audit_script(lines, export_name=DEFAULT_EXPORT_NAME,
                      wire_module=DEFAULT_WIRE):
    """The seam export_publish_wire_identity.audit_script asks at CALL time."""
    return classify_script(lines, export_name, wire_module)


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER,
          wire_module=DEFAULT_WIRE):
    """Read every current publisher and resolve it through the comma table."""
    if not os.path.isdir(root):
        raise CommaBindingConsumerWireError("E_PICBC_NO_ROOT", root)
    scanner = guard()
    lead = identity()
    scanned = 0
    publishers = []
    wire = []
    foreign = []
    unresolved = []
    no_publish = []
    comma_files = 0
    comma_lines = 0
    detail = []
    mine = (SELF_NAME, SELF_TEST_NAME)
    for path in scanner.scan_scripts(root):
        scanned += 1
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if os.path.basename(rel) in mine:
            continue
        try:
            lines = scanner.read_lines(path)
        except (IOError, OSError):
            continue
        code = lead.code_only(lines)
        if not any(scanner.uses_owner(line, owner) for line in code):
            continue
        if has_comma(code):
            comma_files += 1
            for line in code:
                if comma_wire().comma_parts(line):
                    comma_lines += 1
        calls = classify_script(lines, export_name, wire_module)
        verdict = lead.verdict_of([row["state"] for row in calls])
        if verdict == NO_PUBLISH:
            no_publish.append(rel)
            continue
        publishers.append(rel)
        if verdict == WIRE:
            wire.append(rel)
        elif verdict == FOREIGN:
            foreign.append(rel)
        else:
            unresolved.append(rel)
        for row in calls:
            item = dict(row)
            item["path"] = rel
            detail.append(item)
    if foreign:
        verdict = FOREIGN
    elif unresolved:
        verdict = UNRESOLVED
    elif wire:
        verdict = WIRE
    else:
        verdict = EMPTY
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "scanned": scanned,
        "publishers": sorted(publishers),
        "wire": sorted(wire),
        "foreign": sorted(foreign),
        "unresolved": sorted(unresolved),
        "no_publish": sorted(no_publish),
        "comma_files": comma_files,
        "comma_lines": comma_lines,
        "detail": detail,
    }
    return report, (2 if verdict in (FOREIGN, UNRESOLVED) else 0)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    export_name = DEFAULT_EXPORT_NAME
    owner = DEFAULT_OWNER
    wire_module = DEFAULT_WIRE
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export", "--owner", "--wire"):
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_PICBC_BAD_FLAGS missing value for %s\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            elif arg == "--export":
                export_name = argv[index]
            elif arg == "--owner":
                owner = argv[index]
            else:
                wire_module = argv[index]
        else:
            sys.stderr.write("E_PICBC_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_PICBC_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, export_name, owner, wire_module)
    except CommaBindingConsumerWireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "COMMA BINDING CONSUMER WIRE %s verdict=%s scanned=%d "
            "publishers=%d wire=%d foreign=%s unresolved=%s no_publish=%d "
            "comma_files=%d comma_lines=%d wire_module=%s\n" % (
                report["label"], report["verdict"], report["scanned"],
                len(report["publishers"]), len(report["wire"]),
                ",".join(report["foreign"]) or "(none)",
                ",".join(report["unresolved"]) or "(none)",
                len(report["no_publish"]), report["comma_files"],
                report["comma_lines"], wire_module))
        for row in report["detail"]:
            if row["state"] == WIRE:
                continue
            sys.stdout.write("  %s %s:%d kind=%s receiver=%s module=%s\n" % (
                row["state"], row["path"], row["line"], row["kind"],
                row["receiver"] or "(bare)", row["module"] or "(unbound)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))