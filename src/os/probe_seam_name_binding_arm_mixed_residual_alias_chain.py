"""probe_seam_name_binding_arm_mixed_residual_alias_chain - alias chains.

MEASURED at R2553 on the shipped residual-naming face own reader, and
re-measured here BEFORE any code was written:

  (1) a module constant that is ITSELF bound to another module constant
      (`B = A` with `A = "b"`) reads `name-unbound:B`, so a one-hop reader
      answers nothing on a two-hop alias chain;
  (2) a constant declared INSIDE a function body reads `name-unbound:C` even
      though the loop that needs it sits in that same function;
  (3) a chain of three sequential groups under one arm where ONE group
      disagrees publishes both values under the reason `nested-arms`, so the
      row never says WHICH group disagreed.

This face answers all three ON TOP of the shipped residual law rather than
instead of it. The residual entry is asked FIRST and any answer that is not a
name refusal is returned UNCHANGED with that answer carried beside it
(AC-PNDR5). Only a `name-unbound:` or `name-mixed:` refusal is re-read here,
and every re-read runs the SAME shipped fold with an EXTENDED constant table:

  alias_tables(text, scope)
      the residual tables plus a constant table read to a FIXPOINT (a plain
      assignment or an annotated assignment whose right side is a bare NAME is
      an alias edge) with the loop own function body consulted before the
      module body, plus the map from a chain start to the name that actually
      carried two values.
  alias_entry(name, text, scope, line, tables=None)
      the residual answer, plus `alias_chain` (the names followed in order),
      `alias_terminal`, `mixed_terminal` and `disagreeing_group`.
  alias_report(text)
      one row per loop the residual reading publishes, each row carrying this
      face own followed / refused / chains / disagreeing groups.

Disclosed limits, measured this window rather than assumed: a name bound both
to a literal and to another name is not read as any constant; an alias cycle
is NAMED `name-cycle:<name>` rather than resolved; the alias table is built
from plain and annotated assignments only, so a walrus chain is not followed;
and the disagreeing group is only named when the row was refused by a
NAME refusal or by the multi-group fold - a row the shipped faces already
resolved keeps its shipped answer.

Stdlib only, ASCII source, zero network, no clock.
"""

import argparse
import ast
import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

LABEL = "os-probe-seam-name-binding-arm-mixed-residual-alias-chain"

E_ARGS = "E_PNDR_ARGS"
E_NO_ROOT = "E_PNDR_NO_ROOT"

STATE_OK = "ok"
STATE_ARMS = "arms"
STATE_PARTIAL = "partial"
STATE_LOOP = "loop"
STATE_REFUSED = "refused"

REFUSED_NAME_MIXED = "name-mixed:%s"
REFUSED_NAME_UNBOUND = "name-unbound:%s"
REFUSED_CYCLE = "name-cycle:%s"
REFUSED_NESTED_ARMS = "nested-arms"

SOURCE_BASE = "shipped"
SOURCE_ALIAS = "alias-chain"

SCOPE_MODULE = "module"

COVERED = "COVERED"
MISSING_SEAM = "MISSING-SEAM"
OUT_OF_SCOPE = "OUT-OF-SCOPE"
UNREADABLE = "UNREADABLE"
HISTORICAL = "HISTORICAL"

SEAMS_ALIAS_COVERED = "SEAMS-ALIAS-CHAIN-COVERED"
SEAMS_ALIAS_STALE = "SEAMS-ALIAS-CHAIN-STALE"

MAX_CHAIN = 8


class AliasChainError(Exception):
    """The probed root could not be read."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _base():
    """The shipped residual face this module extends."""
    import probe_seam_name_binding_arm_mixed_residual_naming
    return probe_seam_name_binding_arm_mixed_residual_naming


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


def _bindings(tree, entries):
    """(literals, aliases) read off one scope's own table entries.

    literals: name -> the literal values it binds.
    aliases:  name -> the single bare NAME it is assigned from.
    A name bound to both, or to two different names, is dropped from the
    tables rather than guessed at.
    """
    literals = {}
    aliases = {}
    targets = {}
    for entry in entries:
        name = entry.get("name")
        if not name:
            continue
        if entry.get("kind") == "str":
            literals.setdefault(name, set()).add(entry["value"])
            targets.setdefault(name, None)
            continue
        if entry.get("path") or entry.get("loops"):
            continue
        if entry.get("shape") == "with-as":
            continue
        rhs = _rhs_name(tree, entry.get("line"), name)
        if rhs is None:
            targets.setdefault(name, ("not-a-name",))
            continue
        aliases.setdefault(name, set()).add(rhs)
    out_lit = {}
    for name, values in literals.items():
        out_lit[name] = sorted(values)
    out_alias = {}
    for name, seen in aliases.items():
        if len(seen) == 1 and name not in out_lit:
            out_alias[name] = sorted(seen)[0]
    return out_lit, out_alias


def _rhs_name(tree, line, name):
    """The bare name a binding at this line assigns, or None."""
    if tree is None or line is None:
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


def _resolve(name, literals, aliases, seen=None):
    """Follow a chain to a FIXPOINT: (values, terminal, why)."""
    chain = [] if seen is None else list(seen)
    if len(chain) >= MAX_CHAIN:
        return None, name, REFUSED_CYCLE % name
    if name in chain:
        return None, name, REFUSED_CYCLE % name
    chain.append(name)
    values = literals.get(name) or []
    if len(values) > 1:
        return None, name, REFUSED_NAME_MIXED % name
    if len(values) == 1:
        return [values[0]], name, None
    target = aliases.get(name)
    if target is None:
        return None, name, REFUSED_NAME_UNBOUND % name
    values, terminal, why = _resolve(target, literals, aliases, chain)
    return values, terminal, why


def alias_tables(text, scope=None):
    """Residual tables plus a fixpoint constant table and the chain map."""
    tables = _base().residual_tables(text)
    if tables is None:
        return None
    tree = tables.get("tree")
    base = _base()._base()
    inner, where = base._scope_table(tables, scope or SCOPE_MODULE)
    mod_entries = []
    for values in tables["module"].values():
        mod_entries.extend(values)
    mod_lit, mod_alias = _bindings(tree, mod_entries)
    scope_lit, scope_alias = ({}, {})
    if where != SCOPE_MODULE and inner:
        entries = []
        for values in inner.values():
            entries.extend(values)
        scope_lit, scope_alias = _bindings(tree, entries)
    literals = dict(mod_lit)
    aliases = dict(mod_alias)
    literals.update(scope_lit)
    aliases.update(scope_alias)
    for name in scope_lit:
        aliases.pop(name, None)
    consts = {}
    mixed = {}
    cycles = {}
    chains = {}
    for name in sorted(set(literals) | set(aliases)):
        values, terminal, why = _resolve(name, literals, aliases)
        chains[name] = terminal
        if values is not None:
            consts[name] = list(values)
            continue
        if why and why.startswith("name-mixed:"):
            mixed[name] = terminal
            other = literals.get(terminal) or []
            if len(other) > 1:
                consts[name] = sorted(other)
            continue
        if why and why.startswith("name-cycle:"):
            cycles[name] = terminal
    out = dict(tables)
    out["consts"] = consts
    out["alias_mixed"] = mixed
    out["alias_cycles"] = cycles
    out["alias_chains"] = chains
    out["alias_hops"] = dict(aliases)
    out["alias_scope"] = where
    return out


def _rewrite_reason(reason, tables):
    """Name the chain end rather than the name the fold happened to ask."""
    if not reason:
        return reason
    if reason.startswith("name-mixed:"):
        asked = reason.split(":", 1)[1]
        end = (tables.get("alias_mixed") or {}).get(asked)
        if end and end != asked:
            return REFUSED_NAME_MIXED % end
        return reason
    if reason.startswith("name-unbound:"):
        asked = reason.split(":", 1)[1]
        cycles = tables.get("alias_cycles") or {}
        if asked in cycles:
            return REFUSED_CYCLE % cycles[asked]
    return reason


def _groups_of(entries, tables):
    """Every (prefix, key) group under these entries with its own values."""
    seen = []
    for entry in entries:
        for index in range(len(entry["path"])):
            here = tuple(entry["path"][:index])
            key = entry["path"][index][0]
            if (here, key) not in seen:
                seen.append((here, key))
    out = []
    for here, key in seen:
        folded = _base_fold2(key, here, entries, tables)
        if folded["state"] == STATE_OK:
            values = [folded["value"]]
        else:
            values = list(folded.get("values") or [])
        out.append({"depth": len(here), "key": key, "here": here,
                    "values": values, "state": folded["state"]})
    return out


def _base_fold2(key, prefix, entries, tables):
    """Ask the residual face own fold, side-effect free."""
    residual = _base()
    return residual._fold2(key, prefix, entries, tables["groups"], tables,
                          [], [], 0)


def disagreeing_group(entries, tables):
    """The group whose own leaves disagree, or the group that broke the tie."""
    groups = _groups_of(entries, tables)
    if not groups:
        return None
    deep = sorted(groups, key=lambda item: -item["depth"])
    for item in deep:
        if len(item["values"]) > 1:
            return item["key"]
    counts = {}
    for item in groups:
        for value in item["values"]:
            counts[value] = counts.get(value, 0) + 1
    if len(counts) < 2:
        return None
    best = sorted(counts.items(), key=lambda pair: -pair[1])[0][0]
    for item in groups:
        if item["values"] and item["values"] != [best]:
            return item["key"]
    return None


def alias_entry(name, text, scope, line, tables=None):
    """The residual answer, or this face own alias-chain re-read."""
    residual = _base()
    tables_full = alias_tables(text, scope) if tables is None else tables
    plain = residual.residual_entry(name, text, scope, line)
    got = plain
    if tables_full is not None:
        got = residual.residual_entry(name, text, scope, line, tables_full)
    out = dict(got)
    out["alias_chain"] = []
    out["alias_terminal"] = None
    out["mixed_terminal"] = None
    out["cycle_terminal"] = None
    out["disagreeing_group"] = None
    out["base_residual_state"] = plain.get("state")
    out["base_residual_reason"] = plain.get("reason")
    out["base_residual_source"] = plain.get("source")
    out["alias_source"] = SOURCE_BASE
    if tables_full is None:
        return out
    inner, where = residual._base()._scope_table(tables_full, scope)
    if where != SCOPE_MODULE and name in inner:
        entries = list(inner[name])
    else:
        entries = list(tables_full["module"].get(name, []))
    before = [entry for entry in entries if entry["line"] <= line]
    changed = (out.get("state") != plain.get("state")
               or out.get("reason") != plain.get("reason")
               or out.get("value") != plain.get("value"))
    if changed:
        out["source"] = SOURCE_ALIAS
        out["alias_source"] = SOURCE_ALIAS
        if out.get("reason") and out["reason"].startswith("name-cycle:"):
            out["cycle_terminal"] = out["reason"].split(":", 1)[1]
    group = disagreeing_group(before, tables_full)
    if group:
        out["disagreeing_group"] = group
        if out.get("state") == STATE_ARMS:
            out["reason"] = "%s:%s" % (REFUSED_NESTED_ARMS, group)
            out["alias_source"] = SOURCE_ALIAS
    chains = tables_full.get("alias_chains") or {}
    asked = name
    for entry in before:
        if entry.get("kind") != "str" and entry.get("shape") != "with-as":
            rhs = residual._rhs_name(tables_full.get("tree"),
                                     entry.get("line"), entry.get("name"))
            if rhs:
                asked = rhs
            break
    end = chains.get(asked) or chains.get(name)
    if end:
        out["alias_terminal"] = end
        out["alias_chain"] = _chain_text(asked if asked in chains or asked in
                                        (tables_full.get("alias_hops") or {})
                                         else name, tables_full)
    mixed = tables_full.get("alias_mixed") or {}
    if asked in mixed:
        out["mixed_terminal"] = mixed[asked]
    elif name in mixed:
        out["mixed_terminal"] = mixed[name]
    cycles = tables_full.get("alias_cycles") or {}
    if asked in cycles:
        out["cycle_terminal"] = cycles[asked]
    elif name in cycles:
        out["cycle_terminal"] = cycles[name]
    reason = out.get("reason") or ""
    if reason.startswith("name-mixed:"):
        head = reason.split(":", 1)[1]
        end = mixed.get(head)
        if end and end != head:
            out["reason"] = REFUSED_NAME_MIXED % end
            out["alias_source"] = SOURCE_ALIAS
    elif reason.startswith("name-unbound:"):
        head = reason.split(":", 1)[1]
        if head in cycles:
            out["reason"] = REFUSED_CYCLE % cycles[head]
            out["alias_source"] = SOURCE_ALIAS
    if out.get("reason") != plain.get("reason"):
        out["alias_source"] = SOURCE_ALIAS
    return out


def _chain_text(name, tables):
    """The names one chain walks, in the order they were followed."""
    hops = tables.get("alias_hops") or {}
    out = [name]
    seen = {name}
    here = name
    for _step in range(MAX_CHAIN):
        end = hops.get(here)
        if not end or end in seen:
            break
        out.append(end)
        seen.add(end)
        here = end
    return out


def alias_report(text):
    """One row per loop the residual reading publishes."""
    residual = _base()
    shipped = residual.residual_report(text)
    rows = []
    for loop in shipped["loops"]:
        names = set(loop["followed"]) | set(loop["refused"])
        for item in loop.get("arms") or []:
            names.add(item["name"])
        tables = alias_tables(text, loop["scope"])
        if tables is not None:
            names |= residual._guarded_names(tables, loop["scope"],
                                             loop["line"])
            names |= residual._with_as_names(tables, loop["scope"],
                                             loop["line"])
        row = {"line": loop["line"], "kind": loop["kind"],
               "scope": loop["scope"], "followed": {}, "refused": {},
               "resolved_by_alias": [], "chains": {}, "mixed": {},
               "cycles": {}, "disagreeing": {},
               "base_residual_followed": dict(loop["followed"]),
               "base_residual_refused": dict(loop["refused"]),
               "base_residual_arms": list(loop.get("arms") or []),
               "base_residual_groups_folded": dict(
                   loop.get("groups_folded") or {})}
        for name in sorted(names):
            got = alias_entry(name, text, row["scope"], row["line"], tables)
            if got["state"] == STATE_OK:
                row["followed"][name] = got["value"]
                if got.get("alias_source") == SOURCE_ALIAS:
                    row["resolved_by_alias"].append(name)
            elif got["state"] == STATE_ARMS:
                row["refused"][name] = got["reason"]
            else:
                row["refused"][name] = got["reason"]
            if got.get("alias_chain"):
                row["chains"][name] = got["alias_chain"]
            if got.get("mixed_terminal"):
                row["mixed"][name] = got["mixed_terminal"]
            if got.get("cycle_terminal"):
                row["cycles"][name] = got["cycle_terminal"]
            if got.get("disagreeing_group"):
                row["disagreeing"][name] = got["disagreeing_group"]
        rows.append(row)
    return {"tool": LABEL, "loops": rows, "parsed": shipped["parsed"],
            "index_of": [item["line"] for item in rows]}


def _decorate(root, row):
    path = os.path.join(root, row.get("file", ""))
    row["alias_loops"] = []
    if not os.path.isfile(path):
        return row
    try:
        text = _read(path)
    except OSError:
        return row
    for loop in alias_report(text)["loops"]:
        row["alias_loops"].append(loop)
    return row


def audit(root=None, module=None):
    """The shipped residual audit, decorated with this face own chains."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise AliasChainError(E_NO_ROOT, "not a directory: %s" % root_path)
    residual = _base()
    try:
        report = residual.audit(root_path, module)
    except Exception as exc:  # the shipped face own refusal, carried verbatim
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise AliasChainError(code, str(getattr(exc, "detail", exc)))
    for row in report.get("probes", []):
        _decorate(root_path, row)
    report["tool"] = LABEL
    report["verdict"] = (SEAMS_ALIAS_STALE
                         if report.get("verdict") == residual.SEAMS_RESIDUAL_STALE
                         else SEAMS_ALIAS_COVERED)
    report["base_tool"] = residual.LABEL
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except AliasChainError as exc:
        return {"tool": LABEL, "verdict": SEAMS_ALIAS_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_ALIAS_COVERED:
        raise AliasChainError(report["verdict"], "probe seams are stale")
    return report


def digest_file(path):
    """SHA-256 of a file, read as bytes (read-only helper for the suite)."""
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow name alias chains the residual face refused")
    parser.add_argument("--root", default=BASE,
                        help="directory of probe modules to read")
    parser.add_argument("--json", action="store_true", help="machine output")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 5
    if not os.path.isdir(args.root):
        sys.stderr.write("%s: not a directory: %s\n" % (E_NO_ROOT, args.root))
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
            loops = row.get("alias_loops") or []
            resolved = sum(len(loop["resolved_by_alias"]) for loop in loops)
            named = sum(len(loop["mixed"]) + len(loop["cycles"])
                        + len(loop["disagreeing"]) for loop in loops)
            sys.stdout.write(
                "  probe %s alias_loops=%d alias_resolved=%d alias_named=%d\n"
                % (row["file"], len(loops), resolved, named))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_ALIAS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())