"""AC-PNDS1..AC-PNDS6 suite for the alias-position face (R2557).

Criteria were pinned in state/queue/tech.md:593 at R2555 BEFORE this code
existed.

What this proves: MEASURED at R2555 on the shipped alias-chain face own reader,
a WALRUS alias reads `name-unbound:B`, an ATTRIBUTE-valued alias reads
`name-unbound:B`, and a constant declared AFTER the loop still resolves to its
literal (an over-resolution). This face takes a walrus binding as an alias
edge, follows ONE attribute hop on a same-root module constant, and refuses a
binding whose every line is later than the loop line.

Every fixture lives in a string or in a private temporary directory; no shipped
source file is written. Stdlib only, ASCII source, zero network, no clock.
Exit 0 = all green.
"""

import hashlib
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

import probe_seam_name_binding_arm_mixed_residual_alias_position as PNDS  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_chain as PNDR  # noqa
import probe_seam_name_binding_arm_mixed_residual_naming as PNDQ  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE, "probe_seam_name_binding_arm_mixed_residual_alias_position.py")
ALIAS_MODULE = os.path.join(
    BASE, "probe_seam_name_binding_arm_mixed_residual_alias_chain.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'position",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'position.py"),')

CONTAINER = 'D = {"a": {"b": ("pnds_helper",)}}\n'
TAIL = 'for name in D["a"][KEY]:\n    pass\n'

HELPER_TEXT = 'ATTR = "b"\nNOTSTR = 1\n'


def arms(binding):
    return ('if a1:\n    KEY = %s\nelse:\n    KEY = %s\n'
            % (binding, binding)) + TAIL


WALRUS = CONTAINER + 'A = "b"\n(B := A)\n' + arms("B")
WALRUS_LITERAL = CONTAINER + '(B := "b")\n' + arms("B")
ATTRIBUTE = CONTAINER + 'import helpermod\nB = helpermod.ATTR\n' + arms("B")
ATTR_DEEP = CONTAINER + 'import helpermod\nB = helpermod.sub.ATTR\n' \
    + arms("B")
ATTR_MISSING = CONTAINER + 'import helpermod\nB = helpermod.NOPE\n' \
    + arms("B")
ATTR_NOT_STR = CONTAINER + 'import helpermod\nB = helpermod.NOTSTR\n' \
    + arms("B")
ATTR_GHOST = CONTAINER + 'import ghostmod\nB = ghostmod.ATTR\n' + arms("B")
ATTR_NO_IMPORT = CONTAINER + 'B = helpermod.ATTR\n' + arms("B")
AFTER = CONTAINER + arms("C") + 'C = "b"\n'
AFTER_CHAIN = CONTAINER + 'B = A\n' + arms("B") + 'A = "b"\n'
PLAIN = CONTAINER + 'A = "b"\nB = A\n' + arms("B")
DIRECT = CONTAINER + arms('"b"')
WAS = ('with open("x") as WK:\n'
       '    pass\n'
       + CONTAINER
       + arms('"b"'))


def check(ok, label):
    if ok:
        print("PASS %s" % label)
    else:
        print("FAIL %s" % label)
    return ok


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def tail_row(text, root=None):
    rows = PNDS.position_report(text, root)["loops"]
    return rows[-1] if rows else {}


def entry(text, name, root=None):
    row = tail_row(text, root)
    if not row:
        return {}
    return PNDS.position_entry(name, text, row["scope"], row["line"],
                               root=root)


def shipped(text, name):
    row = tail_row(text)
    if not row:
        return {}
    return PNDR.alias_entry(name, text, row["scope"], row["line"])


def residual(text, name):
    row = tail_row(text)
    if not row:
        return {}
    return PNDQ.residual_entry(name, text, row["scope"], row["line"])


def make_world():
    root = tempfile.mkdtemp(prefix="pnds-")
    with open(os.path.join(root, "helpermod.py"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(HELPER_TEXT)
    return root


def ac_pnds1():
    """A walrus alias is an alias edge and resolves to its literal."""
    ok = check(entry(WALRUS, "KEY").get("state") == PNDS.STATE_OK
               and entry(WALRUS, "KEY").get("value") == "b",
               "AC-PNDS1 a walrus alias ((B := A)) resolves to b (%s/%s)"
               % (entry(WALRUS, "KEY").get("state"),
                  entry(WALRUS, "KEY").get("value")))
    ok = check(entry(WALRUS, "KEY").get("position_chain")
               == ["KEY", "B", "A"],
               "AC-PNDS1 the walrus chain names every hop it took (%s)"
               % (entry(WALRUS, "KEY").get("position_chain"),)) and ok
    ok = check(entry(WALRUS_LITERAL, "KEY").get("state") == PNDS.STATE_OK
               and entry(WALRUS_LITERAL, "KEY").get("value") == "b",
               "AC-PNDS1 a walrus str literal ((B := \"b\")) resolves to b") \
        and ok
    base = shipped(WALRUS, "KEY")
    ok = check(base.get("state") == PNDS.STATE_REFUSED
               and base.get("reason") == "name-unbound:B",
               "AC-PNDS1 the SAME fixture still reads %s on the shipped face"
               % (base.get("reason"),)) and ok
    ok = check(entry(WALRUS, "KEY").get("position_source")
               == PNDS.SOURCE_POSITION,
               "AC-PNDS1 the answer says it came from this face") and ok
    return ok


def ac_pnds2():
    """An attribute-valued alias resolves through ONE same-root module hop."""
    root = make_world()
    try:
        got = entry(ATTRIBUTE, "KEY", root)
        base = shipped(ATTRIBUTE, "KEY")
        ok = check(got.get("state") == PNDS.STATE_OK
                   and got.get("value") == "b",
                   "AC-PNDS2 B = helpermod.ATTR resolves to b (%s/%s)"
                   % (got.get("state"), got.get("value")))
        ok = check(got.get("position_chain")
                   == ["KEY", "B", "helpermod.ATTR"],
                   "AC-PNDS2 the attribute hop is published with its module "
                   "(%s)" % (got.get("position_chain"),)) and ok
        ok = check(base.get("state") == PNDS.STATE_REFUSED
                   and base.get("reason") == "name-unbound:B",
                   "AC-PNDS2 the SAME fixture still reads %s on the shipped "
                   "face" % (base.get("reason"),)) and ok
        ghost = entry(ATTR_GHOST, "KEY", root)
        ok = check(ghost.get("state") == PNDS.STATE_REFUSED
                   and ghost.get("reason") == "attr-missing:ghostmod.ATTR",
                   "AC-PNDS2 an imported module with no file is NAMED (%s)"
                   % (ghost.get("reason"),)) and ok
        loose = entry(ATTR_NO_IMPORT, "KEY", root)
        ok = check(loose.get("state") == PNDS.STATE_REFUSED
                   and loose.get("reason")
                   == "attr-not-imported:helpermod.ATTR",
                   "AC-PNDS2 a module the probe never imports is NAMED (%s)"
                   % (loose.get("reason"),)) and ok
        return ok
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_pnds3():
    """A constant bound AFTER the loop is NAMED and never resolved."""
    got = entry(AFTER, "KEY")
    base = shipped(AFTER, "KEY")
    ok = check(got.get("state") == PNDS.STATE_REFUSED
               and got.get("reason") == "not-yet-bound:C",
               "AC-PNDS3 a constant declared after the loop is NAMED (%s)"
               % (got.get("reason"),))
    ok = check(got.get("value") is None,
               "AC-PNDS3 the over-resolution is closed: no value published") \
        and ok
    ok = check(base.get("state") == PNDS.STATE_OK
               and base.get("value") == "b",
               "AC-PNDS3 the SAME fixture still resolves to %s on the "
               "shipped face" % (base.get("value"),)) and ok
    chain = entry(AFTER_CHAIN, "KEY")
    ok = check(chain.get("reason") == "not-yet-bound:A",
               "AC-PNDS3 a chain that ends in a later binding is NAMED at "
               "its end (%s)" % (chain.get("reason"),)) and ok
    row = tail_row(AFTER) or {}
    ok = check(row.get("not_yet_bound", {}).get("KEY") == "not-yet-bound:C",
               "AC-PNDS3 the row publishes the refusal (%s)"
               % (row.get("not_yet_bound"),)) and ok
    return ok


def ac_pnds4():
    """A deeper, broken or non-constant attribute hop is NAMED, not guessed."""
    root = make_world()
    try:
        deep = entry(ATTR_DEEP, "KEY", root)
        miss = entry(ATTR_MISSING, "KEY", root)
        notstr = entry(ATTR_NOT_STR, "KEY", root)
        ok = check(deep.get("state") == PNDS.STATE_REFUSED
                   and deep.get("reason") == "attr-deep:helpermod.sub.ATTR",
                   "AC-PNDS4 a chain deeper than one hop is NAMED (%s)"
                   % (deep.get("reason"),))
        ok = check(miss.get("state") == PNDS.STATE_REFUSED
                   and miss.get("reason") == "attr-missing:helpermod.NOPE",
                   "AC-PNDS4 a missing attribute is NAMED with its hop (%s)"
                   % (miss.get("reason"),)) and ok
        ok = check(notstr.get("state") == PNDS.STATE_REFUSED
                   and notstr.get("reason")
                   == "attr-non-constant:helpermod.NOTSTR",
                   "AC-PNDS4 a non-str attribute is NAMED (%s)"
                   % (notstr.get("reason"),)) and ok
        ok = check(deep.get("value") is None and miss.get("value") is None
                   and notstr.get("value") is None,
                   "AC-PNDS4 nothing is guessed: every refusal publishes no "
                   "value") and ok
        return ok
    finally:
        shutil.rmtree(root, ignore_errors=True)


def ac_pnds5():
    """Every answer the shipped faces already gave is carried unchanged."""
    failures = []
    for label, text in (("direct", DIRECT), ("plain", PLAIN), ("was", WAS)):
        row = tail_row(text) or {}
        for name in ("KEY", "WK"):
            mine = entry(text, name)
            base = shipped(text, name)
            if not base:
                continue
            same = (mine.get("state") == base.get("state")
                    and mine.get("reason") == base.get("reason")
                    and mine.get("value") == base.get("value"))
            if not same:
                failures.append("%s/%s mine=%s/%s base=%s/%s"
                                % (label, name, mine.get("state"),
                                   mine.get("reason"), base.get("state"),
                                   base.get("reason")))
            if mine.get("base_alias_state") != base.get("state") \
                    or mine.get("base_alias_reason") != base.get("reason"):
                failures.append("%s/%s carried fields disagree"
                                % (label, name))
            if mine.get("position_source") != PNDS.SOURCE_BASE:
                failures.append("%s/%s source=%s"
                                % (label, name, mine.get("position_source")))
        same_row = (row.get("base_alias_followed")
                    == (PNDR.alias_report(text)["loops"][-1]["followed"]))
        if not same_row:
            failures.append("%s/row carried followed disagrees" % label)
    ok = check(not failures,
               "AC-PNDS5 every shipped answer is carried unchanged (%s)"
               % (failures[:2] or "no drift",))
    mine = entry(WALRUS, "KEY")
    ok = check(mine.get("base_alias_reason") == "name-unbound:B",
               "AC-PNDS5 the shipped refusal rides beside the new answer "
               "(%s)" % (mine.get("base_alias_reason"),)) and ok
    res = residual(WALRUS, "KEY")
    ok = check(mine.get("base_residual_reason") == res.get("reason")
               and mine.get("base_residual_state") == res.get("state"),
               "AC-PNDS5 the residual answer is carried too (%s/%s)"
               % (mine.get("base_residual_state"),
                  mine.get("base_residual_reason"))) and ok
    return ok


def ac_pnds6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNDS6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNDS6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNDS6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNDS6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNDS6 the face and its suite are wired into the registry") \
        and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNDS6 no duplicate registry row") and ok
    ok = check(PNDS.LABEL
               == "os-probe-seam-name-binding-arm-mixed-residual-"
                  "alias-position",
               "AC-PNDS6 the reconcile label is the face own (%s)"
               % (PNDS.LABEL,)) and ok
    ok = check(PNDS.SEAMS_POSITION_COVERED == "SEAMS-ALIAS-POSITION-COVERED"
               and PNDS.SEAMS_POSITION_STALE == "SEAMS-ALIAS-POSITION-STALE",
               "AC-PNDS6 the reading has its own verdict words") and ok
    ok = check(os.path.isfile(ALIAS_MODULE),
               "AC-PNDS6 the shipped alias face it extends is on disk") and ok
    return ok


def main():
    print("PROBE SEAM NAME BINDING ARM MIXED RESIDUAL ALIAS POSITION SUITE "
          "(AC-PNDS1..AC-PNDS6)")
    results = [ac_pnds1(), ac_pnds2(), ac_pnds3(), ac_pnds4(), ac_pnds5(),
               ac_pnds6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())