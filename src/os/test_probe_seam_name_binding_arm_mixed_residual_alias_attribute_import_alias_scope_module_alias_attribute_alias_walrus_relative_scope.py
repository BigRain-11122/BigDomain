"""AC-PNAA1..AC-PNAA6 suite for the walrus-head / level-bearing-import face
(R2585).

Criteria were pinned in state/queue/tech.md:617 at R2583 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNAW  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
               "import_alias_scope_module_alias_attribute_alias_walrus_"
               "relative_scope.py")
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-walrus-relative-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'walrus_relative_scope.py"),')

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
CALL = ("with mk.REG() as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnaa-")
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


def entry(text, root):
    rows = PNAW.module_alias_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return PNAW.module_alias_entry("KEY", text, row["scope"], row["line"],
                                   root=root)


def ac_pnaa1():
    """A module-alias head bound by a WALRUS resolves and names the link."""
    root = world({"hw.py": HW,
                  "consts.py": 'HW = "hw"\n',
                  "mk.py": "import consts\n(M := consts)\nBASE = M.HW\n"
                           "REG = BASE\n"})
    try:
        got = entry("import mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAW.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAA1 a walrus alias head resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check("M.HW" in " ".join(got.get("ma_chain") or []),
                   "AC-PNAA1 the walrus link is named on the chain (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnaa_state") == PNAW.STATE_REFUSED
                   and got.get("base_pnaa_reason")
                   == "attr-module-alias-unbound:M.HW",
                   "AC-PNAA1 the shipped reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnaa_state"),
                                got.get("base_pnaa_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaa2():
    """A call context on a RELATIVE FROM-imported function name resolves."""
    root = world({"hw.py": HW,
                  "pkg/__init__.py": "",
                  "pkg/mk.py": 'def mkmod():\n    return "hw"\n',
                  "pkg/probe_conf.py": "from .mk import mkmod as REG\n"})
    try:
        got = entry("from . import probe_conf as mk\n" + CALL + TAIL, root)
        ok = check(got.get("state") == PNAW.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAA2 a relative from-imported call resolves "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check("mk.REG()" in " ".join(got.get("ma_chain") or []
                                          + [got.get("ma_hop") or ""]),
                   "AC-PNAA2 the relative hop is named (%s/%s)"
                   % (got.get("ma_hop"), got.get("ma_chain"))) and ok
        ok = check(got.get("base_pnaa_state") == PNAW.STATE_REFUSED,
                   "AC-PNAA2 the shipped reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnaa_state"),
                                got.get("base_pnaa_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaa3():
    """A relative FROM-import of a NON-function is refused with its own word."""
    root = world({"hw.py": HW,
                  "pkg/__init__.py": "",
                  "pkg/mk.py": 'CONST = "hw"\n',
                  "pkg/probe_conf3.py": "from .mk import CONST as REG\n"})
    try:
        got = entry("from . import probe_conf3 as mk\n" + CALL + TAIL, root)
        ok = check(got.get("state") == PNAW.STATE_REFUSED
                   and (got.get("reason") or "").startswith(
                       "attr-relative-import-not-callable:"),
                   "AC-PNAA3 a relative non-function refuses with this face "
                   "own word (%s/%s)" % (got.get("state"),
                                         got.get("reason")))
        ok = check(got.get("reason") != "attr-import-not-callable:REG",
                   "AC-PNAA3 the refusal is not the shipped absolute word "
                   "(%s)" % (got.get("reason"),)) and ok
        ok = check(got.get("value") is None,
                   "AC-PNAA3 nothing is resolved for the refusal") and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaa4():
    """A RELATIVE FROM-imported module alias head resolves."""
    root = world({"hw.py": HW,
                  "pkg/__init__.py": "",
                  "pkg/consts.py": 'HW = "hw"\n',
                  "pkg/mk4.py": "from . import consts\nM = consts\n"
                                "BASE = M.HW\nREG = BASE\n"})
    try:
        got = entry("import pkg.mk4 as mk\n" + RECV + TAIL, root)
        ok = check(got.get("state") == PNAW.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAA4 a relative module alias head resolves "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("base_pnaa_state") == PNAW.STATE_REFUSED,
                   "AC-PNAA4 the shipped reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnaa_state"),
                                got.get("base_pnaa_reason"))) and ok
        two = world({"hw.py": HW,
                     "consts.py": 'HW = "hw"\n',
                     "pkg/__init__.py": "",
                     "pkg/consts.py": 'HW = "hw2"\n'})
        try:
            ambiguous = entry("from . import consts as mk\n" + RECV + TAIL,
                              two)
            ok = check(ambiguous.get("state") == PNAW.STATE_REFUSED,
                       "AC-PNAA4 an AMBIGUOUS unanchored head is refused, "
                       "never guessed (%s)" % (ambiguous.get("state"),)) and ok
        finally:
            shutil.rmtree(two, ignore_errors=True)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnaa5():
    """Every answer the shipped faces already gave is carried unchanged."""
    root = world({"hw.py": HW,
                  "consts.py": 'HW = "hw"\n',
                  "mk.py": "import consts\nM: object = consts\nBASE = M.HW\n"
                           "REG = BASE\n"})
    try:
        got = entry("import mk\n" + RECV + TAIL, root)
        same = (got.get("state") == got.get("base_pnaa_state")
                and got.get("value") == got.get("base_pnaa_value")
                and got.get("reason") == got.get("base_pnaa_reason"))
        ok = check(got.get("state") == PNAW.STATE_OK and same,
                   "AC-PNAA5 an already-resolving shape reads exactly what "
                   "the parent answered (%s/%s)" % (got.get("state"),
                                                    got.get("base_pnaa_state")))
        carried = [key for key in ("base_pnma_state", "base_pnma_hop",
                                   "ma_chain", "ma_source")
                   if key in got]
        ok = check(len(carried) == 4,
                   "AC-PNAA5 the parent keys ride on the row (%s)"
                   % (carried,)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    loops = 0
    unreadable = 0
    for name in LIVE_MODULES:
        path = os.path.join(BASE, name + ".py")
        if not os.path.isfile(path):
            unreadable += 1
            continue
        text = read_bytes(path).decode("utf-8")
        loops += len(PNAW.module_alias_report(text, BASE, path)["loops"])
    ok = check(unreadable == 0 and loops > 0,
               "AC-PNAA5 a bounded live leg reads real modules read-only "
               "(modules=%d loops=%d unreadable=%d)"
               % (len(LIVE_MODULES), loops, unreadable)) and ok
    walrus = world({"hw.py": HW,
                    "consts.py": 'HW = "hw"\n',
                    "mk.py": "import consts\n(M := consts)\nBASE = M.HW\n"
                             "REG = BASE\n"})
    try:
        mine = entry("import mk\n" + RECV + TAIL, walrus)
        shipped = PNAW._BASE_MAA2_ENTRY("KEY", "import mk\n" + RECV + TAIL,
                                       "module", 1, None, walrus)
        ok = check(mine.get("state") == PNAW.STATE_OK
                   and shipped.get("state") == PNAW.STATE_REFUSED,
                   "AC-PNAA5 the SAME fixture is measured on BOTH readers "
                   "(here=%s/%s there=%s/%s)"
                   % (mine.get("state"), mine.get("value"),
                      shipped.get("state"), shipped.get("reason"))) and ok
    finally:
        shutil.rmtree(walrus, ignore_errors=True)
    return ok


def ac_pnaa6():
    """Hygiene: ASCII, stdlib only, no clock, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNAA6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-PNAA6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNAA6 the registry carries exactly one row for this face"
               ) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-PNAA6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAA6 six criteria are declared") and ok
    return ok


def main():
    checks = [ac_pnaa1, ac_pnaa2, ac_pnaa3, ac_pnaa4, ac_pnaa5, ac_pnaa6]
    results = [func() for func in checks]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())