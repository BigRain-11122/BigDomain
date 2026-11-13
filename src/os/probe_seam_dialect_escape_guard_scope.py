"""Escape-form guard for published words (R2706).

The R2704 face validates the CANONICAL FORM of a counted duplicate and the
canonical sibling list, but it never validates the ESCAPES a sibling label
carries. Measured on that shipped face before this module existed:

  read_word('dialect:1+strict-prefix-of:a\\bc')   (one backslash, then b)
      -> dialect '1', siblings ['abc'], refused None
  read_word('dialect:1+strict-prefix-of:abc')
      -> dialect '1', siblings ['abc'], refused None

so an escape this face cannot publish reads back byte for byte as the plain
label, and

  read_word('dialect:1+strict-prefix-of:ab\\')    (trailing backslash)
      -> dialect '1', siblings ['ab\\'], refused None

so a trailing lone backslash is silently kept as text rather than refused.
A THIRD measurement keeps the legal set honest: the publishing face escapes
the escape, the list separator and the part joiner (in that order), so '\\,'
and '\\\\' AND '\\+' all appear in words it emits while a backslash before a
letter never does.

This face keeps every reading R2685, R2689, R2692, R2698, R2701 and R2704
pinned and adds ONE rule behind the canonical guard: a MARKED word whose
strict-prefix sibling text carries a backslash before anything the publishing
face never escapes, or ends in a lone backslash, is REFUSED naming the form
found. A marker-less legacy word is untouched by the escape rule.

Criteria AC-PNAT1..AC-PNAT6 were pinned in state/queue/tech.md:685 at R2704
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_dialect_canonical_guard_scope as PNAS  # noqa
import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa

LABEL = "os-probe-seam-dialect-escape-guard-scope"
BASE_LABEL = PNAS.LABEL

E_ARGS = "E_PNAT_ARGS"
E_NO_ROOT = "E_PNAT_NO_ROOT"

STATE_OK = PNAS.STATE_OK
STATE_REFUSED = PNAS.STATE_REFUSED
SEAMS_STALE = PNAS.SEAMS_STALE

DIALECT_MARKER = PNAS.DIALECT_MARKER
PART_JOINER = PNAS.PART_JOINER
LIST_JOINER = PNAO.LIST_JOINER
ESCAPE = PNAO.ESCAPE
KNOWN_TAGS = PNAS.KNOWN_TAGS

PREFIX_HEAD = PNAS.PREFIX_HEAD
DUP_HEAD = PNAS.DUP_HEAD

REFUSAL_HEAD = PNAS.REFUSAL_HEAD
REFUSAL_ESCAPE_NOT_PUBLISHED = "escape-not-published"
REFUSAL_TRAILING_ESCAPE = "trailing-escape"

FORM_TRAILING = "trailing"

READING_KEYS = PNAS.READING_KEYS
GUARD_KEYS = PNAS.GUARD_KEYS

# The three characters the publishing face ever puts a backslash in front of,
# in the order escape_label applies them: itself, the list separator, the part
# joiner. Derived from that writer rather than typed, so the rule cannot drift
# away from what the face can actually emit.
ESCAPABLE = (ESCAPE, LIST_JOINER, PART_JOINER)

marker_of_word = PNAS.marker_of_word
marker_count = PNAS.marker_count
has_marker = PNAS.has_marker
strip_marker = PNAS.strip_marker
word_parts = PNAS.word_parts
body_parts_of = PNAS.body_parts_of
part_head = PNAS.part_head
ack_unnameable = PNAS.ack_unnameable
ack_words = PNAS.ack_words
ack_legacy_words = PNAS.ack_legacy_words
ack_unnameable_labels = PNAS.ack_unnameable_labels
labels_of_reason = PNAS.labels_of_reason
prefix_siblings_of_part = PNAS.prefix_siblings_of_part
duplicate_count_of_part = PNAS.duplicate_count_of_part
refusal_of = PNAS.refusal_of
refusal_word_of = PNAS.refusal_word_of
escape_label = PNAO.escape_label
unescape_label = PNAO.unescape_label
split_parts_escaped = PNAO.split_parts_escaped


class ModuleAliasDialectEscapeGuardError(Exception):
    """Carries the face own code so a caller never guesses the failure."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def ascii_form_of_char(char):
    """One character named in ASCII only, never as a raw foreign byte."""
    if not isinstance(char, str) or not char:
        return FORM_TRAILING
    code = ord(char)
    if 32 <= code <= 126 and char not in (ESCAPE,):
        return char
    return "U+%04X" % (code,)


def legal_escape_at(text, index):
    """True only when text[index] introduces one escape this face publishes."""
    if index + 1 >= len(text):
        return False
    return text[index + 1] in ESCAPABLE


def escape_form_of_text(text):
    """(code, form) for the first illegal escape in RAW text, else None.

    The text must arrive with its escapes INTACT: this walk consumes escaped
    pairs, so an escaped backslash can never be read as the start of a second
    escape and an escape at the very end is named rather than dropped.
    """
    if not isinstance(text, str):
        return None
    index = 0
    while index < len(text):
        char = text[index]
        if char != ESCAPE:
            index += 1
            continue
        if index + 1 >= len(text):
            return (REFUSAL_TRAILING_ESCAPE, FORM_TRAILING)
        if not legal_escape_at(text, index):
            return (REFUSAL_ESCAPE_NOT_PUBLISHED,
                    ascii_form_of_char(text[index + 1]))
        index += 2
    return None


def sibling_texts_of_part(part):
    """The RAW sibling bodies a strict-prefix part carries, escapes intact."""
    if not isinstance(part, str) or not part.startswith(PREFIX_HEAD):
        return []
    return [part[len(PREFIX_HEAD):]]


def escape_refusal(word):
    """None for a word whose escapes this face publishes, else its refusal.

    Only MARKED words are checked, and only their strict-prefix sibling text:
    a legacy word is handed back to the R2704 law byte for byte, because the
    escape rule is a law about this face own pedigree rather than about
    legacy text.
    """
    body = body_parts_of(word)
    if body is None:
        return None
    for part in body:
        for text in sibling_texts_of_part(part):
            found = escape_form_of_text(text)
            if found is not None:
                code, form = found
                return refusal_of(code, form, word, len(body))
    return None


def escape_state_of_word(word):
    """'legal' for a word this rule accepts, else the refusal code or None."""
    got = read_word(word)
    if got.get("refused") is not None:
        return None
    if body_parts_of(word) is None:
        return None
    return "legal"


def shape_of_word(word):
    """The shape of a legal marked word, None for a legal legacy word."""
    if read_word(word).get("refused") is not None:
        return None
    return PNAS.shape_of_word(word)


def read_word(word):
    """The guarded reading: R2704's own answer OR a named escape refusal.

    A refusal reports dialect None, body None, siblings None and duplicate
    None for the same reason R2704 does - handing back the body verbatim is
    what makes a refusal indistinguishable from a reading - so a refused
    escape can never be mistaken for a tag-1 word with siblings.
    """
    base = PNAS.read_word(word)
    if base.get("refused") is not None:
        return base
    refusal = escape_refusal(word)
    if refusal is not None:
        out = {"word": word, "dialect": None,
               "markers": marker_count(word),
               "body": None, "siblings": None, "duplicate": None}
        out.update(refusal)
        return out
    return base


def base_reading(word):
    """R2704's reading exactly, escape rule aside."""
    return PNAS.read_word(word)


def is_legal_reading(word):
    """True only when the word is read rather than refused by any guard."""
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
    """The R2704 entry, with its published words escape-guarded as well."""
    got = PNAS.module_alias_entry(name, text, scope, line, tables, root,
                                  src_path)
    out = dict(got)
    labels = labels_of_reason(got.get("reason"))
    out["escape_guard"] = guard_summary(ack_words(labels).values())
    out["ack_readings"] = ack_readings(labels)
    return out


def module_alias_report(text, root=None, src_path=None):
    """The R2704 report carried through, plus its escape-guarded reading."""
    report = PNAS.module_alias_report(text, root, src_path)
    out = dict(report)
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict) and probe.get("reason"):
            reasons.append(probe["reason"])
    out["escape_guard"] = reasons_summary(reasons)
    return out


def audit(root=None, module=None):
    """The R2704 audit plus the escape guard over every word it publishes."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasDialectEscapeGuardError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNAS.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasDialectEscapeGuardError(
            code, str(getattr(exc, "detail", exc)))
    out = dict(report)
    out["tool"] = LABEL
    out["base_tool"] = PNAS.LABEL
    words = list(((report.get("dialect") or {}).get("unnameable") or {})
                 .values())
    out["escape_guard"] = guard_summary(words)
    return out


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasDialectEscapeGuardError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "escape_guard": {"known_tags": list(KNOWN_TAGS),
                                 "escapable": list(ESCAPABLE),
                                 "words": 0, "dialects": [], "shapes": [],
                                 "refused": {}, "all_legal": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="dialect escape-form-guarded word reading face")
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
    except ModuleAliasDialectEscapeGuardError as exc:
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
