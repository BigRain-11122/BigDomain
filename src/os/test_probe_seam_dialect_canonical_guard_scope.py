"""AC-PNAS1..AC-PNAS6 suite for the dialect canonical guard face (R2704).

Criteria were pinned in state/queue/tech.md:684 at R2701 BEFORE this code
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

import probe_seam_dialect_canonical_guard_scope as PNAS  # noqa
import probe_seam_dialect_shape_guard_scope as PNAR  # noqa
import probe_seam_dialect_tag_guard_scope as PNAQ  # noqa
import probe_seam_unnameable_dialect_marker_scope as PNAP  # noqa
import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "probe_seam_dialect_canonical_guard_scope.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-dialect-canonical-guard-scope",'
WIRED_SUITE = '"test_probe_seam_dialect_canonical_guard_scope.py"'

CANONICAL_DUP = "dialect:1+duplicate:2"
CANONICAL_DUP_12 = "dialect:1+duplicate:12"
LEADING_ZERO_DUP = "dialect:1+duplicate:02"
LEADING_ZERO_DUP_3 = "dialect:1+duplicate:002"
NON_ASCII_DUP = "dialect:1+duplicate:" + chr(0x662)
SIGN_DUP = "dialect:1+duplicate:+2"
SPACE_DUP = "dialect:1+duplicate: 2"
SUPERSCRIPT_DUP = "dialect:1+duplicate:" + chr(0xB2)
BARE_PREFIX = "dialect:1+strict-prefix-of:ab"
PREFIX_TWO = "dialect:1+strict-prefix-of:ab,ac"
PAIR = "dialect:1+strict-prefix-of:ab+duplicate:2"
REPEATED_PREFIX = "dialect:1+strict-prefix-of:ab,ab"
REPEATED_PREFIX_THREE = "dialect:1+strict-prefix-of:ab,ab,ac"
ESCAPED_COMMA_PREFIX = "dialect:1+strict-prefix-of:ab\\,ac"
LEGACY_DUP = "duplicate:2"
LEGACY_DUP_ZERO = "duplicate:02"
LEGACY_PAIR = "strict-prefix-of:ab+duplicate:2"
LEGACY_REPEATED = "strict-prefix-of:ab,ab"

# every fixture the R2685, R2689, R2692, R2698 and R2701 suites proved
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
    ["a", "ab", "ab"],
]

LIVE_MODULES = [
    "probe_seam_dialect_canonical_guard_scope.py",
    "probe_seam_dialect_shape_guard_scope.py",
    "probe_seam_dialect_tag_guard_scope.py",
    "probe_seam_unnameable_dialect_marker_scope.py",
    "probe_seam_unnameable_part_joiner_escaped_scope.py",
]


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()[:16]


def same_on_keys(got, theirs):
    return all(got[key] == theirs[key] for key in PNAS.READING_KEYS)


def ac_pnas1():
    """A counted duplicate written non-canonically is refused by its form."""
    ok = True
    cases = [
        (LEADING_ZERO_DUP, "leading-zero"),
        (LEADING_ZERO_DUP_3, "leading-zero"),
        (NON_ASCII_DUP, "non-ascii-digit"),
    ]
    for word, form in cases:
        got = PNAS.read_word(word)
        ok = check(got["refused"] == "duplicate-not-canonical",
                   "AC-PNAS1 %r is refused as duplicate-not-canonical (%r)"
                   % (word.encode("unicode_escape").decode("ascii"),
                      got["refused"])) and ok
        ok = check(got["shape"] == form,
                   "AC-PNAS1 and it NAMES the form found (%r)"
                   % (got["shape"],)) and ok
        ok = check(got["refusal_word"]
                   == "refused:duplicate-not-canonical:" + form,
                   "AC-PNAS1 its own word is derived from code and form (%r)"
                   % (got["refusal_word"],)) and ok
        ok = check(got["dialect"] is None and got["body"] is None
                   and got["duplicate"] is None,
                   "AC-PNAS1 it is refused rather than read as a count"
                   " (%r / %r / %r)" % (got["dialect"], got["body"],
                                        got["duplicate"])) and ok
        base = PNAS.base_reading(word)
        ok = check(base["refused"] is None and base["duplicate"] == 2,
                   "AC-PNAS1 the R2701 reading of the same word ACCEPTED it as"
                   " count 2 (%r)" % (base["duplicate"],)) and ok
        ok = check(PNAS.read_word(CANONICAL_DUP)["duplicate"] == 2
                   and got["duplicate"] is None,
                   "AC-PNAS1 it is never read as the same count as the"
                   " canonical word") and ok
    for word in (SIGN_DUP, SPACE_DUP):
        got = PNAS.read_word(word)
        ok = check(got["refused"] == "duplicate-not-counted",
                   "AC-PNAS1 the R2701 shape rule ALREADY refused %r, so the"
                   " canonical rule never sees it (%r)"
                   % (word, got["refused"])) and ok
    crashed = None
    try:
        got = PNAS.base_reading(SUPERSCRIPT_DUP)
    except Exception as exc:
        crashed = "%s: %s" % (type(exc).__name__, exc)
        got = None
    ok = check(crashed is None,
               "AC-PNAS1 the birth-site repair stops the measured ValueError"
               " (%s)" % (crashed,)) and ok
    ok = check(got is not None and got["refused"] == "duplicate-not-counted",
               "AC-PNAS1 a superscript two is now REFUSED rather than raising"
               " (%r)" % ((got or {}).get("refused"),)) and ok
    ok = check(PNAS.read_word(SUPERSCRIPT_DUP)["refused"] is not None,
               "AC-PNAS1 and this face refuses it end to end") and ok
    return ok


def ac_pnas2():
    """A canonically counted word keeps its exact bytes and its count."""
    ok = True
    for word, count in ((CANONICAL_DUP, 2), (CANONICAL_DUP_12, 12)):
        got = PNAS.read_word(word)
        ok = check(got["refused"] is None and got["dialect"] == "1",
                   "AC-PNAS2 %r still reads back tag 1 (%r)"
                   % (word, got["dialect"])) and ok
        ok = check(got["word"] == word and got["body"] == PNAP.strip_marker(word),
                   "AC-PNAS2 its word and body keep their exact bytes (%r)"
                   % (got["body"],)) and ok
        ok = check(got["duplicate"] == count,
                   "AC-PNAS2 its count reads %d (%r)" % (count,
                                                          got["duplicate"])) and ok
        ok = check(PNAS.shape_of_word(word) == "duplicate",
                   "AC-PNAS2 its shape is still duplicate (%r)"
                   % (PNAS.shape_of_word(word),)) and ok
        ok = check(same_on_keys(got, PNAR.read_word(word)),
                   "AC-PNAS2 every reading key rides the R2701 face") and ok
    words = PNAS.ack_words(["a", "a"])
    ok = check(words == {"a": CANONICAL_DUP},
               "AC-PNAS2 the duplicate-only label set still publishes the"
               " canonical word (%r)" % (words,)) and ok
    ok = check(PNAS.ack_readings(["a", "a"])["a"]["duplicate"] == 2,
               "AC-PNAS2 and it reads back count 2 through this face") and ok
    ok = check(PNAS.canonical_state_of_word(CANONICAL_DUP) == "canonical",
               "AC-PNAS2 a legal marked word reports the canonical state") and ok
    ok = check(PNAS.canonical_state_of_word(LEADING_ZERO_DUP) is None,
               "AC-PNAS2 a refused word reports no canonical state") and ok
    return ok


def ac_pnas3():
    """A sibling named twice is refused; ordinary sibling words keep bytes."""
    ok = True
    for word, label in ((REPEATED_PREFIX, "ab"),
                        (REPEATED_PREFIX_THREE, "ab")):
        got = PNAS.read_word(word)
        ok = check(got["refused"] == "sibling-repeated",
                   "AC-PNAS3 %r is refused as sibling-repeated (%r)"
                   % (word, got["refused"])) and ok
        ok = check(got["shape"] == label,
                   "AC-PNAS3 and it NAMES the duplicated sibling (%r)"
                   % (got["shape"],)) and ok
        ok = check(got["siblings"] is None and got["body"] is None,
                   "AC-PNAS3 it hands back no siblings and no body") and ok
        base = PNAS.base_reading(word)
        ok = check(base["refused"] is None and base["siblings"] == ["ab", "ab"]
                   if word == REPEATED_PREFIX else
                   base["refused"] is None,
                   "AC-PNAS3 the R2701 reading of the same word accepted the"
                   " repeated list (%r)" % (base["siblings"],)) and ok
    for word in (BARE_PREFIX, PREFIX_TWO, PAIR, ESCAPED_COMMA_PREFIX):
        mine = PNAS.read_word(word)
        theirs = PNAR.read_word(word)
        ok = check(mine["refused"] is None,
                   "AC-PNAS3 ordinary sibling word %r stays legal (%r)"
                   % (word, mine["refused"])) and ok
        ok = check(same_on_keys(mine, theirs),
                   "AC-PNAS3 and it is byte for byte what R2701 published"
                   " (%s)" % (word,)) and ok
    ok = check(PNAS.ack_words(["a", "ab\\,ac"])
               == PNAP.ack_unnameable(["a", "ab\\,ac"]),
               "AC-PNAS3 the escaped-comma fixture publishes what R2692"
               " published") and ok
    ok = check(PNAS.read_word(ESCAPED_COMMA_PREFIX)["siblings"] == ["ab,ac"],
               "AC-PNAS3 an escaped comma is still ONE label, never a repeat"
               " (%r)" % (PNAS.read_word(ESCAPED_COMMA_PREFIX)["siblings"],)) and ok
    emitted = []
    for labels in FIXTURES:
        emitted.extend(PNAS.ack_unnameable(labels).values())
    repeated = [word for word in sorted(set(emitted))
                if any(PNAS.repeated_sibling_of_part(part) is not None
                       for part in (PNAS.body_parts_of(word) or []))]
    ok = check(repeated == [],
               "AC-PNAS3 the publishing face emits NO repeated sibling list"
               " over every fixture (offenders=%r)" % (repeated,)) and ok
    ok = check(PNAS.ack_all_legal(["a", "ab", "ab"]) is True,
               "AC-PNAS3 and every word it publishes is legal here") and ok
    return ok


def ac_pnas4():
    """Every earlier reading rides, plus one bounded live leg on BOTH faces."""
    ok = True
    seen = 0
    for index, labels in enumerate(FIXTURES):
        ok = check(PNAS.ack_legacy_words(labels) == PNAO.ack_unnameable(labels),
                   "AC-PNAS4 R2689 fixture %d rides byte for byte"
                   % (index,)) and ok
        ok = check(PNAS.ack_words(labels) == PNAP.ack_unnameable(labels),
                   "AC-PNAS4 R2692 fixture %d rides byte for byte"
                   % (index,)) and ok
        for word in sorted(set(PNAP.ack_unnameable(labels).values())):
            seen += 1
            mine = PNAS.read_word(word)
            theirs = PNAR.read_word(word)
            ok = check(same_on_keys(mine, theirs),
                       "AC-PNAS4 R2701 word %r rides on every reading key"
                       % (word,)) and ok
        for word in sorted(set(PNAL.ack_unnameable(labels).values())):
            ok = check(PNAS.read_word(word)["refused"] is None,
                       "AC-PNAS4 R2685 word %r is still legal here"
                       % (word,)) and ok
    ok = check(seen >= 9,
               "AC-PNAS4 the published face covered %d distinct words"
               % (seen,)) and ok
    ok = check(PNAS.base_reading(LEGACY_PAIR) == PNAR.read_word(LEGACY_PAIR),
               "AC-PNAS4 the base reading IS the R2701 reading") and ok
    for index, labels in enumerate([["a", "ab,ac"], ["a", "ab", "ac"],
                                    ["x", "xy"], ["a", "a"],
                                    ["a", "ab", "ac", "ad"],
                                    ["p", "pq,pr", "ps"]]):
        ok = check(PNAS.ack_legacy_words(labels)
                   == PNAL.ack_unnameable(labels),
                   "AC-PNAS4 R2685 fixture %d rides unchanged"
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
        for build in (PNAR.module_alias_report, PNAS.module_alias_report):
            try:
                report = build(text, BASE)
            except Exception:
                unreadable += 1
                continue
            loops += len(report.get("loops") or [])
        if digest(path) != first_digest:
            disagreements += 1
    ok = check(loops > 0 and unreadable == 0 and disagreements == 0,
               "AC-PNAS4 a bounded live leg is read-only (modules=%d loops=%d"
               " unreadable=%d disagree=%d)"
               % (len(before), loops, unreadable, disagreements)) and ok
    mine = PNAS.read_word(PAIR)
    theirs = PNAR.read_word(PAIR)
    ok = check(same_on_keys(mine, theirs),
               "AC-PNAS4 the SAME published fixture reads the same on BOTH"
               " readers") and ok
    base = PNAR.read_word(CANONICAL_DUP)
    ok = check(PNAS.read_word(LEADING_ZERO_DUP)["refused"] is not None
               and base["duplicate"] == 2,
               "AC-PNAS4 the same count written two ways is ONE reading there"
               " and two verdicts here") and ok
    return ok


def ac_pnas5():
    """A marker-less legacy word is untouched by the canonical rule."""
    ok = True
    for word in (LEGACY_DUP, LEGACY_DUP_ZERO, LEGACY_PAIR, LEGACY_REPEATED,
                 "strict-prefix-of:ab,ac", "duplicate:9"):
        mine = PNAS.read_word(word)
        theirs = PNAR.read_word(word)
        ok = check(mine["refused"] is None,
                   "AC-PNAS5 legacy %r is not refused by the canonical rule"
                   " (%r)" % (word, mine["refused"])) and ok
        ok = check(same_on_keys(mine, theirs),
                   "AC-PNAS5 legacy %r rides R2701 on every reading key"
                   % (word,)) and ok
        ok = check(PNAS.shape_of_word(word) is None,
                   "AC-PNAS5 legacy %r carries no pedigree and so no shape"
                   % (word,)) and ok
        ok = check(PNAS.body_parts_of(word) is None,
                   "AC-PNAS5 legacy %r has no body parts for this rule"
                   % (word,)) and ok
    got = PNAS.read_word(LEGACY_DUP_ZERO)
    ok = check(got["duplicate"] == 2 and got["dialect"] is None,
               "AC-PNAS5 a bare 'duplicate:02' stays a legal legacy word (%r)"
               % (got,)) and ok
    ok = check(PNAS.canonical_refusal(LEGACY_DUP_ZERO) is None,
               "AC-PNAS5 the canonical rule answers None off a legacy word") and ok
    ok = check(PNAS.read_word(LEGACY_REPEATED)["siblings"] == ["ab", "ab"],
               "AC-PNAS5 a legacy repeated list is left exactly as R2701 read"
               " it (%r)" % (PNAS.read_word(LEGACY_REPEATED)["siblings"],)) and ok
    return ok


def ac_pnas6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAS6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAS6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    ok = check(all(("probe_seam" in line) or (line.split()[1].split(".")[0]
                                              in ("argparse", "json", "os",
                                                  "sys"))
               for line in imports),
               "AC-PNAS6 every import is stdlib or a shipped probe (%s)"
               % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAS6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAS6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE), "AC-PNAS6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAS6 six criteria are declared") and ok
    parent = read_bytes(os.path.join(
        BASE, "probe_seam_dialect_shape_guard_scope.py")).decode("ascii")
    ok = check("except ValueError" in parent,
               "AC-PNAS6 the birth-site repair that stops the measured"
               " ValueError is on disk") and ok
    return ok


def main():
    checks = [ac_pnas1, ac_pnas2, ac_pnas3, ac_pnas4, ac_pnas5, ac_pnas6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
