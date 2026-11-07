"""probe_seam_name_binding_position_scope - resolve a NAME where it is BOUND.

MEASURED at R2539 on the shipped scope face own reader, in that window own
live legs:

  (1) the tables are read per SCOPE and not per POSITION, so a loop that runs
      before its key is bound reads exactly like one that runs after;
  (2) a class body is not a scope that reading follows, so a class-level
      constant reads unbound for a loop in that class body while the row
      attributes the loop to `module`;
  (3) a loop spelled inside a comprehension is not read at all, because a
      comprehension is not an ast.For node.

This face answers all three, on top of the shipped law rather than instead of
it. The shipped scope face is asked FIRST (`scope_tables`, `scoped_entry`,
`scope_report`) so every shape it already answered keeps its answer, and this
module only adds what that reading could not see:

  position_tables(text)
      the bindings per SCOPE - module body, each function body and each CLASS
      body - each entry carrying the LINE it is written on.
  position_entry(name, text, scope, line, tables=None)
      ('ok', value, where, shadow, later) or ('refused', reason, where,
      shadow, later). A binding written AFTER the loop never resolves the
      loop: it is NAMED 'not-yet-bound'. A name bound before the loop and
      rebound after it resolves to the EARLIER value and publishes the later
      write on the row. A class body resolves its own constants and announces
      a module-level name of the same name as shadowed.
  position_report(text)
      one row per loop: an ast.For, and also every comprehension loop named
      with its own comprehension kind (comprehension:list / :set / :dict /
      :generator) instead of being dropped.
  audit / reading / guard
      the shipped scope audit asked first, each row then decorated with this
      face own position loops; the seam classifier is still the shipped
      registry `quiets` and nothing here is a second classifier.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNSP5). No probe and
no helper is ever imported or run.

Criteria AC-PNSP1..AC-PNSP6 were pinned in state/queue/tech.md:577 at R2539 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: only literally constant values are followed,
a name bound twice BEFORE the loop with two values is still refused as
ambiguous rather than picked, and a loop nested in a class inside a function is
attributed to the class. These shapes can UNDER-report a stale probe but can
never invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-POSITION-COVERED)
  exit 2 = a probe is MISSING-SEAM or a source will not parse
  exit 3 = the root is missing or unreadable
  exit 5 = bad arguments
"""

import argparse
import ast
import hashlib
import json
import os
import sys

LABEL = "os-probe-seam-name-binding-position-scope"
E_ARGS = "E_PNSP_ARGS"
E_NO_ROOT = "E_PNSP_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-POSITION-COVERED"
SEAMS_STALE = "SEAMS-POSITION-STALE"

REFUSED_NOT_YET_BOUND = "not-yet-bound"

SCOPE_MODULE = "module"
SCOPE_FUNCTION = "function:%s"
SCOPE_CLASS = "class:%s"

COMPREHENSION_KINDS = (
    (ast.ListComp, "comprehension:list"),
    (ast.SetComp, "comprehension:set"),
    (ast.DictComp, "comprehension:dict"),
    (ast.GeneratorExp, "comprehension:generator"),
)

BASE = os.path.dirname(os.path.abspath(__file__))


class NameBindingPositionError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base():
    """The shipped scope face, imported once (one law, no copy)."""
    import probe_seam_name_binding_scope_awareness
    return probe_seam_name_binding_scope_awareness


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
    """The shipped value law, asked rather than restated."""
    return _base()._value_entry(value)


def _collect(stmts, table):
    """Bindings declared in one scope body, each carrying its LINE."""
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
    line = getattr(node, "lineno", 0)
    for target in targets:
        if isinstance(target, ast.Name):
            table.setdefault(target.id, []).append(
                (line,) + _value_entry(value))
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
            continue
        _collect_node(child, table)


def position_tables(text):
    """{'module': t, 'functions': {n: t}, 'classes': {n: t}} or None."""
    tree = _parse(text)
    if tree is None:
        return None
    module = {}
    _collect(tree.body, module)
    functions = {}
    classes = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        table = {}
        _collect(node.body, table)
        if isinstance(node, ast.ClassDef):
            classes[node.name] = table
        else:
            functions[node.name] = table
    return {"module": module, "functions": functions, "classes": classes}


def _scope_table(tables, scope):
    if scope == SCOPE_MODULE:
        return tables["module"], SCOPE_MODULE
    head, _, name = scope.partition(":")
    if head == "function":
        return tables["functions"].get(name, {}), SCOPE_FUNCTION % name
    if head == "class":
        return tables["classes"].get(name, {}), SCOPE_CLASS % name
    return {}, scope


def position_entry(name, text, scope, line, tables=None):
    """Resolve a NAME against the bindings that PRECEDE `line` in its scope.

    Returns {'state': 'ok'|'refused', 'value', 'reason', 'scope', 'shadow',
    'later'}; `later` publishes a write that follows the loop, so a rebound
    name is visible as a fact rather than silently ignored.
    """
    tables = position_tables(text) if tables is None else tables
    if tables is None:
        return {"state": "refused", "reason": UNREADABLE.lower(),
                "scope": scope, "shadow": False, "later": {}}
    inner, where = _scope_table(tables, scope)
    outer = tables["module"]
    shadow = False
    if where != SCOPE_MODULE and name in inner:
        entries = inner[name]
        shadow = name in outer
    elif where == SCOPE_MODULE and name in inner:
        entries = inner[name]
    else:
        entries = outer.get(name, [])
        where = SCOPE_MODULE
    before = []
    after = []
    for entry in entries:
        (before if entry[0] <= line else after).append(entry)
    values = []
    words = []
    for _line, kind, value in before:
        if kind == "str":
            if value not in values:
                values.append(value)
        else:
            words.append(value)
    later = {}
    for _line, kind, value in after:
        if kind == "str" and (not values or value != values[0]):
            later[name] = value
    if len(values) > 1 or (values and words):
        return {"state": "refused", "reason": "ambiguous",
                "scope": where, "shadow": shadow, "later": later}
    if values:
        return {"state": "ok", "value": values[0], "reason": None,
                "scope": where, "shadow": shadow, "later": later}
    if words:
        return {"state": "refused", "reason": words[0],
                "scope": where, "shadow": shadow, "later": later}
    if after:
        return {"state": "refused", "reason": REFUSED_NOT_YET_BOUND,
                "scope": where, "shadow": shadow, "later": later}
    return {"state": "refused", "reason": "unbound",
            "scope": where, "shadow": False, "later": later}


def _iter_names(node):
    """The NAME steps a loop iterable spells as subscript keys."""
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
        if isinstance(current, ast.ClassDef):
            return SCOPE_CLASS % current.name
        current = parents.get(current)
    return SCOPE_MODULE


def _row(node, kind, scope, names, text, tables):
    row = {"line": getattr(node, "lineno", 0), "kind": kind, "scope": scope,
           "followed": {}, "refused": {}, "shadowed": [], "later": {},
           "taken_from": {}}
    for name in names:
        got = position_entry(name, text, scope, row["line"], tables)
        row["taken_from"][name] = got["scope"]
        if got["state"] == "ok":
            row["followed"][name] = got["value"]
            if got.get("shadow"):
                row["shadowed"].append(name)
        else:
            row["refused"][name] = got["reason"]
        if got.get("later"):
            row["later"].update(got["later"])
    return row


def position_report(text):
    """One row per loop: every ast.For AND every comprehension loop."""
    tree = _parse(text)
    if tree is None:
        return {"tool": LABEL, "loops": [], "parsed": False}
    tables = position_tables(text)
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    loops = []
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            loops.append(_row(node, "for", _enclosing_scope(node, parents),
                              _iter_names(node.iter), text, tables))
    for node in ast.walk(tree):
        kind = None
        for node_type, word in COMPREHENSION_KINDS:
            if isinstance(node, node_type):
                kind = word
                break
        if kind is None:
            continue
        scope = _enclosing_scope(node, parents)
        for generator in getattr(node, "generators", []):
            sub = _row(generator.iter, kind, scope,
                       _iter_names(generator.iter), text, tables)
            sub["line"] = getattr(node, "lineno", sub["line"])
            loops.append(sub)
    loops.sort(key=lambda entry: (entry["line"], entry["kind"]))
    return {"tool": LABEL, "loops": loops, "parsed": True}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["position_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in position_report(text)["loops"]:
        row["position_loops"].append({
            "line": loop["line"], "kind": loop["kind"],
            "scope": loop["scope"],
            "followed": dict(loop["followed"]),
            "refused": dict(loop["refused"]),
            "shadowed": list(loop["shadowed"]),
            "later": dict(loop["later"]),
            "taken_from": dict(loop["taken_from"]),
        })
    return row


def audit(root=None, module=None):
    """The shipped scope audit, decorated with this face own position rows."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise NameBindingPositionError(E_NO_ROOT,
                                       "not a directory: %s" % root_path)
    base = _base()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise NameBindingPositionError(code,
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
    except NameBindingPositionError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise NameBindingPositionError(report["verdict"],
                                       "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a NAME step against the bindings before it")
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
            sys.stdout.write("  probe %s position_loops=%d\n"
                             % (row["file"], len(row["position_loops"])))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())