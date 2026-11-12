"""AC-PNAJ1..AC-PNAJ6 suite for the unnameable-label ack face (R2679).

Criteria were pinned in state/queue/tech.md:677 at R2678 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_scope as PNAJ  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_scope as PNAI  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_scope as PNAG  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_while_match_while_else_nested_"
               "match_ordinal_unique_prefix_unnameable_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-while-match-'
               'while-else-nested-match-ordinal-unique-prefix-unnameable-'
               'scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_while_match_while_else_'
               'nested_match_ordinal_unique_prefix_unnameable_scope.py"),')

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
IF_ONE = ("import consts\nif a1:\n    (M := consts)\n"
          "BASE = M.HW\nREG = BASE\n")
WITH_ONE = ("import consts\nwith a1:\n    (M := consts)\n"
            "BASE = M.HW\nREG = BASE\n")
WHILE_ONE = ("import consts\nwhile a1:\n    (M := consts)\n"
             "BASE = M.HW\nREG = BASE\n")
WHILE_ELSE = ("import consts\nwhile a1:\n    pass\nelse:\n    (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
WHILE_TWO = ("import consts\nimport consts2\nwhile a1:\n    (M := consts)\n"
             "while a2:\n    (M := consts2)\nBASE = M.HW\nREG = BASE\n")
CASE_ONE = ("import consts\nmatch x:\n    case 1:\n        (M := consts)\n"
            "BASE = M.HW\nREG = BASE\n")
NESTED_CASE = ("import consts\nwhile a1:\n"
               "    match x:\n        case 1:\n            (M := consts)\n"
               "BASE = M.HW\nREG = BASE\n")
TWO_MATCHES_ONE_WHILE = ("import consts\nimport consts2\n"
                         "while a1:\n"
                         "    match x:\n        case 1:\n"
                         "            (M := consts)\n"
                         "    match y:\n        case 1:\n"
                         "            (M := consts2)\n"
                         "BASE = M.HW\nREG = BASE\n")

CARRY_CASES = [("module-level if branch", IF_ONE),
               ("while else direct walrus", WHILE_ELSE),
               ("two matches in ONE while", TWO_MATCHES_ONE_WHILE)]


def world(files):
    root = tempfile.mkdtemp(prefix="pnaj-")
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


def ac_pnaj1():
    """A strict-prefix sibling is named unnameable and NEVER reads COVERED."""
    ok = check(PNAJ.ack_unnameable(["x", "xy"]) == {"x": "strict-prefix-of:xy"},
               "AC-PNAJ1 a strict-prefix label carries its OWN word (%s)"
               % (PNAJ.ack_unnameable(["x", "xy"]),))
    ok = check(PNAJ.ack_fully_named(["x", "xy"]) is False,
               "AC-PNAJ1 the reason is NOT fully named (%s)"
               % (PNAJ.ack_fully_named(["x", "xy"]),)) and ok
    ok = check(PNAJ.unnameable_reason("x", ["x", "xy"])
               == "strict-prefix-of:xy"
               and PNAJ.unnameable_reason("xy", ["x", "xy"]) is None,
               "AC-PNAJ1 only the prefix side is unnameable, the sibling is "
               "not (%s/%s)" % (PNAJ.unnameable_reason("x", ["x", "xy"]),
                                PNAJ.unnameable_reason("xy", ["x", "xy"]))) and ok
    verdict = PNAJ.verdict_of(PNAI.SEAMS_PREFIX_COVERED,
                              {"prefix_free": True},
                              {"ack_unnameable": {"x": "strict-prefix-of:xy"}})
    ok = check(verdict != PNAJ.SEAMS_COVERED
               and verdict == PNAJ.SEAMS_UNNAMEABLE,
               "AC-PNAJ1 a healthy prefix set beside an unnameable label "
               "reads %s, never the covered word"
               % (verdict,)) and ok
    return ok


def ac_pnaj2():
    """Two copies of one label are named by their own word, not merged."""
    got = PNAJ.ack_unnameable(["a", "a"])
    ok = check(got == {"a": "duplicate:2"},
               "AC-PNAJ2 a duplicated label carries a duplicate word with "
               "its count (%s)" % (got,))
    ok = check(PNAJ.duplicate_count("a", ["a", "a"]) == 2
               and PNAJ.duplicate_count("a", ["a"]) == 1,
               "AC-PNAJ2 the count is measured rather than assumed") and ok
    ok = check(PNAJ.ack_fully_named(["a", "a"]) is False
               and PNAJ.ack_fully_named(["a"]) is True,
               "AC-PNAJ2 a duplicate is never fully named, a single one is") and ok
    verdict = PNAJ.verdict_of(PNAI.SEAMS_PREFIX_COVERED, {"prefix_free": True},
                              {"ack_unnameable": got})
    ok = check(verdict == PNAJ.SEAMS_UNNAMEABLE,
               "AC-PNAJ2 a duplicate label withholds the covered word (%s)"
               % (verdict,)) and ok
    ok = check(PNAJ.ack_unnameable(["a", "a"]) != PNAJ.ack_unnameable(["x", "xy"]),
               "AC-PNAJ2 the two shapes carry DIFFERENT words rather than one "
               "generic refusal") and ok
    return ok


def ac_pnaj3():
    """The three-binding and else fixtures publish the R2678 prefixes."""
    ok = True
    for label, body in (("three-binding", THREE_BINDINGS),
                        ("else pair", ELSE_TWO)):
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n',
                      "consts3.py": 'HW = "hw3"\n', "mk.py": body})
        try:
            mine = entry(PNAJ, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAI, "import mk\n" + RECV + TAIL, root)
            ok = check(mine.get("ack_prefixes") == near.get("ack_prefixes")
                       and mine.get("ack_labels") == near.get("ack_labels"),
                       "AC-PNAJ3 the %s prefixes ride byte for byte (%s)"
                       % (label, mine.get("ack_prefixes"))) and ok
            ok = check(mine.get("ack_unnameable") == {}
                       and mine.get("ack_fully_named") is True,
                       "AC-PNAJ3 the %s labels are all nameable, so nothing "
                       "is newly withheld" % (label,)) and ok
            ok = check(mine.get("ack_prefix_free") is True,
                       "AC-PNAJ3 the %s prefixes stay prefix-free (%s)"
                       % (label, sorted(
                           (mine.get("ack_prefixes") or {}).values()))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaj4():
    """The three parked refusals keep the shipped refusal, no ack labels."""
    cases = [("match inside a for body nested in a while", FOR_IN_WHILE),
             ("match nested one level in a while inside another while",
              WHILE_IN_WHILE),
             ("walrus bound by an if nested inside a match case", IF_IN_CASE)]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            mine = entry(PNAJ, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAG, "import mk\n" + RECV + TAIL, root)
            ok = check(mine.get("reason") == near.get("reason")
                       == "attr-module-alias-unbound:M.HW"
                       and mine.get("state") == PNAJ.STATE_REFUSED,
                       "AC-PNAJ4 a %s keeps the shipped refusal byte for "
                       "byte (%s)" % (label, mine.get("reason"))) and ok
            ok = check(not [item for item in (mine.get("branch_reads") or [])
                            if str(item).startswith("branch:")],
                       "AC-PNAJ4 no branch read is published (%s)"
                       % (mine.get("branch_reads"),)) and ok
            ok = check(mine.get("ack_labels") == []
                       and mine.get("ack_prefixes") == {}
                       and mine.get("ack_unnameable") == {},
                       "AC-PNAJ4 a refusal carries no ack labels and no "
                       "unnameable labels (%s/%s)"
                       % (mine.get("ack_labels"),
                          mine.get("ack_unnameable"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaj5():
    """Every R2675/R2678 answer rides unchanged, plus one bounded live leg."""
    ok = True
    for label, body in CARRY_CASES:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n', "mk.py": body})
        try:
            mine = entry(PNAJ, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAG, "import mk\n" + RECV + TAIL, root)
            same = (mine.get("state") == near.get("state")
                    and mine.get("value") == near.get("value")
                    and mine.get("reason") == near.get("reason")
                    and (mine.get("branch_reads") or [])
                    == (near.get("branch_reads") or []))
            ok = check(same, "AC-PNAJ5 %s reads exactly what R2675 answered "
                             "(%s/%s)" % (label, mine.get("state"),
                                          mine.get("value"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    for label, body in (("three-binding", THREE_BINDINGS),
                        ("else pair", ELSE_TWO)):
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n',
                      "consts3.py": 'HW = "hw3"\n', "mk.py": body})
        try:
            mine = entry(PNAJ, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAI, "import mk\n" + RECV + TAIL, root)
            same = (mine.get("state") == near.get("state")
                    and mine.get("reason") == near.get("reason")
                    and mine.get("ack_prefixes") == near.get("ack_prefixes")
                    and mine.get("ack_unmatched") == near.get("ack_unmatched"))
            ok = check(same, "AC-PNAJ5 the %s answer is unchanged from R2678 "
                             "(%s)" % (label, mine.get("state"))) and ok
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
        rows = PNAJ.module_alias_report(text, BASE, path)["loops"]
        shipped = PNAG.module_alias_report(text, BASE, path)["loops"]
        loops += len(rows)
        if len(rows) != len(shipped):
            disagree.append(name)
        if read_bytes(path) != before:
            changed.append(name)
    ok = check(unreadable == 0 and loops > 0 and not changed and not disagree,
               "AC-PNAJ5 a bounded live leg rides unchanged and read-only "
               "(modules=%d loops=%d unreadable=%d changed=%s disagree=%s)"
               % (len(LIVE_MODULES), loops, unreadable, changed,
                  disagree)) and ok
    return ok


def ac_pnaj6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAJ6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAJ6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAJ6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAJ6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAJ6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAJ6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnaj1, ac_pnaj2, ac_pnaj3, ac_pnaj4, ac_pnaj5, ac_pnaj6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
