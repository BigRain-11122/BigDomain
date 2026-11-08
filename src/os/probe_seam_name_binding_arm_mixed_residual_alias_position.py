"""AC-PNDS1..AC-PNDS6: the alias-position face (R2557).

Criteria were pinned in state/queue/tech.md:593 at R2555 BEFORE this code
existed.

What this proves: MEASURED at R2555 on the shipped alias-chain face own reader,
a WALRUS alias ((B := A) at module level) reads `name-unbound:B` because only
plain and annotated assignments are alias edges, an alias whose value is an
ATTRIBUTE (B = M.A) reads `name-unbound:B` because the alias table holds bare
names only, and a constant declared AFTER the loop still resolves to its
literal because source POSITION is not read (an over-resolution rather than a
refusal).

This face asks the shipped alias-chain answer FIRST and carries it unchanged on
every row, then re-reads only what that answer left open:
  * a walrus binding is an alias edge when its value is a bare name, and a
    literal when its value is a str constant;
  * an alias whose value is ONE attribute on a same-root module the probe
    imports resolves to that module own str constant, and the chain names the
    hop it took;
  * a name whose every binding line is LATER than the loop line is NAMED
    not-yet-bound and never resolved, so the over-resolution is closed;
  * an attribute chain deeper than one hop, an attribute that is not a str
    constant, a module that is not imported and a module file that is absent
    are NAMED with the hop instead of being guessed at.

Nothing is imported and nothing is evaluated: every value comes from reading
source text. Stdlib only, ASCII source, zero network, no clock.
"""

import argparse
import ast
import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

LABEL = "os-probe-seam-name-binding-arm-mixed-residual-alias-position"

E_ARGS = "E_PNDS_ARGS"
E_NO_ROOT = "E_PNDS_NO_ROOT"

STATE_OK = "ok"
STATE_ARMS = "arms"
STATE_REFUSED = "refused"

REFUSED_NOT_YET_BOUND = "not-yet-bound:%s"
REFUSED_ATTR_DEEP = "attr-deep:%s"
REFUSED_ATTR_MISSING = "attr-missing:%s"
REFUSED_ATTR_NON_CONSTANT = "attr-non-constant:%s"
REFUSED_ATTR_NOT_IMPORTED = "attr-not-imported:%s"
REFUSED_NAME_MIXED = "name-mixed:%s"
REFUSED_NAME_UNBOUND = "name-unbound:%s"
REFUSED_CYCLE = "name-cycle:%s"

SOURCE_BASE = "shipped"
SOURCE_POSITION = "alias-position"

SCOPE_MODULE = "module"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_POSITION_COVERED = "SEAMS-ALIAS-POSITION-COVERED"
SEAMS_POSITION_STALE = "SEAMS-ALIAS-POSITION-STALE"

MAX_CHAIN = 8


class AliasPositionError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _base():
    """The shipped alias-chain face this module extends."""
    import probe_seam_name_binding_arm_mixed_residual_alias_chain
    return probe_seam_name_binding_arm_mixed_residual_alias_chain


def _parse(text):
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _scope_bodies(tree, scope):
    """The statement bodies that make up one scope."""
    if tree is None:
        return []
    if not scope or scope == SCOPE_MODULE:
        return [tree.body]
    if scope.startswith("function:"):
        name = scope.split(":", 1)[1]
        bodies = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == name:
                    bodies.append(node.body)
        return bodies
    return [tree.body]


def _walk_statements(bodies):
    """Every statement in these bodies, nested blocks included."""
    for body in bodies:
        stack = [body]
        while stack:
            block = stack.pop()
            for node in block:
                yield node
                for field in ("body", "orelse", "finalbody"):
                    inner = getattr(node, field, None)
                    if isinstance(inner, list):
                        stack.append(inner)
                handlers = getattr(node, "handlers", None)
                if isinstance(handlers, list):
                    for handler in handlers:
                        stack.append(handler.body)
                cases = getattr(node, "cases", None)
                if isinstance(cases, list):
                    for case in cases:
                        stack.append(case.body)


def _str_constant(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _binding_records(tree, scope):
    """Every literal, alias, attribute edge and binding line in one scope."""
    records = {"literals": {}, "aliases": {}, "attrs": {}, "deep": {},
               "lines": {}, "imported": {}}
    for node in _walk_statements(_scope_bodies(tree, scope)):
        pairs = []
        if isinstance(node, ast.Assign):
            value = node.value
            for target in node.targets:
                if isinstance(target, ast.Name):
                    pairs.append((target.id, value))
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None:
                pairs.append((node.target.id, node.value))
        elif isinstance(node, ast.Expr):
            inner = node.value
            if isinstance(inner, ast.NamedExpr):
                if isinstance(inner.target, ast.Name):
                    pairs.append((inner.target.id, inner.value))
        for name, value in pairs:
            line = getattr(node, "lineno", None)
            records["lines"].setdefault(name, set()).add(line)
            literal = _str_constant(value)
            if literal is not None:
                records["literals"].setdefault(name, []).append(
                    (line, literal))
                continue
            if isinstance(value, ast.Name):
                records["aliases"].setdefault(name, []).append(
                    (line, value.id))
                continue
            if isinstance(value, ast.Attribute):
                text = _dotted(value)
                if isinstance(value.value, ast.Name):
                    records["attrs"].setdefault(name, []).append(
                        (line, text, value.value.id, value.attr))
                else:
                    records["deep"].setdefault(name, []).append((line, text))
    return records


def _dotted(node):
    """The dotted text of an Attribute / Name chain, or a plain guess."""
    parts = []
    here = node
    while isinstance(here, ast.Attribute):
        parts.append(here.attr)
        here = here.value
    if isinstance(here, ast.Name):
        parts.append(here.id)
    else:
        parts.append("?")
    return ".".join(reversed(parts))


def _imports_of(tree):
    """Module names this probe imports at module level."""
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def _module_bindings(root, module):
    """(str constants, every bound name) of one same-root module file."""
    path = os.path.join(root, module + ".py")
    if not os.path.isfile(path):
        return None
    try:
        text = _read(path)
    except OSError:
        return None
    tree = _parse(text)
    if tree is None:
        return None
    out = {}
    names = set()
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = [target for target in node.targets
                       if isinstance(target, ast.Name)]
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                targets = [node.target]
        elif isinstance(node, ast.Expr):
            inner = node.value
            if isinstance(inner, ast.NamedExpr):
                if isinstance(inner.target, ast.Name):
                    targets = [inner.target]
        for target in targets:
            names.add(target.id)
            literal = _str_constant(node.value)
            if literal is not None:
                out.setdefault(target.id, set()).add(literal)
    return (dict((name, sorted(values)) for name, values in out.items()),
            names)


def _resolve(name, records, context, limit, chain=None, hops=None):
    """Follow one name to a literal, or NAMED the reason it cannot be one."""
    walked = list(chain or [])
    taken = list(hops or [])
    if name in walked or len(walked) >= MAX_CHAIN:
        return None, REFUSED_CYCLE % name, walked + [name], taken
    walked.append(name)
    lines = sorted(records["lines"].get(name) or [])
    if not lines:
        return None, REFUSED_NAME_UNBOUND % name, walked, taken
    if all(line is not None and line > limit for line in lines):
        return None, REFUSED_NOT_YET_BOUND % name, walked, taken
    deep = [text for (line, text) in records["deep"].get(name, [])
            if line is None or line <= limit]
    if deep:
        return None, REFUSED_ATTR_DEEP % deep[0], walked, taken
    values = sorted({value for (line, value)
                     in records["literals"].get(name, [])
                     if line is None or line <= limit})
    if len(values) > 1:
        return None, REFUSED_NAME_MIXED % name, walked, taken
    if len(values) == 1:
        return [values[0]], None, walked, taken
    targets = sorted({target for (line, target)
                      in records["aliases"].get(name, [])
                      if line is None or line <= limit})
    attrs = sorted({(text, module, attr) for (line, text, module, attr)
                    in records["attrs"].get(name, [])
                    if line is None or line <= limit})
    if len(targets) > 1 or len(attrs) > 1 or (targets and attrs):
        return None, REFUSED_NAME_MIXED % name, walked, taken
    if targets:
        return _resolve(targets[0], records, context, limit, walked, taken)
    if attrs:
        text, module, attr = attrs[0]
        if module not in context["imported"]:
            return None, REFUSED_ATTR_NOT_IMPORTED % text, walked, \
                taken + [text]
        table = _module_bindings(context["root"], module)
        if table is None:
            return None, REFUSED_ATTR_MISSING % text, walked, taken + [text]
        literals, names = table
        if attr not in names:
            return None, REFUSED_ATTR_MISSING % text, walked, taken + [text]
        found = literals.get(attr) or []
        if len(found) > 1:
            return None, REFUSED_NAME_MIXED % text, walked, taken + [text]
        if len(found) == 1:
            return [found[0]], None, walked, taken + [text]
        return None, REFUSED_ATTR_NON_CONSTANT % text, walked, taken + [text]
    return None, REFUSED_NAME_UNBOUND % name, walked, taken


def position_tables(text, scope=None, root=None):
    """The shipped alias tables plus the three shapes this face reads."""
    tables = _base().alias_tables(text, scope)
    if tables is None:
        return None
    tree = tables.get("tree")
    records = _binding_records(tree, scope or SCOPE_MODULE)
    out = dict(tables)
    out["position_records"] = records
    out["position_imports"] = sorted(_imports_of(tree)) if tree else []
    out["position_root"] = BASE if root is None else root
    return out


def position_entry(name, text, scope, line, tables=None, root=None):
    """The shipped alias-chain answer, carried, plus this face own re-read."""
    base = _base()
    root_path = BASE if root is None else root
    tables_full = (position_tables(text, scope, root_path)
                   if tables is None else tables)
    plain = (base.alias_entry(name, text, scope, line, tables_full)
             if tables_full is not None
             else base.alias_entry(name, text, scope, line))
    got = dict(plain)
    got["base_alias_state"] = plain.get("state")
    got["base_alias_reason"] = plain.get("reason")
    got["base_alias_value"] = plain.get("value")
    got["base_alias_source"] = plain.get("source")
    got["base_alias_chain"] = list(plain.get("alias_chain") or [])
    got["position_state"] = None
    got["position_reason"] = None
    got["position_value"] = None
    got["position_chain"] = []
    got["position_source"] = SOURCE_BASE
    if tables_full is None:
        return got
    records = tables_full["position_records"]
    context = {"root": tables_full["position_root"],
               "imported": set(tables_full["position_imports"])}
    values, why, walked, taken = _resolve(
        name, records, context, line)
    got["position_chain"] = list(walked) + list(taken)
    if values is not None:
        got["position_state"] = STATE_OK
        got["position_value"] = values[0]
    else:
        got["position_state"] = STATE_REFUSED
        got["position_reason"] = why
    plain_state = plain.get("state")
    if why and why.startswith("not-yet-bound:"):
        got["state"] = STATE_REFUSED
        got["reason"] = why
        got["value"] = None
        got["source"] = SOURCE_POSITION
        got["position_source"] = SOURCE_POSITION
        return got
    if plain_state == STATE_OK:
        return got
    if values is not None:
        got["state"] = STATE_OK
        got["reason"] = None
        got["value"] = values[0]
        got["source"] = SOURCE_POSITION
        got["position_source"] = SOURCE_POSITION
        return got
    if why and why.startswith("attr-"):
        got["state"] = STATE_REFUSED
        got["reason"] = why
        got["value"] = None
        got["source"] = SOURCE_POSITION
        got["position_source"] = SOURCE_POSITION
    return got


def position_report(text, root=None):
    """One row per loop the shipped alias reading publishes."""
    base = _base()
    shipped = base.alias_report(text)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        names = set(loop["followed"]) | set(loop["refused"])
        for item in loop.get("arms") or []:
            names.add(item["name"])
        scope = loop["scope"]
        if scope not in cache:
            cache[scope] = position_tables(text, scope, root)
        tables = cache[scope]
        if tables is not None:
            residual = _base()._base()
            names |= residual._guarded_names(
                tables, loop["scope"], loop["line"])
            names |= residual._with_as_names(
                tables, loop["scope"], loop["line"])
        row = {"line": loop["line"], "kind": loop["kind"],
               "scope": loop["scope"], "followed": {}, "refused": {},
               "resolved_by_position": [], "chains": {},
               "not_yet_bound": {}, "attributes": {},
               "base_alias_followed": dict(loop["followed"]),
               "base_alias_refused": dict(loop["refused"]),
               "base_alias_chains": dict(loop.get("chains") or {}),
               "base_alias_resolved": list(
                   loop.get("resolved_by_alias") or [])}
        for name in sorted(names):
            got = position_entry(name, text, row["scope"], row["line"],
                                tables, root)
            if got.get("state") == STATE_OK:
                row["followed"][name] = got["value"]
                if got.get("position_source") == SOURCE_POSITION:
                    row["resolved_by_position"].append(name)
            else:
                row["refused"][name] = got.get("reason")
            if got.get("position_chain"):
                row["chains"][name] = got["position_chain"]
            if (got.get("position_reason") or "").startswith(
                    "not-yet-bound:"):
                row["not_yet_bound"][name] = got["position_reason"]
            for hop in got.get("position_chain") or []:
                if "." in hop:
                    row["attributes"][name] = hop
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["position_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in position_report(text, root)["loops"]:
        row["position_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped alias audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise AliasPositionError(E_NO_ROOT, "not a directory: %s" % root_path)
    base = _base()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise AliasPositionError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (
        SEAMS_POSITION_STALE
        if report.get("verdict") == base.SEAMS_ALIAS_STALE
        else SEAMS_POSITION_COVERED)
    report["base_tool"] = base.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except AliasPositionError as exc:
        return {"tool": LABEL, "verdict": SEAMS_POSITION_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_POSITION_COVERED:
        raise AliasPositionError(report["verdict"], "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="read alias position, walrus edges and one attribute hop")
    parser.add_argument("--root", default=BASE,
                        help="directory of probe modules to read")
    parser.add_argument("--json", action="store_true", help="machine output")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 5
    if not os.path.isdir(args.root):
        sys.stderr.write("%s: not a directory: %s\n" % (E_NO_ROOT,
                                                        args.root))
        return 3
    report = reading(args.root)
    if args.json:
        sys.stdout.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    else:
        sys.stdout.write("%s verdict=%s base=%s\n"
                         % (LABEL, report["verdict"],
                            report.get("base_tool", "?")))
        for name in sorted(report["counts"]):
            sys.stdout.write("  %s=%s\n" % (name, report["counts"][name]))
        for row in report["probes"]:
            if row["verdict"] != COVERED:
                continue
            loops = row.get("position_loops") or []
            resolved = sum(len(loop["resolved_by_position"])
                           for loop in loops)
            named = sum(len(loop["not_yet_bound"]) + len(loop["attributes"])
                        for loop in loops)
            sys.stdout.write(
                "  probe %s position_loops=%d position_resolved=%d "
                "position_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_POSITION_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())