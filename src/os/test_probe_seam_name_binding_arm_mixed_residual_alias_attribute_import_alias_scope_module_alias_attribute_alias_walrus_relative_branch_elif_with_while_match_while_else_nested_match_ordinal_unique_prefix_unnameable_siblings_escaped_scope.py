"""AC-PNAL1..AC-PNAL6 suite for the escaped sibling-list ack face (R2685).

Criteria were pinned in state/queue/tech.md:680 at R2682 BEFORE this code
existed. Every fixture lives in a private temporary directory; no shipped
source file is written. Stdlib only, ASCII source, zero network, no clock.
Exit 0 = all green.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_scope as PNAK  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_scope as PNAJ  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_scope as PNAI  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_scope as PNAG  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_while_match_while_else_nested_"
               "match_ordinal_unique_prefix_unnameable_siblings_escaped_"
               "scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-while-match-'
               'while-else-nested-match-ordinal-unique-prefix-unnameable-'
               'siblings-escaped-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_while_match_while_else_'
               'nested_match_ordinal_unique_prefix_unnameable_siblings_'
               'escaped_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"
LIVE_MODULES = [
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_two_level_scope",
]
HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")

THREE_BINDINGS = ("import consts\nimport consts2\nimport consts3\n"
                  "while a1:\n"
                  "    match x:\n        case 1:\n            (M := consts)\n"
                  "    match y:\n        case 1:\n            (M := consts2)\n"
                  "while a2:\n"
                  "    match z:\n        case 1:\n            (M := consts3)\n"
                  "BASE = M.HW\nREG = BASE\n")
ELSE_TWO = ("import consts\nimport consts2\n"
            "while a1:\n    pass\nelse:\n"
            "    match x:\n        case 1:\n            (M := consts)\n"
            "    match y:\n        case 1:\n            (M := consts2)\n"
            "BASE = M.HW\nREG = BASE\n")
FOR_IN_WHILE = ("import consts\nwhile a1:\n"
                "    for a2 in items:\n        match x:\n"
                "            case 1:\n                (M := consts)\n"
                "BASE = M.HW\nREG = BASE\n")
WHILE_IN_WHILE = ("import consts\nwhile a1:\n"
                  "    while a2:\n        match x:\n"
                  "            case 1:\n                (M := consts)\n"
                  "BASE = M.HW\nREG = BASE\n")
IF_IN_CASE = ("import consts\nwhile a1:\n"
              "    match x:\n        case 1:\n"
              "            if a2:\n                (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")

ESCAPED_COMMA_WORD = "strict-prefix-of:ab\\,ac"
PLAIN_TWO_WORD = "strict-prefix-of:ab,ac"
SINGLE_WORD = "strict-prefix-of:xy"


def world(files):
    root = tempfile.mkdtemp(prefix="pnal-")
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


def entry(module, text, root):
    rows = module.module_alias_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return module.module_alias_entry("KEY", text, row["scope"], row["line"],
                                     root=root)


def ac_pnal1():
    """One name carrying the separator is never read as two siblings."""
    got = PNAL.ack_unnameable(["a", "ab,ac"])
    ok = check(got == {"a": ESCAPED_COMMA_WORD},
               "AC-PNAL1 one sibling carrying a comma is escaped (%s)"
               % (got,))
    ok = check(got.get("a") != PLAIN_TWO_WORD,
               "AC-PNAL1 the word differs from the two-sibling word") and ok
    ok = check(PNAL.sibling_count_from_word(ESCAPED_COMMA_WORD) == 1,
               "AC-PNAL1 the escaped word names ONE sibling (%s)"
               % (PNAL.sibling_count_from_word(ESCAPED_COMMA_WORD),)) and ok
    ok = check(PNAL.parse_strict_prefix_word(ESCAPED_COMMA_WORD)
               == ["ab,ac"],
               "AC-PNAL1 the round trip recovers the whole label (%s)"
               % (PNAL.parse_strict_prefix_word(ESCAPED_COMMA_WORD),)) and ok
    two = PNAL.ack_unnameable(["a", "ab,ac", "ad"])
    ok = check(two == {"a": "strict-prefix-of:ab\\,ac,ad"}
               and PNAL.sibling_count_from_word(two.get("a", "")) == 2
               and PNAL.parse_strict_prefix_word(two.get("a", ""))
               == ["ab,ac", "ad"],
               "AC-PNAL1 the separator does not swallow the next sibling "
               "(%s)" % (two,)) and ok
    return ok


def ac_pnal2():
    """The ordinary two-sibling word stays byte for byte what R2682 gave."""
    for labels in (["a", "ab", "ac"],
                   ["a", "ab", "ac", "ad"],
                   ["a", "ac", "ab"]):
        mine = PNAL.ack_unnameable(labels)
        theirs = PNAK.ack_unnameable(labels)
        ok = check(mine == theirs,
                   "AC-PNAL2 %s rides R2682 byte for byte (%s vs %s)"
                   % (labels, mine, theirs))
        if not ok:
            return False
    ok = check(PNAL.ack_unnameable(["a", "ab", "ac"])
               == {"a": PLAIN_TWO_WORD},
               "AC-PNAL2 the two-sibling word is still %s" % (PLAIN_TWO_WORD,))
    ok = check(PNAL.sibling_count_from_word(PLAIN_TWO_WORD) == 2,
               "AC-PNAL2 a plain word still names two siblings") and ok
    return ok


def ac_pnal3():
    """The single-sibling word stays byte for byte what R2679 published."""
    mine = PNAL.ack_unnameable(["x", "xy"])
    theirs = PNAJ.ack_unnameable(["x", "xy"])
    ok = check(mine == theirs == {"x": SINGLE_WORD},
               "AC-PNAL3 the single-sibling word is byte identical to "
               "R2679 (%s vs %s)" % (mine, theirs))
    ok = check(PNAL.strict_prefix_sibling("x", ["x", "xy"]) == "xy"
               and PNAL.strict_prefix_siblings("x", ["x", "xy"]) == ["xy"],
               "AC-PNAL3 the first-sibling readers are carried unchanged") and ok
    ok = check(PNAL.sibling_count_from_word(SINGLE_WORD) == 1,
               "AC-PNAL3 the single word names one sibling") and ok
    return ok


def ac_pnal4():
    """The duplicate count rides beside the list; the covered word is withheld."""
    both = PNAL.ack_unnameable(["a", "a", "ab,ac"])
    ok = check(both == {"a": ESCAPED_COMMA_WORD + "+duplicate:2"},
               "AC-PNAL4 a duplicate and an escaped sibling both ride (%s)"
               % (both,))
    word = both.get("a", "")
    ok = check("duplicate:2" in word and ESCAPED_COMMA_WORD in word,
               "AC-PNAL4 the list and the count are both present (%s)"
               % (word,)) and ok
    ok = check(PNAL.sibling_count_from_word(word) == 1,
               "AC-PNAL4 the count is read past the list safely (%s)"
               % (PNAL.parse_strict_prefix_word(word),)) and ok
    ok = check(PNAL.ack_unnameable(["a", "a"]) == {"a": "duplicate:2"},
               "AC-PNAL4 a duplicate with no sibling keeps its own word")
    ok = check(PNAL.ack_fully_named(["alpha", "beta"]) is True
               and PNAL.ack_unnameable(["alpha", "beta"]) == {},
               "AC-PNAL4 nameable labels carry no reason") and ok
    ok = check(PNAL.ack_fully_named(["a", "ab,ac"]) is False,
               "AC-PNAL4 an unnameable label is never fully named") and ok
    blocked = PNAL.verdict_of(PNAL.SEAMS_COVERED, {"prefix_free": True},
                              {"ack_unnameable": {"a": ESCAPED_COMMA_WORD}})
    ok = check(blocked == PNAL.SEAMS_UNNAMEABLE,
               "AC-PNAL4 the covered word is withheld beside an unnameable "
               "label (%s)" % (blocked,)) and ok
    kept = PNAL.verdict_of(PNAL.SEAMS_COVERED, {"prefix_free": True},
                           {"ack_unnameable": {}})
    ok = check(kept == PNAL.SEAMS_COVERED,
               "AC-PNAL4 a fully nameable reason still reaches the covered "
               "word (%s)" % (kept,)) and ok
    stale = PNAL.verdict_of(PNAL.SEAMS_STALE, {"prefix_free": True},
                            {"ack_unnameable": {"a": "duplicate:2"}})
    ok = check(stale == PNAL.SEAMS_STALE,
               "AC-PNAL4 a stale verdict is never overwritten (%s)"
               % (stale,)) and ok
    return ok


def ac_pnal5():
    """Every earlier answer rides unchanged, plus one bounded live leg."""
    ok = True
    keys = ("reason", "ack_labels", "ack_prefixes", "ack_unmatched",
            "ack_prefix_free", "ack_unnameable", "ack_fully_named")
    for label, body in (("three-binding", THREE_BINDINGS),
                        ("else pair", ELSE_TWO)):
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n',
                      "consts3.py": 'HW = "hw3"\n', "mk.py": body})
        try:
            mine = entry(PNAL, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAK, "import mk\n" + RECV + TAIL, root)
            base = entry(PNAI, "import mk\n" + RECV + TAIL, root)
            same = all(mine.get(key) == near.get(key) for key in keys)
            ok = check(same,
                       "AC-PNAL5 the %s answer rides PNAK byte for byte (%s)"
                       % (label, mine.get("ack_prefixes"))) and ok
            ok = check(mine.get("ack_prefixes") == base.get("ack_prefixes"),
                       "AC-PNAL5 the %s prefixes ride PNAI byte for byte "
                       "(%s)" % (label, mine.get("ack_prefixes"))) and ok
            counts = mine.get("ack_sibling_counts") or {}
            wants = {name: len(PNAL.strict_prefix_siblings(name,
                                                           PNAL.labels_of_reason(
                                                               mine.get("reason"))))
                     for name in (mine.get("ack_unnameable") or {})}
            ok = check(counts == wants,
                       "AC-PNAL5 the %s sibling counts are derived (%s vs %s)"
                       % (label, counts, wants)) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    for label, body in (("for body in a while", FOR_IN_WHILE),
                        ("while in a while", WHILE_IN_WHILE),
                        ("if inside a match case", IF_IN_CASE)):
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            mine = entry(PNAL, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAG, "import mk\n" + RECV + TAIL, root)
            ok = check(mine.get("reason") == near.get("reason")
                       == "attr-module-alias-unbound:M.HW"
                       and mine.get("state") == PNAL.STATE_REFUSED
                       and mine.get("ack_unnameable") == {}
                       and mine.get("ack_sibling_counts") == {},
                       "AC-PNAL5 a %s keeps the parked refusal with no ack "
                       "labels (%s)" % (label, mine.get("reason"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    loops = 0
    unreadable = 0
    changed = []
    disagree = []
    for name in LIVE_MODULES:
        path = os.path.join(BASE, name + ".py")
        if not os.path.isfile(path):
            unreadable += 1
            continue
        before = read_bytes(path)
        text = before.decode("utf-8")
        rows = PNAL.module_alias_report(text, BASE, path)["loops"]
        shipped = PNAG.module_alias_report(text, BASE, path)["loops"]
        loops += len(rows)
        if len(rows) != len(shipped):
            disagree.append(name)
        if read_bytes(path) != before:
            changed.append(name)
    ok = check(unreadable == 0 and loops > 0 and not changed and not disagree,
               "AC-PNAL5 a bounded live leg rides unchanged and read-only "
               "(modules=%d loops=%d unreadable=%d changed=%s disagree=%s)"
               % (len(LIVE_MODULES), loops, unreadable, changed,
                  disagree)) and ok
    return ok


def ac_pnal6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAL6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAL6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAL6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAL6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAL6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAL6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnal1, ac_pnal2, ac_pnal3, ac_pnal4, ac_pnal5, ac_pnal6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
