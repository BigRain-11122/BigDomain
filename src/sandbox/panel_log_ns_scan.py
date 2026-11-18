"""Refuse a FOREIGN write into the panel child-log namespace.

R2955 closed the writer: inside panel.py, ``birth_child_log`` is the only
creator of a child log, it lays the marker first, reads the first bytes back
and removes what it just made when they disagree.  What it did not bound is
the NAMESPACE.  Nothing in this tree stopped another module from creating
``bigdomain-panel-child-*.txt``, forging a marker, or leaving a markerless file
that the prune must later count as legacy - the exact residue R2954 had to
measure.  This module is that bound: a static AST read over the shipped tree,
no processes, no sockets, no writes.

Two codes, one question each:

``E_PANEL_LOG_NS_FOREIGN_WRITE``
    a module other than the owner holds a WRITE-CAPABLE creation site whose
    path (or tempfile prefix) statically contains the namespace stem.  Shapes
    recognised: ``open`` / ``io.open`` / ``codecs.open`` (positional or
    keyword ``mode``), ``os.open`` (flags naming O_WRONLY / O_RDWR / O_CREAT /
    O_APPEND / O_TRUNC), ``<path>.open`` (write mode), ``<path>.write_text`` /
    ``.write_bytes``, ``tempfile.NamedTemporaryFile`` / ``mkstemp`` (prefix).
    A mode that is not a literal is judged a WRITE, because a static read
    cannot prove it is a read - the cost of that rule is stated here, not
    discovered later.

``E_PANEL_LOG_NS_FOREIGN_NAME``
    a module other than the owner holds the namespace NAME without writing it
    yet: a literal containing the stem bound at MODULE level, or a borrow of
    ``<anything>.LOG_STEM`` / ``.LOG_SUFFIX`` at any level.  Refused because a
    module-level constant is the licence for a write elsewhere in that module,
    and because a rule that only watched ``open`` would be one refactor away
    from blind.  A FUNCTION-LOCAL assignment of the stem is deliberately NOT a
    name row - it is a step toward a call, and the call is where the write is
    judged; refusing the local variable would redden ordinary code (the first
    draft of this rule did exactly that and AC-PAN27 caught it).
    A read-only BORROW is refused with the writes, because the same import is
    one line from a write; the owner and the fixtures are the named exceptions.

Exempt by name, and MEASURED rather than skipped: ``panel.py`` (the one owner),
``test_*.py`` (suite scaffolding must be able to build a world that contains a
real refusal log - the prune suite measures exactly that), and this scanner
(it must hold the name in order to judge it).  Every exempt row is published in
the verdict with ``why=owner|fixture|judge``, so a report cannot claim a clean
tree while quietly walking past the three places that hold the name.

Not recognised, named rather than implied closed: a path assembled without any
literal (built from an imported variable, or a stem split across variables),
``shutil`` / copy based creation, and a write performed by a child process from
a string it received at run time.  The candidate prefilter reads each file for
the stem before parsing, so a stem assembled from two halves escapes it.

Stdlib only (ast/os/sys), no shell, no network, no writes.
"""

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_ROOT = os.path.join(REPO, "src")

STEM = "bigdomain-panel-child-"
OWNER = "panel.py"
JUDGE = "panel_log_ns_scan.py"
BORROW_ATTRS = frozenset(("LOG_STEM", "LOG_SUFFIX"))

FOREIGN_WRITE = "E_PANEL_LOG_NS_FOREIGN_WRITE"
FOREIGN_NAME = "E_PANEL_LOG_NS_FOREIGN_NAME"

KIND_WRITE = "panel-log-write"
KIND_NAME = "panel-log-name"

SKIP_DIRS = frozenset(("vendor", "node_modules", "__pycache__", "pycrdt-poc",
                       ".git", ".venv", "venv"))

WRITE_CHARS = frozenset("wax+")
OS_WRITE_FLAGS = frozenset(("O_WRONLY", "O_RDWR", "O_CREAT", "O_APPEND",
                            "O_TRUNC"))


def is_test_file(name):
    return name.startswith("test_") and name.endswith(".py")


def _why_exempt(rel):
    """The published reason a path may hold the namespace, else None."""
    base = os.path.basename(rel)
    if base == OWNER:
        return "owner"
    if base == JUDGE:
        return "judge"
    if is_test_file(base):
        return "fixture"
    return None


def _call_shape(call):
    """(owner hint, callee name) for a Call, e.g. ("os", "open")."""
    func = call.func
    if isinstance(func, ast.Name):
        return "", func.id
    if isinstance(func, ast.Attribute):
        base = func.value
        hint = base.id if isinstance(base, ast.Name) else ""
        return hint, func.attr
    return "", None


def _has_stem(node):
    """True when any string literal under ``node`` contains the stem."""
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if STEM in child.value:
                return True
    return False


def _mode_node(call, index):
    """The mode expression of a creation call, or None when absent."""
    for kw in call.keywords:
        if kw.arg == "mode":
            return kw.value
    if len(call.args) > index:
        return call.args[index]
    return None


def _mode_is_write(node):
    """Judgement of a mode expression: None means 'no mode given'."""
    if node is None:
        return False
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return any(ch in node.value for ch in WRITE_CHARS)
    return True  # not a literal: a static read cannot prove it is a read


def _os_open_is_write(call):
    """Judgement of an os.open flags expression."""
    flags = _mode_node(call, 1)
    if flags is None:
        return True  # os.open with no flags does not run; judge as write
    names = set()
    for child in ast.walk(flags):
        if isinstance(child, ast.Attribute):
            names.add(child.attr)
        elif isinstance(child, ast.Name):
            names.add(child.id)
    if names & OS_WRITE_FLAGS:
        return True
    if "O_RDONLY" in names:
        return False
    return True  # a bare number cannot be judged here: conservative


def _write_intent(hint, name, call):
    """(is a creation site, is write-capable) for one Call."""
    if name == "write_text" or name == "write_bytes":
        return True, True
    if name in ("NamedTemporaryFile", "mkstemp"):
        return True, True
    if name != "open":
        return False, False
    if hint == "os":
        return True, _os_open_is_write(call)
    if hint in ("", "io", "codecs"):
        return True, _mode_is_write(_mode_node(call, 1))
    # Path(...).open / handle.open: the mode is the first positional argument
    return True, _mode_is_write(_mode_node(call, 0))


def _stem_names(tree):
    """Names bound anywhere in the file to an expression holding the stem.

    One hop only: real code composes the path first and opens it second, so a
    call-site literal test alone would miss the ordinary shape (the first
    draft did, and AC-PAN27 caught it).  What is NOT followed: a path returned
    from another function, a mutable container, and a name that is later
    re-bound - the name stays on the list for the whole file, which is the
    conservative direction.
    """
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = getattr(node, "value", None)
        if value is None or not _has_stem(value):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def _mentions_stem(node, stem_names):
    """True when ``node`` carries the stem directly or through a known name."""
    if _has_stem(node):
        return True
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in stem_names:
            return True
    return False


def scan_source(path, text):
    """Every namespace-shaped site in one module, with its verdict."""
    rel = path.replace(os.sep, "/")
    rows = []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        rows.append({"path": rel, "line": exc.lineno or 0, "function": "<module>",
                     "kind": "unparseable", "code": "E_PANEL_LOG_NS_UNPARSEABLE",
                     "detail": str(exc)})
        return rows
    stem_names = _stem_names(tree)
    stack = [(tree, None)]
    while stack:
        node, func_node = stack.pop()
        function = func_node.name if func_node is not None else "<module>"
        for child in ast.iter_child_nodes(node):
            name = function
            next_func = func_node
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = child.name
                next_func = child
            if isinstance(child, ast.Call):
                hint, callee = _call_shape(child)
                creation, writes = _write_intent(hint, callee, child)
                if (creation and writes and _mentions_stem(child, stem_names)):
                    rows.append({"path": rel, "line": child.lineno,
                                 "function": name, "kind": KIND_WRITE,
                                 "code": FOREIGN_WRITE,
                                 "detail": (hint + "." if hint else "") + callee})
            elif isinstance(child, (ast.Assign, ast.AnnAssign)):
                value = getattr(child, "value", None)
                if (value is not None and func_node is None
                        and _has_stem(value)):
                    rows.append({"path": rel, "line": child.lineno,
                                 "function": name, "kind": KIND_NAME,
                                 "code": FOREIGN_NAME,
                                 "detail": "binding"})
            elif isinstance(child, ast.Attribute):
                if child.attr in BORROW_ATTRS:
                    rows.append({"path": rel, "line": child.lineno,
                                 "function": name, "kind": KIND_NAME,
                                 "code": FOREIGN_NAME,
                                 "detail": "borrow " + child.attr})
            stack.append((child, next_func))
    return rows


def iter_modules(root):
    """Every .py under ``root``, repo-relative to it."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            full = os.path.join(dirpath, name)
            yield os.path.relpath(full, root), full


def scan(root=None):
    """Read every module under ``root`` and judge the namespace holders."""
    root = root or DEFAULT_ROOT
    rows = []
    modules = 0
    parsed = 0
    for rel, full in iter_modules(root):
        modules += 1
        with open(full, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        if STEM not in text and "LOG_STEM" not in text and "LOG_SUFFIX" not in text:
            continue
        parsed += 1
        rows.extend(scan_source(rel, text))
    exempt = []
    refused = []
    for row in rows:
        why = _why_exempt(row["path"])
        if why:
            row["code"] = None
            row["why"] = why
            exempt.append(row)
        else:
            refused.append(row)
    by_why = {}
    for row in exempt:
        by_why[row["why"]] = by_why.get(row["why"], 0) + 1
    return {
        "root": root,
        "modules": modules,
        "parsed": parsed,
        "sites": len(rows),
        "refused": refused,
        "exempt": exempt,
        "by_why": by_why,
        "ok": not refused,
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = argv[0] if argv else None
    verdict = scan(root=root)
    line = ("[PANEL-LOG-NS] modules=%d parsed=%d sites=%d refused=%d exempt=%d"
            % (verdict["modules"], verdict["parsed"], verdict["sites"],
               len(verdict["refused"]), len(verdict["exempt"])))
    for why in sorted(verdict["by_why"]):
        line += " %s=%d" % (why, verdict["by_why"][why])
    print(line)
    for row in verdict["refused"]:
        print("REFUSED %s:%d %s kind=%s detail=%s"
              % (row["path"], row["line"], row["code"], row["kind"],
                 row["detail"]))
    return 0 if verdict["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
