"""AC-PNDCE1..AC-PNDCE6 suite for the from-import / function-constant /
with-as-call face (R2565).

Criteria were pinned in state/queue/tech.md:601 at R2563 BEFORE this code
existed.

What this proves, MEASURED at R2563 with
src/os/limits_import_alias_residual_R2563.py against one private world where the
honest answer is `b`, and re-measured here before any code: `from pkg import
helper` reads attr-base-local:helper because the shipped import table is built
from plain ast.Import nodes only, a helper constant declared only inside a
function body reads attr-plain-import:helper.ATTR because the module reading
never enters a function body, and `with open_module() as m` reads
attr-with-as:m.ATTR even when the call returns a module name.

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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_from_scope as FSC  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_from_scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_from_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-from-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_from_scope.py"),')

TAIL = 'for name in hw.NAMES:\n    pass\n'


def arms(binding, indent="", tail=True):
    body = ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding)).split("\n")
    text = "\n".join((indent + line) if line else line for line in body)
    return text + (TAIL if tail and not indent else "")


def world(files):
    root = tempfile.mkdtemp(prefix="pndce-")
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
    rows = FSC.from_scope_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return FSC.from_scope_entry(name, text, row["scope"], row["line"],
                                root=root)


def ac_pndce1():
    """A FROM-imported module resolves through pkg/helper.py."""
    root = world({"pkg/helper.py": 'ATTR = "b"\n'})
    try:
        got = entry('from pkg import helper\n' + arms("helper.ATTR"), "KEY",
                    root)
        ok = check(got.get("state") == FSC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCE1 a from-imported module resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_shipped_reason") == "attr-base-local:helper",
                   "AC-PNDCE1 the shipped answer it replaces called it a local "
                   "(%s)" % (got.get("base_shipped_reason"),)) and ok
        ok = check(got.get("from_hop") == "from-import",
                   "AC-PNDCE1 the from-import hop is named (%s)"
                   % (got.get("from_hop"),)) and ok
        ok = check(str(got.get("reason") or "").find("attr-base-local") < 0,
                   "AC-PNDCE1 the module is never a local on this row (%s)"
                   % (got.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"pkg/other.py": 'ATTR = "b"\n'})
    try:
        bad = entry('from pkg import helper\n' + arms("helper.ATTR"), "KEY",
                    root)
        ok = check(bad.get("state") == FSC.STATE_REFUSED
                   and bad.get("value") is None,
                   "AC-PNDCE1 an absent from-imported module resolves nothing "
                   "(%s/%s)" % (bad.get("state"), bad.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndce2():
    """`from pkg import helper as h` resolves through the actual module."""
    root = world({"pkg/helper.py": 'ATTR = "b"\n'})
    try:
        got = entry('from pkg import helper as h\n' + arms("h.ATTR"), "KEY",
                    root)
        ok = check(got.get("state") == FSC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCE2 a from-import alias resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_shipped_reason") == "attr-base-local:h",
                   "AC-PNDCE2 the shipped answer it replaces called it a local "
                   "(%s)" % (got.get("base_shipped_reason"),)) and ok
        ok = check(got.get("base_from_state") is None
                   and got.get("base_from_reason") is None,
                   "AC-PNDCE2 the shipped import-alias layer was silent here "
                   "(%s/%s)" % (got.get("base_from_state"),
                                got.get("base_from_reason"))) and ok
        ok = check(str(got.get("reason") or "").find("attr-base-local") < 0,
                   "AC-PNDCE2 the alias is never a local on this row (%s)"
                   % (got.get("reason"),)) and ok
        ok = check(got.get("from_hop") == "from-import",
                   "AC-PNDCE2 the module is reached by its real name (%s)"
                   % (got.get("from_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndce3():
    """A function-level helper constant resolves when returned, else NAMED."""
    root = world({"helper.py": 'def make():\n    ATTR = "b"\n    return ATTR\n'})
    try:
        got = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(got.get("state") == FSC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCE3 a returned function constant resolves to b "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("base_from_reason") == "attr-plain-import:helper.ATTR",
                   "AC-PNDCE3 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_from_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"helper.py": 'def make():\n    ATTR = "b"\n    return 1\n'})
    try:
        bad = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(bad.get("state") == FSC.STATE_REFUSED,
                   "AC-PNDCE3 an unreturned function constant is refused (%s)"
                   % (bad.get("state"),)) and ok
        ok = check(bad.get("reason") == "attr-function-constant:helper.ATTR",
                   "AC-PNDCE3 an unreturned function constant is NAMED (%s)"
                   % (bad.get("reason"),)) and ok
        ok = check(bad.get("value") is None,
                   "AC-PNDCE3 a refusal resolves nothing (%s)"
                   % (bad.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndce4():
    """A with-as call returning a module name resolves; anything else stays."""
    root = world({"hw3.py": 'ATTR = "b"\n'})
    try:
        text = ('def open_module():\n    return "hw3"\n'
                'with open_module() as m:\n'
                + arms("m.ATTR", "    ") + TAIL)
        got = entry(text, "KEY", root)
        ok = check(got.get("state") == FSC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCE4 a with-as call returning a module resolves to b "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("base_from_reason") == "attr-with-as:m.ATTR",
                   "AC-PNDCE4 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_from_reason"),)) and ok
        ok = check(got.get("from_hop") == "with-as-call",
                   "AC-PNDCE4 the with-as call hop is named (%s)"
                   % (got.get("from_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw3.py": 'ATTR = "b"\n'})
    try:
        text = ('def pick():\n    return "nope"\n'
                'with pick() as m:\n'
                + arms("m.ATTR", "    ") + TAIL)
        bad = entry(text, "KEY", root)
        ok = check(bad.get("state") == FSC.STATE_REFUSED,
                   "AC-PNDCE4 a call returning something else is refused (%s)"
                   % (bad.get("state"),)) and ok
        ok = check(bad.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNDCE4 a non-module call keeps the shipped word (%s)"
                   % (bad.get("reason"),)) and ok
        ok = check(bad.get("value") is None,
                   "AC-PNDCE4 a non-module call resolves nothing (%s)"
                   % (bad.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndce5():
    """Every shipped import-alias answer is carried unchanged."""
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        got = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(got.get("base_from_state") == FSC.STATE_OK
                   and got.get("base_from_value") == "b",
                   "AC-PNDCE5 the shipped ok answer rides beside this face "
                   "(%s/%s)" % (got.get("base_from_state"),
                                got.get("base_from_value")))
        ok = check(got.get("state") == FSC.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCE5 this face does not rewrite the shipped ok "
                   "answer (%s/%s)" % (got.get("state"),
                                       got.get("value"))) and ok
        ok = check(got.get("base_from_hop") is not None,
                   "AC-PNDCE5 the shipped hop rides beside this face (%s)"
                   % (got.get("base_from_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"helper.py": 'BASE = "b"\nATTR = BASE\n'})
    try:
        alias = entry('import helper\n' + arms("helper.ATTR"), "KEY", root)
        ok = check(alias.get("base_from_state") == FSC.STATE_OK
                   and alias.get("base_from_value") == "b",
                   "AC-PNDCE5 the shipped alias answer still rides (%s/%s)"
                   % (alias.get("base_from_state"),
                      alias.get("base_from_value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndce6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNDCE6 module source is pure ASCII (%dB)"
               % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNDCE6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNDCE6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNDCE6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNDCE6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(FSC.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope-from-scope",
               "AC-PNDCE6 the face carries its own label (%s)"
               % (FSC.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNDCE6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNDCE6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNDCE6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pndce1(), ac_pndce2(), ac_pndce3(), ac_pndce4(),
               ac_pndce5(), ac_pndce6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())