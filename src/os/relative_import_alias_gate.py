# relative_import_alias_gate.py - which table binds a renamed publish import?
# Criteria AC-RIAG1..AC-RIAG6 were pre-registered in state/queue/tech.md:486
# (the R2402 seed row) BEFORE this file existed.
#
# Why this exists: three shipped tables answer three different alias questions
# and nothing said which one a reader meant, so the same line could read bound
# or unbound depending on which face looked at it. Measured at R2420 at HEAD,
# per line, before any code here:
#
#   line                                 receiver  absolute  relative
#   from some_wire import other as publish   BOUND  (none)    (none)
#   from .wire import other as publish       (none) (none)    (none)
#   from some_wire import publish as ship    BOUND  BOUND     (none)
#   from .wire import publish as ship        (none) (none)    BOUND
#   from some_wire import publish            BOUND  BOUND     (none)
#   from .wire import publish                (none) (none)    BOUND
#
#   receiver = export_publish_wire_identity.import_bindings (binds ANY
#              from-import local name - the table the attribute path uses)
#   absolute = export_publish_from_import_law.imported_publish_names
#              (binds a local name only when the imported name IS publish)
#   relative = relative_import_publish_binding.relative_publish_names
#              (same rule, but only for a package-relative module)
#
# The seed row claimed the absolute table binds the alias of ANY imported name
# and the relative table only `publish`. MEASURED: the absolute PUBLISH-NAME
# table does not bind `other as publish` at all - it is the RECEIVER table
# that does - and both publish-name tables require the imported name to be
# `publish`, so a renamed relative publish import is invisible to every
# publish-name table. That correction is named here rather than repeated, and
# this module reports what the tables actually answer instead of which side
# the seed expected.
#
# The product is ONE reading, per from-import line that mentions the name
# publish: the question each of the three tables answers, printed side by
# side, plus whether a publish-name table binds that local name at all. A line
# no publish-name table binds reads UNBOUND, and a file with any such line
# reads ASYMMETRIC - so a file can never read CLEAN while the tables disagree
# (AC-RIAG4), because disagreement is exactly what ASYMMETRIC means here.
#
# No table and no import pattern is restated: all three are imported and asked
# at CALL time, and even the line's SPELLING is answered by the relative
# module's own REL_PLAIN_RE / REL_AS_RE (its patterns, not copies).
#
# This module writes nothing and reads no clock (AC-RIAG6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: relative_import_alias_gate.py --check [--root PATH] [--json]
#   exit 0 = CLEAN or EMPTY
#   exit 2 = ASYMMETRIC, naming every line and all three answers
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import json
import os
import sys

LABEL = "os-relative-import-alias-gate"
SELF_NAME = "relative_import_alias_gate.py"
SELF_TEST_NAME = "test_relative_import_alias_gate.py"

TARGET = "publish"
BOUND = "BOUND"
UNBOUND = "UNBOUND"
CLEAN = "CLEAN"
ASYMMETRIC = "ASYMMETRIC"
EMPTY = "EMPTY"
ABSOLUTE = "absolute"
RELATIVE = "relative"
NEITHER = "neither"

FACES = ("receiver", "absolute", "relative")

REPORT_KEYS = ("label", "verdict", "root", "scanned", "files_with_imports",
               "bound_lines", "unbound_lines", "asymmetric_files", "detail")

CALL_KEYS = ("line", "text", "spelling", "imported", "local", "receiver",
             "absolute", "relative", "bound_by", "verdict")

USAGE = (
    "usage: relative_import_alias_gate.py --check [--root PATH] [--json]\n"
    "  --check      read every from-import that mentions publish and print\n"
    "               what the receiver, absolute and relative tables answer\n"
    "  --root PATH  tree to read (default .)\n"
    "  --json       emit one machine-readable object\n"
    "  exit 0 = CLEAN or EMPTY, 2 = ASYMMETRIC, 3 = root missing, "
    "5 = bad flags\n"
)


class RelativeImportAliasGateError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def identity():
    """The module that owns the receiver table and the import patterns."""
    return importlib.import_module("export_publish_wire_identity")


def parent():
    """The module that owns absolute from-import publish-name binding."""
    return importlib.import_module("export_publish_from_import_law")


def relative():
    """The module that owns relative publish-name binding."""
    return importlib.import_module("relative_import_publish_binding")


def guard():
    """The module that owns script discovery and line reading."""
    return importlib.import_module("export_publish_path_guard")


def mentions_publish(line):
    """True when the import tail names publish as the imported or local name."""
    text = line.strip()
    if not text.startswith("from ") or " import " not in " %s " % text:
        return False
    tail = text.split(" import ", 1)[1]
    return TARGET in tail.split()


def tail_names(line):
    """(imported, local) read from the import tail - a name read, not a table.

    A tail carrying `as` binds the alias; otherwise the imported name is the
    local name. Nothing here decides which table owns the line.
    """
    tail = line.strip().split(" import ", 1)[1]
    parts = tail.split()
    if len(parts) >= 3 and parts[-2] == "as":
        return parts[-3], parts[-1]
    return parts[0] if parts else "", parts[0] if parts else ""


def spelling_of(line):
    """absolute / relative / neither, asked of the relative module's patterns."""
    lead = relative()
    if lead.REL_AS_RE.match(line) or lead.REL_PLAIN_RE.match(line):
        return RELATIVE
    lead = identity()
    if lead.FROM_AS_RE.match(line) or lead.FROM_PLAIN_RE.match(line):
        return ABSOLUTE
    return NEITHER


def line_reading(line, number=0):
    """One from-import line with all three tables asked at CALL time."""
    receiver = identity().import_bindings([line])
    absolute = parent().imported_publish_names([line])
    rel = relative().relative_publish_names([line])
    bound_by = [name for name, table in (("receiver", receiver),
                                         ("absolute", absolute),
                                         ("relative", rel)) if table]
    imported, local = tail_names(line)
    if absolute or rel:
        verdict = BOUND
    else:
        verdict = UNBOUND
    return {
        "line": number,
        "text": line.strip()[:120],
        "spelling": spelling_of(line),
        "imported": imported,
        "local": local,
        "receiver": receiver,
        "absolute": absolute,
        "relative": rel,
        "bound_by": ",".join(bound_by) or "(none)",
        "verdict": verdict,
    }


def reading(lines):
    """Every from-import line of one file that mentions publish."""
    found = []
    for number, line in enumerate(lines, 1):
        if not mentions_publish(line):
            continue
        found.append(line_reading(line, number))
    return found


def verdict_of(rows):
    """EMPTY when nothing mentions publish, ASYMMETRIC on any UNBOUND line."""
    if not rows:
        return EMPTY
    for row in rows:
        if row["verdict"] == UNBOUND:
            return ASYMMETRIC
    return CLEAN


def audit(root):
    """Read every script under the root and report the alias asymmetry."""
    if not os.path.isdir(root):
        raise RelativeImportAliasGateError("E_RIAG_NO_ROOT", root)
    scanner = guard()
    scanned = 0
    files_with_imports = 0
    bound_lines = 0
    unbound_lines = 0
    asymmetric_files = []
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
        rows = reading(identity().code_only(lines))
        if not rows:
            continue
        files_with_imports += 1
        verdict = verdict_of(rows)
        if verdict == ASYMMETRIC:
            asymmetric_files.append(rel)
        for row in rows:
            if row["verdict"] == BOUND:
                bound_lines += 1
            else:
                unbound_lines += 1
            item = dict(row)
            item["path"] = rel
            detail.append(item)
    if unbound_lines:
        verdict = ASYMMETRIC
    elif bound_lines:
        verdict = CLEAN
    else:
        verdict = EMPTY
    report = {
        "label": LABEL,
        "verdict": verdict,
        "root": root,
        "scanned": scanned,
        "files_with_imports": files_with_imports,
        "bound_lines": bound_lines,
        "unbound_lines": unbound_lines,
        "asymmetric_files": sorted(asymmetric_files),
        "detail": detail,
    }
    return report, (2 if verdict == ASYMMETRIC else 0)


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
                sys.stderr.write("E_RIAG_BAD_FLAGS missing value for --root\n")
                return 5
            root = argv[index]
        else:
            sys.stderr.write("E_RIAG_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_RIAG_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root)
    except RelativeImportAliasGateError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "RELATIVE IMPORT ALIAS GATE %s verdict=%s scanned=%d "
            "files_with_imports=%d bound=%d unbound=%d asymmetric=%s\n" % (
                report["label"], report["verdict"], report["scanned"],
                report["files_with_imports"], report["bound_lines"],
                report["unbound_lines"],
                ",".join(report["asymmetric_files"]) or "(none)"))
        for row in report["detail"]:
            sys.stdout.write(
                "  %s %s:%d spelling=%s imported=%s local=%s receiver=%s "
                "absolute=%s relative=%s bound_by=%s\n" % (
                    row["verdict"], row["path"], row["line"],
                    row["spelling"], row["imported"] or "-",
                    row["local"] or "-",
                    json.dumps(row["receiver"], sort_keys=True),
                    json.dumps(row["absolute"], sort_keys=True),
                    json.dumps(row["relative"], sort_keys=True),
                    row["bound_by"]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))