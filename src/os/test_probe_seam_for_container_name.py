"""AC-PCAF1..AC-PCAF6 suite for the seam container-name scope face (R2531).

Criteria were pinned in state/queue/tech.md:567 at R2529 BEFORE this code
existed.

What this proves: MEASURED at R2529 on the shipped alias-expression face own
readers, a for-loop over a NAMED container still read empty and named no
shape at all - even though the container itself was in the table - so a probe
written that way read silently absent, and a multi-element container read
nothing where the honest answer is AMBIGUOUS. This face resolves a for-loop
whose iterable is a NAME, an attribute chain into a same-root module, or a
container literal, only when it holds EXACTLY ONE element, and it publishes on
the same cycle-guarded walk every chain it followed and every shape it
refused. Nothing is evaluated: a call, a format, a comprehension and a string
are NAMED rather than guessed.

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

import probe_seam_for_container_name as PCFN  # noqa: E402
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_for_container_name.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-for-container-name",'
WIRED_SUITE = '"test_probe_seam_for_container_name.py"), 6),'

HELPER = "pcfn_helper"
PARTIAL = "pcfn_partial"
PKG = "pcfn_pkg"
MARKER = "pcfn_marker.txt"

CONTAINER_FIXTURE = ('import importlib\n'
                     '\n'
                     'NAMES = ("%s",)\n'
                     '\n'
                     'for name in NAMES:\n'
                     '    importlib.import_module(name)\n' % HELPER)

CONTAINER_LOCAL_FIXTURE = ('import importlib\n'
                           '\n'
                           'def run():\n'
                           '    names = ("%s",)\n'
                           '    for name in names:\n'
                           '        return importlib.import_module(name).QUIETED\n'
                           % HELPER)

MULTI_FIXTURE = ('import importlib\n'
                 '\n'
                 'NAMES = ("pcfn_unused", "%s")\n'
                 '\n'
                 'for name in NAMES:\n'
                 '    importlib.import_module(name)\n' % HELPER)

EMPTY_FIXTURE = ('NAMES = ()\n'
                 '\n'
                 'for name in NAMES:\n'
                 '    pass\n')

STRING_FIXTURE = ('for char in "pcfn":\n'
                  '    pass\n')

CHAIN_FIXTURE = ('import importlib\n'
                 'import %s\n'
                 '\n'
                 'for name in %s.NAMES:\n'
                 '    importlib.import_module(name)\n' % (PKG, PKG))

BROKEN_CHAIN_FIXTURE = ('import %s\n'
                        '\n'
                        'for name in %s.MISSING:\n'
                        '    pass\n' % (PKG, PKG))

SUBSCRIPT_REFUSED_FIXTURE = ('GROUPS = {"a": ("pcfn_helper",)}\n'
                             '\n'
                             'for name in GROUPS["a"]:\n'
                             '    pass\n')

CALL_FIXTURE = ('open("%s", "w", encoding="ascii").write("ran\\n")\n'
                '\n'
                'def build():\n'
                '    return ("%s",)\n'
                '\n'
                'for name in build():\n'
                '    pass\n' % (MARKER, HELPER))

FORMAT_FIXTURE = ('for name in "pcfn_{0}".format("helper"):\n'
                  '    pass\n')

COMPREHENSION_FIXTURE = ('for name in [item for item in ("pcfn_helper",)]:\n'
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
        self.path = tempfile.mkdtemp(prefix="pcfn-suite-")
        self.seams = PCFN.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(self.seams))
        if with_partial:
            write_ascii(os.path.join(self.path, PARTIAL + ".py"),
                        helper_text(self.seams, omit=self.seams[:1]))
        write_ascii(os.path.join(self.path, PKG + ".py"),
                    'NAMES = ("%s",)\n'
                    'CFG = {"NAMES": ("%s",)}\n' % (HELPER, HELPER))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pcaf1():
    """A for-loop over a single-element container name resolves and carries it."""
    table = PCFN.module_bindings(CONTAINER_FIXTURE)
    ok = check(table.get("name") == (PCFN.TREE_STR, HELPER),
               "AC-PCAF1 a module-level loop over a container name resolves "
               "(%r)" % (table,))
    local = PCFN.local_bindings(CONTAINER_LOCAL_FIXTURE)
    ok = check(local.get("name") == (PCFN.TREE_STR, HELPER),
               "AC-PCAF1 a function-body loop over a container name resolves "
               "(%r)" % (local,)) and ok
    report = PCFN.container_report(CONTAINER_FIXTURE)
    ok = check(report.get("followed", {}).get("name") == "for:name@NAMES",
               "AC-PCAF1 the reading carries the chain it took (%r)"
               % (report,)) and ok
    ok = check(report.get("containers", {}).get("name", {}).get("elements")
               == 1,
               "AC-PCAF1 the container count is published (%r)"
               % (report,)) and ok
    report = PCFN.container_report(CONTAINER_LOCAL_FIXTURE)
    ok = check(report.get("followed", {}).get("name") == "for:name@names",
               "AC-PCAF1 the local chain is carried too (%r)"
               % (report,)) and ok
    world = World(with_partial=False)
    try:
        world.write("pcfn_container_probe.py", CONTAINER_LOCAL_FIXTURE)
        report = PCFN.audit(world.path, SM)
        row = row_of(report, "pcfn_container_probe.py")
        expected = "%s:%s@name" % (PDI.SHAPE_IMPORTLIB, HELPER)
        ok = check(row.get("verdict") == PCFN.COVERED
                   and expected in row.get("dynamic", []),
                   "AC-PCAF1 the probe row reads COVERED and names the "
                   "container binding (%r)"
                   % ((row.get("verdict"), row.get("dynamic")),)) and ok
        ok = check(row.get("containers") == ["l:name@for:name@names"],
                   "AC-PCAF1 the row carries the container chain (%r)"
                   % (row.get("containers"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcaf2():
    """A multi-element container is NAMED ambiguous, never resolved."""
    table = PCFN.module_bindings(MULTI_FIXTURE)
    ok = check("name" not in table,
               "AC-PCAF2 a multi-element container never enters the table "
               "(%r)" % (table,))
    report = PCFN.container_report(MULTI_FIXTURE)
    ok = check(report.get("refused", {}).get("name") == "ambiguous",
               "AC-PCAF2 the shape is NAMED ambiguous (%r)"
               % (report,)) and ok
    ok = check(report.get("followed", {}).get("name") is None,
               "AC-PCAF2 and nothing is published as followed (%r)"
               % (report,)) and ok
    table = PCFN.module_bindings(EMPTY_FIXTURE)
    ok = check("name" not in table,
               "AC-PCAF2 an empty container resolves nothing (%r)"
               % (table,)) and ok
    report = PCFN.container_report(EMPTY_FIXTURE)
    ok = check(report.get("refused", {}).get("name") == "empty",
               "AC-PCAF2 an empty container is NAMED empty (%r)"
               % (report,)) and ok
    table = PCFN.module_bindings(STRING_FIXTURE)
    ok = check("char" not in table,
               "AC-PCAF2 a string iterable resolves nothing (%r)"
               % (table,)) and ok
    report = PCFN.container_report(STRING_FIXTURE)
    ok = check(report.get("refused", {}).get("char") == "string",
               "AC-PCAF2 a string iterable is NAMED string (%r)"
               % (report,)) and ok
    return ok


def ac_pcaf3():
    """A chain into a same-root module resolves, a broken one is NAMED."""
    world = World(with_partial=False)
    try:
        table = PCFN.module_bindings(CHAIN_FIXTURE, world.path)
        ok = check(table.get("name") == (PCFN.TREE_STR, HELPER),
                   "AC-PCAF3 a chain container resolves (%r)" % (table,))
        report = PCFN.container_report(CHAIN_FIXTURE, world.path)
        ok = check(report.get("followed", {}).get("name")
                   == "for:name@%s.NAMES" % PKG,
                   "AC-PCAF3 the chain label is published (%r)"
                   % (report,)) and ok
        table = PCFN.module_bindings(BROKEN_CHAIN_FIXTURE, world.path)
        ok = check("name" not in table,
                   "AC-PCAF3 a broken chain resolves nothing (%r)"
                   % (table,)) and ok
        report = PCFN.container_report(BROKEN_CHAIN_FIXTURE, world.path)
        reason = report.get("refused", {}).get("name") or ""
        ok = check(reason.startswith("attribute:") and "MISSING" in reason,
                   "AC-PCAF3 the broken hop is NAMED (%r)" % (report,)) and ok
        report = PCFN.container_report(SUBSCRIPT_REFUSED_FIXTURE, world.path)
        ok = check(report.get("refused", {}).get("name")
                   == "subscript:GROUPS",
                   "AC-PCAF3 a subscript container is refused by name (%r)"
                   % (report,)) and ok
    finally:
        world.close()
    return ok


def ac_pcaf4():
    """A call, a format and a comprehension are NAMED and never evaluated."""
    world = World(with_partial=False)
    try:
        marker = os.path.join(world.path, MARKER)
        report = PCFN.container_report(CALL_FIXTURE, world.path)
        ok = check(report.get("refused", {}).get("name") == "call",
                   "AC-PCAF4 a call iterable is NAMED call (%r)"
                   % (report,))
        ok = check(not os.path.exists(marker),
                   "AC-PCAF4 nothing was evaluated (marker absent)") and ok
        report = PCFN.container_report(FORMAT_FIXTURE, world.path)
        ok = check(report.get("refused", {}).get("name") == "format",
                   "AC-PCAF4 a format iterable is NAMED format (%r)"
                   % (report,)) and ok
        report = PCFN.container_report(COMPREHENSION_FIXTURE, world.path)
        ok = check(report.get("refused", {}).get("name") == "comprehension",
                   "AC-PCAF4 a comprehension is NAMED comprehension (%r)"
                   % (report,)) and ok
        table = PCFN.module_bindings(CALL_FIXTURE, world.path)
        ok = check("name" not in table,
                   "AC-PCAF4 and none of them enters the table (%r)"
                   % (table,)) and ok
    finally:
        world.close()
    return ok


def ac_pcaf5():
    """The reading is read-only: no digest moves across a full audit."""
    world = World(with_partial=False)
    try:
        world.write("pcfn_good_probe.py", CONTAINER_FIXTURE)
        world.write("pcfn_bad_probe.py", BROKEN_CHAIN_FIXTURE)
        before = tree_digest(world.path)
        module_before = digest(MODULE)
        render_before = digest(RENDER_MODULE)
        report = PCFN.audit(world.path, SM)
        ok = check(tree_digest(world.path) == before,
                   "AC-PCAF5 the probed tree is byte-identical after the "
                   "audit")
        ok = check(digest(MODULE) == module_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PCAF5 the reading moved no shipped digest") and ok
        ok = check(report["verdict"] == PCFN.SEAMS_COVERED
                   and report["counts"][PCFN.COVERED] >= 1,
                   "AC-PCAF5 the audit still answers a verdict (%r)"
                   % (report["counts"],)) and ok
        refusal = PCFN.reading(os.path.join(world.path, "absent"),
                               SM)
        ok = check(refusal.get("refusal") == PCFN.E_NO_ROOT
                   and refusal.get("probes") == [],
                   "AC-PCAF5 a missing root is refused, not raised (%r)"
                   % (refusal.get("refusal"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcaf6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PCAF6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PCAF6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PCAF6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PCAF6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PCAF6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PCAF6 no duplicate registry row") and ok
    ok = check(PCFN.LABEL == "os-probe-seam-for-container-name",
               "AC-PCAF6 the reconcile label is the face own (%s)"
               % PCFN.LABEL) and ok
    ok = check(PCFN.SEAMS_COVERED == "SEAMS-CONTAINER-COVERED",
               "AC-PCAF6 the reading has its own verdict word (%s)"
               % PCFN.SEAMS_COVERED) and ok
    return ok


def main():
    print("PROBE SEAM FOR CONTAINER NAME SUITE (AC-PCAF1..AC-PCAF6)")
    results = [ac_pcaf1(), ac_pcaf2(), ac_pcaf3(), ac_pcaf4(), ac_pcaf5(),
               ac_pcaf6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())