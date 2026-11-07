"""probe_seam_name_binding_arm_mixed_residual_naming - the residual naming.

MEASURED at R2551 on the shipped arm-mixed face own reader:

  (1) a `with ... as KEY` binding at module or function level, OUTSIDE any
      guarded arm, comes back as a refusal whose reason is literally None, so
      the caller is told nothing about why it was refused;
  (2) two SEQUENTIAL nested guard groups under one arm read `grouped:<arm>`
      and never resolve, even when every leaf of both groups binds the same
      single literal;
  (3) a direct arm binding written through ONE module-level constant NAME
      (`KEY = CONST` where `CONST = "b"`) reads `non-literal:<arm>` even
      though the name itself binds exactly one literal.

This face answers all three ON TOP of the shipped arm-mixed law rather than
instead of it. The shipped arm-mixed entry is asked FIRST, and when it already
answers OK or ARMS that answer is returned UNCHANGED with the shipped verdict
carried beside it (AC-PNDQ5). Only a refusal from that face is re-read here:

  residual_tables(text)
      the shipped arm-mixed tables plus a module-level constant table
      (name -> the single value it binds) and the parsed tree.
  residual_entry(name, text, scope, line, tables=None)
      the shipped answer, or ONE residual answer:
        * a plain with-as binding is NAMED `with-as:<scope>` and never
          published with an empty reason;
        * two or more sequential groups under one arm are folded together and
          resolve to that literal when every leaf agrees;
        * when those groups disagree, BOTH values are published by full path
          and nothing is resolved;
        * a direct arm binding through ONE module-level constant name resolves
          to that constant literal, while a name bound to more than one value
          is NAMED `name-mixed:<name>` and never guessed.
  residual_report(text)
      one row per loop the shipped arm-mixed reading publishes, each row
      carrying this face own followed / refused / leaves / groups and the
      shipped arm-mixed answer beside it as base_*.
  audit / reading / guard
      the shipped arm-mixed audit asked first, each probe row then decorated
      with this face own loops; the seam classifier is still the shipped
      registry `quiets` and nothing here is a second classifier.

RESOLUTION LAW, stated rather than buried: a tree resolves ONLY when every
group on it covers EVERY path AND every leaf path binds the same single string
literal, where "binds" now includes a direct `NAME = CONST` whose CONST is a
module-level name bound to exactly one literal. A name bound twice is refused
by name, a with-as binding is refused by name, a match, a chain without a
final else, a leaf that binds nothing and a leaf under a loop are never
resolved, and a condition is never evaluated, so the law is SHAPE based.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNDQ5). No probe and
no helper is ever imported or run.

Criteria AC-PNDQ1..AC-PNDQ6 were pinned in state/queue/tech.md:589 at R2551 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: only ONE module-level constant hop is
followed, a constant bound inside a function body is not a module constant, a
try carrying a finally is still refused as incomplete, and a plain assignment
anywhere before the loop short-circuits the fold exactly as the shipped faces
do. These shapes can UNDER-report a stale probe but can never invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-RESIDUAL-COVERED)
  exit 2 = a probe is MISSING-SEAM or a source will not parse
  exit 3 = the root is missing or unreadable
  exit 5 = bad arguments
"""

import argparse
import ast
import hashlib
import json
import os
import sys

LABEL = "os-probe-seam-name-binding-arm-mixed-residual-naming"
E_ARGS = "E_PNDQ_ARGS"
E_NO_ROOT = "E_PNDQ_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_RESIDUAL_COVERED = "SEAMS-RESIDUAL-COVERED"
SEAMS_RESIDUAL_STALE = "SEAMS-RESIDUAL-STALE"

STATE_OK = "ok"
STATE_ARMS = "arms"
STATE_PARTIAL = "partial"
STATE_LOOP = "loop"
STATE_REFUSED = "refused"

REFUSED_WITH_AS = "with-as:%s"
REFUSED_NAME_MIXED = "name-mixed:%s"
REFUSED_NAME_UNBOUND = "name-unbound:%s"
REFUSED_DISAGREE = "disagree:%s"
REFUSED_GROUPED = "grouped:%s"
REFUSED_NON_LITERAL = "non-literal:%s"
REFUSED_NESTED_ARMS = "nested-arms"
REFUSED_UNKNOWN = "unknown-group:%s"
REFUSED_PARTIAL = "partial:%s"
REFUSED_LOOP = "loop:%d"

SOURCE_BASE = "shipped"
SOURCE_RESIDUAL = "arm-mixed-residual"

SCOPE_MODULE = "module"

BASE = os.path.dirname(os.path.abspath(__file__))


class NameBindingResidualNamingError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base():
    """The shipped arm-mixed face this module extends."""
    import probe_seam_name_binding_nested_arm_mixed_scope
    return probe_seam_name_binding_nested_arm_mixed_scope


def _parse(text):
    try:
        return ast.parse(text)
    except (SyntaxError, ValueError):
        return None


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def render_module():
    """The shipped render, imported through the shipped face chain."""
    return _base().render_module()


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    return _base().seam_names(module)


def residual_tables(text):
    """Shipped arm-mixed tables plus a module constant table and the tree."""
    base = _base()
    tables = base.arm_tables(text)
    if tables is None:
        return None
    consts = {}
    for name, entries in (tables.get("module") or {}).items():
        values = sorted({entry["value"] for entry in entries
                         if entry.get("kind") == "str"})
        if values:
            consts[name] = values
    tables["consts"] = consts
    tables["tree"] = _parse(text)
    return tables


def _rhs_name(tree, line, name):
    """The bare name a binding at this line assigns, or None."""
    if tree is None:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and node.lineno == line:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    if isinstance(node.value, ast.Name):
                        return node.value.id
        if isinstance(node, ast.AnnAssign) and node.lineno == line:
            if isinstance(node.target, ast.Name) and node.target.id == name:
                if isinstance(node.value, ast.Name):
                    return node.value.id
    return None


def _literals2(direct, tables):
    """The single literal an arm binds, or the reason it cannot be one."""
    values = []
    for entry in direct:
        if entry.get("kind") == "str":
            values.append(entry["value"])
            continue
        if entry.get("shape") == "with-as":
            return None, REFUSED_WITH_AS
        name = _rhs_name(tables.get("tree"), entry["line"], entry["name"])
        if not name:
            return None, REFUSED_NON_LITERAL
        found = (tables.get("consts") or {}).get(name) or []
        if len(found) == 1:
            values.append(found[0])
            continue
        if len(found) > 1:
            return None, REFUSED_NAME_MIXED % name
        return None, REFUSED_NAME_UNBOUND % name
    return sorted(set(values)), None


def _path_text(path):
    return _base()._path_text(path)


def _leaf(here, arm, values):
    return {"path": _path_text(here), "arm": arm,
            "value": (values[0] if len(values) == 1 else None),
            "values": list(values)}


def _nested_keys(here, deeper):
    return _base()._nested_keys(here, deeper)


def _payload(key, info):
    return _base()._payload(key, info)


def _group_key(here, deeper, leaves, groups, tables, payloads, depth):
    """Fold several sequential groups under one point and merge their leaves."""
    keys = _nested_keys(here, deeper)
    parts = []
    for key in keys:
        sub_leaves = []
        folded = _fold2(key, here, deeper, groups, tables, sub_leaves,
                        payloads, depth + 1)
        parts.append((key, folded, sub_leaves))
    for want in (STATE_REFUSED, STATE_LOOP, STATE_PARTIAL):
        for key, folded, _sub in parts:
            if folded["state"] == want:
                return {"state": want, "reason": folded.get("reason")}
    values = []
    details = []
    for key, folded, sub_leaves in parts:
        leaves.extend(sub_leaves)
        details.append(folded)
        if folded["state"] == STATE_OK:
            values.append(folded["value"])
        else:
            values.extend(folded.get("values") or [])
    values = sorted(set(values))
    if len(values) == 1:
        return {"state": STATE_OK, "value": values[0], "groups_folded": keys}
    return {"state": STATE_ARMS, "reason": REFUSED_DISAGREE,
            "values": values, "arms": details, "groups_folded": keys}


def _direct_arm(arm, here, direct, tables, leaves):
    values, why = _literals2(direct, tables)
    if why == REFUSED_WITH_AS:
        return {"state": STATE_REFUSED, "reason": REFUSED_WITH_AS % arm}
    if why:
        if "%s" in why:
            return {"state": STATE_REFUSED, "reason": why % arm}
        return {"state": STATE_REFUSED, "reason": why}
    leaves.append(_leaf(here, arm, values))
    if len(values) == 1:
        return {"state": STATE_OK, "value": values[0]}
    return {"state": STATE_ARMS, "reason": REFUSED_NESTED_ARMS,
            "values": values}


def _merge_arm(arm, here, direct, deeper, groups, tables, leaves, payloads,
               depth):
    """A direct arm binding merged with every nested group under it."""
    values, why = _literals2(direct, tables)
    if why == REFUSED_WITH_AS:
        return {"state": STATE_REFUSED, "reason": REFUSED_WITH_AS % arm}
    if why:
        return {"state": STATE_REFUSED, "reason": why}
    inner_leaves = []
    folded = _group_key(here, deeper, inner_leaves, groups, tables, payloads,
                        depth)
    leaves.append(_leaf(here, arm, values))
    if folded["state"] in (STATE_REFUSED, STATE_LOOP, STATE_PARTIAL):
        return {"state": folded["state"], "reason": folded.get("reason")}
    leaves.extend(inner_leaves)
    if folded["state"] == STATE_OK:
        inner = [folded["value"]]
    else:
        inner = list(folded.get("values") or [])
    both = sorted(set(values) | set(inner))
    if len(values) == 1 and len(inner) == 1 and values[0] == inner[0]:
        return {"state": STATE_OK, "value": values[0]}
    return {"state": STATE_ARMS, "reason": REFUSED_DISAGREE % arm,
            "values": both}


def _fold2(key, prefix, entries, groups, tables, leaves, payloads, depth=0):
    """Fold one group: resolve only when every leaf binds the same literal."""
    info = groups.get(key)
    if info is None:
        return {"state": STATE_REFUSED, "reason": REFUSED_UNKNOWN % key}
    if depth > 16:
        return {"state": STATE_REFUSED, "reason": REFUSED_GROUPED % key}
    arms, refusal = _base()._arm_plan(key, info,
                                      tables.get("try_flags") or {})
    if refusal:
        out = {"state": STATE_REFUSED, "reason": refusal}
        if info.get("kind") == "match":
            out["cases"] = info.get("cases", 0)
        return out
    if not [item for item in payloads if item["group"] == key]:
        payloads.append(_payload(key, info))
    results = []
    for arm in arms:
        here = tuple(prefix) + ((key, arm),)
        direct = [entry for entry in entries if entry["path"] == here]
        deeper = [entry for entry in entries
                  if len(entry["path"]) > len(here)
                  and entry["path"][:len(here)] == here]
        loop_hit = [entry for entry in direct + deeper if entry["loops"]]
        if loop_hit:
            results.append({"state": STATE_LOOP,
                            "reason": REFUSED_LOOP % loop_hit[0]["loops"][0]})
            continue
        if direct and deeper:
            results.append(_merge_arm(arm, here, direct, deeper, groups,
                                      tables, leaves, payloads, depth))
            continue
        if direct:
            results.append(_direct_arm(arm, here, direct, tables, leaves))
            continue
        if deeper:
            results.append(_group_key(here, deeper, leaves, groups, tables,
                                      payloads, depth))
            continue
        leaves.append({"path": _path_text(here), "arm": arm, "value": None,
                       "values": []})
        results.append({"state": STATE_PARTIAL,
                        "reason": REFUSED_PARTIAL % arm})
    for want in (STATE_REFUSED, STATE_LOOP, STATE_PARTIAL):
        for item in results:
            if item["state"] == want:
                return item
    values = []
    folded_groups = []
    for item in results:
        folded_groups.extend(item.get("groups_folded") or [])
        if item["state"] == STATE_OK:
            values.append(item["value"])
        elif item["state"] == STATE_ARMS:
            values.extend(item.get("values") or [])
    values = sorted(set(values))
    if len(values) == 1:
        out = {"state": STATE_OK, "value": values[0]}
        if folded_groups:
            out["groups_folded"] = folded_groups
        return out
    return {"state": STATE_ARMS, "reason": REFUSED_NESTED_ARMS,
            "values": values, "arms": list(results)}


def residual_entry(name, text, scope, line, tables=None):
    """The shipped arm-mixed answer, or this face own residual answer."""
    base = _base()
    tables_full = residual_tables(text) if tables is None else tables
    shipped = base.arm_entry(name, text, scope, line, tables_full)
    out = {"name": name, "scope": scope, "line": line,
           "state": shipped.get("state"),
           "reason": shipped.get("reason"),
           "value": shipped.get("value"),
           "values": list(shipped.get("values") or []),
           "source": shipped.get("source"),
           "root": shipped.get("root"),
           "groups": list(shipped.get("groups") or []),
           "leaves": list(shipped.get("leaves") or []),
           "partial": shipped.get("partial"),
           "loop": shipped.get("loop"),
           "cases": shipped.get("cases", 0),
           "arms": list(shipped.get("arms") or []),
           "base_arm_mixed_state": shipped.get("state"),
           "base_arm_mixed_reason": shipped.get("reason"),
           "base_arm_mixed_source": shipped.get("source"),
           "base_nested_state": shipped.get("base_nested_state"),
           "base_nested_reason": shipped.get("base_nested_reason"),
           "base_state": shipped.get("base_state"),
           "base_reason": shipped.get("base_reason"),
           "base_guard_state": shipped.get("base_guard_state"),
           "base_guard_reason": shipped.get("base_guard_reason"),
           "with_as": False, "name_mixed": None, "groups_folded": []}
    if shipped.get("state") in (STATE_OK, STATE_ARMS):
        return out
    if tables_full is None:
        return out
    inner, where = base._scope_table(tables_full, scope)
    if where != SCOPE_MODULE and name in inner:
        entries = list(inner[name])
    else:
        entries = list(tables_full["module"].get(name, []))
    before = [entry for entry in entries if entry["line"] <= line]
    plain = [entry for entry in before
             if not entry["path"] and not entry["loops"]
             and entry.get("kind") != "condexpr"]
    plain_literals = [entry for entry in plain
                      if entry.get("kind") == "str"]
    with_as = [entry for entry in plain
               if entry.get("shape") == "with-as"]
    if with_as and not plain_literals:
        out["state"] = STATE_REFUSED
        out["reason"] = REFUSED_WITH_AS % scope
        out["source"] = SOURCE_RESIDUAL
        out["with_as"] = True
        return out
    conds = [entry for entry in before
             if not entry["path"] and not entry["loops"]
             and entry.get("kind") == "condexpr"]
    if conds or plain:
        return out
    roots = []
    for entry in before:
        if entry["path"]:
            root = entry["path"][0][0]
            if root not in roots:
                roots.append(root)
    if not roots:
        return out
    payloads = []
    if len(roots) > 1:
        for key in roots:
            info = tables_full["groups"].get(key)
            if info:
                payloads.append(_payload(key, info))
        out["groups"] = payloads
        out["reason"] = REFUSED_GROUPED % ",".join(roots)
        out["source"] = SOURCE_RESIDUAL
        return out
    root = roots[0]
    leaves = []
    folded = _fold2(root, (), before, tables_full["groups"], tables_full,
                    leaves, payloads)
    out["root"] = root
    out["groups"] = payloads
    out["leaves"] = leaves
    out["source"] = SOURCE_RESIDUAL
    out["groups_folded"] = list(folded.get("groups_folded") or [])
    reason = folded.get("reason")
    if reason and reason.startswith("name-mixed:"):
        out["name_mixed"] = reason.split(":", 1)[1]
    if folded["state"] == STATE_OK:
        out["state"] = STATE_OK
        out["reason"] = None
        out["value"] = folded["value"]
        return out
    out["state"] = STATE_REFUSED
    out["reason"] = reason
    if folded["state"] == STATE_PARTIAL:
        out["partial"] = (reason or "").split(":", 1)[-1]
    if folded["state"] == STATE_LOOP:
        out["loop"] = reason
    if folded["state"] == STATE_ARMS:
        out["state"] = STATE_ARMS
        out["values"] = list(folded.get("values") or [])
        out["arms"] = list(folded.get("arms") or [])
    if folded.get("cases"):
        out["cases"] = folded.get("cases")
    return out


def _guarded_names(tables, scope, line):
    inner, _where = _base()._scope_table(tables, scope)
    names = set()
    for name, entries in inner.items():
        for entry in entries:
            if entry["path"] and entry["line"] <= line:
                names.add(name)
                break
    return names


def _with_as_names(tables, scope, line):
    """Plain with-as bindings in this scope, so they can be NAMED not dropped."""
    inner, _where = _base()._scope_table(tables, scope)
    names = set()
    for name, entries in inner.items():
        for entry in entries:
            if (not entry["path"] and not entry["loops"]
                    and entry.get("shape") == "with-as"
                    and entry["line"] <= line):
                names.add(name)
                break
    return names


def residual_report(text):
    """One row per loop the shipped arm-mixed reading publishes."""
    base = _base()
    shipped = base.arm_report(text)
    tables = residual_tables(text)
    rows = []
    for loop in shipped["loops"]:
        names = set(loop["followed"]) | set(loop["refused"])
        for item in loop.get("arms") or []:
            names.add(item["name"])
        if tables is not None:
            names |= _guarded_names(tables, loop["scope"], loop["line"])
            names |= _with_as_names(tables, loop["scope"], loop["line"])
        row = {"line": loop["line"], "kind": loop["kind"],
               "scope": loop["scope"], "followed": {}, "refused": {},
               "arms": [], "leaves": {}, "partial": {}, "loops": {},
               "groups": [], "resolved_by_residual": [],
               "named_with_as": {}, "named_name_mixed": {},
               "groups_folded": {},
               "base_arm_mixed_followed": dict(loop["followed"]),
               "base_arm_mixed_refused": dict(loop["refused"]),
               "base_arm_mixed_arms": list(loop.get("arms") or []),
               "base_nested_followed": dict(loop["base_nested_followed"]),
               "base_nested_refused": dict(loop["base_nested_refused"]),
               "base_nested_arms": list(loop.get("base_nested_arms") or []),
               "base_followed": dict(loop.get("base_followed") or {}),
               "base_refused": dict(loop.get("base_refused") or {}),
               "base_arms": list(loop.get("base_arms") or []),
               "base_guard_followed": dict(
                   loop.get("base_guard_followed") or {}),
               "base_guard_refused": dict(
                   loop.get("base_guard_refused") or {})}
        for name in sorted(names):
            got = residual_entry(name, text, row["scope"], row["line"],
                                 tables)
            if got["state"] == STATE_OK:
                row["followed"][name] = got["value"]
                if got["source"] == SOURCE_RESIDUAL:
                    row["resolved_by_residual"].append(name)
            elif got["state"] == STATE_ARMS:
                row["arms"].append({"name": name, "arms": got["arms"],
                                    "leaves": got["leaves"],
                                    "values": got["values"],
                                    "reason": got["reason"]})
            else:
                row["refused"][name] = got["reason"]
            if got.get("with_as"):
                row["named_with_as"][name] = got["reason"]
            if got.get("name_mixed"):
                row["named_name_mixed"][name] = got["name_mixed"]
            if got.get("groups_folded"):
                row["groups_folded"][name] = got["groups_folded"]
            if got.get("leaves"):
                row["leaves"][name] = got["leaves"]
            if got.get("partial"):
                row["partial"][name] = got["partial"]
            if got.get("loop"):
                row["loops"][name] = got["loop"]
            for payload in got.get("groups") or []:
                if payload not in row["groups"]:
                    row["groups"].append(payload)
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["residual_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in residual_report(text)["loops"]:
        row["residual_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped arm-mixed audit, decorated with this face own folds."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise NameBindingResidualNamingError(E_NO_ROOT,
                                             "not a directory: %s"
                                             % root_path)
    base = _base()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise NameBindingResidualNamingError(
            code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_RESIDUAL_STALE
                         if report.get("verdict") == base.SEAMS_ARM_MIXED_STALE
                         else SEAMS_RESIDUAL_COVERED)
    report["base_tool"] = base.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except NameBindingResidualNamingError as exc:
        return {"tool": LABEL, "verdict": SEAMS_RESIDUAL_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_RESIDUAL_COVERED:
        raise NameBindingResidualNamingError(report["verdict"],
                                             "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="name the residual shapes the arm-mixed face refused")
    parser.add_argument("--root", default=BASE,
                        help="directory of probe modules to read")
    parser.add_argument("--json", action="store_true", help="machine output")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 5
    if not os.path.isdir(args.root):
        sys.stderr.write("%s: not a directory: %s\n"
                         % (E_NO_ROOT, args.root))
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
            loops = row["residual_loops"]
            resolved = sum(len(loop["resolved_by_residual"])
                           for loop in loops)
            named = sum(len(loop["named_with_as"])
                        + len(loop["named_name_mixed"]) for loop in loops)
            sys.stdout.write(
                "  probe %s residual_loops=%d residual_resolved=%d "
                "residual_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_RESIDUAL_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())