"""probe_seam_nested_key_binding_scope - resolve a NAME step in a key chain.

MEASURED at R2535 on the shipped nested-subscript face own readers, in that
window own live legs:

  KEY = "b"
  D = {"a": {"b": ("x",)}}
  for n in D["a"][KEY]:          -> refused=key@hop2 and the step is named,
                                    but the honest answer IS derivable: KEY is
                                    a literal string constant in the same
                                    scope and the container holds EXACTLY one
                                    element, so D["a"]["b"] follows without
                                    evaluating anything.

The same silence hits an annotated binding (`KEY: str = "b"`) and a walrus
binding. An ambiguous name - bound twice with different values - is the one
case that must STAY refused.

This face reads those shapes ON TOP of the shipped nested-subscript face:

  module_bindings(text, root) / local_bindings(text, root)
      the SHIPPED tables EXTENDED - not replaced. Every earlier answer stands;
      this face adds only for-loop targets whose iterable is a CHAIN of two or
      more constant subscripts in which a step may be a NAME bound to a string
      constant, when the resolved container holds EXACTLY ONE element.
  nested_report(text, root)
      what this reading FOLLOWED (name -> the chain it took, carrying EVERY
      key as 'literal' or 'NAME=value' so the binding label travels with the
      value), what it REFUSED (name -> a short ASCII reason carrying the HOP
      that broke), and the multi-target loops the shipped law already names.
  resolve_expression / dynamic_imports / probe_scope / audit / guard
      the shipped law of the nested face asked FIRST, so every shape it
      already answered keeps its answer, and the shipped registry `quiets` as
      the ONE seam classifier.

Only STRING keys are followed. A step that is a NAME is resolved through the
constant tables at CALL time, and that name is announced on the row with the
value it carried; a name bound twice with different values, or bound to a
call, a format, a comprehension or an arithmetic expression, is NAMED at its
hop and never evaluated. An integer step into a tuple is NAMED as an index at
its hop rather than followed.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNKB5). No probe and
no helper is ever imported or run.

Criteria AC-PNKB1..AC-PNKB6 were pinned in state/queue/tech.md:573 at R2535 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: nothing is evaluated, so a step built by a
call, a format, an f-string, a comprehension or an arithmetic expression is
refused and named with its hop. Helper files are followed with the shipped
nested-subscript walk, so a helper that itself uses a NAME step is a stated
gap. These shapes can UNDER-report a stale probe but can never invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-NESTED-KEY-COVERED)
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

LABEL = "os-probe-seam-nested-key-binding-scope"
E_ARGS = "E_PNKB_ARGS"
E_NO_ROOT = "E_PNKB_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-NESTED-KEY-COVERED"
SEAMS_STALE = "SEAMS-NESTED-KEY-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)
STEM_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

TREE_STR = "str"
TREE_DICT = "dict"

MAX_DEPTH = 4
BINDING_PASSES = 8

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

CHAIN_PREFIX = "nkb"

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


class NestedKeyBindingScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base():
    """The shipped nested-subscript face, imported once."""
    import probe_seam_nested_subscript_scope
    return probe_seam_nested_subscript_scope


def _subscript():
    """The shipped subscript face, one level below the nested face."""
    return _base()._base()


def _container_face():
    """The shipped container-name face (helper walk, merge law)."""
    return _base()._container_face()


def _alias():
    """The shipped alias face (slice label, expression parse, imports)."""
    return _base()._alias()


def _annotated():
    """The shipped annotated face (str constant, chain entry, element law)."""
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
    return _base()._step_word(step)


def _value_word(node):
    """The short ASCII word for a NON-constant value a name is bound to."""
    if node is None:
        return REFUSED_SHAPE
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                         ast.GeneratorExp)):
        return REFUSED_COMPREHENSION
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "format":
            return REFUSED_FORMAT
        if isinstance(func, ast.Name) and func.id == "format":
            return REFUSED_FORMAT
        return REFUSED_CALL
    if isinstance(node, ast.JoinedStr):
        return REFUSED_FORMAT
    if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare)):
        return REFUSED_EXPRESSION
    if isinstance(node, ast.Subscript):
        return REFUSED_NESTED
    return REFUSED_SHAPE


def _bindings_of(text, name):
    """Every value a NAME is bound to in the source, module and functions.

    Returns a list of ('str', value) or ('word', reason) entries, in source
    order. A name bound twice with two different values is the caller's
    ambiguity case; this reader only reports what it saw.
    """
    tree = _parse(text)
    if tree is None:
        return []
    seen = []
    for node in ast.walk(tree):
        targets = []
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            targets = [node.targets[0]]
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        elif isinstance(node, ast.NamedExpr):
            targets = [node.target]
            value = node.value
        elif isinstance(node, ast.For):
            targets = [node.target]
            if isinstance(node.iter, (ast.Tuple, ast.List)) \
                    and len(node.iter.elts) == 1:
                value = node.iter.elts[0]
        for target in targets:
            if not isinstance(target, ast.Name) or target.id != name:
                continue
            if isinstance(value, ast.Constant) \
                    and isinstance(value.value, str):
                seen.append(("str", value.value))
            else:
                seen.append(("word", _value_word(value)))
    return seen


def _name_entry(name, text, module_table, local_table):
    """('ok', value, label) for a bound string constant, or ('refused', word).

    The bindings the SOURCE actually declares are read FIRST, so a name bound
    twice with different values is refused as ambiguous even though the shipped
    tables would have kept one of the two; the tables are asked only as a
    fallback for a name whose assignment this reader did not see.
    """
    seen = _bindings_of(text, name)
    values = [item[1] for item in seen if item[0] == "str"]
    words = [item[1] for item in seen if item[0] == "word"]
    distinct = []
    for value in values:
        if value not in distinct:
            distinct.append(value)
    if len(distinct) > 1 or (distinct and words):
        return "refused", REFUSED_AMBIGUOUS
    if distinct:
        return "ok", distinct[0], name
    if words:
        return "refused", words[0]
    entry = local_table.get(name) or module_table.get(name)
    if entry is not None and entry[0] == TREE_STR:
        return "ok", entry[1], name
    return "refused", REFUSED_NAME


def _step_entry(step, text, module_table, local_table):
    """('ok', value, chain piece) for a step, or ('refused', word, key text)."""
    if isinstance(step, ast.Constant) and isinstance(step.value, str):
        return "ok", step.value, "[%r]" % step.value
    if isinstance(step, ast.NamedExpr):
        target = step.target
        value = step.value
        if isinstance(target, ast.Name) and isinstance(value, ast.Constant) \
                and isinstance(value.value, str):
            return "ok", value.value, "[%s=%r]" % (target.id, value.value)
        return "refused", _value_word(value), _key_text(step)
    if isinstance(step, ast.Name):
        got = _name_entry(step.id, text, module_table, local_table)
        if got[0] == "ok":
            return "ok", got[1], "[%s=%r]" % (got[2], got[1])
        return "refused", got[1], step.id
    return "refused", _step_word(step), _key_text(step)


def _chain_iterable(node, text, module_table, local_table, literals, root,
                    imports, memo):
    """(elements, chain) for a chain whose steps may be NAMEs, or a reason."""
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
    tree, label = _subscript()._container_at(base_node, module_table,
                                             local_table, literals, root,
                                             imports, memo)
    if tree is None:
        return None, label
    chain = label
    for hop, step in enumerate(steps, 1):
        kind, value, piece = _step_entry(step, text, module_table,
                                        local_table)
        if kind != "ok":
            return None, "%s@hop%d:%s[%s]" % (value, hop, chain, piece)
        if tree[0] != TREE_DICT:
            return None, "%s@hop%d:%s%s" % (REFUSED_SHAPE, hop, chain, piece)
        held = tree[1].get(value)
        if held is None:
            return None, "%s@hop%d:%s%s" % (REFUSED_KEY, hop, chain, piece)
        chain = "%s%s" % (chain, piece)
        tree = held
    elements, reason = _elements(tree)
    if elements is None:
        return None, "%s@hop%d:%s" % (reason or REFUSED_SHAPE, len(steps),
                                      chain)
    return elements, chain


def _for_chain(node):
    """The (target, iterable) a CHAIN subscript for-loop pins, or None."""
    return _base()._for_chain(node)


def _loop_targets(text):
    return _base()._loop_targets(text)


def _candidates(text, inside_functions):
    return _base()._candidates(text, inside_functions)


def _resolve_group(nodes, text, module_table, local_table, literals, root,
                   imports, memo):
    """(element, chain, reason) for every iterable a target is bound to."""
    elements = []
    chain = None
    reason = None
    for node in nodes:
        got, cut = _chain_iterable(node, text, module_table, local_table,
                                   literals, root, imports, memo)
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
    base = _subscript()
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
                    groups[name], text, table, other, literals, root, imports,
                    memo)
                if element is None:
                    rest.append(name)
                    continue
                table[name] = (TREE_STR, element)
                followed[scope][name] = "%s:%s@%s" % (CHAIN_PREFIX, name,
                                                     chain)
                containers[scope][name] = {"chain": chain, "elements": 1}
                progress = True
            pending = rest
            if not progress:
                break
        for name in pending:
            if name in table:
                continue
            _el, _c, reason = _resolve_group(
                groups[name], text, table, other, literals, root, imports,
                memo)
            refused[scope][name] = reason or REFUSED_SHAPE
    return module_table, local_table, followed, refused, containers, multi


def module_bindings(text, root=None):
    """The module-level constant table, shipped law plus named-step chains."""
    got = _extend(text, root)
    return None if got is None else got[0]


def local_bindings(text, root=None):
    """The function-body constant table, shipped law plus named-step chains."""
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
    """The shipped nested-face law first; every earlier answer stands."""
    return _base().resolve_expression(expr_text, text, root, imports, memo)


def _name_stem(expr_text, ext):
    """The (stem, name) an expression text names through THIS face tables."""
    node = _alias()._parse_expr(expr_text)
    if node is None or not isinstance(node, ast.Name):
        return None
    entry = ext[1].get(node.id) or ext[0].get(node.id)
    if entry is None or entry[0] != TREE_STR:
        return None
    stem = entry[1].split(".")[0]
    if not STEM_RE.match(stem):
        return None
    return stem, node.id


def dynamic_imports(text, root=None):
    """Chain-bound dynamic imports with NAMED steps, on the shipped detector."""
    base = _base().dynamic_imports(text, root)
    if base is None:
        return None
    ext = _extend(text, root)
    if ext is None:
        return None
    resolved = [(shape, stem, binding)
                for shape, stem, binding in base["resolved"]]
    unresolved = []
    for label in base["unresolved"]:
        shape, _sep, expr = label.partition(":")
        got = _name_stem(expr, ext)
        if got is None:
            unresolved.append(label)
            continue
        triple = (shape, got[0], got[1])
        if triple not in resolved:
            resolved.append(triple)
    return {"resolved": resolved, "unresolved": unresolved,
            "module_bindings": sorted(ext[0]),
            "local_bindings": sorted(ext[1]),
            "followed": ext[2], "refused": ext[3], "containers": ext[4],
            "multi": ext[5]}


def _flat(pairs):
    row = []
    for scope in ("module", "local"):
        for name in sorted(pairs.get(scope, {})):
            row.append("%s:%s@%s" % (scope[0], name, pairs[scope][name]))
    return row


def _dynamic_row(pairs):
    return _base()._dynamic_row(pairs)


def probe_scope(text, seams, root):
    """The seams a probe really quiets: its own plus every local hop."""
    base = _subscript()
    direct = _registry().quiets(text, seams)
    got = dynamic_imports(text, root)
    if direct is None or got is None:
        return None
    static = _static_reader().imports_anywhere(text)
    if static is None:
        return None
    every, _top, lazy = static
    stems = list(every)
    for _shape, stem, _binding in got["resolved"]:
        if stem not in stems:
            stems.append(stem)
    quieted = list(direct)
    helpers = []
    unreadable = []
    lazy_seen = list(lazy)
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
    for stem in stems:
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
        raise NestedKeyBindingScopeError(E_NO_ROOT,
                                        "not a directory: %s" % root)
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
    except NestedKeyBindingScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise NestedKeyBindingScopeError(
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
    lines = ["PROBE SEAM NESTED KEY %s verdict=%s seams=%d probes=%d "
             "covered=%d missing=%d out_of_scope=%d unreadable=%d "
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
                     " helpers=%s dynamic=%s keys=%s refused=%s"
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
    except NestedKeyBindingScopeError as exc:
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