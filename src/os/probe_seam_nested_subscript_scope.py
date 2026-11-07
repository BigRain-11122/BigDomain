"""probe_seam_nested_subscript_scope - follow a CHAIN of constant subscripts.

MEASURED at R2533 on the shipped subscript face own readers, in that window
own legs:

  D = {"a": {"b": ("x",)}}
  for n in D["a"]["b"]:          -> refused=nested and NO key is named at all
  for n in D["a"][0]:            -> the same silence for a key followed by an
                                    index into a tuple

So a container TWO constant keys deep tells the operator nothing about which
step broke, even though the outer and the inner dict are both literal
constants.

This face reads those shapes ON TOP of the shipped subscript face:

  module_bindings(text, root) / local_bindings(text, root)
      the SHIPPED tables (subscript face, which extends the container-name,
      alias and annotated faces) EXTENDED - not replaced. Every earlier answer
      stands; this face adds only names bound by a for-loop whose iterable is
      a CHAIN of two or more constant subscripts, when the resolved container
      holds EXACTLY ONE element.
  nested_report(text, root)
      what this reading FOLLOWED (name -> the chain it took, with EVERY key),
      what it REFUSED (name -> a short ASCII reason carrying the HOP that
      broke), and the multi-target loops the shipped law already names.
  resolve_expression(expr_text, text, root, imports, memo)
      the shipped resolution law is asked FIRST, so every shape the subscript
      face already answered keeps its answer; only when it answers None is
      this table asked for a bare name.
  dynamic_imports / helper_scope / probe_scope / audit / guard
      the shipped dynamic shape detector and the shipped cycle-guarded walk,
      with this reading feeding it, and the shipped registry `quiets` as the
      ONE seam classifier.

Only STRING keys into a dict are followed. An integer step into a tuple is
NAMED as an index at its hop rather than followed, because an index selects a
position rather than a named slot. Nothing is evaluated anywhere.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PCNS5). No probe and
no helper is ever imported or run.

Criteria AC-PCNS1..AC-PCNS6 were pinned in state/queue/tech.md:571 at R2533 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: nothing is evaluated, so a step built by a
call, a format, an f-string, a comprehension or an arithmetic expression is
refused and named with its hop. A step that is not a literal constant is
refused by name rather than guessed - in particular a NAME bound to a
constant is NOT followed at a step, because the shipped law reads literals
only. Only a dict of constants in the SAME root is reached through an
attribute chain, gated by the probe own imports, and the walk follows local
modules in the same root only. Helper files are followed with the shipped
subscript walk, so a helper that itself nests two keys is a stated gap. These
shapes can UNDER-report a stale probe but can never invent one. The seam
CLASSIFIER is still the shipped registry single `quiets`.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-NESTED-SUBSCRIPT-COVERED)
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

LABEL = "os-probe-seam-nested-subscript-scope"
E_ARGS = "E_PCNS_ARGS"
E_NO_ROOT = "E_PCNS_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-NESTED-SUBSCRIPT-COVERED"
SEAMS_STALE = "SEAMS-NESTED-SUBSCRIPT-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)
STEM_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

TREE_STR = "str"
TREE_TUPLE = "tuple"
TREE_DICT = "dict"

MAX_DEPTH = 4
BINDING_PASSES = 8

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

CHAIN_PREFIX = "nsub"

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
REFUSED_KEY = "key"
REFUSED_INDEX = "index"
REFUSED_NESTED = "nested"


class NestedSubscriptScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base():
    """The shipped subscript face (tables, chain law, walk), imported once."""
    import probe_seam_subscript_container_scope
    return probe_seam_subscript_container_scope


def _container_face():
    """The shipped container-name face, one level below the subscript face."""
    return _base()._base()


def _alias():
    """The shipped alias face (slice label, expression parse, one law)."""
    return _base()._alias()


def _annotated():
    """The shipped annotated face (chain entry, element law, constant tree)."""
    return _base()._annotated()


def _registry():
    """The shipped seam reader, imported once (one classifier, no copy)."""
    return _base()._registry()


def _dynamic_reader():
    """The shipped dynamic shape reader (one shape classifier, no copy)."""
    return _base()._dynamic_reader()


def _static_reader():
    """The shipped static/lazy stem reader (one reader, no copy)."""
    return _base()._static_reader()


def render_module():
    """The shipped render, imported from src/sandbox (one reader, no copy)."""
    return _base().render_module()


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    return _base().seam_names(module)


def seam_owners(module=None):
    """Which module owns each seam, read off the seam object, never guessed."""
    return _base().seam_owners(module)


def _parse(text):
    return _base()._parse(text)


def _read(path):
    return _base()._read(path)


def _elements(tree):
    return _base()._elements(tree)


def _key_text(node):
    """A short ASCII label for a subscript key; a bare name is named as is."""
    return _base()._key_text(node)


def _chain_steps(node):
    """(base_node, [slice nodes]) for a chain of TWO or more subscripts."""
    if not isinstance(node, ast.Subscript):
        return None
    steps = []
    cursor = node
    while isinstance(cursor, ast.Subscript):
        steps.append(cursor.slice)
        cursor = cursor.value
    if len(steps) < 2:
        return None
    steps.reverse()
    return cursor, steps


def _step_word(step):
    """The word a step that cannot be followed is NAMED with."""
    if isinstance(step, (ast.ListComp, ast.SetComp, ast.DictComp,
                         ast.GeneratorExp)):
        return REFUSED_COMPREHENSION
    if isinstance(step, ast.Call):
        func = step.func
        if isinstance(func, ast.Attribute) and func.attr == "format":
            return REFUSED_FORMAT
        if isinstance(func, ast.Name) and func.id == "format":
            return REFUSED_FORMAT
        return REFUSED_CALL
    if isinstance(step, ast.Constant) and isinstance(step.value, int) \
            and not isinstance(step.value, bool):
        return REFUSED_INDEX
    return REFUSED_KEY


def _chain_iterable(node, module_table, local_table, literals, root, imports,
                    memo, depth=0):
    """(elements, chain) for a subscript CHAIN, or (None, hop-carrying reason)."""
    if depth > MAX_DEPTH:
        return None, REFUSED_DEPTH
    got = _chain_steps(node)
    if got is None:
        return None, None
    base_node, steps = got
    if isinstance(base_node, (ast.ListComp, ast.SetComp, ast.DictComp,
                              ast.GeneratorExp)):
        return None, "%s@hop1:?" % REFUSED_COMPREHENSION
    if isinstance(base_node, ast.Call):
        return None, "%s@hop1:%s" % (_step_word(base_node),
                                     _alias()._slice_label(base_node))
    tree, label = _base()._container_at(base_node, module_table, local_table,
                                        literals, root, imports, memo)
    if tree is None:
        return None, label
    chain = label
    for hop, step in enumerate(steps, 1):
        entry = _annotated()._str_constant(step)
        if entry is None:
            return None, "%s@hop%d:%s[%s]" % (_step_word(step), hop, chain,
                                              _key_text(step))
        if tree[0] != TREE_DICT:
            return None, "%s@hop%d:%s[%s]" % (REFUSED_SHAPE, hop, chain,
                                              repr(entry))
        value = tree[1].get(entry)
        if value is None:
            return None, "%s@hop%d:%s[%r]" % (REFUSED_KEY, hop, chain, entry)
        chain = "%s[%r]" % (chain, entry)
        tree = value
    elements, reason = _elements(tree)
    if elements is None:
        return None, "%s@hop%d:%s" % (reason or REFUSED_SHAPE, len(steps), chain)
    return elements, chain


def _for_chain(node):
    """The (target, iterable) a CHAIN subscript for-loop pins, or None."""
    if not isinstance(node, ast.For):
        return None
    if not isinstance(node.target, ast.Name):
        return None
    if _chain_steps(node.iter) is None:
        return None
    return node.target.id, node.iter


def _loop_targets(text):
    """Every name a for-loop in the source binds, at any depth."""
    tree = _parse(text)
    if tree is None:
        return None
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _candidates(text, inside_functions):
    """The (pairs, multi) this face may extend a table with, or None."""
    tree = _parse(text)
    if tree is None:
        return None
    pairs = []
    multi = []
    names = []
    if inside_functions:
        scopes = [node for node in ast.walk(tree)
                  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for function in scopes:
            for node in ast.walk(function):
                pair = _for_chain(node)
                if pair is not None:
                    pairs.append(pair)
                label = _base()._for_multi(node)
                if label is not None and label not in names:
                    names.append(label)
                    multi.append(label)
    else:
        top = ast.Module(body=list(tree.body), type_ignores=[])
        for node in _alias()._iter_nodes(top, skip_functions=True):
            pair = _for_chain(node)
            if pair is not None:
                pairs.append(pair)
            label = _base()._for_multi(node)
            if label is not None and label not in names:
                names.append(label)
                multi.append(label)
    return pairs, multi


def _resolve_group(nodes, module_table, local_table, literals, root, imports,
                   memo):
    """(element, chain, reason) for every iterable a target is bound to."""
    elements = []
    chain = None
    reason = None
    for node in nodes:
        got, cut = _chain_iterable(node, module_table, local_table, literals,
                                   root, imports, memo)
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
    """The extended tables plus what was followed, refused and multi-target."""
    base = _base()
    module_table = base.module_bindings(text, root)
    local_table = base.local_bindings(text, root)
    if module_table is None or local_table is None:
        return None
    module_table = dict(module_table)
    local_table = dict(local_table)
    imports = _alias()._imports_of(text)
    memo = {}
    followed = {"module": {}, "local": {}}
    refused = {"module": {}, "local": {}}
    containers = {"module": {}, "local": {}}
    multi = []
    targets = {"module": set(), "local": set()}
    module_literals = base._literal_table(text, False)
    if module_literals is None:
        return None
    for scope in ("module", "local"):
        table = module_table if scope == "module" else local_table
        other = local_table if scope == "module" else module_table
        got = _candidates(text, scope == "local")
        if got is None:
            return None
        pairs, labels = got
        inside = base._literal_table(text, scope == "local")
        if inside is None:
            return None
        literals = dict(module_literals)
        literals.update(inside)
        for name, _node in pairs:
            targets[scope].add(name)
        for label in labels:
            if label not in multi:
                multi.append(label)
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
                    groups[name], table, other, literals, root, imports, memo)
                if element is None:
                    rest.append(name)
                    continue
                table[name] = (TREE_STR, element)
                followed[scope][name] = "%s:%s@%s" % (CHAIN_PREFIX, name, chain)
                containers[scope][name] = {"chain": chain, "elements": 1}
                progress = True
            pending = rest
            if not progress:
                break
        for name in pending:
            if name in table:
                continue
            _el, _c, reason = _resolve_group(
                groups[name], table, other, literals, root, imports, memo)
            refused[scope][name] = reason or REFUSED_SHAPE
    brep = base.subscript_report(text, root)
    if brep is None:
        return None
    loops = _loop_targets(text)
    if loops is None:
        return None
    for name, chain in brep["followed"].items():
        if name not in loops:
            continue
        if name in module_table or name in local_table:
            continue
        scope = (brep["containers"].get(name) or {}).get("scope", "module")
        followed[scope].setdefault(name, chain)
    for name, reason in brep["refused"].items():
        if name not in loops:
            continue
        if name in module_table or name in local_table:
            continue
        if name in followed["module"] or name in followed["local"]:
            continue
        if name in refused["module"] or name in refused["local"]:
            continue
        scope = (brep["containers"].get(name) or {}).get("scope", "module")
        refused[scope][name] = reason
    for label in brep.get("multi", []):
        if label not in multi:
            multi.append(label)
    return module_table, local_table, followed, refused, containers, multi


def module_bindings(text, root=None):
    """The module-level constant table, shipped law plus chain shapes."""
    got = _extend(text, root)
    return None if got is None else got[0]


def local_bindings(text, root=None):
    """The function-body constant table, shipped law plus chain shapes."""
    got = _extend(text, root)
    return None if got is None else got[1]


def nested_report(text, root=None):
    """What this reading followed, refused, and named as multi-target."""
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
            "containers": containers, "multi": list(got[5])}


def resolve_expression(expr_text, text, root=None, imports=None, memo=None):
    """The (stem, binding label) an expression text names, or None.

    The shipped law of the subscript face is asked FIRST, so every shape it
    already answered keeps its answer; only when it answers None is this table
    asked for a bare name bound by a CHAIN subscript for-loop.
    """
    got = _base().resolve_expression(expr_text, text, root, imports, memo)
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
    """Chain-bound dynamic imports, on top of the shipped shape detector."""
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
            "followed": ext[2], "refused": ext[3], "containers": ext[4],
            "multi": ext[5]}


def _flat(pairs):
    """Flatten a scope->name->label map into a sorted label list."""
    row = []
    for scope in ("module", "local"):
        for name in sorted(pairs.get(scope, {})):
            row.append("%s:%s@%s" % (scope[0], name, pairs[scope][name]))
    return row


def _stems(text, root):
    """Every local stem a source reaches, static plus chain-bound dynamic."""
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
            "containers": dynamic["containers"], "multi": dynamic["multi"]}


def _dynamic_row(pairs):
    row = []
    for shape, stem, binding in pairs:
        label = "%s:%s" % (shape, stem)
        if binding:
            label = "%s@%s" % (label, binding)
        row.append(label)
    return row


def probe_scope(text, seams, root):
    """The seams a probe really quiets: its own plus every local hop."""
    base = _base()
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
    multi = list(got["multi"])
    stack = set()
    memo = {}
    for stem in got["every"]:
        path = os.path.join(root, stem + SUFFIX)
        if not os.path.isfile(path):
            continue
        (scope, _sub_h, sub_bad, parsed, sub_lazy, sub_dyn, sub_followed,
         sub_refused, sub_containers) = _container_face().helper_scope(
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
            _container_face()._merge(followed, sub_followed)
            _container_face()._merge(refused, sub_refused)
            _container_face()._merge(containers, sub_containers)
    return {"direct": direct, "helpers": helpers, "quieted": quieted,
            "unreadable": unreadable, "lazy_imports": lazy_seen,
            "dynamic": dynamic_seen, "unresolved": got["unresolved"],
            "module_bindings": got["module_bindings"],
            "local_bindings": got["local_bindings"],
            "followed": followed, "refused": refused,
            "containers": containers, "multi": multi}


def _carry(row, scope):
    row["lazy_imports"] = scope["lazy_imports"]
    row["dynamic"] = _dynamic_row(scope["dynamic"])
    row["unresolved"] = scope["unresolved"]
    row["module_bindings"] = scope["module_bindings"]
    row["local_bindings"] = scope["local_bindings"]
    row["unreadable_helpers"] = scope["unreadable"]
    row["containers"] = _flat(scope["followed"])
    row["container_refusals"] = _flat(scope["refused"])
    row["multi_targets"] = list(scope["multi"])


def _row(name, verdict):
    return {"file": name, "verdict": verdict, "missing": [], "quieted": [],
            "required": [], "helpers": [], "direct": [], "lazy_imports": [],
            "dynamic": [], "unresolved": [], "module_bindings": [],
            "local_bindings": [], "unreadable_helpers": [], "containers": [],
            "container_refusals": [], "multi_targets": []}


def audit(root=None, module=None):
    """Name every probe that quiets a seam, however its import was bound."""
    module = render_module() if module is None else module
    root = BASE if root is None else root
    if not os.path.isdir(root):
        raise NestedSubscriptScopeError(E_NO_ROOT, "not a directory: %s" % root)
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


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except NestedSubscriptScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise NestedSubscriptScopeError(
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
    lines = ["PROBE SEAM NESTED SUBSCRIPT %s verdict=%s seams=%d "
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
                     " helpers=%s dynamic=%s subscripts=%s refused=%s"
                     " multi=%s%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]), len(row["direct"]),
                        ",".join(row["helpers"]) or "-",
                        ",".join(row["dynamic"]) or "-",
                        ",".join(row["containers"]) or "-",
                        ",".join(row["container_refusals"]) or "-",
                        ",".join(row["multi_targets"]) or "-",
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
    except NestedSubscriptScopeError as exc:
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