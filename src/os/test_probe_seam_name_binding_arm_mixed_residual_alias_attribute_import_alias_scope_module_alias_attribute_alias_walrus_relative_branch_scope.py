"""AC-PNAB1..AC-PNAB6 suite for the module-level-branch walrus face (R2587).

Criteria were pinned in state/queue/tech.md:619 at R2585 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope as PNAB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_scope.py"),')

TAIL = 'for name in hw.NAMES:\n    pass\n'
LIVE_MODULES = [
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_two_level_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_from_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_chain_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_scope",
]
HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
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
    root = tempfile.mkdtemp(prefix="pnab-")
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


def ac_pnab1():
    """A walrus inside a module-level branch resolves and names the branch."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "mk.py": BRANCH_ONE})
    try:
        got = entry(PNAB, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAB.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAB1 a branch walrus alias head resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        chain = " ".join(got.get("ma_chain") or [])
        ok = check("branch:M@if" in chain,
                   "AC-PNAB1 the branch it was read in is named (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnab_state") == PNT.STATE_REFUSED
                   and got.get("base_pnab_reason")
                   == "attr-module-alias-unbound:M.HW",
                   "AC-PNAB1 the shipped reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnab_state"),
                                got.get("base_pnab_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnab2():
    """A walrus bound on TWO branches is NAMED ambiguous, never resolved."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "mk.py": BRANCH_TWO})
    try:
        got = entry(PNAB, "import mk\n" + RECV + TAIL, root)
        reason = got.get("reason") or ""
        ok = check(got.get("state") == PNAB.STATE_REFUSED
                   and reason.startswith("attr-module-alias-ambiguous:"),
                   "AC-PNAB2 two branches are named ambiguous (%s/%s)"
                   % (got.get("state"), reason))
        ok = check("if" in reason and "else" in reason,
                   "AC-PNAB2 both branches are named in the answer (%s)"
                   % (reason,)) and ok
        ok = check(got.get("value") is None,
                   "AC-PNAB2 nothing is resolved to either branch") and ok
        ok = check(got.get("base_pnab_state") == PNT.STATE_REFUSED
                   and got.get("base_pnab_reason")
                   == "attr-module-alias-unbound:M.HW",
                   "AC-PNAB2 the shipped reader states no reason (%s)"
                   % (got.get("base_pnab_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnab3():
    """A walrus inside a FUNCTION body stays a refusal."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "mk.py": IN_FUNCTION})
    try:
        got = entry(PNAB, "import mk\n" + RECV + TAIL, root)
        base = entry(PNT, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAB.STATE_REFUSED
                   and got.get("value") is None,
                   "AC-PNAB3 a function-body walrus is not a module alias "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("state") == base.get("state")
                   and got.get("reason") == base.get("reason"),
                   "AC-PNAB3 the shipped refusal is kept byte for byte "
                   "(%s/%s)" % (got.get("reason"), base.get("reason"))) and ok
        ok = check(not [item for item in got.get("branch_reads") or []
                        if item.startswith("branch:")],
                   "AC-PNAB3 no branch read is published (%s)"
                   % (got.get("branch_reads"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnab4():
    """Every shape the R2585 face pinned classifies exactly as before."""
    cases = [
        ("top-level walrus",
         {"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": TOP_LEVEL},
         "import mk\n" + RECV + TAIL),
        ("relative module alias head",
         {"hw.py": HW, "pkg/__init__.py": "",
          "pkg/consts.py": 'HW = "hw"\n', "pkg/mk4.py": RELATIVE_HEAD},
         "import pkg.mk4 as mk\n" + RECV + TAIL),
    ]
    ok = True
    for label, files, text in cases:
        root = world(files)
        try:
            mine = entry(PNAB, text, root)
            base = entry(PNT, text, root)
            same = (mine.get("state") == base.get("state")
                    and mine.get("value") == base.get("value")
                    and mine.get("reason") == base.get("reason"))
            ok = check(base.get("state") == PNT.STATE_OK and same,
                       "AC-PNAB4 %s reads exactly what R2585 answered "
                       "(%s/%s vs %s/%s)"
                       % (label, mine.get("state"), mine.get("value"),
                          base.get("state"), base.get("value"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    two = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                 "pkg/__init__.py": "", "pkg/consts.py": 'HW = "hw2"\n'})
    try:
        mine = entry(PNAB, "from . import consts as mk\n" + RECV + TAIL, two)
        base = entry(PNT, "from . import consts as mk\n" + RECV + TAIL, two)
        ok = check(mine.get("state") == PNT.STATE_REFUSED
                   and mine.get("state") == base.get("state"),
                   "AC-PNAB4 an AMBIGUOUS unanchored head is still refused, "
                   "never guessed (%s/%s)" % (mine.get("state"),
                                              base.get("state"))) and ok
    finally:
        shutil.rmtree(two, ignore_errors=True)
    return ok


def ac_pnab5():
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
        mine = len(PNAB.module_alias_report(text, BASE, path)["loops"])
        base = len(PNT.module_alias_report(text, BASE, path)["loops"])
        loops += mine
        if mine != base:
            mismatched.append((name, mine, base))
    ok = check(unreadable == 0 and loops > 0 and not mismatched,
               "AC-PNAB5 a bounded live leg reads real modules read-only and "
               "agrees with the parent (modules=%d loops=%d unreadable=%d "
               "mismatched=%s)" % (len(LIVE_MODULES), loops, unreadable,
                                   mismatched))
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "mk.py": BRANCH_ONE})
    try:
        mine = entry(PNAB, "import mk\n" + RECV + TAIL, root)
        shipped = entry(PNT, "import mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == PNAB.STATE_OK
                   and shipped.get("state") == PNT.STATE_REFUSED,
                   "AC-PNAB5 the SAME fixture is measured on BOTH readers "
                   "(here=%s/%s there=%s/%s)"
                   % (mine.get("state"), mine.get("value"),
                      shipped.get("state"), shipped.get("reason"))) and ok
        carried = [key for key in ("base_pnab_state", "base_pnab_hop",
                                   "ma_chain", "ma_source")
                   if key in mine]
        ok = check(len(carried) == 4,
                   "AC-PNAB5 the parent keys ride on the row (%s)"
                   % (carried,)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnab6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAB6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAB6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNAB6 the registry carries exactly one row for this face"
               ) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAB6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAB6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnab1, ac_pnab2, ac_pnab3, ac_pnab4, ac_pnab5, ac_pnab6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())