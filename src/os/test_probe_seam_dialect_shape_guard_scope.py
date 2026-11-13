"""AC-PNAR1..AC-PNAR6 suite for the dialect-shape guard face (R2701).

Criteria were pinned in state/queue/tech.md:683 at R2698 BEFORE this code
existed. Every fixture lives in memory; no shipped source file is written.
Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_dialect_shape_guard_scope as PNAR  # noqa
import probe_seam_dialect_tag_guard_scope as PNAQ  # noqa
import probe_seam_unnameable_dialect_marker_scope as PNAP  # noqa
import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "probe_seam_dialect_shape_guard_scope.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-dialect-shape-guard-scope",'
WIRED_SUITE = '"test_probe_seam_dialect_shape_guard_scope.py"'

MARKER_ONLY = "dialect:1"
EMPTY_BODY = "dialect:1+"
BARE_DUP = "dialect:1+duplicate:2"
BARE_PREFIX = "dialect:1+strict-prefix-of:ab"
PAIR = "dialect:1+strict-prefix-of:ab+duplicate:2"
NOT_A_SHAPE = "dialect:1+garbage"
DUP_ONE = "dialect:1+duplicate:1"
DUP_TEXT = "dialect:1+duplicate:x"
PREFIX_EMPTY = "dialect:1+strict-prefix-of:"
PREFIX_EMPTY_SIBLING = "dialect:1+strict-prefix-of:,ab"
ORDER_SWAPPED = "dialect:1+duplicate:2+strict-prefix-of:ab"
THREE_PARTS = "dialect:1+strict-prefix-of:ab+duplicate:2+duplicate:3"
LEGACY_DUP = "duplicate:2"
LEGACY_PAIR = "strict-prefix-of:ab+duplicate:2"
FUTURE_WORD = "dialect:2+strict-prefix-of:ab"
DOUBLED = "dialect:1+dialect:1+strict-prefix-of:ab"

# every fixture the R2685, R2689, R2692 and R2698 suites proved, reused
FIXTURES = [
    ["a", "ab,ac"],
    ["a", "ab", "ac"],
    ["x", "xy"],
    ["a", "a"],
    ["a", "ab", "a"],
    ["a", "ab", "ac", "ad"],
    ["p", "pq,pr", "ps"],
    ["a", "ab+duplicate:2"],
    ["a", "ab\\,ac"],
    ["a", "ab", "ac", "a"],
]

LIVE_MODULES = [
    "probe_seam_dialect_shape_guard_scope.py",
    "probe_seam_dialect_tag_guard_scope.py",
    "probe_seam_unnameable_dialect_marker_scope.py",
    "probe_seam_unnameable_part_joiner_escaped_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
    "branch_elif_with_while_match_while_else_nested_match_ordinal_"
    "unique_prefix_unnameable_siblings_escaped_scope.py",
]


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()[:16]


def ac_pnar1():
    """A marker with no body part is refused naming that state."""
    got = PNAR.read_word(MARKER_ONLY)
    ok = check(got["refused"] == "no-body",
               "AC-PNAR1 a bare marker is refused as no-body (%r)"
               % (got["refused"],))
    ok = check(got["refusal_word"] == "refused:no-body:marker-only",
               "AC-PNAR1 the refusal carries its own word (%r)"
               % (got["refusal_word"],)) and ok
    ok = check(got["dialect"] is None and got["body"] is None,
               "AC-PNAR1 it is never read back as a tag-1 word with the"
               " marker as its body (%r / %r)"
               % (got["dialect"], got["body"])) and ok
    ok = check(got["siblings"] is None and got["duplicate"] is None,
               "AC-PNAR1 and it states NO readings (%r / %r)"
               % (got["siblings"], got["duplicate"])) and ok
    base = PNAR.base_reading(MARKER_ONLY)
    ok = check(base["dialect"] == "1" and base["body"] == MARKER_ONLY
               and base["refused"] is None,
               "AC-PNAR1 the R2698 reading of the same word WAS the accepted"
               " marker-as-body this face refuses (%r)" % (base,)) and ok
    ok = check(PNAR.is_legal_reading(MARKER_ONLY) is False,
               "AC-PNAR1 the word is not a legal reading any more") and ok
    empty = PNAR.read_word(EMPTY_BODY)
    ok = check(empty["refused"] == "empty-body"
               and empty["refusal_word"] == "refused:empty-body:empty-part",
               "AC-PNAR1 a marked word with an EMPTY body part is refused by"
               " its own word (%r)" % (empty["refusal_word"],)) and ok
    ok = check(empty["body"] is None and empty["dialect"] is None,
               "AC-PNAR1 and it is not handed back as an empty body") and ok
    for word in (FUTURE_WORD, DOUBLED):
        got = PNAR.read_word(word)
        ok = check(got["refused"] in ("unknown-dialect",
                                      "multiple-dialect-parts"),
                   "AC-PNAR1 the tag guard still runs FIRST on %r (%r)"
                   % (word, got["refused"])) and ok
    return ok


def ac_pnar2():
    """A tag-1 body outside the published shapes is refused by its shape."""
    cases = [
        (NOT_A_SHAPE, "not-published", "garbage"),
        (DUP_ONE, "duplicate-not-counted", "1"),
        (DUP_TEXT, "duplicate-not-counted", "x"),
        (PREFIX_EMPTY, "siblings-empty", "none"),
        (PREFIX_EMPTY_SIBLING, "siblings-empty", "empty-sibling"),
        (ORDER_SWAPPED, "part-order", "duplicate"),
        (THREE_PARTS, "part-count", "3"),
    ]
    ok = True
    for word, code, shape in cases:
        got = PNAR.read_word(word)
        ok = check(got["refused"] == code,
                   "AC-PNAR2 %r is refused as %s (%r)"
                   % (word, code, got["refused"])) and ok
        ok = check(got["shape"] == shape,
                   "AC-PNAR2 and it NAMES the shape found (%r)"
                   % (got["shape"],)) and ok
        ok = check(got["refusal_word"] == "refused:%s:%s" % (code, shape),
                   "AC-PNAR2 its own word is derived from code and shape"
                   " (%r)" % (got["refusal_word"],)) and ok
        ok = check(got["dialect"] is None and got["body"] is None,
                   "AC-PNAR2 it is refused rather than read (%r / %r)"
                   % (got["dialect"], got["body"])) and ok
        base = PNAR.base_reading(word)
        ok = check(base["refused"] is None and base["dialect"] == "1",
                   "AC-PNAR2 the R2698 reading of the same word ACCEPTED it as"
                   " tag 1 (%r)" % (base["dialect"],)) and ok
    ok = check(PNAR.shape_of_word(NOT_A_SHAPE) is None,
               "AC-PNAR2 a refused word carries no shape") and ok
    ok = check(PNAR.refusals_of([NOT_A_SHAPE, LEGACY_DUP])
               == {NOT_A_SHAPE: "refused:not-published:garbage"},
               "AC-PNAR2 the refusal map names ONLY the refused word") and ok
    return ok


def ac_pnar3():
    """Every word this face publishes still reads back tag 1, intact."""
    ok = True
    for labels in FIXTURES:
        words = PNAR.ack_words(labels)
        ok = check(PNAR.ack_all_legal(labels) is True,
                   "AC-PNAR3 fixture %s publishes only legal words"
                   % (labels,)) and ok
        for label, word in words.items():
            got = PNAR.read_word(word)
            ok = check(got["dialect"] == "1" and got["refused"] is None,
                       "AC-PNAR3 %r reads back tag 1 (%r)"
                       % (word, got["dialect"])) and ok
            ok = check(got["body"] == PNAP.strip_marker(word),
                       "AC-PNAR3 its body is the stripped word (%r)"
                       % (got["body"],)) and ok
            theirs = PNAQ.read_word(word)
            ok = check(all(got[key] == theirs[key]
                           for key in PNAR.READING_KEYS),
                       "AC-PNAR3 every reading key rides R2698 (%s)"
                       % (word,)) and ok
            ok = check(PNAR.shape_of_word(word) is not None,
                       "AC-PNAR3 the word names a published shape (%r)"
                       % (PNAR.shape_of_word(word),)) and ok
    ok = check(PNAR.shape_of_word(BARE_PREFIX) == "strict-prefix-of",
               "AC-PNAR3 a bare prefix body is a published shape") and ok
    ok = check(PNAR.shape_of_word(BARE_DUP) == "duplicate",
               "AC-PNAR3 a bare counted duplicate body is a published shape"
               " (measured for ['a','a'], correcting the R2698 note)") and ok
    ok = check(PNAR.shape_of_word(PAIR) == "strict-prefix-of+duplicate",
               "AC-PNAR3 the pair body is a published shape") and ok
    ok = check(PNAR.ack_all_legal(["a", "a"]) is True,
               "AC-PNAR3 the duplicate-only label set publishes a legal word"
               " (['a','a'] -> %r)" % (PNAR.ack_words(["a", "a"]),)) and ok
    return ok


def ac_pnar4():
    """Every earlier reading rides, plus one bounded live leg on BOTH faces."""
    ok = True
    seen = 0
    for index, labels in enumerate(FIXTURES):
        ok = check(PNAR.ack_legacy_words(labels) == PNAO.ack_unnameable(labels),
                   "AC-PNAR4 R2689 fixture %d rides byte for byte"
                   % (index,)) and ok
        ok = check(PNAR.ack_words(labels) == PNAP.ack_unnameable(labels),
                   "AC-PNAR4 R2692 fixture %d rides byte for byte"
                   % (index,)) and ok
        for word in sorted(set(PNAP.ack_unnameable(labels).values())):
            seen += 1
            mine = PNAR.read_word(word)
            theirs = PNAQ.read_word(word)
            ok = check(all(mine[key] == theirs[key]
                           for key in PNAR.READING_KEYS),
                       "AC-PNAR4 R2698 word %r rides on every reading key"
                       % (word,)) and ok
    ok = check(seen >= 9,
               "AC-PNAR4 the published face covered %d distinct words"
               % (seen,)) and ok
    ok = check(PNAR.base_reading(LEGACY_PAIR) == PNAQ.read_word(LEGACY_PAIR),
               "AC-PNAR4 the base reading IS the R2698 reading") and ok
    for index, labels in enumerate([["a", "ab,ac"], ["a", "ab", "ac"],
                                    ["x", "xy"], ["a", "a"],
                                    ["a", "ab", "ac", "ad"],
                                    ["p", "pq,pr", "ps"]]):
        ok = check(PNAR.ack_legacy_words(labels)
                   == PNAL.ack_unnameable(labels),
                   "AC-PNAR4 R2685 fixture %d rides unchanged"
                   % (index,)) and ok

    before = {}
    for name in LIVE_MODULES:
        path = os.path.join(BASE, name)
        if os.path.isfile(path):
            before[name] = digest(path)
    loops = 0
    unreadable = 0
    disagreements = 0
    for name, first_digest in sorted(before.items()):
        path = os.path.join(BASE, name)
        text = read_bytes(path).decode("utf-8", "replace")
        for build in (PNAQ.module_alias_report, PNAR.module_alias_report):
            try:
                report = build(text, BASE)
            except Exception:
                unreadable += 1
                continue
            loops += len(report.get("loops") or [])
        if digest(path) != first_digest:
            disagreements += 1
    ok = check(loops > 0 and unreadable == 0 and disagreements == 0,
               "AC-PNAR4 a bounded live leg is read-only (modules=%d loops=%d"
               " unreadable=%d disagree=%d)"
               % (len(before), loops, unreadable, disagreements)) and ok
    mine = PNAR.read_word(LEGACY_PAIR)
    theirs = PNAQ.read_word(LEGACY_PAIR)
    ok = check(all(mine[key] == theirs[key] for key in PNAR.READING_KEYS),
               "AC-PNAR4 the SAME legacy fixture reads the same on BOTH"
               " readers") and ok
    base = PNAQ.read_word(MARKER_ONLY)
    ok = check(PNAR.read_word(MARKER_ONLY)["refused"] is not None
               and base["refused"] is None and base["body"] == MARKER_ONLY,
               "AC-PNAR4 the same marked fixture is REFUSED here and was read"
               " as a tag-1 body there (%r)" % (base,)) and ok
    return ok


def ac_pnar5():
    """A marker-less legacy word is untouched by the shape rule."""
    ok = True
    for word in (LEGACY_DUP, LEGACY_PAIR, "strict-prefix-of:ab",
                 "strict-prefix-of:ab,ac", "duplicate:9"):
        mine = PNAR.read_word(word)
        theirs = PNAQ.read_word(word)
        ok = check(mine["refused"] is None,
                   "AC-PNAR5 legacy %r is not refused by the shape rule (%r)"
                   % (word, mine["refused"])) and ok
        ok = check(all(mine[key] == theirs[key]
                       for key in PNAR.READING_KEYS),
                   "AC-PNAR5 legacy %r rides R2698 on every reading key"
                   % (word,)) and ok
        ok = check(PNAR.shape_of_word(word) is None,
                   "AC-PNAR5 legacy %r carries no pedigree and so no shape"
                   % (word,)) and ok
        ok = check(PNAR.body_parts_of(word) is None,
                   "AC-PNAR5 legacy %r has no body parts for this rule"
                   % (word,)) and ok
    got = PNAR.read_word(LEGACY_DUP)
    ok = check(got["duplicate"] == 2 and got["dialect"] is None,
               "AC-PNAR5 a bare duplicate stays a legal legacy word (%r)"
               % (got,)) and ok
    ok = check(PNAR.read_word(LEGACY_DUP + "+dialect:1")["refused"] is None,
               "AC-PNAR5 a TAIL marker is still legacy rather than a shape"
               " failure") and ok
    ok = check(PNAR.shape_refusal(LEGACY_PAIR) is None,
               "AC-PNAR5 the shape rule answers None off a legacy word") and ok
    return ok


def ac_pnar6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAR6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAR6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    ok = check(all(("probe_seam" in line) or (line.split()[1].split(".")[0]
                                              in ("argparse", "json", "os",
                                                  "sys"))
               for line in imports),
               "AC-PNAR6 every import is stdlib or a shipped probe (%s)"
               % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAR6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAR6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE), "AC-PNAR6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAR6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnar1, ac_pnar2, ac_pnar3, ac_pnar4, ac_pnar5, ac_pnar6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
