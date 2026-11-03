"""plain_import_comma_binding - the comma-list blind spot of the receiver table.

Criteria AC-PICB1..AC-PICB6 were pinned inside the R2422 tech seed row of
state/queue/tech.md (line 489) BEFORE this code existed.

The measured defect: export_publish_wire_identity.import_bindings matches a
plain import with an ANCHORED single-module pattern, so at HEAD
`import os, some_wire as publish` binds {"os": "os"} and says nothing about
the second module. A bare `publish(` call on such a line therefore cannot
resolve, and the alias asymmetry the two shipped gates exist to name is
invisible even on the RECEIVER side - the side that was supposed to see it.

What this module adds is exactly one thing: it asks the SHIPPED splitter
(plain_import_alias_gate.plain_parts) for the parts of a statement, asks the
SHIPPED receiver table (export_publish_wire_identity.import_bindings) once for
the whole statement and once per part, and prints both answers side by side
together with the two publish-name tables. No import pattern and no splitter
is restated here: the split law belongs to the alias gate, the table law to
the identity module, and both are imported at CALL time so patching either one
moves this reading.

The one thing this file composes is the per-part question it hands the table
("import <module> as <local>"), which is the split result written back out -
never a second grammar.

CLI: plain_import_comma_binding.py --check [--root PATH] [--json]
  exit 0 = EMPTY, naming no comma-list publish binding
  exit 2 = ASYMMETRIC, naming every such line with both receiver answers
  exit 3 = the root is missing or not a directory
  exit 5 = the flags are bad

Stdlib only, ASCII source, zero network, no clock, writes nothing.
"""

import importlib
import json
import os
import sys

LABEL = "os-plain-import-comma-binding"
SELF_NAME = "plain_import_comma_binding.py"
SELF_TEST_NAME = "test_plain_import_comma_binding.py"

TARGET = "publish"
BOUND = "BOUND"
UNBOUND = "UNBOUND"
ASYMMETRIC = "ASYMMETRIC"
EMPTY = "EMPTY"

REPORT_KEYS = ("label", "verdict", "root", "scanned", "comma_lines",
               "files_with_comma_bindings", "bound_lines", "unbound_lines",
               "dropped_parts", "asymmetric_files", "detail")

CALL_KEYS = ("line", "text", "part_count", "publish_parts", "receiver",
             "receiver_parts", "dropped", "absolute", "relative", "verdict")

USAGE = (
    "usage: plain_import_comma_binding.py --check [--root PATH] [--json]\n"
    "  --check      read every comma-separated plain import that binds the\n"
    "               name publish and print the whole-statement receiver\n"
    "               answer beside the per-part one\n"
    "  --root PATH  tree to read (default .)\n"
    "  --json       emit one machine-readable object\n"
    "  exit 0 = EMPTY, 2 = ASYMMETRIC, 3 = root missing, 5 = bad flags\n"
)


class PlainImportCommaBindingError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def alias_gate():
    """The module that owns the plain-import splitter and the plain-import test."""
    return importlib.import_module("plain_import_alias_gate")


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


def is_comma_import(line):
    """True for a plain import statement that carries a comma list.

    Both questions are asked of the shipped alias gate at CALL time: its
    is_plain_import owns the statement test, and the comma is read here only
    because the splitter is about to be asked for the parts.
    """
    text = line.strip()
    return alias_gate().is_plain_import(line) and "," in text


def parts_of(line):
    """[(module, local)] for one comma list, from the SHIPPED splitter."""
    return alias_gate().plain_parts(line)


def part_statement(module, local):
    """The per-part question handed to the receiver table.

    This is the split result written back out as one statement, so the table
    is asked the same grammar it already owns - no pattern is copied here.
    """
    return "import %s as %s" % (module, local)


def part_bindings(parts):
    """Merged receiver binding of the parts, each asked separately."""
    merged = {}
    for module, local in parts:
        merged.update(identity().import_bindings([part_statement(module, local)]))
    return merged


def line_reading(line, number=0):
    """One comma-list line with the whole-statement answer beside the part one."""
    parts = parts_of(line)
    receiver = identity().import_bindings([line])
    receiver_parts = part_bindings(parts)
    publish_parts = [module for module, local in parts if local == TARGET]
    dropped = sorted(name for name in receiver_parts if name not in receiver)
    absolute = parent().imported_publish_names([line])
    rel = relative().relative_publish_names([line])
    if absolute or rel:
        verdict = BOUND
    else:
        verdict = UNBOUND
    return {
        "line": number,
        "text": line.strip()[:120],
        "part_count": len(parts),
        "publish_parts": ",".join(publish_parts) or "(none)",
        "receiver": receiver,
        "receiver_parts": receiver_parts,
        "dropped": ",".join(dropped) or "(none)",
        "absolute": absolute,
        "relative": rel,
        "verdict": verdict,
    }


def reading(lines):
    """Every comma-list plain import that binds the name publish."""
    found = []
    for number, line in enumerate(lines, 1):
        if not is_comma_import(line):
            continue
        rows = line_reading(line, number)
        if rows["publish_parts"] == "(none)":
            continue
        found.append(rows)
    return found


def verdict_of(rows):
    """ASYMMETRIC on any UNBOUND row, EMPTY when the file binds nothing.

    A BOUND row can only occur when a publish-name table reads the line, which
    no table does today; the word is kept so the reading stays honest if that
    ever changes.
    """
    if not rows:
        return EMPTY
    if all(row["verdict"] == BOUND for row in rows):
        return EMPTY
    return ASYMMETRIC


def audit(root):
    """Read every script under the root and report the comma-list asymmetry."""
    if not os.path.isdir(root):
        raise PlainImportCommaBindingError("E_PICB_NO_ROOT", root)
    scanner = guard()
    scanned = 0
    files_with_comma_bindings = 0
    bound_lines = 0
    unbound_lines = 0
    dropped_parts = 0
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
        files_with_comma_bindings += 1
        if verdict_of(rows) == ASYMMETRIC:
            asymmetric_files.append(rel)
        for row in rows:
            if row["verdict"] == BOUND:
                bound_lines += 1
            else:
                unbound_lines += 1
            if row["dropped"] != "(none)":
                dropped_parts += len(row["dropped"].split(","))
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
        "comma_lines": bound_lines + unbound_lines,
        "files_with_comma_bindings": files_with_comma_bindings,
        "bound_lines": bound_lines,
        "unbound_lines": unbound_lines,
        "dropped_parts": dropped_parts,
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
                sys.stderr.write("E_PICB_BAD_FLAGS missing value for --root\n")
                return 5
            root = argv[index]
        else:
            sys.stderr.write("E_PICB_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
        index += 1

    if not saw_check:
        sys.stderr.write("E_PICB_BAD_FLAGS --check is required\n")
        return 5

    try:
        report, code = audit(root)
    except PlainImportCommaBindingError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "PLAIN IMPORT COMMA BINDING %s verdict=%s scanned=%d "
            "comma_lines=%d files=%d bound=%d unbound=%d dropped=%d "
            "asymmetric=%s\n" % (
                report["label"], report["verdict"], report["scanned"],
                report["comma_lines"], report["files_with_comma_bindings"],
                report["bound_lines"], report["unbound_lines"],
                report["dropped_parts"],
                ",".join(report["asymmetric_files"]) or "(none)"))
        for row in report["detail"]:
            sys.stdout.write(
                "  %s %s:%d parts=%d publish_parts=%s receiver=%s "
                "receiver_parts=%s dropped=%s absolute=%s relative=%s\n" % (
                    row["verdict"], row["path"], row["line"],
                    row["part_count"], row["publish_parts"],
                    json.dumps(row["receiver"], sort_keys=True),
                    json.dumps(row["receiver_parts"], sort_keys=True),
                    row["dropped"],
                    json.dumps(row["absolute"], sort_keys=True),
                    json.dumps(row["relative"], sort_keys=True)))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))