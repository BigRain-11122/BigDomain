"""Module-level alias chain / module-level function / class-constant alias.

The shipped class-source face resolves a module value bound by a CALL and a
class constant declared as a literal or a same-class alias. Three shapes it
cannot read are measured and closed here:

  (1) a module-level value bound by an ALIAS CHAIN - `FIRST = Box().open()`
      then `REG = FIRST` - because the module-value reader accepts a Call and
      never follows a NAME to it;
  (2) a module-level FUNCTION returning a class attribute - `def make():
      return Box.NAME` then `REG = make()` - because the call-target table
      follows a class method and not a module-level function;
  (3) a class constant aliasing a FROM-imported constant - `from consts
      import BASE` then `class K: ATTR = BASE` - because only names bound in
      the class body are collected.

Every answer the shipped faces already gave is asked FIRST and carried
unchanged on the row. Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNCS1..AC-PNCS6 were pinned in state/queue/tech.md:611 at R2575
BEFORE this code existed.
"""

import argparse
import ast
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_source_scope as CS  # noqa: E402

CB = CS.CB
CT = CS.CT
TL = CS.TL
PNDC = CS.PNDC

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-chain-scope")

E_ARGS = "E_PNCS_ARGS"
E_NO_ROOT = "E_PNCS_NO_ROOT"

STATE_OK = CS.STATE_OK
STATE_REFUSED = CS.STATE_REFUSED

SOURCE_MODULE_ALIAS = "module-alias-chain"

REFUSED_ATTR_MODULE_ALIAS_UNBOUND = "attr-module-alias-unbound:%s"

COVERED = CS.COVERED
MISSING_SEAM = CS.MISSING_SEAM
OUT_OF_SCOPE = CS.OUT_OF_SCOPE
UNREADABLE = CS.UNREADABLE
HISTORICAL = CS.HISTORICAL

SEAMS_MODULE_ALIAS_COVERED = "SEAMS-MODULE-ALIAS-COVERED"
SEAMS_MODULE_ALIAS_STALE = "SEAMS-MODULE-ALIAS-STALE"

MAX_CHAIN = CS.MAX_CHAIN
MAX_ALIAS_ROUNDS = 8

_parse = CS._parse
_read = CS._read
_str_constant = CS._str_constant
_module_file = CS._module_file
_module_tree = CS._module_tree
_wrap = CS._wrap
leftmost_name = CS.leftmost_name
module_dotted = CS.module_dotted
module_attribute_scoped = CS.module_attribute_scoped


class ModuleAliasError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def module_level_binding(tree, name):
    """(final expression, chain of names, name that broke) for one name.

    Plain and annotated module-level assignments are followed through NAME
    aliases to a fixpoint; a name bound nowhere is returned with its own name
    so the caller can publish WHICH link broke instead of resolving nothing.
    """
    chain = [name]
    if tree is None:
        return None, chain, name
    seen = set()
    cur = name
    while True:
        if cur in seen or len(chain) > MAX_CHAIN:
            return None, chain, cur
        seen.add(cur)
        value = CS.module_value_binding(tree, cur)
        if value is None:
            return None, chain, cur
        if isinstance(value, ast.Name):
            cur = value.id
            chain.append(cur)
            continue
        return value, chain, None


def module_function_returns(tree, root, module):
    """Module-level FUNCTIONS whose return is a class attribute naming a
    module in this root. A function returning any other literal is absent."""
    out = {}
    if tree is None or not module:
        return out
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for item in ast.walk(node):
            if not isinstance(item, ast.Return) or item.value is None:
                continue
            value = item.value
            if not isinstance(value, ast.Attribute):
                continue
            if not isinstance(value.value, ast.Name):
                continue
            cls = CS._find_class_in(tree, value.value.id)
            if cls is not None:
                got = CS.cross_class_table(root, module, [cls.name])
            else:
                imported = CB.from_import_classes(tree, root)
                if value.value.id not in imported:
                    continue
                got = CS.cross_class_table(root, imported[value.value.id][0],
                                           [imported[value.value.id][1]])
            if got is None:
                continue
            literals = got[0].get(value.attr)
            if not literals or len(literals) > 1:
                continue
            literal = sorted(literals)[0]
            if _module_file(root, literal) is None:
                continue
            out.setdefault(node.name, literal)
    return out


def module_alias_literal(tree, root, module, name):
    """(literal, hop, chain, broken name) for a module-level alias chain.

    Follows the chain to its final expression. A final Call is resolved
    through the shipped call-target reading FIRST and then through this face
    own module-level function table; a final Name bound nowhere is returned
    with the name that broke.
    """
    value, chain, broken = module_level_binding(tree, name)
    if broken:
        return None, None, chain, broken
    if value is None:
        return None, None, chain, name
    if isinstance(value, ast.Call):
        literal = CS._call_target_literal(root, module, value.func, tree)
        if literal:
            return literal, "with-as-module-alias", chain, None
        if isinstance(value.func, ast.Name):
            literal = module_function_returns(tree, root, module).get(
                value.func.id)
            if literal:
                return literal, "with-as-module-function", chain, None
        return None, None, chain, None
    return None, None, chain, None


def with_as_targets_chain(tree, root, module=None):
    """(table, broken) for a with-as receiver.

    The table extends the shipped class-source reading to a module value bound
    by an alias chain or by a module-level function returning a class
    attribute; values are 3-tuples (literal, hop, chain) so this face can name
    the link it followed and every shipped entry is carried with no chain.
    `broken` maps a receiver whose chain ends at a name bound nowhere to that
    name and the chain that reached it.
    """
    shipped = CS.with_as_targets_cross(tree, root, module)
    out = {}
    broken = {}
    for key, value in shipped.items():
        if not value:
            continue
        out[key] = (value[0], value[1], [])
    if tree is None:
        return out, broken
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            var = item.optional_vars
            if not isinstance(var, ast.Name):
                continue
            if out.get(var.id) and out[var.id][0]:
                continue
            context = item.context_expr
            if not isinstance(context, ast.Attribute):
                continue
            head = leftmost_name(context)
            if head is None:
                continue
            dotted = CB.module_binding(tree, root, head)
            if dotted is None:
                continue
            sub = _module_tree(root, dotted)
            if sub is None:
                continue
            literal, hop, chain, link_broken = module_alias_literal(
                sub, root, dotted, context.attr)
            if literal:
                out[var.id] = (literal, hop, ["%s.%s->%s"
                                              % (head, context.attr, literal)]
                               + list(chain))
            elif link_broken:
                broken[var.id] = (link_broken,
                                  ["%s.%s" % (head, context.attr)] + list(chain))
    return out, broken


def module_constant_literal(tree, name):
    """The string literal a module-level name carries, following names."""
    seen = set()
    cur = name
    while cur not in seen:
        seen.add(cur)
        value = CS.module_value_binding(tree, cur)
        if value is None:
            return None
        if isinstance(value, ast.Name):
            cur = value.id
            continue
        return _str_constant(value)
    return None


def from_import_constants(tree, root):
    """name -> literal for an ABSOLUTE FROM-imported module-level STRING
    constant. A name that is not a string constant in its own module is
    absent, so a FROM-imported class or function is never read as one."""
    out = {}
    if tree is None:
        return out
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level != 0:
            continue
        if not node.module:
            continue
        path = _module_file(root, node.module)
        if path is None:
            continue
        try:
            sub = _parse(_read(path))
        except OSError:
            continue
        if sub is None:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            literal = module_constant_literal(sub, alias.name)
            if literal is None:
                continue
            out[alias.asname or alias.name] = literal
    return out


def class_constant_alias(root, tree, class_path, attr):
    """(literal, alias name) for `class_path.attr` bound to a FROM-imported
    module-level constant, or (None, None)."""
    if tree is None:
        return None, None
    if isinstance(class_path, str):
        class_path = [class_path]
    node = tree
    for step in class_path:
        if node is None:
            return None, None
        node = CS._find_class_in(node, step)
    if node is None:
        return None, None
    literals, aliases = CS.class_bodies(node)
    if attr in literals:
        return None, None
    consts = from_import_constants(tree, root)
    for target in sorted(aliases.get(attr, set())):
        if target in consts:
            return consts[target], target
    return None, None


def module_attribute_chain(root, module, attr):
    """(decision, values, hop, chain, broken) for module.attr.

    The shipped module-attribute reading is asked FIRST; only a refusal is
    re-read here, through a module-level alias chain or a module-level
    function returning a class attribute.
    """
    decision, values, hop = module_attribute_scoped(root, module, attr)
    if decision == "ok":
        return decision, values, hop or "direct", [], None
    tree = _module_tree(root, module)
    if tree is None:
        return decision, values, hop, [], None
    literal, hop2, chain, broken = module_alias_literal(tree, root, module,
                                                        attr)
    if literal:
        return "ok", {literal}, hop2, chain, None
    if broken:
        return None, set(), None, chain, broken
    return decision, values, hop, chain, None


def _publish(got, state, value, reason, hop, chain=None):
    got["ma_state"] = state
    got["ma_value"] = value
    got["ma_reason"] = reason
    got["ma_hop"] = hop
    got["ma_source"] = SOURCE_MODULE_ALIAS
    if chain is not None:
        got["ma_chain"] = list(chain)
    got["state"] = state
    got["value"] = value
    got["reason"] = reason
    return got


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The shipped class-source answer, carried, plus this face own re-read."""
    root_path = BASE if root is None else root
    shipped = CS.class_source_entry(name, text, scope, line, tables, root_path,
                                    src_path)
    got = dict(shipped)
    for key in sorted(shipped):
        got.setdefault(key, shipped[key])
    got["base_ma_state"] = shipped.get("state")
    got["base_ma_value"] = shipped.get("value")
    got["base_ma_reason"] = shipped.get("reason")
    got["base_ma_hop"] = shipped.get("cs_hop")
    got["base_ma_source"] = shipped.get("cs_source")
    got["ma_state"] = shipped.get("cs_state")
    got["ma_value"] = shipped.get("cs_value")
    got["ma_reason"] = shipped.get("cs_reason")
    got["ma_hop"] = shipped.get("cs_hop")
    got["ma_chain"] = list(shipped.get("cs_chain") or [])
    got["ma_source"] = shipped.get("cs_source")
    if shipped.get("cs_state") == STATE_OK:
        return got
    tables_full = (PNDC.PNDB.predicate_tables(text, scope, root_path)
                   if tables is None else tables)
    tree = (tables_full or {}).get("predicate_tree")
    if tree is None:
        return got
    node = _wrap(name, tree, scope, line)
    if node is None:
        return got
    attr = node.attr
    base = PNDC.PNDB.base_text(node.value)
    if not base:
        return got
    first = base.split(".")[0]
    rest = base.split(".")[1:]
    label = "%s.%s" % (base, attr)
    found = src_path if src_path else TL.source_path(root_path, text)
    module = module_dotted(root_path, found) if found else None
    if found:
        parts = TL.package_parts(root_path, found)
    else:
        parts = []
    mods, _rel_names = TL.relative_from_scan(tree, root_path, parts)
    targets, broken_targets = with_as_targets_chain(tree, root_path, module)
    classes = CB.from_import_classes(tree, root_path)
    dotted = None
    hop = None
    chain = []
    class_path = None
    if first in broken_targets:
        link_broken, link_chain = broken_targets[first]
        return _publish(got, STATE_REFUSED, None,
                        REFUSED_ATTR_MODULE_ALIAS_UNBOUND % link_broken,
                        "with-as-module-alias/%s" % link_broken,
                        list(link_chain))
    if first in targets:
        dotted, hop, chain = targets[first]
        if dotted is None:
            return got
    elif first in mods:
        dotted = mods[first][0]
        hop = "from-relative" if mods[first][1] > 1 else "from-import"
    elif first in classes:
        dotted, cls = classes[first]
        class_path = [cls]
        hop = "from-class"
    else:
        from_mods = CT.from_import_modules_scoped(tree, root_path)
        if first in from_mods:
            dotted, relative = from_mods[first]
            hop = "from-relative" if relative else "from-import"
        else:
            imports = PNDC.import_bindings(tree)
            if first in imports:
                dotted = imports[first]
                hop = "import"
    same_class = (dotted is None
                  and CS._find_class_in(tree, first) is not None)
    if same_class:
        class_path = [first]
        hop = "class-same"
    if dotted is None and not same_class:
        return got
    if class_path is not None:
        if same_class:
            literal, alias = class_constant_alias(root_path, tree, first, attr)
            if literal:
                return _publish(got, STATE_OK, literal, None,
                                "class-same/from-constant",
                                chain + ["%s.%s<-%s" % (first, attr, alias)])
        decision, values, sub_hop = CS.class_attribute_cross(
            root_path, dotted, class_path, attr)
        if decision == "ok":
            return _publish(got, STATE_OK, sorted(values)[0], None,
                            "%s/%s" % (hop, sub_hop), chain)
        if decision is None:
            return got
        return _publish(got, STATE_REFUSED, None,
                        CS.REFUSED_ATTR_CLASS_SOURCE_CONSTANT % label
                        if decision == "class-constant"
                        else CS.REFUSED_ATTR_CLASS_SOURCE_MIXED % label,
                        "%s/%s" % (hop, sub_hop), chain)
    if rest:
        decision, values, sub_hop = CS.class_attribute_cross(
            root_path, dotted, rest, attr)
        if decision is None:
            if len(rest) == 1:
                sub_tree = _module_tree(root_path, dotted)
                _value, link_chain, link_broken = module_level_binding(
                    sub_tree, rest[0])
                if link_broken:
                    return _publish(
                        got, STATE_REFUSED, None,
                        REFUSED_ATTR_MODULE_ALIAS_UNBOUND % link_broken,
                        "%s/%s" % (hop, link_broken),
                        ["%s.%s" % (first, rest[0])] + list(link_chain))
            return got
        if decision == "class-constant":
            sub_tree = _module_tree(root_path, dotted)
            literal, alias = class_constant_alias(root_path, sub_tree, rest,
                                                  attr)
            if literal:
                return _publish(got, STATE_OK, literal, None,
                                "%s/class-from-constant" % hop,
                                chain + ["%s.%s<-%s"
                                         % (".".join(rest), attr, alias)])
        if decision == "ok":
            return _publish(got, STATE_OK, sorted(values)[0], None,
                            "%s/%s" % (hop, sub_hop), chain)
        return _publish(got, STATE_REFUSED, None,
                        CS.REFUSED_ATTR_CLASS_SOURCE_CONSTANT % label
                        if decision == "class-constant"
                        else CS.REFUSED_ATTR_CLASS_SOURCE_MIXED % label,
                        "%s/%s" % (hop, sub_hop), chain)
    decision, values, sub_hop, deep_chain, broken = module_attribute_chain(
        root_path, dotted, attr)
    if broken:
        return _publish(got, STATE_REFUSED, None,
                        REFUSED_ATTR_MODULE_ALIAS_UNBOUND % broken,
                        "%s/%s" % (hop, broken), chain + list(deep_chain))
    if decision == "ok":
        return _publish(got, STATE_OK, sorted(values)[0], None,
                        "%s/%s" % (hop, sub_hop or "direct"),
                        chain + list(deep_chain))
    return got


def module_alias_report(text, root=None, src_path=None):
    """One row per loop the class-source reading publishes."""
    shipped = CS.class_source_report(text, root, src_path)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["ma_followed"] = {}
        row["ma_refused"] = {}
        row["ma_chains"] = {}
        row["ma_hops"] = {}
        row["ma_resolved"] = []
        names = set()
        for key in ("followed", "refused", "attr_followed", "attr_refused",
                    "pred_followed", "pred_refused", "not_yet_bound",
                    "ia_followed", "ia_refused", "from_followed",
                    "from_refused", "from_resolved", "ct_followed",
                    "ct_refused", "ct_resolved", "tl_followed",
                    "tl_refused", "tl_resolved", "cb_followed",
                    "cb_refused", "cb_resolved", "cs_followed",
                    "cs_refused", "cs_resolved"):
            value = loop.get(key)
            if isinstance(value, dict):
                names |= set(value)
            elif isinstance(value, list):
                names |= set(value)
        for item in loop.get("arms") or []:
            names.add(item["name"])
        scope = loop["scope"]
        if scope not in cache:
            cache[scope] = PNDC.PNDB.predicate_tables(text, scope, root)
        tables = cache[scope]
        for name in sorted(names):
            got = module_alias_entry(name, text, scope, loop["line"], tables,
                                     root, src_path)
            if got.get("ma_hop"):
                row["ma_hops"][name] = got["ma_hop"]
            if got.get("ma_chain"):
                row["ma_chains"][name] = got["ma_chain"]
            if got.get("ma_source") != SOURCE_MODULE_ALIAS:
                continue
            if got.get("ma_state") == STATE_OK:
                row["ma_followed"][name] = got["ma_value"]
                row["ma_resolved"].append(name)
            elif got.get("ma_reason"):
                row["ma_refused"][name] = got["ma_reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["ma_scope_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in module_alias_report(text, root, path)["loops"]:
        row["ma_scope_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped class-source audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasError(E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = CS.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["base_tool"] = CS.LABEL
    report["verdict"] = (SEAMS_MODULE_ALIAS_STALE
                         if report.get("verdict") == CS.SEAMS_CLASS_SOURCE_STALE
                         else SEAMS_MODULE_ALIAS_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasError as exc:
        return {"tool": LABEL, "verdict": SEAMS_MODULE_ALIAS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_MODULE_ALIAS_COVERED:
        raise ModuleAliasError(report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a module-level alias chain, a module-level "
                    "function returning a class attribute, and a class "
                    "constant aliasing a FROM-imported constant")
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
            loops = row.get("ma_scope_loops") or []
            resolved = sum(len(loop["ma_resolved"]) for loop in loops)
            named = sum(len(loop["ma_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s ma_scope_loops=%d ma_resolved=%d ma_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_MODULE_ALIAS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())