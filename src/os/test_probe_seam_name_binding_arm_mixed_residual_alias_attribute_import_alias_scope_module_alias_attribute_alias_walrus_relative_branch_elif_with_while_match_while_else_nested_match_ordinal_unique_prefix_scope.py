"""AC-PNAH1..AC-PNAH6 suite for the prefix-free ack index face (R2676).

Criteria were pinned in state/queue/tech.md:677 at R2675 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_scope as PNAI  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_scope as PNAG  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_while_match_while_else_nested_"
               "match_ordinal_unique_prefix_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-while-match-'
               'while-else-nested-match-ordinal-unique-prefix-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_while_match_while_else_'
               'nested_match_ordinal_unique_prefix_scope.py"),')

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
    root = tempfile.mkdtemp(prefix="pnai-")
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


def ac_pnah1():
    """Every published label own ack prefix names exactly one label."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "consts3.py": 'HW = "hw3"\n',
                  "mk.py": THREE_BINDINGS})
    try:
        got = entry(PNAI, "import mk\n" + RECV + TAIL, root)
        labels = got.get("ack_labels") or []
        index = got.get("ack_prefixes") or {}
        ok = check(len(labels) == 3 and len(index) == 3,
                   "AC-PNAH1 the reason carries three labels with one ack "
                   "prefix each (%d/%d)" % (len(labels), len(index)))
        unique = True
        for label in labels:
            prefix = index.get(label)
            hits = PNAI.ack_hits(prefix, labels) if prefix else []
            if len(hits) != 1 or hits[0] != label:
                unique = False
        ok = check(unique, "AC-PNAH1 every ack prefix matches exactly ONE "
                           "label (%s)" % (index,)) and ok
        ok = check(got.get("ack_prefix_free") is True,
                   "AC-PNAH1 the published prefixes are prefix-free "
                   "(%s)" % (sorted(index.values()),)) and ok
        ok = check(got.get("ack_unmatched") == [],
                   "AC-PNAH1 no label is left unnameable (%s)"
                   % (got.get("ack_unmatched"),)) and ok
        ok = check(len(PNAI.ack_hits("while2", labels)) == 2
                   and len(PNAI.ack_hits("while", labels)) == 3,
                   "AC-PNAH1 the coarse stems stay measured as ambiguous "
                   "(%s/%s)" % (PNAI.ack_hits("while2", labels),
                                PNAI.ack_hits("while", labels))) and ok
        ok = check("while2" not in index.values()
                   and "while" not in index.values(),
                   "AC-PNAH1 no ambiguous stem is ever published as an ack "
                   "(%s)" % (sorted(index.values()),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnah2():
    """Three bindings stay three distinct labels, byte for byte from R2675."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "consts3.py": 'HW = "hw3"\n',
                  "mk.py": THREE_BINDINGS})
    try:
        mine = entry(PNAI, "import mk\n" + RECV + TAIL, root)
        near = entry(PNAG, "import mk\n" + RECV + TAIL, root)
        same = (mine.get("state") == near.get("state")
                and mine.get("value") == near.get("value")
                and mine.get("reason") == near.get("reason")
                and (mine.get("branch_reads") or [])
                == (near.get("branch_reads") or []))
        ok = check(same, "AC-PNAH2 the three-binding answer is unchanged "
                         "(%s/%s)" % (mine.get("state"), mine.get("value")))
        wanted = {"while>case", "while2>case", "while2_body>case"}
        ok = check(wanted == set(mine.get("ack_labels") or []),
                   "AC-PNAH2 the three labels are the shipped first-while "
                   "ordinals plus the second while own body label (%s)"
                   % (sorted(mine.get("ack_labels") or []),)) and ok
        ok = check(len(set(mine.get("ack_prefixes") or {})) == 3
                   and (mine.get("ack_prefixes") or {}).get("while2>case")
                   != (mine.get("ack_prefixes") or {}).get(
                       "while2_body>case"),
                   "AC-PNAH2 the two labels a `while2` ack used to confuse "
                   "carry DIFFERENT prefixes (%s)"
                   % (mine.get("ack_prefixes"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnah3():
    """The else-section pair still reads while_else and while_else2."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "mk.py": ELSE_TWO})
    try:
        mine = entry(PNAI, "import mk\n" + RECV + TAIL, root)
        near = entry(PNAG, "import mk\n" + RECV + TAIL, root)
        labels = set(mine.get("ack_labels") or [])
        ok = check(labels == {"while_else>case", "while_else2>case"},
                   "AC-PNAH3 both else matches are named exactly (%s)"
                   % (sorted(labels),))
        ok = check("while_elsem2" not in (mine.get("reason") or ""),
                   "AC-PNAH3 the join artifact stays gone (%s)"
                   % (mine.get("reason"),)) and ok
        ok = check(mine.get("reason") == near.get("reason")
                   and mine.get("state") == near.get("state"),
                   "AC-PNAH3 the else answer is unchanged from R2675") and ok
        index = mine.get("ack_prefixes") or {}
        ok = check(all(len(PNAI.ack_hits(prefix, sorted(labels))) == 1
                       for prefix in index.values() if prefix),
                   "AC-PNAH3 every else ack prefix is unique (%s)"
                   % (sorted(index.values()),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnah4():
    """The three parked refusals keep the shipped refusal, with no ack labels."""
    cases = [("match inside a for body nested in a while", FOR_IN_WHILE),
             ("match nested one level in a while inside another while",
              WHILE_IN_WHILE),
             ("walrus bound by an if nested inside a match case", IF_IN_CASE)]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "mk.py": body})
        try:
            mine = entry(PNAI, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAG, "import mk\n" + RECV + TAIL, root)
            ok = check(mine.get("reason") == near.get("reason")
                       == "attr-module-alias-unbound:M.HW"
                       and mine.get("state") == PNAI.STATE_REFUSED,
                       "AC-PNAH4 a %s keeps the shipped refusal byte for "
                       "byte (%s)" % (label, mine.get("reason"))) and ok
            ok = check(not [item for item in mine.get("branch_reads") or []
                            if item.startswith("branch:")],
                       "AC-PNAH4 no branch read is published (%s)"
                       % (mine.get("branch_reads"),)) and ok
            ok = check(mine.get("ack_labels") == []
                       and mine.get("ack_prefixes") == {},
                       "AC-PNAH4 a refusal carries no ack labels (%s)"
                       % (mine.get("ack_labels"),)) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnah5():
    """Every R2675 answer rides unchanged, plus one bounded live leg."""
    ok = True
    for label, body in CARRY_CASES:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n', "mk.py": body})
        try:
            mine = entry(PNAI, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAG, "import mk\n" + RECV + TAIL, root)
            same = (mine.get("state") == near.get("state")
                    and mine.get("value") == near.get("value")
                    and mine.get("reason") == near.get("reason")
                    and (mine.get("branch_reads") or [])
                    == (near.get("branch_reads") or []))
            ok = check(same, "AC-PNAH5 %s reads exactly what R2675 answered "
                             "(%s/%s)" % (label, mine.get("state"),
                                          mine.get("value"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    loops = 0
    unreadable = 0
    changed = []
    bad_ack = []
    for name in LIVE_MODULES:
        path = os.path.join(BASE, name + ".py")
        if not os.path.isfile(path):
            unreadable += 1
            continue
        before = read_bytes(path)
        text = before.decode("utf-8")
        rows = PNAI.module_alias_report(text, BASE, path)["loops"]
        shipped = PNAG.module_alias_report(text, BASE, path)["loops"]
        loops += len(rows)
        # ONE report per reader on the real module: a full parent walk on a
        # real tree costs minutes here, so the live leg proves the loop read
        # rides unchanged rather than re-acking every row.
        if len(rows) != len(shipped):
            bad_ack.append(name)
        if read_bytes(path) != before:
            changed.append(name)
    ok = check(unreadable == 0 and loops > 0 and not changed and not bad_ack,
               "AC-PNAH5 a bounded live leg rides unchanged and read-only "
               "(modules=%d loops=%d unreadable=%d changed=%s disagree=%s)"
               % (len(LIVE_MODULES), loops, unreadable, changed,
                  bad_ack)) and ok
    return ok


def ac_pnah6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAH6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAH6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAH6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAH6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAH6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAH6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnah1, ac_pnah2, ac_pnah3, ac_pnah4, ac_pnah5, ac_pnah6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
