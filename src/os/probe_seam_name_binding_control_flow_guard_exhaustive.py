"""probe_seam_name_binding_control_flow_guard_exhaustive - every path.

MEASURED at R2545 on the shipped guard face own reader, in that window own
legs:

  (1) `if a1: KEY = "b" elif a2: KEY = "z" else: KEY = "b"` covers every path
      and dominates to "b", but the reading flattens it to the outer pair and
      reads exclusive arms, so the elif own value never appears AND a provable
      single value is withheld;
  (2) a `match kind: case 1: ... case _: ...` binding is not collected at all,
      so a loop after it reads unbound;
  (3) `KEY = "b" if c else "z"` reads the bare shape word "shape" rather than
      either of its two operands;
  (4) a try/except whose two arms bind the SAME literal is refused exactly
      like the two-arm if the guard face taught to resolve.

This face answers all four on top of the shipped law rather than instead of
it. The shipped guard face is asked FIRST (`guard_entry`, `audit`) and the
shipped control-flow face is asked through it, so every answer those faces
already gave keeps that answer; this module only adds what that reading could
not see:

  exhaustive_tables(text)
      the bindings per SCOPE, each entry carrying its LINE, its value shape,
      its guard CHAIN, the ROOT group it belongs to, its ARM label and whether
      that root group covers EVERY path.
  exhaustive_entry(name, text, scope, line, tables=None)
      the shipped answer, and when the shipped answer was a refusal or an
      INCOMPLETE arm pair, one of four aggregated answers:
        * an if/elif/else chain (or a one-handler try/except with no else and
          no finally) whose every arm binds the same single literal RESOLVES
          to it;
        * the same shape with distinct values publishes EVERY arm by name;
        * a conditional expression publishes its two operands and resolves
          only when they agree;
        * a match statement is COLLECTED as its own guarded group with its
          case count and is never resolved.
  exhaustive_report(text)
      one row per loop the shipped guard reading publishes, each row carrying
      this face own followed / refused / arms / operands / groups / cases and
      the shipped answer beside it.
  audit / reading / guard
      the shipped guard audit asked first, each probe row then decorated with
      this face own exhaustive loops; the seam classifier is still the shipped
      registry `quiets` and nothing here is a second classifier.

RESOLUTION LAW, stated rather than buried: a group resolves ONLY when its
root node COVERS EVERY PATH (an if chain with a final else, or a try with
exactly one handler and no else and no finally) AND every one of its arms
binds the same single string literal. A match statement is never resolved, an
if chain without a final else is never resolved, a two-handler try is never
resolved, and a nested guard keeps the shipped chain answer. A condition is
never evaluated, so the law is SHAPE based.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNCT5). No probe and
no helper is ever imported or run.

Criteria AC-PNCT1..AC-PNCT6 were pinned in state/queue/tech.md:583 at R2545 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: a try arm that binds the name on only SOME
of its statements is still counted as an arm binding (the reading is shape
based, not flow sensitive), a loop inside an arm keeps the shipped loop guard,
and a match never resolves even with a wildcard case. These shapes can
UNDER-report a stale probe but can never invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-EXHAUSTIVE-COVERED)
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

LABEL = "os-probe-seam-name-binding-control-flow-guard-exhaustive"
E_ARGS = "E_PNCT_ARGS"
E_NO_ROOT = "E_PNCT_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_EXHAUSTIVE_COVERED = "SEAMS-EXHAUSTIVE-COVERED"
SEAMS_EXHAUSTIVE_STALE = "SEAMS-EXHAUSTIVE-STALE"

STATE_OK = "ok"
STATE_ARMS = "arms"
REFUSED_CHAIN_ARMS = "exhaustive-arms"
REFUSED_CONDEXPR = "condexpr:%s|%s"
REFUSED_MATCH = "match:%d-cases"
CHAIN_SEP = ">"
SOURCE_SHIPPED = "shipped"
SOURCE_EXHAUSTIVE = "exhaustive"

SCOPE_MODULE = "module"
SCOPE_FUNCTION = "function:%s"
SCOPE_CLASS = "class:%s"

ARM_BODY = "body"
ARM_ELSE = "else"
ARM_ELIF = "elif%d"
ARM_EXCEPT = "except%d"
ARM_CASE = "case%d"

GROUP_IF = "if"
GROUP_TRY = "try"
GROUP_MATCH = "match"

BASE = os.path.dirname(os.path.abspath(__file__))


class NameBindingGuardExhaustiveError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _guard():
    """The shipped guard face (one law, asked not restated)."""
    import probe_seam_name_binding_control_flow_guard_scope
    return probe_seam_name_binding_control_flow_guard_scope


def render_module():
    """The shipped render, imported through the shipped face chain."""
    return _guard().render_module()


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    return _guard().seam_names(module)


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
    return _guard()._value_entry(value)


def _scope_table(tables, scope):
    """The shipped scope resolver (one law, asked not restated)."""
    return _guard()._scope_table(tables, scope)


def _if_chain(node):
    """[(arm label, statements)] for an if/elif/else chain, root first."""
    arms = []
    current = node
    index = 0
    while True:
        label = ARM_BODY if index == 0 else (ARM_ELIF % index)
        arms.append((label, current.body))
        orelse = current.orelse
        if len(orelse) == 1 and isinstance(orelse[0], ast.If):
            index += 1
            current = orelse[0]
            continue
        if orelse:
            arms.append((ARM_ELSE, orelse))
            return arms, True
        return arms, False


def _add(table, name, value, line, chain, group, arm, exhaustive, kind):
    entry_kind, payload = _value_entry(value)
    entry = {"line": line, "kind": entry_kind,
             "value": payload if entry_kind == "str" else None,
             "shape": payload, "operands": None,
             "chain": tuple(chain), "group": group, "arm": arm,
             "exhaustive": bool(exhaustive), "group_kind": kind}
    if isinstance(value, ast.IfExp):
        operands = []
        for side in (value.body, value.orelse):
            side_kind, side_payload = _value_entry(side)
            operands.append({"kind": side_kind,
                             "value": (side_payload if side_kind == "str"
                                       else None),
                             "shape": side_payload})
        entry["kind"] = "condexpr"
        entry["value"] = None
        entry["operands"] = operands
    table.setdefault(name, []).append(entry)


def _collect(stmts, table, groups, chain=(), group=None, arm=None,
             exhaustive=False, kind=None):
    for node in stmts:
        _collect_node(node, table, groups, chain, group, arm, exhaustive, kind)


def _collect_node(node, table, groups, chain, group, arm, exhaustive, kind):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return
    line = getattr(node, "lineno", 0)
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name):
        _add(table, node.targets[0].id, node.value, line, chain, group, arm,
             exhaustive, kind)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        _add(table, node.target.id, node.value, line, chain, group, arm,
             exhaustive, kind)
    elif isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        _add(table, node.target.id, node.value, line, chain, group, arm,
             exhaustive, kind)
    if isinstance(node, ast.For):
        inner = chain + ("loop:%d" % line,)
        if isinstance(node.target, ast.Name):
            value = None
            if isinstance(node.iter, (ast.Tuple, ast.List)) \
                    and len(node.iter.elts) == 1:
                value = node.iter.elts[0]
            _add(table, node.target.id, value, line, inner, group, arm,
                 exhaustive, kind)
        _collect(node.body, table, groups, inner, group, arm, exhaustive, kind)
        _collect(node.orelse, table, groups, chain + ("loop-else:%d" % line,),
                 group, arm, exhaustive, kind)
        return
    if isinstance(node, ast.While):
        inner = chain + ("while:%d" % line,)
        _collect(node.body, table, groups, inner, group, arm, exhaustive, kind)
        _collect(node.orelse, table, groups,
                 chain + ("while-else:%d" % line,), group, arm, exhaustive,
                 kind)
        return
    if isinstance(node, ast.If):
        arms, complete = _if_chain(node)
        key = "if:%d" % line
        inner = chain + (key,)
        groups[key] = {"kind": GROUP_IF, "line": line,
                       "arms": [item[0] for item in arms],
                       "exhaustive": complete, "cases": 0}
        for label, stmts in arms:
            _collect(stmts, table, groups, inner, key, label, complete,
                     GROUP_IF)
        return
    if isinstance(node, (ast.With, ast.AsyncWith)):
        inner = chain + ("with:%d" % line,)
        for item in node.items:
            if isinstance(item.optional_vars, ast.Name):
                table.setdefault(item.optional_vars.id, []).append(
                    {"line": line, "kind": "word", "value": None,
                     "shape": "with-as", "operands": None,
                     "chain": inner, "group": group, "arm": arm,
                     "exhaustive": False, "group_kind": kind})
        _collect(node.body, table, groups, inner, group, arm, exhaustive, kind)
        return
    if isinstance(node, ast.Try):
        key = "try:%d" % line
        inner = chain + (key,)
        arms = [(ARM_BODY, node.body)]
        for index, handler in enumerate(node.handlers):
            arms.append((ARM_EXCEPT % index, handler.body))
        complete = (len(node.handlers) == 1 and not node.orelse
                    and not node.finalbody)
        groups[key] = {"kind": GROUP_TRY, "line": line,
                       "arms": [item[0] for item in arms],
                       "exhaustive": complete, "cases": 0}
        for label, stmts in arms:
            _collect(stmts, table, groups, inner, key, label, complete,
                     GROUP_TRY)
        if node.orelse:
            _collect(node.orelse, table, groups, inner, key, ARM_ELSE, False,
                     GROUP_TRY)
        if node.finalbody:
            _collect(node.finalbody, table, groups,
                     chain + ("finally:%d" % line,), group, arm, exhaustive,
                     kind)
        return
    match_type = getattr(ast, "Match", None)
    if match_type is not None and isinstance(node, match_type):
        key = "match:%d" % line
        inner = chain + (key,)
        labels = [ARM_CASE % index for index in range(len(node.cases))]
        groups[key] = {"kind": GROUP_MATCH, "line": line, "arms": labels,
                       "exhaustive": False, "cases": len(node.cases)}
        for index, case in enumerate(node.cases):
            _collect(case.body, table, groups, inner, key, ARM_CASE % index,
                     False, GROUP_MATCH)
        return
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.stmt):
            _collect_node(child, table, groups, chain, group, arm, exhaustive,
                          kind)


def exhaustive_tables(text):
    """{'module': t, 'functions': {n: t}, 'classes': {n: t}, 'groups': g}."""
    tree = _parse(text)
    if tree is None:
        return None
    module = {}
    groups = {}
    _collect(tree.body, module, groups)
    functions = {}
    classes = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
            continue
        table = {}
        _collect(node.body, table, groups)
        if isinstance(node, ast.ClassDef):
            classes[node.name] = table
        else:
            functions[node.name] = table
    return {"module": module, "functions": functions, "classes": classes,
            "groups": groups}


def _operand_text(operand):
    return operand["value"] if operand["kind"] == "str" else operand["shape"]


def _condexpr_answer(out, entry):
    """A conditional expression: publish both operands, resolve only if equal."""
    operands = list(entry.get("operands") or [])
    out["operands"] = operands
    out["source"] = SOURCE_EXHAUSTIVE
    if len(operands) == 2 and all(item["kind"] == "str" for item in operands) \
            and operands[0]["value"] == operands[1]["value"]:
        out["state"] = STATE_OK
        out["reason"] = None
        out["value"] = operands[0]["value"]
        return out
    out["state"] = "refused"
    out["reason"] = REFUSED_CONDEXPR % (
        _operand_text(operands[0]) if len(operands) > 0 else "?",
        _operand_text(operands[1]) if len(operands) > 1 else "?")
    return out


def _group_payload(key, info, entries):
    """One root group as a row: its arms, its values, its coverage."""
    chains = []
    arm_values = {}
    values = []
    literals = True
    for entry in entries:
        text_chain = CHAIN_SEP.join(entry["chain"])
        if text_chain and text_chain not in chains:
            chains.append(text_chain)
        if entry["arm"] is None or entry["kind"] != "str":
            literals = False
            continue
        arm_values.setdefault(entry["arm"], set()).add(entry["value"])
        if entry["value"] not in values:
            values.append(entry["value"])
    arms = {}
    for arm in sorted(arm_values):
        if len(arm_values[arm]) == 1:
            arms[arm] = sorted(arm_values[arm])[0]
    return {"group": key, "kind": info.get("kind"),
            "exhaustive": bool(info.get("exhaustive")),
            "cases": info.get("cases", 0), "chains": chains, "arms": arms,
            "values": list(values), "literals": literals,
            "covered": set(arm_values) == set(info.get("arms") or [])}


def exhaustive_entry(name, text, scope, line, tables=None):
    """The shipped answer, extended by an exhaustive-path reading."""
    shipped = _guard().guard_entry(name, text, scope, line)
    out = dict(shipped)
    out["source"] = SOURCE_SHIPPED
    out["base_state"] = shipped.get("state")
    out["operands"] = None
    out["exh_groups"] = []
    out["group"] = None
    out["cases"] = 0
    if shipped.get("state") == STATE_OK:
        return out
    tables = exhaustive_tables(text) if tables is None else tables
    if tables is None:
        return out
    inner, where = _scope_table(tables, scope)
    if where != SCOPE_MODULE and name in inner:
        entries = list(inner[name])
    else:
        entries = list(tables["module"].get(name, []))
    before = [entry for entry in entries if entry["line"] <= line]
    plain = [entry for entry in before
             if not entry["chain"] and entry["kind"] != "condexpr"]
    if plain:
        return out
    conds = [entry for entry in before
             if not entry["chain"] and entry["kind"] == "condexpr"]
    if conds:
        return _condexpr_answer(out, conds[-1])
    guarded = [entry for entry in before if entry["chain"]]
    if not guarded:
        return out
    order = []
    for entry in guarded:
        if entry["group"] and entry["group"] not in order:
            order.append(entry["group"])
    payloads = []
    for key in order:
        info = tables["groups"].get(key) or {}
        payloads.append(_group_payload(
            key, info, [entry for entry in guarded
                        if entry["group"] == key]))
    out["exh_groups"] = payloads
    if len(order) != 1:
        return out
    key = order[0]
    info = tables["groups"].get(key) or {}
    payload = payloads[0]
    out["group"] = key
    out["cases"] = info.get("cases", 0)
    out["source"] = SOURCE_EXHAUSTIVE
    if info.get("kind") == GROUP_MATCH:
        out["state"] = "refused"
        out["reason"] = REFUSED_MATCH % info.get("cases", 0)
        return out
    if not (info.get("exhaustive") and payload["literals"]
            and payload["covered"]):
        return out
    if len(payload["values"]) == 1:
        out["state"] = STATE_OK
        out["reason"] = None
        out["value"] = payload["values"][0]
        return out
    out["state"] = STATE_ARMS
    out["reason"] = REFUSED_CHAIN_ARMS
    out["value"] = None
    out["arms"] = [{"group": key, "arm": arm, "value": payload["arms"][arm]}
                   for arm in sorted(payload["arms"])]
    return out


def exhaustive_report(text):
    """One row per loop the shipped guard reading publishes."""
    base = _guard()
    shipped = base.guard_report(text)
    tables = exhaustive_tables(text)
    rows = []
    for loop in shipped["loops"]:
        names = sorted(set(loop["followed"]) | set(loop["refused"])
                       | set(item["name"] for item in loop.get("arms") or []))
        row = {"line": loop["line"], "kind": loop["kind"],
               "scope": loop["scope"], "followed": {}, "refused": {},
               "arms": [], "operands": {}, "exh_groups": [], "cases": {},
               "base_followed": dict(loop["followed"]),
               "base_refused": dict(loop["refused"]),
               "base_arms": list(loop.get("arms") or []),
               "base_groups": list(loop.get("groups") or []),
               "resolved_by_exhaustive": []}
        for name in names:
            got = exhaustive_entry(name, text, row["scope"], row["line"],
                                   tables)
            if got["state"] == STATE_OK:
                row["followed"][name] = got["value"]
                if got["source"] == SOURCE_EXHAUSTIVE:
                    row["resolved_by_exhaustive"].append(name)
            elif got["state"] == STATE_ARMS:
                row["arms"].append({"name": name, "arms": got["arms"]})
            else:
                row["refused"][name] = got["reason"]
            if got.get("operands"):
                row["operands"][name] = list(got["operands"])
            if got.get("exh_groups"):
                row["exh_groups"] = row["exh_groups"] + got["exh_groups"]
            if got.get("cases"):
                row["cases"][name] = got["cases"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["exhaustive_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in exhaustive_report(text)["loops"]:
        row["exhaustive_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped guard audit, decorated with this face own path rows."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise NameBindingGuardExhaustiveError(E_NO_ROOT,
                                              "not a directory: %s"
                                              % root_path)
    base = _guard()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise NameBindingGuardExhaustiveError(
            code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_EXHAUSTIVE_STALE
                         if report.get("verdict") == base.SEAMS_GUARD_STALE
                         else SEAMS_EXHAUSTIVE_COVERED)
    report["base_tool"] = base.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except NameBindingGuardExhaustiveError as exc:
        return {"tool": LABEL, "verdict": SEAMS_EXHAUSTIVE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_EXHAUSTIVE_COVERED:
        raise NameBindingGuardExhaustiveError(report["verdict"],
                                              "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a binding only when every path binds one value")
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
            loops = row["exhaustive_loops"]
            resolved = sum(len(loop["resolved_by_exhaustive"])
                           for loop in loops)
            sys.stdout.write("  probe %s exhaustive_loops=%d "
                             "exhaustive_resolved=%d\n"
                             % (row["file"], len(loops), resolved))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_EXHAUSTIVE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())