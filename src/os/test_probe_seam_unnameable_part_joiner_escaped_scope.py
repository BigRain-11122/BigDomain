"""AC-PNAO1..AC-PNAO6 suite for the part-joiner-escaped ack face (R2689).

Criteria were pinned in state/queue/tech.md:681 at R2685 BEFORE this code
existed. Every fixture lives in memory or in a private temporary directory; no
shipped source file is written. Stdlib only, ASCII source, zero network, no
clock. Exit 0 = all green.
"""

import hashlib
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_unnameable_part_joiner_escaped_scope as PNAO  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_scope as PNAK  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_scope as PNAJ  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_scope as PNAI  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "probe_seam_unnameable_part_joiner_escaped_scope.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-unnameable-part-joiner-escaped-scope",'
WIRED_SUITE = '"test_probe_seam_unnameable_part_joiner_escaped_scope.py"'

PART_WORD = "strict-prefix-of:ab\\+duplicate:2"
GENUINE_WORD = "strict-prefix-of:ab+duplicate:2"
COMMA_WORD = "strict-prefix-of:ab\\,ac"
TWO_WORD = "strict-prefix-of:ab,ac"
SINGLE_WORD = "strict-prefix-of:xy"
DUP_WORD = "duplicate:2"

LIVE_MODULES = [
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
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_"
    "branch_elif_with_while_match_while_else_nested_match_ordinal_"
    "unique_prefix_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_scope.py",
]


def world(files):
    root = tempfile.mkdtemp(prefix="pnao-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()[:16]


def ac_pnao1():
    """One name carrying the part joiner is never read as a duplicate part."""
    got = PNAO.ack_unnameable(["a", "ab+duplicate:2"])
    ok = check(got == {"a": PART_WORD},
               "AC-PNAO1 one label carrying the joiner is escaped (%s)"
               % (got,))
    ok = check(got.get("a") != GENUINE_WORD,
               "AC-PNAO1 the word differs from the genuine duplicate word"
               " (%s vs %s)" % (got.get("a"), GENUINE_WORD)) and ok
    ok = check(PNAO.parse_strict_prefix_word(PART_WORD)
               == ["ab+duplicate:2"],
               "AC-PNAO1 the round trip recovers the whole label (%s)"
               % (PNAO.parse_strict_prefix_word(PART_WORD),)) and ok
    ok = check(PNAO.sibling_count_from_word(PART_WORD) == 1,
               "AC-PNAO1 the escaped word names ONE sibling (%s)"
               % (PNAO.sibling_count_from_word(PART_WORD),)) and ok
    ok = check(PNAO.parse_duplicate_from_word(PART_WORD) is None,
               "AC-PNAO1 the escaped label carries NO duplicate part (%s)"
               % (PNAO.parse_duplicate_from_word(PART_WORD),)) and ok
    ok = check(PNAO.parse_part_word(GENUINE_WORD)
               == {"siblings": ["ab"], "duplicate": 2},
               "AC-PNAO1 the genuine word still reads one sibling AND two"
               " copies (%s)" % (PNAO.parse_part_word(GENUINE_WORD),)) and ok
    return ok


def ac_pnao2():
    """The comma escaping R2685 shipped stays byte for byte."""
    got = PNAO.ack_unnameable(["a", "ab,ac"])
    ok = check(got == {"a": COMMA_WORD},
               "AC-PNAO2 the comma word rides R2685 byte for byte (%s)"
               % (got.get("a"),))
    ok = check(got == PNAL.ack_unnameable(["a", "ab,ac"]),
               "AC-PNAO2 the comma answer equals the R2685 face (%s)"
               % (PNAL.ack_unnameable(["a", "ab,ac"]),)) and ok
    ok = check(PNAO.parse_strict_prefix_word(COMMA_WORD) == ["ab,ac"],
               "AC-PNAO2 the comma round trip still names ONE sibling (%s)"
               % (PNAO.parse_strict_prefix_word(COMMA_WORD),)) and ok
    ok = check(PNAO.sibling_count_from_word(COMMA_WORD) == 1,
               "AC-PNAO2 the comma word counts one sibling (%s)"
               % (PNAO.sibling_count_from_word(COMMA_WORD),)) and ok
    backslash = PNAO.ack_unnameable(["a", "ab\\,ac"])
    ok = check(backslash == PNAL.ack_unnameable(["a", "ab\\,ac"]),
               "AC-PNAO2 the backslash fixture is byte identical (%s vs %s)"
               % (backslash, PNAL.ack_unnameable(["a", "ab\\,ac"]))) and ok
    ok = check(PNAO.parse_strict_prefix_word(backslash["a"]) == ["ab\\,ac"],
               "AC-PNAO2 a label carrying a backslash keeps it (%s)"
               % (PNAO.parse_strict_prefix_word(backslash["a"]),)) and ok
    return ok


def ac_pnao3():
    """The two-sibling, single-sibling and duplicate words stay put."""
    ok = check(PNAO.ack_unnameable(["a", "ab", "ac"]) == {"a": TWO_WORD},
               "AC-PNAO3 the two-sibling word is still %s" % (TWO_WORD,))
    ok = check(PNAO.ack_unnameable(["a", "ab", "ac"])
               == PNAL.ack_unnameable(["a", "ab", "ac"]),
               "AC-PNAO3 the two-sibling answer equals R2685") and ok
    ok = check(PNAO.sibling_count_from_word(TWO_WORD) == 2,
               "AC-PNAO3 a plain word still names two siblings") and ok
    ok = check(PNAO.ack_unnameable(["x", "xy"]) == {"x": SINGLE_WORD},
               "AC-PNAO3 the single-sibling word is byte identical to R2679"
               " (%s)" % (PNAO.ack_unnameable(["x", "xy"]),)) and ok
    ok = check(PNAO.ack_unnameable(["x", "xy"])
               == PNAL.ack_unnameable(["x", "xy"]),
               "AC-PNAO3 the first-sibling reader is carried unchanged") and ok
    ok = check(PNAO.ack_unnameable(["a", "a"]) == {"a": DUP_WORD},
               "AC-PNAO3 a duplicate with no sibling keeps its own word"
               " (%s)" % (PNAO.ack_unnameable(["a", "a"]),)) and ok
    ok = check(PNAO.ack_unnameable(["a", "ab", "a"]) == {"a": GENUINE_WORD},
               "AC-PNAO3 a sibling beside a duplicate still joins with one"
               " part (%s)" % (PNAO.ack_unnameable(["a", "ab", "a"]),)) and ok
    ok = check(PNAO.ack_unnameable(["a", "ab", "ac", "ad"])
               == {"a": "strict-prefix-of:ab,ac,ad"},
               "AC-PNAO3 three siblings still publish in order (%s)"
               % (PNAO.ack_unnameable(["a", "ab", "ac", "ad"]),)) and ok
    return ok


def ac_pnao4():
    """The covered word is withheld and the count is still a reading."""
    ok = check(PNAO.verdict_of(PNAO.SEAMS_COVERED, {"prefix_free": True},
                               {"ack_unnameable": {"a": PART_WORD}})
               == PNAO.SEAMS_UNNAMEABLE,
               "AC-PNAO4 the covered word is withheld beside an unnameable"
               " label")
    ok = check(PNAO.verdict_of(PNAO.SEAMS_COVERED, {"prefix_free": True},
                               {"ack_unnameable": {}}) == PNAO.SEAMS_COVERED,
               "AC-PNAO4 a fully nameable reason still reaches the covered"
               " word") and ok
    ok = check(PNAO.verdict_of(PNAO.SEAMS_STALE, {"prefix_free": True},
                               {"ack_unnameable": {"a": PART_WORD}})
               == PNAO.SEAMS_STALE,
               "AC-PNAO4 a stale verdict is never overwritten") and ok
    labels = ["a", "ab,ac", "ab+duplicate:2"]
    counts = PNAO.ack_sibling_counts(labels)
    ok = check(counts == {"a": 2},
               "AC-PNAO4 the sibling count reads from the word (%s)"
               % (counts,)) and ok
    readings = PNAO.ack_part_readings(labels)
    ok = check(readings["a"] == {"siblings": ["ab,ac", "ab+duplicate:2"],
                                 "duplicate": None},
               "AC-PNAO4 both readings are published (%s)"
               % (readings.get("a"),)) and ok
    ok = check(PNAO.ack_fully_named(labels) is False,
               "AC-PNAO4 an unnameable label is never fully named") and ok
    ok = check(PNAO.ack_unnameable(["a", "b"]) == {},
               "AC-PNAO4 nameable labels carry no reason") and ok
    return ok


def ac_pnao5():
    """Every earlier answer rides, plus one bounded live leg on BOTH readers."""
    fixtures = [
        ["a", "ab,ac"],
        ["a", "ab", "ac"],
        ["x", "xy"],
        ["a", "a"],
        ["a", "ab", "a"],
        ["a", "ab", "ac", "ad"],
        ["p", "pq,pr", "ps"],
    ]
    ok = True
    for index, labels in enumerate(fixtures):
        mine = PNAO.ack_unnameable(labels)
        theirs = PNAL.ack_unnameable(labels)
        ok = check(mine == theirs,
                   "AC-PNAO5 the fixture %d answer rides R2685 byte for byte"
                   " (%s vs %s)" % (index, mine, theirs)) and ok
    chain = [PNAK, PNAJ, PNAI]
    for module in chain:
        same_index = (module.ack_index(["a", "ab", "ac"])
                      == PNAL.ack_index(["a", "ab", "ac"]))
        same_unmatched = (module.ack_unmatched(["a", "ab", "ac"])
                          == PNAL.ack_unmatched(["a", "ab", "ac"]))
        ok = check(same_index and same_unmatched,
                   "AC-PNAO5 the %s readers ride unchanged (index=%s "
                   "unmatched=%s)" % (module.LABEL.split("-")[-3],
                                      same_index, same_unmatched)) and ok

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
        for module in (PNAO, PNAL):
            try:
                report = module.module_alias_report(text, BASE)
            except Exception:
                unreadable += 1
                continue
            loops += len(report.get("loops") or [])
        mine = PNAO.ack_unnameable(["a", "ab+duplicate:2"])
        theirs = PNAL.ack_unnameable(["a", "ab+duplicate:2"])
        if mine == theirs:
            disagreements += 1
        if digest(path) != first_digest:
            disagreements += 1
    ok = check(loops > 0 and unreadable == 0 and disagreements == 0,
               "AC-PNAO5 a bounded live leg is read-only and BOTH readers are"
               " measured on the same fixture (modules=%d loops=%d "
               "unreadable=%d disagree=%s)"
               % (len(before), loops, unreadable, disagreements)) and ok
    ok = check(PNAL.parse_strict_prefix_word(GENUINE_WORD) == ["ab"]
               and PNAO.parse_strict_prefix_word(PART_WORD)
               == ["ab+duplicate:2"],
               "AC-PNAO5 the SAME fixture reads tail-lost there and whole here"
               " (%s vs %s)"
               % (PNAL.parse_strict_prefix_word(GENUINE_WORD),
                  PNAO.parse_strict_prefix_word(PART_WORD))) and ok
    return ok


def ac_pnao6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAO6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAO6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAO6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAO6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAO6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAO6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnao1, ac_pnao2, ac_pnao3, ac_pnao4, ac_pnao5, ac_pnao6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
