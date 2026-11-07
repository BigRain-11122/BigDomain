"""probe_seam_name_binding_nested_arm_mixed_scope - direct plus nested.

MEASURED at R2549 on the shipped nested exhaustive face own reader:

  (1) an arm that binds the name DIRECTLY and also contains a nested guard
      reads `mixed:<arm>` and never resolves, even when the direct value and
      every nested leaf agree;
  (2) a try nested under an arm that carries an else reads
      `incomplete:<group>` even when every handler arm agrees and the else arm
      rebinds the same literal;
  (3) a `with ... as KEY` binding inside an arm reads `non-literal:<arm>` and
      is never named `with-as`, so a with-bound key hides the reason it was
      refused.

This face answers all three ON TOP of the shipped law rather than instead of
it. The shipped nested face is asked FIRST (`arm_entry` asks it, and `audit`
asks its `audit`), and through it the shipped exhaustive face and the shipped
guard face are asked beside it, so every answer those three faces already gave
is carried on the row as base_* beside this face own answer:

  arm_tables(text)
      the shipped nested tables plus the try flags this face needs (handler
      count, else arm present, finally present), read from the same tree.
  arm_entry(name, text, scope, line, tables=None)
      the shipped nested answer, or, when that face refused, ONE folded
      answer:
        * a direct arm binding that AGREES with every leaf of a nested tree
          under it RESOLVES to that literal;
        * a direct binding that DISAGREES with a nested leaf publishes BOTH
          by full path and resolves nothing;
        * a try with an else that rebinds the same literal is COVERAGE, while
          an else that binds nothing is NAMED partial:else;
        * a `with ... as KEY` arm is NAMED with-as:<arm> and never resolved.
  arm_report(text)
      one row per loop the shipped nested reading publishes, each row
      carrying this face own followed / refused / arms / leaves / partial /
      loops and the nested face answer beside it.
  audit / reading / guard
      the shipped nested audit asked first, each probe row then decorated
      with this face own loops; the seam classifier is still the shipped
      registry `quiets` and nothing here is a second classifier.

RESOLUTION LAW, stated rather than buried: a tree resolves ONLY when every
group on it covers EVERY path AND every leaf path binds the same single string
literal. Coverage is if/elif/else with a final else, or a try with at least
one handler, no finally, and an else only when that else binds something. A
match is never resolved, a chain without a final else is never resolved, a
leaf that binds nothing or sits under a loop is never resolved, and a
condition is never evaluated, so the law is SHAPE based.

Read-only: nothing is written, no file is opened for writing, and every digest
this reading touches is unchanged across a full audit (AC-PNDP5). No probe and
no helper is ever imported or run.

Criteria AC-PNDP1..AC-PNDP6 were pinned in state/queue/tech.md:587 at R2549 as
the seed row BEFORE this code existed.

LIMIT, stated rather than buried: a try carrying a finally is still refused as
incomplete even when every arm agrees, two nested groups under one arm are
refused as grouped rather than merged, and a plain assignment anywhere before
the loop short-circuits the fold exactly as the shipped faces do. These shapes
can UNDER-report a stale probe but can never invent one.

Pure ASCII, stdlib only at module level, no clock, no network, writes nothing
but stdout.

CLI: --root DIR [--json]
  exit 0 = every probe quiets what it is responsible for
           (verdict SEAMS-ARM-MIXED-COVERED)
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

LABEL = "os-probe-seam-name-binding-nested-arm-mixed-scope"
E_ARGS = "E_PNDP_ARGS"
E_NO_ROOT = "E_PNDP_NO_ROOT"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_ARM_MIXED_COVERED = "SEAMS-ARM-MIXED-COVERED"
SEAMS_ARM_MIXED_STALE = "SEAMS-ARM-MIXED-STALE"

STATE_OK = "ok"
STATE_ARMS = "arms"
STATE_PARTIAL = "partial"
STATE_LOOP = "loop"
STATE_REFUSED = "refused"

REFUSED_PARTIAL = "partial:%s"
REFUSED_LOOP = "loop:%d"
REFUSED_NESTED_ARMS = "nested-arms"
REFUSED_INCOMPLETE = "incomplete:%s"
REFUSED_MATCH = "match:%d-cases"
REFUSED_GROUPED = "grouped:%s"
REFUSED_UNKNOWN = "unknown-group:%s"
REFUSED_NON_LITERAL = "non-literal:%s"
REFUSED_WITH_AS = "with-as:%s"
REFUSED_DISAGREE = "disagree:%s"
PATH_SEP = ">"
STEP_SEP = "/"
SOURCE_SHIPPED = "shipped"
SOURCE_NESTED = "nested"
SOURCE_ARM_MIXED = "arm-mixed"

SCOPE_MODULE = "module"

BASE = os.path.dirname(os.path.abspath(__file__))


class NameBindingNestedArmMixedError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _nested():
    """The shipped nested exhaustive face this module extends."""
    import probe_seam_name_binding_nested_exhaustive_path
    return probe_seam_name_binding_nested_exhaustive_path


def _direct():
    """The shipped direct-binding law, asked rather than restated."""
    return _nested()._flow()


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
    return _nested().render_module()


def seam_names(module=None):
    """The guard seams the SHIPPED render asks, derived at CALL time."""
    return _nested().seam_names(module)


def arm_tables(text):
    """Shipped nested tables plus the try flags this face needs."""
    base = _nested()
    tables = base.nested_tables(text)
    if tables is None:
        return None
    tree = _parse(text)
    flags = {}
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                flags["try:%d" % node.lineno] = {
                    "handlers": len(node.handlers),
                    "else": bool(node.orelse),
                    "finally": bool(node.finalbody),
                }
    tables["try_flags"] = flags
    return tables


def _scope_table(tables, scope):
    """The shipped scope law, asked rather than restated."""
    return _nested()._scope_table(tables, scope)


def _payload(key, info):
    return _nested()._group_payload(key, info)


def _path_text(path):
    return _nested()._path_text(path)


def _leaf(here, arm, values):
    return {"path": _path_text(here), "arm": arm,
            "value": (values[0] if len(values) == 1 else None),
            "values": list(values)}


def _literals(direct):
    """The single literal an arm binds, or the reason it cannot be one."""
    values = []
    for entry in direct:
        if entry["kind"] == "str":
            values.append(entry["value"])
        elif entry.get("shape") == "with-as":
            return None, REFUSED_WITH_AS
        else:
            return None, REFUSED_NON_LITERAL
    return sorted(set(values)), None


def _arm_plan(key, info, flags):
    """The arms that cover this group, or the reason it does not cover."""
    kind = info.get("kind")
    if kind == "match":
        return None, REFUSED_MATCH % info.get("cases", 0)
    if kind == "try":
        flag = flags.get(key) or {}
        if not flag.get("handlers"):
            return None, REFUSED_INCOMPLETE % key
        if flag.get("finally"):
            return None, REFUSED_INCOMPLETE % key
        arms = list(info.get("arms") or [])
        if flag.get("else"):
            arms.append("else")
        return arms, None
    if not info.get("exhaustive"):
        return None, REFUSED_INCOMPLETE % key
    return list(info.get("arms") or []), None


def _nested_keys(here, deeper):
    keys = []
    for entry in deeper:
        nxt = entry["path"][len(here)][0]
        if nxt not in keys:
            keys.append(nxt)
    return keys


def _direct_arm(arm, here, direct, leaves):
    values, why = _literals(direct)
    if why == REFUSED_WITH_AS:
        return {"state": STATE_REFUSED, "reason": REFUSED_WITH_AS % arm}
    if why:
        return {"state": STATE_REFUSED, "reason": REFUSED_NON_LITERAL % arm}
    leaves.append(_leaf(here, arm, values))
    if len(values) == 1:
        return {"state": STATE_OK, "value": values[0]}
    return {"state": STATE_ARMS, "reason": REFUSED_NESTED_ARMS,
            "values": values}


def _nested_arm(arm, here, deeper, groups, tables, leaves, payloads, depth):
    keys = _nested_keys(here, deeper)
    if len(keys) != 1:
        return {"state": STATE_REFUSED, "reason": REFUSED_GROUPED % arm}
    return _fold(keys[0], here, deeper, groups, tables, leaves, payloads,
                 depth + 1)


def _merge_arm(arm, here, direct, deeper, groups, tables, leaves, payloads,
               depth):
    """A direct arm binding merged with the nested tree under it."""
    values, why = _literals(direct)
    if why == REFUSED_WITH_AS:
        return {"state": STATE_REFUSED, "reason": REFUSED_WITH_AS % arm}
    if why:
        return {"state": STATE_REFUSED, "reason": REFUSED_NON_LITERAL % arm}
    keys = _nested_keys(here, deeper)
    if len(keys) != 1:
        return {"state": STATE_REFUSED, "reason": REFUSED_GROUPED % arm}
    inner_leaves = []
    folded = _fold(keys[0], here, deeper, groups, tables, inner_leaves,
                   payloads, depth + 1)
    leaves.append(_leaf(here, arm, values))
    if folded["state"] in (STATE_REFUSED, STATE_LOOP, STATE_PARTIAL):
        return {"state": folded["state"], "reason": folded["reason"]}
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


def _fold(key, prefix, entries, groups, tables, leaves, payloads, depth=0):
    """Fold one group: resolve only when every leaf binds the same literal."""
    info = groups.get(key)
    if info is None:
        return {"state": STATE_REFUSED, "reason": REFUSED_UNKNOWN % key}
    if depth > 16:
        return {"state": STATE_REFUSED, "reason": REFUSED_GROUPED % key}
    arms, refusal = _arm_plan(key, info, tables.get("try_flags") or {})
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
            results.append(_direct_arm(arm, here, direct, leaves))
            continue
        if deeper:
            results.append(_nested_arm(arm, here, deeper, groups, tables,
                                       leaves, payloads, depth))
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
    for item in results:
        if item["state"] == STATE_OK:
            values.append(item["value"])
        elif item["state"] == STATE_ARMS:
            values.extend(item.get("values") or [])
    values = sorted(set(values))
    if len(values) == 1:
        return {"state": STATE_OK, "value": values[0]}
    return {"state": STATE_ARMS, "reason": REFUSED_NESTED_ARMS,
            "values": values, "arms": list(results)}


def arm_entry(name, text, scope, line, tables=None):
    """The shipped nested answer, or this face own merged answer."""
    base = _nested()
    shipped = base.nested_entry(name, text, scope, line, tables)
    out = {"name": name, "scope": scope, "line": line,
           "state": STATE_REFUSED, "reason": None, "value": None,
           "source": SOURCE_SHIPPED,
           "base_nested_state": shipped.get("state"),
           "base_nested_reason": shipped.get("reason"),
           "base_nested_source": shipped.get("source"),
           "base_nested_followed": None,
           "base_state": shipped.get("base_state"),
           "base_reason": shipped.get("base_reason"),
           "base_guard_state": shipped.get("base_guard_state"),
           "base_guard_reason": shipped.get("base_guard_reason"),
           "root": None, "groups": [], "leaves": [], "partial": None,
           "loop": None, "cases": 0, "arms": [], "values": []}
    if shipped.get("state") == STATE_OK:
        out["state"] = STATE_OK
        out["value"] = shipped.get("value")
        out["reason"] = None
        out["source"] = shipped.get("source") or SOURCE_SHIPPED
        out["root"] = shipped.get("root")
        out["groups"] = list(shipped.get("groups") or [])
        return out
    if shipped.get("state") == STATE_ARMS:
        out["state"] = STATE_ARMS
        out["reason"] = shipped.get("reason")
        out["source"] = shipped.get("source") or SOURCE_SHIPPED
        out["arms"] = list(shipped.get("arms") or [])
        out["values"] = list(shipped.get("values") or [])
        return out
    tables = arm_tables(text) if tables is None else tables
    if tables is None:
        return out
    inner, where = _scope_table(tables, scope)
    if where != SCOPE_MODULE and name in inner:
        entries = list(inner[name])
    else:
        entries = list(tables["module"].get(name, []))
    before = [entry for entry in entries if entry["line"] <= line]
    plain = [entry for entry in before
             if not entry["path"] and not entry["loops"]
             and entry["kind"] != "condexpr"]
    if plain:
        return out
    conds = [entry for entry in before
             if not entry["path"] and not entry["loops"]
             and entry["kind"] == "condexpr"]
    if conds:
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
            info = tables["groups"].get(key)
            if info:
                payloads.append(_payload(key, info))
        out["groups"] = payloads
        out["reason"] = REFUSED_GROUPED % ",".join(roots)
        out["source"] = SOURCE_ARM_MIXED
        return out
    root = roots[0]
    leaves = []
    folded = _fold(root, (), before, tables["groups"], tables, leaves,
                   payloads)
    out["root"] = root
    out["groups"] = payloads
    out["leaves"] = leaves
    out["source"] = SOURCE_ARM_MIXED
    if folded["state"] == STATE_OK:
        out["state"] = STATE_OK
        out["reason"] = None
        out["value"] = folded["value"]
        return out
    out["state"] = STATE_REFUSED
    out["reason"] = folded.get("reason")
    if folded["state"] == STATE_PARTIAL:
        out["partial"] = folded.get("reason", "").split(":", 1)[-1]
    if folded["state"] == STATE_LOOP:
        out["loop"] = folded.get("reason")
    if folded["state"] == STATE_ARMS:
        out["state"] = STATE_ARMS
        out["values"] = list(folded.get("values") or [])
        out["arms"] = list(folded.get("arms") or [])
    if folded.get("cases"):
        out["cases"] = folded.get("cases")
    return out


def _guarded_names(tables, scope, line):
    inner, _where = _scope_table(tables, scope)
    names = set()
    for name, entries in inner.items():
        for entry in entries:
            if entry["path"] and entry["line"] <= line:
                names.add(name)
                break
    return names


def arm_report(text):
    """One row per loop the shipped nested reading publishes."""
    base = _nested()
    nested = base.nested_report(text)
    tables = arm_tables(text)
    rows = []
    for loop in nested["loops"]:
        names = set(loop["followed"]) | set(loop["refused"])
        for item in loop.get("arms") or []:
            names.add(item["name"])
        if tables is not None:
            names |= _guarded_names(tables, loop["scope"], loop["line"])
        row = {"line": loop["line"], "kind": loop["kind"],
               "scope": loop["scope"], "followed": {}, "refused": {},
               "arms": [], "leaves": {}, "partial": {}, "loops": {},
               "groups": [], "resolved_by_arm_mixed": [],
               "base_nested_followed": dict(loop["followed"]),
               "base_nested_refused": dict(loop["refused"]),
               "base_nested_arms": list(loop.get("arms") or []),
               "base_followed": dict(loop.get("base_followed") or {}),
               "base_refused": dict(loop.get("base_refused") or {}),
               "base_arms": list(loop.get("base_arms") or []),
               "base_guard_followed": dict(
                   loop.get("base_guard_followed") or {}),
               "base_guard_refused": dict(
                   loop.get("base_guard_refused") or {})}
        for name in sorted(names):
            got = arm_entry(name, text, row["scope"], row["line"], tables)
            if got["state"] == STATE_OK:
                row["followed"][name] = got["value"]
                if got["source"] == SOURCE_ARM_MIXED:
                    row["resolved_by_arm_mixed"].append(name)
            elif got["state"] == STATE_ARMS:
                row["arms"].append({"name": name, "arms": got["arms"],
                                    "leaves": got["leaves"]})
            else:
                row["refused"][name] = got["reason"]
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
    return {"tool": LABEL, "loops": rows, "parsed": nested["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["arm_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in arm_report(text)["loops"]:
        row["arm_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped nested audit, decorated with this face own folds."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise NameBindingNestedArmMixedError(E_NO_ROOT,
                                             "not a directory: %s"
                                             % root_path)
    base = _nested()
    try:
        report = base.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise NameBindingNestedArmMixedError(
            code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_ARM_MIXED_STALE
                         if report.get("verdict") == base.SEAMS_NESTED_STALE
                         else SEAMS_ARM_MIXED_COVERED)
    report["base_tool"] = base.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except NameBindingNestedArmMixedError as exc:
        return {"tool": LABEL, "verdict": SEAMS_ARM_MIXED_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_ARM_MIXED_COVERED:
        raise NameBindingNestedArmMixedError(report["verdict"],
                                             "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="merge a direct arm binding with its nested tree")
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
            loops = row["arm_loops"]
            resolved = sum(len(loop["resolved_by_arm_mixed"])
                           for loop in loops)
            sys.stdout.write("  probe %s arm_loops=%d arm_resolved=%d\n"
                             % (row["file"], len(loops), resolved))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_ARM_MIXED_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())