"""probe_seam_constant_alias_scope - follow a constant through an alias.

MEASURED at R2525 on the face own readers of the seam annotated-constant
scope: `BASE_NAME = "x"` then `ALIAS: str = BASE_NAME` reads the table
{'BASE_NAME': ('str', 'x')} with ALIAS ABSENT, so an annotated alias of an
existing constant stayed unresolved while a plain annotated literal was read.
A `with open(...) as handle:` binding read {} from the local table, a for-loop
over TWO or more literals read {} as well, and a two-hop dict chain was not
followed - the shapes read EMPTY, which is indistinguishable from a name that
was never declared.

This face reads those shapes with ONE reading and no second classifier:

  alias_chains(text)
      every binding whose VALUE is another NAME is collected (a plain
      assignment, an annotated assignment with a plain-name annotation and a
      walrus), then resolved to a fixpoint against the SHIPPED constant tables
      so an alias of an alias follows the whole chain. A name bound twice with
      different resolutions is dropped, and the chain it followed is published
      on the row (AC-PCAS1).
  refused_shapes(text)
      the shapes that are genuinely not constants are NAMED per name instead
      of reading empty: a with-as binding, a for-loop target over two or more
      literals, and a value built by a call, a format, an arithmetic
      expression or a comprehension (AC-PCAS2, AC-PCAS4).
  module_bindings / local_bindings
      the shipped tables EXTENDED, never replaced: the annotated face answers
      first, the shipped local face underneath it, and the alias fixpoint is
      added on top in the module body and in function bodies.
  resolve_expression
      the shipped resolution law is asked FIRST, then the annotated face
      (which adds the annotated, walrus, for-loop and nested-attribute
      shapes), and only when both answer None is a bare NAME resolved through
      the alias chain. A dict chain of two hops resolves with its FULL binding
      label; a deeper chain is either resolved or REFUSED with the label and
      the hop that broke, never silently None (AC-PCAS3).
  helper_scope / probe_scope / audit / guard
      the same cycle-guarded same-root walk the shipped faces use, with the
      shipped registry `quiets` still the ONE seam classifier.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PCAS5). No probe and
no helper is ever imported or run.

Criteria AC-PCAS1..AC-PCAS6 were pinned in state/queue/tech.md:563 at R2525 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: only literally constant values are followed
and nothing is evaluated, so a call, a format, a join, a comprehension or a
name built at run time stays unresolved and is named as such. An alias chain
is followed inside ONE scope (module body, or function bodies) and never
across scopes, because a name read in a function from the module body would
require guessing the call site. A with-as binding is NEVER resolved even when
the context manager looks constant, because the bound value is a run-time
object. The walk follows local modules in the same root only, at most MAX_HOPS
links with a cycle guard. The walk shape is written here rather than injected
into a shipped module, because parameterising a shipped module would owe a
battery in the same window; the tables and the resolution law are the shipped
ones EXTENDED at call time, and the seam CLASSIFIER is still the registry's
single `quiets`, so no second classifier exists.

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
import warnings

LABEL = "os-probe-seam-constant-alias-scope"
E_ARGS = "E_PCAS_ARGS"
E_NO_ROOT = "E_PCAS_NO_ROOT"

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
MAX_HOPS = 8
MAX_ALIAS = 8

TREE_STR = "str"
TREE_TUPLE = "tuple"
TREE_DICT = "dict"

SHAPE_ALIAS = "alias"
SHAPE_WITH = "with-as"
SHAPE_FOR_MULTI = "for-multi"
SHAPE_FOR_NONCONST = "for-nonconstant"
SHAPE_CALL = "call"
SHAPE_FORMAT = "format"
SHAPE_EXPRESSION = "expression"
SHAPE_COMPREHENSION = "comprehension"
SHAPE_AMBIGUOUS = "alias-ambiguous"
SHAPE_ALIAS_UNRESOLVED = "alias-unresolved"

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")


class AliasScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base_reader():
    """The shipped local-constant face (tables, entry format and law)."""
    import probe_seam_local_constant_scope
    return probe_seam_local_constant_scope


def _annotated_reader():
    """The shipped annotated-constant face (one more rung, no copy)."""
    import probe_seam_annotated_constant_scope
    return probe_seam_annotated_constant_scope


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
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return ast.parse(text)
    except SyntaxError:
        return None


def _parse_expr(text):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return ast.parse(text, mode="eval").body
    except SyntaxError:
        return None


def _shape_of_value(node):
    """The shape name a value expression carries when it is not a constant."""
    if node is None:
        return None
    if isinstance(node, ast.Call):
        return SHAPE_CALL
    if isinstance(node, ast.JoinedStr):
        return SHAPE_FORMAT
    if isinstance(node, ast.BinOp):
        return SHAPE_EXPRESSION
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                         ast.GeneratorExp)):
        return SHAPE_COMPREHENSION
    return None


def _iter_nodes(node, skip_functions):
    """Every descendant of a node, optionally not entering function bodies."""
    stack = [node]
    while stack:
        current = stack.pop()
        if current is not node:
            yield current
        if skip_functions and isinstance(
                current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        stack.extend(ast.iter_child_nodes(current))


def _body_nodes(tree, inside_functions):
    """The nodes one scope is read over: module body, or function bodies."""
    if inside_functions:
        for function in ast.walk(tree):
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for node in ast.walk(function):
                    yield node
    else:
        top = ast.Module(body=list(tree.body), type_ignores=[])
        for node in _iter_nodes(top, skip_functions=True):
            yield node


def _alias_pairs(text, inside_functions):
    """The (name, source name) alias bindings and the refused shapes.

    Returns (pairs, shapes) where pairs is a list in source order and shapes
    maps a name to the shape that makes it genuinely not a constant.
    """
    tree = _parse(text)
    if tree is None:
        return None, None
    pairs = []
    shapes = {}
    literals = {}
    for node in _body_nodes(tree, inside_functions):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            name = target.id
        elif isinstance(node, ast.AnnAssign):
            if not isinstance(node.target, ast.Name):
                continue
            name = node.target.id
        elif isinstance(node, ast.NamedExpr):
            if not isinstance(node.target, ast.Name):
                continue
            name = node.target.id
        elif isinstance(node, ast.For):
            if not isinstance(node.target, ast.Name):
                continue
            elements = None
            if isinstance(node.iter, (ast.Tuple, ast.List)):
                elements = node.iter.elts
            if elements is None:
                shapes[node.target.id] = SHAPE_FOR_NONCONST
            elif len(elements) != 1:
                shapes[node.target.id] = SHAPE_FOR_MULTI
            elif _shape_of_value(elements[0]) is not None:
                shapes[node.target.id] = _shape_of_value(elements[0])
            continue
        elif isinstance(node, ast.With) or isinstance(node, ast.AsyncWith):
            for item in node.items:
                if item.optional_vars is None:
                    continue
                if isinstance(item.optional_vars, ast.Name):
                    shapes[item.optional_vars.id] = SHAPE_WITH
            continue
        else:
            continue
        value = node.value
        if isinstance(value, ast.Name):
            pairs.append((name, value.id))
            continue
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            literals.setdefault(name, set()).add(value.value)
            continue
        shape = _shape_of_value(value)
        if shape is not None:
            shapes[name] = shape
    return pairs, shapes, literals


def _scope_tables(text):
    """The shipped tables this face extends, annotated face underneath."""
    annotated = _annotated_reader()
    module_table = annotated.module_bindings(text)
    local_table = annotated.local_bindings(text)
    if module_table is None or local_table is None:
        return None, None
    return dict(module_table), dict(local_table)


def alias_fixpoint(text, inside_functions):
    """Resolve aliases of aliases inside ONE scope, with their chains.

    Returns (resolved, shapes) where resolved maps a name to (entry, chain)
    and chain is the tuple of names followed, innermost name first. A name
    bound twice with different resolutions is dropped and named ambiguous; a
    chain whose source is not a constant anywhere is named unresolved.
    """
    pairs, shapes, literals = _alias_pairs(text, inside_functions)
    if pairs is None:
        return None, None
    module_table, local_table = _scope_tables(text)
    if module_table is None:
        return None, None
    table = dict(local_table) if inside_functions else dict(module_table)
    if inside_functions:
        for name, entry in module_table.items():
            table.setdefault(name, entry)
    fixed = {}
    pending = {}
    for name, source in pairs:
        entry = table.get(source)
        if entry is not None:
            fixed.setdefault(name, []).append((entry, (source,)))
        else:
            pending.setdefault(name, []).append(source)
    for _step in range(MAX_ALIAS):
        moved = False
        for name in list(pending):
            for source in list(pending[name]):
                chain = fixed.get(source)
                if chain is None or len(chain) != 1:
                    continue
                entry, source_chain = chain[0]
                fixed.setdefault(name, []).append(
                    (entry, (source,) + source_chain))
                pending[name].remove(source)
                moved = True
        if not moved:
            break
    resolved = {}
    for name, items in fixed.items():
        if len(items) != 1 or name in literals:
            shapes[name] = SHAPE_AMBIGUOUS
            continue
        entry, chain = items[0]
        if len(chain) > MAX_ALIAS:
            shapes[name] = SHAPE_ALIAS_UNRESOLVED
            continue
        resolved[name] = (entry, chain)
    for name in pending:
        if name not in resolved:
            shapes.setdefault(name, SHAPE_ALIAS_UNRESOLVED)
    return resolved, shapes


def alias_tables(text):
    """The published alias table for the module body and for functions."""
    module_resolved, module_shapes = alias_fixpoint(text, False)
    local_resolved, local_shapes = alias_fixpoint(text, True)
    if module_resolved is None or local_resolved is None:
        return None
    return {"module": module_resolved, "local": local_resolved,
            "module_shapes": module_shapes, "local_shapes": local_shapes}


def module_bindings(text):
    """The module-level constant table, shipped law plus alias fixpoint."""
    annotated = _annotated_reader()
    table = annotated.module_bindings(text)
    if table is None:
        return None
    table = dict(table)
    got = alias_tables(text)
    if got is None:
        return table
    for name, (entry, _chain) in got["module"].items():
        known = table.get(name)
        if known is not None and known != entry:
            table.pop(name, None)
            continue
        if known is None:
            table[name] = entry
    return table


def local_bindings(text):
    """The function-body constant table, shipped law plus alias fixpoint."""
    annotated = _annotated_reader()
    table = annotated.local_bindings(text)
    if table is None:
        return None
    table = dict(table)
    got = alias_tables(text)
    if got is None:
        return table
    for name, (entry, _chain) in got["local"].items():
        known = table.get(name)
        if known is not None and known != entry:
            table.pop(name, None)
            continue
        if known is None:
            table[name] = entry
    return table


def alias_label(name, got):
    """The chain label for a name this reading followed, or empty."""
    if got is None:
        return ""
    for scope in ("local", "module"):
        resolved = got[scope]
        if name in resolved:
            chain = resolved[name][1]
            return "<-".join((name,) + tuple(chain))
    return ""


def _chain_refusal(node, root, imports, memo):
    """The label of an attribute chain that cannot be resolved, or None.

    The walk answers WHICH hop broke, so a deep chain is refused with its
    label rather than reading silently None (AC-PCAS3).
    """
    if root is None:
        return None
    head = node
    while isinstance(head, ast.Subscript):
        head = head.value
    attributes = []
    while isinstance(head, ast.Attribute):
        attributes.append(head.attr)
        head = head.value
    if not isinstance(head, ast.Name) or not attributes:
        return None
    stem = head.id
    if imports is not None and stem not in imports:
        return None
    annotated = _annotated_reader()
    trees = annotated._module_trees(stem, root, memo)
    if not trees:
        return None
    inner = attributes[-1]
    label = ".".join([stem] + list(reversed(attributes)))
    if inner not in trees:
        return "%s:no-constant %s" % (label, inner)
    tree = trees[inner]
    for attribute in reversed(attributes[:-1]):
        if tree[0] != annotated.TREE_DICT:
            return "%s:not-a-dict %s" % (label, attribute)
        if attribute not in tree[1]:
            return "%s:no-key %s" % (label, attribute)
        tree = tree[1][attribute]
    return None


def resolve_expression(expr_text, text, root=None, imports=None, memo=None):
    """The (stem, binding label, refused label) an expression names.

    The shipped law is asked first, then the annotated face, and only when
    both answer None is a bare NAME resolved through the alias chain.
    """
    node = _parse_expr(expr_text)
    if node is None:
        return None, None
    memo = {} if memo is None else memo
    got = _annotated_reader().resolve_expression(
        expr_text, text, root, imports, memo)
    if got is not None:
        return got, None
    module_table = module_bindings(text)
    local_table = local_bindings(text)
    if module_table is None or local_table is None:
        return None, _chain_refusal(node, root, imports, memo)
    if isinstance(node, ast.Name):
        tables = alias_tables(text)
        entry = local_table.get(node.id) or module_table.get(node.id)
        if entry is not None:
            base = _base_reader()
            if entry[0] == base.SHAPE_STR and STEM_RE.match(entry[1]):
                label = alias_label(node.id, tables)
                return (entry[1].split(".")[0], label), None
    return None, _chain_refusal(node, root, imports, memo)


def _imports_of(text):
    """The local stems the probe imports, or None when it will not parse."""
    got = _static_reader().imports_anywhere(text)
    if got is None:
        return None
    return set(got[0])


def dynamic_imports(text, root=None):
    """Constant-bound dynamic imports, with alias chains and refusals.

    Returns None when the source will not parse, else a dict with RESOLVED
    triples (shape, stem, binding label), UNRESOLVED labels ("shape:expr") and
    REFUSED chain labels. The shipped dynamic face answers the shapes; this
    reading only adds the alias chain and the refused-hop label, so no second
    shape classifier exists.
    """
    annotated = _annotated_reader()
    base = annotated.dynamic_imports(text, root)
    if base is None:
        return None
    module_table = module_bindings(text)
    local_table = local_bindings(text)
    if module_table is None or local_table is None:
        return None
    imports = _imports_of(text)
    memo = {}
    tables = alias_tables(text)
    resolved = []
    for triple in base["resolved"]:
        if len(triple) == 3 and triple[2]:
            resolved.append(triple)
        else:
            resolved.append((triple[0], triple[1], ""))
    unresolved = []
    refused = []
    for label in base["unresolved"]:
        shape, _sep, expr = label.partition(":")
        got, refusal = resolve_expression(expr, text, root, imports, memo)
        if got is None:
            unresolved.append(label)
            if refusal:
                refused.append(refusal)
            continue
        stem, name = got
        triple = (shape, stem, name)
        if triple not in resolved:
            resolved.append(triple)
    shapes = {}
    if tables is not None:
        for scope_shapes in ("module_shapes", "local_shapes"):
            for name, shape in tables[scope_shapes].items():
                shapes[name] = shape
    return {"resolved": resolved, "unresolved": unresolved,
            "refused": refused, "shapes": shapes,
            "alias_chains": _chain_rows(tables),
            "module_bindings": sorted(module_table),
            "local_bindings": sorted(local_table)}


def _chain_rows(tables):
    """The alias chains this reading followed, as publishable labels."""
    rows = []
    if tables is None:
        return rows
    for scope in ("module", "local"):
        for name in sorted(tables[scope]):
            chain = tables[scope][name][1]
            if not chain:
                continue
            rows.append("<-".join((name,) + tuple(chain)))
    return rows


def _stems(text, root):
    """Every local stem a source reaches, static plus extended dynamic."""
    static = _static_reader().imports_anywhere(text)
    dynamic = dynamic_imports(text, root)
    if static is None or dynamic is None:
        return None
    every, top, lazy = static
    stems = list(every)
    for triple in dynamic["resolved"]:
        stem = triple[1]
        if stem not in stems:
            stems.append(stem)
    return {"every": stems, "top": top, "lazy": lazy,
            "resolved": dynamic["resolved"],
            "unresolved": dynamic["unresolved"],
            "refused": dynamic["refused"],
            "shapes": dynamic["shapes"],
            "alias_chains": dynamic["alias_chains"],
            "module_bindings": dynamic["module_bindings"],
            "local_bindings": dynamic["local_bindings"]}


def _dynamic_row(pairs):
    row = []
    for shape, stem, binding in pairs:
        label = "%s:%s" % (shape, stem)
        if binding:
            label = "%s@%s" % (label, binding)
        row.append(label)
    return row


def _shape_row(shapes):
    return ["%s=%s" % (name, shapes[name]) for name in sorted(shapes)]


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def helper_scope(path, seams, stack, memo, root):
    """Seams one helper quiets plus the helpers it reaches at any level."""
    key = os.path.abspath(path)
    if key in memo:
        return memo[key]
    if key in stack:
        return [], [], [], True, [], [], [], []
    stack.add(key)
    try:
        text = _read(path)
    except OSError:
        result = (None, [], [os.path.basename(path)], False, [], [], [], [])
        memo[key] = result
        stack.discard(key)
        return result
    direct = _registry().quiets(text, seams)
    got = _stems(text, root)
    if direct is None or got is None:
        result = (None, [], [os.path.basename(path)], False, [], [], [], [])
        memo[key] = result
        stack.discard(key)
        return result
    quieted = list(direct)
    helpers = []
    unreadable = []
    lazy_seen = list(got["lazy"])
    dynamic_seen = list(got["resolved"])
    refused_seen = list(got["refused"])
    if len(stack) <= MAX_HOPS:
        for stem in got["every"]:
            sub = os.path.join(os.path.dirname(path), stem + SUFFIX)
            if not os.path.isfile(sub):
                continue
            (sub_q, sub_h, sub_bad, sub_ok, sub_lazy, sub_dyn,
             sub_refused, _unused) = helper_scope(
                sub, seams, stack, memo, root)
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
                for item in sub_refused:
                    if item not in refused_seen:
                        refused_seen.append(item)
    result = (quieted, helpers, unreadable, True, lazy_seen, dynamic_seen,
              refused_seen, [])
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
    refused_seen = list(got["refused"])
    stack = set()
    memo = {}
    for stem in got["every"]:
        path = os.path.join(root, stem + SUFFIX)
        if not os.path.isfile(path):
            continue
        (scope, _sub_h, sub_bad, parsed, sub_lazy, sub_dyn,
         sub_refused, _unused) = helper_scope(
            path, seams, stack, memo, root)
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
            for item in sub_refused:
                if item not in refused_seen:
                    refused_seen.append(item)
    return {"direct": direct, "helpers": helpers, "quieted": quieted,
            "unreadable": unreadable, "lazy_imports": lazy_seen,
            "dynamic": dynamic_seen, "unresolved": got["unresolved"],
            "refused": refused_seen, "shapes": got["shapes"],
            "alias_chains": got["alias_chains"],
            "module_bindings": got["module_bindings"],
            "local_bindings": got["local_bindings"]}


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
    row["refused_chains"] = scope["refused"]
    row["shapes"] = _shape_row(scope["shapes"])
    row["alias_chains"] = scope["alias_chains"]
    row["module_bindings"] = scope["module_bindings"]
    row["local_bindings"] = scope["local_bindings"]
    row["unreadable_helpers"] = scope["unreadable"]


def _row(name, verdict):
    return {"file": name, "verdict": verdict, "missing": [], "quieted": [],
            "required": [], "helpers": [], "direct": [], "lazy_imports": [],
            "dynamic": [], "unresolved": [], "refused_chains": [],
            "shapes": [], "alias_chains": [], "module_bindings": [],
            "local_bindings": [], "unreadable_helpers": []}


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
    lines = ["PROBE SEAM CONSTANT ALIAS SCOPE %s verdict=%s seams=%d "
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
            if row["unresolved"] or row["refused_chains"] or row["shapes"]:
                lines.append("  MODULE %s %s unresolved=%s refused=%s "
                             "shapes=%s"
                             % (row["file"], row["verdict"],
                                ",".join(row["unresolved"]) or "-",
                                ",".join(row["refused_chains"]) or "-",
                                ",".join(row["shapes"]) or "-"))
            continue
        lines.append("  PROBE %s %s quieted=%d required=%d direct=%d"
                     " helpers=%s dynamic=%s alias=%s shapes=%s%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]), len(row["direct"]),
                        ",".join(row["helpers"]) or "-",
                        ",".join(row["dynamic"]) or "-",
                        ",".join(row["alias_chains"]) or "-",
                        ",".join(row["shapes"]) or "-",
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