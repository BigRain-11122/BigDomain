"""AC-PNDCG1..AC-PNDCG6 suite for the two-level relative / cross-module call /
class-body / relative-name face (R2571).

Criteria were pinned in state/queue/tech.md:605 at R2569 BEFORE this code
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_two_level_scope as TL  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_"
    "scope_two_level_scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_two_level_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-import-alias-scope-two-level-scope",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_import_alias_scope_two_level_scope.py"),')

TAIL = "for name in hw.NAMES:\n    pass\n"


def arms(binding):
    return ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding))


def world(files):
    root = tempfile.mkdtemp(prefix="pndcg-")
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
    rows = TL.two_level_report(text, root, src)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return TL.two_level_entry("KEY", text, row["scope"], row["line"],
                              root=root, src_path=src)


def ac_pndcg1():
    """A two-level relative import resolves against the parent package."""
    body = "from .. import helper\n" + arms("helper.ATTR") + TAIL
    root = world({"pkg/helper.py": 'ATTR = "b"\n',
                  "pkg/sub/mod.py": body})
    try:
        got = entry(body, root, "pkg/sub/mod.py")
        ok = check(got.get("state") == TL.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCG1 a two-level relative module import resolves to b "
                   "(%s/%s)" % (got.get("state"), got.get("value")))
        ok = check(got.get("base_tl_reason") == "attr-base-local:helper",
                   "AC-PNDCG1 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_tl_reason"),)) and ok
        ok = check(str(got.get("tl_hop") or "").startswith("from-relative"),
                   "AC-PNDCG1 the two-level hop is named (%s)"
                   % (got.get("tl_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        flat = entry(body, root)
        ok = check(flat.get("state") == TL.STATE_REFUSED,
                   "AC-PNDCG1 without an anchor the two-level import stays "
                   "refused (%s)" % (flat.get("state"),)) and ok
        ok = check(flat.get("reason") == "attr-base-local:helper",
                   "AC-PNDCG1 without an anchor the shipped word is kept (%s)"
                   % (flat.get("reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcg2():
    """A with-as call on a method defined in ANOTHER module resolves."""
    files = {"hw3.py": 'ATTR = "b"\n',
             "mk.py": 'class Box:\n    def open(self):\n'
                      '        n = "hw3"\n        return n\n'}
    text = ("import mk\nwith mk.Box().open() as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" + TAIL)
    root = world(files)
    try:
        got = entry(text, root)
        ok = check(got.get("state") == TL.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCG2 a cross-module method returning a module "
                   "resolves to b (%s/%s)" % (got.get("state"),
                                              got.get("value")))
        ok = check(got.get("base_tl_reason") == "attr-call-target:m.ATTR",
                   "AC-PNDCG2 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_tl_reason"),)) and ok
        ok = check(str(got.get("tl_hop") or "").startswith(
            "with-as-cross-call"),
                   "AC-PNDCG2 the cross-call hop is named (%s)"
                   % (got.get("tl_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw3.py": 'ATTR = "b"\n',
                  "mk.py": 'class Box:\n    def open(self):\n'
                           '        return 1\n'})
    try:
        bad = entry(text, root)
        ok = check(bad.get("state") == TL.STATE_REFUSED,
                   "AC-PNDCG2 a cross-module method returning something else "
                   "is refused (%s)" % (bad.get("state"),)) and ok
        ok = check(bad.get("reason") == "attr-cross-call:m.ATTR",
                   "AC-PNDCG2 a non-module cross-call is NAMED (%s)"
                   % (bad.get("reason"),)) and ok
        ok = check(bad.get("value") is None,
                   "AC-PNDCG2 a refusal resolves nothing (%s)"
                   % (bad.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcg3():
    """A class-body constant resolves through its class path."""
    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    try:
        got = entry("import cls\n" + arms("cls.K.ATTR") + TAIL, root)
        ok = check(got.get("state") == TL.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCG3 a class-body constant resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("base_tl_reason") == "attr-from-import:cls.K.ATTR",
                   "AC-PNDCG3 the shipped answer it replaces refused it (%s)"
                   % (got.get("base_tl_reason"),)) and ok
        ok = check(str(got.get("tl_hop") or "").endswith("/class"),
                   "AC-PNDCG3 the class hop is named (%s)"
                   % (got.get("tl_hop"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                            '    pass\n'})
    try:
        inherited = entry("import cls\n" + arms("cls.K.ATTR") + TAIL, root)
        ok = check(inherited.get("reason") == "attr-class-constant:cls.K.ATTR",
                   "AC-PNDCG3 an inherited class constant is NAMED rather "
                   "than guessed (%s)" % (inherited.get("reason"),)) and ok
        ok = check(inherited.get("value") is None,
                   "AC-PNDCG3 the inherited refusal resolves nothing (%s)"
                   % (inherited.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcg4():
    """A relative FROM-imported NAME is refused with its own word."""
    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    try:
        got = entry("from .cls import K\n" + arms("K.ATTR") + TAIL, root)
        ok = check(got.get("state") == TL.STATE_REFUSED,
                   "AC-PNDCG4 a relative FROM-imported NAME is refused (%s)"
                   % (got.get("state"),))
        ok = check(got.get("reason") == "attr-relative-from-name:K.ATTR",
                   "AC-PNDCG4 it carries its own word (%s)"
                   % (got.get("reason"),)) and ok
        ok = check(got.get("reason") != "attr-base-local:K.ATTR"
                   and got.get("reason") != "attr-base-local:K",
                   "AC-PNDCG4 it is never published as a local (%s)"
                   % (got.get("reason"),)) and ok
        ok = check(got.get("base_tl_reason") == "attr-base-local:K",
                   "AC-PNDCG4 the shipped local word still rides beside it "
                   "(%s)" % (got.get("base_tl_reason"),)) and ok
        ok = check(got.get("value") is None,
                   "AC-PNDCG4 the refusal resolves nothing (%s)"
                   % (got.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcg5():
    """Every shipped answer rides unchanged beside this face own."""
    root = world({"helper.py": 'ATTR = "b"\n'})
    try:
        got = entry("import helper\n" + arms("helper.ATTR") + TAIL, root)
        ok = check(got.get("base_tl_state") == TL.STATE_OK
                   and got.get("base_tl_value") == "b",
                   "AC-PNDCG5 the shipped ok answer rides beside this face "
                   "(%s/%s)" % (got.get("base_tl_state"),
                                got.get("base_tl_value")))
        ok = check(got.get("state") == TL.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDCG5 this face does not rewrite the shipped ok "
                   "answer (%s/%s)" % (got.get("state"),
                                       got.get("value"))) and ok
        ok = check(got.get("base_tl_hop") is not None,
                   "AC-PNDCG5 the shipped hop rides beside this face (%s)"
                   % (got.get("base_tl_hop"),)) and ok
        ok = check(got.get("tl_source") == TL.SOURCE_TWO_LEVEL,
                   "AC-PNDCG5 this face stamps its own source (%s)"
                   % (got.get("tl_source"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"pkg/helper.py": 'ATTR = "b"\n'})
    try:
        alias = entry("from pkg import helper as h\n" + arms("h.ATTR") + TAIL, root)
        ok = check(alias.get("base_tl_state") == TL.STATE_OK
                   and alias.get("base_tl_value") == "b",
                   "AC-PNDCG5 the shipped from-import alias answer still "
                   "rides (%s/%s)" % (alias.get("base_tl_state"),
                                      alias.get("base_tl_value"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndcg6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNDCG6 module source is pure ASCII (%dB)"
               % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNDCG6 suite source is pure ASCII (%dB)"
               % len(suite_bytes)) and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNDCG6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNDCG6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNDCG6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(TL.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-import-alias-scope-two-level-scope",
               "AC-PNDCG6 the face carries its own label (%s)"
               % (TL.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNDCG6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNDCG6 the suite is wired into reconcile_all") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-PNDCG6 the suite declares its six criteria (%d)"
               % (EXPECTED_CRITERIA,)) and ok
    return ok


def main():
    results = [ac_pndcg1(), ac_pndcg2(), ac_pndcg3(), ac_pndcg4(),
               ac_pndcg5(), ac_pndcg6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())