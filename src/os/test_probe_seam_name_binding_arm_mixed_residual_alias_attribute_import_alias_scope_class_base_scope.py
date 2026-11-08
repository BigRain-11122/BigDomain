"""AC-PNDCH1..AC-PNDCH6 suite for the class-base / FROM-imported-class /
self-NAME / FROM-import-alias-receiver face (R2573).

Criteria were pinned in state/queue/tech.md:607 at R2571 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_base_scope as CB  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_class_base_scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_class_base_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-class-base-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_class_base_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"


def arms(binding):
    return ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding))


def with_body(receiver, opened):
    return ("with %s.%s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver, opened))


def world(files):
    root = tempfile.mkdtemp(prefix="pndch-")
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
    rows = CB.class_base_report(text, root, src)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return CB.class_base_entry("KEY", text, row["scope"], row["line"],
                              root=root, src_path=src)


def ac_pndch1():
    """A class constant inherited from a base class in the same module."""
    files = {"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                       '    pass\n'}
    text = "import cls\n" + arms("cls.K.ATTR") + TAIL
    root = world(files)
    try:
        got = entry(text, root)
        ok = check(got.get("state") == CB.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCH1 a class constant inherited from a base class "
                   "resolves to b (%s/%s)" % (got.get("state"),
                                              got.get("value")))
        ok = check(got.get("base_cb_reason")
                   == "attr-class-constant:cls.K.ATTR",
                   "AC-PNDCH1 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_cb_reason"),)) and ok
        ok = check(str(got.get("cb_hop") or "").endswith("/class-base"),
                   "AC-PNDCH1 the inherited hop is named (%s)"
                   % (got.get("cb_hop"),)) and ok
        ok = check(got.get("cb_source") == CB.SOURCE_CLASS_BASE,
                   "AC-PNDCH1 this face stamps its own source (%s)"
                   % (got.get("cb_source"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                            '    ATTR = "c"\n'})
    try:
        own = entry(text, root)
        ok = check(own.get("state") == CB.STATE_OK
                   and own.get("value") == "c",
                   "AC-PNDCH1 a subclass own value wins over its base (%s/%s)"
                   % (own.get("state"), own.get("value"))) and ok
        ok = check(str(own.get("cb_hop") or "").endswith("/class"),
                   "AC-PNDCH1 an own value keeps the direct class hop (%s)"
                   % (own.get("cb_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                            '    OTHER = 1\n'})
    try:
        missing = entry("import cls\n" + arms("cls.K.OTHER") + TAIL, root)
        ok = check(missing.get("state") == CB.STATE_REFUSED
                   and missing.get("value") is None,
                   "AC-PNDCH1 an inherited class that does not carry the "
                   "attribute resolves nothing (%s/%s)"
                   % (missing.get("state"), missing.get("value"))) and ok
        ok = check(missing.get("reason") == "attr-class-base-constant:"
                   "cls.K.OTHER",
                   "AC-PNDCH1 the missing base attribute is NAMED (%s)"
                   % (missing.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndch2():
    """An absolute FROM-imported CLASS resolves through its class path."""
    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    text = "from cls import K\n" + arms("K.ATTR") + TAIL
    try:
        got = entry(text, root)
        ok = check(got.get("state") == CB.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCH2 an absolute FROM-imported class resolves to b "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("base_cb_reason") == "attr-base-local:K",
                   "AC-PNDCH2 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_cb_reason"),)) and ok
        ok = check(str(got.get("cb_hop") or "").startswith("from-class"),
                   "AC-PNDCH2 the from-class hop is named (%s)"
                   % (got.get("cb_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"consts.py": 'ATTR = "b"\n'})
    try:
        const = entry("from consts import ATTR\n"
                      + arms("ATTR") + TAIL, root)
        ok = check(const.get("value") is None,
                   "AC-PNDCH2 a FROM-imported CONSTANT is not treated as a "
                   "class (%s)" % (const.get("value"),)) and ok
        ok = check(const.get("state") != CB.STATE_OK,
                   "AC-PNDCH2 a FROM-imported CONSTANT is not resolved (%s)"
                   % (const.get("state"),)) and ok
        ok = check(const.get("base_cb_reason") is not None,
                   "AC-PNDCH2 the shipped reason rides rather than being "
                   "invented (%s)" % (const.get("base_cb_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class K:\n    OTHER = 1\n'})
    try:
        missing = entry(text, root)
        ok = check(missing.get("state") == CB.STATE_REFUSED
                   and missing.get("value") is None,
                   "AC-PNDCH2 a class without the attribute resolves nothing "
                   "(%s/%s)" % (missing.get("state"),
                                missing.get("value"))) and ok
        ok = check(missing.get("reason")
                   == "attr-from-class-constant:K.ATTR",
                   "AC-PNDCH2 the missing class attribute is NAMED (%s)"
                   % (missing.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndch3():
    """A cross-module method returning self.NAME resolves."""
    files = {"hw3.py": 'ATTR = "b"\n',
             "mk.py": 'class Box:\n    NAME = "hw3"\n'
                      '    def open(self):\n        return self.NAME\n'}
    text = "import mk\n" + with_body("mk.Box()", "open()") + TAIL
    root = world(files)
    try:
        got = entry(text, root)
        ok = check(got.get("state") == CB.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCH3 a cross-module method returning self.NAME "
                   "resolves to b (%s/%s)" % (got.get("state"),
                                              got.get("value")))
        ok = check(got.get("base_cb_reason") == "attr-cross-call:m.ATTR",
                   "AC-PNDCH3 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_cb_reason"),)) and ok
        ok = check(str(got.get("cb_hop") or "").startswith("with-as-self-attr"),
                   "AC-PNDCH3 the self-attribute hop is named (%s)"
                   % (got.get("cb_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw3.py": 'ATTR = "b"\n',
                  "mk.py": 'class Box:\n    NAME = 7\n'
                           '    def open(self):\n        return self.NAME\n'})
    try:
        bad = entry(text, root)
        ok = check(bad.get("state") == CB.STATE_REFUSED
                   and bad.get("value") is None,
                   "AC-PNDCH3 a non-string class attribute resolves nothing "
                   "(%s/%s)" % (bad.get("state"), bad.get("value"))) and ok
        ok = check(bad.get("reason") == "attr-cross-call:m.ATTR",
                   "AC-PNDCH3 the refusal keeps the shipped word (%s)"
                   % (bad.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndch4():
    """A receiver bound by a FROM-import alias is found and resolves."""
    files = {"hw3.py": 'ATTR = "b"\n',
             "pkg/mk.py": 'class Box:\n    NAME = "hw3"\n'
                          '    def open(self):\n        return self.NAME\n'}
    text = ("from pkg import mk as m2\n"
            + with_body("m2.Box()", "open()") + TAIL)
    root = world(files)
    try:
        got = entry(text, root)
        ok = check(got.get("state") == CB.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCH4 a receiver bound by a FROM-import alias "
                   "resolves to b (%s/%s)" % (got.get("state"),
                                              got.get("value")))
        ok = check(got.get("base_cb_reason") == "attr-cross-call:m.ATTR",
                   "AC-PNDCH4 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_cb_reason"),)) and ok
        ok = check("with-as-from-alias" in str(got.get("cb_hop") or ""),
                   "AC-PNDCH4 the alias hop is named (%s)"
                   % (got.get("cb_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw3.py": 'ATTR = "b"\n',
                  "pkg/mk.py": 'class Box:\n    NAME = "hw3"\n'
                               '    def open(self):\n        return 1\n'})
    try:
        bad = entry(text, root)
        ok = check(bad.get("state") == CB.STATE_REFUSED
                   and bad.get("value") is None,
                   "AC-PNDCH4 an alias receiver whose method returns nothing "
                   "usable resolves nothing (%s/%s)"
                   % (bad.get("state"), bad.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndch5():
    """Every answer the twelve shipped faces already gave rides unchanged."""
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        got = entry("import helper\n" + arms("helper.ATTR") + TAIL, root)
        ok = check(got.get("base_cb_state") == CB.STATE_OK
                   and got.get("base_cb_value") == "b",
                   "AC-PNDCH5 the shipped ok answer rides beside this face "
                   "(%s/%s)" % (got.get("base_cb_state"),
                                got.get("base_cb_value")))
        ok = check(got.get("state") == CB.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCH5 this face does not rewrite a shipped ok answer "
                   "(%s/%s)" % (got.get("state"), got.get("value"))) and ok
        ok = check(got.get("base_cb_hop") is not None,
                   "AC-PNDCH5 the shipped hop rides beside this face (%s)"
                   % (got.get("base_cb_hop"),)) and ok
        ok = check(got.get("cb_source") == got.get("base_cb_source"),
                   "AC-PNDCH5 a carried answer keeps the shipped source (%s/%s)"
                   % (got.get("cb_source"), got.get("base_cb_source"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    try:
        rel = entry("from .cls import K\n" + arms("K.ATTR") + TAIL, root)
        ok = check(rel.get("state") == CB.STATE_REFUSED,
                   "AC-PNDCH5 the shipped relative-name refusal is kept (%s)"
                   % (rel.get("state"),)) and ok
        ok = check(rel.get("reason") == "attr-relative-from-name:K.ATTR",
                   "AC-PNDCH5 it keeps its own shipped word (%s)"
                   % (rel.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"pkg/helper.py": 'ATTR = "b"\n',
                  "pkg/sub/mod.py": "from .. import helper\n"
                  + arms("helper.ATTR") + TAIL})
    try:
        text = "from .. import helper\n" + arms("helper.ATTR") + TAIL
        anchored = entry(text, root, "pkg/sub/mod.py")
        ok = check(anchored.get("state") == CB.STATE_OK
                   and anchored.get("value") == "b",
                   "AC-PNDCH5 the shipped two-level answer still rides "
                   "(%s/%s)" % (anchored.get("state"),
                                anchored.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndch6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNDCH6 module source is pure ASCII (%dB)"
               % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNDCH6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNDCH6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNDCH6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNDCH6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(CB.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope-class-base-scope",
               "AC-PNDCH6 the face carries its own label (%s)"
               % (CB.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNDCH6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNDCH6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNDCH6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pndch1(), ac_pndch2(), ac_pndch3(), ac_pndch4(),
               ac_pndch5(), ac_pndch6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())