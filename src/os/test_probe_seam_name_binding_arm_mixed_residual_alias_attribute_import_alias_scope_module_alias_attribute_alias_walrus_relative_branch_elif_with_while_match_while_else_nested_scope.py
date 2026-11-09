"""AC-PNAE1..AC-PNAE6 suite for the while-else / nested-case walrus face (R2592).

Criteria were pinned in state/queue/tech.md:625 at R2590 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_scope as PNAE  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_scope as PNAD  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_while_match_while_else_nested_"
               "scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-while-match-'
               'while-else-nested-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_while_match_while_else_'
               'nested_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"
# Two real modules, deliberately bounded: this face re-reads its parent rather
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

WHILE_ELSE = ("import consts\nwhile a1:\n    pass\nelse:\n    (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
WHILE_TWO = ("import consts\nimport consts2\n"
             "while a1:\n    (M := consts)\n"
             "while a2:\n    (M := consts2)\n"
             "BASE = M.HW\nREG = BASE\n")
NESTED_CASE = ("import consts\nwhile a1:\n    match x:\n        case 1:\n"
               "            (M := consts)\nBASE = M.HW\nREG = BASE\n")
NESTED_WITH = ("import consts\nwhile a1:\n    with a2:\n        (M := consts)\n"
               "BASE = M.HW\nREG = BASE\n")
NESTED_TWO = ("import consts\nwhile a1:\n    if a2:\n        (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
FOR_ONE = ("import consts\nfor a1 in (1,):\n    (M := consts)\n"
           "BASE = M.HW\nREG = BASE\n")
WHILE_ONE = ("import consts\nwhile a1:\n    (M := consts)\n"
             "BASE = M.HW\nREG = BASE\n")
CASE_ONE = ("import consts\nmatch x:\n    case 1:\n        (M := consts)\n"
            "BASE = M.HW\nREG = BASE\n")
IF_ONE = ("import consts\nif True:\n    (M := consts)\n"
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
RELATIVE_HEAD = ("from . import consts\nM = consts\nBASE = M.HW\n"
                 "REG = BASE\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnae-")
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


def ac_pnae1():
    """A walrus inside a module-level while else section resolves."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": WHILE_ELSE})
    try:
        got = entry(PNAE, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAE.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAE1 a while-else walrus alias head resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        chain = " ".join(got.get("ma_chain") or [])
        ok = check("branch:M@while_else" in chain,
                   "AC-PNAE1 the else section is named branch:M@while_else "
                   "(%s)" % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnae_state") == PNAD.STATE_REFUSED
                   and got.get("base_pnae_reason")
                   == "attr-module-alias-unbound:M.HW",
                   "AC-PNAE1 the R2590 reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnae_state"),
                                got.get("base_pnae_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnae2():
    """Two while bodies binding one name are refused, naming BOTH whiles."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "mk.py": WHILE_TWO})
    try:
        got = entry(PNAE, "import mk\n" + RECV + TAIL, root)
        reason = got.get("reason") or ""
        ok = check(got.get("state") == PNAE.STATE_REFUSED
                   and got.get("value") is None,
                   "AC-PNAE2 two while bodies are never resolved (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(reason.startswith("attr-module-alias-ambiguous:")
                   and "while+" in reason and "while2" in reason,
                   "AC-PNAE2 the reason names BOTH whiles (%s)" % (reason,)) \
            and ok
        parent = entry(PNAD, "import mk\n" + RECV + TAIL, root)
        ok = check((parent.get("reason") or "").endswith("@while")
                   and "while2" not in (parent.get("reason") or ""),
                   "AC-PNAE2 the R2590 reader named the while only once (%s)"
                   % (parent.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnae3():
    """A lone match nested one level in a while body resolves its case."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "mk.py": NESTED_CASE})
    try:
        got = entry(PNAE, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAE.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAE3 a nested single-case walrus resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        reads = got.get("branch_reads") or []
        ok = check("branch:M@while>case" in reads,
                   "AC-PNAE3 the nested case is named branch:M@while>case "
                   "(%s)" % (reads,)) and ok
        ok = check(got.get("base_pnae_state") == PNAD.STATE_REFUSED
                   and not got.get("base_pnae_branch_reads"),
                   "AC-PNAE3 the R2590 reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnae_state"),
                                got.get("base_pnae_branch_reads"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnae4():
    """A for body, a with nested in a while and a two-deep branch stay refused."""
    cases = [("for body", FOR_ONE), ("with nested in a while", NESTED_WITH),
             ("branch nested two deep in a while", NESTED_TWO)]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            got = entry(PNAE, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAD, "import mk\n" + RECV + TAIL, root)
            ok = check(got.get("state") == PNAE.STATE_REFUSED
                       and got.get("value") is None,
                       "AC-PNAE4 a %s walrus is still refused (%s/%s)"
                       % (label, got.get("state"), got.get("value"))) and ok
            ok = check(got.get("state") == parent.get("state")
                       and got.get("reason") == parent.get("reason"),
                       "AC-PNAE4 the shipped refusal is kept byte for byte "
                       "(%s/%s)" % (got.get("reason"),
                                    parent.get("reason"))) and ok
            ok = check(not [item for item in got.get("branch_reads") or []
                            if item.startswith("branch:")],
                       "AC-PNAE4 no branch read is published (%s)"
                       % (got.get("branch_reads"),)) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnae5():
    """Every answer the R2587, R2588 and R2590 faces already gave is carried."""
    cases = [
        ("module-level if branch", IF_ONE),
        ("module-level elif section", ELIF_ONE),
        ("module-level with body", WITH_ONE),
        ("module-level try finally", TRY_ONE),
        ("module-level while body", WHILE_ONE),
        ("module-level match case", CASE_ONE),
        ("function-body walrus", IN_FUNCTION),
        ("top-level walrus", TOP_LEVEL),
    ]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n', "mk.py": body})
        try:
            mine = entry(PNAE, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAD, "import mk\n" + RECV + TAIL, root)
            same = (mine.get("state") == parent.get("state")
                    and mine.get("value") == parent.get("value")
                    and mine.get("reason") == parent.get("reason")
                    and (mine.get("branch_reads") or [])
                    == (parent.get("branch_reads") or []))
            ok = check(same,
                       "AC-PNAE5 %s reads exactly what R2590 answered "
                       "(%s/%s vs %s/%s)"
                       % (label, mine.get("state"), mine.get("value"),
                          parent.get("state"), parent.get("value"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW, "pkg/__init__.py": "",
                  "pkg/consts.py": 'HW = "hw"\n', "pkg/mk5.py": RELATIVE_HEAD})
    try:
        mine = entry(PNAE, "import pkg.mk5 as mk\n" + RECV + TAIL, root)
        parent = entry(PNAD, "import pkg.mk5 as mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == parent.get("state")
                   and mine.get("value") == parent.get("value"),
                   "AC-PNAE5 a relative module alias head reads as before "
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
        mine = len(PNAE.module_alias_report(text, BASE, path)["loops"])
        parent = len(PNAD.module_alias_report(text, BASE, path)["loops"])
        loops += mine
        if mine != parent:
            mismatched.append((name, mine, parent))
    ok = check(unreadable == 0 and loops > 0 and not mismatched,
               "AC-PNAE5 a bounded live leg reads real modules read-only and "
               "agrees with its parent (modules=%d loops=%d unreadable=%d "
               "mismatched=%s)" % (len(LIVE_MODULES), loops, unreadable,
                                   mismatched)) and ok
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "mk.py": WHILE_ELSE})
    try:
        mine = entry(PNAE, "import mk\n" + RECV + TAIL, root)
        shipped = entry(PNT, "import mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == PNAE.STATE_OK
                   and shipped.get("state") == PNT.STATE_REFUSED,
                   "AC-PNAE5 the SAME fixture is measured on BOTH readers "
                   "(here=%s/%s there=%s/%s)"
                   % (mine.get("state"), mine.get("value"),
                      shipped.get("state"), shipped.get("reason"))) and ok
        carried = [key for key in ("base_pnae_state", "base_pnae_value",
                                   "base_pnae_reason", "base_pnae_chain",
                                   "base_pnae_branch_reads")
                   if key in mine]
        ok = check(len(carried) == 5,
                   "AC-PNAE5 the R2590 keys ride on the row (%s)"
                   % (carried,)) and ok
        left = [key for key in ("base_pnad_state", "base_pnad_reason",
                                "base_pnac_state", "ma_chain")
                if key in mine]
        ok = check(len(left) == 4,
                   "AC-PNAE5 the R2587/R2588/R2590 keys are untouched beside "
                   "them (%s)" % (left,)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnae6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAE6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAE6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAE6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAE6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAE6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAE6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnae1, ac_pnae2, ac_pnae3, ac_pnae4, ac_pnae5, ac_pnae6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())