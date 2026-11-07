"""probe_seam_name_binding_control_flow_scope - resolve only a PROVEN binding.

MEASURED at R2541 on the shipped position face own reader, in that window own
legs:

  (1) a binding written inside `if False:` still resolves for a loop after it,
      because the bindings are collected by walking the syntax tree and no
      branch is ever asked whether it runs;
  (2) a `with open(...) as KEY` binding is not collected at all, so a loop that
      reads KEY after the with-block reads unbound;
  (3) a try/except that binds the SAME name to two different values in two
      exclusive branches reads one ambiguous word instead of two arms.

This face answers all three on top of the shipped law rather than instead of
it. The shipped position face is asked FIRST (`position_report`,
`position_entry`) so every answer it already gave keeps its answer, and this
module only adds what that reading could not see:

  control_flow_tables(text)
      the bindings per SCOPE - module body, each function body and each class
      body - each entry carrying its LINE, its value shape, and the GUARD of
      the statement that must run for the binding to exist (a branch, a loop,
      a with-block, a try/except arm), or no guard at all.
  control_flow_entry(name, text, scope, line, tables=None)
      ('ok', value, ...) only for a binding proved to run before the loop.
      A binding behind a guard is NAMED 'guarded:<guard>' and never resolved,
      a with-as binding is NAMED 'with-as', and two EXCLUSIVE arms of one
      branch publish BOTH arms by name instead of one ambiguity word.
  control_flow_report(text)
      one row per loop the shipped position reading already publishes, each
      row carrying this face own followed / refused / arms and the shipped
      answer beside it, so a row that RESOLVED under the position face and is
      REFUSED here says so on one line.
  audit / reading / guard
      the shipped position audit asked first, each probe row then decorated
      with this face own control-flow loops; the seam classifier is still the
      shipped registry `quiets` and nothing here is a second classifier.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNCF5). No probe and
no helper is ever imported or run.

Criteria AC-PNCF1..AC-PNCF6 were pinned in state/queue/tech.md:579 at R2541 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: control flow is read from the syntax tree
only - a condition is never evaluated, so `if True:` is guarded exactly like
`if False:`; a `for` target is guarded by its own loop because the body may run
zero times; two arms are published only when one `if` binds two DIFFERENT
literal values, and everything else stays a named refusal. These shapes can
UNDER-report a stale probe but can never invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-CONTROL-FLOW-COVERED)
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

LABEL = "os-probe-seam-name-binding-control-flow-scope"
E_ARGS = "E_PNCF_ARGS"
E_NO_ROOT = "E_PNCF_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-CONTROL-FLOW-COVERED"
SEAMS_STALE = "SEAMS-CONTROL-FLOW-STALE"

REFUSED_NOT_YET_BOUND = "not-yet-bound"
REFUSED_WITH_AS = "with-as"
REFUSED_GUARDED = "guarded:%s"
STATE_ARMS = "arms"

SCOPE_MODULE = "module"
SCOPE_FUNCTION = "function:%s"
SCOPE_CLASS = "class:%s"

BASE = os.path.dirname(os.path.abspath(__file__))


class NameBindingControlFlowError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _position():
    """The shipped position face (one law, asked not restated)."""
    import probe_seam_name_binding_position_scope
    return probe_seam_name_binding_position_scope


def render_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    return _position().render_module()


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    return _position().seam_names(module)


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
    return _position()._value_entry(value)


def _record(table, target, value, line, guard, arm):
    entry = (line,) + _value_entry(value) + (guard, arm)
    table.setdefault(target.id, []).append(entry)


def _collect(stmts, table, guard="", arm=None):
    for node in stmts:
        _collect_node(node, table, guard, arm)


def _collect_node(node, table, guard, arm):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return
    line = getattr(node, "lineno", 0)
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name):
        _record(table, node.targets[0], node.value, line, guard, arm)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        _record(table, node.target, node.value, line, guard, arm)
    elif isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        _record(table, node.target, node.value, line, guard, arm)
    if isinstance(node, ast.For):
        inner = "loop:%d" % line
        if isinstance(node.target, ast.Name):
            value = None
            if isinstance(node.iter, (ast.Tuple, ast.List)) \
                    and len(node.iter.elts) == 1:
                value = node.iter.elts[0]
            _record(table, node.target, value, line, inner, arm)
        _collect(node.body, table, inner, arm)
        _collect(node.orelse, table, "loop-else:%d" % line, arm)
        return
    if isinstance(node, ast.While):
        inner = "while:%d" % line
        _collect(node.body, table, inner, arm)
        _collect(node.orelse, table, "while-else:%d" % line, arm)
        return
    if isinstance(node, ast.If):
        group = "if:%d" % line
        _collect(node.body, table, group, (group, "body"))
        _collect(node.orelse, table, group, (group, "else"))
        return
    if isinstance(node, (ast.With, ast.AsyncWith)):
        for item in node.items:
            if isinstance(item.optional_vars, ast.Name):
                entry = (line, "with-as", "with-as",
                         REFUSED_WITH_AS, (REFUSED_WITH_AS, "body"))
                table.setdefault(item.optional_vars.id, []).append(entry)
        _collect(node.body, table, "with:%d" % line,
                 (REFUSED_WITH_AS, "body"))
        return
    if isinstance(node, ast.Try):
        group = "try:%d" % line
        _collect(node.body, table, group, (group, "body"))
        for index, handler in enumerate(node.handlers):
            _collect(handler.body, table, group,
                     (group, "except%d" % index))
        _collect(node.orelse, table, group, (group, "else"))
        _collect(node.finalbody, table, "finally:%d" % line, arm)
        return
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.stmt):
            _collect_node(child, table, guard, arm)


def control_flow_tables(text):
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


def _arms_of(guarded):
    """Two EXCLUSIVE arms of one branch, published by name when they differ."""
    groups = {}
    for entry in guarded:
        if entry[4]:
            groups.setdefault(entry[4][0], []).append(entry)
    for group in sorted(groups):
        values = {}
        for entry in groups[group]:
            if entry[1] == "str":
                values.setdefault(entry[4][1], set()).add(entry[2])
        if len(values) < 2:
            continue
        if not all(len(found) == 1 for found in values.values()):
            continue
        names = [sorted(found)[0] for found in values.values()]
        if len(set(names)) < 2:
            continue
        return [{"group": group, "arm": arm, "value": sorted(values[arm])[0]}
                for arm in sorted(values)]
    return []


def control_flow_entry(name, text, scope, line, tables=None):
    """Resolve a NAME against the bindings PROVED to run before `line`."""
    tables = control_flow_tables(text) if tables is None else tables
    if tables is None:
        return {"state": "refused", "reason": UNREADABLE.lower(),
                "scope": scope, "shadow": False, "later": {}, "arms": []}
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
    proven = [entry for entry in before if not entry[3]]
    guarded = [entry for entry in before if entry[3]]
    values = []
    words = []
    for entry in proven:
        if entry[1] == "str":
            if entry[2] not in values:
                values.append(entry[2])
        else:
            words.append(entry[2])
    later = {}
    for entry in after:
        if entry[1] == "str" and (not values or entry[2] != values[0]):
            later[name] = entry[2]
    out = {"state": "refused", "reason": None, "value": None,
           "scope": where, "shadow": shadow, "later": later, "arms": []}
    if len(values) > 1 or (values and words):
        out["reason"] = "ambiguous"
        return out
    if values:
        out["state"] = "ok"
        out["value"] = values[0]
        return out
    if words:
        out["reason"] = words[0]
        return out
    if guarded:
        arms = _arms_of(guarded)
        if arms:
            out["state"] = STATE_ARMS
            out["reason"] = "exclusive-arms"
            out["arms"] = arms
            return out
        guard = guarded[0][3]
        out["reason"] = (REFUSED_WITH_AS if guard == REFUSED_WITH_AS
                         else REFUSED_GUARDED % guard)
        return out
    if after:
        out["reason"] = REFUSED_NOT_YET_BOUND
        return out
    out["reason"] = "unbound"
    return out


def control_flow_report(text):
    """One row per loop the shipped position reading publishes."""
    base = _position()
    shipped = base.position_report(text)
    tables = control_flow_tables(text)
    rows = []
    for loop in shipped["loops"]:
        names = sorted(set(loop["followed"]) | set(loop["refused"]))
        row = {"line": loop["line"], "kind": loop["kind"],
               "scope": loop["scope"], "followed": {}, "refused": {},
               "arms": [], "base_followed": dict(loop["followed"]),
               "base_refused": dict(loop["refused"])}
        for name in names:
            got = control_flow_entry(name, text, row["scope"], row["line"],
                                     tables)
            if got["state"] == "ok":
                row["followed"][name] = got["value"]
            elif got["state"] == STATE_ARMS:
                row["arms"].append({"name": name, "arms": got["arms"]})
            else:
                row["refused"][name] = got["reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["control_flow_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in control_flow_report(text)["loops"]:
        row["control_flow_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped position audit, decorated with this face own flow rows."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise NameBindingControlFlowError(E_NO_ROOT,
                                          "not a directory: %s" % root_path)
    base = _position()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise NameBindingControlFlowError(
            code, str(getattr(exc, "detail", exc)))
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
    except NameBindingControlFlowError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise NameBindingControlFlowError(report["verdict"],
                                          "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a NAME only when its binding is proved to run")
    parser.add_argument("--root", default=BASE,
                        help="directory of probe modules to read")
    parser.add_argument("--json", action="store_true", help="machine output")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 5
    if not os.path.isdir(args.root):
        sys.stderr.write("%s: not a directory: %s\n"
                         % (E_NO_ROOT, args.root))
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
            sys.stdout.write("  probe %s control_flow_loops=%d\n"
                             % (row["file"], len(row["control_flow_loops"])))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())