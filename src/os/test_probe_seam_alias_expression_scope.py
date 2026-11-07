"""AC-PCAE1..AC-PCAE6 suite for the seam alias-expression scope face (R2529).

Criteria were pinned in state/queue/tech.md:565 at R2527 BEFORE this code
existed.

What this proves: MEASURED at R2527 on the shipped annotated-constant face own
readers, a for-loop over a NAMED constant, an annotated alias whose value is a
subscript or an attribute chain, and a container alias whose elements are names
all read empty from the constant tables and named no shape at all - so a probe
written in any of those shapes read silently absent. This face resolves those
three expressions through the shipped tables and publishes, on the same
cycle-guarded same-root walk, every chain it followed and every shape it
refused. Nothing is evaluated: a call, a format, a comprehension and a nested
container are NAMED rather than guessed.

Every proof runs against the shipped modules; every fixture lives in a private
temporary directory and no shipped source file is written.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import hashlib
import io
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

import probe_seam_alias_expression_scope as PCAE  # noqa: E402
import probe_seam_dynamic_import_scope as PDI  # noqa: E402
import suite_matrix as SM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "probe_seam_alias_expression_scope.py")
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
RENDER_MODULE = os.path.join(SANDBOX, "suite_matrix.py")
WIRED_LABEL = '"os-probe-seam-alias-expression-scope",'
WIRED_SUITE = '"test_probe_seam_alias_expression_scope.py"), 6),'

HELPER = "pcae_helper"
PARTIAL = "pcae_partial"
PKG = "pcae_pkg"
MARKER = "pcae_import_marker.txt"

FOR_MODULE_FIXTURE = ('import importlib\n'
                      '\n'
                      'BASE_NAME = "%s"\n'
                      '\n'
                      'for name in (BASE_NAME,):\n'
                      '    importlib.import_module(name)\n' % HELPER)

FOR_LOCAL_FIXTURE = ('import importlib\n'
                     '\n'
                     'def run():\n'
                     '    base = "%s"\n'
                     '    for name in (base,):\n'
                     '        return importlib.import_module(name).QUIETED\n'
                     % HELPER)

ALIAS_FIXTURE = ('import importlib\n'
                 'import %s\n'
                 '\n'
                 'ALIAS: str = %s.NAMES[1]\n'
                 '\n'
                 'def run():\n'
                 '    return importlib.import_module(ALIAS).QUIETED\n'
                 % (PKG, PKG))

ALIAS_UNRESOLVED_FIXTURE = ('import importlib\n'
                            'import %s\n'
                            '\n'
                            'BAD: str = %s.missing()[0]\n' % (PKG, PKG))

CONTAINER_FIXTURE = ('import importlib\n'
                     '\n'
                     'BASE = "%s"\n'
                     'ALIASES = (BASE,)\n'
                     '\n'
                     'def run():\n'
                     '    return importlib.import_module(ALIASES[0]).QUIETED\n'
                     % HELPER)

CONTAINER_UNRESOLVED_FIXTURE = ('import importlib\n'
                                '\n'
                                'BASE = "pcae_helper"\n'
                                'MIXED = (BASE, build())\n')

REFUSED_FIXTURE = ('import importlib\n'
                   '\n'
                   'def run():\n'
                   '    name = "pcae_" + "helper"\n'
                   '    fmt = "pcae_{0}".format("helper")\n'
                   '    comp = [x for x in ("pcae_unused", "%s")][1]\n'
                   '    return importlib.import_module(name).QUIETED\n'
                   % HELPER)

CALL_FIXTURE = ('import importlib\n'
                '\n'
                'def build():\n'
                '    return "%s"\n'
                '\n'
                'def run():\n'
                '    return importlib.import_module(build()).QUIETED\n'
                % HELPER)


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


def marker_line():
    return 'open("%s", "w", encoding="ascii").write("imported\\n")\n' % MARKER


def row_of(report, name):
    for row in report["probes"]:
        if row["file"] == name:
            return row
    return {}


class World(object):
    """A private root with the helpers and one package module."""

    def __init__(self, with_partial=True):
        self.path = tempfile.mkdtemp(prefix="pcae-suite-")
        self.seams = PCAE.seam_names(SM)
        write_ascii(os.path.join(self.path, HELPER + ".py"),
                    helper_text(self.seams) + marker_line())
        if with_partial:
            write_ascii(os.path.join(self.path, PARTIAL + ".py"),
                        helper_text(self.seams, omit=self.seams[:1])
                        + marker_line())
        write_ascii(os.path.join(self.path, PKG + ".py"),
                    'NAMES = ("pcae_unused", "%s")\n'
                    'CFG = {"NAMES": ("pcae_unused", "%s")}\n'
                    % (HELPER, HELPER))

    def write(self, name, text):
        write_ascii(os.path.join(self.path, name), text)
        return name

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


def ac_pcae1():
    """A for-loop over a single NAMED constant resolves and carries it."""
    table = PCAE.module_bindings(FOR_MODULE_FIXTURE)
    ok = check(table.get("name") == (PCAE.TREE_STR, HELPER),
               "AC-PCAE1 a module-level for-loop over a named constant "
               "resolves (%r)" % (table,))
    local = PCAE.local_bindings(FOR_LOCAL_FIXTURE)
    ok = check(local.get("name") == (PCAE.TREE_STR, HELPER),
               "AC-PCAE1 a function-body for-loop over a named constant "
               "resolves (%r)" % (local,)) and ok
    report = PCAE.alias_report(FOR_MODULE_FIXTURE)
    ok = check(report.get("followed", {}).get("name") == "BASE_NAME",
               "AC-PCAE1 the reading carries the chain it took (%r)"
               % (report,)) and ok
    report = PCAE.alias_report(FOR_LOCAL_FIXTURE)
    ok = check(report.get("followed", {}).get("name") == "base",
               "AC-PCAE1 the local chain is carried too (%r)"
               % (report,)) and ok
    table = PCAE.module_bindings('UNUSED = "x"\n'
                                 'for name in ("a", "b"):\n'
                                 '    pass\n')
    ok = check("name" not in table,
               "AC-PCAE1 a multi-value for target is NOT resolved (%r)"
               % (table,)) and ok
    world = World(with_partial=False)
    try:
        world.write("pcae_for_probe.py", FOR_LOCAL_FIXTURE)
        report = PCAE.audit(world.path, SM)
        row = row_of(report, "pcae_for_probe.py")
        expected = "%s:%s@name" % (PDI.SHAPE_IMPORTLIB, HELPER)
        ok = check(row.get("verdict") == PCAE.COVERED
                   and expected in row.get("dynamic", []),
                   "AC-PCAE1 the probe row reads COVERED and names the "
                   "for-loop binding (%r)"
                   % ((row.get("verdict"), row.get("dynamic")),)) and ok
        ok = check(row.get("aliases") == ["l:name@base"],
                   "AC-PCAE1 the row carries the alias chain (%r)"
                   % (row.get("aliases"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcae2():
    """An annotated alias over a chain resolves, or is NAMED, never empty."""
    world = World(with_partial=False)
    try:
        table = PCAE.module_bindings(ALIAS_FIXTURE, world.path)
        ok = check(table.get("ALIAS") == (PCAE.TREE_STR, HELPER),
                   "AC-PCAE2 an annotated subscript alias resolves (%r)"
                   % (table,))
        report = PCAE.alias_report(ALIAS_FIXTURE, world.path)
        ok = check(report.get("followed", {}).get("ALIAS")
                   == "%s.NAMES" % PKG,
                   "AC-PCAE2 the full chain label is published (%r)"
                   % (report,)) and ok
        report = PCAE.alias_report(ALIAS_UNRESOLVED_FIXTURE, world.path)
        ok = check(report.get("refused", {}).get("BAD") == "call"
                   and "BAD" not in report.get("followed", {}),
                   "AC-PCAE2 an unresolvable alias is NAMED with the hop that "
                   "broke, not absent (%r)" % (report,)) and ok
        table = PCAE.module_bindings(ALIAS_UNRESOLVED_FIXTURE, world.path)
        ok = check("BAD" not in table,
                   "AC-PCAE2 and it does not enter the table (%r)"
                   % (table,)) and ok
        world.write("pcae_alias_probe.py", ALIAS_FIXTURE)
        got = PCAE.audit(world.path, SM)
        row = row_of(got, "pcae_alias_probe.py")
        expected = "%s:%s@ALIAS" % (PDI.SHAPE_IMPORTLIB, HELPER)
        ok = check(row.get("verdict") == PCAE.COVERED
                   and expected in row.get("dynamic", []),
                   "AC-PCAE2 the probe reads COVERED through the alias (%r)"
                   % ((row.get("verdict"), row.get("dynamic")),)) and ok
        ok = check(row.get("aliases") == ["m:ALIAS@pcae_pkg.NAMES"],
                   "AC-PCAE2 the row carries the module chain (%r)"
                   % (row.get("aliases"),)) and ok
    finally:
        world.close()
    return ok


def ac_pcae3():
    """A container alias element is followed, or explicitly refused."""
    table = PCAE.module_bindings(CONTAINER_FIXTURE)
    ok = check(table.get("ALIASES") == (PCAE.TREE_TUPLE, [HELPER]),
               "AC-PCAE3 a container alias substitutes its named element "
               "(%r)" % (table,))
    report = PCAE.alias_report(CONTAINER_FIXTURE)
    ok = check(report.get("followed", {}).get("ALIASES") == "BASE",
               "AC-PCAE3 the element provenance is published (%r)"
               % (report,)) and ok
    got = PCAE.resolve_expression("ALIASES[0]", CONTAINER_FIXTURE)
    ok = check(got == (HELPER, "ALIASES[0]"),
               "AC-PCAE3 the element resolves with its chain (%r)"
               % (got,)) and ok
    report = PCAE.alias_report(CONTAINER_UNRESOLVED_FIXTURE)
    ok = check(report.get("refused", {}).get("MIXED") == "call",
               "AC-PCAE3 an unresolvable element is refused by name (%r)"
               % (report,)) and ok
    table = PCAE.module_bindings(CONTAINER_UNRESOLVED_FIXTURE)
    ok = check("MIXED" not in table,
               "AC-PCAE3 and the container never enters the table (%r)"
               % (table,)) and ok
    world = World(with_partial=False)
    try:
        world.write("pcae_container_probe.py", CONTAINER_FIXTURE)
        got = PCAE.audit(world.path, SM)
        row = row_of(got, "pcae_container_probe.py")
        expected = "%s:%s@ALIASES[0]" % (PDI.SHAPE_IMPORTLIB, HELPER)
        ok = check(row.get("verdict") == PCAE.COVERED
                   and expected in row.get("dynamic", []),
                   "AC-PCAE3 the probe reads COVERED through the element "
                   "(%r)" % ((row.get("verdict"), row.get("dynamic")),)) \
            and ok
    finally:
        world.close()
    return ok


def ac_pcae4():
    """A call, a format and a comprehension are NAMED and never evaluated."""
    text = read_text(MODULE)
    compiles = [part for part in text.split("compile(")[1:]]
    ok = check(not [token for token in ("eval(", "exec(", "__import__(")
                    if token in text],
               "AC-PCAE4 the module never evaluates or imports by name")
    ok = check(all(part.startswith("r\"") or part.startswith("r'")
                   for part in compiles),
               "AC-PCAE4 every compile call in the module is re.compile (%d)"
               % (len(compiles),)) and ok
    report = PCAE.alias_report(REFUSED_FIXTURE)
    refused = report.get("refused", {})
    ok = check(refused.get("name") == "expression",
               "AC-PCAE4 an arithmetic value is named expression (%r)"
               % (refused,)) and ok
    ok = check(refused.get("fmt") == "format",
               "AC-PCAE4 a format call is named format (%r)"
               % (refused,)) and ok
    ok = check(refused.get("comp") == "comprehension",
               "AC-PCAE4 a comprehension element is named, not resolved "
               "(%r)" % (refused,)) and ok
    local = PCAE.local_bindings(REFUSED_FIXTURE)
    ok = check(not [name for name in ("name", "fmt", "comp")
                    if name in local],
               "AC-PCAE4 no refused value enters the table (%r)"
               % (local,)) and ok
    table = PCAE.module_bindings(CALL_FIXTURE)
    ok = check("build" not in table and "name" not in table,
               "AC-PCAE4 a returned container is not a constant (%r)"
               % (table,)) and ok
    report = PCAE.alias_report('VALUE = build()\n')
    ok = check(report.get("refused", {}).get("VALUE") == "call",
               "AC-PCAE4 a plain call is named call (%r)" % (report,)) and ok
    return ok


def ac_pcae5():
    """The reading is read-only: no digest moves, no marker lands."""
    world = World()
    try:
        world.write("pcae_for_probe.py", FOR_LOCAL_FIXTURE)
        world.write("pcae_alias_probe.py", ALIAS_FIXTURE)
        world.write("pcae_container_probe.py", CONTAINER_FIXTURE)
        world.write("pcae_refused.py", REFUSED_FIXTURE)
        before = dict((name, digest(os.path.join(world.path, name)))
                      for name in sorted(os.listdir(world.path)))
        module_before = digest(MODULE)
        render_before = digest(RENDER_MODULE)
        PCAE.audit(world.path, SM)
        PCAE.reading(world.path, SM)
        after = dict((name, digest(os.path.join(world.path, name)))
                     for name in sorted(os.listdir(world.path)))
        ok = check(before == after and not os.path.isfile(
            os.path.join(world.path, MARKER)),
            "AC-PCAE5 every fixture digest is unchanged and nothing landed")
        ok = check(digest(MODULE) == module_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PCAE5 the shipped module and render are unchanged") \
            and ok
        refused = PCAE.reading(os.path.join(world.path, "no-such-root"), SM)
        ok = check(refused.get("refusal") == PCAE.E_NO_ROOT
                   and refused["verdict"] == PCAE.SEAMS_STALE,
                   "AC-PCAE5 a missing root is refused, not silently clean") \
            and ok
        live = PCAE.audit(BASE, SM)
        ok = check(live["verdict"] == PCAE.SEAMS_COVERED,
                   "AC-PCAE5 the REAL tree reads %s (%r)"
                   % (PCAE.SEAMS_COVERED,
                      (live["verdict"], live["counts"]))) and ok
        ok = check(digest(MODULE) == module_before
                   and digest(RENDER_MODULE) == render_before,
                   "AC-PCAE5 the live leg moved no digest either") and ok
        return ok
    finally:
        world.close()


def ac_pcae6():
    """Pure ASCII, stdlib only, no clock, no network, wired once."""
    text = read_text(MODULE)
    suite = read_text(os.path.abspath(__file__))
    ok = check(all(ord(char) < 128 for char in text),
               "AC-PCAE6 the module source is pure ASCII")
    ok = check(all(ord(char) < 128 for char in suite),
               "AC-PCAE6 this suite source is pure ASCII") and ok
    imports = sorted(set(re.findall(r"(?m)^import ([A-Za-z_][A-Za-z0-9_]*)",
                                    text)))
    allowed = ("argparse", "ast", "hashlib", "json", "os", "re", "sys")
    ok = check(not [name for name in imports if name not in allowed],
               "AC-PCAE6 only the allowed stdlib modules are imported (%s)"
               % (",".join(imports),)) and ok
    forbidden = ("time.time", "datetime", "socket", "urllib", "requests",
                 "http.client", "subprocess")
    ok = check(not [token for token in forbidden if token in text],
               "AC-PCAE6 no clock and no network token in the module") and ok
    registry = read_text(REGISTRY)
    ok = check(WIRED_LABEL in registry and WIRED_SUITE in registry,
               "AC-PCAE6 the face and its suite are wired into the registry "
               "exactly once") and ok
    ok = check(registry.count(WIRED_LABEL) == 1
               and registry.count(WIRED_SUITE) == 1,
               "AC-PCAE6 no duplicate registry row") and ok
    ok = check(PCAE.LABEL == "os-probe-seam-alias-expression-scope",
               "AC-PCAE6 the reconcile label is the face own (%s)"
               % PCAE.LABEL) and ok
    ok = check(PCAE.SEAMS_COVERED == "SEAMS-ALIAS-COVERED",
               "AC-PCAE6 the reading has its own verdict word (%s)"
               % PCAE.SEAMS_COVERED) and ok
    return ok


def main():
    print("PROBE SEAM ALIAS EXPRESSION SCOPE SUITE (AC-PCAE1..AC-PCAE6)")
    results = [ac_pcae1(), ac_pcae2(), ac_pcae3(), ac_pcae4(), ac_pcae5(),
               ac_pcae6()]
    passed = len([item for item in results if item])
    print("SUITE %s %d/%d criteria green"
          % ("PASS" if passed == EXPECTED_CRITERIA else "FAIL",
             passed, EXPECTED_CRITERIA))
    return 0 if passed == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())