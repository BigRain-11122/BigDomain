"""probe_seam_dynamic_import_scope - follow an import built at RUN time.

MEASURED at R2517 while closing the lazy face: a probe that builds its import
at run time reads OUT-OF-SCOPE with zero quieted seams under both shipped
readers, because they resolve import STATEMENTS off a syntax tree. Measured in
a private temp root: `def run(): return
importlib.import_module("quiet_helper").QUIETED` reads OUT-OF-SCOPE quieted=0
and `def run(): return __import__("quiet_helper").QUIETED` reads
OUT-OF-SCOPE quieted=0, while the same helper reads COVERED quieted=5. A probe
whose quieting is resolved at run time is therefore invisible again, and a
stale one is never named.

This face closes that gap with ONE reading and no second seam classifier:

  dynamic_imports(text)
      the dynamic import calls a source really makes, read off its own syntax
      tree at CALL time: importlib.import_module, __import__, a from-import of
      import_module, and a module-level binding of any of those callables. Each
      call is split into RESOLVED (its first argument is a string constant, so
      the module is named) and UNRESOLVED (the argument is computed, so the
      call is named and NOT guessed at).
  helper_scope(path, seams, stack, memo)
      the seams a helper - and the helpers IT imports at any level, statically,
      lazily or dynamically in the same root - quiets, with a cycle guard and a
      depth cap. The seam classifier stays the shipped registry's `quiets`.
  probe_scope(text, seams, root)
      the seams a probe really quiets, the helpers it was followed through,
      the dynamic shapes it took and the dynamic calls it could not resolve.
  audit(root=None, module=None)
      every module that quiets at least one seam directly or through local
      imports is a PROBE and reads COVERED, or MISSING-SEAM naming the first
      seam it fails to quiet and the probe file, with the helpers and the
      dynamic shapes named on the row. A module that quiets nothing -
      including one whose only dynamic import is computed - reads OUT-OF-SCOPE
      with the unresolved call named rather than being guessed at or counted
      as clean. A source or a helper that will not parse reads UNREADABLE
      rather than being skipped. A probe is responsible for every seam except
      its OWN, the same rule the registry uses. A file whose name carries a
      round token is HISTORICAL. No probe and no helper is ever imported or
      run: this reads TEXT only, which is why a stale probe is NAMED rather
      than paid for.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PDI5).

Criteria AC-PDI1..AC-PDI6 were pinned in state/queue/tech.md:555 at R2517 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: the walk still follows local modules in the
SAME root only, at most MAX_HOPS links with a cycle guard; a module name that
is not a string constant is never resolved, and a callable reached through a
container or an attribute chain deeper than the shapes above is not seen.
Those shapes can UNDER-report a stale probe but can no longer invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for (verdict SEAMS-DYNAMIC-COVERED)
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

LABEL = "os-probe-seam-dynamic-import-scope"
E_ARGS = "E_PDI_ARGS"
E_NO_ROOT = "E_PDI_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_DYNAMIC_COVERED = "SEAMS-DYNAMIC-COVERED"
SEAMS_DYNAMIC_STALE = "SEAMS-DYNAMIC-STALE"

TEST_PREFIX = "test_"
SUFFIX = ".py"
ROUND_RE = re.compile(r"R[0-9]{3,}", re.IGNORECASE)
STEM_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
MAX_HOPS = 8

BASE = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(os.path.dirname(BASE), "sandbox")

SHAPE_IMPORTLIB = "importlib.import_module"
SHAPE_FROM = "import_module"
SHAPE_BUILTIN = "__import__"


class DynamicScopeError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _registry():
    """The shipped seam reader, imported once (one reader, no copy)."""
    import probe_seam_registry
    return probe_seam_registry


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


def _module_bindings(tree):
    """Names this module binds to a dynamic import callable.

    Returns (importlib_names, callable_names) where importlib_names are the
    names bound to the importlib package (so `name.import_module` is the
    attribute form) and callable_names maps a bound name to the SHAPE it
    stands for. Import bindings are read at ANY nesting level because a local
    `import importlib` still names the same callable; an assignment binding is
    read from the module body only, where a module-level alias lives. Every
    binding is read off THIS tree, never a written list.
    """
    importlib_names = []
    callable_names = {}

    def bind(mapping, name, shape):
        if name and name not in mapping:
            mapping[name] = shape

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level or node.module != "importlib":
                continue
            for alias in node.names:
                if alias.name == "import_module":
                    bind(callable_names, alias.asname or "import_module",
                         SHAPE_FROM)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib" or alias.name.startswith(
                        "importlib."):
                    name = alias.asname or "importlib"
                    if name not in importlib_names:
                        importlib_names.append(name)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            value = node.value
            if (isinstance(value, ast.Attribute) and value.attr
                    == "import_module" and isinstance(value.value, ast.Name)
                    and value.value.id in importlib_names):
                bind(callable_names, target.id, SHAPE_IMPORTLIB)
            elif (isinstance(value, ast.Name)
                  and value.id in callable_names):
                bind(callable_names, target.id, callable_names[value.id])
    return importlib_names, callable_names


def _shape_of(call, importlib_names, callable_names):
    """The dynamic shape a call really is, or None (derived, never a list)."""
    func = call.func
    if isinstance(func, ast.Name):
        if func.id == SHAPE_BUILTIN:
            return SHAPE_BUILTIN
        return callable_names.get(func.id)
    if (isinstance(func, ast.Attribute) and func.attr == "import_module"
            and isinstance(func.value, ast.Name)
            and func.value.id in importlib_names):
        return SHAPE_IMPORTLIB
    return None


def _computed_text(node):
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001 - the shape word is the fallback
        return "?"


def dynamic_imports(text):
    """Literal dynamic imports and the unresolved calls, off the tree.

    Returns None when the source will not parse, else a dict with RESOLVED
    pairs (shape, stem) in source order and UNRESOLVED labels ("shape:expr")
    for calls whose module name is computed rather than a string constant.
    """
    tree = _parse(text)
    if tree is None:
        return None
    importlib_names, callable_names = _module_bindings(tree)
    resolved = []
    unresolved = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        shape = _shape_of(node, importlib_names, callable_names)
        if shape is None:
            continue
        arg = node.args[0] if node.args else None
        if (isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                and STEM_RE.match(arg.value)):
            stem = arg.value.split(".")[0]
            pair = (shape, stem)
            if pair not in resolved:
                resolved.append(pair)
            continue
        label = "%s:%s" % (shape, _computed_text(arg) if arg else "no-arg")
        if label not in unresolved:
            unresolved.append(label)
    return {"resolved": resolved, "unresolved": unresolved}


def _stems(text):
    """Every local stem a source reaches, static at any level plus dynamic."""
    static = _static_reader().imports_anywhere(text)
    dynamic = dynamic_imports(text)
    if static is None or dynamic is None:
        return None
    every, top, lazy = static
    stems = list(every)
    for _shape, stem in dynamic["resolved"]:
        if stem not in stems:
            stems.append(stem)
    return {"every": stems, "top": top, "lazy": lazy,
            "resolved": dynamic["resolved"],
            "unresolved": dynamic["unresolved"]}


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def helper_scope(path, seams, stack, memo):
    """Seams one helper quiets plus the helpers it reaches at any level.

    Returns (quieted, helpers, unreadable, parsed, lazy, dynamic). Cycles
    contribute nothing new (the stack breaks them), a helper that will not
    parse is named rather than skipped, and results are memoised per audit.
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
    dynamic_seen = ["%s:%s" % pair for pair in got["resolved"]]
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
                for name in sub_dyn:
                    if name not in dynamic_seen:
                        dynamic_seen.append(name)
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
    dynamic_seen = ["%s:%s" % pair for pair in got["resolved"]]
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
            for name in sub_dyn:
                if name not in dynamic_seen:
                    dynamic_seen.append(name)
    return {"direct": direct, "helpers": helpers, "quieted": quieted,
            "unreadable": unreadable, "lazy_imports": lazy_seen,
            "dynamic": dynamic_seen, "unresolved": got["unresolved"]}


def audit(root=None, module=None):
    """Name every probe that quiets a seam, however the import was written."""
    module = render_module() if module is None else module
    root = BASE if root is None else root
    if not os.path.isdir(root):
        raise DynamicScopeError(E_NO_ROOT, "not a directory: %s" % root)
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
            rows.append({"file": entry, "verdict": HISTORICAL,
                         "missing": [], "quieted": [], "required": [],
                         "helpers": [], "direct": [], "lazy_imports": [],
                         "dynamic": [], "unresolved": [],
                         "unreadable_helpers": []})
            counts[HISTORICAL] += 1
            continue
        try:
            text = _read(path)
        except OSError:
            rows.append({"file": entry, "verdict": UNREADABLE,
                         "missing": [], "quieted": [], "required": [],
                         "helpers": [], "direct": [], "lazy_imports": [],
                         "dynamic": [], "unresolved": [],
                         "unreadable_helpers": []})
            counts[UNREADABLE] += 1
            continue
        scope = probe_scope(text, seams, root)
        if scope is None or scope["unreadable"]:
            rows.append({"file": entry, "verdict": UNREADABLE,
                         "missing": [], "quieted": [], "required": [],
                         "helpers": [], "direct": [],
                         "lazy_imports": scope["lazy_imports"] if scope
                         else [],
                         "dynamic": scope["dynamic"] if scope else [],
                         "unresolved": scope["unresolved"] if scope else [],
                         "unreadable_helpers":
                             scope["unreadable"] if scope else []})
            counts[UNREADABLE] += 1
            continue
        if not scope["quieted"]:
            rows.append({"file": entry, "verdict": OUT_OF_SCOPE,
                         "missing": [], "quieted": [], "required": [],
                         "helpers": [], "direct": [],
                         "lazy_imports": scope["lazy_imports"],
                         "dynamic": scope["dynamic"],
                         "unresolved": scope["unresolved"],
                         "unreadable_helpers": []})
            counts[OUT_OF_SCOPE] += 1
            continue
        me = stem
        required = [name for name in seams if owners.get(name) != me]
        missing = [name for name in required if name not in scope["quieted"]]
        verdict = MISSING_SEAM if missing else COVERED
        rows.append({"file": entry, "verdict": verdict,
                     "missing": missing, "quieted": scope["quieted"],
                     "required": required, "helpers": scope["helpers"],
                     "direct": scope["direct"],
                     "lazy_imports": scope["lazy_imports"],
                     "dynamic": scope["dynamic"],
                     "unresolved": scope["unresolved"],
                     "unreadable_helpers": []})
        counts[verdict] += 1
    stale = counts[MISSING_SEAM] + counts[UNREADABLE]
    return {"tool": LABEL,
            "verdict": SEAMS_DYNAMIC_STALE if stale else SEAMS_DYNAMIC_COVERED,
            "seams": [{"name": name, "owner": owners.get(name)}
                      for name in seams],
            "probes": rows, "counts": counts}


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except DynamicScopeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_DYNAMIC_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_DYNAMIC_COVERED:
        raise DynamicScopeError(
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
    lines = ["PROBE SEAM DYNAMIC IMPORT SCOPE %s verdict=%s seams=%d "
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
                     " helpers=%s dynamic=%s%s"
                     % (row["file"], row["verdict"], len(row["quieted"]),
                        len(row["required"]), len(row["direct"]),
                        ",".join(row["helpers"]) or "-",
                        ",".join(row["dynamic"]) or "-",
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
    except DynamicScopeError as exc:
        print("FAIL root: %s %s" % (exc.code, exc.detail))
        return 3
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(render(report))
    return 0 if report["verdict"] == SEAMS_DYNAMIC_COVERED else 2


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