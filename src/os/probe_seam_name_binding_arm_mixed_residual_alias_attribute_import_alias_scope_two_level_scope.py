"""AC-PNDCG1..AC-PNDCG6: the two-level relative / cross-module call /
class-body / relative-name face (R2571).

Criteria were pinned in state/queue/tech.md:605 at R2569 BEFORE this code
existed.

What this proves, MEASURED at R2569 with src/os/limits_call_target_R2569.py
against one private world where the honest answer is `b`, and RE-MEASURED here
before any code was written:
  (1) a two-level relative `from .. import helper` reads
      attr-base-local:helper, because only a one-level ImportFrom is resolved
      against the package own directory;
  (2) a with-as call on a method defined in ANOTHER module
      (`with mk.Box().open() as m`) reads attr-call-target:m.ATTR, because the
      call-target table is built from the same source text only;
  (3) a class-body constant read as `cls.K.ATTR` reads
      attr-from-import:cls.K.ATTR, because neither the module reading nor the
      function reading walks a class body;
  (4) `from .cls import K` reads attr-base-local:K, because a relative
      FROM-import of a NAME is not a module and is left where it was.

This face asks the shipped call-target reading FIRST and carries every key it
published, unchanged, on every row, then re-reads:
  * a level-bearing `from .. import helper` resolves against the parent
    package, located by the module own source path or by matching this text
    to a file under the root (AC-PNDCG1);
  * a with-as call on a method defined in another module resolves when that
    method returns a module name and is NAMED otherwise (AC-PNDCG2);
  * a class-body constant resolves through its class path (AC-PNDCG3);
  * a relative FROM-imported NAME is refused with its own word instead of
    being published as a local (AC-PNDCG4);
  * every answer the eleven shipped faces already gave rides beside this
    face own on every row (AC-PNDCG5).

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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope as PNDCF  # noqa: E402

PNDCE = PNDCF.PNDCE
PNDC = PNDCE.PNDC

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-two-level-scope")

E_ARGS = "E_PNDCG_ARGS"
E_NO_ROOT = "E_PNDCG_NO_ROOT"

STATE_OK = PNDCF.STATE_OK
STATE_REFUSED = PNDCF.STATE_REFUSED

REFUSED_ATTR_RELATIVE_NAME = "attr-relative-from-name:%s"
REFUSED_ATTR_CROSS_CALL = "attr-cross-call:%s"
REFUSED_ATTR_CLASS_CONSTANT = "attr-class-constant:%s"
REFUSED_ATTR_CLASS_MIXED = "attr-class-mixed:%s"
REFUSED_ATTR_TWO_LEVEL = "attr-relative-parent:%s"

SOURCE_TWO_LEVEL = "two-level"

COVERED = PNDCF.COVERED
MISSING_SEAM = PNDCF.MISSING_SEAM
OUT_OF_SCOPE = PNDCF.OUT_OF_SCOPE
UNREADABLE = PNDCF.UNREADABLE
HISTORICAL = PNDCF.HISTORICAL

SEAMS_TWO_LEVEL_COVERED = "SEAMS-TWO-LEVEL-COVERED"
SEAMS_TWO_LEVEL_STALE = "SEAMS-TWO-LEVEL-STALE"

MAX_CHAIN = PNDCF.MAX_CHAIN

_parse = PNDCE._parse
_read = PNDCE._read
_str_constant = PNDCE._str_constant
_module_file = PNDCE._module_file
_wrap = PNDCF._wrap
module_attribute_scoped = PNDCF.module_attribute_scoped


class TwoLevelError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def package_parts(root, path):
    """The package directories of one module file, relative to the root."""
    if not path:
        return []
    rel = os.path.relpath(path, root).replace("\\", "/")
    parts = rel.split("/")[:-1]
    if not parts or parts == ["."]:
        return []
    return parts


def source_path(root, text):
    """The file under root whose text is this text; first hit, sorted walk."""
    target = text.replace("\r\n", "\n")
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            try:
                body = _read(path)
            except OSError:
                continue
            except UnicodeDecodeError:
                continue
            if body.replace("\r\n", "\n") == target:
                return path
    return None


def relative_from_scan(tree, root, parts):
    """(name -> (dotted, level)) for level-bearing module imports, plus the
    names a relative FROM-import binds that are NOT modules.

    Level 1 is the package own directory, which is the shipped behaviour and is
    kept byte for byte. Level N strips N-1 directories off the package parts, so
    a two-level import walks up to the parent package once an anchor is known.
    """
    mods = {}
    names = set()
    if tree is None:
        return mods, names
    base = list(parts or [])
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level < 1:
            continue
        strip = node.level - 1
        if strip > len(base):
            continue
        prefix = base[:len(base) - strip] if strip else base
        for alias in node.names:
            if alias.name == "*":
                continue
            segs = list(prefix)
            if node.module:
                segs.append(node.module)
            segs.append(alias.name)
            dotted = ".".join([seg for seg in segs if seg])
            if _module_file(root, dotted) is None:
                names.add(alias.asname or alias.name)
                continue
            mods[alias.asname or alias.name] = (dotted, node.level)
    return mods, names


def module_binding(tree, root, first):
    """name -> dotted module, from imports only (no with-as, so no recursion)."""
    mods, _names = relative_from_scan(tree, root, [])
    if first in mods:
        return mods[first][0]
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


def two_level_with_as(tree, root):
    """The shipped with-as table, extended to a method from another module."""
    out = PNDCF.with_as_targets(tree, root)
    if tree is None:
        return out
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
            if not isinstance(func, ast.Attribute):
                continue
            receiver = receiver_module(tree, root, func)
            if not receiver:
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
            table = PNDCF.call_target_functions(sub, root)
            out[var.id] = (table.get(func.attr), "with-as-cross-call")
    return out


def class_constants(node, path):
    """Class-body str constants for a class path, or None when unreadable.

    Returns a dict of attr -> set(literals); a set with more than one literal is
    a mixed class body and is named rather than resolved.
    """
    if node is None or not path:
        return None
    for item in getattr(node, "body", []):
        if not isinstance(item, ast.ClassDef) or item.name != path[0]:
            continue
        if len(path) > 1:
            return class_constants(item, path[1:])
        out = {}
        for body in item.body:
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
    return None


def class_attribute(root, dotted, path, attr):
    """(decision, values, hop) for a class-body constant through its class path."""
    file_path = _module_file(root, dotted)
    if file_path is None:
        return None, set(), None
    try:
        tree = _parse(_read(file_path))
    except OSError:
        return None, set(), None
    if tree is None:
        return None, set(), None
    table = class_constants(tree, path)
    if table is None:
        return None, set(), None
    if attr not in table:
        return "class-constant", set(), "class"
    literals = table[attr]
    if len(literals) > 1:
        return "class-mixed", literals, "class"
    return "ok", set(literals), "class"


def _publish(got, state, value, reason, hop, chain=None):
    got["tl_state"] = state
    got["tl_value"] = value
    got["tl_reason"] = reason
    got["tl_hop"] = hop
    got["tl_source"] = SOURCE_TWO_LEVEL
    if chain is not None:
        got["tl_chain"] = list(chain)
    got["state"] = state
    got["value"] = value
    got["reason"] = reason
    return got


def two_level_entry(name, text, scope, line, tables=None, root=None,
                    src_path=None):
    """The shipped call-target answer, carried, plus this face own re-read."""
    root_path = BASE if root is None else root
    shipped = PNDCF.call_target_entry(name, text, scope, line, tables,
                                      root_path)
    got = dict(shipped)
    for key in sorted(shipped):
        got.setdefault(key, shipped[key])
    got["base_tl_state"] = shipped.get("state")
    got["base_tl_value"] = shipped.get("value")
    got["base_tl_reason"] = shipped.get("reason")
    got["base_tl_hop"] = shipped.get("ct_hop")
    got["tl_state"] = None
    got["tl_value"] = None
    got["tl_reason"] = None
    got["tl_hop"] = None
    got["tl_chain"] = []
    got["tl_source"] = None
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
        parts = package_parts(root_path, src_path)
    else:
        found = source_path(root_path, text)
        parts = package_parts(root_path, found) if found else []
    mods, rel_names = relative_from_scan(tree, root_path, parts)
    targets = two_level_with_as(tree, root_path)
    dotted = None
    hop = None
    if first in targets:
        dotted, hop = targets[first]
        if dotted is None:
            return _publish(got, STATE_REFUSED, None,
                            REFUSED_ATTR_CROSS_CALL % label,
                            hop, ["%s->?" % first])
    elif first in mods:
        dotted = mods[first][0]
        hop = "from-relative" if mods[first][1] > 1 else "from-import"
    elif first in rel_names:
        return _publish(got, STATE_REFUSED, None,
                        REFUSED_ATTR_RELATIVE_NAME % label,
                        "relative-from-name", ["%s->?" % first])
    else:
        imports = PNDC.import_bindings(tree)
        if first in imports:
            dotted = imports[first]
            hop = "import"
    if dotted is None:
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
                            REFUSED_ATTR_CLASS_MIXED % label,
                            "%s/%s" % (hop, sub_hop), chain)
        return _publish(got, STATE_REFUSED, None,
                        REFUSED_ATTR_CLASS_CONSTANT % label,
                        "%s/%s" % (hop, sub_hop), chain)
    decision, values, sub_hop = module_attribute_scoped(root_path, dotted, attr)
    chain = ["%s->%s.%s" % (first, dotted, attr)]
    if decision == "ok":
        return _publish(got, STATE_OK, sorted(values)[0], None,
                        "%s/%s" % (hop, sub_hop or "direct"), chain)
    if decision in ("mixed", "function-mixed"):
        return got
    if hop == "from-relative":
        return _publish(got, STATE_REFUSED, None,
                        REFUSED_ATTR_TWO_LEVEL % label,
                        "%s/%s" % (hop, sub_hop or "direct"), chain)
    return got


def two_level_report(text, root=None, src_path=None):
    """One row per loop the call-target reading publishes."""
    shipped = PNDCF.call_target_report(text, root)
    rows = []
    cache = {}
    for loop in shipped["loops"]:
        row = dict(loop)
        row["tl_followed"] = {}
        row["tl_refused"] = {}
        row["tl_chains"] = {}
        row["tl_hops"] = {}
        row["tl_resolved"] = []
        names = set()
        for key in ("followed", "refused", "attr_followed", "attr_refused",
                    "pred_followed", "pred_refused", "not_yet_bound",
                    "ia_followed", "ia_refused", "from_followed",
                    "from_refused", "from_resolved", "ct_followed",
                    "ct_refused", "ct_resolved"):
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
            got = two_level_entry(name, text, scope, loop["line"], tables,
                                  root, src_path)
            if got.get("tl_hop"):
                row["tl_hops"][name] = got["tl_hop"]
            if got.get("tl_chain"):
                row["tl_chains"][name] = got["tl_chain"]
            if got.get("tl_source") != SOURCE_TWO_LEVEL:
                continue
            if got.get("tl_state") == STATE_OK:
                row["tl_followed"][name] = got["tl_value"]
                row["tl_resolved"].append(name)
            elif got.get("tl_reason"):
                row["tl_refused"][name] = got["tl_reason"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["tl_scope_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in two_level_report(text, root, path)["loops"]:
        row["tl_scope_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped call-target audit, decorated with this face own readings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise TwoLevelError(E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNDCF.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise TwoLevelError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["base_tool"] = PNDCF.LABEL
    report["verdict"] = (SEAMS_TWO_LEVEL_STALE
                         if report.get("verdict") == PNDCF.SEAMS_CALL_TARGET_STALE
                         else SEAMS_TWO_LEVEL_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except TwoLevelError as exc:
        return {"tool": LABEL, "verdict": SEAMS_TWO_LEVEL_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_TWO_LEVEL_COVERED:
        raise TwoLevelError(report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="resolve a two-level relative import, a with-as call on a "
                    "method from another module, and a class-body constant, "
                    "and refuse a relative FROM-imported NAME")
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
            loops = row.get("tl_scope_loops") or []
            resolved = sum(len(loop["tl_resolved"]) for loop in loops)
            named = sum(len(loop["tl_refused"]) for loop in loops)
            sys.stdout.write(
                "  probe %s tl_scope_loops=%d tl_resolved=%d tl_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_TWO_LEVEL_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())