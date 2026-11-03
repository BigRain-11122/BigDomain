# export_publish_from_import_law.py - a publish imported BY NAME is a publish
# Criteria AC-EPBW1..AC-EPBW6 were pre-registered in state/queue/tech.md:463
# (the R2391 seed row) BEFORE this file existed.
#
# Why this exists: the routed-publish law is the guard's attribute call
# (`receiver.publish(...)`), so a script that does
#
#     from closeout_export_parity_wire import publish
#     ...
#     publish(".", EXPORT, text="{}")
#
# never matched, the script read NO-PUBLISH, and export_publish_wire_identity
# reported a current publisher that "publishes nothing". Measured at R2391 on
# a fixture while pinning AC-EPWI2b, and still true at HEAD before this module.
#
# This module owns ONE question, per line: is this line a publish OF THE EXPORT,
# and which module does the call bind? Three spellings are read:
#
#   attribute    `CEPW.publish(...)` - the guard's own law, asked at CALL time
#                (export_publish_path_guard.routed_publish), never restated
#   from_import  `publish(...)` or `ship(...)` where the file's OWN import lines
#                bind that local name to a module (`from M import publish
#                [as x]`); the module named is the one the import binds
#   bare         `publish(...)` that no import binds - UNRESOLVED, because
#                naming a module there would be a guess
#
# There is one import parser in the tree: the identity module owns the receiver
# table (import_bindings) and the from-import patterns (FROM_PLAIN_RE and
# FROM_AS_RE), and both are asked at CALL time here. This file adds no pattern
# of its own for an import line - it only asks the narrower question of those
# patterns ("which local names are bound to the imported name publish"), which
# the receiver table cannot answer because it keeps only the module. The prose
# mask is the identity module's code_only, so a publish spelled inside a
# docstring or a fixture literal is still not a call.
#
# The attribute spelling returns EXACTLY the receiver and module that module
# already returned, so every already-correct reading stays byte for byte
# (AC-EPBW2). A name imported as something else binds that alias, so renaming
# the import without the call reads UNRESOLVED rather than borrowing the old
# name (AC-EPBW4).
#
# A `def publish(` line is a definition, not a call, and is skipped; a script
# that only defines one never becomes a publisher by definition alone.
#
# This module writes nothing and reads no clock (AC-EPBW6). Source is pure
# ASCII, stdlib only, zero network.
#
# CLI: export_publish_from_import_law.py --check [--root PATH] [--export NAME]
#                                        [--owner MODULE] [--wire MODULE]
#                                        [--json]
#   exit 0 = WIRE (every publish resolves to the wire) or EMPTY
#   exit 2 = FOREIGN or UNRESOLVED, naming every script and line
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import json
import os
import re
import sys

LABEL = "os-export-publish-from-import-law"
DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"
SELF_NAME = "export_publish_from_import_law.py"
SELF_TEST_NAME = "test_export_publish_from_import_law.py"

REPORT_KEYS = ("label", "verdict", "root", "scanned", "publishers",
               "wire", "foreign", "unresolved", "no_publish",
               "from_import", "bare", "detail")

CALL_KEYS = ("kind", "receiver", "module", "state", "line", "text")

WIRE = "WIRE"
FOREIGN = "FOREIGN"
UNRESOLVED = "UNRESOLVED"
NO_PUBLISH = "NO-PUBLISH"
EMPTY = "EMPTY"

ATTR = "attribute"
FROM_IMPORT = "from_import"
BARE = "bare"

DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")
# A bare local-name call: not preceded by a dot (attribute) or a word char.
NAME_CALL_RE = re.compile(r"(?<![\w.])([A-Za-z_]\w*)\s*\(")

USAGE = (
    "usage: export_publish_from_import_law.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--wire MODULE] [--json]\n"
    "  --check         read every current publisher and its publish spelling\n"
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


class ExportPublishFromImportLawError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def guard():
    """The module that owns the attribute-publish and current-path laws."""
    return importlib.import_module("export_publish_path_guard")


def identity():
    """The module that owns the import patterns and the prose mask."""
    return importlib.import_module("export_publish_wire_identity")


def imported_publish_names(lines):
    """local name -> module for every `from M import publish [as x]` line.

    The patterns are the identity module's own (asked at call time), so there
    is one set of import-line regexes in the tree and no second parser here.
    """
    lead = identity()
    found = {}
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        matched = lead.FROM_AS_RE.match(line)
        if matched and matched.group(2) == "publish":
            found[matched.group(3)] = matched.group(1)
            continue
        matched = lead.FROM_PLAIN_RE.match(line)
        if matched and matched.group(2) == "publish":
            found["publish"] = matched.group(1)
    return found


def classify_line(line, receivers, publish_names,
                  export_name=DEFAULT_EXPORT_NAME, wire_module=DEFAULT_WIRE):
    """One publish call on this line, or None when the line is not one.

    The attribute spelling is the guard's decision and the callee is the
    identity module's reader, so neither half can drift from the shipped law:
    the same receiver, module and state as before.
    """
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    if not guard().names_export(line, export_name):
        return None
    defined = DEF_RE.match(line)
    if defined and defined.group(1) == "publish":
        return None
    if guard().routed_publish(line, export_name):
        receiver, module = identity().callee_of(line, receivers)
        kind = ATTR
    else:
        receiver = ""
        module = ""
        kind = ""
        for name in NAME_CALL_RE.findall(line):
            if name in publish_names:
                receiver = name
                module = publish_names[name]
                kind = FROM_IMPORT
                break
            if name == "publish":
                receiver = name
                module = ""
                kind = BARE
                break
        if not kind:
            return None
    if not module:
        state = UNRESOLVED
    elif module == wire_module:
        state = WIRE
    else:
        state = FOREIGN
    return {"kind": kind, "receiver": receiver, "module": module,
            "state": state}


def siblings():
    """The module that owns which receiver table every face consults."""
    return importlib.import_module("comma_binding_sibling_faces")


def classify_script(lines, export_name=DEFAULT_EXPORT_NAME,
                    wire_module=DEFAULT_WIRE):
    """Every publish call in one file, in file order, with its spelling."""
    lead = identity()
    code = lead.code_only(lines)
    # AC-PICBS1: the table choice is the sibling seam's, asked at CALL time, so
    # one spelling cannot read WIRE on the identity face and UNRESOLVED here.
    receivers = siblings().receivers_for(lines)
    publish_names = imported_publish_names(code)
    calls = []
    for number, line in enumerate(code, 1):
        call = classify_line(line, receivers, publish_names,
                             export_name, wire_module)
        if call is None:
            continue
        call["line"] = number
        call["text"] = line.strip()[:120]
        calls.append(call)
    return calls


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER,
          wire_module=DEFAULT_WIRE):
    """Read every current publisher and count how it spells its publish."""
    if not os.path.isdir(root):
        raise ExportPublishFromImportLawError("E_EPBW_NO_ROOT", root)
    scanner = guard()
    lead = identity()
    scanned = 0
    publishers = []
    wire = []
    foreign = []
    unresolved = []
    no_publish = []
    from_import = 0
    bare = 0
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
            if row["kind"] == FROM_IMPORT:
                from_import += 1
            elif row["kind"] == BARE:
                bare += 1
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
        "from_import": from_import,
        "bare": bare,
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
                sys.stderr.write("E_EPBW_BAD_FLAGS missing value for %s\n" % arg)
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
            sys.stderr.write("E_EPBW_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_EPBW_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, export_name, owner, wire_module)
    except ExportPublishFromImportLawError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "EXPORT PUBLISH FROM IMPORT LAW %s verdict=%s scanned=%d "
            "publishers=%d wire=%d foreign=%s unresolved=%s no_publish=%d "
            "from_import=%d bare=%d wire_module=%s\n" % (
                report["label"], report["verdict"], report["scanned"],
                len(report["publishers"]), len(report["wire"]),
                ",".join(report["foreign"]) or "(none)",
                ",".join(report["unresolved"]) or "(none)",
                len(report["no_publish"]), report["from_import"],
                report["bare"], wire_module))
        for row in report["detail"]:
            if row["state"] == WIRE:
                continue
            sys.stdout.write("  %s %s:%d kind=%s receiver=%s module=%s\n" % (
                row["state"], row["path"], row["line"], row["kind"],
                row["receiver"] or "(bare)", row["module"] or "(unbound)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))