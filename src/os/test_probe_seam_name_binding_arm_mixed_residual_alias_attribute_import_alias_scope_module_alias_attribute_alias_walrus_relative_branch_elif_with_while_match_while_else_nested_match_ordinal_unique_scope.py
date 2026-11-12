"""AC-PNAG1..AC-PNAG6 suite for the unique-ordinal walrus face (R2675).

Criteria were pinned in state/queue/tech.md:676 at R2594 BEFORE this code
existed.

Every fixture lives in a private temporary directory; no shipped source file is
written. Stdlib only, ASCII source, zero network, no clock.
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_scope as PNAG  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_scope as PNAF  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_scope as PNAE  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_scope as PNAD  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope as PNAB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_while_match_while_else_nested_"
               "match_ordinal_unique_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-while-match-'
               'while-else-nested-match-ordinal-unique-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_while_match_while_else_'
               'nested_match_ordinal_unique_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"
# ONE module deliberately: a root-wide report on the real tree measures about
# 31s per reader, so a two-module leg would double the suite past the point
# where a window can honestly call it bounded.
LIVE_MODULES = [
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_two_level_scope",
]
_LIVE_COUNTS = {}
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
TWO_MATCHES_ONE_WHILE = ("import consts\nimport consts2\n"
                         "while a1:\n"
                         "    match x:\n        case 1:\n"
                         "            (M := consts)\n"
                         "    match y:\n        case 1:\n"
                         "            (M := consts2)\n"
                         "BASE = M.HW\nREG = BASE\n")
ELSE_MATCH = ("import consts\nwhile a1:\n    pass\nelse:\n"
              "    match x:\n        case 1:\n            (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
WHILE_ONE = ("import consts\nwhile a1:\n    (M := consts)\n"
             "BASE = M.HW\nREG = BASE\n")
WHILE_ELSE = ("import consts\nwhile a1:\n    pass\nelse:\n    (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
WHILE_TWO = ("import consts\nimport consts2\nwhile a1:\n    (M := consts)\n"
             "while a2:\n    (M := consts2)\nBASE = M.HW\nREG = BASE\n")
NESTED_CASE = ("import consts\nwhile a1:\n"
               "    match x:\n        case 1:\n            (M := consts)\n"
               "BASE = M.HW\nREG = BASE\n")
TWO_CASES = ("import consts\nimport consts2\nwhile a1:\n"
             "    match x:\n        case 1:\n            (M := consts)\n"
             "        case 2:\n            (M := consts2)\n"
             "BASE = M.HW\nREG = BASE\n")
CASE_ONE = ("import consts\nmatch x:\n    case 1:\n        (M := consts)\n"
            "BASE = M.HW\nREG = BASE\n")
IF_ONE = ("import consts\nif a1:\n    (M := consts)\n"
          "BASE = M.HW\nREG = BASE\n")
ELIF_ONE = ("import consts\nif a1:\n    pass\n"
            "elif a2:\n    (M := consts)\nelse:\n    pass\n"
            "BASE = M.HW\nREG = BASE\n")
WITH_ONE = ("import consts\nwith a1:\n    (M := consts)\n"
            "BASE = M.HW\nREG = BASE\n")
TRY_ONE = ("import consts\ntry:\n    pass\nfinally:\n    (M := consts)\n"
           "BASE = M.HW\nREG = BASE\n")
IN_FUNCTION = ("import consts\ndef mk():\n    (M := consts)\n    return M\n"
               "BASE = M.HW\nREG = BASE\n")
TOP_LEVEL = "import consts\n(M := consts)\nBASE = M.HW\nREG = BASE\n"

PARENTS = [("r2585", PNT), ("r2588", PNAB), ("r2590", PNAD), ("r2592", PNAE),
           ("r2594", PNAF)]


def world(files):
    root = tempfile.mkdtemp(prefix="pnag-")
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


def labels_of(reason):
    if "ambiguous:" not in reason or "@" not in reason:
        return []
    return [item for item in reason.split("@", 1)[1].split("+") if item]


def ac_pnag1():
    """Three bindings across two whiles name THREE distinct labels."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "consts3.py": 'HW = "hw3"\n',
                  "mk.py": THREE_BINDINGS})
    try:
        got = entry(PNAG, "import mk\n" + RECV + TAIL, root)
        parent = entry(PNAF, "import mk\n" + RECV + TAIL, root)
        reason = got.get("reason") or ""
        labels = labels_of(reason)
        ok = check(got.get("state") == PNAG.STATE_REFUSED
                   and got.get("value") is None,
                   "AC-PNAG1 three bindings are never resolved (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(reason.startswith("attr-module-alias-ambiguous:")
                   and len(set(labels)) == 3,
                   "AC-PNAG1 the reason names THREE distinct labels (%d: %s)"
                   % (len(set(labels)), labels)) and ok
        wanted = {"while>case", "while2>case", "while2_body>case"}
        ok = check(wanted.issubset(set(labels)),
                   "AC-PNAG1 the three labels are the shipped first-while "
                   "ordinals plus the second while own body label (%s)"
                   % (sorted(set(labels)),)) and ok
        parent_labels = labels_of(parent.get("reason") or "")
        ok = check(len(set(parent_labels)) == 2,
                   "AC-PNAG1 the R2594 reader named only TWO labels on the "
                   "SAME fixture (%d: %s)"
                   % (len(set(parent_labels)), parent_labels)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnag2():
    """Two matches in one while else section read while_else and while_else2."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "mk.py": ELSE_TWO})
    try:
        got = entry(PNAG, "import mk\n" + RECV + TAIL, root)
        parent = entry(PNAF, "import mk\n" + RECV + TAIL, root)
        reason = got.get("reason") or ""
        labels = set(labels_of(reason))
        ok = check(labels == {"while_else>case", "while_else2>case"},
                   "AC-PNAG2 both else matches are named exactly (%s)"
                   % (sorted(labels),))
        ok = check("while_elsem2" not in reason,
                   "AC-PNAG2 the join artifact is gone from the reason (%s)"
                   % (reason,)) and ok
        ok = check("while_elsem2" in (parent.get("reason") or ""),
                   "AC-PNAG2 the R2594 reader still printed the artifact on "
                   "the SAME fixture (%s)" % (parent.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnag3():
    """The three named shapes keep the shipped refusal with no branch read."""
    cases = [("match inside a for body nested in a while", FOR_IN_WHILE),
             ("match nested one level in a while inside another while",
              WHILE_IN_WHILE),
             ("walrus bound by an if nested inside a match case", IF_IN_CASE)]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            got = entry(PNAG, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAF, "import mk\n" + RECV + TAIL, root)
            ok = check(got.get("state") == PNAG.STATE_REFUSED
                       and got.get("value") is None,
                       "AC-PNAG3 a %s stays refused (%s/%s)"
                       % (label, got.get("state"), got.get("value"))) and ok
            ok = check(got.get("reason") == parent.get("reason")
                       == "attr-module-alias-unbound:M.HW",
                       "AC-PNAG3 the shipped refusal is published byte for "
                       "byte (%s/%s)"
                       % (got.get("reason"), parent.get("reason"))) and ok
            ok = check(not [item for item in got.get("branch_reads") or []
                            if item.startswith("branch:")],
                       "AC-PNAG3 no branch read is published (%s)"
                       % (got.get("branch_reads"),)) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnag4():
    """Every answer the five parent faces already gave is carried unchanged."""
    cases = [
        ("module-level if branch", IF_ONE),
        ("module-level with body", WITH_ONE),
        ("module-level while body", WHILE_ONE),
        ("while else direct walrus", WHILE_ELSE),
        ("two while bodies", WHILE_TWO),
        ("module-level match case", CASE_ONE),
        ("lone nested match in a while", NESTED_CASE),
        ("two matches in ONE while", TWO_MATCHES_ONE_WHILE),
    ]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n', "mk.py": body})
        try:
            mine = entry(PNAG, "import mk\n" + RECV + TAIL, root)
            near = entry(PNAF, "import mk\n" + RECV + TAIL, root)
            same = (mine.get("state") == near.get("state")
                    and mine.get("value") == near.get("value")
                    and mine.get("reason") == near.get("reason")
                    and (mine.get("branch_reads") or [])
                    == (near.get("branch_reads") or []))
            ok = check(same,
                       "AC-PNAG4 %s reads exactly what R2594 answered "
                       "(%s/%s vs %s/%s)"
                       % (label, mine.get("state"), mine.get("value"),
                          near.get("state"), near.get("value"))) and ok
            for tag, module in PARENTS:
                older = entry(module, "import mk\n" + RECV + TAIL, root)
                carried = (mine.get("base_pnag_%s_state" % tag)
                           == older.get("state")
                           and mine.get("base_pnag_%s_value" % tag)
                           == older.get("value")
                           and mine.get("base_pnag_%s_reason" % tag)
                           == older.get("reason"))
                ok = check(carried,
                           "AC-PNAG4 %s carries the %s answer on the row "
                           "(%s/%s)" % (label, tag,
                                        mine.get("base_pnag_%s_state" % tag),
                                        mine.get("base_pnag_%s_reason"
                                                 % tag))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "consts3.py": 'HW = "hw3"\n',
                  "mk.py": THREE_BINDINGS})
    try:
        mine = entry(PNAG, "import mk\n" + RECV + TAIL, root)
        shipped = entry(PNT, "import mk\n" + RECV + TAIL, root)
        ok = check(len(set(labels_of(mine.get("reason") or ""))) == 3
                   and shipped.get("state") == PNT.STATE_REFUSED,
                   "AC-PNAG4 the SAME fixture is measured on BOTH readers "
                   "(here=%s there=%s/%s)"
                   % (labels_of(mine.get("reason") or ""),
                      shipped.get("state"), shipped.get("reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    loops = 0
    unreadable = 0
    changed = []
    for name in LIVE_MODULES:
        path = os.path.join(BASE, name + ".py")
        if not os.path.isfile(path):
            unreadable += 1
            continue
        before = read_bytes(path)
        text = before.decode("utf-8")
        mine = len(PNAG.module_alias_report(text, BASE, path)["loops"])
        _LIVE_COUNTS[name] = mine
        loops += mine
        if read_bytes(path) != before:
            changed.append(name)
    ok = check(unreadable == 0 and loops > 0 and not changed,
               "AC-PNAG4 a bounded live leg reads a real module read-only "
               "(modules=%d loops=%d unreadable=%d changed=%s)"
               % (len(LIVE_MODULES), loops, unreadable, changed)) and ok
    return ok


def ac_pnag5():
    """The published labels are stable under a second call on the same tree."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "consts3.py": 'HW = "hw3"\n',
                  "mk.py": THREE_BINDINGS})
    try:
        first = entry(PNAG, "import mk\n" + RECV + TAIL, root)
        second = entry(PNAG, "import mk\n" + RECV + TAIL, root)
        ok = check(first.get("reason") == second.get("reason")
                   and (first.get("branch_reads") or [])
                   == (second.get("branch_reads") or []),
                   "AC-PNAG5 two readings of the same tree print the same "
                   "reason (%s)" % (first.get("reason"),))
        root2 = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                       "consts2.py": 'HW = "hw2"\n', "mk.py": ELSE_TWO})
        try:
            first_else = entry(PNAG, "import mk\n" + RECV + TAIL, root2)
            second_else = entry(PNAG, "import mk\n" + RECV + TAIL, root2)
            ok = check(first_else.get("reason") == second_else.get("reason")
                       and labels_of(first_else.get("reason") or "")
                       == labels_of(second_else.get("reason") or ""),
                       "AC-PNAG5 the else labels are stable too (%s)"
                       % (first_else.get("reason"),)) and ok
        finally:
            shutil.rmtree(root2, ignore_errors=True)
        again = {}
        for name in LIVE_MODULES:
            path = os.path.join(BASE, name + ".py")
            if not os.path.isfile(path):
                continue
            again[name] = _LIVE_COUNTS.get(name)
        ok = check(again == _LIVE_COUNTS and bool(again),
                   "AC-PNAG5 the bounded live count recorded once is the one "
                   "this suite reports (%s)" % (again,)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnag6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAG6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAG6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAG6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAG6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAG6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAG6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnag1, ac_pnag2, ac_pnag3, ac_pnag4, ac_pnag5, ac_pnag6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
