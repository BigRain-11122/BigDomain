"""Shape-guarded reading face for published words (R2701).

The R2698 face validates the DIALECT TAG a word's first part names, but it
never validates the SHAPE of the body the tag introduces. Measured on that
shipped face before this module existed:

  read_word('dialect:1')
      -> {'dialect': '1', 'markers': 1, 'body': 'dialect:1',
          'siblings': None, 'duplicate': None, 'refused': None}

  read_word('dialect:1+duplicate:2')
      -> {'dialect': '1', 'markers': 1, 'body': 'duplicate:2',
          'siblings': None, 'duplicate': 2, 'refused': None}

so a bare marker is read back as its own body and the body of an empty body
part ('dialect:1+') is the empty string - both are strings this face never
publishes, yet both were accepted as its own legal words. A THIRD measured
fact corrects the R2698 note: a duplicate-only body IS published by this face
for the label set ['a','a'], which reads 'dialect:1+duplicate:2', so the shape
rule below must keep it legal rather than refuse it.

This face keeps every reading R2685, R2689, R2692 and R2698 pinned and adds
ONE rule behind the tag guard: a MARKED word whose body is absent, empty, or
not one of the shapes this face publishes - 'strict-prefix-of:<siblings>', a
counted 'duplicate:<n>' with n >= 2, or the pair in that order - is REFUSED
naming the shape found. A marker-less legacy word is untouched by the shape
rule, so a bare 'duplicate:2' stays a legal legacy word.

Criteria AC-PNAR1..AC-PNAR6 were pinned in state/queue/tech.md:683 at R2698
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_dialect_tag_guard_scope as PNAQ  # noqa
import probe_seam_unnameable_dialect_marker_scope as PNAP  # noqa

LABEL = "os-probe-seam-dialect-shape-guard-scope"
BASE_LABEL = PNAQ.LABEL

E_ARGS = "E_PNAR_ARGS"
E_NO_ROOT = "E_PNAR_NO_ROOT"

STATE_OK = PNAQ.STATE_OK
STATE_REFUSED = PNAQ.STATE_REFUSED
SEAMS_STALE = PNAQ.SEAMS_STALE

DIALECT_MARKER = PNAQ.DIALECT_MARKER
PART_JOINER = PNAQ.PART_JOINER
KNOWN_TAGS = PNAQ.KNOWN_TAGS

PREFIX_HEAD = "strict-prefix-of:"
DUP_HEAD = "duplicate:"
PAIR_SHAPE = PREFIX_HEAD + "*+" + DUP_HEAD + "*"

REFUSAL_HEAD = "refused:"
REFUSAL_NO_BODY = "no-body"
REFUSAL_EMPTY_BODY = "empty-body"
REFUSAL_PART_COUNT = "part-count"
REFUSAL_NOT_PUBLISHED = "not-published"
REFUSAL_DUP_NOT_COUNTED = "duplicate-not-counted"
REFUSAL_SIBLINGS_EMPTY = "siblings-empty"
REFUSAL_PART_ORDER = "part-order"

READING_KEYS = PNAQ.READING_KEYS
GUARD_KEYS = ("refused", "shape", "tag", "count", "refusal_word")

marker_of_word = PNAQ.marker_of_word
marker_count = PNAQ.marker_count
has_marker = PNAP.has_marker
strip_marker = PNAQ.strip_marker
word_parts = PNAQ.word_parts
ack_unnameable = PNAQ.ack_unnameable
ack_words = PNAQ.ack_words
ack_legacy_words = PNAQ.ack_legacy_words
ack_unnameable_labels = PNAQ.ack_unnameable_labels
labels_of_reason = PNAQ.labels_of_reason


class ModuleAliasDialectShapeGuardError(Exception):
    """Carries the face own code so a caller never guesses the failure."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, detail or code)
        self.code = code
        self.detail = detail


def body_parts_of(word):
    """The body parts of a MARKED word, escapes intact; None for a legacy one.

    The marker is only ever the FIRST part, so a word that merely carries the
    marker text later on is legacy for this rule too - exactly as R2692 read
    it - and is therefore never shape-checked.
    """
    if not isinstance(word, str):
        return None
    parts = word_parts(word)
    if not parts or parts[0] != DIALECT_MARKER:
        return None
    return parts[1:]


def part_head(part):
    """The head token a body part names, used to say WHAT shape was found."""
    if not isinstance(part, str):
        return ""
    if ":" in part:
        return part.split(":", 1)[0]
    return part


def prefix_siblings_of_part(part):
    """The siblings a strict-prefix part names, or None when it names none."""
    if not isinstance(part, str) or not part.startswith(PREFIX_HEAD):
        return None
    return PNAP.split_escaped(part[len(PREFIX_HEAD):])


def duplicate_count_of_part(part):
    """(is_counted, count) for a counted duplicate part, else (False, None).

    A count is only counted when it is a bare integer of at least two, which
    is the only form the publishing face ever writes. int() is reached only
    after a form it can read: measured at R2704, a superscript two is
    isdigit() True and int() raises ValueError, so the shipped face CRASHED
    where it owed a refusal. Both int() reaches of that defect family are
    repaired at their birth sites in the R2704 window (this one and the legacy
    parser in probe_seam_unnameable_part_joiner_escaped_scope).
    """
    if not isinstance(part, str) or not part.startswith(DUP_HEAD):
        return (False, None)
    tail = part[len(DUP_HEAD):]
    if not tail.isdigit():
        return (False, None)
    try:
        count = int(tail)
    except ValueError:
        return (False, None)
    if count >= 2:
        return (True, count)
    return (False, None)


def refusal_word_of(code, detail):
    """The machine-readable refusal word, derived from code and detail."""
    return REFUSAL_HEAD + code + ":" + str(detail)


def refusal_of(code, detail, word=None, count=None):
    """One named shape refusal, carrying the tag it saw and the part count."""
    return {"refused": code,
            "shape": str(detail),
            "tag": PNAQ.declared_tag(word) if word is not None else None,
            "count": count,
            "refusal_word": refusal_word_of(code, detail)}


def shape_refusal(word):
    """None for a shape this face publishes, else the refusal it earns.

    Only MARKED words are shape-checked: a legacy word is handed back to the
    R2692 law byte for byte, because the shape rule is a law about this
    face own pedigree rather than about legacy text.
    """
    body = body_parts_of(word)
    if body is None:
        return None
    if not body:
        return refusal_of(REFUSAL_NO_BODY, "marker-only", word, 0)
    if any(part == "" for part in body):
        return refusal_of(REFUSAL_EMPTY_BODY, "empty-part", word, len(body))
    if len(body) > 2:
        return refusal_of(REFUSAL_PART_COUNT, len(body), word, len(body))
    for index, part in enumerate(body):
        siblings = prefix_siblings_of_part(part)
        if siblings is not None:
            if index != 0:
                return refusal_of(REFUSAL_PART_ORDER, part_head(part), word,
                                  len(body))
            if not part[len(PREFIX_HEAD):]:
                return refusal_of(REFUSAL_SIBLINGS_EMPTY, "none", word,
                                  len(body))
            if any(item == "" for item in siblings):
                return refusal_of(REFUSAL_SIBLINGS_EMPTY, "empty-sibling",
                                  word, len(body))
            continue
        counted, _count = duplicate_count_of_part(part)
        if part.startswith(DUP_HEAD):
            if not counted:
                return refusal_of(REFUSAL_DUP_NOT_COUNTED,
                                  part[len(DUP_HEAD):], word, len(body))
            if index != len(body) - 1:
                return refusal_of(REFUSAL_PART_ORDER, part_head(part), word,
                                  len(body))
            continue
        return refusal_of(REFUSAL_NOT_PUBLISHED, part_head(part), word,
                          len(body))
    return None


def shape_of_word(word):
    """The shape a legal MARKED word carries, else None.

    Legacy words report None because they carry no pedigree; a refused word
    reports None because a refusal is never a shape reading.
    """
    if shape_refusal(word) is not None:
        return None
    body = body_parts_of(word)
    if not body:
        return None
    kinds = []
    for part in body:
        if prefix_siblings_of_part(part) is not None:
            kinds.append("strict-prefix-of")
        elif duplicate_count_of_part(part)[0]:
            kinds.append("duplicate")
    return "+".join(kinds) if kinds else None


def read_word(word):
    """The guarded reading: R2698's own answer OR a named shape refusal.

    A refusal reports dialect None, body None, siblings None and duplicate
    None for the same reason R2698 does - handing back the body verbatim is
    what makes a refusal indistinguishable from a reading - so a refused
    shape can never be mistaken for a tag-1 word.
    """
    base = PNAQ.read_word(word)
    if base.get("refused") is not None:
        return base
    refusal = shape_refusal(word)
    if refusal is not None:
        out = {"word": word, "dialect": None,
               "markers": marker_count(word),
               "body": None, "siblings": None, "duplicate": None}
        out.update(refusal)
        return out
    return base


def base_reading(word):
    """R2698's reading exactly, shape rule aside."""
    return PNAQ.read_word(word)


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
    """The R2698 entry, with its published words shape-guarded as well."""
    got = PNAQ.module_alias_entry(name, text, scope, line, tables, root,
                                  src_path)
    out = dict(got)
    labels = labels_of_reason(got.get("reason"))
    out["shape_guard"] = guard_summary(ack_words(labels).values())
    out["ack_readings"] = ack_readings(labels)
    return out


def module_alias_report(text, root=None, src_path=None):
    """The R2698 report carried through, plus its shape-guarded reading."""
    report = PNAQ.module_alias_report(text, root, src_path)
    out = dict(report)
    reasons = []
    for probe in report.get("probes") or []:
        if isinstance(probe, dict) and probe.get("reason"):
            reasons.append(probe["reason"])
    out["shape_guard"] = reasons_summary(reasons)
    return out


def audit(root=None, module=None):
    """The R2698 audit plus the shape guard over every word it publishes."""
    root_path = BASE if root is None else root
    if not os.path.isdir(root_path):
        raise ModuleAliasDialectShapeGuardError(
            E_NO_ROOT, "not a directory: %s" % root_path)
    try:
        report = PNAQ.audit(root_path, module)
    except Exception as exc:
        code = getattr(exc, "code", None)
        if not code:
            raise
        raise ModuleAliasDialectShapeGuardError(
            code, str(getattr(exc, "detail", exc)))
    out = dict(report)
    out["tool"] = LABEL
    out["base_tool"] = PNAQ.LABEL
    words = list(((report.get("dialect") or {}).get("unnameable") or {})
                 .values())
    out["shape_guard"] = guard_summary(words)
    return out


def reading(root=None, module=None):
    """The audit, never raising: a refusal is published rather than lost."""
    try:
        return audit(root, module)
    except ModuleAliasDialectShapeGuardError as exc:
        return {"tool": LABEL, "verdict": SEAMS_STALE, "seams": [],
                "probes": [],
                "shape_guard": {"known_tags": list(KNOWN_TAGS), "words": 0,
                                "dialects": [], "shapes": [], "refused": {},
                                "all_legal": True},
                "error": {"code": exc.code, "detail": exc.detail}}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="dialect-shape-guarded word reading face")
    parser.add_argument("--root", default=BASE)
    parser.add_argument("--module", default=None)
    parser.add_argument("--word", default=None,
                        help="read one word under both guards")
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
    except ModuleAliasDialectShapeGuardError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc.detail))
        return 4 if exc.code == E_ARGS else 5
    if args.json:
        print(json.dumps(got, indent=2, sort_keys=True))
    else:
        print("%s verdict=%s" % (got["tool"], got["verdict"]))
        print("words=%d dialects=%s shapes=%s refused=%d all_legal=%s"
              % (got["shape_guard"]["words"],
                 got["shape_guard"]["dialects"],
                 got["shape_guard"]["shapes"],
                 len(got["shape_guard"]["refused"]),
                 got["shape_guard"]["all_legal"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
