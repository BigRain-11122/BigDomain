"""probe_seam_name_binding_nested_exhaustive_path - every leaf of a tree.

MEASURED at R2547 on the shipped exhaustive face own reader, in that window
own legs:

  (1) `if a: (if b: KEY = "b" else: KEY = "b") else: KEY = "b"` agrees on
      EVERY path, yet reads as TWO groups - `if:3` exhaustive and `if:2`
      covering only its else arm - so the group key being the INNERMOST If
      hides the outer arm that only contains a block, and nothing resolves;
  (2) an arm that binds nothing on one of its paths is still published as an
      arm binding, because the reading is shape based;
  (3) a loop inside an arm keeps the shipped loop guard and is never folded
      into the root group own coverage.

This face answers all three on top of the shipped law rather than instead of
it. The shipped exhaustive face is asked FIRST (`nested_entry` asks it, and
`audit` asks its `audit`), and the shipped guard face is asked beside it, so
every answer those faces already gave keeps that answer:

  nested_tables(text)
      the bindings per SCOPE, each carrying its LINE, its value shape, the
      whole PATH of (group, arm) steps that must run for it to exist - outer
      step first - and the LOOP LINES standing on that path.
  nested_entry(name, text, scope, line, tables=None)
      the shipped answer, or, when both shipped faces could not resolve a
      guarded binding, ONE folded answer:
        * a guard tree whose EVERY leaf binds the same single literal
          RESOLVES to it, however deep the nesting;
        * a leaf that binds nothing is NAMED partial:<arm>;
        * a loop standing on the path is NAMED loop:<line>;
        * leaves that DISAGREE publish EVERY leaf by its full path
          (if:2/body>if:3/else) and resolve nothing.
  nested_report(text)
      one row per loop the shipped exhaustive reading publishes, each row
      carrying this face own followed / refused / leaves / partial / loops /
      groups and BOTH shipped answers beside it.
  audit / reading / guard
      the shipped exhaustive audit asked first, each probe row then decorated
      with this face own folded loops; the seam classifier is still the
      shipped registry `quiets` and nothing here is a second classifier.

RESOLUTION LAW, stated rather than buried: a tree resolves ONLY when every
group on it covers EVERY path (an if/elif/else chain with a final else, or a
try with exactly one handler and no else and no finally) AND every leaf path
binds the same single string literal. A match is never resolved, a chain
without a final else is never resolved, a leaf that binds nothing or sits
under a loop is never resolved, and a condition is never evaluated, so the law
is SHAPE based.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNCD5). No probe and
no helper is ever imported or run.

Criteria AC-PNCD1..AC-PNCD6 were pinned in state/queue/tech.md:585 at R2547 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: an arm that binds directly AND contains a
nested group is refused rather than merged, a `with ... as NAME` binding is
never counted as coverage, and a plain assignment anywhere before the loop
short-circuits the fold exactly as the shipped faces do. These shapes can
UNDER-report a stale probe but can never invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-NESTED-COVERED)
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

LABEL = "os-probe-seam-name-binding-nested-exhaustive-path"
E_ARGS = "E_PNCD_ARGS"
E_NO_ROOT = "E_PNCD_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_NESTED_COVERED = "SEAMS-NESTED-COVERED"
SEAMS_NESTED_STALE = "SEAMS-NESTED-STALE"

STATE_OK = "ok"
STATE_ARMS = "arms"
STATE_PARTIAL = "partial"
STATE_LOOP = "loop"
STATE_REFUSED = "refused"

REFUSED_PARTIAL = "partial:%s"
REFUSED_LOOP = "loop:%d"
REFUSED_NESTED_ARMS = "nested-arms"
REFUSED_INCOMPLETE = "incomplete:%s"
REFUSED_MATCH = "match:%d-cases"
REFUSED_MIXED = "mixed:%s"
REFUSED_GROUPED = "grouped:%s"
REFUSED_UNKNOWN = "unknown-group:%s"
REFUSED_NON_LITERAL = "non-literal:%s"
PATH_SEP = ">"
STEP_SEP = "/"
SOURCE_SHIPPED = "shipped"
SOURCE_EXHAUSTIVE = "exhaustive"
SOURCE_GUARD = "guard"
SOURCE_NESTED = "nested"

SCOPE_MODULE = "module"
SCOPE_FUNCTION = "function:%s"
SCOPE_CLASS = "class:%s"

BASE = os.path.dirname(os.path.abspath(__file__))


class NameBindingNestedExhaustiveError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _flow():
    """The shipped control-flow face (one law, asked not restated)."""
    import probe_seam_name_binding_control_flow_scope
    return probe_seam_name_binding_control_flow_scope


def _guard():
    """The shipped guard face (one law, asked not restated)."""
    import probe_seam_name_binding_control_flow_guard_scope
    return probe_seam_name_binding_control_flow_guard_scope


def _exh():
    """The shipped exhaustive face this module extends."""
    import probe_seam_name_binding_control_flow_guard_exhaustive
    return probe_seam_name_binding_control_flow_guard_exhaustive


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
    return _flow()._value_entry(value)


def _path_text(path):
    return PATH_SEP.join("%s%s%s" % (group, STEP_SEP, arm)
                         for group, arm in path)


def _record(table, name, value, line, path, loops):
    if value is None:
        kind, payload = "none", None
    else:
        kind, payload = _value_entry(value)
    table.setdefault(name, []).append(
        {"name": name, "line": line, "path": tuple(path), "loops": tuple(loops),
         "kind": kind, "value": (payload if kind == "str" else None),
         "shape": payload})


def _walk(stmts, table, groups, path=(), loops=()):
    for node in stmts:
        _walk_node(node, table, groups, path, loops)


def _walk_node(node, table, groups, path, loops):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return
    line = getattr(node, "lineno", 0)
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name):
        _record(table, node.targets[0].id, node.value, line, path, loops)
        return
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        _record(table, node.target.id, node.value, line, path, loops)
        return
    if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        _record(table, node.target.id, node.value, line, path, loops)
        return
    if isinstance(node, ast.For):
        inner = tuple(loops) + (line,)
        if isinstance(node.target, ast.Name):
            value = None
            if isinstance(node.iter, (ast.Tuple, ast.List)) \
                    and len(node.iter.elts) == 1:
                value = node.iter.elts[0]
            _record(table, node.target.id, value, line, path, inner)
        _walk(node.body, table, groups, path, inner)
        _walk(node.orelse, table, groups, path, loops)
        return
    if isinstance(node, ast.While):
        inner = tuple(loops) + (line,)
        _walk(node.body, table, groups, path, inner)
        _walk(node.orelse, table, groups, path, loops)
        return
    if isinstance(node, ast.If):
        key = "if:%d" % line
        arms, complete = _exh()._if_chain(node)
        groups[key] = {"kind": "if", "line": line,
                       "arms": [item[0] for item in arms],
                       "exhaustive": bool(complete), "cases": 0}
        for label, stmts in arms:
            _walk(stmts, table, groups, tuple(path) + ((key, label),), loops)
        return
    if isinstance(node, (ast.With, ast.AsyncWith)):
        for item in node.items:
            if isinstance(item.optional_vars, ast.Name):
                table.setdefault(item.optional_vars.id, []).append(
                    {"name": item.optional_vars.id, "line": line,
                     "path": tuple(path), "loops": tuple(loops),
                     "kind": "word", "value": None, "shape": "with-as"})
        _walk(node.body, table, groups, path, loops)
        return
    if isinstance(node, ast.Try):
        key = "try:%d" % line
        arms = [("body", node.body)]
        for index, handler in enumerate(node.handlers):
            arms.append(("except%d" % index, handler.body))
        complete = (len(node.handlers) == 1 and not node.orelse
                    and not node.finalbody)
        groups[key] = {"kind": "try", "line": line,
                       "arms": [item[0] for item in arms],
                       "exhaustive": bool(complete), "cases": 0}
        for label, stmts in arms:
            _walk(stmts, table, groups, tuple(path) + ((key, label),), loops)
        if node.orelse:
            _walk(node.orelse, table, groups,
                  tuple(path) + ((key, "else"),), loops)
        if node.finalbody:
            _walk(node.finalbody, table, groups,
                  tuple(path) + ((key, "finally"),), loops)
        return
    match_type = getattr(ast, "Match", None)
    if match_type is not None and isinstance(node, match_type):
        key = "match:%d" % line
        labels = ["case%d" % index for index in range(len(node.cases))]
        groups[key] = {"kind": "match", "line": line, "arms": labels,
                       "exhaustive": False, "cases": len(node.cases)}
        for index, case in enumerate(node.cases):
            _walk(case.body, table, groups,
                  tuple(path) + ((key, labels[index]),), loops)
        return
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.stmt):
            _walk_node(child, table, groups, path, loops)


def nested_tables(text):
    """{'module': t, 'functions': {n: t}, 'classes': {n: t}, 'groups': g}."""
    tree = _parse(text)
    if tree is None:
        return None
    module = {}
    groups = {}
    _walk(tree.body, module, groups)
    functions = {}
    classes = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
            continue
        table = {}
        _walk(node.body, table, groups)
        if isinstance(node, ast.ClassDef):
            classes[node.name] = table
        else:
            functions[node.name] = table
    return {"module": module, "functions": functions, "classes": classes,
            "groups": groups}


def _scope_table(tables, scope):
    if scope == SCOPE_MODULE:
        return tables["module"], SCOPE_MODULE
    head, _, name = scope.partition(":")
    if head == "function":
        return tables["functions"].get(name, {}), SCOPE_FUNCTION % name
    if head == "class":
        return tables["classes"].get(name, {}), SCOPE_CLASS % name
    return {}, scope


def _group_payload(key, info):
    return {"group": key, "kind": info.get("kind"),
            "exhaustive": bool(info.get("exhaustive")),
            "cases": info.get("cases", 0),
            "arms": list(info.get("arms") or [])}


def _fold(key, prefix, entries, groups, leaves, payloads, depth=0):
    """Fold one group: resolve only when every leaf binds the same literal."""
    info = groups.get(key)
    if info is None:
        return {"state": STATE_REFUSED, "reason": REFUSED_UNKNOWN % key}
    if info.get("kind") == "match":
        return {"state": STATE_REFUSED,
                "reason": REFUSED_MATCH % info.get("cases", 0),
                "cases": info.get("cases", 0)}
    if not info.get("exhaustive"):
        return {"state": STATE_REFUSED, "reason": REFUSED_INCOMPLETE % key}
    if depth > 16:
        return {"state": STATE_REFUSED, "reason": REFUSED_GROUPED % key}
    if not [item for item in payloads if item["group"] == key]:
        payloads.append(_group_payload(key, info))
    results = []
    for arm in info.get("arms") or []:
        here = tuple(prefix) + ((key, arm),)
        direct = [entry for entry in entries if entry["path"] == here]
        deeper = [entry for entry in entries
                  if len(entry["path"]) > len(here)
                  and entry["path"][:len(here)] == here]
        loop_hit = [entry for entry in direct + deeper if entry["loops"]]
        if loop_hit:
            results.append({"state": STATE_LOOP,
                            "reason": REFUSED_LOOP % loop_hit[0]["loops"][0]})
            continue
        if direct and deeper:
            results.append({"state": STATE_REFUSED,
                            "reason": REFUSED_MIXED % arm})
            continue
        if direct:
            literals = [entry for entry in direct if entry["kind"] == "str"]
            if len(literals) != len(direct):
                results.append({"state": STATE_REFUSED,
                                "reason": REFUSED_NON_LITERAL % arm})
                continue
            values = sorted(set(entry["value"] for entry in direct))
            leaves.append({"path": _path_text(here), "arm": arm,
                           "value": (values[0] if len(values) == 1 else None),
                           "values": values})
            if len(values) == 1:
                results.append({"state": STATE_OK, "value": values[0]})
            else:
                results.append({"state": STATE_ARMS, "arm": arm,
                                "values": values})
            continue
        if deeper:
            keys = []
            for entry in deeper:
                nxt = entry["path"][len(here)][0]
                if nxt not in keys:
                    keys.append(nxt)
            if len(keys) != 1:
                results.append({"state": STATE_REFUSED,
                                "reason": REFUSED_GROUPED % arm})
                continue
            results.append(_fold(keys[0], here, deeper, groups, leaves,
                                 payloads, depth + 1))
            continue
        leaves.append({"path": _path_text(here), "arm": arm, "value": None,
                       "values": []})
        results.append({"state": STATE_PARTIAL,
                        "reason": REFUSED_PARTIAL % arm})
    for want in (STATE_REFUSED, STATE_LOOP, STATE_PARTIAL):
        for item in results:
            if item["state"] == want:
                return item
    values = []
    for item in results:
        if item["state"] == STATE_OK:
            values.append(item["value"])
        elif item["state"] == STATE_ARMS:
            values.extend(item.get("values") or [])
    values = sorted(set(values))
    if len(values) == 1:
        return {"state": STATE_OK, "value": values[0]}
    return {"state": STATE_ARMS, "reason": REFUSED_NESTED_ARMS,
            "values": values, "arms": list(results)}


def _shipped_answer(out, shipped):
    """Publish the shipped answer verbatim rather than inventing another."""
    if shipped.get("state") == STATE_OK:
        out["state"] = STATE_OK
        out["value"] = shipped.get("value")
        out["reason"] = None
        out["source"] = shipped.get("source") or SOURCE_SHIPPED
        return out
    if shipped.get("state") == STATE_ARMS:
        out["state"] = STATE_ARMS
        out["reason"] = shipped.get("reason")
        out["source"] = shipped.get("source") or SOURCE_SHIPPED
        return out
    out["state"] = STATE_REFUSED
    out["reason"] = shipped.get("reason")
    out["source"] = shipped.get("source") or SOURCE_SHIPPED
    return out


def nested_entry(name, text, scope, line, tables=None):
    """The shipped answer, or this face own folded tree answer."""
    guard = _guard().guard_entry(name, text, scope, line)
    shipped = _exh().exhaustive_entry(name, text, scope, line)
    out = {"name": name, "scope": scope, "line": line,
           "state": STATE_REFUSED, "reason": None, "value": None,
           "source": SOURCE_SHIPPED,
           "base_state": shipped.get("state"),
           "base_reason": shipped.get("reason"),
           "base_source": shipped.get("source"),
           "base_guard_state": guard.get("state"),
           "base_guard_reason": guard.get("reason"),
           "root": None, "groups": [], "leaves": [], "partial": None,
           "loop": None, "cases": 0, "arms": [], "values": []}
    if guard.get("state") == STATE_OK:
        out["state"] = STATE_OK
        out["value"] = guard.get("value")
        out["reason"] = None
        return out
    tables = nested_tables(text) if tables is None else tables
    if tables is None:
        return out
    inner, where = _scope_table(tables, scope)
    if where != SCOPE_MODULE and name in inner:
        entries = list(inner[name])
    else:
        entries = list(tables["module"].get(name, []))
    before = [entry for entry in entries if entry["line"] <= line]
    plain = [entry for entry in before
             if not entry["path"] and not entry["loops"]
             and entry["kind"] != "condexpr"]
    if plain:
        return _shipped_answer(out, shipped)
    conds = [entry for entry in before
             if not entry["path"] and not entry["loops"]
             and entry["kind"] == "condexpr"]
    if conds:
        return _shipped_answer(out, shipped)
    roots = []
    for entry in before:
        if entry["path"]:
            root = entry["path"][0][0]
            if root not in roots:
                roots.append(root)
    if not roots:
        return _shipped_answer(out, shipped)
    payloads = []
    if len(roots) > 1:
        for key in roots:
            info = tables["groups"].get(key)
            if info:
                payloads.append(_group_payload(key, info))
        out["groups"] = payloads
        if shipped.get("state") == STATE_OK:
            return _shipped_answer(out, shipped)
        out["reason"] = REFUSED_GROUPED % ",".join(roots)
        out["source"] = SOURCE_NESTED
        return out
    root = roots[0]
    leaves = []
    folded = _fold(root, (), before, tables["groups"], leaves, payloads)
    out["root"] = root
    out["groups"] = payloads
    out["leaves"] = leaves
    out["source"] = SOURCE_NESTED
    if folded["state"] == STATE_OK:
        out["state"] = STATE_OK
        out["reason"] = None
        out["value"] = folded["value"]
        return out
    out["state"] = STATE_REFUSED
    out["reason"] = folded.get("reason")
    if folded["state"] == STATE_PARTIAL:
        out["partial"] = folded.get("reason", "").split(":", 1)[-1]
    if folded["state"] == STATE_LOOP:
        out["loop"] = folded.get("reason")
    if folded["state"] == STATE_ARMS:
        out["state"] = STATE_ARMS
        out["reason"] = REFUSED_NESTED_ARMS
        out["values"] = list(folded.get("values") or [])
        out["arms"] = list(folded.get("arms") or [])
    if folded.get("cases"):
        out["cases"] = folded.get("cases")
    return out


def nested_report(text):
    """One row per loop the shipped exhaustive reading publishes."""
    base = _exh()
    guard_rows = _guard().guard_report(text)["loops"]
    shipped = base.exhaustive_report(text)
    tables = nested_tables(text)
    rows = []
    for index, loop in enumerate(shipped["loops"]):
        names = sorted(set(loop["followed"]) | set(loop["refused"])
                       | set(item["name"] for item in loop.get("arms") or []))
        guard_row = {}
        for item in guard_rows:
            if item.get("line") == loop.get("line") \
                    and item.get("scope") == loop.get("scope"):
                guard_row = item
                break
        row = {"line": loop["line"], "kind": loop["kind"],
               "scope": loop["scope"], "followed": {}, "refused": {},
               "arms": [], "leaves": {}, "partial": {}, "loops": {},
               "groups": [], "resolved_by_nested": [],
               "base_followed": dict(loop["followed"]),
               "base_refused": dict(loop["refused"]),
               "base_arms": list(loop.get("arms") or []),
               "base_groups": list(loop.get("groups") or []),
               "base_guard_followed": dict(guard_row.get("followed") or {}),
               "base_guard_refused": dict(guard_row.get("refused") or {})}
        for name in names:
            got = nested_entry(name, text, row["scope"], row["line"], tables)
            if got["state"] == STATE_OK:
                row["followed"][name] = got["value"]
                if got["source"] == SOURCE_NESTED:
                    row["resolved_by_nested"].append(name)
            elif got["state"] == STATE_ARMS:
                row["arms"].append({"name": name, "arms": got["arms"],
                                    "leaves": got["leaves"]})
            else:
                row["refused"][name] = got["reason"]
            if got.get("leaves"):
                row["leaves"][name] = got["leaves"]
            if got.get("partial"):
                row["partial"][name] = got["partial"]
            if got.get("loop"):
                row["loops"][name] = got["loop"]
            if got.get("groups"):
                for payload in got["groups"]:
                    if payload not in row["groups"]:
                        row["groups"].append(payload)
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["nested_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in nested_report(text)["loops"]:
        row["nested_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped exhaustive audit, decorated with this face own folds."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise NameBindingNestedExhaustiveError(E_NO_ROOT,
                                               "not a directory: %s"
                                               % root_path)
    base = _exh()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise NameBindingNestedExhaustiveError(
            code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_NESTED_STALE
                         if report.get("verdict") == base.SEAMS_EXHAUSTIVE_STALE
                         else SEAMS_NESTED_COVERED)
    report["base_tool"] = base.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except NameBindingNestedExhaustiveError as exc:
        return {"tool": LABEL, "verdict": SEAMS_NESTED_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_NESTED_COVERED:
        raise NameBindingNestedExhaustiveError(report["verdict"],
                                               "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="fold a nested guard tree whose every leaf agrees")
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
            loops = row["nested_loops"]
            resolved = sum(len(loop["resolved_by_nested"]) for loop in loops)
            sys.stdout.write("  probe %s nested_loops=%d nested_resolved=%d\n"
                             % (row["file"], len(loops), resolved))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_NESTED_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())