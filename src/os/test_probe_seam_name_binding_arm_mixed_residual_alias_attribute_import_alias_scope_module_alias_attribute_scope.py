"""AC-PNMA1..AC-PNMA6 suite for the module-alias-attribute / function-name /
call-context face (R2579).

Criteria were pinned in state/queue/tech.md:613 at R2577 BEFORE this code
existed.

Every fixture lives in a private temporary directory; no shipped source file is
written. Stdlib only, ASCII source, zero network, no clock.
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_scope as MAA  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_module_alias_attribute_scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_'
               'scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"

HW = 'ATTR = "b"\nNAMES = ["x"]\n'


def arms(binding):
    return ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding))


def with_attr(receiver):
    return ("with %s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver,))


def with_call(receiver):
    return ("with %s() as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver,))


def world(files):
    root = tempfile.mkdtemp(prefix="pnpma-")
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
    rows = MAA.module_alias_attribute_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return MAA.module_alias_entry("KEY", text, row["scope"], row["line"],
                                 root=root)


def ac_pnma1():
    """An alias chain whose final link is an ATTRIBUTE naming a module
    resolves as a with-as receiver and names the chain."""
    files = {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nBASE = consts.HW\nREG = BASE\n"}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MAA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNMA1 an attribute-final alias chain resolves to b "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check("attribute" in str(got.get("ma_hop") or ""),
                   "AC-PNMA1 the attribute hop is named (%s)"
                   % (got.get("ma_hop"),)) and ok
        ok = check("REG" in (got.get("ma_chain") or [])
                   and "BASE" in (got.get("ma_chain") or [])
                   and "consts.HW" in (got.get("ma_chain") or []),
                   "AC-PNMA1 the chain names every link (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnma_reason") == "attr-with-as:m.ATTR",
                   "AC-PNMA1 the shipped face it replaces refused it (%s)"
                   % (got.get("base_pnma_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nBASE = consts.HW\nMID = BASE\n"
                      "REG = MID\n"}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MAA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNMA1 a two-hop attribute chain still resolves "
                   "(%s/%s)" % (got.get("state"), got.get("value"))) and ok
        ok = check(len(got.get("ma_chain") or []) >= 3,
                   "AC-PNMA1 the two-hop chain is carried in full (%s)"
                   % (got.get("ma_chain"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnma2():
    """A module-level function returning a NAME bound to a class attribute
    resolves; one returning a NAME bound to a non-module literal is refused."""
    files = {"hw.py": HW,
             "mk.py": ('class Box:\n    NAME = "hw"\n'
                       'REG2 = Box.NAME\n'
                       'def make():\n    return REG2\n'
                       'REG = make()\n')}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MAA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNMA2 a function returning a NAME bound to a class "
                   "attribute resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check("function" in str(got.get("ma_hop") or ""),
                   "AC-PNMA2 the function hop is named (%s)"
                   % (got.get("ma_hop"),)) and ok
        ok = check(got.get("base_pnma_reason") == "attr-with-as:m.ATTR",
                   "AC-PNMA2 the shipped face it replaces refused it (%s)"
                   % (got.get("base_pnma_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"hw.py": HW,
             "mk.py": ('class Box:\n    NAME = "hw"\n'
                       'REG2 = "notamodule"\n'
                       'def make():\n    return REG2\n'
                       'REG = make()\n')}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("ma_state") != MAA.STATE_OK,
                   "AC-PNMA2 a function returning a NAME bound to a "
                   "non-module literal is not resolved (%s/%s)"
                   % (got.get("ma_state"), got.get("ma_value"))) and ok
        ok = check(got.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNMA2 it keeps the shipped refusal word (%s)"
                   % (got.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnma3():
    """A with-as context that is a CALL on an alias chain name resolves and
    names the call hop."""
    files = {"hw.py": HW,
             "mk.py": ('def mkmod():\n    return "hw"\n'
                       'REG = mkmod\n')}
    root = world(files)
    try:
        got = entry("import mk\n" + with_call("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MAA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNMA3 a call context on an alias chain name resolves "
                   "to b (%s/%s)" % (got.get("state"), got.get("value")))
        ok = check("call" in str(got.get("ma_hop") or ""),
                   "AC-PNMA3 the call hop is named (%s)"
                   % (got.get("ma_hop"),)) and ok
        ok = check(any("mk.REG()" == item for item in
                       (got.get("ma_chain") or [])),
                   "AC-PNMA3 the chain carries the call context (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnma_reason") == "attr-cross-call:m.ATTR",
                   "AC-PNMA3 the shipped face it replaces refused it (%s)"
                   % (got.get("base_pnma_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"hw.py": HW,
             "mk.py": ('def mkmod():\n    return "hw"\n'
                       'REG = mkmod\n')}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("ma_state") != MAA.STATE_OK,
                   "AC-PNMA3 a callable alias is not read as a module "
                   "without a call (%s/%s)"
                   % (got.get("ma_state"), got.get("ma_value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnma4():
    """A chain whose attribute link names a module that is not on disk is
    NAMED with the link that broke rather than resolved."""
    files = {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nBASE = consts.NOSUCH\nREG = BASE\n"}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MAA.STATE_REFUSED,
                   "AC-PNMA4 a missing attribute link is refused (%s)"
                   % (got.get("state"),))
        ok = check(str(got.get("reason") or "").endswith(":consts.NOSUCH"),
                   "AC-PNMA4 the broken link is named (%s)"
                   % (got.get("reason"),)) and ok
        ok = check("consts.NOSUCH" in str(got.get("ma_hop") or ""),
                   "AC-PNMA4 the hop carries the broken link (%s)"
                   % (got.get("ma_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"hw.py": HW,
             "mk.py": "import nosuchmod\nREG = nosuchmod.HW\n"}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MAA.STATE_REFUSED
                   and "nosuchmod.HW" in str(got.get("reason") or ""),
                   "AC-PNMA4 a module not on disk is named, not resolved "
                   "(%s/%s)" % (got.get("state"), got.get("reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnma5():
    """Every answer the fifteen shipped faces already gave is carried
    unchanged on the row."""
    root = world({"hw.py": HW})
    try:
        got = entry("import hw\n" + arms("hw.ATTR") + TAIL, root)
        ok = check(got.get("base_pnma_state") == MAA.STATE_OK
                   and got.get("base_pnma_value") == "b",
                   "AC-PNMA5 the shipped ok answer rides beside this face "
                   "(%s/%s)" % (got.get("base_pnma_state"),
                                got.get("base_pnma_value")))
        ok = check(got.get("state") == MAA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNMA5 this face does not rewrite a shipped answer "
                   "(%s/%s)" % (got.get("state"), got.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    try:
        rel = entry("from .cls import K\n" + arms("K.ATTR") + TAIL, root)
        ok = check(rel.get("state") == MAA.STATE_REFUSED,
                   "AC-PNMA5 the shipped relative-name refusal is kept (%s)"
                   % (rel.get("state"),)) and ok
        ok = check(rel.get("reason") == "attr-relative-from-name:K.ATTR",
                   "AC-PNMA5 it keeps its own shipped word (%s)"
                   % (rel.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW,
                  "mk.py": 'class Box:\n    NAME = "hw"\n'
                           '    def open(self):\n        return self.NAME\n',
                  "reg.py": "from mk import Box\nREG = Box().open()\n"})
    try:
        call = entry("import reg\n" + with_attr("reg.REG") + TAIL, root)
        ok = check(call.get("base_pnma_state") == MAA.STATE_OK
                   and call.get("base_pnma_value") == "b",
                   "AC-PNMA5 the shipped module-value answer is carried "
                   "(%s/%s)" % (call.get("base_pnma_state"),
                                call.get("base_pnma_value"))) and ok
        ok = check("module-value" in str(call.get("ma_hop") or ""),
                   "AC-PNMA5 the shipped hop word is carried (%s)"
                   % (call.get("ma_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW, "reg.py": "REG = 3\n"})
    try:
        flat = entry("import reg\n" + with_attr("reg.REG") + TAIL, root)
        ok = check(flat.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNMA5 the shipped with-as refusal still rides (%s)"
                   % (flat.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnma6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNMA6 module source is pure ASCII (%dB)"
               % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNMA6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNMA6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNMA6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNMA6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(MAA.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope-module-alias-attribute-"
               "scope",
               "AC-PNMA6 the face carries its own label (%s)"
               % (MAA.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNMA6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNMA6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNMA6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pnma1(), ac_pnma2(), ac_pnma3(), ac_pnma4(),
               ac_pnma5(), ac_pnma6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())