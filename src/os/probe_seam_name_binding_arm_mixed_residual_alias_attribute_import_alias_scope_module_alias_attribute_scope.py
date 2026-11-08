"""A module alias chain whose FINAL link is an attribute, a module-level
function returning a NAME bound to a class attribute, and a call context on an
alias chain name.

The shipped module-alias-chain face follows an alias chain to a CALL and a
module-level function whose return is a DIRECT class attribute. Three shapes it
cannot read are measured here against private worlds where the honest answer is
`b` and are closed by extending the SAME reading:

  (1) the final link is an ATTRIBUTE naming a module - `BASE = consts.HW` then
      `REG = BASE` - because only a Call final is followed;
  (2) a module-level function returns a NAME bound to a class attribute -
      `REG2 = Box.NAME` then `def make(): return REG2` - because only a direct
      `Class.ATTR` return is read;
  (3) a with-as context that is a CALL on an alias chain name -
      `with mk.REG() as m` - because the extension covers the context-ATTRIBUTE
      branch only.

The extension is applied THROUGH the shipped reading rather than beside it: the
three readers the shipped face calls at run time are swapped for this face own
inside one guarded block and restored in a finally, so every answer the fifteen
shipped faces already gave is carried unchanged on the row.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNMA1..AC-PNMA6 were pinned in state/queue/tech.md:613 at R2577
BEFORE this code existed.
"""

import argparse
import contextlib
import json
import os
import sys
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope as MA  # noqa: E402

import ast  # noqa: E402

CB = MA.CB
CT = MA.CT
TL = MA.TL
PNDC = MA.PNDC
CS = MA.CS

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-scope")

E_ARGS = "E_PNMA_ARGS"
E_NO_ROOT = "E_PNMA_NO_ROOT"

STATE_OK = MA.STATE_OK
STATE_REFUSED = MA.STATE_REFUSED

SOURCE_MODULE_ALIAS_ATTRIBUTE = "module-alias-attribute"

REFUSED_ATTR_MODULE_ALIAS_UNBOUND = MA.REFUSED_ATTR_MODULE_ALIAS_UNBOUND

COVERED = MA.COVERED
MISSING_SEAM = MA.MISSING_SEAM
OUT_OF_SCOPE = MA.OUT_OF_SCOPE
UNREADABLE = MA.UNREADABLE
HISTORICAL = MA.HISTORICAL

SEAMS_MODULE_ALIAS_ATTRIBUTE_COVERED = "SEAMS-MODULE-ALIAS-ATTRIBUTE-COVERED"
SEAMS_MODULE_ALIAS_ATTRIBUTE_STALE = "SEAMS-MODULE-ALIAS-ATTRIBUTE-STALE"

_parse = CS._parse
_read = CS._read
_str_constant = CS._str_constant
_module_file = CS._module_file
_module_tree = CS._module_tree
leftmost_name = CS.leftmost_name
module_dotted = MA.module_dotted
module_attribute_scoped = MA.module_attribute_scoped

# The shipped readers as they were BEFORE this face ever patches them.
_BASE_ALIAS_LITERAL = MA.module_alias_literal
_BASE_FUNCTION_RETURNS = MA.module_function_returns
_BASE_WITH_AS = MA.with_as_targets_chain

_LOCK = threading.Lock()


class ModuleAliasAttributeError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _module_of_head(tree, root, head):
    """The dotted module a head names, through an import or a from-import."""
    if tree is None or head is None:
        return None
    dotted = CB.module_binding(tree, root, head)
    if dotted:
        return dotted
    return PNDC.import_bindings(tree).get(head)


def _class_literal(tree, root, module, head, attr):
    """The module name a same-module class attribute carries, or None."""
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


def resolve_expr(tree, root, module, expr, chain):
    """(literal, hop, chain, broken link) for one module-level expression.

    A string constant naming a module resolves; an attribute naming a module
    through an import, a same-module class or another module resolves; a call
    resolves through the shipped call-target reading and this face own function
    table; a link that cannot be taken is returned by name instead of dropped.
    """
    if expr is None:
        return None, None, chain, None
    if isinstance(expr, ast.Constant):
        literal = _str_constant(expr)
        if literal and _module_file(root, literal):
            return literal, "module-alias-attribute/constant", chain, None
        return None, None, chain, None
    if isinstance(expr, ast.Name):
        value, deeper, broken = MA.module_level_binding(tree, expr.id)
        if broken:
            return None, None, chain + [broken], broken
        return resolve_expr(tree, root, module, value, chain + list(deeper[1:]))
    if isinstance(expr, ast.Attribute):
        head = leftmost_name(expr)
        if head is None:
            return None, None, chain, None
        label = "%s.%s" % (head, expr.attr)
        literal = _class_literal(tree, root, module, head, expr.attr)
        if literal:
            return literal, "module-alias-attribute/class-attribute", \
                chain + [label], None
        dotted = _module_of_head(tree, root, head)
        if dotted is None:
            return None, None, chain + [label], label
        sub = _module_tree(root, dotted)
        if sub is None:
            return None, None, chain + [label], label
        decision, values, _hop = module_attribute_scoped(root, dotted,
                                                         expr.attr)
        if decision == "ok" and values:
            if len(values) == 1:
                literal = sorted(values)[0]
                if _module_file(root, literal):
                    return literal, "module-alias-attribute/attribute", \
                        chain + [label], None
            return None, None, chain + [label], None
        return None, None, chain + [label], label
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


def module_function_literal(tree, root, module, name, seen=None):
    """The module name a module-level FUNCTION returns, following an alias."""
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
        # The chain ends at a NAME that is not an assignment: a module-level
        # function is exactly that shape, so keep reading instead of stopping.
        return module_function_literal(tree, root, module, broken, seen)
    if value is None:
        return None
    if isinstance(value, ast.Name):
        return module_function_literal(tree, root, module, value.id, seen)
    return None


def module_function_returns(tree, root, module):
    """NAME -> module literal for every module-level function of one module."""
    out = dict(_BASE_FUNCTION_RETURNS(tree, root, module))
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
    """(table, broken) extending the shipped table to attribute finals and a
    call context on an alias chain name. Values are (literal, hop, chain)."""
    out, broken = _BASE_WITH_AS(tree, root, module)
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
            name = None
            is_call = False
            dotted = None
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
                if module:
                    literal = module_function_literal(tree, root, module,
                                                      context.func.id)
                    if literal:
                        out[var.id] = (literal, "with-as-call-chain",
                                       ["%s()" % (context.func.id,)])
                continue
            else:
                continue
            if head is None:
                continue
            label = "%s.%s%s" % (head, name, "()" if is_call else "")
            if dotted is None:
                dotted = _module_of_head(tree, root, head)
            if dotted is None:
                broken.setdefault(var.id, (label, [label]))
                continue
            sub = _module_tree(root, dotted)
            if sub is None:
                broken.setdefault(var.id, (label, [label]))
                continue
            if is_call:
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
        saved = (MA.module_alias_literal, MA.module_function_returns,
                 MA.with_as_targets_chain)
        MA.module_alias_literal = module_alias_literal
        MA.module_function_returns = module_function_returns
        MA.with_as_targets_chain = with_as_targets_chain
        try:
            yield
        finally:
            (MA.module_alias_literal, MA.module_function_returns,
             MA.with_as_targets_chain) = saved


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The shipped module-alias answer, re-read through this face own readers.

    The SHIPPED baseline is measured with the readers unpatched so the row
    really carries what the face it extends answered, not what this face made
    it answer.
    """
    base = MA.module_alias_entry(name, text, scope, line, tables, root,
                                src_path)
    with extended_readers():
        got = MA.module_alias_entry(name, text, scope, line, tables, root,
                                    src_path)
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out["base_pnma_state"] = (base.get("ma_state")
                              if base.get("ma_state") is not None
                              else base.get("state"))
    out["base_pnma_value"] = (base.get("ma_value")
                              if base.get("ma_value") is not None
                              else base.get("value"))
    out["base_pnma_reason"] = (base.get("ma_reason")
                               or base.get("reason"))
    out["base_pnma_hop"] = base.get("ma_hop") or base.get("cs_hop")
    return out


def module_alias_attribute_report(text, root=None, src_path=None):
    """One row per loop, read through the extended readers."""
    with extended_readers():
        return MA.module_alias_report(text, root, src_path)


def audit(root=None, module=None):
    """The shipped module-alias audit, re-read through this face own readers."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasAttributeError(E_NO_ROOT,
                                        "not a directory: %s" % root_path)
    with extended_readers():
        try:
            report = MA.audit(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasAttributeError(code,
                                            str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = MA.LABEL
    report["verdict"] = (SEAMS_MODULE_ALIAS_ATTRIBUTE_STALE
                         if report.get("verdict") == MA.SEAMS_MODULE_ALIAS_STALE
                         else SEAMS_MODULE_ALIAS_ATTRIBUTE_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasAttributeError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_MODULE_ALIAS_ATTRIBUTE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_MODULE_ALIAS_ATTRIBUTE_COVERED:
        raise ModuleAliasAttributeError(report["verdict"],
                                        "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias chain whose final link is an "
                    "attribute, a module-level function returning a name "
                    "bound to a class attribute, and a call context on an "
                    "alias chain name")
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
    return 0 if report["verdict"] == SEAMS_MODULE_ALIAS_ATTRIBUTE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())