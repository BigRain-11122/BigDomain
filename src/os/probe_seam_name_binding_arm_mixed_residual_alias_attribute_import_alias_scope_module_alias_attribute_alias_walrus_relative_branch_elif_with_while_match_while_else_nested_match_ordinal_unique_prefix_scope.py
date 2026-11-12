"""Prefix-free ACK index for a reason that names several bindings.

The shipped unique-ordinal face (R2675) made the LABELS distinct, but it did
not make them tellable apart by a PREFIX: on the three-binding fixture the
reason carries `while>case`, `while2>case` and `while2_body>case`, so a caller
that acked a binding with the prefix `while2` matched TWO labels (the first
while own second match and the second while own first match) and `while`
matched all three. Distinct labels are not the same thing as an unambiguous
ack, and the gap was measured, not guessed.

This face keeps every label byte for byte (that is what the five parents
pinned) and publishes the missing reading beside them: for each label in a
reason, the SHORTEST prefix of that label that matches exactly one label in
the SAME reason. Those published prefixes are prefix-free among themselves by
construction, so an ack token has exactly one meaning inside one reason.

  * `ack_prefix(label, labels)` - the shortest unique prefix, or None when the
    label itself occurs more than once (no prefix can ever be unique then);
  * `ack_index(labels)` - {label: prefix} over the labels of one reason;
  * `ack_hits(prefix, labels)` - the labels a prefix actually names;
  * `module_alias_entry(...)` - the R2675 answer plus `ack_labels`,
    `ack_prefixes`, `ack_unmatched`, `ack_prefix_free`, `ack_hits`.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAH1..AC-PNAH6 were pinned in state/queue/tech.md:677 at R2675
BEFORE this code existed.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_scope as PNAG  # noqa: E402

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-while-match-while-else-nested-match-ordinal-"
         "unique-prefix-scope")

E_ARGS = "E_PNAI_ARGS"
E_NO_ROOT = "E_PNAI_NO_ROOT"

STATE_OK = PNAG.STATE_OK
STATE_REFUSED = PNAG.STATE_REFUSED

COVERED = PNAG.COVERED
MISSING_SEAM = PNAG.MISSING_SEAM
OUT_OF_SCOPE = PNAG.OUT_OF_SCOPE
UNREADABLE = PNAG.UNREADABLE
HISTORICAL = PNAG.HISTORICAL

SEAMS_PREFIX_COVERED = "SEAMS-MATCH-ORDINAL-UNIQUE-PREFIX-COVERED"
SEAMS_PREFIX_STALE = "SEAMS-MATCH-ORDINAL-UNIQUE-PREFIX-STALE"

_BASE_PNAG_ENTRY = PNAG.module_alias_entry
_BASE_PNAG_REPORT = PNAG.module_alias_report
_BASE_PNAG_AUDIT = PNAG.audit


class ModuleAliasMatchOrdinalPrefixError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def labels_of_reason(reason):
    """The labels a reason publishes, read the way a caller reads them.

    Same shape the shipped suites use: everything after the first `@`, split
    on `+`, empty pieces dropped. A reason with no `@` carries no labels.
    """
    if not isinstance(reason, str) or "@" not in reason:
        return []
    tail = reason.split("@", 1)[1]
    return [item for item in tail.split("+") if item]


def ack_hits(prefix, labels):
    """The labels in `labels` that `prefix` names, in their published order."""
    if not prefix:
        return []
    return [label for label in labels if label.startswith(prefix)]


def ack_prefix(label, labels):
    """The shortest prefix of `label` that names exactly one label, else None.

    None is returned when `label` itself occurs more than once in `labels`:
    no prefix can distinguish two copies of the same string, so the honest
    answer is "there is no such prefix" rather than the whole label.
    """
    if labels.count(label) != 1:
        return None
    for size in range(1, len(label) + 1):
        prefix = label[:size]
        if len(ack_hits(prefix, labels)) == 1:
            return prefix
    return None


def ack_index(labels):
    """{label: shortest unique prefix} for one reason, deterministic order."""
    out = {}
    for label in sorted(set(labels)):
        out[label] = ack_prefix(label, labels)
    return out


def ack_unmatched(labels):
    """The labels no prefix can name (present once each but not separable)."""
    return [label for label, prefix in ack_index(labels).items()
            if prefix is None]


def prefix_free(index):
    """True when no published prefix is a prefix of another published one."""
    published = [value for value in index.values() if value]
    values = sorted(set(published))
    if len(published) != len(values):
        return False
    for left in values:
        for right in values:
            if left != right and right.startswith(left):
                return False
    return True


def _ack_block(got):
    """The ack reading of one entry answer, derived not typed."""
    labels = labels_of_reason(got.get("reason"))
    index = ack_index(labels)
    return {"ack_labels": sorted(set(labels)),
            "ack_prefixes": index,
            "ack_unmatched": ack_unmatched(labels),
            "ack_prefix_free": prefix_free(index),
            "ack_hits": dict((prefix, ack_hits(prefix, labels))
                             for prefix in sorted(
                                 set(value for value in index.values()
                                     if value)))}


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The R2675 answer, plus a prefix-free ack index for its own reason."""
    got = _BASE_PNAG_ENTRY(name, text, scope, line, tables, root, src_path)
    out = dict(got)
    out.update(_ack_block(got))
    return out


def ack_entry(name, text, scope, line, tables=None, root=None, src_path=None):
    """Alias that names the product this face adds."""
    return module_alias_entry(name, text, scope, line, tables, root, src_path)


def module_alias_report(text, root=None, src_path=None):
    """The R2675 report, carried unchanged: no reason is republished here."""
    return _BASE_PNAG_REPORT(text, root, src_path)


def _collect_reasons(report):
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict):
            reason = probe.get("reason")
            if reason:
                reasons.append(reason)
    return reasons


def ack_summary(report):
    """One prefix-free reading across every reason an audit published."""
    labels = []
    for reason in _collect_reasons(report):
        labels.extend(labels_of_reason(reason))
    index = ack_index(labels)
    return {"reasons": len(_collect_reasons(report)),
            "labels": sorted(set(labels)),
            "prefixes": index,
            "unmatched": ack_unmatched(labels),
            "prefix_free": prefix_free(index)}


def audit(root=None, module=None):
    """The R2675 audit plus a prefix-free ack summary of the reasons it names."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasMatchOrdinalPrefixError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = _BASE_PNAG_AUDIT(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasMatchOrdinalPrefixError(
            code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAG.LABEL
    report["ack"] = ack_summary(report)
    report["verdict"] = (
        SEAMS_PREFIX_STALE
        if report.get("verdict") == PNAG.SEAMS_MATCH_ORDINAL_UNIQUE_STALE
        or not report["ack"]["prefix_free"]
        else SEAMS_PREFIX_COVERED)
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasMatchOrdinalPrefixError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_PREFIX_STALE, "seams": [],
                "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "ack": {"reasons": 0, "labels": [], "prefixes": {},
                        "unmatched": [], "prefix_free": True},
                "refusal": exc.code, "detail": exc.detail}


def guard(root=None, module=None):
    """Ask the reading and raise when the ack index is not prefix-free."""
    report = audit(root, module)
    if report["verdict"] != SEAMS_PREFIX_COVERED:
        raise ModuleAliasMatchOrdinalPrefixError(
            report["verdict"], "the ack index is not prefix-free")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=LABEL,
        description="publish a prefix-free ack index for reasons that name "
                    "several bindings")
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
        sys.stdout.write("%s verdict=%s base=%s ack_labels=%d "
                         "ack_prefix_free=%s\n"
                         % (LABEL, report["verdict"],
                            report.get("base_tool", "?"),
                            len(report["ack"]["labels"]),
                            report["ack"]["prefix_free"]))
        for name in sorted(report["counts"]):
            sys.stdout.write("  %s=%s\n" % (name, report["counts"][name]))
        for label in report["ack"]["labels"]:
            sys.stdout.write("  ack %s <- %s\n"
                             % (label, report["ack"]["prefixes"].get(label)))
    if report.get("refusal"):
        return 2
    return 0 if report["verdict"] == SEAMS_PREFIX_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())
