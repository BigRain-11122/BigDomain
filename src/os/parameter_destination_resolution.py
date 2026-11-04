# parameter_destination_resolution.py - a writer that receives its destination
# as a PARAMETER is resolved through its own call sites instead of being left
# unread.
# Criteria AC-PDR1..AC-PDR6 were pre-registered inside the R2434 seed row of
# state/queue/tech.md (line 514) BEFORE this file existed.
#
# Why this exists: general_writer_dialect_audit reads the destination of each
# writer's own os.replace call and resolves it through that module's data flow
# (local and module assignments, imported constants, os.path.join, a one-hop
# local function). MEASURED at R2434, a writer that RECEIVES its path as a
# function parameter reads E_GWDA_UNRESOLVED and hides among the unread rows -
# qa_writer_census lands its baseline, queue_floor_export_face lands
# docs/status-export.json - so the tier cannot say whether such a writer is
# clean or merely unread.
#
# This module owns one question, derived from the SOURCE call sites and never
# from a whitelist (AC-PDR1):
#
#   for an os.replace whose destination is a parameter of its enclosing
#   function, what does every in-module call site actually pass for it?
#
# The argument at each call site is handed to the CALLER's own resolver, so
# this module never re-implements path resolution: general_writer_dialect_audit
# passes its resolver into by_call_site at CALL time, and the suite proves the
# seam by passing one of its own. A call-site argument that is itself a
# parameter of the CALLING function is followed one hop at a time, with a
# declared depth (MAX_DEPTH) so a cycle cannot loop forever.
#
# Three answers, none silent:
#
#   * a resolved parameter publishes every spelling its call sites pass;
#   * a function with NO in-module call site reads UNRESOLVED naming the
#     function and the parameter (AC-PDR3);
#   * a call site whose argument does not resolve reads UNRESOLVED naming the
#     function rather than being dropped.
#
# Pure: it writes nothing itself, reads no clock, imports no network, and it is
# pure ASCII stdlib (AC-PDR6).

import ast
import io
import os

PREFIX = "E_PDR"
SUITE_LABEL = "os-parameter-destination-resolution"

# a parameter handed down through call sites is followed this far, no further
MAX_DEPTH = 4

REPORT_KEYS = ("verdict", "scanned", "writers", "resolved", "unresolved", "rows")
ROW_KEYS = ("name", "line", "function", "parameter", "target", "answer")


class ResolutionError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _tree(source):
    """The module's own syntax, or None when it does not parse."""
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return ast.parse(source)
    except SyntaxError:
        return None


def _parents(tree):
    """node -> its parent node, so an expression can find its function."""
    out = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            out[child] = node
    return out


def _enclosing_function(node, parents):
    """The nearest function definition around this node, or None."""
    current = parents.get(node)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
        current = parents.get(current)
    return None


def _positional(func):
    """The positional parameter names of a function, in order."""
    return [arg.arg for arg in list(func.args.posonlyargs) + list(func.args.args)]


def _param_index(func, name):
    """The positional index of a parameter, or -1 when it is not one."""
    names = _positional(func)
    if name in names:
        return names.index(name)
    return -1


def _call_sites(tree, func_name):
    """Every in-module call of a function by that name."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == func_name:
            out.append(node)
    return out


def _argument(call, name, index):
    """The argument a call passes for a named parameter, or None."""
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    if 0 <= index < len(call.args):
        return call.args[index]
    return None


def _replace_destinations(tree):
    """Every (os.replace call node, its destination expression)."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "replace"
                and isinstance(func.value, ast.Name) and func.value.id == "os"):
            continue
        destination = node.args[1] if len(node.args) >= 2 else None
        if destination is None:
            for keyword in node.keywords:
                if keyword.arg in ("dst", "dest", "destination"):
                    destination = keyword.value
        if destination is not None:
            out.append((node, destination))
    return out


def _spellings(func, name, tree, resolver, parents, depth):
    """Every spelling this parameter can carry, resolved through call sites."""
    if depth > MAX_DEPTH:
        return [], 0
    index = _param_index(func, name)
    if index < 0:
        return [], 0
    found = []
    sites = 0
    for call in _call_sites(tree, func.name):
        if _enclosing_function(call, parents) is func:
            continue
        argument = _argument(call, name, index)
        if argument is None:
            continue
        sites += 1
        got = [item for item in resolver(argument) if item]
        if not got and isinstance(argument, ast.Name):
            caller = _enclosing_function(call, parents)
            if caller is not None and _param_index(caller, argument.id) >= 0:
                got, _inner = _spellings(caller, argument.id, tree, resolver,
                                         parents, depth + 1)
        for item in got:
            if item not in found:
                found.append(item)
    return found, sites


def by_call_site(source, resolver):
    """Per os.replace line: the spellings its parameter destination carries.

    Returns {"calls": {line: [spelling, ...]}, "unresolved": {line: reason}}.
    Only destinations that really ARE a parameter of their enclosing function
    are read here; every other destination keeps the caller's own law.
    """
    tree = _tree(source)
    if tree is None:
        return {"calls": {}, "unresolved": {}}
    parents = _parents(tree)
    calls = {}
    unresolved = {}
    for node, destination in _replace_destinations(tree):
        if not isinstance(destination, ast.Name):
            continue
        func = _enclosing_function(node, parents)
        if func is None or _param_index(func, destination.id) < 0:
            continue
        found, sites = _spellings(func, destination.id, tree, resolver,
                                  parents, 0)
        line = getattr(node, "lineno", 0)
        if found:
            bucket = calls.setdefault(line, [])
            for item in found:
                if item not in bucket:
                    bucket.append(item)
        elif sites == 0:
            unresolved[line] = ("parameter %s of %s has no in-module call site"
                                % (destination.id, func.name))
        else:
            unresolved[line] = ("parameter %s of %s call site argument does "
                                "not resolve" % (destination.id, func.name))
    return {"calls": calls, "unresolved": unresolved}


def _fallback_resolver(node):
    """A literal-only resolver, used only when a caller passes none."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def read_module(name, source, resolver=None):
    """One module's rows: every parameter destination with its answer."""
    reading = by_call_site(source, resolver or _fallback_resolver)
    rows = []
    for line in sorted(reading["calls"]):
        for target in reading["calls"][line]:
            rows.append({"name": name, "line": line,
                         "function": _function_of(source, line),
                         "parameter": _parameter_of(source, line),
                         "target": target.replace("\\", "/"),
                         "answer": "RESOLVED"})
    for line in sorted(reading["unresolved"]):
        rows.append({"name": name, "line": line,
                     "function": _function_of(source, line),
                     "parameter": _parameter_of(source, line),
                     "target": "-", "answer": "UNRESOLVED",
                     "why": reading["unresolved"][line]})
    return rows


def _function_of(source, line):
    """The enclosing function name at a line, for the published row."""
    tree = _tree(source)
    if tree is None:
        return "-"
    parents = _parents(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node, "lineno", 0) == line:
            func = _enclosing_function(node, parents)
            if func is not None:
                return func.name
    return "-"


def _parameter_of(source, line):
    """The parameter name at a line, for the published row."""
    tree = _tree(source)
    if tree is None:
        return "-"
    parents = _parents(tree)
    for node, destination in _replace_destinations(tree):
        if getattr(node, "lineno", 0) == line and isinstance(destination, ast.Name):
            return destination.id
    return "-"


def scan(root, resolver=None, factory=None):
    """Every writer under <root>/src/os that carries a parameter destination.

    `factory(source)` builds the resolver for THAT module, which is how the CLI
    asks the audit's own path resolution instead of restating it. `resolver` is
    the flat form the audit passes when it already holds one module's maps.
    """
    if (resolver is not None) and (factory is not None):
        raise ResolutionError(PREFIX + "_BAD_ARGS",
                              "give a resolver or a factory, not both")
    base = os.path.join(root, "src", "os")
    if not os.path.isdir(base):
        raise ResolutionError(PREFIX + "_UNREADABLE",
                              "no such directory: %s" % base)
    try:
        names = sorted(entry for entry in os.listdir(base)
                       if entry.endswith(".py") and not entry.startswith("test_"))
    except (IOError, OSError) as exc:
        raise ResolutionError(PREFIX + "_UNREADABLE", "%s (%s)" % (base, exc))
    rows = []
    scanned = 0
    for name in names:
        path = os.path.join(base, name)
        try:
            with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
        except (IOError, OSError) as exc:
            raise ResolutionError(PREFIX + "_UNREADABLE", "%s (%s)" % (path, exc))
        scanned += 1
        res = factory(source) if factory is not None else resolver
        rows.extend(read_module(name, source, res))
    return scanned, rows


def audit_factory(module_dir):
    """A per-module resolver that IS the audit's own law, asked at CALL time.

    This module never restates path resolution: the seam imports
    general_writer_dialect_audit lazily (that module imports this one at module
    level, so a top-level import here would be a cycle) and hands back its
    resolver closed over that module's own maps.
    """
    def factory(source):
        import general_writer_dialect_audit as GWDA
        tree = _tree(source)
        if tree is None:
            return _fallback_resolver
        assigns = GWDA._assignments(tree)
        funcs = GWDA._functions(tree)
        imports = GWDA._imports(tree)
        return lambda node: GWDA._resolve_node(node, assigns, funcs, imports,
                                               module_dir)
    return factory


def report(root, resolver=None, factory=None):
    """The reading over the whole tree, with both answers counted."""
    scanned, rows = scan(root, resolver, factory)
    resolved = [row for row in rows if row["answer"] == "RESOLVED"]
    unresolved = [row for row in rows if row["answer"] == "UNRESOLVED"]
    writers = sorted(set(row["name"] for row in rows))
    if not rows:
        verdict = "NO-PARAM-CALLS"
    elif unresolved:
        verdict = "PARAM-MIXED"
    else:
        verdict = "PARAM-RESOLVED"
    return {"verdict": verdict, "scanned": scanned, "writers": len(writers),
            "resolved": len(resolved), "unresolved": len(unresolved),
            "rows": rows}


def one_line(reading):
    """The single line an operator reads."""
    return ("PARAM DESTINATION scanned=%d writers=%d resolved=%d "
            "unresolved=%d verdict=%s"
            % (reading["scanned"], reading["writers"], reading["resolved"],
               reading["unresolved"], reading["verdict"]))


def render(reading):
    """The one line, then every parameter destination and its answer."""
    out = [one_line(reading)]
    for row in reading["rows"]:
        if row["answer"] == "RESOLVED":
            out.append("  RESOLVED %s line=%d %s(%s) -> %s"
                       % (row["name"], row["line"], row["function"],
                          row["parameter"], row["target"]))
        else:
            out.append("  UNRESOLVED %s line=%d %s_UNRESOLVED (%s)"
                       % (row["name"], row["line"], PREFIX, row["why"]))
    return "\n".join(out)


def to_json(reading):
    """A byte-stable payload over the pinned keys."""
    import json
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = reading[key]
    ordered["rows"] = []
    for row in reading["rows"]:
        item = {}
        for key in ROW_KEYS:
            item[key] = row.get(key, "-")
        ordered["rows"].append(item)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: parameter_destination_resolution.py --check [--root PATH] "
         "[--json]\n"
         "  exit 0 = every parameter destination resolves through its call "
         "sites\n"
         "  exit 2 = at least one parameter destination does not resolve\n"
         "  exit 3 = src/os is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    as_json = False
    checked = False
    root = "."
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            checked = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                import sys
                sys.stdout.write("%s_BAD_ARGS: --root needs a value\n" % PREFIX)
                sys.stdout.write(USAGE)
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            import sys
            sys.stdout.write(USAGE)
            return 0
        else:
            import sys
            sys.stdout.write("%s_BAD_ARGS: unknown flag %s\n" % (PREFIX, arg))
            sys.stdout.write(USAGE)
            return 5
        index += 1
    import sys
    if not checked:
        sys.stdout.write("%s_BAD_ARGS: --check is required\n" % PREFIX)
        sys.stdout.write(USAGE)
        return 5
    try:
        reading = report(root, factory=audit_factory(
            os.path.join(os.path.abspath(root), "src", "os")))
    except ResolutionError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 3
    if as_json:
        sys.stdout.write(to_json(reading))
    else:
        sys.stdout.write(render(reading) + "\n")
    return 0 if reading["verdict"] != "PARAM-MIXED" else 2


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))