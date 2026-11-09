"""A module alias HEAD bound by a WALRUS inside a module-level WHILE or CASE.

The shipped branch faces follow a walrus bound in a module-level `if` body, its
`elif` and `else` sections, a module-level `with` body and a module-level `try`
body, and name the branch it was read in. They stop there: `while` bodies and
`match` `case` bodies are invisible because the branch table lists only `if`
chains, `with` bodies and `try` sections, so

    while a1:
        (M := consts)
    BASE = M.HW

still reads `attr-module-alias-unbound:M.HW`. Two shapes were measured at
R2588 with src/os/limits_module_alias_walrus_elif_with_next_R2588.py against
private worlds and re-measured here BEFORE any code with
src/os/limits_module_alias_walrus_elif_with_next_R2590.py: both the `while`
body and the `match` `case` body read the shipped refusal, and the `for` body
plus the branch nested inside another branch read it too - and those two stay
refused on purpose.

The extension is applied THROUGH the shipped reading rather than beside it: the
branch table the R2588 readers call at run time is swapped for this face own
inside one guarded block and restored in a finally, so every answer the twenty
shipped faces already gave is carried unchanged on the row. A `for` body, a
branch nested inside another branch and a `while` `else` are still not
descended into, which is the shipped refusal kept rather than changed.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAD1..AC-PNAD6 were pinned in state/queue/tech.md:623 at R2588
BEFORE this code existed.
"""

import argparse
import ast
import contextlib
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_scope as PNAC  # noqa: E402

PNAB = PNAC.PNAB

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-while-match-scope")

E_ARGS = "E_PNAD_ARGS"
E_NO_ROOT = "E_PNAD_NO_ROOT"

STATE_OK = PNAC.STATE_OK
STATE_REFUSED = PNAC.STATE_REFUSED

COVERED = PNAC.COVERED
MISSING_SEAM = PNAC.MISSING_SEAM
OUT_OF_SCOPE = PNAC.OUT_OF_SCOPE
UNREADABLE = PNAC.UNREADABLE
HISTORICAL = PNAC.HISTORICAL

SEAMS_ELIF_WITH_WHILE_MATCH_COVERED = "SEAMS-WHILE-MATCH-WALRUS-COVERED"
SEAMS_ELIF_WITH_WHILE_MATCH_STALE = "SEAMS-WHILE-MATCH-WALRUS-STALE"

_BASE_PNAC_ENTRY = PNAC.module_alias_entry
_BASE_PNAC_REPORT = PNAC.module_alias_report
_BASE_PNAC_AUDIT = PNAC.audit
_BASE_PNAC_BINDINGS = PNAC.branch_bindings


class ModuleAliasWalrusWhileMatchError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _case_label(index):
    """Name the case a binding was read in: `case`, then `case2`, `case3`...

    A single case is named `case`; two or more cases that bind the same name
    must still name BOTH of them on the ambiguous reason, so the ordinal is
    spelled out rather than deduplicated away.
    """
    return "case" if index == 0 else "case%d" % (index + 1)


def branch_bindings(tree, name):
    """[(value, branch)] for every module-level branch that binds `name`.

    Same answer as the R2588 table for `if` chains, `with` bodies and `try`
    sections, with module-level `while` bodies and `match` case bodies added.
    A `for` body, a `while` else and a branch nested inside another branch's
    body are NOT descended into, which is the shipped refusal kept.
    """
    found = list(_BASE_PNAC_BINDINGS(tree, name))
    if tree is None:
        return found
    for node in tree.body:
        if isinstance(node, ast.While):
            for bound, value in PNAB._walrus_in_body(node.body):
                if bound == name:
                    found.append((value, "while"))
        elif isinstance(node, ast.Match):
            for index, case in enumerate(node.cases):
                for bound, value in PNAB._walrus_in_body(case.body):
                    if bound == name:
                        found.append((value, _case_label(index)))
    return found


@contextlib.contextmanager
def extended_branch_bindings():
    """Install this face own branch table as the LAST one applied.

    The R2588 readers install their OWN table into the R2587 module globals for
    the duration of every call, so swapping only `PNAB._branch_bindings` gets
    SHADOWED by the parent context and this face answer never reaches the row.
    That was measured here before it was repaired: both the while and the case
    fixture still read the shipped refusal. The table is therefore installed on
    BOTH names the two parents resolve at run time - the R2587 module global and
    the R2588 function its own context manager copies from - and both are
    restored in a finally.
    """
    saved_pnab = PNAB._branch_bindings
    saved_pnac = PNAC.branch_bindings
    PNAB._branch_bindings = branch_bindings
    PNAC.branch_bindings = branch_bindings
    try:
        yield
    finally:
        PNAB._branch_bindings = saved_pnab
        PNAC.branch_bindings = saved_pnac


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The R2588 answer, re-read with while and case bindings."""
    parent = _BASE_PNAC_ENTRY(name, text, scope, line, tables, root, src_path)
    with extended_branch_bindings():
        got = _BASE_PNAC_ENTRY(name, text, scope, line, tables, root,
                               src_path)
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out["base_pnad_state"] = parent.get("state")
    out["base_pnad_value"] = parent.get("value")
    out["base_pnad_reason"] = parent.get("reason")
    out["base_pnad_chain"] = parent.get("ma_chain")
    out["base_pnad_branch_reads"] = parent.get("branch_reads")
    return out


def module_alias_report(text, root=None, src_path=None):
    """One row per loop, read through the extended branch table."""
    with extended_branch_bindings():
        return _BASE_PNAC_REPORT(text, root, src_path)


def audit(root=None, module=None):
    """The R2588 module-alias audit, re-read with while and case bindings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasWalrusWhileMatchError(E_NO_ROOT,
                                               "not a directory: %s"
                                               % root_path)
    with extended_branch_bindings():
        try:
            report = _BASE_PNAC_AUDIT(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasWalrusWhileMatchError(
                code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAC.LABEL
    report["verdict"] = (
        SEAMS_ELIF_WITH_WHILE_MATCH_STALE
        if report.get("verdict") == PNAC.SEAMS_ELIF_WITH_STALE
        else SEAMS_ELIF_WITH_WHILE_MATCH_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasWalrusWhileMatchError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_ELIF_WITH_WHILE_MATCH_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_ELIF_WITH_WHILE_MATCH_COVERED:
        raise ModuleAliasWalrusWhileMatchError(report["verdict"],
                                               "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias head bound by a walrus inside a "
                    "module-level while or match case body")
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
    return 0 if report["verdict"] == SEAMS_ELIF_WITH_WHILE_MATCH_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())