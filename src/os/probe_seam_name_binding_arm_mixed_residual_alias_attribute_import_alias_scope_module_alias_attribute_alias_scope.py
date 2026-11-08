"""A module alias HEAD bound by a plain name alias, a TWO-STEP attribute path,
and a call context on a FROM-imported function name.

The shipped module-alias-attribute face follows an attribute head that is an
import or a from-import, takes exactly ONE attribute hop, and finds a call's
function only inside the current module file. Three shapes it cannot read are
measured in qa/module-alias-alias-scope-limits-R2583.log against private worlds
where the honest answer is `b`, and are closed by extending the SAME reading:

  (a) an attribute head bound by a MODULE ALIAS - `import consts` then
      `M = consts` then `BASE = M.HW` - read attr-module-alias-unbound:M.HW;
  (b) a TWO-STEP attribute path - `BASE = inner.INNER.HW` - read
      attr-module-alias-unbound:inner.HW, because only one hop is taken;
  (c) a with-as CALL context on a FROM-imported function name - `from mk
      import mkmod as REG` then `with REG() as m` - read attr-cross-call:m.ATTR.

The extension is applied THROUGH the shipped reading rather than beside it: the
readers both shipped faces call at run time are swapped for this face own
inside one guarded block and restored in a finally, so every answer the sixteen
shipped faces already gave is carried unchanged on the row.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAM1..AC-PNAM6 were pinned in state/queue/tech.md:615 at R2579
BEFORE this code existed.
"""

import argparse
import ast
import contextlib
import json
import os
import re
import sys
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_scope as MAA  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope as MA  # noqa: E402

CB = MA.CB
CS = MAA.CS
PNDC = MAA.PNDC

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-scope")

E_ARGS = "E_PNAM_ARGS"
E_NO_ROOT = "E_PNAM_NO_ROOT"

STATE_OK = MA.STATE_OK
STATE_REFUSED = MA.STATE_REFUSED

SOURCE_MODULE_ALIAS_ALIAS = "module-alias-attribute-alias"

COVERED = MA.COVERED
MISSING_SEAM = MA.MISSING_SEAM
OUT_OF_SCOPE = MA.OUT_OF_SCOPE
UNREADABLE = MA.UNREADABLE
HISTORICAL = MA.HISTORICAL

SEAMS_MODULE_ALIAS_ALIAS_COVERED = "SEAMS-MODULE-ALIAS-ALIAS-COVERED"
SEAMS_MODULE_ALIAS_ALIAS_STALE = "SEAMS-MODULE-ALIAS-ALIAS-STALE"

REFUSED_IMPORT_NOT_CALLABLE = "attr-import-not-callable:%s"

MAX_STEPS = 8

_parse = CS._parse
_read = CS._read
_str_constant = CS._str_constant
_module_file = CS._module_file
_module_tree = CS._module_tree
leftmost_name = CS.leftmost_name
module_attribute_scoped = MAA.module_attribute_scoped

_not_callable_wrapped = re.compile(
    r"^attr-module-alias-unbound:not-callable:(.+)$")

# The shipped faces as they were BEFORE this face ever patches them.
_BASE_R2579_ALIAS_LITERAL = MAA.module_alias_literal
_BASE_R2579_FUNCTION_RETURNS = MAA.module_function_returns
_BASE_R2579_WITH_AS = MAA.with_as_targets_chain

_SHIPPED_MA_READERS = (MA.module_alias_literal, MA.module_function_returns,
                       MA.with_as_targets_chain)
_SHIPPED_MAA_READERS = (MAA.module_alias_literal, MAA.module_function_returns,
                        MAA.with_as_targets_chain, MAA.module_function_literal,
                        MAA.resolve_expr, MAA._module_of_head)

_LOCK = threading.Lock()


class ModuleAliasAliasError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _attribute_path(expr):
    """[head, attr, attr, ...] for a dotted attribute expression, or None."""
    attrs = []
    cur = expr
    while isinstance(cur, ast.Attribute):
        attrs.append(cur.attr)
        if len(attrs) > MAX_STEPS:
            return None
        cur = cur.value
    if not isinstance(cur, ast.Name):
        return None
    return [cur.id] + list(reversed(attrs))


def _module_of_head(tree, root, head, seen=None):
    """The dotted module a head names.

    An import, a module FROM-import, or - new here - a module-level NAME alias
    chain that ends at one (`import consts` then `M = consts`), cycle-guarded
    by the names already walked.
    """
    if tree is None or head is None:
        return None
    dotted = CB.module_binding(tree, root, head)
    if dotted:
        return dotted
    dotted = PNDC.import_bindings(tree).get(head)
    if dotted:
        return dotted
    seen = set() if seen is None else seen
    if head in seen or len(seen) >= MAX_STEPS:
        return None
    seen.add(head)
    value = CS.module_value_binding(tree, head)
    if isinstance(value, ast.Name):
        return _module_of_head(tree, root, value.id, seen)
    if _module_file(root, head) is not None:
        return head
    return None


def _head_is_alias(tree, root, head):
    """True when the head reached its module through a plain name alias."""
    if tree is None or head is None:
        return False
    if CB.module_binding(tree, root, head):
        return False
    if PNDC.import_bindings(tree).get(head):
        return False
    return _module_of_head(tree, root, head) is not None


def _class_literal(tree, root, module, head, attr):
    """The module name a class attribute carries, or None."""
    if tree is None:
        return None
    cls = CS._find_class_in(tree, head)
    if cls is not None:
        got = CS.cross_class_table(root, module, [cls.name])
    else:
        imported = CB.from_import_classes(tree, root)
        if head not in imported:
            return None
        got = CS.cross_class_table(root, imported[head][0], [imported[head][1]])
    if not got:
        return None
    literals = got[0].get(attr)
    if not literals or len(literals) > 1:
        return None
    literal = sorted(literals)[0]
    return literal if _module_file(root, literal) else None


def _walk_attribute_path(root, dotted, path, chain, hop_head):
    """Follow every attribute step of a dotted path.

    An intermediate step must name a module on disk so the next step can be
    read through it; a step that names no module is refused BY NAME (the
    source link that broke), and a final step must name a module file.
    """
    steps = path[1:]
    walked = list(chain)
    if hop_head:
        walked.append("%s<-%s" % (path[0], dotted))
    cur = dotted
    for idx, attr in enumerate(steps):
        link = ".".join(path[:idx + 2])
        sub = _module_tree(root, cur)
        if sub is None:
            return None, None, walked + [link], link
        decision, values, _hop = module_attribute_scoped(root, cur, attr)
        if decision == "ok" and values and len(values) == 1:
            literal = sorted(values)[0]
        else:
            value = CS.module_value_binding(sub, attr)
            if value is None:
                return None, None, walked + [link], link
            literal, _h, _c, _broken = resolve_expr(sub, root, cur, value,
                                                    walked + [link])
            if not literal:
                return None, None, walked + [link], link
        walked.append(link)
        last = idx == len(steps) - 1
        if not _module_file(root, literal):
            return None, None, walked, link
        if last:
            hop = ("module-alias-attribute/attribute" if len(steps) == 1
                   else "module-alias-attribute/attribute-path")
            return literal, hop, walked, None
        cur = literal
    return None, None, walked, None


def resolve_expr(tree, root, module, expr, chain):
    """(literal, hop, chain, broken link) for one module-level expression."""
    if expr is None:
        return None, None, chain, None
    if isinstance(expr, ast.Constant):
        literal = _str_constant(expr)
        if literal and _module_file(root, literal):
            return literal, "module-alias-attribute/constant", chain, None
        return None, None, chain, None
    if isinstance(expr, ast.Name):
        dotted = _module_of_head(tree, root, expr.id)
        if dotted:
            return dotted, "module-alias-attribute/module-name", \
                chain + [expr.id], None
        value, deeper, broken = MA.module_level_binding(tree, expr.id)
        if broken:
            return None, None, chain + [broken], broken
        return resolve_expr(tree, root, module, value, chain + list(deeper[1:]))
    if isinstance(expr, ast.Attribute):
        head = leftmost_name(expr)
        if head is None:
            return None, None, chain, None
        label = "%s.%s" % (head, expr.attr)
        if isinstance(expr.value, ast.Name):
            literal = _class_literal(tree, root, module, head, expr.attr)
            if literal:
                return literal, "module-alias-attribute/class-attribute", \
                    chain + [label], None
        path = _attribute_path(expr)
        if path is None:
            return None, None, chain + [label], label
        dotted = _module_of_head(tree, root, head)
        if dotted is None:
            return None, None, chain + [label], label
        return _walk_attribute_path(root, dotted, path, chain,
                                    _head_is_alias(tree, root, head))
    if isinstance(expr, ast.Call):
        literal = CS._call_target_literal(root, module, expr.func, tree)
        if literal:
            return literal, "with-as-module-alias", chain, None
        if isinstance(expr.func, ast.Name):
            literal = module_function_returns(tree, root, module).get(
                expr.func.id)
            if literal:
                return literal, "with-as-module-function", chain, None
        if isinstance(expr.func, ast.Attribute):
            head = leftmost_name(expr.func)
            dotted = _module_of_head(tree, root, head) if head else None
            sub = _module_tree(root, dotted) if dotted else None
            if sub is not None:
                literal = module_function_literal(sub, root, dotted,
                                                  expr.func.attr)
                if literal:
                    return literal, "with-as-call-chain", \
                        chain + ["%s.%s()" % (head, expr.func.attr)], None
        return None, None, chain, None
    return None, None, chain, None


def _from_import_members(tree):
    """bound name -> (source module dotted, original member name).

    Absolute FROM-imports only (level 0). The shipped from-import reader keeps
    a member only when the joined dotted text is itself a module file, so a
    FROM-imported FUNCTION or CONSTANT is invisible to it; that is the shape
    AC-PNAM3 and AC-PNAM4 close.
    """
    out = {}
    if tree is None:
        return out
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level != 0 or not node.module:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            out[alias.asname or alias.name] = (node.module, alias.name)
    return out


def _local_function_literal(tree, root, module, name, seen=None):
    """The module name a module-level FUNCTION of THIS file returns."""
    if tree is None or not name:
        return None
    seen = set() if seen is None else seen
    if name in seen:
        return None
    seen.add(name)
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != name:
            continue
        literals = set()
        for item in ast.walk(node):
            if not isinstance(item, ast.Return) or item.value is None:
                continue
            literal, _hop, _chain, _broken = resolve_expr(
                tree, root, module, item.value, [name])
            if literal:
                literals.add(literal)
        if len(literals) == 1:
            return sorted(literals)[0]
        return None
    value, _chain, broken = MA.module_level_binding(tree, name)
    if value is None and broken and broken not in seen:
        return _local_function_literal(tree, root, module, broken, seen)
    if value is None:
        return None
    if isinstance(value, ast.Name):
        return _local_function_literal(tree, root, module, value.id, seen)
    return None


def module_function_literal(tree, root, module, name, seen=None):
    """The module name a module-level function returns, following a
    FROM-import of the function itself."""
    literal = _local_function_literal(tree, root, module, name, seen)
    if literal:
        return literal
    got, kind = _function_via_from_import(tree, root, name, seen)
    return got if kind == "ok" else None


def _function_via_from_import(tree, root, name, seen=None):
    """(literal, kind) for a name bound by an absolute FROM-import.

    kind is "ok" when the imported member is a function whose own returns name
    a module, "not-callable" when it is imported but is not such a function.
    """
    if tree is None or not name:
        return None, None
    entry = _from_import_members(tree).get(name)
    if entry is None:
        return None, None
    source, original = entry
    sub = _module_tree(root, source)
    if sub is None:
        return None, "not-callable"
    literal = _local_function_literal(sub, root, source, original, seen)
    if literal:
        return literal, "ok"
    return None, "not-callable"


def module_function_returns(tree, root, module):
    """NAME -> module literal for every module-level function of one module."""
    out = dict(_BASE_R2579_FUNCTION_RETURNS(tree, root, module))
    if tree is None:
        return out
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name in out:
            continue
        literal = module_function_literal(tree, root, module, node.name)
        if literal:
            out[node.name] = literal
    for name in _from_import_members(tree):
        if name in out:
            continue
        literal = module_function_literal(tree, root, module, name)
        if literal:
            out[name] = literal
    return out


def module_alias_literal(tree, root, module, name):
    """(literal, hop, chain, broken) extending the chain to attribute finals."""
    value, chain, broken = MA.module_level_binding(tree, name)
    if broken:
        return None, None, chain, broken
    if value is None:
        return None, None, chain, name
    literal, hop, deep, link = resolve_expr(tree, root, module, value, chain)
    if literal:
        return literal, hop, deep, None
    if link:
        return None, None, deep, link
    return None, None, chain, None


def with_as_targets_chain(tree, root, module=None):
    """(table, broken) extending the shipped table to a plain module alias
    head, a two-step attribute path and a FROM-imported call context."""
    out, broken = _BASE_R2579_WITH_AS(tree, root, module)
    if tree is None:
        return out, broken
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            var = item.optional_vars
            if not isinstance(var, ast.Name):
                continue
            if out.get(var.id) and out[var.id][0]:
                continue
            context = item.context_expr
            head = None
            name = None
            is_call = False
            bare = False
            if isinstance(context, ast.Attribute):
                head = leftmost_name(context)
                name = context.attr
            elif isinstance(context, ast.Call) and isinstance(
                    context.func, ast.Attribute):
                head = leftmost_name(context.func)
                name = context.func.attr
                is_call = True
            elif isinstance(context, ast.Call) and isinstance(
                    context.func, ast.Name):
                name = context.func.id
                is_call = True
                bare = True
            else:
                continue
            if bare:
                if not module:
                    continue
                literal, kind = _function_via_from_import(tree, root, name)
                if kind == "ok" and literal:
                    out[var.id] = (literal, "with-as-call-from-import",
                                   ["%s()" % (name,)])
                elif kind == "not-callable":
                    broken.setdefault(var.id,
                                      ("not-callable:%s" % name,
                                       ["%s()" % (name,)]))
                continue
            if head is None:
                continue
            label = "%s.%s%s" % (head, name, "()" if is_call else "")
            dotted = _module_of_head(tree, root, head)
            if dotted is None:
                broken.setdefault(var.id, (label, [label]))
                continue
            sub = _module_tree(root, dotted)
            if sub is None:
                broken.setdefault(var.id, (label, [label]))
                continue
            if is_call:
                literal, kind = _function_via_from_import(sub, root, name)
                if kind == "ok" and literal:
                    out[var.id] = (literal, "with-as-call-from-import", [label])
                    continue
                if kind == "not-callable":
                    broken.setdefault(var.id,
                                      ("not-callable:%s" % name, [label]))
                    continue
                literal = module_function_literal(sub, root, dotted, name)
                if literal:
                    out[var.id] = (literal, "with-as-call-chain", [label])
                continue
            literal, hop, chain, link_broken = module_alias_literal(
                sub, root, dotted, name)
            if literal:
                out[var.id] = (literal, hop, [label] + list(chain))
            elif link_broken:
                broken.setdefault(var.id, (link_broken, [label] + list(chain)))
    return out, broken


@contextlib.contextmanager
def extended_readers():
    """Swap the shipped readers for this face own and restore them."""
    with _LOCK:
        MA.module_alias_literal = module_alias_literal
        MA.module_function_returns = module_function_returns
        MA.with_as_targets_chain = with_as_targets_chain
        MAA.module_alias_literal = module_alias_literal
        MAA.module_function_returns = module_function_returns
        MAA.with_as_targets_chain = with_as_targets_chain
        MAA.resolve_expr = resolve_expr
        MAA._module_of_head = _module_of_head
        try:
            yield
        finally:
            (MA.module_alias_literal, MA.module_function_returns,
             MA.with_as_targets_chain) = _SHIPPED_MA_READERS
            (MAA.module_alias_literal, MAA.module_function_returns,
             MAA.with_as_targets_chain, MAA.module_function_literal,
             MAA.resolve_expr, MAA._module_of_head) = _SHIPPED_MAA_READERS


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The shipped two-level answer, re-read through this face own readers.

    The SHIPPED baseline is measured with the readers unpatched so the row
    really carries what the face it extends answered, not what this face made
    it answer. A FROM-imported name that is not a function is re-worded with
    this face own code so the refusal says WHAT was not callable.
    """
    base = MAA.module_alias_entry(name, text, scope, line, tables, root,
                                 src_path)
    with extended_readers():
        got = MAA.module_alias_entry(name, text, scope, line, tables, root,
                                     src_path)
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out["base_pnam_state"] = (base.get("base_pnma_state")
                              if base.get("base_pnma_state") is not None
                              else base.get("state"))
    out["base_pnam_value"] = (base.get("base_pnma_value")
                              if base.get("base_pnma_value") is not None
                              else base.get("value"))
    out["base_pnam_reason"] = (base.get("base_pnma_reason")
                               or base.get("reason"))
    out["base_pnam_hop"] = base.get("base_pnma_hop") or base.get("ma_hop")
    reason = out.get("reason") or ""
    match = _not_callable_wrapped.match(reason)
    if match:
        out["reason"] = REFUSED_IMPORT_NOT_CALLABLE % match.group(1)
        out["refusal_source"] = "this-face"
    return out


def module_alias_alias_report(text, root=None, src_path=None):
    """One row per loop, read through the extended readers."""
    with extended_readers():
        return MA.module_alias_report(text, root, src_path)


def audit(root=None, module=None):
    """The shipped module-alias audit, re-read through this face own readers."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasAliasError(E_NO_ROOT,
                                    "not a directory: %s" % root_path)
    with extended_readers():
        try:
            report = MA.audit(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasAliasError(code,
                                        str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = MAA.LABEL
    report["verdict"] = (SEAMS_MODULE_ALIAS_ALIAS_STALE
                         if report.get("verdict") == MA.SEAMS_MODULE_ALIAS_STALE
                         else SEAMS_MODULE_ALIAS_ALIAS_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasAliasError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_MODULE_ALIAS_ALIAS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_MODULE_ALIAS_ALIAS_COVERED:
        raise ModuleAliasAliasError(report["verdict"],
                                    "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias head bound by a plain name alias, "
                    "a two-step attribute path, and a call context on a "
                    "FROM-imported function name")
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
            loops = row.get("ma_scope_loops") or []
            resolved = sum(len(loop["ma_resolved"]) for loop in loops)
            named = sum(len(loop["ma_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s ma_scope_loops=%d ma_resolved=%d ma_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_MODULE_ALIAS_ALIAS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())