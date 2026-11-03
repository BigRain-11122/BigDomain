# plain_import_alias_gate.py - what happens when publish is bound by a PLAIN import?
# Criteria AC-PIAG1..AC-PIAG6 were pre-registered in the R2420 tech seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: the shipped alias gate reads FROM-imports only, so the house
# idiom is outside its scope. Measured at R2420 at HEAD:
#
#   import closeout_export_parity_wire as publish
#
# binds publish in the receiver table (export_publish_wire_identity asks any
# import line) while BOTH publish-name tables answer {} and the from-import
# gate reads mentions_publish=False / spelling=neither - i.e. exactly the
# asymmetry the gate exists to name is invisible when it is spelled as a plain
# import, and every real publisher in src/os uses that spelling.
#
# The product is ONE reading, per plain-import statement that binds the local
# name publish: the question each of the three shipped tables answers, printed
# side by side, plus whether any publish-name table confirms the binding. A
# line no publish-name table binds reads UNBOUND.
#
# HONEST CORRECTION of the pre-registered wording: AC-PIAG4 was pinned as "no
# file reads CLEAN while a plain-import alias binds publish unbound". Measured
# at HEAD, neither publish-name table reads a plain import at ALL (they match
# from-import spellings only), so a plain-import publish binding is UNBOUND by
# construction and the word CLEAN is unreachable for this gate. Rather than
# ship a green word nobody can reach, this module's vocabulary is ASYMMETRIC
# (any file carrying such a line) and EMPTY (no such line anywhere) - a
# stronger reading than the pinned text asked for, and the pinned text's
# intent (a file can never report clean while the tables disagree) holds by
# construction.
#
# No table and no import pattern is restated: the three tables are imported and
# asked at CALL time, and the line's own spelling is answered by the receiver
# table's own IMPORT_AS_RE / IMPORT_PLAIN_RE (its patterns, not copies).
#
# This module writes nothing and reads no clock (AC-PIAG6). Source is pure
# ASCII, stdlib only, zero network, read-only.
#
# CLI: plain_import_alias_gate.py --check [--root PATH] [--json]
#   exit 0 = EMPTY, naming no plain-import publish binding
#   exit 2 = ASYMMETRIC, naming every line and all three answers
#   exit 3 = the root is missing or not a directory
#   exit 5 = the flags are bad

import importlib
import json
import os
import sys

LABEL = "os-plain-import-alias-gate"
SELF_NAME = "plain_import_alias_gate.py"
SELF_TEST_NAME = "test_plain_import_alias_gate.py"

TARGET = "publish"
BOUND = "BOUND"
UNBOUND = "UNBOUND"
ASYMMETRIC = "ASYMMETRIC"
EMPTY = "EMPTY"
PLAIN = "plain"
NEITHER = "neither"

FACES = ("receiver", "absolute", "relative")

REPORT_KEYS = ("label", "verdict", "root", "scanned", "files_with_imports",
               "bound_lines", "unbound_lines", "asymmetric_files", "detail")

CALL_KEYS = ("line", "text", "spelling", "imported", "local", "receiver",
             "absolute", "relative", "bound_by", "verdict")

USAGE = (
    "usage: plain_import_alias_gate.py --check [--root PATH] [--json]\n"
    "  --check      read every plain import that binds the name publish and\n"
    "               print what the receiver, absolute and relative tables say\n"
    "  --root PATH  tree to read (default .)\n"
    "  --json       emit one machine-readable object\n"
    "  exit 0 = EMPTY, 2 = ASYMMETRIC, 3 = root missing, 5 = bad flags\n"
)


class PlainImportAliasGateError(Exception):
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


def is_plain_import(line):
    """True for an `import ...` statement that is not a from-import."""
    text = line.strip()
    return text.startswith("import ") and not text.startswith("from ")


def plain_parts(line):
    """[(module, local)] for one plain import statement, split on commas.

    `import a.b` binds a; `import a.b as c` binds c; the tail is read here
    because a comma-separated statement carries one binding per comma.
    """
    text = line.strip()[len("import "):]
    found = []
    for chunk in text.split(","):
        part = chunk.strip()
        if not part:
            continue
        pieces = part.split()
        if len(pieces) >= 3 and pieces[-2] == "as":
            found.append((pieces[0], pieces[-1]))
        elif pieces:
            found.append((pieces[0], pieces[0].split(".")[0]))
    return found


def mentions_publish(line):
    """True when a plain import in this statement binds the local name publish."""
    if not is_plain_import(line):
        return False
    for _module, local in plain_parts(line):
        if local == TARGET:
            return True
    return False


def spelling_of(line):
    """plain when the receiver table's own patterns recognise the line."""
    lead = identity()
    if lead.IMPORT_AS_RE.match(line) or lead.IMPORT_PLAIN_RE.match(line):
        return PLAIN
    return NEITHER


def line_reading(line, number=0):
    """One plain-import line with all three tables asked at CALL time."""
    receiver = identity().import_bindings([line])
    absolute = parent().imported_publish_names([line])
    rel = relative().relative_publish_names([line])
    bound_by = [name for name, table in (("receiver", receiver),
                                         ("absolute", absolute),
                                         ("relative", rel)) if table]
    imported, local = "", ""
    for module, name in plain_parts(line):
        if name == TARGET:
            imported, local = module, name
            break
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
    """Every plain-import line of one file that binds the name publish."""
    found = []
    for number, line in enumerate(lines, 1):
        if not mentions_publish(line):
            continue
        found.append(line_reading(line, number))
    return found


def verdict_of(rows):
    """ASYMMETRIC on any UNBOUND row, EMPTY when this file binds nothing.

    A fully BOUND set cannot occur today (no publish-name table reads a plain
    import), so it reads EMPTY rather than inventing a clean word - see the
    header's honest correction of AC-PIAG4.
    """
    if not rows:
        return EMPTY
    if all(row["verdict"] == BOUND for row in rows):
        return EMPTY
    return ASYMMETRIC


def audit(root):
    """Read every script under the root and report the plain-import asymmetry."""
    if not os.path.isdir(root):
        raise PlainImportAliasGateError("E_PIAG_NO_ROOT", root)
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
                sys.stderr.write("E_PIAG_BAD_FLAGS missing value for --root\n")
                return 5
            root = argv[index]
        else:
            sys.stderr.write("E_PIAG_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_PIAG_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root)
    except PlainImportAliasGateError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "PLAIN IMPORT ALIAS GATE %s verdict=%s scanned=%d "
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