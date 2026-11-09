"""A module alias HEAD bound by a WALRUS in a `while` ELSE or a nested `match`.

The shipped while/match face (R2590) follows a walrus bound in a module-level
`while` body and in a module-level `match` `case` body, and names the branch it
was read in. It stops there: a `while` `else` section is not descended into, a
`match` nested one level inside a `while` body is invisible to it, and two
`while` bodies that bind one name are refused with the while named only ONCE
because the label has no ordinal. Four shapes were measured at R2590 with
src/os/limits_module_alias_walrus_while_match_next_R2590.py against private
worlds and re-measured here BEFORE any code with
src/os/limits_module_alias_walrus_while_else_nested_R2592.py:

  (a) a WALRUS inside a `while` `else` section reads the shipped refusal;
  (b) two `while` bodies binding one name read `attr-module-alias-ambiguous:M@while`
      - the reason names the while once, so a reader cannot tell which two;
  (c) a lone `match` nested one level inside a `while` body reads the shipped
      refusal instead of resolving its single case;
  (d) a `with` body nested in a `while`, a branch nested two deep in a `while`
      and a `for` body keep the shipped refusal - and those stay refused.

The extension is applied THROUGH the shipped reading rather than beside it: the
branch table the R2590 context manager resolves at run time is swapped for this
face own inside one guarded block and restored in a finally, so every answer
the twenty-one shipped faces already gave is carried unchanged on the row.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAE1..AC-PNAE6 were pinned in state/queue/tech.md:625 at R2590
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_scope as PNAD  # noqa: E402

PNAB = PNAD.PNAB

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-while-match-while-else-nested-scope")

E_ARGS = "E_PNAE_ARGS"
E_NO_ROOT = "E_PNAE_NO_ROOT"

STATE_OK = PNAD.STATE_OK
STATE_REFUSED = PNAD.STATE_REFUSED

COVERED = PNAD.COVERED
MISSING_SEAM = PNAD.MISSING_SEAM
OUT_OF_SCOPE = PNAD.OUT_OF_SCOPE
UNREADABLE = PNAD.UNREADABLE
HISTORICAL = PNAD.HISTORICAL

SEAMS_WHILE_ELSE_NESTED_COVERED = "SEAMS-WHILE-ELSE-NESTED-WALRUS-COVERED"
SEAMS_WHILE_ELSE_NESTED_STALE = "SEAMS-WHILE-ELSE-NESTED-WALRUS-STALE"

_BASE_PNAD_ENTRY = PNAD.module_alias_entry
_BASE_PNAD_REPORT = PNAD.module_alias_report
_BASE_PNAD_AUDIT = PNAD.audit
_BASE_PNAD_BINDINGS = PNAD.branch_bindings


class ModuleAliasWalrusWhileElseNestedError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _while_label(index):
    """Name a module-level while by its POSITION: `while`, `while2`, ..."""
    return "while" if index == 0 else "while%d" % (index + 1)


def _case_label(index):
    """Name a case by its position: `case`, `case2`, ..."""
    return "case" if index == 0 else "case%d" % (index + 1)


def branch_bindings(tree, name):
    """[(value, branch)] for every module-level branch that binds `name`.

    Same answer as the R2590 table for `if` chains, `with` bodies, `try`
    sections, module-level `while` bodies and module-level `match` cases, with
    the `while` `else` sections and a `match` nested one level inside a `while`
    body added. Two `while` bodies now carry an ORDINAL so an ambiguous reason
    can name both. A `for` body, a `with` body nested in a `while` and a branch
    nested two deep are NOT descended into, which is the shipped refusal kept.
    """
    found = [(value, label) for value, label in
             _BASE_PNAD_BINDINGS(tree, name) if label != "while"]
    if tree is None:
        return found
    index = 0
    for node in tree.body:
        if not isinstance(node, ast.While):
            continue
        label = _while_label(index)
        index += 1
        for bound, value in PNAB._walrus_in_body(node.body):
            if bound == name:
                found.append((value, label))
        for bound, value in PNAB._walrus_in_body(node.orelse):
            if bound == name:
                found.append((value, label + "_else"))
        for inner in node.body:
            if not isinstance(inner, ast.Match):
                continue
            for position, case in enumerate(inner.cases):
                case_label = "%s>%s" % (label, _case_label(position))
                for bound, value in PNAB._walrus_in_body(case.body):
                    if bound == name:
                        found.append((value, case_label))
    return found


@contextlib.contextmanager
def extended_branch_bindings():
    """Install this face own branch table as the LAST one applied.

    The R2590 context manager resolves the name it installs from its OWN module
    globals at call time, so patching that one name is enough to carry this
    table through the whole parent chain. It is restored in a finally.
    """
    saved = PNAD.branch_bindings
    PNAD.branch_bindings = branch_bindings
    try:
        yield
    finally:
        PNAD.branch_bindings = saved


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The R2590 answer, re-read with while-else and nested case bindings."""
    parent = _BASE_PNAD_ENTRY(name, text, scope, line, tables, root, src_path)
    with extended_branch_bindings():
        got = _BASE_PNAD_ENTRY(name, text, scope, line, tables, root,
                               src_path)
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out["base_pnae_state"] = parent.get("state")
    out["base_pnae_value"] = parent.get("value")
    out["base_pnae_reason"] = parent.get("reason")
    out["base_pnae_chain"] = parent.get("ma_chain")
    out["base_pnae_branch_reads"] = parent.get("branch_reads")
    return out


def module_alias_report(text, root=None, src_path=None):
    """One row per loop, read through the extended branch table."""
    with extended_branch_bindings():
        return _BASE_PNAD_REPORT(text, root, src_path)


def audit(root=None, module=None):
    """The R2590 module-alias audit, re-read with while-else and nested cases."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasWalrusWhileElseNestedError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    with extended_branch_bindings():
        try:
            report = _BASE_PNAD_AUDIT(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasWalrusWhileElseNestedError(
                code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAD.LABEL
    report["verdict"] = (
        SEAMS_WHILE_ELSE_NESTED_STALE
        if report.get("verdict") == PNAD.SEAMS_ELIF_WITH_WHILE_MATCH_STALE
        else SEAMS_WHILE_ELSE_NESTED_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasWalrusWhileElseNestedError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_WHILE_ELSE_NESTED_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_WHILE_ELSE_NESTED_COVERED:
        raise ModuleAliasWalrusWhileElseNestedError(report["verdict"],
                                                    "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias head bound by a walrus inside a "
                    "module-level while else section or a match nested in a "
                    "while body")
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
    return 0 if report["verdict"] == SEAMS_WHILE_ELSE_NESTED_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())