# closeout_export_parity_wire_binding_consumer.py - name every caller of the
# parity wire and say whether its bytes are its own composition.
# Criteria AC-CEPB1..AC-CEPB6 were pre-registered in state/queue/tech.md:702
# (the R2501 seed row) BEFORE this file existed.
#
# Why this exists: R2501 shipped closeout_export_parity_text_binding, which
# proves a handed-in text really is the document's own composition - but only
# for callers that CHOOSE to ask it. MEASURED in that row: twelve closeout
# scripts hand their own composed text straight to
# closeout_export_parity_wire.publish and not one of them asks the binding, so
# the guard only protects the callers that opt in.
#
# This face is the missing census. It DERIVES the caller set from the shipped
# tree at CALL time (AC-CEPB1) - never a hardcoded list, and never a regex over
# the bytes, because a file that only PRINTS a publish call inside a string
# literal is not a caller and a regex cannot tell the difference. Each real
# caller is reported:
#   BOUND        - it hands in the document's own composition (the export it
#                  publishes is the document it read); the caller's bytes are
#                  left exactly as they are (AC-CEPB2).
#   UNBOUND      - its text is another document's composition; the file and the
#                  FIRST DIFFERING FIELD are named and the caller is NOT run
#                  (AC-CEPB3).
#   OUT-OF-SCOPE - the file never calls the wire publish, and it is named with
#                  that verdict rather than dropped from the count (AC-CEPB4).
# The whole reading writes nothing and reads no clock (AC-CEPB5), is pure
# ASCII and stdlib only (AC-CEPB6).
#
# CLI: closeout_export_parity_wire_binding_consumer.py --check [--root PATH]
#              [--doc PATH] [--json] [--fail-on-unbound]
#   exit 0 = measured (clean or unbound rows reported)
#   exit 2 = unbound rows found and --fail-on-unbound was asked
#   exit 3 = the root or its src/os directory is missing
#   exit 5 = the flags are bad

import ast
import io
import json
import os
import sys
import warnings

LABEL = "os-closeout-export-parity-wire-binding-consumer"
WIRE = "closeout_export_parity_wire"
OS_DIR = os.path.join("src", "os")
DEFAULT_DOC = os.path.join("docs", "status-export.json")
SELF = "closeout_export_parity_wire_binding_consumer.py"
OWN_SUITE = "test_closeout_export_parity_wire_binding_consumer.py"

BOUND = "BOUND"
UNBOUND = "UNBOUND"
OUT_OF_SCOPE = "OUT-OF-SCOPE"

REPORT_KEYS = ("label", "verdict", "root", "doc", "scanned", "bound",
               "unbound", "out_of_scope", "unparsed", "rows")

USAGE = (
    "usage: closeout_export_parity_wire_binding_consumer.py --check "
    "[--root PATH] [--doc PATH]\n"
    "       [--json] [--fail-on-unbound]\n"
    "  --check            derive the wire caller set and name each binding\n"
    "  --root PATH        repository root to scan (default .)\n"
    "  --doc PATH         export document the wire publishes "
    "(default docs/status-export.json)\n"
    "  --json             emit one machine-readable object\n"
    "  --fail-on-unbound  exit 2 when any caller reads UNBOUND\n"
    "  exit 0 = measured, 2 = unbound gated, 3 = missing root, 5 = bad flags\n"
)


class BindingConsumerError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code,
                                                                    detail))
        self.code = code
        self.detail = detail


def read(root=".", doc=DEFAULT_DOC):
    """Derive the caller set from the tree at CALL time and name every row."""
    if not os.path.isdir(root):
        raise BindingConsumerError("E_CEPB_ROOT", root)
    folder = os.path.join(root, OS_DIR)
    if not os.path.isdir(folder):
        raise BindingConsumerError("E_CEPB_ROOT", folder)
    doc_path = doc if os.path.isabs(doc) else os.path.join(root, doc)
    doc_name = os.path.basename(doc_path)
    export = _load(doc_path)
    rows = []
    unparsed = []
    scanned = 0
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py"):
            continue
        if name in (SELF, OWN_SUITE, WIRE + ".py"):
            continue
        scanned += 1
        path = os.path.join(folder, name)
        try:
            text = io.open(path, "r", encoding="utf-8").read()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tree = ast.parse(text)
        except (SyntaxError, UnicodeDecodeError, IOError):
            unparsed.append(name)
            continue
        rows.extend(_rows_for(name, tree, doc_name, export, root))
    bound = sum(1 for row in rows if row["verdict"] == BOUND)
    unbound = sum(1 for row in rows if row["verdict"] == UNBOUND)
    out = sum(1 for row in rows if row["verdict"] == OUT_OF_SCOPE)
    return {
        "label": LABEL,
        "verdict": "CLEAN" if unbound == 0 else "UNBOUND-PRESENT",
        "root": root,
        "doc": doc_name,
        "scanned": scanned,
        "bound": bound,
        "unbound": unbound,
        "out_of_scope": out,
        "unparsed": unparsed,
        "rows": rows,
    }


def _load(path):
    """The export document on disk, or an empty object when it is missing."""
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (IOError, OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _rows_for(name, tree, doc_name, export, root):
    """Every wire publish call in one file, plus its OUT-OF-SCOPE row."""
    aliases, bare = _wire_names(tree)
    calls = _publish_calls(tree, aliases, bare)
    if not calls:
        return [_row(name, 0, OUT_OF_SCOPE, "no wire publish call", "",
                     "(none)")]
    docs = _loaded_documents(tree)
    constants = _path_constants(tree)
    rows = []
    for node in calls:
        rows.append(_classify(name, tree, node, doc_name, export, docs,
                              constants, root))
    return rows


def _wire_names(tree):
    """Aliases bound to the wire module, and bare publish names, read by AST."""
    aliases = set()
    bare = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == WIRE:
                    aliases.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] == WIRE:
                for alias in node.names:
                    if alias.name == "publish":
                        bare.add(alias.asname or "publish")
    return aliases, bare


def _publish_calls(tree, aliases, bare):
    """The real publish call nodes - string literals are never a call."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "publish":
            if isinstance(func.value, ast.Name) and func.value.id in aliases:
                found.append(node)
        elif isinstance(func, ast.Name) and func.id in bare:
            found.append(node)
    found.sort(key=lambda item: getattr(item, "lineno", 0))
    return found


def _path_constants(tree):
    """Module-level names whose value is a string or an os.path.join of them."""
    table = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                parts = _parts(node.value, table)
                if parts:
                    table[target.id] = parts
    return table


def _parts(node, table):
    """The literal path parts of one expression, outermost first."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Name):
        return list(table.get(node.id, []))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "join":
            out = []
            for arg in node.args:
                out.extend(_parts(arg, table))
            return out
    return []


def _loaded_documents(tree):
    """basename -> pointer, for every json.loads argument this file reads."""
    out = {}
    constants = _path_constants(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = ""
        if isinstance(func, ast.Attribute):
            name = func.attr
        elif isinstance(func, ast.Name):
            name = func.id
        if name != "loads" or not node.args:
            continue
        base = _document_of(node.args[0], constants)
        if base:
            out[base] = base
    return out


def _document_of(node, constants):
    """The document basename a loaded argument names, literal first."""
    literal = ""
    deepest = []
    for inner in ast.walk(node):
        if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
            if inner.value.endswith(".json") and not literal:
                literal = inner.value
        elif isinstance(inner, ast.Name) and inner.id in constants:
            parts = constants[inner.id]
            if len(parts) > len(deepest):
                deepest = parts
    if literal:
        return literal
    return deepest[-1] if deepest else ""


def _dumps_anywhere(node):
    """True when the expression composes text through a json dumps call."""
    for inner in ast.walk(node):
        if isinstance(inner, ast.Call):
            func = inner.func
            if isinstance(func, ast.Attribute) and func.attr == "dumps":
                return True
            if isinstance(func, ast.Name) and func.id == "dumps":
                return True
    return False


def _trace(tree, node, depth=0):
    """Follow a Name back to the last assignment in this file, up to 3 hops."""
    if not isinstance(node, ast.Name) or depth >= 3:
        return node
    last = None
    for item in ast.walk(tree):
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == node.id:
                    if last is None or item.lineno > last.lineno:
                        last = item
    if last is None:
        return node
    return _trace(tree, last.value, depth + 1)


def _classify(name, tree, node, doc_name, export, docs, constants, root):
    """Name one caller's binding, without running the caller."""
    keywords = {}
    for keyword in node.keywords:
        if keyword.arg:
            keywords[keyword.arg] = keyword.value
    line = getattr(node, "lineno", 0)
    if "text" not in keywords:
        return _row(name, line, BOUND, "wire.compose", "", "(unchanged)")
    value = _trace(tree, keywords["text"])
    if isinstance(value, ast.Constant):
        other = "(literal)"
        return _row(name, line, UNBOUND, "literal text", other,
                    _first_field(export, {}))
    if not _dumps_anywhere(value):
        other = "(uncomposed)"
        return _row(name, line, UNBOUND, "no json composition", other,
                    _first_field(export, {}))
    if doc_name in docs:
        return _row(name, line, BOUND, "own document %s" % doc_name, doc_name,
                    "(unchanged)")
    other = ""
    for base, pointer in sorted(docs.items()):
        other = base
        break
    if not other:
        other = "(no document)"
    return _row(name, line, UNBOUND, "another document", other,
                _first_field(export, _other_document(root, other)))


def _other_document(root, base):
    """The document a caller composed, read from disk beside the export."""
    if base in ("(literal)", "(uncomposed)", "(no document)"):
        return {}
    for folder in ("docs", "qa", os.path.join("src", "os")):
        path = os.path.join(root, folder, base)
        if os.path.isfile(path):
            return _load(path)
    return {}


def _first_field(export, other):
    """The first export field whose value the other document does not share."""
    for key in export:
        if key not in other or other[key] != export[key]:
            return key
    if not export:
        return "(empty export)"
    return "(no field differs)"


def _row(name, line, verdict, source, other, first_field):
    return {
        "file": name,
        "line": line,
        "verdict": verdict,
        "source": source,
        "other": other,
        "first_field": first_field,
    }


def _check_flags(argv):
    if not argv or "--help" in argv or "-h" in argv:
        return None, None, False, False, True
    root = "."
    doc = DEFAULT_DOC
    as_json = False
    fail_on_unbound = False
    saw_check = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            saw_check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--fail-on-unbound":
            fail_on_unbound = True
        elif arg in ("--root", "--doc"):
            index += 1
            if index >= len(argv):
                raise BindingConsumerError("E_CEPB_BAD_FLAGS",
                                           "missing value for %s" % arg)
            if arg == "--root":
                root = argv[index]
            else:
                doc = argv[index]
        else:
            raise BindingConsumerError("E_CEPB_BAD_FLAGS",
                                       "unknown argument %s" % arg)
        index += 1
    if not saw_check:
        raise BindingConsumerError("E_CEPB_BAD_FLAGS", "--check is required")
    return root, doc, as_json, fail_on_unbound, False


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        root, doc, as_json, fail_on_unbound, help_wanted = _check_flags(argv)
    except BindingConsumerError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5
    if help_wanted:
        sys.stdout.write(USAGE)
        return 0
    try:
        report = read(root, doc)
    except BindingConsumerError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3
    if as_json:
        payload = {}
        for key in REPORT_KEYS:
            payload[key] = report[key]
        sys.stdout.write(json.dumps(payload, ensure_ascii=False,
                                    sort_keys=True) + "\n")
    else:
        sys.stdout.write(
            "CLOSEOUT EXPORT WIRE BINDING %s verdict=%s root=%s doc=%s "
            "scanned=%d bound=%d unbound=%d out_of_scope=%d unparsed=%d\n"
            % (report["label"], report["verdict"], report["root"],
               report["doc"], report["scanned"], report["bound"],
               report["unbound"], report["out_of_scope"],
               len(report["unparsed"])))
        for row in report["rows"]:
            sys.stdout.write(
                "  %s %s:%d source=%s other=%s first_field=%s\n"
                % (row["verdict"], row["file"], row["line"], row["source"],
                   row["other"], row["first_field"]))
    if fail_on_unbound and report["unbound"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
