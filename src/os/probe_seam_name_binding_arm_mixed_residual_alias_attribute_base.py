"""AC-PNDA1..AC-PNDA6: the alias attribute-base face (R2559).

Criteria were pinned in state/queue/tech.md:595 at R2557 BEFORE this code
existed.

What this proves: MEASURED at R2557 on the alias-position face own reader, an
attribute whose BASE is a function parameter or a local (`node.value` inside a
probe own `_collect_node`) reads `attr-not-imported`, so the module-import check
cannot tell a parameter from a module the probe forgot to import; a
package-relative module (`import pkg.mod` then `B = pkg.mod.ATTR`) is never
found because the hop joins `<mod>.py` on the root; and a helper constant
declared by a walrus, or inside a function body, reads `attr-missing` or
`attr-non-constant` because only module-level plain and annotated assignments
are read.

This face asks the shipped position answer FIRST and carries every key it
already published, unchanged, on every row, then re-reads only a refusal whose
reason names an attribute hop:
  * a base that is a parameter or a local of this tree is NAMED
    attr-base-local:<base>, so a parameter is never reported as a module the
    probe forgot to import;
  * a base that is neither imported nor local keeps the shipped
    attr-not-imported:<text>, so a genuinely absent module is still named;
  * a dotted module path (pkg.mod.ATTR) is resolved by joining the FULL dotted
    path onto the root, so a package-relative attribute is found when the file
    is on disk;
  * a helper constant declared by a walrus or inside a function body is read,
    and two different values read name-mixed rather than being picked.

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

LABEL = "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-base"

E_ARGS = "E_PNDA_ARGS"
E_NO_ROOT = "E_PNDA_NO_ROOT"

STATE_OK = "ok"
STATE_ARMS = "arms"
STATE_REFUSED = "refused"

REFUSED_ATTR_BASE_LOCAL = "attr-base-local:%s"
REFUSED_ATTR_MISSING = "attr-missing:%s"
REFUSED_ATTR_NON_CONSTANT = "attr-non-constant:%s"
REFUSED_ATTR_NOT_IMPORTED = "attr-not-imported:%s"
REFUSED_NAME_MIXED = "name-mixed:%s"

SOURCE_BASE = "shipped"
SOURCE_ATTRIBUTE = "attribute-base"

SCOPE_MODULE = "module"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_ATTRIBUTE_COVERED = "SEAMS-ATTRIBUTE-BASE-COVERED"
SEAMS_ATTRIBUTE_STALE = "SEAMS-ATTRIBUTE-BASE-STALE"

MAX_CHAIN = 8


class AliasAttributeError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _position():
    """The shipped alias-position face this module extends."""
    import probe_seam_name_binding_arm_mixed_residual_alias_position
    return probe_seam_name_binding_arm_mixed_residual_alias_position


def _parse(text):
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _str_constant(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _split_attribute(text):
    """(base, attr) of a dotted text, splitting at the LAST dot."""
    if "." not in text:
        return text, ""
    base, _, attr = text.rpartition(".")
    return base, attr


def _local_bases(tree):
    """Every name that is a function parameter or a local of this tree.

    A base rooted here can never be a module the probe forgot to import, so it
    is named separately (AC-PNDA1).
    """
    found = set()
    if tree is None:
        return found
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.Lambda)):
            args = node.args
            for group in (args.posonlyargs, args.args, args.kwonlyargs):
                for arg in group:
                    found.add(arg.arg)
            if args.vararg is not None:
                found.add(args.vararg.arg)
            if args.kwarg is not None:
                found.add(args.kwarg.arg)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found.add(target.id)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if isinstance(node.target, ast.Name):
                found.add(node.target.id)
        elif isinstance(node, ast.NamedExpr):
            if isinstance(node.target, ast.Name):
                found.add(node.target.id)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            target = node.target
            if isinstance(target, ast.Name):
                found.add(target.id)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if isinstance(item.optional_vars, ast.Name):
                    found.add(item.optional_vars.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                found.add((alias.asname or alias.name).split(".")[0])
    return found


def _module_file(root, dotted):
    """The same-root file a dotted module path names, or None."""
    if not dotted:
        return None
    path = os.path.join(root, *dotted.split(".")) + ".py"
    if os.path.isfile(path):
        return path
    return None


def _module_constants(root, dotted):
    """(str constants, every bound name) of one dotted module file.

    The module body is read as the shipped readers read it, and one level of
    FUNCTION bodies is read too so a constant declared by a walrus or inside a
    function body is found rather than reported missing (AC-PNDA4).
    """
    path = _module_file(root, dotted)
    if path is None:
        return None
    try:
        text = _read(path)
    except OSError:
        return None
    tree = _parse(text)
    if tree is None:
        return None
    literals = {}
    names = set()

    def take(node):
        pairs = []
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    pairs.append((target.id, node.value))
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None:
                pairs.append((node.target.id, node.value))
        elif isinstance(node, ast.Expr):
            inner = node.value
            if isinstance(inner, ast.NamedExpr):
                if isinstance(inner.target, ast.Name):
                    pairs.append((inner.target.id, inner.value))
        for name, value in pairs:
            names.add(name)
            literal = _str_constant(value)
            if literal is not None:
                literals.setdefault(name, set()).add(literal)

    for node in tree.body:
        take(node)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack = [node.body]
            while stack:
                block = stack.pop()
                for inner in block:
                    take(inner)
                    for field in ("body", "orelse", "finalbody"):
                        nested = getattr(inner, field, None)
                        if isinstance(nested, list):
                            stack.append(nested)
    return (dict((name, sorted(values))
                 for name, values in literals.items()), names)


def _resolve_attribute(text, context, locals_):
    """Resolve ONE attribute hop, or NAMED the reason it cannot be one."""
    base, attr = _split_attribute(text)
    if not attr:
        return None, REFUSED_ATTR_MISSING % text, []
    dotted = "." in base
    if not dotted and base not in context["imported"]:
        if base in locals_:
            return None, REFUSED_ATTR_BASE_LOCAL % base, [text]
        return None, REFUSED_ATTR_NOT_IMPORTED % text, [text]
    table = _module_constants(context["root"], base)
    if table is None:
        if dotted:
            return None, REFUSED_ATTR_NOT_IMPORTED % text, [text]
        return None, REFUSED_ATTR_MISSING % text, [text]
    literals, names = table
    if attr not in names:
        return None, REFUSED_ATTR_MISSING % text, [text]
    found = literals.get(attr) or []
    if len(found) > 1:
        return None, REFUSED_NAME_MIXED % text, [text]
    if len(found) == 1:
        return [found[0]], None, [text]
    return None, REFUSED_ATTR_NON_CONSTANT % text, [text]


def attribute_tables(text, scope=None, root=None):
    """The shipped position tables plus what this face needs to name a base."""
    pos = _position()
    tables = pos.position_tables(text, scope, root)
    if tables is None:
        return None
    out = dict(tables)
    tree = tables.get("tree")
    out["attribute_locals"] = sorted(_local_bases(tree))
    out["attribute_root"] = BASE if root is None else root
    return out


def attribute_entry(name, text, scope, line, tables=None, root=None):
    """The shipped position answer, carried, plus this face own re-read."""
    pos = _position()
    root_path = BASE if root is None else root
    tables_full = (attribute_tables(text, scope, root_path)
                   if tables is None else tables)
    plain = (pos.position_entry(name, text, scope, line, tables_full)
             if tables_full is not None
             else pos.position_entry(name, text, scope, line))
    got = dict(plain)
    for key in sorted(plain):
        got.setdefault(key, plain[key])
    got["base_position_state"] = plain.get("state")
    got["base_position_reason"] = plain.get("reason")
    got["base_position_value"] = plain.get("value")
    got["base_position_source"] = plain.get("source")
    got["base_position_chain"] = list(plain.get("position_chain") or [])
    got["attr_state"] = None
    got["attr_reason"] = None
    got["attr_value"] = None
    got["attr_chain"] = []
    got["attr_source"] = SOURCE_BASE
    if tables_full is None:
        return got
    if plain.get("state") == STATE_OK:
        return got
    why = plain.get("reason") or ""
    if not why.startswith("attr-"):
        return got
    text_hint = why.split(":", 1)[1] if ":" in why else ""
    context = {"root": tables_full["attribute_root"],
               "imported": set(tables_full.get("position_imports") or [])}
    locals_ = set(tables_full.get("attribute_locals") or [])
    values, named, chain = _resolve_attribute(text_hint, context, locals_)
    got["attr_chain"] = list(chain)
    got["attr_source"] = SOURCE_ATTRIBUTE
    if values is not None:
        got["attr_state"] = STATE_OK
        got["attr_value"] = values[0]
        got["state"] = STATE_OK
        got["reason"] = None
        got["value"] = values[0]
        return got
    got["attr_state"] = STATE_REFUSED
    got["attr_reason"] = named
    if why.startswith("attr-not-imported:"):
        got["state"] = STATE_REFUSED
        got["reason"] = named
        got["value"] = None
    elif named.startswith("attr-base-local:"):
        got["state"] = STATE_REFUSED
        got["reason"] = named
        got["value"] = None
    elif named.startswith("name-mixed:"):
        got["state"] = STATE_REFUSED
        got["reason"] = named
        got["value"] = None
    elif values is None and named.startswith(("attr-missing:",)):
        got["state"] = STATE_REFUSED
        got["reason"] = named
        got["value"] = None
    return got


def attribute_report(text, root=None):
    """One row per loop the shipped position reading publishes."""
    pos = _position()
    shipped = pos.position_report(text, root)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["attr_followed"] = {}
        row["attr_refused"] = {}
        row["attr_chains"] = {}
        row["attr_resolved"] = []
        row["attr_local_bases"] = []
        names = set(loop.get("followed") or {})
        names |= set(loop.get("refused") or {})
        names |= set(row.get("not_yet_bound") or {})
        names |= set(row.get("attributes") or {})
        for item in loop.get("arms") or []:
            names.add(item["name"])
        scope = loop["scope"]
        if scope not in cache:
            cache[scope] = attribute_tables(text, scope, root)
        tables = cache[scope]
        if tables is not None:
            row["attr_local_bases"] = list(
                tables.get("attribute_locals") or [])
        for name in sorted(names):
            got = attribute_entry(name, text, row["scope"], row["line"],
                                  tables, root)
            if got.get("attr_chain"):
                row["attr_chains"][name] = got["attr_chain"]
            if got.get("attr_source") != SOURCE_ATTRIBUTE:
                continue
            if got.get("attr_state") == STATE_OK:
                row["attr_followed"][name] = got["attr_value"]
                row["attr_resolved"].append(name)
            else:
                row["attr_refused"][name] = got.get("attr_reason")
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["attribute_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in attribute_report(text, root)["loops"]:
        row["attribute_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped position audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise AliasAttributeError(E_NO_ROOT, "not a directory: %s" % root_path)
    pos = _position()
    try:
        report = pos.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise AliasAttributeError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (
        SEAMS_ATTRIBUTE_STALE
        if report.get("verdict") == pos.SEAMS_POSITION_STALE
        else SEAMS_ATTRIBUTE_COVERED)
    report["base_tool"] = pos.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except AliasAttributeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_ATTRIBUTE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_ATTRIBUTE_COVERED:
        raise AliasAttributeError(report["verdict"], "probe seams are stale")


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="name an attribute BASE and resolve a dotted module hop")
    parser.add_argument("--root", default=BASE,
                        help="directory of probe modules to read")
    parser.add_argument("--module", default=None,
                        help="read one module by name (bounded leg)")
    parser.add_argument("--json", action="store_true", help="machine output")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 5
    if not os.path.isdir(args.root):
        sys.stderr.write("%s: not a directory: %s\n" % (E_NO_ROOT,
                                                        args.root))
        return 3
    report = reading(args.root, args.module)
    if args.json:
        sys.stdout.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    else:
        sys.stdout.write("%s verdict=%s base=%s probes=%d\n"
                         % (LABEL, report["verdict"],
                            report.get("base_tool", "?"),
                            len(report.get("probes") or [])))
        for name in sorted(report["counts"]):
            sys.stdout.write("  %s=%s\n" % (name, report["counts"][name]))
        for row in report["probes"]:
            if row["verdict"] != COVERED:
                continue
            loops = row.get("attribute_loops") or []
            resolved = sum(len(loop["attr_resolved"]) for loop in loops)
            named = sum(len(loop["attr_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s attribute_loops=%d attr_resolved=%d "
                "attr_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_ATTRIBUTE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())