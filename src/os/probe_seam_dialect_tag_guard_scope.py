"""Dialect-tag-guarded reading face for published words (R2698).

The R2692 face stamps `dialect:1` as the FIRST part of every word it publishes
and reads that marker back from the parts, but it does not VALIDATE the tag.
Measured on the shipped face before this module existed:

  read_word('dialect:2+strict-prefix-of:ab')
      -> {'dialect': None, 'markers': 0,
          'body': 'dialect:2+strict-prefix-of:ab',
          'siblings': ['ab'], 'duplicate': None}

so a word published by a FUTURE dialect is silently mis-typed as a LEGACY word
and its body is then parsed by the legacy law, which is exactly the confusion
the marker was introduced to end. The second measured shape is
`read_word('dialect:1+dialect:1+strict-prefix-of:ab')` -> dialect '1' with
markers=2, i.e. a string this face would never publish is accepted as its own.

This face keeps every reading R2685, R2689 and R2692 pinned and adds ONE rule
in front of them: a word whose FIRST part names a dialect tag this face does
not know is REFUSED naming that tag, and a word carrying more than one dialect
part is REFUSED naming the count. A refused word reports NO body, NO siblings
and NO duplicate, so a refusal can never be mistaken for a legacy reading; a
marker-less legacy word still reads exactly as R2692 read it.

Criteria AC-PNAQ1..AC-PNAQ6 were pinned in state/queue/tech.md:682 at R2692
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_unnameable_dialect_marker_scope as PNAP  # noqa

LABEL = "os-probe-seam-dialect-tag-guard-scope"
BASE_LABEL = PNAP.LABEL

E_ARGS = "E_PNAQ_ARGS"
E_NO_ROOT = "E_PNAQ_NO_ROOT"

STATE_OK = PNAP.STATE_OK
STATE_REFUSED = PNAP.STATE_REFUSED
SEAMS_STALE = PNAP.SEAMS_STALE

DIALECT_HEAD = PNAP.DIALECT_HEAD
DIALECT_MARKER = PNAP.DIALECT_MARKER
PART_JOINER = PNAP.PART_JOINER
KNOWN_TAGS = ("1",)

REFUSAL_HEAD = "refused:"
REFUSAL_UNKNOWN = "unknown-dialect"
REFUSAL_MULTIPLE = "multiple-dialect-parts"

READING_KEYS = ("dialect", "markers", "body", "siblings", "duplicate")
GUARD_KEYS = ("refused", "tag", "count", "refusal_word")

word_parts = PNAP.word_parts
marker_of_word = PNAP.marker_of_word
marker_count = PNAP.marker_count
strip_marker = PNAP.strip_marker
with_marker = PNAP.with_marker
ack_unnameable = PNAP.ack_unnameable
ack_legacy_words = PNAP.ack_legacy_words
ack_unnameable_labels = PNAP.ack_unnameable_labels
ack_fully_named = PNAP.ack_fully_named
parse_strict_prefix_word = PNAP.parse_strict_prefix_word
parse_duplicate_from_word = PNAP.parse_duplicate_from_word
parse_part_word = PNAP.parse_part_word
labels_of_reason = PNAP.labels_of_reason


class ModuleAliasDialectTagGuardError(Exception):
    """Carries the face own code so a caller never guesses the failure."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def dialect_part_indexes(word):
    """[] for a legacy word, else the indexes of every dialect-naming part.

    A part NAMES a dialect when it starts with the dialect head, so an unknown
    tag is visible as a dialect part rather than hiding as body text. Position
    is reported, not assumed: only the FIRST part is a claim of pedigree.
    """
    if not isinstance(word, str):
        return []
    parts = word_parts(word)
    return [index for index, part in enumerate(parts)
            if part.startswith(DIALECT_HEAD)]


def dialect_tag_at(word, index):
    """The tag a part at that index names, with no validation applied."""
    if not isinstance(word, str):
        return None
    parts = word_parts(word)
    if index < 0 or index >= len(parts):
        return None
    return parts[index][len(DIALECT_HEAD):]


def declared_tag(word):
    """The tag the FIRST part claims, or None when the first part claims none."""
    indexes = dialect_part_indexes(word)
    if not indexes or indexes[0] != 0:
        return None
    return dialect_tag_at(word, 0)


def unknown_tag_of_word(word):
    """The unvalidated tag when it is not a tag this face knows, else None."""
    tag = declared_tag(word)
    if tag is None or tag in KNOWN_TAGS:
        return None
    return tag


def refusal_word_of(code, detail):
    """The machine-readable refusal word, derived from the code and its detail."""
    return REFUSAL_HEAD + code + ":" + str(detail)


def refusal_of_word(word):
    """None for a readable word, else the refusal it earns.

    More than one dialect part is refused FIRST, because such a string is not
    a word this face could ever have published whatever its tags say.
    """
    indexes = dialect_part_indexes(word)
    if len(indexes) > 1:
        return {"refused": REFUSAL_MULTIPLE,
                "count": len(indexes),
                "tag": dialect_tag_at(word, 0) if indexes[0] == 0 else None,
                "refusal_word": refusal_word_of(REFUSAL_MULTIPLE,
                                                len(indexes))}
    tag = unknown_tag_of_word(word)
    if tag is not None:
        return {"refused": REFUSAL_UNKNOWN,
                "tag": tag,
                "count": len(indexes),
                "refusal_word": refusal_word_of(REFUSAL_UNKNOWN, tag)}
    return None


def read_word(word):
    """The guarded reading: EITHER R2692's reading OR a named refusal.

    A refused word reports dialect None, body None, siblings None and
    duplicate None on purpose - handing back the body verbatim is precisely
    the mis-typing this face exists to stop - so a refusal is never a legacy
    reading with extra keys.
    """
    refusal = refusal_of_word(word)
    if refusal is not None:
        out = {"word": word, "dialect": None,
               "markers": marker_count(word),
               "body": None, "siblings": None, "duplicate": None}
        out.update(refusal)
        return out
    out = {"word": word}
    out.update(PNAP.read_word(word))
    out.update({"refused": None, "tag": declared_tag(word),
                "count": len(dialect_part_indexes(word)),
                "refusal_word": None})
    return out


def base_reading(word):
    """R2692's reading carried unchanged, refusal rule aside."""
    return PNAP.read_word(word)


def is_legal_reading(word):
    """True only when the word is read rather than refused."""
    return refusal_of_word(word) is None


def validated_tag(word):
    """The tag of a legal marked word, None for a legal legacy word."""
    if refusal_of_word(word) is not None:
        return None
    return declared_tag(word)


def tag_of_ack_word(word):
    """The tag this face own published word must read back, or None."""
    got = read_word(word)
    return got["dialect"]


def read_words(words):
    """{word: guarded reading} over a collection, order kept by sorted key."""
    out = {}
    for word in sorted(set(words or [])):
        out[word] = read_word(word)
    return out


def refusals_of(words):
    """{word: refusal_word} over the words that are refused."""
    out = {}
    for word in sorted(set(words or [])):
        refusal = refusal_of_word(word)
        if refusal is not None:
            out[word] = refusal["refusal_word"]
    return out


def ack_words(labels):
    """{label: word} exactly as R2692 publishes it, this face adds no byte."""
    return ack_unnameable(labels)


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
    """The R2692 entry, with its published words guarded as well."""
    got = PNAP.module_alias_entry(name, text, scope, line, tables, root,
                                  src_path)
    out = dict(got)
    labels = labels_of_reason(got.get("reason"))
    out["tag_guard"] = guard_summary(ack_words(labels).values())
    out["ack_readings"] = ack_readings(labels)
    return out


def module_alias_report(text, root=None, src_path=None):
    """The R2692 report carried through, plus its guarded word reading."""
    report = PNAP.module_alias_report(text, root, src_path)
    out = dict(report)
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict) and probe.get("reason"):
            reasons.append(probe["reason"])
    out["tag_guard"] = reasons_summary(reasons)
    return out


def audit(root=None, module=None):
    """The R2692 audit plus the guard over every word it publishes."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasDialectTagGuardError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNAP.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasDialectTagGuardError(
            code, str(getattr(exc, "detail", exc)))
    out = dict(report)
    out["tool"] = LABEL
    out["base_tool"] = PNAP.LABEL
    words = list(((report.get("dialect") or {}).get("unnameable") or {})
                 .values())
    out["tag_guard"] = guard_summary(words)
    return out


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasDialectTagGuardError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "tag_guard": {"known_tags": list(KNOWN_TAGS), "words": 0,
                              "dialects": [], "refused": {},
                              "all_legal": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="dialect-tag-guarded word reading face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--word", default=None,
                        help="read one word under the guard")
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
    except ModuleAliasDialectTagGuardError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc.detail))
        return 4 if exc.code == E_ARGS else 5
    if args.json:
        print(json.dumps(got, indent=2, sort_keys=True))
    else:
        print("%s verdict=%s" % (got["tool"], got["verdict"]))
        print("words=%d dialects=%s refused=%d all_legal=%s"
              % (got["tag_guard"]["words"],
                 got["tag_guard"]["dialects"],
                 len(got["tag_guard"]["refused"]),
                 got["tag_guard"]["all_legal"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
