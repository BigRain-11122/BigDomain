"""AC-PNAM1..AC-PNAM6 suite for the module-alias-head / two-step-path /
FROM-imported-call face (R2583).

Criteria were pinned in state/queue/tech.md:615 at R2579 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_scope as MAA2  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_module_alias_attribute_alias_scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-module-alias-attribute-'
               'alias-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_module_alias_attribute_alias_'
               'scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"

HW = 'ATTR = "b"\nNAMES = ["x"]\n'


def with_attr(receiver):
    return ("with %s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver,))


def with_call(receiver):
    return ("with %s() as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver,))


def world(files):
    root = tempfile.mkdtemp(prefix="pnam-")
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
    rows = MAA2.module_alias_alias_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return MAA2.module_alias_entry("KEY", text, row["scope"], row["line"],
                                   root=root)


def ac_pnam1():
    """An attribute head bound by a MODULE ALIAS resolves as a with-as
    receiver and names the alias link."""
    root = world({"hw.py": HW,
                  "consts.py": 'HW = "hw"\n',
                  "mk.py": "import consts\nM = consts\nBASE = M.HW\n"
                           "REG = BASE\n"})
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MAA2.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAM1 a module-alias head resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check("M.HW" in " ".join(got.get("ma_chain") or []),
                   "AC-PNAM1 the alias link is named on the chain (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnam_state") == MAA2.STATE_REFUSED,
                   "AC-PNAM1 the shipped reader still refuses this shape "
                   "(%s/%s)" % (got.get("base_pnam_state"),
                                got.get("base_pnam_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnam2():
    """A TWO-STEP attribute path resolves to the module its final link names,
    while a path whose middle link names no module is refused BY NAME."""
    root = world({"hw.py": HW,
                  "consts.py": 'HW = "hw"\n',
                  "inner.py": "INNER = consts\n",
                  "mk.py": ("import consts\nimport inner\n"
                            "BASE = inner.INNER.HW\nREG = BASE\n")})
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        ok = check(got.get("state") == MAA2.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAM2 a two-step attribute path resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check("inner.INNER.HW" in " ".join(got.get("ma_chain") or []),
                   "AC-PNAM2 every step is carried on the chain (%s)"
                   % (got.get("ma_chain"),)) and ok
        ok = check(got.get("base_pnam_state") == MAA2.STATE_REFUSED,
                   "AC-PNAM2 the shipped one-hop reader still refuses "
                   "(%s/%s)" % (got.get("base_pnam_state"),
                                got.get("base_pnam_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW,
                  "consts.py": 'HW = "hw"\n',
                  "wedge.py": 'INNER = "not_a_module"\n',
                  "mk.py": ("import consts\nimport wedge\n"
                            "BASE = wedge.INNER.HW\nREG = BASE\n")})
    try:
        got = entry("import mk\n" + with_attr("mk.REG") + TAIL, root)
        broken = "%s %s" % (got.get("reason") or "",
                            " ".join(got.get("ma_chain") or []))
        ok = check(got.get("state") == MAA2.STATE_REFUSED
                   and "wedge.INNER" in broken,
                   "AC-PNAM2 a middle link naming no module is refused by "
                   "name (%s | %s)" % (got.get("reason"),
                                       got.get("ma_chain"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnam3():
    """A with-as CALL context on a FROM-imported function name resolves and
    names the import hop."""
    root = world({"hw.py": HW,
                  "mk.py": 'def mkmod():\n    return "hw"\n',
                  "probe_conf.py": "from mk import mkmod as REG\n"})
    try:
        got = entry("import probe_conf as mk\n" + with_call("mk.REG") + TAIL,
                    root)
        ok = check(got.get("state") == MAA2.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAM3 a FROM-imported function call resolves "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check("from-import" in str(got.get("ma_hop") or ""),
                   "AC-PNAM3 the import hop is named (%s)"
                   % (got.get("ma_hop"),)) and ok
        ok = check(got.get("base_pnam_state") == MAA2.STATE_REFUSED,
                   "AC-PNAM3 the shipped same-file reader still refuses "
                   "(%s/%s)" % (got.get("base_pnam_state"),
                                got.get("base_pnam_reason"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnam4():
    """A call on a name that is imported but is NOT a function is refused with
    its own word rather than resolved."""
    root = world({"hw.py": HW,
                  "mk.py": 'CONST = "hw"\n',
                  "probe_conf.py": "from mk import CONST as REG\n"})
    try:
        got = entry("import probe_conf as mk\n" + with_call("mk.REG") + TAIL,
                    root)
        ok = check(got.get("state") == MAA2.STATE_REFUSED
                   and got.get("value") is None,
                   "AC-PNAM4 a non-function import is not resolved (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("reason") == "attr-import-not-callable:REG",
                   "AC-PNAM4 it is refused with this face own word (%s)"
                   % (got.get("reason"),)) and ok
        ok = check(got.get("base_pnam_state") == MAA2.STATE_REFUSED,
                   "AC-PNAM4 the shipped reader refuses it too (%s)"
                   % (got.get("base_pnam_state"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnam5():
    """Every answer the sixteen shipped faces already gave is carried
    unchanged on the row."""
    root = world({"hw.py": HW})
    try:
        got = entry("import hw\n"
                    "if a1:\n    KEY = hw.ATTR\nelse:\n    KEY = hw.ATTR\n"
                    + TAIL, root)
        ok = check(got.get("base_pnam_state") == MAA2.STATE_OK
                   and got.get("base_pnam_value") == "b",
                   "AC-PNAM5 the shipped ok answer rides beside this face "
                   "(%s/%s)" % (got.get("base_pnam_state"),
                                got.get("base_pnam_value")))
        ok = check(got.get("state") == MAA2.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNAM5 this face does not rewrite a shipped answer "
                   "(%s/%s)" % (got.get("state"), got.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    try:
        rel = entry("from .cls import K\n"
                    "if a1:\n    KEY = K.ATTR\nelse:\n    KEY = K.ATTR\n"
                    + TAIL, root)
        ok = check(rel.get("reason") == "attr-relative-from-name:K.ATTR",
                   "AC-PNAM5 the shipped relative-name refusal is kept (%s)"
                   % (rel.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW, "reg.py": "REG = 3\n"})
    try:
        flat = entry("import reg\n" + with_attr("reg.REG") + TAIL, root)
        ok = check(flat.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNAM5 the shipped with-as refusal still rides (%s)"
                   % (flat.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": HW,
                  "mk.py": 'class Box:\n    NAME = "hw"\n'
                           '    def open(self):\n        return self.NAME\n',
                  "reg.py": "from mk import Box\nREG = Box().open()\n"})
    try:
        call = entry("import reg\n" + with_attr("reg.REG") + TAIL, root)
        ok = check(call.get("base_pnam_state") == MAA2.STATE_OK
                   and call.get("base_pnam_value") == "b",
                   "AC-PNAM5 the shipped module-value answer is carried "
                   "(%s/%s)" % (call.get("base_pnam_state"),
                                call.get("base_pnam_value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnam6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNAM6 module source is pure ASCII (%dB)"
               % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNAM6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = __import__("re").findall(
        r"^\s*(?:import|from)\s+(socket|urllib|http|requests|asyncio)\b",
        text, __import__("re").M)
    ok = check(not net, "AC-PNAM6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = __import__("re").findall(
        r"^\s*(?:import|from)\s+(time|datetime)\b", text, __import__("re").M)
    ok = check(not clock, "AC-PNAM6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = __import__("re").findall(r"\b(eval|exec)\s*\(", text)
    ok = check(not banned, "AC-PNAM6 no eval/exec (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(MAA2.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope-module-alias-attribute-"
               "alias-scope",
               "AC-PNAM6 the face carries its own label (%s)"
               % (MAA2.LABEL,)) and ok
    type_name = "".join(("import ", "re", "\n"))
    ok = check(type_name in text,
               "AC-PNAM6 the face imports its own stdlib modules") and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNAM6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNAM6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNAM6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pnam1(), ac_pnam2(), ac_pnam3(), ac_pnam4(),
               ac_pnam5(), ac_pnam6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())