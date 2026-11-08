"""AC-PNDB1..AC-PNDB6: the alias attribute-predicate face (R2561).

Criteria were pinned in state/queue/tech.md:597 at R2559 BEFORE this code
existed.

What this proves: MEASURED at R2559 on the alias attribute-base face own reader
(src/os/limits_attribute_base_R2559.py, four shapes run against one private
world): a WALRUS-bound attribute alias (`(B := h.ATTR)`) comes back with
state=None and NO reason at all, so the caller is told nothing; a SUBSCRIPT base
(`items[0].ATTR`) is published as `attr-not-imported:?.ATTR` because the dotted
text only understands Name and Attribute chains, so a real base is reported as a
question mark; a package own constant (`pkg3/__init__.py` holding ATTR) reads
`attr-missing:pkg3.ATTR` because the hop asks for `pkg3.py` and never for a
package index; and a helper name bound by `with ... as NAME` reads `attr-missing`
because the extended table collects only assignment, annotation and walrus forms.

This face asks the shipped attribute-base reading FIRST and carries every key it
published, unchanged, on every row, then re-reads only a refusal:
  * the base text is taken from the ACTUAL binding the loop followed, so a
    subscript or call base is published as its own text (`items[0]`,
    `factory()`) and is never reported as `?` (AC-PNDB2);
  * a walrus-bound attribute edge is an edge like any other: it resolves when
    the hop resolves and is NAMED `attr-walrus:<text>` when it does not, instead
    of publishing no reason at all (AC-PNDB1);
  * a package own `__init__.py` is joined as well as `<mod>.py`, so a constant
    declared in a package index resolves through the dotted path (AC-PNDB3);
  * a helper name bound by `with ... as NAME` is read, resolves when that module
    also binds it to exactly one string literal, and reads `name-mixed` when it
    carries two values (AC-PNDB4).

Nothing is imported and nothing is evaluated: every value comes from reading
source text. Stdlib only, ASCII source, zero network, no clock.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import ast  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_base as PNDA  # noqa: E402

LABEL = "os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-predicate"

E_ARGS = "E_PNDB_ARGS"
E_NO_ROOT = "E_PNDB_NO_ROOT"

STATE_OK = PNDA.STATE_OK
STATE_REFUSED = PNDA.STATE_REFUSED

REFUSED_ATTR_SUBSCRIPT = "attr-subscript-base:%s"
REFUSED_ATTR_CALL = "attr-call-base:%s"
REFUSED_ATTR_WALRUS = "attr-walrus:%s"
REFUSED_ATTR_WITH_AS = "attr-with-as:%s"

SOURCE_PREDICATE = "attribute-predicate"

COVERED = PNDA.COVERED
MISSING_SEAM = PNDA.MISSING_SEAM
OUT_OF_SCOPE = PNDA.OUT_OF_SCOPE
UNREADABLE = PNDA.UNREADABLE
HISTORICAL = PNDA.HISTORICAL

SEAMS_PREDICATE_COVERED = "SEAMS-PREDICATE-COVERED"
SEAMS_PREDICATE_STALE = "SEAMS-PREDICATE-STALE"

MAX_CHAIN = 8


class PredicateError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


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


def base_text(node):
    """The base text of a value expression, without ever inventing a `?`."""
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        inner = base_text(node.value)
        return ("%s.%s" % (inner, node.attr)) if inner else node.attr
    if isinstance(node, ast.Subscript):
        inner = base_text(node.value)
        try:
            slice_text = ast.unparse(node.slice)
        except Exception:
            slice_text = "?"
        return "%s[%s]" % (inner, slice_text) if inner else "?[%s]" % slice_text
    if isinstance(node, ast.Call):
        func = base_text(node.func)
        return ("%s()" % func) if func else "()"
    try:
        return ast.unparse(node)
    except Exception:
        return "?"


def _dotted_only(text):
    """True when a base text is a plain dotted chain of names."""
    if not text:
        return False
    parts = text.split(".")
    for part in parts:
        if not part.isidentifier():
            return False
    return True


def _scope_blocks(tree):
    """(label, block) pairs: the module body and each function body."""
    blocks = [("module", tree.body)]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            blocks.append(("function:%s" % node.name, node.body))
    return blocks


def _collect_bindings(tree, name, scope):
    """Bindings of one name in one scope, in source order.

    Each entry is (line, kind, value_node, extra) where kind is one of
    assign / annotate / walrus / with-as and extra carries the with-as context
    expression text for the last of those.
    """
    found = []
    if tree is None:
        return found

    def walk(block):
        for node in block:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        found.append((node.lineno, "assign", node.value, None))
            elif isinstance(node, ast.AnnAssign):
                if (isinstance(node.target, ast.Name) and node.target.id == name
                        and node.value is not None):
                    found.append((node.lineno, "annotate", node.value, None))
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if isinstance(item.optional_vars, ast.Name) \
                            and item.optional_vars.id == name:
                        found.append((node.lineno, "with-as", item.context_expr,
                                      base_text(item.context_expr)))
            for field in ("body", "orelse", "finalbody"):
                nested = getattr(node, field, None)
                if isinstance(nested, list):
                    walk(nested)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(node):
                    if isinstance(inner, ast.NamedExpr) \
                            and isinstance(inner.target, ast.Name) \
                            and inner.target.id == name:
                        found.append((getattr(inner, "lineno", 0), "walrus",
                                      inner.value, None))

    for label, block in _scope_blocks(tree):
        if label == scope:
            walk(block)
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.NamedExpr):
            inner = node.value
            if isinstance(inner.target, ast.Name) and inner.target.id == name:
                found.append((node.lineno, "walrus", inner.value, None))
    found.sort(key=lambda item: item[0])
    return found


def _pick_binding(bindings, line):
    """The binding the loop followed: last one at or before the loop line."""
    before = [item for item in bindings if item[0] and item[0] <= line]
    if before:
        return before[-1]
    return bindings[-1] if bindings else None


def _module_file(root, dotted):
    """Same-root `<dotted>.py`, else the package own `__init__.py` (AC-PNDB3)."""
    if not dotted or not _dotted_only(dotted):
        return None
    plain = os.path.join(root, *dotted.split(".")) + ".py"
    if os.path.isfile(plain):
        return plain
    index = os.path.join(root, *dotted.split("."), "__init__.py")
    if os.path.isfile(index):
        return index
    return None


def module_constants(root, dotted):
    """(str constants, every bound name) of one dotted module, with-as included.

    MEASURED limit this extension closes: the shipped table collects only
    assignment, annotation and walrus forms, so a name bound by `with ... as
    NAME` reads attr-missing although it is bound (AC-PNDB4).
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
    for node in ast.walk(tree):
        groups = []
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    groups.append((target.id, node.value))
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None:
                groups.append((node.target.id, node.value))
        elif isinstance(node, ast.Expr):
            inner = node.value
            if isinstance(inner, ast.NamedExpr) \
                    and isinstance(inner.target, ast.Name):
                groups.append((inner.target.id, inner.value))
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if isinstance(item.optional_vars, ast.Name):
                    groups.append((item.optional_vars.id, None))
        for name, value in groups:
            names.add(name)
            literal = _str_constant(value) if value is not None else None
            if literal is not None:
                literals.setdefault(name, set()).add(literal)
    return (dict((name, sorted(values))
                 for name, values in literals.items()), names)


def predicate_tables(text, scope=None, root=None):
    """The attribute-base tables plus the source text this face needs."""
    tables = PNDA.attribute_tables(text, scope, root)
    if tables is None:
        return None
    out = dict(tables)
    out["predicate_tree"] = tables.get("tree")
    out["predicate_root"] = tables.get("attribute_root")
    return out


def _follow(name, tree, scope, line):
    """Follow name edges to the ACTUAL value expression, at most MAX_CHAIN.

    A loop variable is normally bound to another NAME (`KEY = B`) and only the
    end of that chain carries the attribute, so the edge is taken from the last
    hop rather than from the first. Returns (kind, node, extra) or None.
    """
    seen = set()
    current = name
    for _ in range(MAX_CHAIN):
        if current in seen:
            return None
        seen.add(current)
        picked = _pick_binding(_collect_bindings(tree, current, scope), line)
        if picked is None:
            return None
        _, kind, value, extra = picked
        if kind == "with-as":
            return ("with-as", None, extra)
        node = value
        walrus = False
        if isinstance(node, ast.NamedExpr):
            node = node.value
            walrus = True
        if isinstance(node, ast.Name):
            current = node.id
            continue
        if walrus:
            return ("walrus-attr", node, None)
        return (kind, node, None)
    return None


def predicate_entry(name, text, scope, line, tables=None, root=None):
    """The shipped attribute-base answer, carried, plus this face own re-read."""
    root_path = BASE if root is None else root
    tables_full = (predicate_tables(text, scope, root_path)
                   if tables is None else tables)
    shipped = (PNDA.attribute_entry(name, text, scope, line, tables_full, root)
               if tables_full is not None
               else PNDA.attribute_entry(name, text, scope, line, root=root))
    got = dict(shipped)
    for key in sorted(shipped):
        got.setdefault(key, shipped[key])
    got["base_attr_state"] = shipped.get("attr_state")
    got["base_attr_reason"] = shipped.get("attr_reason")
    got["base_attr_value"] = shipped.get("attr_value")
    got["base_attr_chain"] = list(shipped.get("attr_chain") or [])
    got["pred_state"] = None
    got["pred_reason"] = None
    got["pred_value"] = None
    got["pred_chain"] = []
    got["pred_edge"] = None
    got["pred_source"] = PNDA.SOURCE_BASE
    if tables_full is None:
        return got
    if shipped.get("state") == STATE_OK:
        return got
    tree = tables_full.get("predicate_tree")
    root_dir = tables_full["predicate_root"]
    imported = set(tables_full.get("position_imports") or [])
    locals_ = set(tables_full.get("attribute_locals") or [])
    picked = _follow(name, tree, scope, line)
    got["pred_source"] = SOURCE_PREDICATE
    if picked is None:
        return got
    kind, value, extra = picked
    got["pred_edge"] = kind
    if kind == "with-as":
        got["pred_state"] = STATE_REFUSED
        got["pred_reason"] = REFUSED_ATTR_WITH_AS % (extra or name)
        got["pred_chain"] = [extra or name]
        if shipped.get("state") is None:
            got["state"] = STATE_REFUSED
            got["reason"] = got["pred_reason"]
            got["value"] = None
        return got
    node = value
    if not isinstance(node, ast.Attribute):
        return got
    attr = node.attr
    base = base_text(node.value)
    chain = ["%s.%s" % (base, attr)]
    got["pred_chain"] = chain
    if not base or base == "?" or not _dotted_only(base):
        if base and ("[" in base or base.endswith(")")):
            word = (REFUSED_ATTR_SUBSCRIPT if "[" in base
                    else REFUSED_ATTR_CALL)
            got["pred_state"] = STATE_REFUSED
            got["pred_reason"] = word % ("%s.%s" % (base, attr))
        elif got["pred_edge"] == "walrus-attr":
            got["pred_state"] = STATE_REFUSED
            got["pred_reason"] = REFUSED_ATTR_WALRUS % ("%s.%s" % (base, attr))
        if got["pred_reason"]:
            got["state"] = STATE_REFUSED
            got["reason"] = got["pred_reason"]
            got["value"] = None
        return got
    if base not in imported and base.split(".")[0] not in imported:
        if base.split(".")[0] in locals_:
            got["pred_state"] = STATE_REFUSED
            got["pred_reason"] = PNDA.REFUSED_ATTR_BASE_LOCAL % base
            got["state"] = STATE_REFUSED
            got["reason"] = got["pred_reason"]
            got["value"] = None
            return got
        got["pred_state"] = STATE_REFUSED
        got["pred_reason"] = PNDA.REFUSED_ATTR_NOT_IMPORTED % ("%s.%s"
                                                              % (base, attr))
        return got
    table = module_constants(root_dir, base)
    if table is None:
        got["pred_state"] = STATE_REFUSED
        got["pred_reason"] = PNDA.REFUSED_ATTR_MISSING % ("%s.%s"
                                                         % (base, attr))
        return got
    literals, names = table
    if attr not in names:
        got["pred_state"] = STATE_REFUSED
        got["pred_reason"] = PNDA.REFUSED_ATTR_MISSING % ("%s.%s"
                                                         % (base, attr))
        return got
    found = literals.get(attr) or []
    if len(found) > 1:
        got["pred_state"] = STATE_REFUSED
        got["pred_reason"] = PNDA.REFUSED_NAME_MIXED % ("%s.%s"
                                                       % (base, attr))
        got["state"] = STATE_REFUSED
        got["reason"] = got["pred_reason"]
        got["value"] = None
        return got
    if len(found) == 1:
        got["pred_state"] = STATE_OK
        got["pred_value"] = found[0]
        got["state"] = STATE_OK
        got["reason"] = None
        got["value"] = found[0]
        got["attr_state"] = STATE_OK
        got["attr_value"] = found[0]
        got["attr_reason"] = None
        return got
    got["pred_state"] = STATE_REFUSED
    got["pred_reason"] = PNDA.REFUSED_ATTR_NON_CONSTANT % ("%s.%s"
                                                          % (base, attr))
    if shipped.get("state") is None:
        got["state"] = STATE_REFUSED
        got["reason"] = got["pred_reason"]
        got["value"] = None
    return got


def predicate_report(text, root=None):
    """One row per loop the attribute-base reading publishes."""
    shipped = PNDA.attribute_report(text, root)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["pred_followed"] = {}
        row["pred_refused"] = {}
        row["pred_chains"] = {}
        row["pred_edges"] = {}
        row["pred_resolved"] = []
        names = set(loop.get("followed") or {})
        names |= set(loop.get("refused") or {})
        names |= set(loop.get("attr_followed") or {})
        names |= set(loop.get("attr_refused") or {})
        names |= set(loop.get("not_yet_bound") or {})
        names |= set(loop.get("attributes") or {})
        for item in loop.get("arms") or []:
            names.add(item["name"])
        scope = loop["scope"]
        if scope not in cache:
            cache[scope] = predicate_tables(text, scope, root)
        tables = cache[scope]
        for name in sorted(names):
            got = predicate_entry(name, text, scope, loop["line"], tables, root)
            if got.get("pred_edge"):
                row["pred_edges"][name] = got["pred_edge"]
            if got.get("pred_chain"):
                row["pred_chains"][name] = got["pred_chain"]
            if got.get("pred_source") != SOURCE_PREDICATE:
                continue
            if got.get("pred_state") == STATE_OK:
                row["pred_followed"][name] = got["pred_value"]
                row["pred_resolved"].append(name)
            elif got.get("pred_reason"):
                row["pred_refused"][name] = got["pred_reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["predicate_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in predicate_report(text, root)["loops"]:
        row["predicate_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped attribute-base audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise PredicateError(E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNDA.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise PredicateError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_PREDICATE_STALE
                         if report.get("verdict") == PNDA.SEAMS_ATTRIBUTE_STALE
                         else SEAMS_PREDICATE_COVERED)
    report["base_tool"] = PNDA.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except PredicateError as exc:
        return {"tool": LABEL, "verdict": SEAMS_PREDICATE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_PREDICATE_COVERED:
        raise PredicateError(report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="name a walrus, subscript, call, package or with-as "
                    "attribute base")
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
        sys.stderr.write("%s: not a directory: %s\n" % (E_NO_ROOT, args.root))
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
            loops = row.get("predicate_loops") or []
            resolved = sum(len(loop["pred_resolved"]) for loop in loops)
            named = sum(len(loop["pred_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s predicate_loops=%d pred_resolved=%d pred_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_PREDICATE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())