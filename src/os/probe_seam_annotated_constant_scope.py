"""probe_seam_annotated_constant_scope - read the other constant shapes.

MEASURED at R2523 on the shipped local-constant face own readers, in that
window own legs: `NAME: str = "x"` is an ast.AnnAssign and reads {} from BOTH
module_bindings and local_bindings, a walrus binding `if (name := "x"):` reads
{} from local_bindings, and a for-loop target `for name in ("x",):` reads {}
as well - so a probe that declares its module name in any of those three forms
still reads OUT-OF-SCOPE. A container reached through a NESTED attribute
(`pkg.CFG.NAMES[0]`) resolved to None too, because only one attribute hop on a
module file in the same root was followed.

This face reads those shapes with ONE reading and no second classifier:

  module_bindings(text) / local_bindings(text)
      the SHIPPED constant tables, extended - not replaced. The shipped law
      answers first; this face adds an annotated assignment whose annotation
      is a PLAIN NAME (`NAME: str = "x"`), a walrus binding of a constant,
      and a for-loop target over a single-element constant sequence, in the
      module body and in function bodies. A name bound twice with different
      constants, or once to something that is not a constant, is dropped: an
      ambiguous name is never resolved. An annotated assignment whose
      annotation is NOT a plain name (`NAME: Dict[str, str] = ...`) is never
      resolved, so the shape is refused rather than guessed.
  resolve_expression(expr_text, text, root, imports, memo)
      the shipped resolution law is asked FIRST with the extended tables, so
      a plain name, a tuple element and a dict value keep exactly the shipped
      answer. When it answers None, ONE more attribute hop is taken over a
      module-level constant TREE (`pkg.CFG.NAMES[0]`), and the row carries
      the binding label it was followed through. A Call node is never
      resolved, so a container returned by a function stays unresolved.
  dynamic_imports(text, root)
      the shipped dynamic face answers the shapes (its detection is the ONE
      shape classifier). Each call it could not resolve is offered to the
      extended reading; a resolvable one moves to RESOLVED carrying the
      binding label, the rest stay UNRESOLVED and are named, not guessed.
  helper_scope / probe_scope / audit / guard
      the same cycle-guarded same-root walk the shipped faces use, with the
      extended stems feeding it, and the shipped registry `quiets` as the ONE
      seam classifier.

Read-only: nothing is written, no file is opened for writing, and every
digest this reading touches is unchanged across a full audit (AC-PLAC5). No
probe and no helper is ever imported or run, which is why a stale probe is
NAMED rather than paid for.

Criteria AC-PLAC1..AC-PLAC6 were pinned in state/queue/tech.md:561 at R2523 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: only literally constant values are followed
(str, tuple/list, dict of constants) and nothing is evaluated, so a call, a
join, an f-string, a comprehension or a name built from a variable stays
unresolved. An annotated assignment counts only when its annotation is a plain
name. One extra attribute hop is taken on a module file in the SAME root,
gated by the probe own imports, and the chain must be dict entries after the
first hop; deeper chains, a container reached by a call and a container
imported from another package are NOT resolved. The walk follows local
modules in the same root only, at most MAX_HOPS links with a cycle guard.
These shapes can UNDER-report a stale probe but can never invent one. The
walk shape is written here rather than injected into the shipped
constant-binding face, because parameterising a shipped module would owe a
battery in the same window; the tables and the resolution law are the shipped
ones EXTENDED at call time, and the seam CLASSIFIER is still the shipped
registry single `quiets`, so no second classifier exists.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-ANNOTATED-COVERED)
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

LABEL = "os-probe-seam-annotated-constant-scope"
E_ARGS = "E_PLAC_ARGS"
E_NO_ROOT = "E_PLAC_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-ANNOTATED-COVERED"
SEAMS_STALE = "SEAMS-ANNOTATED-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)
STEM_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
MAX_HOPS = 8

TREE_STR = "str"
TREE_TUPLE = "tuple"
TREE_DICT = "dict"

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")


class AnnotatedScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base_reader():
    """The shipped constant-binding face, imported once (tables and law)."""
    import probe_seam_local_constant_scope
    return probe_seam_local_constant_scope


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


def _str_constant(node):
    """The string a node literally holds, or None. Nothing is evaluated."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _annotated_value(node):
    """The value of an annotated assignment this face may read, or None.

    Only a plain-name annotation (`NAME: str = ...`) is read. Any other
    annotation shape is refused rather than guessed, because the annotation is
    part of what the binding claims to be.
    """
    if not isinstance(node, ast.AnnAssign):
        return None
    if not isinstance(node.target, ast.Name):
        return None
    if not isinstance(node.annotation, ast.Name):
        return None
    return node.value


def _for_targets(node):
    """The (name, value) pairs a for-loop pins, or None when not constant.

    Only a single-element tuple/list of string constants pins a name to one
    value; anything else leaves the name ambiguous and unread.
    """
    if not isinstance(node, ast.For):
        return None
    if not isinstance(node.target, ast.Name):
        return None
    if not isinstance(node.iter, (ast.Tuple, ast.List)):
        return None
    if len(node.iter.elts) != 1:
        return None
    text = _str_constant(node.iter.elts[0])
    if text is None:
        return None
    return node.target.id, text


def _walrus_pairs(node):
    """The (name, value) pairs a walrus binding pins, or None."""
    if not isinstance(node, ast.NamedExpr):
        return None
    if not isinstance(node.target, ast.Name):
        return None
    text = _str_constant(node.value)
    if text is None:
        return None
    return node.target.id, text


def _entry_for_value(value):
    """The shipped (shape, value) entry for a constant value, or None.

    The shapes and the entry format are the SHIPPED ones, so a table built
    here can be handed straight to the shipped resolution law.
    """
    base = _base_reader()
    if value is None:
        return None
    return base._constant_entry(value)


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


def _extended_entries(text, inside_functions):
    """The extra constant entries this face reads, with ambiguity dropped.

    Returns (extras, poisoned): extras maps a name to a shipped-shape entry,
    poisoned holds a name bound to something that is not a constant or bound
    twice with different constants. Only the shapes the shipped tables do not
    read are collected here - an annotated assignment with a plain-name
    annotation, a walrus binding and a single-element for-loop target.
    """
    tree = _parse(text)
    if tree is None:
        return None, None
    extras = {}
    poisoned = set()

    def note(name, entry):
        if entry is None:
            poisoned.add(name)
            return
        previous = extras.get(name)
        if previous is None:
            extras[name] = entry
        elif previous != entry:
            poisoned.add(name)

    if inside_functions:
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(function):
                if isinstance(node, ast.AnnAssign):
                    got = _annotated_value(node)
                    if got is None and not isinstance(node.annotation, ast.Name):
                        continue
                    note(node.target.id, _entry_for_value(got))
                elif isinstance(node, ast.NamedExpr):
                    pair = _walrus_pairs(node)
                    if pair is not None:
                        note(pair[0], (TREE_STR, pair[1]))
                elif isinstance(node, ast.For):
                    pair = _for_targets(node)
                    if pair is not None:
                        note(pair[0], (TREE_STR, pair[1]))
    else:
        top = ast.Module(body=list(tree.body), type_ignores=[])
        for node in _iter_nodes(top, skip_functions=True):
            if isinstance(node, ast.AnnAssign):
                got = _annotated_value(node)
                if got is None and not isinstance(node.annotation, ast.Name):
                    continue
                note(node.target.id, _entry_for_value(got))
            elif isinstance(node, ast.NamedExpr):
                pair = _walrus_pairs(node)
                if pair is not None:
                    note(pair[0], (TREE_STR, pair[1]))
            elif isinstance(node, ast.For):
                pair = _for_targets(node)
                if pair is not None:
                    note(pair[0], (TREE_STR, pair[1]))
    for name in list(poisoned):
        extras.pop(name, None)
    return extras, poisoned


def module_bindings(text):
    """The module-level constant table, shipped law plus annotated shapes."""
    base = _base_reader()
    table = base.module_bindings(text)
    if table is None:
        return None
    table = dict(table)
    extras, poisoned = _extended_entries(text, inside_functions=False)
    if extras is None:
        return table
    for name, entry in extras.items():
        if name in poisoned:
            continue
        if name in table and table[name] != entry:
            continue
        table[name] = entry
    return table


def local_bindings(text):
    """The function-body constant table, shipped law plus annotated shapes."""
    base = _base_reader()
    table = base.local_bindings(text)
    if table is None:
        return None
    table = dict(table)
    extras, poisoned = _extended_entries(text, inside_functions=True)
    if extras is None:
        return table
    for name, entry in extras.items():
        if name in poisoned:
            continue
        if name in table and table[name] != entry:
            continue
        table[name] = entry
    return table


def _constant_tree(node):
    """The nested constant a node literally holds, or None. Nothing evaluated.

    str -> (TREE_STR, text); tuple/list of constants -> (TREE_TUPLE, [trees]);
    dict of str keys to constants -> (TREE_DICT, {key: tree}). A name, a call,
    a comprehension or any other node is not constant and reads None.
    """
    text = _str_constant(node)
    if text is not None:
        return (TREE_STR, text)
    if isinstance(node, (ast.Tuple, ast.List)):
        items = []
        for element in node.elts:
            item = _constant_tree(element)
            if item is None:
                return None
            items.append(item)
        return (TREE_TUPLE, items)
    if isinstance(node, ast.Dict):
        pairs = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                return None
            key = _constant_tree(key_node)
            value = _constant_tree(value_node)
            if key is None or key[0] != TREE_STR or value is None:
                return None
            pairs[key[1]] = value
        return (TREE_DICT, pairs)
    return None


def _module_trees(stem, root, memo):
    """The module-level constant trees of a module file in the same root."""
    if root is None:
        return None
    if stem in memo:
        return memo[stem]
    path = os.path.join(root, stem + SUFFIX)
    trees = None
    if os.path.isfile(path):
        try:
            text = _read(path)
        except OSError:
            text = None
        tree = _parse(text) if text is not None else None
        if tree is not None:
            trees = {}
            for node in tree.body:
                value = None
                name = None
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    if isinstance(node.targets[0], ast.Name):
                        name = node.targets[0].id
                        value = node.value
                elif isinstance(node, ast.AnnAssign):
                    got = _annotated_value(node)
                    if got is not None:
                        name = node.target.id
                        value = got
                if name is None:
                    continue
                constant = _constant_tree(value)
                if constant is not None:
                    trees[name] = constant
    memo[stem] = trees
    return trees


def _chain_parts(node):
    """The (stem, [outer..inner attributes]) an attribute chain names."""
    attributes = []
    head = node
    while isinstance(head, ast.Attribute):
        attributes.append(head.attr)
        head = head.value
    if not isinstance(head, ast.Name) or not attributes:
        return None
    return head.id, attributes


def _chain_entry(node, root, imports, memo):
    """The constant tree an attribute chain reaches, with its binding label.

    Only a plain attribute chain on a module file in the SAME root is
    followed, gated by the probe own imports; after the first hop every step
    must be a dict entry. A call anywhere in the chain resolves nothing.
    """
    if root is None:
        return None
    parts = _chain_parts(node)
    if parts is None:
        return None
    stem, attributes = parts
    if imports is not None and stem not in imports:
        return None
    trees = _module_trees(stem, root, memo)
    if not trees:
        return None
    inner = attributes[-1]
    tree = trees.get(inner)
    if tree is None:
        return None
    steps = []
    for attribute in reversed(attributes[:-1]):
        if tree[0] != TREE_DICT:
            return None
        tree = tree[1].get(attribute)
        if tree is None:
            return None
        steps.append(attribute)
    label = ".".join([stem, inner] + list(reversed(steps)))
    return tree, label


def _name_string(node, module_table, local_table):
    """The string a bare name is bound to, local scope first."""
    if not isinstance(node, ast.Name):
        return None
    base = _base_reader()
    entry = local_table.get(node.id) or module_table.get(node.id)
    if entry is None or entry[0] != base.SHAPE_STR:
        return None
    return entry[1]


def _tree_element(tree, index_node, module_table, local_table):
    """The constant a tree holds at a constant index or key, or None."""
    if tree is None:
        return None
    if tree[0] == TREE_TUPLE:
        if not isinstance(index_node, ast.Constant):
            return None
        position = index_node.value
        if not isinstance(position, int) or isinstance(position, bool):
            return None
        if not -len(tree[1]) <= position < len(tree[1]):
            return None
        return tree[1][position]
    if tree[0] == TREE_DICT:
        key = _str_constant(index_node)
        if key is None:
            key = _name_string(index_node, module_table, local_table)
        if key is None or key not in tree[1]:
            return None
        return tree[1][key]
    return None


def _chain_resolve(node, module_table, local_table, root, imports, memo):
    """The (stem, binding label) an attribute chain names, or None."""
    if isinstance(node, ast.Subscript):
        base_node = node.value
        if not isinstance(base_node, ast.Attribute):
            return None
        got = _chain_entry(base_node, root, imports, memo)
        if got is None:
            return None
        tree, label = got
        item = _tree_element(tree, node.slice, module_table, local_table)
        if item is None or item[0] != TREE_STR:
            return None
        if not STEM_RE.match(item[1]):
            return None
        return item[1].split(".")[0], label
    if isinstance(node, ast.Attribute):
        got = _chain_entry(node, root, imports, memo)
        if got is None:
            return None
        tree, label = got
        if tree[0] != TREE_STR or not STEM_RE.match(tree[1]):
            return None
        return tree[1].split(".")[0], label
    return None


def resolve_expression(expr_text, text, root=None, imports=None, memo=None):
    """The (stem, binding label) an expression text names, or None.

    The shipped resolution law is asked first with the extended tables, so
    every shape it already answered keeps its answer; only when it answers
    None is one more attribute hop taken on a module-level constant tree.
    """
    node = _parse_expr(expr_text)
    if node is None:
        return None
    module_table = module_bindings(text)
    local_table = local_bindings(text)
    if module_table is None or local_table is None:
        return None
    memo = {} if memo is None else memo
    got = _base_reader()._resolve_node(node, module_table, local_table, root,
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
    ("shape:expr") for calls whose module name is still not a constant this
    reading can follow. The shipped dynamic face answers the shapes; this
    reading only adds the extended tables and the extra hop, so no second
    shape classifier exists.
    """
    base = _dynamic_reader().dynamic_imports(text)
    if base is None:
        return None
    module_table = module_bindings(text)
    local_table = local_bindings(text)
    if module_table is None or local_table is None:
        return None
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
            "local_bindings": sorted(local_table)}


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
            "local_bindings": dynamic["local_bindings"]}


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


def helper_scope(path, seams, stack, memo, root):
    """Seams one helper quiets plus the helpers it reaches at any level."""
    key = os.path.abspath(path)
    if key in memo:
        return memo[key]
    if key in stack:
        return [], [], [], True, [], []
    stack.add(key)
    try:
        text = _read(path)
    except OSError:
        result = (None, [], [os.path.basename(path)], False, [], [])
        memo[key] = result
        stack.discard(key)
        return result
    direct = _registry().quiets(text, seams)
    got = _stems(text, root)
    if direct is None or got is None:
        result = (None, [], [os.path.basename(path)], False, [], [])
        memo[key] = result
        stack.discard(key)
        return result
    quieted = list(direct)
    helpers = []
    unreadable = []
    lazy_seen = list(got["lazy"])
    dynamic_seen = list(got["resolved"])
    if len(stack) <= MAX_HOPS:
        for stem in got["every"]:
            sub = os.path.join(os.path.dirname(path), stem + SUFFIX)
            if not os.path.isfile(sub):
                continue
            sub_q, sub_h, sub_bad, sub_ok, sub_lazy, sub_dyn = helper_scope(
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
    result = (quieted, helpers, unreadable, True, lazy_seen, dynamic_seen)
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
    stack = set()
    memo = {}
    for stem in got["every"]:
        path = os.path.join(root, stem + SUFFIX)
        if not os.path.isfile(path):
            continue
        scope, sub_h, sub_bad, parsed, sub_lazy, sub_dyn = helper_scope(
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
    return {"direct": direct, "helpers": helpers, "quieted": quieted,
            "unreadable": unreadable, "lazy_imports": lazy_seen,
            "dynamic": dynamic_seen, "unresolved": got["unresolved"],
            "module_bindings": got["module_bindings"],
            "local_bindings": got["local_bindings"]}


def audit(root=None, module=None):
    """Name every probe that quiets a seam, however the name was bound."""
    module = render_module() if module is None else module
    root = BASE if root is None else root
    if not os.path.isdir(root):
        raise AnnotatedScopeError(E_NO_ROOT, "not a directory: %s" % root)
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


def _row(name, verdict):
    return {"file": name, "verdict": verdict, "missing": [], "quieted": [],
            "required": [], "helpers": [], "direct": [], "lazy_imports": [],
            "dynamic": [], "unresolved": [], "module_bindings": [],
            "local_bindings": [], "unreadable_helpers": []}


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except AnnotatedScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise AnnotatedScopeError(
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
    lines = ["PROBE SEAM ANNOTATED CONSTANT SCOPE %s verdict=%s seams=%d "
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
                     " helpers=%s dynamic=%s local=%s%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]), len(row["direct"]),
                        ",".join(row["helpers"]) or "-",
                        ",".join(row["dynamic"]) or "-",
                        ",".join(row["local_bindings"]) or "-",
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
    except AnnotatedScopeError as exc:
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