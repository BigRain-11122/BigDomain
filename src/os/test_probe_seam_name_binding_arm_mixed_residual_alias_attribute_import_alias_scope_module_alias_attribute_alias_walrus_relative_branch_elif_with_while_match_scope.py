"""AC-PNAD1..AC-PNAD6 suite for the while/match walrus face (R2590).

Criteria were pinned in state/queue/tech.md:623 at R2588 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_scope as PNAD  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_scope as PNAC  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope as PNAB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_while_match_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-while-match-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_while_match_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"
# Two real modules, deliberately bounded: this face re-reads both parents rather
# than replacing them, so the live leg is about agreement, not about coverage.
LIVE_MODULES = [
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_two_level_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_from_scope",
]
HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")

WHILE_ONE = ("import consts\nwhile a1:\n    (M := consts)\n"
             "BASE = M.HW\nREG = BASE\n")
CASE_ONE = ("import consts\nmatch x:\n    case 1:\n        (M := consts)\n"
            "BASE = M.HW\nREG = BASE\n")
CASE_TWO_SIDES = ("import consts\nimport consts2\n"
                  "match x:\n    case 1:\n        (M := consts)\n"
                  "    case 2:\n        (M := consts2)\n"
                  "BASE = M.HW\nREG = BASE\n")
FOR_ONE = ("import consts\nfor a1 in (1,):\n    (M := consts)\n"
           "BASE = M.HW\nREG = BASE\n")
NESTED_TWO = ("import consts\nif a1:\n    if a2:\n        (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
IF_ONE = ("import consts\nif True:\n    (M := consts)\n"
          "BASE = M.HW\nREG = BASE\n")
IF_TWO = ("import consts\nimport consts2\n"
          "if a1:\n    (M := consts)\n"
          "else:\n    (M := consts2)\n"
          "BASE = M.HW\nREG = BASE\n")
ELIF_ONE = ("import consts\nif a1:\n    pass\n"
            "elif a2:\n    (M := consts)\nelse:\n    pass\n"
            "BASE = M.HW\nREG = BASE\n")
WITH_ONE = ("import consts\nwith a1:\n    (M := consts)\n"
            "BASE = M.HW\nREG = BASE\n")
ELIF_TWO_SIDES = ("import consts\nimport consts2\n"
                  "if a1:\n    pass\n"
                  "elif a2:\n    (M := consts)\n"
                  "else:\n    (M := consts2)\n"
                  "BASE = M.HW\nREG = BASE\n")
IN_FUNCTION = ("import consts\ndef mk():\n    (M := consts)\n    return M\n"
               "BASE = M.HW\nREG = BASE\n")
TOP_LEVEL = "import consts\n(M := consts)\nBASE = M.HW\nREG = BASE\n"
RELATIVE_HEAD = ("from . import consts\nM = consts\nBASE = M.HW\n"
                 "REG = BASE\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnad-")
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


def ac_pnad1():
    """A walrus inside a module-level while body resolves and names the while."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": WHILE_ONE})
    try:
        got = entry(PNAD, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAD.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAD1 a while-body walrus alias head resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        chain = " ".join(got.get("ma_chain") or [])
        ok = check("branch:M@while" in chain,
                   "AC-PNAD1 the while it was read in is named (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnad_state") == PNAC.STATE_REFUSED
                   and got.get("base_pnad_reason")
                   == "attr-module-alias-unbound:M.HW",
                   "AC-PNAD1 the R2588 reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnad_state"),
                                got.get("base_pnad_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnad2():
    """A walrus inside a match case body resolves and names the case."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": CASE_ONE})
    try:
        got = entry(PNAD, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAD.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAD2 a case-body walrus alias head resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        chain = " ".join(got.get("ma_chain") or [])
        ok = check("branch:M@case" in chain,
                   "AC-PNAD2 the case it was read in is named (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnad_state") == PNAC.STATE_REFUSED
                   and got.get("base_pnad_value") is None,
                   "AC-PNAD2 the R2588 reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnad_state"),
                                got.get("base_pnad_value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnad3():
    """Two case bodies binding one name are refused, naming both cases."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "mk.py": CASE_TWO_SIDES})
    try:
        got = entry(PNAD, "import mk\n" + RECV + TAIL, root)
        reason = got.get("reason") or ""
        ok = check(got.get("state") == PNAD.STATE_REFUSED
                   and got.get("value") is None,
                   "AC-PNAD3 two case bodies are never resolved (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(reason.startswith("attr-module-alias-ambiguous:")
                   and "case" in reason and "case2" in reason,
                   "AC-PNAD3 the refusal names BOTH cases (%s)" % (reason,)) \
            and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnad4():
    """A for body and a nested branch keep the shipped refusal."""
    cases = [("for body", FOR_ONE), ("nested two deep", NESTED_TWO)]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            got = entry(PNAD, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAC, "import mk\n" + RECV + TAIL, root)
            ok = check(got.get("state") == PNAD.STATE_REFUSED
                       and got.get("value") is None,
                       "AC-PNAD4 a %s walrus is still refused (%s/%s)"
                       % (label, got.get("state"), got.get("value"))) and ok
            ok = check(got.get("state") == parent.get("state")
                       and got.get("reason") == parent.get("reason"),
                       "AC-PNAD4 the shipped refusal is kept byte for byte "
                       "(%s/%s)" % (got.get("reason"),
                                    parent.get("reason"))) and ok
            ok = check(not [item for item in got.get("branch_reads") or []
                            if item.startswith("branch:")],
                       "AC-PNAD4 no branch read is published (%s)"
                       % (got.get("branch_reads"),)) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnad5():
    """Every answer the R2587 and R2588 faces already gave is carried."""
    cases = [
        ("module-level if branch", IF_ONE),
        ("module-level if/else pair", IF_TWO),
        ("module-level elif section", ELIF_ONE),
        ("module-level with body", WITH_ONE),
        ("function-body walrus", IN_FUNCTION),
        ("top-level walrus", TOP_LEVEL),
    ]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n', "mk.py": body})
        try:
            mine = entry(PNAD, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAC, "import mk\n" + RECV + TAIL, root)
            same = (mine.get("state") == parent.get("state")
                    and mine.get("value") == parent.get("value")
                    and mine.get("reason") == parent.get("reason")
                    and (mine.get("branch_reads") or [])
                    == (parent.get("branch_reads") or []))
            ok = check(same,
                       "AC-PNAD5 %s reads exactly what R2588 answered "
                       "(%s/%s vs %s/%s)"
                       % (label, mine.get("state"), mine.get("value"),
                          parent.get("state"), parent.get("value"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW, "pkg/__init__.py": "",
                  "pkg/consts.py": 'HW = "hw"\n', "pkg/mk5.py": RELATIVE_HEAD})
    try:
        mine = entry(PNAD, "import pkg.mk5 as mk\n" + RECV + TAIL, root)
        parent = entry(PNAC, "import pkg.mk5 as mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == parent.get("state")
                   and mine.get("value") == parent.get("value"),
                   "AC-PNAD5 a relative module alias head reads as before "
                   "(%s/%s vs %s/%s)"
                   % (mine.get("state"), mine.get("value"),
                      parent.get("state"), parent.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    loops = 0
    unreadable = 0
    mismatched = []
    for name in LIVE_MODULES:
        path = os.path.join(BASE, name + ".py")
        if not os.path.isfile(path):
            unreadable += 1
            continue
        text = read_bytes(path).decode("utf-8")
        mine = len(PNAD.module_alias_report(text, BASE, path)["loops"])
        p2588 = len(PNAC.module_alias_report(text, BASE, path)["loops"])
        p2587 = len(PNAB.module_alias_report(text, BASE, path)["loops"])
        loops += mine
        if mine != p2588 or mine != p2587:
            mismatched.append((name, mine, p2588, p2587))
    ok = check(unreadable == 0 and loops > 0 and not mismatched,
               "AC-PNAD5 a bounded live leg reads real modules read-only and "
               "agrees with BOTH parents (modules=%d loops=%d unreadable=%d "
               "mismatched=%s)" % (len(LIVE_MODULES), loops, unreadable,
                                   mismatched)) and ok
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": WHILE_ONE})
    try:
        mine = entry(PNAD, "import mk\n" + RECV + TAIL, root)
        shipped = entry(PNT, "import mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == PNAD.STATE_OK
                   and shipped.get("state") == PNT.STATE_REFUSED,
                   "AC-PNAD5 the SAME fixture is measured on BOTH readers "
                   "(here=%s/%s there=%s/%s)"
                   % (mine.get("state"), mine.get("value"),
                      shipped.get("state"), shipped.get("reason"))) and ok
        carried = [key for key in ("base_pnad_state", "base_pnad_value",
                                   "base_pnad_reason", "base_pnad_chain",
                                   "base_pnad_branch_reads")
                   if key in mine]
        ok = check(len(carried) == 5,
                   "AC-PNAD5 the R2588 keys ride on the row (%s)"
                   % (carried,)) and ok
        left = [key for key in ("ma_chain", "branch_reads",
                                "base_pnac_state")
                if key in mine]
        ok = check(len(left) == 3,
                   "AC-PNAD5 the R2587 keys are untouched beside them (%s)"
                   % (left,)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    two_sides = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                       "consts2.py": 'HW = "hw2"\n', "mk.py": ELIF_TWO_SIDES})
    try:
        got = entry(PNAD, "import mk\n" + RECV + TAIL, two_sides)
        reason = got.get("reason") or ""
        ok = check(got.get("state") == PNAD.STATE_REFUSED
                   and reason.startswith("attr-module-alias-ambiguous:")
                   and got.get("value") is None,
                   "AC-PNAD5 an elif/else pair still reads ambiguous, never "
                   "resolved (%s/%s)" % (got.get("state"), reason)) and ok
    finally:
        shutil.rmtree(two_sides, ignore_errors=True)
    return ok


def ac_pnad6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAD6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAD6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAD6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAD6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAD6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAD6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnad1, ac_pnad2, ac_pnad3, ac_pnad4, ac_pnad5, ac_pnad6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())