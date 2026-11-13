"""Marker-escape and duplicate-tail-escape guard (R2710).

The R2706 face walks escapes for the strict-prefix sibling text alone.
Measured on that shipped face before this module existed:

  read_word('dialect\\:1+duplicate:2')        (escaped colon in the marker)
      -> dialect None, body 'dialect\\:1+duplicate:2', refused None
  read_word('dialect:1+strict-prefix-of:ab+duplicate:a\\2c')
      -> refused 'duplicate-not-counted', shape 'a\\2c'

so an escape inside the MARKER part is never looked at and the word is read
as a LEGACY word, and an illegal escape inside a DUPLICATE tail is named by
the shape law alone, never by the escape law - the two laws disagree about
what "not published" means. A THIRD shape is kept honest:

  read_word('dialect:1+duplicate:a\\+2')      (escaped part joiner in tail)
      -> refused 'duplicate-not-counted', shape 'a\\\\'

so the raw tail bytes are lost before the refusal is built.

This face adds TWO rules behind the R2706 guard and changes nothing else:

  1. a first raw part that carries an escape and that unescapes to a dialect
     marker is REFUSED naming that form, never read as a legacy word;
  2. a marked word whose duplicate tail carries an escape is REFUSED naming
     BOTH the escape and the shape, with the RAW tail bytes kept.

Every reading R2685, R2689, R2692, R2698, R2701, R2704 and R2706 pinned rides
unchanged, and a marker-less legacy word is untouched by both rules.

Criteria AC-PNAU1..AC-PNAU6 were pinned in state/queue/tech.md:687 at R2706
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_dialect_escape_guard_scope as PNAT  # noqa
import probe_seam_dialect_canonical_guard_scope as PNAS  # noqa
import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa

LABEL = "os-probe-seam-dialect-marker-escape-guard-scope"
BASE_LABEL = PNAT.LABEL

E_ARGS = "E_PNAU_ARGS"
E_NO_ROOT = "E_PNAU_NO_ROOT"

STATE_OK = PNAT.STATE_OK
STATE_REFUSED = PNAT.STATE_REFUSED
SEAMS_STALE = PNAT.SEAMS_STALE

DIALECT_MARKER = PNAS.DIALECT_MARKER
PART_JOINER = PNAS.PART_JOINER
LIST_JOINER = PNAO.LIST_JOINER
ESCAPE = PNAO.ESCAPE
KNOWN_TAGS = PNAS.KNOWN_TAGS

PREFIX_HEAD = PNAS.PREFIX_HEAD
DUP_HEAD = PNAS.DUP_HEAD

REFUSAL_HEAD = PNAS.REFUSAL_HEAD
REFUSAL_MARKER_ESCAPED = "marker-escaped"
REFUSAL_DUP_TAIL_ESCAPE = "duplicate-escape-not-counted"

READING_KEYS = PNAT.READING_KEYS
GUARD_KEYS = PNAT.GUARD_KEYS

ESCAPABLE = PNAT.ESCAPABLE

marker_of_word = PNAT.marker_of_word
marker_count = PNAT.marker_count
has_marker = PNAT.has_marker
strip_marker = PNAT.strip_marker
word_parts = PNAT.word_parts
body_parts_of = PNAT.body_parts_of
part_head = PNAT.part_head
ack_unnameable = PNAT.ack_unnameable
ack_words = PNAT.ack_words
ack_legacy_words = PNAT.ack_legacy_words
ack_unnameable_labels = PNAT.ack_unnameable_labels
labels_of_reason = PNAT.labels_of_reason
prefix_siblings_of_part = PNAT.prefix_siblings_of_part
duplicate_count_of_part = PNAT.duplicate_count_of_part
refusal_of = PNAT.refusal_of
refusal_word_of = PNAT.refusal_word_of
escape_label = PNAT.escape_label
unescape_label = PNAT.unescape_label
escape_form_of_text = PNAT.escape_form_of_text
ascii_form_of_char = PNAT.ascii_form_of_char


class ModuleAliasDialectMarkerEscapeError(Exception):
    """Carries the face own code so a caller never guesses the failure."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def raw_part_spans(text):
    """Split on PART_JOINER that is not escaped, KEEPING every escape.

    Unlike the shipped splitter this walk also keeps an escaped part joiner
    inside one part, so a duplicate tail such as 'a\\+2' stays one span and
    its raw bytes are never lost before a refusal names them.
    """
    if not isinstance(text, str):
        return []
    spans = []
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == ESCAPE and index + 1 < len(text):
            index += 2
            continue
        if char == PART_JOINER:
            spans.append(text[start:index])
            start = index + 1
        index += 1
    spans.append(text[start:])
    return spans


def first_escape_char(text):
    """The character the first escape in RAW text introduces, or None."""
    if not isinstance(text, str):
        return None
    index = 0
    while index < len(text):
        if text[index] == ESCAPE:
            if index + 1 >= len(text):
                return None
            return text[index + 1]
        index += 1
    return None


def marker_escape_refusal(word):
    """AC-PNAU1: a first part that escapes its way into a marker is refused.

    The part must carry an escape AND unescape to a dialect marker; a word
    whose first part merely contains a backslash before something else stays
    a legacy word exactly as R2706 read it.
    """
    spans = raw_part_spans(word)
    if not spans:
        return None
    first = spans[0]
    if ESCAPE not in first:
        return None
    plain = unescape_label(first)
    if not plain.startswith(DIALECT_MARKER):
        return None
    return refusal_of(REFUSAL_MARKER_ESCAPED,
                      ascii_form_of_char(first_escape_char(first)),
                      word, max(len(spans) - 1, 0))


def duplicate_tail_escape_refusal(word):
    """AC-PNAU2/3: a marked word whose duplicate tail carries an escape.

    The refusal names the escape (its code) AND the shape (not-counted) and
    keeps the RAW tail bytes, so an escaped part joiner and an escape before
    a letter are named the same way this face names any unpublished escape.
    A marker-less legacy word is untouched: the duplicate rule belongs to
    this face own pedigree.
    """
    if not has_marker(word):
        return None
    spans = raw_part_spans(word)
    body = spans[1:] if spans else []
    for part in body:
        if not part.startswith(DUP_HEAD):
            continue
        tail = part[len(DUP_HEAD):]
        if ESCAPE in tail:
            return refusal_of(REFUSAL_DUP_TAIL_ESCAPE, tail, word, len(body))
    return None


def escape_refusal(word):
    """This face own two rules, then the R2706 rule, in that order."""
    found = marker_escape_refusal(word)
    if found is not None:
        return found
    found = duplicate_tail_escape_refusal(word)
    if found is not None:
        return found
    return PNAT.escape_refusal(word)


def read_word(word):
    """The guarded reading: a named refusal OR the R2706 reading verbatim.

    A refusal reports dialect None, body None, siblings None and duplicate
    None for the same reason the parents do - handing back the body verbatim
    is what makes a refusal indistinguishable from a reading.
    """
    refusal = escape_refusal(word)
    if refusal is not None:
        out = {"word": word, "dialect": None,
               "markers": marker_count(word),
               "body": None, "siblings": None, "duplicate": None}
        out.update(refusal)
        return out
    return PNAT.read_word(word)


def base_reading(word):
    """The R2706 reading exactly, both rules aside."""
    return PNAT.read_word(word)


def is_legal_reading(word):
    """True only when the word is read rather than refused by any guard."""
    return read_word(word).get("refused") is None


def shape_of_word(word):
    """The shape of a legal marked word, None for a legal legacy word."""
    if read_word(word).get("refused") is not None:
        return None
    return PNAT.shape_of_word(word)


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
    """{word: refusal_word} over the words any guard refuses."""
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
            "escapable": list(ESCAPABLE),
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
    """The R2706 entry, with its published words guarded by both rules."""
    got = PNAT.module_alias_entry(name, text, scope, line, tables, root,
                                  src_path)
    out = dict(got)
    labels = labels_of_reason(got.get("reason"))
    out["escape_guard"] = guard_summary(ack_words(labels).values())
    out["ack_readings"] = ack_readings(labels)
    return out


def module_alias_report(text, root=None, src_path=None):
    """The R2706 report carried through, plus both guarded readings."""
    report = PNAT.module_alias_report(text, root, src_path)
    out = dict(report)
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict) and probe.get("reason"):
            reasons.append(probe["reason"])
    out["escape_guard"] = reasons_summary(reasons)
    return out


def audit(root=None, module=None):
    """The R2706 audit plus both rules over every word it publishes."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasDialectMarkerEscapeError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNAT.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasDialectMarkerEscapeError(
            code, str(getattr(exc, "detail", exc)))
    out = dict(report)
    out["tool"] = LABEL
    out["base_tool"] = PNAT.LABEL
    words = list(((report.get("dialect") or {}).get("unnameable") or {})
                 .values())
    out["escape_guard"] = guard_summary(words)
    return out


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasDialectMarkerEscapeError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "escape_guard": {"known_tags": list(KNOWN_TAGS),
                                 "escapable": list(ESCAPABLE),
                                 "words": 0, "dialects": [], "shapes": [],
                                 "refused": {}, "all_legal": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="dialect marker-escape guarded word reading face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--word", default=None,
                        help="read one word under every guard")
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
    except ModuleAliasDialectMarkerEscapeError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc.detail))
        return 4 if exc.code == E_ARGS else 5
    if args.json:
        print(json.dumps(got, indent=2, sort_keys=True))
    else:
        print("%s verdict=%s" % (got["tool"], got["verdict"]))
        print("words=%d dialects=%s shapes=%s refused=%d all_legal=%s"
              % (got["escape_guard"]["words"],
                 got["escape_guard"]["dialects"],
                 got["escape_guard"]["shapes"],
                 len(got["escape_guard"]["refused"]),
                 got["escape_guard"]["all_legal"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
