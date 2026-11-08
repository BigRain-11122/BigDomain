"""A module alias HEAD bound by a WALRUS, and RELATIVE FROM-imports at the
call site and at the module alias head.

The shipped module-alias-attribute-alias face (R2583) follows an attribute head
that is an import, a from-import or a plain/annotated name alias, and it reads
FROM-imported function names only for ABSOLUTE imports (level 0). Four shapes
are measured in qa/module-alias-walrus-relative-limits-R2585.log against
private worlds where the honest answer is `b`, and every one is closed by
extending the SAME reading:

  (a) a module-alias head bound by a WALRUS - `(M := consts)` then
      `BASE = M.HW` - read attr-module-alias-unbound:M.HW;
  (b) a with-as CALL context on a RELATIVE FROM-imported function name - the
      probe's `from . import probe_conf as mk` plus `with mk.REG() as m` - read
      attr-module-alias-unbound:mk.REG();
  (c) a RELATIVE FROM-import of a name that is NOT a function is refused with
      this face own word rather than resolved;
  (d) a RELATIVE FROM-imported MODULE alias head - `from . import consts`
      then `M = consts` - read attr-module-alias-unbound:M.HW.

The extension is applied THROUGH the shipped reading rather than beside it: the
readers the parent faces call at run time are swapped for this face own inside
one guarded block and restored in a finally, so every answer the seventeen
shipped faces already gave is carried unchanged on the row. A level-bearing
import is resolved against the PACKAGE ANCHOR of the module being read; a
synthetic probe text carries no anchor, and then it is resolved only when
exactly ONE module of that name exists under the root - never guessed.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAA1..AC-PNAA6 were pinned in state/queue/tech.md:617 at R2583
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_scope as MAA2  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope as MA  # noqa: E402

MAA = MAA2.MAA
CS = MAA2.CS
CB = MAA2.CB
TL = CB.CB
PNDC = MAA2.PNDC

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "scope")

E_ARGS = "E_PNAW_ARGS"
E_NO_ROOT = "E_PNAW_NO_ROOT"

STATE_OK = MA.STATE_OK
STATE_REFUSED = MA.STATE_REFUSED

SOURCE_MODULE_ALIAS_WALRUS_RELATIVE = "module-alias-attribute-alias-walrus-relative"

COVERED = MA.COVERED
MISSING_SEAM = MA.MISSING_SEAM
OUT_OF_SCOPE = MA.OUT_OF_SCOPE
UNREADABLE = MA.UNREADABLE
HISTORICAL = MA.HISTORICAL

SEAMS_WALRUS_RELATIVE_COVERED = "SEAMS-WALRUS-RELATIVE-COVERED"
SEAMS_WALRUS_RELATIVE_STALE = "SEAMS-WALRUS-RELATIVE-STALE"

REFUSED_RELATIVE_NOT_CALLABLE = "attr-relative-import-not-callable:%s"

MAX_STEPS = 8
_ROOT_INDEX = {}
_ROOT_INDEX_LIMIT = 20000

_parse = CS._parse
_read = CS._read
_str_constant = CS._str_constant
_module_file = CS._module_file
_module_tree = CS._module_tree
leftmost_name = CS.leftmost_name
module_attribute_scoped = MAA.module_attribute_scoped

_relative_not_callable_wrapped = re.compile(
    r"^attr-module-alias-unbound:not-callable-relative:(.+)$")

# The shipped readers as they were BEFORE this face ever patches them.
_BASE_CS_MODULE_VALUE = CS.module_value_binding
_BASE_RELATIVE_FROM_SCAN = TL.relative_from_scan
_BASE_MA_MODULE_LEVEL = MA.module_level_binding
_BASE_MA_ALIAS_LITERAL = MA.module_alias_literal
_BASE_MA_FUNCTION_RETURNS = MA.module_function_returns
_BASE_MA_WITH_AS = MA.with_as_targets_chain

_BASE_MAA2_RESOLVE = MAA2.resolve_expr
_BASE_MAA2_MODULE_OF_HEAD = MAA2._module_of_head
_BASE_MAA2_ALIAS_LITERAL = MAA2.module_alias_literal
_BASE_MAA2_FUNCTION_RETURNS = MAA2.module_function_returns
_BASE_MAA2_WITH_AS = MAA2.with_as_targets_chain
_BASE_MAA2_FUNCTION_LITERAL = MAA2.module_function_literal
_BASE_MAA2_LOCAL_FUNCTION = MAA2._local_function_literal
_BASE_MAA2_ENTRY = MAA2.module_alias_entry
_BASE_MAA2_REPORT = MAA2.module_alias_alias_report

_SHIPPED_MA_READERS = (MA.module_alias_literal, MA.module_function_returns,
                       MA.with_as_targets_chain, MA.module_level_binding)
_SHIPPED_MAA_READERS = (MAA.module_alias_literal, MAA.module_function_returns,
                        MAA.with_as_targets_chain, MAA.module_function_literal,
                        MAA.resolve_expr, MAA._module_of_head)
_SHIPPED_MAA2_READERS = (MAA2.module_alias_literal,
                         MAA2.module_function_returns,
                         MAA2.with_as_targets_chain,
                         MAA2.module_function_literal, MAA2.resolve_expr,
                         MAA2._module_of_head)

_LOCK = threading.Lock()


class ModuleAliasWalrusRelativeError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _parts_of(module):
    """The package parts of a module dotted path (its own name dropped)."""
    if not module:
        return []
    return module.split(".")[:-1]


def _dotted_from_path(root, path):
    rel = os.path.relpath(path, root).replace("\\", "/")
    parts = rel.split("/")
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join([part for part in parts if part])


def _root_index(root):
    """stem -> set of dotted modules under `root`, built once per root."""
    if root in _ROOT_INDEX:
        return _ROOT_INDEX[root]
    index = {}
    if os.path.isdir(root):
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            for name in filenames:
                if name.endswith(".py") and name != "__init__.py":
                    stem = name[:-3]
                elif name == "__init__.py":
                    stem = os.path.basename(dirpath)
                else:
                    continue
                index.setdefault(stem, set()).add(
                    _dotted_from_path(root, os.path.join(dirpath, name)))
            if len(index) > _ROOT_INDEX_LIMIT:
                break
    _ROOT_INDEX[root] = index
    return index


def _unique_module_named(root, stem):
    """The ONE dotted module whose last segment is `stem`, else None.

    A synthetic probe text carries no package anchor, so a level-bearing import
    is resolved only when the name is unambiguous under the root; two
    candidates read None rather than a guess.
    """
    if not stem:
        return None
    hits = _root_index(root).get(stem) or set()
    if len(hits) != 1:
        return None
    dotted = sorted(hits)[0]
    if _module_file(root, dotted) is None:
        return None
    return dotted


def _walrus_value(tree, name):
    """The module-level expression bound to `name` by a WALRUS, or None."""
    if tree is None:
        return None
    for node in tree.body:
        expr = None
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.NamedExpr):
            expr = node.value
        elif isinstance(node, ast.Assign) and isinstance(node.value,
                                                         ast.NamedExpr):
            expr = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value,
                                                            ast.NamedExpr):
            expr = node.value
        if expr is None:
            continue
        if isinstance(expr.target, ast.Name) and expr.target.id == name:
            return expr.value
    return None


def module_value_binding(tree, name):
    """The shipped module-level expression, extended to a WALRUS binding."""
    value = _BASE_CS_MODULE_VALUE(tree, name)
    if value is not None:
        return value
    return _walrus_value(tree, name)


def module_level_binding(tree, name, seen=None):
    """The shipped alias chain, extended to a WALRUS link."""
    value, chain, broken = _BASE_MA_MODULE_LEVEL(tree, name)
    if value is not None or broken is None:
        return value, chain, broken
    seen = set() if seen is None else seen
    if broken in seen:
        return value, chain, broken
    seen.add(broken)
    walrus = _walrus_value(tree, broken)
    if walrus is None:
        return value, chain, broken
    if isinstance(walrus, ast.Name):
        got, deep, deeper_broken = module_level_binding(tree, walrus.id, seen)
        return got, list(chain) + list(deep[1:]), deeper_broken
    return walrus, list(chain) + ["%s:=%s" % (broken, broken)], None


def _relative_module_for(tree, root, head, module):
    """The dotted module a LEVEL-BEARING import of `head` names, or None.

    The package anchor is the dotted path of the module being read; a synthetic
    probe text has none and falls back to a UNIQUE module of that name.
    """
    if tree is None or not head:
        return None
    parts = _parts_of(module)
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level < 1:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            if (alias.asname or alias.name) != head:
                continue
            strip = node.level - 1
            if parts:
                if strip > len(parts):
                    continue
                prefix = parts[:len(parts) - strip] if strip else list(parts)
                segs = list(prefix)
                segs.append(node.module if node.module else alias.name)
                dotted = ".".join([seg for seg in segs if seg])
                if _module_file(root, dotted) is not None:
                    return dotted
                continue
            stem = (node.module if node.module else alias.name).split(".")[-1]
            found = _unique_module_named(root, stem)
            if found and _module_file(root, found) is not None:
                return found
    return None


def relative_from_scan(tree, root, parts):
    """The shipped level-bearing scan, extended to an UNANCHORED probe text.

    With package parts known the shipped answer is kept byte for byte; without
    them a binding is added only when the named module is unambiguous.
    """
    mods, names = _BASE_RELATIVE_FROM_SCAN(tree, root, parts)
    if parts or tree is None:
        return mods, names
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level < 1:
            continue
        strip = node.level - 1
        for alias in node.names:
            if alias.name == "*":
                continue
            bound = alias.asname or alias.name
            if bound in mods:
                continue
            if strip:
                continue
            stem = (node.module if node.module else alias.name).split(".")[-1]
            found = _unique_module_named(root, stem)
            if found and _module_file(root, found) is not None:
                mods[bound] = (found, node.level)
    return mods, names


def _module_of_head(tree, root, head, module=None, seen=None):
    """The dotted module a head names, now including a level-bearing import."""
    if tree is None or head is None:
        return None
    dotted = CB.module_binding(tree, root, head)
    if dotted:
        return dotted
    dotted = PNDC.import_bindings(tree).get(head)
    if dotted:
        return dotted
    dotted = _relative_module_for(tree, root, head, module)
    if dotted:
        return dotted
    seen = set() if seen is None else seen
    if head in seen or len(seen) >= MAX_STEPS:
        return None
    seen.add(head)
    value = module_value_binding(tree, head)
    if isinstance(value, ast.Name):
        return _module_of_head(tree, root, value.id, module, seen)
    if _module_file(root, head) is not None:
        return head
    return None


def _head_is_alias(tree, root, head, module=None):
    """True when the head reached its module through an alias or a walrus."""
    if tree is None or head is None:
        return False
    if CB.module_binding(tree, root, head):
        return False
    if PNDC.import_bindings(tree).get(head):
        return False
    return _module_of_head(tree, root, head, module) is not None


def _attribute_path(expr):
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


def _class_literal(tree, root, module, head, attr):
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
                value = _walrus_value(sub, attr)
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
        dotted = _module_of_head(tree, root, expr.id, module)
        if dotted:
            return dotted, "module-alias-attribute/module-name", \
                chain + [expr.id], None
        value, deeper, broken = module_level_binding(tree, expr.id)
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
        dotted = _module_of_head(tree, root, head, module)
        if dotted is None:
            return None, None, chain + [label], label
        return _walk_attribute_path(root, dotted, path, chain,
                                    _head_is_alias(tree, root, head, module))
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
            dotted = (_module_of_head(tree, root, head, module)
                      if head else None)
            sub = _module_tree(root, dotted) if dotted else None
            if sub is not None:
                literal = module_function_literal(sub, root, dotted,
                                                  expr.func.attr)
                if literal:
                    return literal, "with-as-call-chain", \
                        chain + ["%s.%s()" % (head, expr.func.attr)], None
        return None, None, chain, None
    return None, None, chain, None


def _from_import_members_ctx(tree, root, module):
    """bound name -> (source module dotted, original member, is_relative).

    Both absolute (level 0) and level-bearing imports are read; a relative one
    is resolved against the package anchor of `module` and never guessed.
    """
    out = {}
    if tree is None:
        return out
    parts = _parts_of(module)
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            bound = alias.asname or alias.name
            if node.level == 0:
                if not node.module:
                    continue
                out[bound] = (node.module, alias.name, False)
                continue
            source = _relative_source(root, node, alias, parts)
            if source:
                out[bound] = (source, alias.name, True)
    return out


def _relative_source(root, node, alias, parts):
    strip = node.level - 1
    if parts:
        if strip > len(parts):
            return None
        prefix = parts[:len(parts) - strip] if strip else list(parts)
        segs = list(prefix)
        segs.append(node.module if node.module else alias.name)
        dotted = ".".join([seg for seg in segs if seg])
        return dotted if _module_file(root, dotted) is not None else None
    stem = (node.module if node.module else alias.name).split(".")[-1]
    found = _unique_module_named(root, stem)
    if found and _module_file(root, found) is not None:
        return found
    return None


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
    value, _chain, broken = module_level_binding(tree, name)
    if value is None and broken and broken not in seen:
        return _local_function_literal(tree, root, module, broken, seen)
    if value is None:
        return None
    if isinstance(value, ast.Name):
        return _local_function_literal(tree, root, module, value.id, seen)
    return None


def _function_via_from_import(tree, root, name, module=None, seen=None):
    """(literal, kind) for a name bound by a FROM-import, relative or not.

    kind is "ok" when the imported member is a function whose own returns name
    a module, "not-callable" when an ABSOLUTE import is not such a function and
    "not-callable-relative" when a LEVEL-BEARING one is not.
    """
    if tree is None or not name:
        return None, None
    entry = _from_import_members_ctx(tree, root, module).get(name)
    if entry is None:
        return None, None
    source, original, relative = entry
    refused = "not-callable-relative" if relative else "not-callable"
    sub = _module_tree(root, source)
    if sub is None:
        return None, refused
    literal = _local_function_literal(sub, root, source, original, seen)
    if literal:
        return literal, "ok"
    return None, refused


def module_function_literal(tree, root, module, name, seen=None):
    """The module name a module-level function returns, following a
    FROM-import of the function itself, absolute or relative."""
    literal = _local_function_literal(tree, root, module, name, seen)
    if literal:
        return literal
    got, kind = _function_via_from_import(tree, root, name, module, seen)
    return got if kind == "ok" else None


def module_function_returns(tree, root, module):
    """NAME -> module literal for every module-level function of one module."""
    out = dict(_BASE_MAA2_FUNCTION_RETURNS(tree, root, module))
    if tree is None:
        return out
    for name in _from_import_members_ctx(tree, root, module):
        if name in out:
            continue
        literal = module_function_literal(tree, root, module, name)
        if literal:
            out[name] = literal
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
    """The shipped alias reading, carried here so every parent answer rides."""
    return _BASE_MAA2_ALIAS_LITERAL(tree, root, module, name)


def with_as_targets_chain(tree, root, module=None):
    """(table, broken) extending the shipped table to a level-bearing import."""
    out, broken = _BASE_MAA2_WITH_AS(tree, root, module)
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
                literal, kind = _function_via_from_import(tree, root, name,
                                                          module)
                if kind == "ok" and literal:
                    out[var.id] = (literal, "with-as-call-from-import",
                                   ["%s()" % (name,)])
                elif kind == "not-callable-relative":
                    broken.setdefault(
                        var.id, ("not-callable-relative:%s" % name,
                                 ["%s()" % (name,)]))
                continue
            if head is None:
                continue
            label = "%s.%s%s" % (head, name, "()" if is_call else "")
            dotted = _module_of_head(tree, root, head, module)
            if dotted is None:
                broken.setdefault(var.id, (label, [label]))
                continue
            sub = _module_tree(root, dotted)
            if sub is None:
                broken.setdefault(var.id, (label, [label]))
                continue
            if is_call:
                literal, kind = _function_via_from_import(sub, root, name,
                                                          dotted)
                if kind == "ok" and literal:
                    out[var.id] = (literal, "with-as-call-from-import", [label])
                    broken.pop(var.id, None)
                    continue
                if kind == "not-callable-relative":
                    broken.setdefault(
                        var.id, ("not-callable-relative:%s" % name, [label]))
                    continue
                literal = module_function_literal(sub, root, dotted, name)
                if literal:
                    out[var.id] = (literal, "with-as-call-chain", [label])
                    broken.pop(var.id, None)
                continue
            literal, hop, chain, link_broken = module_alias_literal(
                sub, root, dotted, name)
            if literal:
                out[var.id] = (literal, hop, [label] + list(chain))
                broken.pop(var.id, None)
            elif link_broken:
                broken.setdefault(var.id, (link_broken, [label] + list(chain)))
    return out, broken


@contextlib.contextmanager
def extended_readers():
    """Swap the shipped readers for this face own and restore them."""
    with _LOCK:
        CS.module_value_binding = module_value_binding
        TL.relative_from_scan = relative_from_scan
        MA.module_level_binding = module_level_binding
        MA.module_alias_literal = module_alias_literal
        MA.module_function_returns = module_function_returns
        MA.with_as_targets_chain = with_as_targets_chain
        MAA.module_alias_literal = module_alias_literal
        MAA.module_function_returns = module_function_returns
        MAA.with_as_targets_chain = with_as_targets_chain
        MAA.module_function_literal = module_function_literal
        MAA.resolve_expr = resolve_expr
        MAA._module_of_head = _module_of_head
        MAA2.module_alias_literal = module_alias_literal
        MAA2.module_function_returns = module_function_returns
        MAA2.with_as_targets_chain = with_as_targets_chain
        MAA2.module_function_literal = module_function_literal
        MAA2.resolve_expr = resolve_expr
        MAA2._module_of_head = _module_of_head
        try:
            yield
        finally:
            (CS.module_value_binding, TL.relative_from_scan) = (
                _BASE_CS_MODULE_VALUE, _BASE_RELATIVE_FROM_SCAN)
            (MA.module_alias_literal, MA.module_function_returns,
             MA.with_as_targets_chain,
             MA.module_level_binding) = _SHIPPED_MA_READERS
            (MAA.module_alias_literal, MAA.module_function_returns,
             MAA.with_as_targets_chain, MAA.module_function_literal,
             MAA.resolve_expr, MAA._module_of_head) = _SHIPPED_MAA_READERS
            (MAA2.module_alias_literal, MAA2.module_function_returns,
             MAA2.with_as_targets_chain, MAA2.module_function_literal,
             MAA2.resolve_expr, MAA2._module_of_head) = _SHIPPED_MAA2_READERS


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The shipped two-level answer, re-read through this face own readers."""
    base = _BASE_MAA2_ENTRY(name, text, scope, line, tables, root, src_path)
    with extended_readers():
        got = _BASE_MAA2_ENTRY(name, text, scope, line, tables, root,
                               src_path)
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out["base_pnaa_state"] = base.get("state")
    out["base_pnaa_value"] = base.get("value")
    out["base_pnaa_reason"] = base.get("reason")
    out["base_pnaa_hop"] = base.get("pnam_hop") or base.get("ma_hop")
    reason = out.get("reason") or ""
    match = _relative_not_callable_wrapped.match(reason)
    if match:
        out["reason"] = REFUSED_RELATIVE_NOT_CALLABLE % match.group(1)
        out["refusal_source"] = "this-face"
    return out


def module_alias_report(text, root=None, src_path=None):
    """One row per loop, read through the extended readers."""
    with extended_readers():
        return _BASE_MAA2_REPORT(text, root, src_path)


def audit(root=None, module=None):
    """The shipped module-alias audit, re-read through this face own readers."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasWalrusRelativeError(E_NO_ROOT,
                                             "not a directory: %s" % root_path)
    with extended_readers():
        try:
            report = MA.audit(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasWalrusRelativeError(
                code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = MAA2.LABEL
    report["verdict"] = (SEAMS_WALRUS_RELATIVE_STALE
                         if report.get("verdict") == MA.SEAMS_MODULE_ALIAS_STALE
                         else SEAMS_WALRUS_RELATIVE_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasWalrusRelativeError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_WALRUS_RELATIVE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_WALRUS_RELATIVE_COVERED:
        raise ModuleAliasWalrusRelativeError(report["verdict"],
                                             "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias head bound by a walrus and a "
                    "level-bearing FROM-import at the call site or at the "
                    "alias head")
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
    return 0 if report["verdict"] == SEAMS_WALRUS_RELATIVE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())