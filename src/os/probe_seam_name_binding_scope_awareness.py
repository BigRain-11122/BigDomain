"""probe_seam_name_binding_scope_awareness - resolve a NAME step in ITS scope.

MEASURED at R2537 on the shipped nested-key face own readers, in that window
own live legs: `_bindings_of` walks the WHOLE module, so

  def a():
      KEY = "b"
      for name in D["a"][KEY]: ...
  def b():
      KEY = "c"
      ...

reads refused=ambiguous for the loop inside `a()` even though that scope holds
EXACTLY ONE constant, and the same over-broad read makes a function-local name
visible to a module-level loop it cannot reach.

This face resolves a NAME step against the binding table of the SCOPE the loop
is in and publishes which scope it followed:

  scope_tables(text)
      the bindings per SCOPE - the module body and each function body, read
      with the same shapes the shipped faces already read (plain assignment,
      annotated assignment, walrus, and a single-element for target), and
      never descending into a nested def or class.
  scoped_entry(name, text, scope, tables=None)
      ('ok', value, where, shadow) or ('refused', reason, where, shadow).
      The enclosing function is asked FIRST; the module body is the fallback,
      and a name bound in BOTH resolves to the inner binding with shadow=True
      announced. A name bound twice with two different values INSIDE one scope
      is refused as ambiguous, exactly as the shipped law refuses it.
  scope_report(text)
      one row per for-loop naming its scope, what it FOLLOWED, what it
      REFUSED, and the names it SHADOWED.
  audit / reading / guard
      the shipped nested-key face asked FIRST, so every shape it already
      answered keeps its answer and the seam classifier is still the shipped
      registry `quiets`; each row is then decorated with this window own scope
      loops. Nothing here is a second classifier.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNSB5). No probe and
no helper is ever imported or run.

Criteria AC-PNSB1..AC-PNSB6 were pinned in state/queue/tech.md:575 at R2537 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: only literally constant values are followed,
a name bound twice inside one scope is refused rather than picked, a class body
is not a scope this reading follows, and a loop nested in a class inside a
function is attributed to the function. These shapes can UNDER-report a stale
probe but can never invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-NAME-SCOPE-COVERED)
  exit 2 = a probe is MISSING-SEAM or a source will not parse
  exit 3 = the root is missing or unreadable
  exit 5 = bad arguments
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys

LABEL = "os-probe-seam-name-binding-scope-awareness"
E_ARGS = "E_PNSB_ARGS"
E_NO_ROOT = "E_PNSB_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-NAME-SCOPE-COVERED"
SEAMS_STALE = "SEAMS-NAME-SCOPE-STALE"

REFUSED_AMBIGUOUS = "ambiguous"
REFUSED_CALL = "call"
REFUSED_FORMAT = "format"
REFUSED_EXPRESSION = "expression"
REFUSED_COMPREHENSION = "comprehension"
REFUSED_SHAPE = "shape"
REFUSED_UNBOUND = "unbound"
REFUSED_UNREADABLE = "unreadable"

SCOPE_MODULE = "module"
SCOPE_FUNCTION = "function:%s"

BASE = os.path.dirname(os.path.abspath(__file__))
SCAN_SUFFIX = ".py"


class NameBindingScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base():
    """The shipped nested-key face, imported once (one law, no copy)."""
    import probe_seam_nested_key_binding_scope
    return probe_seam_nested_key_binding_scope


def render_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    return _base().render_module()


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    return _base().seam_names(module)


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _parse(text):
    try:
        return ast.parse(text)
    except (SyntaxError, ValueError):
        return None


def _value_entry(value):
    """('str', text) for a literal constant, else ('word', reason)."""
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return ("str", value.value)
    if value is None:
        return ("word", REFUSED_SHAPE)
    if isinstance(value, ast.Call):
        if isinstance(value.func, ast.Attribute) and value.func.attr == "format":
            return ("word", REFUSED_FORMAT)
        return ("word", REFUSED_CALL)
    if isinstance(value, ast.JoinedStr):
        return ("word", REFUSED_FORMAT)
    if isinstance(value, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare)):
        return ("word", REFUSED_EXPRESSION)
    if isinstance(value, (ast.ListComp, ast.SetComp, ast.DictComp,
                          ast.GeneratorExp)):
        return ("word", REFUSED_COMPREHENSION)
    return ("word", REFUSED_SHAPE)


def _collect(stmts, table):
    """Bindings declared in one scope, never descending into a nested def."""
    for node in stmts:
        _collect_node(node, table)


def _collect_node(node, table):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return
    targets = []
    value = None
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        targets = [node.targets[0]]
        value = node.value
    elif isinstance(node, ast.AnnAssign):
        targets = [node.target]
        value = node.value
    elif isinstance(node, ast.NamedExpr):
        targets = [node.target]
        value = node.value
    elif isinstance(node, ast.For):
        targets = [node.target]
        if isinstance(node.iter, (ast.Tuple, ast.List)) \
                and len(node.iter.elts) == 1:
            value = node.iter.elts[0]
    for target in targets:
        if isinstance(target, ast.Name):
            table.setdefault(target.id, []).append(_value_entry(value))
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
            continue
        _collect_node(child, table)


def scope_tables(text):
    """{'module': table, 'functions': {name: table}} or None if unparseable."""
    tree = _parse(text)
    if tree is None:
        return None
    module = {}
    _collect(tree.body, module)
    functions = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            table = {}
            _collect(node.body, table)
            functions[node.name] = table
    return {"module": module, "functions": functions}


def _scope_name(scope):
    if scope == SCOPE_MODULE:
        return None
    return scope.split(":", 1)[1] if ":" in scope else scope


def scoped_entry(name, text, scope, tables=None):
    """Resolve a NAME inside the scope the loop is in.

    Returns {'state': 'ok'|'refused', 'value', 'reason', 'scope', 'shadow'};
    'scope' is the scope the value was actually taken from, so a module
    fallback and a shadowed inner binding are distinguishable on the row.
    """
    tables = scope_tables(text) if tables is None else tables
    if tables is None:
        return {"state": "refused", "reason": REFUSED_UNREADABLE,
                "scope": scope, "shadow": False}
    inner_name = _scope_name(scope)
    inner = {} if inner_name is None else tables["functions"].get(
        inner_name, {})
    outer = tables["module"]
    if name in inner:
        entries = inner[name]
        where = SCOPE_FUNCTION % inner_name
        shadow = name in outer
    else:
        entries = outer.get(name, [])
        where = SCOPE_MODULE
        shadow = False
    values = []
    words = []
    for kind, value in entries:
        if kind == "str":
            if value not in values:
                values.append(value)
        else:
            words.append(value)
    if len(values) > 1 or (values and words):
        return {"state": "refused", "reason": REFUSED_AMBIGUOUS,
                "scope": where, "shadow": shadow}
    if values:
        return {"state": "ok", "value": values[0], "reason": None,
                "scope": where, "shadow": shadow}
    if words:
        return {"state": "refused", "reason": words[0],
                "scope": where, "shadow": shadow}
    return {"state": "refused", "reason": REFUSED_UNBOUND,
            "scope": where, "shadow": False}


def _iter_names(node):
    """The NAME steps the loop iterable spells as subscript keys."""
    names = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Subscript):
            continue
        step = child.slice
        if isinstance(step, ast.Name) and step.id not in names:
            names.append(step.id)
    return names


def _enclosing_scope(node, parents):
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return SCOPE_FUNCTION % current.name
        current = parents.get(current)
    return SCOPE_MODULE


def scope_report(text):
    """One row per for-loop naming its scope and what it resolved there."""
    tree = _parse(text)
    if tree is None:
        return {"tool": LABEL, "loops": [], "parsed": False}
    tables = scope_tables(text)
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    loops = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        scope = _enclosing_scope(node, parents)
        row = {"line": getattr(node, "lineno", 0), "scope": scope,
               "followed": {}, "refused": {}, "shadowed": [], "taken_from": {}}
        for name in _iter_names(node.iter):
            got = scoped_entry(name, text, scope, tables)
            row["taken_from"][name] = got["scope"]
            if got["state"] == "ok":
                row["followed"][name] = got["value"]
                if got.get("shadow"):
                    row["shadowed"].append(name)
            else:
                row["refused"][name] = got["reason"]
        loops.append(row)
    return {"tool": LABEL, "loops": loops, "parsed": True}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["scope_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in scope_report(text)["loops"]:
        row["scope_loops"].append({
            "line": loop["line"], "scope": loop["scope"],
            "followed": dict(loop["followed"]),
            "refused": dict(loop["refused"]),
            "shadowed": list(loop["shadowed"]),
            "taken_from": dict(loop["taken_from"]),
        })
    return row


def audit(root=None, module=None):
    """The shipped nested-key audit, decorated with this face own scope rows."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise NameBindingScopeError(E_NO_ROOT,
                                    "not a directory: %s" % root_path)
    base = _base()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise NameBindingScopeError(code,
                                    str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_STALE if report.get("verdict") == base.SEAMS_STALE
                         else SEAMS_COVERED)
    report["base_tool"] = base.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except NameBindingScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise NameBindingScopeError(report["verdict"],
                                    "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL, description="resolve a NAME step inside its own scope")
    parser.add_argument("--root", default=BASE,
                        help="directory of probe modules to read")
    parser.add_argument("--json", action="store_true", help="machine output")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 5
    if not os.path.isdir(args.root):
        sys.stderr.write("%s: not a directory: %s\n" % (E_NO_ROOT, args.root))
        return 3
    report = reading(args.root)
    if args.json:
        sys.stdout.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    else:
        sys.stdout.write("%s verdict=%s base=%s\n"
                         % (LABEL, report["verdict"],
                            report.get("base_tool", "?")))
        for name in sorted(report["counts"]):
            sys.stdout.write("  %s=%s\n" % (name, report["counts"][name]))
        for row in report["probes"]:
            if row["verdict"] != COVERED:
                continue
            sys.stdout.write("  probe %s scope_loops=%d\n"
                             % (row["file"], len(row["scope_loops"])))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())