"""Prefix ack whose strict-prefix word cannot be read as the wrong count.

The R2682 face (PNAK) made the strict-prefix word carry EVERY sibling, but
its separator was a bare comma that nothing escaped. Measured at R2685
BEFORE any byte here was written, `ack_unnameable(['a','ab,ac'])` answered
`{'a': 'strict-prefix-of:ab,ac'}` - byte for byte what `['a','ab','ac']`
answers - so ONE sibling published with a comma in its name read as TWO, and
a caller counting bindings from the word alone was counting the wrong thing.

This face keeps every answer PNAK, PNAJ, PNAI and PNAG published byte for
byte and makes the word unambiguous:

  * `escape_label(label)` - a sibling carries `\\\\` for its own backslash and
    `\\\\,` for a comma, so the escape character is escaped FIRST and an
    escaped label can never be mistaken for two;
  * `strict_prefix_word(siblings)` - `strict-prefix-of:<escaped>,<escaped>`;
  * `parse_strict_prefix_word(word)` - the round trip, so the count is a
    READING rather than a guess;
  * `sibling_count_from_word(word)` - how many siblings a word names;
  * `unnameable_reason(label, labels)` - the same word shape PNAK published
    plus `+duplicate:<n>`, now with each sibling escaped;
  * `ack_unnameable(labels)` - {label: reason} over the unnameable labels;
  * `ack_sibling_counts(labels)` - how many siblings each word names;
  * `module_alias_entry(...)` - the PNAK answer whose `ack_unnameable`,
    `ack_unnameable_labels` and `ack_fully_named` are re-derived here, plus
    `ack_sibling_counts`.

A label with no comma and no backslash is escaped to itself, which is why
the single-sibling word `strict-prefix-of:xy` and the two-sibling word
`strict-prefix-of:ab,ac` stay byte for byte what earlier rounds published.

Verdict: a reason carrying an unnameable label earns
SEAMS-MATCH-ORDINAL-UNIQUE-PREFIX-UNNAMEABLE and NEVER the covered word.

Pure ASCII, stdlib only, no clock, zero network.

Criteria AC-PNAL1..AC-PNAL6 were pinned in state/queue/tech.md:680 at R2682
BEFORE this code existed.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_scope as PNAK  # noqa: E402

LABEL = ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
         "import-alias-scope-module-alias-attribute-alias-walrus-relative-"
         "branch-elif-with-while-match-while-else-nested-match-ordinal-"
         "unique-prefix-unnameable-siblings-escaped-scope")

E_ARGS = "E_PNAL_ARGS"
E_NO_ROOT = "E_PNAL_NO_ROOT"
E_BAD_WORD = "E_PNAL_BAD_WORD"

STATE_OK = PNAK.STATE_OK
STATE_REFUSED = PNAK.STATE_REFUSED

COVERED = PNAK.COVERED
MISSING_SEAM = PNAK.MISSING_SEAM
OUT_OF_SCOPE = PNAK.OUT_OF_SCOPE
UNREADABLE = PNAK.UNREADABLE
HISTORICAL = PNAK.HISTORICAL

SEAMS_UNNAMEABLE = PNAK.SEAMS_UNNAMEABLE
SEAMS_STALE = PNAK.SEAMS_STALE
SEAMS_COVERED = PNAK.SEAMS_COVERED

PREFIX_HEAD = "strict-prefix-of:"
DUP_HEAD = "duplicate:"
PART_JOINER = "+"
LIST_JOINER = ","
ESCAPE = "\\"

labels_of_reason = PNAK.labels_of_reason
ack_hits = PNAK.ack_hits
ack_index = PNAK.ack_index
ack_unmatched = PNAK.ack_unmatched
prefix_free = PNAK.prefix_free
duplicate_count = PNAK.duplicate_count
strict_prefix_siblings = PNAK.strict_prefix_siblings
strict_prefix_sibling = PNAK.strict_prefix_sibling

_BASE_PNAK_ENTRY = PNAK.module_alias_entry
_BASE_PNAK_REPORT = PNAK.module_alias_report
_BASE_PNAK_AUDIT = PNAK.audit


class ModuleAliasUnnameableSiblingsEscapedError(Exception):
    """A refusal this face raises with its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def escape_label(label):
    """One sibling label made safe for the list separator.

    The escape character is escaped FIRST, so a label that already carries a
    backslash cannot smuggle an escaped comma past the reader.
    """
    return str(label).replace(ESCAPE, ESCAPE + ESCAPE).replace(
        LIST_JOINER, ESCAPE + LIST_JOINER)


def unescape_label(text):
    """The inverse of escape_label; an unknown escape is kept verbatim."""
    out = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == ESCAPE and index + 1 < len(text):
            out.append(text[index + 1])
            index += 2
        else:
            out.append(char)
            index += 1
    return "".join(out)


def split_escaped(text):
    """Split on the list separator that is not escaped, then unescape."""
    parts = []
    current = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == ESCAPE and index + 1 < len(text):
            current.append(text[index:index + 2])
            index += 2
        elif char == LIST_JOINER:
            parts.append("".join(current))
            current = []
            index += 1
        else:
            current.append(char)
            index += 1
    parts.append("".join(current))
    return [unescape_label(part) for part in parts]


def strict_prefix_word(siblings):
    """`strict-prefix-of:<escaped>,<escaped>` over every sibling, in order."""
    return PREFIX_HEAD + LIST_JOINER.join(escape_label(item)
                                          for item in siblings)


def parse_strict_prefix_word(word):
    """The siblings a published word names, or None if it names none."""
    if not isinstance(word, str):
        return None
    for part in word.split(PART_JOINER):
        if part.startswith(PREFIX_HEAD):
            body = part[len(PREFIX_HEAD):]
            return split_escaped(body)
    return None


def sibling_count_from_word(word):
    """How many siblings a published word names, or None if it names none."""
    siblings = parse_strict_prefix_word(word)
    return None if siblings is None else len(siblings)


def unnameable_reason(label, labels):
    """Its own word when no prefix can name it, else None.

    Carries the same two parts PNAK published - the sibling list and the
    duplicate count, joined by `+` - with every sibling escaped so one name
    carrying the separator can never be read as two.
    """
    parts = []
    siblings = strict_prefix_siblings(label, labels)
    if siblings:
        parts.append(strict_prefix_word(siblings))
    count = duplicate_count(label, labels)
    if count > 1:
        parts.append("%s%d" % (DUP_HEAD, count))
    return PART_JOINER.join(parts) if parts else None


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


def ack_sibling_counts(labels):
    """{label: how many siblings its word names} for the unnameable ones."""
    out = {}
    for label, reason in ack_unnameable(labels).items():
        count = sibling_count_from_word(reason)
        if count is not None:
            out[label] = count
    return out


def _unnameable_block(labels):
    """The unnameable reading of one reason, derived not typed."""
    reasons = ack_unnameable(labels)
    return {"ack_unnameable": reasons,
            "ack_unnameable_labels": sorted(reasons),
            "ack_fully_named": not reasons}


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The PNAK answer, with its unnameable reading re-derived and escaped."""
    got = _BASE_PNAK_ENTRY(name, text, scope, line, tables, root, src_path)
    out = dict(got)
    labels = labels_of_reason(got.get("reason"))
    out.update(_unnameable_block(labels))
    out["ack_sibling_counts"] = ack_sibling_counts(labels)
    return out


def escaped_entry(name, text, scope, line, tables=None, root=None,
                  src_path=None):
    """Alias that names the product this face adds."""
    return module_alias_entry(name, text, scope, line, tables, root, src_path)


def module_alias_report(text, root=None, src_path=None):
    """The PNAK report, carried unchanged: no reason is republished here."""
    return _BASE_PNAK_REPORT(text, root, src_path)


def _collect_reasons(report):
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict):
            reason = probe.get("reason")
            if reason:
                reasons.append(reason)
    return reasons


def escaped_summary(report):
    """One unnameable reading across every reason an audit published."""
    collected = _collect_reasons(report)
    labels = []
    for reason in collected:
        labels.extend(labels_of_reason(reason))
    return {"reasons": len(collected),
            "labels": sorted(set(labels)),
            "unnameable": ack_unnameable(labels),
            "sibling_counts": ack_sibling_counts(labels),
            "fully_named": ack_fully_named(labels)}


def verdict_of(base_verdict, ack, unnameable_block):
    """The one place a covered word can be withheld.

    A reason carrying any unnameable label NEVER earns the covered word, no
    matter what the published prefixes look like.
    """
    if base_verdict == SEAMS_STALE:
        return SEAMS_STALE
    if unnameable_block.get("ack_unnameable"):
        return SEAMS_UNNAMEABLE
    if not ack.get("prefix_free", True):
        return SEAMS_STALE
    return SEAMS_COVERED


def audit(root=None, module=None):
    """The PNAK audit plus an escaped unnameable reading of its reasons."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasUnnameableSiblingsEscapedError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = _BASE_PNAK_AUDIT(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasUnnameableSiblingsEscapedError(
            code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAK.LABEL
    report["unnameable"] = escaped_summary(report)
    report["verdict"] = verdict_of(report.get("verdict"),
                                   report.get("ack") or {},
                                   {"ack_unnameable":
                                    report["unnameable"]["unnameable"]})
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasUnnameableSiblingsEscapedError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_STALE, "seams": [], "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "unnameable": {"reasons": 0, "labels": [],
                               "unnameable": {}, "sibling_counts": {},
                               "fully_named": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="escaped unnameable-label sibling-list ack face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--word", default=None,
                        help="parse one strict-prefix word and report it")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.word is not None:
        siblings = parse_strict_prefix_word(args.word)
        payload = {"word": args.word, "siblings": siblings,
                   "count": sibling_count_from_word(args.word)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("word=%s siblings=%s count=%s"
                  % (args.word, siblings, payload["count"]))
        return 0
    try:
        got = audit(args.root, args.module)
    except ModuleAliasUnnameableSiblingsEscapedError as exc:
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
