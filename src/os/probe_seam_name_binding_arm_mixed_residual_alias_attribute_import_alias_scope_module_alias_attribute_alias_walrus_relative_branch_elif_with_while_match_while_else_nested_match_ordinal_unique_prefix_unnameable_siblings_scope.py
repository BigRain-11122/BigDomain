"""Prefix ack whose strict-prefix word carries EVERY sibling (R2682).

The R2679 face (PNAJ) withheld the covered word whenever a label was
unnameable, but its strict-prefix word named only the FIRST sibling:
measured at R2682 BEFORE any byte here was written,
`ack_unnameable(['a','ab','ac','ad'])` answered `{'a':
'strict-prefix-of:ab'}`, so a caller could not tell how many bindings
outranked the label from the word alone.

This face keeps every answer PNAJ published byte for byte and makes the
strict-prefix word carry EVERY sibling that makes the label unnameable, in
published order:

  * `strict_prefix_siblings(label, labels)` - every distinct OTHER label
    `label` is a strict prefix of, in published order;
  * `strict_prefix_sibling(label, labels)` - the first one, byte for byte
    what R2679 published;
  * `unnameable_reason(label, labels)` - its own word,
    `strict-prefix-of:<s1>,<s2>` and/or `duplicate:<n>`, joined by `+`;
  * `ack_unnameable(labels)` - {label: reason} over the unnameable
    labels, duplicates counted rather than merged;
  * `ack_fully_named(labels)` - True only when every label is nameable;
  * `module_alias_entry(...)` - the PNAJ answer plus `ack_unnameable`,
    `ack_unnameable_labels`, `ack_fully_named`.

Verdict: a reason carrying an unnameable label earns
SEAMS-MATCH-ORDINAL-UNIQUE-PREFIX-UNNAMEABLE and NEVER the covered word.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAK1..AC-PNAK6 were pinned in state/queue/tech.md:679 at R2679
BEFORE this code existed.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_scope as PNAJ  # noqa: E402

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-while-match-while-else-nested-match-ordinal-"
         "unique-prefix-unnameable-siblings-scope")

E_ARGS = "E_PNAK_ARGS"
E_NO_ROOT = "E_PNAK_NO_ROOT"

STATE_OK = PNAJ.STATE_OK
STATE_REFUSED = PNAJ.STATE_REFUSED

COVERED = PNAJ.COVERED
MISSING_SEAM = PNAJ.MISSING_SEAM
OUT_OF_SCOPE = PNAJ.OUT_OF_SCOPE
UNREADABLE = PNAJ.UNREADABLE
HISTORICAL = PNAJ.HISTORICAL

SEAMS_UNNAMEABLE = PNAJ.SEAMS_UNNAMEABLE
SEAMS_STALE = PNAJ.SEAMS_STALE
SEAMS_COVERED = PNAJ.SEAMS_COVERED

labels_of_reason = PNAJ.labels_of_reason
ack_hits = PNAJ.ack_hits
ack_index = PNAJ.ack_index
ack_unmatched = PNAJ.ack_unmatched
prefix_free = PNAJ.prefix_free

_BASE_PNAJ_ENTRY = PNAJ.module_alias_entry
_BASE_PNAJ_REPORT = PNAJ.module_alias_report
_BASE_PNAJ_AUDIT = PNAJ.audit


class ModuleAliasUnnameableSiblingsError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def duplicate_count(label, labels):
    """How many times `label` occurs in `labels`."""
    return list(labels).count(label)


def strict_prefix_siblings(label, labels):
    """Every distinct OTHER label `label` is a strict prefix of, in order.

    Distinct rather than repeated: a sibling published twice is one label
    whose multiplicity the duplicate word already carries, so the sibling
    list answers "which labels outrank me", not "how often".
    """
    out = []
    for other in labels:
        if other != label and other.startswith(label) and other not in out:
            out.append(other)
    return out


def strict_prefix_sibling(label, labels):
    """The first OTHER label `label` is a strict prefix of, else None."""
    siblings = strict_prefix_siblings(label, labels)
    return siblings[0] if siblings else None


def unnameable_reason(label, labels):
    """Its own word when no prefix can name it, else None.

    The strict-prefix word names EVERY sibling, in published order, so a
    caller can count the bindings that outrank the label; a single sibling
    keeps exactly the word R2679 published.
    """
    parts = []
    siblings = strict_prefix_siblings(label, labels)
    if siblings:
        parts.append("strict-prefix-of:%s" % ",".join(siblings))
    count = duplicate_count(label, labels)
    if count > 1:
        parts.append("duplicate:%d" % count)
    return "+".join(parts) if parts else None


def ack_unnameable(labels):
    """{label: reason} over the labels no prefix can name, duplicates kept."""
    out = {}
    for label in sorted(set(labels)):
        reason = unnameable_reason(label, labels)
        if reason:
            out[label] = reason
    return out


def ack_unnameable_labels(labels):
    """The sorted labels no prefix can name."""
    return sorted(ack_unnameable(labels))


def ack_fully_named(labels):
    """True only when every published label is nameable by some prefix."""
    return not ack_unnameable(labels)


def _unnameable_block(labels):
    """The unnameable reading of one reason, derived not typed."""
    reasons = ack_unnameable(labels)
    return {"ack_unnameable": reasons,
            "ack_unnameable_labels": sorted(reasons),
            "ack_fully_named": not reasons}


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The PNAJ answer, plus whether every one of its labels is nameable."""
    got = _BASE_PNAJ_ENTRY(name, text, scope, line, tables, root, src_path)
    out = dict(got)
    out.update(_unnameable_block(labels_of_reason(got.get("reason"))))
    return out


def siblings_entry(name, text, scope, line, tables=None, root=None,
                   src_path=None):
    """Alias that names the product this face adds."""
    return module_alias_entry(name, text, scope, line, tables, root, src_path)


def module_alias_report(text, root=None, src_path=None):
    """The PNAJ report, carried unchanged: no reason is republished here."""
    return _BASE_PNAJ_REPORT(text, root, src_path)


def _collect_reasons(report):
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict):
            reason = probe.get("reason")
            if reason:
                reasons.append(reason)
    return reasons


def siblings_summary(report):
    """One unnameable reading across every reason an audit published."""
    collected = _collect_reasons(report)
    labels = []
    for reason in collected:
        labels.extend(labels_of_reason(reason))
    return {"reasons": len(collected),
            "labels": sorted(set(labels)),
            "unnameable": ack_unnameable(labels),
            "fully_named": ack_fully_named(labels)}


def verdict_of(base_verdict, ack, unnameable_block):
    """The one place a covered word can be withheld.

    A reason carrying any unnameable label NEVER earns the covered word, no
    matter what the published prefixes look like; that is the whole point of
    this family and it is asserted directly rather than inferred from a tree.
    """
    if base_verdict == SEAMS_STALE:
        return SEAMS_STALE
    if unnameable_block.get("ack_unnameable"):
        return SEAMS_UNNAMEABLE
    if not ack.get("prefix_free", True):
        return SEAMS_STALE
    return SEAMS_COVERED


def audit(root=None, module=None):
    """The PNAJ audit plus an unnameable reading of the reasons it names."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasUnnameableSiblingsError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = _BASE_PNAJ_AUDIT(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasUnnameableSiblingsError(
            code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAJ.LABEL
    report["unnameable"] = siblings_summary(report)
    report["verdict"] = verdict_of(report.get("verdict"),
                                   report.get("ack") or {},
                                   {"ack_unnameable":
                                    report["unnameable"]["unnameable"]})
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasUnnameableSiblingsError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_STALE, "seams": [], "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "unnameable": {"reasons": 0, "labels": [],
                               "unnameable": {}, "fully_named": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="unnameable-label sibling-list ack face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        got = audit(args.root, args.module)
    except ModuleAliasUnnameableSiblingsError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc.detail))
        return 4 if exc.code == E_ARGS else 5
    if args.json:
        print(json.dumps(got, indent=2, sort_keys=True))
    else:
        print("%s verdict=%s" % (got["tool"], got["verdict"]))
        print("labels=%d fully_named=%s unnameable=%s"
              % (len(got["unnameable"]["labels"]),
                 got["unnameable"]["fully_named"],
                 json.dumps(got["unnameable"]["unnameable"],
                            sort_keys=True)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
