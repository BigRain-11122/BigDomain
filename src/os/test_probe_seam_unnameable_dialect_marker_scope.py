"""AC-PNAP1..AC-PNAP6 suite for the dialect-marked ack face (R2692).

Criteria were pinned in state/queue/tech.md:681 at R2689 BEFORE this code
existed. Every fixture lives in memory or in a private temporary directory; no
shipped source file is written. Stdlib only, ASCII source, zero network, no
clock. Exit 0 = all green.
"""

import hashlib
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_unnameable_dialect_marker_scope as PNAP  # noqa
import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_scope as PNAK  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_scope as PNAJ  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "probe_seam_unnameable_dialect_marker_scope.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-unnameable-dialect-marker-scope",'
WIRED_SUITE = '"test_probe_seam_unnameable_dialect_marker_scope.py"'

MARKER = "dialect:1"
ESCAPE_PLUS = "\\+"
MARKED_PART_WORD = "dialect:1+strict-prefix-of:ab\\+duplicate:2"
BODY_PART_WORD = "strict-prefix-of:ab\\+duplicate:2"
LEGACY_GENUINE = "strict-prefix-of:ab+duplicate:2"
COMMA_WORD = "strict-prefix-of:ab\\,ac"
TWO_WORD = "strict-prefix-of:ab,ac"
SINGLE_WORD = "strict-prefix-of:xy"
DUP_WORD = "duplicate:2"

# every fixture the R2689 suite proved, reused rather than retyped
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
    "probe_seam_unnameable_dialect_marker_scope.py",
    "probe_seam_unnameable_part_joiner_escaped_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
    "branch_elif_with_while_match_while_else_nested_match_ordinal_"
    "unique_prefix_unnameable_siblings_escaped_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
    "branch_elif_with_while_match_while_else_nested_match_ordinal_"
    "unique_prefix_unnameable_siblings_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
    "branch_elif_with_while_match_while_else_nested_match_ordinal_"
    "unique_prefix_unnameable_scope.py",
]


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()[:16]


def ac_pnap1():
    """A published word carries the marker AND the marker is read back."""
    got = PNAP.ack_unnameable(["a", "ab+duplicate:2"])
    ok = check(got == {"a": MARKED_PART_WORD},
               "AC-PNAP1 the one-label word is marked (%s)" % (got.get("a"),))
    ok = check(PNAP.has_marker(got["a"]) is True,
               "AC-PNAP1 the marker is present in the first part") and ok
    ok = check(PNAP.marker_of_word(got["a"]) == "1",
               "AC-PNAP1 the marker READS BACK as its tag (%s)"
               % (PNAP.marker_of_word(got["a"]),)) and ok
    ok = check(PNAP.marker_of_word(LEGACY_GENUINE) is None,
               "AC-PNAP1 a legacy string reports NO dialect (%s)"
               % (PNAP.marker_of_word(LEGACY_GENUINE),)) and ok
    ok = check(PNAP.marker_of_word(got["a"][len(MARKER) + 1:]) is None,
               "AC-PNAP1 with the marker removed the SAME word reports none,"
               " so the reading is taken from the bytes") and ok
    ok = check(PNAP.marker_of_word(LEGACY_GENUINE + "+" + MARKER) is None,
               "AC-PNAP1 a marker appended to the TAIL claims no dialect"
               " (%s)" % (PNAP.marker_of_word(
                   LEGACY_GENUINE + "+" + MARKER),)) and ok
    ok = check(PNAP.marker_of_word(MARKER + "+" + BODY_PART_WORD) == "1",
               "AC-PNAP1 a marker in the FIRST part is read even when the"
               " word is handed in from outside") and ok
    return ok


def ac_pnap2():
    """Every legacy word (no marker) still parses exactly as R2689."""
    ok = True
    seen = 0
    for labels in FIXTURES:
        for word in sorted(set(PNAO.ack_unnameable(labels).values())
                           | set(PNAL.ack_unnameable(labels).values())):
            seen += 1
            ok = check(PNAP.parse_strict_prefix_word(word)
                       == PNAO.parse_strict_prefix_word(word),
                       "AC-PNAP2 %r siblings ride R2689 (%s)"
                       % (word, PNAP.parse_strict_prefix_word(word))) and ok
            ok = check(PNAP.sibling_count_from_word(word)
                       == PNAO.sibling_count_from_word(word),
                       "AC-PNAP2 %r sibling count rides R2689" % (word,)) and ok
            ok = check(PNAP.parse_duplicate_from_word(word)
                       == PNAO.parse_duplicate_from_word(word),
                       "AC-PNAP2 %r duplicate rides R2689 (%s)"
                       % (word, PNAP.parse_duplicate_from_word(word))) and ok
            ok = check(PNAP.parse_part_word(word)
                       == PNAO.parse_part_word(word),
                       "AC-PNAP2 %r both readings ride R2689" % (word,)) and ok
            ok = check(PNAP.strip_marker(word) == word,
                       "AC-PNAP2 %r is handed back byte for byte" % (word,)) and ok
    ok = check(seen >= 9,
               "AC-PNAP2 the legacy face covered %d distinct words" % (seen,)) and ok
    ok = check(PNAP.read_word(LEGACY_GENUINE)
               == {"dialect": None, "markers": 0, "body": LEGACY_GENUINE,
                   "siblings": ["ab"], "duplicate": 2},
               "AC-PNAP2 the legacy string reads exactly as before, with"
               " dialect None (%s)" % (PNAP.read_word(LEGACY_GENUINE),)) and ok
    return ok


def ac_pnap3():
    """The body stays byte for byte what R2689 published."""
    mine = PNAP.ack_unnameable(["a", "ab+duplicate:2"])["a"]
    theirs = PNAO.ack_unnameable(["a", "ab+duplicate:2"])["a"]
    ok = check(PNAP.strip_marker(mine) == theirs,
               "AC-PNAP3 the body equals the R2689 word (%r vs %r)"
               % (PNAP.strip_marker(mine), theirs))
    ok = check(theirs == BODY_PART_WORD,
               "AC-PNAP3 and that word is %r (%r)"
               % (BODY_PART_WORD, theirs)) and ok
    ok = check(mine == MARKER + "+" + theirs,
               "AC-PNAP3 the marked word is the marker plus that body"
               " (%r)" % (mine,)) and ok
    ok = check(PNAP.sibling_count_from_word(mine) == 1,
               "AC-PNAP3 the marked word still names ONE sibling") and ok
    ok = check(PNAP.parse_strict_prefix_word(mine) == ["ab+duplicate:2"],
               "AC-PNAP3 the marked word still recovers the whole label"
               " (%s)" % (PNAP.parse_strict_prefix_word(mine),)) and ok
    return ok


def ac_pnap4():
    """A forger label carrying the marker text can never impersonate it."""
    forged = PNAP.ack_unnameable(["a", "ab+" + MARKER])["a"]
    ok = check(PNAP.marker_count(forged) == 1,
               "AC-PNAP4 the forger word carries exactly ONE marker part"
               " (%d)" % (PNAP.marker_count(forged),))
    ok = check(PNAP.word_parts(forged)[0] == MARKER,
               "AC-PNAP4 that one marker is this face own first part") and ok
    ok = check(("+" + MARKER) not in forged.replace(ESCAPE_PLUS + MARKER, ""),
               "AC-PNAP4 the forger label cannot produce a second, unescaped"
               " marker part (%r)" % (forged,)) and ok
    ok = check(PNAP.parse_strict_prefix_word(forged) == ["ab+" + MARKER],
               "AC-PNAP4 the forger label stays ONE whole sibling (%s)"
               % (PNAP.parse_strict_prefix_word(forged),)) and ok
    sibling_marker = PNAP.ack_unnameable(["di", MARKER])["di"]
    ok = check(PNAP.marker_count(sibling_marker) == 1,
               "AC-PNAP4 a sibling NAMED the marker text adds no marker part"
               " (%d)" % (PNAP.marker_count(sibling_marker),)) and ok
    ok = check(PNAP.parse_strict_prefix_word(sibling_marker) == [MARKER],
               "AC-PNAP4 that sibling is read as a label, not as pedigree"
               " (%s)" % (PNAP.parse_strict_prefix_word(sibling_marker),)) and ok
    ok = check(PNAP.word_parts(forged)[1].startswith(PNAO.PREFIX_HEAD),
               "AC-PNAP4 the marker is FIRST and the body SECOND (%s)"
               % (PNAP.word_parts(forged),)) and ok
    return ok


def ac_pnap5():
    """R2685 and R2689 answers ride, plus one bounded live leg on BOTH readers."""
    ok = True
    for index, labels in enumerate(FIXTURES):
        mine = PNAP.ack_legacy_words(labels)
        r2689 = PNAO.ack_unnameable(labels)
        ok = check(mine == r2689,
                   "AC-PNAP5 fixture %d body rides R2689 byte for byte (%s vs"
                   " %s)" % (index, mine, r2689)) and ok
    for index, labels in enumerate([["a", "ab,ac"], ["a", "ab", "ac"],
                                    ["x", "xy"], ["a", "a"],
                                    ["a", "ab", "ac", "ad"],
                                    ["p", "pq,pr", "ps"]]):
        mine = PNAP.ack_legacy_words(labels)
        r2685 = PNAL.ack_unnameable(labels)
        ok = check(mine == r2685,
                   "AC-PNAP5 R2685 fixture %d rides unchanged (%s vs %s)"
                   % (index, mine, r2685)) and ok
    ok = check(PNAP.ack_unnameable(["a", "b"]) == {},
               "AC-PNAP5 nameable labels still carry no word") and ok
    ok = check(PNAP.ack_index(["a", "ab", "ac"])
               == PNAL.ack_index(["a", "ab", "ac"])
               and PNAP.ack_unmatched(["a", "ab", "ac"])
               == PNAL.ack_unmatched(["a", "ab", "ac"]),
               "AC-PNAP5 the index and unmatched readers ride R2685") and ok
    ok = check(PNAP.ack_fully_named(["a", "ab", "ac"]) is False,
               "AC-PNAP5 an unnameable label is never fully named") and ok

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
        for module in (PNAP, PNAO):
            try:
                report = module.module_alias_report(text, BASE)
            except Exception:
                unreadable += 1
                continue
            loops += len(report.get("loops") or [])
        if digest(path) != first_digest:
            disagreements += 1
    # the SAME fixture, measured on BOTH readers
    legacy_read = PNAO.parse_part_word(LEGACY_GENUINE)
    mine_read = PNAP.parse_part_word(LEGACY_GENUINE)
    own_word = PNAP.ack_unnameable(["a", "ab+duplicate:2"])["a"]
    ok = check(legacy_read == mine_read == {"siblings": ["ab"],
                                            "duplicate": 2},
               "AC-PNAP5 the legacy string reads the SAME on both readers"
               " (%s vs %s)" % (legacy_read, mine_read)) and ok
    ok = check(PNAP.marker_of_word(LEGACY_GENUINE) is None
               and PNAP.marker_of_word(own_word) == "1",
               "AC-PNAP5 the same fixture is pedigree-less there and marked"
               " here (%s vs %s)"
               % (PNAP.marker_of_word(LEGACY_GENUINE),
                  PNAP.marker_of_word(own_word))) and ok
    ok = check(loops > 0 and unreadable == 0 and disagreements == 0,
               "AC-PNAP5 a bounded live leg is read-only (modules=%d loops=%d"
               " unreadable=%d disagree=%d)"
               % (len(before), loops, unreadable, disagreements)) and ok
    return ok


def ac_pnap6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAP6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAP6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAP6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAP6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAP6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAP6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnap1, ac_pnap2, ac_pnap3, ac_pnap4, ac_pnap5, ac_pnap6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
