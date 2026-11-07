"""probe_seam_constant_binding_scope - follow a name bound to a constant.

MEASURED at R2519 in the AC-PDI1 and AC-PDI4 fixtures of the dynamic face: a
probe that binds the module name to a module-level string constant and then
imports it reads OUT-OF-SCOPE with the call named unresolved - a module-level
`NAME = "<stem>"` followed by `importlib.import_module(NAME)` reads
unresolved=['importlib.import_module:NAME'] quieted=0, while the same call with
the literal in the argument position reads COVERED. The one shape between a
literal and a computation was still invisible, so a stale probe written that
way was never named.

This face closes that gap with ONE reading and no second seam classifier:

  constant_bindings(text)
      the STRING CONSTANT table the probe own tree declares, read at CALL time
      and only from module-level assignments: a str literal, a tuple or list
      of str literals, a dict of str keys to str values, and (fixed point) a
      name whose value is a constant-key lookup into that table. A name bound
      to a computation - a call, a join, a format, an f-string, an imported
      constant - is NOT in the table and is therefore never resolved.
  resolve_expression(expr_text, bindings)
      the stem a module-name expression really names, or None: a bound str
      name, a tuple element by constant integer index, a dict value by
      constant str key. Nothing here evaluates anything.
  dynamic_imports(text)
      the shipped dynamic face answers first (its shape detection is the ONE
      shape classifier). Each call it could not resolve is then offered to the
      constant table: a resolvable one moves to RESOLVED and carries the
      binding name that resolved it; the rest stay UNRESOLVED and are named
      rather than guessed at.
  helper_scope / probe_scope / audit / guard
      the same cycle-guarded same-root walk the shipped faces use, with the
      constant-aware dynamic stems feeding it, and the shipped registry's
      `quiets` as the ONE seam classifier. Each row names the helpers it was
      followed through, the dynamic shapes it took WITH the binding names, and
      the constant-bound calls it still could not resolve.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PCB5). No probe and
no helper is ever imported or run, which is why a stale probe is NAMED rather
than paid for.

Criteria AC-PCB1..AC-PCB6 were pinned in state/queue/tech.md:557 at R2519 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: the binding table is module-level only, so a
constant declared inside a function body is not resolved; a container reached
through an attribute or a call is not resolved; a module name computed at run
time from a real value is never evaluated and never resolved. The walk follows
local modules in the SAME root only, at most MAX_HOPS links with a cycle
guard. These shapes can UNDER-report a stale probe but can never invent one.
The walk shape is written here rather than injected into the shipped dynamic
face, because parameterising a shipped module would owe a battery in the same
window; the seam CLASSIFIER is still the shipped registry's single `quiets`,
so no second classifier exists.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-CONSTANT-COVERED)
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

LABEL = "os-probe-seam-constant-binding-scope"
E_ARGS = "E_PCB_ARGS"
E_NO_ROOT = "E_PCB_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_COVERED = "SEAMS-CONSTANT-COVERED"
SEAMS_STALE = "SEAMS-CONSTANT-STALE"

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


class ConstantScopeError(Exception):
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


def constant_bindings(text):
    """The string constant table a source declares, off its OWN tree.

    Only module-level assignments are read, and only values that are literally
    constant: a str literal, a tuple/list of str literals, a dict of str keys
    to str values, and - by fixed point - a name whose value is a constant-key
    lookup into the table already read. A name bound to a call, a join, a
    format, an f-string or an imported constant is NOT in the table, so such a
    name is never resolved. Returns None when the source will not parse.
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
        value = node.value
        text_value = _str_constant(value)
        if text_value is not None:
            table[target.id] = (SHAPE_STR, text_value)
            continue
        values = _tuple_values(value)
        if values is not None:
            table[target.id] = (SHAPE_TUPLE, values)
            continue
        pairs = _dict_values(value)
        if pairs is not None:
            table[target.id] = (SHAPE_DICT, pairs)
            continue
        pending.append((target.id, value))
    for _ in range(BINDING_PASSES):
        moved = False
        rest = []
        for name, value in pending:
            got = _resolve_node(value, table)
            if got is None:
                rest.append((name, value))
                continue
            table[name] = (SHAPE_STR, got[0])
            moved = True
        pending = rest
        if not moved:
            break
    return table


def _bound_string(node, bindings):
    """The str-literal value a name is bound to, or None."""
    if not isinstance(node, ast.Name):
        return None
    entry = bindings.get(node.id)
    if entry is None or entry[0] != SHAPE_STR:
        return None
    return entry[1]


def _resolve_node(node, bindings):
    """The (stem, binding name) a module-name node names, or None."""
    if isinstance(node, ast.Name):
        entry = bindings.get(node.id)
        if entry is None or entry[0] != SHAPE_STR:
            return None
        stem = entry[1].split(".")[0]
        if not STEM_RE.match(entry[1]):
            return None
        return stem, node.id
    if isinstance(node, ast.Subscript):
        base = node.value
        if not isinstance(base, ast.Name):
            return None
        entry = bindings.get(base.id)
        if entry is None:
            return None
        index = node.slice
        if entry[0] == SHAPE_TUPLE:
            if not isinstance(index, ast.Constant):
                return None
            position = index.value
            if not isinstance(position, int) or isinstance(position, bool):
                return None
            if not -len(entry[1]) <= position < len(entry[1]):
                return None
            value = entry[1][position]
        elif entry[0] == SHAPE_DICT:
            key = _str_constant(index)
            if key is None:
                key = _bound_string(index, bindings)
            if key is None or key not in entry[1]:
                return None
            value = entry[1][key]
        else:
            return None
        if not STEM_RE.match(value):
            return None
        return value.split(".")[0], base.id
    return None


def resolve_expression(expr_text, bindings):
    """The (stem, binding name) an expression text names, or None."""
    node = _parse_expr(expr_text)
    if node is None:
        return None
    return _resolve_node(node, bindings)


def dynamic_imports(text):
    """Constant-bound dynamic imports, on top of the shipped shape detector.

    Returns None when the source will not parse, else a dict with RESOLVED
    triples (shape, stem, binding name) in source order and UNRESOLVED labels
    ("shape:expr") for calls whose module name is still not a constant the
    probe own tree declares. The shipped dynamic face answers the shapes; this
    reading only adds the constant table, so no second shape classifier exists.
    """
    base = _dynamic_reader().dynamic_imports(text)
    if base is None:
        return None
    bindings = constant_bindings(text)
    if bindings is None:
        return None
    resolved = [(shape, stem, "") for shape, stem in base["resolved"]]
    unresolved = []
    for label in base["unresolved"]:
        shape, _sep, expr = label.partition(":")
        got = resolve_expression(expr, bindings)
        if got is None:
            unresolved.append(label)
            continue
        stem, binding = got
        triple = (shape, stem, binding)
        if triple not in resolved:
            resolved.append(triple)
    return {"resolved": resolved, "unresolved": unresolved,
            "bindings": sorted(bindings)}


def _stems(text):
    """Every local stem a source reaches, static plus constant-bound dynamic."""
    static = _static_reader().imports_anywhere(text)
    dynamic = dynamic_imports(text)
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
            "bindings": dynamic["bindings"]}


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


def helper_scope(path, seams, stack, memo):
    """Seams one helper quiets plus the helpers it reaches at any level.

    Returns (quieted, helpers, unreadable, parsed, lazy, dynamic), where
    dynamic pairs carry the binding name that resolved them, if any. Cycles
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
    got = _stems(text)
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
                sub, seams, stack, memo)
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
    got = _stems(text)
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
            path, seams, stack, memo)
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
            "bindings": got["bindings"]}


def audit(root=None, module=None):
    """Name every probe that quiets a seam, however the name was bound."""
    module = render_module() if module is None else module
    root = BASE if root is None else root
    if not os.path.isdir(root):
        raise ConstantScopeError(E_NO_ROOT, "not a directory: %s" % root)
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
                row["lazy_imports"] = scope["lazy_imports"]
                row["dynamic"] = _dynamic_row(scope["dynamic"])
                row["unresolved"] = scope["unresolved"]
                row["bindings"] = scope["bindings"]
                row["unreadable_helpers"] = scope["unreadable"]
            rows.append(row)
            counts[UNREADABLE] += 1
            continue
        if not scope["quieted"]:
            row = _row(entry, OUT_OF_SCOPE)
            row["lazy_imports"] = scope["lazy_imports"]
            row["dynamic"] = _dynamic_row(scope["dynamic"])
            row["unresolved"] = scope["unresolved"]
            row["bindings"] = scope["bindings"]
            rows.append(row)
            counts[OUT_OF_SCOPE] += 1
            continue
        required = [name for name in seams if owners.get(name) != stem]
        missing = [name for name in required if name not in scope["quieted"]]
        verdict = MISSING_SEAM if missing else COVERED
        row = _row(entry, verdict)
        row["missing"] = missing
        row["quieted"] = scope["quieted"]
        row["required"] = required
        row["helpers"] = scope["helpers"]
        row["direct"] = scope["direct"]
        row["lazy_imports"] = scope["lazy_imports"]
        row["dynamic"] = _dynamic_row(scope["dynamic"])
        row["unresolved"] = scope["unresolved"]
        row["bindings"] = scope["bindings"]
        rows.append(row)
        counts[verdict] += 1
    stale = counts[MISSING_SEAM] + counts[UNREADABLE]
    return {"tool": LABEL,
            "verdict": SEAMS_STALE if stale else SEAMS_COVERED,
            "seams": [{"name": name, "owner": owners.get(name)}
                      for name in seams],
            "probes": rows, "counts": counts}


def _row(name, verdict):
    return {"file": name, "verdict": verdict, "missing": [], "quieted": [],
            "required": [], "helpers": [], "direct": [], "lazy_imports": [],
            "dynamic": [], "unresolved": [], "bindings": [],
            "unreadable_helpers": []}


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ConstantScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_COVERED:
        raise ConstantScopeError(
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
    lines = ["PROBE SEAM CONSTANT BINDING SCOPE %s verdict=%s seams=%d "
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
                     " helpers=%s dynamic=%s bindings=%s%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]), len(row["direct"]),
                        ",".join(row["helpers"]) or "-",
                        ",".join(row["dynamic"]) or "-",
                        ",".join(row["bindings"]) or "-",
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
    except ConstantScopeError as exc:
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