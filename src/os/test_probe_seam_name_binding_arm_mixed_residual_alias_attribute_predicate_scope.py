"""AC-PNDB1..AC-PNDB6 suite for the alias attribute-predicate face (R2561).

Criteria were pinned in state/queue/tech.md:597 at R2559 BEFORE this code
existed.

What this proves: MEASURED at R2559 on the alias attribute-base face own reader,
a walrus-bound attribute alias publishes no reason at all, a subscript base is
published as `attr-not-imported:?.ATTR` with a question mark where the base
should be, a package own `__init__.py` constant reads attr-missing because the
hop asks for `<mod>.py`, and a helper name bound by `with ... as NAME` is not
collected at all. This face follows name edges to the ACTUAL attribute edge,
publishes a subscript or call base as its own text, joins a package index, and
reads a with-as helper binding, while carrying every answer the shipped faces
already gave.

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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_base as PNDA  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_scope as PNDB  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_"
    "scope.py")
SUITE = os.path.join(
    BASE,
    "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "predicate_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-predicate",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_predicate_scope.py"),')

CONTAINER = 'D = {"a": {"b": ("pndb_helper",)}}\n'
TAIL = 'for name in D["a"][KEY]:\n    pass\n'
HELPER = 'ATTR = "b"\n'


def arms(binding):
    return ('if a1:\n    KEY = %s\nelse:\n    KEY = %s\n'
            % (binding, binding)) + TAIL


# AC-PNDB1: a walrus-bound attribute edge inside a function body, where the
# shipped reader refuses `name-unbound:B` because only plain and annotated
# assignments record an attribute edge there.
WALRUS_OK = (CONTAINER + 'import hw\n'
             'def probe():\n'
             '    B = (K := hw.ATTR)\n'
             '    if a1:\n        KEY = B\n    else:\n        KEY = B\n'
             '    ' + TAIL.replace('\n', '\n    ').rstrip() + '\n')
WALRUS_TREE = 'ATTR = 1\n'


def world(files):
    root = tempfile.mkdtemp(prefix="pndb-")
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
    rows = PNDB.predicate_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return PNDB.predicate_entry(name, text, row["scope"], row["line"],
                               root=root)


def ac_pndb1():
    """A walrus-bound attribute edge resolves, and is NAMED when it cannot."""
    root = world({"hw.py": HELPER})
    try:
        got = entry(WALRUS_OK, "KEY", root)
        ok = check(got.get("pred_state") == PNDB.STATE_OK
                   and got.get("pred_value") == "b",
                   "AC-PNDB1 a walrus attribute edge resolves to b (%s/%s)"
                   % (got.get("pred_state"), got.get("pred_value")))
        ok = check(got.get("pred_edge") == "walrus-attr",
                   "AC-PNDB1 the edge is recorded as a walrus (%s)"
                   % (got.get("pred_edge"),)) and ok
        ok = check(got.get("pred_chain") == ["hw.ATTR"],
                   "AC-PNDB1 the chain names the hop (%s)"
                   % (got.get("pred_chain"),)) and ok
        shipped_why = str(got.get("base_position_reason")
                          or got.get("base_attr_reason") or "")
        ok = check(shipped_why.startswith("name-unbound:"),
                   "AC-PNDB1 the shipped answer it replaces refused the name "
                   "(%s)" % (shipped_why,)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hw.py": WALRUS_TREE})
    try:
        bad = entry(WALRUS_OK, "KEY", root)
        ok = check(bad.get("pred_state") == PNDB.STATE_REFUSED
                   and str(bad.get("pred_reason") or "").startswith("attr-"),
                   "AC-PNDB1 an unresolvable walrus edge is NAMED (%s)"
                   % (bad.get("pred_reason"),)) and ok
        ok = check(bad.get("value") is None,
                   "AC-PNDB1 an unresolvable walrus edge resolves nothing "
                   "(%s)" % (bad.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndb2():
    """A subscript or call base keeps its own text and is never a `?`."""
    root = world({"h.py": HELPER})
    try:
        sub = entry(CONTAINER + 'import h\nitems = [h]\n'
                    'B = items[0].ATTR\n' + arms("B"), "KEY", root)
        ok = check(sub.get("pred_reason")
                   == "attr-subscript-base:items[0].ATTR",
                   "AC-PNDB2 a subscript base keeps its text (%s)"
                   % (sub.get("pred_reason"),))
        ok = check("?" not in str(sub.get("pred_reason") or ""),
                   "AC-PNDB2 a subscript base is never reported as ? (%s)"
                   % (sub.get("pred_reason"),)) and ok
        ok = check(sub.get("base_attr_reason")
                   == "attr-not-imported:?.ATTR",
                   "AC-PNDB2 the shipped answer it replaces did carry the ? "
                   "(%s)" % (sub.get("base_attr_reason"),)) and ok
        call = entry(CONTAINER + 'import h\n'
                     'def factory():\n    return h\n'
                     'B = factory().ATTR\n' + arms("B"), "KEY", root)
        ok = check(call.get("pred_reason")
                   == "attr-call-base:factory().ATTR",
                   "AC-PNDB2 a call base keeps its text (%s)"
                   % (call.get("pred_reason"),)) and ok
        ok = check("?" not in str(call.get("pred_reason") or ""),
                   "AC-PNDB2 a call base is never reported as ? (%s)"
                   % (call.get("pred_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndb3():
    """A constant in a package own __init__.py resolves through the path."""
    root = world({"pkg3/__init__.py": HELPER})
    try:
        got = entry(CONTAINER + 'import pkg3\nB = pkg3.ATTR\n' + arms("B"),
                    "KEY", root)
        ok = check(got.get("pred_state") == PNDB.STATE_OK
                   and got.get("pred_value") == "b",
                   "AC-PNDB3 a package index constant resolves to b (%s/%s)"
                   % (got.get("pred_state"), got.get("pred_value")))
        ok = check(got.get("base_attr_reason") == "attr-missing:pkg3.ATTR",
                   "AC-PNDB3 the shipped answer it replaces was attr-missing "
                   "(%s)" % (got.get("base_attr_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"pkg4/mod.py": HELPER})
    try:
        plain = entry(CONTAINER + 'import pkg4.mod\nB = pkg4.mod.ATTR\n'
                      + arms("B"), "KEY", root)
        ok = check(plain.get("state") == PNDB.STATE_OK
                   and plain.get("pred_state") is None,
                   "AC-PNDB3 a <mod>.py hop the shipped face already answers is "
                   "carried unchanged (%s/%s)"
                   % (plain.get("state"), plain.get("pred_state"))) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndb4():
    """A with-as helper binding is read; two values read name-mixed."""
    root = world({"hwa.py": 'ATTR = "b"\nwith open("x") as ATTR:\n    pass\n'})
    try:
        got = entry(CONTAINER + 'import hwa\nB = hwa.ATTR\n' + arms("B"),
                    "KEY", root)
        ok = check(got.get("state") == PNDB.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDB4 a with-as helper binding resolves (%s/%s)"
                   % (got.get("state"), got.get("value")))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hwb.py": 'ATTR = "b"\nwith open("x") as ATTR:\n    pass\n'
                            'ATTR = "c"\n'})
    try:
        mixed = entry(CONTAINER + 'import hwb\nB = hwb.ATTR\n' + arms("B"),
                      "KEY", root)
        ok = check(mixed.get("pred_reason") == "name-mixed:hwb.ATTR",
                   "AC-PNDB4 two values read name-mixed (%s)"
                   % (mixed.get("pred_reason"),)) and ok
        ok = check(mixed.get("value") is None,
                   "AC-PNDB4 a mixed name resolves nothing (%s)"
                   % (mixed.get("value"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root = world({"hwc.py": 'with open("x") as ATTR:\n    pass\n'})
    try:
        lone = entry(CONTAINER + 'import hwc\nB = hwc.ATTR\n' + arms("B"),
                     "KEY", root)
        ok = check(lone.get("pred_reason") in ("attr-with-as:hwc.ATTR",
                                               "attr-non-constant:hwc.ATTR",
                                               "attr-missing:hwc.ATTR"),
                   "AC-PNDB4 a with-as-only name is NAMED rather than silent "
                   "(%s)" % (lone.get("pred_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pndb5():
    """Every answer the shipped faces already gave is carried unchanged."""
    plain = entry(CONTAINER + 'A = "b"\nB = A\n' + arms("B"), "KEY")
    direct = entry(CONTAINER + arms('"b"'), "KEY")
    ok = check(plain.get("state") == PNDB.STATE_OK
               and plain.get("value") == "b"
               and plain.get("pred_source") == PNDA.SOURCE_BASE,
               "AC-PNDB5 a plain name keeps the shipped answer (%s/%s/%s)"
               % (plain.get("state"), plain.get("value"),
                  plain.get("pred_source")))
    ok = check(direct.get("state") == PNDB.STATE_OK
               and direct.get("value") == "b",
               "AC-PNDB5 a direct literal keeps the shipped answer (%s/%s)"
               % (direct.get("state"), direct.get("value"))) and ok
    keys = ("base_position_state", "base_position_reason",
            "base_position_value", "base_position_source",
            "base_position_chain", "attr_state", "attr_reason", "attr_value",
            "attr_chain", "attr_source")
    ok = check(all(key in plain and key in direct for key in keys),
               "AC-PNDB5 every shipped key is still on the row") and ok
    shipped = PNDA.attribute_entry("KEY", CONTAINER + 'A = "b"\nB = A\n'
                                  + arms("B"), "module", 6)
    ok = check(shipped.get("state") == plain.get("state")
               and shipped.get("value") == plain.get("value"),
               "AC-PNDB5 the row agrees with the face it extends "
               "(%s/%s)" % (shipped.get("state"), shipped.get("value"))) and ok
    return ok


def ac_pndb6():
    """Pure ASCII, stdlib only, no clock, no network, own label and suite."""
    module_bytes = read_bytes(MODULE)
    suite_bytes = read_bytes(SUITE)
    ok = check(all(byte < 128 for byte in module_bytes),
               "AC-PNDB6 module source is pure ASCII (%dB)" % len(module_bytes))
    ok = check(all(byte < 128 for byte in suite_bytes),
               "AC-PNDB6 suite source is pure ASCII (%dB)" % len(suite_bytes)) \
        and ok
    text = module_bytes.decode("ascii")
    net = re.findall(r"^\s*(?:import|from)\s+(socket|urllib|http|requests|"
                     r"asyncio)\b", text, re.M)
    ok = check(not net, "AC-PNDB6 zero network imports (%s)"
               % (",".join(net) or "none",)) and ok
    clock = re.findall(r"^\s*(?:import|from)\s+(time|datetime)\b", text, re.M)
    ok = check(not clock, "AC-PNDB6 no clock import (%s)"
               % (",".join(clock) or "none",)) and ok
    banned = re.findall(r"\b(eval|exec|__import__)\s*\(", text)
    ok = check(not banned, "AC-PNDB6 no eval/exec/__import__ (%s)"
               % (",".join(banned) or "none",)) and ok
    ok = check(PNDB.LABEL == "os-probe-seam-name-binding-arm-mixed-residual-"
               "alias-attribute-predicate",
               "AC-PNDB6 the face carries its own label (%s)"
               % (PNDB.LABEL,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8", "replace")
    ok = check(WIRED_LABEL in registry,
               "AC-PNDB6 the label is wired into reconcile_all") and ok
    ok = check(WIRED_SUITE in registry,
               "AC-PNDB6 the suite is wired into reconcile_all") and ok
    return ok


def main():
    results = [ac_pndb1(), ac_pndb2(), ac_pndb3(), ac_pndb4(), ac_pndb5(),
               ac_pndb6()]
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())