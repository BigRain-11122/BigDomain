"""AC-PNDC1..AC-PNDC6 suite for the alias attribute import-alias face (R2563).

Criteria were pinned in state/queue/tech.md:599 at R2561 BEFORE this code
existed.

What this proves, MEASURED at R2561 and re-measured at R2563 with
src/os/limits_attribute_import_alias_R2563.py against one private world where the
honest answer is `b`: a plain `import helper` base reads state=None with no
reason at all (silent, not refused), `import helper as h` reads attr-base-local:h
because the import set records the module name and the alias is mistaken for a
local, a module reached by `with hw2 as m` reads attr-base-local:m, a helper
constant that is an alias of another constant reads attr-non-constant, a helper
constant re-exported by `from hc import ATTR` reads attr-missing, and a helper
carrying TWO values through an alias reads `ok` - an over-resolution.

Every fixture lives in a string or in a private temporary directory; no shipped
source file is written. Stdlib only, ASCII source, zero network, no clock.
Exit 0 = all green.
"""

import os
import re
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_scope as PNDB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope as PNDC  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope.py"),')

TAIL = 'for name in hw.NAMES:\n    pass\n'


def arms(binding):
    return ('if a1:\n    KEY = %s\nelse:\n    KEY = %s\n'
            % (binding, binding)) + TAIL


def world(files):
    root = tempfile.mkdtemp(prefix="pndc-")
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


def entry(text, name, root=None):
    rows = PNDC.import_alias_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return PNDC.import_alias_entry(name, text, row["scope"], row["line"],
                                   root=root)


def ac_pndc1():
    """A plain import base resolves, and is NAMED when it cannot be."""
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        got = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(got.get("state") == PNDC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDC1 a plain import base resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_import_alias_state") is None
                   and got.get("base_import_alias_reason") is None,
                   "AC-PNDC1 the shipped answer it replaces was silent "
                   "(%s/%s)" % (got.get("base_import_alias_state"),
                                got.get("base_import_alias_reason"))) and ok
        ok = check(got.get("ia_hop") == "import",
                   "AC-PNDC1 the hop is named (%s)"
                   % (got.get("ia_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({})
    try:
        bad = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(bad.get("state") == PNDC.STATE_REFUSED,
                   "AC-PNDC1 an unresolvable plain import is refused (%s)"
                   % (bad.get("state"),)) and ok
        ok = check(bad.get("reason") == "attr-plain-import:helper.ATTR",
                   "AC-PNDC1 an unresolvable plain import is NAMED (%s)"
                   % (bad.get("reason"),)) and ok
        ok = check(bad.get("value") is None,
                   "AC-PNDC1 a refusal resolves nothing (%s)"
                   % (bad.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndc2():
    """An `import m as x` base resolves through the ACTUAL module name."""
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        got = entry('import helper as h\n' + arms("h.ATTR"), "KEY", root)
        ok = check(got.get("state") == PNDC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDC2 an import alias resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_import_alias_reason") == "attr-base-local:h",
                   "AC-PNDC2 the shipped answer it replaces called it a local "
                   "(%s)" % (got.get("base_import_alias_reason"),)) and ok
        ok = check(str(got.get("reason") or "").find("attr-base-local") < 0,
                   "AC-PNDC2 the alias is never a local on this row (%s)"
                   % (got.get("reason"),)) and ok
        ok = check(got.get("ia_hop") == "import-alias",
                   "AC-PNDC2 the alias hop is named (%s)"
                   % (got.get("ia_hop"),)) and ok
        ok = check(got.get("ia_chain") == ["h->helper.ATTR"],
                   "AC-PNDC2 the chain names alias and module (%s)"
                   % (got.get("ia_chain"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndc3():
    """A with-as module binding resolves; a non-module context is NAMED."""
    root = world({"hw2.py": 'ATTR = "b"\n'})
    try:
        got = entry('with hw2 as m:\n'
                    '    if a1:\n        KEY = m.ATTR\n'
                    '    else:\n        KEY = m.ATTR\n' + TAIL, "KEY", root)
        ok = check(got.get("state") == PNDC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDC3 a with-as module resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_import_alias_reason") == "attr-base-local:m",
                   "AC-PNDC3 the shipped answer it replaces called it a local "
                   "(%s)" % (got.get("base_import_alias_reason"),)) and ok
        ok = check(got.get("ia_hop") == "with-as",
                   "AC-PNDC3 the with-as hop is named (%s)"
                   % (got.get("ia_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw2.py": 'ATTR = "b"\nctx = 1\n'})
    try:
        bad = entry('with hw2.ctx as m:\n'
                    '    if a1:\n        KEY = m.ATTR\n'
                    '    else:\n        KEY = m.ATTR\n' + TAIL, "KEY", root)
        ok = check(bad.get("state") == PNDC.STATE_REFUSED
                   and bad.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNDC3 a non-module with-as context is NAMED (%s)"
                   % (bad.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndc4():
    """A constant alias is followed; two values still read name-mixed."""
    root = world({"helper.py": 'BASE = "b"\nATTR = BASE\n'})
    try:
        got = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(got.get("state") == PNDC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDC4 an alias constant resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(str(got.get("base_import_alias_reason")
                       or "").startswith("attr-non-constant:"),
                   "AC-PNDC4 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_import_alias_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"helper.py": 'BASE = "b"\nATTR = BASE\n'
                              'if z:\n    ATTR = "c"\n'})
    try:
        mixed = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(mixed.get("reason") == "name-mixed:helper.ATTR",
                   "AC-PNDC4 two values read name-mixed (%s)"
                   % (mixed.get("reason"),)) and ok
        ok = check(mixed.get("value") is None,
                   "AC-PNDC4 a mixed name resolves nothing (%s)"
                   % (mixed.get("value"),)) and ok
        ok = check(mixed.get("base_import_alias_state") == PNDC.STATE_OK,
                   "AC-PNDC4 the shipped answer it replaces OVER-resolved (%s)"
                   % (mixed.get("base_import_alias_state"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndc5():
    """A re-export `from other import NAME` resolves through that module."""
    root = world({"helper.py": 'from hc import ATTR\n',
                  "hc.py": 'ATTR = "b"\n'})
    try:
        got = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(got.get("state") == PNDC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDC5 a re-export resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_import_alias_reason")
                   == "attr-missing:helper.ATTR",
                   "AC-PNDC5 the shipped answer it replaces read attr-missing "
                   "(%s)" % (got.get("base_import_alias_reason"),)) and ok
        ok = check(str(got.get("ia_hop") or "").find("reexport") >= 0,
                   "AC-PNDC5 the re-export hop is published (%s)"
                   % (got.get("ia_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"helper.py": 'from hc import ATTR\n',
                  "hc.py": 'BASE = "b"\nATTR = BASE\n'})
    try:
        deep = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(deep.get("state") == PNDC.STATE_OK
                   and deep.get("value") == "b",
                   "AC-PNDC5 a re-export of an alias resolves to b (%s/%s)"
                   % (deep.get("state"), deep.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndc6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNDC6 module source is pure ASCII (%dB)" % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNDC6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNDC6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNDC6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNDC6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(PNDC.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope",
               "AC-PNDC6 the face carries its own label (%s)"
               % (PNDC.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNDC6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNDC6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNDC6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pndc1(), ac_pndc2(), ac_pndc3(), ac_pndc4(), ac_pndc5(),
               ac_pndc6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())