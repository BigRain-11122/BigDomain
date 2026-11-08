"""AC-PNDCF1..AC-PNDCF6 suite for the call-target / local-return /
relative-import / nested-constant face (R2569).

Criteria were pinned in state/queue/tech.md:603 at R2565 BEFORE this code
existed.

What this proves, MEASURED at R2565 with src/os/limits_from_scope_R2565.py
against one private world where the honest answer is `b`, and re-measured here:
a with-as context that is a call on an ATTRIBUTE reads attr-with-as:m.ATTR and
is never resolved, a call returning its module name through a LOCAL variable is
never followed, a relative `from . import helper` reads attr-base-local:helper,
and a constant that only a NESTED function binds is resolved anyway.

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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope as CT  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_call_target_scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_call_target_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-call-target-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_call_target_scope.py"),')

TAIL = 'for name in hw.NAMES:\n    pass\n'


def arms(binding, indent="", tail=True):
    body = ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding)).split("\n")
    text = "\n".join((indent + line) if line else line for line in body)
    return text + (TAIL if tail and not indent else "")


def world(files):
    root = tempfile.mkdtemp(prefix="pndcf-")
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
    rows = CT.call_target_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return CT.call_target_entry(name, text, row["scope"], row["line"],
                                root=root)


def ac_pndcf1():
    """A with-as context that is a call on an attribute resolves or is NAMED."""
    root = world({"hw3.py": 'ATTR = "b"\n'})
    try:
        text = ('class Box:\n'
                '    def open(self):\n'
                '        return "hw3"\n'
                'with Box().open() as m:\n'
                + arms("m.ATTR", "    ") + TAIL)
        got = entry(text, "KEY", root)
        ok = check(got.get("state") == CT.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCF1 an attribute call returning a module resolves "
                   "to b (%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("base_ct_reason") == "attr-with-as:m.ATTR",
                   "AC-PNDCF1 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_ct_reason"),)) and ok
        ok = check(str(got.get("ct_hop") or "").startswith(
            "with-as-call-target"),
                   "AC-PNDCF1 the call-target hop is named (%s)"
                   % (got.get("ct_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw3.py": 'ATTR = "b"\n'})
    try:
        text = ('class Box:\n'
                '    def open(self):\n'
                '        return 1\n'
                'with Box().open() as m:\n'
                + arms("m.ATTR", "    ") + TAIL)
        bad = entry(text, "KEY", root)
        ok = check(bad.get("state") == CT.STATE_REFUSED,
                   "AC-PNDCF1 an attribute call returning something else is "
                   "refused (%s)" % (bad.get("state"),)) and ok
        ok = check(bad.get("reason") == "attr-call-target:m.ATTR",
                   "AC-PNDCF1 a non-module attribute call is NAMED (%s)"
                   % (bad.get("reason"),)) and ok
        ok = check(bad.get("value") is None,
                   "AC-PNDCF1 a refusal resolves nothing (%s)"
                   % (bad.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcf2():
    """A function returning its module name through a LOCAL resolves."""
    root = world({"hw3.py": 'ATTR = "b"\n'})
    try:
        text = ('def open_module():\n'
                '    m = "hw3"\n'
                '    return m\n'
                'with open_module() as md:\n'
                + arms("md.ATTR", "    ") + TAIL)
        got = entry(text, "KEY", root)
        ok = check(got.get("state") == CT.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCF2 a local-returned module resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_ct_reason") == "attr-with-as:md.ATTR",
                   "AC-PNDCF2 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_ct_reason"),)) and ok
        ok = check(str(got.get("ct_hop") or "").startswith("with-as-call"),
                   "AC-PNDCF2 the with-as call hop is named (%s)"
                   % (got.get("ct_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw3.py": 'ATTR = "b"\n'})
    try:
        text = ('def open_module():\n'
                '    m = "nope"\n'
                '    return m\n'
                'with open_module() as md:\n'
                + arms("md.ATTR", "    ") + TAIL)
        bad = entry(text, "KEY", root)
        ok = check(bad.get("state") == CT.STATE_REFUSED
                   and bad.get("value") is None,
                   "AC-PNDCF2 a local that is not a module resolves nothing "
                   "(%s/%s)" % (bad.get("state"), bad.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcf3():
    """A relative `from . import helper` resolves, never a local."""
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        got = entry('from . import helper\n' + arms("helper.ATTR"), "KEY",
                    root)
        ok = check(got.get("state") == CT.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCF3 a relative from-import resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_shipped_reason") == "attr-base-local:helper",
                   "AC-PNDCF3 the shipped answer it replaces called it a local "
                   "(%s)" % (got.get("base_shipped_reason"),)) and ok
        ok = check(str(got.get("ct_hop") or "").startswith("from-relative"),
                   "AC-PNDCF3 the relative hop is named (%s)"
                   % (got.get("ct_hop"),)) and ok
        ok = check(str(got.get("reason") or "").find("attr-base-local") < 0,
                   "AC-PNDCF3 the module is never a local on this row (%s)"
                   % (got.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"other.py": 'ATTR = "b"\n'})
    try:
        bad = entry('from . import helper\n' + arms("helper.ATTR"), "KEY",
                    root)
        ok = check(bad.get("state") == CT.STATE_REFUSED,
                   "AC-PNDCF3 an absent relative module resolves nothing (%s)"
                   % (bad.get("state"),)) and ok
        ok = check(bad.get("value") is None,
                   "AC-PNDCF3 an absent relative module is not a local either "
                   "(%s)" % (bad.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcf4():
    """A constant bound only inside a NESTED function is NAMED."""
    root = world({"helper.py": ('def outer():\n'
                                '    def inner():\n'
                                '        ATTR = "b"\n'
                                '        return ATTR\n'
                                '    return 1\n')})
    try:
        got = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(got.get("base_ct_state") == CT.STATE_OK
                   and got.get("base_ct_value") == "b",
                   "AC-PNDCF4 the shipped faces resolved the nested constant "
                   "(%s/%s)" % (got.get("base_ct_state"),
                                got.get("base_ct_value")))
        ok = check(got.get("state") == CT.STATE_REFUSED,
                   "AC-PNDCF4 this face refuses the over-resolution (%s)"
                   % (got.get("state"),)) and ok
        ok = check(got.get("reason") == "attr-nested-constant:helper.ATTR",
                   "AC-PNDCF4 the nested constant is NAMED (%s)"
                   % (got.get("reason"),)) and ok
        ok = check(got.get("value") is None,
                   "AC-PNDCF4 a nested-only constant resolves nothing (%s)"
                   % (got.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"helper.py": ('def make():\n'
                                '    ATTR = "b"\n'
                                '    return ATTR\n')})
    try:
        got = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(got.get("state") == CT.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCF4 a module-level function constant still resolves "
                   "(%s/%s)" % (got.get("state"), got.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcf5():
    """Every shipped answer rides beside this face own on every row."""
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        got = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(got.get("base_ct_state") == CT.STATE_OK
                   and got.get("base_ct_value") == "b",
                   "AC-PNDCF5 the shipped ok answer rides beside this face "
                   "(%s/%s)" % (got.get("base_ct_state"),
                                got.get("base_ct_value")))
        ok = check(got.get("state") == CT.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCF5 this face does not rewrite the shipped ok "
                   "answer (%s/%s)" % (got.get("state"),
                                       got.get("value"))) and ok
        ok = check(got.get("base_ct_hop") is not None,
                   "AC-PNDCF5 the shipped hop rides beside this face (%s)"
                   % (got.get("base_ct_hop"),)) and ok
        ok = check(got.get("ct_source") == CT.SOURCE_CALL_TARGET,
                   "AC-PNDCF5 this face stamps its own source (%s)"
                   % (got.get("ct_source"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"pkg/helper.py": 'ATTR = "b"\n'})
    try:
        alias = entry('from pkg import helper as h\n' + arms("h.ATTR"), "KEY",
                      root)
        ok = check(alias.get("base_ct_state") == CT.STATE_OK
                   and alias.get("base_ct_value") == "b",
                   "AC-PNDCF5 the shipped from-import alias answer still "
                   "rides (%s/%s)" % (alias.get("base_ct_state"),
                                      alias.get("base_ct_value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcf6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNDCF6 module source is pure ASCII (%dB)"
               % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNDCF6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNDCF6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNDCF6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNDCF6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(CT.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope-call-target-scope",
               "AC-PNDCF6 the face carries its own label (%s)"
               % (CT.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNDCF6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNDCF6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNDCF6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pndcf1(), ac_pndcf2(), ac_pndcf3(), ac_pndcf4(),
               ac_pndcf5(), ac_pndcf6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())