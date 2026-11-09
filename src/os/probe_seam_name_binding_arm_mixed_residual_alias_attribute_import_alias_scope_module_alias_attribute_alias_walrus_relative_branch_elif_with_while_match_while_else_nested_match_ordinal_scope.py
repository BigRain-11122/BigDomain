"""A module alias HEAD bound by a WALRUS in a nested `match` with an ORDINAL.

The shipped while-else/nested-case face (R2592) follows a walrus bound in a
module-level `while` `else` section and in ONE `match` nested one level inside
a `while` body. It stops there: two lone `match` statements inside ONE `while`
body collide on the label `while>case` (the label carries no ordinal across
matches), and a `match` inside a `while` `else` section is not descended into
at all. Four shapes were measured at R2592 with
src/os/limits_module_alias_walrus_while_else_nested_next_R2592.py against
private worlds:

  (a) two lone `match` statements in ONE `while` body read
      `attr-module-alias-ambiguous:M@while>case` - the case is named ONCE, so
      a reader cannot tell which two matches were seen;
  (b) a `match` inside a `while` `else` section reads the shipped refusal
      `attr-module-alias-unbound:M.HW` with no branch read published;
  (c) a `for` body and a `for` `else` section keep the shipped refusal;
  (d) a `match` nested TWO levels inside a `while` body keeps the shipped
      refusal - and that stays refused rather than guessed at.

The extension is applied THROUGH the shipped reading rather than beside it: the
branch table the R2592 context manager resolves from its own module globals at
call time is swapped for this face own inside one guarded block and restored in
a finally, so every answer the twenty-two shipped faces already gave is carried
unchanged on the row.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAF1..AC-PNAF6 were pinned in state/queue/tech.md:627 at R2592
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_scope as PNAE  # noqa: E402

PNAB = PNAE.PNAB

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-while-match-while-else-nested-match-ordinal-scope")

E_ARGS = "E_PNAF_ARGS"
E_NO_ROOT = "E_PNAF_NO_ROOT"

STATE_OK = PNAE.STATE_OK
STATE_REFUSED = PNAE.STATE_REFUSED

COVERED = PNAE.COVERED
MISSING_SEAM = PNAE.MISSING_SEAM
OUT_OF_SCOPE = PNAE.OUT_OF_SCOPE
UNREADABLE = PNAE.UNREADABLE
HISTORICAL = PNAE.HISTORICAL

SEAMS_MATCH_ORDINAL_COVERED = "SEAMS-MATCH-ORDINAL-WALRUS-COVERED"
SEAMS_MATCH_ORDINAL_STALE = "SEAMS-MATCH-ORDINAL-WALRUS-STALE"

_BASE_PNAE_ENTRY = PNAE.module_alias_entry
_BASE_PNAE_REPORT = PNAE.module_alias_report
_BASE_PNAE_AUDIT = PNAE.audit
_BASE_PNAE_BINDINGS = PNAE.branch_bindings


class ModuleAliasWalrusMatchOrdinalError(Exception):
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


def _match_label(while_index, match_index):
    """Name a lone nested `match` by its ORDINAL inside its while body.

    The first while shares the label space with the shipped while names, so two
    matches in it read `while` and `while2` - the exact labels the pinned
    criterion AC-PNAF1 names. Later whiles keep their own prefix so a second
    while body can never collide with the first one own second match.
    """
    if while_index == 0:
        return _while_label(match_index)
    base = _while_label(while_index)
    if match_index == 0:
        return base
    return "%sm%d" % (base, match_index + 1)


def _else_match_label(while_index, match_index):
    base = _while_label(while_index) + "_else"
    if match_index == 0:
        return base
    return "%sm%d" % (base, match_index + 1)


def branch_bindings(tree, name):
    """[(value, branch)] for every module-level branch that binds `name`.

    Same answer as the R2592 table for `if` chains, `with` bodies, `try`
    sections, module-level `while` bodies and `while` `else` sections, with two
    additions: each lone `match` nested one level inside a `while` body carries
    its OWN ordinal so two matches are named separately, and a `match` nested in
    a `while` `else` section is followed and named `while_else>case`. A `for`
    body, a `for` `else` section, a `with` body nested in a `while` and a
    branch nested two deep are NOT descended into, which is the shipped refusal
    kept; a `match` nested two levels deep stays refused on purpose.
    """
    found = [(value, label) for value, label in
             _BASE_PNAE_BINDINGS(tree, name)
             if not label.startswith("while")]
    if tree is None:
        return found
    index = 0
    for node in tree.body:
        if not isinstance(node, ast.While):
            continue
        label = _while_label(index)
        for bound, value in PNAB._walrus_in_body(node.body):
            if bound == name:
                found.append((value, label))
        for bound, value in PNAB._walrus_in_body(node.orelse):
            if bound == name:
                found.append((value, label + "_else"))
        match_index = 0
        for inner in node.body:
            if not isinstance(inner, ast.Match):
                continue
            match_label = _match_label(index, match_index)
            match_index += 1
            for position, case in enumerate(inner.cases):
                case_label = "%s>%s" % (match_label, _case_label(position))
                for bound, value in PNAB._walrus_in_body(case.body):
                    if bound == name:
                        found.append((value, case_label))
        match_index = 0
        for inner in node.orelse:
            if not isinstance(inner, ast.Match):
                continue
            match_label = _else_match_label(index, match_index)
            match_index += 1
            for position, case in enumerate(inner.cases):
                case_label = "%s>%s" % (match_label, _case_label(position))
                for bound, value in PNAB._walrus_in_body(case.body):
                    if bound == name:
                        found.append((value, case_label))
        index += 1
    return found


@contextlib.contextmanager
def extended_branch_bindings():
    """Install this face own branch table as the LAST one applied.

    The R2592 context manager resolves the name it installs from its OWN module
    globals at call time, so patching that one name is enough to carry this
    table through the whole parent chain. It is restored in a finally.
    """
    saved = PNAE.branch_bindings
    PNAE.branch_bindings = branch_bindings
    try:
        yield
    finally:
        PNAE.branch_bindings = saved


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The R2592 answer, re-read with per-match ordinals and else-section
    matches."""
    parent = _BASE_PNAE_ENTRY(name, text, scope, line, tables, root, src_path)
    with extended_branch_bindings():
        got = _BASE_PNAE_ENTRY(name, text, scope, line, tables, root,
                               src_path)
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out["base_pnaf_state"] = parent.get("state")
    out["base_pnaf_value"] = parent.get("value")
    out["base_pnaf_reason"] = parent.get("reason")
    out["base_pnaf_chain"] = parent.get("ma_chain")
    out["base_pnaf_branch_reads"] = parent.get("branch_reads")
    return out


def module_alias_report(text, root=None, src_path=None):
    """One row per loop, read through the extended branch table."""
    with extended_branch_bindings():
        return _BASE_PNAE_REPORT(text, root, src_path)


def audit(root=None, module=None):
    """The R2592 module-alias audit, re-read with per-match ordinals."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasWalrusMatchOrdinalError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    with extended_branch_bindings():
        try:
            report = _BASE_PNAE_AUDIT(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasWalrusMatchOrdinalError(
                code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAE.LABEL
    report["verdict"] = (
        SEAMS_MATCH_ORDINAL_STALE
        if report.get("verdict") == PNAE.SEAMS_WHILE_ELSE_NESTED_STALE
        else SEAMS_MATCH_ORDINAL_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasWalrusMatchOrdinalError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_MATCH_ORDINAL_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_MATCH_ORDINAL_COVERED:
        raise ModuleAliasWalrusMatchOrdinalError(report["verdict"],
                                                 "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias head bound by a walrus inside one "
                    "of two lone matches nested in a while body, or a match "
                    "nested in a while else section")
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
    return 0 if report["verdict"] == SEAMS_MATCH_ORDINAL_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())