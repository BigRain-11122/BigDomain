"""A module alias HEAD bound by a WALRUS under an ordinal unique ACROSS whiles.

The shipped match-ordinal face (R2594) gave each lone `match` nested one level
inside a `while` body its OWN ordinal, but the ordinal was per-while: the first
while shared the label space with the shipped while names (`while`, `while2`),
so a second while own single match claimed `while2` as well. Three shapes were
re-measured at R2675 with src/os/limits_module_alias_match_ordinal_unique_R2675.py
against private worlds BEFORE this module existed:

  (a) one while with TWO matches plus a SECOND while with one match carries
      THREE bindings and named only TWO labels (`while2>case`, `while>case`),
      so a reader cannot tell which binding was which;
  (b) two matches inside ONE `while` `else` section name both, but the second
      reads the join artifact `while_elsem2>case` instead of `while_else2`;
  (c) a `match` inside a `for` body nested in a `while`, a `match` nested one
      level in a `while` inside another `while`, and an `if` nested inside a
      `match` case keep the shipped `attr-module-alias-unbound:M.HW` refusal
      with NO branch read published - and those three stay refused here.

The extension is applied THROUGH the shipped reading rather than beside it: the
branch table the R2594 context manager resolves from its own module globals at
call time is swapped for this face own inside one guarded block and restored in
a finally, so every answer the shipped faces already gave is carried unchanged
on the row - and this face publishes the answer of EACH of the five parents it
chains through, not only its immediate one.

Label law (the whole point of this face):
  * the FIRST while keeps the shipped ordinal labels for its body matches
    (`while>case`, `while2>case`, `while3>case`, ...) because R2594 pinned
    exactly those;
  * every LATER while names its body matches with its own prefix and `_body`
    (`while2_body>case`, `while2_body2>case`), so a second while can never
    claim a label the first while already used;
  * a `while` `else` section names its matches `<while>_else`,
    `<while>_else2`, ... (`while_else>case`, `while_else2>case`), never the
    old join artifact;
  * a direct walrus in a while body or else section keeps the shipped while
    label (`while`, `while2`, `while_else`).

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAG1..AC-PNAG6 were pinned in state/queue/tech.md:676 at R2594
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_scope as PNAF  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_scope as PNAE  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_scope as PNAD  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope as PNAB  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa: E402

PNAB_HELPERS = PNAF.PNAB

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-while-match-while-else-nested-match-ordinal-"
         "unique-scope")

E_ARGS = "E_PNAG_ARGS"
E_NO_ROOT = "E_PNAG_NO_ROOT"

STATE_OK = PNAF.STATE_OK
STATE_REFUSED = PNAF.STATE_REFUSED

COVERED = PNAF.COVERED
MISSING_SEAM = PNAF.MISSING_SEAM
OUT_OF_SCOPE = PNAF.OUT_OF_SCOPE
UNREADABLE = PNAF.UNREADABLE
HISTORICAL = PNAF.HISTORICAL

SEAMS_MATCH_ORDINAL_UNIQUE_COVERED = "SEAMS-MATCH-ORDINAL-UNIQUE-WALRUS-COVERED"
SEAMS_MATCH_ORDINAL_UNIQUE_STALE = "SEAMS-MATCH-ORDINAL-UNIQUE-WALRUS-STALE"

# The five parents AC-PNAG4 names, in the order the seed row names them.
PARENTS = [("r2585", PNT), ("r2588", PNAB), ("r2590", PNAD), ("r2592", PNAE),
           ("r2594", PNAF)]

_BASE_PNAF_ENTRY = PNAF.module_alias_entry
_BASE_PNAF_REPORT = PNAF.module_alias_report
_BASE_PNAF_AUDIT = PNAF.audit
_BASE_PNAF_BINDINGS = PNAF.branch_bindings


class ModuleAliasWalrusMatchOrdinalUniqueError(Exception):
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


def _body_match_label(while_index, match_index):
    """Name a lone body match so no label can be claimed twice.

    The FIRST while keeps the shipped ordinal labels (`while`, `while2`, ...)
    because R2594 pinned them; every later while keeps its own prefix plus
    `_body`, so a second while can never collide with the first while own
    second match.
    """
    if while_index == 0:
        return _while_label(match_index)
    base = _while_label(while_index) + "_body"
    if match_index == 0:
        return base
    return "%s%d" % (base, match_index + 1)


def _else_match_label(while_index, match_index):
    base = _while_label(while_index) + "_else"
    if match_index == 0:
        return base
    return "%s%d" % (base, match_index + 1)


def branch_bindings(tree, name):
    """[(value, branch)] for every module-level branch that binds `name`.

    Same answer as the R2594 table for `if` chains, `with` bodies, `try`
    sections, module-level `while` bodies and `while` `else` sections, with the
    match ordinals made unique ACROSS matches and whiles. A `for` body, a
    `while` nested in a `while` and an `if` nested inside a `match` case are
    NOT descended into, which is the shipped refusal kept.
    """
    found = [(value, label) for value, label in
             _BASE_PNAF_BINDINGS(tree, name)
             if not label.startswith("while")]
    if tree is None:
        return found
    index = 0
    for node in tree.body:
        if not isinstance(node, ast.While):
            continue
        label = _while_label(index)
        for bound, value in PNAB_HELPERS._walrus_in_body(node.body):
            if bound == name:
                found.append((value, label))
        for bound, value in PNAB_HELPERS._walrus_in_body(node.orelse):
            if bound == name:
                found.append((value, label + "_else"))
        match_index = 0
        for inner in node.body:
            if not isinstance(inner, ast.Match):
                continue
            match_label = _body_match_label(index, match_index)
            match_index += 1
            for position, case in enumerate(inner.cases):
                case_label = "%s>%s" % (match_label, _case_label(position))
                for bound, value in PNAB_HELPERS._walrus_in_body(case.body):
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
                for bound, value in PNAB_HELPERS._walrus_in_body(case.body):
                    if bound == name:
                        found.append((value, case_label))
        index += 1
    return found


@contextlib.contextmanager
def extended_branch_bindings():
    """Install this face own branch table as the LAST one applied.

    The R2594 context manager resolves the name it installs from its OWN module
    globals at call time, so patching that one name is enough to carry this
    table through the whole parent chain. It is restored in a finally.
    """
    saved = PNAF.branch_bindings
    PNAF.branch_bindings = branch_bindings
    try:
        yield
    finally:
        PNAF.branch_bindings = saved


def _parent_answers(name, text, scope, line, tables, root, src_path):
    """Ask EACH of the five parents the same question, unpatched."""
    out = {}
    for tag, module in PARENTS:
        got = module.module_alias_entry(name, text, scope, line, tables, root,
                                        src_path)
        out["base_pnag_%s_state" % tag] = got.get("state")
        out["base_pnag_%s_value" % tag] = got.get("value")
        out["base_pnag_%s_reason" % tag] = got.get("reason")
    return out


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The R2594 answer, re-read with ordinals unique across matches/whiles."""
    with extended_branch_bindings():
        got = _BASE_PNAF_ENTRY(name, text, scope, line, tables, root,
                               src_path)
    out = dict(got)
    for key in sorted(got):
        out.setdefault(key, got[key])
    out.update(_parent_answers(name, text, scope, line, tables, root,
                               src_path))
    # The R2594 parent answer is asked ONCE, through _parent_answers, rather
    # than twice: every extra entry on this chain costs a full parent walk.
    out["base_pnag_state"] = out["base_pnag_r2594_state"]
    out["base_pnag_value"] = out["base_pnag_r2594_value"]
    out["base_pnag_reason"] = out["base_pnag_r2594_reason"]
    out["base_pnag_chain"] = None
    out["base_pnag_branch_reads"] = None
    return out


def module_alias_report(text, root=None, src_path=None):
    """One row per loop, read through the unique-ordinal branch table."""
    with extended_branch_bindings():
        return _BASE_PNAF_REPORT(text, root, src_path)


def audit(root=None, module=None):
    """The R2594 module-alias audit, re-read with unique ordinals."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasWalrusMatchOrdinalUniqueError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    with extended_branch_bindings():
        try:
            report = _BASE_PNAF_AUDIT(root_path, module)
        except Exception as exc:
            code = getattr(exc, "code", None)
            if not code:
                raise
            raise ModuleAliasWalrusMatchOrdinalUniqueError(
                code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAF.LABEL
    report["verdict"] = (
        SEAMS_MATCH_ORDINAL_UNIQUE_STALE
        if report.get("verdict") == PNAF.SEAMS_MATCH_ORDINAL_STALE
        else SEAMS_MATCH_ORDINAL_UNIQUE_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasWalrusMatchOrdinalUniqueError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_MATCH_ORDINAL_UNIQUE_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when a probe has fallen behind the render."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_MATCH_ORDINAL_UNIQUE_COVERED:
        raise ModuleAliasWalrusMatchOrdinalUniqueError(
            report["verdict"], "probe seams are stale")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="follow a module alias head bound by a walrus under an "
                    "ordinal that is unique across matches and whiles")
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
    return 0 if report["verdict"] == SEAMS_MATCH_ORDINAL_UNIQUE_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())
