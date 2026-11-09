"""AC-PNAC1..AC-PNAC6 suite for the elif/with walrus face (R2588).

Criteria were pinned in state/queue/tech.md:621 at R2587 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_scope as PNAC  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope as PNAB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"
# Two real modules, deliberately bounded: this face re-reads the parent rather
# than replacing it, so the live leg is about agreement, not about coverage.
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

ELIF_ONE = ("import consts\nif a1:\n    pass\n"
            "elif a2:\n    (M := consts)\nelse:\n    pass\n"
            "BASE = M.HW\nREG = BASE\n")
WITH_ONE = ("import consts\nwith a1:\n    (M := consts)\n"
            "BASE = M.HW\nREG = BASE\n")
FOR_ONE = ("import consts\nfor a1 in (1,):\n    (M := consts)\n"
           "BASE = M.HW\nREG = BASE\n")
NESTED_TWO = ("import consts\nif a1:\n    if a2:\n        (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
ELIF_TWO_SIDES = ("import consts\nimport consts2\n"
                  "if a1:\n    pass\n"
                  "elif a2:\n    (M := consts)\n"
                  "else:\n    (M := consts2)\n"
                  "BASE = M.HW\nREG = BASE\n")
BRANCH_ONE = ("import consts\nif True:\n    (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
BRANCH_TWO = ("import consts\nimport consts2\n"
              "if a1:\n    (M := consts)\n"
              "else:\n    (M := consts2)\n"
              "BASE = M.HW\nREG = BASE\n")
IN_FUNCTION = ("import consts\ndef mk():\n    (M := consts)\n    return M\n"
               "BASE = M.HW\nREG = BASE\n")
TOP_LEVEL = "import consts\n(M := consts)\nBASE = M.HW\nREG = BASE\n"
RELATIVE_HEAD = ("from . import consts\nM = consts\nBASE = M.HW\n"
                 "REG = BASE\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnac-")
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


def ac_pnac1():
    """A walrus inside a module-level elif body resolves and names the elif."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": ELIF_ONE})
    try:
        got = entry(PNAC, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAC1 an elif-body walrus alias head resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        chain = " ".join(got.get("ma_chain") or [])
        ok = check("branch:M@elif" in chain,
                   "AC-PNAC1 the elif it was read in is named (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnac_state") == PNAB.STATE_REFUSED
                   and got.get("base_pnac_reason")
                   == "attr-module-alias-unbound:M.HW",
                   "AC-PNAC1 the R2587 reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnac_state"),
                                got.get("base_pnac_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnac2():
    """A walrus inside a module-level with body resolves and names the with."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": WITH_ONE})
    try:
        got = entry(PNAC, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAC2 a with-body walrus alias head resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        chain = " ".join(got.get("ma_chain") or [])
        ok = check("branch:M@with" in chain,
                   "AC-PNAC2 the with it was read in is named (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnac_state") == PNAB.STATE_REFUSED
                   and got.get("base_pnac_value") is None,
                   "AC-PNAC2 the R2587 reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnac_state"),
                                got.get("base_pnac_value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnac3():
    """A for body and a two-level nested branch keep the shipped refusal."""
    cases = [("for body", FOR_ONE), ("nested two deep", NESTED_TWO)]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            got = entry(PNAC, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAB, "import mk\n" + RECV + TAIL, root)
            ok = check(got.get("state") == PNAC.STATE_REFUSED
                       and got.get("value") is None,
                       "AC-PNAC3 a %s walrus is still refused (%s/%s)"
                       % (label, got.get("state"), got.get("value"))) and ok
            ok = check(got.get("state") == parent.get("state")
                       and got.get("reason") == parent.get("reason"),
                       "AC-PNAC3 the shipped refusal is kept byte for byte "
                       "(%s/%s)" % (got.get("reason"),
                                    parent.get("reason"))) and ok
            ok = check(not [item for item in got.get("branch_reads") or []
                            if item.startswith("branch:")],
                       "AC-PNAC3 no branch read is published (%s)"
                       % (got.get("branch_reads"),)) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnac4():
    """Every shape the R2587 face pinned classifies exactly as before."""
    cases = [
        ("module-level if branch", BRANCH_ONE),
        ("module-level if/else pair", BRANCH_TWO),
        ("function-body walrus", IN_FUNCTION),
        ("top-level walrus", TOP_LEVEL),
    ]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n', "mk.py": body})
        try:
            mine = entry(PNAC, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAB, "import mk\n" + RECV + TAIL, root)
            same = (mine.get("state") == parent.get("state")
                    and mine.get("value") == parent.get("value")
                    and mine.get("reason") == parent.get("reason")
                    and (mine.get("branch_reads") or [])
                    == (parent.get("branch_reads") or []))
            ok = check(same,
                       "AC-PNAC4 %s reads exactly what R2587 answered "
                       "(%s/%s vs %s/%s)"
                       % (label, mine.get("state"), mine.get("value"),
                          parent.get("state"), parent.get("value"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW, "pkg/__init__.py": "",
                  "pkg/consts.py": 'HW = "hw"\n', "pkg/mk4.py": RELATIVE_HEAD})
    try:
        mine = entry(PNAC, "import pkg.mk4 as mk\n" + RECV + TAIL, root)
        parent = entry(PNAB, "import pkg.mk4 as mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == parent.get("state")
                   and mine.get("value") == parent.get("value"),
                   "AC-PNAC4 a relative module alias head reads as before "
                   "(%s/%s vs %s/%s)"
                   % (mine.get("state"), mine.get("value"),
                      parent.get("state"), parent.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    two_sides = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                       "consts2.py": 'HW = "hw2"\n', "mk.py": ELIF_TWO_SIDES})
    try:
        got = entry(PNAC, "import mk\n" + RECV + TAIL, two_sides)
        reason = got.get("reason") or ""
        ok = check(got.get("state") == PNAC.STATE_REFUSED
                   and reason.startswith("attr-module-alias-ambiguous:")
                   and "elif" in reason and "else" in reason
                   and got.get("value") is None,
                   "AC-PNAC4 an elif/else pair is named ambiguous, never "
                   "resolved (%s/%s)" % (got.get("state"), reason)) and ok
    finally:
        shutil.rmtree(two_sides, ignore_errors=True)
    return ok


def ac_pnac5():
    """Every answer the shipped faces already gave is carried unchanged."""
    loops = 0
    unreadable = 0
    mismatched = []
    for name in LIVE_MODULES:
        path = os.path.join(BASE, name + ".py")
        if not os.path.isfile(path):
            unreadable += 1
            continue
        text = read_bytes(path).decode("utf-8")
        mine = len(PNAC.module_alias_report(text, BASE, path)["loops"])
        parent = len(PNAB.module_alias_report(text, BASE, path)["loops"])
        loops += mine
        if mine != parent:
            mismatched.append((name, mine, parent))
    ok = check(unreadable == 0 and loops > 0 and not mismatched,
               "AC-PNAC5 a bounded live leg reads real modules read-only and "
               "agrees with the parent (modules=%d loops=%d unreadable=%d "
               "mismatched=%s)" % (len(LIVE_MODULES), loops, unreadable,
                                   mismatched))
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": WITH_ONE})
    try:
        mine = entry(PNAC, "import mk\n" + RECV + TAIL, root)
        shipped = entry(PNT, "import mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == PNAC.STATE_OK
                   and shipped.get("state") == PNT.STATE_REFUSED,
                   "AC-PNAC5 the SAME fixture is measured on BOTH readers "
                   "(here=%s/%s there=%s/%s)"
                   % (mine.get("state"), mine.get("value"),
                      shipped.get("state"), shipped.get("reason"))) and ok
        carried = [key for key in ("base_pnac_state", "base_pnac_value",
                                   "base_pnac_reason", "base_pnac_chain",
                                   "base_pnac_branch_reads")
                   if key in mine]
        ok = check(len(carried) == 5,
                   "AC-PNAC5 the R2587 keys ride on the row (%s)"
                   % (carried,)) and ok
        left = [key for key in ("ma_chain", "branch_reads", "ma_source")
                if key in mine]
        ok = check(len(left) == 3,
                   "AC-PNAC5 the R2587 row keys are untouched beside them "
                   "(%s)" % (left,)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnac6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAC6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAC6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAC6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAC6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAC6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAC6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnac1, ac_pnac2, ac_pnac3, ac_pnac4, ac_pnac5, ac_pnac6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())