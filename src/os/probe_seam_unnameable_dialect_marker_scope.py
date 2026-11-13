"""Dialect-marked unnameable-label ack face (R2692).

The R2685 face published `strict-prefix-of:ab+duplicate:2` for BOTH the
one-label shape (`['a','ab+duplicate:2']`) and the genuine sibling-plus-copy
shape (`['a','ab','a']`), and the R2689 face repaired its OWN words without
leaving any pedigree in them: neither publisher stamps which dialect produced
a word, so a consumer holding a pre-R2689 string reads it as siblings `['ab']`
plus duplicate 2 and cannot tell what the publisher meant.

This face publishes the dialect marker `dialect:1` as the FIRST part of every
word it writes, reads that marker back from the parts rather than assuming it,
and keeps the body after the marker byte for byte what R2689 published for the
same labels. A word carrying no marker in its first part is a LEGACY word and
is parsed exactly as R2689 parses it today, so nothing already published is
re-read differently.

Criteria AC-PNAP1..AC-PNAP6 were pinned in state/queue/tech.md:681 at R2689
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa

LABEL = "os-probe-seam-unnameable-dialect-marker-scope"
BASE_LABEL = PNAO.LABEL
LEGACY_LABEL = PNAL.LABEL

E_ARGS = "E_PNAP_ARGS"
E_NO_ROOT = "E_PNAP_NO_ROOT"

STATE_OK = PNAO.STATE_OK
STATE_REFUSED = PNAO.STATE_REFUSED
COVERED = PNAO.COVERED
MISSING_SEAM = PNAO.MISSING_SEAM
OUT_OF_SCOPE = PNAO.OUT_OF_SCOPE
UNREADABLE = PNAO.UNREADABLE
HISTORICAL = PNAO.HISTORICAL
SEAMS_UNNAMEABLE = PNAO.SEAMS_UNNAMEABLE
SEAMS_STALE = PNAO.SEAMS_STALE
SEAMS_COVERED = PNAO.SEAMS_COVERED

PREFIX_HEAD = PNAO.PREFIX_HEAD
DUP_HEAD = PNAO.DUP_HEAD
PART_JOINER = PNAO.PART_JOINER
LIST_JOINER = PNAO.LIST_JOINER
ESCAPE = PNAO.ESCAPE

DIALECT_HEAD = "dialect:"
DIALECT_TAG = "1"
DIALECT_MARKER = DIALECT_HEAD + DIALECT_TAG

labels_of_reason = PNAO.labels_of_reason
ack_hits = PNAO.ack_hits
ack_index = PNAO.ack_index
ack_unmatched = PNAO.ack_unmatched
prefix_free = PNAO.prefix_free
duplicate_count = PNAO.duplicate_count
strict_prefix_siblings = PNAO.strict_prefix_siblings
strict_prefix_sibling = PNAO.strict_prefix_sibling
escape_label = PNAO.escape_label
unescape_label = PNAO.unescape_label
split_escaped = PNAO.split_escaped
split_parts_escaped = PNAO.split_parts_escaped
strict_prefix_word = PNAO.strict_prefix_word

_BASE_PNAP_ENTRY = PNAO.module_alias_entry
_BASE_PNAP_REPORT = PNAO.module_alias_report
_BASE_PNAP_AUDIT = PNAO.audit


class ModuleAliasUnnameableDialectMarkerError(Exception):
    """Carries the face own code so a caller never guesses the failure."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def word_parts(word):
    """Every part of a word, escapes intact, marker included."""
    return split_parts_escaped(str(word))


def marker_of_word(word):
    """The dialect tag a word carries, or None for a LEGACY word.

    The marker is only ever the FIRST part: a part equal to the marker text
    further down the word is body content and never a pedigree, so a word
    cannot claim a dialect by appending the marker to its tail.
    """
    if not isinstance(word, str):
        return None
    parts = word_parts(word)
    if parts and parts[0] == DIALECT_MARKER:
        return DIALECT_TAG
    return None


def has_marker(word):
    """True only when the first part is exactly the dialect marker."""
    return marker_of_word(word) == DIALECT_TAG


def marker_count(word):
    """How many parts of a word read as the marker text, position aside."""
    if not isinstance(word, str):
        return 0
    return sum(1 for part in word_parts(word) if part == DIALECT_MARKER)


def with_marker(body):
    """One escaped body prefixed with the dialect marker part."""
    return DIALECT_MARKER + PART_JOINER + str(body)


def strip_marker(word):
    """The word as R2689 would have published it, marker removed.

    A legacy word is handed back byte for byte, so this is a reading and not
    a rewrite: no byte of a legacy string moves.
    """
    if not isinstance(word, str) or not has_marker(word):
        return word
    head = DIALECT_MARKER + PART_JOINER
    return word[len(head):] if word.startswith(head) else word


def parse_strict_prefix_word(word):
    """The siblings a word names; legacy words keep R2689's answer exactly."""
    return PNAO.parse_strict_prefix_word(word)


def sibling_count_from_word(word):
    """How many siblings a word names, or None if it names none."""
    return PNAO.sibling_count_from_word(word)


def parse_duplicate_from_word(word):
    """The duplicate count a word names, or None."""
    return PNAO.parse_duplicate_from_word(word)


def parse_part_word(word):
    """Both readings a word carries, derived rather than typed."""
    return PNAO.parse_part_word(word)


def read_word(word):
    """Everything a word states about itself, marker first.

    `dialect` is a READING of the first part, so a legacy string reports None
    and a fabricated tail marker reports None as well.
    """
    return {"dialect": marker_of_word(word),
            "markers": marker_count(word),
            "body": strip_marker(word),
            "siblings": parse_strict_prefix_word(word),
            "duplicate": parse_duplicate_from_word(word)}


def unnameable_reason(label, labels):
    """Its own marked word when no prefix can name it, else None."""
    body = PNAO.unnameable_reason(label, labels)
    return None if body is None else with_marker(body)


def ack_unnameable(labels):
    """{label: marked word} over the labels no prefix can name."""
    out = {}
    for label in sorted(set(labels)):
        reason = unnameable_reason(label, labels)
        if reason:
            out[label] = reason
    return out


def ack_legacy_words(labels):
    """{label: the R2689 word for the same labels} - marker stripped."""
    return dict((label, strip_marker(word))
                for label, word in ack_unnameable(labels).items())


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


def ack_part_readings(labels):
    """{label: both readings its word carries} for the unnameable ones."""
    out = {}
    for label, reason in ack_unnameable(labels).items():
        out[label] = parse_part_word(reason)
    return out


def ack_word_readings(labels):
    """{label: the whole self-description of its published word}."""
    out = {}
    for label, reason in ack_unnameable(labels).items():
        out[label] = read_word(reason)
    return out


def dialect_tags_of(words):
    """The distinct dialect tags a collection of words reports."""
    tags = []
    for word in words:
        tag = marker_of_word(word)
        if tag is not None:
            tags.append(tag)
    return sorted(set(tags))


def _unnameable_block(labels):
    """The unnameable reading of one reason set, derived not typed."""
    words = ack_unnameable(labels)
    return {"ack_unnameable": words,
            "ack_unnameable_labels": sorted(words),
            "ack_fully_named": not words,
            "ack_dialects": dialect_tags_of(words.values()),
            "ack_legacy_words": ack_legacy_words(labels)}


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The R2689 answer, with its unnameable reading re-published marked."""
    got = _BASE_PNAP_ENTRY(name, text, scope, line, tables, root, src_path)
    out = dict(got)
    labels = labels_of_reason(got.get("reason"))
    out.update(_unnameable_block(labels))
    out["ack_sibling_counts"] = ack_sibling_counts(labels)
    out["ack_part_readings"] = ack_part_readings(labels)
    out["ack_word_readings"] = ack_word_readings(labels)
    return out


def dialect_entry(name, text, scope, line, tables=None, root=None,
                  src_path=None):
    """Alias that names the product this face adds."""
    return module_alias_entry(name, text, scope, line, tables, root, src_path)


def module_alias_report(text, root=None, src_path=None):
    """The R2689 report, carried unchanged: no reason is republished here."""
    return _BASE_PNAP_REPORT(text, root, src_path)


def _collect_reasons(report):
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict):
            reason = probe.get("reason")
            if reason:
                reasons.append(reason)
    return reasons


def dialect_summary(report):
    """One marked reading across every reason an audit published."""
    collected = _collect_reasons(report)
    labels = []
    for reason in collected:
        labels.extend(labels_of_reason(reason))
    words = ack_unnameable(labels)
    return {"reasons": len(collected),
            "labels": sorted(set(labels)),
            "marker": DIALECT_MARKER,
            "dialect": dialect_tags_of(words.values()),
            "unnameable": words,
            "legacy_words": ack_legacy_words(labels),
            "sibling_counts": ack_sibling_counts(labels),
            "part_readings": ack_part_readings(labels),
            "fully_named": ack_fully_named(labels)}


def verdict_of(base_verdict, ack, unnameable_block):
    """The one place a covered word can be withheld."""
    return PNAO.verdict_of(base_verdict, ack, unnameable_block)


def audit(root=None, module=None):
    """The R2689 audit plus a marked reading of the words it publishes."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasUnnameableDialectMarkerError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = _BASE_PNAP_AUDIT(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasUnnameableDialectMarkerError(
            code, str(getattr(exc, "detail", exc)))
    report["tool"] = LABEL
    report["base_tool"] = PNAO.LABEL
    report["dialect"] = dialect_summary(report)
    report["verdict"] = verdict_of(report.get("verdict"),
                                   report.get("ack") or {},
                                   {"ack_unnameable":
                                    report["dialect"]["unnameable"]})
    return report


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasUnnameableDialectMarkerError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_STALE, "seams": [], "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "dialect": {"reasons": 0, "labels": [], "marker":
                            DIALECT_MARKER, "dialect": [], "unnameable": {},
                            "legacy_words": {}, "sibling_counts": {},
                            "part_readings": {}, "fully_named": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="dialect-marked unnameable-label ack face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--word", default=None,
                        help="read one published word and report it")
    parser.add_argument("--labels", default=None,
                        help="comma separated labels to publish words for")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.word is not None:
        payload = read_word(args.word)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("word=%s %s" % (args.word,
                                 json.dumps(payload, sort_keys=True)))
        return 0
    if args.labels is not None:
        labels = [item for item in args.labels.split(",") if item]
        payload = {"labels": labels,
                   "words": ack_unnameable(labels),
                   "readings": ack_word_readings(labels)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(json.dumps(payload, sort_keys=True))
        return 0
    try:
        got = audit(args.root, args.module)
    except ModuleAliasUnnameableDialectMarkerError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc.detail))
        return 4 if exc.code == E_ARGS else 5
    if args.json:
        print(json.dumps(got, indent=2, sort_keys=True))
    else:
        print("%s verdict=%s" % (got["tool"], got["verdict"]))
        print("labels=%d marker=%s dialects=%s fully_named=%s"
              % (len(got["dialect"]["labels"]),
                 got["dialect"]["marker"],
                 got["dialect"]["dialect"],
                 got["dialect"]["fully_named"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
