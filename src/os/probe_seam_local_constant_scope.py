"""probe_seam_local_constant_scope - follow a name bound to a constant.

MEASURED at R2521 in the AC-PCB1 and AC-PCB4 legs of the constant-binding
face: that face reads its constant table off MODULE-level assignments only, so
a probe that declares its module name inside a function body reads
OUT-OF-SCOPE - `def run():` / `    name = "<stem>"` / `    return
importlib.import_module(name)` reads unresolved=['importlib.import_module:name']
quieted=0 while the same call one indentation level up reads COVERED. A
container reached through an attribute (`CFG.NAMES[0]`) was not resolved
either, because the table held literals rather than evaluated objects. Two
shapes between a literal and a computation were therefore still invisible, and
a stale probe written that way was never named.

This face closes both gaps with ONE reading and no second seam classifier:

  module_bindings(text)
      the module-level string constant table, unchanged from the shipped
      sibling law: a str literal, a tuple/list of str literals, a dict of str
      keys to str values, and (fixed point) a name whose value is such a
      lookup.
  local_bindings(text)
      the string constants declared INSIDE function bodies, read at CALL time
      off the probe own syntax tree with the same shapes. A name that is also
      bound to something that is not a constant anywhere in the tree, or bound
      to two different constants, is NOT in the table: an ambiguous name is
      never resolved.
  resolve_expression(expr_text, text, root)
      the stem a module-name expression really names, or None: a bound str
      name (local scope first, then module), a tuple element by constant index,
      a dict value by constant key, and a constant-key lookup into a module
      level container reached by a PLAIN ATTRIBUTE on a module bound in the
      same tree (`CFG.NAMES[0]`). Nothing here evaluates anything: a Call node
      is never resolved, so `build()[0]` stays unresolved and is named.
  dynamic_imports(text, root)
      the shipped dynamic face answers the shapes (its detection is the ONE
      shape classifier). Each call it could not resolve is offered to both
      constant tables; a resolvable one moves to RESOLVED carrying the binding
      label that resolved it (`NAME`, `CFG.NAMES`), the rest stay UNRESOLVED
      and are named rather than guessed at.
  helper_scope / probe_scope / audit / guard
      the same cycle-guarded same-root walk the shipped faces use, with the
      constant-aware dynamic stems feeding it, and the shipped registry's
      `quiets` as the ONE seam classifier. Each row names the helpers it was
      followed through, the dynamic shapes it took WITH their binding labels,
      the local bindings it read and the containers it resolved.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PLC5). No probe and
no helper is ever imported or run, which is why a stale probe is NAMED rather
than paid for.

Criteria AC-PLC1..AC-PLC6 were pinned in state/queue/tech.md:559 at R2521 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: only string constants are followed, only in
the probe own tree, only through assignments whose value is literally constant
- a name built by a call, a join, a format, an f-string or a comprehension is
never evaluated and never resolved. A container is only reached through a
plain attribute on a module bound in the same root at most one attribute deep,
so `pkg.CFG.NAMES[0]` and a container returned by a function are not resolved.
The walk follows local modules in the SAME root only, at most MAX_HOPS links
with a cycle guard. These shapes can UNDER-report a stale probe but can never
invent one. The walk shape is written here rather than injected into the
shipped constant-binding face, because parameterising a shipped module would
owe a battery in the same window; the seam CLASSIFIER is still the shipped
registry's single `quiets`, so no second classifier exists.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-LOCAL-COVERED)
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

LABEL = "os-probe-seam-local-constant-scope"
E_ARGS = "E_PLC_ARGS"
E_NO_ROOT = "E_PLC_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-LOCAL-COVERED"
SEAMS_STALE = "SEAMS-LOCAL-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)
STEM_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
MAX_HOPS = 8
BINDING_PASSES = 3

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

SHAPE_STR = "str"
SHAPE_TUPLE = "tuple"
SHAPE_DICT = "dict"


class LocalScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


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


def _tuple_values(node):
    """The strings a tuple/list literal holds, or None when not all strings."""
    if not isinstance(node, (ast.Tuple, ast.List)):
        return None
    values = []
    for element in node.elts:
        text = _str_constant(element)
        if text is None:
            return None
        values.append(text)
    return values


def _dict_values(node):
    """The str->str pairs a dict literal holds, or None when any key or value
    is not a string constant."""
    if not isinstance(node, ast.Dict):
        return None
    pairs = {}
    for key, value in zip(node.keys, node.values):
        if key is None:
            return None
        name = _str_constant(key)
        text = (None if isinstance(value, ast.Dict) else _str_constant(value))
        if name is None or text is None:
            return None
        pairs[name] = text
    return pairs


def _constant_entry(value):
    """The (shape, value) an assignment value literally is, or None."""
    text_value = _str_constant(value)
    if text_value is not None:
        return (SHAPE_STR, text_value)
    values = _tuple_values(value)
    if values is not None:
        return (SHAPE_TUPLE, values)
    pairs = _dict_values(value)
    if pairs is not None:
        return (SHAPE_DICT, pairs)
    return None


def _fill(table, pending):
    """Resolve pending names whose value is a constant-key lookup, in place."""
    for _ in range(BINDING_PASSES):
        moved = False
        rest = []
        for name, value in pending:
            got = _resolve_node(value, table, {}, None, None, None)
            if got is None:
                rest.append((name, value))
                continue
            table[name] = (SHAPE_STR, got[0])
            moved = True
        pending = rest
        if not moved:
            break
    return table


def module_bindings(text):
    """The module-level string constant table, off the probe own tree.

    Only assignments in the module body are read, and only values that are
    literally constant. A name bound to a call, a join, a format, an f-string
    or an imported constant is NOT in the table. Returns None when the source
    will not parse.
    """
    tree = _parse(text)
    if tree is None:
        return None
    table = {}
    pending = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        entry = _constant_entry(node.value)
        if entry is not None:
            table[target.id] = entry
            continue
        pending.append((target.id, node.value))
    return _fill(table, pending)


def _function_nodes(node):
    """Every function definition below a node, at any nesting level."""
    found = []
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append(child)
    return found


def local_bindings(text):
    """The string constants declared inside function bodies.

    Same shapes as the module table. A name that is ALSO bound to something
    that is not a constant anywhere in the tree, or bound to two different
    constants, is dropped: an ambiguous name is never resolved. Returns None
    when the source will not parse.
    """
    tree = _parse(text)
    if tree is None:
        return None
    seen = {}
    poisoned = set()
    for function in _function_nodes(tree):
        for node in ast.walk(function):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            entry = _constant_entry(node.value)
            if entry is None:
                poisoned.add(target.id)
                continue
            previous = seen.get(target.id)
            if previous is None:
                seen[target.id] = entry
            elif previous != entry:
                poisoned.add(target.id)
    for name in list(poisoned):
        seen.pop(name, None)
    return seen


def _bound_string(node, module_table, local_table):
    """The str-literal value a name is bound to, local scope first."""
    if not isinstance(node, ast.Name):
        return None
    entry = local_table.get(node.id) or module_table.get(node.id)
    if entry is None or entry[0] != SHAPE_STR:
        return None
    return entry[1]


def _entry_of(name, module_table, local_table):
    """The table entry a bare name holds, local scope first."""
    entry = local_table.get(name)
    if entry is not None:
        return entry
    return module_table.get(name)


def _element(entry, index_node, module_table, local_table):
    """The string a container entry holds at a constant index, or None."""
    if entry is None:
        return None
    if entry[0] == SHAPE_TUPLE:
        if not isinstance(index_node, ast.Constant):
            return None
        position = index_node.value
        if not isinstance(position, int) or isinstance(position, bool):
            return None
        if not -len(entry[1]) <= position < len(entry[1]):
            return None
        return entry[1][position]
    if entry[0] == SHAPE_DICT:
        key = _str_constant(index_node)
        if key is None:
            key = _bound_string(index_node, module_table, local_table)
        if key is None or key not in entry[1]:
            return None
        return entry[1][key]
    return None


def _container_attribute(node, root, memo):
    """The (MOD, ATTR, entry) a plain attribute on a module names, or None.

    The module must be a FILE IN THE SAME ROOT, so a container reached by a
    plain attribute is resolved off that module own tree; a call is never
    resolved, so `build()` and `pkg.CFG` stay unresolved.
    """
    if not isinstance(node, ast.Attribute):
        return None
    if not isinstance(node.value, ast.Name):
        return None
    if root is None:
        return None
    stem = node.value.id
    path = os.path.join(root, stem + SUFFIX)
    if not os.path.isfile(path):
        return None
    if stem not in memo:
        try:
            memo[stem] = module_bindings(_read(path))
        except OSError:
            memo[stem] = None
    table = memo[stem]
    if table is None:
        return None
    entry = table.get(node.attr)
    if entry is None:
        return None
    return stem, node.attr, entry


def _resolve_node(node, module_table, local_table, root, imports, memo):
    """The (stem, binding label) a module-name node names, or None."""
    if isinstance(node, ast.Call):
        return None
    if isinstance(node, ast.Constant):
        text = _str_constant(node)
        if text is None or not STEM_RE.match(text):
            return None
        return text.split(".")[0], ""
    if isinstance(node, ast.Name):
        entry = _entry_of(node.id, module_table, local_table)
        if entry is None or entry[0] != SHAPE_STR:
            return None
        if not STEM_RE.match(entry[1]):
            return None
        return entry[1].split(".")[0], node.id
    if isinstance(node, ast.Subscript):
        base = node.value
        if isinstance(base, ast.Name):
            entry = _entry_of(base.id, module_table, local_table)
            value = _element(entry, node.slice, module_table, local_table)
            if value is None or not STEM_RE.match(value):
                return None
            return value.split(".")[0], base.id
        if isinstance(base, ast.Attribute):
            got = _container_attribute(base, root, memo or {})
            if got is None:
                return None
            stem, attr, entry = got
            if imports is not None and stem not in imports:
                return None
            value = _element(entry, node.slice, module_table, local_table)
            if value is None or not STEM_RE.match(value):
                return None
            return value.split(".")[0], "%s.%s" % (stem, attr)
        return None
    if isinstance(node, ast.Attribute):
        got = _container_attribute(node, root, memo or {})
        if got is None:
            return None
        stem, attr, entry = got
        if imports is not None and stem not in imports:
            return None
        if entry[0] != SHAPE_STR or not STEM_RE.match(entry[1]):
            return None
        return entry[1].split(".")[0], "%s.%s" % (stem, attr)
    return None


def resolve_expression(expr_text, text, root=None, imports=None, memo=None):
    """The (stem, binding label) an expression text names, or None."""
    node = _parse_expr(expr_text)
    if node is None:
        return None
    module_table = module_bindings(text)
    local_table = local_bindings(text)
    if module_table is None or local_table is None:
        return None
    return _resolve_node(node, module_table, local_table, root, imports,
                         memo if memo is not None else {})


def dynamic_imports(text, root=None):
    """Constant-bound dynamic imports, on top of the shipped shape detector.

    Returns None when the source will not parse, else a dict with RESOLVED
    triples (shape, stem, binding label) in source order and UNRESOLVED labels
    ("shape:expr") for calls whose module name is still not a constant the
    probe own tree declares. The shipped dynamic face answers the shapes; this
    reading only adds the two constant tables, so no second shape classifier
    exists.
    """
    base = _dynamic_reader().dynamic_imports(text)
    if base is None:
        return None
    module_table = module_bindings(text)
    local_table = local_bindings(text)
    if module_table is None or local_table is None:
        return None
    imports = None
    got = _static_reader().imports_anywhere(text)
    if got is not None:
        imports = set(got[0])
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
    """Every local stem a source reaches, static plus constant-bound dynamic."""
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
    """Seams one helper quiets plus the helpers it reaches at any level.

    Returns (quieted, helpers, unreadable, parsed, lazy, dynamic), where
    dynamic pairs carry the binding label that resolved them, if any. Cycles
    contribute nothing new, a helper that will not parse is named rather than
    skipped, and results are memoised per audit.
    """
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
        raise LocalScopeError(E_NO_ROOT, "not a directory: %s" % root)
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
    except LocalScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise LocalScopeError(
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
    lines = ["PROBE SEAM LOCAL CONSTANT SCOPE %s verdict=%s seams=%d "
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
    except LocalScopeError as exc:
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