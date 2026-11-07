"""probe_seam_name_binding_control_flow_guard_scope - aggregate guards.

MEASURED at R2543 on the shipped control-flow face own reader, in that window
own legs:

  (1) `if c: KEY = "b" else: KEY = "b"` refuses as guarded:if:2 although BOTH
      arms agree, so a provably single value is withheld;
  (2) two SEPARATE if statements binding one name to two different values read
      as ONE guard word for the first statement, so the second group is
      invisible rather than published;
  (3) a binding nested `if a: if b: KEY = "b"` publishes only guarded:if:3 and
      drops the outer guard standing on the same path.

This face answers all three on top of the shipped law rather than instead of
it. The shipped control-flow face is asked FIRST (`guard_entry` calls its
`control_flow_entry`, and `audit` calls its `audit`), so every answer it
already gave keeps that answer; this module only adds what that reading could
not see:

  guard_tables(text)
      the bindings per SCOPE, each entry carrying its LINE, its value shape,
      and the whole GUARD CHAIN that must run for the binding to exist -
      outermost guard first - rather than only the innermost word.
  guard_entry(name, text, scope, line, tables=None)
      the shipped entry answer, or, when the shipped face refused a guarded
      binding, one of three aggregated answers:
        * the two arms of ONE if binding the SAME literal resolve to it;
        * two separate guard groups are published as TWO groups, each with
          its own guards, instead of one word;
        * every guard on the path is published in order, outermost first,
          never only the innermost.
  guard_report(text)
      one row per loop the shipped control-flow reading already publishes,
      each row carrying this face own followed / refused / arms / chains /
      groups and the shipped answer beside it, so a row the shipped face
      refused and this face resolved says so on one line.
  audit / reading / guard
      the shipped control-flow audit asked first, each probe row then
      decorated with this face own guard loops; the seam classifier is still
      the shipped registry `quiets` and nothing here is a second classifier.

RESOLUTION LAW, stated rather than buried: a guarded binding is resolved ONLY
when its group is the two arms of ONE if (body AND else), both binding the
same single string literal - those two arms cover every path, so the value is
provable. A nested guard, a one-armed branch, a loop body or a handler is
published with its whole chain and NEVER resolved, because none of them is
proved to run.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNCG5). No probe and
no helper is ever imported or run.

Criteria AC-PNCG1..AC-PNCG6 were pinned in state/queue/tech.md:581 at R2543 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: a condition is never evaluated, so `if
True:` is guarded exactly like `if False:`; an exhaustive pair is recognised
by SHAPE (one if, both arms, one literal each), never by evaluating the
condition. These shapes can UNDER-report a stale probe but can never invent
one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-GUARD-COVERED)
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

LABEL = "os-probe-seam-name-binding-control-flow-guard-scope"
E_ARGS = "E_PNCG_ARGS"
E_NO_ROOT = "E_PNCG_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_GUARD_COVERED = "SEAMS-GUARD-COVERED"
SEAMS_GUARD_STALE = "SEAMS-GUARD-STALE"

STATE_OK = "ok"
STATE_ARMS = "arms"
REFUSED_GROUPED = "guarded-groups"
REFUSED_GUARDED = "guarded:%s"
REFUSED_WITH_AS = "with-as"
CHAIN_SEP = ">"
SOURCE_SHIPPED = "shipped"
SOURCE_GUARD = "guard"

SCOPE_MODULE = "module"
SCOPE_FUNCTION = "function:%s"
SCOPE_CLASS = "class:%s"

BASE = os.path.dirname(os.path.abspath(__file__))


class NameBindingGuardScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _flow():
    """The shipped control-flow face (one law, asked not restated)."""
    import probe_seam_name_binding_control_flow_scope
    return probe_seam_name_binding_control_flow_scope


def render_module():
    """The shipped render, imported through the shipped face chain."""
    return _flow().render_module()


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    return _flow().seam_names(module)


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
    return _flow()._value_entry(value)


def _record(table, target, value, line, chain, arm):
    entry = (line,) + _value_entry(value) + (tuple(chain), arm)
    table.setdefault(target.id, []).append(entry)


def _collect(stmts, table, chain=(), arm=None):
    for node in stmts:
        _collect_node(node, table, chain, arm)


def _collect_node(node, table, chain, arm):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return
    line = getattr(node, "lineno", 0)
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name):
        _record(table, node.targets[0], node.value, line, chain, arm)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        _record(table, node.target, node.value, line, chain, arm)
    elif isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        _record(table, node.target, node.value, line, chain, arm)
    if isinstance(node, ast.For):
        inner = chain + ("loop:%d" % line,)
        if isinstance(node.target, ast.Name):
            value = None
            if isinstance(node.iter, (ast.Tuple, ast.List)) \
                    and len(node.iter.elts) == 1:
                value = node.iter.elts[0]
            _record(table, node.target, value, line, inner, arm)
        _collect(node.body, table, inner, arm)
        _collect(node.orelse, table, chain + ("loop-else:%d" % line,), arm)
        return
    if isinstance(node, ast.While):
        inner = chain + ("while:%d" % line,)
        _collect(node.body, table, inner, arm)
        _collect(node.orelse, table, chain + ("while-else:%d" % line,), arm)
        return
    if isinstance(node, ast.If):
        group = "if:%d" % line
        inner = chain + (group,)
        _collect(node.body, table, inner, (group, "body"))
        _collect(node.orelse, table, inner, (group, "else"))
        return
    if isinstance(node, (ast.With, ast.AsyncWith)):
        inner = chain + ("with:%d" % line,)
        for item in node.items:
            if isinstance(item.optional_vars, ast.Name):
                entry = (line, "with-as", "with-as", inner,
                         (REFUSED_WITH_AS, "body"))
                table.setdefault(item.optional_vars.id, []).append(entry)
        _collect(node.body, table, inner, (REFUSED_WITH_AS, "body"))
        return
    if isinstance(node, ast.Try):
        group = "try:%d" % line
        inner = chain + (group,)
        _collect(node.body, table, inner, (group, "body"))
        for index, handler in enumerate(node.handlers):
            _collect(handler.body, table, inner,
                     (group, "except%d" % index))
        _collect(node.orelse, table, inner, (group, "else"))
        _collect(node.finalbody, table, chain + ("finally:%d" % line,), arm)
        return
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.stmt):
            _collect_node(child, table, chain, arm)


def guard_tables(text):
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


def _chain_text(chain):
    return CHAIN_SEP.join(chain)


def _group_payload(group, entries):
    """One guard group as a row: its FULL chain, its arms and its values."""
    chains = []
    for entry in entries:
        text = _chain_text(entry[3])
        if text and text not in chains:
            chains.append(text)
    arms = {}
    values = []
    for entry in entries:
        if entry[1] == "str":
            if entry[2] not in values:
                values.append(entry[2])
            if len(entry[3]) == 1 and entry[4]:
                arms[entry[4][1]] = entry[2]
    return {"group": group, "chains": chains, "arms": dict(arms),
            "values": list(values), "depth": max(
                [len(entry[3]) for entry in entries] or [0])}


def _exhaustive_single(entries):
    """True when the group is one if, both arms, agreeing on one literal."""
    if len(entries) != 2:
        return None
    arms = {}
    for entry in entries:
        if len(entry[3]) != 1 or not entry[4]:
            return None
        if entry[1] != "str":
            return None
        arms[entry[4][1]] = entry[2]
    if set(arms) != set(["body", "else"]):
        return None
    if len(set(arms.values())) != 1:
        return None
    return list(arms.values())[0]


def guard_entry(name, text, scope, line, tables=None):
    """The shipped answer, or this face own aggregation of a guarded refusal."""
    shipped = _flow().control_flow_entry(name, text, scope, line)
    out = dict(shipped)
    out["source"] = SOURCE_SHIPPED
    out["chains"] = []
    out["groups"] = []
    out["guard_value"] = None
    if shipped.get("state") != "refused":
        return out
    reason = shipped.get("reason") or ""
    if not reason.startswith("guarded:"):
        return out
    tables = guard_tables(text) if tables is None else tables
    if tables is None:
        return out
    inner, where = _scope_table(tables, scope)
    if where != SCOPE_MODULE and name in inner:
        entries = list(inner[name])
    else:
        entries = list(tables["module"].get(name, []))
    before = [entry for entry in entries if entry[0] <= line]
    proven = [entry for entry in before if not entry[3]]
    guarded = [entry for entry in before if entry[3]]
    if proven or not guarded:
        return out
    ordered = []
    for entry in guarded:
        if entry[3][0] not in ordered:
            ordered.append(entry[3][0])
    groups = []
    for group in ordered:
        groups.append(_group_payload(
            group, [entry for entry in guarded if entry[3][0] == group]))
    out["groups"] = groups
    chains = []
    for entry in guarded:
        text_chain = _chain_text(entry[3])
        if text_chain not in chains:
            chains.append(text_chain)
    out["chains"] = chains
    if len(groups) == 1:
        agreed = _exhaustive_single(
            [entry for entry in guarded if entry[3][0] == ordered[0]])
        if agreed is not None:
            out["state"] = STATE_OK
            out["reason"] = None
            out["value"] = agreed
            out["guard_value"] = agreed
            out["source"] = SOURCE_GUARD
            return out
        out["reason"] = REFUSED_GUARDED % chains[0]
        return out
    out["reason"] = REFUSED_GROUPED
    return out


def guard_report(text):
    """One row per loop the shipped control-flow reading publishes."""
    base = _flow()
    shipped = base.control_flow_report(text)
    tables = guard_tables(text)
    rows = []
    for loop in shipped["loops"]:
        names = sorted(set(loop["followed"]) | set(loop["refused"])
                       | set(item["name"] for item in loop.get("arms") or []))
        row = {"line": loop["line"], "kind": loop["kind"],
               "scope": loop["scope"], "followed": {}, "refused": {},
               "arms": [], "chains": {}, "groups": [],
               "base_followed": dict(loop["followed"]),
               "base_refused": dict(loop["refused"]),
               "base_arms": list(loop.get("arms") or []),
               "resolved_by_guard": []}
        for name in names:
            got = guard_entry(name, text, row["scope"], row["line"], tables)
            if got["state"] == "ok":
                row["followed"][name] = got["value"]
                if got["source"] == SOURCE_GUARD:
                    row["resolved_by_guard"].append(name)
            elif got["state"] == STATE_ARMS:
                row["arms"].append({"name": name, "arms": got["arms"]})
            else:
                row["refused"][name] = got["reason"]
                if got["chains"]:
                    row["chains"][name] = list(got["chains"])
                if got["groups"]:
                    row["groups"] = row["groups"] + got["groups"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["guard_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in guard_report(text)["loops"]:
        row["guard_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped control-flow audit, decorated with this face own guards."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise NameBindingGuardScopeError(E_NO_ROOT,
                                         "not a directory: %s" % root_path)
    base = _flow()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise NameBindingGuardScopeError(
            code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_GUARD_STALE
                         if report.get("verdict") == base.SEAMS_STALE
                         else SEAMS_GUARD_COVERED)
    report["base_tool"] = base.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except NameBindingGuardScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_GUARD_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_GUARD_COVERED:
        raise NameBindingGuardScopeError(report["verdict"],
                                         "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="aggregate the guards standing on a binding path")
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
            loops = row["guard_loops"]
            resolved = sum(len(loop["resolved_by_guard"]) for loop in loops)
            sys.stdout.write("  probe %s guard_loops=%d guard_resolved=%d\n"
                             % (row["file"], len(loops), resolved))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_GUARD_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())