"""AC-PNAT1..AC-PNAT6 suite for the dialect escape guard face (R2706).

Criteria were pinned in state/queue/tech.md:685 at R2704 BEFORE this code
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

import probe_seam_dialect_escape_guard_scope as PNAT  # noqa
import probe_seam_dialect_canonical_guard_scope as PNAS  # noqa
import probe_seam_dialect_shape_guard_scope as PNAR  # noqa
import probe_seam_unnameable_dialect_marker_scope as PNAP  # noqa
import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "probe_seam_dialect_escape_guard_scope.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-dialect-escape-guard-scope",'
WIRED_SUITE = '"test_probe_seam_dialect_escape_guard_scope.py"'

ESCAPE = PNAO.ESCAPE
LIST_JOINER = PNAO.LIST_JOINER
PART_JOINER = PNAO.PART_JOINER

PREFIX = "dialect:1+strict-prefix-of:"
# one backslash then a letter: an escape the publishing face never emits
ILLEGAL_LETTER = PREFIX + "a" + ESCAPE + "bc"
PLAIN = PREFIX + "abc"
# one backslash then the list separator: an escape that IS published
ESCAPED_COMMA = PREFIX + "ab" + ESCAPE + LIST_JOINER + "ac"
ESCAPED_JOINER = PREFIX + "ab" + ESCAPE + PART_JOINER + "c"
ESCAPED_ESCAPE = PREFIX + "ab" + ESCAPE + ESCAPE + "c"
TRAILING_ESCAPE = PREFIX + "ab" + ESCAPE
TRAILING_AFTER_PAIR = PREFIX + "ab" + ESCAPE + ESCAPE + ESCAPE
ILLEGAL_NUMBER = PREFIX + "a" + ESCAPE + "7b"
ILLEGAL_JOINER_CASE = PREFIX + "ab,cd" + ESCAPE + "ef"
LEGACY_ILLEGAL = "strict-prefix-of:a" + ESCAPE + "bc"
LEGACY_TRAILING = "strict-prefix-of:ab" + ESCAPE

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
    return all(got[key] == theirs[key] for key in PNAT.READING_KEYS)


def shown(text):
    return text.encode("unicode_escape").decode("ascii")


def ac_pnat1():
    """An escape this face cannot publish is refused, naming the form."""
    ok = True
    for word, form in ((ILLEGAL_LETTER, "b"), (ILLEGAL_NUMBER, "7")):
        got = PNAT.read_word(word)
        ok = check(got["refused"] == "escape-not-published",
                   "AC-PNAT1 %r is refused as escape-not-published (%r)"
                   % (shown(word), got["refused"])) and ok
        ok = check(got["shape"] == form,
                   "AC-PNAT1 and it NAMES the character it escaped (%r)"
                   % (got["shape"],)) and ok
        ok = check(got["refusal_word"]
                   == "refused:escape-not-published:" + form,
                   "AC-PNAT1 its own word is derived from code and form (%r)"
                   % (got["refusal_word"],)) and ok
        ok = check(got["dialect"] is None and got["body"] is None
                   and got["siblings"] is None and got["duplicate"] is None,
                   "AC-PNAT1 it is refused rather than read as siblings"
                   " (%r / %r)" % (got["dialect"], got["siblings"])) and ok
        ok = check(PNAT.base_reading(word)["siblings"] == ["abc"]
                   if word == ILLEGAL_LETTER else
                   PNAT.base_reading(word)["refused"] is None,
                   "AC-PNAT1 the R2704 reading of the same word ACCEPTED it"
                   " (%r)" % (PNAT.base_reading(word)["siblings"],)) and ok
    got = PNAT.read_word(ILLEGAL_LETTER)
    plain = PNAT.read_word(PLAIN)
    ok = check(got["siblings"] != plain["siblings"],
               "AC-PNAT1 it is never read as the label its text would"
               " unescape to (%r vs %r)"
               % (got["siblings"], plain["siblings"])) and ok
    ok = check(plain["siblings"] == ["abc"] and plain["refused"] is None,
               "AC-PNAT1 the plain label still reads as itself (%r)"
               % (plain["siblings"],)) and ok
    ok = check(PNAT.read_word(ILLEGAL_JOINER_CASE)["refused"]
               == "escape-not-published",
               "AC-PNAT1 an illegal escape in the SECOND sibling is refused"
               " too (%r)" % (PNAT.read_word(ILLEGAL_JOINER_CASE)["refused"],)) and ok
    foreign = PREFIX + "a" + ESCAPE + chr(0x62)
    got = PNAT.read_word(foreign)
    ok = check(got["shape"] == "b" and got["refused"] is not None,
               "AC-PNAT1 the form is named in ASCII only (%r)" % (got["shape"],)) and ok
    return ok


def ac_pnat2():
    """A sibling label ending in a lone unescaped backslash is refused."""
    ok = True
    got = PNAT.read_word(TRAILING_ESCAPE)
    ok = check(got["refused"] == "trailing-escape",
               "AC-PNAT2 %r is refused as trailing-escape (%r)"
               % (shown(TRAILING_ESCAPE), got["refused"])) and ok
    ok = check(got["shape"] == "trailing",
               "AC-PNAT2 and it names the trailing form (%r)"
               % (got["shape"],)) and ok
    ok = check(got["refusal_word"] == "refused:trailing-escape:trailing",
               "AC-PNAT2 its own word is derived (%r)"
               % (got["refusal_word"],)) and ok
    ok = check(got["siblings"] is None and got["body"] is None,
               "AC-PNAT2 it hands back no siblings and no body") and ok
    base = PNAT.base_reading(TRAILING_ESCAPE)
    ok = check(base["refused"] is None
               and base["siblings"] == ["ab" + ESCAPE],
               "AC-PNAT2 the R2704 reading of the same word kept the lone"
               " backslash as text (%r)" % (base["siblings"],)) and ok
    ok = check(PNAT.read_word(TRAILING_AFTER_PAIR)["refused"]
               == "trailing-escape",
               "AC-PNAT2 a trailing lone escape after a pair is refused as"
               " trailing (%r)"
               % (PNAT.read_word(TRAILING_AFTER_PAIR)["refused"],)) and ok
    ok = check(PNAT.read_word(PREFIX + "ab" + ESCAPE + ESCAPE)["refused"] is None,
               "AC-PNAT2 an escaped backslash at the end is NOT trailing") and ok
    return ok


def ac_pnat3():
    """Every escape this face publishes keeps its bytes and its reading."""
    ok = True
    cases = ((ESCAPED_COMMA, ["ab,ac"]),
             (ESCAPED_JOINER, ["ab" + PART_JOINER + "c"]),
             (ESCAPED_ESCAPE, ["ab" + ESCAPE + "c"]))
    for word, siblings in cases:
        got = PNAT.read_word(word)
        ok = check(got["refused"] is None,
                   "AC-PNAT3 %r stays legal (%r)"
                   % (shown(word), got["refused"])) and ok
        ok = check(got["siblings"] == siblings,
                   "AC-PNAT3 and its unescaped reading is exact (%r)"
                   % (got["siblings"],)) and ok
        ok = check(got["word"] == word,
                   "AC-PNAT3 and its own bytes are untouched") and ok
        ok = check(same_on_keys(got, PNAS.read_word(word)),
                   "AC-PNAT3 every reading key rides the R2704 face") and ok
    ok = check(sorted(PNAT.ESCAPABLE) == sorted([ESCAPE, LIST_JOINER,
                                                 PART_JOINER]),
               "AC-PNAT3 the legal set IS what the publishing face escapes"
               " (%r)" % (PNAT.ESCAPABLE,)) and ok
    emitted = []
    for labels in FIXTURES:
        emitted.extend(PNAO.ack_unnameable(labels).values())
        emitted.extend(PNAP.ack_unnameable(labels).values())
        emitted.extend(PNAS.ack_unnameable(labels).values())
    bad = [word for word in sorted(set(emitted))
           if PNAT.read_word(word)["refused"] is not None]
    ok = check(bad == [],
               "AC-PNAT3 every word those faces publish stays legal here"
               " (offenders=%r)" % (bad,)) and ok
    ok = check(PNAT.ack_all_legal(["a", "a" + ESCAPE + "b",
                                    "a" + ESCAPE + "bc"]) is True,
               "AC-PNAT3 and the publishing face own escapes read back tag 1") and ok
    return ok


def ac_pnat4():
    """Every earlier reading rides, plus one bounded live leg on BOTH faces."""
    ok = True
    seen = 0
    for index, labels in enumerate(FIXTURES):
        ok = check(PNAT.ack_legacy_words(labels) == PNAO.ack_unnameable(labels),
                   "AC-PNAT4 R2689 fixture %d rides byte for byte"
                   % (index,)) and ok
        ok = check(PNAT.ack_words(labels) == PNAP.ack_unnameable(labels),
                   "AC-PNAT4 R2692 fixture %d rides byte for byte"
                   % (index,)) and ok
        for word in sorted(set(PNAS.ack_unnameable(labels).values())):
            seen += 1
            mine = PNAT.read_word(word)
            theirs = PNAS.read_word(word)
            ok = check(same_on_keys(mine, theirs),
                       "AC-PNAT4 R2704 word %r rides on every reading key"
                       % (shown(word),)) and ok
        for word in sorted(set(PNAL.ack_unnameable(labels).values())):
            ok = check(PNAT.read_word(word)["refused"] is None,
                       "AC-PNAT4 R2685 word %r is still legal here"
                       % (shown(word),)) and ok
    ok = check(seen >= 9,
               "AC-PNAT4 the published face covered %d distinct words"
               % (seen,)) and ok
    pair = PREFIX + "ab+duplicate:2"
    ok = check(PNAT.base_reading(pair) == PNAS.read_word(pair),
               "AC-PNAT4 the base reading IS the R2704 reading") and ok

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
        for build in (PNAS.module_alias_report, PNAT.module_alias_report):
            try:
                report = build(text, BASE)
            except Exception:
                unreadable += 1
                continue
            loops += len(report.get("loops") or [])
        if digest(path) != first_digest:
            disagreements += 1
    ok = check(loops > 0 and unreadable == 0 and disagreements == 0,
               "AC-PNAT4 a bounded live leg is read-only (modules=%d loops=%d"
               " unreadable=%d disagree=%d)"
               % (len(before), loops, unreadable, disagreements)) and ok
    ok = check(same_on_keys(PNAT.read_word(ESCAPED_COMMA),
                            PNAS.read_word(ESCAPED_COMMA)),
               "AC-PNAT4 the SAME published fixture reads the same on BOTH"
               " readers") and ok
    ok = check(PNAT.read_word(ILLEGAL_LETTER)["refused"] is not None
               and PNAS.read_word(ILLEGAL_LETTER)["siblings"] == ["abc"],
               "AC-PNAT4 the same bytes are ONE reading there and a refusal"
               " here") and ok
    return ok


def ac_pnat5():
    """A marker-less legacy word is untouched by the escape rule."""
    ok = True
    for word in (LEGACY_ILLEGAL, LEGACY_TRAILING, "strict-prefix-of:ab,ac",
                 "duplicate:2", "duplicate:02",
                 "strict-prefix-of:ab+duplicate:2"):
        mine = PNAT.read_word(word)
        theirs = PNAS.read_word(word)
        ok = check(mine["refused"] is None,
                   "AC-PNAT5 legacy %r is not refused by the escape rule (%r)"
                   % (shown(word), mine["refused"])) and ok
        ok = check(same_on_keys(mine, theirs),
                   "AC-PNAT5 legacy %r rides R2704 on every reading key"
                   % (shown(word),)) and ok
        ok = check(PNAT.shape_of_word(word) is None,
                   "AC-PNAT5 legacy %r carries no pedigree and so no shape"
                   % (shown(word),)) and ok
        ok = check(PNAT.body_parts_of(word) is None,
                   "AC-PNAT5 legacy %r has no body parts for this rule"
                   % (shown(word),)) and ok
    ok = check(PNAT.escape_refusal(LEGACY_ILLEGAL) is None,
               "AC-PNAT5 the escape rule answers None off a legacy word") and ok
    ok = check(PNAT.escape_refusal(LEGACY_TRAILING) is None,
               "AC-PNAT5 so a legacy trailing backslash is left as text") and ok
    return ok


def ac_pnat6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAT6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAT6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    ok = check(all(("probe_seam" in line) or (line.split()[1].split(".")[0]
                                              in ("argparse", "json", "os",
                                                  "sys"))
               for line in imports),
               "AC-PNAT6 every import is stdlib or a shipped probe (%s)"
               % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAT6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAT6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE), "AC-PNAT6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAT6 six criteria are declared") and ok
    ok = check(PNAT.LABEL == "os-probe-seam-dialect-escape-guard-scope",
               "AC-PNAT6 the face carries its own reconcile label (%r)"
               % (PNAT.LABEL,)) and ok
    return ok


def main():
    checks = [ac_pnat1, ac_pnat2, ac_pnat3, ac_pnat4, ac_pnat5, ac_pnat6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
