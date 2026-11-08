"""AC-PNDCI1..AC-PNDCI6 suite for the cross-module base / module-value
receiver / class-constant-alias face (R2575).

Criteria were pinned in state/queue/tech.md:609 at R2573 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_source_scope as CS  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_class_source_scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_class_source_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-class-source-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_class_source_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"


def arms(binding):
    return ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding))


def with_body(receiver, opened):
    return ("with %s.%s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver, opened))


def with_attr(receiver):
    return ("with %s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver,))


def world(files):
    root = tempfile.mkdtemp(prefix="pndci-")
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
    rows = CS.class_source_report(text, root, src)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return CS.class_source_entry("KEY", text, row["scope"], row["line"],
                                 root=root, src_path=src)


def ac_pndci1():
    """A base class from another module resolves through the subclass path."""
    files = {"base.py": 'class Base:\n    ATTR = "b"\n',
             "cls.py": "from base import Base\n\nclass K(Base):\n    pass\n"}
    text = "import cls\n" + arms("cls.K.ATTR") + TAIL
    root = world(files)
    try:
        got = entry(text, root)
        ok = check(got.get("state") == CS.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCI1 a base class from another module resolves to b "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("base_cs_reason")
                   == "attr-class-base-constant:cls.K.ATTR",
                   "AC-PNDCI1 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_cs_reason"),)) and ok
        ok = check(str(got.get("cs_hop") or "").endswith("/class-base"),
                   "AC-PNDCI1 the cross base hop is named (%s)"
                   % (got.get("cs_hop"),)) and ok
        ok = check(got.get("cs_source") == CS.SOURCE_CLASS_SOURCE,
                   "AC-PNDCI1 this face stamps its own source (%s)"
                   % (got.get("cs_source"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"base.py": 'class Base:\n    ATTR = "b"\n',
             "mid.py": "from base import Base\n\nclass Mid(Base):\n    pass\n",
             "cls.py": "from mid import Mid\n\nclass K(Mid):\n    pass\n"}
    root = world(files)
    try:
        two = entry(text, root)
        ok = check(two.get("state") == CS.STATE_OK
                   and two.get("value") == "b",
                   "AC-PNDCI1 a two-hop cross base resolves to b (%s/%s)"
                   % (two.get("state"), two.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"base.py": 'class Base:\n    OTHER = 1\n',
             "cls.py": "from base import Base\n\nclass K(Base):\n    pass\n"}
    root = world(files)
    try:
        missing = entry(text, root)
        ok = check(missing.get("state") == CS.STATE_REFUSED
                   and missing.get("value") is None,
                   "AC-PNDCI1 a cross base without the attribute resolves "
                   "nothing (%s/%s)" % (missing.get("state"),
                                        missing.get("value"))) and ok
        ok = check(missing.get("reason")
                   == "attr-class-source-constant:cls.K.ATTR",
                   "AC-PNDCI1 the missing cross attribute is NAMED (%s)"
                   % (missing.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"a.py": "from b import B\n\nclass A(B):\n    ATTR = \"a\"\n",
             "b.py": "from a import A\n\nclass B(A):\n    ATTR = \"b\"\n"}
    root = world(files)
    try:
        cyc = entry("import a\n" + arms("a.A.ATTR") + TAIL, root)
        ok = check(cyc.get("state") == CS.STATE_OK
                   and cyc.get("value") == "a",
                   "AC-PNDCI1 a base cycle is bounded and the own value wins "
                   "(%s/%s)" % (cyc.get("state"), cyc.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndci2():
    """A method returning an inherited class attribute through self
    resolves."""
    files = {"hw3.py": 'ATTR = "b"\n',
             "mk.py": 'class Box:\n    NAME = "hw3"\n'
                      '    def open(self):\n        return self.NAME\n'}
    text = "import mk\n" + with_body("mk.Box()", "open()") + TAIL
    root = world(files)
    try:
        got = entry(text, root)
        ok = check(got.get("state") == CS.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCI2 a self.NAME method resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_cs_state") == CS.STATE_OK,
                   "AC-PNDCI2 the shipped answer for the same-module base "
                   "rides (%s)" % (got.get("base_cs_state"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"base.py": 'class Base:\n    NAME = "hw3"\n',
             "hw3.py": 'ATTR = "b"\n',
             "mk.py": 'from base import Base\n\nclass Box(Base):\n'
                      '    def open(self):\n        return self.NAME\n'}
    root = world(files)
    try:
        cross = entry(text, root)
        ok = check(cross.get("state") == CS.STATE_OK
                   and cross.get("value") == "b",
                   "AC-PNDCI2 a self.NAME method through a cross-module base "
                   "resolves to b (%s/%s)" % (cross.get("state"),
                                              cross.get("value"))) and ok
        ok = check("self-attr" in str(cross.get("cs_hop") or ""),
                   "AC-PNDCI2 the cross self hop is named (%s)"
                   % (cross.get("cs_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"base.py": 'class Base:\n    NAME = 7\n',
             "hw3.py": 'ATTR = "b"\n',
             "mk.py": 'from base import Base\n\nclass Box(Base):\n'
                      '    def open(self):\n        return self.NAME\n'}
    root = world(files)
    try:
        bad = entry(text, root)
        ok = check(bad.get("state") != CS.STATE_OK
                   and bad.get("value") is None,
                   "AC-PNDCI2 a non-string inherited attribute resolves "
                   "nothing (%s/%s)" % (bad.get("state"),
                                        bad.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndci3():
    """A module-level value bound by a call returning a class attribute
    resolves as a with-as receiver."""
    files = {"hw3.py": 'ATTR = "b"\n',
             "mk.py": 'class Box:\n    NAME = "hw3"\n'
                      '    def open(self):\n        return self.NAME\n',
             "reg.py": 'from mk import Box\nREG = Box().open()\n'}
    text = "import reg\n" + with_attr("reg.REG") + TAIL
    root = world(files)
    try:
        got = entry(text, root)
        ok = check(got.get("state") == CS.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCI3 a module value bound by a call resolves to b "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("base_cs_reason") == "attr-with-as:m.ATTR",
                   "AC-PNDCI3 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_cs_reason"),)) and ok
        ok = check("with-as-module-value" in str(got.get("cs_hop") or ""),
                   "AC-PNDCI3 the module-value hop is named (%s)"
                   % (got.get("cs_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"mk.py": 'class Box:\n    NAME = 7\n'
                      '    def open(self):\n        return self.NAME\n',
             "reg.py": 'from mk import Box\nREG = Box().open()\n'}
    root = world(files)
    try:
        bad = entry(text, root)
        ok = check(bad.get("state") == CS.STATE_REFUSED
                   and bad.get("value") is None,
                   "AC-PNDCI3 a call returning nothing usable resolves "
                   "nothing (%s/%s)" % (bad.get("state"),
                                        bad.get("value"))) and ok
        ok = check(bad.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNDCI3 the refusal keeps the shipped word (%s)"
                   % (bad.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"mk.py": 'class Box:\n    NAME = "hw3"\n'
                      '    def open(self):\n        return self.NAME\n',
             "reg.py": 'from mk import Box\nREG = 3\n'}
    root = world(files)
    try:
        flat = entry(text, root)
        ok = check(flat.get("state") == CS.STATE_REFUSED
                   and flat.get("value") is None,
                   "AC-PNDCI3 a module value that is not a call resolves "
                   "nothing (%s/%s)" % (flat.get("state"),
                                        flat.get("value"))) and ok
        ok = check(flat.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNDCI3 the flat value keeps the shipped word (%s)"
                   % (flat.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndci4():
    """A class-constant alias resolves to the same literal to a fixpoint."""
    files = {"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                       '    OTHER = ATTR\n'}
    root = world(files)
    try:
        got = entry("import cls\n" + arms("cls.K.OTHER") + TAIL, root)
        ok = check(got.get("state") == CS.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCI4 a class alias resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_cs_reason")
                   == "attr-class-base-constant:cls.K.OTHER",
                   "AC-PNDCI4 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_cs_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"cls.py": 'class K:\n    FIRST = "b"\n    SECOND = FIRST\n'
                       '    THIRD = SECOND\n'}
    root = world(files)
    try:
        chain = entry("import cls\n" + arms("cls.K.THIRD") + TAIL, root)
        ok = check(chain.get("state") == CS.STATE_OK
                   and chain.get("value") == "b",
                   "AC-PNDCI4 a two-step alias chain resolves to b (%s/%s)"
                   % (chain.get("state"), chain.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"cls.py": 'class K:\n    A = B\n    B = A\n'}
    root = world(files)
    try:
        loop = entry("import cls\n" + arms("cls.K.A") + TAIL, root)
        ok = check(loop.get("state") == CS.STATE_REFUSED
                   and loop.get("value") is None,
                   "AC-PNDCI4 an alias cycle resolves nothing and does not "
                   "hang (%s/%s)" % (loop.get("state"),
                                     loop.get("value"))) and ok
        ok = check(loop.get("reason")
                   == "attr-class-source-constant:cls.K.A",
                   "AC-PNDCI4 the cyclic alias is NAMED (%s)"
                   % (loop.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    files = {"cls.py": 'class K:\n    OTHER = MISSING\n'}
    root = world(files)
    try:
        dangling = entry("import cls\n" + arms("cls.K.OTHER") + TAIL, root)
        ok = check(dangling.get("state") == CS.STATE_REFUSED
                   and dangling.get("value") is None,
                   "AC-PNDCI4 a dangling alias resolves nothing (%s/%s)"
                   % (dangling.get("state"),
                      dangling.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndci5():
    """Every answer the thirteen shipped faces already gave rides unchanged."""
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        got = entry("import helper\n" + arms("helper.ATTR") + TAIL, root)
        ok = check(got.get("base_cs_state") == CS.STATE_OK
                   and got.get("base_cs_value") == "b",
                   "AC-PNDCI5 the shipped ok answer rides beside this face "
                   "(%s/%s)" % (got.get("base_cs_state"),
                                got.get("base_cs_value")))
        ok = check(got.get("state") == CS.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCI5 this face does not rewrite a shipped answer "
                   "(%s/%s)" % (got.get("state"), got.get("value"))) and ok
        ok = check(got.get("cs_source") == got.get("base_cs_source"),
                   "AC-PNDCI5 a carried answer keeps the shipped source "
                   "(%s/%s)" % (got.get("cs_source"),
                                got.get("base_cs_source"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    try:
        rel = entry("from .cls import K\n" + arms("K.ATTR") + TAIL, root)
        ok = check(rel.get("state") == CS.STATE_REFUSED,
                   "AC-PNDCI5 the shipped relative-name refusal is kept (%s)"
                   % (rel.get("state"),)) and ok
        ok = check(rel.get("reason") == "attr-relative-from-name:K.ATTR",
                   "AC-PNDCI5 it keeps its own shipped word (%s)"
                   % (rel.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"mk.py": 'class Box:\n    NAME = "hw3"\n'
                           '    def open(self):\n        return self.NAME\n',
                  "reg.py": 'from mk import Box\nREG = 3\n'})
    try:
        flat = entry("import reg\n" + with_attr("reg.REG") + TAIL, root)
        ok = check(flat.get("reason") == "attr-with-as:m.ATTR",
                   "AC-PNDCI5 the shipped with-as refusal still rides (%s)"
                   % (flat.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"pkg/helper.py": 'ATTR = "b"\n',
                  "pkg/sub/mod.py": "from .. import helper\n"
                  + arms("helper.ATTR") + TAIL})
    try:
        text = "from .. import helper\n" + arms("helper.ATTR") + TAIL
        anchored = entry(text, root, "pkg/sub/mod.py")
        ok = check(anchored.get("state") == CS.STATE_OK
                   and anchored.get("value") == "b",
                   "AC-PNDCI5 the shipped two-level answer still rides "
                   "(%s/%s)" % (anchored.get("state"),
                                anchored.get("value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndci6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNDCI6 module source is pure ASCII (%dB)"
               % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNDCI6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNDCI6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNDCI6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNDCI6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(CS.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope-class-source-scope",
               "AC-PNDCI6 the face carries its own label (%s)"
               % (CS.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNDCI6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNDCI6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNDCI6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pndci1(), ac_pndci2(), ac_pndci3(), ac_pndci4(),
               ac_pndci5(), ac_pndci6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())