"""AC-PNDCE1..AC-PNDCE6: the from-import / function-constant / with-as-call face (R2565).

Criteria were pinned in state/queue/tech.md:601 at R2563 BEFORE this code
existed.

What this proves, MEASURED at R2563 with
src/os/limits_import_alias_residual_R2563.py against one private world where
the honest answer is `b`, and RE-MEASURED here before any code was written:
  (1) a module bound by `from pkg import helper` and read as `helper.ATTR`
      reads attr-base-local:helper, because the shipped import table is built
      from plain ast.Import nodes only, so a FROM-imported module is mistaken
      for a local;
  (2) a helper constant declared ONLY inside a function body reads
      attr-plain-import:helper.ATTR, because the module reading walks the
      module body and its control flow but never enters a function body;
  (3) a `with open_module() as m` binding reads attr-with-as:m.ATTR and is
      never resolved even when the call returns a module name, because the
      context must be a plain Name to be treated as a module.

This face asks the shipped import-alias reading FIRST and carries every key it
published, unchanged, on every row, then re-reads only a refusal:
  * a module bound by `from pkg import helper` resolves through `pkg/helper.py`
    (AC-PNDCE1);
  * a module bound by `from pkg import helper as h` resolves through the actual
    module and is never published as a local (AC-PNDCE2);
  * a helper constant declared only inside a function body resolves to its
    literal when that function returns it, and is NAMED when it does not
    (AC-PNDCE3);
  * a `with ... as NAME` binding whose context is a call to a function that
    returns a module name resolves, and a call that returns anything else keeps
    the shipped attr-with-as word (AC-PNDCE4);
  * every answer the shipped import-alias face already gave rides beside this
    face own on every row (AC-PNDCE5).

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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope as PNDC  # noqa: E402

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-from-scope")

E_ARGS = "E_PNDCE_ARGS"
E_NO_ROOT = "E_PNDCE_NO_ROOT"

STATE_OK = PNDC.STATE_OK
STATE_REFUSED = PNDC.STATE_REFUSED

REFUSED_ATTR_FROM_IMPORT = "attr-from-import:%s"
REFUSED_ATTR_FROM_ALIAS = "attr-from-alias:%s"
REFUSED_ATTR_FUNCTION_CONSTANT = "attr-function-constant:%s"
REFUSED_ATTR_FUNCTION_MIXED = "attr-function-mixed:%s"
REFUSED_ATTR_WITH_AS = PNDC.REFUSED_ATTR_WITH_AS
REFUSED_ATTR_WITH_AS_CALL = "attr-with-as-call:%s"

SOURCE_FROM_SCOPE = "from-scope"

COVERED = PNDC.COVERED
MISSING_SEAM = PNDC.MISSING_SEAM
OUT_OF_SCOPE = PNDC.OUT_OF_SCOPE
UNREADABLE = PNDC.UNREADABLE
HISTORICAL = PNDC.HISTORICAL

SEAMS_FROM_SCOPE_COVERED = "SEAMS-FROM-SCOPE-COVERED"
SEAMS_FROM_SCOPE_STALE = "SEAMS-FROM-SCOPE-STALE"

MAX_CHAIN = PNDC.MAX_CHAIN


class FromScopeError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _parse(text):
    return PNDC._parse(text)


def _read(path):
    return PNDC._read(path)


def _str_constant(node):
    return PNDC._str_constant(node)


def _module_file(root, dotted):
    return PNDC._module_file(root, dotted)


def from_import_modules(tree, root):
    """Bound name -> module it names, for FROM-imports that name a module.

    `from pkg import helper` binds helper -> pkg.helper; `from pkg import
    helper as h` binds h -> pkg.helper. An imported NAME whose file is not on
    disk is a constant re-export, not a module, and is left to the shipped
    reading rather than guessed at.
    """
    out = {}
    if tree is None:
        return out
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        if node.level:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            dotted = "%s.%s" % (node.module, alias.name)
            if _module_file(root, dotted) is None:
                continue
            out[alias.asname or alias.name] = dotted
    return out


def function_constants(tree):
    """Name -> (literal values, whether a function returns it).

    Only a function own OWN body is read, and only a str literal assignment in
    it; a function that returns the name is a value the module can publish, one
    that does not is a name declared in a scope nothing can reach.
    """
    out = {}
    if tree is None:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
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
            elif isinstance(item, (ast.If, ast.For, ast.While, ast.Try,
                                   ast.With)):
                for field in ("body", "orelse", "finalbody"):
                    nested = getattr(item, field, None)
                    if not isinstance(nested, list):
                        continue
                    for inner in nested:
                        if isinstance(inner, ast.Assign):
                            for target in inner.targets:
                                if isinstance(target, ast.Name):
                                    assigned.setdefault(
                                        target.id, []).append(inner.value)
                        elif isinstance(inner, ast.Return):
                            if isinstance(inner.value, ast.Name):
                                returned.add(inner.value.id)
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
            listed = out.setdefault(name, (set(), False))
            out[name] = (listed[0] | literals, listed[1] or name in returned)
    return out


def call_returns_module(tree, root):
    """Function name -> module dotted text, when it returns a module name."""
    out = {}
    if tree is None:
        return out
    module_names = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            literal = _str_constant(node.value)
            if literal is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    module_names[target.id] = literal
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for item in ast.walk(node):
            if not isinstance(item, ast.Return) or item.value is None:
                continue
            literal = _str_constant(item.value)
            if literal is None and isinstance(item.value, ast.Name):
                literal = module_names.get(item.value.id)
            if literal is None:
                continue
            if _module_file(root, literal) is None:
                continue
            out.setdefault(node.name, literal)
    return out


def with_as_call_modules(tree, root):
    """`with call() as NAME` bindings that resolve to a module name."""
    out = {}
    if tree is None:
        return out
    callers = call_returns_module(tree, root)
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
            if isinstance(func, ast.Name) and func.id in callers:
                out[var.id] = callers[func.id]
    return out


def module_attribute(root, dotted, attr, depth=0, seen=()):
    """The shipped module attribute reading, extended with function constants."""
    decision, values, hop = PNDC.module_attribute(root, dotted, attr, depth,
                                                 seen)
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
    table = function_constants(tree)
    if attr not in table:
        return decision, values, hop
    literals, returned = table[attr]
    if not returned:
        return ("function-constant", set(), "%s/function" % hop)
    if len(literals) > 1:
        return ("function-mixed", literals, "%s/function" % hop)
    return ("ok", set(literals), "%s/function" % hop)


def from_scope_entry(name, text, scope, line, tables=None, root=None):
    """The shipped import-alias answer, carried, plus this face own re-read."""
    root_path = BASE if root is None else root
    tables_full = (PNDC.PNDB.predicate_tables(text, scope, root_path)
                   if tables is None else tables)
    shipped = PNDC.import_alias_entry(name, text, scope, line, tables_full,
                                     root_path)
    got = dict(shipped)
    for key in sorted(shipped):
        got.setdefault(key, shipped[key])
    got["base_from_state"] = shipped.get("ia_state")
    got["base_from_reason"] = shipped.get("ia_reason")
    got["base_from_value"] = shipped.get("ia_value")
    got["base_from_hop"] = shipped.get("ia_hop")
    got["base_shipped_state"] = shipped.get("state")
    got["base_shipped_reason"] = shipped.get("reason")
    got["from_state"] = shipped.get("ia_state")
    got["from_reason"] = shipped.get("ia_reason")
    got["from_value"] = shipped.get("ia_value")
    got["from_chain"] = list(shipped.get("ia_chain") or [])
    got["from_hop"] = shipped.get("ia_hop")
    got["from_source"] = PNDC.SOURCE_IMPORT_ALIAS
    if shipped.get("ia_state") == STATE_OK:
        return got
    tree = (tables_full or {}).get("predicate_tree")
    if tree is None:
        return got
    picked = PNDC.PNDB._follow(name, tree, scope, line)
    if picked is None:
        return got
    kind, value, extra = picked
    node = value
    if isinstance(node, ast.NamedExpr):
        node = node.value
    if not isinstance(node, ast.Attribute):
        return got
    attr = node.attr
    base = PNDC.PNDB.base_text(node.value)
    if not base:
        return got
    first = base.split(".")[0]
    label = "%s.%s" % (base, attr)
    with_as = with_as_call_modules(tree, root_path)
    from_mods = from_import_modules(tree, root_path)
    imports = PNDC.import_bindings(tree)
    aliases = PNDC.import_aliases(tree)
    aliased = False
    dotted = None
    hop = None
    if first in with_as:
        dotted = with_as[first]
        hop = "with-as-call"
    elif first in from_mods:
        dotted = from_mods[first]
        hop = "from-import"
        aliased = True
    elif first in imports:
        dotted = imports[first]
        hop = "import-alias" if first in aliases else "import"
        aliased = first in aliases
    else:
        return got
    if "." in base:
        rest = base.split(".", 1)[1]
        dotted = "%s.%s" % (dotted, rest)
    got["from_source"] = SOURCE_FROM_SCOPE
    got["from_hop"] = hop
    got["from_chain"] = ["%s->%s.%s" % (first, dotted, attr)
                         if hop == "from-import" else "%s().%s" % (first, attr)]
    decision, values, sub_hop = module_attribute(root_path, dotted, attr)
    if sub_hop and sub_hop != "direct":
        got["from_hop"] = "%s/%s" % (hop, sub_hop)
    if decision == "ok":
        literal = sorted(values)[0]
        got["from_state"] = STATE_OK
        got["from_reason"] = None
        got["from_value"] = literal
        got["state"] = STATE_OK
        got["reason"] = None
        got["value"] = literal
        got["attr_state"] = STATE_OK
        got["attr_value"] = literal
        got["attr_reason"] = None
        return got
    if decision in ("mixed", "function-mixed"):
        got["from_state"] = STATE_REFUSED
        got["from_reason"] = (REFUSED_ATTR_FUNCTION_MIXED % label
                              if decision == "function-mixed"
                              else PNDC.PNDB.PNDA.REFUSED_NAME_MIXED % dotted)
        got["from_value"] = None
        got["state"] = STATE_REFUSED
        got["reason"] = got["from_reason"]
        got["value"] = None
        return got
    got["from_state"] = STATE_REFUSED
    got["from_value"] = None
    if decision == "function-constant":
        word = REFUSED_ATTR_FUNCTION_CONSTANT
    elif hop == "with-as-call":
        word = REFUSED_ATTR_WITH_AS_CALL
    elif aliased:
        word = REFUSED_ATTR_FROM_ALIAS
    else:
        word = REFUSED_ATTR_FROM_IMPORT
    got["from_reason"] = word % label
    got["state"] = STATE_REFUSED
    got["reason"] = got["from_reason"]
    got["value"] = None
    return got


def from_scope_report(text, root=None):
    """One row per loop the import-alias reading publishes."""
    shipped = PNDC.import_alias_report(text, root)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["from_followed"] = {}
        row["from_refused"] = {}
        row["from_chains"] = {}
        row["from_hops"] = {}
        row["from_resolved"] = []
        names = set(loop.get("followed") or {})
        names |= set(loop.get("refused") or {})
        names |= set(loop.get("attr_followed") or {})
        names |= set(loop.get("attr_refused") or {})
        names |= set(loop.get("pred_followed") or {})
        names |= set(loop.get("pred_refused") or {})
        names |= set(loop.get("not_yet_bound") or {})
        names |= set(loop.get("ia_followed") or {})
        names |= set(loop.get("ia_refused") or {})
        for item in loop.get("arms") or []:
            names.add(item["name"])
        scope = loop["scope"]
        if scope not in cache:
            cache[scope] = PNDC.PNDB.predicate_tables(text, scope, root)
        tables = cache[scope]
        for name in sorted(names):
            got = from_scope_entry(name, text, scope, loop["line"], tables,
                                   root)
            if got.get("from_hop"):
                row["from_hops"][name] = got["from_hop"]
            if got.get("from_chain"):
                row["from_chains"][name] = got["from_chain"]
            if got.get("from_source") != SOURCE_FROM_SCOPE:
                continue
            if got.get("from_state") == STATE_OK:
                row["from_followed"][name] = got["from_value"]
                row["from_resolved"].append(name)
            elif got.get("from_reason"):
                row["from_refused"][name] = got["from_reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["from_scope_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in from_scope_report(text, root)["loops"]:
        row["from_scope_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped import-alias audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise FromScopeError(E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNDC.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise FromScopeError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_FROM_SCOPE_STALE
                         if report.get("verdict") == PNDC.SEAMS_IMPORT_ALIAS_STALE
                         else SEAMS_FROM_SCOPE_COVERED)
    report["base_tool"] = PNDC.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except FromScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_FROM_SCOPE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_FROM_SCOPE_COVERED:
        raise FromScopeError(report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a FROM-imported module, a function-level helper "
                    "constant or a with-as call returning a module name as an "
                    "attribute base")
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
            loops = row.get("from_scope_loops") or []
            resolved = sum(len(loop["from_resolved"]) for loop in loops)
            named = sum(len(loop["from_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s from_scope_loops=%d from_resolved=%d "
                "from_named=%d\n" % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_FROM_SCOPE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())