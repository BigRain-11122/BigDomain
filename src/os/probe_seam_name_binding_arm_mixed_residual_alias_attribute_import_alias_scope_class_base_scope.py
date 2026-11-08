"""AC-PNDCH1..AC-PNDCH6: the class-base / FROM-imported-class / self-NAME /
FROM-import-alias-receiver face (R2573).

Criteria were pinned in state/queue/tech.md:607 at R2571 BEFORE this code
existed.

What this proves, MEASURED at R2571 with src/os/limits_two_level_R2571.py and
RE-MEASURED here with src/os/limits_class_base_R2573.py before any code was
written:
  (1) a class-body constant reached through a subclass (`cls.K.ATTR` where
      ATTR is bound on `class Base`) reads attr-class-constant:cls.K.ATTR,
      because the class reading walks only the named class own body;
  (2) `from cls import K` then `K.ATTR` reads attr-base-local:K, because only
      a FROM-import whose target is a module file is treated as a module;
  (3) a cross-module with-as call whose method returns `self.NAME` reads
      attr-cross-call:m.ATTR, because the cross-module table follows a returned
      literal, a module-level name and a local, never a class attribute read
      through self;
  (4) a receiver bound by a FROM-import alias (`from pkg import mk as m2` then
      `with m2.Box().open() as m`) reads attr-cross-call:m.ATTR, because the
      receiver reading consults plain imports only.

This face asks the shipped two-level reading FIRST and carries every key it
published, unchanged, on every row, then re-reads only where that reading did
not resolve:
  * a class-body constant inherited from a base class in the same module
    resolves through the subclass path (AC-PNDCH1);
  * an absolute FROM-imported CLASS resolves through its class path
    (AC-PNDCH2);
  * a cross-module with-as call whose method returns self.NAME resolves when
    that class constant is a module name (AC-PNDCH3);
  * a receiver bound by a FROM-import alias is found and its call resolves
    (AC-PNDCH4);
  * every answer the twelve shipped faces already gave rides beside this face
    own on every row (AC-PNDCH5).

Nothing is imported and nothing is evaluated: every value comes from reading
source text. Stdlib only, ASCII source, zero network, no clock.
"""

import argparse
import ast
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope as CT  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_two_level_scope as CB  # noqa: E402

PNDCE = CT.PNDCE
PNDC = PNDCE.PNDC

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-class-base-scope")

E_ARGS = "E_PNDCH_ARGS"
E_NO_ROOT = "E_PNDCH_NO_ROOT"

STATE_OK = CB.STATE_OK
STATE_REFUSED = CB.STATE_REFUSED

SOURCE_CLASS_BASE = "class-base"

REFUSED_ATTR_CLASS_BASE_MIXED = "attr-class-base-mixed:%s"
REFUSED_ATTR_CLASS_BASE_CONSTANT = "attr-class-base-constant:%s"
REFUSED_ATTR_FROM_CLASS_MIXED = "attr-from-class-mixed:%s"
REFUSED_ATTR_FROM_CLASS_CONSTANT = "attr-from-class-constant:%s"
REFUSED_ATTR_FROM_IMPORT_NOT_CLASS = "attr-from-import-not-class:%s"

COVERED = CB.COVERED
MISSING_SEAM = CB.MISSING_SEAM
OUT_OF_SCOPE = CB.OUT_OF_SCOPE
UNREADABLE = CB.UNREADABLE
HISTORICAL = CB.HISTORICAL

SEAMS_CLASS_BASE_COVERED = "SEAMS-CLASS-BASE-COVERED"
SEAMS_CLASS_BASE_STALE = "SEAMS-CLASS-BASE-STALE"

MAX_CHAIN = CB.MAX_CHAIN
MAX_BASE_DEPTH = 8

_parse = PNDCE._parse
_read = PNDCE._read
_str_constant = PNDCE._str_constant
_module_file = PNDCE._module_file
_wrap = CT._wrap
module_attribute_scoped = CT.module_attribute_scoped


class ClassBaseError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _find_class(scope, name):
    """The ClassDef called `name` in this body, or None."""
    for item in getattr(scope, "body", []):
        if isinstance(item, ast.ClassDef) and item.name == name:
            return item
    return None


def own_constants(node):
    """attr -> set(literals) from this class body only."""
    out = {}
    for body in getattr(node, "body", []):
        if isinstance(body, ast.Assign):
            literal = _str_constant(body.value)
            if literal is None:
                continue
            for target in body.targets:
                if isinstance(target, ast.Name):
                    out.setdefault(target.id, set()).add(literal)
        elif isinstance(body, ast.AnnAssign):
            if not isinstance(body.target, ast.Name):
                continue
            if body.value is None:
                continue
            literal = _str_constant(body.value)
            if literal is not None:
                out.setdefault(body.target.id, set()).add(literal)
    return out


def class_table(tree, path):
    """attr -> set(literals) for a class path, following same-module bases."""
    if tree is None or not path:
        return None
    node = _find_class(tree, path[0])
    if node is None:
        return None
    if len(path) > 1:
        return class_table(node, path[1:])
    return _merge_bases(node, tree, set(), 0)


def _merge_bases(node, tree, seen, depth):
    """This class own constants, then the first same-module base that has them.

    A subclass own value always wins; a base fills only the attributes the
    subclass body does not bind, in source order, one level at a time.
    """
    if node.name in seen or depth > MAX_BASE_DEPTH:
        return {}
    seen = set(seen)
    seen.add(node.name)
    out = own_constants(node)
    for base in node.bases:
        if not isinstance(base, ast.Name):
            continue
        parent_node = _find_class(tree, base.id)
        if parent_node is None:
            continue
        inherited = _merge_bases(parent_node, tree, seen, depth + 1)
        for key, values in inherited.items():
            if key not in out:
                out[key] = set(values)
    return out


def class_attribute(root, dotted, path, attr):
    """(decision, values, hop) for a class-body constant through its path.

    The hop word says whether the value was found in the named class own body
    (class) or on a base class in the same module (class-base).
    """
    file_path = _module_file(root, dotted)
    if file_path is None:
        return None, set(), None
    try:
        tree = _parse(_read(file_path))
    except OSError:
        return None, set(), None
    if tree is None:
        return None, set(), None
    node = _find_class(tree, path[0])
    if node is None:
        return None, set(), None
    table = class_table(tree, path)
    if table is None:
        return None, set(), None
    direct = own_constants(node) if len(path) == 1 else {}
    hop = "class" if attr in direct else "class-base"
    if attr not in table:
        return "class-constant", set(), hop
    literals = table[attr]
    if len(literals) > 1:
        return "class-mixed", literals, hop
    return "ok", set(literals), hop


def from_import_classes(tree, root):
    """name -> (module dotted, class name) for an ABSOLUTE FROM-imported class.

    Only a name whose module file exists on disk and whose module body defines
    a class of that name is read, so a FROM-imported CONSTANT is never mistaken
    for a class.
    """
    out = {}
    if tree is None:
        return out
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level != 0:
            continue
        if not node.module:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            dotted = "%s.%s" % (node.module, alias.name)
            if _module_file(root, dotted) is not None:
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
            if _find_class(sub, alias.name) is None:
                continue
            out[alias.asname or alias.name] = (node.module, alias.name)
    return out


def module_binding(tree, root, first):
    """name -> dotted module, from a plain import, a module FROM-import or a
    FROM-import ALIAS of a module (the R2571 gap)."""
    mods, _names = CB.relative_from_scan(tree, root, [])
    if first in mods:
        return mods[first][0]
    from_mods = CT.from_import_modules_scoped(tree, root)
    if first in from_mods:
        return from_mods[first][0]
    imports = PNDC.import_bindings(tree)
    return imports.get(first)


def receiver_module(tree, root, node):
    """The module dotted a call chain hangs off, for `mk.Box().open()`."""
    cur = node
    while isinstance(cur, ast.Call):
        cur = cur.func
    while isinstance(cur, ast.Attribute):
        value = cur.value
        while isinstance(value, ast.Attribute):
            value = value.value
        if isinstance(value, ast.Name):
            return module_binding(tree, root, value.id)
        if isinstance(value, ast.Call):
            cur = value
            while isinstance(cur, ast.Call):
                cur = cur.func
            continue
        return None
    return None


def self_attribute_functions(tree, root):
    """Method names that return a class constant through self/cls."""
    out = set()
    if tree is None:
        return out
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        table = class_table(tree, [cls.name]) or {}
        for node in cls.body:
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
                if value.value.id not in ("self", "cls"):
                    continue
                literals = table.get(value.attr)
                if not literals or len(literals) > 1:
                    continue
                if _module_file(root, sorted(literals)[0]) is None:
                    continue
                out.add(node.name)
    return out


def receiver_name(node):
    """The base NAME a call chain hangs off, for `m2.Box().open()`."""
    cur = node
    while isinstance(cur, ast.Call):
        cur = cur.func
    while isinstance(cur, ast.Attribute):
        value = cur.value
        while isinstance(value, ast.Attribute):
            value = value.value
        if isinstance(value, ast.Name):
            return value.id
        if isinstance(value, ast.Call):
            cur = value
            while isinstance(cur, ast.Call):
                cur = cur.func
            continue
        return None
    return None


def call_target_functions(tree, root):
    """The shipped table, extended to a method returning `self.NAME` or
    `cls.NAME` when that class constant is a module name."""
    out = dict(CT.call_target_functions(tree, root))
    if tree is None:
        return out
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        table = class_table(tree, [cls.name]) or {}
        for node in cls.body:
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
                if value.value.id not in ("self", "cls"):
                    continue
                literals = table.get(value.attr)
                if not literals or len(literals) > 1:
                    continue
                literal = sorted(literals)[0]
                if _module_file(root, literal) is None:
                    continue
                out.setdefault(node.name, literal)
    return out


def with_as_targets(tree, root):
    """The shipped with-as table, extended to a receiver bound by a
    FROM-import alias and to a method returning self.NAME."""
    out = CB.two_level_with_as(tree, root)
    if tree is None:
        return out
    callers = call_target_functions(tree, root)
    self_fn = self_attribute_functions(tree, root)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for item in node.items:
            var = item.optional_vars
            if not isinstance(var, ast.Name):
                continue
            if var.id in out and out[var.id][0] is not None:
                continue
            context = item.context_expr
            if not isinstance(context, ast.Call):
                continue
            func = context.func
            if isinstance(func, ast.Name):
                if func.id in callers:
                    out[var.id] = (callers[func.id], "with-as-call")
                continue
            if not isinstance(func, ast.Attribute):
                continue
            receiver = receiver_module(tree, root, func)
            if not receiver:
                out.setdefault(var.id, (None, "with-as-alias-unread"))
                continue
            path = _module_file(root, receiver)
            if path is None:
                continue
            try:
                sub = _parse(_read(path))
            except OSError:
                continue
            if sub is None:
                continue
            table = call_target_functions(sub, root)
            alias_bound = (receiver_name(func) is not None
                           and receiver_name(func) not in PNDC.import_bindings(tree))
            if alias_bound:
                hop = "with-as-from-alias"
            elif func.attr in self_attribute_functions(sub, root):
                hop = "with-as-self-attr"
            else:
                hop = "with-as-cross-call"
            out[var.id] = (table.get(func.attr), hop)
    return out


def _publish(got, state, value, reason, hop, chain=None):
    got["cb_state"] = state
    got["cb_value"] = value
    got["cb_reason"] = reason
    got["cb_hop"] = hop
    got["cb_source"] = SOURCE_CLASS_BASE
    if chain is not None:
        got["cb_chain"] = list(chain)
    got["state"] = state
    got["value"] = value
    got["reason"] = reason
    return got


def class_base_entry(name, text, scope, line, tables=None, root=None,
                     src_path=None):
    """The shipped two-level answer, carried, plus this face own re-read."""
    root_path = BASE if root is None else root
    shipped = CB.two_level_entry(name, text, scope, line, tables, root_path,
                                 src_path)
    got = dict(shipped)
    for key in sorted(shipped):
        got.setdefault(key, shipped[key])
    got["base_cb_state"] = shipped.get("state")
    got["base_cb_value"] = shipped.get("value")
    got["base_cb_reason"] = shipped.get("reason")
    got["base_cb_hop"] = shipped.get("tl_hop")
    got["base_cb_source"] = shipped.get("tl_source")
    got["cb_state"] = None
    got["cb_value"] = None
    got["cb_reason"] = None
    got["cb_hop"] = None
    got["cb_chain"] = []
    got["cb_source"] = None
    if shipped.get("state") == STATE_OK:
        got["cb_state"] = shipped.get("state")
        got["cb_value"] = shipped.get("value")
        got["cb_reason"] = shipped.get("reason")
        got["cb_hop"] = shipped.get("tl_hop")
        got["cb_chain"] = list(shipped.get("tl_chain") or [])
        got["cb_source"] = shipped.get("tl_source")
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
    if src_path:
        parts = CB.package_parts(root_path, src_path)
    else:
        found = CB.source_path(root_path, text)
        parts = CB.package_parts(root_path, found) if found else []
    mods, _rel_names = CB.relative_from_scan(tree, root_path, parts)
    targets = with_as_targets(tree, root_path)
    classes = from_import_classes(tree, root_path)
    dotted = None
    hop = None
    class_path = None
    if first in targets:
        dotted, hop = targets[first]
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
    if dotted is None:
        return got
    if class_path is not None:
        decision, values, sub_hop = class_attribute(root_path, dotted,
                                                    class_path, attr)
        chain = ["%s->%s.%s" % (first, dotted, class_path[0])]
        if decision == "ok":
            return _publish(got, STATE_OK, sorted(values)[0], None,
                            "%s/%s" % (hop, sub_hop), chain)
        if decision == "class-mixed":
            return _publish(got, STATE_REFUSED, None,
                            REFUSED_ATTR_FROM_CLASS_MIXED % label,
                            "%s/%s" % (hop, sub_hop), chain)
        if decision == "class-constant":
            return _publish(got, STATE_REFUSED, None,
                            REFUSED_ATTR_FROM_CLASS_CONSTANT % label,
                            "%s/%s" % (hop, sub_hop), chain)
        return got
    if rest:
        decision, values, sub_hop = class_attribute(root_path, dotted, rest,
                                                    attr)
        if decision is None:
            return got
        chain = ["%s->%s.%s" % (first, dotted, ".".join(rest))]
        if decision == "ok":
            return _publish(got, STATE_OK, sorted(values)[0], None,
                            "%s/%s" % (hop, sub_hop), chain)
        if decision == "class-mixed":
            return _publish(got, STATE_REFUSED, None,
                            REFUSED_ATTR_CLASS_BASE_MIXED % label,
                            "%s/%s" % (hop, sub_hop), chain)
        return _publish(got, STATE_REFUSED, None,
                        REFUSED_ATTR_CLASS_BASE_CONSTANT % label,
                        "%s/%s" % (hop, sub_hop), chain)
    decision, values, sub_hop = module_attribute_scoped(root_path, dotted, attr)
    chain = ["%s->%s.%s" % (first, dotted, attr)]
    if decision == "ok":
        return _publish(got, STATE_OK, sorted(values)[0], None,
                        "%s/%s" % (hop, sub_hop or "direct"), chain)
    return got


def class_base_report(text, root=None, src_path=None):
    """One row per loop the two-level reading publishes."""
    shipped = CB.two_level_report(text, root, src_path)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["cb_followed"] = {}
        row["cb_refused"] = {}
        row["cb_chains"] = {}
        row["cb_hops"] = {}
        row["cb_resolved"] = []
        names = set()
        for key in ("followed", "refused", "attr_followed", "attr_refused",
                    "pred_followed", "pred_refused", "not_yet_bound",
                    "ia_followed", "ia_refused", "from_followed",
                    "from_refused", "from_resolved", "ct_followed",
                    "ct_refused", "ct_resolved", "tl_followed",
                    "tl_refused", "tl_resolved"):
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
            got = class_base_entry(name, text, scope, loop["line"], tables,
                                   root, src_path)
            if got.get("cb_hop"):
                row["cb_hops"][name] = got["cb_hop"]
            if got.get("cb_chain"):
                row["cb_chains"][name] = got["cb_chain"]
            if got.get("cb_source") != SOURCE_CLASS_BASE:
                continue
            if got.get("cb_state") == STATE_OK:
                row["cb_followed"][name] = got["cb_value"]
                row["cb_resolved"].append(name)
            elif got.get("cb_reason"):
                row["cb_refused"][name] = got["cb_reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["cb_scope_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in class_base_report(text, root, path)["loops"]:
        row["cb_scope_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped two-level audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ClassBaseError(E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = CB.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ClassBaseError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["base_tool"] = CB.LABEL
    report["verdict"] = (SEAMS_CLASS_BASE_STALE
                         if report.get("verdict") == CB.SEAMS_TWO_LEVEL_STALE
                         else SEAMS_CLASS_BASE_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ClassBaseError as exc:
        return {"tool": LABEL, "verdict": SEAMS_CLASS_BASE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_CLASS_BASE_COVERED:
        raise ClassBaseError(report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a class constant inherited from a base class, an "
                    "absolute FROM-imported CLASS, a cross-module method "
                    "returning self.NAME, and a FROM-import alias receiver")
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
            loops = row.get("cb_scope_loops") or []
            resolved = sum(len(loop["cb_resolved"]) for loop in loops)
            named = sum(len(loop["cb_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s cb_scope_loops=%d cb_resolved=%d cb_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_CLASS_BASE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())