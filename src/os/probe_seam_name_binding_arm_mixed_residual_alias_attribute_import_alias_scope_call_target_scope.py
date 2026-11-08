"""AC-PNDCF1..AC-PNDCF6: the call-target / local-return / relative-import /
nested-constant face (R2569).

Criteria were pinned in state/queue/tech.md:603 at R2565 BEFORE this code
existed.

What this proves, MEASURED at R2565 with src/os/limits_from_scope_R2565.py
against one private world where the honest answer is `b`, and RE-MEASURED here
before any code was written:
  (1) a with-as binding whose CONTEXT is a call on an ATTRIBUTE
      (`with Box().open() as m`) reads attr-with-as:m.ATTR and is never
      resolved even when that method returns a module name, because only a
      bare-name call is looked up;
  (2) a call that returns its module name through a LOCAL variable
      (`m = "hw3"; return m`) reads attr-with-as:m.ATTR, because only a
      returned str literal or a module-level name is followed;
  (3) a relative `from . import helper` reads attr-base-local:helper, because
      a level-bearing ImportFrom is skipped outright;
  (4) a constant declared in a NESTED function is resolved through the inner
      function (ok/b), which is an OVER-resolution because nothing in the
      outer scope binds it.

This face asks the shipped from-scope reading FIRST and carries every key it
published, unchanged, on every row, then re-reads:
  * a with-as context that is a call on an attribute resolves when that call
    returns a module name and is NAMED otherwise (AC-PNDCF1);
  * a function returning its module name through a LOCAL variable resolves
    (AC-PNDCF2);
  * a relative `from . import helper` resolves against the package own
    directory and is never a local (AC-PNDCF3);
  * a constant bound only inside a NESTED function is NAMED rather than
    resolved, even where the shipped faces resolved it (AC-PNDCF4);
  * every answer the ten shipped faces already gave rides beside this face
    own on every row (AC-PNDCF5).

Nothing is imported and nothing is evaluated: every value comes from reading
source text. Stdlib only, ASCII source, zero network, no clock.
"""

import argparse
import ast
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_from_scope as PNDCE  # noqa: E402

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-call-target-scope")

E_ARGS = "E_PNDCF_ARGS"
E_NO_ROOT = "E_PNDCF_NO_ROOT"

STATE_OK = PNDCE.STATE_OK
STATE_REFUSED = PNDCE.STATE_REFUSED

REFUSED_ATTR_CALL_TARGET = "attr-call-target:%s"
REFUSED_ATTR_NESTED_CONSTANT = "attr-nested-constant:%s"
REFUSED_ATTR_RELATIVE = "attr-relative-import:%s"
REFUSED_ATTR_FROM_IMPORT = PNDCE.REFUSED_ATTR_FROM_IMPORT
REFUSED_ATTR_FROM_ALIAS = PNDCE.REFUSED_ATTR_FROM_ALIAS
REFUSED_ATTR_FUNCTION_CONSTANT = PNDCE.REFUSED_ATTR_FUNCTION_CONSTANT
REFUSED_ATTR_FUNCTION_MIXED = PNDCE.REFUSED_ATTR_FUNCTION_MIXED
REFUSED_ATTR_WITH_AS_CALL = PNDCE.REFUSED_ATTR_WITH_AS_CALL

SOURCE_CALL_TARGET = "call-target"

COVERED = PNDCE.COVERED
MISSING_SEAM = PNDCE.MISSING_SEAM
OUT_OF_SCOPE = PNDCE.OUT_OF_SCOPE
UNREADABLE = PNDCE.UNREADABLE
HISTORICAL = PNDCE.HISTORICAL

SEAMS_CALL_TARGET_COVERED = "SEAMS-CALL-TARGET-COVERED"
SEAMS_CALL_TARGET_STALE = "SEAMS-CALL-TARGET-STALE"

MAX_CHAIN = PNDCE.MAX_CHAIN

_parse = PNDCE._parse
_read = PNDCE._read
_str_constant = PNDCE._str_constant
_module_file = PNDCE._module_file


class CallTargetError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def module_level_constants(tree):
    """Name -> str literal bound at module level only."""
    out = {}
    if tree is None:
        return out
    for node in tree.body:
        if isinstance(node, ast.Assign):
            literal = _str_constant(node.value)
            if literal is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = literal
        elif isinstance(node, ast.AnnAssign):
            if not isinstance(node.target, ast.Name) or node.value is None:
                continue
            literal = _str_constant(node.value)
            if literal is not None:
                out[node.target.id] = literal
    return out


def call_target_functions(tree, root):
    """Function or method name -> module it returns.

    A function counts when a Return hands back a str literal, a module-level
    name, or a LOCAL it bound to a literal. Methods are read the same way,
    which is what lets a call on an attribute resolve.
    """
    out = {}
    if tree is None:
        return out
    wide = module_level_constants(tree)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        binds = {}
        for item in ast.walk(node):
            if isinstance(item, ast.Assign):
                literal = _str_constant(item.value)
                if literal is None:
                    continue
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        binds[target.id] = literal
            elif isinstance(item, ast.AnnAssign):
                if not isinstance(item.target, ast.Name):
                    continue
                if item.value is None:
                    continue
                literal = _str_constant(item.value)
                if literal is not None:
                    binds[item.target.id] = literal
        for item in ast.walk(node):
            if not isinstance(item, ast.Return) or item.value is None:
                continue
            literal = _str_constant(item.value)
            if literal is None and isinstance(item.value, ast.Name):
                literal = binds.get(item.value.id) or wide.get(item.value.id)
            if literal is None:
                continue
            if _module_file(root, literal) is None:
                continue
            out.setdefault(node.name, literal)
    return out


def with_as_targets(tree, root):
    """`with call() as NAME` bindings -> (module or None, hop word).

    A bare-name call and a call on an attribute are both looked up by the
    function name that returns the module; an attribute call that returns
    nothing still records its hop so it can be NAMED rather than silently
    left as the shipped with-as word.
    """
    out = {}
    if tree is None:
        return out
    callers = call_target_functions(tree, root)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            var = item.optional_vars
            if not isinstance(var, ast.Name):
                continue
            if not isinstance(item.context_expr, ast.Call):
                continue
            func = item.context_expr.func
            if isinstance(func, ast.Name):
                if func.id in callers:
                    out[var.id] = (callers[func.id], "with-as-call")
            elif isinstance(func, ast.Attribute):
                out[var.id] = (callers.get(func.attr), "with-as-call-target")
    return out


def from_import_modules_scoped(tree, root):
    """Bound name -> (module dotted, whether the import was relative).

    The shipped reading takes plain ast.Import nodes only, so a FROM-import is
    mistaken for a local; this reading resolves an absolute and a one-level
    relative ImportFrom against the package own directory.
    """
    out = PNDCE.from_import_modules(tree, root)
    scoped = {name: (dotted, False) for name, dotted in out.items()}
    if tree is None:
        return scoped
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level not in (0, 1):
            continue
        relative = node.level == 1
        if not relative and not node.module:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            if node.module:
                dotted = "%s.%s" % (node.module, alias.name)
            else:
                dotted = alias.name
            if _module_file(root, dotted) is None:
                continue
            scoped[alias.asname or alias.name] = (dotted, relative)
    return scoped


def function_constants_scoped(tree):
    """Name -> (literal values, whether a module-level function returns it).

    Only a function whose own chain carries no other function is read, so a
    constant that nothing outside the inner scope binds is never published.
    """
    out = {}
    if tree is None:
        return out

    def collect(node):
        assigned = {}
        returned = set()
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        assigned.setdefault(target.id, []).append(item.value)
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name) and item.value is not None:
                    assigned.setdefault(item.target.id, []).append(item.value)
            elif isinstance(item, ast.Return):
                if isinstance(item.value, ast.Name):
                    returned.add(item.value.id)
        for name, nodes in assigned.items():
            literals = set()
            clean = True
            for value in nodes:
                literal = _str_constant(value)
                if literal is None:
                    clean = False
                    continue
                literals.add(literal)
            if not clean:
                continue
            previous = out.setdefault(name, (set(), False))
            out[name] = (previous[0] | literals,
                         previous[1] or name in returned)

    def visit(node, depth):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if depth == 0:
                    collect(child)
                visit(child, depth + 1)
            else:
                visit(child, depth)

    visit(tree, 0)
    return out


def module_attribute_scoped(root, dotted, attr):
    """Module-level constants first, then a module-level function constant."""
    decision, values, hop = PNDCE.PNDC.module_attribute(root, dotted, attr)
    if decision in ("ok", "mixed"):
        return decision, values, hop
    path = _module_file(root, dotted)
    if path is None:
        return decision, values, hop
    try:
        tree = _parse(_read(path))
    except OSError:
        return decision, values, hop
    if tree is None:
        return decision, values, hop
    table = function_constants_scoped(tree)
    if attr not in table:
        return decision, values, hop
    literals, returned = table[attr]
    if not returned:
        return "function-constant", set(), "%s/function" % hop
    if len(literals) > 1:
        return "function-mixed", literals, "%s/function" % hop
    return "ok", set(literals), "%s/function" % hop


def module_of(tree, root, base, first):
    """(module dotted or None, hop word, aliased) for an attribute base."""
    targets = with_as_targets(tree, root)
    if first in targets:
        dotted, hop = targets[first]
        return dotted, hop, False
    from_mods = from_import_modules_scoped(tree, root)
    if first in from_mods:
        dotted, relative = from_mods[first]
        return dotted, ("from-relative" if relative else "from-import"), True
    imports = PNDCE.PNDC.import_bindings(tree)
    if first in imports:
        aliases = PNDCE.PNDC.import_aliases(tree)
        return imports[first], ("import-alias" if first in aliases
                                else "import"), first in aliases
    return None, None, False


def _wrap(name, tree, scope, line):
    picked = PNDCE.PNDC.PNDB._follow(name, tree, scope, line)
    if picked is None:
        return None
    node = picked[1]
    if isinstance(node, ast.NamedExpr):
        node = node.value
    if not isinstance(node, ast.Attribute):
        return None
    return node


def call_target_entry(name, text, scope, line, tables=None, root=None):
    """The shipped from-scope answer, carried, plus this face own re-read."""
    root_path = BASE if root is None else root
    tables_full = (PNDCE.PNDC.PNDB.predicate_tables(text, scope, root_path)
                   if tables is None else tables)
    shipped = PNDCE.from_scope_entry(name, text, scope, line, tables_full,
                                     root_path)
    got = dict(shipped)
    for key in sorted(shipped):
        got.setdefault(key, shipped[key])
    got["base_ct_state"] = shipped.get("state")
    got["base_ct_reason"] = shipped.get("reason")
    got["base_ct_value"] = shipped.get("value")
    got["base_ct_hop"] = shipped.get("from_hop")
    got["base_ct_source"] = shipped.get("from_source")
    got["base_shipped_state"] = shipped.get("base_shipped_state")
    got["base_shipped_reason"] = shipped.get("base_shipped_reason")
    got["ct_state"] = shipped.get("state")
    got["ct_reason"] = shipped.get("reason")
    got["ct_value"] = shipped.get("value")
    got["ct_hop"] = shipped.get("from_hop")
    got["ct_chain"] = list(shipped.get("from_chain") or [])
    got["ct_source"] = SOURCE_CALL_TARGET
    tree = (tables_full or {}).get("predicate_tree")
    if tree is None:
        return got
    node = _wrap(name, tree, scope, line)
    if node is None:
        return got
    attr = node.attr
    base = PNDCE.PNDC.PNDB.base_text(node.value)
    if not base:
        return got
    first = base.split(".")[0]
    label = "%s.%s" % (base, attr)
    dotted, hop, aliased = module_of(tree, root_path, base, first)
    if dotted and "." in base:
        dotted = "%s.%s" % (dotted, base.split(".", 1)[1])
    if (shipped.get("state") == STATE_OK
            and str(shipped.get("from_hop") or "").endswith("/function")
            and dotted):
        path = _module_file(root_path, dotted)
        table = {}
        if path is not None:
            try:
                sub = _parse(_read(path))
            except OSError:
                sub = None
            if sub is not None:
                table = function_constants_scoped(sub)
        if attr not in table:
            got["ct_state"] = STATE_REFUSED
            got["ct_value"] = None
            got["ct_reason"] = REFUSED_ATTR_NESTED_CONSTANT % label
            got["state"] = STATE_REFUSED
            got["reason"] = got["ct_reason"]
            got["value"] = None
            got["ct_hop"] = "nested-constant"
            return got
    if shipped.get("state") == STATE_OK:
        return got
    if dotted is None:
        if hop == "with-as-call-target":
            got["ct_state"] = STATE_REFUSED
            got["ct_value"] = None
            got["ct_reason"] = REFUSED_ATTR_CALL_TARGET % label
            got["state"] = STATE_REFUSED
            got["reason"] = got["ct_reason"]
            got["value"] = None
            got["ct_hop"] = hop
        return got
    got["ct_source"] = SOURCE_CALL_TARGET
    got["ct_hop"] = hop
    got["ct_chain"] = ["%s->%s.%s" % (first, dotted, attr)]
    decision, values, sub_hop = module_attribute_scoped(root_path, dotted, attr)
    if sub_hop and sub_hop != "direct":
        got["ct_hop"] = "%s/%s" % (hop, sub_hop)
    if decision == "ok":
        literal = sorted(values)[0]
        got["ct_state"] = STATE_OK
        got["ct_reason"] = None
        got["ct_value"] = literal
        got["state"] = STATE_OK
        got["reason"] = None
        got["value"] = literal
        got["attr_state"] = STATE_OK
        got["attr_value"] = literal
        got["attr_reason"] = None
        return got
    if decision in ("mixed", "function-mixed"):
        got["ct_state"] = STATE_REFUSED
        got["ct_reason"] = (REFUSED_ATTR_FUNCTION_MIXED % label
                            if decision == "function-mixed"
                            else PNDCE.PNDC.PNDB.PNDA.REFUSED_NAME_MIXED % dotted)
        got["ct_value"] = None
        got["state"] = STATE_REFUSED
        got["reason"] = got["ct_reason"]
        got["value"] = None
        return got
    got["ct_state"] = STATE_REFUSED
    got["ct_value"] = None
    if decision == "function-constant":
        word = REFUSED_ATTR_FUNCTION_CONSTANT
    elif hop == "from-relative":
        word = REFUSED_ATTR_RELATIVE
    elif hop == "with-as-call-target":
        word = REFUSED_ATTR_CALL_TARGET
    elif hop == "with-as-call":
        word = REFUSED_ATTR_WITH_AS_CALL
    elif aliased:
        word = REFUSED_ATTR_FROM_ALIAS
    else:
        word = REFUSED_ATTR_FROM_IMPORT
    got["ct_reason"] = word % label
    got["state"] = STATE_REFUSED
    got["reason"] = got["ct_reason"]
    got["value"] = None
    return got


def call_target_report(text, root=None):
    """One row per loop the from-scope reading publishes."""
    shipped = PNDCE.from_scope_report(text, root)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["ct_followed"] = {}
        row["ct_refused"] = {}
        row["ct_chains"] = {}
        row["ct_hops"] = {}
        row["ct_resolved"] = []
        names = set()
        for key in ("followed", "refused", "attr_followed", "attr_refused",
                    "pred_followed", "pred_refused", "not_yet_bound",
                    "ia_followed", "ia_refused", "from_followed",
                    "from_refused", "from_resolved"):
            value = loop.get(key)
            if isinstance(value, dict):
                names |= set(value)
            elif isinstance(value, list):
                names |= set(value)
        for item in loop.get("arms") or []:
            names.add(item["name"])
        scope = loop["scope"]
        if scope not in cache:
            cache[scope] = PNDCE.PNDC.PNDB.predicate_tables(text, scope, root)
        tables = cache[scope]
        for name in sorted(names):
            got = call_target_entry(name, text, scope, loop["line"], tables,
                                    root)
            if got.get("ct_hop"):
                row["ct_hops"][name] = got["ct_hop"]
            if got.get("ct_chain"):
                row["ct_chains"][name] = got["ct_chain"]
            if got.get("ct_source") != SOURCE_CALL_TARGET:
                continue
            if got.get("ct_state") == STATE_OK:
                row["ct_followed"][name] = got["ct_value"]
                row["ct_resolved"].append(name)
            elif got.get("ct_reason"):
                row["ct_refused"][name] = got["ct_reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["ct_scope_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in call_target_report(text, root)["loops"]:
        row["ct_scope_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped from-scope audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise CallTargetError(E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNDCE.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise CallTargetError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_CALL_TARGET_STALE
                         if report.get("verdict") == PNDCE.SEAMS_FROM_SCOPE_STALE
                         else SEAMS_CALL_TARGET_COVERED)
    report["base_tool"] = PNDCE.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except CallTargetError as exc:
        return {"tool": LABEL, "verdict": SEAMS_CALL_TARGET_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_CALL_TARGET_COVERED:
        raise CallTargetError(report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a with-as call on an attribute or a local-returned "
                    "module name as an attribute base, and refuse a constant "
                    "only a nested function binds")
    parser.add_argument("--root", default=BASE,
                        help="directory of probe modules to read")
    parser.add_argument("--module", default=None,
                        help="read one module by name (bounded leg)")
    parser.add_argument("--json", action="store_true", help="machine output")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 5
    if not os.path.isdir(args.root):
        sys.stderr.write("%s: not a directory: %s\n" % (E_NO_ROOT, args.root))
        return 3
    report = reading(args.root, args.module)
    if args.json:
        sys.stdout.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    else:
        sys.stdout.write("%s verdict=%s base=%s probes=%d\n"
                         % (LABEL, report["verdict"],
                            report.get("base_tool", "?"),
                            len(report.get("probes") or [])))
        for name in sorted(report["counts"]):
            sys.stdout.write("  %s=%s\n" % (name, report["counts"][name]))
        for row in report["probes"]:
            if row["verdict"] != COVERED:
                continue
            loops = row.get("ct_scope_loops") or []
            resolved = sum(len(loop["ct_resolved"]) for loop in loops)
            named = sum(len(loop["ct_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s ct_scope_loops=%d ct_resolved=%d ct_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_CALL_TARGET_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())