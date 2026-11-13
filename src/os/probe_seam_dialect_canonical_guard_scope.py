"""Canonical-form and sibling-semantics guard for published words (R2704).

The R2701 face validates the SHAPE a marked word carries but never the
CANONICAL FORM of that shape. Measured on that shipped face before this module
existed:

  read_word('dialect:1+duplicate:02')
      -> dialect '1', duplicate 2, refused None
  read_word('dialect:1+duplicate:2')
      -> dialect '1', duplicate 2, refused None

so two byte-different words collapse into one reading although the publishing
face only ever writes the canonical integer. And

  read_word('dialect:1+strict-prefix-of:ab,ab')
      -> dialect '1', siblings ['ab', 'ab'], refused None

although a sibling is named once: ack_unnameable(['a','ab','ab']) publishes
{'a': 'strict-prefix-of:ab', 'ab': 'duplicate:2'} and never a repeated list.

A THIRD measurement narrows the queue note honestly: the sign form
('duplicate:+2') and the whitespace form ('duplicate: 2') are ALREADY refused
by the R2701 shape rule as duplicate-not-counted, so the uncovered forms this
face must refuse are the leading zero ('02', '002') and the non-ASCII digit
(the Arabic-Indic two, which isdigit() accepts and int() reads as 2). A FOURTH
measurement found a genuine crash rather than a refusal: 'duplicate:' followed
by a superscript two is isdigit() True and int() raises ValueError, so the
R2701 face raised where it should have refused - that is repaired at its birth
site in this window (int() can no longer be reached with a form it rejects)
before this face layers the canonical rule on top.

This face keeps every reading R2685, R2689, R2692, R2698 and R2701 pinned and
adds ONE rule behind the shape guard: a MARKED word whose counted duplicate is
written in a non-canonical form, or whose sibling list names one label twice,
is REFUSED naming the form found. A marker-less legacy word is untouched by
the canonical rule, so a bare 'duplicate:02' stays a legal legacy word.

Criteria AC-PNAS1..AC-PNAS6 were pinned in state/queue/tech.md:684 at R2701
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_dialect_shape_guard_scope as PNAR  # noqa

LABEL = "os-probe-seam-dialect-canonical-guard-scope"
BASE_LABEL = PNAR.LABEL

E_ARGS = "E_PNAS_ARGS"
E_NO_ROOT = "E_PNAS_NO_ROOT"

STATE_OK = PNAR.STATE_OK
STATE_REFUSED = PNAR.STATE_REFUSED
SEAMS_STALE = PNAR.SEAMS_STALE

DIALECT_MARKER = PNAR.DIALECT_MARKER
PART_JOINER = PNAR.PART_JOINER
KNOWN_TAGS = PNAR.KNOWN_TAGS

PREFIX_HEAD = PNAR.PREFIX_HEAD
DUP_HEAD = PNAR.DUP_HEAD
PAIR_SHAPE = PNAR.PAIR_SHAPE

REFUSAL_HEAD = PNAR.REFUSAL_HEAD
REFUSAL_DUP_NON_CANONICAL = "duplicate-not-canonical"
REFUSAL_SIBLING_REPEATED = "sibling-repeated"

FORM_LEADING_ZERO = "leading-zero"
FORM_NON_ASCII_DIGIT = "non-ascii-digit"
FORM_UNNAMED = "unnamed"

READING_KEYS = PNAR.READING_KEYS
GUARD_KEYS = PNAR.GUARD_KEYS

marker_of_word = PNAR.marker_of_word
marker_count = PNAR.marker_count
has_marker = PNAR.has_marker
strip_marker = PNAR.strip_marker
word_parts = PNAR.word_parts
ack_unnameable = PNAR.ack_unnameable
ack_words = PNAR.ack_words
ack_legacy_words = PNAR.ack_legacy_words
ack_unnameable_labels = PNAR.ack_unnameable_labels
labels_of_reason = PNAR.labels_of_reason
body_parts_of = PNAR.body_parts_of
part_head = PNAR.part_head
prefix_siblings_of_part = PNAR.prefix_siblings_of_part
duplicate_count_of_part = PNAR.duplicate_count_of_part
refusal_of = PNAR.refusal_of
refusal_word_of = PNAR.refusal_word_of


class ModuleAliasDialectCanonicalGuardError(Exception):
    """Carries the face own code so a caller never guesses the failure."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def duplicate_tail_of_part(part):
    """The text after 'duplicate:', or None when the part is another shape."""
    if not isinstance(part, str) or not part.startswith(DUP_HEAD):
        return None
    return part[len(DUP_HEAD):]


def canonical_tail_of_count(count):
    """The one integer spelling this face ever publishes for a count."""
    return str(count)


def non_canonical_count_of_part(part):
    """The tail of a COUNTED duplicate written non-canonically, else None.

    A counted part is one the shape guard already accepted (a bare digit run
    of at least two), so anything whose text differs from the canonical
    spelling of that count - a leading zero or a non-ASCII digit - is named
    here rather than read as the same count.
    """
    counted, count = duplicate_count_of_part(part)
    if not counted:
        return None
    tail = duplicate_tail_of_part(part)
    if tail is None:
        return None
    if tail != canonical_tail_of_count(count):
        return tail
    return None


def canonical_form_of_tail(tail):
    """The form a non-canonical duplicate tail was written in, named."""
    if tail is None:
        return None
    if any(ord(item) > 127 for item in tail):
        return FORM_NON_ASCII_DIGIT
    if tail != tail.lstrip("0"):
        return FORM_LEADING_ZERO
    return FORM_UNNAMED


def repeated_sibling_of_part(part):
    """The first sibling label a strict-prefix part names twice, else None.

    Labels are compared AFTER unescaping, because the publishing face dedupes
    by label: a comma inside one label is escaped, so 'ab\\,ac' is one label
    and never a repeat of 'ab' plus 'ac'.
    """
    siblings = prefix_siblings_of_part(part)
    if not siblings:
        return None
    seen = set()
    for item in siblings:
        if item in seen:
            return item
        seen.add(item)
    return None


def canonical_refusal(word):
    """None for a canonically written word, else the refusal it earns.

    Only MARKED words are checked: a legacy word is handed back to the R2701
    law byte for byte, because the canonical rule is a law about this face own
    pedigree rather than about legacy text.
    """
    body = body_parts_of(word)
    if body is None:
        return None
    for part in body:
        tail = non_canonical_count_of_part(part)
        if tail is not None:
            return refusal_of(REFUSAL_DUP_NON_CANONICAL,
                              canonical_form_of_tail(tail), word, len(body))
        repeated = repeated_sibling_of_part(part)
        if repeated is not None:
            return refusal_of(REFUSAL_SIBLING_REPEATED, repeated, word,
                              len(body))
    return None


def canonical_state_of_word(word):
    """'canonical' for a legal marked word, else the refusal code or None."""
    got = read_word(word)
    if got.get("refused") is not None:
        return None
    body = body_parts_of(word)
    if body is None:
        return None
    return "canonical"


def shape_of_word(word):
    """The shape of a legal marked word, None for a legal legacy word."""
    if read_word(word).get("refused") is not None:
        return None
    return PNAR.shape_of_word(word)


def read_word(word):
    """The guarded reading: R2701's own answer OR a named canonical refusal.

    A refusal reports dialect None, body None, siblings None and duplicate
    None for the same reason R2701 does - handing back the body verbatim is
    what makes a refusal indistinguishable from a reading - so a refused form
    can never be mistaken for a tag-1 word with a count.
    """
    base = PNAR.read_word(word)
    if base.get("refused") is not None:
        return base
    refusal = canonical_refusal(word)
    if refusal is not None:
        out = {"word": word, "dialect": None,
               "markers": marker_count(word),
               "body": None, "siblings": None, "duplicate": None}
        out.update(refusal)
        return out
    return base


def base_reading(word):
    """R2701's reading exactly, canonical rule aside."""
    return PNAR.read_word(word)


def is_legal_reading(word):
    """True only when the word is read rather than refused by either guard."""
    return read_word(word).get("refused") is None


def validated_shape(word):
    """The shape of a legal marked word, None for a legal legacy word."""
    return shape_of_word(word)


def tag_of_ack_word(word):
    """The tag a published word must read back, or None."""
    return read_word(word)["dialect"]


def read_words(words):
    """{word: guarded reading} over a collection, order kept by sorted key."""
    out = {}
    for word in sorted(set(words or [])):
        out[word] = read_word(word)
    return out


def refusals_of(words):
    """{word: refusal_word} over the words either guard refuses."""
    out = {}
    for word in sorted(set(words or [])):
        got = read_word(word)
        if got.get("refused") is not None:
            out[word] = got["refusal_word"]
    return out


def ack_readings(labels):
    """{label: guarded reading} over the words this face publishes."""
    out = {}
    for label, word in ack_words(labels).items():
        out[label] = read_word(word)
    return out


def ack_all_legal(labels):
    """True only when every word this face publishes reads back tag 1."""
    got = ack_readings(labels)
    return all(item["refused"] is None and item["dialect"] in KNOWN_TAGS
               for item in got.values())


def guard_summary(words):
    """One guarded reading across a collection of words, derived not typed."""
    readings = read_words(words)
    return {"known_tags": list(KNOWN_TAGS),
            "words": len(readings),
            "dialects": sorted(set(item["dialect"] for item in
                                   readings.values()
                                   if item["dialect"] is not None)),
            "shapes": sorted(set(shape_of_word(word)
                                 for word in readings
                                 if shape_of_word(word))),
            "refused": dict((word, item["refusal_word"])
                            for word, item in readings.items()
                            if item["refused"] is not None),
            "all_legal": all(item["refused"] is None
                             for item in readings.values())}


def reasons_summary(reasons):
    """The guarded reading of the words a collection of reasons publishes."""
    labels = []
    for reason in reasons or []:
        labels.extend(labels_of_reason(reason))
    return guard_summary(ack_words(labels).values())


def module_alias_entry(name, text, scope, line, tables=None, root=None,
                       src_path=None):
    """The R2701 entry, with its published words canonical-guarded as well."""
    got = PNAR.module_alias_entry(name, text, scope, line, tables, root,
                                  src_path)
    out = dict(got)
    labels = labels_of_reason(got.get("reason"))
    out["canonical_guard"] = guard_summary(ack_words(labels).values())
    out["ack_readings"] = ack_readings(labels)
    return out


def module_alias_report(text, root=None, src_path=None):
    """The R2701 report carried through, plus its canonical-guarded reading."""
    report = PNAR.module_alias_report(text, root, src_path)
    out = dict(report)
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict) and probe.get("reason"):
            reasons.append(probe["reason"])
    out["canonical_guard"] = reasons_summary(reasons)
    return out


def audit(root=None, module=None):
    """The R2701 audit plus the canonical guard over every word it publishes."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasDialectCanonicalGuardError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNAR.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasDialectCanonicalGuardError(
            code, str(getattr(exc, "detail", exc)))
    out = dict(report)
    out["tool"] = LABEL
    out["base_tool"] = PNAR.LABEL
    words = list(((report.get("dialect") or {}).get("unnameable") or {})
                 .values())
    out["canonical_guard"] = guard_summary(words)
    return out


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasDialectCanonicalGuardError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "canonical_guard": {"known_tags": list(KNOWN_TAGS),
                                    "words": 0, "dialects": [], "shapes": [],
                                    "refused": {}, "all_legal": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="dialect canonical-form-guarded word reading face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--word", default=None,
                        help="read one word under all three guards")
    parser.add_argument("--labels", default=None,
                        help="comma separated labels to publish and read")
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
        payload = {"labels": labels, "words": ack_words(labels),
                   "readings": ack_readings(labels),
                   "all_legal": ack_all_legal(labels)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(json.dumps(payload, sort_keys=True))
        return 0
    try:
        got = audit(args.root, args.module)
    except ModuleAliasDialectCanonicalGuardError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc.detail))
        return 4 if exc.code == E_ARGS else 5
    if args.json:
        print(json.dumps(got, indent=2, sort_keys=True))
    else:
        print("%s verdict=%s" % (got["tool"], got["verdict"]))
        print("words=%d dialects=%s shapes=%s refused=%d all_legal=%s"
              % (got["canonical_guard"]["words"],
                 got["canonical_guard"]["dialects"],
                 got["canonical_guard"]["shapes"],
                 len(got["canonical_guard"]["refused"]),
                 got["canonical_guard"]["all_legal"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
