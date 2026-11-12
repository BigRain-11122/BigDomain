"""Escaped unnameable-label ack face: the PART JOINER is escaped too (R2689).

The R2685 face escapes the escape character first and the list separator
second, so one sibling carrying a comma can never be read as two. It never
escapes the part joiner (`+`), so a single label named `ab+duplicate:2`
publishes byte for byte the word a genuine sibling plus a genuine duplicate
part publishes, and parsing that word recovers only `ab` and loses the tail.

This face escapes the escape character first, the list separator second and
the part joiner third, so no label can be read as a part boundary either. The
round trip is published for BOTH readings (siblings and the duplicate count),
so a caller reads what a word names instead of guessing.

Criteria AC-PNAO1..AC-PNAO6 were pinned in state/queue/tech.md:681 at R2685
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_scope as PNAK  # noqa

LABEL = "os-probe-seam-unnameable-part-joiner-escaped-scope"
BASE_LABEL = PNAL.LABEL

E_ARGS = "E_PNAO_ARGS"
E_NO_ROOT = "E_PNAO_NO_ROOT"

STATE_OK = PNAL.STATE_OK
STATE_REFUSED = PNAL.STATE_REFUSED
COVERED = PNAL.COVERED
MISSING_SEAM = PNAL.MISSING_SEAM
OUT_OF_SCOPE = PNAL.OUT_OF_SCOPE
UNREADABLE = PNAL.UNREADABLE
HISTORICAL = PNAL.HISTORICAL
SEAMS_UNNAMEABLE = PNAL.SEAMS_UNNAMEABLE
SEAMS_STALE = PNAL.SEAMS_STALE
SEAMS_COVERED = PNAL.SEAMS_COVERED

PREFIX_HEAD = PNAL.PREFIX_HEAD
DUP_HEAD = PNAL.DUP_HEAD
PART_JOINER = PNAL.PART_JOINER
LIST_JOINER = PNAL.LIST_JOINER
ESCAPE = PNAL.ESCAPE

labels_of_reason = PNAL.labels_of_reason
ack_hits = PNAL.ack_hits
ack_index = PNAL.ack_index
ack_unmatched = PNAL.ack_unmatched
prefix_free = PNAL.prefix_free
duplicate_count = PNAL.duplicate_count
strict_prefix_siblings = PNAL.strict_prefix_siblings
strict_prefix_sibling = PNAL.strict_prefix_sibling

_BASE_PNAK_ENTRY = PNAK.module_alias_entry
_BASE_PNAK_REPORT = PNAK.module_alias_report
_BASE_PNAK_AUDIT = PNAK.audit


class ModuleAliasUnnameablePartJoinerEscapedError(Exception):
    """Carries the face own code so a caller never guesses the failure."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def escape_label(label):
    """One sibling label made safe for BOTH separators and the escape.

    The escape character is escaped FIRST, so a label that already carries a
    backslash cannot smuggle an escaped comma or an escaped joiner past the
    reader; the list separator goes second and the part joiner third.
    """
    text = str(label)
    text = text.replace(ESCAPE, ESCAPE + ESCAPE)
    text = text.replace(LIST_JOINER, ESCAPE + LIST_JOINER)
    return text.replace(PART_JOINER, ESCAPE + PART_JOINER)


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


def _split_on(text, separator):
    """Split on one separator that is not escaped, keeping escapes intact."""
    parts = []
    current = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == ESCAPE and index + 1 < len(text):
            current.append(text[index:index + 2])
            index += 2
        elif char == separator:
            parts.append("".join(current))
            current = []
            index += 1
        else:
            current.append(char)
            index += 1
    parts.append("".join(current))
    return parts


def split_escaped(text):
    """Split on the list separator that is not escaped, then unescape."""
    return [unescape_label(part) for part in _split_on(text, LIST_JOINER)]


def split_parts_escaped(text):
    """Split on the part joiner that is not escaped, WITHOUT unescaping.

    The parts are handed back with their escapes intact on purpose: the
    sibling body still has to be split on the list separator, and unescaping
    here would turn an escaped comma into a real one and read one sibling as
    two (measured on this face first pass).
    """
    return _split_on(text, PART_JOINER)


def strict_prefix_word(siblings):
    """`strict-prefix-of:<escaped>,<escaped>` over every sibling, in order."""
    return PREFIX_HEAD + LIST_JOINER.join(escape_label(item)
                                          for item in siblings)


def parse_strict_prefix_word(word):
    """The siblings a published word names, or None if it names none.

    A part boundary is a joiner that is NOT escaped, so a single label
    carrying the joiner stays one sibling instead of losing its tail.
    """
    if not isinstance(word, str):
        return None
    for part in split_parts_escaped(word):
        if part.startswith(PREFIX_HEAD):
            return split_escaped(part[len(PREFIX_HEAD):])
    return None


def sibling_count_from_word(word):
    """How many siblings a published word names, or None if it names none."""
    siblings = parse_strict_prefix_word(word)
    return None if siblings is None else len(siblings)


def parse_duplicate_from_word(word):
    """The duplicate count a published word names, or None."""
    if not isinstance(word, str):
        return None
    for part in split_parts_escaped(word):
        if part.startswith(DUP_HEAD):
            body = unescape_label(part[len(DUP_HEAD):])
            if body.isdigit():
                return int(body)
    return None


def parse_part_word(word):
    """Both readings a published word carries, derived rather than typed."""
    if not isinstance(word, str):
        return {"siblings": None, "duplicate": None}
    return {"siblings": parse_strict_prefix_word(word),
            "duplicate": parse_duplicate_from_word(word)}


def unnameable_reason(label, labels):
    """Its own word when no prefix can name it, else None.

    Carries the same two parts PNAK published - the sibling list and the
    duplicate count, joined by `+` - with every sibling escaped so one name
    carrying either separator can never be read as two siblings or as a
    part boundary.
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


def ack_part_readings(labels):
    """{label: both readings its word carries} for the unnameable ones."""
    out = {}
    for label, reason in ack_unnameable(labels).items():
        out[label] = parse_part_word(reason)
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
    out["ack_part_readings"] = ack_part_readings(labels)
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
            "part_readings": ack_part_readings(labels),
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
        raise ModuleAliasUnnameablePartJoinerEscapedError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = _BASE_PNAK_AUDIT(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasUnnameablePartJoinerEscapedError(
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
    except ModuleAliasUnnameablePartJoinerEscapedError as exc:
        return {"tool": LABEL,
                "verdict": SEAMS_STALE, "seams": [], "probes": [],
                "counts": {COVERED: 0, MISSING_SEAM: 0, OUT_OF_SCOPE: 0,
                           UNREADABLE: 0, HISTORICAL: 0},
                "unnameable": {"reasons": 0, "labels": [],
                               "unnameable": {}, "sibling_counts": {},
                               "part_readings": {}, "fully_named": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="escaped unnameable-label part-joiner ack face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--word", default=None,
                        help="parse one published word and report it")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.word is not None:
        payload = {"word": args.word,
                   "siblings": parse_strict_prefix_word(args.word),
                   "count": sibling_count_from_word(args.word),
                   "duplicate": parse_duplicate_from_word(args.word)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("word=%s siblings=%s count=%s duplicate=%s"
                  % (args.word, payload["siblings"], payload["count"],
                     payload["duplicate"]))
        return 0
    try:
        got = audit(args.root, args.module)
    except ModuleAliasUnnameablePartJoinerEscapedError as exc:
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
