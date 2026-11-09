"""A module alias HEAD bound by a WALRUS inside a module-level ELIF or WITH.

The shipped branch face (R2587) follows a walrus bound in a module-level `if`
body, its `else` body and a module-level `try` body, and names the branch it
was read in. It stops there: `elif` sections and `with` bodies are invisible to
it because its branch table lists only body/orelse/handlers, so
`if a1:` / `elif a2:` / `(M := consts)` followed by `BASE = M.HW` still reads
`attr-module-alias-unbound:M.HW`. Four shapes were measured at R2587 with
src/os/limits_module_alias_walrus_branch_next_R2587.py against private worlds
and re-measured here before any code:

  (a) a WALRUS inside a module-level `elif` branch is not read;
  (b) a WALRUS inside a module-level `with` body is not read;
  (c) a WALRUS inside a module-level `for` body is not read - and stays so;
  (d) a WALRUS inside a branch nested two levels deep is not read - and stays
      so.

The extension is applied THROUGH the shipped reading rather than beside it: the
branch table the R2587 readers call at run time is swapped for this face own
inside one guarded block and restored in a finally, so every answer the
nineteen shipped faces already gave is carried unchanged on the row. The if
chain is walked as a chain (`if` -> `elif`* -> `else`) rather than descended
into, so a branch that merely CONTAINS another branch is still refused.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAC1..AC-PNAC6 were pinned in state/queue/tech.md:621 at R2587
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope as PNAB  # noqa: E402

PNT = PNAB.PNT

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-scope")

E_ARGS = "E_PNAC_ARGS"
E_NO_ROOT = "E_PNAC_NO_ROOT"

STATE_OK = PNAB.STATE_OK
STATE_REFUSED = PNAB.STATE_REFUSED

COVERED = PNAB.COVERED
MISSING_SEAM = PNAB.MISSING_SEAM
OUT_OF_SCOPE = PNAB.OUT_OF_SCOPE
UNREADABLE = PNAB.UNREADABLE
HISTORICAL = PNAB.HISTORICAL

SEAMS_ELIF_WITH_COVERED = "SEAMS-ELIF-WITH-WALRUS-COVERED"
SEAMS_ELIF_WITH_STALE = "SEAMS-ELIF-WITH-WALRUS-STALE"

_BASE_PNAB_ENTRY = PNAB.module_alias_entry
_BASE_PNAB_REPORT = PNAB.module_alias_report
_BASE_PNAB_AUDIT = PNAB.audit
_BASE_PNAB_BINDINGS = PNAB._branch_bindings


class ModuleAliasWalrusElifWithError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def _collect_if_chain(node, name, found):
    """Walk one module-level if chain as a chain, never into a nested branch."""
    label = "if"
    current = node
    while True:
        for bound, value in PNAB._walrus_in_body(current.body):
            if bound == name:
                found.append((value, label))
        orelse = current.orelse
        if len(orelse) == 1 and isinstance(orelse[0], ast.If):
            current = orelse[0]
            label = "elif"
            continue
        for bound, value in PNAB._walrus_in_body(orelse):
            if bound == name:
                found.append((value, "else"))
        return


def branch_bindings(tree, name):
    """[(value, branch)] for every module-level branch that binds `name`.

    Same answer as the R2587 table for `if` / `else` / `try` sections, with the
    `elif` sections of the if chain and module-level `with` bodies added. A
    `for` body and a branch nested inside another branch's body are NOT
    descended into, which is the shipped refusal kept rather than changed.
    """
    found = []
    if tree is None:
        return found
    for node in tree.body:
        if isinstance(node, ast.If):
            _collect_if_chain(node, name, found)
        elif isinstance(node, ast.With):
            for bound, value in PNAB._walrus_in_body(node.body):
                if bound == name:
                    found.append((value, "with"))
        elif isinstance(node, ast.Try):
            sections = [(node.body, "try"), (node.orelse, "else"),
                        (node.finalbody, "finally")]
            for handler in node.handlers:
                sections.append((handler.body, "except"))
            for body, label in sections:
                for bound, value in PNAB._walrus_in_body(body):
                    if bound == name:
                        found.append((value, label))
    return found


@contextlib.contextmanager
def extended_branch_bindings():
    """Swap the R2587 branch table for this face own and restore it.

    The readers the parent faces call resolve their branch table in the R2587
    module globals at run time, so swapping that one name inside a guarded
    block is enough to extend every path that already goes through it.
    """
    saved = PNAB._branch_bindings
    PNAB._branch_bindings = branch_bindings
    try:
        yield
    finally:
        PNAB._branch_bindings = saved


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The R2587 answer, re-read with elif and with bindings."""
    parent = _BASE_PNAB_ENTRY(name, text, scope, line, tables, root, src_path)
    with extended_branch_bindings():
        got = _BASE_PNAB_ENTRY(name, text, scope, line, tables, root, src_path)
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out["base_pnac_state"] = parent.get("state")
    out["base_pnac_value"] = parent.get("value")
    out["base_pnac_reason"] = parent.get("reason")
    out["base_pnac_chain"] = parent.get("ma_chain")
    out["base_pnac_branch_reads"] = parent.get("branch_reads")
    return out


def module_alias_report(text, root=None, src_path=None):
    """One row per loop, read through the extended branch table."""
    with extended_branch_bindings():
        return _BASE_PNAB_REPORT(text, root, src_path)


def audit(root=None, module=None):
    """The R2587 module-alias audit, re-read with elif and with bindings."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasWalrusElifWithError(E_NO_ROOT,
                                             "not a directory: %s" % root_path)
    with extended_branch_bindings():
        try:
            report = _BASE_PNAB_AUDIT(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasWalrusElifWithError(
                code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAB.LABEL
    report["verdict"] = (SEAMS_ELIF_WITH_STALE
                         if report.get("verdict") == PNAB.SEAMS_BRANCH_STALE
                         else SEAMS_ELIF_WITH_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasWalrusElifWithError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_ELIF_WITH_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_ELIF_WITH_COVERED:
        raise ModuleAliasWalrusElifWithError(report["verdict"],
                                             "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias head bound by a walrus inside a "
                    "module-level elif or with body")
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
    return 0 if report["verdict"] == SEAMS_ELIF_WITH_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())