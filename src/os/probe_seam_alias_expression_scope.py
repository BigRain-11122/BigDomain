"""probe_seam_alias_expression_scope - read the alias shapes that read empty.

MEASURED at R2527 on the shipped annotated-constant face own readers, in that
window own legs:

  BASE_NAME = "x"
  for name in (BASE_NAME,):      -> local_bindings {} and NO shape named, so a
                                    loop over a NAMED constant still reads
                                    silent
  ALIAS: str = pkg.NAMES[0]      -> module_bindings {} with no shape named, so
                                    an alias whose value is a subscript or an
                                    attribute chain is invisible
  ALIASES = (BASE,)              -> BASE is kept but no alias entry is
                                    published for the container element

This face reads those three expressions with ONE reading and no second
classifier:

  module_bindings(text, root) / local_bindings(text, root)
      the SHIPPED tables (annotated face, which extends the local-constant
      face), EXTENDED - not replaced. Every earlier answer stands; this face
      adds only names that resolve through a for-loop over a named constant,
      an annotated alias whose value is a subscript or attribute chain, and a
      container alias whose elements are names. Values are substituted
      recursively, at most MAX_DEPTH deep, and a name bound twice with
      different trees is dropped as ambiguous (the shipped law).
  alias_report(text, root)
      what this reading FOLLOWED (name -> the chain it took) and what it
      REFUSED (name -> a short ASCII reason). A refused shape is published,
      never silently absent, and nothing is ever evaluated.
  resolve_expression(expr_text, text, root, imports, memo)
      the shipped resolution law is asked FIRST with the extended tables, so
      a plain name, a tuple element, a dict value and one attribute hop keep
      exactly the shipped answer. Then the same law is re-asked with the
      extended tables and the shipped chain hop, so an alias element resolves
      with the label that produced it.
  dynamic_imports(text, root)
      the shipped dynamic face answers the shapes (its detection is the ONE
      shape classifier). Each call it could not resolve is offered to the
      extended reading; a resolvable one moves to RESOLVED carrying the
      binding label, the rest stay UNRESOLVED and are named.
  helper_scope / probe_scope / audit / guard
      the same cycle-guarded same-root walk the shipped faces use, with the
      extended stems feeding it, and the shipped registry `quiets` as the ONE
      seam classifier. Each probe row carries the alias chains it followed
      and the alias shapes it refused.

Read-only: nothing is written, no file is opened for writing, and every
digest this reading touches is unchanged across a full audit (AC-PCAE5). No
probe and no helper is ever imported or run, which is why a stale probe is
NAMED rather than paid for.

Criteria AC-PCAE1..AC-PCAE6 were pinned in state/queue/tech.md:565 at R2527 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: nothing is evaluated, so a call, a join, an
f-string, a comprehension or a name built from a variable is refused and named
rather than resolved. Only literally constant values are followed (str, tuple,
list, dict of constants) with names substituted through the shipped tables.
An annotated alias counts only when its annotation is a plain name and its
value reaches a constant by at most one attribute hop on a module file in the
SAME root. Deeper chains, a container returned by a call and a container
imported from another package are NOT resolved. The walk follows local modules
in the same root only, at most MAX_HOPS links with a cycle guard. These shapes
can UNDER-report a stale probe but can never invent one. The walk shape is
written here rather than injected into the shipped annotated face, because
parameterising a shipped module would owe a battery in the same window; the
tables and the resolution law are the shipped ones EXTENDED at call time, and
the seam CLASSIFIER is still the shipped registry single `quiets`.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-ALIAS-COVERED)
  exit 2 = a probe is MISSING-SEAM or a source will not parse
  exit 3 = the root is missing or unreadable
  exit 5 = bad arguments
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys

LABEL = "os-probe-seam-alias-expression-scope"
E_ARGS = "E_PCAE_ARGS"
E_NO_ROOT = "E_PCAE_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-ALIAS-COVERED"
SEAMS_STALE = "SEAMS-ALIAS-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)
STEM_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")

TREE_STR = "str"
TREE_TUPLE = "tuple"
TREE_DICT = "dict"

MAX_HOPS = 8
MAX_DEPTH = 4
BINDING_PASSES = 8

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

REFUSED_AMBIGUOUS = "ambiguous"
REFUSED_CALL = "call"
REFUSED_FORMAT = "format"
REFUSED_EXPRESSION = "expression"
REFUSED_COMPREHENSION = "comprehension"
REFUSED_SHAPE = "shape"
REFUSED_DEPTH = "depth"
REFUSED_DICT_KEY = "dict-key"
REFUSED_SLICE = "subscript"
REFUSED_ATTR = "attribute"
REFUSED_NAME = "unresolved-name"
REFUSED_NESTED = "nested"


class AliasScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _annotated_reader():
    """The shipped annotated-constant face, imported once (tables and law)."""
    import probe_seam_annotated_constant_scope
    return probe_seam_annotated_constant_scope


def _local_reader():
    """The shipped local-constant face (honest constant entry law)."""
    return _annotated_reader()._base_reader()


def _registry():
    """The shipped seam reader, imported once (one classifier, no copy)."""
    import probe_seam_registry
    return probe_seam_registry


def _dynamic_reader():
    """The shipped dynamic shape reader (one shape classifier, no copy)."""
    import probe_seam_dynamic_import_scope
    return probe_seam_dynamic_import_scope


def _static_reader():
    """The shipped static/lazy stem reader (one reader, no copy)."""
    import probe_seam_lazy_scope
    return probe_seam_lazy_scope


def render_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    if SANDBOX not in sys.path:
        sys.path.insert(0, SANDBOX)
    import suite_matrix
    return suite_matrix


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    module = render_module() if module is None else module
    return _registry().seam_names(module)


def seam_owners(module=None):
    """Which module owns each seam, read off the seam object, never guessed."""
    module = render_module() if module is None else module
    registry = _registry()
    return dict((name, registry.seam_owner(name, module))
                for name in seam_names(module))


def _parse(text):
    return _annotated_reader()._parse(text)


def _parse_expr(text):
    return _annotated_reader()._parse_expr(text)


def _str_constant(node):
    return _annotated_reader()._str_constant(node)


def _iter_nodes(node, skip_functions):
    return _annotated_reader()._iter_nodes(node, skip_functions)


def _tree_element(tree, index_node, module_table, local_table):
    return _annotated_reader()._tree_element(tree, index_node,
                                             module_table, local_table)


def _chain_resolve(node, module_table, local_table, root, imports, memo):
    return _annotated_reader()._chain_resolve(node, module_table, local_table,
                                              root, imports, memo)


def _slice_label(slice_node):
    """A short ASCII label for a subscription index, or None."""
    value = _str_constant(slice_node)
    if value is not None:
        return repr(value)
    if isinstance(slice_node, ast.Constant):
        number = slice_node.value
        if isinstance(number, (int, float)) and not isinstance(number, bool):
            return str(number)
    return "..."


def _tree_of(node, module_table, local_table, root, imports, memo,
             depth=0):
    """(tree, provenance) for a value node this reading may follow.

    Returns (None, reason) when the shape is refused. Nothing is evaluated:
    a call, a join, an f-string, a comprehension and an arithmetic expression
    all read None with their own reason, so the caller can NAME them.
    """
    if node is None:
        return None, REFUSED_SHAPE
    if depth > MAX_DEPTH:
        return None, REFUSED_DEPTH
    text = _str_constant(node)
    if text is not None:
        return (TREE_STR, text), []
    if isinstance(node, ast.Name):
        entry = local_table.get(node.id)
        if entry is None:
            entry = module_table.get(node.id)
        if entry is None:
            return None, REFUSED_NAME
        return entry, [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        values = []
        provenance = []
        for element in node.elts:
            tree, cut = _tree_of(element, module_table, local_table, root,
                                 imports, memo, depth + 1)
            if tree is None:
                return None, cut
            if tree[0] != TREE_STR:
                return None, REFUSED_NESTED
            values.append(tree[1])
            provenance.extend(cut)
        return (TREE_TUPLE, values), provenance
    if isinstance(node, ast.Dict):
        pairs = {}
        provenance = []
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                return None, REFUSED_DICT_KEY
            key_tree, key_cut = _tree_of(key_node, module_table, local_table,
                                         root, imports, memo, depth + 1)
            if key_tree is None:
                return None, key_cut
            if key_tree[0] != TREE_STR:
                return None, REFUSED_DICT_KEY
            value_tree, value_cut = _tree_of(value_node, module_table,
                                             local_table, root, imports,
                                             memo, depth + 1)
            if value_tree is None:
                return None, value_cut
            if value_tree[0] != TREE_STR:
                return None, REFUSED_NESTED
            pairs[key_tree[1]] = value_tree[1]
            provenance.extend(key_cut)
            provenance.extend(value_cut)
        return (TREE_DICT, pairs), provenance
    if isinstance(node, ast.Subscript):
        base_node = node.value
        if isinstance(base_node, (ast.ListComp, ast.SetComp, ast.DictComp,
                                  ast.GeneratorExp)):
            return None, REFUSED_COMPREHENSION
        if isinstance(base_node, ast.Call):
            return None, REFUSED_CALL
        if isinstance(base_node, ast.Name):
            entry = local_table.get(base_node.id)
            if entry is None:
                entry = module_table.get(base_node.id)
            element = _tree_element(entry, node.slice, module_table,
                                    local_table)
            if element is not None:
                label = "%s[%s]" % (base_node.id, _slice_label(node.slice))
                return (TREE_STR, element), [label]
        got = _chain_resolve(node, module_table, local_table, root, imports,
                             memo)
        if got is not None:
            stem, label = got
            return (TREE_STR, stem), [label]
        return None, REFUSED_SLICE
    if isinstance(node, ast.Attribute):
        got = _chain_resolve(node, module_table, local_table, root, imports,
                             memo)
        if got is not None:
            stem, label = got
            return (TREE_STR, stem), [label]
        return None, REFUSED_ATTR
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Attribute) and function.attr in (
                "format", "join", "replace", "lower", "upper", "strip",
                "lstrip", "rstrip"):
            return None, REFUSED_FORMAT
        return None, REFUSED_CALL
    if isinstance(node, ast.JoinedStr):
        return None, REFUSED_FORMAT
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                         ast.GeneratorExp)):
        return None, REFUSED_COMPREHENSION
    if isinstance(node, (ast.BinOp, ast.IfExp, ast.BoolOp, ast.Compare)):
        return None, REFUSED_EXPRESSION
    return None, REFUSED_SHAPE


def _annotated_value(node):
    return _annotated_reader()._annotated_value(node)


def _for_named_target(node):
    """The (name, element_node) a single-element for-loop pins, or None.

    The element is returned even when it is a NAME, which is exactly the shape
    the shipped tables read as empty; whether it resolves is decided later.
    """
    if not isinstance(node, ast.For):
        return None
    if not isinstance(node.target, ast.Name):
        return None
    if not isinstance(node.iter, (ast.Tuple, ast.List)):
        return None
    if len(node.iter.elts) != 1:
        return None
    return node.target.id, node.iter.elts[0]


def _candidates(text, inside_functions):
    """Every (name, value_node) this face may extend a table with.

    Only the three alias shapes are collected: a for-loop over one element, an
    annotated alias and a plain single-target assignment. The shipped tables
    keep their own answers for everything else.
    """
    tree = _parse(text)
    if tree is None:
        return None
    found = []
    if inside_functions:
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef,
                                         ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(function):
                if isinstance(node, ast.For):
                    pair = _for_named_target(node)
                    if pair is not None:
                        found.append(pair)
                    continue
                if isinstance(node, ast.AnnAssign):
                    if not isinstance(node.target, ast.Name):
                        continue
                    if not isinstance(node.annotation, ast.Name):
                        continue
                    found.append((node.target.id, node.value))
                    continue
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    if isinstance(node.targets[0], ast.Name):
                        found.append((node.targets[0].id, node.value))
    else:
        top = ast.Module(body=list(tree.body), type_ignores=[])
        for node in _iter_nodes(top, skip_functions=True):
            if isinstance(node, ast.For):
                pair = _for_named_target(node)
                if pair is not None:
                    found.append(pair)
                continue
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and isinstance(
                        node.annotation, ast.Name):
                    found.append((node.target.id, node.value))
                continue
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                if isinstance(node.targets[0], ast.Name):
                    found.append((node.targets[0].id, node.value))
    return found


def _resolve_group(nodes, module_table, local_table, root, imports, memo):
    """(tree, provenance, reason) for every node a name is bound to.

    One tree and every node agrees = resolved. A node that refuses, or two
    nodes that disagree, = refused with a reason, never guessed.
    """
    trees = []
    provenance = []
    reason = None
    for node in nodes:
        tree, cut = _tree_of(node, module_table, local_table, root, imports,
                             memo)
        if tree is None:
            reason = reason or cut
            continue
        trees.append(tree)
        provenance.extend(cut)
    if reason is not None:
        return None, [], reason
    if not trees:
        return None, [], REFUSED_SHAPE
    first = trees[0]
    for other in trees[1:]:
        if other != first:
            return None, [], REFUSED_AMBIGUOUS
    return first, provenance, None


def _scopes(text, root=None):
    """The extended tables plus what was followed and what was refused.

    Returns (module_table, local_table, followed, refused) or None when the
    source will not parse. followed maps scope -> {name: chain}, refused maps
    scope -> {name: reason}.
    """
    base = _annotated_reader()
    module_table = base.module_bindings(text)
    local_table = base.local_bindings(text)
    if module_table is None or local_table is None:
        return None
    module_table = dict(module_table)
    local_table = dict(local_table)
    imports = base._imports_of(text)
    memo = {}
    followed = {"module": {}, "local": {}}
    refused = {"module": {}, "local": {}}
    for scope in ("module", "local"):
        table = module_table if scope == "module" else local_table
        other = local_table if scope == "module" else module_table
        candidates = _candidates(text, scope == "local")
        if candidates is None:
            return None
        groups = {}
        order = []
        for name, node in candidates:
            if name not in groups:
                groups[name] = []
                order.append(name)
            groups[name].append(node)
        pending = list(order)
        for _ in range(BINDING_PASSES):
            progress = False
            rest = []
            for name in pending:
                if name in table:
                    continue
                tree, provenance, reason = _resolve_group(
                    groups[name], table, other, root, imports, memo)
                if tree is None:
                    rest.append(name)
                    continue
                if name in table and table[name] != tree:
                    continue
                table[name] = tree
                if provenance:
                    followed[scope][name] = " <- ".join(provenance)
                else:
                    followed[scope][name] = name
                progress = True
            pending = rest
            if not progress:
                break
        for name in pending:
            if name in table:
                continue
            _tree, _cut, reason = _resolve_group(
                groups[name], table, other, root, imports, memo)
            refused[scope][name] = reason or REFUSED_SHAPE
    return module_table, local_table, followed, refused


def module_bindings(text, root=None):
    """The module-level constant table, shipped law plus alias shapes."""
    got = _scopes(text, root)
    if got is None:
        return None
    return got[0]


def local_bindings(text, root=None):
    """The function-body constant table, shipped law plus alias shapes."""
    got = _scopes(text, root)
    if got is None:
        return None
    return got[1]


def alias_report(text, root=None):
    """What this reading followed, and what it refused, as flat maps."""
    got = _scopes(text, root)
    if got is None:
        return None
    followed = {}
    refused = {}
    for scope in ("module", "local"):
        for name, chain in got[2][scope].items():
            followed[name] = chain
        for name, reason in got[3][scope].items():
            refused[name] = reason
    return {"followed": followed, "refused": refused}


def resolve_expression(expr_text, text, root=None, imports=None, memo=None):
    """The (stem, binding label) an expression text names, or None.

    The shipped resolution law is asked FIRST, so every shape it already
    answered keeps its answer; only then is the same law re-asked with the
    extended tables and the shipped chain hop.
    """
    node = _parse_expr(expr_text)
    if node is None:
        return None
    got = _annotated_reader().resolve_expression(expr_text, text, root,
                                                 imports, memo)
    if got is not None:
        return got
    scopes = _scopes(text, root)
    if scopes is None:
        return None
    module_table, local_table = scopes[0], scopes[1]
    memo = {} if memo is None else memo
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        base_name = node.value.id
        entry = local_table.get(base_name)
        if entry is None:
            entry = module_table.get(base_name)
        element = _tree_element(entry, node.slice, module_table, local_table)
        if element is not None and STEM_RE.match(element):
            label = "%s[%s]" % (base_name, _slice_label(node.slice))
            return element.split(".")[0], label
    got = _local_reader()._resolve_node(node, module_table, local_table, root,
                                       imports, memo)
    if got is not None:
        return got
    return _chain_resolve(node, module_table, local_table, root, imports, memo)


def _imports_of(text):
    """The local stems the probe imports, or None when it will not parse."""
    got = _static_reader().imports_anywhere(text)
    if got is None:
        return None
    return set(got[0])


def dynamic_imports(text, root=None):
    """Constant-bound dynamic imports, on top of the shipped shape detector.

    Returns None when the source will not parse, else a dict with RESOLVED
    triples (shape, stem, binding label) in source order and UNRESOLVED labels
    ("shape:expr") for calls whose module name this reading still cannot
    follow, plus the alias shapes it followed and refused so the row can carry
    them. The shipped dynamic face answers the shapes; this reading only adds
    the extended tables, so no second shape classifier exists.
    """
    base = _dynamic_reader().dynamic_imports(text)
    if base is None:
        return None
    scopes = _scopes(text, root)
    if scopes is None:
        return None
    module_table, local_table = scopes[0], scopes[1]
    imports = _imports_of(text)
    memo = {}
    resolved = [(shape, stem, "") for shape, stem in base["resolved"]]
    unresolved = []
    for label in base["unresolved"]:
        shape, _sep, expr = label.partition(":")
        binding = resolve_expression(expr, text, root, imports, memo)
        if binding is None:
            unresolved.append(label)
            continue
        stem, name = binding
        triple = (shape, stem, name)
        if triple not in resolved:
            resolved.append(triple)
    return {"resolved": resolved, "unresolved": unresolved,
            "module_bindings": sorted(module_table),
            "local_bindings": sorted(local_table),
            "aliases": scopes[2], "refused": scopes[3]}


def _flat_aliases(pairs):
    """Flatten a scope->name->label map into a sorted label list."""
    row = []
    for scope in ("module", "local"):
        for name in sorted(pairs.get(scope, {})):
            row.append("%s:%s@%s" % (scope[0], name, pairs[scope][name]))
    return row


def _stems(text, root):
    """Every local stem a source reaches, static plus extended dynamic."""
    static = _static_reader().imports_anywhere(text)
    dynamic = dynamic_imports(text, root)
    if static is None or dynamic is None:
        return None
    every, top, lazy = static
    stems = list(every)
    for _shape, stem, _binding in dynamic["resolved"]:
        if stem not in stems:
            stems.append(stem)
    return {"every": stems, "top": top, "lazy": lazy,
            "resolved": dynamic["resolved"],
            "unresolved": dynamic["unresolved"],
            "module_bindings": dynamic["module_bindings"],
            "local_bindings": dynamic["local_bindings"],
            "aliases": dynamic["aliases"], "refused": dynamic["refused"]}


def _dynamic_row(pairs):
    row = []
    for shape, stem, binding in pairs:
        label = "%s:%s" % (shape, stem)
        if binding:
            label = "%s@%s" % (label, binding)
        row.append(label)
    return row


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _merge_aliases(target, source, field):
    for scope in ("module", "local"):
        for name, value in source.get(scope, {}).items():
            target[scope].setdefault(name, value)


def helper_scope(path, seams, stack, memo, root):
    """Seams one helper quiets plus the helpers it reaches at any level."""
    key = os.path.abspath(path)
    if key in memo:
        return memo[key]
    if key in stack:
        return [], [], [], True, [], [], {"module": {}, "local": {}}
    stack.add(key)
    empty = {"module": {}, "local": {}}
    try:
        text = _read(path)
    except OSError:
        result = (None, [], [os.path.basename(path)], False, [], [], empty)
        memo[key] = result
        stack.discard(key)
        return result
    direct = _registry().quiets(text, seams)
    got = _stems(text, root)
    if direct is None or got is None:
        result = (None, [], [os.path.basename(path)], False, [], [], empty)
        memo[key] = result
        stack.discard(key)
        return result
    quieted = list(direct)
    helpers = []
    unreadable = []
    lazy_seen = list(got["lazy"])
    dynamic_seen = list(got["resolved"])
    aliases = {"module": dict(got["aliases"]["module"]),
               "local": dict(got["aliases"]["local"])}
    refused = {"module": dict(got["refused"]["module"]),
               "local": dict(got["refused"]["local"])}
    if len(stack) <= MAX_HOPS:
        for stem in got["every"]:
            sub = os.path.join(os.path.dirname(path), stem + SUFFIX)
            if not os.path.isfile(sub):
                continue
            (sub_q, _sub_h, sub_bad, sub_ok, sub_lazy, sub_dyn,
             sub_alias) = helper_scope(sub, seams, stack, memo, root)
            if not sub_ok:
                unreadable.extend(sub_bad)
                continue
            if sub_q:
                helpers.append(os.path.basename(sub)[:-len(SUFFIX)])
                for name in sub_q:
                    if name not in quieted:
                        quieted.append(name)
                for name in sub_lazy:
                    if name not in lazy_seen:
                        lazy_seen.append(name)
                for pair in sub_dyn:
                    if pair not in dynamic_seen:
                        dynamic_seen.append(pair)
                _merge_aliases(aliases, sub_alias, "aliases")
    result = (quieted, helpers, unreadable, True, lazy_seen, dynamic_seen,
              {"module": aliases["module"], "local": aliases["local"]})
    memo[key] = result
    stack.discard(key)
    return result


def probe_scope(text, seams, root):
    """The seams a probe really quiets: its own plus every local hop."""
    direct = _registry().quiets(text, seams)
    got = _stems(text, root)
    if direct is None or got is None:
        return None
    quieted = list(direct)
    helpers = []
    unreadable = []
    lazy_seen = list(got["lazy"])
    dynamic_seen = list(got["resolved"])
    aliases = {"module": dict(got["aliases"]["module"]),
               "local": dict(got["aliases"]["local"])}
    refused = {"module": dict(got["refused"]["module"]),
               "local": dict(got["refused"]["local"])}
    stack = set()
    memo = {}
    for stem in got["every"]:
        path = os.path.join(root, stem + SUFFIX)
        if not os.path.isfile(path):
            continue
        (scope, _sub_h, sub_bad, parsed, sub_lazy, sub_dyn,
         sub_alias) = helper_scope(path, seams, stack, memo, root)
        if not parsed:
            unreadable.extend(sub_bad)
            continue
        if scope:
            helpers.append(os.path.basename(path)[:-len(SUFFIX)])
            for name in scope:
                if name not in quieted:
                    quieted.append(name)
            for name in sub_lazy:
                if name not in lazy_seen:
                    lazy_seen.append(name)
            for pair in sub_dyn:
                if pair not in dynamic_seen:
                    dynamic_seen.append(pair)
            _merge_aliases(aliases, sub_alias, "aliases")
    return {"direct": direct, "helpers": helpers, "quieted": quieted,
            "unreadable": unreadable, "lazy_imports": lazy_seen,
            "dynamic": dynamic_seen, "unresolved": got["unresolved"],
            "module_bindings": got["module_bindings"],
            "local_bindings": got["local_bindings"],
            "aliases": aliases, "refused": refused}


def audit(root=None, module=None):
    """Name every probe that quiets a seam, however the name was bound."""
    module = render_module() if module is None else module
    root = BASE if root is None else root
    if not os.path.isdir(root):
        raise AliasScopeError(E_NO_ROOT, "not a directory: %s" % root)
    seams = seam_names(module)
    owners = seam_owners(module)
    rows = []
    counts = {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0, UNREADABLE: 0,
              HISTORICAL: 0}
    for entry in sorted(os.listdir(root)):
        if not entry.endswith(SUFFIX) or entry.startswith(TEST_PREFIX):
            continue
        path = os.path.join(root, entry)
        if not os.path.isfile(path):
            continue
        stem = entry[:-len(SUFFIX)]
        if ROUND_RE.search(stem):
            rows.append(_row(entry, HISTORICAL))
            counts[HISTORICAL] += 1
            continue
        try:
            text = _read(path)
        except OSError:
            rows.append(_row(entry, UNREADABLE))
            counts[UNREADABLE] += 1
            continue
        scope = probe_scope(text, seams, root)
        if scope is None or scope["unreadable"]:
            row = _row(entry, UNREADABLE)
            if scope:
                _carry(row, scope)
            rows.append(row)
            counts[UNREADABLE] += 1
            continue
        if not scope["quieted"]:
            row = _row(entry, OUT_OF_SCOPE)
            _carry(row, scope)
            rows.append(row)
            counts[OUT_OF_SCOPE] += 1
            continue
        required = [name for name in seams if owners.get(name) != stem]
        missing = [name for name in required if name not in scope["quieted"]]
        verdict = MISSING_SEAM if missing else COVERED
        row = _row(entry, verdict)
        _carry(row, scope)
        row["missing"] = missing
        row["quieted"] = scope["quieted"]
        row["required"] = required
        row["helpers"] = scope["helpers"]
        row["direct"] = scope["direct"]
        rows.append(row)
        counts[verdict] += 1
    stale = counts[MISSING_SEAM] + counts[UNREADABLE]
    return {"tool": LABEL,
            "verdict": SEAMS_STALE if stale else SEAMS_COVERED,
            "seams": [{"name": name, "owner": owners.get(name)}
                      for name in seams],
            "probes": rows, "counts": counts}


def _carry(row, scope):
    row["lazy_imports"] = scope["lazy_imports"]
    row["dynamic"] = _dynamic_row(scope["dynamic"])
    row["unresolved"] = scope["unresolved"]
    row["module_bindings"] = scope["module_bindings"]
    row["local_bindings"] = scope["local_bindings"]
    row["unreadable_helpers"] = scope["unreadable"]
    row["aliases"] = _flat_aliases(scope["aliases"])
    row["alias_refusals"] = _flat_aliases(scope["refused"])


def _row(name, verdict):
    return {"file": name, "verdict": verdict, "missing": [], "quieted": [],
            "required": [], "helpers": [], "direct": [], "lazy_imports": [],
            "dynamic": [], "unresolved": [], "module_bindings": [],
            "local_bindings": [], "unreadable_helpers": [], "aliases": [],
            "alias_refusals": []}


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except AliasScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise AliasScopeError(
            report["verdict"],
            ", ".join("%s:%s" % (row["file"],
                                 "/".join(row["missing"]) or row["verdict"])
                      for row in report["probes"]
                      if row["verdict"] in (MISSING_SEAM, UNREADABLE)))
    return report


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def render(report):
    lines = ["PROBE SEAM ALIAS EXPRESSION SCOPE %s verdict=%s seams=%d "
             "probes=%d covered=%d missing=%d out_of_scope=%d unreadable=%d "
             "historical=%d"
             % (report["tool"], report["verdict"], len(report["seams"]),
                len(report["probes"]), report["counts"][COVERED],
                report["counts"][MISSING_SEAM],
                report["counts"][OUT_OF_SCOPE],
                report["counts"][UNREADABLE], report["counts"][HISTORICAL])]
    if report.get("refusal"):
        lines.append("  refused=%s detail=%s"
                     % (report["refusal"], report["detail"]))
    for seam in report["seams"]:
        lines.append("  SEAM %s owner=%s" % (seam["name"], seam["owner"]))
    for row in report["probes"]:
        if row["verdict"] in (OUT_OF_SCOPE, HISTORICAL):
            if row["unresolved"]:
                lines.append("  MODULE %s %s unresolved=%s"
                             % (row["file"], row["verdict"],
                                ",".join(row["unresolved"])))
            continue
        lines.append("  PROBE %s %s quieted=%d required=%d direct=%d"
                     " helpers=%s dynamic=%s local=%s aliases=%s refused=%s%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]), len(row["direct"]),
                        ",".join(row["helpers"]) or "-",
                        ",".join(row["dynamic"]) or "-",
                        ",".join(row["local_bindings"]) or "-",
                        ",".join(row["aliases"]) or "-",
                        ",".join(row["alias_refusals"]) or "-",
                        (" missing=%s" % ",".join(row["missing"]))
                        if row["missing"] else ""))
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=None, metavar="DIR",
                        help="the directory probed for seam-quieting modules")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])
    try:
        report = audit(args.root)
    except AliasScopeError as exc:
        print("FAIL root: %s %s" % (exc.code, exc.detail))
        return 3
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(render(report))
    return 0 if report["verdict"] == SEAMS_COVERED else 2


def main_entry():
    argv = sys.argv
    try:
        return main(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 5


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - CLI guard
        sys.stderr.write("%s %s\n" % (E_ARGS, exc))
        sys.exit(5)