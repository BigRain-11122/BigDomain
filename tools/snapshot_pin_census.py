"""snapshot_pin_census - which test assertions pin the current tree (R3348).

AC-SPC1..AC-SPC7 were pinned in src/os/backlog.md BEFORE this file existed.

Why this exists: R3347 cleared two reds that were not product defects but
"ambient snapshot pins" - an assertion that writes the current shape of the
tree into a number (len(unreadable) == 1, count(call) == 1). Such a pin is
green until the day the tree legitimately grows, and then it reddens a healthy
shipped file. Nobody could say how many more of that shape exist, so every
window met them one at a time, by accident. This tool turns that into a
reading:

  - the corpus is every test_*.py in the tree, with a fixed skip list; a file
    that carries a UTF-8 BOM is reported as "bom" and a file that cannot be
    parsed at all as "unreadable", and neither is ever counted as a pin
    (AC-SPC1);
  - a pin is an assert whose test is a single-operator == or != against a
    non-bool int constant on one side and a counting expression (len/sum/
    .count) on the other; a range check or a length-vs-length comparison is
    not a pin (AC-SPC2);
  - each pin is traced (bounded depth, visited set) to a terminal: reading a
    file on disk is "ambient", a world built inside this file is "private",
    an imported module is "foreign", and anything else is "unknown", each
    with its because= basis (AC-SPC3);
  - private fixtures prove the labels are load-bearing rather than renamed:
    the same line reads ambient when it reads a file and private when that
    read becomes a literal (AC-SPC4);
  - --order lists only the pins that must be re-pinned, in a stable
    (file, line) order that matches --json (AC-SPC5);
  - the tool writes nothing and reads no clock (AC-SPC6);
  - --max-ambient is a ratchet: it is off unless asked for, and an explicit
    budget below the measured count returns rc=2 naming the excess
    (AC-SPC7).

A label is a heuristic, not a proof. "private" only proves the value is built
inside this file, "foreign" only proves the determinism lives elsewhere, and
"unknown" is a real bucket rather than a zero. The census is a floor.

Source discipline: pure ASCII, stdlib only, no clock, no network, no writes.
"""
import argparse
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = frozenset((
    ".git", "qa", "logs", "tmp", "preview", "node_modules", "__pycache__",
    ".codely-cli", ".playwright-mcp", "media", "state",
))

MAX_DEPTH = 6

# A file read is the shape that makes a pin ambient: the number describes
# whatever is on disk today. The name must stand alone (_open( is a local
# helper that builds a private world, not a file read), and bare .read( is
# deliberately absent because http.client responses read a private world.
FILE_READ = re.compile(r"(?<![A-Za-z0-9_])(?:open|read_text|read_bytes)\s*\(")

COUNT_FUNCS = frozenset(("len", "sum"))

BUILTINS = frozenset((
    "len", "sum", "int", "str", "sorted", "set", "list", "dict", "tuple",
    "bool", "float", "min", "max", "abs", "range", "enumerate", "zip",
    "any", "all", "isinstance", "getattr", "print", "open",
))

LABELS = ("ambient", "foreign", "unknown", "private")


class Refuse(Exception):
    """A named refusal that must reach the caller as rc=3."""


def _parents(tree):
    """node -> parent, so a name can be resolved from where it is used."""
    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    return parent


def _bind_in_scope(scope):
    """{name: rhs} for ONE scope, never descending into nested scopes."""
    table = {}

    def bind_target(target, value):
        for sub in ast.walk(target):
            if isinstance(sub, ast.Name):
                table[sub.id] = value

    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        args = scope.args
        for arg in (list(args.posonlyargs) + list(args.args)
                    + list(args.kwonlyargs)):
            table[arg.arg] = "PARAM"
        for arg in (args.vararg, args.kwarg):
            if arg is not None:
                table[arg.arg] = "PARAM"
        body = [scope.body] if isinstance(scope, ast.Lambda) else scope.body
    else:
        body = scope.body
    stack = list(body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                bind_target(target, node.value)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            bind_target(node.target, node.value)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    bind_target(item.optional_vars, item.context_expr)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            bind_target(node.target, "PARAM")
        elif isinstance(node, ast.ExceptHandler) and node.name:
            table[node.name] = "PARAM"
        elif isinstance(node, ast.NamedExpr):
            bind_target(node.target, node.value)
        stack.extend(ast.iter_child_nodes(node))
    return table


def _scope_bindings(tree):
    """(scope_node, {name: rhs_node}) for the module and every function."""
    scopes = [tree]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            scopes.append(node)
    return dict((scope, _bind_in_scope(scope)) for scope in scopes)


def _imported_names(tree):
    names = set()
    local_funcs = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local_funcs.add(node.name)
    return names, local_funcs


def _comprehension_targets(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp,
                             ast.DictComp)):
            for generator in node.generators:
                for sub in ast.walk(generator.target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
    return names


def _segment(source, node):
    try:
        text = ast.get_source_segment(source, node)
    except Exception:
        text = None
    return " ".join((text or "").split())


def _names_of(node):
    return set(sub.id for sub in ast.walk(node) if isinstance(sub, ast.Name))


def _resolve(name, at, scopes, parent, imports, local_funcs, comp_targets):
    """One step of the trace: where does this name come from?"""
    if name in comp_targets:
        return "private"
    if name in BUILTINS:
        return "builtin"
    if name in local_funcs:
        return "private"
    if name in imports:
        return "foreign"
    node = at
    while node is not None:
        table = scopes.get(node)
        if table is not None and name in table:
            return table[name]
        node = parent.get(node)
    return None


def _terminals(source, node, scope, scopes, parent, imports, local_funcs,
               comp_targets, depth, visited):
    """Every terminal this expression reaches, bounded and cycle-safe."""
    found = set()
    for name in _names_of(node):
        if name in visited:
            found.add("unknown")
            continue
        if depth >= MAX_DEPTH:
            found.add("unknown")
            continue
        resolved = _resolve(name, scope, scopes, parent, imports, local_funcs,
                            comp_targets)
        if resolved == "builtin":
            continue
        if resolved == "private":
            found.add("private")
            continue
        if resolved == "foreign":
            found.add("foreign")
            continue
        if resolved is None:
            found.add("unknown")
            continue
        if isinstance(resolved, str) and resolved == "PARAM":
            found.add("private")
            continue
        text = _segment(source, resolved)
        if FILE_READ.search(text):
            found.add("ambient")
            continue
        inner = _terminals(source, resolved, scope, scopes, parent, imports,
                           local_funcs, comp_targets, depth + 1,
                           visited | {name})
        if not inner:
            found.add("private")
        else:
            found.update(inner)
    return found


def _label(found):
    if "ambient" in found:
        return "ambient"
    if "foreign" in found:
        return "foreign"
    if found <= {"private"}:
        return "private"
    return "unknown"


def _count_side(compare):
    """The counting side of a single-operator int comparison, or None."""
    left, right = compare.left, compare.comparators[0]
    for candidate, other in ((left, right), (right, left)):
        if (isinstance(other, ast.Constant) and isinstance(other.value, int)
                and not isinstance(other.value, bool)):
            if isinstance(candidate, ast.Call):
                func = candidate.func
                name = func.id if isinstance(func, ast.Name) else (
                    func.attr if isinstance(func, ast.Attribute) else "")
                if name in COUNT_FUNCS or name == "count":
                    return candidate
    return None


def _family(rel):
    parts = rel.replace("\\", "/").split("/")
    if parts and parts[0] == "src" and len(parts) > 1:
        return parts[1]
    return parts[0] if parts else rel


def test_files(root):
    """AC-SPC1: the corpus is every test_*.py, minus a fixed skip list."""
    if not os.path.isdir(root):
        raise Refuse("E_ROOT_MISSING %s" % root)
    found = []
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            if name.startswith("test_") and name.endswith(".py"):
                found.append(os.path.join(base, name))
    return found


def read_source(path):
    """(text, dialect) where dialect is utf-8, bom, or unreadable."""
    raw = open(path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        try:
            return raw.decode("utf-8-sig"), "bom"
        except UnicodeDecodeError:
            return None, "unreadable"
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return None, "unreadable"


def scan_file(path, root):
    """All pins in one file plus its dialect reading."""
    text, dialect = read_source(path)
    rel = os.path.relpath(path, root).replace("\\", "/")
    if text is None:
        return [], {"file": rel, "dialect": "unreadable"}
    tree = None
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], {"file": rel, "dialect": "unreadable"}
    parent = _parents(tree)
    scopes = _scope_bindings(tree)
    imports, local_funcs = _imported_names(tree)
    comp_targets = _comprehension_targets(tree)
    pins = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        test = node.test
        if not isinstance(test, ast.Compare) or len(test.ops) != 1:
            continue
        if not isinstance(test.ops[0], (ast.Eq, ast.NotEq)):
            continue
        side = _count_side(test)
        if side is None:
            continue
        scope = parent.get(node)
        while scope is not None and scope not in scopes:
            scope = parent.get(scope)
        found = _terminals(text, side, scope, scopes, parent, imports,
                           local_funcs, comp_targets, 0, set())
        basis = ",".join(sorted(found)) or "nothing"
        pins.append({
            "file": rel,
            "line": node.lineno,
            "expr": _segment(text, side),
            "label": _label(found),
            "because": basis,
        })
    pins.sort(key=lambda item: (item["file"], item["line"]))
    return pins, {"file": rel, "dialect": dialect}


def census(root=None):
    """AC-SPC1..SPC3: every pin, grouped, with its dialect face."""
    base = root or ROOT
    files = test_files(base)
    pins = []
    bom = []
    unreadable = []
    for path in files:
        file_pins, info = scan_file(path, base)
        if info["dialect"] == "bom":
            bom.append(info["file"])
        elif info["dialect"] == "unreadable":
            unreadable.append(info["file"])
        pins.extend(file_pins)
    counts = dict((label, 0) for label in LABELS)
    for pin in pins:
        counts[pin["label"]] += 1
    families = {}
    for pin in pins:
        family = _family(pin["file"])
        slot = families.setdefault(family, dict((label, 0) for label in LABELS))
        slot[pin["label"]] += 1
    return {
        "files": len(files),
        "pins": len(pins),
        "counts": counts,
        "bom": sorted(bom),
        "unreadable": sorted(unreadable),
        "families": dict(sorted(families.items())),
        "rows": pins,
    }


def repin_order(result):
    """AC-SPC5: only pins whose determinism is not held inside the file."""
    return [pin for pin in result["rows"]
            if pin["label"] in ("ambient", "foreign", "unknown")]


def summary_line(result):
    counts = result["counts"]
    return ("PIN CENSUS files=%d pins=%d ambient=%d foreign=%d unknown=%d "
            "private=%d bom=%d unreadable=%d"
            % (result["files"], result["pins"], counts["ambient"],
               counts["foreign"], counts["unknown"], counts["private"],
               len(result["bom"]), len(result["unreadable"])))


def render(result, order=False):
    lines = [summary_line(result)]
    for family, slot in result["families"].items():
        lines.append("FAMILY %s pins=%d ambient=%d foreign=%d unknown=%d "
                     "private=%d"
                     % (family, sum(slot.values()), slot["ambient"],
                        slot["foreign"], slot["unknown"], slot["private"]))
    for pin in result["rows"]:
        lines.append("PIN %s:%d label=%s expr=%s because=%s"
                     % (pin["file"], pin["line"], pin["label"], pin["expr"],
                        pin["because"]))
    if result["bom"]:
        for path in result["bom"]:
            lines.append("BOM %s parses only with utf-8-sig" % path)
    for path in result["unreadable"]:
        lines.append("UNREADABLE %s not counted in any label" % path)
    if order:
        for index, pin in enumerate(repin_order(result), 1):
            lines.append("REPIN %d %s:%d label=%s"
                         % (index, pin["file"], pin["line"], pin["label"]))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="census of assertions that pin the current tree")
    parser.add_argument("--root", default=None,
                        help="corpus root (default: this repo)")
    parser.add_argument("--order", action="store_true",
                        help="list only pins that need re-pinning")
    parser.add_argument("--json", action="store_true",
                        help="byte-stable json reading")
    parser.add_argument("--max-ambient", type=int, default=None,
                        help="ratchet: rc=2 when ambient exceeds this")
    args = parser.parse_args(argv)
    try:
        result = census(args.root)
    except Refuse as exc:
        print("REFUSE %s" % exc)
        return 3
    if args.json:
        payload = dict(result)
        if not args.order:
            payload.pop("rows")
        print(json.dumps(payload, indent=2, sort_keys=True,
                         ensure_ascii=True))
    else:
        print(render(result, order=args.order))
    if args.max_ambient is not None:
        ambient = result["counts"]["ambient"]
        if ambient > args.max_ambient:
            print("RATCHET ambient=%d max=%d excess=%d"
                  % (ambient, args.max_ambient, ambient - args.max_ambient))
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
