"""AC-PCSC1..AC-PCSC6 suite for the seam subscript-container scope face (R2533).

Criteria were pinned in state/queue/tech.md:569 at R2531 BEFORE this code
existed.

What this proves: MEASURED at R2531 on the shipped container-name face own
readers, a for-loop over a constant SUBSCRIPT of a container name read
refused=subscript and never followed, even though the dict and its tuple were
BOTH in the table, and a multi-target loop was not read and named nowhere.
This face follows a subscript one constant key deep on a name or on a same-root
module chain, resolves it only when the result holds EXACTLY ONE element and
carries the chain WITH its key, and NAMES every shape it refuses - including
the multi-target loops it used to ignore. Nothing is evaluated.

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

import probe_seam_subscript_container_scope as PCSC  # noqa: E402
import probe_seam_for_container_name as PCFN  # noqa: E402
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_subscript_container_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-subscript-container-scope",'
WIRED_SUITE = '"test_probe_seam_subscript_container_scope.py"), 6),'

HELPER = "pcsc_helper"
PARTIAL = "pcsc_partial"
PKG = "pcsc_pkg"
MARKER = "pcsc_marker.txt"

SUB_FIXTURE = ('import importlib\n'
               '\n'
               'GROUPS = {"a": ("%s",), "b": ("pcsc_unused",)}\n'
               '\n'
               'for name in GROUPS["a"]:\n'
               '    importlib.import_module(name)\n' % HELPER)

SUB_LOCAL_FIXTURE = ('import importlib\n'
                     '\n'
                     'def run():\n'
                     '    groups = {"a": ("%s",)}\n'
                     '    for name in groups["a"]:\n'
                     '        return importlib.import_module(name).QUIETED\n'
                     % HELPER)

MULTI_ELEMENT_FIXTURE = ('import importlib\n'
                         '\n'
                         'GROUPS = {"a": ("pcsc_unused", "%s")}\n'
                         '\n'
                         'for name in GROUPS["a"]:\n'
                         '    importlib.import_module(name)\n' % HELPER)

CHAIN_FIXTURE = ('import importlib\n'
                 'import %s\n'
                 '\n'
                 'for name in %s.GROUPS["a"]:\n'
                 '    importlib.import_module(name)\n' % (PKG, PKG))

CHAIN_BROKEN_FIXTURE = ('import %s\n'
                        '\n'
                        'for name in %s.MISSING["a"]:\n'
                        '    pass\n' % (PKG, PKG))

KEY_MISSING_FIXTURE = ('GROUPS = {"a": ("%s",)}\n'
                       '\n'
                       'for name in GROUPS["zzz"]:\n'
                       '    pass\n' % HELPER)

KEY_NONCONST_FIXTURE = ('GROUPS = {"a": ("%s",)}\n'
                        'KEY = "a"\n'
                        '\n'
                        'for name in GROUPS[KEY]:\n'
                        '    pass\n' % HELPER)

CALL_FIXTURE = ('open("%s", "w", encoding="ascii").write("ran\\n")\n'
                '\n'
                'GROUPS = {"a": ("%s",)}\n'
                '\n'
                'def pick():\n'
                '    return GROUPS\n'
                '\n'
                'for name in pick()["a"]:\n'
                '    pass\n' % (MARKER, HELPER))

FORMAT_FIXTURE = ('GROUPS = {"a": ("%s",)}\n'
                  '\n'
                  'for name in "{}".format("x"):\n'
                  '    pass\n' % HELPER)

COMPREHENSION_FIXTURE = ('for name in [item for item in ("pcsc_helper",)][0]:\n'
                         '    pass\n')

MULTI_TARGET_FIXTURE = ('PAIRS = (("a", "b"),)\n'
                        '\n'
                        'for first, second in PAIRS:\n'
                        '    pass\n')


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
        self.path = tempfile.mkdtemp(prefix="pcsc-suite-")
        self.seams = PCSC.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(self.seams))
        if with_partial:
            write_ascii(os.path.join(self.path, PARTIAL + ".py"),
                        helper_text(self.seams, omit=self.seams[:1]))
        write_ascii(os.path.join(self.path, PKG + ".py"),
                    'GROUPS = {"a": ("%s",)}\n'
                    'NAMES = ("%s",)\n' % (HELPER, HELPER))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pcsc1():
    """A subscript of a NAME container resolves with its key on the chain."""
    table = PCSC.module_bindings(SUB_FIXTURE)
    ok = check(table.get("name") == (PCSC.TREE_STR, HELPER),
               "AC-PCSC1 a module-level subscript loop resolves (%r)"
               % (table,))
    local = PCSC.local_bindings(SUB_LOCAL_FIXTURE)
    ok = check(local.get("name") == (PCSC.TREE_STR, HELPER),
               "AC-PCSC1 a function-body subscript loop resolves (%r)"
               % (local,)) and ok
    report = PCSC.subscript_report(SUB_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "sub:name@GROUPS['a']",
               "AC-PCSC1 the chain carries the key (%r)" % (report,)) and ok
    report = PCSC.subscript_report(SUB_LOCAL_FIXTURE)
    ok = check(report.get("followed", {}).get("name")
               == "sub:name@groups['a']",
               "AC-PCSC1 the local chain carries the key too (%r)"
               % (report,)) and ok
    world = World(with_partial=False)
    try:
        world.write("pcsc_probe.py", SUB_LOCAL_FIXTURE)
        report = PCSC.audit(world.path, SM)
        row = row_of(report, "pcsc_probe.py")
        expected = "%s:%s@name" % (PDI.SHAPE_IMPORTLIB, HELPER)
        ok = check(row.get("verdict") == PCSC.COVERED
                   and expected in row.get("dynamic", []),
                   "AC-PCSC1 the probe row reads COVERED and names the "
                   "subscript binding (%r)"
                   % ((row.get("verdict"), row.get("dynamic")),)) and ok
        ok = check(row.get("containers")
                   == ["l:name@sub:name@groups['a']"],
                   "AC-PCSC1 the row carries the subscript chain (%r)"
                   % (row.get("containers"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcsc2():
    """A same-root chain resolves; a broken hop or a bad key is NAMED."""
    world = World(with_partial=False)
    try:
        table = PCSC.module_bindings(CHAIN_FIXTURE, world.path)
        ok = check(table.get("name") == (PCSC.TREE_STR, HELPER),
                   "AC-PCSC2 a chained subscript resolves (%r)" % (table,))
        report = PCSC.subscript_report(CHAIN_FIXTURE, world.path)
        ok = check(report.get("followed", {}).get("name")
                   == "sub:name@%s.GROUPS['a']" % PKG,
                   "AC-PCSC2 the chained label carries the key (%r)"
                   % (report,)) and ok
        report = PCSC.subscript_report(CHAIN_BROKEN_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("attribute:") and "MISSING" in reason,
                   "AC-PCSC2 a broken chain hop is NAMED (%r)"
                   % (report,)) and ok
        report = PCSC.subscript_report(KEY_MISSING_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("key:GROUPS['zzz']"),
                   "AC-PCSC2 a missing key is NAMED with the key (%r)"
                   % (report,)) and ok
        report = PCSC.subscript_report(KEY_NONCONST_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("key:GROUPS[") and "KEY" in reason,
                   "AC-PCSC2 a non-constant key is NAMED, never guessed (%r)"
                   % (report,)) and ok
        table = PCSC.module_bindings(KEY_NONCONST_FIXTURE, world.path)
        ok = check("name" not in table,
                   "AC-PCSC2 and no refused key enters the table (%r)"
                   % (table,)) and ok
    finally:
        world.close()
    return ok


def ac_pcsc3():
    """A multi-element result is NAMED ambiguous, never the first element."""
    table = PCSC.module_bindings(MULTI_ELEMENT_FIXTURE)
    ok = check("name" not in table,
               "AC-PCSC3 a two-element result never enters the table (%r)"
               % (table,))
    report = PCSC.subscript_report(MULTI_ELEMENT_FIXTURE)
    ok = check(report.get("refused", {}).get("name") == "ambiguous",
               "AC-PCSC3 the shape is NAMED ambiguous (%r)" % (report,)) and ok
    ok = check(report.get("followed", {}).get("name") is None,
               "AC-PCSC3 and nothing is published as followed (%r)"
               % (report,)) and ok
    ok = check(PCSC.module_bindings(MULTI_TARGET_FIXTURE) == {},
               "AC-PCSC3 a multi-target loop resolves nothing") and ok
    report = PCSC.subscript_report(MULTI_TARGET_FIXTURE)
    ok = check(report.get("multi") == ["multi-target:first,second"],
               "AC-PCSC3 a multi-target loop is NAMED instead of ignored (%r)"
               % (report,)) and ok
    world = World(with_partial=False)
    try:
        world.write("pcsc_multi_probe.py", MULTI_TARGET_FIXTURE)
        got = PCSC.audit(world.path, SM)
        row = row_of(got, "pcsc_multi_probe.py")
        ok = check(row.get("multi_targets") == ["multi-target:first,second"],
                   "AC-PCSC3 the row carries the named multi target (%r)"
                   % (row.get("multi_targets"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcsc4():
    """A call, a format and a comprehension are NAMED and never evaluated."""
    world = World(with_partial=False)
    try:
        marker = os.path.join(world.path, MARKER)
        report = PCSC.subscript_report(CALL_FIXTURE, world.path)
        ok = check(report.get("refused", {}).get("name") == "call",
                   "AC-PCSC4 a call base is NAMED call (%r)" % (report,))
        ok = check(not os.path.exists(marker),
                   "AC-PCSC4 nothing was evaluated (marker absent)") and ok
        report = PCSC.subscript_report(KEY_NONCONST_FIXTURE, world.path)
        ok = check(report.get("refused", {}).get("name", "").startswith("key:"),
                   "AC-PCSC4 a computed key is NAMED key (%r)"
                   % (report,)) and ok
        table = PCSC.module_bindings(CALL_FIXTURE, world.path)
        ok = check("name" not in table,
                   "AC-PCSC4 and it never enters the table (%r)"
                   % (table,)) and ok
        ok = check(PCSC.module_bindings(COMPREHENSION_FIXTURE) == {},
                   "AC-PCSC4 a comprehension base resolves nothing") and ok
        report = PCSC.subscript_report(COMPREHENSION_FIXTURE)
        ok = check(report.get("refused", {}).get("name")
                   == "comprehension",
                   "AC-PCSC4 a comprehension is NAMED comprehension (%r)"
                   % (report,)) and ok
        report = PCSC.subscript_report(FORMAT_FIXTURE)
        ok = check(report.get("refused", {}).get("name") == "format",
                   "AC-PCSC4 a format call iterable is NAMED format by the "
                   "shipped law, never treated as a container (%r)"
                   % (report,)) and ok
    finally:
        world.close()
    return ok


def ac_pcsc5():
    """The reading is read-only: no digest moves across a full audit."""
    world = World(with_partial=False)
    try:
        world.write("pcsc_good_probe.py", SUB_FIXTURE)
        world.write("pcsc_bad_probe.py", CHAIN_BROKEN_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        base_before = digest(os.path.join(BASE,
                                          "probe_seam_for_container_name.py"))
        render_before = digest(RENDER_MODULE)
        report = PCSC.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PCSC5 the probed tree is byte-identical after the audit")
        ok = check(digest(MODULE) == module_before
                   and digest(os.path.join(BASE,
                                           "probe_seam_for_container_name.py"))
                   == base_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PCSC5 the reading moved no shipped digest") and ok
        ok = check(report["verdict"] == PCSC.SEAMS_COVERED
                   and report["counts"][PCSC.COVERED] >= 1,
                   "AC-PCSC5 the audit still answers a verdict (%r)"
                   % (report["counts"],)) and ok
        refusal = PCSC.reading(os.path.join(world.path, "absent"), SM)
        ok = check(refusal.get("refusal") == PCSC.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PCSC5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcsc6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PCSC6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PCSC6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PCSC6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PCSC6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PCSC6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PCSC6 no duplicate registry row") and ok
    ok = check(PCSC.LABEL == "os-probe-seam-subscript-container-scope",
               "AC-PCSC6 the reconcile label is the face own (%s)"
               % PCSC.LABEL) and ok
    ok = check(PCSC.SEAMS_COVERED == "SEAMS-SUBSCRIPT-COVERED",
               "AC-PCSC6 the reading has its own verdict word (%s)"
               % PCSC.SEAMS_COVERED) and ok
    ok = check(PCFN.LABEL == "os-probe-seam-for-container-name",
               "AC-PCSC6 the shipped base face it extends is still named (%s)"
               % PCFN.LABEL) and ok
    return ok


def main():
    print("PROBE SEAM SUBSCRIPT CONTAINER SUITE (AC-PCSC1..AC-PCSC6)")
    results = [ac_pcsc1(), ac_pcsc2(), ac_pcsc3(), ac_pcsc4(), ac_pcsc5(),
               ac_pcsc6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())