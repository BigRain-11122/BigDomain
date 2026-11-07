"""probe_seam_for_container_name - read a for-loop over a NAMED container.

MEASURED at R2529 on the shipped alias-expression face own readers, in that
window own legs:

  NAMES = ("x",)
  for name in NAMES:              -> local_bindings {} for name and the row
                                    names NO shape at all, so a loop over a
                                    container NAME still reads silent even
                                    when the container itself is in the table
  for name in pkg.NAMES:          -> the same shape one attribute hop out
  NAMES = ("a", "b")
  for name in NAMES:              -> reads nothing and says nothing, where the
                                    honest answer is AMBIGUOUS rather than the
                                    first element

This face reads that ONE shape and no second classifier:

  module_bindings(text, root) / local_bindings(text, root)
      the SHIPPED tables (alias-expression face, which extends the annotated
      and local-constant faces) EXTENDED - not replaced. Every earlier answer
      stands; this face adds only names bound by a for-loop whose iterable is
      a NAME, an attribute chain into a same-root module, or a container
      literal, when that iterable resolves to EXACTLY ONE element.
  container_report(text, root)
      what this reading FOLLOWED (name -> the container chain it took) and
      what it REFUSED (name -> a short ASCII reason, with the hop when the
      chain broke). A refused shape is published, never silently absent, and
      nothing is ever evaluated.
  resolve_expression(expr_text, text, root, imports, memo)
      the shipped resolution law is asked FIRST, so a plain name, a tuple
      element, a dict value, a subscript alias, an annotated alias and one
      attribute hop keep exactly the shipped answer. Only when it answers
      None is the extended table asked for a bare name.
  dynamic_imports(text, root)
      the SHIPPED dynamic face answers the shapes (its detection is the ONE
      shape classifier). Each call it could not resolve is offered to this
      reading, so a container-bound name moves to RESOLVED carrying the
      binding label; the rest stay UNRESOLVED and named.
  helper_scope / probe_scope / audit / guard
      the same cycle-guarded same-root walk the shipped faces use, with this
      reading feeding it, and the shipped registry `quiets` as the ONE seam
      classifier. Each row carries the container chains it followed and the
      shapes it refused.

Read-only: nothing is written, no file is opened for writing, and every
digest this reading touches is unchanged across a full audit (AC-PCAF5). No
probe and no helper is ever imported or run, which is why a stale probe is
NAMED rather than paid for.

Criteria AC-PCAF1..AC-PCAF6 were pinned in state/queue/tech.md:567 at R2529 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: nothing is evaluated, so a container built
by a call, a join, an f-string, a comprehension or an arithmetic expression is
refused and named rather than resolved. A container reached through a
subscript on a name (a dict of tuples) is refused by name, not followed. A
multi-element container is AMBIGUOUS and never resolved to its first element.
Only module-level containers of the SAME root are reached through an
attribute chain, gated by the probe own imports. Iterating a str is refused
because a character is not a module. These shapes can UNDER-report a stale
probe but can never invent one. The walk shape is written here rather than
injected into the shipped alias face, because parameterising a shipped module
would owe a battery in the same window; the tables and the resolution law are
the shipped ones EXTENDED at call time, and the seam CLASSIFIER is still the
shipped registry single `quiets`.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-CONTAINER-COVERED)
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

LABEL = "os-probe-seam-for-container-name"
E_ARGS = "E_PCFN_ARGS"
E_NO_ROOT = "E_PCFN_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-CONTAINER-COVERED"
SEAMS_STALE = "SEAMS-CONTAINER-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)
STEM_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

TREE_STR = "str"
TREE_TUPLE = "tuple"
TREE_DICT = "dict"

MAX_HOPS = 8
MAX_DEPTH = 4
BINDING_PASSES = 8

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

REFUSED_AMBIGUOUS = "ambiguous"
REFUSED_EMPTY = "empty"
REFUSED_STRING = "string"
REFUSED_CALL = "call"
REFUSED_FORMAT = "format"
REFUSED_EXPRESSION = "expression"
REFUSED_COMPREHENSION = "comprehension"
REFUSED_SHAPE = "shape"
REFUSED_DEPTH = "depth"
REFUSED_NAME = "unresolved-name"
REFUSED_ATTR = "attribute"
REFUSED_SLICE = "subscript"
REFUSED_NESTED = "nested"


class ContainerNameError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _alias():
    """The shipped alias-expression face (tables, law, walk), imported once."""
    import probe_seam_alias_expression_scope
    return probe_seam_alias_expression_scope


def _annotated():
    """The shipped annotated-constant face (chain entry law, no copy)."""
    return _alias()._annotated_reader()


def _registry():
    """The shipped seam reader, imported once (one classifier, no copy)."""
    import probe_seam_registry
    return probe_seam_registry


def _dynamic_reader():
    """The shipped dynamic shape reader (one shape classifier, no copy)."""
    return _alias()._dynamic_reader()


def _static_reader():
    """The shipped static/lazy stem reader (one reader, no copy)."""
    return _alias()._static_reader()


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
    return _annotated()._parse(text)


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _chain_text(node):
    """The dotted text an attribute chain spells, or None when it is no chain."""
    parts = _annotated()._chain_parts(node)
    if parts is None:
        return None
    stem, attributes = parts
    return ".".join([stem] + list(reversed(attributes)))


def _raw(element):
    """The raw string an element holds, whichever tree law produced it.

    MEASURED at R2531: the two shipped producers disagree - the alias face
    own `_tree_of` publishes raw strings inside a container, while the
    annotated face `_module_trees` publishes nested (type, value) trees for
    the same literal. Both are accepted here, and anything that is not a
    string element is refused, so a nested container is named rather than
    flattened.
    """
    if isinstance(element, str):
        return element
    if isinstance(element, tuple) and len(element) == 2:
        if element[0] == TREE_STR and isinstance(element[1], str):
            return element[1]
        if element[0] in (TREE_TUPLE, TREE_DICT):
            return None
    return None


def _elements(tree):
    """The elements a constant tree yields when iterated, or (None, reason)."""
    if tree is None:
        return None, REFUSED_SHAPE
    if tree[0] == TREE_STR:
        return None, REFUSED_STRING
    if tree[0] == TREE_TUPLE:
        items = list(tree[1])
    elif tree[0] == TREE_DICT:
        items = list(tree[1].keys())
    else:
        return None, REFUSED_SHAPE
    values = []
    for item in items:
        raw = _raw(item)
        if raw is None:
            return None, REFUSED_NESTED
        values.append(raw)
    if not values:
        return None, REFUSED_EMPTY
    return values, None


def _iterable(node, module_table, local_table, root, imports, memo, depth=0):
    """(elements, chain label) for a for-loop iterable, or (None, reason)."""
    if depth > MAX_DEPTH:
        return None, REFUSED_DEPTH
    if isinstance(node, ast.Name):
        entry = local_table.get(node.id)
        if entry is None:
            entry = module_table.get(node.id)
        if entry is None:
            return None, REFUSED_NAME
        elements, reason = _elements(entry)
        if elements is None:
            return None, reason
        return elements, node.id
    if isinstance(node, ast.Attribute):
        got = _annotated()._chain_entry(node, root, imports, memo)
        if got is None:
            return None, "%s:%s" % (REFUSED_ATTR,
                                    _chain_text(node) or "?")
        tree, label = got
        elements, reason = _elements(tree)
        if elements is None:
            return None, "%s:%s" % (reason, label)
        return elements, label
    if isinstance(node, ast.Subscript):
        base = node.value
        if isinstance(base, (ast.Name, ast.Attribute)):
            text = base.id if isinstance(base, ast.Name) else (
                _chain_text(base) or "?")
            return None, "%s:%s" % (REFUSED_SLICE, text)
        return None, REFUSED_SLICE
    if isinstance(node, (ast.Tuple, ast.List, ast.Dict)):
        tree, cut = _alias()._tree_of(node, module_table, local_table, root,
                                      imports, memo, depth)
        if tree is None:
            return None, cut
        elements, reason = _elements(tree)
        if elements is None:
            return None, reason
        return elements, "+".join(cut) or "literal"
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Attribute) and function.attr in (
                "format", "join", "replace", "lower", "upper", "strip",
                "lstrip", "rstrip"):
            return None, REFUSED_FORMAT
        return None, REFUSED_CALL
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return None, REFUSED_STRING
        return None, REFUSED_SHAPE
    if isinstance(node, ast.JoinedStr):
        return None, REFUSED_FORMAT
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                         ast.GeneratorExp)):
        return None, REFUSED_COMPREHENSION
    if isinstance(node, (ast.BinOp, ast.IfExp, ast.BoolOp, ast.Compare)):
        return None, REFUSED_EXPRESSION
    return None, REFUSED_SHAPE


def _for_container(node):
    """The (target, iterable) a container for-loop pins, or None.

    A literal single-element tuple or list is the shipped alias face own
    shape and is left to it; this face takes every other iterable of a
    single-target for-loop.
    """
    if not isinstance(node, ast.For):
        return None
    if not isinstance(node.target, ast.Name):
        return None
    if isinstance(node.iter, (ast.Tuple, ast.List)):
        return None
    return node.target.id, node.iter


def _candidates(text, inside_functions):
    """Every (name, iterable_node) this face may extend a table with."""
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
                pair = _for_container(node)
                if pair is not None:
                    found.append(pair)
    else:
        top = ast.Module(body=list(tree.body), type_ignores=[])
        for node in _alias()._iter_nodes(top, skip_functions=True):
            pair = _for_container(node)
            if pair is not None:
                found.append(pair)
    return found


def _resolve_group(nodes, module_table, local_table, root, imports, memo):
    """(element, chain, reason) for every iterable a target is bound to.

    One element and every node agrees = resolved. A node that refuses, or two
    nodes that disagree, = refused with a reason, never guessed.
    """
    elements = []
    chain = None
    reason = None
    for node in nodes:
        got, cut = _iterable(node, module_table, local_table, root, imports,
                             memo)
        if got is None:
            reason = reason or cut
            continue
        if len(got) != 1:
            reason = reason or REFUSED_AMBIGUOUS
            continue
        elements.append(got[0])
        chain = chain or cut
    if reason is not None:
        return None, None, reason
    if not elements:
        return None, None, REFUSED_SHAPE
    first = elements[0]
    for other in elements[1:]:
        if other != first:
            return None, None, REFUSED_AMBIGUOUS
    return first, chain, None


def _extend(text, root=None):
    """The extended tables plus what was followed, refused and counted.

    Returns (module_table, local_table, followed, refused, containers) or None
    when the source will not parse. The shipped tables are asked FIRST and a
    name they already answer is never overwritten, so every earlier answer
    stands.
    """
    base = _alias()._scopes(text, root)
    if base is None:
        return None
    module_table = dict(base[0])
    local_table = dict(base[1])
    imports = _alias()._imports_of(text)
    memo = {}
    followed = {"module": dict(base[2]["module"]),
                "local": dict(base[2]["local"])}
    refused = {"module": dict(base[3]["module"]),
               "local": dict(base[3]["local"])}
    containers = {"module": {}, "local": {}}
    for scope in ("module", "local"):
        table = module_table if scope == "module" else local_table
        other = local_table if scope == "module" else module_table
        pairs = _candidates(text, scope == "local")
        if pairs is None:
            return None
        groups = {}
        order = []
        for name, node in pairs:
            if name not in groups:
                groups[name] = []
                order.append(name)
            groups[name].append(node)
        pending = [name for name in order if name not in table]
        for _step in range(BINDING_PASSES):
            progress = False
            rest = []
            for name in pending:
                if name in table:
                    continue
                element, chain, reason = _resolve_group(
                    groups[name], table, other, root, imports, memo)
                if element is None:
                    rest.append(name)
                    continue
                table[name] = (TREE_STR, element)
                followed[scope][name] = "for:%s@%s" % (name, chain)
                containers[scope][name] = {"chain": chain, "elements": 1}
                progress = True
            pending = rest
            if not progress:
                break
        for name in pending:
            if name in table:
                continue
            _e, _c, reason = _resolve_group(
                groups[name], table, other, root, imports, memo)
            refused[scope][name] = reason or REFUSED_SHAPE
    return module_table, local_table, followed, refused, containers


def module_bindings(text, root=None):
    """The module-level constant table, shipped law plus container names."""
    got = _extend(text, root)
    if got is None:
        return None
    return got[0]


def local_bindings(text, root=None):
    """The function-body constant table, shipped law plus container names."""
    got = _extend(text, root)
    if got is None:
        return None
    return got[1]


def container_report(text, root=None):
    """What this reading followed and refused, and the containers it counted."""
    got = _extend(text, root)
    if got is None:
        return None
    followed = {}
    refused = {}
    containers = {}
    for scope in ("module", "local"):
        for name, chain in got[2][scope].items():
            followed[name] = chain
        for name, reason in got[3][scope].items():
            refused[name] = reason
        for name, info in got[4][scope].items():
            containers[name] = dict(info, scope=scope)
    return {"followed": followed, "refused": refused,
            "containers": containers}


def resolve_expression(expr_text, text, root=None, imports=None, memo=None):
    """The (stem, binding label) an expression text names, or None.

    The shipped law is asked FIRST, so every shape it already answered keeps
    its answer; only when it answers None is the extended table asked for a
    bare name bound by a container for-loop.
    """
    got = _alias().resolve_expression(expr_text, text, root, imports, memo)
    if got is not None:
        return got
    node = _alias()._parse_expr(expr_text)
    if node is None or not isinstance(node, ast.Name):
        return None
    ext = _extend(text, root)
    if ext is None:
        return None
    entry = ext[1].get(node.id) or ext[0].get(node.id)
    if entry is None or entry[0] != TREE_STR:
        return None
    stem = entry[1].split(".")[0]
    if not STEM_RE.match(stem):
        return None
    return stem, node.id


def dynamic_imports(text, root=None):
    """Container-bound dynamic imports, on top of the shipped shape detector.

    Returns None when the source will not parse, else a dict with RESOLVED
    triples (shape, stem, binding label) in source order and UNRESOLVED labels
    ("shape:expr") for calls this reading still cannot follow, plus the
    container shapes it followed and refused so the row can carry them. The
    shipped dynamic face answers the shapes; this reading only adds the
    extended table, so no second shape classifier exists.
    """
    base = _dynamic_reader().dynamic_imports(text)
    if base is None:
        return None
    ext = _extend(text, root)
    if ext is None:
        return None
    imports = _alias()._imports_of(text)
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
            "module_bindings": sorted(ext[0]),
            "local_bindings": sorted(ext[1]),
            "followed": ext[2], "refused": ext[3], "containers": ext[4]}


def _flat(pairs):
    """Flatten a scope->name->label map into a sorted label list."""
    row = []
    for scope in ("module", "local"):
        for name in sorted(pairs.get(scope, {})):
            row.append("%s:%s@%s" % (scope[0], name, pairs[scope][name]))
    return row


def _stems(text, root):
    """Every local stem a source reaches, static plus container-bound dynamic."""
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
            "followed": dynamic["followed"], "refused": dynamic["refused"],
            "containers": dynamic["containers"]}


def _dynamic_row(pairs):
    row = []
    for shape, stem, binding in pairs:
        label = "%s:%s" % (shape, stem)
        if binding:
            label = "%s@%s" % (label, binding)
        row.append(label)
    return row


def _empty_shapes():
    return {"module": {}, "local": {}}


def _merge(target, source):
    for scope in ("module", "local"):
        for name, value in source.get(scope, {}).items():
            target[scope].setdefault(name, value)


def _empty_result(bad):
    return (None, [], [bad], False, [], [], _empty_shapes(), _empty_shapes(),
            _empty_shapes())


def helper_scope(path, seams, stack, memo, root):
    """Seams one helper quiets plus the helpers it reaches at any level."""
    key = os.path.abspath(path)
    if key in memo:
        return memo[key]
    if key in stack:
        return ([], [], [], True, [], [], _empty_shapes(), _empty_shapes(),
                _empty_shapes())
    stack.add(key)
    try:
        text = _read(path)
    except OSError:
        result = _empty_result(os.path.basename(path))
        memo[key] = result
        stack.discard(key)
        return result
    direct = _registry().quiets(text, seams)
    got = _stems(text, root)
    if direct is None or got is None:
        result = _empty_result(os.path.basename(path))
        memo[key] = result
        stack.discard(key)
        return result
    quieted = list(direct)
    helpers = []
    unreadable = []
    lazy_seen = list(got["lazy"])
    dynamic_seen = list(got["resolved"])
    followed = {"module": dict(got["followed"]["module"]),
                "local": dict(got["followed"]["local"])}
    refused = {"module": dict(got["refused"]["module"]),
               "local": dict(got["refused"]["local"])}
    containers = {"module": dict(got["containers"]["module"]),
                  "local": dict(got["containers"]["local"])}
    if len(stack) <= MAX_HOPS:
        for stem in got["every"]:
            sub = os.path.join(os.path.dirname(path), stem + SUFFIX)
            if not os.path.isfile(sub):
                continue
            (sub_q, _sub_h, sub_bad, sub_ok, sub_lazy, sub_dyn, sub_followed,
             sub_refused, sub_containers) = helper_scope(sub, seams, stack,
                                                          memo, root)
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
                _merge(followed, sub_followed)
                _merge(refused, sub_refused)
                _merge(containers, sub_containers)
    result = (quieted, helpers, unreadable, True, lazy_seen, dynamic_seen,
              followed, refused, containers)
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
    followed = {"module": dict(got["followed"]["module"]),
                "local": dict(got["followed"]["local"])}
    refused = {"module": dict(got["refused"]["module"]),
               "local": dict(got["refused"]["local"])}
    containers = {"module": dict(got["containers"]["module"]),
                  "local": dict(got["containers"]["local"])}
    stack = set()
    memo = {}
    for stem in got["every"]:
        path = os.path.join(root, stem + SUFFIX)
        if not os.path.isfile(path):
            continue
        (scope, _sub_h, sub_bad, parsed, sub_lazy, sub_dyn, sub_followed,
         sub_refused, sub_containers) = helper_scope(path, seams, stack,
                                                     memo, root)
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
            _merge(followed, sub_followed)
            _merge(refused, sub_refused)
            _merge(containers, sub_containers)
    return {"direct": direct, "helpers": helpers, "quieted": quieted,
            "unreadable": unreadable, "lazy_imports": lazy_seen,
            "dynamic": dynamic_seen, "unresolved": got["unresolved"],
            "module_bindings": got["module_bindings"],
            "local_bindings": got["local_bindings"],
            "followed": followed, "refused": refused,
            "containers": containers}


def audit(root=None, module=None):
    """Name every probe that quiets a seam, however its import was bound."""
    module = render_module() if module is None else module
    root = BASE if root is None else root
    if not os.path.isdir(root):
        raise ContainerNameError(E_NO_ROOT, "not a directory: %s" % root)
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
    row["containers"] = _flat(scope["followed"])
    row["container_refusals"] = _flat(scope["refused"])
    row["container_counts"] = sorted(
        "%s:%s=%d" % (letter, name, info.get("elements", 0))
        for letter, names in (("m", scope["containers"]["module"]),
                              ("l", scope["containers"]["local"]))
        for name, info in names.items())


def _row(name, verdict):
    return {"file": name, "verdict": verdict, "missing": [], "quieted": [],
            "required": [], "helpers": [], "direct": [], "lazy_imports": [],
            "dynamic": [], "unresolved": [], "module_bindings": [],
            "local_bindings": [], "unreadable_helpers": [], "containers": [],
            "container_refusals": [], "container_counts": []}


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ContainerNameError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise ContainerNameError(
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
    lines = ["PROBE SEAM FOR CONTAINER NAME %s verdict=%s seams=%d "
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
                     " helpers=%s dynamic=%s containers=%s refused=%s%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]), len(row["direct"]),
                        ",".join(row["helpers"]) or "-",
                        ",".join(row["dynamic"]) or "-",
                        ",".join(row["containers"]) or "-",
                        ",".join(row["container_refusals"]) or "-",
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
    except ContainerNameError as exc:
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