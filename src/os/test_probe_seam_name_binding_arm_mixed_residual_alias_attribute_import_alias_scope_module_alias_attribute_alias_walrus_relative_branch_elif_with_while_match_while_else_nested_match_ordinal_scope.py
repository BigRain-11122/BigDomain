"""AC-PNAF1..AC-PNAF6 suite for the per-match ordinal walrus face (R2594).

Criteria were pinned in state/queue/tech.md:627 at R2592 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_scope as PNAF  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_scope as PNAE  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_scope as PNAD  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope as PNAB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_branch_elif_with_while_match_while_else_nested_"
               "match_ordinal_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-branch-elif-with-while-match-'
               'while-else-nested-match-ordinal-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_branch_elif_with_while_match_while_else_'
               'nested_match_ordinal_scope.py"),')

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

TWO_MATCHES = ("import consts\nimport consts2\n"
               "while a1:\n"
               "    match x:\n        case 1:\n            (M := consts)\n"
               "    match y:\n        case 1:\n            (M := consts2)\n"
               "BASE = M.HW\nREG = BASE\n")
ELSE_MATCH = ("import consts\nwhile a1:\n    pass\nelse:\n"
              "    match x:\n        case 1:\n            (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
FOR_ONE = ("import consts\nfor a1 in (1,):\n    (M := consts)\n"
           "BASE = M.HW\nREG = BASE\n")
FOR_ELSE = ("import consts\nfor a1 in (1,):\n    pass\nelse:\n"
            "    (M := consts)\nBASE = M.HW\nREG = BASE\n")
NESTED_WITH = ("import consts\nwhile a1:\n    with a2:\n        (M := consts)\n"
               "BASE = M.HW\nREG = BASE\n")
NESTED_TWO = ("import consts\nwhile a1:\n    if a2:\n        (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
MATCH_TWO_DEEP = ("import consts\nwhile a1:\n    with a2:\n"
                  "        match x:\n            case 1:\n"
                  "                (M := consts)\n"
                  "BASE = M.HW\nREG = BASE\n")
WHILE_ELSE = ("import consts\nwhile a1:\n    pass\nelse:\n    (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
WHILE_TWO = ("import consts\nimport consts2\n"
             "while a1:\n    (M := consts)\n"
             "while a2:\n    (M := consts2)\n"
             "BASE = M.HW\nREG = BASE\n")
NESTED_CASE = ("import consts\nwhile a1:\n    match x:\n        case 1:\n"
               "            (M := consts)\nBASE = M.HW\nREG = BASE\n")
TWO_CASES = ("import consts\nimport consts2\n"
             "while a1:\n    match x:\n        case 1:\n"
             "            (M := consts)\n        case 2:\n"
             "            (M := consts2)\nBASE = M.HW\nREG = BASE\n")
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

PARENTS = [("R2592", PNAE), ("R2590", PNAD), ("R2588", PNAB), ("R2585", PNT)]


def world(files):
    root = tempfile.mkdtemp(prefix="pnaf-")
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


def ac_pnaf1():
    """Two lone matches in one while body name BOTH cases."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "consts2.py": 'HW = "hw2"\n', "mk.py": TWO_MATCHES})
    try:
        got = entry(PNAF, "import mk\n" + RECV + TAIL, root)
        parent = entry(PNAE, "import mk\n" + RECV + TAIL, root)
        reason = got.get("reason") or ""
        ok = check(got.get("state") == PNAF.STATE_REFUSED
                   and got.get("value") is None,
                   "AC-PNAF1 two lone matches are never resolved (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(reason.startswith("attr-module-alias-ambiguous:")
                   and "while>case" in reason and "while2>case" in reason,
                   "AC-PNAF1 the reason names BOTH matches (%s)" % (reason,)) \
            and ok
        reads = got.get("branch_reads") or []
        ok = check(len([item for item in reads
                        if item.startswith("ambiguous:")]) == 1,
                   "AC-PNAF1 one ambiguous read is published (%s)" % (reads,)) \
            and ok
        parent_reason = parent.get("reason") or ""
        ok = check("while2>case" not in parent_reason,
                   "AC-PNAF1 the R2592 reader named the case ONCE (%s)"
                   % (parent_reason,)) and ok
        ok = check(got.get("base_pnaf_reason") == parent_reason,
                   "AC-PNAF1 the parent answer rides on the row unchanged "
                   "(%s)" % (got.get("base_pnaf_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaf2():
    """A lone match in a while else section resolves its case."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": ELSE_MATCH})
    try:
        got = entry(PNAF, "import mk\n" + RECV + TAIL, root)
        parent = entry(PNAE, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAF.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAF2 a while-else nested match resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        reads = got.get("branch_reads") or []
        chain = " ".join(got.get("ma_chain") or [])
        ok = check("branch:M@while_else>case" in reads
                   and "branch:M@while_else>case" in chain,
                   "AC-PNAF2 the else case is named branch:M@while_else>case "
                   "(%s / %s)" % (reads, chain)) and ok
        ok = check(parent.get("state") == PNAE.STATE_REFUSED
                   and parent.get("reason")
                   == "attr-module-alias-unbound:M.HW",
                   "AC-PNAF2 the R2592 reader still refuses this shape "
                   "(%s/%s)" % (parent.get("state"),
                                parent.get("reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaf3():
    """A for body, a for else, a with in a while and a two-deep branch stay."""
    cases = [("for body", FOR_ONE), ("for else section", FOR_ELSE),
             ("with nested in a while", NESTED_WITH),
             ("branch nested two deep in a while", NESTED_TWO)]
    ok = True
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            got = entry(PNAF, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAE, "import mk\n" + RECV + TAIL, root)
            ok = check(got.get("state") == PNAF.STATE_REFUSED
                       and got.get("value") is None,
                       "AC-PNAF3 a %s walrus is still refused (%s/%s)"
                       % (label, got.get("state"), got.get("value"))) and ok
            ok = check(got.get("state") == parent.get("state")
                       and got.get("reason") == parent.get("reason"),
                       "AC-PNAF3 the shipped refusal is kept byte for byte "
                       "(%s/%s)" % (got.get("reason"),
                                    parent.get("reason"))) and ok
            ok = check(not [item for item in got.get("branch_reads") or []
                            if item.startswith("branch:")],
                       "AC-PNAF3 no branch read is published (%s)"
                       % (got.get("branch_reads"),)) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaf4():
    """A match nested two levels inside a while body stays refused."""
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "mk.py": MATCH_TWO_DEEP})
    try:
        got = entry(PNAF, "import mk\n" + RECV + TAIL, root)
        parent = entry(PNAE, "import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAF.STATE_REFUSED
                   and got.get("value") is None,
                   "AC-PNAF4 a two-deep match walrus is refused (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("reason") == parent.get("reason"),
                   "AC-PNAF4 the refusal is the shipped one rather than a "
                   "guess (%s/%s)" % (got.get("reason"),
                                      parent.get("reason"))) and ok
        ok = check(not [item for item in got.get("branch_reads") or []
                        if item.startswith("branch:")],
                   "AC-PNAF4 no branch read is published (%s)"
                   % (got.get("branch_reads"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaf5():
    """Every answer the four parent faces already gave is carried."""
    cases = [
        ("module-level if branch", IF_ONE, True),
        ("module-level elif section", ELIF_ONE, True),
        ("module-level with body", WITH_ONE, True),
        ("module-level try finally", TRY_ONE, True),
        ("module-level while body", WHILE_ONE, False),
        ("module-level match case", CASE_ONE, False),
        ("while else direct walrus", WHILE_ELSE, False),
        ("two while bodies", WHILE_TWO, False),
        ("lone nested match in a while", NESTED_CASE, False),
        ("two cases in one nested match", TWO_CASES, False),
        ("function-body walrus", IN_FUNCTION, True),
        ("top-level walrus", TOP_LEVEL, True),
    ]
    ok = True
    for label, body, base in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n', "mk.py": body})
        try:
            mine = entry(PNAF, "import mk\n" + RECV + TAIL, root)
            parent = entry(PNAE, "import mk\n" + RECV + TAIL, root)
            same = (mine.get("state") == parent.get("state")
                    and mine.get("value") == parent.get("value")
                    and mine.get("reason") == parent.get("reason")
                    and (mine.get("branch_reads") or [])
                    == (parent.get("branch_reads") or []))
            ok = check(same,
                       "AC-PNAF5 %s reads exactly what R2592 answered "
                       "(%s/%s vs %s/%s)"
                       % (label, mine.get("state"), mine.get("value"),
                          parent.get("state"), parent.get("value"))) and ok
            carried = (mine.get("base_pnaf_state") == parent.get("state")
                       and mine.get("base_pnaf_value") == parent.get("value")
                       and mine.get("base_pnaf_reason") == parent.get("reason")
                       and (mine.get("base_pnaf_branch_reads") or [])
                       == (parent.get("branch_reads") or []))
            ok = check(carried,
                       "AC-PNAF5 %s carries the R2592 answer on the row "
                       "(%s/%s)" % (label, mine.get("base_pnaf_state"),
                                    mine.get("base_pnaf_reason"))) and ok
            if not base:
                continue
            # Wherever an older parent RESOLVES this shape, this face must
            # resolve to the same value. A shape a parent does not cover is its
            # pinned refusal, not a regression, so it is skipped rather than
            # compared.
            for tag, module in PARENTS[1:]:
                older = entry(module, "import mk\n" + RECV + TAIL, root)
                if older.get("state") != module.STATE_OK:
                    continue
                ok = check(older.get("value") == mine.get("value")
                           and mine.get("state") == module.STATE_OK,
                           "AC-PNAF5 %s still resolves where %s resolved "
                           "(%s/%s vs %s/%s)"
                           % (label, tag, mine.get("state"),
                              mine.get("value"), older.get("state"),
                              older.get("value"))) and ok
        finally:
            shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW, "pkg/__init__.py": "",
                  "pkg/consts.py": 'HW = "hw"\n', "pkg/mk5.py": RELATIVE_HEAD})
    try:
        mine = entry(PNAF, "import pkg.mk5 as mk\n" + RECV + TAIL, root)
        parent = entry(PNAE, "import pkg.mk5 as mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == parent.get("state")
                   and mine.get("value") == parent.get("value"),
                   "AC-PNAF5 a relative module alias head reads as before "
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
        mine = len(PNAF.module_alias_report(text, BASE, path)["loops"])
        parent = len(PNAE.module_alias_report(text, BASE, path)["loops"])
        loops += mine
        if mine != parent:
            mismatched.append((name, mine, parent))
    ok = check(unreadable == 0 and loops > 0 and not mismatched,
               "AC-PNAF5 a bounded live leg reads real modules read-only and "
               "agrees with its parent (modules=%d loops=%d unreadable=%d "
               "mismatched=%s)" % (len(LIVE_MODULES), loops, unreadable,
                                   mismatched)) and ok
    root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                  "mk.py": ELSE_MATCH})
    try:
        mine = entry(PNAF, "import mk\n" + RECV + TAIL, root)
        shipped = entry(PNT, "import mk\n" + RECV + TAIL, root)
        ok = check(mine.get("state") == PNAF.STATE_OK
                   and shipped.get("state") == PNT.STATE_REFUSED,
                   "AC-PNAF5 the SAME fixture is measured on BOTH readers "
                   "(here=%s/%s there=%s/%s)"
                   % (mine.get("state"), mine.get("value"),
                      shipped.get("state"), shipped.get("reason"))) and ok
        carried = [key for key in ("base_pnaf_state", "base_pnaf_value",
                                   "base_pnaf_reason", "base_pnaf_chain",
                                   "base_pnaf_branch_reads")
                   if key in mine]
        ok = check(len(carried) == 5,
                   "AC-PNAF5 the R2592 keys ride on the row (%s)"
                   % (carried,)) and ok
        left = [key for key in ("base_pnae_state", "base_pnae_reason",
                                "base_pnad_state", "base_pnad_reason",
                                "ma_chain")
                if key in mine]
        ok = check(len(left) == 5,
                   "AC-PNAF5 the R2587/R2590/R2592 keys are untouched beside "
                   "them (%s)" % (left,)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaf6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAF6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAF6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNAF6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNAF6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAF6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAF6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnaf1, ac_pnaf2, ac_pnaf3, ac_pnaf4, ac_pnaf5, ac_pnaf6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())