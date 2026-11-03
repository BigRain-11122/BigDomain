# relative_import_publish_binding.py - a RELATIVE import binds its name too
# Criteria AC-RIPB1..AC-RIPB6 were pre-registered in state/queue/tech.md:465
# (the R2400 seed row) BEFORE this file existed.
#
# Why this exists: the from-import spelling law reads `from M import publish`,
# and the identity module's own patterns require a DOTTED module name after
# `from` (FROM_PLAIN_RE / FROM_AS_RE both start the module group with
# [A-Za-z_]). Measured at R2400 on a fixture, so a PACKAGE-RELATIVE import
#
#     from . import publish
#     ...
#     publish(".", EXPORT, text="{}")
#
# matched nothing, the call read kind=bare state=UNRESOLVED, and a real
# package-internal publisher was reported as an unbound call - the false
# negative that reads a publisher as an unknown one.
#
# This module adds ONE notion and no second classifier: the local name a
# RELATIVE import binds, with the module text exactly as the file wrote it
# (".wire", "..", ".a.b") - never an absolute module this law invented. The
# absolute table stays the parent law's own, asked at CALL time, and every
# call is classified by the parent law's classify_line with the merged name
# table, so the attribute half is still the guard's law and the prose mask is
# still the identity module's code_only.
#
# A bound relative call reads state RELATIVE, a distinct word from FOREIGN and
# from UNRESOLVED: the import DID bind the name, but the module it binds is
# relative to a package this law cannot resolve from one file, so it is named
# rather than guessed - that is the "refuses naming the relative form it
# cannot place" branch of the seed, chosen over inventing an absolute module.
#
# The alias law holds in the relative case exactly as in the absolute one: the
# local name is the ALIAS, so `from .wire import publish as ship` binds ship
# and a bare `publish(` still reads bare (AC-RIPB3).
#
# This module writes nothing and reads no clock (AC-RIPB6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: relative_import_publish_binding.py --check [--root PATH]
#                                        [--export NAME] [--owner MODULE]
#                                        [--wire MODULE] [--json]
#   exit 0 = WIRE (every publish resolves to the wire) or EMPTY
#   exit 2 = FOREIGN, UNRESOLVED or RELATIVE, naming every script and line
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import json
import os
import re
import sys

LABEL = "os-relative-import-publish-binding"
DEFAULT_WIRE = "closeout_export_parity_wire"
DEFAULT_EXPORT_NAME = "status-export.json"
DEFAULT_OWNER = "queue_floor_export_face"
SELF_NAME = "relative_import_publish_binding.py"
SELF_TEST_NAME = "test_relative_import_publish_binding.py"

RELATIVE = "RELATIVE"

REPORT_KEYS = ("label", "verdict", "root", "scanned", "publishers",
               "wire", "foreign", "unresolved", "relative", "no_publish",
               "from_import", "bare", "detail")

CALL_KEYS = ("kind", "receiver", "module", "state", "line", "relative",
             "text")

# A relative module group is one or two dots followed by an optional dotted
# tail: ".", "..", ".wire", "..wire.sub". The absolute patterns cannot match
# any of these because they require a word character first, so the two tables
# are disjoint by construction and the merge below can never overwrite an
# absolute binding with a relative one by accident.
REL_PLAIN_RE = re.compile(
    r"^\s*from\s+(\.{1,2}(?:[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)?)"
    r"\s+import\s+([A-Za-z_]\w*)")
REL_AS_RE = re.compile(
    r"^\s*from\s+(\.{1,2}(?:[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)?)"
    r"\s+import\s+([A-Za-z_]\w*)\s+as\s+([A-Za-z_]\w*)")

USAGE = (
    "usage: relative_import_publish_binding.py --check [--root PATH] "
    "[--export NAME] [--owner MODULE] [--wire MODULE] [--json]\n"
    "  --check         read every current publisher and its publish spelling\n"
    "  --root PATH     tree to read (default .)\n"
    "  --export NAME   export document basename (default status-export.json)\n"
    "  --owner MODULE  module that owns the current export shape\n"
    "                  (default queue_floor_export_face)\n"
    "  --wire MODULE   module that proves the bytes before publishing\n"
    "                  (default closeout_export_parity_wire)\n"
    "  --json          emit one machine-readable object\n"
    "  exit 0 = WIRE or EMPTY, 2 = FOREIGN, UNRESOLVED or RELATIVE, "
    "3 = root missing, 5 = bad flags\n"
)


class RelativeImportPublishBindingError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def parent():
    """The module that owns absolute from-import binding and the classifier."""
    return importlib.import_module("export_publish_from_import_law")


def guard():
    """The module that owns the attribute-publish and current-path laws."""
    return importlib.import_module("export_publish_path_guard")


def identity():
    """The module that owns the import patterns and the prose mask."""
    return importlib.import_module("export_publish_wire_identity")


def relative_publish_names(lines):
    """local name -> relative module text for `from .[m] import publish [as x]`.

    The local name is the ALIAS when the line carries one, so renaming the
    import without renaming the call leaves the call bare (AC-RIPB3).
    """
    found = {}
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        matched = REL_AS_RE.match(line)
        if matched:
            if matched.group(2) == "publish":
                found[matched.group(3)] = matched.group(1)
            continue
        matched = REL_PLAIN_RE.match(line)
        if matched and matched.group(2) == "publish":
            found["publish"] = matched.group(1)
    return found


def imported_publish_names(lines):
    """The absolute table (parent law, at call time) plus the relative one.

    The two pattern families are disjoint (an absolute module starts with a
    word character, a relative one with a dot), so no entry is lost; where a
    file binds the SAME local name twice the relative line wins, because it is
    the binding this module exists to read.
    """
    merged = parent().imported_publish_names(lines)
    merged.update(relative_publish_names(lines))
    return merged


def classify_line(line, receivers, publish_names,
                  export_name=DEFAULT_EXPORT_NAME, wire_module=DEFAULT_WIRE):
    """One publish call on this line, or None - the parent law's decision.

    The parent law owns the spelling test, the two-sided import/call agreement
    and the absolute module table; this file only supplies the merged name
    table and turns a bound-but-unplaceable relative module into RELATIVE.
    """
    row = parent().classify_line(line, receivers, publish_names,
                                export_name, wire_module)
    if row is None:
        return None
    module = row["module"]
    if row["kind"] == "from_import" and module.startswith("."):
        row["state"] = RELATIVE
        row["relative"] = True
    else:
        row["relative"] = False
    return row


def verdict_of(states):
    """UNRESOLVED outranks FOREIGN, which outranks RELATIVE, which outranks
    WIRE; nothing at all is the identity module's NO-PUBLISH word."""
    if not states:
        return identity().NO_PUBLISH
    for state in (identity().UNRESOLVED, identity().FOREIGN, RELATIVE):
        if state in states:
            return state
    return identity().WIRE


def classify_script(lines, export_name=DEFAULT_EXPORT_NAME,
                    wire_module=DEFAULT_WIRE):
    """Every publish call in one file, in file order, with its spelling."""
    lead = identity()
    code = lead.code_only(lines)
    # AC-PICBS1: the receiver table is the sibling seam's, asked at CALL time,
    # so a comma-list publisher cannot read UNRESOLVED here while the identity
    # face reads WIRE. A file with no comma list gets the very same table.
    receivers = importlib.import_module(
        "comma_binding_sibling_faces").receivers_for(lines)
    publish_names = imported_publish_names(code)
    calls = []
    for number, line in enumerate(code, 1):
        call = classify_line(line, receivers, publish_names,
                             export_name, wire_module)
        if call is None:
            continue
        calls.append({
            "kind": call["kind"],
            "receiver": call["receiver"],
            "module": call["module"],
            "state": call["state"],
            "line": number,
            "relative": call["relative"],
            "text": line.strip()[:120],
        })
    return calls


def audit(root, export_name=DEFAULT_EXPORT_NAME, owner=DEFAULT_OWNER,
          wire_module=DEFAULT_WIRE):
    """Read every current publisher and count how it spells its publish."""
    if not os.path.isdir(root):
        raise RelativeImportPublishBindingError("E_RIPB_NO_ROOT", root)
    scanner = guard()
    lead = identity()
    scanned = 0
    publishers = []
    wire = []
    foreign = []
    unresolved = []
    relative = []
    no_publish = []
    from_import = 0
    bare = 0
    relative_calls = 0
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
        verdict = verdict_of([row["state"] for row in calls])
        if verdict == lead.NO_PUBLISH:
            no_publish.append(rel)
            continue
        publishers.append(rel)
        if verdict == lead.WIRE:
            wire.append(rel)
        elif verdict == lead.FOREIGN:
            foreign.append(rel)
        elif verdict == RELATIVE:
            relative.append(rel)
        else:
            unresolved.append(rel)
        for row in calls:
            if row["kind"] == "from_import":
                from_import += 1
            elif row["kind"] == "bare":
                bare += 1
            if row["relative"]:
                relative_calls += 1
            item = dict(row)
            item["path"] = rel
            detail.append(item)
    if unresolved:
        verdict = lead.UNRESOLVED
    elif foreign:
        verdict = lead.FOREIGN
    elif relative:
        verdict = RELATIVE
    elif wire:
        verdict = lead.WIRE
    else:
        verdict = lead.EMPTY
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "scanned": scanned,
        "publishers": sorted(publishers),
        "wire": sorted(wire),
        "foreign": sorted(foreign),
        "unresolved": sorted(unresolved),
        "relative": relative_calls,
        "no_publish": sorted(no_publish),
        "from_import": from_import,
        "bare": bare,
        "detail": detail,
    }
    return report, (2 if verdict in (lead.FOREIGN, lead.UNRESOLVED,
                                     RELATIVE) else 0)


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
                sys.stderr.write("E_RIPB_BAD_FLAGS missing value for %s\n" % arg)
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
            sys.stderr.write("E_RIPB_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_RIPB_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root, export_name, owner, wire_module)
    except RelativeImportPublishBindingError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "RELATIVE IMPORT PUBLISH BINDING %s verdict=%s scanned=%d "
            "publishers=%d wire=%d foreign=%s unresolved=%s relative=%d "
            "no_publish=%d from_import=%d bare=%d wire_module=%s\n" % (
                report["label"], report["verdict"], report["scanned"],
                len(report["publishers"]), len(report["wire"]),
                ",".join(report["foreign"]) or "(none)",
                ",".join(report["unresolved"]) or "(none)",
                report["relative"], len(report["no_publish"]),
                report["from_import"], report["bare"], wire_module))
        for row in report["detail"]:
            if row["state"] == identity().WIRE:
                continue
            sys.stdout.write("  %s %s:%d kind=%s receiver=%s module=%s\n" % (
                row["state"], row["path"], row["line"], row["kind"],
                row["receiver"] or "(bare)", row["module"] or "(unbound)"))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))