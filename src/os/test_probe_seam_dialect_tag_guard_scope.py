"""AC-PNAQ1..AC-PNAQ6 suite for the dialect-tag guard face (R2698).

Criteria were pinned in state/queue/tech.md:682 at R2692 BEFORE this code
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

import probe_seam_dialect_tag_guard_scope as PNAQ  # noqa
import probe_seam_unnameable_dialect_marker_scope as PNAP  # noqa
import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "probe_seam_dialect_tag_guard_scope.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-dialect-tag-guard-scope",'
WIRED_SUITE = '"test_probe_seam_dialect_tag_guard_scope.py"'

MARKED_WORD = "dialect:1+strict-prefix-of:ab\\+duplicate:2"
LEGACY_GENUINE = "strict-prefix-of:ab+duplicate:2"
FUTURE_GUARDED = "dialect:2+strict-prefix-of:ab"
FUTURE_BARE = "dialect:2"
DOUBLED = "dialect:1+dialect:1+strict-prefix-of:ab"
TAIL_MARKER = LEGACY_GENUINE + "+dialect:1"
MARKER_ONLY = "dialect:1"

# every fixture the R2689 and R2692 suites proved, reused rather than retyped
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


def ac_pnaq1():
    """A first part naming an unknown tag is REFUSED naming that tag."""
    got = PNAQ.read_word(FUTURE_GUARDED)
    ok = check(got["refused"] == "unknown-dialect",
               "AC-PNAQ1 a future dialect is refused (%s)" % (got["refused"],))
    ok = check(got["tag"] == "2",
               "AC-PNAQ1 the refusal NAMES the unknown tag (%r)"
               % (got["tag"],)) and ok
    ok = check(got["refusal_word"] == "refused:unknown-dialect:2",
               "AC-PNAQ1 the refusal carries its own word (%r)"
               % (got["refusal_word"],)) and ok
    ok = check(got["dialect"] is None and got["body"] is None,
               "AC-PNAQ1 it is never handed back as a legacy word with its"
               " body verbatim (%r / %r)" % (got["dialect"], got["body"])) and ok
    ok = check(got["siblings"] is None and got["duplicate"] is None,
               "AC-PNAQ1 and it states NO readings (%r / %r)"
               % (got["siblings"], got["duplicate"])) and ok
    ok = check(PNAQ.is_legal_reading(FUTURE_GUARDED) is False,
               "AC-PNAQ1 the word is not a legal reading") and ok
    base = PNAQ.base_reading(FUTURE_GUARDED)
    ok = check(base["dialect"] is None
               and base["body"] == FUTURE_GUARDED,
               "AC-PNAQ1 the R2692 reading of the same word WAS the legacy"
               " mis-typing this face refuses (%r)" % (base,)) and ok
    bare = PNAQ.read_word(FUTURE_BARE)
    ok = check(bare["refused"] == "unknown-dialect" and bare["tag"] == "2",
               "AC-PNAQ1 a bare future marker is refused too (%r)"
               % (bare["refusal_word"],)) and ok
    empty = PNAQ.read_word("dialect:+strict-prefix-of:ab")
    ok = check(empty["refused"] == "unknown-dialect"
               and empty["tag"] == "",
               "AC-PNAQ1 an empty tag is an unknown tag, not a pedigree (%r)"
               % (empty["tag"],)) and ok
    named = PNAQ.read_word("dialect:x+strict-prefix-of:ab")
    ok = check(named["refusal_word"] == "refused:unknown-dialect:x",
               "AC-PNAQ1 a named stranger tag is refused by that name (%r)"
               % (named["refusal_word"],)) and ok
    return ok


def ac_pnaq2():
    """A marker-less legacy word still reads exactly as R2692 reads it."""
    ok = True
    seen = 0
    for labels in FIXTURES:
        words = sorted(set(PNAP.ack_unnameable(labels).values()))
        for word in words:
            seen += 1
            mine = PNAQ.read_word(word)
            theirs = PNAP.read_word(word)
            same = all(mine[key] == theirs[key] for key in PNAQ.READING_KEYS)
            ok = check(same,
                       "AC-PNAQ2 %r rides R2692 on every reading key (%s vs"
                       " %s)" % (word, mine, theirs)) and ok
            ok = check(mine["refused"] is None,
                       "AC-PNAQ2 %r is read, not refused" % (word,)) and ok
    ok = check(seen >= 9,
               "AC-PNAQ2 the legacy face covered %d distinct words"
               % (seen,)) and ok
    got = PNAQ.read_word(LEGACY_GENUINE)
    ok = check(got["dialect"] is None and got["markers"] == 0,
               "AC-PNAQ2 the legacy string reports no dialect (%r)"
               % (got["dialect"],)) and ok
    ok = check(got["siblings"] == ["ab"] and got["duplicate"] == 2,
               "AC-PNAQ2 and the same readings as before (%s / %s)"
               % (got["siblings"], got["duplicate"])) and ok
    ok = check(got["body"] == LEGACY_GENUINE,
               "AC-PNAQ2 its body is handed back verbatim (%r)"
               % (got["body"],)) and ok
    ok = check(PNAQ.ack_legacy_words(FIXTURES[9])
               == PNAP.ack_legacy_words(FIXTURES[9]),
               "AC-PNAQ2 the legacy words of a fixture ride R2692 byte for"
               " byte") and ok
    return ok


def ac_pnaq3():
    """The word this face publishes keeps its bytes and reads back tag 1."""
    mine = PNAQ.ack_words(["a", "ab+duplicate:2"])
    theirs = PNAP.ack_unnameable(["a", "ab+duplicate:2"])
    ok = check(mine == theirs,
               "AC-PNAQ3 the published word is byte for byte R2692's (%s vs"
               " %s)" % (mine, theirs))
    ok = check(mine["a"] == MARKED_WORD,
               "AC-PNAQ3 and that word is the marked one (%r)"
               % (mine.get("a"),)) and ok
    got = PNAQ.read_word(mine["a"])
    ok = check(got["dialect"] == "1",
               "AC-PNAQ3 it reads back its tag (%r)" % (got["dialect"],)) and ok
    ok = check(got["refused"] is None and got["count"] == 1,
               "AC-PNAQ3 it carries one dialect part and is not refused") and ok
    ok = check(got["body"] == PNAP.strip_marker(mine["a"]),
               "AC-PNAQ3 the body is the stripped word (%r)"
               % (got["body"],)) and ok
    ok = check(got["siblings"] == ["ab+duplicate:2"]
               and got["duplicate"] is None,
               "AC-PNAQ3 the readings are R2692's own (%s / %s)"
               % (got["siblings"], got["duplicate"])) and ok
    ok = check(PNAQ.validated_tag(mine["a"]) == "1",
               "AC-PNAQ3 the validated tag agrees") and ok
    ok = check(PNAQ.ack_all_legal(["a", "ab+duplicate:2"]) is True,
               "AC-PNAQ3 every word this face publishes is legal") and ok
    for labels in FIXTURES:
        ok = check(PNAQ.ack_all_legal(labels) is True,
                   "AC-PNAQ3 fixture %s publishes only legal words"
                   % (labels,)) and ok
    return ok


def ac_pnaq4():
    """More than one dialect part is refused naming the count."""
    got = PNAQ.read_word(DOUBLED)
    ok = check(got["refused"] == "multiple-dialect-parts",
               "AC-PNAQ4 a doubled marker is refused (%r)"
               % (got["refused"],))
    ok = check(got["count"] == 2,
               "AC-PNAQ4 the refusal NAMES the count (%r)" % (got["count"],)) and ok
    ok = check(got["refusal_word"] == "refused:multiple-dialect-parts:2",
               "AC-PNAQ4 and carries its own word (%r)"
               % (got["refusal_word"],)) and ok
    ok = check(got["body"] is None and got["siblings"] is None,
               "AC-PNAQ4 it is not read as this face own word") and ok
    base = PNAQ.base_reading(DOUBLED)
    ok = check(base["dialect"] == "1" and base["markers"] == 2,
               "AC-PNAQ4 the R2692 reading of the same word ACCEPTED it as tag"
               " 1 with markers=2 (%s)" % (base,)) and ok
    tail = PNAQ.read_word(TAIL_MARKER)
    ok = check(tail["refused"] is None and tail["dialect"] is None,
               "AC-PNAQ4 ONE tail marker still claims no pedigree (%r / %r)"
               % (tail["refused"], tail["dialect"])) and ok
    ok = check(tail["count"] == 1,
               "AC-PNAQ4 and the count reports it without a refusal (%r)"
               % (tail["count"],)) and ok
    ok = check(tail["markers"] == 1,
               "AC-PNAQ4 while the marker count still sees it (%r)"
               % (tail["markers"],)) and ok
    empty_body = PNAQ.read_word(MARKER_ONLY)
    ok = check(empty_body["refused"] is None
               and empty_body["dialect"] == "1",
               "AC-PNAQ4 a marker with no body is still a legal tag-1 word"
               " (the SHAPE is the seeded successor, not this criterion)"
               " (%r)" % (empty_body,)) and ok
    return ok


def ac_pnaq5():
    """Every pinned answer rides, plus one bounded live leg on BOTH readers."""
    ok = True
    for index, labels in enumerate(FIXTURES):
        ok = check(PNAQ.ack_legacy_words(labels)
                   == PNAO.ack_unnameable(labels),
                   "AC-PNAQ5 R2689 fixture %d rides byte for byte" % (index,)) and ok
        ok = check(PNAQ.ack_words(labels) == PNAP.ack_unnameable(labels),
                   "AC-PNAQ5 R2692 fixture %d rides byte for byte" % (index,)) and ok
    for index, labels in enumerate([["a", "ab,ac"], ["a", "ab", "ac"],
                                    ["x", "xy"], ["a", "a"],
                                    ["a", "ab", "ac", "ad"],
                                    ["p", "pq,pr", "ps"]]):
        ok = check(PNAQ.ack_legacy_words(labels) == PNAL.ack_unnameable(labels),
                   "AC-PNAQ5 R2685 fixture %d rides unchanged" % (index,)) and ok
    ok = check(PNAQ.ack_words(["a", "b"]) == {},
               "AC-PNAQ5 nameable labels still carry no word") and ok
    ok = check(PNAQ.ack_fully_named(["a", "ab", "ac"]) is False,
               "AC-PNAQ5 an unnameable label is never fully named") and ok
    ok = check(PNAQ.parse_part_word(LEGACY_GENUINE)
               == PNAP.parse_part_word(LEGACY_GENUINE)
               == {"siblings": ["ab"], "duplicate": 2},
               "AC-PNAQ5 the body parser itself rides R2692 unchanged") and ok
    ok = check(PNAQ.reasons_summary([LEGACY_GENUINE])["all_legal"] is True,
               "AC-PNAQ5 a reason summary over a legacy word is all legal") and ok

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
        for build in (PNAP.module_alias_report, PNAQ.module_alias_report):
            try:
                report = build(text, BASE)
            except Exception:
                unreadable += 1
                continue
            loops += len(report.get("loops") or [])
        if digest(path) != first_digest:
            disagreements += 1
    ok = check(loops > 0 and unreadable == 0 and disagreements == 0,
               "AC-PNAQ5 a bounded live leg is read-only (modules=%d loops=%d"
               " unreadable=%d disagree=%d)"
               % (len(before), loops, unreadable, disagreements)) and ok
    mine = PNAQ.read_word(LEGACY_GENUINE)
    theirs = PNAP.read_word(LEGACY_GENUINE)
    ok = check(all(mine[key] == theirs[key] for key in PNAQ.READING_KEYS),
               "AC-PNAQ5 the SAME fixture reads the same on BOTH readers") and ok
    base = PNAP.read_word(FUTURE_GUARDED)
    ok = check(PNAQ.read_word(FUTURE_GUARDED)["refused"] is not None
               and base["dialect"] is None
               and base["body"] == FUTURE_GUARDED,
               "AC-PNAQ5 the same FUTURE word is REFUSED here and was read as"
               " a legacy body there (%r)" % (base,)) and ok
    return ok


def ac_pnaq6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAQ6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAQ6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    ok = check(all(("probe_seam" in line) or (line.split()[1].split(".")[0]
                                              in ("argparse", "json", "os",
                                                  "sys"))
               for line in imports),
               "AC-PNAQ6 every import is stdlib or a shipped probe (%s)"
               % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAQ6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAQ6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE), "AC-PNAQ6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAQ6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnaq1, ac_pnaq2, ac_pnaq3, ac_pnaq4, ac_pnaq5, ac_pnaq6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
