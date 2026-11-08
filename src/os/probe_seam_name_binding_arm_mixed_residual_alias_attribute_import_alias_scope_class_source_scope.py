"""AC-PNDCI1..AC-PNDCI6: the cross-module base / module-value receiver /
class-constant-alias face (R2575).

Criteria were pinned in state/queue/tech.md:609 at R2573 BEFORE this code
existed.

RE-MEASURED at R2575 with the shipped class-base face on the four shapes the
seed row named, so the row states what is still open rather than quoting it:
  (1) a base class imported from ANOTHER module (`class K(Base)` where Base
      comes from `from base import Base`) reads
      attr-class-base-constant:cls.K.ATTR, because the base walk stays inside
      the one module body it was handed (STILL OPEN);
  (2) a method returning a class attribute of a base class through self
      ALREADY resolves at HEAD through the shipped same-module base merge
      (measured ok/b), so this face only carries that answer;
  (3) `REG = Box().open()` at module level then `with reg.REG as m` reads
      attr-with-as:m.ATTR, because the with-as table follows calls but never a
      module-level VALUE (STILL OPEN);
  (4) `class K(Base): OTHER = ATTR` reads attr-class-base-constant:cls.K.OTHER,
      because only str literals are collected, never an alias (STILL OPEN).

This face asks the shipped class-base reading FIRST and carries every key it
published, unchanged, on every row, then re-reads only where that reading did
not resolve:
  * a base class from another module in the SAME root resolves through the
    subclass path, cycle-guarded and depth-bounded (AC-PNDCI1);
  * a method returning an inherited class attribute through self rides the
    shipped answer and is re-read through the cross-module table
    (AC-PNDCI2);
  * a module-level value bound by a call returning a class attribute resolves
    as a with-as receiver (AC-PNDCI3);
  * a class-constant alias resolves to the same literal to a fixpoint
    (AC-PNDCI4);
  * every answer the thirteen shipped faces already gave rides beside this
    face own on every row (AC-PNDCI5).

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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_base_scope as CB  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope as CT  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_two_level_scope as TL  # noqa: E402

PNDCE = CT.PNDCE
PNDC = PNDCE.PNDC

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-class-source-scope")

E_ARGS = "E_PNDCI_ARGS"
E_NO_ROOT = "E_PNDCI_NO_ROOT"

STATE_OK = CB.STATE_OK
STATE_REFUSED = CB.STATE_REFUSED

SOURCE_CLASS_SOURCE = "class-source"

REFUSED_ATTR_CLASS_SOURCE_MIXED = "attr-class-source-mixed:%s"
REFUSED_ATTR_CLASS_SOURCE_CONSTANT = "attr-class-source-constant:%s"
REFUSED_ATTR_MODULE_VALUE = "attr-module-value:%s"

COVERED = CB.COVERED
MISSING_SEAM = CB.MISSING_SEAM
OUT_OF_SCOPE = CB.OUT_OF_SCOPE
UNREADABLE = CB.UNREADABLE
HISTORICAL = CB.HISTORICAL

SEAMS_CLASS_SOURCE_COVERED = "SEAMS-CLASS-SOURCE-COVERED"
SEAMS_CLASS_SOURCE_STALE = "SEAMS-CLASS-SOURCE-STALE"

MAX_CHAIN = CB.MAX_CHAIN
MAX_BASE_DEPTH = 8
MAX_ALIAS_ROUNDS = 8

_parse = PNDCE._parse
_read = PNDCE._read
_str_constant = PNDCE._str_constant
_module_file = PNDCE._module_file
_wrap = CT._wrap
module_attribute_scoped = CT.module_attribute_scoped


class ClassSourceError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _find_class_in(scope, name):
    """The ClassDef called `name` directly in this body, or None."""
    for item in getattr(scope, "body", []):
        if isinstance(item, ast.ClassDef) and item.name == name:
            return item
    return None


def _descend(scope, path):
    """Walk a class path inside one module body."""
    node = scope
    for name in path:
        node = _find_class_in(node, name)
        if node is None:
            return None
    return node


def class_bodies(node):
    """(attr -> set(literals), attr -> set(alias names)) for one class body."""
    literals = {}
    aliases = {}
    for body in getattr(node, "body", []):
        if isinstance(body, ast.Assign):
            value = body.value
            literal = _str_constant(value)
            target_names = [t for t in body.targets if isinstance(t, ast.Name)]
            for target in target_names:
                if literal is not None:
                    literals.setdefault(target.id, set()).add(literal)
                elif isinstance(value, ast.Name):
                    aliases.setdefault(target.id, set()).add(value.id)
        elif isinstance(body, ast.AnnAssign):
            if not isinstance(body.target, ast.Name) or body.value is None:
                continue
            literal = _str_constant(body.value)
            if literal is not None:
                literals.setdefault(body.target.id, set()).add(literal)
            elif isinstance(body.value, ast.Name):
                aliases.setdefault(body.target.id, set()).add(body.value.id)
    return literals, aliases


def module_dotted(root, path):
    """The dotted module name of one file under root, or None."""
    if not path:
        return None
    rel = os.path.relpath(path, root).replace("\\", "/")
    if rel.startswith("../") or rel == "..":
        return None
    parts = rel.split("/")
    if not parts or not parts[-1].endswith(".py"):
        return None
    name = parts[-1][:-3]
    if name == "__init__":
        parts = parts[:-1]
    else:
        parts = parts[:-1] + [name]
    if not parts:
        return None
    return ".".join(parts)


def base_targets(tree, root, module, base):
    """(module dotted, class name) pairs one base expression names."""
    out = []
    if isinstance(base, ast.Name):
        imported = CB.from_import_classes(tree, root)
        if base.id in imported:
            out.append(imported[base.id])
        elif _find_class_in(tree, base.id) is not None:
            out.append((module, base.id))
        return out
    if isinstance(base, ast.Attribute):
        attrs = []
        cur = base
        while isinstance(cur, ast.Attribute):
            attrs.append(cur.attr)
            cur = cur.value
        attrs.reverse()
        if not isinstance(cur, ast.Name):
            return out
        head = cur.id
        dotted = CB.module_binding(tree, root, head)
        if dotted is None:
            if _find_class_in(tree, head) is not None:
                out.append((module, head))
            return out
        if attrs:
            out.append((dotted, attrs[-1]))
        return out
    return out


def cross_class_table(root, module, path, seen=None, depth=0):
    """(attr -> set(literals), own attrs) for a class path across modules.

    A subclass own value wins; a base fills only the attributes the subclass
    body does not bind. A base in ANOTHER module is followed through the same
    root, cycle-guarded by (module, path) and bounded by MAX_BASE_DEPTH. An
    alias (`OTHER = ATTR`) is resolved to a fixpoint after the base merge.
    """
    if not module or not path or depth > MAX_BASE_DEPTH:
        return None
    key = (module, tuple(path))
    if seen is None:
        seen = set()
    if key in seen:
        return None
    file_path = _module_file(root, module)
    if file_path is None:
        return None
    try:
        tree = _parse(_read(file_path))
    except OSError:
        return None
    if tree is None:
        return None
    node = _descend(tree, path)
    if node is None:
        return None
    literals, aliases = class_bodies(node)
    table = {name: set(values) for name, values in literals.items()}
    own = set(literals) | set(aliases)
    seen = set(seen)
    seen.add(key)
    for base in node.bases:
        for base_module, base_class in base_targets(tree, root, module, base):
            sub = cross_class_table(root, base_module, [base_class], seen,
                                    depth + 1)
            if not sub:
                continue
            for name, values in sub[0].items():
                if name not in table:
                    table[name] = set(values)
    for _round in range(MAX_ALIAS_ROUNDS):
        changed = False
        for name in sorted(aliases):
            values = set(table.get(name, set()))
            for target in aliases[name]:
                values |= table.get(target, set())
            if not values:
                continue
            if table.get(name) != values:
                table[name] = values
                changed = True
        if not changed:
            break
    return table, own


def class_attribute_cross(root, module, path, attr):
    """(decision, values, hop) for a class constant through its cross path.

    The hop word says whether the value was found in the named class own body
    (class) or on a base class, same module or another module in the root
    (class-base).
    """
    got = cross_class_table(root, module, path)
    if got is None:
        return None, set(), None
    table, own = got
    hop = "class" if attr in own else "class-base"
    if attr not in table:
        return "class-constant", set(), hop
    literals = table[attr]
    if len(literals) > 1:
        return "class-mixed", literals, hop
    return "ok", set(literals), hop


def self_attribute_functions_cross(tree, root, module):
    """Method names that return a class constant through self/cls, with bases
    followed across modules in this root."""
    out = set()
    if tree is None or not module:
        return out
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        got = cross_class_table(root, module, [cls.name])
        if got is None:
            continue
        table = got[0]
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


def call_target_functions_cross(tree, root, module):
    """The shipped call-target table, extended to self.NAME through a base
    class that lives in ANOTHER module."""
    out = dict(CB.call_target_functions(tree, root))
    if tree is None or not module:
        return out
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        got = cross_class_table(root, module, [cls.name])
        if got is None:
            continue
        table = got[0]
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
                if not out.get(node.name):
                    out[node.name] = literal
    return out


def leftmost_name(node):
    """The base NAME a call/attribute chain hangs off, or None."""
    cur = node
    while True:
        if isinstance(cur, ast.Call):
            cur = cur.func
            continue
        if isinstance(cur, ast.Attribute):
            cur = cur.value
            continue
        break
    if isinstance(cur, ast.Name):
        return cur.id
    return None


def receiver_module_any(tree, root, module, node):
    """The module a receiver chain hangs off, falling back to a class in this
    module or a FROM-imported class."""
    dotted = CB.receiver_module(tree, root, node)
    if dotted:
        return dotted
    if tree is None:
        return None
    name = leftmost_name(node)
    if name is None:
        return None
    if _find_class_in(tree, name) is not None:
        return module
    imported = CB.from_import_classes(tree, root)
    if name in imported:
        return imported[name][0]
    return None


def module_value_binding(tree, name):
    """The module-level expression bound to `name`, or None."""
    if tree is None:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                if node.value is not None:
                    return node.value
    return None


def _call_target_literal(root, module, func, tree=None):
    """The module name a call's function returns in `module`, or None.

    An attribute call resolves through its RECEIVER, so a receiver naming a
    module does not need the current file own module name (a synthetic loop
    text has none); a bare-name call does.
    """
    if isinstance(func, ast.Attribute):
        if tree is None and module:
            tree = _module_tree(root, module)
        receiver = receiver_module_any(tree, root, module, func)
        if receiver is None:
            return None
        sub = _module_tree(root, receiver)
        if sub is None:
            return None
        return call_target_functions_cross(sub, root, receiver).get(func.attr)
    if isinstance(func, ast.Name):
        if not module:
            return None
        if tree is None:
            tree = _module_tree(root, module)
        if tree is None:
            return None
        return call_target_functions_cross(tree, root, module).get(func.id)
    return None


def _module_tree(root, module):
    """The parsed tree of one module, or None."""
    path = _module_file(root, module)
    if path is None:
        return None
    try:
        return _parse(_read(path))
    except OSError:
        return None


def with_as_targets_cross(tree, root, module=None):
    """The shipped with-as table, extended to a module-level value bound by a
    call returning a class attribute, and to a self.NAME method through a base
    class in another module."""
    out = dict(CB.with_as_targets(tree, root))
    if tree is None:
        return out
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
            if isinstance(context, ast.Attribute):
                head = leftmost_name(context)
                if head is None:
                    continue
                dotted = CB.module_binding(tree, root, head)
                if dotted is None:
                    continue
                sub = _module_tree(root, dotted)
                if sub is None:
                    continue
                value = module_value_binding(sub, context.attr)
                if not isinstance(value, ast.Call):
                    continue
                literal = _call_target_literal(root, dotted, value.func, sub)
                if literal:
                    out[var.id] = (literal, "with-as-module-value")
                continue
            if isinstance(context, ast.Call):
                literal = _call_target_literal(root, module, context.func, tree)
                if not literal:
                    continue
                if isinstance(context.func, ast.Attribute):
                    receiver = receiver_module_any(tree, root, module,
                                                   context.func)
                    sub = _module_tree(root, receiver) if receiver else None
                    if sub is not None and context.func.attr in \
                            self_attribute_functions_cross(sub, root, receiver):
                        out[var.id] = (literal, "with-as-self-attr")
                    else:
                        out[var.id] = (literal, "with-as-cross-call")
                else:
                    out[var.id] = (literal, "with-as-call")
    return out


def _publish(got, state, value, reason, hop, chain=None):
    got["cs_state"] = state
    got["cs_value"] = value
    got["cs_reason"] = reason
    got["cs_hop"] = hop
    got["cs_source"] = SOURCE_CLASS_SOURCE
    if chain is not None:
        got["cs_chain"] = list(chain)
    got["state"] = state
    got["value"] = value
    got["reason"] = reason
    return got


def class_source_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The shipped class-base answer, carried, plus this face own re-read."""
    root_path = BASE if root is None else root
    shipped = CB.class_base_entry(name, text, scope, line, tables, root_path,
                                  src_path)
    got = dict(shipped)
    for key in sorted(shipped):
        got.setdefault(key, shipped[key])
    got["base_cs_state"] = shipped.get("state")
    got["base_cs_value"] = shipped.get("value")
    got["base_cs_reason"] = shipped.get("reason")
    got["base_cs_hop"] = shipped.get("cb_hop")
    got["base_cs_source"] = shipped.get("cb_source")
    got["cs_state"] = None
    got["cs_value"] = None
    got["cs_reason"] = None
    got["cs_hop"] = None
    got["cs_chain"] = []
    got["cs_source"] = None
    if shipped.get("state") == STATE_OK:
        got["cs_state"] = shipped.get("state")
        got["cs_value"] = shipped.get("value")
        got["cs_reason"] = shipped.get("reason")
        got["cs_hop"] = shipped.get("cb_hop")
        got["cs_chain"] = list(shipped.get("cb_chain") or [])
        got["cs_source"] = shipped.get("cb_source")
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
    targets = with_as_targets_cross(tree, root_path, module)
    classes = CB.from_import_classes(tree, root_path)
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
        decision, values, sub_hop = class_attribute_cross(root_path, dotted,
                                                          class_path, attr)
        chain = ["%s->%s.%s" % (first, dotted, class_path[0])]
        if decision == "ok":
            return _publish(got, STATE_OK, sorted(values)[0], None,
                            "%s/%s" % (hop, sub_hop), chain)
        if decision == "class-mixed":
            return _publish(got, STATE_REFUSED, None,
                            REFUSED_ATTR_CLASS_SOURCE_MIXED % label,
                            "%s/%s" % (hop, sub_hop), chain)
        if decision == "class-constant":
            return _publish(got, STATE_REFUSED, None,
                            REFUSED_ATTR_CLASS_SOURCE_CONSTANT % label,
                            "%s/%s" % (hop, sub_hop), chain)
        return got
    if rest:
        decision, values, sub_hop = class_attribute_cross(root_path, dotted,
                                                          rest, attr)
        if decision is None:
            return got
        chain = ["%s->%s.%s" % (first, dotted, ".".join(rest))]
        if decision == "ok":
            return _publish(got, STATE_OK, sorted(values)[0], None,
                            "%s/%s" % (hop, sub_hop), chain)
        if decision == "class-mixed":
            return _publish(got, STATE_REFUSED, None,
                            REFUSED_ATTR_CLASS_SOURCE_MIXED % label,
                            "%s/%s" % (hop, sub_hop), chain)
        return _publish(got, STATE_REFUSED, None,
                        REFUSED_ATTR_CLASS_SOURCE_CONSTANT % label,
                        "%s/%s" % (hop, sub_hop), chain)
    decision, values, sub_hop = module_attribute_scoped(root_path, dotted, attr)
    chain = ["%s->%s.%s" % (first, dotted, attr)]
    if decision == "ok":
        return _publish(got, STATE_OK, sorted(values)[0], None,
                        "%s/%s" % (hop, sub_hop or "direct"), chain)
    return got


def class_source_report(text, root=None, src_path=None):
    """One row per loop the class-base reading publishes."""
    shipped = CB.class_base_report(text, root, src_path)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["cs_followed"] = {}
        row["cs_refused"] = {}
        row["cs_chains"] = {}
        row["cs_hops"] = {}
        row["cs_resolved"] = []
        names = set()
        for key in ("followed", "refused", "attr_followed", "attr_refused",
                    "pred_followed", "pred_refused", "not_yet_bound",
                    "ia_followed", "ia_refused", "from_followed",
                    "from_refused", "from_resolved", "ct_followed",
                    "ct_refused", "ct_resolved", "tl_followed",
                    "tl_refused", "tl_resolved", "cb_followed",
                    "cb_refused", "cb_resolved"):
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
            got = class_source_entry(name, text, scope, loop["line"], tables,
                                     root, src_path)
            if got.get("cs_hop"):
                row["cs_hops"][name] = got["cs_hop"]
            if got.get("cs_chain"):
                row["cs_chains"][name] = got["cs_chain"]
            if got.get("cs_source") != SOURCE_CLASS_SOURCE:
                continue
            if got.get("cs_state") == STATE_OK:
                row["cs_followed"][name] = got["cs_value"]
                row["cs_resolved"].append(name)
            elif got.get("cs_reason"):
                row["cs_refused"][name] = got["cs_reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["cs_scope_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in class_source_report(text, root, path)["loops"]:
        row["cs_scope_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped class-base audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ClassSourceError(E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = CB.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ClassSourceError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["base_tool"] = CB.LABEL
    report["verdict"] = (SEAMS_CLASS_SOURCE_STALE
                         if report.get("verdict") == CB.SEAMS_CLASS_BASE_STALE
                         else SEAMS_CLASS_SOURCE_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ClassSourceError as exc:
        return {"tool": LABEL, "verdict": SEAMS_CLASS_SOURCE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_CLASS_SOURCE_COVERED:
        raise ClassSourceError(report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a base class imported from another module, a "
                    "module value bound by a call returning a class "
                    "attribute, and a class-constant alias")
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
            loops = row.get("cs_scope_loops") or []
            resolved = sum(len(loop["cs_resolved"]) for loop in loops)
            named = sum(len(loop["cs_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s cs_scope_loops=%d cs_resolved=%d cs_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_CLASS_SOURCE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())