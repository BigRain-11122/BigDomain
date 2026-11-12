"""Prefix ack that never reads COVERED while a label is unnameable.

The R2678 face (PNAI) made the published prefixes prefix-free AMONG
THEMSELVES, but `prefix_free` only looks at the prefixes it managed to
publish. Two shapes slipped through it, both measured at R2679 BEFORE any
byte here was written:

  * ['x', 'xy'] -> ack_index {'x': None, 'xy': 'xy'}, ack_unmatched ['x'],
    prefix_free True. `x` is a STRICT PREFIX of a sibling, so no prefix of
    `x` can ever name exactly one label while `xy` exists.
  * ['a', 'a'] -> ack_index {'a': None}, ack_unmatched ['a'], prefix_free
    True on an empty prefix set. The same string published twice cannot be
    told apart by any prefix at all.

In both shapes the shipped face published ...PREFIX-COVERED, which is the
exact false green this family exists to refuse. This face keeps every answer
PNAI published byte for byte and adds the missing reading:

  * `strict_prefix_sibling(label, labels)` - the first OTHER label that
    `label` is a strict prefix of, or None;
  * `duplicate_count(label, labels)` - how many times `label` occurs;
  * `unnameable_reason(label, labels)` - its own word, `duplicate:<n>`
    and/or `strict-prefix-of:<sibling>`, or None when it is nameable;
  * `ack_unnameable(labels)` - {label: reason} over the labels no prefix
    can name, duplicates counted rather than merged;
  * `ack_fully_named(labels)` - True only when every label is nameable;
  * `module_alias_entry(...)` - the PNAI answer plus `ack_unnameable`,
    `ack_unnameable_labels`, `ack_fully_named`.

Verdict: a reason carrying an unnameable label earns
SEAMS-MATCH-ORDINAL-UNIQUE-PREFIX-UNNAMEABLE and NEVER the covered word.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAJ1..AC-PNAJ6 were pinned in state/queue/tech.md:677 at R2678
BEFORE this code existed.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_scope as PNAI  # noqa: E402

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-while-match-while-else-nested-match-ordinal-"
         "unique-prefix-unnameable-scope")

E_ARGS = "E_PNAJ_ARGS"
E_NO_ROOT = "E_PNAJ_NO_ROOT"

STATE_OK = PNAI.STATE_OK
STATE_REFUSED = PNAI.STATE_REFUSED

COVERED = PNAI.COVERED
MISSING_SEAM = PNAI.MISSING_SEAM
OUT_OF_SCOPE = PNAI.OUT_OF_SCOPE
UNREADABLE = PNAI.UNREADABLE
HISTORICAL = PNAI.HISTORICAL

SEAMS_UNNAMEABLE = "SEAMS-MATCH-ORDINAL-UNIQUE-PREFIX-UNNAMEABLE"
SEAMS_STALE = PNAI.SEAMS_PREFIX_STALE
SEAMS_COVERED = PNAI.SEAMS_PREFIX_COVERED

labels_of_reason = PNAI.labels_of_reason
ack_hits = PNAI.ack_hits
ack_index = PNAI.ack_index
ack_unmatched = PNAI.ack_unmatched
prefix_free = PNAI.prefix_free

_BASE_PNAI_ENTRY = PNAI.module_alias_entry
_BASE_PNAI_REPORT = PNAI.module_alias_report
_BASE_PNAI_AUDIT = PNAI.audit


class ModuleAliasMatchOrdinalUnnameableError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def duplicate_count(label, labels):
    """How many times `label` occurs in `labels`."""
    return list(labels).count(label)


def strict_prefix_sibling(label, labels):
    """The first OTHER label `label` is a strict prefix of, else None."""
    for other in labels:
        if other != label and other.startswith(label):
            return other
    return None


def unnameable_reason(label, labels):
    """Its own word when no prefix can name it, else None."""
    parts = []
    sibling = strict_prefix_sibling(label, labels)
    if sibling is not None:
        parts.append("strict-prefix-of:%s" % sibling)
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
    """The PNAI answer, plus whether every one of its labels is nameable."""
    got = _BASE_PNAI_ENTRY(name, text, scope, line, tables, root, src_path)
    out = dict(got)
    out.update(_unnameable_block(labels_of_reason(got.get("reason"))))
    return out


def unnameable_entry(name, text, scope, line, tables=None, root=None,
                     src_path=None):
    """Alias that names the product this face adds."""
    return module_alias_entry(name, text, scope, line, tables, root, src_path)


def module_alias_report(text, root=None, src_path=None):
    """The PNAI report, carried unchanged: no reason is republished here."""
    return _BASE_PNAI_REPORT(text, root, src_path)


def _collect_reasons(report):
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict):
            reason = probe.get("reason")
            if reason:
                reasons.append(reason)
    return reasons


def unnameable_summary(report):
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
    this face and it is asserted directly rather than inferred from a tree.
    """
    if base_verdict == SEAMS_STALE:
        return SEAMS_STALE
    if unnameable_block.get("ack_unnameable"):
        return SEAMS_UNNAMEABLE
    if not ack.get("prefix_free", True):
        return SEAMS_STALE
    return SEAMS_COVERED


def audit(root=None, module=None):
    """The PNAI audit plus an unnameable reading of the reasons it names."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasMatchOrdinalUnnameableError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = _BASE_PNAI_AUDIT(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasMatchOrdinalUnnameableError(
            code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAI.LABEL
    report["unnameable"] = unnameable_summary(report)
    report["verdict"] = verdict_of(report.get("verdict"),
                                   report.get("ack") or {},
                                   {"ack_unnameable":
                                    report["unnameable"]["unnameable"]})
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasMatchOrdinalUnnameableError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_STALE, "seams": [], "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "unnameable": {"reasons": 0, "labels": [],
                               "unnameable": {}, "fully_named": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(description="unnameable-label ack face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        got = audit(args.root, args.module)
    except ModuleAliasMatchOrdinalUnnameableError as exc:
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
