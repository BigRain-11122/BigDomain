"""AC-PNDA1..AC-PNDA6 suite for the alias attribute-base face (R2559).

Criteria were pinned in state/queue/tech.md:595 at R2557 BEFORE this code
existed.

What this proves: MEASURED at R2557 on the alias-position face own reader, an
attribute whose BASE is a function parameter or a local reads
`attr-not-imported`, a package-relative module (pkg.mod.ATTR) is never found
because the hop joins `<mod>.py` on the root, and a helper constant declared by
a walrus or inside a function body reads `attr-missing` / `attr-non-constant`.
This face names the base separately, resolves the FULL dotted path, and reads a
walrus or function-level helper constant, while carrying every answer the
shipped faces already gave.

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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_base as PNDA  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_position as PNDS  # noqa

EXPECTED_CRITERIA = 6
MODULE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_base.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = ('"os-probe-seam-name-binding-arm-mixed-residual-alias-'
               'attribute-base",')
WIRED_SUITE = ('"test_probe_seam_name_binding_arm_mixed_residual_alias_'
               'attribute_base.py"),')

CONTAINER = 'D = {"a": {"b": ("pnda_helper",)}}\n'
TAIL = 'for name in D["a"][KEY]:\n    pass\n'

HELPER_TEXT = 'ATTR = "b"\nNOTSTR = 1\n'
HELPER_EXTENDED = 'ATTR = "b"\n(WAL := "w")\n(DUP := "x")\n(DUP := "y")\n' \
    'def holder():\n    FNC = "c"\n'


def arms(binding):
    return ('if a1:\n    KEY = %s\nelse:\n    KEY = %s\n'
            % (binding, binding)) + TAIL


# AC-PNDA1: a base that is a parameter or a local of the tree.
LOCAL_PARAM = ('def probe(node):\n'
               '    B = node.value\n'
               + '    ' + CONTAINER.replace('\n', '\n    ').rstrip()
               + '\n'
               + '\n'.join('    ' + line for line in arms("B").splitlines())
               + '\n')
LOCAL_NAME = CONTAINER + 'node = object()\nB = node.value\n' + arms("B")

# AC-PNDA2: a genuinely absent module keeps the shipped word.
GHOST = CONTAINER + 'B = ghostmod.ATTR\n' + arms("B")

# AC-PNDA3: a package-relative attribute reached through the FULL dotted path.
DOTTED = CONTAINER + 'import pkg.mod\nB = pkg.mod.ATTR\n' + arms("B")

# AC-PNDA4: a walrus constant and a function-level constant in the helper.
WALRUS_CONST = CONTAINER + 'import helpere\nB = helpere.WAL\n' + arms("B")
FUNC_CONST = CONTAINER + 'import helpere\nB = helpere.FNC\n' + arms("B")
MIXED_CONST = CONTAINER + 'import helpere\nB = helpere.DUP\n' + arms("B")

# AC-PNDA5: shapes the shipped position face already answers.
PLAIN = CONTAINER + 'A = "b"\nB = A\n' + arms("B")
DIRECT = CONTAINER + arms('"b"')


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
    rows = PNDA.attribute_report(text, root)["loops"]
    return rows[-1] if rows else {}


def entry(text, name, root=None):
    row = tail_row(text, root)
    if not row:
        return {}
    return PNDA.attribute_entry(name, text, row["scope"], row["line"],
                                root=root)


def position_row(text, root=None):
    rows = PNDS.position_report(text, root)["loops"]
    return rows[-1] if rows else {}


def make_world(extended=False):
    root = tempfile.mkdtemp(prefix="pnda-")
    with open(os.path.join(root, "helpermod.py"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(HELPER_TEXT)
    with open(os.path.join(root, "helpere.py"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(HELPER_EXTENDED if extended else HELPER_TEXT)
    package = os.path.join(root, "pkg")
    os.makedirs(package)
    with open(os.path.join(package, "mod.py"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(HELPER_TEXT)
    return root


def ac_pnda1():
    """A parameter- or local-rooted attribute names its BASE, not a module."""
    got = entry(LOCAL_PARAM, "KEY")
    ok = check(got.get("attr_reason") == "attr-base-local:node",
               "AC-PNDA1 a parameter base reads attr-base-local:node (%s)"
               % (got.get("attr_reason"),))
    ok = check(got.get("state") == PNDA.STATE_REFUSED
               and got.get("value") is None,
               "AC-PNDA1 a parameter base resolves nothing (%s/%s)"
               % (got.get("state"), got.get("value"))) and ok
    shipped = entry(LOCAL_PARAM, "KEY").get("base_position_reason") or ""
    ok = check(shipped.startswith("attr-not-imported:"),
               "AC-PNDA1 the shipped answer it replaces was "
               "attr-not-imported (%s)" % (shipped,)) and ok
    got_local = entry(LOCAL_NAME, "KEY")
    ok = check(got_local.get("attr_reason") == "attr-base-local:node",
               "AC-PNDA1 a local base reads attr-base-local:node (%s)"
               % (got_local.get("attr_reason"),)) and ok
    return ok


def ac_pnda2():
    """A module that is genuinely not imported keeps attr-not-imported."""
    got = entry(GHOST, "KEY")
    ok = check(got.get("attr_reason") == "attr-not-imported:ghostmod.ATTR",
               "AC-PNDA2 an absent module keeps attr-not-imported with its "
               "text (%s)" % (got.get("attr_reason"),))
    ok = check(got.get("base_position_reason")
               == got.get("attr_reason"),
               "AC-PNDA2 the shipped word is unchanged for that shape "
               "(%s/%s)" % (got.get("base_position_reason"),
                            got.get("attr_reason"))) and ok
    root = make_world()
    try:
        ok = check(entry(GHOST, "KEY", root).get("attr_reason")
                   == "attr-not-imported:ghostmod.ATTR",
                   "AC-PNDA2 a same-root world with other modules still "
                   "keeps the word") and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnda3():
    """pkg.mod.ATTR resolves through the dotted import path."""
    root = make_world()
    try:
        got = entry(DOTTED, "KEY", root)
        ok = check(got.get("attr_state") == PNDA.STATE_OK
                   and got.get("attr_value") == "b",
                   "AC-PNDA3 a dotted module path resolves to b (%s/%s)"
                   % (got.get("attr_state"), got.get("attr_value")))
        ok = check(got.get("attr_chain") == ["pkg.mod.ATTR"],
                   "AC-PNDA3 the chain names the dotted hop (%s)"
                   % (got.get("attr_chain"),)) and ok
        ok = check((got.get("base_position_reason") or "")
                   .startswith("attr-deep:"),
                   "AC-PNDA3 the shipped answer it replaces was attr-deep "
                   "(%s)" % (got.get("base_position_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    root2 = make_world()
    shutil.rmtree(root2, ignore_errors=True)
    ok = check(entry(DOTTED, "KEY", root2).get("attr_state")
               != PNDA.STATE_OK,
               "AC-PNDA3 a dotted path with no file on disk does not resolve")
    return ok


def ac_pnda4():
    """A walrus or function-level helper constant resolves; two mix."""
    root = make_world(extended=True)
    try:
        walrus = entry(WALRUS_CONST, "KEY", root)
        ok = check(walrus.get("attr_state") == PNDA.STATE_OK
                   and walrus.get("attr_value") == "w",
                   "AC-PNDA4 a walrus helper constant resolves to w (%s/%s/%s)"
                   % (walrus.get("attr_state"), walrus.get("attr_value"),
                      walrus.get("base_position_reason")))
        func = entry(FUNC_CONST, "KEY", root)
        ok = check(func.get("attr_state") == PNDA.STATE_OK
                   and func.get("attr_value") == "c",
                   "AC-PNDA4 a function-level helper constant resolves to c "
                   "(%s/%s)" % (func.get("attr_state"),
                                func.get("attr_value"))) and ok
        mixed = entry(MIXED_CONST, "KEY", root)
        ok = check(mixed.get("attr_reason") == "name-mixed:helpere.DUP",
                   "AC-PNDA4 two helper values read name-mixed (%s)"
                   % (mixed.get("attr_reason"),)) and ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ok


def ac_pnda5():
    """Every answer the shipped faces already gave is carried unchanged."""
    ok = True
    for text, label in ((PLAIN, "a plain alias chain"),
                        (DIRECT, "a direct literal"),
                        (GHOST, "a refused hop")):
        shipped = position_row(text)
        carried = tail_row(text)
        ok = check(all(shipped.get(key) == carried.get(key)
                       for key in ("line", "kind", "scope", "followed",
                                   "refused", "chains",
                                   "resolved_by_position",
                                   "not_yet_bound", "attributes")),
                   "AC-PNDA5 the %s row carries every shipped key unchanged"
                   % label) and ok
        ok = check(carried.get("base_alias_followed")
                   == shipped.get("base_alias_followed")
                   and carried.get("base_alias_refused")
                   == shipped.get("base_alias_refused"),
                   "AC-PNDA5 the %s row carries the shipped alias answer "
                   "unchanged" % label) and ok
    ok = check(entry(PLAIN, "KEY").get("state") == PNDA.STATE_OK
               and entry(PLAIN, "KEY").get("value") == "b"
               and entry(PLAIN, "KEY").get("attr_source") == PNDA.SOURCE_BASE,
               "AC-PNDA5 an already-resolved name keeps the shipped answer "
               "and its source") and ok
    return ok


def ac_pnda6():
    """Hygiene, its own reconcile label and its own registered suite."""
    raw = read_bytes(MODULE)
    text = raw.decode("utf-8")
    ok = check(all(byte < 128 for byte in raw),
               "AC-PNDA6 the module is pure ASCII")
    ok = check(re.search(r"^\s*import\s+time\b|^\s*from\s+time\s+import|"
                         r"datetime|perf_counter|\.now\(", text,
                         re.MULTILINE) is None,
               "AC-PNDA6 the module reads no clock") and ok
    ok = check(re.search(r"socket|urllib|http\.client|requests\.", text)
               is None,
               "AC-PNDA6 the module opens no network") and ok
    imports = set(re.findall(r"^\s*import\s+([A-Za-z_][\w.]*)", text,
                             re.MULTILINE))
    stdlib = {"argparse", "ast", "hashlib", "json", "os", "sys"}
    outside = sorted(name for name in imports
                     if name not in stdlib
                     and not name.startswith("probe_seam_"))
    ok = check(not outside,
               "AC-PNDA6 the module imports the stdlib and its shipped "
               "readers only (outside=%s)" % (outside,)) and ok
    ok = check(imports - stdlib
               <= {"probe_seam_name_binding_arm_mixed_residual_alias_"
                   "position"},
               "AC-PNDA6 the one project import is the shipped reader it "
               "extends (%s)" % (sorted(imports - stdlib),)) and ok
    registry = read_text(REGISTRY)
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-PNDA6 the registry carries the row exactly once (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-PNDA6 the registry wires the suite exactly once (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    suite = os.path.join(
        BASE, "test_probe_seam_name_binding_arm_mixed_residual_alias_"
              "attribute_base.py")
    ok = check(os.path.isfile(suite),
               "AC-PNDA6 the suite file is on disk") and ok
    return ok


def main():
    print("LABEL %s" % PNDA.LABEL)
    results = [ac_pnda1(), ac_pnda2(), ac_pnda3(), ac_pnda4(), ac_pnda5(),
               ac_pnda6()]
    total = sum(1 for item in results if item)
    if total == len(results):
        print("SUITE PASS %d/%d" % (total, EXPECTED_CRITERIA))
        return 0
    print("SUITE FAIL %d/%d" % (total, EXPECTED_CRITERIA))
    return 1


if __name__ == "__main__":
    sys.exit(main())