"""A module alias HEAD bound by a WALRUS inside a MODULE-LEVEL BRANCH.

The shipped walrus-relative face (R2585) reads a walrus only when it is bound at
the TOP LEVEL of the module body. A walrus nested in a module-level `if`,
`else` or `try` body is invisible to it, so `if True:` then `(M := consts)`
followed by `BASE = M.HW` reads `attr-module-alias-unbound:M.HW` while the
honest answer is `b`. Two more shapes are measured in
qa/module-alias-walrus-branch-limits-R2587.log against private worlds:

  (a) one walrus inside a module-level branch is not followed;
  (b) the same name bound by a walrus on TWO branches is not resolved either,
      and the shipped reading does not say why;
  (c) a walrus inside a FUNCTION body is correctly NOT a module-level alias,
      which is the shipped design and is kept rather than changed.

The extension is applied THROUGH the shipped reading rather than beside it: the
readers the parent faces call at run time are swapped for this face own inside
one guarded block and restored in a finally, so every answer the eighteen
shipped faces already gave is carried unchanged on the row. A branch binding is
followed only when exactly ONE branch binds the name; two branches are NAMED
ambiguous rather than resolved to either.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAB1..AC-PNAB6 were pinned in state/queue/tech.md:619 at R2585
BEFORE this code existed.
"""

import argparse
import ast
import contextlib
import json
import os
import re
import sys
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa: E402

CS = PNT.CS
MA = PNT.MA
MAA = PNT.MAA
MAA2 = PNT.MAA2
TL = PNT.TL
CB = PNT.CB
PNDC = PNT.PNDC

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-scope")

E_ARGS = "E_PNAB_ARGS"
E_NO_ROOT = "E_PNAB_NO_ROOT"

STATE_OK = PNT.STATE_OK
STATE_REFUSED = PNT.STATE_REFUSED

COVERED = PNT.COVERED
MISSING_SEAM = PNT.MISSING_SEAM
OUT_OF_SCOPE = PNT.OUT_OF_SCOPE
UNREADABLE = PNT.UNREADABLE
HISTORICAL = PNT.HISTORICAL

SEAMS_BRANCH_COVERED = "SEAMS-BRANCH-WALRUS-COVERED"
SEAMS_BRANCH_STALE = "SEAMS-BRANCH-WALRUS-STALE"

REFUSED_AMBIGUOUS = "attr-module-alias-ambiguous:%s"

_BASE_PNT_VALUE = PNT.module_value_binding
_BASE_PNT_LEVEL = PNT.module_level_binding
_BASE_PNT_ENTRY = PNT.module_alias_entry
_BASE_PNT_REPORT = PNT.module_alias_report
_BASE_PNT_AUDIT = PNT.audit

_AMBIGUOUS_UNBOUND = re.compile(r"^attr-module-alias-unbound:ambiguous:(.+)$")

_TARGET_MODULES = [PNT, CS, MA, MAA, MAA2]

_RLOCK = threading.RLock()

_BRANCH_READS = []

_SEAMS = MA.SEAMS_MODULE_ALIAS_STALE
_SEAMS_COVERED = MA.SEAMS_MODULE_ALIAS_COVERED




class ModuleAliasWalrusBranchError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _walrus_in_body(body):
    """(name, value) for every WALRUS bound directly in one statement body."""
    for node in body:
        expr = None
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.NamedExpr):
            expr = node.value
        elif isinstance(node, ast.Assign) and isinstance(node.value,
                                                         ast.NamedExpr):
            expr = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value,
                                                            ast.NamedExpr):
            expr = node.value
        if expr is None:
            continue
        if isinstance(expr.target, ast.Name):
            yield expr.target.id, expr.value


def _branch_bindings(tree, name):
    """[(value, branch)] for every module-level branch that binds `name`."""
    found = []
    if tree is None:
        return found
    for node in tree.body:
        sections = []
        if isinstance(node, ast.If):
            sections = [(node.body, "if"), (node.orelse, "else")]
        elif isinstance(node, ast.Try):
            sections = [(node.body, "try"), (node.orelse, "else"),
                        (node.finalbody, "finally")]
            for handler in node.handlers:
                sections.append((handler.body, "except"))
        else:
            continue
        for body, label in sections:
            for bound, value in _walrus_in_body(body):
                if bound == name:
                    found.append((value, label))
    return found


def branch_walrus_reading(tree, name):
    """The branch answer for one name, published rather than guessed.

    state is "ok" for one branch, "ambiguous" for two or more, and "none"
    when no module-level branch binds the name.
    """
    found = _branch_bindings(tree, name)
    labels = [label for _value, label in found]
    if not found:
        return {"state": "none", "branches": [], "value": None}
    if len(found) > 1:
        return {"state": "ambiguous", "branches": sorted(set(labels)),
                "value": None,
                "reason": "ambiguous:%s@%s"
                          % (name, "+".join(sorted(set(labels))))}
    return {"state": "ok", "branches": labels, "value": found[0][0]}


def module_value_binding(tree, name):
    """The shipped module-level expression, extended to a branch WALRUS."""
    value = _BASE_PNT_VALUE(tree, name)
    if value is not None:
        return value
    got = branch_walrus_reading(tree, name)
    if got["state"] == "ok":
        _BRANCH_READS.append("branch:%s@%s" % (name, got["branches"][0]))
        return got["value"]
    if got["state"] == "ambiguous":
        _BRANCH_READS.append(got["reason"])
    return None


def module_level_binding(tree, name, seen=None):
    """The shipped alias chain, extended to a branch WALRUS link."""
    value, chain, broken = _BASE_PNT_LEVEL(tree, name, seen)
    if value is not None or broken is None:
        return value, chain, broken
    seen = set() if seen is None else seen
    if broken in seen:
        return value, chain, broken
    seen.add(broken)
    got = branch_walrus_reading(tree, broken)
    if got["state"] == "ambiguous":
        return None, list(chain), got["reason"]
    if got["state"] != "ok":
        return value, chain, broken
    walrus = got["value"]
    label = got["branches"][0]
    if isinstance(walrus, ast.Name):
        deeper_value, deeper_chain, deeper_broken = module_level_binding(
            tree, walrus.id, seen)
        return deeper_value, list(chain) + list(deeper_chain[1:]), \
            deeper_broken
    return walrus, list(chain) + ["%s:=%s@%s" % (broken, broken, label)], None


@contextlib.contextmanager
def extended_readers():
    """Swap the shipped readers for this face own and restore them.

    The parent context takes a plain lock, and this face nests inside it, so
    the lock is swapped for a re-entrant one for the span of the block and put
    back afterwards. A single process owns these readers, so the exclusion
    this buys is unchanged.
    """
    saved_lock = PNT._LOCK
    PNT._LOCK = _RLOCK
    try:
        with _RLOCK:
            with _patched_readers():
                yield
    finally:
        PNT._LOCK = saved_lock


@contextlib.contextmanager
def _patched_readers():
    with PNT.extended_readers():
        saved = []
        for module in _TARGET_MODULES:
            if hasattr(module, "module_value_binding"):
                saved.append((module, "module_value_binding",
                              module.module_value_binding))
                module.module_value_binding = module_value_binding
            if hasattr(module, "module_level_binding"):
                saved.append((module, "module_level_binding",
                              module.module_level_binding))
                module.module_level_binding = module_level_binding
        try:
            yield
        finally:
            for module, attribute, original in reversed(saved):
                setattr(module, attribute, original)


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The shipped walrus-relative answer, re-read with branch bindings."""
    base = _BASE_PNT_ENTRY(name, text, scope, line, tables, root, src_path)
    del _BRANCH_READS[:]
    with extended_readers():
        got = _BASE_PNT_ENTRY(name, text, scope, line, tables, root, src_path)
    branch_reads = sorted(set(_BRANCH_READS))
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out["base_pnab_state"] = base.get("state")
    out["base_pnab_value"] = base.get("value")
    out["base_pnab_reason"] = base.get("reason")
    out["base_pnab_hop"] = base.get("pnaa_hop") or base.get("pnam_hop") or \
        base.get("ma_hop")
    out["branch_reads"] = branch_reads
    reason = out.get("reason") or ""
    match = _AMBIGUOUS_UNBOUND.match(reason)
    if match:
        out["reason"] = REFUSED_AMBIGUOUS % match.group(1)
        out["refusal_source"] = "this-face"
        out["branch_ambiguous"] = match.group(1)
    ambiguous = [item for item in branch_reads
                 if item.startswith("ambiguous:")]
    if ambiguous and out.get("state") == STATE_REFUSED:
        detail = ambiguous[0][len("ambiguous:"):]
        out["reason"] = REFUSED_AMBIGUOUS % detail
        out["refusal_source"] = "this-face"
        out["branch_ambiguous"] = detail
    followed = [item for item in branch_reads if item.startswith("branch:")]
    if followed and out.get("state") == STATE_OK and out.get("ma_chain"):
        out["ma_chain"] = list(out["ma_chain"]) + followed
    return out


def module_alias_report(text, root=None, src_path=None):
    """One row per loop, read through the extended readers."""
    with extended_readers():
        return _BASE_PNT_REPORT(text, root, src_path)


def audit(root=None, module=None):
    """The shipped module-alias audit, re-read with branch bindings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasWalrusBranchError(E_NO_ROOT,
                                           "not a directory: %s" % root_path)
    with extended_readers():
        try:
            report = _BASE_PNT_AUDIT(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasWalrusBranchError(
                code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNT.LABEL
    report["verdict"] = (SEAMS_BRANCH_STALE
                         if report.get("verdict") == _SEAMS
                         else SEAMS_BRANCH_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasWalrusBranchError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_BRANCH_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_BRANCH_COVERED:
        raise ModuleAliasWalrusBranchError(report["verdict"],
                                           "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias head bound by a walrus inside a "
                    "module-level branch")
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
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_BRANCH_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())