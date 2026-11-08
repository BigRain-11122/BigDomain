"""AC-PNDC1..AC-PNDC6: the alias attribute import-alias face (R2563).

Criteria were pinned in state/queue/tech.md:599 at R2561 BEFORE this code
existed.

What this proves, MEASURED at R2561 on the alias attribute-predicate face and
re-measured at R2563 with src/os/limits_attribute_import_alias_R2563.py (every
shape against one private world where the honest answer is `b`):
  (1) a PLAIN `import helper` base reads state=None with NO reason at all, so a
      row is silent rather than refused;
  (2) `import helper as h` read as `h.ATTR` reads attr-base-local:h, because the
      import set records the module name and the alias is then mistaken for a
      local;
  (3) a module reached by `with hw2 as m` reads attr-base-local:m, the same
      mistake through a with-as binding;
  (4) a helper constant that is ITSELF an alias (`ATTR = BASE` with
      `BASE = "b"`) reads attr-non-constant and one re-exported by
      `from hc import ATTR` reads attr-missing, so a two-step constant is never
      followed - and a helper that carries TWO values through an alias reads
      `ok` on the predicate face, i.e. it OVER-resolves.

This face asks the shipped attribute-predicate reading FIRST and carries every
key it published, unchanged, on every row, then re-reads the attribute base:
  * a plain `import m` base resolves through `<m>.py` (or the package index) and
    is NAMED when it cannot be resolved, never silent (AC-PNDC1);
  * a module bound by `import m as x` resolves through the ACTUAL module name
    and is never published as attr-base-local:<alias> (AC-PNDC2);
  * a `with ... as NAME` binding whose context is a module resolves through that
    module and is named attr-with-as otherwise (AC-PNDC3);
  * a helper constant that is an alias of another constant is followed to its
    literal, and a helper carrying two values still reads name-mixed - which is
    narrower than the shipped reading, which resolved one of them (AC-PNDC4);
  * a helper constant re-exported by `from other import NAME` resolves through
    that module (AC-PNDC5).

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
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_scope as PNDB  # noqa: E402

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope")

E_ARGS = "E_PNDC_ARGS"
E_NO_ROOT = "E_PNDC_NO_ROOT"

STATE_OK = PNDB.STATE_OK
STATE_REFUSED = PNDB.STATE_REFUSED

REFUSED_ATTR_PLAIN_IMPORT = "attr-plain-import:%s"
REFUSED_ATTR_IMPORT_ALIAS = "attr-import-alias:%s"
REFUSED_ATTR_WITH_AS = "attr-with-as:%s"
REFUSED_ATTR_SILENT = "attr-base-silent:%s"

SOURCE_IMPORT_ALIAS = "import-alias"

COVERED = PNDB.COVERED
MISSING_SEAM = PNDB.MISSING_SEAM
OUT_OF_SCOPE = PNDB.OUT_OF_SCOPE
UNREADABLE = PNDB.UNREADABLE
HISTORICAL = PNDB.HISTORICAL

SEAMS_IMPORT_ALIAS_COVERED = "SEAMS-IMPORT-ALIAS-COVERED"
SEAMS_IMPORT_ALIAS_STALE = "SEAMS-IMPORT-ALIAS-STALE"

MAX_CHAIN = 8


class ImportAliasError(Exception):
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


def _module_file(root, dotted):
    """Same-root `<dotted>.py`, else the package own `__init__.py`."""
    if not dotted:
        return None
    parts = dotted.split(".")
    for part in parts:
        if not part.isidentifier():
            return None
    plain = os.path.join(root, *parts) + ".py"
    if os.path.isfile(plain):
        return plain
    index = os.path.join(root, *parts, "__init__.py")
    if os.path.isfile(index):
        return index
    return None


def import_bindings(tree):
    """Module-level bound name -> the module it actually names.

    `import m` binds m -> m; `import m as x` binds x -> m (AC-PNDC2). The
    shipped import set records only the module name, which is why an alias is
    later mistaken for a local.
    """
    out = {}
    if tree is None:
        return out
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                actual = alias.name
                bound = alias.asname or alias.name.split(".")[0]
                out[bound] = actual
    return out


def import_aliases(tree):
    """Bound names that are an ALIAS of the module, i.e. bound != actual."""
    aliases = {}
    for bound, actual in import_bindings(tree).items():
        if bound != actual.split(".")[0]:
            aliases[bound] = actual
    return aliases


def with_as_modules(tree, root):
    """`with ... as NAME` bindings: NAME -> module dotted text or None."""
    out = {}
    if tree is None:
        return out
    imports = import_bindings(tree)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                var = item.optional_vars
                if not isinstance(var, ast.Name):
                    continue
                context = item.context_expr
                if isinstance(context, ast.Name):
                    if context.id in imports:
                        out[var.id] = imports[context.id]
                        names.add(var.id)
                        continue
                    if _module_file(root, context.id) is not None:
                        out[var.id] = context.id
                        names.add(var.id)
                        continue
                out[var.id] = None
                names.add(var.id)
    return out


def _module_values(tree):
    """(values by name, re-exports by name, every bound name) of a module.

    Module-level control flow is read (an assignment inside an if / else / try /
    for block is still a value the name can carry), while function and class
    bodies are not entered: this reading stays a MODULE reading.
    """
    values = {}
    reexports = {}
    names = set()
    if tree is None:
        return values, reexports, names

    def walk(block):
        for node in block:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        values.setdefault(target.id, []).append(node.value)
                        names.add(target.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    names.add(node.target.id)
                    if node.value is not None:
                        values.setdefault(node.target.id,
                                          []).append(node.value)
            elif isinstance(node, ast.Expr) and isinstance(node.value,
                                                           ast.NamedExpr):
                inner = node.value
                if isinstance(inner.target, ast.Name):
                    values.setdefault(inner.target.id,
                                      []).append(inner.value)
                    names.add(inner.target.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for alias in node.names:
                        target = alias.asname or alias.name
                        reexports[target] = (node.module, alias.name)
                        names.add(target)
                else:
                    for alias in node.names:
                        names.add(alias.asname or alias.name.split(".")[0])
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                names.add(node.name)
                continue
            for field in ("body", "orelse", "finalbody"):
                nested = getattr(node, field, None)
                if isinstance(nested, list) and nested:
                    walk(nested)

    walk(tree.body)
    return values, reexports, names


def _local_literals(name, values, depth, seen):
    """Every literal a NAME can carry through plain name edges (fixpoint)."""
    key = ("name", name)
    if depth > MAX_CHAIN or key in seen:
        return set(), True
    seen = set(seen) | {key}
    literals = set()
    non_constant = False
    for node in values.get(name) or []:
        literal = _str_constant(node)
        if literal is not None:
            literals.add(literal)
            continue
        if isinstance(node, ast.Name) and node.id in values:
            inner, bad = _local_literals(node.id, values, depth + 1, seen)
            literals |= inner
            non_constant = non_constant or bad
            continue
        non_constant = True
    return literals, non_constant


def module_attribute(root, dotted, attr, depth=0, seen=()):
    """(decision, values, hop) for one attribute of one same-root module.

    decision is one of ok / mixed / non-constant / missing / no-module. A
    constant that is an alias of another constant is followed, and a re-export
    `from other import NAME` is followed through that module (AC-PNDC4/5).
    """
    key = (dotted, attr)
    if depth > MAX_CHAIN or key in seen:
        return ("non-constant", set(), "alias-cycle")
    seen = seen + (key,)
    path = _module_file(root, dotted)
    if path is None:
        return ("no-module", set(), "module")
    try:
        tree = _parse(_read(path))
    except OSError:
        return ("no-module", set(), "module")
    if tree is None:
        return ("non-constant", set(), "unparseable")
    values, reexports, names = _module_values(tree)
    hop = "direct"
    literals = set()
    non_constant = False
    if attr in values:
        literals, non_constant = _local_literals(attr, values, depth, seen)
    elif attr in reexports:
        module, original = reexports[attr]
        hop = "reexport"
        if original != attr:
            decision, inner, _ = module_attribute(root, module, original,
                                                  depth + 1, seen)
            return (decision, inner, hop)
        decision, literals, _ = module_attribute(root, module, original,
                                                 depth + 1, seen)
        if decision in ("ok", "mixed"):
            return (decision, literals, hop)
        return (decision, literals, hop)
    elif attr in names:
        non_constant = True
    else:
        return ("missing", set(), "attr")
    if len(literals) > 1 or (literals and non_constant):
        return ("mixed", literals, hop)
    if len(literals) == 1:
        return ("ok", literals, hop)
    return ("non-constant", set(), hop)


def import_alias_entry(name, text, scope, line, tables=None, root=None):
    """The shipped predicate answer, carried, plus this face own re-read."""
    root_path = BASE if root is None else root
    tables_full = (PNDB.predicate_tables(text, scope, root_path)
                   if tables is None else tables)
    shipped = PNDB.predicate_entry(name, text, scope, line, tables_full, root)
    got = dict(shipped)
    for key in sorted(shipped):
        got.setdefault(key, shipped[key])
    got["base_import_alias_state"] = shipped.get("pred_state")
    got["base_import_alias_reason"] = shipped.get("pred_reason")
    got["ia_state"] = None
    got["ia_reason"] = None
    got["ia_value"] = None
    got["ia_chain"] = []
    got["ia_hop"] = None
    got["ia_source"] = (PNDB.SOURCE_PREDICATE if tables_full is not None
                        else "shipped")
    tree = (tables_full or {}).get("predicate_tree")
    if tree is None:
        return got
    picked = PNDB._follow(name, tree, scope, line)
    if picked is None:
        return got
    kind, value, extra = picked
    node = value
    if isinstance(node, ast.NamedExpr):
        node = node.value
    if not isinstance(node, ast.Attribute):
        return got
    attr = node.attr
    base = PNDB.base_text(node.value)
    if not base:
        return got
    first = base.split(".")[0]
    with_as = with_as_modules(tree, root_path)
    imports = import_bindings(tree)
    aliases = import_aliases(tree)
    hop = None
    module = None
    if first in with_as:
        hop = "with-as"
        module = with_as[first]
        if module is None:
            got["ia_state"] = STATE_REFUSED
            got["ia_reason"] = REFUSED_ATTR_WITH_AS % ("%s.%s" % (base, attr))
            got["ia_hop"] = hop
            got["ia_chain"] = ["%s.%s" % (base, attr)]
            got["state"] = STATE_REFUSED
            got["reason"] = got["ia_reason"]
            got["value"] = None
            got["ia_source"] = SOURCE_IMPORT_ALIAS
            return got
    elif first in imports:
        module = imports[first]
        hop = "import-alias" if first in aliases else "import"
    else:
        if shipped.get("state") is None and not shipped.get("reason"):
            got["ia_state"] = STATE_REFUSED
            got["ia_reason"] = REFUSED_ATTR_SILENT % ("%s.%s" % (base, attr))
            got["ia_hop"] = "silent"
            got["ia_chain"] = ["%s.%s" % (base, attr)]
            got["state"] = STATE_REFUSED
            got["reason"] = got["ia_reason"]
            got["value"] = None
            got["ia_source"] = SOURCE_IMPORT_ALIAS
        return got
    got["ia_source"] = SOURCE_IMPORT_ALIAS
    got["ia_hop"] = hop
    label = "%s.%s" % (base, attr)
    if first in aliases:
        label = "%s->%s.%s" % (first, aliases[first], attr)
    got["ia_chain"] = [label]
    dotted = "%s.%s" % (module, attr)
    if "." in base:
        rest = base.split(".", 1)[1]
        dotted = "%s.%s.%s" % (module, rest, attr)
    decision, values, sub_hop = module_attribute(root_path, module, attr)
    got["ia_hop"] = "%s/%s" % (hop, sub_hop) if sub_hop != "direct" else hop
    if decision == "ok":
        literal = sorted(values)[0]
        got["ia_state"] = STATE_OK
        got["ia_value"] = literal
        got["state"] = STATE_OK
        got["reason"] = None
        got["value"] = literal
        got["attr_state"] = STATE_OK
        got["attr_value"] = literal
        got["attr_reason"] = None
        return got
    if decision == "mixed":
        got["ia_state"] = STATE_REFUSED
        got["ia_reason"] = PNDB.PNDA.REFUSED_NAME_MIXED % dotted
        got["state"] = STATE_REFUSED
        got["reason"] = got["ia_reason"]
        got["value"] = None
        return got
    got["ia_state"] = STATE_REFUSED
    if decision == "missing" or decision == "no-module":
        if hop == "with-as":
            word = REFUSED_ATTR_WITH_AS
        elif hop == "import-alias":
            word = REFUSED_ATTR_IMPORT_ALIAS
        else:
            word = REFUSED_ATTR_PLAIN_IMPORT
        got["ia_reason"] = word % ("%s.%s" % (base, attr))
    else:
        got["ia_reason"] = PNDB.PNDA.REFUSED_ATTR_NON_CONSTANT % dotted
    got["state"] = STATE_REFUSED
    got["reason"] = got["ia_reason"]
    got["value"] = None
    return got


def import_alias_report(text, root=None):
    """One row per loop the predicate reading publishes."""
    shipped = PNDB.predicate_report(text, root)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["ia_followed"] = {}
        row["ia_refused"] = {}
        row["ia_chains"] = {}
        row["ia_hops"] = {}
        row["ia_resolved"] = []
        names = set(loop.get("followed") or {})
        names |= set(loop.get("refused") or {})
        names |= set(loop.get("attr_followed") or {})
        names |= set(loop.get("attr_refused") or {})
        names |= set(loop.get("pred_followed") or {})
        names |= set(loop.get("pred_refused") or {})
        names |= set(loop.get("not_yet_bound") or {})
        for item in loop.get("arms") or []:
            names.add(item["name"])
        scope = loop["scope"]
        if scope not in cache:
            cache[scope] = PNDB.predicate_tables(text, scope, root)
        tables = cache[scope]
        for name in sorted(names):
            got = import_alias_entry(name, text, scope, loop["line"], tables,
                                     root)
            if got.get("ia_hop"):
                row["ia_hops"][name] = got["ia_hop"]
            if got.get("ia_chain"):
                row["ia_chains"][name] = got["ia_chain"]
            if got.get("ia_source") != SOURCE_IMPORT_ALIAS:
                continue
            if got.get("ia_state") == STATE_OK:
                row["ia_followed"][name] = got["ia_value"]
                row["ia_resolved"].append(name)
            elif got.get("ia_reason"):
                row["ia_refused"][name] = got["ia_reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["import_alias_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in import_alias_report(text, root)["loops"]:
        row["import_alias_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped predicate audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ImportAliasError(E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNDB.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ImportAliasError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_IMPORT_ALIAS_STALE
                         if report.get("verdict") == PNDB.SEAMS_PREDICATE_STALE
                         else SEAMS_IMPORT_ALIAS_COVERED)
    report["base_tool"] = PNDB.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ImportAliasError as exc:
        return {"tool": LABEL, "verdict": SEAMS_IMPORT_ALIAS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_IMPORT_ALIAS_COVERED:
        raise ImportAliasError(report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a plain import, an import alias, a with-as "
                    "module, an aliased constant or a re-export as an "
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
            loops = row.get("import_alias_loops") or []
            resolved = sum(len(loop["ia_resolved"]) for loop in loops)
            named = sum(len(loop["ia_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s import_alias_loops=%d ia_resolved=%d "
                "ia_named=%d\n" % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_IMPORT_ALIAS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())