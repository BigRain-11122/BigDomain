"""AC-PNAU1..AC-PNAU6 suite for the dialect marker-escape guard face (R2710).

Criteria were pinned in state/queue/tech.md:687 at R2706 BEFORE this code
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

import probe_seam_dialect_marker_escape_guard_scope as PNAU  # noqa
import probe_seam_dialect_escape_guard_scope as PNAT  # noqa
import probe_seam_dialect_canonical_guard_scope as PNAS  # noqa
import probe_seam_dialect_shape_guard_scope as PNAR  # noqa
import probe_seam_unnameable_dialect_marker_scope as PNAP  # noqa
import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "probe_seam_dialect_marker_escape_guard_scope.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-dialect-marker-escape-guard-scope",'
WIRED_SUITE = '"test_probe_seam_dialect_marker_escape_guard_scope.py"'

ESCAPE = PNAO.ESCAPE
LIST_JOINER = PNAO.LIST_JOINER
PART_JOINER = PNAO.PART_JOINER
DUP = "duplicate:"
PREFIX = "dialect:1+strict-prefix-of:"

# an escaped colon inside the marker part: the R2706 face never looked at it
MARKER_ESCAPED = "dialect" + ESCAPE + ":1+" + DUP + "2"
# an illegal escape (backslash before a letter) inside a duplicate tail
DUP_ILLEGAL = "dialect:1+strict-prefix-of:ab+" + DUP + "a" + ESCAPE + "2c"
# the escaped part joiner inside a duplicate tail: raw tail must survive
DUP_JOINER = "dialect:1+" + DUP + "a" + ESCAPE + PART_JOINER + "2"
# escaped forms that ARE published, used as the legal control set
DUP_PLAIN = "dialect:1+" + DUP + "2"
TWO_BODY = "dialect:1+strict-prefix-of:ab+" + DUP + "2"
# marker-less legacy words: both new rules must leave them exactly alone
LEGACY_BARE = DUP + "2"
LEGACY_ESCAPE = DUP + "a" + ESCAPE + "2c"
LEGACY_JOINER = DUP + "a" + ESCAPE + PART_JOINER + "2"
LEGACY_PREFIX = "strict-prefix-of:a" + ESCAPE + "bc"

FIXTURES = [
    ["a", "ab,ac"],
    ["a", "ab", "ac"],
    ["x", "xy"],
    ["a", "a"],
    ["a", "ab", "a"],
    ["a", "ab", "ac", "ad"],
    ["p", "pq,pr", "ps"],
    ["a", "ab+duplicate:2"],
    ["a", "ab" + ESCAPE + LIST_JOINER + "ac"],
    ["a", "ab" + ESCAPE + PART_JOINER + "c"],
    ["a", "a" + ESCAPE + "b", "a" + ESCAPE + "bc"],
    ["a", "ab", "ac", "a"],
    ["a", "ab", "ab"],
]

LIVE_MODULES = [
    "probe_seam_dialect_marker_escape_guard_scope.py",
    "probe_seam_dialect_escape_guard_scope.py",
    "probe_seam_dialect_canonical_guard_scope.py",
    "probe_seam_dialect_shape_guard_scope.py",
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
    return all(got[key] == theirs[key] for key in PNAU.READING_KEYS)


def shown(text):
    return text.encode("unicode_escape").decode("ascii")


def ac_pnau1():
    """AC-PNAU1: an escaped marker is refused, never read as a legacy word."""
    ok = True
    mine = PNAU.read_word(MARKER_ESCAPED)
    theirs = PNAT.read_word(MARKER_ESCAPED)
    ok = check(theirs["refused"] is None and theirs["body"] == MARKER_ESCAPED,
               "AC-PNAU1 R2706 really reads %r as a legacy word today (%r)"
               % (shown(MARKER_ESCAPED), theirs["refused"])) and ok
    ok = check(mine["refused"] == PNAU.REFUSAL_MARKER_ESCAPED,
               "AC-PNAU1 the escaped marker is refused as %r, got %r"
               % (PNAU.REFUSAL_MARKER_ESCAPED, mine["refused"])) and ok
    ok = check(mine["body"] is None and mine["dialect"] is None,
               "AC-PNAU1 a refusal hands back no body and no dialect") and ok
    ok = check(mine["shape"] == ":" and
               mine["refusal_word"] == "refused:marker-escaped::",
               "AC-PNAU1 the escape form is NAMED, got %r"
               % (mine["refusal_word"],)) and ok
    ok = check(PNAU.marker_escape_refusal(MARKER_ESCAPED) is not None,
               "AC-PNAU1 the rule answers its own refusal directly") and ok
    ok = check(PNAU.marker_escape_refusal(DUP_PLAIN) is None,
               "AC-PNAU1 a plain marker carries no escape and is untouched") and ok
    plain_escape = "dialect" + ESCAPE + "x:1+" + DUP + "2"
    ok = check(PNAU.marker_escape_refusal(plain_escape) is None,
               "AC-PNAU1 an escape that does NOT unescape into a marker"
               " leaves the word alone") and ok
    return ok


def ac_pnau2():
    """AC-PNAU2: a duplicate-tail escape is named by BOTH laws at once."""
    ok = True
    mine = PNAU.read_word(DUP_ILLEGAL)
    theirs = PNAT.read_word(DUP_ILLEGAL)
    ok = check(theirs["refused"] == "duplicate-not-counted",
               "AC-PNAU2 R2706 answers the shape law alone today (%r)"
               % (theirs["refused"],)) and ok
    ok = check(mine["refused"] == PNAU.REFUSAL_DUP_TAIL_ESCAPE,
               "AC-PNAU2 the escape is named as well, got %r"
               % (mine["refused"],)) and ok
    ok = check("escape" in mine["refused"] and "not-counted" in mine["refused"],
               "AC-PNAU2 the ONE code names BOTH the escape and the shape"
               " (%r)" % (mine["refused"],)) and ok
    ok = check(mine["shape"] == "a" + ESCAPE + "2c",
               "AC-PNAU2 the raw tail bytes are kept as the shape (%r)"
               % (mine["shape"],)) and ok
    ok = check(mine["refusal_word"] ==
               "refused:" + PNAU.REFUSAL_DUP_TAIL_ESCAPE + ":a" + ESCAPE + "2c",
               "AC-PNAU2 the refusal word carries code AND raw tail (%r)"
               % (mine["refusal_word"],)) and ok
    ok = check(mine["body"] is None and mine["siblings"] is None,
               "AC-PNAU2 the refusal is not mistakable for a reading") and ok
    ok = check(PNAU.read_word(DUP_PLAIN)["refused"] is None,
               "AC-PNAU2 a canonical tail with no escape stays legal") and ok
    return ok


def ac_pnau3():
    """AC-PNAU3: an escaped part joiner in a tail is refused, bytes kept."""
    ok = True
    mine = PNAU.read_word(DUP_JOINER)
    theirs = PNAT.read_word(DUP_JOINER)
    ok = check(theirs["refused"] == "duplicate-not-counted"
               and theirs["shape"] == "a" + ESCAPE + PART_JOINER + "2",
               "AC-PNAU3 R2706 names the SHAPE alone and keeps the raw tail"
               " (%r)" % (theirs["shape"],)) and ok
    ok = check(mine["refused"] == PNAU.REFUSAL_DUP_TAIL_ESCAPE,
               "AC-PNAU3 the escaped joiner is refused by name (%r)"
               % (mine["refused"],)) and ok
    ok = check(mine["shape"] == "a" + ESCAPE + PART_JOINER + "2",
               "AC-PNAU3 the refusal keeps the RAW tail bytes (%r)"
               % (mine["shape"],)) and ok
    ok = check(PNAU.raw_part_spans(DUP_JOINER) ==
               ["dialect:1", DUP + "a" + ESCAPE + PART_JOINER + "2"],
               "AC-PNAU3 the escaped joiner stays inside ONE raw span (%r)"
               % (PNAU.raw_part_spans(DUP_JOINER),)) and ok
    ok = check(PNAU.duplicate_tail_escape_refusal(DUP_JOINER) is not None,
               "AC-PNAU3 the tail rule answers its own refusal directly") and ok
    ok = check(PNAU.duplicate_tail_escape_refusal(LEGACY_JOINER) is None,
               "AC-PNAU3 the tail rule is off for a marker-less legacy word"
               ) and ok
    return ok


def ac_pnau4():
    """AC-PNAU4: every earlier reading rides, plus one live leg on BOTH."""
    ok = True
    seen = 0
    for index, labels in enumerate(FIXTURES):
        ok = check(PNAU.ack_legacy_words(labels) == PNAO.ack_unnameable(labels),
                   "AC-PNAU4 R2689 fixture %d rides byte for byte"
                   % (index,)) and ok
        ok = check(PNAU.ack_words(labels) == PNAP.ack_unnameable(labels),
                   "AC-PNAU4 R2692 fixture %d rides byte for byte"
                   % (index,)) and ok
        for word in sorted(set(PNAS.ack_unnameable(labels).values())):
            seen += 1
            ok = check(same_on_keys(PNAU.base_reading(word), PNAS.read_word(word)),
                       "AC-PNAU4 R2704 word %r rides on every reading key"
                       % (shown(word),)) and ok
        for word in sorted(set(PNAL.ack_unnameable(labels).values())):
            ok = check(PNAU.read_word(word)["refused"] is None,
                       "AC-PNAU4 R2685 word %r is still legal here"
                       % (shown(word),)) and ok
    ok = check(seen >= 9,
               "AC-PNAU4 the published face covered %d distinct words"
               % (seen,)) and ok
    ok = check(PNAU.base_reading(TWO_BODY) == PNAT.read_word(TWO_BODY),
               "AC-PNAU4 the base reading IS the R2706 reading") and ok
    legal = [DUP_PLAIN, TWO_BODY, LEGACY_BARE, LEGACY_PREFIX]
    for word in legal:
        ok = check(same_on_keys(PNAU.read_word(word), PNAT.read_word(word)),
                   "AC-PNAU4 legal %r is byte for byte what R2706 read"
                   % (shown(word),)) and ok

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
        for build in (PNAT.module_alias_report, PNAU.module_alias_report):
            try:
                report = build(text, BASE)
            except Exception:
                unreadable += 1
                continue
            loops += len(report.get("loops") or [])
        if digest(path) != first_digest:
            disagreements += 1
    ok = check(loops > 0 and unreadable == 0 and disagreements == 0,
               "AC-PNAU4 a bounded live leg is read-only (modules=%d loops=%d"
               " unreadable=%d disagree=%d)"
               % (len(before), loops, unreadable, disagreements)) and ok
    ok = check(same_on_keys(PNAU.read_word(DUP_PLAIN),
                            PNAT.read_word(DUP_PLAIN)),
               "AC-PNAU4 the SAME published fixture reads the same on BOTH"
               " readers") and ok
    ok = check(PNAU.read_word(MARKER_ESCAPED)["refused"] is not None
               and PNAT.read_word(MARKER_ESCAPED)["body"] == MARKER_ESCAPED,
               "AC-PNAU4 the same bytes are ONE reading there and a refusal"
               " here") and ok
    return ok


def ac_pnau5():
    """AC-PNAU5: a marker-less legacy word is untouched by both additions."""
    ok = True
    for word in (LEGACY_BARE, LEGACY_ESCAPE, LEGACY_JOINER, LEGACY_PREFIX):
        mine = PNAU.read_word(word)
        theirs = PNAT.read_word(word)
        ok = check(mine["refused"] is None,
                   "AC-PNAU5 legacy %r is not refused by either rule (%r)"
                   % (shown(word), mine["refused"])) and ok
        ok = check(same_on_keys(mine, theirs),
                   "AC-PNAU5 legacy %r rides R2706 on every reading key"
                   % (shown(word),)) and ok
        ok = check(PNAU.shape_of_word(word) is None,
                   "AC-PNAU5 legacy %r carries no pedigree and so no shape"
                   % (shown(word),)) and ok
        ok = check(PNAU.body_parts_of(word) is None,
                   "AC-PNAU5 legacy %r has no body parts for either rule"
                   % (shown(word),)) and ok
    ok = check(PNAU.marker_escape_refusal(LEGACY_ESCAPE) is None,
               "AC-PNAU5 the marker rule answers None off a legacy word") and ok
    ok = check(PNAU.duplicate_tail_escape_refusal(LEGACY_ESCAPE) is None,
               "AC-PNAU5 so a legacy escaped tail is left as text") and ok
    return ok


def ac_pnau6():
    """AC-PNAU6: hygiene - ASCII, stdlib only, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAU6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAU6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    ok = check(all(("probe_seam" in line) or (line.split()[1].split(".")[0]
                                              in ("argparse", "json", "os",
                                                  "sys"))
               for line in imports),
               "AC-PNAU6 every import is stdlib or a shipped probe (%s)"
               % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAU6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAU6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE), "AC-PNAU6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAU6 six criteria are declared") and ok
    ok = check(PNAU.LABEL ==
               "os-probe-seam-dialect-marker-escape-guard-scope",
               "AC-PNAU6 the face carries its own reconcile label (%r)"
               % (PNAU.LABEL,)) and ok
    return ok


def main():
    checks = [ac_pnau1, ac_pnau2, ac_pnau3, ac_pnau4, ac_pnau5, ac_pnau6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
