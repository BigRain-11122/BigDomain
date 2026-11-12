"""AC-PNAK1..AC-PNAK6 suite for the sibling-list ack face (R2682).

Criteria were pinned in state/queue/tech.md:679 at R2679 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_scope as PNAK  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_scope as PNAJ  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_scope as PNAI  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_scope as PNAG  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_while_match_while_else_nested_"
               "match_ordinal_unique_prefix_unnameable_siblings_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-while-match-'
               'while-else-nested-match-ordinal-unique-prefix-unnameable-'
               'siblings-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_while_match_while_else_'
               'nested_match_ordinal_unique_prefix_unnameable_siblings_'
               'scope.py"),')

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


def world(files):
    root = tempfile.mkdtemp(prefix="pnak-")
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


def ac_pnak1():
    """A label strict prefix of TWO siblings names BOTH, in published order."""
    two = PNAK.ack_unnameable(["a", "ab", "ac"])
    ok = check(two == {"a": "strict-prefix-of:ab,ac"},
               "AC-PNAK1 a strict prefix of two siblings names BOTH (%s)"
               % (two,))
    three = PNAK.ack_unnameable(["a", "ab", "ac", "ad"])
    ok = check(three == {"a": "strict-prefix-of:ab,ac,ad"},
               "AC-PNAK1 a third sibling is named too (%s)" % (three,)) and ok
    flipped = PNAK.ack_unnameable(["a", "ac", "ab"])
    ok = check(flipped == {"a": "strict-prefix-of:ac,ab"},
               "AC-PNAK1 the list follows PUBLISHED order, not sorted (%s)"
               % (flipped,)) and ok
    ok = check(PNAK.strict_prefix_siblings("a", ["a", "ab", "ac"])
               == ["ab", "ac"],
               "AC-PNAK1 the sibling reader answers the list in order") and ok
    return ok


def ac_pnak2():
    """Two copies AND two siblings keep the count AND the full list."""
    got = PNAK.ack_unnameable(["a", "a", "ab", "ac"])
    ok = check(got == {"a": "strict-prefix-of:ab,ac+duplicate:2"},
               "AC-PNAK2 two copies plus two siblings keep both (%s)"
               % (got,))
    word = got.get("a", "")
    ok = check("duplicate:2" in word and "ab,ac" in word,
               "AC-PNAK2 the count and the full sibling list both ride "
               "(%s)" % (word,)) and ok
    dup_only = PNAK.ack_unnameable(["a", "a"])
    ok = check(dup_only == {"a": "duplicate:2"},
               "AC-PNAK2 a duplicate with no sibling keeps its own word "
               "(%s)" % (dup_only,)) and ok
    return ok


def ac_pnak3():
    """The single-sibling word stays byte for byte what R2679 published."""
    mine = PNAK.ack_unnameable(["x", "xy"])
    theirs = PNAJ.ack_unnameable(["x", "xy"])
    ok = check(mine == theirs == {"x": "strict-prefix-of:xy"},
               "AC-PNAK3 the single-sibling word is byte identical to "
               "R2679 (%s vs %s)" % (mine, theirs))
    ok = check(PNAK.strict_prefix_sibling("x", ["x", "xy"]) == "xy"
               and PNAK.strict_prefix_siblings("x", ["x", "xy"]) == ["xy"],
               "AC-PNAK3 the first-sibling reader is carried unchanged") and ok
    return ok


def ac_pnak4():
    """Nameable labels keep None; the covered word is withheld when needed."""
    ok = check(PNAK.ack_unnameable(["alpha", "beta"]) == {},
               "AC-PNAK4 nameable labels carry no reason (%s)"
               % (PNAK.ack_unnameable(["alpha", "beta"]),))
    ok = check(PNAK.ack_fully_named(["alpha", "beta"]) is True,
               "AC-PNAK4 a nameable reason is fully named") and ok
    ok = check(PNAK.ack_fully_named(["a", "ab", "ac"]) is False,
               "AC-PNAK4 an unnameable label is never fully named") and ok
    blocked = PNAK.verdict_of(PNAK.SEAMS_COVERED, {"prefix_free": True},
                              {"ack_unnameable":
                               {"a": "strict-prefix-of:ab,ac"}})
    ok = check(blocked == PNAK.SEAMS_UNNAMEABLE,
               "AC-PNAK4 the covered word is withheld beside an unnameable "
               "label (%s)" % (blocked,)) and ok
    kept = PNAK.verdict_of(PNAK.SEAMS_COVERED, {"prefix_free": True},
                           {"ack_unnameable": {}})
    ok = check(kept == PNAK.SEAMS_COVERED,
               "AC-PNAK4 a fully nameable reason still reaches the covered "
               "word (%s)" % (kept,)) and ok
    stale = PNAK.verdict_of(PNAK.SEAMS_STALE, {"prefix_free": True},
                            {"ack_unnameable": {"a": "duplicate:2"}})
    ok = check(stale == PNAK.SEAMS_STALE,
               "AC-PNAK4 a stale verdict is never overwritten (%s)"
               % (stale,)) and ok
    return ok


def ac_pnak5():
    """Every earlier answer rides unchanged, plus one bounded live leg."""
    ok = True
    for label, body in (("three-binding", THREE_BINDINGS),
                        ("else pair", ELSE_TWO)):
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n',
                      "consts3.py": 'HW = "hw3"\n', "mk.py": body})
        try:
            mine = entry(PNAK, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAJ, "import mk\n" + RECV + TAIL, root)
            base = entry(PNAI, "import mk\n" + RECV + TAIL, root)
            keys = ("reason", "ack_labels", "ack_prefixes", "ack_unmatched",
                    "ack_prefix_free", "ack_unnameable", "ack_fully_named")
            same = all(mine.get(key) == near.get(key) for key in keys)
            ok = check(same,
                       "AC-PNAK5 the %s answer rides PNAJ byte for byte (%s)"
                       % (label, mine.get("ack_prefixes"))) and ok
            ok = check(mine.get("ack_prefixes") == base.get("ack_prefixes"),
                       "AC-PNAK5 the %s prefixes ride PNAI byte for byte "
                       "(%s)" % (label, mine.get("ack_prefixes"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    parked = [("for body in a while", FOR_IN_WHILE),
              ("while in a while", WHILE_IN_WHILE),
              ("if inside a match case", IF_IN_CASE)]
    for label, body in parked:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            mine = entry(PNAK, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAG, "import mk\n" + RECV + TAIL, root)
            ok = check(mine.get("reason") == near.get("reason")
                       == "attr-module-alias-unbound:M.HW"
                       and mine.get("state") == PNAK.STATE_REFUSED
                       and mine.get("ack_unnameable") == {},
                       "AC-PNAK5 a %s keeps the parked refusal with no ack "
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
        rows = PNAK.module_alias_report(text, BASE, path)["loops"]
        shipped = PNAG.module_alias_report(text, BASE, path)["loops"]
        loops += len(rows)
        if len(rows) != len(shipped):
            disagree.append(name)
        if read_bytes(path) != before:
            changed.append(name)
    ok = check(unreadable == 0 and loops > 0 and not changed and not disagree,
               "AC-PNAK5 a bounded live leg rides unchanged and read-only "
               "(modules=%d loops=%d unreadable=%d changed=%s disagree=%s)"
               % (len(LIVE_MODULES), loops, unreadable, changed,
                  disagree)) and ok
    return ok


def ac_pnak6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-PNAK6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAK6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAK6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAK6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAK6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAK6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnak1, ac_pnak2, ac_pnak3, ac_pnak4, ac_pnak5, ac_pnak6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
