# comma_binding_wire.py - a comma-list publisher finally RESOLVES
# Criteria AC-PICBW1..AC-PICBW6 were pre-registered in the R2424 tech seed row
# of state/queue/tech.md (line 490) BEFORE this file existed.
#
# Why this exists: plain_import_comma_binding (R2424) NAMED the blind spot but
# left it in place. Measured at R2424 and re-measured here at HEAD:
#
#   import os, some_wire as publish
#   ...
#   publish(".", EXPORT, text="{}")
#
# the shipped receiver table (export_publish_wire_identity.import_bindings)
# matches a plain import with an ANCHORED single-module pattern, so it binds
# {"os": "os"} and says nothing about the second module. callee_of therefore
# returns module "" for that call and the identity reading reports UNRESOLVED
# for a publisher that a bare `publish(` call would actually resolve.
#
# This module closes that one seam and adds no law of its own:
#
#   * the SPLIT of a comma list is asked of the shipped splitter
#     (plain_import_comma_binding.parts_of -> plain_import_alias_gate.plain_parts)
#     at CALL time, so nothing here restates an import grammar;
#   * the per-part question handed back to the table is the shipped
#     composition (plain_import_comma_binding.part_statement), not a new
#     string format;
#   * the receiver table itself is the identity module's import_bindings,
#     asked at CALL time;
#   * the callee is the identity module's own callee_of, so there is still
#     exactly one publish-call law in the tree.
#
# SCOPE, stated rather than guessed: every comma-separated plain import is
# re-read, not only one whose local name happens to be `publish`. The anchored
# pattern drops EVERY part after the first, so a publisher aliased there - the
# house spelling `import os, closeout_export_parity_wire as CEPW` followed by
# `CEPW.publish(...)` - cannot resolve either, and that is the shape this wire
# exists to fix. A bare `publish(...)` call is outside callee_of's attribute
# law and stays with the spelling law (export_publish_from_import_law); it is
# not re-specified here. A file with no comma list is answered by the shipped
# table alone, byte for byte, which is why AC-PICBW3 holds by construction.
#
# Not edited on purpose: export_publish_wire_identity.py. Its refusal codes,
# exit codes and printed lines stay exactly as they were, and AC-PICBW5 proves
# that against the HEAD copy of that module run as its own script.
#
# This module writes nothing and reads no clock (AC-PICBW6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: comma_binding_wire.py --check [--root PATH] [--json]
#   exit 0 = EMPTY (no comma-list publisher anywhere) or RESOLVED (all resolve)
#   exit 2 = UNRESOLVED, naming every comma-list publisher still unbound
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import json
import os
import sys

LABEL = "os-comma-binding-wire"
SELF_NAME = "comma_binding_wire.py"
SELF_TEST_NAME = "test_comma_binding_wire.py"

BOUND = "BOUND"
UNRESOLVED = "UNRESOLVED"
RESOLVED = "RESOLVED"
EMPTY = "EMPTY"

REPORT_KEYS = ("label", "verdict", "root", "scanned", "files_compared",
               "parity_files", "comma_files", "comma_lines",
               "resolved_lines", "unresolved_lines", "detail")

CALL_KEYS = ("line", "text", "receiver", "table_module", "wire_module",
             "state")

USAGE = (
    "usage: comma_binding_wire.py --check [--root PATH] [--json]\n"
    "  --check      read every comma-separated plain import that binds the\n"
    "               name publish and resolve its callee through the shipped\n"
    "               splitter and the shipped receiver table\n"
    "  --root PATH  tree to read (default .)\n"
    "  --json       emit one machine-readable object\n"
    "  exit 0 = EMPTY or RESOLVED, 2 = UNRESOLVED, 3 = root missing,\n"
    "  5 = bad flags\n"
)


class CommaBindingWireError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def identity():
    """The module that owns the receiver table, the callee law and the mask."""
    return importlib.import_module("export_publish_wire_identity")


def comma_module():
    """The module that owns the comma-list reading, its splitter and its parts."""
    return importlib.import_module("plain_import_comma_binding")


def guard():
    """The module that owns script discovery and line reading."""
    return importlib.import_module("export_publish_path_guard")


def comma_parts(line):
    """[(module, local)] for a comma-separated plain import, else [].

    Both questions are the shipped comma module's at CALL time: its
    is_comma_import owns the statement test and its parts_of owns the split.
    """
    shipped = comma_module()
    if not shipped.is_comma_import(line):
        return []
    return shipped.parts_of(line)


def bindings(lines):
    """alias -> module, with comma lists read part by part.

    The whole-statement answer is the shipped table's and is kept as it is;
    only the parts the anchored pattern drops are added, and only for a
    comma-separated statement. A file with no comma list is therefore
    answered exactly as the table answers it today (AC-PICBW3).
    """
    table = identity()
    merged = dict(table.import_bindings(lines))
    shipped = comma_module()
    for line in lines:
        parts = comma_parts(line)
        for module, local in parts:
            found = table.import_bindings([shipped.part_statement(module, local)])
            for name, target in found.items():
                if name not in merged:
                    merged[name] = target
    return merged


def resolve(line, wire_bindings, table_bindings=None):
    """{receiver, module, state} for the publish call on this line.

    The callee law is the identity module's own, so a receiver no import line
    binds keeps its module '' and reads UNRESOLVED rather than being guessed
    (AC-PICBW4). `table_bindings` is the answer to compare against; when it is
    not supplied the table face is reported as '' rather than mirrored from
    the wire, because a fabricated comparison would hide the difference.
    """
    receiver, module = identity().callee_of(line, wire_bindings)
    _table_receiver, table_module = identity().callee_of(
        line, table_bindings if table_bindings is not None else {})
    return {
        "receiver": receiver,
        "module": module,
        "table_module": table_module,
        "state": BOUND if module else UNRESOLVED,
    }


def script_rows(lines):
    """The publish calls of one file whose local name a comma list binds.

    Only those calls are read, because only those are the seam this wire
    closes; every other call keeps the identity module's reading untouched.
    """
    table = identity()
    code = table.code_only(lines)
    wire_bindings = bindings(code)
    table_bindings = table.import_bindings(code)
    publishers = set()
    for line in code:
        for _module, local in comma_parts(line):
            publishers.add(local)
    rows = []
    for number, line in enumerate(code, 1):
        receiver, _module = table.callee_of(line, wire_bindings)
        if not receiver or receiver not in publishers:
            continue
        row = resolve(line, wire_bindings, table_bindings)
        rows.append({
            "line": number,
            "text": line.strip()[:120],
            "receiver": row["receiver"],
            "table_module": row["table_module"],
            "wire_module": row["module"],
            "state": row["state"],
        })
    return rows


def audit(root):
    """Read every script under the root and resolve its comma-list publishers."""
    if not os.path.isdir(root):
        raise CommaBindingWireError("E_PICBW_NO_ROOT", root)
    scanner = guard()
    table = identity()
    scanned = 0
    files_compared = 0
    parity_files = 0
    comma_files = 0
    comma_lines = 0
    resolved_lines = 0
    unresolved_lines = 0
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
        code = table.code_only(lines)
        comma = [line for line in code if comma_parts(line)]
        files_compared += 1
        if not comma:
            # AC-PICBW3: no comma-list publisher -> the wire must answer
            # exactly what the table answers, for every binding of the file.
            if bindings(code) == table.import_bindings(code):
                parity_files += 1
            continue
        comma_files += 1
        for line in comma:
            comma_lines += 1
        for row in script_rows(lines):
            if row["state"] == BOUND:
                resolved_lines += 1
            else:
                unresolved_lines += 1
            item = dict(row)
            item["path"] = rel
            detail.append(item)
    if resolved_lines == 0 and unresolved_lines == 0:
        # Comma lists may exist, but no publish call is bound by one: there is
        # no publisher for this wire to resolve, and EMPTY says exactly that
        # instead of claiming a green catch.
        verdict = EMPTY
    elif unresolved_lines:
        verdict = UNRESOLVED
    else:
        verdict = RESOLVED
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "scanned": scanned,
        "files_compared": files_compared,
        "parity_files": parity_files,
        "comma_files": comma_files,
        "comma_lines": comma_lines,
        "resolved_lines": resolved_lines,
        "unresolved_lines": unresolved_lines,
        "detail": detail,
    }
    return report, (2 if verdict == UNRESOLVED else 0)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0

    root = "."
    as_json = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stderr.write("E_PICBW_BAD_FLAGS missing value for --root\n")
                return 5
            root = argv[index]
        else:
            sys.stderr.write("E_PICBW_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_PICBW_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root)
    except CommaBindingWireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "COMMA BINDING WIRE %s verdict=%s scanned=%d compared=%d "
            "parity=%d comma_files=%d comma_lines=%d resolved=%d "
            "unresolved=%d\n" % (
                report["label"], report["verdict"], report["scanned"],
                report["files_compared"], report["parity_files"],
                report["comma_files"], report["comma_lines"],
                report["resolved_lines"], report["unresolved_lines"]))
        for row in report["detail"]:
            sys.stdout.write(
                "  %s %s:%d receiver=%s table_module=%s wire_module=%s\n" % (
                    row["state"], row["path"], row["line"],
                    row["receiver"], row["table_module"] or "(unbound)",
                    row["wire_module"] or "(unbound)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))