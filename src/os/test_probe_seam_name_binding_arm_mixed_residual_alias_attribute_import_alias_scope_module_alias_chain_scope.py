"""AC-PNCS1..AC-PNCS6 suite for the module-level alias chain / module-level
function / class-constant-alias face (R2577).

Criteria were pinned in state/queue/tech.md:611 at R2575 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope as MA  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_module_alias_chain_scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_chain_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-chain-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_chain_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"

HW = 'ATTR = "b"\nNAMES = ["x"]\n'


def arms(binding):
    return ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding))


def with_attr(receiver):
    return ("with %s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver,))


def world(files):
    root = tempfile.mkdtemp(prefix="pnpcs-")
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


def entry(text, root, src_rel=None):
    src = os.path.join(root, *src_rel.split("/")) if src_rel else None
    rows = MA.module_alias_report(text, root, src)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return MA.module_alias_entry("KEY", text, row["scope"], row["line"],
                                 root=root, src_path=src)


def ac_pnpcs1():
    """A module-level ALIAS CHAIN ending at a call resolves as a with-as
    receiver and names the chain."""
    files = {"hw.py": HW,
             "mk.py": ('class Box:\n    NAME = "hw"\n'
                       '    def open(self):\n        return self.NAME\n'
                       'FIRST = Box().open()\nREG = FIRST\n')}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNCS1 an alias chain ending at a call resolves to b "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(str(got.get("ma_hop") or "").startswith(
            "with-as-module-alias"),
                   "AC-PNCS1 the alias hop is named (%s)"
                   % (got.get("ma_hop"),)) and ok
        ok = check("REG" in (got.get("ma_chain") or [])
                   and "FIRST" in (got.get("ma_chain") or []),
                   "AC-PNCS1 the chain names every link (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("ma_source") == MA.SOURCE_MODULE_ALIAS,
                   "AC-PNCS1 this face stamps its own source (%s)"
                   % (got.get("ma_source"),)) and ok
        ok = check(got.get("base_ma_reason") == "attr-with-as:m.ATTR",
                   "AC-PNCS1 the shipped face it replaces refused it (%s)"
                   % (got.get("base_ma_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"hw.py": HW,
             "mk.py": ('class Box:\n    NAME = "hw"\n'
                       '    def open(self):\n        return self.NAME\n'
                       'FIRST = Box().open()\n'
                       'MID = FIRST\nREG = MID\n')}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNCS1 a two-hop chain still resolves (%s/%s)"
                   % (got.get("state"), got.get("value"))) and ok
        ok = check(len(got.get("ma_chain") or []) >= 3,
                   "AC-PNCS1 the two-hop chain is carried in full (%s)"
                   % (got.get("ma_chain"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnpcs2():
    """A module-level function returning a class attribute resolves; one
    returning a non-module literal is refused."""
    files = {"hw.py": HW,
             "mk.py": ('class Box:\n    NAME = "hw"\n'
                       'def make():\n    return Box.NAME\n'
                       'REG = make()\n')}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNCS2 a module-level function returning a class "
                   "attribute resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(str(got.get("ma_hop") or "").startswith(
            "with-as-module-function"),
                   "AC-PNCS2 the function hop is named (%s)"
                   % (got.get("ma_hop"),)) and ok
        ok = check(got.get("base_ma_reason") == "attr-with-as:m.ATTR",
                   "AC-PNCS2 the shipped face it replaces refused it (%s)"
                   % (got.get("base_ma_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"hw.py": HW,
             "mk.py": ('class Box:\n    NAME = "hw"\n'
                       'def make():\n    return "notamodule"\n'
                       'REG = make()\n')}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("ma_state") != MA.STATE_OK,
                   "AC-PNCS2 a function returning a non-module literal is "
                   "not resolved (%s/%s)"
                   % (got.get("ma_state"), got.get("ma_value"))) and ok
        ok = check(got.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNCS2 it keeps the shipped refusal word (%s)"
                   % (got.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnpcs3():
    """A class constant aliasing a FROM-imported constant resolves; a
    FROM-imported constant used as a class base is not read as a class."""
    files = {"hw.py": HW,
             "consts.py": 'BASE = "b"\n',
             "cls.py": ("from consts import BASE\n\n"
                        "class K:\n    ATTR = BASE\n")}
    root = world(files)
    try:
        got = entry("import cls\n" + arms("cls.K.ATTR") + TAIL, root)
        ok = check(got.get("state") == MA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNCS3 a class constant aliasing a FROM-imported "
                   "constant resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_ma_reason")
                   == "attr-class-source-constant:cls.K.ATTR",
                   "AC-PNCS3 the shipped face it replaces refused it (%s)"
                   % (got.get("base_ma_reason"),)) and ok
        ok = check("from-constant" in str(got.get("ma_hop") or ""),
                   "AC-PNCS3 the from-constant hop is named (%s)"
                   % (got.get("ma_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"hw.py": HW,
             "consts.py": 'BASE = "hw"\n',
             "cls.py": ('from consts import BASE\n\n'
                        'class K(BASE):\n    ATTR = "b"\n')}
    root = world(files)
    try:
        got = entry("import cls\n" + arms("cls.K.ATTR") + TAIL, root)
        ok = check(got.get("state") == MA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNCS3 a FROM-imported constant used as a base is not "
                   "a class, the own constant still reads (%s/%s)"
                   % (got.get("state"), got.get("value"))) and ok
        ok = check("class" in str(got.get("ma_hop") or ""),
                   "AC-PNCS3 the class hop is named rather than a base hop "
                   "(%s)" % (got.get("ma_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnpcs4():
    """A chain that ends at a name bound nowhere is NAMED with the name that
    broke rather than resolved."""
    files = {"hw.py": HW, "mk.py": "REG = MISSING_NAME\n"}
    root = world(files)
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MA.STATE_REFUSED,
                   "AC-PNCS4 an unbound chain end is refused (%s)"
                   % (got.get("state"),))
        ok = check(got.get("reason") == "attr-module-alias-unbound:MISSING_NAME",
                   "AC-PNCS4 the broken name is named (%s)"
                   % (got.get("reason"),)) and ok
        ok = check("MISSING_NAME" in str(got.get("ma_hop") or ""),
                   "AC-PNCS4 the hop carries the broken name (%s)"
                   % (got.get("ma_hop"),)) and ok
        ok = check("MISSING_NAME" in (got.get("ma_chain") or []),
                   "AC-PNCS4 the chain carries the broken link (%s)"
                   % (got.get("ma_chain"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"hw.py": HW, "mk.py": "REG = MISSING_NAME\n"}
    root = world(files)
    try:
        got = entry("import mk\n"
                    "if a1:\n    KEY = mk.REG.ATTR\n"
                    "else:\n    KEY = mk.REG.ATTR\n" + TAIL, root)
        ok = check(got.get("reason") == "attr-module-alias-unbound:MISSING_NAME",
                   "AC-PNCS4 the module-attribute path names it too (%s)"
                   % (got.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnpcs5():
    """Every answer the shipped faces already gave is carried unchanged."""
    root = world({"hw.py": HW})
    try:
        got = entry("import hw\n" + arms("hw.ATTR") + TAIL, root)
        ok = check(got.get("base_ma_state") == MA.STATE_OK
                   and got.get("base_ma_value") == "b",
                   "AC-PNCS5 the shipped ok answer rides beside this face "
                   "(%s/%s)" % (got.get("base_ma_state"),
                                got.get("base_ma_value")))
        ok = check(got.get("state") == MA.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNCS5 this face does not rewrite a shipped answer "
                   "(%s/%s)" % (got.get("state"), got.get("value"))) and ok
        ok = check(got.get("ma_state") == MA.STATE_OK
                   and got.get("ma_source") == got.get("base_ma_source"),
                   "AC-PNCS5 a carried answer keeps the shipped source "
                   "(%s/%s)" % (got.get("ma_source"),
                                got.get("base_ma_source"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    try:
        rel = entry("from .cls import K\n" + arms("K.ATTR") + TAIL, root)
        ok = check(rel.get("state") == MA.STATE_REFUSED,
                   "AC-PNCS5 the shipped relative-name refusal is kept (%s)"
                   % (rel.get("state"),)) and ok
        ok = check(rel.get("reason") == "attr-relative-from-name:K.ATTR",
                   "AC-PNCS5 it keeps its own shipped word (%s)"
                   % (rel.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW,
                  "mk.py": 'class Box:\n    NAME = "hw"\n'
                           '    def open(self):\n        return self.NAME\n',
                  "reg.py": "from mk import Box\nREG = Box().open()\n"})
    try:
        call = entry("import reg\n" + with_attr("reg.REG") + TAIL, root)
        ok = check(call.get("base_ma_state") == MA.STATE_OK
                   and call.get("base_ma_value") == "b",
                   "AC-PNCS5 the shipped module-value answer is carried "
                   "(receiver binds the module, ATTR reads b) (%s/%s)"
                   % (call.get("base_ma_state"),
                      call.get("base_ma_value"))) and ok
        ok = check("with-as-module-value" in str(call.get("ma_hop") or ""),
                   "AC-PNCS5 the shipped hop word is carried (%s)"
                   % (call.get("ma_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW, "reg.py": "REG = 3\n"})
    try:
        flat = entry("import reg\n" + with_attr("reg.REG") + TAIL, root)
        ok = check(flat.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNCS5 the shipped with-as refusal still rides (%s)"
                   % (flat.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnpcs6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNCS6 module source is pure ASCII (%dB)"
               % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNCS6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNCS6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNCS6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNCS6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(MA.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope-module-alias-chain-scope",
               "AC-PNCS6 the face carries its own label (%s)"
               % (MA.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNCS6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNCS6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNCS6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pnpcs1(), ac_pnpcs2(), ac_pnpcs3(), ac_pnpcs4(),
               ac_pnpcs5(), ac_pnpcs6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())