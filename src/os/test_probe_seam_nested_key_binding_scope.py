"""AC-PNKB1..AC-PNKB6 suite for the seam nested-key-binding scope face (R2537).

Criteria were pinned in state/queue/tech.md:573 at R2535 BEFORE this code
existed.

What this proves: MEASURED at R2535 on the shipped nested-subscript face own
readers, a for-loop step that is a NAME bound to a string constant read
refused=key@hop2 and was never followed, even though the honest answer was
derivable from the constant tables. This face follows such a step at CALL time
(module body and function bodies), publishes the chain with BOTH the key value
and the binding label, resolves an annotated or walrus binding of the same
constant, and NAMES an ambiguous name, a name bound to a call, a format or a
comprehension at its hop - never evaluating anything.

Every proof runs against the shipped modules; every fixture lives in a private
temporary directory and no shipped source file is written.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
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

import probe_seam_nested_key_binding_scope as PNKB  # noqa: E402
import probe_seam_nested_subscript_scope as PCNS  # noqa: E402
import probe_seam_subscript_container_scope as PCSC  # noqa: E402
import probe_seam_for_container_name as PCFN  # noqa: E402
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_nested_key_binding_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-nested-key-binding-scope",'
WIRED_SUITE = '"test_probe_seam_nested_key_binding_scope.py"), 6),'

HELPER = "pnkb_helper"
PARTIAL = "pnkb_partial"
PKG = "pnkb_pkg"
MARKER = "pnkb_marker.txt"

NAMED_FIXTURE = ('import importlib\n'
                 '\n'
                 'D = {"a": {"b": ("%s",)}}\n'
                 'KEY = "b"\n'
                 '\n'
                 'for name in D["a"][KEY]:\n'
                 '    importlib.import_module(name)\n' % HELPER)

NAMED_LOCAL_FIXTURE = ('import importlib\n'
                       '\n'
                       'D = {"a": {"b": ("%s",)}}\n'
                       '\n'
                       'def run():\n'
                       '    KEY = "b"\n'
                       '    for name in D["a"][KEY]:\n'
                       '        return importlib.import_module(name).QUIETED\n'
                       % HELPER)

ANNOTATED_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                     'KEY: str = "b"\n'
                     '\n'
                     'for name in D["a"][KEY]:\n'
                     '    pass\n' % HELPER)

WALRUS_STEP_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                       '\n'
                       'for name in D["a"][(KEY := "b")]:\n'
                       '    pass\n' % HELPER)

WALRUS_BOUND_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                        'if (KEY := "b"):\n'
                        '    pass\n'
                        '\n'
                        'for name in D["a"][KEY]:\n'
                        '    pass\n' % HELPER)

AMBIGUOUS_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                     'KEY = "b"\n'
                     'KEY = "zzz"\n'
                     '\n'
                     'for name in D["a"][KEY]:\n'
                     '    pass\n' % HELPER)

CALL_FIXTURE = ('open("%s", "w", encoding="ascii").write("ran\\n")\n'
                '\n'
                'D = {"a": {"b": ("%s",)}}\n'
                '\n'
                'def pick():\n'
                '    return "b"\n'
                '\n'
                'KEY = pick()\n'
                '\n'
                'for name in D["a"][KEY]:\n'
                '    pass\n' % (MARKER, HELPER))

FORMAT_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                  'KEY = "{}".format("b")\n'
                  '\n'
                  'for name in D["a"][KEY]:\n'
                  '    pass\n' % HELPER)

COMPREHENSION_FIXTURE = ('D = {"a": {"b": ("%s",)}}\n'
                         'KEY = [item for item in ("b",)][0]\n'
                         '\n'
                         'for name in D["a"][KEY]:\n'
                         '    pass\n' % HELPER)

MIXED_FIXTURE = ('D = {"a": {"b": {"c": ("%s",)}}}\n'
                 'K1 = "b"\n'
                 '\n'
                 'for name in D["a"][K1]["c"]:\n'
                 '    pass\n' % HELPER)

MIXED_PKG_FIXTURE = ('import %s\n'
                     '\n'
                     'KEY = "b"\n'
                     '\n'
                     'for name in %s.GROUPS["a"][KEY]:\n'
                     '    pass\n' % (PKG, PKG))

MULTI_ELEMENT_FIXTURE = ('D = {"a": {"b": ("pnkb_unused", "%s")}}\n'
                         'KEY = "b"\n'
                         '\n'
                         'for name in D["a"][KEY]:\n'
                         '    pass\n' % HELPER)


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


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


def write_ascii(path, text):
    with open(path, "w", encoding="ascii", newline="\n") as handle:
        handle.write(text)


def helper_text(seams, omit=()):
    kept = [name for name in seams if name not in omit]
    return 'QUIETED = (%s,)\n' % ", ".join('"%s"' % name for name in kept)


def row_of(report, name):
    for row in report["probes"]:
        if row["file"] == name:
            return row
    return {}


def tree_digest(root):
    parts = []
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        if os.path.isfile(path):
            parts.append("%s=%s" % (entry, digest(path)))
    return "|".join(parts)


class World(object):
    """A private root with the helpers and one package module."""

    def __init__(self, with_partial=True):
        self.path = tempfile.mkdtemp(prefix="pnkb-suite-")
        self.seams = PNKB.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(self.seams))
        if with_partial:
            write_ascii(os.path.join(self.path, PARTIAL + ".py"),
                        helper_text(self.seams, omit=self.seams[:1]))
        write_ascii(os.path.join(self.path, PKG + ".py"),
                    'GROUPS = {"a": {"b": ("%s",)}}\n'
                    'NAMES = ("%s",)\n' % (HELPER, HELPER))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pnkb1():
    """A step naming a literal constant resolves with value AND label."""
    table = PNKB.module_bindings(NAMED_FIXTURE)
    ok = check(table.get("name") == (PNKB.TREE_STR, HELPER),
               "AC-PNKB1 a module-level named step resolves (%r)" % (table,))
    local = PNKB.local_bindings(NAMED_LOCAL_FIXTURE)
    ok = check(local.get("name") == (PNKB.TREE_STR, HELPER),
               "AC-PNKB1 a function-body named step resolves (%r)"
               % (local,)) and ok
    report = PNKB.nested_report(NAMED_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "nkb:name@D['a'][KEY='b']",
               "AC-PNKB1 the chain carries BOTH the key value and the "
               "binding label (%r)" % (report,)) and ok
    report = PNKB.nested_report(NAMED_LOCAL_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "nkb:name@D['a'][KEY='b']",
               "AC-PNKB1 the local chain carries both too (%r)"
               % (report,)) and ok
    world = World(with_partial=False)
    try:
        world.write("pnkb_probe.py", NAMED_LOCAL_FIXTURE)
        report = PNKB.audit(world.path, SM)
        row = row_of(report, "pnkb_probe.py")
        expected = "%s:%s@name" % (PDI.SHAPE_IMPORTLIB, HELPER)
        ok = check(row.get("verdict") == PNKB.COVERED
                   and expected in row.get("dynamic", []),
                   "AC-PNKB1 the probe row reads COVERED and names the "
                   "binding (%r)"
                   % ((row.get("verdict"), row.get("dynamic")),)) and ok
        ok = check(row.get("containers") == ["l:name@nkb:name@D['a'][KEY='b']"],
                   "AC-PNKB1 the row carries the chain with the label (%r)"
                   % (row.get("containers"),)) and ok
    finally:
        world.close()
    return ok


def ac_pnkb2():
    """Annotated and walrus bindings resolve; a twice-bound name is ambiguous."""
    table = PNKB.module_bindings(ANNOTATED_FIXTURE)
    ok = check(table.get("name") == (PNKB.TREE_STR, HELPER),
               "AC-PNKB2 an annotated binding resolves (%r)" % (table,))
    report = PNKB.nested_report(ANNOTATED_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "nkb:name@D['a'][KEY='b']",
               "AC-PNKB2 the annotated chain carries the label (%r)"
               % (report,)) and ok
    table = PNKB.module_bindings(WALRUS_STEP_FIXTURE)
    ok = check(table.get("name") == (PNKB.TREE_STR, HELPER),
               "AC-PNKB2 a walrus step binding resolves (%r)" % (table,)) and ok
    report = PNKB.nested_report(WALRUS_STEP_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "nkb:name@D['a'][KEY='b']",
               "AC-PNKB2 the walrus chain carries the label (%r)"
               % (report,)) and ok
    table = PNKB.module_bindings(WALRUS_BOUND_FIXTURE)
    ok = check(table.get("name") == (PNKB.TREE_STR, HELPER),
               "AC-PNKB2 a walrus-bound name resolves too (%r)"
               % (table,)) and ok
    report = PNKB.nested_report(AMBIGUOUS_FIXTURE)
    reason = report.get("refused", {}).get("name") or ""
    ok = check(reason.startswith("ambiguous@hop2:")
               and "KEY" in reason,
               "AC-PNKB2 a twice-bound name is NAMED ambiguous at its hop "
               "(%r)" % (report,)) and ok
    ok = check("name" not in PNKB.module_bindings(AMBIGUOUS_FIXTURE),
               "AC-PNKB2 and it never enters the table") and ok
    return ok


def ac_pnkb3():
    """A name bound to a call, a format or a comprehension is NAMED."""
    world = World(with_partial=False)
    try:
        marker = os.path.join(world.path, MARKER)
        report = PNKB.nested_report(CALL_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("call@hop2:") and "KEY" in reason,
                   "AC-PNKB3 a call-bound name is NAMED call at its hop (%r)"
                   % (report,))
        ok = check(not os.path.exists(marker),
                   "AC-PNKB3 nothing was evaluated (marker absent)") and ok
        ok = check(PNKB.module_bindings(CALL_FIXTURE, world.path).get("name")
                   is None,
                   "AC-PNKB3 and it enters no table") and ok
        report = PNKB.nested_report(FORMAT_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("format@hop2:"),
                   "AC-PNKB3 a format-bound name is NAMED format (%r)"
                   % (report,)) and ok
        report = PNKB.nested_report(COMPREHENSION_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("comprehension@hop2:")
                   or reason.startswith("nested@hop2:"),
                   "AC-PNKB3 a comprehension-bound name is NAMED (%r)"
                   % (report,)) and ok
    finally:
        world.close()
    return ok


def ac_pnkb4():
    """A chain mixing literal and named steps resolves in order, every step."""
    report = PNKB.nested_report(MIXED_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "nkb:name@D['a'][K1='b']['c']",
               "AC-PNKB4 a mixed chain carries every step in order (%r)"
               % (report,))
    ok = check(PNKB.module_bindings(MIXED_FIXTURE).get("name")
               == (PNKB.TREE_STR, HELPER),
               "AC-PNKB4 and it resolves (%r)"
               % (PNKB.module_bindings(MIXED_FIXTURE),)) and ok
    world = World(with_partial=False)
    try:
        table = PNKB.module_bindings(MIXED_PKG_FIXTURE, world.path)
        ok = check(table.get("name") == (PNKB.TREE_STR, HELPER),
                   "AC-PNKB4 a same-root base with a named step resolves (%r)"
                   % (table,)) and ok
        report = PNKB.nested_report(MIXED_PKG_FIXTURE, world.path)
        ok = check(report.get("followed", {}).get("name")
                   == "nkb:name@%s.GROUPS['a'][KEY='b']" % PKG,
                   "AC-PNKB4 and its label carries the module and the label "
                   "(%r)" % (report,)) and ok
        report = PNKB.nested_report(MULTI_ELEMENT_FIXTURE, world.path)
        ok = check(report.get("refused", {}).get("name") == "ambiguous",
                   "AC-PNKB4 a two-element result stays ambiguous (%r)"
                   % (report,)) and ok
    finally:
        world.close()
    return ok


def ac_pnkb5():
    """The reading is read-only: no digest moves across a full audit."""
    world = World(with_partial=False)
    try:
        world.write("pnkb_good_probe.py", NAMED_FIXTURE)
        world.write("pnkb_bad_probe.py", AMBIGUOUS_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        base_before = digest(os.path.join(
            BASE, "probe_seam_nested_subscript_scope.py"))
        render_before = digest(RENDER_MODULE)
        report = PNKB.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PNKB5 the probed tree is byte-identical after the "
                   "audit")
        ok = check(digest(MODULE) == module_before
                   and digest(os.path.join(
                       BASE, "probe_seam_nested_subscript_scope.py"))
                   == base_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PNKB5 the reading moved no shipped digest") and ok
        ok = check(report["verdict"] == PNKB.SEAMS_COVERED
                   and report["counts"][PNKB.COVERED] >= 1,
                   "AC-PNKB5 the audit still answers a verdict (%r)"
                   % (report["counts"],)) and ok
        refusal = PNKB.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PNKB.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PNKB5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pnkb6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PNKB6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PNKB6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PNKB6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PNKB6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PNKB6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PNKB6 no duplicate registry row") and ok
    ok = check(PNKB.LABEL == "os-probe-seam-nested-key-binding-scope",
               "AC-PNKB6 the reconcile label is the face own (%s)"
               % PNKB.LABEL) and ok
    ok = check(PNKB.SEAMS_COVERED == "SEAMS-NESTED-KEY-COVERED",
               "AC-PNKB6 the reading has its own verdict word (%s)"
               % PNKB.SEAMS_COVERED) and ok
    ok = check(PCNS.LABEL == "os-probe-seam-nested-subscript-scope"
               and PCSC.LABEL == "os-probe-seam-subscript-container-scope"
               and PCFN.LABEL == "os-probe-seam-for-container-name",
               "AC-PNKB6 the shipped faces it extends are still named") and ok
    return ok


def main():
    print("PROBE SEAM NESTED KEY BINDING SUITE (AC-PNKB1..AC-PNKB6)")
    results = [ac_pnkb1(), ac_pnkb2(), ac_pnkb3(), ac_pnkb4(), ac_pnkb5(),
               ac_pnkb6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())